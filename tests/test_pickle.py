from pickle import loads, dumps

from cadquery import (
    Vector,
    Matrix,
    Plane,
    Location,
    Shape,
    Sketch,
    Assembly,
    Color,
    Workplane,
)
from cadquery.func import box

from pytest import mark


@mark.parametrize(
    "obj",
    [
        Vector(2, 3, 4),
        Matrix(),
        Plane((-2, 1, 1)),
        Location(1, 2, 4),
        Sketch().rect(1, 1),
        Color("red"),
        Workplane().sphere(1),
    ],
)
def test_simple(obj):

    assert isinstance(loads(dumps(obj)), type(obj))


def test_shape():

    s = Shape(box(1, 1, 1).wrapped)

    assert isinstance(loads(dumps(s)), Shape)


def test_assy():

    assy = Assembly().add(box(1, 1, 1), color=Color("blue")).add(box(2, 2, 2))

    assert isinstance(loads(dumps(assy)), Assembly)
