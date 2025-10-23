import pytest
import os
from itertools import product
from math import degrees
import copy
from path import Path
from pathlib import PurePath
import re
from pytest import approx

import cadquery as cq
from cadquery.occ_impl.exporters.assembly import (
    exportAssembly,
    exportStepMeta,
    exportCAF,
    exportVTKJS,
    exportVRML,
)
from cadquery.occ_impl.assembly import toJSON, toCAF, toFusedCAF
from cadquery.occ_impl.shapes import Face, box, cone, plane

from OCP.gp import gp_XYZ
from OCP.TDocStd import TDocStd_Document
from OCP.TDataStd import TDataStd_Name
from OCP.TCollection import TCollection_ExtendedString
from OCP.XCAFPrs import (
    XCAFPrs_DocumentExplorer,
    XCAFPrs_DocumentExplorerFlags_None,
    XCAFPrs_DocumentExplorerFlags_OnlyLeafNodes,
    XCAFPrs_Style,
)
from OCP.XCAFDoc import XCAFDoc_DocumentTool, XCAFDoc_ColorType
from OCP.XCAFApp import XCAFApp_Application
from OCP.STEPCAFControl import STEPCAFControl_Reader
from OCP.IFSelect import IFSelect_RetDone
from OCP.TDF import TDF_ChildIterator
from OCP.Quantity import Quantity_ColorRGBA, Quantity_TOC_sRGB, Quantity_NameOfColor
from OCP.TopAbs import TopAbs_ShapeEnum


@pytest.fixture(scope="function")
def tmpdir(tmp_path_factory):
    return Path(tmp_path_factory.mktemp("assembly"))


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

    assy = cq.Assembly(name="top")
    assy.add(b1, color=cq.Color("green"), name="b")

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

    sub_assy2 = cq.Assembly(name="sub2", metadata={"mykey": "sub2-data"})
    sub_assy2.add(
        b1, name="sub2-0", loc=cq.Location((1, 0, 0)), metadata={"mykey": "sub2-0-data"}
    )
    sub_assy2.add(
        b1, name="sub2-1", loc=cq.Location((2, 0, 0)), metadata={"mykey": "sub2-1-data"}
    )
    assy.add(
        sub_assy2, metadata={"mykey": "sub2-data-add"}
    )  # override metadata mykey:sub2-data

    return assy


@pytest.fixture
def simple_assy2():

    b1 = cq.Workplane().box(1, 1, 1)
    b2 = cq.Workplane().box(2, 1, 1)

    assy = cq.Assembly()
    assy.add(b1, name="b1")
    assy.add(b2, loc=cq.Location(cq.Vector(0, 0, 4)), name="b2")

    return assy


@pytest.fixture
def single_compound0_assy():

    b0 = cq.Workplane().rect(1, 2).extrude(3, both=True)

    assy = cq.Assembly(name="single_compound0")
    assy.add(b0, color=cq.Color(1, 0, 0, 0.8))

    return assy


@pytest.fixture
def single_compound1_assy():

    b0 = cq.Workplane().circle(1).extrude(2)
    b1 = cq.Workplane().circle(1).extrude(-2)

    assy = cq.Assembly(name="single_compound1")
    assy.add(
        cq.Compound.makeCompound([b0.val(), b1.val()]), color=cq.Color(1, 0, 0, 0.8)
    )

    return assy


@pytest.fixture
def boxes0_assy():

    b0 = cq.Workplane().box(1, 1, 1)

    assy = cq.Assembly()
    assy.add(b0, name="box0", color=cq.Color("red"))
    assy.add(b0, name="box1", color=cq.Color("red"), loc=cq.Location((1, 0, 0)))

    return assy


@pytest.fixture
def boxes1_assy():

    b0 = cq.Workplane().box(1, 1, 1)

    assy = cq.Assembly(name="boxes", color=cq.Color("red"))
    assy.add(b0, name="box0")
    assy.add(b0, name="box1", loc=cq.Location((1, 0, 0)))

    return assy


@pytest.fixture
def boxes2_assy():

    b0 = cq.Workplane().box(1, 1, 1)

    assy = cq.Assembly()
    assy.add(b0, name="box0", color=cq.Color("red"))
    assy.add(b0, name="box1", color=cq.Color("green"), loc=cq.Location((1, 0, 0)))

    return assy


@pytest.fixture
def boxes3_assy():

    b0 = cq.Workplane().box(1, 1, 1)

    assy = cq.Assembly()
    assy.add(b0, name="box0", color=cq.Color("red"))
    assy.add(b0, name="box1", loc=cq.Location((1, 0, 0)))

    return assy


@pytest.fixture
def boxes4_assy():

    b0 = cq.Workplane().box(1, 1, 1)

    assy = cq.Assembly()
    assy.add(b0, name="box_0", color=cq.Color("red"))
    assy.add(b0, name="box_1", color=cq.Color("green"), loc=cq.Location((1, 0, 0)))

    return assy


@pytest.fixture
def boxes5_assy():

    b0 = cq.Workplane().box(1, 1, 1)

    assy = cq.Assembly()
    assy.add(b0, name="box:a", color=cq.Color("red"))
    assy.add(b0, name="box:b", color=cq.Color("green"), loc=cq.Location((1, 0, 0)))

    return assy


@pytest.fixture
def boxes6_assy():

    b0 = cq.Workplane().box(1, 1, 1)

    assy = cq.Assembly()
    assy.add(b0, name="box__0", color=cq.Color("red"))
    assy.add(b0, name="box__1", color=cq.Color("green"), loc=cq.Location((1, 0, 0)))

    return assy


@pytest.fixture
def boxes7_assy():

    b0 = cq.Workplane().box(1, 1, 1)

    assy = cq.Assembly()
    assy.add(b0, name="box_0", color=cq.Color("red"))
    assy.add(b0, name="box", color=cq.Color("green"), loc=cq.Location((1, 0, 0)))
    assy.add(
        b0,
        name="another box",
        color=cq.Color(0.23, 0.26, 0.26, 0.6),
        loc=cq.Location((2, 0, 0)),
    )

    return assy


@pytest.fixture
def boxes8_assy():

    b0 = box(1, 1, 1)

    assy = cq.Assembly(loc=cq.Location(0, 10, 0))
    assy.add(b0, name="box0", color=cq.Color("red"))
    assy.add(b0, name="box1", color=cq.Color("green"), loc=cq.Location((1, 0, 0)))

    return assy


@pytest.fixture
def boxes9_assy():

    b0 = box(1, 1, 1)

    assy = cq.Assembly(
        b0, name="box0", loc=cq.Location(0, 10, 0), color=cq.Color("red")
    )
    assy.add(b0, name="box1", color=cq.Color("green"), loc=cq.Location((1, 0, 0)))

    return assy


@pytest.fixture
def spheres0_assy():

    b0 = cq.Workplane().sphere(1)

    assy = cq.Assembly(name="spheres0")
    assy.add(b0, name="a", color=cq.Color(1, 0, 0, 0.2))
    assy.add(b0, name="b", color=cq.Color(0, 1, 0, 0.2), loc=cq.Location((2.1, 0, 0)))

    return assy


@pytest.fixture
def chassis0_assy():

    r_wheel = 25
    w_wheel = 10
    l_axle = 80
    l_chassis = 100

    wheel = cq.Workplane("YZ").circle(r_wheel).extrude(w_wheel, both=True)

    axle = cq.Workplane("YZ").circle(r_wheel / 10).extrude(l_axle / 2, both=True)

    wheel_axle = cq.Assembly(name="wheel-axle")

    wheel_axle.add(
        wheel,
        name="wheel:left",
        color=cq.Color("red"),
        loc=cq.Location((-l_axle / 2 - w_wheel, 0, 0)),
    )

    wheel_axle.add(
        wheel,
        name="wheel:right",
        color=cq.Color("red"),
        loc=cq.Location((l_axle / 2 + w_wheel, 0, 0)),
    )

    wheel_axle.add(axle, name="axle", color=cq.Color("green"))

    chassis = cq.Assembly(name="chassis")
    chassis.add(
        wheel_axle, name="wheel-axle-front", loc=cq.Location((0, l_chassis / 2, 0))
    )
    chassis.add(
        wheel_axle, name="wheel-axle-rear", loc=cq.Location((0, -l_chassis / 2, 0))
    )

    return chassis


@pytest.fixture
def subshape_assy():
    """
    Builds an assembly with the needed subshapes to test the export and import of STEP files.
    """

    # Create a simple assembly
    assy = cq.Assembly(name="top_level")
    cube_1 = cq.Workplane().box(10.0, 10.0, 10.0)
    assy.add(cube_1, name="cube_1", color=cq.Color("green"))

    # Add subshape name, color and layer
    assy["cube_1"].addSubshape(
        cube_1.faces(">Z").val(),
        name="cube_1_top_face",
        color=cq.Color("red"),
        layer="cube_1_top_face_layer",
    )

    # Add a cylinder to the assembly
    cyl_1 = cq.Workplane().cylinder(10.0, 2.5)
    assy.add(
        cyl_1, name="cyl_1", color=cq.Color("blue"), loc=cq.Location((0.0, 0.0, -10.0))
    )

    # Add a subshape face for the cylinder
    assy["cyl_1"].addSubshape(
        cyl_1.faces("<Z").val(),
        name="cylinder_bottom_face",
        color=cq.Color("green"),
        layer="cylinder_bottom_face_layer",
    )

    # Add a subshape wire for the cylinder
    assy["cyl_1"].addSubshape(
        cyl_1.wires("<Z").val(),
        name="cylinder_bottom_wire",
        color=cq.Color("blue"),
        layer="cylinder_bottom_wire_layer",
    )

    return assy


@pytest.fixture
def multi_subshape_assy():

    # Create a basic assembly
    cube_1 = cq.Workplane().box(10, 10, 10)
    assy = cq.Assembly(name="top_level")
    assy.add(cube_1, name="cube_1", color=cq.Color("green"))
    cube_2 = cq.Workplane().box(5, 5, 5)
    assy.add(cube_2, name="cube_2", color=cq.Color("blue"), loc=cq.Location(10, 10, 10))

    # Add subshape name, color and layer
    assy.addSubshape(
        cube_1.faces(">Z").val(),
        name="cube_1_top_face",
        color=cq.Color("red"),
        layer="cube_1_top_face",
    )
    assy.addSubshape(
        cube_2.faces(">X").val(),
        name="cube_2_right_face",
        color=cq.Color("red"),
        layer="cube_2_right_face",
    )

    return assy


def read_step(stepfile) -> TDocStd_Document:
    """Read STEP file, return XCAF document"""

    app = XCAFApp_Application.GetApplication_s()
    doc = TDocStd_Document(TCollection_ExtendedString("XmlOcaf"))
    app.InitDocument(doc)
    reader = STEPCAFControl_Reader()
    status = reader.ReadFile(str(stepfile))
    assert status == IFSelect_RetDone
    reader.Transfer(doc)

    return doc


def get_doc_nodes(doc, leaf=False):
    """Read document and return list of nodes (dicts)"""

    if leaf:
        flags = XCAFPrs_DocumentExplorerFlags_OnlyLeafNodes
    else:
        flags = XCAFPrs_DocumentExplorerFlags_None

    expl = XCAFPrs_DocumentExplorer(doc, flags, XCAFPrs_Style())
    tool = XCAFDoc_DocumentTool.ShapeTool_s(doc.Main())

    nodes = []
    while expl.More():
        node = expl.Current()
        ctool = expl.ColorTool()
        style = node.Style
        label = node.RefLabel
        label2 = node.Label

        name_att = TDataStd_Name()
        label.FindAttribute(TDataStd_Name.GetID_s(), name_att)

        if label2.IsAttribute(TDataStd_Name.GetID_s()):
            name_att = TDataStd_Name()
            label2.FindAttribute(TDataStd_Name.GetID_s(), name_att)

        color = style.GetColorSurfRGBA()
        shape = expl.FindShapeFromPathId_s(doc, node.Id)
        color_shape = Quantity_ColorRGBA()
        ctool.GetColor(shape, XCAFDoc_ColorType.XCAFDoc_ColorSurf, color_shape)

        # on STEP import colors applied to subshapes; and fused export mode
        color_subshapes = None
        color_subshapes_set = set()
        faces = []
        if not node.IsAssembly:
            it = TDF_ChildIterator(label)
            while it.More():
                child = it.Value()
                child_shape = tool.GetShape_s(child)
                if child_shape.ShapeType() == TopAbs_ShapeEnum.TopAbs_FACE:
                    face = Face(child_shape)

                    color_subshape = Quantity_ColorRGBA()
                    face_color = None

                    if ctool.GetColor_s(
                        child, XCAFDoc_ColorType.XCAFDoc_ColorGen, color_subshape
                    ) or ctool.GetColor_s(
                        child, XCAFDoc_ColorType.XCAFDoc_ColorSurf, color_subshape
                    ):
                        face_color = (
                            *color_subshape.GetRGB().Values(Quantity_TOC_sRGB),
                            color_subshape.Alpha(),
                        )

                        faces.append(
                            {"center": face.Center().toTuple(), "color": face_color}
                        )

                else:
                    color_subshape = Quantity_ColorRGBA()
                    if ctool.GetColor_s(
                        child, XCAFDoc_ColorType.XCAFDoc_ColorSurf, color_subshape
                    ):
                        color_subshapes_set.add(
                            (
                                *color_subshape.GetRGB().Values(Quantity_TOC_sRGB),
                                color_subshape.Alpha(),
                            )
                        )
                it.Next()
            if color_subshapes_set:
                color_subshapes = color_subshapes_set.pop()

        nodes.append(
            {
                "path": PurePath(node.Id.ToCString()),
                "name": TCollection_ExtendedString(name_att.Get()).ToExtString(),
                "color": (*color.GetRGB().Values(Quantity_TOC_sRGB), color.Alpha()),
                "color_shape": (
                    *color_shape.GetRGB().Values(Quantity_TOC_sRGB),
                    color_shape.Alpha(),
                ),
                "color_subshapes": color_subshapes,
                "faces": faces,
            }
        )

        expl.Next()

    return nodes


def find_node(node_list, name_path):
    """Return node(s) matching node name path

    :param node_list: list of nodes (output of get_doc_nodes)
    :param name_path: list of node names (corresponding to path)
    """

    def purepath_is_relative_to(p0, p1):
        """Alternative to PurePath.is_relative_to for Python 3.8
        PurePath.is_relative_to is new in Python 3.9
        """
        try:
            if p0.relative_to(p1):
                is_relative_to = True
        except ValueError:
            is_relative_to = False

        return is_relative_to

    def get_nodes(node_list, name, parents):
        if parents:
            nodes = []
            for parent in parents:
                nodes.extend(
                    [
                        p
                        for p in node_list
                        # if p["path"].is_relative_to(parent["path"])
                        if purepath_is_relative_to(p["path"], parent["path"])
                        and len(p["path"].relative_to(parent["path"]).parents) == 1
                        and re.fullmatch(name, p["name"])
                        and p not in nodes
                    ]
                )
        else:
            nodes = [p for p in node_list if re.fullmatch(name, p["name"])]

        return nodes

    parents = None
    for name in name_path:
        nodes = get_nodes(node_list, name, parents)
        parents = nodes

    return nodes


def test_metadata(metadata_assy):
    """Verify the metadata is present in both the base and sub assemblies"""
    assert metadata_assy.metadata["b1"] == "base-data"
    # The metadata should be able to be modified
    metadata_assy.metadata["b2"] = 0
    assert len(metadata_assy.metadata) == 2
    # Test that metadata was copied by _copy() during the processing of adding the subassembly
    assert metadata_assy.children[0].metadata["b2"] == "sub-data"
    assert metadata_assy.children[1].metadata["mykey"] == "sub2-data-add"
    assert metadata_assy.children[1].children[0].metadata["mykey"] == "sub2-0-data"
    assert metadata_assy.children[1].children[1].metadata["mykey"] == "sub2-1-data"


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

    # test for srgb
    c4 = cq.Color(0.5, 0.2, 0, 0.5, True)
    assert c4.wrapped.GetRGB().Red() != 0.5
    assert c4.wrapped.GetRGB().Green() != 0.2
    assert c4.wrapped.Alpha() == 0.5

    # test for linear rgb
    c4 = cq.Color(0.5, 0.2, 0, 0.5, False)
    assert c4.wrapped.GetRGB().Red() == pytest.approx(0.5)
    assert c4.wrapped.GetRGB().Green() == pytest.approx(0.2)
    assert c4.wrapped.Alpha() == 0.5

    with pytest.raises(ValueError):
        cq.Color("?????")

    with pytest.raises(ValueError):
        cq.Color(1, 2, 3, 4, 5, 6)


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


@pytest.mark.parametrize(
    "assy_fixture, root_name", [("simple_assy", None), ("nested_assy", "TOP")],
)
def test_assy_root_name(assy_fixture, root_name, request):
    assy = request.getfixturevalue(assy_fixture)
    _, doc = toCAF(assy, True)
    root = get_doc_nodes(doc, False)[0]
    if root_name:
        assert root["name"] == root_name
    else:
        # When a name is not user-specifed, the name is assigned a UUID
        m = re.findall(r"[0-9a-f]+", root["name"])
        assert list(map(len, m)) == [8, 4, 4, 4, 12]


def test_step_export(nested_assy, tmp_path_factory):
    # Use a temporary directory
    tmpdir = tmp_path_factory.mktemp("out")
    nested_path = os.path.join(tmpdir, "nested.step")
    nested_options_path = os.path.join(tmpdir, "nested_options.step")

    exportAssembly(nested_assy, nested_path)
    exportAssembly(
        nested_assy, nested_options_path, write_pcurves=False, precision_mode=0
    )

    w = cq.importers.importStep(nested_path)
    o = cq.importers.importStep(nested_options_path)
    assert w.solids().size() == 4
    assert o.solids().size() == 4

    # check that locations were applied correctly
    c = cq.Compound.makeCompound(w.solids().vals()).Center()
    assert pytest.approx(c.toTuple()) == (0, 4, 0)
    c2 = cq.Compound.makeCompound(o.solids().vals()).Center()
    assert pytest.approx(c2.toTuple()) == (0, 4, 0)


def test_meta_step_export(tmp_path_factory):
    """
    Tests that an assembly can be exported to a STEP file with faces tagged with names and colors,
    and layers added.
    """

    # Use a temporary directory
    tmpdir = tmp_path_factory.mktemp("out")
    meta_path = os.path.join(tmpdir, "meta.step")

    # Most nested level of the assembly
    subsubassy = cq.Assembly(name="third-level")
    cone_1 = cq.Workplane(cone(5.0, 10.0, 5.0))
    cone_2 = cq.Workplane(cone(2.5, 5.0, 2.5))
    subsubassy.add(
        cone_1,
        name="cone_1",
        color=cq.Color(1.0, 1.0, 1.0),
        loc=cq.Location(-15.0, 10.0, 0.0),
    )
    subsubassy.add(
        cone_2,
        name="cone_2",
        color=cq.Color(0.0, 0.0, 0.0),
        loc=cq.Location((15.0, 10.0, -5.0)),
    )

    # First layer of nested assembly
    subassy = cq.Assembly(name="second-level")
    cylinder_1 = cq.Workplane().cylinder(radius=5.0, height=10.0)
    cylinder_2 = cq.Workplane().cylinder(radius=2.5, height=5.0)
    subassy.add(
        cylinder_1,
        name="cylinder_1",
        color=cq.Color(1.0, 1.0, 0.0),
        loc=cq.Location(-15.0, 0.0, 0.0),
    )
    subassy.add(
        cylinder_2,
        name="cylinder_2",
        color=cq.Color(0.0, 1.0, 1.0),
        loc=cq.Location((15.0, -10.0, -5.0)),
    )
    subassy.add(subsubassy)

    # Top level of the assembly
    assy = cq.Assembly(name="top-level")
    cube_1 = cq.Workplane().box(10.0, 10.0, 10.0)
    assy.add(cube_1, name="cube_1", color=cq.Color(0.5, 0.0, 0.5))
    cube_2 = cq.Workplane().box(5.0, 5.0, 5.0)
    assy.add(
        cube_2,
        name="cube_2",
        color=cq.Color(0.0, 0.5, 0.0),
        loc=cq.Location(10.0, 10.0, 10.0),
    )
    assy.add(subassy)

    # Tag faces to test from all levels of the assembly
    assy.addSubshape(cube_1.faces(">Z").val(), name="cube_1_top_face")
    assy.addSubshape(cube_1.faces(">Z").val(), color=cq.Color(1.0, 0.0, 0.0))
    assy.addSubshape(cube_1.faces(">Z").val(), layer="cube_1_top_face")

    assy.cube_2.addSubshape(cube_2.faces("<Z").val(), name="cube_2_bottom_face")
    assy.cube_2.addSubshape(cube_2.faces("<Z").val(), color=cq.Color(1.0, 0.0, 0.0))
    assy.cube_2.addSubshape(cube_2.faces("<Z").val(), layer="cube_2_bottom_face")

    with pytest.raises(ValueError):
        assy.addSubshape(cylinder_1.faces(">Z").val(), name="cylinder_1_top_face")
        assy.addSubshape(cylinder_1.faces(">Z").val(), color=cq.Color(1.0, 0.0, 0.0))
        assy.addSubshape(cylinder_1.faces(">Z").val(), layer="cylinder_1_top_face")
        assy.addSubshape(cylinder_2.faces("<Z").val(), name="cylinder_2_bottom_face")
        assy.addSubshape(cylinder_2.faces("<Z").val(), color=cq.Color(1.0, 0.0, 0.0))
        assy.addSubshape(cylinder_2.faces("<Z").val(), layer="cylinder_2_bottom_face")
        assy.addSubshape(cone_1.faces(">Z").val(), name="cone_1_top_face")
        assy.addSubshape(cone_1.faces(">Z").val(), color=cq.Color(1.0, 0.0, 0.0))
        assy.addSubshape(cone_1.faces(">Z").val(), layer="cone_1_top_face")
        assy.addSubshape(cone_2.faces("<Z").val(), name="cone_2_bottom_face")
        assy.addSubshape(cone_2.faces("<Z").val(), color=cq.Color(1.0, 0.0, 0.0))
        assy.addSubshape(cone_2.faces("<Z").val(), layer="cone_2_bottom_face")

    # Write once with pcurves turned on
    success = exportStepMeta(assy, meta_path)
    assert success

    # Write again with pcurves turned off
    success = exportStepMeta(assy, meta_path, write_pcurves=False)
    assert success

    # Make sure the step file exists
    assert os.path.exists(meta_path)

    # Read the contents as a step file as a string so we can check the outputs
    with open(meta_path, "r") as f:
        step_contents = f.read()

        # Make sure that the face name strings were applied in ADVACED_FACE entries
        assert "ADVANCED_FACE('cube_1_top_face'" in step_contents
        assert "ADVANCED_FACE('cube_2_bottom_face'" in step_contents

        # Make reasonably sure that the colors were applied to the faces
        assert "DRAUGHTING_PRE_DEFINED_COLOUR('black')" in step_contents
        assert "DRAUGHTING_PRE_DEFINED_COLOUR('white')" in step_contents
        assert "DRAUGHTING_PRE_DEFINED_COLOUR('cyan')" in step_contents
        assert "DRAUGHTING_PRE_DEFINED_COLOUR('yellow')" in step_contents

        # Make sure that the layers were created
        assert (
            "PRESENTATION_LAYER_ASSIGNMENT('cube_1_top_face','visible'" in step_contents
        )
        assert (
            "PRESENTATION_LAYER_ASSIGNMENT('cube_2_bottom_face','visible'"
            in step_contents
        )


def test_meta_step_export_edge_cases(tmp_path_factory):
    """
    Test all the edge cases of the STEP export function.
    """

    # Use a temporary directory
    tmpdir = tmp_path_factory.mktemp("out")
    meta_path = os.path.join(tmpdir, "meta_edges_cases.step")

    # Create an assembly where the child is empty
    assy = cq.Assembly(name="top-level")
    subassy = cq.Assembly(name="second-level")
    assy.add(subassy)

    # Write an assembly with no children
    success = exportStepMeta(assy, meta_path)
    assert success

    # Test an object with no color set
    cube = cq.Workplane().box(10.0, 10.0, 10.0)
    assy.add(cube, name="cube")
    success = exportStepMeta(assy, meta_path)
    assert success

    # Tag a face that does not match the object
    with pytest.raises(ValueError):
        assy.addSubshape(plane(1, 1), name="cube_top_face")

    # Tag the name but nothing else
    assy.addSubshape(cube.faces(">Z").val(), name="cube_top_face")
    success = exportStepMeta(assy, meta_path)
    assert success

    # Reset the assembly
    assy.remove("cube")
    cube = cq.Workplane().box(9.9, 9.9, 9.9)
    assy.add(cube, name="cube")

    # Tag the color but nothing else
    assy.addSubshape(cube.faces(">Z").val(), color=cq.Color(1.0, 0.0, 0.0))
    success = exportStepMeta(assy, meta_path)
    assert success

    # Reset the assembly
    assy.remove("cube")
    cube = cq.Workplane().box(9.8, 9.8, 9.8)
    assy.add(cube, name="cube")

    # Tag the layer but nothing else
    assy.addSubshape(cube.faces(">Z").val(), layer="cube_top_face")
    success = exportStepMeta(assy, meta_path)
    assert success


def test_assembly_step_import(tmp_path_factory, subshape_assy):
    """
    Test if the STEP import works correctly for an assembly with subshape data attached.
    """

    # Use a temporary directory
    tmpdir = tmp_path_factory.mktemp("out")
    assy_step_path = os.path.join(tmpdir, "assembly_with_subshapes.step")

    subshape_assy.export(assy_step_path)

    # Import the STEP file back in
    imported_assy = cq.Assembly.importStep(assy_step_path)

    # Check that the assembly was imported successfully
    assert imported_assy is not None

    # Check for appropriate part name
    assert imported_assy.children[0].name == "cube_1"
    # Check for approximate color match
    assert pytest.approx(imported_assy.children[0].color.toTuple(), rel=0.01) == (
        0.0,
        1.0,
        0.0,
        1.0,
    )
    # Check for appropriate part name
    assert imported_assy.children[1].name == "cyl_1"
    # Check for approximate color match
    assert pytest.approx(imported_assy.children[1].color.toTuple(), rel=0.01) == (
        0.0,
        0.0,
        1.0,
        1.0,
    )

    # Make sure the shape locations were applied correctly
    assert imported_assy.children[1].loc.toTuple()[0] == (0.0, 0.0, -10.0)

    # Check the top-level assembly name
    assert imported_assy.name == "top_level"

    # Test a STEP file that does not contain an assembly
    wp_step_path = os.path.join(tmpdir, "plain_workplane.step")
    res = cq.Workplane().box(10, 10, 10)
    res.export(wp_step_path)

    # Import the STEP file back in
    with pytest.raises(ValueError):
        imported_assy = cq.Assembly.importStep(wp_step_path)


@pytest.mark.parametrize("kind", ["step", "xml", "xbf"])
def test_assembly_subshape_import(tmp_path_factory, subshape_assy, kind):
    """
    Test if a STEP/XBF/XML file containing subshape information can be imported correctly.
    """

    tmpdir = tmp_path_factory.mktemp("out")
    assy_step_path = os.path.join(tmpdir, f"subshape_assy.{kind}")

    # Export the assembly
    subshape_assy.export(assy_step_path)

    # Import the file back in
    imported_assy = cq.Assembly.load(assy_step_path)
    assert imported_assy.name == "top_level"

    # Check the advanced face name
    assert len(imported_assy.children[0]._subshape_names) == 1
    assert (
        list(imported_assy.children[0]._subshape_names.values())[0] == "cube_1_top_face"
    )

    # Check the color
    color = list(imported_assy.children[0]._subshape_colors.values())[0]
    assert Quantity_NameOfColor.Quantity_NOC_RED == color.wrapped.GetRGB().Name()

    # Check the layer info
    layer_name = list(imported_assy["cube_1"]._subshape_layers.values())[0]
    assert layer_name == "cube_1_top_face_layer"

    assert (
        "cylinder_bottom_face_layer" in imported_assy["cyl_1"]._subshape_layers.values()
    )
    assert (
        "cylinder_bottom_wire_layer" in imported_assy["cyl_1"]._subshape_layers.values()
    )


@pytest.mark.parametrize("kind", ["step", "xml", "xbf"])
def test_assembly_multi_subshape_import(tmp_path_factory, multi_subshape_assy, kind):
    """
    Test if a file containing subshape information can be imported correctly.
    """

    tmpdir = tmp_path_factory.mktemp("out")
    assy_step_path = os.path.join(tmpdir, f"multi_subshape_assy.{kind}")

    # Export the assembly
    multi_subshape_assy.export(assy_step_path)

    # Import the file back in
    imported_assy = cq.Assembly.load(assy_step_path)

    # Check that the top-level assembly name is correct
    assert imported_assy.name == "top_level"

    # Check the advanced face name for the first cube
    assert len(imported_assy.children[0]._subshape_names) == 1
    assert (
        list(imported_assy.children[0]._subshape_names.values())[0] == "cube_1_top_face"
    )

    # Check the color for the first cube
    color = list(imported_assy.children[0]._subshape_colors.values())[0]
    assert Quantity_NameOfColor.Quantity_NOC_RED == color.wrapped.GetRGB().Name()

    # Check the layer info for the first cube
    layer_name = list(imported_assy.children[0]._subshape_layers.values())[0]
    assert layer_name == "cube_1_top_face"

    # Check the advanced face name for the second cube
    assert len(imported_assy.children[1]._subshape_names) == 1
    assert (
        list(imported_assy.children[1]._subshape_names.values())[0]
        == "cube_2_right_face"
    )

    # Check the color
    color = list(imported_assy.children[1]._subshape_colors.values())[0]
    assert Quantity_NameOfColor.Quantity_NOC_RED == color.wrapped.GetRGB().Name()

    # Check the layer info
    layer_name = list(imported_assy.children[1]._subshape_layers.values())[0]
    assert layer_name == "cube_2_right_face"


def test_bad_step_file_import(tmp_path_factory):
    """
    Test if a bad STEP file raises an error when importing.
    """

    tmpdir = tmp_path_factory.mktemp("out")
    bad_step_path = os.path.join(tmpdir, "bad_step.step")

    # Check that an error is raised when trying to import a non-existent STEP file
    with pytest.raises(ValueError):
        # Export the assembly
        cq.Assembly.importStep(bad_step_path)


def test_plain_assembly_import(tmp_path_factory):
    """
    Test to make sure that importing plain assemblies has not been broken.
    """

    tmpdir = tmp_path_factory.mktemp("out")
    plain_step_path = os.path.join(tmpdir, "plain_assembly_step.step")

    # Simple cubes
    cube_1 = cq.Workplane().box(10, 10, 10)
    cube_2 = cq.Workplane().box(5, 5, 5)
    cube_3 = cq.Workplane().box(5, 5, 5)
    cube_4 = cq.Workplane().box(5, 5, 5)

    assy = cq.Assembly(name="top_level", loc=cq.Location(10, 10, 10))
    assy.add(cube_1, color=cq.Color("green"))
    assy.add(cube_2, loc=cq.Location((10, 10, 10)), color=cq.Color("red"))
    assy.add(cube_3, loc=cq.Location((-10, -10, -10)), color=cq.Color("red"))
    assy.add(cube_4, loc=cq.Location((10, -10, -10)), color=cq.Color("red"))

    # Export the assembly, but do not use the meta STEP export method
    assy.export(plain_step_path)

    # Import the STEP file back in
    imported_assy = cq.Assembly.importStep(plain_step_path)
    assert imported_assy.name == "top_level"

    # Check the locations
    assert imported_assy.children[0].loc.toTuple()[0] == (0.0, 0.0, 0.0,)
    assert imported_assy.children[1].loc.toTuple()[0] == (10.0, 10.0, 10.0,)
    assert imported_assy.children[2].loc.toTuple()[0] == (-10.0, -10.0, -10.0,)
    assert imported_assy.children[3].loc.toTuple()[0] == (10.0, -10.0, -10.0,)

    # Make sure the location of the top-level assembly was preserved
    assert imported_assy.loc.toTuple() == cq.Location((10, 10, 10)).toTuple()

    # Check the colors
    assert pytest.approx(imported_assy.children[0].color.toTuple(), rel=0.01) == (
        0.0,
        1.0,
        0.0,
        1.0,
    )  # green
    assert pytest.approx(imported_assy.children[1].color.toTuple(), rel=0.01) == (
        1.0,
        0.0,
        0.0,
        1.0,
    )  # red
    assert pytest.approx(imported_assy.children[2].color.toTuple(), rel=0.01) == (
        1.0,
        0.0,
        0.0,
        1.0,
    )  # red
    assert pytest.approx(imported_assy.children[3].color.toTuple(), rel=0.01) == (
        1.0,
        0.0,
        0.0,
        1.0,
    )  # red


def test_copied_assembly_import(tmp_path_factory):
    """
    Tests to make sure that copied children in assemblies work correctly.
    """
    from cadquery import Assembly, Location, Color
    from cadquery.func import box, rect

    # Create the temporary directory
    tmpdir = tmp_path_factory.mktemp("out")

    # prepare the model
    def make_model(name: str, COPY: bool):
        name = os.path.join(tmpdir, name)

        b = box(1, 1, 1)

        assy = Assembly(name="test_assy")
        assy.add(box(1, 2, 5), color=Color("green"))

        for i, v in enumerate(rect(10, 10).vertices()):
            assy.add(
                b.copy() if COPY else b,
                name=f"element_{i}",
                loc=Location(v.Center()),
                color=Color("red"),
            )

        assy.export(name)

        return assy

    make_model("test_assy_copy.step", True)
    make_model("test_assy.step", False)

    # import the assy with copies
    assy_copy = Assembly.importStep(os.path.join(tmpdir, "test_assy_copy.step"))
    assert 5 == len(assy_copy.children)

    # import the assy without copies
    assy_normal = Assembly.importStep(os.path.join(tmpdir, "test_assy.step"))
    assert 5 == len(assy_normal.children)


def test_nested_subassembly_step_import(tmp_path_factory):
    """
    Tests if the STEP import works correctly with nested subassemblies.
    """

    tmpdir = tmp_path_factory.mktemp("out")
    nested_step_path = os.path.join(tmpdir, "plain_assembly_step.step")

    # Create a simple assembly
    assy = cq.Assembly()
    assy.add(cq.Workplane().box(10, 10, 10), name="box_1")

    # Create a simple subassembly
    subassy = cq.Assembly()
    subassy.add(cq.Workplane().box(5, 5, 5), name="box_2", loc=cq.Location(10, 10, 10))

    # Nest the subassembly
    assy.add(subassy)

    # Export and then re-import the nested assembly STEP
    assy.export(nested_step_path)
    imported_assy = cq.Assembly.importStep(nested_step_path)

    # Check the locations
    assert imported_assy.children[0].loc.toTuple()[0] == (0.0, 0.0, 0.0)
    assert imported_assy.children[1].objects["box_2"].loc.toTuple()[0] == (
        10.0,
        10.0,
        10.0,
    )


@pytest.mark.parametrize("kind", ["step", "xml", "xbf"])
@pytest.mark.parametrize(
    "assy_orig", ["subshape_assy", "boxes0_assy", "nested_assy", "simple_assy"],
)
def test_assembly_step_import_roundtrip(assy_orig, kind, tmp_path_factory, request):
    """
    Tests that the assembly does not mutate during successive export-import round trips.
    """

    assy_orig = request.getfixturevalue(assy_orig)

    # Set up the temporary directory
    tmpdir = tmp_path_factory.mktemp("out")
    round_trip_path = os.path.join(tmpdir, f"round_trip.{kind}")

    # First export
    assy_orig.export(round_trip_path)

    # First import
    assy = cq.Assembly.load(round_trip_path)

    # Second export
    assy.export(round_trip_path)

    # Second import
    assy = cq.Assembly.load(round_trip_path)

    # Check some general aspects of the assembly structure now
    for k in assy_orig.objects:
        assert k in assy

    for k in assy.objects:
        assert k in assy_orig

    if kind == "step":
        # First meta export
        exportStepMeta(assy, round_trip_path)

        # First meta import
        assy = cq.Assembly.importStep(round_trip_path)

        # Second meta export
        exportStepMeta(assy, round_trip_path)

        # Second meta import
        assy = cq.Assembly.importStep(round_trip_path)

        # Check some general aspects of the assembly structure now
        for k in assy_orig.objects:
            assert k in assy

        for k in assy.objects:
            assert k in assy_orig


@pytest.mark.parametrize(
    "assy_fixture, expected",
    [
        ("boxes8_assy", {"nsolids": 2, "center": (0.5, 10, 0.5)},),
        ("boxes9_assy", {"nsolids": 2, "center": (0.5, 10, 0.5)},),
    ],
)
def test_step_export_loc(assy_fixture, expected, request, tmpdir):
    stepfile = (Path(tmpdir) / assy_fixture).with_suffix(".step")
    if not stepfile.exists():
        assy = request.getfixturevalue(assy_fixture)
        assy.save(str(stepfile))
    o = cq.importers.importStep(str(stepfile))
    assert o.solids().size() == expected["nsolids"]
    c = cq.Compound.makeCompound(o.solids().vals()).Center()
    assert pytest.approx(c.toTuple()) == expected["center"]


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
        ("stl", ("STL",)),
    ],
)
def test_save(extension, args, nested_assy, nested_assy_sphere):

    filename = "nested." + extension
    nested_assy.save(filename, *args)
    assert os.path.exists(filename)


@pytest.mark.parametrize(
    "extension, args, kwargs",
    [
        ("step", (), {}),
        ("xml", (), {}),
        ("xbf", (), {}),
        ("vrml", (), {}),
        ("gltf", (), {}),
        ("glb", (), {}),
        ("stl", (), {"ascii": False}),
        ("stl", (), {"ascii": True}),
        ("stp", ("STEP",), {}),
        ("caf", ("XML",), {}),
        ("wrl", ("VRML",), {}),
        ("stl", ("STL",), {}),
    ],
)
def test_export(extension, args, kwargs, tmpdir, nested_assy):

    filename = "nested." + extension

    with tmpdir:
        nested_assy.export(filename, *args, **kwargs)
        assert os.path.exists(filename)


def test_export_vtkjs(tmpdir, nested_assy):

    with tmpdir:
        nested_assy.export("nested.vtkjs")
        assert os.path.exists("nested.vtkjs.zip")


def test_export_errors(nested_assy):

    with pytest.raises(ValueError):
        nested_assy.export("nested.1234")

    with pytest.raises(ValueError):
        nested_assy.export("nested.stl", "1234")

    with pytest.raises(ValueError):
        nested_assy.export("nested.step", mode="1234")


def test_save_stl_formats(nested_assy_sphere):

    # Binary export
    nested_assy_sphere.save("nested.stl", "STL", ascii=False)
    assert os.path.exists("nested.stl")

    # Trying to read a binary file as UTF-8/ASCII should throw an error
    with pytest.raises(UnicodeDecodeError):
        with open("nested.stl", "r") as file:
            file.read()

    # ASCII export
    nested_assy_sphere.save("nested_ascii.stl", ascii=True)
    assert os.path.exists("nested_ascii.stl")
    assert os.path.getsize("nested_ascii.stl") > 3960 * 1024


def test_save_gltf(nested_assy_sphere):

    # Binary export
    nested_assy_sphere.save("nested.glb")
    assert os.path.exists("nested.glb")

    # Trying to read a binary file as UTF-8/ASCII should throw an error
    with pytest.raises(UnicodeDecodeError):
        with open("nested.glb", "r") as file:
            file.read()

    # ASCII export
    nested_assy_sphere.save("nested_ascii.gltf")
    assert os.path.exists("nested_ascii.gltf")
    assert os.path.getsize("nested_ascii.gltf") > 5 * 1024


def test_exportGLTF(nested_assy_sphere):
    """Tests the exportGLTF function directly for binary vs ascii export."""

    # Test binary export inferred from file extension
    cq.exporters.assembly.exportGLTF(nested_assy_sphere, "nested_export_gltf.glb")
    with pytest.raises(UnicodeDecodeError):
        with open("nested_export_gltf.glb", "r") as file:
            file.read()

    # Test explicit binary export
    cq.exporters.assembly.exportGLTF(
        nested_assy_sphere, "nested_export_gltf_2.glb", binary=True
    )
    with pytest.raises(UnicodeDecodeError):
        with open("nested_export_gltf_2.glb", "r") as file:
            file.read()

    # Test explicit ascii export
    cq.exporters.assembly.exportGLTF(
        nested_assy_sphere, "nested_export_gltf_3.gltf", binary=False
    )
    with open("nested_export_gltf_3.gltf", "r") as file:
        lines = file.readlines()
        assert lines[0].startswith('{"accessors"')


def test_save_gltf_boxes2(boxes2_assy, tmpdir, capfd):
    """
    Output must not contain:

    RWGltf_CafWriter skipped node '<name>' without triangulation data
    """

    boxes2_assy.save(str(Path(tmpdir) / "boxes2_assy.glb"), "GLTF")

    output = capfd.readouterr()
    assert output.out == ""
    assert output.err == ""


def test_save_vtkjs(nested_assy):

    nested_assy.save("nested", "VTKJS")
    assert os.path.exists("nested.zip")


def test_save_raises(nested_assy):

    with pytest.raises(ValueError):
        nested_assy.save("nested.dxf")

    with pytest.raises(ValueError):
        nested_assy.save("nested.step", "DXF")


@pytest.mark.parametrize(
    "assy_fixture, count",
    [("simple_assy", 3), ("nested_assy", 3), ("empty_top_assy", 1),],
)
def test_leaf_node_count(assy_fixture, count, request):

    assy = request.getfixturevalue(assy_fixture)
    _, doc = toCAF(assy, True)

    assert len(get_doc_nodes(doc, True)) == count


def check_assy(assy, assy_i):

    for k in assy.objects:

        ref = assy[k]
        val = assy_i[k]

        # check colors
        if ref.color:
            assert ref.color.toTuple() == pytest.approx(val.color.toTuple())
        else:
            assert val.color is None

        # check loc
        assert pytest.approx(ref.loc.toTuple()[0]) == val.loc.toTuple()[0]
        assert pytest.approx(ref.loc.toTuple()[1]) == val.loc.toTuple()[1]

        # check names
        assert ref.name == val.name

        # check subshape names
        if ref._subshape_names:
            for v in ref._subshape_names.values():
                assert v in val._subshape_names.values()

        # check subshape layers
        if ref._subshape_layers:
            for v in ref._subshape_layers.values():
                assert v in val._subshape_layers.values()

        # check colors
        if ref._subshape_colors:
            colors = set(v.toTuple() for v in ref._subshape_colors.values())

            for v in val._subshape_colors.values():
                assert v.toTuple() in colors


@pytest.mark.parametrize("kind", ["xbf", "xml"])
@pytest.mark.parametrize(
    "assy_fixture",
    ["chassis0_assy", "boxes1_assy", "subshape_assy", "multi_subshape_assy"],
)
def test_colors_assy0(assy_fixture, request, tmpdir, kind):
    """Validate assembly roundtrip, checks colors, locs, names, subshapes.
    """

    assy = request.getfixturevalue(assy_fixture)
    stepfile = (Path(tmpdir) / assy_fixture).with_suffix(f".{kind}")
    assy.export(stepfile)

    assy_i = assy.load(stepfile)

    check_assy(assy, assy_i)


@pytest.mark.parametrize("kind", ["step", "xbf"])
@pytest.mark.parametrize(
    "assy_fixture",
    [
        "boxes7_assy",
        "boxes6_assy",
        "boxes5_assy",
        "boxes4_assy",
        "boxes3_assy",
        "boxes2_assy",
        "boxes0_assy",
        "nested_assy",
        "empty_top_assy",
        "subshape_assy",
        "multi_subshape_assy",
    ],
)
def test_colors_assy1(assy_fixture, request, tmpdir, kind):
    """Validate assembly colors with document explorer.

    Check both documents created with toCAF and STEP export round trip.
    """

    assy = request.getfixturevalue(assy_fixture)
    stepfile = (Path(tmpdir) / assy_fixture).with_suffix(f".{kind}")
    assy.export(stepfile)

    assy_i = assy.load(stepfile)

    check_assy(assy, assy_i)


@pytest.mark.parametrize(
    "assy_fixture, expected",
    [
        (
            "empty_top_assy",
            {
                "faces": [
                    {"center": (-0.5, 0, 0), "color": (0, 1, 0, 1)},
                    {"center": (0.5, 0, 0), "color": (0, 1, 0, 1)},
                    {"center": (0, -0.5, 0), "color": (0, 1, 0, 1)},
                    {"center": (0, 0.5, 0), "color": (0, 1, 0, 1)},
                    {"center": (0, 0, -0.5), "color": (0, 1, 0, 1)},
                    {"center": (0, 0, 0.5), "color": (0, 1, 0, 1)},
                ]
            },
        ),
        (
            "single_compound0_assy",
            {
                "name": "single_compound0",
                "faces": [
                    {"center": (-0.5, 0, 0), "color": (1, 0, 0, 0.8)},
                    {"center": (0.5, 0, 0), "color": (1, 0, 0, 0.8)},
                    {"center": (0, -1.0, 0), "color": (1, 0, 0, 0.8)},
                    {"center": (0, 1.0, 0), "color": (1, 0, 0, 0.8)},
                    {"center": (0, 0, -3.0), "color": (1, 0, 0, 0.8)},
                    {"center": (0, 0, 3.0), "color": (1, 0, 0, 0.8)},
                ],
            },
        ),
        (
            "single_compound1_assy",
            {
                "faces": [
                    {"center": (0, 0, -1.0), "color": (1, 0, 0, 0.8)},
                    {"center": (0, 0, 1.0), "color": (1, 0, 0, 0.8)},
                    {"center": (0, 0, -2.0), "color": (1, 0, 0, 0.8)},
                    {"center": (0, 0, 2.0), "color": (1, 0, 0, 0.8)},
                ]
            },
        ),
        (
            "spheres0_assy",
            {
                "faces": [
                    {"center": (0, 0, 0), "color": (1, 0, 0, 0.2)},
                    {"center": (2.1, 0, 0), "color": (0, 1, 0, 0.2)},
                ]
            },
        ),
        (
            "boxes2_assy",
            {
                "faces": [
                    {"center": (-0.5, 0, 0), "color": (1, 0, 0, 1)},
                    {"center": (0, -0.5, 0), "color": (1, 0, 0, 1)},
                    {"center": (0, 0, 0.5), "color": (1, 0, 0, 1)},
                    {"center": (0, 0.5, 0), "color": (1, 0, 0, 1)},
                    {"center": (0, 0, -0.5), "color": (1, 0, 0, 1)},
                    {"center": (1.0, -0.5, 0), "color": (0, 1, 0, 1)},
                    {"center": (1.0, 0, 0.5), "color": (0, 1, 0, 1)},
                    {"center": (1.0, 0.5, 0), "color": (0, 1, 0, 1)},
                    {"center": (1.0, 0, -0.5), "color": (0, 1, 0, 1)},
                    {"center": (1.5, 0, 0), "color": (0, 1, 0, 1)},
                ]
            },
        ),
        (
            "chassis0_assy",
            {
                "faces": [
                    # wheel
                    {"center": (-40.0, 50.0, 0), "color": (1, 0, 0, 1)},
                    {"center": (-45.0, 50.0, 0), "color": (1, 0, 0, 1)},
                    {"center": (-55.0, 50.0, 0), "color": (1, 0, 0, 1)},
                    {"center": (-60.0, 50.0, 0), "color": (1, 0, 0, 1)},
                    # wheel
                    {"center": (40.0, 50.0, 0), "color": (1, 0, 0, 1)},
                    {"center": (45.0, 50.0, 0), "color": (1, 0, 0, 1)},
                    {"center": (55.0, 50.0, 0), "color": (1, 0, 0, 1)},
                    {"center": (60.0, 50.0, 0), "color": (1, 0, 0, 1)},
                    # axle
                    {"center": (-20.0, 50.0, 0), "color": (0, 1, 0, 1)},
                    {"center": (20.0, 50.0, 0), "color": (0, 1, 0, 1)},
                    # wheel
                    {"center": (-40.0, -50.0, 0), "color": (1, 0, 0, 1)},
                    {"center": (-45.0, -50.0, 0), "color": (1, 0, 0, 1)},
                    {"center": (-55.0, -50.0, 0), "color": (1, 0, 0, 1)},
                    {"center": (-60.0, -50.0, 0), "color": (1, 0, 0, 1)},
                    # wheel
                    {"center": (40.0, -50.0, 0), "color": (1, 0, 0, 1)},
                    {"center": (45.0, -50.0, 0), "color": (1, 0, 0, 1)},
                    {"center": (55.0, -50.0, 0), "color": (1, 0, 0, 1)},
                    {"center": (60.0, -50.0, 0), "color": (1, 0, 0, 1)},
                    # axle
                    {"center": (-20.0, -50.0, 0), "color": (0, 1, 0, 1)},
                    {"center": (20.0, -50.0, 0), "color": (0, 1, 0, 1)},
                ]
            },
        ),
    ],
)
def test_colors_fused_assy(assy_fixture, expected, request, tmpdir):
    def check_nodes(doc, expected):
        nodes = get_doc_nodes(doc, False)
        assert len(nodes) == 1
        count_face = 0
        if "name" in expected:
            assert expected["name"] == nodes[0]["name"]
        for props in expected["faces"]:
            for props_doc in nodes[0]["faces"]:
                if (
                    pytest.approx(props["center"], abs=1e-6) == props_doc["center"]
                    and pytest.approx(props["color"], abs=1e-3) == props_doc["color"]
                ):
                    count_face += 1

        assert len(expected["faces"]) == count_face

    assy = request.getfixturevalue(assy_fixture)
    _, doc = toFusedCAF(assy, False)
    check_nodes(doc, expected)

    # repeat color check again - after STEP export round trip
    stepfile = (Path(tmpdir) / f"{assy_fixture}_fused").with_suffix(".step")
    if not stepfile.exists():
        assy.save(str(stepfile), mode=cq.exporters.assembly.ExportModes.FUSED)
    doc = read_step(stepfile)
    check_nodes(doc, expected)


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


@pytest.fixture
def touching_assy():

    b1 = cq.Workplane().box(1, 1, 1)
    b2 = cq.Workplane(origin=(1, 0, 0)).box(1, 1, 1)

    return cq.Assembly().add(b1).add(b2)


@pytest.fixture
def disjoint_assy():

    b1 = cq.Workplane().box(1, 1, 1)
    b2 = cq.Workplane(origin=(2, 0, 0)).box(1, 1, 1)

    return cq.Assembly().add(b1).add(b2)


def test_imprinting(touching_assy, disjoint_assy):

    # normal usecase
    r, o = cq.occ_impl.assembly.imprint(touching_assy)

    assert len(r.Solids()) == 2
    assert len(r.Faces()) == 11

    for s in r.Solids():
        assert s in o

    # edge usecase
    r, o = cq.occ_impl.assembly.imprint(disjoint_assy)

    assert len(r.Solids()) == 2
    assert len(r.Faces()) == 12

    for s in r.Solids():
        assert s in o


def test_order_of_transform():

    part = cq.Workplane().box(1, 1, 1).faces(">Z").vertices("<XY").tag("vtag")
    marker = cq.Workplane().sphere(0.2)

    assy0 = cq.Assembly().add(
        part, name="part1", loc=cq.Location((0, 0, 1.5), (0, 0, 1), 45),
    )

    assy1 = (
        cq.Assembly()
        .add(assy0, name="assy0", loc=cq.Location(2, 0, 0))
        .add(marker, name="marker1")
    )

    # attach the first marker to the tagged corner
    assy1.constrain("assy0/part1", "Fixed")
    assy1.constrain("marker1", "assy0/part1?vtag", "Point")
    assy1.solve()

    assy2 = cq.Assembly().add(assy1, name="assy1").add(marker, name="marker2")

    # attach the second marker to the tagged corner, but this time with nesting
    assy2.constrain("assy1/marker1", "Fixed")
    assy2.constrain("marker2", "assy1/assy0/part1?vtag", "Point")
    assy2.solve()

    # marker1 and marker2 should coincide
    m1, m2 = assy2.toCompound().Solids()

    assert (m1.Center() - m2.Center()).Length == approx(0)


def test_step_export_filesize(tmpdir):
    """A sanity check of STEP file size.
    Multiple instances of a shape with same color is not expected to result
    in significant file size increase.
    """
    part = box(1, 1, 1)
    N = 10
    filesize = {}

    for i, color in enumerate((None, cq.Color("red"))):
        assy = cq.Assembly()
        for j in range(1, N + 1):
            assy.add(
                part, name=f"part{j}", loc=cq.Location(x=j * 1), color=copy.copy(color)
            )
        stepfile = Path(tmpdir) / f"assy_step_filesize{i}.step"
        assy.export(str(stepfile))
        filesize[i] = stepfile.stat().st_size

    assert filesize[1] < 1.2 * filesize[0]


def test_assembly_remove_no_name_match():
    """
    Tests to make sure that removing a part/subassembly with a name that does not exist fails.
    """

    assy = cq.Assembly()
    assy.add(box(1, 1, 1), name="part1")
    assy.add(box(2, 2, 2), name="part2")

    with pytest.raises(ValueError):
        assy.remove("part3")


def test_assembly_remove_part():
    """
    Tests the ability to remove a part from an assembly.
    """
    assy = cq.Assembly()
    assy.add(box(1, 1, 1), name="part1")
    assy.add(box(2, 2, 2), name="part2", loc=cq.Location(5.0, 5.0, 5.0))

    # Make sure we have the correct number of children (2 parts)
    assert len(assy.children) == 2
    assert len(assy.objects) == 3

    # Remove the first part
    assy.remove("part1")

    # Make sure we have the correct number of children (1 part)
    assert len(assy.children) == 1
    assert len(assy.objects) == 2


def test_assembly_remove_subassy():
    """
    Tests the ability to remove a subassembly from an assembly.
    """

    # Create the top-level assembly
    assy = cq.Assembly()
    assy.add(box(1, 1, 1), name="loplevel_part1")

    # Create the subassembly
    subassy = cq.Assembly()
    subassy.add(box(1, 1, 1), name="part1")
    subassy.add(box(2, 2, 2), name="part2", loc=cq.Location(5.0, 5.0, 5.0))

    # Add the subassembly to the top-level assembly
    assy.add(subassy, name="subassy")

    # Make sure we have the 1 top-level part and the subassembly
    assert len(assy.children) == 2
    assert len(assy.objects) == 5

    # Remove the subassembly
    assy.remove("subassy")

    # Make sure we have the correct number of children (1 part)
    assert len(assy.children) == 1
    assert len(assy.objects) == 2

    # Recreate the assembly with a nested subassembly
    assy = cq.Assembly()
    assy.add(box(1, 1, 1), name="loplevel_part1")
    subassy = cq.Assembly()
    subassy.add(box(1, 1, 1), name="part1")
    subassy.add(box(2, 2, 2), name="part2", loc=cq.Location(2.0, 2.0, 2.0))
    assy.add(subassy, name="subassy")

    # Try to remove a part from a subassembly by using the path string
    assert len(assy.children[1].children) == 2
    assy.remove("subassy/part2")
    assert len(assy.children[1].children) == 1


def test_remove_without_parent():
    """
    Tests the ability to remove a part from an assembly when the part has no parent.
    This may never happen in practice, but the case has to be covered for mypy to pass.
    """

    # Create a root assembly
    assy = cq.Assembly(name="root")

    # Create a part and add it to the assembly
    part = cq.Workplane().box(1, 1, 1)
    assy.add(part, name="part")

    # Artificially remove the parent to cover a branching test case
    assy.children[0].parent = None

    # Remove the part
    assy.remove("part")

    assert len(assy.children) == 1
    assert len(assy.objects) == 1


def test_step_color(tmp_path_factory):
    """
    Checks color handling for STEP export.
    """

    # Use a temporary directory
    tmpdir = tmp_path_factory.mktemp("out")
    step_color_path = os.path.join(tmpdir, "step_color.step")

    # Create a simple assembly with color
    assy = cq.Assembly()
    assy.add(cq.Workplane().box(10, 10, 10), color=cq.Color(0.47, 0.253, 0.18, 1.0))

    success = exportStepMeta(assy, step_color_path)
    assert success

    # Read the file as a string and check for the correct colors
    with open(step_color_path, "r") as f:
        step_content = f.readlines()

        # Step through and try to find the COLOUR line
        for line in step_content:
            if "COLOUR_RGB(''," in line:
                assert "0.47" in line
                assert "0.25" in line
                assert "0.18" in line


def test_special_methods(subshape_assy):
    """
    Smoke-test some special methods.
    """

    assert "cube_1" in subshape_assy.__dir__()
    assert "cube_1" in subshape_assy._ipython_key_completions_()
    assert "cube_1" in subshape_assy

    subshape_assy["cube_1"]
    subshape_assy.cube_1

    with pytest.raises(KeyError):
        subshape_assy["123456"]

    with pytest.raises(AttributeError):
        subshape_assy.cube_123456


def test_shallow_assy():
    """
    toCAF edge case.
    """

    # shallow assy
    toCAF(cq.Assembly(cq.Workplane().box(1, 1, 1)))

    with pytest.raises(ValueError):
        toCAF(cq.Assembly())
