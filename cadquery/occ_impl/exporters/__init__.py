import tempfile
import os
import io as StringIO

from typing import IO, Optional, Union, cast
from typing_extensions import Literal

from ...cq import Workplane
from ..shapes import Shape

from .svg import getSVG
from .json import JsonMesh
from .amf import AmfWriter
from .dxf import exportDXF
from .utils import toCompound


class ExportTypes:
    STL = "STL"
    STEP = "STEP"
    AMF = "AMF"
    SVG = "SVG"
    TJS = "TJS"
    DXF = "DXF"


ExportLiterals = Literal["STL", "STEP", "AMF", "SVG", "TJS", "DXF"]


def export(
    w: Union[Shape, Workplane],
    fname: str,
    exportType: Optional[ExportLiterals] = None,
    tolerance: float = 0.1,
):

    shape: Shape
    if isinstance(w, Workplane):
        shape = toCompound(w)
    else:
        shape = w

    if exportType is None:
        t = fname.split(".")[-1].upper()
        if t in ExportTypes.__dict__.values():
            exportType = cast(ExportLiterals, t)
        else:
            raise ValueError("Unknown extensions, specify export type explicitly")

    if exportType == ExportTypes.TJS:
        tess = shape.tessellate(tolerance)
        mesher = JsonMesh()

        # add vertices
        for v in tess[0]:
            mesher.addVertex(v.x, v.y, v.z)

        # add triangles
        for ixs in tess[1]:
            mesher.addTriangleFace(*ixs)

        with open(fname) as f:
            f.write(mesher.toJson())

    elif exportType == ExportTypes.SVG:
        with open(fname) as f:
            f.write(getSVG(shape))

    elif exportType == ExportTypes.AMF:
        tess = shape.tessellate(tolerance)
        aw = AmfWriter(tess)
        with open(fname) as f:
            aw.writeAmf(f)

    elif exportType == ExportTypes.DXF:
        if isinstance(w, Workplane):
            exportDXF(w, fname)
        else:
            raise ValueError("Only Workplanes can be exported as DXF")

    elif exportType == ExportTypes.STEP:
        shape.exportStep(fname)

    elif exportType == ExportTypes.STL:
        shape.exportStl(fname, tolerance)


def toString(shape, exportType, tolerance=0.1):
    s = StringIO.StringIO()
    exportShape(shape, exportType, s, tolerance)
    return s.getvalue()


def exportShape(
    w: Union[Shape, Workplane],
    exportType: ExportLiterals,
    fileLike: IO,
    tolerance: float = 0.1,
):
    """
        :param shape:  the shape to export. it can be a shape object, or a cadquery object. If a cadquery
        object, the first value is exported
        :param exportFormat: the exportFormat to use
        :param tolerance: the tolerance, in model units
        :param fileLike: a file like object to which the content will be written.
        The object should be already open and ready to write. The caller is responsible
        for closing the object
    """

    def tessellate(shape):

        return shape.tessellate(tolerance)

    shape: Shape
    if isinstance(w, Workplane):
        shape = toCompound(w)
    else:
        shape = w

    if exportType == ExportTypes.TJS:
        tess = tessellate(shape)
        mesher = JsonMesh()

        # add vertices
        for v in tess[0]:
            mesher.addVertex(v.x, v.y, v.z)

        # add triangles
        for t in tess[1]:
            mesher.addTriangleFace(*t)

        fileLike.write(mesher.toJson())

    elif exportType == ExportTypes.SVG:
        fileLike.write(getSVG(shape))
    elif exportType == ExportTypes.AMF:
        tess = tessellate(shape)
        aw = AmfWriter(tess)
        aw.writeAmf(fileLike)
    else:

        # all these types required writing to a file and then
        # re-reading. this is due to the fact that FreeCAD writes these
        (h, outFileName) = tempfile.mkstemp()
        # weird, but we need to close this file. the next step is going to write to
        # it from c code, so it needs to be closed.
        os.close(h)

        if exportType == ExportTypes.STEP:
            shape.exportStep(outFileName)
        elif exportType == ExportTypes.STL:
            shape.exportStl(outFileName, tolerance)
        else:
            raise ValueError("No idea how i got here")

        res = readAndDeleteFile(outFileName)
        fileLike.write(res)


def readAndDeleteFile(fileName):
    """
        read data from file provided, and delete it when done
        return the contents as a string
    """
    res = ""
    with open(fileName, "r") as f:
        res = "{}".format(f.read())

    os.remove(fileName)
    return res
