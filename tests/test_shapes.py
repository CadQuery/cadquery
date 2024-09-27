from cadquery.occ_impl.shapes import (
    wire,
    segment,
    polyline,
    Vector,
    box,
    Solid,
    compound,
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
