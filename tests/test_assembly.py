import pytest
import os
from itertools import product
from math import degrees
import copy
from pathlib import Path, PurePath
import re

import cadquery as cq
from cadquery.occ_impl.exporters.assembly import (
    exportAssembly,
    exportCAF,
    exportVTKJS,
    exportVRML,
)
from cadquery.occ_impl.assembly import toJSON, toCAF

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
from OCP.Quantity import Quantity_ColorRGBA, Quantity_TOC_RGB


@pytest.fixture(scope="module")
def tmpdir(tmp_path_factory):
    return tmp_path_factory.mktemp("assembly")


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

        name_att = TDataStd_Name()
        label.FindAttribute(TDataStd_Name.GetID_s(), name_att)
        name = TCollection_ExtendedString(name_att.Get()).ToExtString()

        color = style.GetColorSurfRGBA()
        shape = expl.FindShapeFromPathId_s(doc, node.Id)
        color_shape = Quantity_ColorRGBA()
        ctool.GetColor(shape, XCAFDoc_ColorType.XCAFDoc_ColorSurf, color_shape)

        # on STEP import colors applied to subshapes
        color_subshapes = None
        color_subshapes_set = set()
        if not node.IsAssembly and shape.NbChildren() > 1:
            it = TDF_ChildIterator(label)
            i = 0
            while it.More():
                child = it.Value()
                color_subshape = Quantity_ColorRGBA()
                if ctool.GetColor(
                    child, XCAFDoc_ColorType.XCAFDoc_ColorSurf, color_subshape
                ):
                    color_subshapes_set.add(
                        (
                            *color_subshape.GetRGB().Values(Quantity_TOC_RGB),
                            color_subshape.Alpha(),
                        )
                    )
                it.Next()
                i += 1
                if i > 5:
                    break
            assert len(color_subshapes_set) == 1
            color_subshapes = color_subshapes_set.pop()

        nodes.append(
            {
                "path": PurePath(node.Id.ToCString()),
                "name": TCollection_ExtendedString(name_att.Get()).ToExtString(),
                "color": (*color.GetRGB().Values(Quantity_TOC_RGB), color.Alpha()),
                "color_shape": (
                    *color_shape.GetRGB().Values(Quantity_TOC_RGB),
                    color_shape.Alpha(),
                ),
                "color_subshapes": color_subshapes,
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

    c4 = cq.Color()

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
    c.toTuple()
    assert pytest.approx(c.toTuple()) == (0, 4, 0)
    c2 = cq.Compound.makeCompound(o.solids().vals()).Center()
    c2.toTuple()
    assert pytest.approx(c2.toTuple()) == (0, 4, 0)


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


def test_save_gltf(nested_assy_sphere):

    nested_assy_sphere.save("nested.glb", "GLTF")
    assert os.path.exists("nested.glb")
    assert os.path.getsize("nested.glb") > 50 * 1024


def test_save_gltf_boxes2(boxes2_assy, tmpdir, capfd):
    """
    Output must not contain:

    RWGltf_CafWriter skipped node '<name>' without triangulation data
    """

    boxes2_assy.save(str(Path(tmpdir, "boxes2_assy.glb")), "GLTF")

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


@pytest.mark.parametrize(
    "assy_fixture, expected",
    [
        (
            "chassis0_assy",
            [
                (
                    ["chassis", "wheel-axle.*", "wheel:.*"],
                    {
                        "color": (1.0, 0.0, 0.0, 1.0),
                        "color_shape": (1.0, 0.0, 0.0, 1.0),
                        "num_nodes": 4,
                    },
                ),
                (
                    ["chassis", "wheel-axle.*", "wheel:.*", "wheel.*_part"],
                    {"color": (1.0, 0.0, 0.0, 1.0), "num_nodes": 4},
                ),
                (
                    ["chassis", "wheel-axle.*", "axle"],
                    {
                        "color": (0.0, 1.0, 0.0, 1.0),
                        "color_shape": (0.0, 1.0, 0.0, 1.0),
                        "num_nodes": 2,
                    },
                ),
                (
                    ["chassis", "wheel-axle.*", "axle", "axle_part"],
                    {"color": (0.0, 1.0, 0.0, 1.0), "num_nodes": 2},
                ),
            ],
        ),
    ],
)
def test_colors_assy0(assy_fixture, expected, request):
    """Validate assembly colors with document explorer.

    Check toCAF wth color shape parameter False.
    """

    def check_nodes(doc, expected):
        allnodes = get_doc_nodes(doc, False)
        for name_path, props in expected:
            nodes = find_node(allnodes, name_path)
            if "num_nodes" in props:
                assert len(nodes) == props["num_nodes"]
                props.pop("num_nodes")
            else:
                assert len(nodes) > 0
            for n in nodes:
                for k, v in props.items():
                    assert pytest.approx(n[k], abs=1e-3) == v

    assy = request.getfixturevalue(assy_fixture)
    _, doc = toCAF(assy, False)
    check_nodes(doc, expected)


@pytest.mark.parametrize(
    "assy_fixture, expected",
    [
        (
            "nested_assy",
            [
                (
                    ["TOP", "SECOND", "SECOND_part"],
                    {"color_shape": (0.0, 1.0, 0.0, 1.0)},
                ),
                (
                    ["TOP", "SECOND", "BOTTOM", "BOTTOM_part"],
                    {
                        "color_shape": (0.0, 1.0, 0.0, 1.0),
                        "color_subshapes": (0.0, 1.0, 0.0, 1.0),
                    },
                ),
            ],
        ),
        ("empty_top_assy", [([".*_part"], {"color_shape": (0.0, 1.0, 0.0, 1.0)}),]),
        (
            "boxes0_assy",
            [
                (["box0", "box0_part"], {"color_shape": (1.0, 0.0, 0.0, 1.0)}),
                (["box1", "box1_part"], {"color_shape": (1.0, 0.0, 0.0, 1.0)}),
            ],
        ),
        (
            "boxes1_assy",
            [
                (["box0", "box0_part"], {"color_shape": (1.0, 0.0, 0.0, 1.0)}),
                (["box1", "box0_part"], {"color_shape": (1.0, 0.0, 0.0, 1.0)}),
            ],
        ),
        (
            "boxes2_assy",
            [
                (["box0", "box0_part"], {"color_shape": (1.0, 0.0, 0.0, 1.0)}),
                (["box1", "box1_part"], {"color_shape": (0.0, 1.0, 0.0, 1.0)}),
            ],
        ),
        (
            "boxes3_assy",
            [
                (["box0", "box0_part"], {"color_shape": (1.0, 0.0, 0.0, 1.0)}),
                (
                    ["box1", "box1_part"],
                    {"color_shape": cq.Color().toTuple()},
                ),  # default color when unspecified
            ],
        ),
        (
            "boxes4_assy",
            [
                (["box_0", "box_0_part"], {"color_shape": (1.0, 0.0, 0.0, 1.0)}),
                (["box_1", "box_1_part"], {"color_shape": (0.0, 1.0, 0.0, 1.0)}),
            ],
        ),
        (
            "boxes5_assy",
            [
                (["box:a", "box:a_part"], {"color_shape": (1.0, 0.0, 0.0, 1.0)}),
                (["box:b", "box:b_part"], {"color_shape": (0.0, 1.0, 0.0, 1.0)}),
            ],
        ),
        (
            "boxes6_assy",
            [
                (["box__0", "box__0_part"], {"color_shape": (1.0, 0.0, 0.0, 1.0)}),
                (["box__1", "box__1_part"], {"color_shape": (0.0, 1.0, 0.0, 1.0)}),
            ],
        ),
        (
            "boxes7_assy",
            [
                (["box_0", "box_0_part"], {"color_shape": (1.0, 0.0, 0.0, 1.0)}),
                (["box", "box_part"], {"color_shape": (0.0, 1.0, 0.0, 1.0)}),
                (
                    ["another box", "another box_part"],
                    {"color_shape": (0.23, 0.26, 0.26, 0.6)},
                ),
            ],
        ),
        (
            "chassis0_assy",
            [
                (
                    ["chassis", "wheel-axle-front", "wheel:left", "wheel:left_part"],
                    {"color_shape": (1.0, 0.0, 0.0, 1.0)},
                ),
                (
                    ["chassis", "wheel-axle-front", "wheel:right", "wheel:right_part"],
                    {"color_shape": (1.0, 0.0, 0.0, 1.0)},
                ),
                (
                    ["chassis", "wheel-axle-rear", "wheel:left", "wheel:left_part"],
                    {"color_shape": (1.0, 0.0, 0.0, 1.0)},
                ),
                (
                    ["chassis", "wheel-axle-rear", "wheel:right", "wheel:right_part"],
                    {"color_shape": (1.0, 0.0, 0.0, 1.0)},
                ),
                (
                    ["chassis", "wheel-axle-front", "axle", "axle_part"],
                    {"color_shape": (0.0, 1.0, 0.0, 1.0)},
                ),
                (
                    ["chassis", "wheel-axle-rear", "axle", "axle_part"],
                    {"color_shape": (0.0, 1.0, 0.0, 1.0)},
                ),
            ],
        ),
    ],
)
def test_colors_assy1(assy_fixture, expected, request, tmpdir):
    """Validate assembly colors with document explorer.

    Check both documents created with toCAF and STEP export round trip.
    """

    def check_nodes(doc, expected, is_STEP=False):
        expected = copy.deepcopy(expected)
        allnodes = get_doc_nodes(doc, False)
        for name_path, props in expected:
            nodes = find_node(allnodes, name_path)
            if "num_nodes" in props:
                assert len(nodes) == props["num_nodes"]
                props.pop("num_nodes")
            else:
                assert len(nodes) > 0
            for n in nodes:
                if not is_STEP:
                    if "color_subshapes" in props:
                        props.pop("color_subshapes")
                for k, v in props.items():
                    if (
                        k == "color_shape"
                        and "color_subshapes" in props
                        and props["color_subshapes"]
                    ):
                        continue
                    assert pytest.approx(n[k], abs=1e-3) == v

    assy = request.getfixturevalue(assy_fixture)
    _, doc = toCAF(assy, True)
    check_nodes(doc, expected)

    # repeat color check again - after STEP export round trip
    stepfile = Path(tmpdir, assy_fixture).with_suffix(".step")
    if not stepfile.exists():
        assy.save(str(stepfile))
    doc = read_step(stepfile)
    check_nodes(doc, expected, True)


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
