from cadquery.occ_impl.shapes import (
    vertex,
    segment,
    polyline,
    polygon,
    rect,
    circle,
    ellipse,
    face,
    plane,
    box,
    cylinder,
    sphere,
    torus,
    cone,
)

from pytest import approx
from math import pi

#%% primitives


def test_vertex():

    v = vertex((1, 2,))

    assert v.isValid()
    assert v.Center().toTuple() == approx((1, 2, 0))

    v = vertex(1, 2, 3)

    assert v.isValid()
    assert v.Center().toTuple() == approx((1, 2, 3))


def test_segment():

    s = segment((0, 0, 0), (0, 0, 1))

    assert s.isValid()
    assert s.Length() == approx(1)


def test_polyline():

    s = polyline((0, 0), (0, 1), (1, 1))

    assert s.isValid()
    assert s.Length() == approx(2)


def test_polygon():

    s = polygon((0, 0), (0, 1), (1, 1), (1, 0))

    assert s.isValid()
    assert s.IsClosed()
    assert s.Length() == approx(4)


def test_rect():

    s = rect(2, 1)

    assert s.isValid()
    assert s.IsClosed()
    assert s.Length() == approx(6)


def test_circle():

    s = circle(1)

    assert s.isValid()
    assert s.IsClosed()
    assert s.Length() == approx(2 * pi)


def test_ellipse():

    s = ellipse(3, 2)

    assert s.isValid()
    assert s.IsClosed()
    assert face(s).Area() == approx(6 * pi)


def test_plane():

    s = plane(1, 2)

    assert s.isValid()
    assert s.Area() == approx(2)


def test_box():

    s = box(1, 1, 1)

    assert s.isValid()
    assert s.Volume() == approx(1)


def test_cylinder():

    s = cylinder(2, 1)

    assert s.isValid()
    assert s.Volume() == approx(pi)


def test_sphere():

    s = sphere(2)

    assert s.isValid()
    assert s.Volume() == approx(4 / 3 * pi)


def test_torus():

    s = torus(10, 2)

    assert s.isValid()
    assert s.Volume() == approx(2 * pi ** 2 * 5)


def test_cone():

    s = cone(2, 1)

    assert s.isValid()
    assert s.Volume() == approx(1 / 3 * pi)

    s = cone(2, 1, 1)

    assert s.isValid()
    assert s.Volume() == approx(1 / 3 * pi * (1 + 0.25 + 0.5))
