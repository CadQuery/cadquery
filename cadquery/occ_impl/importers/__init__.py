from math import pi
from typing import List, Literal
from pathlib import Path

import OCP.IFSelect
from OCP.STEPControl import STEPControl_Reader

from ... import cq
from ..shapes import Shape
from .dxf import _importDXF

RAD2DEG = 360.0 / (2 * pi)


class ImportTypes:
    STEP = "STEP"
    DXF = "DXF"
    BREP = "BREP"
    BIN = "BIN"


class UNITS:
    MM = "mm"
    IN = "in"


def importShape(
    importType: Literal["STEP", "DXF", "BREP", "BIN"],
    fileName: Path | str,
    *args,
    **kwargs
) -> "cq.Workplane":
    """
    Imports a file based on the type (STEP, STL, etc)

    :param importType: The type of file that we're importing
    :param fileName: The name of the file that we're importing
    """
    if isinstance(fileName, str):
        fileName = Path(fileName)

    # Check to see what type of file we're working with
    if importType == ImportTypes.STEP:
        return importStep(fileName)
    elif importType == ImportTypes.DXF:
        return importDXF(fileName, *args, **kwargs)
    elif importType == ImportTypes.BREP:
        return importBrep(fileName)
    elif importType == ImportTypes.BIN:
        return importBin(fileName)
    else:
        raise RuntimeError("Unsupported import type: {!r}".format(importType))


def importBrep(fileName: Path | str) -> "cq.Workplane":
    """
    Loads the BREP file as a single shape into a cadquery Workplane.

    :param fileName: The path and name of the BREP file to be imported

    """
    if isinstance(fileName, str):
        fileName = Path(fileName)

    shape = Shape.importBrep(fileName)

    # We know a single shape is returned. Sending it as a list prevents
    # newObject from decomposing the part into its constituent parts. If the
    # shape is a compound, it will be stored as a compound on the workplane. In
    # some cases it may be desirable for the compound to be broken into its
    # constituent solids. To do this, use list(shape) or shape.Solids().
    return cq.Workplane("XY").newObject([shape])


def importBin(fileName: Path | str) -> "cq.Workplane":
    """
    Loads the binary BREP file as a single shape into a cadquery Workplane.

    :param fileName: The path and name of the BREP file to be imported

    """
    if isinstance(fileName, str):
        fileName = Path(fileName)

    shape = Shape.importBin(fileName)

    return cq.Workplane("XY").newObject([shape])


# Loads a STEP file into a CQ.Workplane object
def importStep(fileName: Path | str) -> "cq.Workplane":
    """
    Accepts a file name and loads the STEP file into a cadquery Workplane

    :param fileName: The path and name of the STEP file to be imported
    """
    if isinstance(fileName, str):
        fileName = Path(fileName)

    # Now read and return the shape
    reader = STEPControl_Reader()
    readStatus = reader.ReadFile(str(fileName))
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


def importDXF(
    filename: Path | str,
    tol: float = 1e-6,
    exclude: List[str] = [],
    include: List[str] = [],
) -> "cq.Workplane":
    """
    Loads a DXF file into a Workplane.

    All layers are imported by default.  Provide a layer include or exclude list
    to select layers.  Layer names are handled as case-insensitive.

    :param filename: The path and name of the DXF file to be imported
    :param tol: The tolerance used for merging edges into wires
    :param exclude: a list of layer names not to import
    :param include: a list of layer names to import
    """
    if isinstance(filename, str):
        filename = Path(filename)

    faces = _importDXF(filename, tol, exclude, include)

    return cq.Workplane("XY").newObject(faces)
