import pytest
import os
from itertools import product

import cadquery as cq
from cadquery.occ_impl.exporters.assembly import exportAssembly, exportCAF

from OCP.gp import gp_XYZ


@pytest.fixture
def simple_assy():

    b1 = cq.Solid.makeBox(1, 1, 1)
    b2 = cq.Workplane().box(1, 1, 2)
    b3 = cq.Workplane().pushPoints([(0, 0), (-2, -5)]).box(1, 1, 3)

    assy = cq.Assembly(b1, loc=cq.Location(cq.Vector(2, -5, 0)))
    assy.add(b2, loc=cq.Location(cq.Vector(1, 1, 0)))
    assy.add(b3, loc=cq.Location(cq.Vector(2, 3, 0)))

    return assy


@pytest.fixture
def nested_assy():

    b1 = cq.Workplane().box(1, 1, 1).faces("<Z").tag("top_face").end()
    b2 = cq.Workplane().box(1, 1, 1).faces("<Z").tag("bottom_face").end()
    b3 = (
        cq.Workplane()
        .pushPoints([(-2, 0), (2, 0)])
        .tag("pts")
        .box(1, 1, 0.5)
        .tag("boxes")
    )

    assy = cq.Assembly(b1, loc=cq.Location(cq.Vector(0, 0, 0)), name="TOP")
    assy2 = cq.Assembly(b2, loc=cq.Location(cq.Vector(0, 4, 0)), name="SECOND")
    assy2.add(b3, loc=cq.Location(cq.Vector(0, 4, 0)), name="BOTTOM")

    assy.add(assy2, color=cq.Color("green"))

    return assy


@pytest.fixture
def box_and_vertex():

    assy = cq.Assembly()
    box_wp = cq.Workplane().box(1, 2, 3)
    assy.add(box_wp, name="box")
    vertex_wp = cq.Workplane().newObject([cq.Vertex.makeVertex(0, 0, 0)])
    assy.add(vertex_wp, name="vertex")
    return assy


def test_color():

    c1 = cq.Color("red")
    assert c1.wrapped.GetRGB().Red() == 1
    assert c1.wrapped.Alpha() == 1

    c2 = cq.Color(1, 0, 0)
    assert c2.wrapped.GetRGB().Red() == 1
    assert c2.wrapped.Alpha() == 1

    c3 = cq.Color(1, 0, 0, 0.5)
    assert c3.wrapped.GetRGB().Red() == 1
    assert c3.wrapped.Alpha() == 0.5

    with pytest.raises(ValueError):
        cq.Color("?????")

    with pytest.raises(ValueError):
        cq.Color(1, 2, 3, 4, 5)


def test_assembly(simple_assy, nested_assy):

    # basic checks
    assert len(simple_assy.objects) == 3
    assert len(simple_assy.children) == 2
    assert len(simple_assy.shapes) == 1

    assert len(nested_assy.objects) == 3
    assert len(nested_assy.children) == 1
    assert nested_assy.objects["SECOND"].parent is nested_assy

    # bottom-up traversal
    kvs = list(nested_assy.traverse())

    assert kvs[0][0] == "BOTTOM"
    assert len(kvs[0][1].shapes[0].Solids()) == 2
    assert kvs[-1][0] == "TOP"


def test_step_export(nested_assy):

    exportAssembly(nested_assy, "nested.step")

    w = cq.importers.importStep("nested.step")
    assert w.solids().size() == 4

    # check that locations were applied correctly
    c = cq.Compound.makeCompound(w.solids().vals()).Center()
    c.toTuple()
    assert pytest.approx(c.toTuple()) == (0, 4, 0)


def test_native_export(simple_assy):

    exportCAF(simple_assy, "assy.xml")

    # only sanity check for now
    assert os.path.exists("assy.xml")


def test_save(simple_assy, nested_assy):

    simple_assy.save("simple.step")
    assert os.path.exists("simple.step")

    simple_assy.save("simple.xml")
    assert os.path.exists("simple.xml")

    simple_assy.save("simple.step")
    assert os.path.exists("simple.step")

    simple_assy.save("simple.stp", "STEP")
    assert os.path.exists("simple.stp")

    simple_assy.save("simple.caf", "XML")
    assert os.path.exists("simple.caf")

    with pytest.raises(ValueError):
        simple_assy.save("simple.dxf")

    with pytest.raises(ValueError):
        simple_assy.save("simple.step", "DXF")


def test_constrain(simple_assy, nested_assy):

    subassy1 = simple_assy.children[0]
    subassy2 = simple_assy.children[1]

    b1 = simple_assy.obj
    b2 = subassy1.obj
    b3 = subassy2.obj

    simple_assy.constrain(
        simple_assy.name, b1.Faces()[0], subassy1.name, b2.faces("<Z").val(), "Plane"
    )
    simple_assy.constrain(
        simple_assy.name, b1.Faces()[0], subassy2.name, b3.faces("<Z").val(), "Axis"
    )
    simple_assy.constrain(
        subassy1.name,
        b2.faces(">Z").val(),
        subassy2.name,
        b3.faces("<Z").val(),
        "Point",
    )

    assert len(simple_assy.constraints) == 3

    nested_assy.constrain("TOP@faces@>Z", "SECOND/BOTTOM@faces@<Z", "Plane")
    nested_assy.constrain("TOP@faces@>X", "SECOND/BOTTOM@faces@<X", "Axis")

    assert len(nested_assy.constraints) == 2

    constraint = nested_assy.constraints[0]

    assert constraint.objects == ("TOP", "SECOND")
    assert (
        constraint.sublocs[0]
        .wrapped.Transformation()
        .TranslationPart()
        .IsEqual(gp_XYZ(), 1e-9)
    )
    assert constraint.sublocs[1].wrapped.IsEqual(
        nested_assy.objects["SECOND/BOTTOM"].loc.wrapped
    )

    simple_assy.solve()

    assert (
        simple_assy.loc.wrapped.Transformation()
        .TranslationPart()
        .IsEqual(gp_XYZ(2, -5, 0), 1e-9)
    )

    assert (
        simple_assy.children[0]
        .loc.wrapped.Transformation()
        .TranslationPart()
        .IsEqual(gp_XYZ(-1, 0.5, 0.5), 1e-6)
    )

    nested_assy.solve()

    assert (
        nested_assy.children[0]
        .loc.wrapped.Transformation()
        .TranslationPart()
        .IsEqual(gp_XYZ(2, -4, 0.75), 1e-6)
    )


def test_constrain_with_tags(nested_assy):

    nested_assy.add(None, name="dummy")
    nested_assy.constrain("TOP?top_face", "SECOND/BOTTOM", "Plane")

    assert len(nested_assy.constraints) == 1

    # test selection of a non-shape object
    with pytest.raises(ValueError):
        nested_assy.constrain("SECOND/BOTTOM ? pts", "dummy", "Plane")


def test_duplicate_name(nested_assy):

    with pytest.raises(ValueError):
        nested_assy.add(None, name="SECOND")


def test_empty_solve(nested_assy):

    with pytest.raises(ValueError):
        nested_assy.solve()


def test_expression_grammar(nested_assy):

    nested_assy.constrain(
        "TOP@faces@>Z", "SECOND/BOTTOM@vertices@>X and >Y and >Z", "Point"
    )


def test_InPlane_constraint(box_and_vertex):

    # add first constraint
    box_and_vertex.constrain(
        "box",
        box_and_vertex.children[0].obj.faces(">X").val(),
        "vertex",
        box_and_vertex.children[1].obj.val(),
        "InPlane",
        param=0,
    )
    box_and_vertex.solve()

    x_pos = (
        box_and_vertex.children[1].loc.wrapped.Transformation().TranslationPart().X()
    )
    assert x_pos == pytest.approx(0.5)

    # add a second InPlane constraint
    box_and_vertex.constrain("box@faces@>Y", "vertex", "InPlane", param=0)
    box_and_vertex.solve()

    vertex_translation_part = (
        box_and_vertex.children[1].loc.wrapped.Transformation().TranslationPart()
    )
    # should still be on the >X face from the first constraint
    assert vertex_translation_part.X() == pytest.approx(0.5)
    # now should additionally be on the >Y face
    assert vertex_translation_part.Y() == pytest.approx(1)

    # add a third InPlane constraint
    box_and_vertex.constrain("box@faces@>Z", "vertex", "InPlane", param=0)
    box_and_vertex.solve()

    # should now be on the >X and >Y and >Z corner
    assert (
        box_and_vertex.children[1]
        .loc.wrapped.Transformation()
        .TranslationPart()
        .IsEqual(gp_XYZ(0.5, 1, 1.5), 1e-6)
    )


def test_InPlane_3_parts(box_and_vertex):

    cylinder_height = 2
    cylinder = cq.Workplane().circle(0.1).extrude(cylinder_height)
    box_and_vertex.add(cylinder, name="cylinder")
    box_and_vertex.constrain("box@faces@>Z", "cylinder@faces@<Z", "Plane")
    box_and_vertex.constrain("cylinder@faces@>Z", "vertex", "InPlane")
    box_and_vertex.constrain("box@faces@>X", "vertex", "InPlane")
    box_and_vertex.solve()
    vertex_translation_part = (
        box_and_vertex.children[1].loc.wrapped.Transformation().TranslationPart()
    )
    assert vertex_translation_part.Z() == pytest.approx(1.5 + cylinder_height)
    assert vertex_translation_part.X() == pytest.approx(0.5)


@pytest.mark.parametrize("param1", [-1, 0, 2])
@pytest.mark.parametrize("param0", [-2, 0, 0.01])
def test_InPlane_param(box_and_vertex, param0, param1):

    box_and_vertex.constrain("box@faces@>Z", "vertex", "InPlane", param=param0)
    box_and_vertex.constrain("box@faces@>X", "vertex", "InPlane", param=param1)
    box_and_vertex.solve()

    vertex_translation_part = (
        box_and_vertex.children[1].loc.wrapped.Transformation().TranslationPart()
    )
    assert vertex_translation_part.Z() - 1.5 == pytest.approx(param0, abs=1e-6)
    assert vertex_translation_part.X() - 0.5 == pytest.approx(param1, abs=1e-6)


def test_constraint_getPlane():
    """
    Test that _getPlane does the right thing with different arguments
    """
    ids = (0, 1)
    sublocs = (cq.Location(), cq.Location())

    def make_constraint(shape0):
        return cq.Constraint(ids, (shape0, shape0), sublocs, "InPlane", 0)

    def fail_this(shape0):
        c0 = make_constraint(shape0)
        with pytest.raises(ValueError):
            c0._getPlane(c0.args[0])

    def resulting_plane(shape0):
        c0 = make_constraint(shape0)
        return c0._getPlane(c0.args[0])

    # point should fail
    fail_this(cq.Vertex.makeVertex(0, 0, 0))

    # line should fail
    fail_this(cq.Edge.makeLine(cq.Vector(1, 0, 0), cq.Vector(0, 0, 0)))

    # planar edge (circle) should succeed
    origin = cq.Vector(1, 2, 3)
    direction = cq.Vector(4, 5, 6).normalized()
    p1 = resulting_plane(cq.Edge.makeCircle(1, pnt=origin, dir=direction))
    assert p1.zDir == direction
    assert p1.origin == origin

    # planar edge (spline) should succeed
    # it's a touch risky calling a spline a planar edge, but lets see if it's within tolerance
    points0 = [cq.Vector(x) for x in [(-1, 0, 1), (0, 1, 1), (1, 0, 1), (0, -1, 1)]]
    planar_spline = cq.Edge.makeSpline(points0, periodic=True)
    p2 = resulting_plane(planar_spline)
    assert p2.origin == planar_spline.Center()
    assert p2.zDir == cq.Vector(0, 0, 1)

    # non-planar edge should fail
    points1 = [cq.Vector(x) for x in [(-1, 0, -1), (0, 1, 1), (1, 0, -1), (0, -1, 1)]]
    nonplanar_spline = cq.Edge.makeSpline(points1, periodic=True)
    fail_this(nonplanar_spline)

    # planar wire should succeed
    # make a triangle in the XZ plane
    points2 = [cq.Vector(x) for x in [(-1, 0, -1), (0, 0, 1), (1, 0, -1)]]
    points2.append(points2[0])
    triangle = cq.Wire.makePolygon(points2)
    p3 = resulting_plane(triangle)
    assert p3.origin == triangle.Center()
    assert p3.zDir == cq.Vector(0, 1, 0)

    # non-planar wire should fail
    points3 = [cq.Vector(x) for x in [(-1, 0, -1), (0, 1, 1), (1, 0, 0), (0, -1, 1)]]
    wonky_shape = cq.Wire.makePolygon(points3)
    fail_this(wonky_shape)

    # all faces should succeed
    for length, width in product([None, 10], [None, 11]):
        f0 = cq.Face.makePlane(
            length=length, width=width, basePnt=(1, 2, 3), dir=(1, 0, 0)
        )
        p4 = resulting_plane(f0)
        if length and width:
            assert p4.origin == cq.Vector(1, 2, 3)
        assert p4.zDir == cq.Vector(1, 0, 0)

    f1 = cq.Face.makeFromWires(triangle, [])
    p5 = resulting_plane(f1)
    # not sure why, but the origins only roughly line up
    assert (p5.origin - triangle.Center()).Length < 0.1
    assert p5.zDir == cq.Vector(0, 1, 0)

    # shell... not sure?

    # solid should fail
    fail_this(cq.Solid.makeBox(1, 1, 1))
