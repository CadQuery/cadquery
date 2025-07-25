from cadquery.occ_impl.nurbs import (
    designMatrix,
    periodicDesignMatrix,
    designMatrix2D,
    nbFindSpan,
    nbBasis,
    nbBasisDer,
    Curve,
    Surface,
    approximate,
    periodicApproximate,
    periodicLoft,
    loft,
)

from cadquery.func import circle

import numpy as np
import scipy.sparse as sp

from pytest import approx, fixture, mark


@fixture
def circles() -> list[Curve]:

    # u,v periodic
    c1 = circle(1).toSplines()
    c2 = circle(5)

    cs = [
        Curve.fromEdge(c1.moved(loc))
        for loc in c2.locations(np.linspace(0, 1, 10, False))
    ]

    return cs


@fixture
def trimmed_circles() -> list[Curve]:

    c1 = circle(1).trim(0, 1).toSplines()
    c2 = circle(5)

    cs = [
        Curve.fromEdge(c1.moved(loc))
        for loc in c2.locations(np.linspace(0, 1, 10, False))
    ]

    return cs


def test_periodic_dm():

    knots = np.linspace(0, 1, 5)
    params = np.linspace(0, 1, 100)
    order = 3

    res = periodicDesignMatrix(params, order, knots)

    C = sp.coo_array((res.v, (res.i, res.j)))

    assert C.shape[0] == len(params)
    assert C.shape[1] == len(knots) - 1


def test_dm_2d():

    uknots = np.array([0, 0, 0, 0, 0.25, 0.5, 0.75, 1, 1, 1, 1])
    uparams = np.linspace(0, 1, 100)
    uorder = 3

    vknots = np.array([0, 0, 0, 0.5, 1, 1, 1])
    vparams = np.linspace(0, 1, 100)
    vorder = 2

    params = np.column_stack((uparams, vparams))

    res = designMatrix2D(params, uorder, vorder, uknots, vknots)

    C = res.coo()

    assert C.shape[0] == len(uparams)
    assert C.shape[1] == (len(uknots) - uorder - 1) * (len(vknots) - vorder - 1)


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


def test_periodic_curve():

    knots = np.linspace(0, 1, 5)
    pts = np.array([[0, 0, 0], [0, 0, 1], [0, 1, 2], [0, 2, 0]])

    crv = Curve(pts, knots, 3, True)

    # is it indeed periodic?
    assert crv.curve().IsPeriodic()

    # convert to an edge
    e = crv.edge()

    assert e.isValid()
    assert e.ShapeType() == "Edge"


def test_curve():

    knots = np.array([0, 0, 0, 0, 1, 1, 1, 1])
    pts = np.array([[0, 0, 0], [0, 0, 1], [0, 1, 2], [0, 2, 0]])

    crv = Curve(pts, knots, 3, False)

    # sanity check
    assert not crv.curve().IsPeriodic()

    # convert to an edge
    e = crv.edge()

    assert e.isValid()
    assert e.ShapeType() == "Edge"

    # edge to curve
    crv2 = Curve.fromEdge(e)
    e2 = crv2.edge()

    assert e2.isValid()

    # check roundtrip
    crv3 = Curve.fromEdge(e2)

    assert np.allclose(crv2.knots, crv3.knots)
    assert np.allclose(crv2.pts, crv3.pts)


def test_surface():

    uknots = vknots = np.array([0, 0, 1, 1])
    pts = np.array([[[0, 0, 0], [0, 1, 0]], [[1, 0, 0], [1, 1, 0]]])

    srf = Surface(pts, uknots, vknots, 1, 1, False, False)

    # convert to a face
    f = srf.face()

    assert f.isValid()
    assert f.Area() == approx(1)

    # roundtrip
    srf2 = Surface.fromFace(f)

    assert np.allclose(srf.uknots, srf2.uknots)
    assert np.allclose(srf.vknots, srf2.vknots)
    assert np.allclose(srf.pts, srf2.pts)


def test_approximate():

    pts_ = circle(1).trim(0, 1).sample(100)[0]
    pts = np.array([list(p) for p in pts_])

    # regular approximate
    crv = approximate(pts)
    e = crv.edge()

    assert e.isValid()
    assert e.Length() == approx(1)

    # approximate with a  double penalty
    crv = approximate(pts, penalty=4, lam=1e-9)
    e = crv.edge()

    assert e.isValid()
    assert e.Length() == approx(1)

    # approximate with a single penalty
    crv = approximate(pts, penalty=2, lam=1e-9)
    e = crv.edge()

    assert e.isValid()
    assert e.Length() == approx(1)


def test_periodic_approximate():

    pts_ = circle(1).sample(100)[0]
    pts = np.array([list(p) for p in pts_])

    crv = periodicApproximate(pts)
    e = crv.edge()

    assert e.isValid()
    assert e.Length() == approx(2 * np.pi)


def test_periodic_loft(circles, trimmed_circles):

    # u,v periodic
    surf1 = periodicLoft(*circles)

    assert surf1.face().isValid()

    # u periodic
    surf2 = periodicLoft(*trimmed_circles)

    assert surf2.face().isValid()


def test_loft(circles, trimmed_circles):

    # v periodic
    surf1 = loft(*circles)

    assert surf1.face().isValid()

    # non-periodic
    surf2 = loft(*trimmed_circles)

    assert surf2.face().isValid()
