# %% imports
import numpy as np
import scipy.sparse as sp

from numba import njit as _njit

from typing import NamedTuple, Optional, Tuple, List, Union, cast

from numpy.typing import NDArray
from numpy import linspace, ndarray

from casadi import ldl, ldl_solve

from OCP.Geom import Geom_BSplineCurve, Geom_BSplineSurface
from OCP.TColgp import TColgp_Array1OfPnt, TColgp_Array2OfPnt
from OCP.TColStd import (
    TColStd_Array1OfInteger,
    TColStd_Array1OfReal,
)
from OCP.gp import gp_Pnt
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeEdge, BRepBuilderAPI_MakeFace

from .shapes import Face, Edge

from multimethod import multidispatch

njit = _njit(cache=True, error_model="numpy", fastmath=True, nogil=True, parallel=False)

njiti = _njit(
    cache=True, inline="always", error_model="numpy", fastmath=True, parallel=False
)


# %% internal helpers


def _colPtsArray(pts: NDArray) -> TColgp_Array1OfPnt:

    rv = TColgp_Array1OfPnt(1, pts.shape[0])

    for i, p in enumerate(pts):
        rv.SetValue(i + 1, gp_Pnt(*p))

    return rv


def _colPtsArray2(pts: NDArray) -> TColgp_Array2OfPnt:

    assert pts.ndim == 3

    nu, nv, _ = pts.shape

    rv = TColgp_Array2OfPnt(1, len(pts), 1, len(pts[0]))

    for i, row in enumerate(pts):
        for j, pt in enumerate(row):
            rv.SetValue(i + 1, j + 1, gp_Pnt(*pt))

    return rv


def _colRealArray(knots: NDArray) -> TColStd_Array1OfReal:

    rv = TColStd_Array1OfReal(1, len(knots))

    for i, el in enumerate(knots):
        rv.SetValue(i + 1, el)

    return rv


def _colIntArray(knots: NDArray) -> TColStd_Array1OfInteger:

    rv = TColStd_Array1OfInteger(1, len(knots))

    for i, el in enumerate(knots):
        rv.SetValue(i + 1, el)

    return rv


# %% vocabulary types

Array = ndarray  # NDArray[np.floating]
ArrayI = ndarray  # NDArray[np.int_]


class COO(NamedTuple):
    """
    COO sparse matrix container.
    """

    i: ArrayI
    j: ArrayI
    v: Array

    def coo(self):

        return sp.coo_matrix((self.v, (self.i, self.j)))

    def csc(self):

        return self.coo().tocsc()

    def csr(self):

        return self.coo().tocsr()


class Curve(NamedTuple):
    """
    B-spline curve container.
    """

    pts: Array
    knots: Array
    order: int
    periodic: bool

    def curve(self) -> Geom_BSplineCurve:

        if self.periodic:
            mults = _colIntArray(np.ones_like(self.knots, dtype=int))
            knots = _colRealArray(self.knots)
        else:
            unique_knots, mults_arr = np.unique(self.knots, return_counts=True)
            knots = _colRealArray(unique_knots)
            mults = _colIntArray(mults_arr)

        return Geom_BSplineCurve(
            _colPtsArray(self.pts), knots, mults, self.order, self.periodic,
        )

    def edge(self) -> Edge:

        return Edge(BRepBuilderAPI_MakeEdge(self.curve()).Shape())

    @classmethod
    def fromEdge(cls, e: Edge):

        assert (
            e.geomType() == "BSPLINE"
        ), "B-spline geometry required, try converting first."

        g = e._geomAdaptor().BSpline()

        knots = np.array(list(e._geomAdaptor().BSpline().KnotSequence()))
        pts = np.array([(p.X(), p.Y(), p.Z()) for p in g.Poles()])
        order = g.Degree()
        periodic = g.IsPeriodic()

        if periodic:
            knots = knots[order:-order]

        return cls(pts, knots, order, periodic)

    def __call__(self, us: Array) -> Array:

        return nbCurve(
            np.atleast_1d(us), self.order, self.knots, self.pts, self.periodic
        )

    def der(self, us: NDArray, dorder: int) -> NDArray:

        return nbCurveDer(
            np.atleast_1d(us), self.order, dorder, self.knots, self.pts, self.periodic
        )


class Surface(NamedTuple):
    """
    B-spline surface container.
    """

    pts: Array
    uknots: Array
    vknots: Array
    uorder: int
    vorder: int
    uperiodic: bool
    vperiodic: bool

    def surface(self) -> Geom_BSplineSurface:

        if self.uperiodic:
            umults = _colIntArray(np.ones_like(self.uknots, dtype=int))
            uknots = _colRealArray(self.uknots)
        else:
            unique_knots, mults_arr = np.unique(self.uknots, return_counts=True)
            uknots = _colRealArray(unique_knots)
            umults = _colIntArray(mults_arr)

        if self.vperiodic:
            vmults = _colIntArray(np.ones_like(self.vknots, dtype=int))
            vknots = _colRealArray(self.vknots)
        else:
            unique_knots, mults_arr = np.unique(self.vknots, return_counts=True)
            vknots = _colRealArray(unique_knots)
            vmults = _colIntArray(mults_arr)

        return Geom_BSplineSurface(
            _colPtsArray2(self.pts),
            uknots,
            vknots,
            umults,
            vmults,
            self.uorder,
            self.vorder,
            self.uperiodic,
            self.vperiodic,
        )

    def face(self, tol: float = 1e-3) -> Face:

        return Face(BRepBuilderAPI_MakeFace(self.surface(), tol).Shape())

    @classmethod
    def fromFace(cls, f: Face):
        """
        Construct a surface from a face.
        """

        assert (
            f.geomType() == "BSPLINE"
        ), "B-spline geometry required, try converting first."

        g = cast(Geom_BSplineSurface, f._geomAdaptor())

        uknots = np.array(list(g.UKnotSequence()))
        vknots = np.array(list(g.VKnotSequence()))

        tmp = []
        for i in range(1, g.NbUPoles() + 1):
            tmp.append(
                [
                    [g.Pole(i, j).X(), g.Pole(i, j).Y(), g.Pole(i, j).Z(),]
                    for j in range(1, g.NbVPoles() + 1)
                ]
            )

        pts = np.array(tmp)

        uorder = g.UDegree()
        vorder = g.VDegree()

        uperiodic = g.IsUPeriodic()
        vperiodic = g.IsVPeriodic()

        if uperiodic:
            uknots = uknots[uorder:-uorder]

        if vperiodic:
            vknots = vknots[vorder:-vorder]

        return cls(pts, uknots, vknots, uorder, vorder, uperiodic, vperiodic)

    def __call__(self, u: Array, v: Array) -> Array:
        """
        Evaluate surface at (u,v) points.
        """

        return nbSurface(
            np.atleast_1d(u),
            np.atleast_1d(v),
            self.uorder,
            self.vorder,
            self.uknots,
            self.vknots,
            self.pts,
            self.uperiodic,
            self.vperiodic,
        )

    def der(self, u: Array, v: Array, dorder: int) -> Array:
        """
        Evaluate surface and derivatives at (u,v) points.
        """

        return nbSurfaceDer(
            np.atleast_1d(u),
            np.atleast_1d(v),
            self.uorder,
            self.vorder,
            dorder,
            self.uknots,
            self.vknots,
            self.pts,
            self.uperiodic,
            self.vperiodic,
        )


# %% basis functions


@njiti
def _preprocess(
    u: Array, order: int, knots: Array, periodic: float
) -> Tuple[Array, Array, Optional[int], Optional[int], int]:
    """
    Helper for handling peridocity. This function extends the knot vector,
    wraps the parameters and calculates the delta span.
    """

    # handle periodicity
    if periodic:
        period = knots[-1] - knots[0]
        u_ = u % period
        knots_ext = extendKnots(order, knots)
        minspan = 0
        maxspan = len(knots) - 1
        deltaspan = order - 1
    else:
        u_ = u
        knots_ext = knots
        minspan = order
        maxspan = knots.shape[0] - order - 1
        deltaspan = 0

    return u_, knots_ext, minspan, maxspan, deltaspan


@njiti
def extendKnots(order: int, knots: Array) -> Array:
    """
    Knot vector extension for periodic b-splines.

    Parameters
    ----------
    order : int
        B-spline order.
    knots : Array
        Knot vector.

    Returns
    -------
    knots_ext : Array
        Extended knots vector.

    """

    return np.concat((knots[-order:-1] - knots[-1], knots, knots[-1] + knots[1:order]))


@njiti
def nbFindSpan(
    u: float,
    order: int,
    knots: Array,
    low: Optional[int] = None,
    high: Optional[int] = None,
) -> int:
    """
    NURBS book A2.1 with modifications to handle periodic usecases.

    Parameters
    ----------
    u : float
        Parameter value.
    order : int
        Spline order.
    knots : ndarray
        Knot vector.

    Returns
    -------
    Span index.

    """

    if low is None:
        low = order

    if high is None:
        high = knots.shape[0] - order - 1

    mid = (low + high) // 2

    if u >= knots[-1]:
        return high - 1  # handle last span
    elif u < knots[0]:
        return low

    while u < knots[mid] or u >= knots[mid + 1]:
        if u < knots[mid]:
            high = mid
        else:
            low = mid

        mid = (low + high) // 2

    return mid


@njiti
def nbBasis(i: int, u: float, order: int, knots: Array, out: Array):
    """
    NURBS book A2.2

    Parameters
    ----------
    i : int
        Span index.
    u : float
        Parameter value.
    order : int
        B-spline order.
    knots : ndarray
        Knot vector.
    out : ndarray
        B-spline basis function values.

    Returns
    -------
    None.

    """

    out[0] = 1.0

    left = np.zeros_like(out)
    right = np.zeros_like(out)

    for j in range(1, order + 1):
        left[j] = u - knots[i + 1 - j]
        right[j] = knots[i + j] - u

        saved = 0.0

        for r in range(j):
            temp = out[r] / (right[r + 1] + left[j - r])
            out[r] = saved + right[r + 1] * temp
            saved = left[j - r] * temp

        out[j] = saved


@njiti
def nbBasisDer(i: int, u: float, order: int, dorder: int, knots: Array, out: Array):
    """
    NURBS book A2.3

    Parameters
    ----------
    i : int
        Span index.
    u : float
        Parameter value.
    order : int
        B-spline order.
    dorder : int
        Derivative order.
    knots : ndarray
        Knot vector.
    out : ndarray
        B-spline basis function and derivative values.

    Returns
    -------
    None.

    """

    ndu = np.zeros((order + 1, order + 1))

    left = np.zeros(order + 1)
    right = np.zeros(order + 1)

    a = np.zeros((2, order + 1))

    ndu[0, 0] = 1

    for j in range(1, order + 1):
        left[j] = u - knots[i + 1 - j]
        right[j] = knots[i + j] - u

        saved = 0.0

        for r in range(j):
            ndu[j, r] = right[r + 1] + left[j - r]
            temp = ndu[r, j - 1] / ndu[j, r]

            ndu[r, j] = saved + right[r + 1] * temp
            saved = left[j - r] * temp

        ndu[j, j] = saved

    # store the basis functions
    out[0, :] = ndu[:, order]

    # calculate and store derivatives

    # loop over basis functions
    for r in range(order + 1):
        s1 = 0
        s2 = 1

        a[0, 0] = 1

        # loop over derivative orders
        for k in range(1, dorder + 1):
            d = 0.0
            rk = r - k
            pk = order - k

            if r >= k:
                a[s2, 0] = a[s1, 0] / ndu[pk + 1, rk]
                d = a[s2, 0] * ndu[rk, pk]

            if rk >= -1:
                j1 = 1
            else:
                j1 = -rk

            if r - 1 <= pk:
                j2 = k - 1
            else:
                j2 = order - r

            for j in range(j1, j2 + 1):
                a[s2, j] = (a[s1, j] - a[s1, j - 1]) / ndu[pk + 1, rk + j]
                d += a[s2, j] * ndu[rk + j, pk]

            if r <= pk:
                a[s2, k] = -a[s1, k - 1] / ndu[pk + 1, r]
                d += a[s2, k] * ndu[r, pk]

            # store the kth derivative of rth basis
            out[k, r] = d

            # switch
            s1, s2 = s2, s1

    # multiply recursively by the order
    r = order

    for k in range(1, dorder + 1):
        out[k, :] *= r
        r *= order - k


# %% evaluation


@njit
def nbCurve(
    u: Array, order: int, knots: Array, pts: Array, periodic: bool = False
) -> Array:
    """
    NURBS book A3.1 with modifications to handle periodicity.

    Parameters
    ----------
    u : Array
        Parameter values.
    order : int
        B-spline order.
    knots : Array
        Knot vector.
    pts : Array
        Control points.
    periodic : bool, optional
        Periodicity flag. The default is False.

    Returns
    -------
    Array
        Curve values.

    """

    # number of control points
    nb = pts.shape[0]

    u_, knots_ext, minspan, maxspan, deltaspan = _preprocess(u, order, knots, periodic)

    # number of param values
    nu = np.size(u)

    # chunck size
    n = order + 1

    # temp chunck storage
    temp = np.zeros(n)

    # initialize
    out = np.zeros((nu, 3))

    for i in range(nu):
        ui = u_[i]

        # find span
        span = nbFindSpan(ui, order, knots, minspan, maxspan) + deltaspan

        # evaluate chunk
        nbBasis(span, ui, order, knots_ext, temp)

        # multiply by ctrl points
        for j in range(order + 1):
            out[i, :] += temp[j] * pts[(span - order + j) % nb, :]

    return out


@njit
def nbCurveDer(
    u: Array, order: int, dorder: int, knots: Array, pts: Array, periodic: bool = False
) -> Array:
    """
    NURBS book A3.2 with modifications to handle periodicity.

    Parameters
    ----------
    u : Array
        Parameter values.
    order : int
        B-spline order.
    dorder : int
        Derivative order.
    knots : Array
        Knot vector.
    pts : Array
        Control points.
    periodic : bool, optional
        Periodicity flag. The default is False.


    Returns
    -------
    Array
        Curve values and derivatives.

    """
    # number of control points
    nb = pts.shape[0]

    # handle periodicity
    u_, knots_ext, minspan, maxspan, deltaspan = _preprocess(u, order, knots, periodic)

    # number of param values
    nu = np.size(u)

    # chunck size
    n = order + 1

    # temp chunck storage
    temp = np.zeros((dorder + 1, n))

    # initialize
    out = np.zeros((nu, dorder + 1, 3))

    for i in range(nu):
        ui = u_[i]

        # find span
        span = nbFindSpan(ui, order, knots, minspan, maxspan) + deltaspan

        # evaluate chunk
        nbBasisDer(span, ui, order, dorder, knots_ext, temp)

        # multiply by ctrl points
        for j in range(order + 1):
            for k in range(dorder + 1):
                out[i, k, :] += temp[k, j] * pts[(span - order + j) % nb, :]

    return out


@njit
def nbSurface(
    u: Array,
    v: Array,
    uorder: int,
    vorder: int,
    uknots: Array,
    vknots: Array,
    pts: Array,
    uperiodic: bool = False,
    vperiodic: bool = False,
) -> Array:
    """
    NURBS book A3.5 with modifications to handle periodicity.

    Parameters
    ----------
    u : Array
        U parameter values.
    v : Array
        V parameter values.
    uorder : int
        B-spline u order.
    vorder : int
        B-spline v order.
    uknots : Array
        U knot vector..
    vknots : Array
        V knot vector..
    pts : Array
        Control points.
    uperiodic : bool, optional
        U periodicity flag. The default is False.
    vperiodic : bool, optional
        V periodicity flag. The default is False.

    Returns
    -------
    Array
        Surface values.

    """

    # number of control points
    nub = pts.shape[0]
    nvb = pts.shape[1]

    # handle periodicity
    u_, uknots_ext, minspanu, maxspanu, deltaspanu = _preprocess(
        u, uorder, uknots, uperiodic
    )
    v_, vknots_ext, minspanv, maxspanv, deltaspanv = _preprocess(
        v, vorder, vknots, vperiodic
    )

    # number of param values
    nu = np.size(u)

    # chunck sizes
    un = uorder + 1
    vn = vorder + 1

    # temp chunck storage
    utemp = np.zeros(un)
    vtemp = np.zeros(vn)

    # initialize
    out = np.zeros((nu, 3))

    for i in range(nu):
        ui = u_[i]
        vi = v_[i]

        # find span
        uspan = nbFindSpan(ui, uorder, uknots, minspanu, maxspanu) + deltaspanu
        vspan = nbFindSpan(vi, vorder, vknots, minspanv, maxspanv) + deltaspanv

        # evaluate chunk
        nbBasis(uspan, ui, uorder, uknots_ext, utemp)
        nbBasis(vspan, vi, vorder, vknots_ext, vtemp)

        uind = uspan - uorder
        temp = np.empty(3)

        # multiply by ctrl points: Nu.T*P*Nv
        for j in range(vorder + 1):

            temp[:] = 0.0
            vind = vspan - vorder + j

            # calculate Nu.T*P
            for k in range(uorder + 1):
                temp += utemp[k] * pts[(uind + k) % nub, vind % nvb, :]

            # multiple by Nv
            out[i, :] += vtemp[j] * temp

    return out


@njit
def nbSurfaceDer(
    u: Array,
    v: Array,
    uorder: int,
    vorder: int,
    dorder: int,
    uknots: Array,
    vknots: Array,
    pts: Array,
    uperiodic: bool = False,
    vperiodic: bool = False,
) -> Array:
    """
    NURBS book A3.6 with modifications to handle periodicity.

    Parameters
    ----------
    u : Array
        U parameter values.
    v : Array
        V parameter values.
    uorder : int
        B-spline u order.
    vorder : int
        B-spline v order.
    dorder : int
        Maximum derivative order.
    uknots : Array
        U knot vector..
    vknots : Array
        V knot vector..
    pts : Array
        Control points.
    uperiodic : bool, optional
        U periodicity flag. The default is False.
    vperiodic : bool, optional
        V periodicity flag. The default is False.

    Returns
    -------
    Array
        Surface and derivative values.

    """

    # max derivative orders
    du = min(dorder, uorder)
    dv = min(dorder, vorder)

    # number of control points
    nub = pts.shape[0]
    nvb = pts.shape[1]

    # handle periodicity
    u_, uknots_ext, minspanu, maxspanu, deltaspanu = _preprocess(
        u, uorder, uknots, uperiodic
    )
    v_, vknots_ext, minspanv, maxspanv, deltaspanv = _preprocess(
        v, vorder, vknots, vperiodic
    )

    # number of param values
    nu = np.size(u)

    # chunck sizes
    un = uorder + 1
    vn = vorder + 1

    # temp chunck storage

    utemp = np.zeros((du + 1, un))
    vtemp = np.zeros((dv + 1, vn))

    # initialize
    out = np.zeros((nu, du + 1, dv + 1, 3))

    for i in range(nu):
        ui = u_[i]
        vi = v_[i]

        # find span
        uspan = nbFindSpan(ui, uorder, uknots, minspanu, maxspanu) + deltaspanu
        vspan = nbFindSpan(vi, vorder, vknots, minspanv, maxspanv) + deltaspanv

        # evaluate chunk
        nbBasisDer(uspan, ui, uorder, du, uknots_ext, utemp)
        nbBasisDer(vspan, vi, vorder, dv, vknots_ext, vtemp)

        for k in range(du + 1):

            temp = np.zeros((vorder + 1, 3))

            # Nu.T^(k)*pts
            for s in range(vorder + 1):
                for r in range(uorder + 1):
                    temp[s, :] += (
                        utemp[k, r]
                        * pts[(uspan - uorder + r) % nub, (vspan - vorder + s) % nvb, :]
                    )

            # ramaining derivative orders: dk + du <= dorder
            dd = min(dorder - k, dv)

            # .. * Nv^(l)
            for l in range(dd + 1):
                for s in range(vorder + 1):
                    out[i, k, l, :] += vtemp[l, s] * temp[s, :]

    return out


# %% matrices


@njit
def designMatrix(u: Array, order: int, knots: Array, periodic: bool = False) -> COO:
    """
    Create a sparse (possibly periodic) design matrix.
    """

    # extend the knots
    knots_ext = np.concat(
        (knots[-order:-1] - knots[-1], knots, knots[-1] + knots[1:order])
    )

    u_, knots_ext, minspan, maxspan, deltaspan = _preprocess(u, order, knots, periodic)

    # number of param values
    nu = len(u)

    # number of basis functions
    nb = maxspan

    # chunck size
    n = order + 1

    # temp chunck storage
    temp = np.zeros(n)

    # initialize the empty matrix
    rv = COO(
        i=np.empty(n * nu, dtype=np.int64),
        j=np.empty(n * nu, dtype=np.int64),
        v=np.empty(n * nu),
    )

    # loop over param values
    for i in range(nu):
        ui = u_[i]

        # find the supporting span
        span = nbFindSpan(ui, order, knots, minspan, maxspan) + deltaspan

        # evaluate non-zero functions
        nbBasis(span, ui, order, knots_ext, temp)

        # update the matrix
        rv.i[i * n : (i + 1) * n] = i
        rv.j[i * n : (i + 1) * n] = (
            span - order + np.arange(n)
        ) % nb  # NB: this is due to peridicity
        rv.v[i * n : (i + 1) * n] = temp

    return rv


# @njit
def designMatrix2D(
    uv: Array,
    uorder: int,
    vorder: int,
    uknots: Array,
    vknots: Array,
    uperiodic: bool = False,
    vperiodic: bool = False,
) -> COO:
    """
    Create a sparse tensor product design matrix.
    """

    u_, uknots_ext, minspanu, maxspanu, deltaspanu = _preprocess(
        uv[:, 0], uorder, uknots, uperiodic
    )
    v_, vknots_ext, minspanv, maxspanv, deltaspanv = _preprocess(
        uv[:, 1], vorder, vknots, vperiodic
    )

    # number of param values
    ni = uv.shape[0]

    # chunck size
    nu = uorder + 1
    nv = vorder + 1
    nj = nu * nv

    # number of basis
    nu_total = maxspanu
    nv_total = maxspanv

    # temp chunck storage
    utemp = np.zeros(nu)
    vtemp = np.zeros(nv)

    # initialize the empty matrix
    rv = COO(
        i=np.empty(ni * nj, dtype=np.int64),
        j=np.empty(ni * nj, dtype=np.int64),
        v=np.empty(ni * nj),
    )

    # loop over param values
    for i in range(ni):
        ui, vi = u_[i], v_[i]

        # find the supporting span
        uspan = nbFindSpan(ui, uorder, uknots, minspanu, maxspanu) + deltaspanu
        vspan = nbFindSpan(vi, vorder, vknots, minspanv, maxspanv) + deltaspanv

        # evaluate non-zero functions
        nbBasis(uspan, ui, uorder, uknots_ext, utemp)
        nbBasis(vspan, vi, vorder, vknots_ext, vtemp)

        # update the matrix
        rv.i[i * nj : (i + 1) * nj] = i
        rv.j[i * nj : (i + 1) * nj] = (
            ((uspan - uorder + np.arange(nu)) % nu_total) * nv_total
            + ((vspan - vorder + np.arange(nv)) % nv_total)[:, np.newaxis]
        ).ravel()
        rv.v[i * nj : (i + 1) * nj] = (utemp * vtemp[:, np.newaxis]).ravel()

    return rv


@njit
def periodicDesignMatrix(u: Array, order: int, knots: Array) -> COO:
    """
    Create a sparse periodic design matrix.
    """

    return designMatrix(u, order, knots, periodic=True)


@njit
def derMatrix(u: Array, order: int, dorder: int, knots: Array) -> list[COO]:
    """
    Create a sparse design matrix and corresponding derivative matrices.
    """

    # number of param values
    nu = np.size(u)

    # chunck size
    n = order + 1

    # temp chunck storage
    temp = np.zeros((dorder + 1, n))

    # initialize the empty matrix
    rv = []

    for _ in range(dorder + 1):
        rv.append(
            COO(
                i=np.empty(n * nu, dtype=np.int64),
                j=np.empty(n * nu, dtype=np.int64),
                v=np.empty(n * nu),
            )
        )

    # loop over param values
    for i in range(nu):
        ui = u[i]

        # find the supporting span
        span = nbFindSpan(ui, order, knots)

        # evaluate non-zero functions
        nbBasisDer(span, ui, order, dorder, knots, temp)

        # update the matrices
        for di in range(dorder + 1):
            rv[di].i[i * n : (i + 1) * n] = i
            rv[di].j[i * n : (i + 1) * n] = span - order + np.arange(n)
            rv[di].v[i * n : (i + 1) * n] = temp[di, :]

    return rv


@njit
def periodicDerMatrix(u: Array, order: int, dorder: int, knots: Array) -> list[COO]:
    """
    Create a sparse periodic design matrix and corresponding derivative matrices.
    """

    # extend the knots
    knots_ext = np.concat(
        (knots[-order:-1] - knots[-1], knots, knots[-1] + knots[1:order])
    )

    # number of param values
    nu = len(u)

    # number of basis functions
    nb = len(knots) - 1

    # chunck size
    n = order + 1

    # temp chunck storage
    temp = np.zeros((dorder + 1, n))

    # initialize the empty matrix
    rv = []

    for _ in range(dorder + 1):
        rv.append(
            COO(
                i=np.empty(n * nu, dtype=np.int64),
                j=np.empty(n * nu, dtype=np.int64),
                v=np.empty(n * nu),
            )
        )

    # loop over param values
    for i in range(nu):
        ui = u[i]

        # find the supporting span
        span = nbFindSpan(ui, order, knots, 0, nb) + order - 1

        # evaluate non-zero functions
        nbBasisDer(span, ui, order, dorder, knots_ext, temp)

        # update the matrices
        for di in range(dorder + 1):
            rv[di].i[i * n : (i + 1) * n] = i
            rv[di].j[i * n : (i + 1) * n] = (
                span - order + np.arange(n)
            ) % nb  # NB: this is due to peridicity
            rv[di].v[i * n : (i + 1) * n] = temp[di, :]

    return rv


@njit
def periodicDiscretePenalty(us: Array, order: int) -> COO:

    if order not in (1, 2):
        raise ValueError(
            f"Only 1st and 2nd order penalty is supported, requested order {order}"
        )

    # number of rows
    nb = len(us)

    # number of elements per row
    ne = order + 1

    # initialize the penlaty matrix
    rv = COO(
        i=np.empty(nb * ne, dtype=np.int64),
        j=np.empty(nb * ne, dtype=np.int64),
        v=np.empty(nb * ne),
    )

    if order == 1:
        for ix in range(nb):
            rv.i[ne * ix] = ix
            rv.j[ne * ix] = (ix - 1) % nb
            rv.v[ne * ix] = -0.5

            rv.i[ne * ix + 1] = ix
            rv.j[ne * ix + 1] = (ix + 1) % nb
            rv.v[ne * ix + 1] = 0.5

    elif order == 2:
        for ix in range(nb):
            rv.i[ne * ix] = ix
            rv.j[ne * ix] = (ix - 1) % nb
            rv.v[ne * ix] = 1

            rv.i[ne * ix + 1] = ix
            rv.j[ne * ix + 1] = ix
            rv.v[ne * ix + 1] = -2

            rv.i[ne * ix + 2] = ix
            rv.j[ne * ix + 2] = (ix + 1) % nb
            rv.v[ne * ix + 2] = 1

    return rv


@njit
def discretePenalty(us: Array, order: int, splineorder: int = 3) -> COO:

    if order not in (1, 2):
        raise ValueError(
            f"Only 1st and 2nd order penalty is supported, requested order {order}"
        )

    # number of rows
    nb = len(us)

    # number of elements per row
    ne = order + 1

    # initialize the penlaty matrix
    rv = COO(
        i=np.empty(nb * ne, dtype=np.int64),
        j=np.empty(nb * ne, dtype=np.int64),
        v=np.empty(nb * ne),
    )

    if order == 1:
        for ix in range(nb):
            if ix == 0:
                rv.i[ne * ix] = ix
                rv.j[ne * ix] = ix
                rv.v[ne * ix] = -1

                rv.i[ne * ix + 1] = ix
                rv.j[ne * ix + 1] = ix + 1
                rv.v[ne * ix + 1] = 1
            elif ix < nb - 1:
                rv.i[ne * ix] = ix
                rv.j[ne * ix] = ix - 1
                rv.v[ne * ix] = -0.5

                rv.i[ne * ix + 1] = ix
                rv.j[ne * ix + 1] = ix + 1
                rv.v[ne * ix + 1] = 0.5
            else:
                rv.i[ne * ix] = ix
                rv.j[ne * ix] = ix - 1
                rv.v[ne * ix] = -1

                rv.i[ne * ix + 1] = ix
                rv.j[ne * ix + 1] = ix
                rv.v[ne * ix + 1] = 1

    elif order == 2:
        for ix in range(nb):
            if ix == 0:
                rv.i[ne * ix] = ix
                rv.j[ne * ix] = ix
                rv.v[ne * ix] = 1

                rv.i[ne * ix + 1] = ix
                rv.j[ne * ix + 1] = ix + 1
                rv.v[ne * ix + 1] = -2

                rv.i[ne * ix + 2] = ix
                rv.j[ne * ix + 2] = ix + 2
                rv.v[ne * ix + 2] = 1
            elif ix < nb - 1:
                rv.i[ne * ix] = ix
                rv.j[ne * ix] = ix - 1
                rv.v[ne * ix] = 1

                rv.i[ne * ix + 1] = ix
                rv.j[ne * ix + 1] = ix
                rv.v[ne * ix + 1] = -2

                rv.i[ne * ix + 2] = ix
                rv.j[ne * ix + 2] = ix + 1
                rv.v[ne * ix + 2] = 1
            else:
                rv.i[ne * ix] = ix
                rv.j[ne * ix] = ix - 2
                rv.v[ne * ix] = 1

                rv.i[ne * ix + 1] = ix
                rv.j[ne * ix + 1] = ix - 1
                rv.v[ne * ix + 1] = -2

                rv.i[ne * ix + 2] = ix
                rv.j[ne * ix + 2] = ix
                rv.v[ne * ix + 2] = 1

    return rv


# %% construction


@multidispatch
def periodicApproximate(
    data: Array,
    us: Optional[Array] = None,
    knots: int | Array = 50,
    order: int = 3,
    penalty: int = 4,
    lam: float = 0,
) -> Curve:

    npts = data.shape[0]

    # parametrize the points
    us = linspace(0, 1, npts, endpoint=False)

    # construct the knot vector
    if isinstance(knots, int):
        knots_ = linspace(0, 1, knots)
    else:
        knots_ = np.array(knots)

    # construct the design matrix
    C = periodicDesignMatrix(us, order, knots_).csc()
    CtC = C.T @ C

    # add the penalty if requested
    if lam:
        up = linspace(0, 1, order * npts, endpoint=False)

        assert penalty <= order + 2

        # discrete + exact derivatives
        if penalty > order:
            Pexact = periodicDerMatrix(up, order, order - 1, knots_)[-1].csc()
            Pdiscrete = periodicDiscretePenalty(up, penalty - order).csc()

            P = Pdiscrete @ Pexact

        # only exact derivatives
        else:
            P = periodicDerMatrix(up, order, penalty, knots_)[-1].csc()

        CtC += lam * P.T @ P

    # factorize
    D, L, P = ldl(CtC, True)

    # invert
    pts = ldl_solve(C.T @ data, D, L, P).toarray()

    # convert to an edge
    rv = Curve(pts, knots_, order, periodic=True)

    return rv


@periodicApproximate.register
def periodicApproximate(
    data: List[Array],
    us: Optional[Array] = None,
    knots: int | Array = 50,
    order: int = 3,
    penalty: int = 4,
    lam: float = 0,
) -> List[Curve]:

    rv = []

    npts = data[0].shape[0]

    # parametrize the points
    us = linspace(0, 1, npts, endpoint=False)

    # construct the knot vector
    if isinstance(knots, int):
        knots_ = linspace(0, 1, knots)
    else:
        knots_ = np.array(knots)

    # construct the design matrix
    C = periodicDesignMatrix(us, order, knots_).csc()
    CtC = C.T @ C

    # add the penalty if requested
    if lam:
        up = linspace(0, 1, order * npts, endpoint=False)

        assert penalty <= order + 2

        # discrete + exact derivatives
        if penalty > order:
            Pexact = periodicDerMatrix(up, order, order - 1, knots_)[-1].csc()
            Pdiscrete = periodicDiscretePenalty(up, penalty - order).csc()

            P = Pdiscrete @ Pexact

        # only exact derivatives
        else:
            P = periodicDerMatrix(up, order, penalty, knots_)[-1].csc()

        CtC += lam * P.T @ P

    # factorize
    D, L, P = ldl(CtC, True)

    # invert every dataset
    for dataset in data:
        pts = ldl_solve(C.T @ dataset, D, L, P).toarray()

        # convert to an edge and store
        rv.append(Curve(pts, knots_, order, periodic=True))

    return rv


@multidispatch
def approximate(
    data: Array,
    us: Optional[Array] = None,
    knots: int | Array = 50,
    order: int = 3,
    penalty: int = 4,
    lam: float = 0,
    tangents: Optional[Tuple[Array, Array]] = None,
) -> Curve:

    npts = data.shape[0]

    # parametrize the points
    us = linspace(0, 1, npts)

    # construct the knot vector
    if isinstance(knots, int):
        knots_ = np.concatenate(
            (np.repeat(0, order), linspace(0, 1, knots), np.repeat(1, order))
        )
    else:
        knots_ = np.array(knots)

    # construct the design matrix
    C = designMatrix(us, order, knots_).csc()
    CtC = C.T @ C

    # add a penalty term if requested
    if lam:
        up = linspace(0, 1, order * npts)

        assert penalty <= order + 2

        # discrete + exact derivatives
        if penalty > order:
            Pexact = derMatrix(up, order, order - 1, knots_)[-1].csc()
            Pdiscrete = discretePenalty(up, penalty - order, order).csc()

            P = Pdiscrete @ Pexact

        # only exact derivatives
        else:
            P = derMatrix(up, order, penalty, knots_)[-1].csc()

        CtC += lam * P.T @ P

    # clamp first and last point
    Cc = C[[0, -1], :]
    bc = data[[0, -1], :]
    nc = 2  # number of constraints

    # handle tangent constraints if needed
    if tangents:
        nc += 2

        Cc2 = derMatrix(us[[0, -1]], order, 1, knots_)[-1].csc()

        Cc = sp.vstack((Cc, Cc2))
        bc = np.vstack((bc, *tangents))

    # final matrix and vector
    Aug = sp.bmat([[CtC, Cc.T], [Cc, None]])
    data_aug = np.vstack((C.T @ data, bc))

    # factorize
    D, L, P = ldl(Aug, False)

    # invert
    pts = ldl_solve(data_aug, D, L, P).toarray()[:-nc, :]

    # convert to an edge
    rv = Curve(pts, knots_, order, periodic=False)

    return rv


@approximate.register
def approximate(
    data: List[Array],
    us: Optional[Array] = None,
    knots: int | Array = 50,
    order: int = 3,
    penalty: int = 4,
    lam: float = 0,
    tangents: Optional[Union[Tuple[Array, Array], List[Tuple[Array, Array]]]] = None,
) -> List[Curve]:

    rv = []

    npts = data[0].shape[0]

    # parametrize the points
    us = linspace(0, 1, npts)

    # construct the knot vector
    if isinstance(knots, int):
        knots_ = np.concatenate(
            (np.repeat(0, order), linspace(0, 1, knots), np.repeat(1, order))
        )
    else:
        knots_ = np.array(knots)

    # construct the design matrix
    C = designMatrix(us, order, knots_).csc()
    CtC = C.T @ C

    # add a penalty term if requested
    if lam:
        up = linspace(0, 1, order * npts)

        assert penalty <= order + 2

        # discrete + exact derivatives
        if penalty > order:
            Pexact = derMatrix(up, order, order - 1, knots_)[-1].csc()
            Pdiscrete = discretePenalty(up, penalty - order, order).csc()

            P = Pdiscrete @ Pexact

        # only exact derivatives
        else:
            P = derMatrix(up, order, penalty, knots_)[-1].csc()

        CtC += lam * P.T @ P

    # clamp first and last point
    Cc = C[[0, -1], :]

    nc = 2  # number of constraints

    # handle tangent constraints if needed
    if tangents:
        nc += 2
        Cc2 = derMatrix(us[[0, -1]], order, 1, knots_)[-1].csc()
        Cc = sp.vstack((Cc, Cc2))

    # final matrix and vector
    Aug = sp.bmat([[CtC, Cc.T], [Cc, None]])

    # factorize
    D, L, P = ldl(Aug, False)

    # invert all datasets
    for ix, dataset in enumerate(data):
        bc = dataset[[0, -1], :]  # first and last point for clamping

        if tangents:
            if len(tangents) == len(data):
                bc = np.vstack((bc, *tangents[ix]))
            else:
                bc = np.vstack((bc, *tangents))

        # construct the LHS of the linear system
        dataset_aug = np.vstack((C.T @ dataset, bc))

        # actual solver
        pts = ldl_solve(dataset_aug, D, L, P).toarray()[:-nc, :]

        # convert to an edge
        rv.append(Curve(pts, knots_, order, periodic=False))

    return rv


def periodicLoft(*curves: Curve, order: int = 3) -> Surface:

    nknots: int = len(curves) + 1

    # collect control pts
    pts = [el for el in np.stack([c.pts for c in curves]).swapaxes(0, 1)]

    # approximate
    pts_new = [el.pts for el in periodicApproximate(pts, knots=nknots, order=order)]

    # construct the final surface
    rv = Surface(
        np.stack(pts_new).swapaxes(0, 1),
        linspace(0, 1, nknots),
        curves[0].knots,
        order,
        curves[0].order,
        True,
        curves[0].periodic,
    )

    return rv


def loft(
    *curves: Curve,
    order: int = 3,
    lam: float = 1e-9,
    penalty: int = 4,
    tangents: Optional[List[Tuple[Array, Array]]] = None,
) -> Surface:

    nknots: int = len(curves)

    # collect control pts
    pts = np.stack([c.pts for c in curves])

    # approximate
    pts_new = []

    for j in range(pts.shape[1]):
        pts_new.append(
            approximate(
                pts[:, j, :],
                knots=nknots,
                order=order,
                lam=lam,
                penalty=penalty,
                tangents=tangents[j] if tangents else None,
            ).pts
        )

    # construct the final surface
    rv = Surface(
        np.stack(pts_new).swapaxes(0, 1),
        np.concatenate(
            (np.repeat(0, order), linspace(0, 1, nknots), np.repeat(1, order))
        ),
        curves[0].knots,
        order,
        curves[0].order,
        False,
        curves[0].periodic,
    )

    return rv


def reparametrize(
    *curves: Curve, n: int = 100, knots: int = 100, w1: float = 1, w2: float = 1e-1
) -> List[Curve]:

    from scipy.optimize import fmin_l_bfgs_b

    n_curves = len(curves)

    u0_0 = np.linspace(0, 1, n, False)
    u0 = np.tile(u0_0, n_curves)

    # scaling for the second cost term
    scale = n * np.linalg.norm(curves[0](u0[0]) - curves[1](u0[n]))

    def cost(u: Array) -> float:

        rv1 = 0
        us = np.split(u, n_curves)

        pts = []

        for i, ui in enumerate(us):

            # evaluate
            pts.append(curves[i](ui))

            # parametric distance between points on the same curve
            rv1 += np.sum((ui[:-1] - ui[1:]) ** 2) + np.sum((ui[0] + 1 - ui[-1]) ** 2)

        rv2 = 0

        for p1, p2 in zip(pts, pts[1:]):

            # geometric distance between points on adjecent curves
            rv2 += np.sum(((p1 - p2) / scale) ** 2)

        return w1 * rv1 + w2 * rv2

    def grad(u: Array) -> Array:

        rv1 = np.zeros_like(u)
        us = np.split(u, n_curves)

        pts = []
        tgts = []

        for i, ui in enumerate(us):

            # evaluate up to 1st derivative
            tmp = curves[i].der(ui, 1)

            pts.append(tmp[:, 0, :].squeeze())
            tgts.append(tmp[:, 1, :].squeeze())

            # parametric distance between points on the same curve
            delta = np.roll(ui, -1) - ui
            delta[-1] += 1
            delta *= -2
            delta -= np.roll(delta, 1)

            rv1[i * n : (i + 1) * n] = delta

        rv2 = np.zeros_like(u)

        for i, _ in enumerate(us):
            # geometric distance between points on adjecent curves

            # first profile
            if i == 0:
                p1, p2, t = pts[i], pts[i + 1], tgts[i]

                rv2[i * n : (i + 1) * n] = (2 / scale ** 2 * (p1 - p2) * t).sum(1)

            # middle profile
            elif i + 1 < n_curves:
                p1, p2, t = pts[i], pts[i + 1], tgts[i]
                p0 = pts[i - 1]

                rv2[i * n : (i + 1) * n] = (2 / scale ** 2 * (p1 - p2) * t).sum(1)
                rv2[i * n : (i + 1) * n] += (-2 / scale ** 2 * (p0 - p1) * t).sum(1)

            # last profile
            else:
                p1, p2, t = pts[i - 1], pts[i], tgts[i]

                rv2[i * n : (i + 1) * n] = (-2 / scale ** 2 * (p1 - p2) * t).sum(1)

        return w1 * rv1 + w2 * rv2

    usol, _, _ = fmin_l_bfgs_b(cost, u0, grad)

    us = np.split(usol, n_curves)

    return periodicApproximate(
        [crv(u) for crv, u in zip(curves, us)], knots=knots, lam=0
    )


# %% for removal?
@njit
def findSpan(v, knots):

    return np.searchsorted(knots, v, "right") - 1


@njit
def findSpanLinear(v, knots):

    for rv in range(len(knots)):
        if knots[rv] <= v and knots[rv + 1] > v:
            return rv

    return -1


@njit
def periodicKnots(degree: int, n_pts: int):
    rv = np.arange(0.0, n_pts + degree + 1, 1.0)
    rv /= rv[-1]

    return rv
