from ...cq import Workplane, Plane, Face
from ...units import RAD2DEG
from ..shapes import Edge
from .utils import toCompound

from OCP.gp import gp_Dir
from OCP.GeomConvert import GeomConvert

from typing import Optional, Literal

import ezdxf

CURVE_TOLERANCE = 1e-9


def _dxf_line(e: Edge, msp: ezdxf.layouts.Modelspace, plane: Plane):

    msp.add_line(
        e.startPoint().toTuple(), e.endPoint().toTuple(),
    )


def _dxf_circle(e: Edge, msp: ezdxf.layouts.Modelspace, plane: Plane):

    geom = e._geomAdaptor()
    circ = geom.Circle()

    r = circ.Radius()
    c = circ.Location()

    c_dy = circ.YAxis().Direction()
    c_dz = circ.Axis().Direction()

    dy = gp_Dir(0, 1, 0)

    phi = c_dy.AngleWithRef(dy, c_dz)

    if c_dz.XYZ().Z() > 0:
        a1 = RAD2DEG * (geom.FirstParameter() - phi)
        a2 = RAD2DEG * (geom.LastParameter() - phi)
    else:
        a1 = -RAD2DEG * (geom.LastParameter() - phi) + 180
        a2 = -RAD2DEG * (geom.FirstParameter() - phi) + 180

    if e.IsClosed():
        msp.add_circle((c.X(), c.Y(), c.Z()), r)
    else:
        msp.add_arc((c.X(), c.Y(), c.Z()), r, a1, a2)


def _dxf_ellipse(e: Edge, msp: ezdxf.layouts.Modelspace, plane: Plane):

    geom = e._geomAdaptor()
    ellipse = geom.Ellipse()

    r1 = ellipse.MinorRadius()
    r2 = ellipse.MajorRadius()

    c = ellipse.Location()
    xdir = ellipse.XAxis().Direction()
    xax = r2 * xdir.XYZ()

    msp.add_ellipse(
        (c.X(), c.Y(), c.Z()),
        (xax.X(), xax.Y(), xax.Z()),
        r1 / r2,
        geom.FirstParameter(),
        geom.LastParameter(),
    )


def _dxf_spline(e: Edge, msp: ezdxf.layouts.Modelspace, plane: Plane):

    adaptor = e._geomAdaptor()
    curve = GeomConvert.CurveToBSplineCurve_s(adaptor.Curve().Curve())

    spline = GeomConvert.SplitBSplineCurve_s(
        curve, adaptor.FirstParameter(), adaptor.LastParameter(), CURVE_TOLERANCE
    )

    # need to apply the transform on the geometry level
    spline.Transform(plane.fG.wrapped.Trsf())

    order = spline.Degree() + 1
    knots = list(spline.KnotSequence())
    poles = [(p.X(), p.Y(), p.Z()) for p in spline.Poles()]
    weights = (
        [spline.Weight(i) for i in range(1, spline.NbPoles() + 1)]
        if spline.IsRational()
        else None
    )

    if spline.IsPeriodic():
        pad = spline.NbKnots() - spline.LastUKnotIndex()
        poles += poles[:pad]

    dxf_spline = ezdxf.math.BSpline(poles, order, knots, weights)

    msp.add_spline().apply_construction_tool(dxf_spline)


DXF_CONVERTERS = {
    "LINE": _dxf_line,
    "CIRCLE": _dxf_circle,
    "ELLIPSE": _dxf_ellipse,
    "BSPLINE": _dxf_spline,
}


def exportDXF(
    w: Workplane,
    fname: str,
    approx: Optional[Literal["spline", "arc"]] = None,
    tolerance: float = 1e-3,
):
    """
    Export Workplane content to DXF. Works with 2D sections.

    :param w: Workplane to be exported.
    :param fname: Output filename.
    :param approx: Approximation strategy. None means no approximation is applied.
    "spline" results in all splines being approximated as cubic splines. "arc" results
    in all curves being approximated as arcs and straight segments.
    :param tolerance: Approximation tolerance.

    """

    plane = w.plane
    shape = toCompound(w).transformShape(plane.fG)

    dxf = ezdxf.new()
    msp = dxf.modelspace()

    if approx == "spline":
        edges = [
            e.toSplines() if e.geomType() == "BSPLINE" else e for e in shape.Edges()
        ]

    elif approx == "arc":
        edges = []

        # this is needed to handle free wires
        for el in shape.Wires():
            edges.extend(Face.makeFromWires(el).toArcs(tolerance).Edges())

    else:
        edges = shape.Edges()

    for e in edges:

        conv = DXF_CONVERTERS.get(e.geomType(), _dxf_spline)
        conv(e, msp, plane)

    dxf.saveas(fname)
