from collections import OrderedDict
from math import pi
from typing import List

from ... import cq
from ..geom import Vector
from ..shapes import Shape, Edge, Face, sortWiresByBuildOrder

import ezdxf

from OCP.ShapeAnalysis import ShapeAnalysis_FreeBounds
from OCP.TopTools import TopTools_HSequenceOfShape
from OCP.gp import gp_Pnt
from OCP.Geom import Geom_BSplineCurve
from OCP.TColgp import TColgp_Array1OfPnt
from OCP.TColStd import TColStd_Array1OfReal, TColStd_Array1OfInteger
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeEdge


RAD2DEG = 360.0 / (2 * pi)


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

        # assemble weights if present:
        if el.weights:
            rational = True

            weights = TColStd_Array1OfReal(1, len(el.weights))
            for i, w in enumerate(el.weights):
                weights.SetValue(i + 1, w)

        # assemble control points
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


def _importDXF(filename: str, tol: float = 1e-6, exclude: List[str] = []) -> List[Face]:
    """
    Loads a DXF file into a list of faces.

    :param fileName: The path and name of the DXF file to be imported
    :param tol: The tolerance used for merging edges into wires (default: 1e-6)
    :param exclude: a list of layer names not to import (default: [])
    """

    # normalize layer names to conform the DXF spec
    exclude_lwr = [ex.lower() for ex in exclude]

    dxf = ezdxf.readfile(filename)
    faces = []

    for name, layer in dxf.modelspace().groupby(dxfattrib="layer").items():
        res = _dxf_convert(layer, tol) if name.lower() not in exclude_lwr else None
        if res:
            wire_sets = sortWiresByBuildOrder(res)
            for wire_set in wire_sets:
                faces.append(Face.makeFromWires(wire_set[0], wire_set[1:]))

    return faces
