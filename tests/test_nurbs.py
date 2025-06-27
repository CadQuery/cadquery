from cadquery.occ_impl.nurbs import (
    designMatrix,
    periodicDesignMatrix,
    nbFindSpan,
    nbBasis,
    nbBasisDer,
)

import numpy as np
import scipy.sparse as sp


def test_periodic_dm():

    knots = np.linspace(0, 1, 5)
    params = np.linspace(0, 1, 100)
    order = 3

    res = periodicDesignMatrix(params, order, knots)

    C = sp.coo_array((res.v, (res.i, res.j)))

    assert C.shape[0] == len(params)
    assert C.shape[1] == len(knots) - 1


def test_dm():

    knots = np.array([0, 0, 0, 0, 0.25, 0.5, 0.75, 1, 1, 1, 1])
    params = np.linspace(0, 1, 100)
    order = 3

    res = designMatrix(params, order, knots)

    C = sp.coo_array((res.v, (res.i, res.j)))

    assert C.shape[0] == len(params)
    assert C.shape[1] == len(knots) - order - 1


def test_der():

    knots = np.array([0, 0, 0, 0, 0.25, 0.5, 0.75, 1, 1, 1, 1])
    params = np.linspace(0, 1, 100)
    order = 3

    out_der = np.zeros((order + 1, order + 1))
    out = np.zeros(order + 1)

    for p in params:
        nbBasisDer(nbFindSpan(p, order, knots), p, order, order - 1, knots, out_der)
        nbBasis(nbFindSpan(p, order, knots), p, order, knots, out)

        # sanity check
        assert np.allclose(out_der[0, :], out)
