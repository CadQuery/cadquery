import pytest
import os

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
    assert nested_assy.objects["TOP/SECOND"].parent is nested_assy

    # bottom-up traversal
    kvs = list(nested_assy.traverse())

    assert kvs[0][0] == "TOP/SECOND/BOTTOM"
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

    nested_assy.constrain("TOP@faces@>Z", "TOP/SECOND/BOTTOM@faces@<Z", "Plane")
    nested_assy.constrain("TOP@faces@>X", "TOP/SECOND/BOTTOM@faces@<X", "Axis")

    assert len(nested_assy.constraints) == 2

    constraint = nested_assy.constraints[0]

    assert constraint.objects == ("TOP", "TOP/SECOND")
    assert constraint.sublocs[0].wrapped.Transformation().TranslationPart().IsEqual(gp_XYZ(), 1e-9)
    assert constraint.sublocs[1].wrapped.IsEqual(
        nested_assy.objects["TOP/SECOND/BOTTOM"].loc.wrapped
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
    nested_assy.constrain("TOP?top_face", "TOP/SECOND/BOTTOM", "Plane")

    assert len(nested_assy.constraints) == 1

    # test selection of a non-shape object
    with pytest.raises(ValueError):
        nested_assy.constrain("TOP/SECOND/BOTTOM ? pts", "TOP/dummy", "Plane")


def test_hierarchical_id():
    root1 = cq.Workplane().box(1, 1, 1).tag("root1")
    root2 = cq.Workplane().box(1, 1, 1).tag("root2")
    root3 = cq.Workplane().box(1, 1, 1).tag("root3")
    obj1 = cq.Workplane().box(1, 1, 1).tag("obj1")
    obj2 = cq.Workplane().box(1, 1, 1).tag("obj2")
    obj3 = cq.Workplane().box(1, 1, 1).tag("obj3")
    obj4 = cq.Workplane().box(1, 1, 1).tag("obj4")
    obj5 = cq.Workplane().box(1, 1, 1).tag("obj5")

    assy1 = cq.Assembly(root1, name="root1").add(obj1, name="obj1").add(obj2, name="obj2")
    expected1 = {  # assemly_id: object tag
        "root1": "root1",
        "root1/obj1": "obj1",
        "root1/obj2": "obj2",
    }

    assy2 = (
        cq.Assembly(root2, name="root2")
        .add(obj1, name="obj1")
        .add(obj3, name="obj3")
        .add(assy1)
        .add(assy1, name="assy1_2")
        .add(obj4, name="obj4")
    )
    expected2 = {  # assemly_id: object tag
        "root2": "root2",
        "root2/obj1": "obj1",
        "root2/obj3": "obj3",
        "root2/root1": "root1",
        "root2/root1/obj1": "obj1",
        "root2/root1/obj2": "obj2",
        "root2/assy1_2": "root1",
        "root2/assy1_2/obj1": "obj1",
        "root2/assy1_2/obj2": "obj2",
        "root2/obj4": "obj4",
    }

    assy3 = (
        cq.Assembly(root3, name="root3")
        .add(assy1, name="assy1_1")
        .add(assy2)
        .add(assy2, name="assy2_2")
        .add(assy1)
        .add(obj5, name="obj5")
    )

    expected3 = {  # assemly_id: object tag
        "root3": "root3",
        "root3/assy1_1": "root1",
        "root3/assy1_1/obj1": "obj1",
        "root3/assy1_1/obj2": "obj2",
        "root3/root2": "root2",
        "root3/root2/obj1": "obj1",
        "root3/root2/obj3": "obj3",
        "root3/root2/root1": "root1",
        "root3/root2/root1/obj1": "obj1",
        "root3/root2/root1/obj2": "obj2",
        "root3/root2/assy1_2": "root1",
        "root3/root2/assy1_2/obj1": "obj1",
        "root3/root2/assy1_2/obj2": "obj2",
        "root3/root2/obj4": "obj4",
        "root3/assy2_2": "root2",
        "root3/assy2_2/obj1": "obj1",
        "root3/assy2_2/obj3": "obj3",
        "root3/assy2_2/root1": "root1",
        "root3/assy2_2/root1/obj1": "obj1",
        "root3/assy2_2/root1/obj2": "obj2",
        "root3/assy2_2/assy1_2": "root1",
        "root3/assy2_2/assy1_2/obj1": "obj1",
        "root3/assy2_2/assy1_2/obj2": "obj2",
        "root3/assy2_2/obj4": "obj4",
        "root3/root1": "root1",
        "root3/root1/obj1": "obj1",
        "root3/root1/obj2": "obj2",
        "root3/obj5": "obj5",
    }

    for assy, expected in ((assy1, expected1), (assy2, expected2), (assy3, expected3)):
        assert len(expected) == len(assy.objects)
        for k, v in assy.objects.items():
            assert expected[k] == v.obj._tag
        # check traversed assemblies are the same as in object dict
        assert all([v is assy.objects[k] for k, v in assy.traverse()])
