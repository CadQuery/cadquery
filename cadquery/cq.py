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

import math
from copy import copy
from itertools import chain
from typing import (
    overload,
    Sequence,
    TypeVar,
    Union,
    Tuple,
    Optional,
    Any,
    Iterable,
    Callable,
    List,
    cast,
    Dict,
)
from typing_extensions import Literal
from inspect import Parameter, Signature


from .occ_impl.geom import Vector, Plane, Location
from .occ_impl.shapes import (
    Shape,
    Edge,
    Wire,
    Face,
    Solid,
    Compound,
    wiresToFaces,
)

from .occ_impl.exporters.svg import getSVG, exportSVG

from .utils import deprecate, deprecate_kwarg_name

from .selectors import (
    Selector,
    StringSyntaxSelector,
)

from .sketch import Sketch

CQObject = Union[Vector, Location, Shape, Sketch]
VectorLike = Union[Tuple[float, float], Tuple[float, float, float], Vector]
CombineMode = Union[bool, Literal["cut", "a", "s"]]  # a : additive, s: subtractive
TOL = 1e-6

T = TypeVar("T", bound="Workplane")
"""A type variable used to make the return type of a method the same as the
type of `self` or another argument.

This is useful when you want to allow a class to derive from
:class:`.Workplane`, and you want a (fluent) method in the derived class to
return an instance of the derived class, rather than of :class:`.Workplane`.
"""


def _selectShapes(objects: Iterable[Any]) -> List[Shape]:

    return [el for el in objects if isinstance(el, Shape)]


class CQContext(object):
    """
    A shared context for modeling.

    All objects in the same CQ chain share a reference to this same object instance
    which allows for shared state when needed.
    """

    pendingWires: List[Wire]
    pendingEdges: List[Edge]
    firstPoint: Optional[Vector]
    tolerance: float
    tags: Dict[str, "Workplane"]

    def __init__(self):
        self.pendingWires = (
            []
        )  # a list of wires that have been created and need to be extruded
        # a list of created pending edges that need to be joined into wires
        self.pendingEdges = []
        # a reference to the first point for a set of edges.
        # Used to determine how to behave when close() is called
        self.firstPoint = None
        self.tolerance = 0.0001  # user specified tolerance
        self.tags = {}

    def popPendingEdges(self, errorOnEmpty: bool = True) -> List[Edge]:
        """
        Get and clear pending edges.

        :raises ValueError: if errorOnEmpty is True and no edges are present.
        """
        if errorOnEmpty and not self.pendingEdges:
            raise ValueError("No pending edges present")
        out = self.pendingEdges
        self.pendingEdges = []
        return out

    def popPendingWires(self, errorOnEmpty: bool = True) -> List[Wire]:
        """
        Get and clear pending wires.

        :raises ValueError: if errorOnEmpty is True and no wires are present.
        """
        if errorOnEmpty and not self.pendingWires:
            raise ValueError("No pending wires present")
        out = self.pendingWires
        self.pendingWires = []
        return out


class Workplane(object):
    """
    Defines a coordinate system in space, in which 2D coordinates can be used.

    :param plane: the plane in which the workplane will be done
    :type plane: a Plane object, or a string in (XY|YZ|XZ|front|back|top|bottom|left|right)
    :param origin: the desired origin of the new workplane
    :type origin: a 3-tuple in global coordinates, or None to default to the origin
    :param obj: an object to use initially for the stack
    :type obj: a CAD primitive, or None to use the centerpoint of the plane as the initial
        stack value.
    :raises: ValueError if the provided plane is not a plane, a valid named workplane
    :return: A Workplane object, with coordinate system matching the supplied plane.

    The most common use is::

        s = Workplane("XY")

    After creation, the stack contains a single point, the origin of the underlying plane,
    and the *current point* is on the origin.

    .. note::
        You can also create workplanes on the surface of existing faces using
        :py:meth:`CQ.workplane`
    """

    objects: List[CQObject]
    ctx: CQContext
    parent: Optional["Workplane"]
    plane: Plane

    _tag: Optional[str]

    @overload
    def __init__(self, obj: CQObject) -> None:
        ...

    @overload
    def __init__(
        self,
        inPlane: Union[Plane, str] = "XY",
        origin: VectorLike = (0, 0, 0),
        obj: Optional[CQObject] = None,
    ) -> None:
        ...

    def __init__(self, inPlane="XY", origin=(0, 0, 0), obj=None):
        """
        make a workplane from a particular plane

        :param inPlane: the plane in which the workplane will be done
        :type inPlane: a Plane object, or a string in (XY|YZ|XZ|front|back|top|bottom|left|right)
        :param origin: the desired origin of the new workplane
        :type origin: a 3-tuple in global coordinates, or None to default to the origin
        :param obj: an object to use initially for the stack
        :type obj: a CAD primitive, or None to use the centerpoint of the plane as the initial
            stack value.
        :raises: ValueError if the provided plane is not a plane, or one of XY|YZ|XZ
        :return: A Workplane object, with coordinate system matching the supplied plane.

        The most common use is::

            s = Workplane("XY")

        After creation, the stack contains a single point, the origin of the underlying plane, and
        the *current point* is on the origin.
        """

        if isinstance(inPlane, Plane):
            tmpPlane = inPlane
        elif isinstance(inPlane, str):
            tmpPlane = Plane.named(inPlane, origin)
        elif isinstance(inPlane, (Vector, Location, Shape)):
            obj = inPlane
            tmpPlane = Plane.named("XY", origin)
        else:
            raise ValueError(
                "Provided value {} is not a valid work plane".format(inPlane)
            )

        self.plane = tmpPlane
        # Changed so that workplane has the center as the first item on the stack
        if obj:
            self.objects = [obj]
        else:
            self.objects = []

        self.parent = None
        self.ctx = CQContext()
        self._tag = None

    def tag(self: T, name: str) -> T:
        """
        Tags the current CQ object for later reference.

        :param name: the name to tag this object with
        :type name: string
        :returns: self, a cq object with tag applied
        """
        self._tag = name
        self.ctx.tags[name] = self

        return self

    def _collectProperty(self, propName: str) -> List[CQObject]:
        """
        Collects all of the values for propName,
        for all items on the stack.
        OCCT objects do not implement id correctly,
        so hashCode is used to ensure we don't add the same
        object multiple times.

        One weird use case is that the stack could have a solid reference object
        on it.  This is meant to be a reference to the most recently modified version
        of the context solid, whatever it is.
        """
        all = {}
        for o in self.objects:

            # tricky-- if an object is a compound of solids,
            # do not return all of the solids underneath-- typically
            # then we'll keep joining to ourself
            if (
                propName == "Solids"
                and isinstance(o, Solid)
                and o.ShapeType() == "Compound"
            ):
                for i in getattr(o, "Compounds")():
                    all[i.hashCode()] = i
            else:
                if hasattr(o, propName):
                    for i in getattr(o, propName)():
                        all[i.hashCode()] = i

        return list(all.values())

    @overload
    def split(self: T, keepTop: bool = False, keepBottom: bool = False) -> T:
        ...

    @overload
    def split(self: T, splitter: Union[T, Shape]) -> T:
        ...

    def split(self: T, *args, **kwargs) -> T:
        """
        Splits a solid on the stack into two parts, optionally keeping the separate parts.

        :param boolean keepTop: True to keep the top, False or None to discard it
        :param boolean keepBottom: True to keep the bottom, False or None to discard it
        :raises ValueError: if keepTop and keepBottom are both false.
        :raises ValueError: if there is no solid in the current stack or parent chain
        :returns: CQ object with the desired objects on the stack.

        The most common operation splits a solid and keeps one half. This sample creates
        split bushing::

            # drill a hole in the side
            c = Workplane().box(1,1,1).faces(">Z").workplane().circle(0.25).cutThruAll()

            # now cut it in half sideways
            c = c.faces(">Y").workplane(-0.5).split(keepTop=True)
        """

        # split using an object
        if len(args) == 1 and isinstance(args[0], (Workplane, Shape)):

            arg = args[0]

            solid = self.findSolid()
            tools = (
                (arg,)
                if isinstance(arg, Shape)
                else [v for v in arg.vals() if isinstance(v, Shape)]
            )
            rv = [solid.split(*tools)]
            if isinstance(arg, Workplane):
                self._mergeTags(arg)

        # split using the current workplane
        else:

            # boilerplate for arg/kwarg parsing
            sig = Signature(
                (
                    Parameter(
                        "keepTop", Parameter.POSITIONAL_OR_KEYWORD, default=False
                    ),
                    Parameter(
                        "keepBottom", Parameter.POSITIONAL_OR_KEYWORD, default=False
                    ),
                )
            )

            bound_args = sig.bind(*args, **kwargs)
            bound_args.apply_defaults()

            keepTop = bound_args.arguments["keepTop"]
            keepBottom = bound_args.arguments["keepBottom"]

            if (not keepTop) and (not keepBottom):
                raise ValueError("You have to keep at least one half")

            solid = self.findSolid()

            maxDim = solid.BoundingBox().DiagonalLength * 10.0
            topCutBox = self.rect(maxDim, maxDim)._extrude(maxDim)
            bottomCutBox = self.rect(maxDim, maxDim)._extrude(-maxDim)

            top = solid.cut(bottomCutBox)
            bottom = solid.cut(topCutBox)

            if keepTop and keepBottom:
                # Put both on the stack, leave original unchanged.
                rv = [top, bottom]
            else:
                # Put the one we are keeping on the stack, and also update the
                # context solid to the one we kept.
                if keepTop:
                    rv = [top]
                else:
                    rv = [bottom]

        return self.newObject(rv)

    @deprecate()
    def combineSolids(
        self, otherCQToCombine: Optional["Workplane"] = None
    ) -> "Workplane":
        """
        !!!DEPRECATED!!! use union()
        Combines all solids on the current stack, and any context object, together
        into a single object.

        After the operation, the returned solid is also the context solid.

        :param otherCQToCombine: another CadQuery to combine.
        :return: a cQ object with the resulting combined solid on the stack.

        Most of the time, both objects will contain a single solid, which is
        combined and returned on the stack of the new object.
        """
        # loop through current stack objects, and combine them
        toCombine = cast(List[Solid], self.solids().vals())

        if otherCQToCombine:
            otherSolids = cast(List[Solid], otherCQToCombine.solids().vals())
            for obj in otherSolids:
                toCombine.append(obj)

        if len(toCombine) < 1:
            raise ValueError("Cannot Combine: at least one solid required!")

        # get context solid and we don't want to find our own objects
        ctxSolid = self._findType(
            (Solid, Compound), searchStack=False, searchParents=True
        )
        if ctxSolid is None:
            ctxSolid = toCombine.pop(0)

        # now combine them all. make sure to save a reference to the ctxSolid pointer!
        s: Shape = ctxSolid
        if toCombine:
            s = s.fuse(*_selectShapes(toCombine))

        return self.newObject([s])

    def all(self: T) -> List[T]:
        """
        Return a list of all CQ objects on the stack.

        useful when you need to operate on the elements
        individually.

        Contrast with vals, which returns the underlying
        objects for all of the items on the stack
        """
        return [self.newObject([o]) for o in self.objects]

    def size(self) -> int:
        """
        Return the number of objects currently on the stack
        """
        return len(self.objects)

    def vals(self) -> List[CQObject]:
        """
        get the values in the current list

        :rtype: list of occ_impl objects
        :returns: the values of the objects on the stack.

        Contrast with :py:meth:`all`, which returns CQ objects for all of the items on the stack
        """
        return self.objects

    @overload
    def add(self: T, obj: "Workplane") -> T:
        ...

    @overload
    def add(self: T, obj: CQObject) -> T:
        ...

    @overload
    def add(self: T, obj: Iterable[CQObject]) -> T:
        ...

    def add(self, obj):
        """
        Adds an object or a list of objects to the stack

        :param obj: an object to add
        :type obj: a Workplane, CAD primitive, or list of CAD primitives
        :return: a Workplane with the requested operation performed

        If an Workplane object, the values of that object's stack are added. If
        a list of cad primitives, they are all added. If a single CAD primitive
        then it is added.

        Used in rare cases when you need to combine the results of several CQ
        results into a single Workplane object.
        """
        if isinstance(obj, list):
            self.objects.extend(obj)
        elif isinstance(obj, Workplane):
            self.objects.extend(obj.objects)
            self._mergeTags(obj)
        else:
            self.objects.append(obj)
        return self

    def val(self) -> CQObject:
        """
        Return the first value on the stack. If no value is present, current plane origin is returned.

        :return: the first value on the stack.
        :rtype: A CAD primitive
        """
        return self.objects[0] if self.objects else self.plane.origin

    def _getTagged(self, name: str) -> "Workplane":
        """
        Search the parent chain for an object with tag == name.

        :param name: the tag to search for
        :returns: the Workplane object with tag == name
        :raises: ValueError if no object tagged name
        """
        rv = self.ctx.tags.get(name)

        if rv is None:
            raise ValueError(f"No Workplane object named {name} in chain")

        return rv

    def _mergeTags(self: T, obj: "Workplane") -> T:
        """
        Merge tags

        This is automatically called when performing boolean ops.
        """

        if self.ctx != obj.ctx:
            self.ctx.tags = {**obj.ctx.tags, **self.ctx.tags}

        return self

    def toOCC(self) -> Any:
        """
        Directly returns the wrapped OCCT object.
        :return: The wrapped OCCT object
        :rtype TopoDS_Shape or a subclass
        """

        v = self.val()

        return v._faces if isinstance(v, Sketch) else v.wrapped

    def workplane(
        self: T,
        offset: float = 0.0,
        invert: bool = False,
        centerOption: Literal[
            "CenterOfMass", "ProjectedOrigin", "CenterOfBoundBox"
        ] = "ProjectedOrigin",
        origin: Optional[VectorLike] = None,
    ) -> T:
        """
        Creates a new 2D workplane, located relative to the first face on the stack.

        :param offset:  offset for the workplane in its normal direction . Default
        :param invert:  invert the normal direction from that of the face.
        :param centerOption: how local origin of workplane is determined.
        :param origin: origin for plane center, requires 'ProjectedOrigin' centerOption.
        :type offset: float or None=0.0
        :type invert: boolean or None=False
        :type centerOption: string or None='ProjectedOrigin'
        :type origin: Vector or None
        :rtype: Workplane object 

        The first element on the stack must be a face, a set of
        co-planar faces or a vertex.  If a vertex, then the parent
        item on the chain immediately before the vertex must be a
        face.

        The result will be a 2D working plane
        with a new coordinate system set up as follows:

           * The centerOption parameter sets how the center is defined.
             Options are 'CenterOfMass', 'CenterOfBoundBox', or 'ProjectedOrigin'.
             'CenterOfMass' and 'CenterOfBoundBox' are in relation to the selected
             face(s) or vertex (vertices). 'ProjectedOrigin' uses by default the current origin
             or the optional origin parameter (if specified) and projects it onto the plane
             defined by the selected face(s).
           * The Z direction will be the normal of the face, computed
             at the center point.
           * The X direction will be parallel to the x-y plane. If the workplane is  parallel to
             the global x-y plane, the x direction of the workplane will co-incide with the
             global x direction.

        Most commonly, the selected face will be planar, and the workplane lies in the same plane
        of the face ( IE, offset=0). Occasionally, it is useful to define a face offset from
        an existing surface, and even more rarely to define a workplane based on a face that is
        not planar.
        """

        def _isCoPlanar(f0, f1):
            """Test if two faces are on the same plane."""
            p0 = f0.Center()
            p1 = f1.Center()
            n0 = f0.normalAt()
            n1 = f1.normalAt()

            # test normals (direction of planes)
            if not (
                (abs(n0.x - n1.x) < self.ctx.tolerance)
                or (abs(n0.y - n1.y) < self.ctx.tolerance)
                or (abs(n0.z - n1.z) < self.ctx.tolerance)
            ):
                return False

            # test if p1 is on the plane of f0 (offset of planes)
            return abs(n0.dot(p0.sub(p1)) < self.ctx.tolerance)

        def _computeXdir(normal):
            """
            Figures out the X direction based on the given normal.
            :param :normal The direction that's normal to the plane.
            :type :normal A Vector
            :return A vector representing the X direction.
            """
            xd = Vector(0, 0, 1).cross(normal)
            if xd.Length < self.ctx.tolerance:
                # this face is parallel with the x-y plane, so choose x to be in global coordinates
                xd = Vector(1, 0, 0)
            return xd

        if centerOption not in {"CenterOfMass", "ProjectedOrigin", "CenterOfBoundBox"}:
            raise ValueError("Undefined centerOption value provided.")

        if len(self.objects) > 1:
            objs: List[Face] = [o for o in self.objects if isinstance(o, Face)]

            if not all(o.geomType() in ("PLANE", "CIRCLE") for o in objs) or len(
                objs
            ) < len(self.objects):
                raise ValueError(
                    "If multiple objects selected, they all must be planar faces."
                )

            # are all faces co-planar with each other?
            if not all(_isCoPlanar(self.objects[0], f) for f in self.objects[1:]):
                raise ValueError("Selected faces must be co-planar.")

            if centerOption in {"CenterOfMass", "ProjectedOrigin"}:
                center = Shape.CombinedCenter(_selectShapes(self.objects))
            elif centerOption == "CenterOfBoundBox":
                center = Shape.CombinedCenterOfBoundBox(_selectShapes(self.objects))

            normal = objs[0].normalAt()
            xDir = _computeXdir(normal)

        else:
            obj = self.val()

            if isinstance(obj, Face):
                if centerOption in {"CenterOfMass", "ProjectedOrigin"}:
                    center = obj.Center()
                elif centerOption == "CenterOfBoundBox":
                    center = obj.CenterOfBoundBox()
                normal = obj.normalAt(center)
                xDir = _computeXdir(normal)
            elif isinstance(obj, (Shape, Vector)):
                if centerOption in {"CenterOfMass", "ProjectedOrigin"}:
                    center = obj.Center()
                elif centerOption == "CenterOfBoundBox":
                    center = (
                        obj.CenterOfBoundBox()
                        if isinstance(obj, Shape)
                        else obj.Center()
                    )

                val = self.parent.val() if self.parent else None
                if isinstance(val, Face):
                    normal = val.normalAt(center)
                    xDir = _computeXdir(normal)
                else:
                    normal = self.plane.zDir
                    xDir = self.plane.xDir
            else:
                raise ValueError("Needs a face or a vertex or point on a work plane")

        # update center to projected origin if desired
        if centerOption == "ProjectedOrigin":
            orig: Vector
            if origin is None:
                orig = self.plane.origin
            elif isinstance(origin, tuple):
                orig = Vector(origin)
            else:
                orig = origin

            center = orig.projectToPlane(Plane(center, xDir, normal))

        # invert if requested
        if invert:
            normal = normal.multiply(-1.0)

        # offset origin if desired
        offsetVector = normal.normalized().multiply(offset)
        offsetCenter = center.add(offsetVector)

        # make the new workplane
        plane = Plane(offsetCenter, xDir, normal)
        s = self.__class__(plane)
        s.parent = self
        s.ctx = self.ctx

        # a new workplane has the center of the workplane on the stack
        return s

    def copyWorkplane(self, obj: T) -> T:
        """
        Copies the workplane from obj.

        :param obj: an object to copy the workplane from
        :type obj: a CQ object
        :returns: a CQ object with obj's workplane
        """
        out = obj.__class__(obj.plane)
        out.parent = self
        out.ctx = self.ctx
        return out

    def workplaneFromTagged(self, name: str) -> "Workplane":
        """
        Copies the workplane from a tagged parent.

        :param name: tag to search for
        :type name: string
        :returns: a CQ object with name's workplane
        """
        tagged = self._getTagged(name)
        out = self.copyWorkplane(tagged)
        return out

    def first(self: T) -> T:
        """
        Return the first item on the stack
        :returns: the first item on the stack.
        :rtype: a CQ object
        """
        return self.newObject(self.objects[0:1])

    def item(self: T, i: int) -> T:
        """

        Return the ith item on the stack.
        :rtype: a CQ object
        """
        return self.newObject([self.objects[i]])

    def last(self: T) -> T:
        """
        Return the last item on the stack.
        :rtype: a CQ object
        """
        return self.newObject([self.objects[-1]])

    def end(self, n: int = 1) -> "Workplane":
        """
        Return the nth parent of this CQ element
        :param n: number of ancestor to return (default: 1)
        :rtype: a CQ object
        :raises: ValueError if there are no more parents in the chain.

        For example::

            CQ(obj).faces("+Z").vertices().end()

        will return the same as::

            CQ(obj).faces("+Z")
        """

        rv = self
        for _ in range(n):
            if rv.parent:
                rv = rv.parent
            else:
                raise ValueError("Cannot End the chain-- no parents!")

        return rv

    def _findType(self, types, searchStack=True, searchParents=True):

        if searchStack:
            rv = [s for s in self.objects if isinstance(s, types)]
            if rv and types == (Solid, Compound):
                return Compound.makeCompound(rv)
            elif rv:
                return rv[0]

        if searchParents and self.parent is not None:
            return self.parent._findType(types, searchStack=True, searchParents=True)

        return None

    def findSolid(
        self, searchStack: bool = True, searchParents: bool = True
    ) -> Union[Solid, Compound]:
        """
        Finds the first solid object in the chain, searching from the current node
        backwards through parents until one is found.

        :param searchStack: should objects on the stack be searched first?
        :param searchParents: should parents be searched?
        :raises ValueError: if no solid is found

        This function is very important for chains that are modifying a single parent object,
        most often a solid.

        Most of the time, a chain defines or selects a solid, and then modifies it using workplanes
        or other operations.

        Plugin Developers should make use of this method to find the solid that should be modified,
        if the plugin implements a unary operation, or if the operation will automatically merge its
        results with an object already on the stack.
        """

        found = self._findType((Solid, Compound), searchStack, searchParents)

        if found is None:
            message = "on the stack or " if searchStack else ""
            raise ValueError(
                "Cannot find a solid {}in the parent chain".format(message)
            )

        return found

    @deprecate()
    def findFace(self, searchStack: bool = True, searchParents: bool = True) -> Face:
        """
        Finds the first face object in the chain, searching from the current node
        backwards through parents until one is found.

        :param searchStack: should objects on the stack be searched first.
        :param searchParents: should parents be searched?
        :returns: A face or None if no face is found.
        """

        found = self._findType(Face, searchStack, searchParents)

        if found is None:
            message = "on the stack or " if searchStack else ""
            raise ValueError("Cannot find a face {}in the parent chain".format(message))

        return found

    def _selectObjects(
        self: T,
        objType: Any,
        selector: Optional[Union[Selector, str]] = None,
        tag: Optional[str] = None,
    ) -> T:
        """
        Filters objects of the selected type with the specified selector,and returns results

        :param objType: the type of object we are searching for
        :type objType: string: (Vertex|Edge|Wire|Solid|Shell|Compound|CompSolid)
        :param tag: if set, search the tagged CQ object instead of self
        :type tag: string
        :return: a CQ object with the selected objects on the stack.

        **Implementation Note**: This is the base implementation of the vertices,edges,faces,
        solids,shells, and other similar selector methods.  It is a useful extension point for
        plugin developers to make other selector methods.
        """
        self_as_workplane: Workplane = self
        cq_obj = self._getTagged(tag) if tag else self_as_workplane
        # A single list of all faces from all objects on the stack
        toReturn = cq_obj._collectProperty(objType)

        selectorObj: Selector
        if selector:
            if isinstance(selector, str):
                selectorObj = StringSyntaxSelector(selector)
            else:
                selectorObj = selector
            toReturn = selectorObj.filter(toReturn)

        return self.newObject(toReturn)

    def vertices(
        self: T,
        selector: Optional[Union[Selector, str]] = None,
        tag: Optional[str] = None,
    ) -> T:
        """
        Select the vertices of objects on the stack, optionally filtering the selection. If there
        are multiple objects on the stack, the vertices of all objects are collected and a list of
        all the distinct vertices is returned.

        :param selector:
        :type selector:  None, a Selector object, or a string selector expression.
        :param tag: if set, search the tagged CQ object instead of self
        :type tag: string
        :return: a CQ object who's stack contains  the *distinct* vertices of *all* objects on the
           current stack, after being filtered by the selector, if provided

        If there are no vertices for any objects on the current stack, an empty CQ object
        is returned

        The typical use is to select the vertices of a single object on the stack. For example::

           Workplane().box(1,1,1).faces("+Z").vertices().size()

        returns 4, because the topmost face of cube will contain four vertices. While this::

           Workplane().box(1,1,1).faces().vertices().size()

        returns 8, because a cube has a total of 8 vertices

        **Note** Circles are peculiar, they have a single vertex at the center!

        :py:class:`StringSyntaxSelector`

        """
        return self._selectObjects("Vertices", selector, tag)

    def faces(
        self: T,
        selector: Optional[Union[Selector, str]] = None,
        tag: Optional[str] = None,
    ) -> T:
        """
        Select the faces of objects on the stack, optionally filtering the selection. If there are
        multiple objects on the stack, the faces of all objects are collected and a list of all the
        distinct faces is returned.

        :param selector: A selector
        :type selector:  None, a Selector object, or a string selector expression.
        :param tag: if set, search the tagged CQ object instead of self
        :type tag: string
        :return: a CQ object who's stack contains all of the *distinct* faces of *all* objects on
            the current stack, filtered by the provided selector.

        If there are no vertices for any objects on the current stack, an empty CQ object
        is returned.

        The typical use is to select the faces of a single object on the stack. For example::

           CQ(aCube).faces("+Z").size()

        returns 1, because a cube has one face with a normal in the +Z direction. Similarly::

           CQ(aCube).faces().size()

        returns 6, because a cube has a total of 6 faces, And::

            CQ(aCube).faces("|Z").size()

        returns 2, because a cube has 2 faces having normals parallel to the z direction
        """
        return self._selectObjects("Faces", selector, tag)

    def edges(
        self: T,
        selector: Optional[Union[Selector, str]] = None,
        tag: Optional[str] = None,
    ) -> T:
        """
        Select the edges of objects on the stack, optionally filtering the selection. If there are
        multiple objects on the stack, the edges of all objects are collected and a list of all the
        distinct edges is returned.

        :param selector: A selector
        :type selector:  None, a Selector object, or a string selector expression.
        :param tag: if set, search the tagged CQ object instead of self
        :type tag: string
        :return: a CQ object who's stack contains all of the *distinct* edges of *all* objects on
            the current stack, filtered by the provided selector.

        If there are no edges for any objects on the current stack, an empty CQ object is returned

        The typical use is to select the edges of a single object on the stack. For example::

           CQ(aCube).faces("+Z").edges().size()

        returns 4, because a cube has one face with a normal in the +Z direction. Similarly::

           CQ(aCube).edges().size()

        returns 12, because a cube has a total of 12 edges, And::

            CQ(aCube).edges("|Z").size()

        returns 4, because a cube has 4 edges parallel to the z direction
        """
        return self._selectObjects("Edges", selector, tag)

    def wires(
        self: T,
        selector: Optional[Union[Selector, str]] = None,
        tag: Optional[str] = None,
    ) -> T:
        """
        Select the wires of objects on the stack, optionally filtering the selection. If there are
        multiple objects on the stack, the wires of all objects are collected and a list of all the
        distinct wires is returned.

        :param selector: A selector
        :type selector:  None, a Selector object, or a string selector expression.
        :param tag: if set, search the tagged CQ object instead of self
        :type tag: string
        :return: a CQ object who's stack contains all of the *distinct* wires of *all* objects on
            the current stack, filtered by the provided selector.

        If there are no wires for any objects on the current stack, an empty CQ object is returned

        The typical use is to select the wires of a single object on the stack. For example::

           CQ(aCube).faces("+Z").wires().size()

        returns 1, because a face typically only has one outer wire
        """
        return self._selectObjects("Wires", selector, tag)

    def solids(
        self: T,
        selector: Optional[Union[Selector, str]] = None,
        tag: Optional[str] = None,
    ) -> T:
        """
        Select the solids of objects on the stack, optionally filtering the selection. If there are
        multiple objects on the stack, the solids of all objects are collected and a list of all the
        distinct solids is returned.

        :param selector: A selector
        :type selector:  None, a Selector object, or a string selector expression.
        :param tag: if set, search the tagged CQ object instead of self
        :type tag: string
        :return: a CQ object who's stack contains all of the *distinct* solids of *all* objects on
            the current stack, filtered by the provided selector.

        If there are no solids for any objects on the current stack, an empty CQ object is returned

        The typical use is to select the  a single object on the stack. For example::

           CQ(aCube).solids().size()

        returns 1, because a cube consists of one solid.

        It is possible for single CQ object ( or even a single CAD primitive ) to contain
        multiple solids.
        """
        return self._selectObjects("Solids", selector, tag)

    def shells(
        self: T,
        selector: Optional[Union[Selector, str]] = None,
        tag: Optional[str] = None,
    ) -> T:
        """
        Select the shells of objects on the stack, optionally filtering the selection. If there are
        multiple objects on the stack, the shells of all objects are collected and a list of all the
        distinct shells is returned.

        :param selector: A selector
        :type selector:  None, a Selector object, or a string selector expression.
        :param tag: if set, search the tagged CQ object instead of self
        :type tag: string
        :return: a CQ object who's stack contains all of the *distinct* solids of *all* objects on
            the current stack, filtered by the provided selector.

        If there are no shells for any objects on the current stack, an empty CQ object is returned

        Most solids will have a single shell, which represents the outer surface. A shell will
        typically be composed of multiple faces.
        """
        return self._selectObjects("Shells", selector, tag)

    def compounds(
        self: T,
        selector: Optional[Union[Selector, str]] = None,
        tag: Optional[str] = None,
    ) -> T:
        """
        Select compounds on the stack, optionally filtering the selection. If there are multiple
        objects on the stack, they are collected and a list of all the distinct compounds
        is returned.

        :param selector: A selector
        :type selector:  None, a Selector object, or a string selector expression.
        :param tag: if set, search the tagged CQ object instead of self
        :type tag: string
        :return: a CQ object who's stack contains all of the *distinct* solids of *all* objects on
            the current stack, filtered by the provided selector.

        A compound contains multiple CAD primitives that resulted from a single operation, such as
        a union, cut, split, or fillet.  Compounds can contain multiple edges, wires, or solids.
        """
        return self._selectObjects("Compounds", selector, tag)

    def toSvg(self, opts: Any = None) -> str:
        """
        Returns svg text that represents the first item on the stack.

        for testing purposes.

        :param opts: svg formatting options
        :type opts: dictionary, width and height
        :return: a string that contains SVG that represents this item.
        """
        return getSVG(self.val(), opts)

    def exportSvg(self, fileName: str) -> None:
        """
        Exports the first item on the stack as an SVG file

        For testing purposes mainly.

        :param fileName: the filename to export
        :type fileName: String, absolute path to the file
        """
        exportSVG(self, fileName)

    def rotateAboutCenter(self: T, axisEndPoint: VectorLike, angleDegrees: float) -> T:
        """
        Rotates all items on the stack by the specified angle, about the specified axis

        The center of rotation is a vector starting at the center of the object on the stack,
        and ended at the specified point.

        :param axisEndPoint: the second point of axis of rotation
        :type axisEndPoint: a three-tuple in global coordinates
        :param angleDegrees: the rotation angle, in degrees
        :type angleDegrees: float
        :returns: a CQ object, with all items rotated.

        WARNING: This version returns the same cq object instead of a new one-- the
        old object is not accessible.

        Future Enhancements:
            * A version of this method that returns a transformed copy, rather than modifying
              the originals
            * This method doesn't expose a very good interface, because the axis of rotation
              could be inconsistent between multiple objects.  This is because the beginning
              of the axis is variable, while the end is fixed. This is fine when operating on
              one object, but is not cool for multiple.
        """

        # center point is the first point in the vector
        endVec = Vector(axisEndPoint)

        def _rot(obj):
            startPt = obj.Center()
            endPt = startPt + endVec
            return obj.rotate(startPt, endPt, angleDegrees)

        return self.each(_rot, False, False)

    def rotate(
        self: T,
        axisStartPoint: VectorLike,
        axisEndPoint: VectorLike,
        angleDegrees: float,
    ) -> T:
        """
        Returns a copy of all of the items on the stack rotated through and angle around the axis
        of rotation.

        :param axisStartPoint: The first point of the axis of rotation
        :type axisStartPoint: a 3-tuple of floats
        :param axisEndPoint: The second point of the axis of rotation
        :type axisEndPoint: a 3-tuple of floats
        :param angleDegrees: the rotation angle, in degrees
        :type angleDegrees: float
        :returns: a CQ object
        """
        return self.newObject(
            [
                o.rotate(Vector(axisStartPoint), Vector(axisEndPoint), angleDegrees)
                if isinstance(o, Shape)
                else o
                for o in self.objects
            ]
        )

    def mirror(
        self: T,
        mirrorPlane: Union[
            Literal["XY", "YX", "XZ", "ZX", "YZ", "ZY"], VectorLike, Face, "Workplane"
        ] = "XY",
        basePointVector: Optional[VectorLike] = None,
        union: bool = False,
    ) -> T:
        """
        Mirror a single CQ object.

        :param mirrorPlane: the plane to mirror about
        :type mirrorPlane: string, one of "XY", "YX", "XZ", "ZX", "YZ", "ZY" the planes
        or the normal vector of the plane eg (1,0,0) or a Face object
        :param basePointVector: the base point to mirror about (this is overwritten if a Face is passed)
        :type basePointVector: tuple
        :param union: If true will perform a union operation on the mirrored object
        :type union: bool
        """

        mp: Union[Literal["XY", "YX", "XZ", "ZX", "YZ", "ZY"], Vector]
        bp: Vector
        face: Optional[Face] = None

        # handle mirrorPLane
        if isinstance(mirrorPlane, Workplane):
            val = mirrorPlane.val()
            if isinstance(val, Face):
                mp = val.normalAt()
                face = val
            else:
                raise ValueError(f"Face required, got {val}")
        elif isinstance(mirrorPlane, Face):
            mp = mirrorPlane.normalAt()
            face = mirrorPlane
        elif not isinstance(mirrorPlane, str):
            mp = Vector(mirrorPlane)
        else:
            mp = mirrorPlane

        # handle basePointVector
        if face and basePointVector is None:
            bp = face.Center()
        elif basePointVector is None:
            bp = Vector()
        else:
            bp = Vector(basePointVector)

        newS = self.newObject(
            [obj.mirror(mp, bp) for obj in self.vals() if isinstance(obj, Shape)]
        )

        if union:
            return self.union(newS)
        else:
            return newS

    def translate(self: T, vec: VectorLike) -> T:
        """
        Returns a copy of all of the items on the stack moved by the specified translation vector.

        :param tupleDistance: distance to move, in global coordinates
        :type  tupleDistance: a 3-tuple of float
        :returns: a CQ object
        """
        return self.newObject(
            [
                o.translate(Vector(vec)) if isinstance(o, Shape) else o
                for o in self.objects
            ]
        )

    def shell(
        self: T, thickness: float, kind: Literal["arc", "intersection"] = "arc"
    ) -> T:
        """
        Remove the selected faces to create a shell of the specified thickness.

        To shell, first create a solid, and *in the same chain* select the faces you wish to remove.

        :param thickness: thickness of the desired shell.
            Negative values shell inwards, positive values shell outwards.
        :param kind: kind of join, arc or intersection (default: arc).
        :raises ValueError: if the current stack contains objects that are not faces of a solid
             further up in the chain.
        :returns: a CQ object with the resulting shelled solid selected.

        This example will create a hollowed out unit cube, where the top most face is open,
        and all other walls are 0.2 units thick::

            Workplane().box(1, 1, 1).faces("+Z").shell(0.2)

        You can also select multiple faces at once. Here is an example that creates a three-walled
        corner, by removing three faces of a cube::

            Workplane().box(10, 10, 10).faces(">Z or >X or <Y").shell(1)

        **Note**:  When sharp edges are shelled inwards, they remain sharp corners, but **outward**
        shells are automatically filleted (unless kind="intersection"), because an outward offset
        from a corner generates a radius.
        """
        solidRef = self.findSolid()

        faces = [f for f in self.objects if isinstance(f, Face)]

        s = solidRef.shell(faces, thickness, kind=kind)
        return self.newObject([s])

    def fillet(self: T, radius: float) -> T:
        """
        Fillets a solid on the selected edges.

        The edges on the stack are filleted. The solid to which the edges belong must be in the
        parent chain of the selected edges.

        :param radius: the radius of the fillet, must be > zero
        :type radius: positive float
        :raises ValueError: if at least one edge is not selected
        :raises ValueError: if the solid containing the edge is not in the chain
        :returns: cq object with the resulting solid selected.

        This example will create a unit cube, with the top edges filleted::

            s = Workplane().box(1,1,1).faces("+Z").edges().fillet(0.1)
        """
        # TODO: ensure that edges selected actually belong to the solid in the chain, otherwise,
        # TODO: we segfault

        solid = self.findSolid()

        edgeList = cast(List[Edge], self.edges().vals())
        if len(edgeList) < 1:
            raise ValueError("Fillets requires that edges be selected")

        s = solid.fillet(radius, edgeList)
        return self.newObject([s.clean()])

    def chamfer(self: T, length: float, length2: Optional[float] = None) -> T:
        """
        Chamfers a solid on the selected edges.

        The edges on the stack are chamfered. The solid to which the
        edges belong must be in the parent chain of the selected
        edges.

        Optional parameter `length2` can be supplied with a different
        value than `length` for a chamfer that is shorter on one side
        longer on the other side.

        :param length: the length of the chamfer, must be greater than zero
        :param length2: optional parameter for asymmetrical chamfer
        :type length: positive float
        :type length2: positive float
        :raises ValueError: if at least one edge is not selected
        :raises ValueError: if the solid containing the edge is not in the chain
        :returns: cq object with the resulting solid selected.

        This example will create a unit cube, with the top edges chamfered::

            s = Workplane("XY").box(1,1,1).faces("+Z").chamfer(0.1)

        This example will create chamfers longer on the sides::

            s = Workplane("XY").box(1,1,1).faces("+Z").chamfer(0.2, 0.1)
        """
        solid = self.findSolid()

        edgeList = cast(List[Edge], self.edges().vals())
        if len(edgeList) < 1:
            raise ValueError("Chamfer requires that edges be selected")

        s = solid.chamfer(length, length2, edgeList)

        return self.newObject([s])

    def transformed(
        self: T, rotate: VectorLike = (0, 0, 0), offset: VectorLike = (0, 0, 0)
    ) -> T:
        """
        Create a new workplane based on the current one.
        The origin of the new plane is located at the existing origin+offset vector, where offset is
        given in coordinates local to the current plane
        The new plane is rotated through the angles specified by the components of the rotation
        vector.
        :param rotate: 3-tuple of angles to rotate, in degrees relative to work plane coordinates
        :param offset: 3-tuple to offset the new plane, in local work plane coordinates
        :return: a new work plane, transformed as requested
        """

        # old api accepted a vector, so we'll check for that.
        if isinstance(rotate, Vector):
            rotate = rotate.toTuple()

        if isinstance(offset, Vector):
            offset = offset.toTuple()

        p = self.plane.rotated(rotate)
        p.origin = self.plane.toWorldCoords(offset)
        ns = self.newObject([p.origin])
        ns.plane = p

        return ns

    def newObject(self: T, objlist: Iterable[CQObject]) -> T:
        """
        Create a new workplane object from this one.

        Overrides CQ.newObject, and should be used by extensions, plugins, and
        subclasses to create new objects.

        :param objlist: new objects to put on the stack
        :type objlist: a list of CAD primitives
        :return: a new Workplane object with the current workplane as a parent.
        """

        # copy the current state to the new object
        ns = self.__class__()
        ns.plane = copy(self.plane)
        ns.parent = self
        ns.objects = list(objlist)
        ns.ctx = self.ctx
        return ns

    def _findFromPoint(self, useLocalCoords: bool = False) -> Vector:
        """
        Finds the start point for an operation when an existing point
        is implied.  Examples include 2d operations such as lineTo,
        which allows specifying the end point, and implicitly use the
        end of the previous line as the starting point

        :return: a Vector representing the point to use, or none if
        such a point is not available.

        :param useLocalCoords: selects whether the point is returned
        in local coordinates or global coordinates.

        The algorithm is this:
            * If an Edge is on the stack, its end point is used.yp
            * if a vector is on the stack, it is used

        WARNING: only the last object on the stack is used.

        NOTE:
        """
        obj = self.objects[-1] if self.objects else self.plane.origin

        if isinstance(obj, Edge):
            p = obj.endPoint()
        elif isinstance(obj, Vector):
            p = obj
        else:
            raise RuntimeError("Cannot convert object type '%s' to vector " % type(obj))

        if useLocalCoords:
            return self.plane.toLocalCoords(p)
        else:
            return p

    def _findFromEdge(self, useLocalCoords: bool = False) -> Edge:
        """
        Finds the previous edge for an operation that needs it, similar to
        method _findFromPoint. Examples include tangentArcPoint.

        :param useLocalCoords: selects whether the point is returned
        in local coordinates or global coordinates.
        :return: an Edge
        """
        obj = self.objects[-1] if self.objects else self.plane.origin

        if not isinstance(obj, Edge):
            raise RuntimeError(
                "Previous Edge requested, but the previous object was of "
                + f"type {type(obj)}, not an Edge."
            )

        rv: Edge = obj

        if useLocalCoords:
            rv = self.plane.toLocalCoords(rv)

        return rv

    def rarray(
        self: T,
        xSpacing: float,
        ySpacing: float,
        xCount: int,
        yCount: int,
        center: Union[bool, Tuple[bool, bool]] = True,
    ) -> T:
        """
        Creates an array of points and pushes them onto the stack.
        If you want to position the array at another point, create another workplane
        that is shifted to the position you would like to use as a reference

        :param xSpacing: spacing between points in the x direction ( must be > 0)
        :param ySpacing: spacing between points in the y direction ( must be > 0)
        :param xCount: number of points ( > 0 )
        :param yCount: number of points ( > 0 )
        :param center: If True, the array will be centered around the workplane center.
          If False, the lower corner will be on the reference point and the array will
          extend in the positive x and y directions. Can also use a 2-tuple to specify
          centering along each axis.
        """

        if xSpacing <= 0 or ySpacing <= 0 or xCount < 1 or yCount < 1:
            raise ValueError("Spacing and count must be > 0 ")

        if isinstance(center, bool):
            center = (center, center)

        lpoints = []  # coordinates relative to bottom left point
        for x in range(xCount):
            for y in range(yCount):
                lpoints.append(Vector(xSpacing * x, ySpacing * y))

        # shift points down and left relative to origin if requested
        offset = Vector()
        if center[0]:
            offset += Vector(-xSpacing * (xCount - 1) * 0.5, 0)
        if center[1]:
            offset += Vector(0, -ySpacing * (yCount - 1) * 0.5)
        lpoints = [x + offset for x in lpoints]

        return self.pushPoints(lpoints)

    def polarArray(
        self: T,
        radius: float,
        startAngle: float,
        angle: float,
        count: int,
        fill: bool = True,
        rotate: bool = True,
    ) -> T:
        """
        Creates a polar array of points and pushes them onto the stack.
        The zero degree reference angle is located along the local X-axis.

        :param radius: Radius of the array.
        :param startAngle: Starting angle (degrees) of array. Zero degrees is
            situated along the local X-axis.
        :param angle: The angle (degrees) to fill with elements. A positive
            value will fill in the counter-clockwise direction. If fill is
            False, angle is the angle between elements.
        :param count: Number of elements in array. (count >= 1)
        :param fill: Interpret the angle as total if True (default: True).
        :param rotate: Rotate every item (default: True).
        """

        if count < 1:
            raise ValueError(f"At least 1 element required, requested {count}")

        # Calculate angle between elements
        if fill:
            if abs(math.remainder(angle, 360)) < TOL:
                angle = angle / count
            else:
                # Inclusive start and end
                angle = angle / (count - 1) if count > 1 else startAngle

        locs = []

        # Add elements
        for i in range(0, count):
            phi_deg = startAngle + (angle * i)
            phi = math.radians(phi_deg)
            x = radius * math.cos(phi)
            y = radius * math.sin(phi)

            if rotate:
                loc = Location(Vector(x, y), Vector(0, 0, 1), phi_deg)
            else:
                loc = Location(Vector(x, y))

            locs.append(loc)

        return self.pushPoints(locs)

    def pushPoints(self: T, pntList: Iterable[Union[VectorLike, Location]]) -> T:
        """
        Pushes a list of points onto the stack as vertices.
        The points are in the 2D coordinate space of the workplane face

        :param pntList: a list of points to push onto the stack
        :type pntList: list of 2-tuples, in *local* coordinates
        :return: a new workplane with the desired points on the stack.

        A common use is to provide a list of points for a subsequent operation, such as creating
        circles or holes. This example creates a cube, and then drills three holes through it,
        based on three points::

            s = Workplane().box(1,1,1).faces(">Z").workplane().\
                pushPoints([(-0.3,0.3),(0.3,0.3),(0,0)])
            body = s.circle(0.05).cutThruAll()

        Here the circle function operates on all three points, and is then extruded to create three
        holes. See :py:meth:`circle` for how it works.
        """
        vecs: List[Union[Location, Vector]] = []
        for pnt in pntList:
            vecs.append(
                pnt if isinstance(pnt, Location) else self.plane.toWorldCoords(pnt)
            )

        return self.newObject(vecs)

    def center(self: T, x: float, y: float) -> T:
        """
        Shift local coordinates to the specified location.

        The location is specified in terms of local coordinates.

        :param float x: the new x location
        :param float y: the new y location
        :returns: the workplane object, with the center adjusted.

        The current point is set to the new center.
        This method is useful to adjust the center point after it has been created automatically on
        a face, but not where you'd like it to be.

        In this example, we adjust the workplane center to be at the corner of a cube, instead of
        the center of a face, which is the default::

            #this workplane is centered at x=0.5,y=0.5, the center of the upper face
            s = Workplane().box(1,1,1).faces(">Z").workplane()

            s = s.center(-0.5,-0.5) # move the center to the corner
            t = s.circle(0.25).extrude(0.2)
            assert ( t.faces().size() == 9 ) # a cube with a cylindrical nub at the top right corner

        The result is a cube with a round boss on the corner
        """
        "Shift local coordinates to the specified location, according to current coordinates"
        new_origin = self.plane.toWorldCoords((x, y))
        n = self.newObject([new_origin])
        n.plane.setOrigin2d(x, y)
        return n

    def lineTo(self: T, x: float, y: float, forConstruction: bool = False) -> T:
        """
        Make a line from the current point to the provided point

        :param float x: the x point, in workplane plane coordinates
        :param float y: the y point, in workplane plane coordinates
        :return: the Workplane object with the current point at the end of the new line

        see :py:meth:`line` if you want to use relative dimensions to make a line instead.
        """
        startPoint = self._findFromPoint(False)

        endPoint = self.plane.toWorldCoords((x, y))

        p = Edge.makeLine(startPoint, endPoint)

        if not forConstruction:
            self._addPendingEdge(p)

        return self.newObject([p])

    # line a specified incremental amount from current point
    def line(self: T, xDist: float, yDist: float, forConstruction: bool = False) -> T:
        """
        Make a line from the current point to the provided point, using
        dimensions relative to the current point

        :param float xDist: x distance from current point
        :param float yDist: y distance from current point
        :return: the workplane object with the current point at the end of the new line

        see :py:meth:`lineTo` if you want to use absolute coordinates to make a line instead.
        """
        p = self._findFromPoint(True)  # return local coordinates
        return self.lineTo(p.x + xDist, yDist + p.y, forConstruction)

    def vLine(self: T, distance: float, forConstruction: bool = False) -> T:
        """
        Make a vertical line from the current point the provided distance

        :param float distance: (y) distance from current point
        :return: the workplane object with the current point at the end of the new line
        """
        return self.line(0, distance, forConstruction)

    def hLine(self: T, distance: float, forConstruction: bool = False) -> T:
        """
        Make a horizontal line from the current point the provided distance

        :param float distance: (x) distance from current point
        :return: the Workplane object with the current point at the end of the new line
        """
        return self.line(distance, 0, forConstruction)

    def vLineTo(self: T, yCoord: float, forConstruction: bool = False) -> T:
        """
        Make a vertical line from the current point to the provided y coordinate.

        Useful if it is more convenient to specify the end location rather than distance,
        as in :py:meth:`vLine`

        :param float yCoord: y coordinate for the end of the line
        :return: the Workplane object with the current point at the end of the new line
        """
        p = self._findFromPoint(True)
        return self.lineTo(p.x, yCoord, forConstruction)

    def hLineTo(self: T, xCoord: float, forConstruction: bool = False) -> T:
        """
        Make a horizontal line from the current point to the provided x coordinate.

        Useful if it is more convenient to specify the end location rather than distance,
        as in :py:meth:`hLine`

        :param float xCoord: x coordinate for the end of the line
        :return: the Workplane object with the current point at the end of the new line
        """
        p = self._findFromPoint(True)
        return self.lineTo(xCoord, p.y, forConstruction)

    def polarLine(
        self: T, distance: float, angle: float, forConstruction: bool = False
    ) -> T:
        """
        Make a line of the given length, at the given angle from the current point

        :param float distance: distance of the end of the line from the current point
        :param float angle: angle of the vector to the end of the line with the x-axis
        :return: the Workplane object with the current point at the end of the new line
        """
        x = math.cos(math.radians(angle)) * distance
        y = math.sin(math.radians(angle)) * distance

        return self.line(x, y, forConstruction)

    def polarLineTo(
        self: T, distance: float, angle: float, forConstruction: bool = False
    ) -> T:
        """
        Make a line from the current point to the given polar coordinates

        Useful if it is more convenient to specify the end location rather than
        the distance and angle from the current point

        :param float distance: distance of the end of the line from the origin
        :param float angle: angle of the vector to the end of the line with the x-axis
        :return: the Workplane object with the current point at the end of the new line
        """
        x = math.cos(math.radians(angle)) * distance
        y = math.sin(math.radians(angle)) * distance

        return self.lineTo(x, y, forConstruction)

    # absolute move in current plane, not drawing
    def moveTo(self: T, x: float = 0, y: float = 0) -> T:
        """
        Move to the specified point, without drawing.

        :param x: desired x location, in local coordinates
        :type x: float, or none for zero
        :param y: desired y location, in local coordinates
        :type y: float, or none for zero.

        Not to be confused with :py:meth:`center`, which moves the center of the entire
        workplane, this method only moves the current point ( and therefore does not affect objects
        already drawn ).

        See :py:meth:`move` to do the same thing but using relative dimensions
        """
        newCenter = Vector(x, y, 0)
        return self.newObject([self.plane.toWorldCoords(newCenter)])

    # relative move in current plane, not drawing
    def move(self: T, xDist: float = 0, yDist: float = 0) -> T:
        """
        Move the specified distance from the current point, without drawing.

        :param xDist: desired x distance, in local coordinates
        :type xDist: float, or none for zero
        :param yDist: desired y distance, in local coordinates
        :type yDist: float, or none for zero.

        Not to be confused with :py:meth:`center`, which moves the center of the entire
        workplane, this method only moves the current point ( and therefore does not affect objects
        already drawn ).

        See :py:meth:`moveTo` to do the same thing but using absolute coordinates
        """
        p = self._findFromPoint(True)
        newCenter = p + Vector(xDist, yDist, 0)
        return self.newObject([self.plane.toWorldCoords(newCenter)])

    def slot2D(self: T, length: float, diameter: float, angle: float = 0) -> T:
        """
        Creates a rounded slot for each point on the stack.

        :param diameter: desired diameter, or width, of slot
        :param length: desired end to end length of slot
        :param angle: angle of slot in degrees, with 0 being along x-axis
        :return: a new CQ object with the created wires on the stack

        Can be used to create arrays of slots, such as in cooling applications:

        result = cq.Workplane("XY").box(10,25,1).rarray(1,2,1,10).slot2D(8,1,0).cutThruAll()
        """

        radius = diameter / 2

        p1 = Vector((-length / 2) + radius, diameter / 2)
        p2 = p1 + Vector(length - diameter, 0)
        p3 = p1 + Vector(length - diameter, -diameter)
        p4 = p1 + Vector(0, -diameter)
        arc1 = p2 + Vector(radius, -radius)
        arc2 = p4 + Vector(-radius, radius)

        edges = [(Edge.makeLine(p1, p2))]
        edges.append(Edge.makeThreePointArc(p2, arc1, p3))
        edges.append(Edge.makeLine(p3, p4))
        edges.append(Edge.makeThreePointArc(p4, arc2, p1))

        slot = Wire.assembleEdges(edges)
        slot = slot.rotate(Vector(), Vector(0, 0, 1), angle)

        return self.eachpoint(lambda loc: slot.moved(loc), True)

    def _toVectors(
        self, pts: Iterable[VectorLike], includeCurrent: bool
    ) -> List[Vector]:

        vecs = [self.plane.toWorldCoords(p) for p in pts]

        if includeCurrent:
            gstartPoint = self._findFromPoint(False)
            allPoints = [gstartPoint] + vecs
        else:
            allPoints = vecs

        return allPoints

    def spline(
        self: T,
        listOfXYTuple: Iterable[VectorLike],
        tangents: Optional[Sequence[VectorLike]] = None,
        periodic: bool = False,
        parameters: Optional[Sequence[float]] = None,
        scale: bool = True,
        tol: Optional[float] = None,
        forConstruction: bool = False,
        includeCurrent: bool = False,
        makeWire: bool = False,
    ) -> T:
        """
        Create a spline interpolated through the provided points (2D or 3D).

        :param listOfXYTuple: points to interpolate through
        :param tangents: vectors specifying the direction of the tangent to the
            curve at each of the specified interpolation points.

            If only 2 tangents are given, they will be used as the initial and
            final tangent.

            If some tangents are not specified (i.e., are None), no tangent
            constraint will be applied to the corresponding interpolation point.

            The spline will be C2 continuous at the interpolation points where
            no tangent constraint is specified, and C1 continuous at the points
            where a tangent constraint is specified.
        :param periodic: creation of periodic curves
        :param parameters: the value of the parameter at each interpolation point.
            (The interpolated curve is represented as a vector-valued function of a
            scalar parameter.)

            If periodic == True, then len(parameters) must be
            len(interpolation points) + 1, otherwise len(parameters) must be equal to
            len(interpolation points).
        :param scale: whether to scale the specified tangent vectors before
            interpolating.

            Each tangent is scaled, so it's length is equal to the derivative of
            the Lagrange interpolated curve.

            I.e., set this to True, if you want to use only the direction of
            the tangent vectors specified by ``tangents``, but not their magnitude.
        :param tol: tolerance of the algorithm (consult OCC documentation)

            Used to check that the specified points are not too close to each
            other, and that tangent vectors are not too short. (In either case
            interpolation may fail.)

            Set to None to use the default tolerance.
        :param includeCurrent: use current point as a starting point of the curve
        :param makeWire: convert the resulting spline edge to a wire
        :return: a Workplane object with the current point at the end of the spline

        The spline will begin at the current point, and
        end with the last point in the XY tuple list

        This example creates a block with a spline for one side::

            s = Workplane(Plane.XY())
            sPnts = [
                (2.75,1.5),
                (2.5,1.75),
                (2.0,1.5),
                (1.5,1.0),
                (1.0,1.25),
                (0.5,1.0),
                (0,1.0)
            ]
            r = s.lineTo(3.0,0).lineTo(3.0,1.0).spline(sPnts).close()
            r = r.extrude(0.5)

        *WARNING*  It is fairly easy to create a list of points
        that cannot be correctly interpreted as a spline.
        """

        allPoints = self._toVectors(listOfXYTuple, includeCurrent)

        if tangents:
            tangents_g: Optional[Sequence[Vector]] = [
                self.plane.toWorldCoords(t) - self.plane.origin
                if t is not None
                else None
                for t in tangents
            ]
        else:
            tangents_g = None

        e = Edge.makeSpline(
            allPoints,
            tangents=tangents_g,
            periodic=periodic,
            parameters=parameters,
            scale=scale,
            **({"tol": tol} if tol else {}),
        )

        if makeWire:
            rv_w = Wire.assembleEdges([e])
            if not forConstruction:
                self._addPendingWire(rv_w)
        else:
            if not forConstruction:
                self._addPendingEdge(e)

        return self.newObject([rv_w if makeWire else e])

    def splineApprox(
        self: T,
        points: Iterable[VectorLike],
        tol: Optional[float] = 1e-6,
        minDeg: int = 1,
        maxDeg: int = 6,
        smoothing: Optional[Tuple[float, float, float]] = (1, 1, 1),
        forConstruction: bool = False,
        includeCurrent: bool = False,
        makeWire: bool = False,
    ) -> T:
        """
        Create a spline interpolated through the provided points (2D or 3D).

        :param points: points to interpolate through
        :param tol: tolerance of the algorithm (default: 1e-6)
        :param minDeg: minimum spline degree (default: 1)
        :param maxDeg: maximum spline degree (default: 6)
        :param smoothing: optional parameters for the variational smoothing algorithm (default: (1,1,1))
        :param includeCurrent: use current point as a starting point of the curve
        :param makeWire: convert the resulting spline edge to a wire
        :return: a Workplane object with the current point at the end of the spline

        *WARNING*  for advanced users.
        """

        allPoints = self._toVectors(points, includeCurrent)

        e = Edge.makeSplineApprox(
            allPoints,
            minDeg=minDeg,
            maxDeg=maxDeg,
            smoothing=smoothing,
            **({"tol": tol} if tol else {}),
        )

        if makeWire:
            rv_w = Wire.assembleEdges([e])
            if not forConstruction:
                self._addPendingWire(rv_w)
        else:
            if not forConstruction:
                self._addPendingEdge(e)

        return self.newObject([rv_w if makeWire else e])

    def parametricCurve(
        self: T,
        func: Callable[[float], VectorLike],
        N: int = 400,
        start: float = 0,
        stop: float = 1,
        tol: float = 1e-6,
        minDeg: int = 1,
        maxDeg: int = 6,
        smoothing: Optional[Tuple[float, float, float]] = (1, 1, 1),
        makeWire: bool = True,
    ) -> T:
        """
        Create a spline curve approximating the provided function.

        :param func: function f(t) that will generate (x,y,z) pairs
        :type func: float --> (float,float,float)
        :param N: number of points for discretization
        :param start: starting value of the parameter t
        :param stop: final value of the parameter t
        :param tol: tolerance of the algorithm (default: 1e-6)
        :param minDeg: minimum spline degree (default: 1)
        :param maxDeg: maximum spline degree (default: 6)
        :param smoothing: optional parameters for the variational smoothing algorithm (default: (1,1,1))
        :param makeWire: convert the resulting spline edge to a wire
        :return: a Workplane object with the current point unchanged

        """

        diff = stop - start
        allPoints = self._toVectors(
            (func(start + diff * t / N) for t in range(N + 1)), False
        )

        e = Edge.makeSplineApprox(
            allPoints, tol=tol, smoothing=smoothing, minDeg=minDeg, maxDeg=maxDeg
        )

        if makeWire:
            rv_w = Wire.assembleEdges([e])
            self._addPendingWire(rv_w)
        else:
            self._addPendingEdge(e)

        return self.newObject([rv_w if makeWire else e])

    def parametricSurface(
        self: T,
        func: Callable[[float, float], VectorLike],
        N: int = 20,
        start: float = 0,
        stop: float = 1,
        tol: float = 1e-2,
        minDeg: int = 1,
        maxDeg: int = 6,
        smoothing: Optional[Tuple[float, float, float]] = (1, 1, 1),
    ) -> T:
        """
        Create a spline surface approximating the provided function.

        :param func: function f(u,v) that will generate (x,y,z) pairs
        :type func: (float,float) --> (float,float,float)
        :param N: number of points for discretization in one direction
        :param start: starting value of the parameters u,v
        :param stop: final value of the parameters u,v
        :param tol: tolerance used by the approximation algorithm (default: 1e-3)
        :param minDeg: minimum spline degree (default: 1)
        :param maxDeg: maximum spline degree (default: 3)
        :param smoothing: optional parameters for the variational smoothing algorithm (default: (1,1,1))
        :return: a Workplane object with the current point unchanged

        This method might be unstable and may require tuning of the tol parameter.

        """

        diff = stop - start
        allPoints = []

        for i in range(N + 1):
            generator = (
                func(start + diff * i / N, start + diff * j / N) for j in range(N + 1)
            )
            allPoints.append(self._toVectors(generator, False))

        f = Face.makeSplineApprox(
            allPoints, tol=tol, smoothing=smoothing, minDeg=minDeg, maxDeg=maxDeg
        )

        return self.newObject([f])

    def ellipseArc(
        self: T,
        x_radius: float,
        y_radius: float,
        angle1: float = 360,
        angle2: float = 360,
        rotation_angle: float = 0.0,
        sense: Literal[-1, 1] = 1,
        forConstruction: bool = False,
        startAtCurrent: bool = True,
        makeWire: bool = False,
    ) -> T:
        """Draw an elliptical arc with x and y radiuses either with start point at current point or
        or current point being the center of the arc

        :param x_radius: x radius of the ellipse (along the x-axis of plane the ellipse should lie in)
        :param y_radius: y radius of the ellipse (along the y-axis of plane the ellipse should lie in)
        :param angle1: start angle of arc
        :param angle2: end angle of arc (angle2 == angle1 return closed ellipse = default)
        :param rotation_angle: angle to rotate the created ellipse / arc
        :param sense: clockwise (-1) or counter clockwise (1)
        :param startAtCurrent: True: start point of arc is moved to current point; False: center of
            arc is on current point
        :param makeWire: convert the resulting arc edge to a wire
        """

        # Start building the ellipse with the current point as center
        center = self._findFromPoint(useLocalCoords=False)
        e = Edge.makeEllipse(
            x_radius,
            y_radius,
            center,
            self.plane.zDir,
            self.plane.xDir,
            angle1,
            angle2,
            sense,
        )

        # Rotate if necessary
        if rotation_angle != 0.0:
            e = e.rotate(center, center.add(self.plane.zDir), rotation_angle)

        # Move the start point of the ellipse onto the last current point
        if startAtCurrent:
            startPoint = e.startPoint()
            e = e.translate(center.sub(startPoint))

        if makeWire:
            rv_w = Wire.assembleEdges([e])
            if not forConstruction:
                self._addPendingWire(rv_w)
        else:
            if not forConstruction:
                self._addPendingEdge(e)

        return self.newObject([rv_w if makeWire else e])

    def threePointArc(
        self: T, point1: VectorLike, point2: VectorLike, forConstruction: bool = False,
    ) -> T:
        """
        Draw an arc from the current point, through point1, and ending at point2

        :param point1: point to draw through
        :type point1: 2-tuple, in workplane coordinates
        :param point2: end point for the arc
        :type point2: 2-tuple, in workplane coordinates
        :return: a workplane with the current point at the end of the arc

        Future Enhancements:
            provide a version that allows an arc using relative measures
            provide a centerpoint arc
            provide tangent arcs
        """

        gstartPoint = self._findFromPoint(False)
        gpoint1 = self.plane.toWorldCoords(point1)
        gpoint2 = self.plane.toWorldCoords(point2)

        arc = Edge.makeThreePointArc(gstartPoint, gpoint1, gpoint2)

        if not forConstruction:
            self._addPendingEdge(arc)

        return self.newObject([arc])

    def sagittaArc(
        self: T, endPoint: VectorLike, sag: float, forConstruction: bool = False,
    ) -> T:
        """
        Draw an arc from the current point to endPoint with an arc defined by the sag (sagitta).

        :param endPoint: end point for the arc
        :type endPoint: 2-tuple, in workplane coordinates
        :param sag: the sagitta of the arc
        :type sag: float, perpendicular distance from arc center to arc baseline.
        :return: a workplane with the current point at the end of the arc

        The sagitta is the distance from the center of the arc to the arc base.
        Given that a closed contour is drawn clockwise;
        A positive sagitta means convex arc and negative sagitta means concave arc.
        See "https://en.wikipedia.org/wiki/Sagitta_(geometry)" for more information.
        """

        startPoint = self._findFromPoint(useLocalCoords=True)
        endPoint = Vector(endPoint)
        midPoint = endPoint.add(startPoint).multiply(0.5)

        sagVector = endPoint.sub(startPoint).normalized().multiply(abs(sag))
        if sag > 0:
            sagVector.x, sagVector.y = (
                -sagVector.y,
                sagVector.x,
            )  # Rotate sagVector +90 deg
        else:
            sagVector.x, sagVector.y = (
                sagVector.y,
                -sagVector.x,
            )  # Rotate sagVector -90 deg

        sagPoint = midPoint.add(sagVector)

        return self.threePointArc(sagPoint, endPoint, forConstruction)

    def radiusArc(
        self: T, endPoint: VectorLike, radius: float, forConstruction: bool = False,
    ) -> T:
        """
        Draw an arc from the current point to endPoint with an arc defined by the radius.

        :param endPoint: end point for the arc
        :type endPoint: 2-tuple, in workplane coordinates
        :param radius: the radius of the arc
        :type radius: float, the radius of the arc between start point and end point.
        :return: a workplane with the current point at the end of the arc

        Given that a closed contour is drawn clockwise;
        A positive radius means convex arc and negative radius means concave arc.
        """

        startPoint = self._findFromPoint(useLocalCoords=True)
        endPoint = Vector(endPoint)

        # Calculate the sagitta from the radius
        length = endPoint.sub(startPoint).Length / 2.0
        try:
            sag = abs(radius) - math.sqrt(radius ** 2 - length ** 2)
        except ValueError:
            raise ValueError("Arc radius is not large enough to reach the end point.")

        # Return a sagittaArc
        if radius > 0:
            return self.sagittaArc(endPoint, sag, forConstruction)
        else:
            return self.sagittaArc(endPoint, -sag, forConstruction)

    def tangentArcPoint(
        self: T,
        endpoint: VectorLike,
        forConstruction: bool = False,
        relative: bool = True,
    ) -> T:
        """
        Draw an arc as a tangent from the end of the current edge to endpoint.

        :param endpoint: point for the arc to end at
        :type endpoint: 2-tuple, 3-tuple or Vector
        :param relative: True if endpoint is specified relative to the current point, False if endpoint is in workplane coordinates
        :type relative: Bool
        :return: a Workplane object with an arc on the stack

        Requires the the current first object on the stack is an Edge, as would
        be the case after a lineTo operation or similar.
        """

        if not isinstance(endpoint, Vector):
            endpoint = Vector(endpoint)
        if relative:
            endpoint = endpoint + self._findFromPoint(useLocalCoords=True)
        endpoint = self.plane.toWorldCoords(endpoint)

        previousEdge = self._findFromEdge()

        arc = Edge.makeTangentArc(
            previousEdge.endPoint(), previousEdge.tangentAt(1), endpoint
        )

        if not forConstruction:
            self._addPendingEdge(arc)

        return self.newObject([arc])

    def mirrorY(self: T) -> T:
        """
        Mirror entities around the y axis of the workplane plane.

        :return: a new object with any free edges consolidated into as few wires as possible.

        All free edges are collected into a wire, and then the wire is mirrored,
        and finally joined into a new wire

        Typically used to make creating wires with symmetry easier. This line of code::

             s = Workplane().lineTo(2,2).threePointArc((3,1),(2,0)).mirrorX().extrude(0.25)

        Produces a flat, heart shaped object
        """
        # convert edges to a wire, if there are pending edges
        n = self.wire(forConstruction=False)

        # attempt to consolidate wires together.
        consolidated = n.consolidateWires()

        mirroredWires = self.plane.mirrorInPlane(consolidated.wires().vals(), "Y")

        for w in mirroredWires:
            consolidated.objects.append(w)
            consolidated._addPendingWire(w)

        # attempt again to consolidate all of the wires
        return consolidated.consolidateWires()

    def mirrorX(self: T) -> T:
        """
        Mirror entities around the x axis of the workplane plane.

        :return: a new object with any free edges consolidated into as few wires as possible.

        All free edges are collected into a wire, and then the wire is mirrored,
        and finally joined into a new wire

        Typically used to make creating wires with symmetry easier.
        """
        # convert edges to a wire, if there are pending edges
        n = self.wire(forConstruction=False)

        # attempt to consolidate wires together.
        consolidated = n.consolidateWires()

        mirroredWires = self.plane.mirrorInPlane(consolidated.wires().vals(), "X")

        for w in mirroredWires:
            consolidated.objects.append(w)
            consolidated._addPendingWire(w)

        # attempt again to consolidate all of the wires
        return consolidated.consolidateWires()

    def _addPendingEdge(self, edge: Edge) -> None:
        """
        Queues an edge for later combination into a wire.

        :param edge:
        :return:
        """
        self.ctx.pendingEdges.append(edge)

        if self.ctx.firstPoint is None:
            self.ctx.firstPoint = self.plane.toLocalCoords(edge.startPoint())

    def _addPendingWire(self, wire: Wire) -> None:
        """
        Queue a Wire for later extrusion

        Internal Processing Note.  In OCCT, edges-->wires-->faces-->solids.

        but users do not normally care about these distinctions.  Users 'think' in terms
        of edges, and solids.

        CadQuery tracks edges as they are drawn, and automatically combines them into wires
        when the user does an operation that needs it.

        Similarly, cadQuery tracks pending wires, and automatically combines them into faces
        when necessary to make a solid.
        """
        self.ctx.pendingWires.append(wire)

    def _consolidateWires(self) -> List[Wire]:

        # note: do not use CQContext.popPendingEdges or Wires here, this method does not
        # clear pending edges or wires.
        wires = cast(
            List[Union[Edge, Wire]],
            [el for el in chain(self.ctx.pendingEdges, self.ctx.pendingWires)],
        )
        if not wires:
            return []

        return Wire.combine(wires)

    def consolidateWires(self: T) -> T:
        """
        Attempt to consolidate wires on the stack into a single.
        If possible, a new object with the results are returned.
        if not possible, the wires remain separated
        """

        w = self._consolidateWires()

        if not w:
            return self

        # ok this is a little tricky. if we consolidate wires, we have to actually
        # modify the pendingWires collection to remove the original ones, and replace them
        # with the consolidate done
        # since we are already assuming that all wires could be consolidated, its easy, we just
        # clear the pending wire list
        r = self.newObject(w)
        r.ctx.pendingWires = w
        r.ctx.pendingEdges = []

        return r

    def wire(self: T, forConstruction: bool = False) -> T:
        """
        Returns a CQ object with all pending edges connected into a wire.

        All edges on the stack that can be combined will be combined into a single wire object,
        and other objects will remain on the stack unmodified. If there are no pending edges,
        this method will just return self.

        :param forConstruction: whether the wire should be used to make a solid, or if it is just
            for reference

        This method is primarily of use to plugin developers making utilities for 2D construction.
        This method should be called when a user operation implies that 2D construction is
        finished, and we are ready to begin working in 3d.

        SEE '2D construction concepts' for a more detailed explanation of how CadQuery handles
        edges, wires, etc.

        Any non edges will still remain.
        """

        # do not consolidate if there are no free edges
        if len(self.ctx.pendingEdges) == 0:
            return self

        edges = self.ctx.popPendingEdges()
        w = Wire.assembleEdges(edges)
        if not forConstruction:
            self._addPendingWire(w)

        others = [e for e in self.objects if not isinstance(e, Edge)]

        return self.newObject(others + [w])

    def each(
        self: T,
        callback: Callable[[CQObject], Shape],
        useLocalCoordinates: bool = False,
        combine: CombineMode = True,
        clean: bool = True,
    ) -> T:
        """
        Runs the provided function on each value in the stack, and collects the return values into
        a new CQ object.

        Special note: a newly created workplane always has its center point as its only stack item

        :param callBackFunction: the function to call for each item on the current stack.
        :param useLocalCoordinates: should  values be converted from local coordinates first?
        :type useLocalCoordinates: boolean
        :param combine: True or "a" to combine the resulting solid with parent solids if found, "cut" or "s" to remove the resulting solid from the parent solids if found. False to keep the resulting solid separated from the parent solids.
        :param boolean clean: call :py:meth:`clean` afterwards to have a clean shape


        The callback function must accept one argument, which is the item on the stack, and return
        one object, which is collected. If the function returns None, nothing is added to the stack.
        The object passed into the callBackFunction is potentially transformed to local coordinates,
        if useLocalCoordinates is true

        useLocalCoordinates is very useful for plugin developers.

        If false, the callback function is assumed to be working in global coordinates.  Objects
        created are added as-is, and objects passed into the function are sent in using global
        coordinates

        If true, the calling function is assumed to be  working in local coordinates.  Objects are
        transformed to local coordinates before they are passed into the callback method, and result
        objects are transformed to global coordinates after they are returned.

        This allows plugin developers to create objects in local coordinates, without worrying
        about the fact that the working plane is different than the global coordinate system.


        TODO: wrapper object for Wire will clean up forConstruction flag everywhere
        """
        results = []
        for obj in self.objects:

            if useLocalCoordinates:
                # TODO: this needs to work for all types of objects, not just vectors!
                r = callback(self.plane.toLocalCoords(obj))
                r = r.transformShape(self.plane.rG)
            else:
                r = callback(obj)

            if isinstance(r, Wire):
                if not r.forConstruction:
                    self._addPendingWire(r)
            results.append(r)

        return self._combineWithBase(results, combine, clean)

    def eachpoint(
        self: T,
        callback: Callable[[Location], Shape],
        useLocalCoordinates: bool = False,
        combine: CombineMode = False,
        clean: bool = True,
    ) -> T:
        """
        Same as each(), except each item on the stack is converted into a point before it
        is passed into the callback function.

        :return: CadQuery object which contains a list of  vectors (points ) on its stack.

        :param useLocalCoordinates: should points be in local or global coordinates
        :type useLocalCoordinates: boolean
        :param combine: True or "a" to combine the resulting solid with parent solids if found, "cut" or "s" to remove the resulting solid from the parent solids if found. False to keep the resulting solid separated from the parent solids.
        :param boolean clean: call :py:meth:`clean` afterwards to have a clean shape


        The resulting object has a point on the stack for each object on the original stack.
        Vertices and points remain a point.  Faces, Wires, Solids, Edges, and Shells are converted
        to a point by using their center of mass.

        If the stack has zero length, a single point is returned, which is the center of the current
        workplane/coordinate system
        """
        # convert stack to a list of points
        pnts = []
        plane = self.plane
        loc = self.plane.location

        if len(self.objects) == 0:
            # nothing on the stack. here, we'll assume we should operate with the
            # origin as the context point
            pnts.append(Location())
        else:
            for o in self.objects:
                if isinstance(o, (Vector, Shape)):
                    pnts.append(loc.inverse * Location(plane, o.Center()))
                elif isinstance(o, Sketch):
                    pnts.append(loc.inverse * Location(plane, o._faces.Center()))
                else:
                    pnts.append(o)

        if useLocalCoordinates:
            res = [callback(p).move(loc) for p in pnts]
        else:
            res = [callback(p * loc) for p in pnts]

        for r in res:
            if isinstance(r, Wire) and not r.forConstruction:
                self._addPendingWire(r)

        return self._combineWithBase(res, combine, clean)

    def rect(
        self: T,
        xLen: float,
        yLen: float,
        centered: Union[bool, Tuple[bool, bool]] = True,
        forConstruction: bool = False,
    ) -> T:
        """
        Make a rectangle for each item on the stack.

        :param xLen: length in the x direction (in workplane coordinates)
        :param yLen: length in the y direction (in workplane coordinates)
        :param centered: If True, the rectangle will be centered around the reference
          point. If False, the corner of the rectangle will be on the reference point and
          it will extend in the positive x and y directions. Can also use a 2-tuple to
          specify centering along each axis.
        :param forConstruction: should the new wires be reference geometry only?
        :type forConstruction: true if the wires are for reference, false if they are creating part
            geometry
        :return: a new CQ object with the created wires on the stack

        A common use case is to use a for-construction rectangle to define the centers of a hole
        pattern::

            s = Workplane().rect(4.0,4.0,forConstruction=True).vertices().circle(0.25)

        Creates 4 circles at the corners of a square centered on the origin.

        Negative values for xLen and yLen are permitted, although they only have an effect when
        centered is False.

        Future Enhancements:
            * project points not in the workplane plane onto the workplane plane
        """

        if isinstance(centered, bool):
            centered = (centered, centered)

        offset = Vector()
        if not centered[0]:
            offset += Vector(xLen / 2, 0, 0)
        if not centered[1]:
            offset += Vector(0, yLen / 2, 0)

        points = [
            Vector(xLen / -2.0, yLen / -2.0, 0),
            Vector(xLen / 2.0, yLen / -2.0, 0),
            Vector(xLen / 2.0, yLen / 2.0, 0),
            Vector(xLen / -2.0, yLen / 2.0, 0),
        ]

        points = [x + offset for x in points]

        # close the wire
        points.append(points[0])

        w = Wire.makePolygon(points, forConstruction)

        return self.eachpoint(lambda loc: w.moved(loc), True)

    # circle from current point
    def circle(self: T, radius: float, forConstruction: bool = False) -> T:
        """
        Make a circle for each item on the stack.

        :param radius: radius of the circle
        :type radius: float > 0
        :param forConstruction: should the new wires be reference geometry only?
        :type forConstruction: true if the wires are for reference, false if they are creating
            part geometry
        :return: a new CQ object with the created wires on the stack

        A common use case is to use a for-construction rectangle to define the centers of a
        hole pattern::

            s = Workplane().rect(4.0,4.0,forConstruction=True).vertices().circle(0.25)

        Creates 4 circles at the corners of a square centered on the origin. Another common case is
        to use successive circle() calls to create concentric circles.  This works because the
        center of a circle is its reference point::

            s = Workplane().circle(2.0).circle(1.0)

        Creates two concentric circles, which when extruded will form a ring.

        Future Enhancements:
            better way to handle forConstruction
            project points not in the workplane plane onto the workplane plane

        """

        c = Wire.makeCircle(radius, Vector(), Vector(0, 0, 1))
        c.forConstruction = forConstruction

        return self.eachpoint(lambda loc: c.moved(loc), True)

    # ellipse from current point
    def ellipse(
        self: T,
        x_radius: float,
        y_radius: float,
        rotation_angle: float = 0.0,
        forConstruction: bool = False,
    ) -> T:
        """
        Make an ellipse for each item on the stack.

        :param x_radius: x radius of the ellipse (x-axis of plane the ellipse should lie in)
        :type x_radius: float > 0
        :param y_radius: y radius of the ellipse (y-axis of plane the ellipse should lie in)
        :type y_radius: float > 0
        :param rotation_angle: angle to rotate the ellipse (0 = no rotation = default)
        :type rotation_angle: float
        :param forConstruction: should the new wires be reference geometry only?
        :type forConstruction: true if the wires are for reference, false if they are creating
            part geometry
        :return: a new CQ object with the created wires on the stack

        *NOTE* Due to a bug in opencascade (https://tracker.dev.opencascade.org/view.php?id=31290)
        the center of mass (equals center for next shape) is shifted. To create concentric ellipses
        use Workplane("XY")
            .center(10, 20).ellipse(100,10)
            .center(0, 0).ellipse(50, 5)
        """

        e = Wire.makeEllipse(
            x_radius,
            y_radius,
            Vector(),
            Vector(0, 0, 1),
            Vector(1, 0, 0),
            rotation_angle=rotation_angle,
        )
        e.forConstruction = forConstruction

        return self.eachpoint(lambda loc: e.moved(loc), True)

    def polygon(
        self: T,
        nSides: int,
        diameter: float,
        forConstruction: bool = False,
        circumscribed: bool = False,
    ) -> T:
        """
        Make a polygon for each item on the stack.

        By default, each polygon is created by inscribing it in a circle of the
        specified diameter, such that the first vertex is oriented in the x direction.
        Alternatively, each polygon can be created by circumscribing it around
        a circle of the specified diameter, such that the midpoint of the first edge
        is oriented in the x direction. Circumscribed polygons are thus rotated by
        pi/nSides radians relative to the inscribed polygon. This ensures the extent
        of the polygon along the positive x-axis is always known.
        This has the advantage of not requiring additional formulae for purposes such as
        tiling on the x-axis (at least for even sided polygons).

        :param nSides: number of sides, must be >= 3
        :param diameter: the diameter of the circle for constructing the polygon
        :param circumscribed: circumscribe the polygon about a circle
        :type circumscribed: true to create the polygon by circumscribing it about a circle,
            false to create the polygon by inscribing it in a circle
        :return: a polygon wire
        """

        # pnt is a vector in local coordinates
        angle = 2.0 * math.pi / nSides
        radius = diameter / 2.0
        if circumscribed:
            radius /= math.cos(angle / 2.0)
        pnts = []
        for i in range(nSides + 1):
            o = angle * i
            if circumscribed:
                o += angle / 2.0
            pnts.append(Vector(radius * math.cos(o), radius * math.sin(o), 0,))
        p = Wire.makePolygon(pnts, forConstruction)

        return self.eachpoint(lambda loc: p.moved(loc), True)

    def polyline(
        self: T,
        listOfXYTuple: Sequence[VectorLike],
        forConstruction: bool = False,
        includeCurrent: bool = False,
    ) -> T:
        """
        Create a polyline from a list of points

        :param listOfXYTuple: a list of points in Workplane coordinates
        :type listOfXYTuple: list of 2-tuples
        :param forConstruction: whether or not the edges are used for reference
        :type forConstruction: true if the edges are for reference, false if they are for creating geometry
            part geometry
        :param includeCurrent: use current point as a starting point of the polyline
        :return: a new CQ object with a list of edges on the stack

        *NOTE* most commonly, the resulting wire should be closed.
        """

        # Our list of new edges that will go into a new CQ object
        edges = []

        if includeCurrent:
            startPoint = self._findFromPoint(False)
            points = listOfXYTuple
        else:
            startPoint = self.plane.toWorldCoords(listOfXYTuple[0])
            points = listOfXYTuple[1:]

        # Draw a line for each set of points, starting from the from-point of the original CQ object
        for curTuple in points:
            endPoint = self.plane.toWorldCoords(curTuple)

            edges.append(Edge.makeLine(startPoint, endPoint))

            # We need to move the start point for the next line that we draw or we get stuck at the same startPoint
            startPoint = endPoint

            if not forConstruction:
                self._addPendingEdge(edges[-1])

        return self.newObject(edges)

    def close(self: T) -> T:
        """
        End 2D construction, and attempt to build a closed wire.

        :return: a CQ object with a completed wire on the stack, if possible.

        After 2D drafting with methods such as lineTo, threePointArc,
        tangentArcPoint and polyline, it is necessary to convert the edges
        produced by these into one or more wires.

        When a set of edges is closed, cadQuery assumes it is safe to build
        the group of edges into a wire. This example builds a simple triangular
        prism::

            s = Workplane().lineTo(1,0).lineTo(1,1).close().extrude(0.2)
        """
        endPoint = self._findFromPoint(True)

        if self.ctx.firstPoint is None:
            raise ValueError("No start point specified - cannot close")
        else:
            startPoint = self.ctx.firstPoint

        # Check if there is a distance between startPoint and endPoint
        # that is larger than what is considered a numerical error.
        # If so; add a line segment between endPoint and startPoint
        if endPoint.sub(startPoint).Length > 1e-6:
            self.lineTo(self.ctx.firstPoint.x, self.ctx.firstPoint.y)

        # Need to reset the first point after closing a wire
        self.ctx.firstPoint = None

        return self.wire()

    def largestDimension(self) -> float:
        """
        Finds the largest dimension in the stack.

        Used internally to create thru features, this is how you can compute
        how long or wide a feature must be to make sure to cut through all of the material

        :raises ValueError: if no solids or compounds are found
        :return: A value representing the largest dimension of the first solid on the stack
        """
        # Get all the solids contained within this CQ object
        compound = self.findSolid()

        return compound.BoundingBox().DiagonalLength

    def cutEach(
        self: T,
        fcn: Callable[[Location], Shape],
        useLocalCoords: bool = False,
        clean: bool = True,
    ) -> T:
        """
        Evaluates the provided function at each point on the stack (ie, eachpoint)
        and then cuts the result from the context solid.
        :param fcn: a function suitable for use in the eachpoint method: ie, that accepts a vector
        :param useLocalCoords: same as for :py:meth:`eachpoint`
        :param boolean clean: call :py:meth:`clean` afterwards to have a clean shape
        :raises ValueError: if no solids or compounds are found in the stack or parent chain
        :return: a CQ object that contains the resulting solid
        """
        ctxSolid = self.findSolid()

        # will contain all of the counterbores as a single compound
        results = cast(List[Shape], self.eachpoint(fcn, useLocalCoords).vals())

        s = ctxSolid.cut(*results)

        if clean:
            s = s.clean()

        return self.newObject([s])

    # but parameter list is different so a simple function pointer won't work
    def cboreHole(
        self: T,
        diameter: float,
        cboreDiameter: float,
        cboreDepth: float,
        depth: Optional[float] = None,
        clean: bool = True,
    ) -> T:
        """
        Makes a counterbored hole for each item on the stack.

        :param diameter: the diameter of the hole
        :type diameter: float > 0
        :param cboreDiameter: the diameter of the cbore
        :type cboreDiameter: float > 0 and > diameter
        :param cboreDepth: depth of the counterbore
        :type cboreDepth: float > 0
        :param depth: the depth of the hole
        :type depth: float > 0 or None to drill thru the entire part.
        :param boolean clean: call :py:meth:`clean` afterwards to have a clean shape

        The surface of the hole is at the current workplane plane.

        One hole is created for each item on the stack.  A very common use case is to use a
        construction rectangle to define the centers of a set of holes, like so::

                s = Workplane(Plane.XY()).box(2,4,0.5).faces(">Z").workplane()\
                    .rect(1.5,3.5,forConstruction=True)\
                    .vertices().cboreHole(0.125, 0.25,0.125,depth=None)

        This sample creates a plate with a set of holes at the corners.

        **Plugin Note**: this is one example of the power of plugins. Counterbored holes are quite
        time consuming to create, but are quite easily defined by users.

        see :py:meth:`cskHole` to make countersinks instead of counterbores
        """
        if depth is None:
            depth = self.largestDimension()

        boreDir = Vector(0, 0, -1)
        center = Vector()
        # first make the hole
        hole = Solid.makeCylinder(
            diameter / 2.0, depth, center, boreDir
        )  # local coordinates!

        # add the counter bore
        cbore = Solid.makeCylinder(cboreDiameter / 2.0, cboreDepth, Vector(), boreDir)
        r = hole.fuse(cbore)

        return self.cutEach(lambda loc: r.moved(loc), True, clean)

    # TODO: almost all code duplicated!
    # but parameter list is different so a simple function pointer won't work
    def cskHole(
        self: T,
        diameter: float,
        cskDiameter: float,
        cskAngle: float,
        depth: Optional[float] = None,
        clean: bool = True,
    ) -> T:
        """
        Makes a countersunk hole for each item on the stack.

        :param diameter: the diameter of the hole
        :type diameter: float > 0
        :param cskDiameter: the diameter of the countersink
        :type cskDiameter: float > 0 and > diameter
        :param cskAngle: angle of the countersink, in degrees ( 82 is common )
        :type cskAngle: float > 0
        :param depth: the depth of the hole
        :type depth: float > 0 or None to drill thru the entire part.
        :param boolean clean: call :py:meth:`clean` afterwards to have a clean shape

        The surface of the hole is at the current workplane.

        One hole is created for each item on the stack.  A very common use case is to use a
        construction rectangle to define the centers of a set of holes, like so::

                s = Workplane(Plane.XY()).box(2,4,0.5).faces(">Z").workplane()\
                    .rect(1.5,3.5,forConstruction=True)\
                    .vertices().cskHole(0.125, 0.25,82,depth=None)

        This sample creates a plate with a set of holes at the corners.

        **Plugin Note**: this is one example of the power of plugins. CounterSunk holes are quite
        time consuming to create, but are quite easily defined by users.

        see :py:meth:`cboreHole` to make counterbores instead of countersinks
        """

        if depth is None:
            depth = self.largestDimension()

        boreDir = Vector(0, 0, -1)
        center = Vector()

        # first make the hole
        hole = Solid.makeCylinder(
            diameter / 2.0, depth, center, boreDir
        )  # local coords!
        r = cskDiameter / 2.0
        h = r / math.tan(math.radians(cskAngle / 2.0))
        csk = Solid.makeCone(r, 0.0, h, center, boreDir)
        res = hole.fuse(csk)

        return self.cutEach(lambda loc: res.moved(loc), True, clean)

    # TODO: almost all code duplicated!
    # but parameter list is different so a simple function pointer won't work
    def hole(
        self: T, diameter: float, depth: Optional[float] = None, clean: bool = True,
    ) -> T:
        """
        Makes a hole for each item on the stack.

        :param diameter: the diameter of the hole
        :type diameter: float > 0
        :param depth: the depth of the hole
        :type depth: float > 0 or None to drill thru the entire part.
        :param boolean clean: call :py:meth:`clean` afterwards to have a clean shape

        The surface of the hole is at the current workplane.

        One hole is created for each item on the stack.  A very common use case is to use a
        construction rectangle to define the centers of a set of holes, like so::

                s = Workplane(Plane.XY()).box(2,4,0.5).faces(">Z").workplane()\
                    .rect(1.5,3.5,forConstruction=True)\
                    .vertices().hole(0.125, 0.25,82,depth=None)

        This sample creates a plate with a set of holes at the corners.

        **Plugin Note**: this is one example of the power of plugins. CounterSunk holes are quite
        time consuming to create, but are quite easily defined by users.

        see :py:meth:`cboreHole` and :py:meth:`cskHole` to make counterbores or countersinks
        """
        if depth is None:
            depth = self.largestDimension()

        boreDir = Vector(0, 0, -1)
        # first make the hole
        h = Solid.makeCylinder(
            diameter / 2.0, depth, Vector(), boreDir
        )  # local coordinates!

        return self.cutEach(lambda loc: h.moved(loc), True, clean)

    # TODO: duplicated code with _extrude and extrude
    def twistExtrude(
        self: T,
        distance: float,
        angleDegrees: float,
        combine: CombineMode = True,
        clean: bool = True,
    ) -> T:
        """
        Extrudes a wire in the direction normal to the plane, but also twists by the specified
        angle over the length of the extrusion.

        The center point of the rotation will be the center of the workplane.

        See extrude for more details, since this method is the same except for the the addition
        of the angle. In fact, if angle=0, the result is the same as a linear extrude.

        **NOTE**  This method can create complex calculations, so be careful using it with
        complex geometries

        :param distance: the distance to extrude normal to the workplane
        :param angle: angle (in degrees) to rotate through the extrusion
        :param combine: True or "a" to combine the resulting solid with parent solids if found, "cut" or "s" to remove the resulting solid from the parent solids if found. False to keep the resulting solid separated from the parent solids.
        :param boolean clean: call :py:meth:`clean` afterwards to have a clean shape
        :return: a CQ object with the resulting solid selected.
        """
        faces = self._getFaces()

        # compute extrusion vector and extrude
        eDir = self.plane.zDir.multiply(distance)

        # one would think that fusing faces into a compound and then extruding would work,
        # but it doesn't-- the resulting compound appears to look right, ( right number of faces, etc)
        # but then cutting it from the main solid fails with BRep_NotDone.
        # the work around is to extrude each and then join the resulting solids, which seems to work

        # underlying cad kernel can only handle simple bosses-- we'll aggregate them if there
        # are multiple sets
        shapes: List[Shape] = []
        for f in faces:
            thisObj = Solid.extrudeLinearWithRotation(
                f, self.plane.origin, eDir, angleDegrees
            )
            shapes.append(thisObj)

        r = Compound.makeCompound(shapes).fuse()

        return self._combineWithBase(r, combine, clean)

    def extrude(
        self: T,
        until: Union[float, Literal["next", "last"], Face],
        combine: CombineMode = True,
        clean: bool = True,
        both: bool = False,
        taper: Optional[float] = None,
    ) -> T:
        """
        Use all un-extruded wires in the parent chain to create a prismatic solid.

        :param until: The distance to extrude, normal to the workplane plane. When a float is
          passed, the extrusion extends this far and a negative value is in the opposite direction
          to the normal of the plane. The string "next" extrudes until the next face orthogonal to
          the wire normal. "last" extrudes to the last face. If a object of type Face is passed then
          the extrusion will extend until this face. **Note that the Workplane must contain a Solid for extruding to a given face.**        
        :param combine: True or "a" to combine the resulting solid with parent solids if found, "cut" or "s" to remove the resulting solid from the parent solids if found. False to keep the resulting solid separated from the parent solids.
        :param boolean clean: call :py:meth:`clean` afterwards to have a clean shape
        :param boolean both: extrude in both directions symmetrically
        :param float taper: angle for optional tapered extrusion
        :return: a CQ object with the resulting solid selected.

        The returned object is always a CQ object, and depends on whether combine is True, and
        whether a context solid is already defined:

        *  if combine is False, the new value is pushed onto the stack. Note that when extruding
          until a specified face, combine can not be False
        *  if combine is true, the value is combined with the context solid if it exists,
           and the resulting solid becomes the new context solid.
        """

        # If subtractive mode is requested, use cutBlind
        if combine in ("cut", "s"):
            return self.cutBlind(until, clean, taper)

        # Handle `until` multiple values
        elif until in ("next", "last") and combine in (True, "a"):
            if until == "next":
                faceIndex = 0
            elif until == "last":
                faceIndex = -1

            r = self._extrude(None, both=both, taper=taper, upToFace=faceIndex)

        elif isinstance(until, Face) and combine:
            r = self._extrude(None, both=both, taper=taper, upToFace=until)

        elif isinstance(until, (int, float)):
            r = self._extrude(until, both=both, taper=taper, upToFace=None)

        elif isinstance(until, (str, Face)) and combine is False:
            raise ValueError(
                "`combine` can't be set to False when extruding until a face"
            )

        else:
            raise ValueError(
                f"Do not know how to handle until argument of type {type(until)}"
            )

        return self._combineWithBase(r, combine, clean)

    def revolve(
        self: T,
        angleDegrees: float = 360.0,
        axisStart: Optional[VectorLike] = None,
        axisEnd: Optional[VectorLike] = None,
        combine: CombineMode = True,
        clean: bool = True,
    ) -> T:
        """
        Use all un-revolved wires in the parent chain to create a solid.

        :param angleDegrees: the angle to revolve through.
        :type angleDegrees: float, anything less than 360 degrees will leave the shape open
        :param axisStart: the start point of the axis of rotation
        :type axisStart: tuple, a two tuple
        :param axisEnd: the end point of the axis of rotation
        :type axisEnd: tuple, a two tuple
        :param combine: True or "a" to combine the resulting solid with parent solids if found, "cut" or "s" to remove the resulting solid from the parent solids if found. False to keep the resulting solid separated from the parent solids.
        :param boolean clean: call :py:meth:`clean` afterwards to have a clean shape
        :return: a CQ object with the resulting solid selected.

        The returned object is always a CQ object, and depends on whether combine is True, and
        whether a context solid is already defined:

        *  if combine is False, the new value is pushed onto the stack.
        *  if combine is true, the value is combined with the context solid if it exists,
           and the resulting solid becomes the new context solid.

        .. note::
            Keep in mind that `axisStart` and `axisEnd` are defined relative to the current Workplane center position.
            So if for example you want to revolve a circle centered at (10,0,0) around the Y axis, be sure to either :py:meth:`move` (or :py:meth:`moveTo`)
            the current Workplane position or specify `axisStart` and `axisEnd` with the correct vector position.
            In this example (0,0,0), (0,1,0) as axis coords would fail.
        """
        # Make sure we account for users specifying angles larger than 360 degrees
        angleDegrees %= 360.0

        # Compensate for OCCT not assuming that a 0 degree revolve means a 360 degree revolve
        angleDegrees = 360.0 if angleDegrees == 0 else angleDegrees

        # The default start point of the vector defining the axis of rotation will be the origin
        # of the workplane
        if axisStart is None:
            axisStart = self.plane.toWorldCoords((0, 0)).toTuple()
        else:
            axisStart = self.plane.toWorldCoords(axisStart).toTuple()

        # The default end point of the vector defining the axis of rotation should be along the
        # normal from the plane
        if axisEnd is None:
            # Make sure we match the user's assumed axis of rotation if they specified an start
            # but not an end
            if axisStart[1] != 0:
                axisEnd = self.plane.toWorldCoords((0, axisStart[1])).toTuple()
            else:
                axisEnd = self.plane.toWorldCoords((0, 1)).toTuple()
        else:
            axisEnd = self.plane.toWorldCoords(axisEnd).toTuple()

        # returns a Solid (or a compound if there were multiple)
        r = self._revolve(angleDegrees, axisStart, axisEnd)

        return self._combineWithBase(r, combine, clean)

    def sweep(
        self: T,
        path: Union["Workplane", Wire, Edge],
        multisection: bool = False,
        sweepAlongWires: Optional[bool] = None,
        makeSolid: bool = True,
        isFrenet: bool = False,
        combine: CombineMode = True,
        clean: bool = True,
        transition: Literal["right", "round", "transformed"] = "right",
        normal: Optional[VectorLike] = None,
        auxSpine: Optional["Workplane"] = None,
    ) -> T:
        """
        Use all un-extruded wires in the parent chain to create a swept solid.

        :param path: A wire along which the pending wires will be swept
        :param boolean multiSection: False to create multiple swept from wires on the chain along path. True to create only one solid swept along path with shape following the list of wires on the chain
        :param combine: True or "a" to combine the resulting solid with parent solids if found, "cut" or "s" to remove the resulting solid from the parent solids if found. False to keep the resulting solid separated from the parent solids.
        :param boolean clean: call :py:meth:`clean` afterwards to have a clean shape
        :param transition: handling of profile orientation at C1 path discontinuities. Possible values are {'transformed','round', 'right'} (default: 'right').
        :param normal: optional fixed normal for extrusion
        :param auxSpine: a wire defining the binormal along the extrusion path
        :return: a CQ object with the resulting solid selected.
        """

        if not sweepAlongWires is None:
            multisection = sweepAlongWires

            from warnings import warn

            warn(
                "sweepAlongWires keyword argument is is deprecated and will "
                "be removed in the next version; use multisection instead",
                DeprecationWarning,
            )

        r = self._sweep(
            path.wire() if isinstance(path, Workplane) else path,
            multisection,
            makeSolid,
            isFrenet,
            transition,
            normal,
            auxSpine,
        )  # returns a Solid (or a compound if there were multiple)

        return self._combineWithBase(r, combine, clean)

    def _combineWithBase(
        self: T,
        obj: Union[Shape, Iterable[Shape]],
        mode: CombineMode = True,
        clean: bool = False,
    ) -> T:
        """
        Combines the provided object with the base solid, if one can be found.
        :param obj: The object to be combined with the context solid
        :param mode: The mode to combine with the base solid (True, False, "cut", "a" or "s")
        :return: a new object that represents the result of combining the base object with obj,
           or obj if one could not be found
        """

        if mode:
            # since we are going to do something convert the iterable if needed
            if not isinstance(obj, Shape):
                obj = Compound.makeCompound(obj)

            # dispatch on the mode
            if mode in ("cut", "s"):
                newS = self._cutFromBase(obj)
            elif mode in (True, "a"):
                newS = self._fuseWithBase(obj)

        else:
            # do not combine branch
            newS = self.newObject(obj if not isinstance(obj, Shape) else [obj])

        if clean:
            # NB: not calling self.clean() to not pollute the parents
            newS.objects = [
                obj.clean() if isinstance(obj, Shape) else obj for obj in newS.objects
            ]

        return newS

    def _fuseWithBase(self: T, obj: Shape) -> T:
        """
        Fuse the provided object with the base solid, if one can be found.
        :param obj:
        :return: a new object that represents the result of combining the base object with obj,
           or obj if one could not be found
        """
        baseSolid = self._findType(
            (Solid, Compound), searchStack=True, searchParents=True
        )
        r = obj
        if baseSolid is not None:
            r = baseSolid.fuse(obj)
        elif isinstance(obj, Compound):
            r = obj.fuse()
        return self.newObject([r])

    def _cutFromBase(self: T, obj: Shape) -> T:
        """
        Cuts the provided object from the base solid, if one can be found.
        :param obj:
        :return: a new object that represents the result of combining the base object with obj,
           or obj if one could not be found
        """
        baseSolid = self._findType((Solid, Compound), True, True)

        r = obj
        if baseSolid is not None:
            r = baseSolid.cut(obj)

        return self.newObject([r])

    def combine(
        self: T, clean: bool = True, glue: bool = False, tol: Optional[float] = None,
    ) -> T:
        """
        Attempts to combine all of the items on the stack into a single item.
        WARNING: all of the items must be of the same type!

        :param boolean clean: call :py:meth:`clean` afterwards to have a clean shape
        :param boolean glue: use a faster gluing mode for non-overlapping shapes (default False)
        :param float tol: tolerance value for fuzzy bool operation mode (default None)
        :raises: ValueError if there are no items on the stack, or if they cannot be combined
        :return: a CQ object with the resulting object selected
        """

        items: List[Shape] = [o for o in self.objects if isinstance(o, Shape)]
        s = items.pop(0)

        if items:
            s = s.fuse(*items, glue=glue, tol=tol)

        if clean:
            s = s.clean()

        return self.newObject([s])

    def union(
        self: T,
        toUnion: Optional[Union["Workplane", Solid, Compound]] = None,
        clean: bool = True,
        glue: bool = False,
        tol: Optional[float] = None,
    ) -> T:
        """
        Unions all of the items on the stack of toUnion with the current solid.
        If there is no current solid, the items in toUnion are unioned together.

        :param toUnion:
        :type toUnion: a solid object, or a Workplane object having a solid,
        :param clean: call :py:meth:`clean` afterwards to have a clean shape (default True)
        :param glue: use a faster gluing mode for non-overlapping shapes (default False)
        :param tol: tolerance value for fuzzy bool operation mode (default None)
        :raises: ValueError if there is no solid to add to in the chain
        :return: a Workplane object with the resulting object selected
        """

        # first collect all of the items together
        newS: List[Shape]
        if isinstance(toUnion, Workplane):
            newS = cast(List[Shape], toUnion.solids().vals())
            if len(newS) < 1:
                raise ValueError(
                    "Workplane object must have at least one solid on the stack to union!"
                )
            self._mergeTags(toUnion)
        elif isinstance(toUnion, (Solid, Compound)):
            newS = [toUnion]
        else:
            raise ValueError("Cannot union type '{}'".format(type(toUnion)))

        # now combine with existing solid, if there is one
        # look for parents to cut from
        solidRef = self._findType(
            (Solid, Compound), searchStack=True, searchParents=True
        )
        if solidRef is not None:
            r = solidRef.fuse(*newS, glue=glue, tol=tol)
        elif len(newS) > 1:
            r = newS.pop(0).fuse(*newS, glue=glue, tol=tol)
        else:
            r = newS[0]

        if clean:
            r = r.clean()

        return self.newObject([r])

    def __or__(self: T, toUnion: Union["Workplane", Solid, Compound]) -> T:
        """
        Syntactic sugar for union.
        Notice that :code:`r = a | b` is equivalent to :code:`r = a.union(b)` and :code:`r = a + b`.

        Example::

            Box = Workplane("XY").box(1, 1, 1, centered=(False, False, False))
            Sphere = Workplane("XY").sphere(1)
            result = Box | Sphere
        """
        return self.union(toUnion)

    def __add__(self: T, toUnion: Union["Workplane", Solid, Compound]) -> T:
        """
        Syntactic sugar for union.
        Notice that :code:`r = a + b` is equivalent to :code:`r = a.union(b)` and :code:`r = a | b`.
        """
        return self.union(toUnion)

    def cut(
        self: T, toCut: Union["Workplane", Solid, Compound], clean: bool = True
    ) -> T:
        """
        Cuts the provided solid from the current solid, IE, perform a solid subtraction.

        :param toCut: object to cut
        :type toCut: a solid object, or a Workplane object having a solid,
        :param clean: call :py:meth:`clean` afterwards to have a clean shape
        :raises ValueError: if there is no solid to subtract from in the chain
        :return: a Workplane object with the resulting object selected
        """

        # look for parents to cut from
        solidRef = self.findSolid(searchStack=True, searchParents=True)

        solidToCut: Sequence[Shape]

        if isinstance(toCut, Workplane):
            solidToCut = _selectShapes(toCut.vals())
            self._mergeTags(toCut)
        elif isinstance(toCut, (Solid, Compound)):
            solidToCut = (toCut,)
        else:
            raise ValueError("Cannot cut type '{}'".format(type(toCut)))

        newS = solidRef.cut(*solidToCut)

        if clean:
            newS = newS.clean()

        return self.newObject([newS])

    def __sub__(self: T, toUnion: Union["Workplane", Solid, Compound]) -> T:
        """
        Syntactic sugar for cut.
        Notice that :code:`r = a - b` is equivalent to :code:`r = a.cut(b)`.

        Example::

            Box = Workplane("XY").box(1, 1, 1, centered=(False, False, False))
            Sphere = Workplane("XY").sphere(1)
            result = Box - Sphere
        """
        return self.cut(toUnion)

    def intersect(
        self: T, toIntersect: Union["Workplane", Solid, Compound], clean: bool = True,
    ) -> T:
        """
        Intersects the provided solid from the current solid.

        :param toIntersect: object to intersect
        :type toIntersect: a solid object, or a Workplane object having a solid,
        :param clean: call :py:meth:`clean` afterwards to have a clean shape
        :raises ValueError: if there is no solid to intersect with in the chain
        :return: a Workplane object with the resulting object selected
        """

        # look for parents to intersect with
        solidRef = self.findSolid(searchStack=True, searchParents=True)

        solidToIntersect: Sequence[Shape]

        if isinstance(toIntersect, Workplane):
            solidToIntersect = _selectShapes(toIntersect.vals())
            self._mergeTags(toIntersect)
        elif isinstance(toIntersect, (Solid, Compound)):
            solidToIntersect = (toIntersect,)
        else:
            raise ValueError("Cannot intersect type '{}'".format(type(toIntersect)))

        newS = solidRef.intersect(*solidToIntersect)

        if clean:
            newS = newS.clean()

        return self.newObject([newS])

    def __and__(self: T, toUnion: Union["Workplane", Solid, Compound]) -> T:
        """
        Syntactic sugar for intersect.
        Notice that :code:`r = a & b` is equivalent to :code:`r = a.intersect(b)`.

        Example::

            Box = Workplane("XY").box(1, 1, 1, centered=(False, False, False))
            Sphere = Workplane("XY").sphere(1)
            result = Box & Sphere
        """
        return self.intersect(toUnion)

    def cutBlind(
        self: T,
        until: Union[float, Literal["next", "last"], Face],
        clean: bool = True,
        taper: Optional[float] = None,
    ) -> T:
        """
        Use all un-extruded wires in the parent chain to create a prismatic cut from existing solid.
        You must define either :distance: , :untilNextFace: or :untilLastFace:

        Similar to extrude, except that a solid in the parent chain is required to remove material
        from. cutBlind always removes material from a part.

        :param until: The distance to cut to, normal to the workplane plane. When a negative float
          is passed the cut extends this far in the opposite direction to the normal of the plane
          (i.e in the solid). The string "next" cuts until the next face orthogonal to the wire
          normal.  "last" cuts to the last face. If a object of type Face is passed then the cut
          will extend until this face.
        :param boolean clean: call :py:meth:`clean` afterwards to have a clean shape
        :param float taper: angle for optional tapered extrusion
        :raises ValueError: if there is no solid to subtract from in the chain
        :return: a CQ object with the resulting object selected

        see :py:meth:`cutThruAll` to cut material from the entire part
        """
        # Handling of `until` passed values
        s: Union[Compound, Solid, Shape]
        if isinstance(until, str) and until in ("next", "last"):
            if until == "next":
                faceIndex = 0
            elif until == "last":
                faceIndex = -1

            s = self._extrude(None, taper=taper, upToFace=faceIndex, additive=False)

        elif isinstance(until, Face):
            s = self._extrude(None, taper=taper, upToFace=until, additive=False)

        elif isinstance(until, (int, float)):
            toCut = self._extrude(until, taper=taper, upToFace=None, additive=False)
            solidRef = self.findSolid()
            s = solidRef.cut(toCut)
        else:
            raise ValueError(
                f"Do not know how to handle until argument of type {type(until)}"
            )
        if clean:
            s = s.clean()

        return self.newObject([s])

    def cutThruAll(self: T, clean: bool = True, taper: float = 0) -> T:
        """
        Use all un-extruded wires in the parent chain to create a prismatic cut from existing solid.
        Cuts through all material in both normal directions of workplane.

        Similar to extrude, except that a solid in the parent chain is required to remove material
        from. cutThruAll always removes material from a part.

        :param boolean clean: call :py:meth:`clean` afterwards to have a clean shape
        :raises ValueError: if there is no solid to subtract from in the chain
        :raises ValueError: if there are no pending wires to cut with
        :return: a CQ object with the resulting object selected

        see :py:meth:`cutBlind` to cut material to a limited depth
        """
        solidRef = self.findSolid()

        s = solidRef.dprism(
            None, self._getFaces(), thruAll=True, additive=False, taper=-taper
        )

        if clean:
            s = s.clean()

        return self.newObject([s])

    def loft(
        self: T, ruled: bool = False, combine: CombineMode = True, clean: bool = True
    ) -> T:
        """
        Make a lofted solid, through the set of wires.

        :param boolean ruled: When set to `True` connects each section linearly and without continuity
        :param combine: True or "a" to combine the resulting solid with parent solids if found, "cut" or "s" to remove the resulting solid from the parent solids if found. False to keep the resulting solid separated from the parent solids.
        :param boolean clean: call :py:meth:`clean` afterwards to have a clean shape

        :return: a Workplane object containing the created loft
        
        """

        if self.ctx.pendingWires:
            wiresToLoft = self.ctx.popPendingWires()
        else:
            wiresToLoft = [f.outerWire() for f in self._getFaces()]

        if not wiresToLoft:
            raise ValueError("Nothing to loft")

        r: Shape = Solid.makeLoft(wiresToLoft, ruled)

        newS = self._combineWithBase(r, combine, clean)

        return newS

    def _getFaces(self) -> List[Face]:
        """
        Convert pending wires or sketches to faces for subsequent operation
        """

        rv: List[Face] = []

        for el in self.objects:
            if isinstance(el, Sketch):
                rv.extend(el)

        if not rv:
            rv.extend(wiresToFaces(self.ctx.popPendingWires()))

        return rv

    def _extrude(
        self,
        distance: Optional[float] = None,
        both: bool = False,
        taper: Optional[float] = None,
        upToFace: Optional[Union[int, Face]] = None,
        additive: bool = True,
    ) -> Union[Solid, Compound]:
        """
        Make a prismatic solid from the existing set of pending wires.

        :param distance: distance to extrude
        :param boolean both: extrude in both directions symetrically
        :param upToFace: if specified extrude up to the :upToFace: face, 0 for the next, -1 for the last
        :param additive: specify if extruding or cutting, required param for uptoface algorithm

        :return: OCCT solid(s), suitable for boolean operations.

        This method is a utility method, primarily for plugin and internal use.
        It is the basis for cutBlind, extrude, cutThruAll, and all similar methods.
        """

        def getFacesList(face, eDir, direction, both=False):
            """
            Utility function to make the code further below more clean and tidy
            Performs some test and raise appropriate error when no Faces are found for extrusion
            """
            facesList = self.findSolid().facesIntersectedByLine(
                face.Center(), eDir, direction=direction
            )
            if len(facesList) == 0 and both:
                raise ValueError(
                    "Couldn't find a face to extrude/cut to for at least one of the two required directions of extrusion/cut."
                )

            if len(facesList) == 0:
                # if we don't find faces in the workplane normal direction we try the other
                # direction (as the user might have created a workplane with wrong orientation)
                facesList = self.findSolid().facesIntersectedByLine(
                    face.Center(), eDir.multiply(-1.0), direction=direction
                )
                if len(facesList) == 0:
                    raise ValueError(
                        "Couldn't find a face to extrude/cut to. Check your workplane orientation."
                    )
            return facesList

        # process sketches or pending wires
        faces = self._getFaces()

        # check for nested geometry and tapered extrusion
        for face in faces:
            if taper and face.innerWires():
                raise ValueError("Inner wires not allowed with tapered extrusion")

        # compute extrusion vector and extrude
        if upToFace is not None:
            eDir = self.plane.zDir
        elif distance is not None:
            eDir = self.plane.zDir.multiply(distance)

        direction = "AlongAxis" if additive else "Opposite"
        taper = 0.0 if taper is None else taper

        toFuse = []

        if upToFace is not None:
            res = self.findSolid()
            for face in faces:
                if isinstance(upToFace, int):
                    facesList = getFacesList(face, eDir, direction, both=both)
                    if (
                        res.isInside(face.outerWire().Center())
                        and additive
                        and upToFace == 0
                    ):
                        upToFace = 1  # extrude until next face outside the solid

                    limitFace = facesList[upToFace]
                else:
                    limitFace = upToFace

                res = res.dprism(
                    None, [face], taper=taper, upToFace=limitFace, additive=additive,
                )

                if both:
                    facesList2 = getFacesList(
                        face, eDir.multiply(-1.0), direction, both=both
                    )
                    limitFace2 = facesList2[upToFace]
                    res = res.dprism(
                        None,
                        [face],
                        taper=taper,
                        upToFace=limitFace2,
                        additive=additive,
                    )

        else:
            for face in faces:
                res = Solid.extrudeLinear(face, eDir, taper=taper)
                toFuse.append(res)

                if both:
                    res = Solid.extrudeLinear(face, eDir.multiply(-1.0), taper=taper)
                    toFuse.append(res)

        return res if upToFace is not None else Compound.makeCompound(toFuse)

    def _revolve(
        self, angleDegrees: float, axisStart: VectorLike, axisEnd: VectorLike
    ) -> Compound:
        """
        Make a solid from the existing set of pending wires.

        :param angleDegrees: the angle to revolve through.
        :type angleDegrees: float, anything less than 360 degrees will leave the shape open
        :param axisStart: the start point of the axis of rotation
        :type axisStart: tuple, a two tuple
        :param axisEnd: the end point of the axis of rotation
        :type axisEnd: tuple, a two tuple
        :return: a OCCT solid(s), suitable for boolean operations.

        This method is a utility method, primarily for plugin and internal use.
        """

        # Revolve, make a compound out of them and then fuse them
        toFuse = []
        for f in self._getFaces():
            thisObj = Solid.revolve(f, angleDegrees, Vector(axisStart), Vector(axisEnd))
            toFuse.append(thisObj)

        return Compound.makeCompound(toFuse)

    def _sweep(
        self,
        path: Union["Workplane", Wire, Edge],
        multisection: bool = False,
        makeSolid: bool = True,
        isFrenet: bool = False,
        transition: Literal["right", "round", "transformed"] = "right",
        normal: Optional[VectorLike] = None,
        auxSpine: Optional["Workplane"] = None,
    ) -> Compound:
        """
        Makes a swept solid from an existing set of pending wires.

        :param path: A wire along which the pending wires will be swept
        :param boolean multisection:
            False to create multiple swept from wires on the chain along path
            True to create only one solid swept along path with shape following the list of wires on the chain
        :param transition:
            handling of profile orientation at C1 path discontinuities.
            Possible values are {'transformed','round', 'right'} (default: 'right').
        :param normal: optional fixed normal for extrusion
        :param auxSpine: a wire defining the binormal along the extrusion path
        :return: a solid, suitable for boolean operations
        """

        toFuse = []

        p = path.val() if isinstance(path, Workplane) else path
        if not isinstance(p, (Wire, Edge)):
            raise ValueError("Wire or Edge instance required")

        mode: Union[Vector, Edge, Wire, None] = None
        if normal:
            mode = Vector(normal)
        elif auxSpine:
            wire = auxSpine.val()
            if not isinstance(wire, (Edge, Wire)):
                raise ValueError("Wire or Edge instance required")
            mode = wire

        if not multisection:
            for f in self._getFaces():
                thisObj = Solid.sweep(f, p, makeSolid, isFrenet, mode, transition)
                toFuse.append(thisObj)
        else:
            sections = self.ctx.popPendingWires()
            thisObj = Solid.sweep_multi(sections, p, makeSolid, isFrenet, mode)
            toFuse.append(thisObj)

        return Compound.makeCompound(toFuse)

    def interpPlate(
        self: T,
        surf_edges: Union[Sequence[VectorLike], Sequence[Edge]],
        surf_pts: Sequence[VectorLike] = [],
        thickness: float = 0,
        combine: bool = False,
        clean: bool = True,
        degree: int = 3,
        nbPtsOnCur: int = 15,
        nbIter: int = 2,
        anisotropy: bool = False,
        tol2d: float = 0.00001,
        tol3d: float = 0.0001,
        tolAng: float = 0.01,
        tolCurv: float = 0.1,
        maxDeg: int = 8,
        maxSegments: int = 9,
    ) -> T:
        """
        Returns a plate surface that is 'thickness' thick, enclosed by 'surf_edge_pts' points,  and going through 'surf_pts' points.  Using pushpoints directly with interpPlate and combine=True, can be very resources intensive depending on the complexity of the shape. In this case set combine=False.

        :param surf_edges
        :type 1 surf_edges: list of [x,y,z] float ordered coordinates
        :type 2 surf_edges: list of ordered or unordered CadQuery wires
        :param surf_pts = [] (uses only edges if [])
        :type surf_pts: list of [x,y,z] float coordinates
        :param thickness = 0 (returns 2D surface if 0)
        :type thickness: float (may be negative or positive depending on thickening direction)
        :param combine: should the results be combined with other solids on the stack
            (and each other)?
        :type combine: true to combine shapes, false otherwise.
        :param boolean clean: call :py:meth:`clean` afterwards to have a clean shape
        :param Degree = 3 (OCCT default)
        :type Degree: Integer >= 2
        :param NbPtsOnCur = 15 (OCCT default)
        :type: NbPtsOnCur Integer >= 15
        :param NbIter = 2 (OCCT default)
        :type: NbIterInteger >= 2
        :param anisotropy = False (OCCT default)
        :type anisotropy: Boolean
        :param: Tol2d = 0.00001 (OCCT default)
        :type Tol2d: float > 0
        :param Tol3d = 0.0001 (OCCT default)
        :type Tol3dReal: float > 0
        :param TolAng = 0.01 (OCCT default)
        :type TolAngReal: float > 0
        :param TolCurv = 0.1 (OCCT default)
        :type TolCurvReal: float > 0
        :param MaxDeg = 8 (OCCT default)
        :type MaxDegInteger: Integer >= 2 (?)
        :param MaxSegments = 9 (OCCT default)
        :type MaxSegments: Integer >= 2 (?)
        """

        # If thickness is 0, only a 2D surface will be returned.
        if thickness == 0:
            combine = False

        # Creates interpolated plate
        p = Solid.interpPlate(
            surf_edges,
            surf_pts,
            thickness,
            degree,
            nbPtsOnCur,
            nbIter,
            anisotropy,
            tol2d,
            tol3d,
            tolAng,
            tolCurv,
            maxDeg,
            maxSegments,
        )

        plates = self.eachpoint(lambda loc: p.moved(loc), True)

        # if combination is not desired, just return the created boxes
        if not combine:
            return plates
        else:
            return self.union(plates, clean=clean)

    def box(
        self: T,
        length: float,
        width: float,
        height: float,
        centered: Union[bool, Tuple[bool, bool, bool]] = True,
        combine: bool = True,
        clean: bool = True,
    ) -> T:
        """
        Return a 3d box with specified dimensions for each object on the stack.

        :param length: box size in X direction
        :type length: float > 0
        :param width: box size in Y direction
        :type width: float > 0
        :param height: box size in Z direction
        :type height: float > 0
        :param centered: If True, the box will be centered around the reference point.
          If False, the corner of the box will be on the reference point and it will
          extend in the positive x, y and z directions. Can also use a 3-tuple to
          specify centering along each axis.
        :param combine: should the results be combined with other solids on the stack
            (and each other)?
        :param clean: call :py:meth:`clean` afterwards to have a clean shape

        One box is created for each item on the current stack. If no items are on the stack, one box
        using the current workplane center is created.

        If combine is true, the result will be a single object on the stack. If a solid was found
        in the chain, the result is that solid with all boxes produced fused onto it otherwise, the
        result is the combination of all the produced boxes.

        If combine is false, the result will be a list of the boxes produced.

        Most often boxes form the basis for a part::

            # make a single box with lower left corner at origin
            s = Workplane().box(1, 2, 3, centered=False)

        But sometimes it is useful to create an array of them::

            # create 4 small square bumps on a larger base plate:
            s = (
                Workplane().
                box(4, 4, 0.5).
                faces(">Z").
                workplane().
                rect(3, 3, forConstruction=True)
                .vertices()
                .box(0.25, 0.25, 0.25, combine=True)
            )

        """

        if isinstance(centered, bool):
            centered = (centered, centered, centered)

        offset = Vector()
        if centered[0]:
            offset += Vector(-length / 2, 0, 0)
        if centered[1]:
            offset += Vector(0, -width / 2, 0)
        if centered[2]:
            offset += Vector(0, 0, -height / 2)

        box = Solid.makeBox(length, width, height, offset)

        boxes = self.eachpoint(lambda loc: box.moved(loc), True)

        # if combination is not desired, just return the created boxes
        if not combine:
            return boxes
        else:
            # combine everything
            return self.union(boxes, clean=clean)

    def sphere(
        self: T,
        radius: float,
        direct: VectorLike = (0, 0, 1),
        angle1: float = -90,
        angle2: float = 90,
        angle3: float = 360,
        centered: Union[bool, Tuple[bool, bool, bool]] = True,
        combine: bool = True,
        clean: bool = True,
    ) -> T:
        """
        Returns a 3D sphere with the specified radius for each point on the stack.

        :param radius: The radius of the sphere
        :type radius: float > 0
        :param direct: The direction axis for the creation of the sphere
        :type direct: A three-tuple
        :param angle1: The first angle to sweep the sphere arc through
        :type angle1: float > 0
        :param angle2: The second angle to sweep the sphere arc through
        :type angle2: float > 0
        :param angle3: The third angle to sweep the sphere arc through
        :type angle3: float > 0
        :param centered: If True, the sphere will be centered around the reference point. If False,
          the corner of a bounding box around the sphere will be on the reference point and it
          will extend in the positive x, y and z directions. Can also use a 3-tuple to specify
          centering along each axis.
        :param combine: Whether the results should be combined with other solids on the stack
            (and each other)
        :type combine: true to combine shapes, false otherwise
        :param clean: call :py:meth:`clean` afterwards to have a clean shape
        :return: A sphere object for each point on the stack

        One sphere is created for each item on the current stack. If no items are on the stack, one
        box using the current workplane center is created.

        If combine is true, the result will be a single object on the stack. If a solid was found
        in the chain, the result is that solid with all spheres produced fused onto it otherwise,
        the result is the combination of all the produced spheres.

        If combine is false, the result will be a list of the spheres produced.
        """

        # Convert the direction tuple to a vector, if needed
        if isinstance(direct, tuple):
            direct = Vector(direct)

        if isinstance(centered, bool):
            centered = (centered, centered, centered)

        offset = Vector()
        if not centered[0]:
            offset += Vector(radius, 0, 0)
        if not centered[1]:
            offset += Vector(0, radius, 0)
        if not centered[2]:
            offset += Vector(0, 0, radius)

        s = Solid.makeSphere(radius, offset, direct, angle1, angle2, angle3)

        # We want a sphere for each point on the workplane
        spheres = self.eachpoint(lambda loc: s.moved(loc), True)

        # If we don't need to combine everything, just return the created spheres
        if not combine:
            return spheres
        else:
            return self.union(spheres, clean=clean)

    def cylinder(
        self: T,
        height: float,
        radius: float,
        direct: Vector = Vector(0, 0, 1),
        angle: float = 360,
        centered: Union[bool, Tuple[bool, bool, bool]] = True,
        combine: bool = True,
        clean: bool = True,
    ) -> T:
        """
        Returns a cylinder with the specified radius and height for each point on the stack

        :param height: The height of the cylinder
        :type height: float > 0
        :param radius: The radius of the cylinder
        :type radius: float > 0
        :param direct: The direction axis for the creation of the cylinder
        :type direct: A three-tuple
        :param angle: The angle to sweep the cylinder arc through
        :type angle: float > 0
        :param centered: If True, the cylinder will be centered around the reference point. If False,
            the corner of a bounding box around the cylinder will be on the reference point and it
            will extend in the positive x, y and z directions. Can also use a 3-tuple to specify
            centering along each axis.
        :param combine: Whether the results should be combined with other solids on the stack
            (and each other)
        :type combine: true to combine shapes, false otherwise
        :param clean: call :py:meth:`clean` afterwards to have a clean shape
        :return: A cylinder object for each point on the stack

        One cylinder is created for each item on the current stack. If no items are on the stack, one
        cylinder is created using the current workplane center.

        If combine is true, the result will be a single object on the stack. If a solid was found
        in the chain, the result is that solid with all cylinders produced fused onto it otherwise,
        the result is the combination of all the produced cylinders.

        If combine is false, the result will be a list of the cylinders produced.
        """

        if isinstance(centered, bool):
            centered = (centered, centered, centered)

        offset = Vector()
        if not centered[0]:
            offset += Vector(radius, 0, 0)
        if not centered[1]:
            offset += Vector(0, radius, 0)
        if centered[2]:
            offset += Vector(0, 0, -height / 2)

        s = Solid.makeCylinder(radius, height, offset, direct, angle)

        # We want a cylinder for each point on the workplane
        cylinders = self.eachpoint(lambda loc: s.moved(loc), True)

        # If we don't need to combine everything, just return the created cylinders
        if not combine:
            return cylinders
        else:
            return self.union(cylinders, clean=clean)

    def wedge(
        self: T,
        dx: float,
        dy: float,
        dz: float,
        xmin: float,
        zmin: float,
        xmax: float,
        zmax: float,
        pnt: VectorLike = Vector(0, 0, 0),
        dir: VectorLike = Vector(0, 0, 1),
        centered: Union[bool, Tuple[bool, bool, bool]] = True,
        combine: bool = True,
        clean: bool = True,
    ) -> T:
        """
        Returns a 3D wedge with the specified dimensions for each point on the stack.

        :param dx: Distance along the X axis
        :param dy: Distance along the Y axis
        :param dz: Distance along the Z axis
        :param xmin: The minimum X location
        :param zmin: The minimum Z location
        :param xmax: The maximum X location
        :param zmax: The maximum Z location
        :param pnt: A vector (or tuple) for the origin of the direction for the wedge
        :param dir: The direction vector (or tuple) for the major axis of the wedge
        :param centered: If True, the wedge will be centered around the reference point.
          If False, the corner of the wedge will be on the reference point and it will
          extend in the positive x, y and z directions. Can also use a 3-tuple to
          specify centering along each axis.
        :param combine: Whether the results should be combined with other solids on the stack
          (and each other)
        :param clean: True to attempt to have the kernel clean up the geometry, False otherwise
        :return: A wedge object for each point on the stack

        One wedge is created for each item on the current stack. If no items are on the stack, one
        wedge using the current workplane center is created.

        If combine is True, the result will be a single object on the stack. If a solid was found
        in the chain, the result is that solid with all wedges produced fused onto it otherwise,
        the result is the combination of all the produced wedges.

        If combine is False, the result will be a list of the wedges produced.
        """

        # Convert the point tuple to a vector, if needed
        if isinstance(pnt, tuple):
            pnt = Vector(pnt)

        # Convert the direction tuple to a vector, if needed
        if isinstance(dir, tuple):
            dir = Vector(dir)

        if isinstance(centered, bool):
            centered = (centered, centered, centered)

        offset = Vector()
        if centered[0]:
            offset += Vector(-dx / 2, 0, 0)
        if centered[1]:
            offset += Vector(0, -dy / 2, 0)
        if centered[2]:
            offset += Vector(0, 0, -dz / 2)

        w = Solid.makeWedge(dx, dy, dz, xmin, zmin, xmax, zmax, offset, dir)

        # We want a wedge for each point on the workplane
        wedges = self.eachpoint(lambda loc: w.moved(loc), True)

        # If we don't need to combine everything, just return the created wedges
        if not combine:
            return wedges
        else:
            return self.union(wedges, clean=clean)

    def clean(self: T) -> T:
        """
        Cleans the current solid by removing unwanted edges from the
        faces.

        Normally you don't have to call this function. It is
        automatically called after each related operation. You can
        disable this behavior with `clean=False` parameter if method
        has any. In some cases this can improve performance
        drastically but is generally dis-advised since it may break
        some operations such as fillet.

        Note that in some cases where lots of solid operations are
        chained, `clean()` may actually improve performance since
        the shape is 'simplified' at each step and thus next operation
        is easier.

        Also note that, due to limitation of the underlying engine,
        `clean` may fail to produce a clean output in some cases such as
        spherical faces.
        """

        cleanObjects = [
            obj.clean() if isinstance(obj, Shape) else obj for obj in self.objects
        ]

        return self.newObject(cleanObjects)

    @deprecate_kwarg_name("cut", "combine='cut'")
    def text(
        self: T,
        txt: str,
        fontsize: float,
        distance: float,
        cut: bool = True,
        combine: CombineMode = False,
        clean: bool = True,
        font: str = "Arial",
        fontPath: Optional[str] = None,
        kind: Literal["regular", "bold", "italic"] = "regular",
        halign: Literal["center", "left", "right"] = "center",
        valign: Literal["center", "top", "bottom"] = "center",
    ) -> T:
        """
        Returns a 3D text.

        :param txt: text to be rendered
        :param fontsize: size of the font in model units
        :param distance: the distance to extrude or cut, normal to the workplane plane
        :type distance: float, negative means opposite the normal direction
        :param cut: True to cut the resulting solid from the parent solids if found
        :param combine: True or "a" to combine the resulting solid with parent solids if found, "cut" or "s" to remove the resulting solid from the parent solids if found. False to keep the resulting solid separated from the parent solids.
        :param clean: call :py:meth:`clean` afterwards to have a clean shape
        :param font: font name
        :param fontPath: path to font file
        :param kind: font type
        :param halign: horizontal alignment
        :param valign: vertical alignment
        :return: a CQ object with the resulting solid selected

        The returned object is always a Workplane object, and depends on whether combine is True, and
        whether a context solid is already defined:

        *  if combine is False, the new value is pushed onto the stack.
        *  if combine is true, the value is combined with the context solid if it exists,
           and the resulting solid becomes the new context solid.

        Examples::

            cq.Workplane().text("CadQuery", 5, 1)

        Specify the font (name), and kind to use an installed system font::

            cq.Workplane().text("CadQuery", 5, 1, font="Liberation Sans Narrow", kind="italic")

        Specify fontPath to use a font from a given file::

            cq.Workplane().text("CadQuery", 5, 1, fontPath="/opt/fonts/texgyrecursor-bold.otf")

        Cutting text into a solid::

            cq.Workplane().box(8, 8, 8).faces(">Z").workplane().text("Z", 5, -1.0)

        """
        r = Compound.makeText(
            txt,
            fontsize,
            distance,
            font=font,
            fontPath=fontPath,
            kind=kind,
            halign=halign,
            valign=valign,
            position=self.plane,
        )

        if cut:
            combine = "cut"

        return self._combineWithBase(r, combine, clean)

    def section(self: T, height: float = 0.0) -> T:
        """
        Slices current solid at the given height.

        :param float height: height to slice at (default: 0)
        :raises ValueError: if no solids or compounds are found
        :return: a CQ object with the resulting face(s).
        """

        solidRef = self.findSolid(searchStack=True, searchParents=True)

        plane = Face.makePlane(
            basePnt=self.plane.origin + self.plane.zDir * height, dir=self.plane.zDir
        )

        r = solidRef.intersect(plane)

        return self.newObject([r])

    def toPending(self: T) -> T:
        """
        Adds wires/edges to pendingWires/pendingEdges.

        :return: same CQ object with updated context.
        """

        self.ctx.pendingWires.extend(el for el in self.objects if isinstance(el, Wire))
        self.ctx.pendingEdges.extend(el for el in self.objects if isinstance(el, Edge))

        return self

    def offset2D(
        self: T,
        d: float,
        kind: Literal["arc", "intersection", "tangent"] = "arc",
        forConstruction: bool = False,
    ) -> T:
        """
        Creates a 2D offset wire.

        :param d: thickness. Negative thickness denotes offset to inside.
        :param kind: offset kind. Use "arc" for rounded and "intersection" for sharp edges (default: "arc")
        :param forConstruction: Should the result be added to pending wires?

        :return: CQ object with resulting wire(s).
        """

        ws = self._consolidateWires()
        rv = list(chain.from_iterable(w.offset2D(d, kind) for w in ws))

        self.ctx.pendingEdges = []
        if forConstruction:
            for wire in rv:
                wire.forConstruction = True
            self.ctx.pendingWires = []
        else:
            self.ctx.pendingWires = rv

        return self.newObject(rv)

    def _locs(self: T) -> List[Location]:
        """
        Convert items on the stack into locations.
        """

        plane = self.plane
        locs: List[Location] = []

        for obj in self.objects:
            if isinstance(obj, (Vector, Shape)):
                locs.append(Location(plane, obj.Center()))
            elif isinstance(obj, Location):
                locs.append(obj)
        if not locs:
            locs.append(self.plane.location)

        return locs

    def sketch(self: T) -> Sketch:
        """
        Initialize and return a sketch

        :return: Sketch object with the current workplane as a parent.
        """

        parent = self.newObject([])

        rv = Sketch(parent=parent, locs=self._locs())
        parent.objects.append(rv)

        return rv

    def placeSketch(self: T, *sketches: Sketch) -> T:
        """
        Place the provided sketch(es) based on the current items on the stack.

        :return: Workplane object with the sketch added.
        """

        rv = []

        for s in sketches:
            s_new = s.copy()
            s_new.locs = self._locs()

            rv.append(s_new)

        return self.newObject(rv)

    def _repr_javascript_(self) -> Any:
        """
        Special method for rendering current object in a jupyter notebook
        """

        if type(self.val()) is Vector:
            return "&lt {} &gt".format(self.__repr__()[1:-1])
        else:
            return Compound.makeCompound(
                _selectShapes(self.objects)
            )._repr_javascript_()


# alias for backward compatibility
CQ = Workplane
