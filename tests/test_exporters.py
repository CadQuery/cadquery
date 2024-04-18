"""
    Tests exporters
"""
# core modules
import os
import io
from pathlib import Path
import re
import sys
import math
import pytest
import ezdxf

from pytest import approx

# my modules
from cadquery import (
    exporters,
    importers,
    Sketch,
    Workplane,
    Edge,
    Vertex,
    Assembly,
    Plane,
    Location,
    Vector,
    Color,
)
from cadquery.occ_impl.exporters.dxf import DxfDocument
from cadquery.occ_impl.exporters.utils import toCompound
from tests import BaseTest
from OCP.GeomConvert import GeomConvert
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeEdge


@pytest.fixture(scope="module")
def tmpdir(tmp_path_factory):
    return tmp_path_factory.mktemp("out")


@pytest.fixture(scope="module")
def testdatadir():
    return Path(__file__).parent.joinpath("testdata")


@pytest.fixture()
def box123():
    return Workplane().box(1, 2, 3)


def test_step_options(tmpdir):
    """
    Exports a box using the options to decrease STEP file size and
    then imports that STEP to validate it.
    """
    # Use a temporary directory
    box_path = os.path.join(tmpdir, "out.step")

    # Simple object to export
    box = Workplane().box(1, 1, 1)

    # Export the STEP with the size-saving options and then import it back in
    box.val().exportStep(box_path, write_pcurves=False, precision_mode=0)
    w = importers.importStep(box_path)

    # Make sure there was a valid box in the exported file
    assert w.solids().size() == 1
    assert w.faces().size() == 6


def test_fused_assembly(tmpdir):
    """
    Exports as simple assembly using the "fused" STEP export mode
    and then imports that STEP again to validate it.
    """

    # Create the sample assembly
    assy = Assembly()
    body = Workplane().box(10, 10, 10)
    assy.add(body, color=Color(1, 0, 0), name="body")
    pin = Workplane().center(2, 2).cylinder(radius=2, height=20)
    assy.add(pin, color=Color(0, 1, 0), name="pin")

    # Export the assembly
    step_path = os.path.join(tmpdir, "fused.step")
    assy.save(
        path=str(step_path),
        exportType=exporters.ExportTypes.STEP,
        mode=exporters.assembly.ExportModes.FUSED,
    )

    # Import the assembly and make sure it acts as expected
    model = importers.importStep(step_path)
    assert model.solids().size() == 1


def test_fused_not_touching_assembly(tmpdir):
    """
    Exports as simple assembly using the "fused" STEP export mode
    and then imports that STEP again to validate it. This tests whether
    or not the fuse method correctly handles fusing solids to do not touch.
    """

    # Create the sample assembly
    assy = Assembly()
    body = Workplane().box(10, 10, 10)
    assy.add(body, color=Color(1, 0, 0), name="body")
    pin = Workplane().center(8, 8).cylinder(radius=2, height=20)
    assy.add(pin, color=Color(0, 1, 0), name="pin")

    # Export the assembly
    step_path = os.path.join(tmpdir, "fused_not_touching.step")
    assy.save(
        path=str(step_path),
        exportType=exporters.ExportTypes.STEP,
        mode=exporters.assembly.ExportModes.FUSED,
    )

    # Import the assembly and make sure it acts as expected
    model = importers.importStep(step_path)
    assert model.solids().size() == 2


def test_nested_fused_assembly(tmpdir):
    """
    Tests a nested assembly being exported as a single, fused solid.
    The resulting STEP is imported again to test it.
    """
    # Create the nested assembly
    assy = Assembly()
    body = Workplane().box(10, 10, 10)
    assy.add(body, color=Color(1, 0, 0), name="body")
    pins = Assembly()
    pin1 = Workplane().center(8, 8).cylinder(radius=2, height=20)
    pin2 = Workplane().center(-8, -8).cylinder(radius=2, height=20)
    pins.add(pin1, color=Color(0, 1, 0), name="pin1")
    pins.add(pin2, color=Color(0, 0, 1), name="pin2")
    assy.add(pins, name="pins")

    # Export the assembly
    step_path = os.path.join(tmpdir, "nested_fused_assembly.step")
    assy.save(
        path=str(step_path),
        exportType=exporters.ExportTypes.STEP,
        mode=exporters.assembly.ExportModes.FUSED,
    )

    # Import the assembly and make sure it acts as expected
    model = importers.importStep(step_path)
    assert model.solids().size() == 3


def test_fused_assembly_with_one_part(tmpdir):
    """
    Tests the ability to fuse an assembly with only one part present.
    The resulting STEP is imported again to test it.
    """
    # Create the single-part assembly
    assy = Assembly()
    body = Workplane().box(10, 10, 10)
    assy.add(body, color=Color(1, 0, 0), name="body")

    # Export the assembly
    step_path = os.path.join(tmpdir, "single_part_fused_assembly.step")
    assy.save(
        path=str(step_path),
        exportType=exporters.ExportTypes.STEP,
        mode=exporters.assembly.ExportModes.FUSED,
    )

    # Import the assembly and make sure it acts as expected
    model = importers.importStep(step_path)
    assert model.solids().size() == 1


def test_fused_assembly_glue_tol(tmpdir):
    """
    Tests the glue and tol settings of the fused assembly export.
    The resulting STEP is imported again to test it.
    """

    # Create the sample assembly
    assy = Assembly()
    body = Workplane().box(10, 10, 10)
    assy.add(body, color=Color(1, 0, 0), name="body")
    pin = Workplane().center(8, 8).cylinder(radius=2, height=20)
    assy.add(pin, color=Color(0, 1, 0), name="pin")

    # Export the assembly
    step_path = os.path.join(tmpdir, "fused_glue_tol.step")
    assy.save(
        path=str(step_path),
        exportType=exporters.ExportTypes.STEP,
        mode=exporters.assembly.ExportModes.FUSED,
        fuzzy_tol=0.1,
        glue=True,
    )

    # Import the assembly and make sure it acts as expected
    model = importers.importStep(step_path)
    assert model.solids().size() == 2


def test_fused_assembly_top_level_only(tmpdir):
    """
    Tests the assembly with only a top level shape and no children.
    The resulting STEP is imported again to test it.
    """

    # Create the assembly
    body = Workplane().box(10, 10, 10)
    assy = Assembly(body)

    # Export the assembly
    step_path = os.path.join(tmpdir, "top_level_only_fused_assembly.step")
    assy.save(
        path=str(step_path),
        exportType=exporters.ExportTypes.STEP,
        mode=exporters.assembly.ExportModes.FUSED,
    )

    # Import the assembly and make sure it acts as expected
    model = importers.importStep(step_path)
    assert model.solids().size() == 1


def test_fused_assembly_top_level_with_children(tmpdir):
    """
    Tests the assembly with a top level shape and multiple children.
    The resulting STEP is imported again to test it.
    """

    # Create the assembly
    body = Workplane().box(10, 10, 10)
    assy = Assembly(body)
    mark = Workplane().center(3, 3).cylinder(radius=1, height=10)
    assy.add(mark, color=Color(1, 0, 0), name="mark")
    pin = Workplane().center(-5, -5).cylinder(radius=2, height=20)
    assy.add(pin, loc=Location(Vector(0, 0, 15)), color=Color(0, 1, 0), name="pin")

    # Export the assembly
    step_path = os.path.join(tmpdir, "top_level_with_children_fused_assembly.step")
    assy.save(
        path=str(step_path),
        exportType=exporters.ExportTypes.STEP,
        mode=exporters.assembly.ExportModes.FUSED,
    )

    # Import the assembly and make sure it acts as expected
    model = importers.importStep(step_path)
    assert model.solids().size() == 1
    assert model.faces(">Z").val().Center().z == approx(25)


def test_fused_empty_assembly(tmpdir):
    """
    Tests that a save of an empty fused assembly will fail.
    """
    # Create the assembly
    assy = Assembly()

    # Make sure an export with no top level shape raises an exception
    with pytest.raises(Exception):
        # Export the assembly
        step_path = os.path.join(tmpdir, "empty_fused_assembly.step")
        assy.save(
            path=str(step_path),
            exportType=exporters.ExportTypes.STEP,
            mode=exporters.assembly.ExportModes.FUSED,
        )


def test_fused_invalid_mode(tmpdir):
    """
    Tests that an exception is raised when a user passes a bad mode
    for assembly export to STEP.
    """
    # Create the assembly
    body = Workplane().box(10, 10, 10)
    assy = Assembly(body)

    # Make sure an export with an invalid export mode raises an exception
    with pytest.raises(Exception):
        # Export the assembly
        step_path = os.path.join(tmpdir, "invalid_mode_fused_assembly.step")
        assy.save(
            path=str(step_path),
            exportType=exporters.ExportTypes.STEP,
            mode="INCORRECT",
        )


class TestDxfDocument(BaseTest):
    """Test class DxfDocument."""

    def test_line(self):
        workplane = Workplane().line(1, 1)

        plane = workplane.plane
        shape = toCompound(workplane).transformShape(plane.fG)
        edges = shape.Edges()

        result = DxfDocument._dxf_line(edges[0])

        expected = ("LINE", {"start": (0.0, 0.0, 0.0), "end": (1.0, 1.0, 0.0)})

        self.assertEqual(expected, result)

    def test_circle(self):
        workplane = Workplane().circle(1)

        plane = workplane.plane
        shape = toCompound(workplane).transformShape(plane.fG)
        edges = shape.Edges()

        result = DxfDocument._dxf_circle(edges[0])

        expected = ("CIRCLE", {"center": (0.0, 0.0, 0.0), "radius": 1.0})

        self.assertEqual(expected, result)

    def test_arc(self):
        workplane = Workplane().radiusArc((1, 1), 1)

        plane = workplane.plane
        shape = toCompound(workplane).transformShape(plane.fG)
        edges = shape.Edges()

        result_type, result_attributes = DxfDocument._dxf_circle(edges[0])

        expected_type, expected_attributes = (
            "ARC",
            {"center": (1, 0, 0), "radius": 1, "start_angle": 90, "end_angle": 180,},
        )

        self.assertEqual(expected_type, result_type)
        self.assertTupleAlmostEquals(
            expected_attributes["center"], result_attributes["center"], 3
        )
        self.assertAlmostEqual(
            expected_attributes["radius"], approx(result_attributes["radius"])
        )
        self.assertAlmostEqual(
            expected_attributes["start_angle"], result_attributes["start_angle"]
        )
        self.assertAlmostEqual(
            expected_attributes["end_angle"], result_attributes["end_angle"]
        )

    def test_ellipse(self):
        workplane = Workplane().ellipse(2, 1, 0)

        plane = workplane.plane
        shape = toCompound(workplane).transformShape(plane.fG)
        edges = shape.Edges()

        result_type, result_attributes = DxfDocument._dxf_ellipse(edges[0])

        expected_type, expected_attributes = (
            "ELLIPSE",
            {
                "center": (0, 0, 0),
                "major_axis": (2.0, 0, 0),
                "ratio": 0.5,
                "start_param": 0,
                "end_param": 6.283185307179586,
            },
        )

        self.assertEqual(expected_type, result_type)
        self.assertEqual(expected_attributes["center"], result_attributes["center"])
        self.assertEqual(
            expected_attributes["major_axis"], result_attributes["major_axis"]
        )
        self.assertEqual(expected_attributes["ratio"], result_attributes["ratio"])
        self.assertEqual(
            expected_attributes["start_param"], result_attributes["start_param"]
        )
        self.assertAlmostEqual(
            expected_attributes["end_param"], result_attributes["end_param"]
        )

    def test_spline(self):
        pts = [(0, 0), (0, 0.5), (1, 1)]
        workplane = (
            Workplane().spline(pts).close().extrude(1).edges("|Z").fillet(0.1).section()
        )

        plane = workplane.plane
        shape = toCompound(workplane).transformShape(plane.fG)
        edges = shape.Edges()

        result_type, result_attributes = DxfDocument._dxf_spline(edges[0], plane)

        expected_type, expected_attributes = (
            "SPLINE",
            {
                "control_points": [
                    (-0.032010295564216654, 0.2020130195642037, 0.0),
                    (-0.078234124721739, 0.8475143728081896, 0.0),
                    (0.7171193004814275, 0.9728923786984539, 0.0),
                ],
                "order": 3,
                "knots": [
                    0.18222956891558767,
                    0.18222956891558767,
                    0.18222956891558767,
                    1.416096480384525,
                    1.416096480384525,
                    1.416096480384525,
                ],
                "weights": None,
            },
        )

        self.assertEqual(expected_type, result_type)

        for expected, result in zip(
            expected_attributes["control_points"], result_attributes["control_points"]
        ):
            assert result == approx(expected)

        self.assertEqual(expected_attributes["order"], result_attributes["order"])
        assert result_attributes["knots"] == approx(expected_attributes["knots"])
        self.assertEqual(expected_attributes["weights"], result_attributes["weights"])

    def test_add_layer_definition(self):
        dxf = DxfDocument()
        dxf.add_layer("layer_1")

        self.assertIn("layer_1", dxf.document.layers)

    def test_add_layer_definition_with_color(self):
        dxf = DxfDocument()
        dxf.add_layer("layer_1", color=2)
        layer = dxf.document.layers.get("layer_1")

        self.assertEqual(2, layer.color)

    def test_add_layer_definition_with_linetype(self):
        dxf = DxfDocument(setup=True)
        dxf.add_layer("layer_1", linetype="CENTER")
        layer = dxf.document.layers.get("layer_1")

        self.assertEqual("CENTER", layer.dxf.linetype)

    def test_add_shape_to_layer(self):
        line = Workplane().line(0, 10)

        dxf = DxfDocument(setup=True)

        default_layer_names = set()
        for layer in dxf.document.layers:
            default_layer_names.add(layer.dxf.name)

        dxf = dxf.add_layer("layer_1").add_shape(line, "layer_1")

        expected_layer_names = default_layer_names.copy()
        expected_layer_names.add("layer_1")

        self.assertEqual({"0", "Defpoints"}, default_layer_names)

        self.assertEqual(1, len(dxf.msp))
        self.assertEqual({"0", "Defpoints", "layer_1"}, expected_layer_names)
        self.assertEqual("layer_1", dxf.msp[0].dxf.layer)
        self.assertEqual("LINE", dxf.msp[0].dxftype())

    def test_set_dxf_version(self):
        dxfversion = "AC1032"

        dxf_default = DxfDocument()
        dxf = DxfDocument(dxfversion=dxfversion)

        self.assertNotEqual(dxfversion, dxf_default.document.dxfversion)
        self.assertEqual(dxfversion, dxf.document.dxfversion)

    def test_set_units(self):
        doc_units = 17

        dxf_default = DxfDocument()
        dxf = DxfDocument(doc_units=17)

        self.assertNotEqual(doc_units, dxf_default.document.units)
        self.assertEqual(doc_units, dxf.document.units)

    def test_set_metadata(self):
        metadata = {"CUSTOM_KEY": "custom value"}

        dxf = DxfDocument(metadata=metadata)

        self.assertEqual(
            metadata["CUSTOM_KEY"], dxf.document.ezdxf_metadata().get("CUSTOM_KEY"),
        )

    def test_add_shape_line(self):
        workplane = Workplane().line(1, 1)
        dxf = DxfDocument()
        dxf.add_shape(workplane)

        result = dxf.msp.query("LINE")[0]

        expected = ezdxf.entities.line.Line.new(
            dxfattribs={"start": (0.0, 0.0, 0.0), "end": (1.0, 1.0, 0.0),},
        )

        self.assertEqual(expected.dxf.start, result.dxf.start)
        self.assertEqual(expected.dxf.end, result.dxf.end)

    def test_DxfDocument_import(self):
        assert isinstance(exporters.DxfDocument(), DxfDocument)


class TestExporters(BaseTest):
    def _exportBox(self, eType, stringsToFind, tolerance=0.1, angularTolerance=0.1):
        """
        Exports a test object, and then looks for
        all of the supplied strings to be in the result
        returns the result in case the case wants to do more checks also
        """
        p = Workplane("XY").box(1, 2, 3)

        if eType in (exporters.ExportTypes.AMF, exporters.ExportTypes.THREEMF):
            s = io.BytesIO()
        else:
            s = io.StringIO()

        exporters.exportShape(
            p, eType, s, tolerance=tolerance, angularTolerance=angularTolerance
        )

        result = "{}".format(s.getvalue())

        for q in stringsToFind:
            self.assertTrue(result.find(q) > -1)
        return result

    def _box(self):

        return Workplane().box(1, 1, 1)

    def testSTL(self):
        # New STL tests have been added; Keep this to test deprecated exportShape
        self._exportBox(exporters.ExportTypes.STL, ["facet normal"])

    def testSVG(self):
        self._exportBox(exporters.ExportTypes.SVG, ["<svg", "<g transform"])

        exporters.export(self._box(), "out.svg")

    def testSVGOptions(self):
        self._exportBox(exporters.ExportTypes.SVG, ["<svg", "<g transform"])

        exporters.export(
            self._box(),
            "out.svg",
            opt={
                "width": 100,
                "height": None,
                "marginLeft": 10,
                "marginTop": 10,
                "showAxes": False,
                "projectionDir": (0, 0, 1),
                "strokeWidth": 0.25,
                "strokeColor": (255, 0, 0),
                "hiddenColor": (0, 0, 255),
                "showHidden": True,
                "focus": 4,
            },
        )

        exporters.export(
            self._box(),
            "out.svg",
            opt={
                "width": None,
                "height": 100,
                "marginLeft": 10,
                "marginTop": 10,
                "showAxes": False,
                "projectionDir": (0, 0, 1),
                "strokeWidth": 0.25,
                "strokeColor": (255, 0, 0),
                "hiddenColor": (0, 0, 255),
                "showHidden": True,
                "focus": 4,
            },
        )

    def testAMF(self):
        self._exportBox(exporters.ExportTypes.AMF, ["<amf units", "</object>"])

        exporters.export(self._box(), "out.amf")

    def testSTEP(self):
        self._exportBox(exporters.ExportTypes.STEP, ["FILE_SCHEMA"])

        exporters.export(self._box(), "out.step")

    def test3MF(self):
        self._exportBox(
            exporters.ExportTypes.THREEMF,
            ["3D/3dmodel.model", "[Content_Types].xml", "_rels/.rels"],
        )
        exporters.export(self._box(), "out1.3mf")  # Compound
        exporters.export(self._box().val(), "out2.3mf")  # Solid

        # No zlib support
        import zlib

        sys.modules["zlib"] = None
        exporters.export(self._box(), "out3.3mf")
        sys.modules["zlib"] = zlib

    def testTJS(self):
        self._exportBox(
            exporters.ExportTypes.TJS, ["vertices", "formatVersion", "faces"]
        )

        exporters.export(self._box(), "out.tjs")

    def testVRML(self):

        exporters.export(self._box(), "out.vrml")

        with open("out.vrml") as f:
            res = f.read(10)

        assert res.startswith("#VRML V2.0")

        # export again to trigger all paths in the code
        exporters.export(self._box(), "out.vrml")

    def testVTP(self):

        exporters.export(self._box(), "out.vtp")

        with open("out.vtp") as f:
            res = f.read(100)

        assert res.startswith('<?xml version="1.0"?>\n<VTKFile')

    def testDXF(self):

        exporters.export(self._box().section(), "out.dxf")

        with self.assertRaises(ValueError):
            exporters.export(self._box().val(), "out.dxf")

        s1 = (
            Workplane("XZ")
            .polygon(10, 10)
            .ellipse(1, 2)
            .extrude(1)
            .edges("|Y")
            .fillet(1)
            .section()
        )
        exporters.dxf.exportDXF(s1, "res1.dxf")

        s1_i = importers.importDXF("res1.dxf")

        self.assertAlmostEqual(s1.val().Area(), s1_i.val().Area(), 6)
        self.assertAlmostEqual(s1.edges().size(), s1_i.edges().size())

        pts = [(0, 0), (0, 0.5), (1, 1)]
        s2 = (
            Workplane().spline(pts).close().extrude(1).edges("|Z").fillet(0.1).section()
        )
        exporters.dxf.exportDXF(s2, "res2.dxf")

        s2_i = importers.importDXF("res2.dxf")

        self.assertAlmostEqual(s2.val().Area(), s2_i.val().Area(), 6)
        self.assertAlmostEqual(s2.edges().size(), s2_i.edges().size())

        s3 = (
            Workplane("XY")
            .ellipseArc(1, 2, 0, 180)
            .close()
            .extrude(1)
            .edges("|Z")
            .fillet(0.1)
            .section()
        )
        exporters.dxf.exportDXF(s3, "res3.dxf")

        s3_i = importers.importDXF("res3.dxf")

        self.assertAlmostEqual(s3.val().Area(), s3_i.val().Area(), 6)
        self.assertAlmostEqual(s3.edges().size(), s3_i.edges().size())

        cyl = Workplane("XY").circle(22).extrude(10, both=True).translate((-50, 0, 0))

        s4 = Workplane("XY").box(80, 60, 5).cut(cyl).section()

        exporters.dxf.exportDXF(s4, "res4.dxf")

        s4_i = importers.importDXF("res4.dxf")

        self.assertAlmostEqual(s4.val().Area(), s4_i.val().Area(), 6)
        self.assertAlmostEqual(s4.edges().size(), s4_i.edges().size())

        # test periodic spline
        w = Workplane().spline([(1, 1), (2, 2), (3, 2), (3, 1)], periodic=True)
        exporters.dxf.exportDXF(w, "res5.dxf")

        w_i = importers.importDXF("res5.dxf")

        self.assertAlmostEqual(w.val().Length(), w_i.wires().val().Length(), 6)

        # test rational spline
        c = Edge.makeCircle(1)
        adaptor = c._geomAdaptor()
        curve = GeomConvert.CurveToBSplineCurve_s(adaptor.Curve().Curve())

        e = Workplane().add(Edge(BRepBuilderAPI_MakeEdge(curve).Shape()))
        exporters.dxf.exportDXF(e, "res6.dxf")

        e_i = importers.importDXF("res6.dxf")

        self.assertAlmostEqual(e.val().Length(), e_i.wires().val().Length(), 6)

        # test non-planar section
        s5 = (
            Workplane()
            .spline([(0, 0), (1, 0), (1, 1), (0, 1)])
            .close()
            .extrude(1, both=True)
            .translate((-3, -4, 0))
        )

        s5.plane = Plane(origin=(0, 0.1, 0.5), normal=(0.05, 0.05, 1))
        s5 = s5.section()
        exporters.dxf.exportDXF(s5, "res7.dxf")

        s5_i = importers.importDXF("res7.dxf")

        self.assertAlmostEqual(s5.val().Area(), s5_i.val().Area(), 4)

    def testTypeHandling(self):

        with self.assertRaises(ValueError):
            exporters.export(self._box(), "out.random")

        with self.assertRaises(ValueError):
            exporters.export(self._box(), "out.stl", "STP")


@pytest.mark.parametrize(
    "id, opt, matchvals",
    [
        (0, {"ascii": True}, ["solid", "facet normal"]),
        (1, {"ASCII": True}, ["solid", "facet normal"]),
        (2, {"unknown_opt": 1, "ascii": True}, ["solid", "facet normal"]),
        (3, {"ASCII": False, "ascii": True}, ["solid", "facet normal"]),
    ],
)
def test_stl_ascii(tmpdir, box123, id, opt, matchvals):
    """
    :param tmpdir: temporary directory fixture
    :param box123: box fixture
    :param id: The index or id; output filename is <test name>_<id>.stl
    :param opt: The export opt dict
    :param matchval: List of strings to match at start of file
    """

    fpath = tmpdir.joinpath(f"stl_ascii_{id}.stl").resolve()
    assert not fpath.exists()

    assert matchvals

    exporters.export(box123, str(fpath), None, 0.1, 0.1, opt)

    with open(fpath, "r") as f:
        for i, line in enumerate(f):
            if i > len(matchvals) - 1:
                break
            assert line.find(matchvals[i]) > -1


@pytest.mark.parametrize(
    "id, opt, matchval",
    [
        (0, None, b"STL Exported by Open CASCADE"),
        (1, {"ascii": False}, b"STL Exported by Open CASCADE"),
        (2, {"ASCII": False}, b"STL Exported by Open CASCADE"),
        (3, {"unknown_opt": 1}, b"STL Exported by Open CASCADE"),
        (4, {"unknown_opt": 1, "ascii": False}, b"STL Exported by Open CASCADE"),
    ],
)
def test_stl_binary(tmpdir, box123, id, opt, matchval):
    """
    :param tmpdir: temporary directory fixture
    :param box123: box fixture
    :param id: The index or id; output filename is <test name>_<id>.stl
    :param opt: The export opt dict
    :param matchval: Check that the file starts with the specified value
    """

    fpath = tmpdir.joinpath(f"stl_binary_{id}.stl").resolve()
    assert not fpath.exists()

    assert matchval

    exporters.export(box123, str(fpath), None, 0.1, 0.1, opt)

    with open(fpath, "rb") as f:
        r = f.read(len(matchval))
        assert r == matchval


def test_assy_vtk_rotation(tmpdir):

    v0 = Vertex.makeVertex(1, 0, 0)

    assy = Assembly()
    assy.add(
        v0, name="v0", loc=Location(Vector(0, 0, 0), Vector(1, 0, 0), 90),
    )

    fwrl = Path(tmpdir, "v0.wrl")
    assert not fwrl.exists()
    assy.save(str(fwrl), "VRML")
    assert fwrl.exists()

    matched_rot = False
    with open(fwrl) as f:
        pat_rot = re.compile("""rotation 1 0 0 1.5707963267""")
        for line in f:
            if m := re.search(pat_rot, line):
                matched_rot = True
                break

    assert matched_rot


def test_tessellate(box123):

    verts, triangles = box123.val().tessellate(1e-6)
    assert len(verts) == 24
    assert len(triangles) == 12


def _dxf_spline_max_degree(fname):

    dxf = ezdxf.readfile(fname)
    msp = dxf.modelspace()

    rv = 0

    for el in msp:
        if isinstance(el, ezdxf.entities.Spline):
            rv = el.dxf.degree if el.dxf.degree > rv else rv

    return rv


def _check_dxf_no_spline(fname):

    dxf = ezdxf.readfile(fname)
    msp = dxf.modelspace()

    for el in msp:
        if isinstance(el, ezdxf.entities.Spline):
            return False

    return True


def test_dxf_approx():

    pts = [(0, 0), (0, 0.5), (1, 1)]
    w1 = Workplane().spline(pts).close().extrude(1).edges("|Z").fillet(0.1).section()
    exporters.exportDXF(w1, "orig.dxf")

    assert _dxf_spline_max_degree("orig.dxf") == 6

    exporters.exportDXF(w1, "limit1.dxf", approx="spline")
    w1_i1 = importers.importDXF("limit1.dxf")

    assert _dxf_spline_max_degree("limit1.dxf") == 3

    assert w1.val().Area() == approx(w1_i1.val().Area(), 1e-3)
    assert w1.edges().size() == w1_i1.edges().size()

    exporters.exportDXF(w1, "limit2.dxf", approx="arc")
    w1_i2 = importers.importDXF("limit2.dxf")

    assert _check_dxf_no_spline("limit2.dxf")

    assert w1.val().Area() == approx(w1_i2.val().Area(), 1e-3)


def test_dxf_text(tmpdir, testdatadir):

    w1 = (
        Workplane("XZ")
        .box(8, 8, 1)
        .faces("<Y")
        .workplane()
        .text(
            ",,", 10, -1, True, fontPath=str(Path(testdatadir, "OpenSans-Regular.ttf")),
        )
    )

    fname = tmpdir.joinpath(f"dxf_text.dxf").resolve()
    exporters.exportDXF(w1.section(), fname)

    s2 = Sketch().importDXF(fname)
    w2 = Workplane("XZ", origin=(0, -0.5, 0)).placeSketch(s2).extrude(-1)

    assert w1.val().Volume() == approx(61.669465, 1e-2)
    assert w2.val().Volume() == approx(w1.val().Volume(), 1e-2)
    assert w2.intersect(w1).val().Volume() == approx(w1.val().Volume(), 1e-2)


def test_dxf_ellipse_arc(tmpdir):

    normal = (0, 1, 0)
    plane = Plane((0, 0, 0), (1, 0, 0), normal=normal)
    w1 = Workplane(plane)

    r = 10
    normal_reversed = (0, -1, 0)
    e1 = Edge.makeEllipse(r, r, (0, 0, 0), normal_reversed, (1, 0, 1), 90, 135)
    e2 = Edge.makeEllipse(r, r, (0, 0, 0), normal, (0, 0, -1), 45, 90)
    e3 = Edge.makeLine(
        (0, 0, 0), (-r * math.sin(math.pi / 4), 0, r * math.sin(math.pi / 4))
    )
    e4 = Edge.makeLine(
        (0, 0, 0), (-r * math.sin(math.pi / 4), 0, -r * math.sin(math.pi / 4))
    )

    w1.add([e1, e2, e3, e4])

    dxf = exporters.dxf.DxfDocument()
    dxf.add_layer("layer1", color=1)
    dxf.add_shape(w1, "layer1")
    fname = tmpdir.joinpath("ellipse_arc.dxf").resolve()
    dxf.document.saveas(fname)

    s1 = Sketch().importDXF(fname)
    w2 = Workplane("XZ", origin=(0, 0, 0)).placeSketch(s1).extrude(1)

    assert w2.val().isValid()
    assert w2.val().Volume() == approx(math.pi * r ** 2 / 4)
