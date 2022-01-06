"""
    Tests file importers such as STEP
"""
# core modules
import tempfile
import os

from cadquery import importers, Workplane
from tests import BaseTest

# where unit test output will be saved
OUTDIR = tempfile.gettempdir()

# test data directory
testdataDir = os.path.join(os.path.dirname(__file__), "testdata")


class TestImporters(BaseTest):
    def importBox(self, importType, fileName):
        """
        Exports a simple box to a STEP file and then imports it again
        :param importType: The type of file we're importing (STEP, STL, etc)
        :param fileName: The path and name of the file to write to
        """
        # We're importing a STEP file
        if importType == importers.ImportTypes.STEP:
            # We first need to build a simple shape to export
            shape = Workplane("XY").box(1, 2, 3).val()

            # Export the shape to a temporary file
            shape.exportStep(fileName)

            # Reimport the shape from the new STEP file
            importedShape = importers.importShape(importType, fileName)

            # Check to make sure we got a solid back
            self.assertTrue(importedShape.val().ShapeType() == "Solid")

            # Check the number of faces and vertices per face to make sure we have a box shape
            self.assertTrue(
                importedShape.faces("+X").size() == 1
                and importedShape.faces("+X").vertices().size() == 4
            )
            self.assertTrue(
                importedShape.faces("+Y").size() == 1
                and importedShape.faces("+Y").vertices().size() == 4
            )
            self.assertTrue(
                importedShape.faces("+Z").size() == 1
                and importedShape.faces("+Z").vertices().size() == 4
            )

    def testSTEP(self):
        """
        Tests STEP file import
        """
        self.importBox(importers.ImportTypes.STEP, OUTDIR + "/tempSTEP.step")

    def testInvalidSTEP(self):
        """
        Attempting to load an invalid STEP file should throw an exception, but
        not segfault.
        """
        tmpfile = OUTDIR + "/badSTEP.step"
        with open(tmpfile, "w") as f:
            f.write("invalid STEP file")
        with self.assertRaises(ValueError):
            importers.importShape(importers.ImportTypes.STEP, tmpfile)

    def testImportMultipartSTEP(self):
        """
        Import a STEP file that contains two objects and ensure that both are
        loaded.
        """

        filename = os.path.join(testdataDir, "red_cube_blue_cylinder.step")
        objs = importers.importShape(importers.ImportTypes.STEP, filename)
        self.assertEqual(2, len(objs.all()))

    def testImportDXF(self):
        """
        Test DXF import with various tolerances.
        """

        filename = os.path.join(testdataDir, "gear.dxf")

        with self.assertRaises(ValueError):
            # tol >~ 2e-4 required for closed wires
            obj = importers.importDXF(filename)

        obj = importers.importDXF(filename, tol=1e-3)
        self.assertTrue(obj.val().isValid())
        self.assertEqual(obj.faces().size(), 1)
        self.assertEqual(obj.wires().size(), 2)

        obj = obj.wires().toPending().extrude(1)
        self.assertTrue(obj.val().isValid())
        self.assertEqual(obj.solids().size(), 1)

        obj = importers.importShape(importers.ImportTypes.DXF, filename, tol=1e-3)
        self.assertTrue(obj.val().isValid())

        # additional files to test more DXF entities

        filename = os.path.join(testdataDir, "MC 12x31.dxf")
        obj = importers.importDXF(filename)
        self.assertTrue(obj.val().isValid())

        filename = os.path.join(testdataDir, "1001.dxf")
        obj = importers.importDXF(filename)
        self.assertTrue(obj.val().isValid())

        # test spline import

        filename = os.path.join(testdataDir, "spline.dxf")
        obj = importers.importDXF(filename, tol=1)
        self.assertTrue(obj.val().isValid())
        self.assertEqual(obj.faces().size(), 1)
        self.assertEqual(obj.wires().size(), 2)

        # test rational spline import
        filename = os.path.join(testdataDir, "rational_spline.dxf")
        obj = importers.importDXF(filename)
        self.assertTrue(obj.val().isValid())
        self.assertEqual(obj.faces().size(), 1)
        self.assertEqual(obj.edges().size(), 1)

        # importing of a complex shape exported from Inkscape
        filename = os.path.join(testdataDir, "genshi.dxf")
        obj = importers.importDXF(filename)
        self.assertTrue(obj.val().isValid())
        self.assertEqual(obj.faces().size(), 1)

        # test layer filtering
        filename = os.path.join(testdataDir, "three_layers.dxf")
        obj = importers.importDXF(filename, exclude=["Layer2"])
        self.assertTrue(obj.val().isValid())
        self.assertEqual(obj.faces().size(), 2)
        self.assertEqual(obj.wires().size(), 2)

        # test dxf extrusion into the third dimension
        extrusion_value = 15.0
        tmp = obj.wires()
        tmp.ctx.pendingWires = tmp.vals()
        threed = tmp.extrude(extrusion_value)
        self.assertEqual(threed.findSolid().BoundingBox().zlen, extrusion_value)


if __name__ == "__main__":
    import unittest

    unittest.main()
