from cadquery.sketch import Sketch, Vector

from math import pi


def test_assemble():

    s1 = Sketch()
    s1.segment((0.0, 0), (0.0, 2.0))
    s1.segment(Vector(4.0, -1)).close().arc((0.7, 0.6), 0.4, 0.0, 360.0).assemble()


def test_constraints():

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

    s2.solve()

    assert s1._solve_status["status"] == 4

    s2.assemble()

    assert s1._faces.isValid()
