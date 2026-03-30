"""
    Tests file importers such as STEP
"""
# core modules
import tempfile
import os

from cadquery import importers, Workplane, Compound
from tests import BaseTest
from pytest import approx, raises

# where unit test output will be saved
OUTDIR = tempfile.gettempdir()

# test data directory
testdataDir = os.path.join(os.path.dirname(__file__), "testdata")


class TestImporters(BaseTest):
    def importBox(self, importType, fileName):
        """
        Exports a simple box and then imports it again
        :param importType: The type of file we're importing (STEP, STL, etc)
        :param fileName: The path and name of the file to write to
        """
        # We first need to build a simple shape to export
        shape = Workplane("XY").box(1, 2, 3).val()

        if importType == importers.ImportTypes.STEP:
            # Export the shape to a temporary file
            shape.exportStep(fileName)
        elif importType == importers.ImportTypes.BREP:
            shape.exportBrep(fileName)
        elif importType == importers.ImportTypes.BIN:
            shape.exportBin(fileName)

        # Reimport the shape from the new file
        importedShape = importers.importShape(importType, fileName)

        # Check to make sure we got a single solid back.
        self.assertTrue(importedShape.val().isValid())
        self.assertEqual(importedShape.val().ShapeType(), "Solid")
        self.assertEqual(len(importedShape.objects), 1)

        # Check the number of faces and vertices per face to make sure we have a
        # box shape.
        self.assertNFacesAndNVertices(importedShape, (1, 1, 1), (4, 4, 4))
        # Check that the volume is correct.
        self.assertAlmostEqual(importedShape.findSolid().Volume(), 6)

    def importCompound(self, importType, fileName):
        """
        Exports a "+" shaped compound box and then imports it again.
        :param importType: The type of file we're importing (STEP, STL, etc)
        :param fileName: The path and name of the file to write to
        """
        # We first need to build a simple shape to export
        b1 = Workplane("XY").box(1, 2, 3).val()
        b2 = Workplane("XZ").box(1, 2, 3).val()
        shape = Compound.makeCompound([b1, b2])

        if importType == importers.ImportTypes.STEP:
            # Export the shape to a temporary file
            shape.exportStep(fileName)
        elif importType == importers.ImportTypes.BREP:
            shape.exportBrep(fileName)
        elif importType == importers.ImportTypes.BIN:
            shape.exportBin(fileName)

        # Reimport the shape from the new file
        importedShape = importers.importShape(importType, fileName)

        # Check to make sure we got the shapes we expected.
        self.assertTrue(importedShape.val().isValid())
        self.assertEqual(importedShape.val().ShapeType(), "Compound")
        self.assertEqual(len(importedShape.objects), 1)

        # Check the number of faces and vertices per face to make sure we have
        # two boxes.
        self.assertNFacesAndNVertices(importedShape, (2, 2, 2), (8, 8, 8))

        # Check that the volume is the independent sum of the two boxes' 6mm^2
        # volumes.
        self.assertAlmostEqual(importedShape.findSolid().Volume(), 12)

        # Join the boxes together and ensure that they are geometrically where
        # we expected them to be. This should be a workplane containing a
        # compound composed of a single Solid.
        fusedShape = Workplane("XY").newObject(importedShape.val().fuse())

        # Check to make sure we got a valid shape
        self.assertTrue(fusedShape.val().isValid())

        # Check the number of faces and vertices per face to make sure we have
        # two boxes.
        self.assertNFacesAndNVertices(fusedShape, (5, 3, 3), (12, 12, 12))

        # Check that the volume accounts for the overlap of the two shapes.
        self.assertAlmostEqual(fusedShape.findSolid().Volume(), 8)

    def assertNFacesAndNVertices(self, workplane, nFacesXYZ, nVerticesXYZ):
        """
        Checks that the workplane has the number of faces and vertices expected
        in X, Y, and Z.
        :param workplane: The workplane to assess.
        :param nFacesXYZ: The number of faces expected in +X, +Y, and +Z planes.
        :param nVerticesXYZ: The number of vertices expected in +X, +Y, and +Z planes.
        """
        nFacesX, nFacesY, nFacesZ = nFacesXYZ
        nVerticesX, nVerticesY, nVerticesZ = nVerticesXYZ

        self.assertEqual(workplane.faces("+X").size(), nFacesX)
        self.assertEqual(workplane.faces("+X").vertices().size(), nVerticesX)

        self.assertEqual(workplane.faces("+Y").size(), nFacesY)
        self.assertEqual(workplane.faces("+Y").vertices().size(), nVerticesY)

        self.assertEqual(workplane.faces("+Z").size(), nFacesZ)
        self.assertEqual(workplane.faces("+Z").vertices().size(), nVerticesZ)

    def testInvalidImportTypeRaisesRuntimeError(self):
        fileName = os.path.join(OUTDIR, "tempSTEP.step")
        shape = Workplane("XY").box(1, 2, 3).val()
        shape.exportStep(fileName)
        self.assertRaises(RuntimeError, importers.importShape, "INVALID", fileName)

    def testBREP(self):
        """
        Test BREP file import.
        """
        self.importBox(
            importers.ImportTypes.BREP, os.path.join(OUTDIR, "tempBREP.brep")
        )
        self.importCompound(
            importers.ImportTypes.BREP, os.path.join(OUTDIR, "tempBREP.brep")
        )

    def testBIN(self):
        """
        Test binary BREP file import.
        """
        self.importBox(importers.ImportTypes.BIN, os.path.join(OUTDIR, "tempBIN.bin"))
        self.importCompound(
            importers.ImportTypes.BIN, os.path.join(OUTDIR, "tempBIN.bin")
        )

    def testSTEP(self):
        """
        Tests STEP file import
        """
        self.importBox(
            importers.ImportTypes.STEP, os.path.join(OUTDIR, "tempSTEP.step")
        )
        self.importCompound(
            importers.ImportTypes.STEP, os.path.join(OUTDIR, "tempSTEP.step")
        )

    def testInvalidSTEP(self):
        """
        Attempting to load an invalid STEP file should throw an exception, but
        not segfault.
        """
        tmpfile = os.path.join(OUTDIR, "badSTEP.step")
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

    def testSTEPImportUnitDefault(self):
        """
        Exports and re-imports a STEP file with the default unit (MM) and
        verifies the shape geometry is unchanged.
        """

        fileName = os.path.join(OUTDIR, "unit_default_import.step")
        shape = Workplane("XY").box(1, 2, 3).val()
        shape.exportStep(fileName)

        imported = importers.importStep(fileName, unit="MM")
        self.assertTrue(imported.val().isValid())
        self.assertAlmostEqual(imported.findSolid().Volume(), 6)

    def testSTEPImportUnitOverride(self):
        """
        Exports a 1x1x1 box as MM and re-imports it with unit="M" to verify
        whether read.step.unit overrides the unit declared in the STEP header.
        If it overrides, the box will be 500x500x500 (0.5 treated as meters).
        If it only applies as a fallback, the box will remain 1x1x1.
        """

        mm_path = os.path.join(OUTDIR, "unit_override_test.step")
        Workplane().box(1, 1, 1).val().exportStep(mm_path)

        imported = importers.importStep(mm_path, unit="M")
        bb = imported.val().BoundingBox()

        assert bb.xlen == approx(1.0, rel=1e-3)
        assert bb.ylen == approx(1.0, rel=1e-3)

    def testSTEPImportUnitViaImportShape(self):
        """
        Verifies that the unit parameter is correctly threaded through
        importShape to importStep.
        """

        fileName = os.path.join(OUTDIR, "unit_importshape.step")
        shape = Workplane("XY").box(1, 2, 3).val()
        shape.exportStep(fileName)

        imported = importers.importShape(
            importers.ImportTypes.STEP, fileName, unit="MM"
        )
        self.assertTrue(imported.val().isValid())
        self.assertAlmostEqual(imported.findSolid().Volume(), 6)

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

        obj = importers.importDXF(filename, include=["Layer2"])
        assert obj.vertices("<XY").val().toTuple() == approx(
            (104.2871791623584, 0.0038725018551133, 0.0)
        )

        obj = importers.importDXF(filename, include=["Layer2", "Layer3"])
        assert obj.vertices("<XY").val().toTuple() == approx(
            (104.2871791623584, 0.0038725018551133, 0.0)
        )
        assert obj.vertices(">XY").val().toTuple() == approx(
            (257.6544359816229, 93.62447646419444, 0.0)
        )

        with raises(ValueError):
            importers.importDXF(filename, include=["Layer1"], exclude=["Layer3"])

        with raises(ValueError):
            # Layer4 does not exist
            importers.importDXF(filename, include=["Layer4"])

        # test dxf extrusion into the third dimension
        extrusion_value = 15.0
        tmp = obj.wires()
        tmp.ctx.pendingWires = tmp.vals()
        threed = tmp.extrude(extrusion_value)
        self.assertEqual(threed.findSolid().BoundingBox().zlen, extrusion_value)


if __name__ == "__main__":
    import unittest

    unittest.main()
