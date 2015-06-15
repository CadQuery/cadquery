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

import re
import math
from cadquery import Vector,Edge,Vertex,Face,Solid,Shell,Compound


class Selector(object):
    """
        Filters a list of objects

        Filters must provide a single method that filters objects.
    """
    def filter(self,objectList):
        """
            Filter the provided list
            :param objectList: list to filter
            :type objectList: list of FreeCAD primatives
            :return: filtered list

            The default implementation returns the original list unfiltered

        """
        return objectList

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
    def __init__(self,pnt ):
        self.pnt = pnt
    def filter(self,objectList):

        def dist(tShape):
            return tShape.Center().sub(Vector(*self.pnt)).Length
            #if tShape.ShapeType == 'Vertex':
            #    return tShape.Point.sub(toVector(self.pnt)).Length
            #else:
            #    return tShape.CenterOfMass.sub(toVector(self.pnt)).Length

        return [ min(objectList,key=dist) ]

class BoxSelector(Selector):
    """
    Selects objects inside the 3D box defined by 2 points.

    Applicability: all types of shapes

    Example::

        CQ(aCube).edges(BoxSelector((0,1,0), (1,2,1))
    """
    def __init__(self, point0, point1):
        self.p0 = Vector(*point0)
        self.p1 = Vector(*point1)

    def filter(self, objectList):

        result = []
        x0, y0, z0 = self.p0.toTuple()
        x1, y1, z1 = self.p1.toTuple()

        for o in objectList:
            c = o.Center()
            # using XOR for checking if x/y/z is in between regardless
            # of order of x/y/z0 and x/y/z1
            if ((c.x < x0) ^ (c.x < x1)) and \
               ((c.y < y0) ^ (c.y < y1)) and \
               ((c.z < z0) ^ (c.z < z1)):
                result.append(o)

        return result

class BaseDirSelector(Selector):
    """
        A selector that handles selection on the basis of a single
        direction vector
    """
    def __init__(self,vector,tolerance=0.0001 ):
        self.direction = vector
        self.TOLERANCE = tolerance

    def test(self,vec):
        "Test a specified vector. Subclasses override to provide other implementations"
        return True

    def filter(self,objectList):
        """
            There are lots of kinds of filters, but
            for planes they are always based on the normal of the plane,
            and for edges on the tangent vector along the edge
        """
        r = []
        for o in objectList:
            #no really good way to avoid a switch here, edges and faces are simply different!

            if type(o) == Face:
                # a face is only parallell to a direction if it is a plane, and its normal is parallel to the dir
                normal = o.normalAt(None)

                if self.test(normal):
                    r.append(o)
            elif type(o) == Edge and o.geomType() == 'LINE':
                #an edge is parallel to a direction if it is a line, and the line is parallel to the dir
                tangent = o.tangentAt(None)
                if self.test(tangent):
                    r.append(o)

        return r

class ParallelDirSelector(BaseDirSelector):
    """
        Selects objects parallel with the provided direction

        Applicability:
            Linear Edges
            Planar Faces

        Use the string syntax shortcut \|(X|Y|Z) if you want to select
        based on a cardinal direction.

        Example::

            CQ(aCube).faces(ParallelDirSelector((0,0,1))

        selects faces with a normals in the z direction, and is equivalent to::

            CQ(aCube).faces("|Z")
    """

    def test(self,vec):
        return self.direction.cross(vec).Length < self.TOLERANCE

class DirectionSelector(BaseDirSelector):
    """
        Selects objects aligned with the provided direction

        Applicability:
            Linear Edges
            Planar Faces

        Use the string syntax shortcut +/-(X|Y|Z) if you want to select
        based on a cardinal direction.

        Example::

            CQ(aCube).faces(DirectionSelector((0,0,1))

        selects faces with a normals in the z direction, and is equivalent to::

            CQ(aCube).faces("+Z")
    """

    def test(self,vec):
        return abs(self.direction.getAngle(vec) < self.TOLERANCE)

class PerpendicularDirSelector(BaseDirSelector):
    """
        Selects objects perpendicular with the provided direction

        Applicability:
            Linear Edges
            Planar Faces

        Use the string syntax shortcut #(X|Y|Z) if you want to select
        based on a cardinal direction.

        Example::

            CQ(aCube).faces(PerpendicularDirSelector((0,0,1))

        selects faces with a normals perpendicular to the z direction, and is equivalent to::

            CQ(aCube).faces("#Z")
    """

    def test(self,vec):
        angle = self.direction.getAngle(vec)
        r = (abs(angle) < self.TOLERANCE) or (abs(angle - math.pi) < self.TOLERANCE )
        return not r


class TypeSelector(Selector):
    """
        Selects objects of the prescribed topological type.

        Applicability:
            Faces: Plane,Cylinder,Sphere
            Edges: Line,Circle,Arc

        You can use the shortcut selector %(PLANE|SPHERE|CONE) for faces,
        and %(LINE|ARC|CIRCLE) for edges.

        For example this::

            CQ(aCube).faces ( TypeSelector("PLANE") )

        will select 6 faces, and is equivalent to::

            CQ(aCube).faces( "%PLANE" )

    """
    def __init__(self,typeString):
        self.typeString = typeString.upper()

    def filter(self,objectList):
        r = []
        for o in objectList:
            if o.geomType() == self.typeString:
                r.append(o)
        return r

class DirectionMinMaxSelector(Selector):
    """
        Selects objects closest or farthest in the specified direction
        Used for faces, points, and edges

        Applicability:
            All object types. for a vertex, its point is used. for all other kinds
            of objects, the center of mass of the object is used.

        You can use the string shortcuts >(X|Y|Z) or <(X|Y|Z) if you want to
        select based on a cardinal direction.

        For example this::

            CQ(aCube).faces ( DirectionMinMaxSelector((0,0,1),True )

        Means to select the face having the center of mass farthest in the positive z direction,
        and is the same as:

            CQ(aCube).faces( ">Z" )

        Future Enhancements:
            provide a nicer way to select in arbitrary directions. IE, a bit more code could
            allow '>(0,0,1)' to work.

    """
    def __init__(self,vector,directionMax=True):
        self.vector = vector
        self.max = max
        self.directionMax = directionMax
    def filter(self,objectList):

        #then sort by distance from origin, along direction specified
        def distance(tShape):
            return tShape.Center().dot(self.vector)
            #if tShape.ShapeType == 'Vertex':
            #    pnt = tShape.Point
            #else:
            #    pnt = tShape.Center()
            #return pnt.dot(self.vector)

        if self.directionMax:
            return [ max(objectList,key=distance) ]
        else:
            return [ min(objectList,key=distance) ]


class StringSyntaxSelector(Selector):
    """
        Filter lists objects using a simple string syntax. All of the filters available in the string syntax
        are also available ( usually with more functionality ) through the creation of full-fledged
        selector objects. see :py:class:`Selector` and its subclasses

        Filtering works differently depending on the type of object list being filtered.

        :param selectorString: A two-part selector string, [selector][axis]

        :return: objects that match the specified selector

        ***Modfiers*** are ``('|','+','-','<','>','%')``

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

        ***axisStrings*** are: ``X,Y,Z,XY,YZ,XZ``

        Selectors are a complex topic: see :ref:`selector_reference` for more information



    """
    def __init__(self,selectorString):

        self.axes = {
            'X': Vector(1,0,0),
            'Y': Vector(0,1,0),
            'Z': Vector(0,0,1),
            'XY': Vector(1,1,0),
            'YZ': Vector(0,1,1),
            'XZ': Vector(1,0,1)
        }

        namedViews = {
            'front': ('>','Z' ),
            'back': ('<','Z'),
            'left':('<', 'X'),
            'right': ('>', 'X'),
            'top': ('>','Y'),
            'bottom': ('<','Y')
        }
        self.selectorString = selectorString
        r = re.compile("\s*([-\+<>\|\%#])*\s*(\w+)\s*",re.IGNORECASE)
        m = r.match(selectorString)

        if m != None:
            if namedViews.has_key(selectorString):
                (a,b) = namedViews[selectorString]
                self.mySelector = self._chooseSelector(a,b )
            else:
                self.mySelector = self._chooseSelector(m.groups()[0],m.groups()[1])
        else:
            raise ValueError ("Selector String format must be [-+<>|#%] X|Y|Z ")


    def _chooseSelector(self,selType,selAxis):
        """Sets up the underlying filters accordingly"""

        if selType == "%":
            return TypeSelector(selAxis)

        #all other types need to select axis as a vector
        #get the axis vector first, will throw an except if an unknown axis is used
        try:
            vec = self.axes[selAxis]
        except KeyError:
            raise ValueError ("Axis value %s not allowed: must be one of %s" % (selAxis, str(self.axes)))

        if selType in (None, "+"):
            #use direction filter
            return DirectionSelector(vec)
        elif selType == '-':
            #just use the reverse of the direction vector
            return DirectionSelector(vec.multiply(-1.0))
        elif selType == "|":
            return ParallelDirSelector(vec)
        elif selType == ">":
            return DirectionMinMaxSelector(vec,True)
        elif selType == "<":
            return DirectionMinMaxSelector(vec,False)
        elif selType == '#':
            return PerpendicularDirSelector(vec)
        else:
            raise ValueError ("Selector String format must be [-+<>|] X|Y|Z ")

    def filter(self,objectList):
        """
            selects minimum, maximum, positive or negative values relative to a direction
            [+\|-\|<\|>\|] \<X\|Y\|Z>
        """
        return self.mySelector.filter(objectList)
