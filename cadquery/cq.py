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


from .occ_impl.geom import Vector, Plane, Location
from .occ_impl.shapes import (
    Shape,
    Edge,
    Wire,
    Face,
    Solid,
    Compound,
    sortWiresByBuildOrder,
)

from .occ_impl.exporters.svg import getSVG, exportSVG

from .utils import deprecate_kwarg, deprecate

from .selectors import (
    Selector,
    PerpendicularDirSelector,
    NearestToPointSelector,
    StringSyntaxSelector,
)

CQObject = Union[Vector, Location, Shape]
VectorLike = Union[Tuple[float, float], Tuple[float, float, float], Vector]


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


class Workplane(object):
    """
    Defines a coordinate system in space, in which 2-d coordinates can be used.

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

    def tag(self, name: str) -> "Workplane":
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

    def split(self, keepTop: bool = False, keepBottom: bool = False) -> "Workplane":
        """
        Splits a solid on the stack into two parts, optionally keeping the separate parts.

        :param boolean keepTop: True to keep the top, False or None to discard it
        :param boolean keepBottom: True to keep the bottom, False or None to discard it
        :raises: ValueError if keepTop and keepBottom are both false.
        :raises: ValueError if there is not a solid in the current stack or the parent chain
        :returns: CQ object with the desired objects on the stack.

        The most common operation splits a solid and keeps one half. This sample creates
        split bushing::

            # drill a hole in the side
            c = Workplane().box(1,1,1).faces(">Z").workplane().circle(0.25).cutThruAll()
            
            # now cut it in half sideways
            c = c.faces(">Y").workplane(-0.5).split(keepTop=True)
        """

        solid = self.findSolid()

        if (not keepTop) and (not keepBottom):
            raise ValueError("You have to keep at least one half")

        maxDim = solid.BoundingBox().DiagonalLength * 10.0
        topCutBox = self.rect(maxDim, maxDim)._extrude(maxDim)
        bottomCutBox = self.rect(maxDim, maxDim)._extrude(-maxDim)

        top = solid.cut(bottomCutBox)
        bottom = solid.cut(topCutBox)

        if keepTop and keepBottom:
            # Put both on the stack, leave original unchanged.
            return self.newObject([top, bottom])
        else:
            # Put the one we are keeping on the stack, and also update the
            # context solidto the one we kept.
            if keepTop:
                return self.newObject([top])
            else:
                return self.newObject([bottom])

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
        toCombine = self.solids().vals()

        if otherCQToCombine:
            for obj in otherCQToCombine.solids().vals():
                toCombine.append(obj)

        if len(toCombine) < 1:
            raise ValueError("Cannot Combine: at least one solid required!")

        # get context solid and we don't want to find our own objects
        ctxSolid = self.findSolid(searchStack=False, searchParents=True)

        if ctxSolid is None:
            ctxSolid = toCombine.pop(0)

        # now combine them all. make sure to save a reference to the ctxSolid pointer!
        s: Shape = ctxSolid
        if toCombine:
            s = s.fuse(*_selectShapes(toCombine))

        return self.newObject([s])

    def all(self) -> List["Workplane"]:
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
    def add(self, obj: "Workplane") -> "Workplane":
        ...

    @overload
    def add(self, obj: CQObject) -> "Workplane":
        ...

    @overload
    def add(self, obj: Iterable[CQObject]) -> "Workplane":
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
        results into a single Workplane object. Shelling is one common example.
        """
        if isinstance(obj, list):
            self.objects.extend(obj)
        elif isinstance(obj, Workplane):
            self.objects.extend(obj.objects)
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
        Search the parent chain for a an object with tag == name.

        :param name: the tag to search for
        :type name: string
        :returns: the CQ object with tag == name
        :raises: ValueError if no object tagged name
        """
        rv = self.ctx.tags.get(name)

        if rv is None:
            raise ValueError(f"No CQ object named {name} in chain")

        return rv

    def toOCC(self) -> Any:
        """
        Directly returns the wrapped OCCT object.
        :return: The wrapped OCCT object
        :rtype TopoDS_Shape or a subclass
        """

        return self.val().wrapped

    def workplane(
        self,
        offset: float = 0.0,
        invert: bool = False,
        centerOption: Literal[
            "CenterOfMass", "ProjectedOrigin", "CenterOfBoundBox"
        ] = "ProjectedOrigin",
        origin: Optional[VectorLike] = None,
    ) -> "Workplane":
        """
        Creates a new 2-D workplane, located relative to the first face on the stack.

        :param offset:  offset for the work plane in the Z direction. Default
        :param invert:  invert the Z direction from that of the face.
        :param centerOption: how local origin of workplane is determined.
        :param origin: origin for plane center, requires 'ProjectedOrigin' centerOption.
        :type offset: float or None=0.0
        :type invert: boolean or None=False
        :type centerOption: string or None='ProjectedOrigin'
        :type origin: Vector or None
        :rtype: Workplane object ( which is a subclass of CQ )

        The first element on the stack must be a face, a set of
        co-planar faces or a vertex.  If a vertex, then the parent
        item on the chain immediately before the vertex must be a
        face.

        The result will be a 2-d working plane
        with a new coordinate system set up as follows:

           * The centerOption paramter sets how the center is defined.
             Options are 'CenterOfMass', 'CenterOfBoundBox', or 'ProjectedOrigin'.
             'CenterOfMass' and 'CenterOfBoundBox' are in relation to the selected
             face(s) or vertex (vertices). 'ProjectedOrigin' uses by default the current origin 
             or the optional origin parameter (if specified) and projects it onto the plane
             defined by the selected face(s).
           * The Z direction will be normal to the plane of the face,computed
             at the center point.
           * The X direction will be parallel to the x-y plane. If the workplane is  parallel to
             the global x-y plane, the x direction of the workplane will co-incide with the
             global x direction.

        Most commonly, the selected face will be planar, and the workplane lies in the same plane
        of the face ( IE, offset=0).  Occasionally, it is useful to define a face offset from
        an existing surface, and even more rarely to define a workplane based on a face that is
        not planar.

        To create a workplane without first having a face, use the Workplane() method.

        Future Enhancements:
          * Allow creating workplane from planar wires
          * Allow creating workplane based on an arbitrary point on a face, not just the center.
            For now you can work around by creating a workplane and then offsetting the center
            afterwards.
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
        s = Workplane(plane)
        s.parent = self
        s.ctx = self.ctx

        # a new workplane has the center of the workplane on the stack
        return s

    def copyWorkplane(self, obj: "Workplane") -> "Workplane":
        """
        Copies the workplane from obj.

        :param obj: an object to copy the workplane from
        :type obj: a CQ object
        :returns: a CQ object with obj's workplane
        """
        out = Workplane(obj.plane)
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

    def first(self) -> "Workplane":
        """
        Return the first item on the stack
        :returns: the first item on the stack.
        :rtype: a CQ object
        """
        return self.newObject(self.objects[0:1])

    def item(self, i: int) -> "Workplane":
        """

        Return the ith item on the stack.
        :rtype: a CQ object
        """
        return self.newObject([self.objects[i]])

    def last(self) -> "Workplane":
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

        :param searchStack: should objects on the stack be searched first.
        :param searchParents: should parents be searched?
        :raises: ValueError if no solid is found in the current object or its parents,
            and errorOnEmpty is True

        This function is very important for chains that are modifying a single parent object,
        most often a solid.

        Most of the time, a chain defines or selects a solid, and then modifies it using workplanes
        or other operations.

        Plugin Developers should make use of this method to find the solid that should be modified,
        if the plugin implements a unary operation, or if the operation will automatically merge its
        results with an object already on the stack.
        """

        return self._findType((Solid, Compound), searchStack, searchParents)

    def findFace(self, searchStack: bool = True, searchParents: bool = True) -> Face:
        """
        Finds the first face object in the chain, searching from the current node
        backwards through parents until one is found.

        :param searchStack: should objects on the stack be searched first.
        :param searchParents: should parents be searched?
        :raises: ValueError if no face is found in the current object or its parents,
            and errorOnEmpty is True
        """

        return self._findType(Face, searchStack, searchParents)

    def _selectObjects(
        self,
        objType: Any,
        selector: Optional[Union[Selector, str]] = None,
        tag: Optional[str] = None,
    ) -> "Workplane":
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
        cq_obj = self._getTagged(tag) if tag else self
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
        self, selector: Optional[Union[Selector, str]] = None, tag: Optional[str] = None
    ) -> "Workplane":
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
        self, selector: Optional[Union[Selector, str]] = None, tag: Optional[str] = None
    ) -> "Workplane":
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
        self, selector: Optional[Union[Selector, str]] = None, tag: Optional[str] = None
    ) -> "Workplane":
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
        self, selector: Optional[Union[Selector, str]] = None, tag: Optional[str] = None
    ) -> "Workplane":
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
        self, selector: Optional[Union[Selector, str]] = None, tag: Optional[str] = None
    ) -> "Workplane":
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
        self, selector: Optional[Union[Selector, str]] = None, tag: Optional[str] = None
    ) -> "Workplane":
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
        self, selector: Optional[Union[Selector, str]] = None, tag: Optional[str] = None
    ) -> "Workplane":
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

    def rotateAboutCenter(
        self, axisEndPoint: VectorLike, angleDegrees: float
    ) -> "Workplane":
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
            * This method doesnt expose a very good interface, because the axis of rotation
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

        return self.each(_rot, False)

    def rotate(
        self, axisStartPoint: VectorLike, axisEndPoint: VectorLike, angleDegrees: float
    ) -> "Workplane":
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
        self,
        mirrorPlane: Union[
            Literal["XY", "YX", "XZ", "ZX", "YZ", "ZY"], VectorLike, Face, "Workplane"
        ] = "XY",
        basePointVector: Optional[VectorLike] = None,
        union: bool = False,
    ):
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

    def translate(self, vec: VectorLike) -> "Workplane":
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
        self, thickness: float, kind: Literal["arc", "intersection"] = "arc"
    ) -> "Workplane":
        """
        Remove the selected faces to create a shell of the specified thickness.

        To shell, first create a solid, and *in the same chain* select the faces you wish to remove.

        :param thickness: a positive float, representing the thickness of the desired shell.
            Negative values shell inwards, positive values shell outwards.
        :param kind: kind of joints, intersetion or arc (default: arc).
        :raises: ValueError if the current stack contains objects that are not faces of a solid
             further up in the chain.
        :returns: a CQ object with the resulting shelled solid selected.

        This example will create a hollowed out unit cube, where the top most face is open,
        and all other walls are 0.2 units thick::

            Workplane().box(1,1,1).faces("+Z").shell(0.2)

        Shelling is one of the cases where you may need to use the add method to select several
        faces. For example, this example creates a 3-walled corner, by removing three faces
        of a cube::

            s = Workplane().box(1,1,1)
            s1 = s.faces("+Z")
            s1.add(s.faces("+Y")).add(s.faces("+X"))
            self.saveModel(s1.shell(0.2))

        This fairly yucky syntax for selecting multiple faces is planned for improvement

        **Note**:  When sharp edges are shelled inwards, they remain sharp corners, but **outward**
        shells are automatically filleted, because an outward offset from a corner generates
        a radius.


        Future Enhancements:
            Better selectors to make it easier to select multiple faces
        """
        solidRef = self.findSolid()

        faces = [f for f in self.objects if isinstance(f, Face)]

        s = solidRef.shell(faces, thickness, kind=kind)
        return self.newObject([s])

    def fillet(self, radius: float) -> "Workplane":
        """
        Fillets a solid on the selected edges.

        The edges on the stack are filleted. The solid to which the edges belong must be in the
        parent chain of the selected edges.

        :param radius: the radius of the fillet, must be > zero
        :type radius: positive float
        :raises: ValueError if at least one edge is not selected
        :raises: ValueError if the solid containing the edge is not in the chain
        :returns: cq object with the resulting solid selected.

        This example will create a unit cube, with the top edges filleted::

            s = Workplane().box(1,1,1).faces("+Z").edges().fillet(0.1)
        """
        # TODO: we will need much better edge selectors for this to work
        # TODO: ensure that edges selected actually belong to the solid in the chain, otherwise,
        # TODO: we segfault

        solid = self.findSolid()

        edgeList = cast(List[Edge], self.edges().vals())
        if len(edgeList) < 1:
            raise ValueError("Fillets requires that edges be selected")

        s = solid.fillet(radius, edgeList)
        return self.newObject([s.clean()])

    def chamfer(self, length: float, length2: Optional[float] = None) -> "Workplane":
        """
        Chamfers a solid on the selected edges.

        The edges on the stack are chamfered. The solid to which the
        edges belong must be in the parent chain of the selected
        edges.

        Optional parameter `length2` can be supplied with a different
        value than `length` for a chamfer that is shorter on one side
        longer on the other side.

        :param length: the length of the fillet, must be greater than zero
        :param length2: optional parameter for asymmetrical chamfer
        :type length: positive float
        :type length2: positive float
        :raises: ValueError if at least one edge is not selected
        :raises: ValueError if the solid containing the edge is not in the chain
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
        self, rotate: VectorLike = (0, 0, 0), offset: VectorLike = (0, 0, 0)
    ) -> "Workplane":
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

    def newObject(self, objlist: Iterable[CQObject]) -> "Workplane":
        """
        Create a new workplane object from this one.

        Overrides CQ.newObject, and should be used by extensions, plugins, and
        subclasses to create new objects.

        :param objlist: new objects to put on the stack
        :type objlist: a list of CAD primitives
        :return: a new Workplane object with the current workplane as a parent.
        """

        # copy the current state to the new object
        ns = Workplane()
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
        self,
        xSpacing: float,
        ySpacing: float,
        xCount: int,
        yCount: int,
        center: bool = True,
    ) -> "Workplane":
        """
        Creates an array of points and pushes them onto the stack.
        If you want to position the array at another point, create another workplane
        that is shifted to the position you would like to use as a reference

        :param xSpacing: spacing between points in the x direction ( must be > 0)
        :param ySpacing: spacing between points in the y direction ( must be > 0)
        :param xCount: number of points ( > 0 )
        :param yCount: number of points ( > 0 )
        :param center: if true, the array will be centered at the center of the workplane. if
            false, the lower left corner will be at the center of the work plane
        """

        if xSpacing <= 0 or ySpacing <= 0 or xCount < 1 or yCount < 1:
            raise ValueError("Spacing and count must be > 0 ")

        lpoints = []  # coordinates relative to bottom left point
        for x in range(xCount):
            for y in range(yCount):
                lpoints.append((xSpacing * x, ySpacing * y))

        # shift points down and left relative to origin if requested
        if center:
            xc = xSpacing * (xCount - 1) * 0.5
            yc = ySpacing * (yCount - 1) * 0.5
            cpoints = []
            for p in lpoints:
                cpoints.append((p[0] - xc, p[1] - yc))
            lpoints = list(cpoints)

        return self.pushPoints(lpoints)

    def polarArray(
        self,
        radius: float,
        startAngle: float,
        angle: float,
        count: int,
        fill: bool = True,
        rotate: bool = True,
    ) -> "Workplane":
        """
        Creates an polar array of points and pushes them onto the stack.
        The 0 degree reference angle is located along the local X-axis.

        :param radius: Radius of the array.
        :param startAngle: Starting angle (degrees) of array. 0 degrees is
            situated along local X-axis.
        :param angle: The angle (degrees) to fill with elements. A positive
            value will fill in the counter-clockwise direction. If fill is
            false, angle is the angle between elements.
        :param count: Number of elements in array. ( > 0 )
        :param fill: Interpret the angle as total if True (default: True).
        :param rotate: Rorate every item (default: True).
        """

        if count <= 0:
            raise ValueError("No elements in array")

        # First element at start angle, convert to cartesian coords
        x = radius * math.sin(math.radians(startAngle))
        y = radius * math.cos(math.radians(startAngle))

        if rotate:
            loc = Location(Vector(x, y), Vector(0, 0, 1), -startAngle)
        else:
            loc = Location(Vector(x, y))

        locs = [loc]

        # Calculate angle between elements
        if fill:
            if angle % 360 == 0:
                angle = angle / count
            elif count > 1:
                # Inclusive start and end
                angle = angle / (count - 1)

        # Add additional elements
        for i in range(1, count):
            phi_deg = startAngle + (angle * i)
            phi = math.radians(phi_deg)
            x = radius * math.sin(phi)
            y = radius * math.cos(phi)

            if rotate:
                loc = Location(Vector(x, y), Vector(0, 0, 1), -phi_deg)
            else:
                loc = Location(Vector(x, y))

            locs.append(loc)

        return self.pushPoints(locs)

    def pushPoints(self, pntList: Iterable[Union[VectorLike, Location]]) -> "Workplane":
        """
        Pushes a list of points onto the stack as vertices.
        The points are in the 2-d coordinate space of the workplane face

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

    def center(self, x: float, y: float) -> "Workplane":
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

    def lineTo(self, x: float, y: float, forConstruction: bool = False) -> "Workplane":
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
    def line(
        self, xDist: float, yDist: float, forConstruction: bool = False
    ) -> "Workplane":
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

    def vLine(self, distance: float, forConstruction: bool = False) -> "Workplane":
        """
        Make a vertical line from the current point the provided distance

        :param float distance: (y) distance from current point
        :return: the workplane object with the current point at the end of the new line
        """
        return self.line(0, distance, forConstruction)

    def hLine(self, distance: float, forConstruction: bool = False) -> "Workplane":
        """
        Make a horizontal line from the current point the provided distance

        :param float distance: (x) distance from current point
        :return: the Workplane object with the current point at the end of the new line
        """
        return self.line(distance, 0, forConstruction)

    def vLineTo(self, yCoord: float, forConstruction: bool = False) -> "Workplane":
        """
        Make a vertical line from the current point to the provided y coordinate.

        Useful if it is more convenient to specify the end location rather than distance,
        as in :py:meth:`vLine`

        :param float yCoord: y coordinate for the end of the line
        :return: the Workplane object with the current point at the end of the new line
        """
        p = self._findFromPoint(True)
        return self.lineTo(p.x, yCoord, forConstruction)

    def hLineTo(self, xCoord: float, forConstruction: bool = False) -> "Workplane":
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
        self, distance: float, angle: float, forConstruction: bool = False
    ) -> "Workplane":
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
        self, distance: float, angle: float, forConstruction: bool = False
    ) -> "Workplane":
        """
        Make a line from the current point to the given polar co-ordinates

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
    def moveTo(self, x: float = 0, y: float = 0) -> "Workplane":
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
    def move(self, xDist: float = 0, yDist: float = 0) -> "Workplane":
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

    def slot2D(self, length: float, diameter: float, angle: float = 0) -> "Workplane":
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

    def spline(
        self,
        listOfXYTuple: Iterable[VectorLike],
        tangents: Optional[Sequence[VectorLike]] = None,
        periodic: bool = False,
        forConstruction: bool = False,
        includeCurrent: bool = False,
        makeWire: bool = False,
    ) -> "Workplane":
        """
        Create a spline interpolated through the provided points.

        :param listOfXYTuple: points to interpolate through
        :type listOfXYTuple: list of 2-tuple
        :param tangents: tuple of Vectors specifying start and finish tangent
        :param periodic: creation of periodic curves
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

        Future Enhancements:
          * provide access to control points
        """

        vecs = [self.plane.toWorldCoords(p) for p in listOfXYTuple]

        if includeCurrent:
            gstartPoint = self._findFromPoint(False)
            allPoints = [gstartPoint] + vecs
        else:
            allPoints = vecs

        if tangents:
            t1, t2 = Vector(tangents[0]), Vector(tangents[1])
            tangents_g: Optional[Tuple[Vector, Vector]] = (
                self.plane.toWorldCoords(t1) - self.plane.origin,
                self.plane.toWorldCoords(t2) - self.plane.origin,
            )
        else:
            tangents_g = None

        e = Edge.makeSpline(allPoints, tangents=tangents_g, periodic=periodic)

        if makeWire:
            rv_w = Wire.assembleEdges([e])
            if not forConstruction:
                self._addPendingWire(rv_w)
        else:
            if not forConstruction:
                self._addPendingEdge(e)

        return self.newObject([rv_w if makeWire else e])

    def parametricCurve(
        self,
        func: Callable[[float], VectorLike],
        N: int = 400,
        start: float = 0,
        stop: float = 1,
        makeWire: bool = True,
    ) -> "Workplane":
        """
        Create a spline interpolated through the provided points.

        :param func: function f(t) that will generate (x,y) pairs
        :type func: float --> (float,float)
        :param N: number of points for discretization
        :param start: starting value of the parameter t
        :param stop: final value of the parameter t
        :param makeWire: convert the resulting spline edge to a wire
        :return: a Workplane object with the current point unchanged

        """

        diff = stop - start
        allPoints = [func(start + diff * t / N) for t in range(N + 1)]

        return self.spline(allPoints, includeCurrent=False, makeWire=makeWire)

    def ellipseArc(
        self,
        x_radius: float,
        y_radius: float,
        angle1: float = 360,
        angle2: float = 360,
        rotation_angle: float = 0.0,
        sense: Literal[-1, 1] = 1,
        forConstruction: bool = False,
        startAtCurrent: bool = True,
        makeWire: bool = False,
    ) -> "Workplane":
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
        self, point1: VectorLike, point2: VectorLike, forConstruction: bool = False
    ) -> "Workplane":
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
        self, endPoint: VectorLike, sag: float, forConstruction: bool = False
    ) -> "Workplane":
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
        self, endPoint: VectorLike, radius: float, forConstruction: bool = False
    ) -> "Workplane":
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
        self, endpoint: VectorLike, forConstruction: bool = False, relative: bool = True
    ) -> "Workplane":
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

    def mirrorY(self) -> "Workplane":
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

    def mirrorX(self) -> "Workplane":
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

        wires = cast(
            List[Union[Edge, Wire]],
            [el for el in chain(self.ctx.pendingEdges, self.ctx.pendingWires)],
        )
        if not wires:
            return []

        return Wire.combine(wires)

    def consolidateWires(self) -> "Workplane":
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

    def wire(self, forConstruction: bool = False) -> "Workplane":
        """
        Returns a CQ object with all pending edges connected into a wire.

        All edges on the stack that can be combined will be combined into a single wire object,
        and other objects will remain on the stack unmodified

        :param forConstruction: whether the wire should be used to make a solid, or if it is just
            for reference
        :type forConstruction: boolean. true if the object is only for reference

        This method is primarily of use to plugin developers making utilities for 2-d construction.
        This method should be called when a user operation implies that 2-d construction is
        finished, and we are ready to begin working in 3d

        SEE '2-d construction concepts' for a more detailed explanation of how CadQuery handles
        edges, wires, etc

        Any non edges will still remain.
        """

        edges = self.ctx.pendingEdges

        # do not consolidate if there are no free edges
        if len(edges) == 0:
            return self

        self.ctx.pendingEdges = []

        others = []
        for e in self.objects:
            if type(e) != Edge:
                others.append(e)

        w = Wire.assembleEdges(edges)
        if not forConstruction:
            self._addPendingWire(w)

        return self.newObject(others + [w])

    def each(
        self, callback: Callable[[CQObject], Shape], useLocalCoordinates: bool = False
    ) -> "Workplane":
        """
        Runs the provided function on each value in the stack, and collects the return values into
        a new CQ object.

        Special note: a newly created workplane always has its center point as its only stack item

        :param callBackFunction: the function to call for each item on the current stack.
        :param useLocalCoordinates: should  values be converted from local coordinates first?
        :type useLocalCoordinates: boolean

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

        return self.newObject(results)

    def eachpoint(
        self, callback: Callable[[Location], Shape], useLocalCoordinates: bool = False
    ) -> "Workplane":
        """
        Same as each(), except each item on the stack is converted into a point before it
        is passed into the callback function.

        :return: CadQuery object which contains a list of  vectors (points ) on its stack.

        :param useLocalCoordinates: should points be in local or global coordinates
        :type useLocalCoordinates: boolean

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
                else:
                    pnts.append(o)

        if useLocalCoordinates:
            res = [callback(p).move(loc) for p in pnts]
        else:
            res = [callback(p * loc) for p in pnts]

        for r in res:
            if isinstance(r, Wire) and not r.forConstruction:
                self._addPendingWire(r)

        return self.newObject(res)

    def rect(
        self,
        xLen: float,
        yLen: float,
        centered: bool = True,
        forConstruction: bool = False,
    ) -> "Workplane":
        """
        Make a rectangle for each item on the stack.

        :param xLen: length in xDirection ( in workplane coordinates )
        :type xLen: float > 0
        :param yLen: length in yDirection ( in workplane coordinates )
        :type yLen: float > 0
        :param boolean centered: true if the rect is centered on the reference point, false if the
            lower-left is on the reference point
        :param forConstruction: should the new wires be reference geometry only?
        :type forConstruction: true if the wires are for reference, false if they are creating part
            geometry
        :return: a new CQ object with the created wires on the stack

        A common use case is to use a for-construction rectangle to define the centers of a hole
        pattern::

            s = Workplane().rect(4.0,4.0,forConstruction=True).vertices().circle(0.25)

        Creates 4 circles at the corners of a square centered on the origin.

        Future Enhancements:
            better way to handle forConstruction
            project points not in the workplane plane onto the workplane plane
        """

        if centered:
            p1 = Vector(xLen / -2.0, yLen / -2.0, 0)
            p2 = Vector(xLen / 2.0, yLen / -2.0, 0)
            p3 = Vector(xLen / 2.0, yLen / 2.0, 0)
            p4 = Vector(xLen / -2.0, yLen / 2.0, 0)
        else:
            p1 = Vector()
            p2 = Vector(xLen, 0, 0)
            p3 = Vector(xLen, yLen, 0)
            p4 = Vector(0, yLen, 0)

        w = Wire.makePolygon([p1, p2, p3, p4, p1], forConstruction)

        return self.eachpoint(lambda loc: w.moved(loc), True)

    # circle from current point
    def circle(self, radius: float, forConstruction: bool = False) -> "Workplane":
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
        self,
        x_radius: float,
        y_radius: float,
        rotation_angle: float = 0.0,
        forConstruction: bool = False,
    ) -> "Workplane":
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
        self, nSides: int, diameter: float, forConstruction: bool = False
    ) -> "Workplane":
        """
        Creates a polygon inscribed in a circle of the specified diameter for each point on
        the stack

        The first vertex is always oriented in the x direction.

        :param nSides: number of sides, must be > 3
        :param diameter: the size of the circle the polygon is inscribed into
        :return: a polygon wire
        """

        # pnt is a vector in local coordinates
        angle = 2.0 * math.pi / nSides
        pnts = []
        for i in range(nSides + 1):
            pnts.append(
                Vector(
                    (diameter / 2.0 * math.cos(angle * i)),
                    (diameter / 2.0 * math.sin(angle * i)),
                    0,
                )
            )
        p = Wire.makePolygon(pnts, forConstruction)

        return self.eachpoint(lambda loc: p.moved(loc), True)

    def polyline(
        self,
        listOfXYTuple: Sequence[VectorLike],
        forConstruction: bool = False,
        includeCurrent: bool = False,
    ) -> "Workplane":
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

    def close(self) -> "Workplane":
        """
        End 2-d construction, and attempt to build a closed wire.

        :return: a CQ object with a completed wire on the stack, if possible.

        After 2-d drafting with methods such as lineTo, threePointArc,
        tangentArcPoint and polyline, it is necessary to convert the edges
        produced by these into one or more wires.

        When a set of edges is closed, cadQuery assumes it is safe to build
        the group of edges into a wire. This example builds a simple triangular
        prism::

            s = Workplane().lineTo(1,0).lineTo(1,1).close().extrude(0.2)
        """
        endPoint = self._findFromPoint(True)

        if self.ctx.firstPoint is None:
            raise ValueError("Not start point specified - cannot close")
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
        :return: A value representing the largest dimension of the first solid on the stack
        """
        # Get all the solids contained within this CQ object
        compound = self.findSolid()

        # Protect against this being called on something like a blank workplane
        if not compound:
            return -1

        return compound.BoundingBox().DiagonalLength

    def cutEach(
        self,
        fcn: Callable[[Location], Shape],
        useLocalCoords: bool = False,
        clean: bool = True,
    ) -> "Workplane":
        """
        Evaluates the provided function at each point on the stack (ie, eachpoint)
        and then cuts the result from the context solid.
        :param fcn: a function suitable for use in the eachpoint method: ie, that accepts a vector
        :param useLocalCoords: same as for :py:meth:`eachpoint`
        :param boolean clean: call :py:meth:`clean` afterwards to have a clean shape
        :return: a CQ object that contains the resulting solid
        :raises: an error if there is not a context solid to cut from
        """
        ctxSolid = self.findSolid()
        if ctxSolid is None:
            raise ValueError("Must have a solid in the chain to cut from!")

        # will contain all of the counterbores as a single compound
        results = cast(List[Shape], self.eachpoint(fcn, useLocalCoords).vals())

        s = ctxSolid.cut(*results)

        if clean:
            s = s.clean()

        return self.newObject([s])

    # but parameter list is different so a simple function pointer wont work
    def cboreHole(
        self,
        diameter: float,
        cboreDiameter: float,
        cboreDepth: float,
        depth: Optional[float] = None,
        clean: bool = True,
    ) -> "Workplane":
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
        )  # local coordianates!

        # add the counter bore
        cbore = Solid.makeCylinder(cboreDiameter / 2.0, cboreDepth, Vector(), boreDir)
        r = hole.fuse(cbore)

        return self.cutEach(lambda loc: r.moved(loc), True, clean)

    # TODO: almost all code duplicated!
    # but parameter list is different so a simple function pointer wont work
    def cskHole(
        self,
        diameter: float,
        cskDiameter: float,
        cskAngle: float,
        depth: Optional[float] = None,
        clean: bool = True,
    ) -> "Workplane":
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
    # but parameter list is different so a simple function pointer wont work
    def hole(
        self, diameter: float, depth: Optional[float] = None, clean: bool = True
    ) -> "Workplane":
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
        self,
        distance: float,
        angleDegrees: float,
        combine: bool = True,
        clean: bool = True,
    ) -> "Workplane":
        """
        Extrudes a wire in the direction normal to the plane, but also twists by the specified
        angle over the length of the extrusion

        The center point of the rotation will be the center of the workplane

        See extrude for more details, since this method is the same except for the the addition
        of the angle. In fact, if angle=0, the result is the same as a linear extrude.

        **NOTE**  This method can create complex calculations, so be careful using it with
        complex geometries

        :param distance: the distance to extrude normal to the workplane
        :param angle: angline ( in degrees) to rotate through the extrusion
        :param boolean combine: True to combine the resulting solid with parent solids if found.
        :param boolean clean: call :py:meth:`clean` afterwards to have a clean shape
        :return: a CQ object with the resulting solid selected.
        """
        # group wires together into faces based on which ones are inside the others
        # result is a list of lists
        wireSets = sortWiresByBuildOrder(list(self.ctx.pendingWires))

        # now all of the wires have been used to create an extrusion
        self.ctx.pendingWires = []

        # compute extrusion vector and extrude
        eDir = self.plane.zDir.multiply(distance)

        # one would think that fusing faces into a compound and then extruding would work,
        # but it doesnt-- the resulting compound appears to look right, ( right number of faces, etc)
        # but then cutting it from the main solid fails with BRep_NotDone.
        # the work around is to extrude each and then join the resulting solids, which seems to work

        # underlying cad kernel can only handle simple bosses-- we'll aggregate them if there
        # are multiple sets
        shapes: List[Shape] = []
        for ws in wireSets:
            thisObj = Solid.extrudeLinearWithRotation(
                ws[0], ws[1:], self.plane.origin, eDir, angleDegrees
            )
            shapes.append(thisObj)

        r = Compound.makeCompound(shapes).fuse()

        if combine:
            newS = self._combineWithBase(r)
        else:
            newS = self.newObject([r])
        if clean:
            newS = newS.clean()
        return newS

    def extrude(
        self,
        distance: float,
        combine: bool = True,
        clean: bool = True,
        both: bool = False,
        taper: Optional[float] = None,
    ) -> "Workplane":
        """
        Use all un-extruded wires in the parent chain to create a prismatic solid.

        :param distance: the distance to extrude, normal to the workplane plane
        :type distance: float, negative means opposite the normal direction
        :param boolean combine: True to combine the resulting solid with parent solids if found.
        :param boolean clean: call :py:meth:`clean` afterwards to have a clean shape
        :param boolean both: extrude in both directions symmetrically
        :param float taper: angle for optional tapered extrusion
        :return: a CQ object with the resulting solid selected.

        extrude always *adds* material to a part.

        The returned object is always a CQ object, and depends on wither combine is True, and
        whether a context solid is already defined:

        *  if combine is False, the new value is pushed onto the stack.
        *  if combine is true, the value is combined with the context solid if it exists,
           and the resulting solid becomes the new context solid.

        FutureEnhancement:
            Support for non-prismatic extrusion ( IE, sweeping along a profile, not just
            perpendicular to the plane extrude to surface. this is quite tricky since the surface
            selected may not be planar
        """
        r = self._extrude(
            distance, both=both, taper=taper
        )  # returns a Solid (or a compound if there were multiple)

        if combine:
            newS = self._combineWithBase(r)
        else:
            newS = self.newObject([r])
        if clean:
            newS = newS.clean()
        return newS

    def revolve(
        self,
        angleDegrees: float = 360.0,
        axisStart: Optional[VectorLike] = None,
        axisEnd: Optional[VectorLike] = None,
        combine: bool = True,
        clean: bool = True,
    ) -> "Workplane":
        """
        Use all un-revolved wires in the parent chain to create a solid.

        :param angleDegrees: the angle to revolve through.
        :type angleDegrees: float, anything less than 360 degrees will leave the shape open
        :param axisStart: the start point of the axis of rotation
        :type axisStart: tuple, a two tuple
        :param axisEnd: the end point of the axis of rotation
        :type axisEnd: tuple, a two tuple
        :param combine: True to combine the resulting solid with parent solids if found.
        :type combine: boolean, combine with parent solid
        :param boolean clean: call :py:meth:`clean` afterwards to have a clean shape
        :return: a CQ object with the resulting solid selected.

        The returned object is always a CQ object, and depends on wither combine is True, and
        whether a context solid is already defined:

        *  if combine is False, the new value is pushed onto the stack.
        *  if combine is true, the value is combined with the context solid if it exists,
           and the resulting solid becomes the new context solid.
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
        if combine:
            newS = self._combineWithBase(r)
        else:
            newS = self.newObject([r])
        if clean:
            newS = newS.clean()
        return newS

    def sweep(
        self,
        path: "Workplane",
        multisection: bool = False,
        sweepAlongWires: Optional[bool] = None,
        makeSolid: bool = True,
        isFrenet: bool = False,
        combine: bool = True,
        clean: bool = True,
        transition: Literal["right", "round", "transformed"] = "right",
        normal: Optional[VectorLike] = None,
        auxSpine: Optional["Workplane"] = None,
    ) -> "Workplane":
        """
        Use all un-extruded wires in the parent chain to create a swept solid.

        :param path: A wire along which the pending wires will be swept
        :param boolean multiSection: False to create multiple swept from wires on the chain along path. True to create only one solid swept along path with shape following the list of wires on the chain
        :param boolean combine: True to combine the resulting solid with parent solids if found.
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
                "sweepAlongWires keyword argument is is depracated and will "
                "be removed in the next version; use multisection instead",
                DeprecationWarning,
            )

        r = self._sweep(
            path.wire(), multisection, makeSolid, isFrenet, transition, normal, auxSpine
        )  # returns a Solid (or a compound if there were multiple)
        newS: "CQ"
        if combine:
            newS = self._combineWithBase(r)
        else:
            newS = self.newObject([r])
        if clean:
            newS = newS.clean()
        return newS

    def _combineWithBase(self, obj: Shape) -> "Workplane":
        """
        Combines the provided object with the base solid, if one can be found.
        :param obj:
        :return: a new object that represents the result of combining the base object with obj,
           or obj if one could not be found
        """
        baseSolid = self.findSolid(searchParents=True)
        r = obj
        if baseSolid is not None:
            r = baseSolid.fuse(obj)
        elif isinstance(obj, Compound):
            r = obj.fuse()

        return self.newObject([r])

    def _cutFromBase(self, obj: Shape) -> "Workplane":
        """
        Cuts the provided object from the base solid, if one can be found.
        :param obj:
        :return: a new object that represents the result of combining the base object with obj,
           or obj if one could not be found
        """
        baseSolid = self.findSolid(searchParents=True)
        r = obj
        if baseSolid is not None:
            r = baseSolid.cut(obj)

        return self.newObject([r])

    def combine(
        self, clean: bool = True, glue: bool = False, tol: Optional[float] = None
    ) -> "Workplane":
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
        self,
        toUnion: Optional[Union["Workplane", Solid, Compound]] = None,
        clean: bool = True,
        glue: bool = False,
        tol: Optional[float] = None,
    ) -> "Workplane":
        """
        Unions all of the items on the stack of toUnion with the current solid.
        If there is no current solid, the items in toUnion are unioned together.
        
        :param toUnion:
        :type toUnion: a solid object, or a CQ object having a solid,
        :param boolean clean: call :py:meth:`clean` afterwards to have a clean shape (default True)
        :param boolean glue: use a faster gluing mode for non-overlapping shapes (default False)
        :param float tol: tolerance value for fuzzy bool operation mode (default None)
        :raises: ValueError if there is no solid to add to in the chain
        :return: a CQ object with the resulting object selected
        """

        # first collect all of the items together
        newS: Sequence[Shape]
        if isinstance(toUnion, CQ):
            newS = cast(List[Shape], toUnion.solids().vals())
            if len(newS) < 1:
                raise ValueError(
                    "CQ object  must have at least one solid on the stack to union!"
                )
        elif isinstance(toUnion, (Solid, Compound)):
            newS = (toUnion,)
        else:
            raise ValueError("Cannot union type '{}'".format(type(toUnion)))

        # now combine with existing solid, if there is one
        # look for parents to cut from
        solidRef = self.findSolid(searchStack=True, searchParents=True)
        if solidRef is not None:
            r = solidRef.fuse(*newS, glue=glue, tol=tol)
        elif len(newS) > 1:
            r = newS.pop(0).fuse(*newS, glue=glue, tol=tol)
        else:
            r = newS[0]

        if clean:
            r = r.clean()

        return self.newObject([r])

    def cut(
        self, toCut: Union["Workplane", Solid, Compound], clean: bool = True
    ) -> "Workplane":
        """
        Cuts the provided solid from the current solid, IE, perform a solid subtraction
        
        :param toCut: object to cut
        :type toCut: a solid object, or a CQ object having a solid,
        :param boolean clean: call :py:meth:`clean` afterwards to have a clean shape
        :raises: ValueError if there is no solid to subtract from in the chain
        :return: a CQ object with the resulting object selected
        """

        # look for parents to cut from
        solidRef = self.findSolid(searchStack=True, searchParents=True)

        if solidRef is None:
            raise ValueError("Cannot find solid to cut from")

        solidToCut: Sequence[Shape]

        if isinstance(toCut, CQ):
            solidToCut = _selectShapes(toCut.vals())
        elif isinstance(toCut, (Solid, Compound)):
            solidToCut = (toCut,)
        else:
            raise ValueError("Cannot cut type '{}'".format(type(toCut)))

        newS = solidRef.cut(*solidToCut)

        if clean:
            newS = newS.clean()

        return self.newObject([newS])

    def intersect(
        self, toIntersect: Union["Workplane", Solid, Compound], clean: bool = True
    ) -> "Workplane":
        """
        Intersects the provided solid from the current solid.
        
        :param toIntersect: object to intersect
        :type toIntersect: a solid object, or a CQ object having a solid,
        :param boolean clean: call :py:meth:`clean` afterwards to have a clean shape
        :raises: ValueError if there is no solid to intersect with in the chain
        :return: a CQ object with the resulting object selected
        """

        # look for parents to intersect with
        solidRef = self.findSolid(searchStack=True, searchParents=True)

        if solidRef is None:
            raise ValueError("Cannot find solid to intersect with")

        solidToIntersect: Sequence[Shape]

        if isinstance(toIntersect, CQ):
            solidToIntersect = _selectShapes(toIntersect.vals())
        elif isinstance(toIntersect, (Solid, Compound)):
            solidToIntersect = (toIntersect,)
        else:
            raise ValueError("Cannot intersect type '{}'".format(type(toIntersect)))

        newS = solidRef.intersect(*solidToIntersect)

        if clean:
            newS = newS.clean()

        return self.newObject([newS])

    def cutBlind(
        self, distanceToCut: float, clean: bool = True, taper: Optional[float] = None
    ) -> "Workplane":
        """
        Use all un-extruded wires in the parent chain to create a prismatic cut from existing solid.

        Similar to extrude, except that a solid in the parent chain is required to remove material
        from. cutBlind always removes material from a part.

        :param distanceToCut: distance to extrude before cutting
        :type distanceToCut: float, >0 means in the positive direction of the workplane normal,
            <0 means in the negative direction
        :param boolean clean: call :py:meth:`clean` afterwards to have a clean shape
        :param float taper: angle for optional tapered extrusion
        :raises: ValueError if there is no solid to subtract from in the chain
        :return: a CQ object with the resulting object selected

        see :py:meth:`cutThruAll` to cut material from the entire part

        Future Enhancements:
            Cut Up to Surface
        """
        # first, make the object
        toCut = self._extrude(distanceToCut, taper=taper)

        # now find a solid in the chain

        solidRef = self.findSolid()

        s = solidRef.cut(toCut)

        if clean:
            s = s.clean()

        return self.newObject([s])

    def cutThruAll(self, clean: bool = True, taper: float = 0) -> "Workplane":
        """
        Use all un-extruded wires in the parent chain to create a prismatic cut from existing solid.
        Cuts through all material in both normal directions of workplane.

        Similar to extrude, except that a solid in the parent chain is required to remove material
        from. cutThruAll always removes material from a part.

        :param boolean clean: call :py:meth:`clean` afterwards to have a clean shape
        :raises: ValueError if there is no solid to subtract from in the chain
        :return: a CQ object with the resulting object selected

        see :py:meth:`cutBlind` to cut material to a limited depth
        """
        wires = self.ctx.pendingWires
        self.ctx.pendingWires = []

        solidRef = self.findSolid()
        rv = []
        for solid in solidRef.Solids():
            s = solid.dprism(None, wires, thruAll=True, additive=False, taper=-taper)

            if clean:
                s = s.clean()

            rv.append(s)

        return self.newObject(rv)

    def loft(
        self, filled: bool = True, ruled: bool = False, combine: bool = True
    ) -> "Workplane":
        """
        Make a lofted solid, through the set of wires.
        :return: a CQ object containing the created loft
        """
        wiresToLoft = self.ctx.pendingWires
        self.ctx.pendingWires = []

        r: Shape = Solid.makeLoft(wiresToLoft, ruled)

        if combine:
            parentSolid = self.findSolid(searchStack=False, searchParents=True)
            if parentSolid is not None:
                r = parentSolid.fuse(r)

        return self.newObject([r])

    def _extrude(
        self, distance: float, both: bool = False, taper: Optional[float] = None
    ) -> Compound:
        """
        Make a prismatic solid from the existing set of pending wires.

        :param distance: distance to extrude
        :param boolean both: extrude in both directions symmetrically
        :return: OCCT solid(s), suitable for boolean operations.

        This method is a utility method, primarily for plugin and internal use.
        It is the basis for cutBlind,extrude,cutThruAll, and all similar methods.

        Future Enhancements:
            extrude along a profile (sweep)
        """

        # group wires together into faces based on which ones are inside the others
        # result is a list of lists

        wireSets = sortWiresByBuildOrder(list(self.ctx.pendingWires))
        # now all of the wires have been used to create an extrusion
        self.ctx.pendingWires = []

        # compute extrusion vector and extrude
        eDir = self.plane.zDir.multiply(distance)

        # one would think that fusing faces into a compound and then extruding would work,
        # but it doesnt-- the resulting compound appears to look right, ( right number of faces, etc)
        # but then cutting it from the main solid fails with BRep_NotDone.
        # the work around is to extrude each and then join the resulting solids, which seems to work

        # underlying cad kernel can only handle simple bosses-- we'll aggregate them if there are
        # multiple sets

        toFuse = []

        if taper:
            for ws in wireSets:
                thisObj = Solid.extrudeLinear(ws[0], [], eDir, taper)
                toFuse.append(thisObj)
        else:
            for ws in wireSets:
                thisObj = Solid.extrudeLinear(ws[0], ws[1:], eDir)
                toFuse.append(thisObj)

                if both:
                    thisObj = Solid.extrudeLinear(ws[0], ws[1:], eDir.multiply(-1.0))
                    toFuse.append(thisObj)

        return Compound.makeCompound(toFuse)

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
        # We have to gather the wires to be revolved
        wireSets = sortWiresByBuildOrder(list(self.ctx.pendingWires))

        # Mark that all of the wires have been used to create a revolution
        self.ctx.pendingWires = []

        # Revolve the wires, make a compound out of them and then fuse them
        toFuse = []
        for ws in wireSets:
            thisObj = Solid.revolve(
                ws[0], ws[1:], angleDegrees, Vector(axisStart), Vector(axisEnd)
            )
            toFuse.append(thisObj)

        return Compound.makeCompound(toFuse)

    def _sweep(
        self,
        path: "Workplane",
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

        p = path.val()
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
            wireSets = sortWiresByBuildOrder(list(self.ctx.pendingWires))
            for ws in wireSets:
                thisObj = Solid.sweep(
                    ws[0], ws[1:], p, makeSolid, isFrenet, mode, transition
                )
                toFuse.append(thisObj)
        else:
            sections = self.ctx.pendingWires
            thisObj = Solid.sweep_multi(sections, p, makeSolid, isFrenet, mode)
            toFuse.append(thisObj)

        self.ctx.pendingWires = []

        return Compound.makeCompound(toFuse)

    def interpPlate(
        self,
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
    ) -> "Workplane":
        """
        Returns a plate surface that is 'thickness' thick, enclosed by 'surf_edge_pts' points,  and going through 'surf_pts' points.  Using pushpoints directly with interpPlate and combine=True, can be very ressources intensive depending on the complexity of the shape. In this case set combine=False.

        :param surf_edges
        :type 1 surf_edges: list of [x,y,z] float ordered coordinates
        :type 2 surf_edges: list of ordered or unordered CadQuery wires
        :param surf_pts = [] (uses only edges if [])
        :type surf_pts: list of [x,y,z] float coordinates
        :param thickness = 0 (returns 2D surface if 0)
        :type thickness: float (may be negative or positive depending on thicknening direction)
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
        :param Anisotropie = False (OCCT default)
        :type Anisotropie: Boolean
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
        self,
        length: float,
        width: float,
        height: float,
        centered: Tuple[bool, bool, bool] = (True, True, True),
        combine: bool = True,
        clean: bool = True,
    ) -> "Workplane":
        """
        Return a 3d box with specified dimensions for each object on the stack.

        :param length: box size in X direction
        :type length: float > 0
        :param width: box size in Y direction
        :type width: float > 0
        :param height: box size in Z direction
        :type height: float > 0
        :param centered: should the box be centered, or should reference point be at the lower
            bound of the range?
        :param combine: should the results be combined with other solids on the stack
            (and each other)?
        :type combine: true to combine shapes, false otherwise.
        :param boolean clean: call :py:meth:`clean` afterwards to have a clean shape

        Centered is a tuple that describes whether the box should be centered on the x,y, and
        z axes.  If true, the box is centered on the respective axis relative to the workplane
        origin, if false, the workplane center will represent the lower bound of the resulting box

        one box is created for each item on the current stack. If no items are on the stack, one box
        using the current workplane center is created.

        If combine is true, the result will be a single object on the stack:
            if a solid was found in the chain, the result is that solid with all boxes produced
            fused onto it otherwise, the result is the combination of all the produced boxes

        if combine is false, the result will be a list of the boxes produced

        Most often boxes form the basis for a part::

            #make a single box with lower left corner at origin
            s = Workplane().box(1,2,3,centered=(False,False,False)

        But sometimes it is useful to create an array of them:

            #create 4 small square bumps on a larger base plate:
            s = Workplane().box(4,4,0.5).faces(">Z").workplane()\
                .rect(3,3,forConstruction=True).vertices().box(0.25,0.25,0.25,combine=True)

        """

        (xp, yp, zp) = (0.0, 0.0, 0.0)
        if centered[0]:
            xp -= length / 2.0
        if centered[1]:
            yp -= width / 2.0
        if centered[2]:
            zp -= height / 2.0

        box = Solid.makeBox(length, width, height, Vector(xp, yp, zp))

        boxes = self.eachpoint(lambda loc: box.moved(loc), True)

        # if combination is not desired, just return the created boxes
        if not combine:
            return boxes
        else:
            # combine everything
            return self.union(boxes, clean=clean)

    def sphere(
        self,
        radius: float,
        direct: VectorLike = (0, 0, 1),
        angle1: float = -90,
        angle2: float = 90,
        angle3: float = 360,
        centered: Tuple[bool, bool, bool] = (True, True, True),
        combine: bool = True,
        clean: bool = True,
    ) -> "Workplane":
        """
        Returns a 3D sphere with the specified radius for each point on the stack

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
        :param centered: A three-tuple of booleans that determines whether the sphere is centered
            on each axis origin
        :param combine: Whether the results should be combined with other solids on the stack
            (and each other)
        :type combine: true to combine shapes, false otherwise
        :return: A sphere object for each point on the stack

        Centered is a tuple that describes whether the sphere should be centered on the x,y, and
        z axes.  If true, the sphere is centered on the respective axis relative to the workplane
        origin, if false, the workplane center will represent the lower bound of the resulting
        sphere.

        One sphere is created for each item on the current stack. If no items are on the stack, one
        box using the current workplane center is created.

        If combine is true, the result will be a single object on the stack:
            If a solid was found in the chain, the result is that solid with all spheres produced
            fused onto it otherwise, the result is the combination of all the produced boxes

        If combine is false, the result will be a list of the spheres produced
        """

        # Convert the direction tuple to a vector, if needed
        if isinstance(direct, tuple):
            direct = Vector(direct)

        (xp, yp, zp) = (0.0, 0.0, 0.0)

        if not centered[0]:
            xp += radius

        if not centered[1]:
            yp += radius

        if not centered[2]:
            zp += radius

        s = Solid.makeSphere(radius, Vector(xp, yp, zp), direct, angle1, angle2, angle3)

        # We want a sphere for each point on the workplane
        spheres = self.eachpoint(lambda loc: s.moved(loc), True)

        # If we don't need to combine everything, just return the created spheres
        if not combine:
            return spheres
        else:
            return self.union(spheres, clean=clean)

    def wedge(
        self,
        dx: float,
        dy: float,
        dz: float,
        xmin: float,
        zmin: float,
        xmax: float,
        zmax: float,
        pnt: VectorLike = Vector(0, 0, 0),
        dir: VectorLike = Vector(0, 0, 1),
        centered: Tuple[bool, bool, bool] = (True, True, True),
        combine: bool = True,
        clean: bool = True,
    ) -> "Workplane":
        """
        :param dx: Distance along the X axis
        :param dy: Distance along the Y axis
        :param dz: Distance along the Z axis
        :param xmin: The minimum X location
        :param zmin:The minimum Z location
        :param xmax:The maximum X location
        :param zmax: The maximum Z location
        :param pnt: A vector (or tuple) for the origin of the direction for the wedge
        :param dir: The direction vector (or tuple) for the major axis of the wedge
        :param combine: Whether the results should be combined with other solids on the stack
            (and each other)
        :param clean: true to attempt to have the kernel clean up the geometry, false otherwise
        :return: A wedge object for each point on the stack

        One wedge is created for each item on the current stack. If no items are on the stack, one
        wedge using the current workplane center is created.

        If combine is true, the result will be a single object on the stack:
            If a solid was found in the chain, the result is that solid with all wedges produced
            fused onto it otherwise, the result is the combination of all the produced wedges

        If combine is false, the result will be a list of the wedges produced
        """

        # Convert the point tuple to a vector, if needed
        if isinstance(pnt, tuple):
            pnt = Vector(pnt)

        # Convert the direction tuple to a vector, if needed
        if isinstance(dir, tuple):
            dir = Vector(dir)

        (xp, yp, zp) = (0.0, 0.0, 0.0)

        if centered[0]:
            xp -= dx / 2.0

        if centered[1]:
            yp -= dy / 2.0

        if centered[2]:
            zp -= dz / 2.0

        w = Solid.makeWedge(dx, dy, dz, xmin, zmin, xmax, zmax, Vector(xp, yp, zp), dir)

        # We want a wedge for each point on the workplane
        wedges = self.eachpoint(lambda loc: w.moved(loc), True)

        # If we don't need to combine everything, just return the created wedges
        if not combine:
            return wedges
        else:
            return self.union(wedges, clean=clean)

    def clean(self) -> "Workplane":
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

    def text(
        self,
        txt: str,
        fontsize: float,
        distance: float,
        cut: bool = True,
        combine: bool = False,
        clean: bool = True,
        font: str = "Arial",
        fontPath: Optional[str] = None,
        kind: Literal["regular", "bold", "italic"] = "regular",
        halign: Literal["center", "left", "right"] = "center",
        valign: Literal["center", "top", "bottom"] = "center",
    ) -> "Workplane":
        """
        Create a 3D text

        :param str txt: text to be rendered
        :param distance: the distance to extrude, normal to the workplane plane
        :type distance: float, negative means opposite the normal direction
        :param float fontsize: size of the font
        :param boolean cut: True to cut the resulting solid from the parent solids if found.
        :param boolean combine: True to combine the resulting solid with parent solids if found.
        :param boolean clean: call :py:meth:`clean` afterwards to have a clean shape
        :param str font: fontname (default: Arial)
        :param str kind: font type (default: Normal)
        :param str halign: horizontal alignment (default: center)
        :param str valign: vertical alignment (default: center)
        :return: a CQ object with the resulting solid selected.

        extrude always *adds* material to a part.

        The returned object is always a CQ object, and depends on wither combine is True, and
        whether a context solid is already defined:

        *  if combine is False, the new value is pushed onto the stack.
        *  if combine is true, the value is combined with the context solid if it exists,
           and the resulting solid becomes the new context solid.

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
            newS = self._cutFromBase(r)
        elif combine:
            newS = self._combineWithBase(r)
        else:
            newS = self.newObject([r])
        if clean:
            newS = newS.clean()
        return newS

    def section(self, height: float = 0.0) -> "Workplane":
        """
        Slices current solid at the given height.
        
        :param float height: height to slice at (default: 0)
        :return: a CQ object with the resulting face(s).
        """

        solidRef = self.findSolid(searchStack=True, searchParents=True)

        if solidRef is None:
            raise ValueError("Cannot find solid to slice")

        plane = Face.makePlane(
            basePnt=self.plane.origin + self.plane.zDir * height, dir=self.plane.zDir
        )

        r = solidRef.intersect(plane)

        return self.newObject([r])

    def toPending(self) -> "Workplane":
        """
        Adds wires/edges to pendingWires/pendingEdges.
        
        :return: same CQ object with updated context.
        """

        self.ctx.pendingWires.extend(el for el in self.objects if isinstance(el, Wire))
        self.ctx.pendingEdges.extend(el for el in self.objects if isinstance(el, Edge))

        return self

    def offset2D(
        self, d: float, kind: Literal["arc", "intersection", "tangent"] = "arc"
    ) -> "Workplane":
        """
        Creates a 2D offset wire.
        
        :param float d: thickness. Negative thickness denotes offset to inside.
        :param kind: offset kind. Use "arc" for rounded and "intersection" for sharp edges (default: "arc")
        
        :return: CQ object with resulting wire(s).
        """

        ws = self._consolidateWires()
        rv = list(chain.from_iterable(w.offset2D(d, kind) for w in ws))

        self.ctx.pendingEdges = []
        self.ctx.pendingWires = rv

        return self.newObject(rv)

    def _repr_html_(self) -> Any:
        """
        Special method for rendering current object in a jupyter notebook
        """

        if type(self.val()) is Vector:
            return "&lt {} &gt".format(self.__repr__()[1:-1])
        else:
            return Compound.makeCompound(_selectShapes(self.objects))._repr_html_()


# alias for backward compatibility
CQ = Workplane
