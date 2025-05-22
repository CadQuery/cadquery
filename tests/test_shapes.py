from cadquery.occ_impl.shapes import (
    Vector,
    Shape,
    Solid,
    wire,
    segment,
    polyline,
    box,
    compound,
    circle,
    plane,
    torus,
    cylinder,
    ellipse,
    spline,
    sweep,
    polygon,
    wireOn,
)

from pytest import approx, raises

from math import pi


def test_edge_paramAt():

    # paramAt for a segment
    e = segment((0, 0), (0, 1))

    p1 = e.paramAt(Vector(0, 0))
    p2 = e.paramAt(Vector(-1, 0))
    p3 = e.paramAt(Vector(0, 1))

    assert p1 == approx(p2)
    assert p1 == approx(0)
    assert p3 == approx(e.paramAt(1))

    # paramAt for a simple wire
    w1 = wire(e)

    p4 = w1.paramAt(Vector(0, 0))
    p5 = w1.paramAt(Vector(0, 1))

    assert p4 == approx(p1)
    assert p5 == approx(p3)

    # paramAt for a complex wire
    w2 = polyline((0, 0), (0, 1), (1, 1))

    p6 = w2.paramAt(Vector(0, 0))
    p7 = w2.paramAt(Vector(0, 1))
    p8 = w2.paramAt(Vector(0.1, 0.1))

    assert p6 == approx(w2.paramAt(0))
    assert p7 == approx(w2.paramAt(0.5))
    assert p8 == approx(w2.paramAt(0.1 / 2))


def test_face_paramAt():

    f = plane(1, 1)

    u, v = f.paramAt((0.5, 0))

    assert u == approx(0.5)
    assert v == approx(0.0)


def test_face_params():

    f = plane(1, 1)

    us, vs = f.params([(0.49, 0.0), (0.5, 0)])

    u1, u2 = us
    v1, v2 = vs

    assert u1 == approx(0.49)
    assert v1 == approx(0.0)

    assert u2 == approx(0.5)
    assert v2 == approx(0.0)


def test_face_positionAt():

    f = plane(1, 1)

    p = f.positionAt(0.5, 0.5)

    assert p.x == approx(0.5)
    assert p.y == approx(0.5)
    assert p.z == approx(0)


def test_face_positions():

    f = plane(1, 1)

    ps = f.positions([(0, 0), (0.5, 0.5)])

    p1, p2 = ps

    assert p1.x == approx(0)
    assert p1.y == approx(0)
    assert p1.z == approx(0)

    assert p2.x == approx(0.5)
    assert p2.y == approx(0.5)
    assert p2.z == approx(0)


def test_edge_params():

    e = spline([(0, 0), (1, 0), (1, 1), (2, 0), (2, -1)], periodic=True)
    N = 5

    pts_orig = e.sample(N)[0]
    pts = [pt + Vector(0, 0, 1e-1) for pt in pts_orig]

    ps = e.params(pts)

    for i in range(N):
        assert (e.positionAt(ps[i], mode="parameter") - pts_orig[i]).Length == approx(0)


def test_edge_tangents():

    e = circle(1)

    tgts = e.tangents([0, 1], mode="length")

    assert (tgts[0] - Vector(0, 1, 0)).Length == approx(0)
    assert (tgts[0] - tgts[1]).Length == approx(0)

    tgts = e.tangents([0, pi], mode="parameter")

    assert (tgts[1] - Vector(0, -1, 0)).Length == approx(0)
    assert (tgts[0] - tgts[1]).Length == approx(2)


def test_isSolid():

    s = box(1, 1, 1)

    assert Solid.isSolid(s)
    assert Solid.isSolid(compound(s))
    assert not Solid.isSolid(s.faces())


def test_shells():

    s = box(2, 2, 2) - box(1, 1, 1).moved(z=0.5)

    assert s.outerShell().Area() == approx(6 * 4)
    assert len(s.innerShells()) == 1
    assert s.innerShells()[0].Area() == approx(6 * 1)


def test_curvature():

    r = 10

    c = circle(r)
    w = polyline((0, 0), (1, 0), (1, 1))

    assert c.curvatureAt(0) == approx(1 / r)

    curvatures = c.curvatures([0, 0.5])

    assert approx(curvatures[0]) == curvatures[1]

    assert w.curvatureAt(0) == approx(w.curvatureAt(0.5))


def test_normals():

    r1 = 10
    r2 = 1

    t = torus(2 * r1, 2 * r2).faces()

    n1 = t.normalAt((r1, 0, r2))
    n2 = t.normalAt((r1 + r2, 0))

    assert n1.toTuple() == approx((0, 0, 1))
    assert n2.toTuple() == approx((1, 0, 0))

    n3, p3 = t.normalAt(0, 0)

    assert n3.toTuple() == approx((1, 0, 0))
    assert p3.toTuple() == approx((r1 + r2, 0, 0))

    (n4, n5), _ = t.normals((0, 0), (0, pi / 2))

    assert n4.toTuple() == approx((1, 0, 0))
    assert n5.toTuple() == approx((0, 0, 1))


def test_trimming():

    e = segment((0, 0), (0, 1))
    f = plane(1, 1)

    # edge trim
    assert e.trim(0, 0.5).Length() == approx(e.Length() / 2)

    # face trim
    assert f.trim(0, 0.5, -0.5, 0.5).Area() == approx(f.Area() / 2)

    # face trim using wires
    assert f.trim(
        wireOn(f, polygon((0, -0.5), (0.5, -0.5), (0.5, 0.5), (0, 0.5)))
    ).Area() == approx(f.Area() / 2)

    # face trim using wires - single edge case
    assert f.trim(wireOn(f, circle(1))).isValid()

    # face trim using points
    assert f.trim((0, -0.5), (0.5, -0.5), (0.5, 0.5), (0, 0.5)).Area() == approx(
        f.Area() / 2
    )


def test_bin_import_export():

    b = box(1, 1, 1)

    from io import BytesIO

    bio = BytesIO()

    b.exportBin(bio)
    bio.seek(0)

    r = Shape.importBin(bio)

    assert r.isValid()
    assert r.Volume() == approx(1)

    with raises(Exception):
        Shape.importBin(BytesIO())


def test_sample():

    e = ellipse(10, 1)
    s = segment((0, 0), (1, 0))

    pts1, params1 = e.sample(10)  # equidistant
    pts2, params2 = e.sample(0.1)  # deflection based
    pts3, params3 = s.sample(10)  # equidistant, open

    assert len(pts1) == len(params1)
    assert len(pts1) == 10  # e is closed

    assert len(pts2) == len(params2)
    assert len(pts2) == 16

    assert len(pts3) == len(params3)
    assert len(pts3) == 10  # s is open


def test_isolines():

    c = cylinder(1, 2).faces("%CYLINDER")

    isos_v = c.isolines([0, 1])
    isos_u = c.isolines([0, 1], "u")

    assert len(isos_u) == 2
    assert len(isos_v) == 2

    assert isos_u[0].Length() == approx(2)
    assert isos_v[0].Length() == approx(pi)


def test_extend():

    f = sweep(spline((0, 0), (0, 1), (2, 0)), spline((0, 0, 0), (0, 1, 1), (0, 1, 5)))
    f_ext = f.extend(1)

    assert f_ext.Area() > f.Area()


def test_remove():

    b = box(2, 2, 2) - box(1, 1, 1).moved(z=0.5)

    assert len(b.Faces()) == 12

    br = b.remove(*b.innerShells())

    assert len(br.Faces()) == 6
    assert br.isValid()


def test_addCavity():

    b1 = box(2, 2, 2)
    b2 = box(1, 1, 1).moved(z=0.5)

    br = b1.addCavity(b2)

    assert len(br.Faces()) == 12
    assert len(br.Shells()) == 2
    assert br.isValid()


def test_replace():

    b = box(1, 1, 1)
    f_top = b.faces(">Z")
    f_top_split = f_top / plane(0.5, 0.5).moved(f_top.Center())

    br1 = b.replace(f_top, f_top_split)

    assert len(br1.Faces()) == len(b.Faces()) + 1
    assert br1.isValid()

    br2 = b.replace(f_top, *f_top_split)  # invoke with individual faces

    assert len(br2.Faces()) == len(b.Faces()) + 1
    assert br2.isValid()


def test_addHole():

    f = plane(1, 1)
    c = circle(0.1)

    f1 = f.addHole(c)

    assert len(f1.innerWires()) == 1
    assert f1.isValid()

    f2 = f.addHole(wire(c))

    assert len(f2.innerWires()) == 1
    assert f2.isValid()

    f3 = f.addHole(*c.moved((-0.3, 0), (0.3, 0)))

    assert len(f3.innerWires()) == 2
    assert f3.isValid()
