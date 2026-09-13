from itertools import permutations
from math import pi

import pytest

import cadquery as cq
from cadquery import hull


def test_hull():

    c1 = cq.Edge.makeCircle(0.5, (-1.5, 0.5, 0))
    c2 = cq.Edge.makeCircle(0.5, (1.9, 0.0, 0))
    c3 = cq.Edge.makeCircle(0.2, (0.3, 1.5, 0))
    c4 = cq.Edge.makeCircle(0.2, (1.0, 1.5, 0))
    c5 = cq.Edge.makeCircle(0.1, (0.0, 0.0, 0.0))
    e1 = cq.Edge.makeLine(cq.Vector(0, -0.5), cq.Vector(-0.5, 1.5))
    e2 = cq.Edge.makeLine(cq.Vector(2.1, 1.5), cq.Vector(2.6, 1.5))

    edges = [c1, c2, c3, c4, c5, e1, e2]

    h = hull.find_hull(edges)

    assert len(h.Vertices()) == 11
    assert h.IsClosed()
    assert h.isValid()


def test_validation():

    with pytest.raises(ValueError):

        e1 = cq.Edge.makeEllipse(2, 1)
        c1 = cq.Edge.makeCircle(0.5, (-1.5, 0.5, 0))
        hull.find_hull([c1, e1])


def test_collinear():

    r = 2.5
    spacing = 8.0

    # collinear centres let an inner circle enter the hull as a zero span arc;
    # only some traversal orders reach it, so permute the input
    for n in (3, 4, 5):

        expected = spacing * (n - 1) * 2 * r + pi * r ** 2

        for order in permutations(range(n)):

            edges = [cq.Edge.makeCircle(r, (i * spacing, 0, 0)) for i in order]

            h = hull.find_hull(edges)

            assert h.IsClosed()
            assert h.isValid()
            assert cq.Face.makeFromWires(h).Area() == pytest.approx(expected)


def test_eq():

    a = hull.Arc(hull.Point(0.0, 0.0), 1.0, 0.0, 2 * pi)
    b = hull.Arc(hull.Point(0.0, 0.0), 1.0, 0.0, 2 * pi)
    p = hull.Point(0.0, 0.0)

    assert a == b
    assert hash(a) == hash(b)
    assert p == hull.Point(0.0, 0.0)

    assert a != hull.Arc(hull.Point(0.0, 0.0), 2.0, 0.0, 2 * pi)
    assert a != p
    assert p != a
    assert a != None
