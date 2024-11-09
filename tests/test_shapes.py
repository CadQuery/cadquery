from cadquery.occ_impl.shapes import (
    wire,
    segment,
    polyline,
    Vector,
    box,
    Solid,
    compound,
    circle,
    plane,
    torus,
)

from pytest import approx


def test_paramAt():

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

    d1 = 10
    d2 = 1

    (t,) = torus(d1, d2).faces()

    n1 = t.normalAt((d1, d2))
    n2 = t.normalAt((d1 + d2, 0))

    assert approx(n1.toTuple()) == (0, 0, 1)
    assert approx(n2.toTuple()) == (1, 0, 0)

    n2, n3 = t.normals([(d1, d2), (d1 + d2, 0)])

    assert approx(n2.toTuple()) == (0, 0, 1)
    assert approx(n3.toTuple()) == (1, 0, 0)


def test_trimming():

    e = segment((0, 0), (0, 1))
    f = plane(1, 1)

    assert e.trim(0, 0.5).Length() == approx(e.Lengnth() / 2)
    assert f.trim(0, 0.5, -0.5, 0.5).Area() == approx(f.Area() / 2)
