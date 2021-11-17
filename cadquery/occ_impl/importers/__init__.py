from math import pi

from ... import cq
from ..shapes import Shape
from .dxf import _importDXF


from OCP.STEPControl import STEPControl_Reader

import OCP.IFSelect

RAD2DEG = 360.0 / (2 * pi)


class ImportTypes:
    STEP = "STEP"
    DXF = "DXF"


class UNITS:
    MM = "mm"
    IN = "in"


def importShape(importType, fileName, *args, **kwargs):
    """
    Imports a file based on the type (STEP, STL, etc)

    :param importType: The type of file that we're importing
    :param fileName: THe name of the file that we're importing
    """

    # Check to see what type of file we're working with
    if importType == ImportTypes.STEP:
        return importStep(fileName, *args, **kwargs)
    elif importType == ImportTypes.DXF:
        return importDXF(fileName, *args, **kwargs)
    else:
        raise RuntimeError("Unsupported import type: {!r}".format(importType))


# Loads a STEP file into a CQ.Workplane object
def importStep(fileName):
    """
    Accepts a file name and loads the STEP file into a cadquery Workplane

    :param fileName: The path and name of the STEP file to be imported
    """

    # Now read and return the shape
    reader = STEPControl_Reader()
    readStatus = reader.ReadFile(fileName)
    if readStatus != OCP.IFSelect.IFSelect_RetDone:
        raise ValueError("STEP File could not be loaded")
    for i in range(reader.NbRootsForTransfer()):
        reader.TransferRoot(i + 1)

    occ_shapes = []
    for i in range(reader.NbShapes()):
        occ_shapes.append(reader.Shape(i + 1))

    # Make sure that we extract all the solids
    solids = []
    for shape in occ_shapes:
        solids.append(Shape.cast(shape))

    return cq.Workplane("XY").newObject(solids)


def importDXF(filename, tol=1e-6, exclude=[]):
    """
    Loads a DXF file into a cadquery Workplane.

    :param fileName: The path and name of the DXF file to be imported
    :param tol: The tolerance used for merging edges into wires (default: 1e-6)
    :param exclude: a list of layer names not to import (default: [])
    """

    faces = _importDXF(filename, tol, exclude)

    return cq.Workplane("XY").newObject(faces)
