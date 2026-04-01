from cadquery.occ_impl.nurbs import (
    approximate2D,
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
    array2vec,
    vec2array,
)

from cadquery.func import circle, torus, ellipse, spline, plane
from cadquery import Vector

from OCP.gp import gp_Pnt, gp_Vec

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


@fixture
def rotated_circles() -> list[Curve]:

    pts1 = np.array([v.toTuple() for v in circle(1).sample(100)[0]])
    pts2 = np.array([v.toTuple() for v in circle(1).moved(z=1, rz=90).sample(100)[0]])

    c1 = periodicApproximate(pts1)
    c2 = periodicApproximate(pts2)

    return [c1, c2]


def test_periodic_dm():

    knots = np.linspace(0, 1, 5)
    params = np.linspace(0, 1, 100)
    order = 3

    res = periodicDesignMatrix(params, order, knots)

    C = res.coo()

    assert C.shape[0] == len(params)
    assert C.shape[1] == len(knots) - 1


def test_dm_2d():

    uknots = np.array([0, 0, 0, 0, 0.25, 0.5, 0.75, 1, 1, 1, 1])
    uparams = np.linspace(0, 1, 100)
    uorder = 3

    vknots = np.array([0, 0, 0, 0.5, 1, 1, 1])
    vparams = np.linspace(0, 1, 100)
    vorder = 2

    res = designMatrix2D(uparams, vparams, uorder, vorder, uknots, vknots)

    C = res.coo()

    assert C.shape[0] == len(uparams)
    assert C.shape[1] == (len(uknots) - uorder - 1) * (len(vknots) - vorder - 1)


def test_dm():

    knots = np.array([0, 0, 0, 0, 0.25, 0.5, 0.75, 1, 1, 1, 1])
    params = np.linspace(0, 1, 100)
    order = 3

    res = designMatrix(params, order, knots)

    C = res.coo()

    assert C.shape[0] == len(params)
    assert C.shape[1] == len(knots) - order - 1


def test_COO():

    knots = np.array([0, 0, 0, 0, 0.25, 0.5, 0.75, 1, 1, 1, 1])
    params = np.linspace(0, 1, 100)
    order = 3

    res = designMatrix(params, order, knots)

    assert isinstance(res.coo(), sp.coo_matrix)
    assert isinstance(res.csr(), sp.csr_matrix)
    assert isinstance(res.csc(), sp.csc_matrix)


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

    # eval
    pt = crv(0)
    assert np.allclose(pt, pts[0])

    # eval der
    der = crv.der(0, 1)

    ga = e._geomAdaptor()

    tmp = gp_Pnt()
    res = gp_Vec()

    ga.D1(0, tmp, res)

    assert np.allclose(der[0, 1], np.array(Vector(res).toTuple()))


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

    # eval
    pt = srf(0, 0)
    assert np.allclose(pt, pts[0, 0])

    # eval der
    der = srf.der(0, 0, 1)
    assert np.allclose(der[0, 1, 0], np.array([1, 0, 0]))
    assert np.allclose(der[0, 0, 1], np.array([0, 1, 0]))

    # eval normal
    n, pos = srf.normal(0, 0)
    assert np.allclose(n, np.array([[0, 0, 1]]))
    assert np.allclose(pos, np.array([[0, 0, 0]]))


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

    # multiple approximate
    crvs = approximate([pts, pts], penalty=2, lam=1e-9)

    for crv in crvs:
        e = crv.edge()

        assert e.isValid()
        assert e.Length() == approx(1)


def test_periodic_approximate():

    circ = circle(1)
    pts_ = circ.sample(100)[0]
    pts = np.array([list(p) for p in pts_])

    crv = periodicApproximate(pts)
    e = crv.edge()

    assert e.isValid()
    assert e.Length() == approx(2 * np.pi)

    # check params
    us0 = circ.params(pts_)
    us1 = e.params(pts_)

    assert np.allclose(us0, np.array(us1) * 2 * np.pi)

    # multiple approximate
    crvs = periodicApproximate([pts, pts])

    for crv in crvs:
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


@mark.parametrize("lam", [0, 1e-6])
@mark.parametrize("penalty", [2, 3, 4, 5])
def test_approximate2D(lam, penalty):

    t = torus(5, 1).face()

    # double periodic surface
    us = np.linspace(0, 1, endpoint=False)
    vs = np.linspace(0, 1, endpoint=False)

    pts = np.array(
        [t.positionAt(u * 2 * np.pi, v * 2 * np.pi).toTuple() for v in vs for u in us]
    )

    surf = approximate2D(
        pts,
        us[None, :].repeat(len(vs), 0).ravel(),
        vs[:, None].repeat(len(us), 1).ravel(),
        3,
        3,
        50,
        50,
        uperiodic=True,
        vperiodic=True,
        penalty=penalty,
        lam=lam,
    )

    f = surf.face()

    # general sanity checks
    assert f.isValid()
    assert f.Area() == approx(t.Area(), rel=1e-3)

    # check the stability of the parameters
    us0 = us[None, :].repeat(len(vs), 0).ravel()
    vs0 = vs[:, None].repeat(len(us), 1).ravel()

    us2, vs2 = f.params(array2vec(pts))

    delta_u = np.array(us2 - us0)
    delta_v = np.array(vs2 - vs0)

    assert np.allclose(np.where(delta_u >= 1, delta_u, 0) % 1, 0)
    assert np.allclose(np.where(delta_v >= 1, delta_v, 0) % 1, 0)


EDGES = (
    periodicApproximate(vec2array(ellipse(2, 1).sample(100)[0])).edge(),
    spline([(0, 0), (1, 0)], tgts=((0, 1), (1, 0))),
)

PARAMS = np.array((0, 0.1, 0.5))


@mark.parametrize("e", EDGES)
def test_curve_position(e):

    crv = Curve.fromEdge(e)

    for u in PARAMS:
        assert np.allclose(np.array(e.positionAt(u, mode="param").toTuple()), crv(u))


@mark.parametrize("e", EDGES)
def test_curve_tangents(e):

    crv = Curve.fromEdge(e)

    for u in PARAMS:
        tgt = crv.der(u, 1)[0, 1, :]
        tgt /= np.linalg.norm(tgt)

        assert np.allclose(np.array(e.tangentAt(u, mode="param").toTuple()), tgt)


@fixture
def torus_face():

    t = torus(5, 1).face()

    # double periodic surface
    us = np.linspace(0, 1, endpoint=False)
    vs = np.linspace(0, 1, endpoint=False)

    pts = np.array(
        [t.positionAt(u * 2 * np.pi, v * 2 * np.pi).toTuple() for v in vs for u in us]
    )

    surf = approximate2D(
        pts,
        us[None, :].repeat(len(vs), 0).ravel(),
        vs[:, None].repeat(len(us), 1).ravel(),
        3,
        3,
        50,
        50,
        uperiodic=True,
        vperiodic=True,
        penalty=3,
        lam=1e-6,
    )

    return surf.face()


@fixture
def torus_surf(torus_face):

    return Surface.fromFace(torus_face)


@fixture
def plane_face():

    return plane(1, 1).toNURBS()


FACES = ("torus_face", "plane_face")


@mark.parametrize("face", FACES)
def test_surface_positions(face, request):

    f = request.getfixturevalue(face)
    surf = Surface.fromFace(f)

    for u in PARAMS:
        for v in PARAMS:
            assert np.allclose(f.positionAt(u, v).toTuple(), surf(u, v))


@mark.parametrize("face", FACES)
def test_surface_tangents(face, request):

    f = request.getfixturevalue(face)
    surf = Surface.fromFace(f)

    for u in PARAMS:
        for v in PARAMS:
            dun, dvn, p = f.tangentAt(u, v)
            der = surf.der(u, v, 1).squeeze()
            du = der[1, 0, :]
            dv = der[0, 1, :]

            assert np.allclose(dun.toTuple(), du / np.linalg.norm(du))
            assert np.allclose(dvn.toTuple(), dv / np.linalg.norm(dv))
            assert np.allclose(p.toTuple(), der[0, 0, :])


@mark.parametrize("isoparam", PARAMS)
@mark.parametrize("u", PARAMS)
def test_isolines(torus_surf, isoparam, u):

    uiso = torus_surf.isoline(isoparam)
    viso = torus_surf.isoline(isoparam, "v")

    assert isinstance(uiso, Curve)
    assert isinstance(viso, Curve)

    pt_u = uiso(u)
    pt_v = viso(u)

    # ref
    f = torus_surf.face()
    uiso_ref = f.isoline(isoparam, "u")
    viso_ref = f.isoline(isoparam, "v")

    pt_u_ref = uiso_ref.positionAt(u, mode="param")
    pt_v_ref = viso_ref.positionAt(u, mode="param")

    assert np.allclose(pt_u_ref.toTuple(), pt_u)
    assert np.allclose(pt_v_ref.toTuple(), pt_v)
