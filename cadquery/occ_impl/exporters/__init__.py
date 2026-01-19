import tempfile
import os
import io as StringIO

from typing import IO, Optional, Union, cast, Dict, Any, Iterable
from typing_extensions import Literal

from OCP.VrmlAPI import VrmlAPI

from ...utils import deprecate
from ..shapes import Shape, compound

from .svg import getSVG
from .json import JsonMesh
from .amf import AmfWriter
from .threemf import ThreeMFWriter
from .dxf import exportDXF, DxfDocument
from .vtk import exportVTP


class ExportTypes:
    STL = "STL"
    STEP = "STEP"
    AMF = "AMF"
    SVG = "SVG"
    TJS = "TJS"
    DXF = "DXF"
    VRML = "VRML"
    VTP = "VTP"
    THREEMF = "3MF"
    BREP = "BREP"
    BIN = "BIN"


ExportLiterals = Literal[
    "STL", "STEP", "AMF", "SVG", "TJS", "DXF", "VRML", "VTP", "3MF", "BREP", "BIN"
]


def export(
    w: Union[Shape, Iterable[Shape]],
    fname: str,
    exportType: Optional[ExportLiterals] = None,
    tolerance: float = 0.1,
    angularTolerance: float = 0.1,
    opt: Optional[Dict[str, Any]] = None,
):

    """
    Export Workplane or Shape to file. Multiple entities are converted to compound.

    :param w:  Shape or Iterable[Shape] (e.g. Workplane) to be exported.
    :param fname: output filename.
    :param exportType: the exportFormat to use. If None will be inferred from the extension. Default: None.
    :param tolerance: the deflection tolerance, in model units. Default 0.1.
    :param angularTolerance: the angular tolerance, in radians. Default 0.1.
    :param opt: additional options passed to the specific exporter. Default None.
    """

    shape: Shape
    f: IO

    if not opt:
        opt = {}

    if isinstance(w, Shape):
        shape = w
    else:
        shape = compound(*w)

    if exportType is None:
        t = fname.split(".")[-1].upper()
        if t in ExportTypes.__dict__.values():
            exportType = cast(ExportLiterals, t)
        else:
            raise ValueError("Unknown extensions, specify export type explicitly")

    if exportType == ExportTypes.TJS:
        tess = shape.tessellate(tolerance, angularTolerance)
        mesher = JsonMesh()

        # add vertices
        for v in tess[0]:
            mesher.addVertex(v.x, v.y, v.z)

        # add triangles
        for ixs in tess[1]:
            mesher.addTriangleFace(*ixs)

        with open(fname, "w") as f:
            f.write(mesher.toJson())

    elif exportType == ExportTypes.SVG:
        with open(fname, "w") as f:
            f.write(getSVG(shape, opt))

    elif exportType == ExportTypes.AMF:
        tess = shape.tessellate(tolerance, angularTolerance)
        aw = AmfWriter(tess)
        with open(fname, "wb") as f:
            aw.writeAmf(f)

    elif exportType == ExportTypes.THREEMF:
        tmfw = ThreeMFWriter(shape, tolerance, angularTolerance, **opt)
        with open(fname, "wb") as f:
            tmfw.write3mf(f)

    elif exportType == ExportTypes.DXF:
        exportDXF(w, fname, **opt)

    elif exportType == ExportTypes.STEP:
        shape.exportStep(fname, **opt)

    elif exportType == ExportTypes.STL:
        if opt:
            useascii = opt.get("ascii", False) or opt.get("ASCII", False)
        else:
            useascii = False

        shape.exportStl(fname, tolerance, angularTolerance, useascii)

    elif exportType == ExportTypes.VRML:
        shape.mesh(tolerance, angularTolerance)
        VrmlAPI.Write_s(shape.wrapped, fname)

    elif exportType == ExportTypes.VTP:
        exportVTP(shape, fname, tolerance, angularTolerance)

    elif exportType == ExportTypes.BREP:
        shape.exportBrep(fname)

    elif exportType == ExportTypes.BIN:
        shape.exportBin(fname)

    else:
        raise ValueError("Unknown export type")
