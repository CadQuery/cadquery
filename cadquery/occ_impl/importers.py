from collections import OrderedDict
from math import pi

from .. import cq
from .geom import Vector
from .shapes import Shape, Edge, Face, sortWiresByBuildOrder, DEG2RAD

import ezdxf

from OCP.STEPControl import STEPControl_Reader
from OCP.ShapeAnalysis import ShapeAnalysis_FreeBounds
from OCP.TopTools import TopTools_HSequenceOfShape
from OCP.gp import gp_Pnt
from OCP.Geom import Geom_BSplineCurve
from OCP.TColgp import TColgp_Array1OfPnt
from OCP.TColStd import TColStd_Array1OfReal, TColStd_Array1OfInteger
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeEdge


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


def _dxf_line(el):

    try:
        return (Edge.makeLine(Vector(el.dxf.start.xyz), Vector(el.dxf.end.xyz)),)
    except Exception:
        return ()


def _dxf_circle(el):

    try:
        return (Edge.makeCircle(el.dxf.radius, Vector(el.dxf.center.xyz)),)
    except Exception:
        return ()


def _dxf_arc(el):

    try:
        return (
            Edge.makeCircle(
                el.dxf.radius,
                Vector(el.dxf.center.xyz),
                angle1=el.dxf.start_angle,
                angle2=el.dxf.end_angle,
            ),
        )
    except Exception:
        return ()


def _dxf_polyline(el):

    rv = (DXF_CONVERTERS[e.dxf.dxftype](e) for e in el.virtual_entities())

    return (e[0] for e in rv if e)


def _dxf_spline(el):

    try:
        degree = el.dxf.degree
        periodic = el.closed
        rational = False

        knots_unique = OrderedDict()
        for k in el.knots:
            if k in knots_unique:
                knots_unique[k] += 1
            else:
                knots_unique[k] = 1

        # assmble knots
        knots = TColStd_Array1OfReal(1, len(knots_unique))
        multiplicities = TColStd_Array1OfInteger(1, len(knots_unique))
        for i, (k, m) in enumerate(knots_unique.items()):
            knots.SetValue(i + 1, k)
            multiplicities.SetValue(i + 1, m)

        # assemble wieghts if present:
        if el.weights:
            rational = True

            weights = OCP.TColStd.TColStd_Array1OfReal(1, len(el.weights))
            for i, w in enumerate(el.weights):
                weights.SetValue(i + 1, w)

        # assmeble conotrol points
        pts = TColgp_Array1OfPnt(1, len(el.control_points))
        for i, p in enumerate(el.control_points):
            pts.SetValue(i + 1, gp_Pnt(*p))

        if rational:
            spline = Geom_BSplineCurve(
                pts, weights, knots, multiplicities, degree, periodic
            )
        else:
            spline = Geom_BSplineCurve(pts, knots, multiplicities, degree, periodic)

        return (Edge(BRepBuilderAPI_MakeEdge(spline).Edge()),)

    except Exception:
        return ()


def _dxf_ellipse(el):

    try:

        return (
            Edge.makeEllipse(
                el.dxf.major_axis.magnitude,
                el.minor_axis.magnitude,
                pnt=Vector(el.dxf.center.xyz),
                xdir=Vector(el.dxf.major_axis.xyz),
                angle1=el.dxf.start_param * RAD2DEG,
                angle2=el.dxf.end_param * RAD2DEG,
            ),
        )
    except Exception:
        return ()


DXF_CONVERTERS = {
    "LINE": _dxf_line,
    "CIRCLE": _dxf_circle,
    "ARC": _dxf_arc,
    "POLYLINE": _dxf_polyline,
    "LWPOLYLINE": _dxf_polyline,
    "SPLINE": _dxf_spline,
    "ELLIPSE": _dxf_ellipse,
}


def _dxf_convert(elements, tol):

    rv = []
    edges = []

    for el in elements:
        conv = DXF_CONVERTERS.get(el.dxf.dxftype)
        if conv:
            edges.extend(conv(el))

    if edges:
        edges_in = TopTools_HSequenceOfShape()
        wires_out = TopTools_HSequenceOfShape()

        for e in edges:
            edges_in.Append(e.wrapped)
        ShapeAnalysis_FreeBounds.ConnectEdgesToWires_s(edges_in, tol, False, wires_out)

        rv = [Shape.cast(el) for el in wires_out]

    return rv


def importDXF(filename, tol=1e-6, exclude=[]):
    """
    Loads a DXF file into a cadquery Workplane.
    
    :param fileName: The path and name of the DXF file to be imported
    :param tol: The tolerance used for merging edges into wires (default: 1e-6)
    :param exclude: a list of layer names not to import (default: [])
    """

    dxf = ezdxf.readfile(filename)
    faces = []

    for name, layer in dxf.modelspace().groupby(dxfattrib="layer").items():
        res = _dxf_convert(layer, tol) if name not in exclude else None
        if res:
            wire_sets = sortWiresByBuildOrder(res)
            for wire_set in wire_sets:
                faces.append(Face.makeFromWires(wire_set[0], wire_set[1:]))

    return cq.Workplane("XY").newObject(faces)
