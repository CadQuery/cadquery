from cadquery.sketch import Sketch, Vector

from pytest import approx, raises
from math import pi, sqrt


def test_face_interface():

    s1 = Sketch().rect(1, 2, 45)

    assert s1._faces.Area() == approx(2)
    assert s1.vertices(">X")._selection[0].toTuple()[0] == approx(1.5 / sqrt(2))

    s2 = Sketch().circle(1)

    assert s2._faces.Area() == approx(pi)

    s3 = Sketch().ellipse(2, 0.5)

    assert s3._faces.Area() == approx(pi)

    s4 = Sketch().trapezoid(2, 0.5, 45)

    assert s4._faces.Area() == approx(0.75)

    s4 = Sketch().trapezoid(2, 0.5, 45)

    assert s4._faces.Area() == approx(0.75)

    s5 = Sketch().slot(3, 2)

    assert s5._faces.Area() == approx(6 + pi)
    assert s5.edges(">Y")._selection[0].Length() == approx(3)

    s6 = Sketch().regularPolygon(1, 5)

    assert len(s6.vertices()._selection) == 5
    assert s6.vertices(">Y")._selection[0].toTuple()[1] == approx(1)

    s7 = Sketch().polygon([(0, 0), (0, 1), (1, 0)])

    assert len(s7.vertices()._selection) == 3
    assert s7._faces.Area() == approx(0.5)


def test_modes():

    s1 = Sketch().rect(2, 2).rect(1, 1, mode="a")

    assert s1._faces.Area() == approx(4)
    assert len(s1._faces.Faces()) == 2

    s2 = Sketch().rect(2, 2).rect(1, 1, mode="s")

    assert s2._faces.Area() == approx(4 - 1)
    assert len(s2._faces.Faces()) == 1

    s3 = Sketch().rect(2, 2).rect(1, 1, mode="i")

    assert s3._faces.Area() == approx(1)
    assert len(s3._faces.Faces()) == 1

    s4 = Sketch().rect(2, 2).rect(1, 1, mode="c", tag="t")

    assert s4._faces.Area() == approx(4)
    assert len(s4._faces.Faces()) == 1
    assert s4._tags["t"][0].Area() == approx(1)

    with raises(ValueError):
        Sketch().rect(2, 2).rect(1, 1, mode="c")

    with raises(ValueError):
        Sketch().rect(2, 2).rect(1, 1, mode="dummy")


def test_distribute():

    pass


def test_modifiers():

    pass


def test_edge_interface():

    pass


def test_assemble():

    s1 = Sketch()
    s1.segment((0.0, 0), (0.0, 2.0))
    s1.segment(Vector(4.0, -1)).close().arc((0.7, 0.6), 0.4, 0.0, 360.0).assemble()


def test_constraint_validation():

    with raises(ValueError):
        Sketch().segment(1.0, 1.0, "s").constrain("s", "Dummy", None)

    with raises(ValueError):
        Sketch().segment(1.0, 1.0, "s").constrain("s", "s", "Fixed", None)

    with raises(ValueError):
        Sketch().spline([(1.0, 1.0), (2.0, 1.0), (0.0, 0.0)], "s").constrain(
            "s", "Fixed", None
        )

    with raises(ValueError):
        Sketch().segment(1.0, 1.0, "s").constrain("s", "Fixed", 1)


def test_constraint_solver():

    s1 = (
        Sketch()
        .segment((0.0, 0), (0.0, 2.0), "s1")
        .segment((0.5, 2.5), (1.0, 1), "s2")
        .close("s3")
    )
    s1.constrain("s1", "Fixed", None)
    s1.constrain("s1", "s2", "Coincident", None)
    s1.constrain("s2", "s3", "Coincident", None)
    s1.constrain("s3", "s1", "Coincident", None)
    s1.constrain("s3", "s1", "Angle", pi / 2)
    s1.constrain("s2", "s3", "Angle", pi - pi / 4)

    s1.solve()

    assert s1._solve_status["status"] == 4

    s1.assemble()

    assert s1._faces.isValid()

    s2 = (
        Sketch()
        .arc((0.0, 0.0), (-0.5, 0.5), (0.0, 1.0), "a1")
        .arc((0.0, 1.0), (0.5, 1.5), (1.0, 1.0), "a2")
        .segment((1.0, 0.0), "s1")
        .close("s2")
    )

    s2.constrain("s2", "Fixed", None)
    s2.constrain("s1", "s2", "Coincident", None)
    s2.constrain("a2", "s1", "Coincident", None)
    s2.constrain("s2", "a1", "Coincident", None)
    s2.constrain("a1", "a2", "Coincident", None)
    s2.constrain("s1", "s2", "Angle", pi / 2)
    s2.constrain("s2", "a1", "Angle", pi / 2)
    s2.constrain("a1", "a2", "Angle", -pi / 2)
    s2.constrain("a2", "s1", "Angle", pi / 2)
    s2.constrain("s1", "Length", 0.5)
    s2.constrain("a1", "Length", 1.0)

    s2.solve()

    assert s2._solve_status["status"] == 4

    s2.assemble()

    assert s2._faces.isValid()

    s2._tags["s1"][0].Length() == approx(0.5)
    s2._tags["a1"][0].Length() == approx(1.0)

    s3 = (
        Sketch()
        .arc((0.0, 0.0), (-0.5, 0.5), (0.0, 1.0), "a1")
        .segment((1.0, 0.0), "s1")
        .close("s2")
    )

    s3.constrain("s2", "Fixed", None)
    s3.constrain("a1", "ArcAngle", pi / 3)
    s3.constrain("a1", "Radius", 1.0)
    s3.constrain("s2", "a1", "Coincident", None)
    s3.constrain("a1", "s1", "Coincident", None)
    s3.constrain("s1", "s2", "Coincident", None)

    s3.solve()

    assert s3._solve_status["status"] == 4

    s3.assemble()

    assert s3._faces.isValid()

    s3._tags["a1"][0].radius() == approx(1)
    s3._tags["a1"][0].Length() == approx(pi / 3)

    s4 = (
        Sketch()
        .arc((0.0, 0.0), (-0.5, 0.5), (0.0, 1.0), "a1")
        .segment((1.0, 0.0), "s1")
        .close("s2")
    )

    s4.constrain("s2", "Fixed", None)
    s4.constrain("s1", "Orientation", (-1.0, -1.0))
    s4.constrain("s1", "s2", "Distance", (0.0, 0.5, 2.0))
    s4.constrain("s2", "a1", "Coincident", None)
    s4.constrain("a1", "s1", "Coincident", None)
    s4.constrain("s1", "s2", "Coincident", None)

    s4.solve()

    assert s4._solve_status["status"] == 4

    s4.assemble()

    assert s4._faces.isValid()

    seg1 = s4._tags["s1"][0]
    seg2 = s4._tags["s2"][0]

    assert (seg1.endPoint() - seg1.startPoint()).getAngle(Vector(-1, -1)) == approx(
        0, abs=1e-9
    )

    midpoint = (seg2.startPoint() + seg2.endPoint()) / 2

    (midpoint - seg1.startPoint()).Length == approx(2)
