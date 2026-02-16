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


def test_hull_overlapping_circles():
    """Hull of overlapping circles should not raise ZeroDivisionError.

    When two circles overlap, boolean face fusion splits them into
    multiple arc segments sharing the same center. arc_arc() must
    handle these concentric arcs without dividing by zero.
    """
    from cadquery import Sketch

    s = Sketch().push([(-19, 0), (19, 0)]).circle(35).reset().hull()

    assert s._faces.Area() > 0
    assert len(s._faces.Faces()) >= 1


def test_hull_overlapping_circles_equal_radii_via_face():
    """Hull via .face() with overlapping equal-radii circles."""
    from cadquery import Sketch, Location, Vector

    s = (
        Sketch()
        .face(Sketch().circle(35).moved(Location(Vector(-19, 0, 0))))
        .face(Sketch().circle(35).moved(Location(Vector(19, 0, 0))))
        .hull()
    )

    assert s._faces.Area() > 0
    assert len(s._faces.Faces()) >= 1


def test_validation():

    with pytest.raises(ValueError):

        e1 = cq.Edge.makeEllipse(2, 1)
        c1 = cq.Edge.makeCircle(0.5, (-1.5, 0.5, 0))
        hull.find_hull([c1, e1])
