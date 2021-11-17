"""
    Copyright (C) 2011-2015  Parametric Products Intellectual Holdings, LLC

    This file is part of CadQuery.

    CadQuery is free software; you can redistribute it and/or
    modify it under the terms of the GNU Lesser General Public
    License as published by the Free Software Foundation; either
    version 2.1 of the License, or (at your option) any later version.

    CadQuery is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
    Lesser General Public License for more details.

    You should have received a copy of the GNU Lesser General Public
    License along with this library; If not, see <http://www.gnu.org/licenses/>
"""

from abc import abstractmethod, ABC
import math
from .occ_impl.geom import Vector
from .occ_impl.shapes import (
    Shape,
    Edge,
    Face,
    Wire,
    Shell,
    Solid,
    geom_LUT_EDGE,
    geom_LUT_FACE,
)
from pyparsing import (
    pyparsing_common,
    Literal,
    Word,
    nums,
    Optional,
    Combine,
    oneOf,
    CaselessLiteral,
    Group,
    infixNotation,
    opAssoc,
    Forward,
    ZeroOrMore,
    Keyword,
)
from functools import reduce
from typing import List, Union, Sequence


class Selector(object):
    """
    Filters a list of objects.

    Filters must provide a single method that filters objects.
    """

    def filter(self, objectList):
        """
        Filter the provided list.

        The default implementation returns the original list unfiltered.
        :param objectList: list to filter
        :type objectList: list of OCCT primitives
        :return: filtered list
        """
        return objectList

    def __and__(self, other):
        return AndSelector(self, other)

    def __add__(self, other):
        return SumSelector(self, other)

    def __sub__(self, other):
        return SubtractSelector(self, other)

    def __neg__(self):
        return InverseSelector(self)


class NearestToPointSelector(Selector):
    """
    Selects object nearest the provided point.

    If the object is a vertex or point, the distance
    is used. For other kinds of shapes, the center of mass
    is used to to compute which is closest.

    Applicability: All Types of Shapes

    Example::

       CQ(aCube).vertices(NearestToPointSelector((0,1,0))

    returns the vertex of the unit cube closest to the point x=0,y=1,z=0

    """

    def __init__(self, pnt):
        self.pnt = pnt

    def filter(self, objectList):
        def dist(tShape):
            return tShape.Center().sub(Vector(*self.pnt)).Length
            # if tShape.ShapeType == 'Vertex':
            #    return tShape.Point.sub(toVector(self.pnt)).Length
            # else:
            #    return tShape.CenterOfMass.sub(toVector(self.pnt)).Length

        return [min(objectList, key=dist)]


class BoxSelector(Selector):
    """
    Selects objects inside the 3D box defined by 2 points.

    If `boundingbox` is True only the objects that have their bounding
    box inside the given box is selected. Otherwise only center point
    of the object is tested.

    Applicability: all types of shapes

    Example::

        CQ(aCube).edges(BoxSelector((0,1,0), (1,2,1))
    """

    def __init__(self, point0, point1, boundingbox=False):
        self.p0 = Vector(*point0)
        self.p1 = Vector(*point1)
        self.test_boundingbox = boundingbox

    def filter(self, objectList):

        result = []
        x0, y0, z0 = self.p0.toTuple()
        x1, y1, z1 = self.p1.toTuple()

        def isInsideBox(p):
            # using XOR for checking if x/y/z is in between regardless
            # of order of x/y/z0 and x/y/z1
            return (
                ((p.x < x0) ^ (p.x < x1))
                and ((p.y < y0) ^ (p.y < y1))
                and ((p.z < z0) ^ (p.z < z1))
            )

        for o in objectList:
            if self.test_boundingbox:
                bb = o.BoundingBox()
                if isInsideBox(Vector(bb.xmin, bb.ymin, bb.zmin)) and isInsideBox(
                    Vector(bb.xmax, bb.ymax, bb.zmax)
                ):
                    result.append(o)
            else:
                if isInsideBox(o.Center()):
                    result.append(o)

        return result


class BaseDirSelector(Selector):
    """
    A selector that handles selection on the basis of a single direction vector.
    """

    def __init__(self, vector: Vector, tolerance: float = 0.0001):
        self.direction = vector
        self.tolerance = tolerance

    def test(self, vec: Vector) -> bool:
        "Test a specified vector. Subclasses override to provide other implementations"
        return True

    def filter(self, objectList: Sequence[Shape]) -> List[Shape]:
        """
        There are lots of kinds of filters, but for planes they are always
        based on the normal of the plane, and for edges on the tangent vector
        along the edge
        """
        r = []
        for o in objectList:
            # no really good way to avoid a switch here, edges and faces are simply different!
            if isinstance(o, Face) and o.geomType() == "PLANE":
                # a face is only parallel to a direction if it is a plane, and
                # its normal is parallel to the dir
                test_vector = o.normalAt(None)
            elif isinstance(o, Edge) and o.geomType() == "LINE":
                # an edge is parallel to a direction if its underlying geometry is plane or line
                test_vector = o.tangentAt()
            else:
                continue

            if self.test(test_vector):
                r.append(o)

        return r


class ParallelDirSelector(BaseDirSelector):
    r"""
    Selects objects parallel with the provided direction.

    Applicability:
        Linear Edges
        Planar Faces

    Use the string syntax shortcut \|(X|Y|Z) if you want to select based on a cardinal direction.

    Example::

        CQ(aCube).faces(ParallelDirSelector((0, 0, 1))

    selects faces with the normal parallel to the z direction, and is equivalent to::

        CQ(aCube).faces("|Z")
    """

    def test(self, vec: Vector) -> bool:
        return self.direction.cross(vec).Length < self.tolerance


class DirectionSelector(BaseDirSelector):
    """
    Selects objects aligned with the provided direction.

    Applicability:
        Linear Edges
        Planar Faces

    Use the string syntax shortcut +/-(X|Y|Z) if you want to select based on a cardinal direction.

    Example::

        CQ(aCube).faces(DirectionSelector((0, 0, 1))

    selects faces with the normal in the z direction, and is equivalent to::

        CQ(aCube).faces("+Z")
    """

    def test(self, vec: Vector) -> bool:
        return self.direction.getAngle(vec) < self.tolerance


class PerpendicularDirSelector(BaseDirSelector):
    """
    Selects objects perpendicular with the provided direction.

    Applicability:
        Linear Edges
        Planar Faces

    Use the string syntax shortcut #(X|Y|Z) if you want to select based on a
    cardinal direction.

    Example::

        CQ(aCube).faces(PerpendicularDirSelector((0, 0, 1))

    selects faces with the normal perpendicular to the z direction, and is equivalent to::

        CQ(aCube).faces("#Z")
    """

    def test(self, vec: Vector) -> bool:
        return abs(self.direction.getAngle(vec) - math.pi / 2) < self.tolerance


class TypeSelector(Selector):
    """
    Selects objects having the prescribed geometry type.

    Applicability:
        Faces: PLANE, CYLINDER, CONE, SPHERE, TORUS, BEZIER, BSPLINE, REVOLUTION, EXTRUSION, OFFSET, OTHER
        Edges: LINE, CIRCLE, ELLIPSE, HYPERBOLA, PARABOLA, BEZIER, BSPLINE, OFFSET, OTHER

    You can use the string selector syntax. For example this::

        CQ(aCube).faces ( TypeSelector("PLANE") )

    will select 6 faces, and is equivalent to::

        CQ(aCube).faces( "%PLANE" )

    """

    def __init__(self, typeString: str):
        self.typeString = typeString.upper()

    def filter(self, objectList: Sequence[Shape]) -> List[Shape]:
        r = []
        for o in objectList:
            if o.geomType() == self.typeString:
                r.append(o)
        return r


class _NthSelector(Selector, ABC):
    """
    An abstract class that provides the methods to select the Nth object/objects of an ordered list.
    """

    def __init__(self, n: int, directionMax: bool = True, tolerance: float = 0.0001):
        self.n = n
        self.directionMax = directionMax
        self.tolerance = tolerance

    def filter(self, objectlist: Sequence[Shape]) -> List[Shape]:
        """
        Return the nth object in the objectlist sorted by self.key and
        clustered if within self.tolerance.
        """
        if len(objectlist) == 0:
            # nothing to filter
            raise ValueError("Can not return the Nth element of an empty list")
        clustered = self.cluster(objectlist)
        if not self.directionMax:
            clustered.reverse()
        try:
            out = clustered[self.n]
        except IndexError:
            raise IndexError(
                f"Attempted to access index {self.n} of a list with length {len(clustered)}"
            )

        return out

    @abstractmethod
    def key(self, obj: Shape) -> float:
        """
        Return the key for ordering. Can raise a ValueError if obj can not be
        used to create a key, which will result in obj being dropped by the
        clustering method.
        """
        raise NotImplementedError

    def cluster(self, objectlist: Sequence[Shape]) -> List[List[Shape]]:
        """
        Clusters the elements of objectlist if they are within tolerance.
        """
        key_and_obj = []
        for obj in objectlist:
            # Need to handle value errors, such as what occurs when you try to
            # access the radius of a straight line
            try:
                key = self.key(obj)
            except ValueError:
                # forget about this element and continue
                continue
            key_and_obj.append((key, obj))
        key_and_obj.sort(key=lambda x: x[0])
        clustered = [[]]  # type: List[List[Shape]]
        start = key_and_obj[0][0]
        for key, obj in key_and_obj:
            if abs(key - start) <= self.tolerance:
                clustered[-1].append(obj)
            else:
                clustered.append([obj])
                start = key
        return clustered


class RadiusNthSelector(_NthSelector):
    """
    Select the object with the Nth radius.

    Applicability:
        All Edge and Wires.

    Will ignore any shape that can not be represented as a circle or an arc of
    a circle.
    """

    def key(self, obj: Shape) -> float:
        if isinstance(obj, (Edge, Wire)):
            return obj.radius()
        else:
            raise ValueError("Can not get a radius from this object")


class CenterNthSelector(_NthSelector):
    """
    Sorts objects into a list with order determined by the distance of their center projected onto the specified direction.

    Applicability:
        All Shapes.
    """

    def __init__(
        self,
        vector: Vector,
        n: int,
        directionMax: bool = True,
        tolerance: float = 0.0001,
    ):
        super().__init__(n, directionMax, tolerance)
        self.direction = vector

    def key(self, obj: Shape) -> float:
        return obj.Center().dot(self.direction)


class DirectionMinMaxSelector(CenterNthSelector):
    """
    Selects objects closest or farthest in the specified direction.

    Applicability:
        All object types. for a vertex, its point is used. for all other kinds
        of objects, the center of mass of the object is used.

    You can use the string shortcuts >(X|Y|Z) or <(X|Y|Z) if you want to select
    based on a cardinal direction.

    For example this::

        CQ(aCube).faces(DirectionMinMaxSelector((0, 0, 1), True)

    Means to select the face having the center of mass farthest in the positive
    z direction, and is the same as::

        CQ(aCube).faces(">Z")

    """

    def __init__(
        self, vector: Vector, directionMax: bool = True, tolerance: float = 0.0001
    ):
        super().__init__(
            n=-1, vector=vector, directionMax=directionMax, tolerance=tolerance
        )


# inherit from CenterNthSelector to get the CenterNthSelector.key method
class DirectionNthSelector(ParallelDirSelector, CenterNthSelector):
    """
    Filters for objects parallel (or normal) to the specified direction then returns the Nth one.

    Applicability:
        Linear Edges
        Planar Faces
    """

    def __init__(
        self,
        vector: Vector,
        n: int,
        directionMax: bool = True,
        tolerance: float = 0.0001,
    ):
        ParallelDirSelector.__init__(self, vector, tolerance)
        _NthSelector.__init__(self, n, directionMax, tolerance)

    def filter(self, objectlist: Sequence[Shape]) -> List[Shape]:
        objectlist = ParallelDirSelector.filter(self, objectlist)
        objectlist = _NthSelector.filter(self, objectlist)
        return objectlist


class LengthNthSelector(_NthSelector):
    """
    Select the object(s) with the Nth length

    Applicability:
        All Edge and Wire objects
    """

    def key(self, obj: Shape) -> float:
        if isinstance(obj, (Edge, Wire)):
            return obj.Length()
        else:
            raise ValueError(
                f"LengthNthSelector supports only Edges and Wires, not {type(obj).__name__}"
            )


class AreaNthSelector(_NthSelector):
    """
    Selects the object(s) with Nth area

    Applicability:
        - Faces, Shells, Solids - Shape.Area() is used to compute area
        - closed planar Wires - a temporary face is created to compute area

    Will ignore non-planar or non-closed wires.

    Among other things can be used to select one of
    the nested coplanar wires or faces.

    For example to create a fillet on a shank::

       result = (
           cq.Workplane("XY")
           .circle(5)
           .extrude(2)
           .circle(2)
           .extrude(10)
           .faces(">Z[-2]")
           .wires(AreaNthSelector(0))
           .fillet(2)
       )

    Or to create a lip on a case seam::

       result = (
           cq.Workplane("XY")
           .rect(20, 20)
           .extrude(10)
           .edges("|Z or <Z")
           .fillet(2)
           .faces(">Z")
           .shell(2)
           .faces(">Z")
           .wires(AreaNthSelector(-1))
           .toPending()
           .workplane()
           .offset2D(-1)
           .extrude(1)
           .faces(">Z[-2]")
           .wires(AreaNthSelector(0))
           .toPending()
           .workplane()
           .cutBlind(2)
       )
    """

    def key(self, obj: Shape) -> float:
        if isinstance(obj, (Face, Shell, Solid)):
            return obj.Area()
        elif isinstance(obj, Wire):
            try:
                return abs(Face.makeFromWires(obj).Area())
            except Exception as ex:
                raise ValueError(
                    f"Can not compute area of the Wire: {ex}. AreaNthSelector supports only closed planar Wires."
                )
        else:
            raise ValueError(
                f"AreaNthSelector supports only Wires, Faces, Shells and Solids, not {type(obj).__name__}"
            )


class BinarySelector(Selector):
    """
    Base class for selectors that operates with two other
    selectors. Subclass must implement the :filterResults(): method.
    """

    def __init__(self, left, right):
        self.left = left
        self.right = right

    def filter(self, objectList):
        return self.filterResults(
            self.left.filter(objectList), self.right.filter(objectList)
        )

    def filterResults(self, r_left, r_right):
        raise NotImplementedError


class AndSelector(BinarySelector):
    """
    Intersection selector. Returns objects that is selected by both selectors.
    """

    def filterResults(self, r_left, r_right):
        # return intersection of lists
        return list(set(r_left) & set(r_right))


class SumSelector(BinarySelector):
    """
    Union selector. Returns the sum of two selectors results.
    """

    def filterResults(self, r_left, r_right):
        # return the union (no duplicates) of lists
        return list(set(r_left + r_right))


class SubtractSelector(BinarySelector):
    """
    Difference selector. Subtract results of a selector from another
    selectors results.
    """

    def filterResults(self, r_left, r_right):
        return list(set(r_left) - set(r_right))


class InverseSelector(Selector):
    """
    Inverts the selection of given selector. In other words, selects
    all objects that is not selected by given selector.
    """

    def __init__(self, selector):
        self.selector = selector

    def filter(self, objectList):
        # note that Selector() selects everything
        return SubtractSelector(Selector(), self.selector).filter(objectList)


def _makeGrammar():
    """
    Define the simple string selector grammar using PyParsing
    """

    # float definition
    point = Literal(".")
    plusmin = Literal("+") | Literal("-")
    number = Word(nums)
    integer = Combine(Optional(plusmin) + number)
    floatn = Combine(integer + Optional(point + Optional(number)))

    # vector definition
    lbracket = Literal("(")
    rbracket = Literal(")")
    comma = Literal(",")
    vector = Combine(
        lbracket + floatn("x") + comma + floatn("y") + comma + floatn("z") + rbracket,
        adjacent=False,
    )

    # direction definition
    simple_dir = oneOf(["X", "Y", "Z", "XY", "XZ", "YZ"])
    direction = simple_dir("simple_dir") | vector("vector_dir")

    # CQ type definition
    cqtype = oneOf(
        set(geom_LUT_EDGE.values()) | set(geom_LUT_FACE.values()), caseless=True,
    )
    cqtype = cqtype.setParseAction(pyparsing_common.upcaseTokens)

    # type operator
    type_op = Literal("%")

    # direction operator
    direction_op = oneOf([">", "<"])

    # center Nth operator
    center_nth_op = oneOf([">>", "<<"])

    # index definition
    ix_number = Group(Optional("-") + Word(nums))
    lsqbracket = Literal("[").suppress()
    rsqbracket = Literal("]").suppress()

    index = lsqbracket + ix_number("index") + rsqbracket

    # other operators
    other_op = oneOf(["|", "#", "+", "-"])

    # named view
    named_view = oneOf(["front", "back", "left", "right", "top", "bottom"])

    return (
        direction("only_dir")
        | (type_op("type_op") + cqtype("cq_type"))
        | (direction_op("dir_op") + direction("dir") + Optional(index))
        | (center_nth_op("center_nth_op") + direction("dir") + Optional(index))
        | (other_op("other_op") + direction("dir"))
        | named_view("named_view")
    )


_grammar = _makeGrammar()  # make a grammar instance


class _SimpleStringSyntaxSelector(Selector):
    """
    This is a private class that converts a parseResults object into a simple
    selector object
    """

    def __init__(self, parseResults):

        # define all token to object mappings
        self.axes = {
            "X": Vector(1, 0, 0),
            "Y": Vector(0, 1, 0),
            "Z": Vector(0, 0, 1),
            "XY": Vector(1, 1, 0),
            "YZ": Vector(0, 1, 1),
            "XZ": Vector(1, 0, 1),
        }

        self.namedViews = {
            "front": (Vector(0, 0, 1), True),
            "back": (Vector(0, 0, 1), False),
            "left": (Vector(1, 0, 0), False),
            "right": (Vector(1, 0, 0), True),
            "top": (Vector(0, 1, 0), True),
            "bottom": (Vector(0, 1, 0), False),
        }

        self.operatorMinMax = {
            ">": True,
            ">>": True,
            "<": False,
            "<<": False,
        }

        self.operator = {
            "+": DirectionSelector,
            "-": lambda v: DirectionSelector(-v),
            "#": PerpendicularDirSelector,
            "|": ParallelDirSelector,
        }

        self.parseResults = parseResults
        self.mySelector = self._chooseSelector(parseResults)

    def _chooseSelector(self, pr):
        """
        Sets up the underlying filters accordingly
        """
        if "only_dir" in pr:
            vec = self._getVector(pr)
            return DirectionSelector(vec)

        elif "type_op" in pr:
            return TypeSelector(pr.cq_type)

        elif "dir_op" in pr:
            vec = self._getVector(pr)
            minmax = self.operatorMinMax[pr.dir_op]

            if "index" in pr:
                return DirectionNthSelector(
                    vec, int("".join(pr.index.asList())), minmax
                )
            else:
                return DirectionMinMaxSelector(vec, minmax)

        elif "center_nth_op" in pr:
            vec = self._getVector(pr)
            minmax = self.operatorMinMax[pr.center_nth_op]

            if "index" in pr:
                return CenterNthSelector(vec, int("".join(pr.index.asList())), minmax)
            else:
                return CenterNthSelector(vec, -1, minmax)

        elif "other_op" in pr:
            vec = self._getVector(pr)
            return self.operator[pr.other_op](vec)

        else:
            args = self.namedViews[pr.named_view]
            return DirectionMinMaxSelector(*args)

    def _getVector(self, pr):
        """
        Translate parsed vector string into a CQ Vector
        """
        if "vector_dir" in pr:
            vec = pr.vector_dir
            return Vector(float(vec.x), float(vec.y), float(vec.z))
        else:
            return self.axes[pr.simple_dir]

    def filter(self, objectList):
        r"""
        selects minimum, maximum, positive or negative values relative to a direction
        ``[+|-|<|>|] <X|Y|Z>``
        """
        return self.mySelector.filter(objectList)


def _makeExpressionGrammar(atom):
    """
    Define the complex string selector grammar using PyParsing (which supports
    logical operations and nesting)
    """

    # define operators
    and_op = Literal("and")
    or_op = Literal("or")
    delta_op = oneOf(["exc", "except"])
    not_op = Literal("not")

    def atom_callback(res):
        return _SimpleStringSyntaxSelector(res)

    # construct a simple selector from every matched
    atom.setParseAction(atom_callback)

    # define callback functions for all operations
    def and_callback(res):
        # take every secend items, i.e. all operands
        items = res.asList()[0][::2]
        return reduce(AndSelector, items)

    def or_callback(res):
        # take every secend items, i.e. all operands
        items = res.asList()[0][::2]
        return reduce(SumSelector, items)

    def exc_callback(res):
        # take every secend items, i.e. all operands
        items = res.asList()[0][::2]
        return reduce(SubtractSelector, items)

    def not_callback(res):
        right = res.asList()[0][1]  # take second item, i.e. the operand
        return InverseSelector(right)

    # construct the final grammar and set all the callbacks
    expr = infixNotation(
        atom,
        [
            (and_op, 2, opAssoc.LEFT, and_callback),
            (or_op, 2, opAssoc.LEFT, or_callback),
            (delta_op, 2, opAssoc.LEFT, exc_callback),
            (not_op, 1, opAssoc.RIGHT, not_callback),
        ],
    )

    return expr


_expression_grammar = _makeExpressionGrammar(_grammar)


class StringSyntaxSelector(Selector):
    r"""
    Filter lists objects using a simple string syntax. All of the filters available in the string syntax
    are also available ( usually with more functionality ) through the creation of full-fledged
    selector objects. see :py:class:`Selector` and its subclasses

    Filtering works differently depending on the type of object list being filtered.

    :param selectorString: A two-part selector string, [selector][axis]

    :return: objects that match the specified selector

    ***Modifiers*** are ``('|','+','-','<','>','%')``

        :\|:
            parallel to ( same as :py:class:`ParallelDirSelector` ). Can return multiple objects.
        :#:
            perpendicular to (same as :py:class:`PerpendicularDirSelector` )
        :+:
            positive direction (same as :py:class:`DirectionSelector` )
        :-:
            negative direction (same as :py:class:`DirectionSelector`  )
        :>:
            maximize (same as :py:class:`DirectionMinMaxSelector` with directionMax=True)
        :<:
            minimize (same as :py:class:`DirectionMinMaxSelector` with directionMax=False )
        :%:
            curve/surface type (same as :py:class:`TypeSelector`)

    ***axisStrings*** are: ``X,Y,Z,XY,YZ,XZ`` or ``(x,y,z)`` which defines an arbitrary direction

    It is possible to combine simple selectors together using logical operations.
    The following operations are supported

        :and:
            Logical AND, e.g. >X and >Y
        :or:
            Logical OR, e.g. \|X or \|Y
        :not:
            Logical NOT, e.g. not #XY
        :exc(ept):
            Set difference (equivalent to AND NOT): \|X exc >Z

    Finally, it is also possible to use even more complex expressions with nesting
    and arbitrary number of terms, e.g.

        (not >X[0] and #XY) or >XY[0]

    Selectors are a complex topic: see :ref:`selector_reference` for more information
    """

    def __init__(self, selectorString):
        """
        Feed the input string through the parser and construct an relevant complex selector object
        """
        self.selectorString = selectorString
        parse_result = _expression_grammar.parseString(selectorString, parseAll=True)
        self.mySelector = parse_result.asList()[0]

    def filter(self, objectList):
        """
        Filter give object list through th already constructed complex selector object
        """
        return self.mySelector.filter(objectList)
