"""
    Tests basic workplane functionality
"""
# core modules
import sys
import io
from pathlib import Path
import re

# my modules
from cadquery import *
from cadquery import exporters, importers
from tests import BaseTest
from OCP.GeomConvert import GeomConvert
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeEdge


class TestExporters(BaseTest):
    def _exportBox(self, eType, stringsToFind, tolerance=0.1, angularTolerance=0.1):
        """
        Exports a test object, and then looks for
        all of the supplied strings to be in the result
        returns the result in case the case wants to do more checks also
        """
        p = Workplane("XY").box(1, 2, 3)

        if eType == exporters.ExportTypes.AMF:
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
        self._exportBox(exporters.ExportTypes.STL, ["facet normal"])

        exporters.export(self._box(), "out.stl")

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
                "height": 100,
                "marginLeft": 10,
                "marginTop": 10,
                "showAxes": False,
                "projectionDir": (0, 0, 1),
                "strokeWidth": 0.25,
                "strokeColor": (255, 0, 0),
                "hiddenColor": (0, 0, 255),
                "showHidden": True,
            },
        )

    def testAMF(self):
        self._exportBox(exporters.ExportTypes.AMF, ["<amf units", "</object>"])

        exporters.export(self._box(), "out.amf")

    def testSTEP(self):
        self._exportBox(exporters.ExportTypes.STEP, ["FILE_SCHEMA"])

        exporters.export(self._box(), "out.step")

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


def test_assy_vtk_rotation(tmp_path_factory):
    tmpdir = tmp_path_factory.mktemp("out")

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
