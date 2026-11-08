from copy import copy, deepcopy
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
    Material,
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


@mark.parametrize(
    "copier",
    [copy, deepcopy, lambda obj: loads(dumps(obj))],
    ids=["copy", "deepcopy", "pickle"],
)
def test_shape_type(copier):
    """
    Copying or unpickling a shape keeps its specialized TopoDS type
    (e.g. TopoDS_Solid), as constructing it does.
    """

    s = box(1, 1, 1)

    for obj in (s, s.Faces()[0], s.Edges()[0], s.Vertices()[0]):
        assert type(copier(obj).wrapped) is type(obj.wrapped)


def test_null_shape():
    """
    Unpickling a null shape keeps it null rather than raising.
    """

    s = box(1, 1, 1)
    s.wrapped.Nullify()

    assert loads(dumps(s)).wrapped.IsNull()


def test_assy():

    mat_1 = Material(
        "test", description="Test material", density=1.0, densityUnit="lb/in^3"
    )

    assy = (
        Assembly()
        .add(box(1, 1, 1), color=Color("blue"), material=mat_1)
        .add(box(2, 2, 2))
    )

    assert isinstance(loads(dumps(assy)), Assembly)
