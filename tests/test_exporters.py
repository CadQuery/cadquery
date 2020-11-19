"""
    Tests basic workplane functionality
"""
# core modules
import sys
import io

# my modules
from cadquery import *
from cadquery import exporters, importers
from tests import BaseTest


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

    def testTypeHandling(self):

        with self.assertRaises(ValueError):
            exporters.export(self._box(), "out.random")

        with self.assertRaises(ValueError):
            exporters.export(self._box(), "out.stl", "STP")
