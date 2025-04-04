from typing import Sequence

from numpy import (
    atleast_1d,
    concat,
    zeros,
    searchsorted,
    zeros_like,
)

from numba import njit as _njit, prange, f8

njit = _njit(cache=True, fastmath=False, parallel=True)
njiti = _njit(cache=True, inline="always", fastmath=False, parallel=False)


from cadquery.occ_impl.shapes import Edge
from cadquery.occ_impl.geom import Vector

from OCP.Geom import Geom_BSplineCurve
from OCP.gp import gp_Pnt
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeEdge
from OCP.TColgp import TColgp_Array1OfPnt, TColgp_Array2OfPnt
from OCP.TColStd import (
    TColStd_Array1OfReal,
    TColStd_Array1OfInteger,
    TColStd_Array2OfPnt,
)


def periodicDM(knots: f8[:], xs: f8[:]) -> f8[:, :]:
    """
    Periodic cubic B-spline design matrix.
    """

    order = 3

    knots_ext = concat(
        (knots[-(order + 1) : -1] - knots[-1], knots, knots[-1] + knots[1 : order + 1])
    )

    n = len(xs)
    m = len(knots) - 1

    rv = zeros((n, m))

    for j in prange(m + 3):
        rv[:, j % m] += cubicBS(xs, j + 2, knots_ext)

    return rv, knots_ext


def DM(knots: f8[:], xs: f8[:]) -> f8[:, :]:
    """
    Non-periodic cubic B-spline design matrix.
    """

    order = 3

    knots_ext = concat((knots[:1].repeat(order), knots, knots[-1:].repeat(order)))

    n = len(xs)
    m = len(knots) + order - 1

    rv = zeros((n, m))
    if xs[0] == knots[0]:
        rv[0, 0] = 1.0

    for j in prange(m):
        rv[:, j] += cubicBS(xs, j + order - 1, knots_ext)

    return rv, knots_ext


@njiti
def cubicBS(xs: f8[:], i: int, knots: f8[:]) -> f8[:]:
    """
    Cubic B-spline basis function.
    """

    u = knots
    ts = atleast_1d(xs)
    res = zeros_like(xs)

    d1 = u[i + 1] - u[i - 2]
    d2 = u[i] - u[i - 2]
    d3 = u[i - 1] - u[i - 2]
    d4 = u[i] - u[i - 1]
    d5 = u[i + 1] - u[i - 1]
    d6 = u[i + 2] - u[i - 1]
    d7 = u[i + 1] - u[i]
    d8 = u[i + 2] - u[i]
    d9 = u[i + 2] - u[i + 1]

    j1, j2 = searchsorted(ts, (u[i - 2], u[i + 2]))

    for j in range(j1, j2 + 1):
        t = ts[j]
        rv = 0.0

        if t <= u[i - 1] and t > u[i - 2]:
            if d1 == 0 or d2 == 0 or d3 == 0:
                rv = 0
            else:
                rv = (t - u[i - 2]) ** 3
                rv /= d1 * d2 * d3

        elif t <= u[i] and t > u[i - 1]:
            tmp1 = 0.0

            if d2 != 0 and d4 != 0:
                tmp1 = (t - u[i - 2]) * (u[i] - t)
                tmp1 /= d2 * d4

            tmp2 = 0.0

            if d5 != 0 and d4 != 0:
                tmp2 = (u[i + 1] - t) * (t - u[i - 1])
                tmp2 /= d5 * d4

            if d1 != 0:
                rv += (t - u[i - 2]) / d1
                rv *= tmp1 + tmp2

            tmp3 = 0.0

            if d6 != 0 and d5 != 0 and d4 != 0:
                tmp3 = (u[i + 2] - t) * (t - u[i - 1]) ** 2
                tmp3 /= d6 * d5 * d4

                rv += tmp3

        elif t <= u[i + 1] and t > u[i]:

            tmp1 = 0.0

            if d1 != 0 and d7 != 0 and d5 != 0:
                tmp1 = (t - u[i - 2]) * (u[i + 1] - t) ** 2
                tmp1 /= d1 * d7 * d5

            rv += tmp1

            tmp2 = 0.0

            if d5 != 0 and d7 != 0:
                tmp2 = (t - u[i - 1]) * (u[i + 1] - t)
                tmp2 /= d5 * d7

            tmp3 = 0

            if d8 != 0 and d7 != 0:
                tmp3 = (u[i + 2] - t) * (t - u[i])
                tmp3 /= d8 * d7

            if d6 != 0:
                rv += (tmp2 + tmp3) * (u[i + 2] - t) / d6

        elif t <= u[i + 2] and t > u[i + 1]:

            if d9 != 0 and d8 != 0 and d6 != 0:
                rv += (u[i + 2] - t) ** 3
                rv /= d9 * d8 * d6

        res[j] = rv

    return res


def _to_pts_arr(pts: Sequence[gp_Pnt]) -> TColgp_Array1OfPnt:
    """
    Helper to construct a TColgp_Array1OfPnt.
    """

    rv = TColgp_Array1OfPnt(1, len(pts))

    for i, p in enumerate(pts):
        rv.SetValue(i + 1, gp_Pnt(*p))

    return rv


def _to_pts_arr2(pts: Sequence[Sequence[Vector]]) -> TColStd_Array2OfPnt:
    """
    Helper to construct a TColgp_Array2OfReal.
    """

    rv = TColgp_Array2OfPnt(1, len(pts), 1, len(pts[0]))

    for i, ps_v in enumerate(pts):
        for j, pt in enumerate(ps_v):
            rv.SetValue(i + 1, j + 1, gp_Pnt(*pt))

    return rv


def _to_real_arr(vals: Sequence[float]) -> TColStd_Array1OfReal:
    """
    Helper to construct a TColStd_Array1OfReal.
    """

    rv = TColStd_Array1OfReal(1, len(vals))

    for i, v in enumerate(vals):
        rv.SetValue(i + 1, v)

    return rv


def _nominal_mults_periodic(knots: Sequence[float]) -> TColStd_Array1OfInteger:
    """
    Generate a nominal multipicity vector for a given periodic knot vector.
    """

    n_knots = len(knots)

    # init multiplicites
    mults = TColStd_Array1OfInteger(1, n_knots)
    mults.Init(1)

    return mults


def _nominal_mults(knots: Sequence[float], order: int) -> TColStd_Array1OfInteger:
    """
    Generate a nominal multipicity vector for a given clamped knot vector.
    """

    n_knots = len(knots)

    # init multiplicites
    mults = TColStd_Array1OfInteger(1, n_knots)
    mults.Init(1)

    mults.SetValue(1, order + 1)
    mults.SetValue(n_knots, order + 1)

    return mults


def toPeriodicCurve(
    pts: Sequence[Sequence[float]], knots: Sequence[float], order: int = 3
) -> Geom_BSplineCurve:
    """
    Construct a Geom periodic curve.
    """

    return Geom_BSplineCurve(
        _to_pts_arr(pts),
        _to_real_arr(knots),
        _nominal_mults_periodic(knots),
        order,
        True,
    )


def toCurve(
    pts: Sequence[gp_Pnt], knots: Sequence[float], order: int = 3
) -> Geom_BSplineCurve:
    """
    Construct a Geom non-periodic curve.
    """

    return Geom_BSplineCurve(
        _to_pts_arr(pts),
        _to_real_arr(knots),
        _nominal_mults(knots, order),
        order,
        False,
    )


def toEdge(geom: Geom_BSplineCurve) -> Edge:
    """
    Construct an edge from Geom curve
    """

    return Edge(BRepBuilderAPI_MakeEdge(geom).Shape())
