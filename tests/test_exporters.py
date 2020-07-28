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
    def _exportBox(self, eType, stringsToFind):
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

        exporters.exportShape(p, eType, s, 0.1)

        result = "{}".format(s.getvalue())

        for q in stringsToFind:
            self.assertTrue(result.find(q) > -1)
        return result

    def testSTL(self):
        self._exportBox(exporters.ExportTypes.STL, ["facet normal"])

    def testSVG(self):
        self._exportBox(exporters.ExportTypes.SVG, ["<svg", "<g transform"])

    def testAMF(self):
        self._exportBox(exporters.ExportTypes.AMF, ["<amf units", "</object>"])

    def testSTEP(self):
        self._exportBox(exporters.ExportTypes.STEP, ["FILE_SCHEMA"])

    def testTJS(self):
        self._exportBox(
            exporters.ExportTypes.TJS, ["vertices", "formatVersion", "faces"]
        )

    def testDXF(self):

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

        self.assertAlmostEquals(s1.val().Area(), s1_i.val().Area(), 6)
        self.assertAlmostEquals(s1.edges().size(), s1_i.edges().size())

        pts = [(0, 0), (0, 0.5), (1, 1)]
        s2 = (
            Workplane().spline(pts).close().extrude(1).edges("|Z").fillet(0.1).section()
        )
        exporters.dxf.exportDXF(s2, "res2.dxf")

        s2_i = importers.importDXF("res2.dxf")

        self.assertAlmostEquals(s2.val().Area(), s2_i.val().Area(), 6)
        self.assertAlmostEquals(s2.edges().size(), s2_i.edges().size())

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

        self.assertAlmostEquals(s3.val().Area(), s3_i.val().Area(), 6)
        self.assertAlmostEquals(s3.edges().size(), s3_i.edges().size())
