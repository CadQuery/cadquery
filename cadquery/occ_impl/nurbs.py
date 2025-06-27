#%% imports
from numba import njit, prange
from numpy import linspace, array, empty_like, atleast_1d
import numpy as np
import math

from numba import njit as _njit, prange
from typing import NamedTuple, Optional
from numpy.typing import NDArray

njit = _njit(cache=False, error_model="numpy", fastmath=True, parallel=False)

njiti = _njit(
    cache=True, inline="always", error_model="numpy", fastmath=True, parallel=False
)


#%% vocabulary types

Array = NDArray[np.float64]
ArrayI = NDArray[np.int_]


class COO(NamedTuple):
    """
    COO sparse matrix container.
    """

    i: ArrayI
    j: ArrayI
    v: Array


#%% basis functions


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
        Knot vectr.

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
        Knot vectr.
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
        Knot vectr.
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


@njit
def designMatrix(u: Array, order: int, knots: Array) -> COO:
    """
    Create a sparse design matrix.
    """

    # number of param values
    nu = np.size(u)

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
        ui = u[i]

        # find the supporting span
        span = nbFindSpan(ui, order, knots)

        # evaluate non-zero functions
        nbBasis(span, ui, order, knots, temp)

        # update the matrix
        rv.i[i * n : (i + 1) * n] = i
        rv.j[i * n : (i + 1) * n] = span - order + np.arange(n)
        rv.v[i * n : (i + 1) * n] = temp

    return rv


@njit
def periodicDesignMatrix(u: Array, order: int, knots: Array) -> COO:
    """
    Create a sparse periodic design matrix.
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
    temp = np.zeros(n)

    # initialize the empty matrix
    rv = COO(
        i=np.empty(n * nu, dtype=np.int64),
        j=np.empty(n * nu, dtype=np.int64),
        v=np.empty(n * nu),
    )

    # loop over param values
    for i in range(nu):
        ui = u[i]

        # find the supporting span
        # span = np.clip(findSpan(ui, knots), None, nb - 1)  + order - 1
        span = nbFindSpan(ui, order, knots, 0, nb) + order - 1

        # evaluate non-zero functions
        nbBasis(span, ui, order, knots_ext, temp)

        # update the matrix
        rv.i[i * n : (i + 1) * n] = i
        rv.j[i * n : (i + 1) * n] = (
            span - order + np.arange(n)
        ) % nb  # NB: this is due to peridicity
        rv.v[i * n : (i + 1) * n] = temp

    return rv


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
