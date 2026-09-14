from itertools import permutations
from math import pi

import pytest

import cadquery as cq
from cadquery import hull


def area(edges):
    return cq.Face.makeFromWires(hull.find_hull(edges)).Area()


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

    p = hull.Point(0.0, 0.0)

    assert p == hull.Point(0.0, 0.0)
    assert hash(p) == hash(hull.Point(0.0, 0.0))

    assert p != hull.Point(1.0, 0.0)
    assert p != hull.Arc(p, 1.0, 0.0, 2 * pi)
    assert p != None


def test_lines_only():
    edges = [
        cq.Edge.makeLine(cq.Vector(0, 0), cq.Vector(4, 0)),
        cq.Edge.makeLine(cq.Vector(4, 0), cq.Vector(0, 3)),
        cq.Edge.makeLine(cq.Vector(0, 3), cq.Vector(0, 0)),
    ]

    assert area(edges) == pytest.approx(6.0)


def test_empty():
    with pytest.raises(ValueError):
        hull.find_hull([])


def test_arc_inside_hull():
    outer = [cq.Edge.makeCircle(20.0, (0, 0, 0)), cq.Edge.makeCircle(20.0, (60, 0, 0))]
    arc = cq.Edge.makeCircle(5.0, (30, 0, 0), angle1=0, angle2=180)

    assert area(outer + [arc]) == pytest.approx(area(outer))


def test_single_circle():
    assert area([cq.Edge.makeCircle(5.0, (0, 0, 0))]) == pytest.approx(25 * pi)


def test_march_closes():
    edges = [
        cq.Edge.makeCircle(6.0, (0, 12, 0)),
        cq.Edge.makeLine(cq.Vector(-2, 5), cq.Vector(9, 10)),
    ]

    h = cq.Face.makeFromWires(hull.find_hull(edges))

    for v in edges[1].Vertices():
        assert h.distance(v) == pytest.approx(0.0)


def test_arc_endpoints():
    a = hull.Arc(hull.Point(10.0, 20.0), 1.0, 0.0, pi)

    assert (a.s.x, a.s.y) == pytest.approx((11.0, 20.0))
    assert (a.e.x, a.e.y) == pytest.approx((9.0, 20.0))


@pytest.mark.parametrize(
    "inner",
    [
        cq.Edge.makeCircle(5.0, (2, 0, 0)),
        cq.Edge.makeLine(cq.Vector(-3, 0), cq.Vector(3, 0)),
        cq.Edge.makeLine(cq.Vector(0, 20), cq.Vector(0, 10)),
    ],
    ids=["circle", "line", "line from the circle"],
)
def test_geometry_inside_circle(inner):
    outer = [cq.Edge.makeCircle(20.0, (0, 0, 0)), cq.Edge.makeCircle(20.0, (60, 5, 0))]

    assert area(outer + [inner]) == pytest.approx(area(outer))


def test_circle_with_nested_only():
    edges = [cq.Edge.makeCircle(20.0, (0, 0, 0)), cq.Edge.makeCircle(5.0, (2, 0, 0))]

    assert area(edges) == pytest.approx(400 * pi)


def test_coincident_arcs():
    # the start is the circle's bottom only if the halves are read as one circle
    halves = [
        cq.Edge.makeCircle(5.0, (0, 0, 0), angle1=0, angle2=180),
        cq.Edge.makeCircle(5.0, (0, 0, 0), angle1=180, angle2=360),
    ]
    segment = cq.Edge.makeLine(cq.Vector(-2, -3), cq.Vector(2, -3))

    for order in permutations(halves):
        assert area(list(order) + [segment]) == pytest.approx(25 * pi)


def test_intersecting_circles():
    # a fuse splits each circle at the seam and at the intersections
    edges = cq.Sketch().push([(-19, 0), (19, 0)]).circle(35).reset()._faces.Edges()

    assert len(edges) == 6
    assert area(edges) == pytest.approx(38 * 70 + pi * 35 ** 2)


def test_hull_contains_input():
    # the line end at (20, 0) lies on the +x axis of the circle, the 0/2pi seam
    edges = [
        cq.Edge.makeCircle(5.0, (0, 0, 0)),
        cq.Edge.makeLine(cq.Vector(20, 0), cq.Vector(20, 10)),
    ]

    h = cq.Face.makeFromWires(hull.find_hull(edges))

    assert h.distance(cq.Vertex.makeVertex(20, 0, 0)) == pytest.approx(0.0)


def test_rotation_invariance():
    def shape(dx, dy):
        return [
            cq.Edge.makeCircle(20.0, (0, 0, 0)),
            cq.Edge.makeCircle(10.0, (dx, dy, 0)),
            cq.Edge.makeCircle(10.0, (-dx, -dy, 0)),
        ]

    assert area(shape(0, 40)) == pytest.approx(area(shape(40, 0)))


# temporary: two plain circles stall the march until the arc rework (3/3)
@pytest.mark.xfail(strict=True, raises=ValueError, reason="fixed by the arc rework")
def test_two_circles():
    edges = [
        cq.Edge.makeCircle(0.7, (-3.8, 2.9, 0)),
        cq.Edge.makeCircle(2.4, (0.8, 4.6, 0)),
    ]

    assert area(edges) == pytest.approx(25.943, abs=1e-3)
