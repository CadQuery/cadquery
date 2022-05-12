import pytest
import os
from itertools import product
from math import degrees

import cadquery as cq
from cadquery.occ_impl.exporters.assembly import (
    exportAssembly,
    exportCAF,
    exportVTKJS,
    exportVRML,
)
from cadquery.occ_impl.assembly import toJSON
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
def nested_assy_sphere():

    b1 = cq.Workplane().box(1, 1, 1).faces("<Z").tag("top_face").end()
    b2 = cq.Workplane().box(1, 1, 1).faces("<Z").tag("bottom_face").end()
    b3 = cq.Workplane().pushPoints([(-2, 0), (2, 0)]).tag("pts").sphere(1).tag("boxes")

    assy = cq.Assembly(b1, loc=cq.Location(cq.Vector(0, 0, 0)), name="TOP")
    assy2 = cq.Assembly(b2, loc=cq.Location(cq.Vector(0, 4, 0)), name="SECOND")
    assy2.add(b3, loc=cq.Location(cq.Vector(0, 4, 0)), name="BOTTOM")

    assy.add(assy2, color=cq.Color("green"))

    return assy


@pytest.fixture
def empty_top_assy():

    b1 = cq.Workplane().box(1, 1, 1)

    assy = cq.Assembly()
    assy.add(b1, color=cq.Color("green"))

    return assy


@pytest.fixture
def box_and_vertex():

    box_wp = cq.Workplane().box(1, 2, 3)
    assy = cq.Assembly(box_wp, name="box")
    vertex_wp = cq.Workplane().newObject([cq.Vertex.makeVertex(0, 0, 0)])
    assy.add(vertex_wp, name="vertex")

    return assy


@pytest.fixture
def metadata_assy():

    b1 = cq.Solid.makeBox(1, 1, 1)
    b2 = cq.Workplane().box(1, 1, 2)

    assy = cq.Assembly(
        b1,
        loc=cq.Location(cq.Vector(2, -5, 0)),
        name="base",
        metadata={"b1": "base-data"},
    )
    sub_assy = cq.Assembly(
        b2, loc=cq.Location(cq.Vector(1, 1, 1)), name="sub", metadata={"b2": "sub-data"}
    )
    assy.add(sub_assy)

    return assy


@pytest.fixture
def simple_assy2():

    b1 = cq.Workplane().box(1, 1, 1)
    b2 = cq.Workplane().box(2, 1, 1)

    assy = cq.Assembly()
    assy.add(b1, name="b1")
    assy.add(b2, loc=cq.Location(cq.Vector(0, 0, 4)), name="b2")

    return assy


def test_metadata(metadata_assy):
    """Verify the metadata is present in both the base and sub assemblies"""
    assert metadata_assy.metadata["b1"] == "base-data"
    # The metadata should be able to be modified
    metadata_assy.metadata["b2"] = 0
    assert len(metadata_assy.metadata) == 2
    # Test that metadata was copied by _copy() during the processing of adding the subassembly
    assert metadata_assy.children[0].metadata["b2"] == "sub-data"


def solve_result_check(solve_result: dict) -> bool:
    checks = [
        solve_result["success"] == True,
        solve_result["iterations"]["inf_pr"][-1] < 1e-9,
    ]
    return all(checks)


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


def test_vtkjs_export(nested_assy):

    exportVTKJS(nested_assy, "assy")

    # only sanity check for now
    assert os.path.exists("assy.zip")


def test_vrml_export(simple_assy):

    exportVRML(simple_assy, "assy.wrl")

    # only sanity check for now
    assert os.path.exists("assy.wrl")


def test_toJSON(simple_assy, nested_assy, empty_top_assy):

    r1 = toJSON(simple_assy)
    r2 = toJSON(simple_assy)
    r3 = toJSON(empty_top_assy)

    assert len(r1) == 3
    assert len(r2) == 3
    assert len(r3) == 1


@pytest.mark.parametrize(
    "extension, args",
    [
        ("step", ()),
        ("xml", ()),
        ("stp", ("STEP",)),
        ("caf", ("XML",)),
        ("wrl", ("VRML",)),
    ],
)
def test_save(extension, args, nested_assy, nested_assy_sphere):

    filename = "nested." + extension
    nested_assy.save(filename, *args)
    assert os.path.exists(filename)


def test_save_gltf(nested_assy_sphere):

    nested_assy_sphere.save("nested.glb", "GLTF")
    assert os.path.exists("nested.glb")
    assert os.path.getsize("nested.glb") > 50 * 1024


def test_save_vtkjs(nested_assy):

    nested_assy.save("nested", "VTKJS")
    assert os.path.exists("nested.zip")


def test_save_raises(nested_assy):

    with pytest.raises(ValueError):
        nested_assy.save("nested.dxf")

    with pytest.raises(ValueError):
        nested_assy.save("nested.step", "DXF")


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

    assert solve_result_check(simple_assy._solve_result)

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

    assert solve_result_check(nested_assy._solve_result)

    assert (
        nested_assy.children[0]
        .loc.wrapped.Transformation()
        .TranslationPart()
        .IsEqual(gp_XYZ(2, -4, 0.75), 1e-6)
    )


def test_constrain_with_tags(nested_assy):

    nested_assy.add(None, name="dummy")
    nested_assy.constrain("TOP?top_face", "SECOND/BOTTOM", "Point")

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


def test_PointInPlane_constraint(box_and_vertex):

    # add first constraint
    box_and_vertex.constrain(
        "vertex",
        box_and_vertex.children[0].obj.val(),
        "box",
        box_and_vertex.obj.faces(">X").val(),
        "PointInPlane",
        param=0,
    )
    box_and_vertex.solve()
    solve_result_check(box_and_vertex._solve_result)

    x_pos = (
        box_and_vertex.children[0].loc.wrapped.Transformation().TranslationPart().X()
    )
    assert x_pos == pytest.approx(0.5)

    # add a second PointInPlane constraint
    box_and_vertex.constrain("vertex", "box@faces@>Y", "PointInPlane", param=0)
    box_and_vertex.solve()
    solve_result_check(box_and_vertex._solve_result)

    vertex_translation_part = (
        box_and_vertex.children[0].loc.wrapped.Transformation().TranslationPart()
    )
    # should still be on the >X face from the first constraint
    assert vertex_translation_part.X() == pytest.approx(0.5)
    # now should additionally be on the >Y face
    assert vertex_translation_part.Y() == pytest.approx(1)

    # add a third PointInPlane constraint
    box_and_vertex.constrain("vertex", "box@faces@>Z", "PointInPlane", param=0)
    box_and_vertex.solve()
    solve_result_check(box_and_vertex._solve_result)

    # should now be on the >X and >Y and >Z corner
    assert (
        box_and_vertex.children[0]
        .loc.wrapped.Transformation()
        .TranslationPart()
        .IsEqual(gp_XYZ(0.5, 1, 1.5), 1e-6)
    )


def test_PointInPlane_3_parts(box_and_vertex):

    cylinder_height = 2
    cylinder = cq.Workplane().circle(0.1).extrude(cylinder_height)
    box_and_vertex.add(cylinder, name="cylinder")
    box_and_vertex.constrain("box@faces@>Z", "cylinder@faces@<Z", "Plane")
    box_and_vertex.constrain("vertex", "cylinder@faces@>Z", "PointInPlane")
    box_and_vertex.constrain("vertex", "box@faces@>X", "PointInPlane")
    box_and_vertex.solve()
    solve_result_check(box_and_vertex._solve_result)
    vertex_translation_part = (
        box_and_vertex.children[0].loc.wrapped.Transformation().TranslationPart()
    )
    assert vertex_translation_part.Z() == pytest.approx(1.5 + cylinder_height)
    assert vertex_translation_part.X() == pytest.approx(0.5)


@pytest.mark.parametrize("param1", [-1, 0, 2])
@pytest.mark.parametrize("param0", [-2, 0, 0.01])
def test_PointInPlane_param(box_and_vertex, param0, param1):

    box_and_vertex.constrain("vertex", "box@faces@>Z", "PointInPlane", param=param0)
    box_and_vertex.constrain("vertex", "box@faces@>X", "PointInPlane", param=param1)
    box_and_vertex.solve()
    solve_result_check(box_and_vertex._solve_result)

    vertex_translation_part = (
        box_and_vertex.children[0].loc.wrapped.Transformation().TranslationPart()
    )
    assert vertex_translation_part.Z() - 1.5 == pytest.approx(param0, abs=1e-6)
    assert vertex_translation_part.X() - 0.5 == pytest.approx(param1, abs=1e-6)


def test_constraint_getPln():
    """
    Test that _getPln does the right thing with different arguments
    """
    ids = (0, 1)
    sublocs = (cq.Location(), cq.Location())

    def make_constraint(shape0):
        return cq.Constraint(ids, (shape0, shape0), sublocs, "PointInPlane", 0)

    def fail_this(shape0):
        with pytest.raises(ValueError):
            make_constraint(shape0)

    def resulting_pln(shape0):
        c0 = make_constraint(shape0)
        return c0._getPln(c0.args[0])

    def resulting_plane(shape0):
        p0 = resulting_pln(shape0)
        return cq.Plane(
            cq.Vector(p0.Location()),
            cq.Vector(p0.XAxis().Direction()),
            cq.Vector(p0.Axis().Direction()),
        )

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

    # all makePlane faces should succeed
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


def test_toCompound(simple_assy, nested_assy):

    c0 = simple_assy.toCompound()
    assert isinstance(c0, cq.Compound)
    assert len(c0.Solids()) == 4

    c1 = nested_assy.toCompound()
    assert isinstance(c1, cq.Compound)
    assert len(c1.Solids()) == 4

    # check nested assy location appears in compound
    # create four boxes, stack them on top of each other, check highest face is in final compound
    box0 = cq.Workplane().box(1, 1, 3, centered=(True, True, False))
    box1 = cq.Workplane().box(1, 1, 4)
    box2 = cq.Workplane().box(1, 1, 5)
    box3 = cq.Workplane().box(1, 1, 6)
    # top level assy
    assy0 = cq.Assembly(box0, name="box0")
    assy0.add(box1, name="box1")
    assy0.constrain("box0@faces@>Z", "box1@faces@<Z", "Plane")
    # subassy
    assy1 = cq.Assembly()
    assy1.add(box2, name="box2")
    assy1.add(box3, name="box3")
    assy1.constrain("box2@faces@>Z", "box3@faces@<Z", "Plane")
    assy1.solve()
    assy0.add(assy1, name="assy1")
    assy0.constrain("box1@faces@>Z", "assy1/box2@faces@<Z", "Plane")
    # before solving there should be no face with Center = (0, 0, 18)
    c2 = assy0.toCompound()
    assert not cq.Vector(0, 0, 18) in [x.Center() for x in c2.Faces()]
    # after solving there should be a face with Center = (0, 0, 18)
    assy0.solve()
    c3 = assy0.toCompound()
    assert cq.Vector(0, 0, 18) in [x.Center() for x in c3.Faces()]
    # also check with bounding box
    assert c3.BoundingBox().zlen == pytest.approx(18)


@pytest.mark.parametrize("origin", [(0, 0, 0), (10, -10, 10)])
@pytest.mark.parametrize("normal", [(0, 0, 1), (-1, -1, 1)])
def test_infinite_face_constraint_PointInPlane(origin, normal):
    """
    An OCCT infinite face has a center at (1e99, 1e99), but when a user uses it
    in a constraint, the center should be basePnt.
    """

    f0 = cq.Face.makePlane(length=None, width=None, basePnt=origin, dir=normal)

    c0 = cq.assembly.Constraint(
        ("point", "plane"),
        (cq.Vertex.makeVertex(10, 10, 10), f0),
        sublocs=(cq.Location(), cq.Location()),
        kind="PointInPlane",
    )
    p0 = c0._getPln(c0.args[1])  # a gp_Pln
    derived_origin = cq.Vector(p0.Location())
    assert derived_origin == cq.Vector(origin)


@pytest.mark.parametrize("kind", ["Plane", "PointInPlane", "Point"])
def test_infinite_face_constraint_Plane(kind):

    assy = cq.Assembly(cq.Workplane().sphere(1), name="part0")
    assy.add(cq.Workplane().sphere(1), name="part1")
    assy.constrain(
        "part0", cq.Face.makePlane(), "part1", cq.Face.makePlane(), kind,
    )
    assy.solve()
    assert solve_result_check(assy._solve_result)


def test_unary_constraints(simple_assy2):

    assy = simple_assy2

    assy.constrain("b1", "Fixed")
    assy.constrain("b2", "FixedPoint", (0, 0, -3))
    assy.constrain("b2@faces@>Z", "FixedAxis", (0, 1, 1))

    assy.solve()

    w = cq.Workplane().add(assy.toCompound())

    assert w.solids(">Z").val().Center().Length == pytest.approx(0)
    assert w.solids("<Z").val().Center().z == pytest.approx(-3)
    assert w.solids("<Z").edges(">Z").size() == 1


def test_fixed_rotation(simple_assy2):

    assy = simple_assy2

    assy.constrain("b1", "Fixed")
    assy.constrain("b2", "FixedPoint", (0, 0, -3))
    assy.constrain("b2@faces@>Z", "FixedRotation", (45, 0, 0))

    assy.solve()

    w = cq.Workplane().add(assy.toCompound())

    assert w.solids(">Z").val().Center().Length == pytest.approx(0)
    assert w.solids("<Z").val().Center().z == pytest.approx(-3)
    assert w.solids("<Z").edges(">Z").size() == 1


def test_constraint_validation(simple_assy2):

    with pytest.raises(ValueError):
        simple_assy2.constrain("b1", "Fixed?")

    with pytest.raises(ValueError):
        cq.assembly.Constraint((), (), (), "Fixed?")


def test_single_unary_constraint(simple_assy2):

    with pytest.raises(ValueError):
        simple_assy2.constrain("b1", "FixedRotation", (45, 0, 45))
        simple_assy2.solve()


def test_point_on_line(simple_assy2):

    assy = simple_assy2

    assy.constrain("b1", "Fixed")
    assy.constrain("b2@faces@>Z", "FixedAxis", (0, 2, 1))
    assy.constrain("b2@faces@>X", "FixedAxis", (1, 0, 0))
    assy.constrain("b2@faces@>X", "b1@edges@>>Z and >>Y", "PointOnLine")

    assy = assy.solve()

    w = cq.Workplane().add(assy.toCompound())

    assert w.solids("<Z").val().Center().Length == pytest.approx(0)
    assert w.solids(">Z").val().Center().z == pytest.approx(0.5)
    assert w.solids(">Z").val().Center().y == pytest.approx(0.5)
    assert w.solids(">Z").val().Center().x == pytest.approx(0.0)


def test_axis_constraint(simple_assy2):

    assy = simple_assy2

    assy.constrain("b1@faces@>Z", "b2@faces@>Z", "Axis", 0)
    assy.constrain("b1@faces@>X", "b2@faces@>X", "Axis", 45)

    assy.solve()

    q2 = assy.children[1].loc.wrapped.Transformation().GetRotation()

    assert degrees(q2.GetRotationAngle()) == pytest.approx(45)


def test_point_constraint(simple_assy2):

    assy = simple_assy2

    assy.constrain("b1", "b2", "Point", 1)

    assy.solve()

    t2 = assy.children[1].loc.wrapped.Transformation().TranslationPart()

    assert t2.Modulus() == pytest.approx(1)
