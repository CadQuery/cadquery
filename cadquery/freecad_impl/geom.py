"""
    Copyright (C) 2011-2013  Parametric Products Intellectual Holdings, LLC

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

import math,sys
#import FreeCAD
from .verutil import fc_import
FreeCAD = fc_import("FreeCAD")
#Turns out we don't need the Part module here.

def sortWiresByBuildOrder(wireList,plane,result=[]):
    """
        Tries to determine how wires should be combined into faces.
        Assume:
            The wires make up one or more faces, which could have 'holes'
            Outer wires are listed ahead of inner wires
            there are no wires inside wires inside wires ( IE, islands -- we can deal with that later on )
            none of the wires are construction wires
        Compute:
            one or more sets of wires, with the outer wire listed first, and inner ones
        Returns, list of lists.
    """
    result = []

    remainingWires = list(wireList)
    while remainingWires:
        outerWire = remainingWires.pop(0)
        group = [outerWire]
        otherWires = list(remainingWires)
        for w in otherWires:
            if plane.isWireInside(outerWire,w):
                group.append(w)
                remainingWires.remove(w)
        result.append(group)

    return result

class Vector(object):
    """
        Create a 3-dimensional vector

        :param *args: a 3-d vector, with x-y-z parts.

        you can either provide:
            * a FreeCAD vector
            * a vector ( in which case it is copied )
            * a 3-tuple
            * three float values, x, y, and z

        FreeCAD's vector implementation has a dumb
        implementation for multiply and add-- they modify the existing
        value and return a copy as well.

        This vector is immutable-- all mutations return a copy!

    """
    def __init__(self,*args):

        if len(args) == 3:
            fV = FreeCAD.Base.Vector(args[0],args[1],args[2])
        elif len(args) == 1:
            if type(args[0]) is tuple:
                fV = FreeCAD.Base.Vector(args[0][0],args[0][1],args[0][2])
            elif type(args[0] is FreeCAD.Base.Vector):
                fV = args[0]
            elif type(args[0] is Vector):
                fV = args[0].wrapped
            else:
                fV = args[0]
        else:
            raise ValueError("Expected three floats, FreeCAD Vector, or 3-tuple")

        self.wrapped = fV
        self.Length = fV.Length
        self.x = fV.x
        self.y = fV.y
        self.z = fV.z

    def toTuple(self):
        return (self.x,self.y,self.z)

    #TODO: is it possible to create a dynamic proxy without all this code?
    def cross(self,v):
        return Vector( self.wrapped.cross(v.wrapped))

    def dot(self,v):
        return  self.wrapped.dot(v.wrapped)

    def sub(self,v):
        return self.wrapped.sub(v.wrapped)

    def add(self,v):
        return Vector( self.wrapped.add(v.wrapped))

    def multiply(self,scale):
        """
            Return self multiplied by the provided scalar

            Note: FreeCAD has a bug here, where the
            base is also modified
        """
        tmp = FreeCAD.Base.Vector(self.wrapped)
        return Vector( tmp.multiply(scale))

    def normalize(self):
        """
            Return normalized version this vector.

            Note: FreeCAD has a bug here, where the
            base is also modified
        """
        tmp = FreeCAD.Base.Vector(self.wrapped)
        tmp.normalize()
        return Vector( tmp )

    def Center(self):
        """
        The center of myself is myself.
        Provided so that vectors, vertexes, and other shapes all support a common interface,
        when Center() is requested for all objects on the stack
        """
        return self

    def getAngle(self,v):
        return self.wrapped.getAngle(v.wrapped)

    def distanceToLine(self):
        raise NotImplementedError("Have not needed this yet, but FreeCAD supports it!")

    def projectToLine(self):
        raise NotImplementedError("Have not needed this yet, but FreeCAD supports it!")

    def distanceToPlane(self):
        raise NotImplementedError("Have not needed this yet, but FreeCAD supports it!")

    def projectToPlane(self):
        raise NotImplementedError("Have not needed this yet, but FreeCAD supports it!")

    def __hash__(self):
        return self.wrapped.__hash__()

    def __add__(self,v):
        return self.add(v)

    def __len__(self):
        return self.Length

    def __repr__(self):
        return self.wrapped.__repr__()

    def __str__(self):
        return self.wrapped.__str__()

    def __len__(self,other):
        return self.wrapped.__len__(other)

    def __lt__(self,other):
        return self.wrapped.__lt__(other)

    def __gt__(self,other):
        return self.wrapped.__gt__(other)

    def __ne__(self,other):
        return self.wrapped.__ne__(other)

    def __le__(self,other):
        return self.wrapped.__le__(other)

    def __ge__(self,other):
        return self.wrapped.__ge__(other)

    def __eq__(self,other):
        return self.wrapped.__eq__(other)

class Matrix:
    """
        A 3d , 4x4 transformation matrix.

        Used to move geometry in space.
    """
    def __init__(self,matrix=None):
        if matrix == None:
            self.wrapped = FreeCAD.Base.Matrix()
        else:
            self.wrapped = matrix

    def rotateX(self,angle):
        self.wrapped.rotateX(angle)

    def rotateY(self,angle):
        self.wrapped.rotateY(angle)


class Plane:
    """
        A 2d coordinate system in space, with the x-y axes on the a plane, and a particular point as the origin.

        A plane allows the use of 2-d coordinates, which are later converted to global, 3d coordinates when
        the operations are complete.

        Frequently, it is not necessary to create work planes, as they can be created automatically from faces.

    """

    @classmethod
    def named(cls,stdName,origin=(0,0,0)):
        """
            Create a predefined Plane based on the conventional names.

            :param stdName: one of (XY|YZ|XZ|front|back|left|right|top|bottom
            :type stdName: string
            :param origin: the desired origin, specified in global coordinates
            :type origin: 3-tuple of the origin of the new plane, in global coorindates.

            Available named planes are as follows. Direction references refer to the global
            directions

            =========== ======= ======= ======
            Name        xDir    yDir    zDir
            =========== ======= ======= ======
            XY          +x      +y      +z
            YZ          +y      +z      +x
            XZ          +x      +z      -y
            front       +x      +y      +z
            back        -x      +y      -z
            left        +z      +y      -x
            right       -z      +y      +x
            top         +x      -z      +y
            bottom      +x      +z      -y
            =========== ======= ======= ======
        """

        namedPlanes = {
            #origin, xDir, normal
            'XY' : Plane(Vector(origin),Vector((1,0,0)),Vector((0,0,1))),
            'YZ' : Plane(Vector(origin),Vector((0,1,0)),Vector((1,0,0))),
            'XZ' : Plane(Vector(origin),Vector((1,0,0)),Vector((0,-1,0))),
            'front': Plane(Vector(origin),Vector((1,0,0)),Vector((0,0,1))),
            'back': Plane(Vector(origin),Vector((-1,0,0)),Vector((0,0,-1))),
            'left': Plane(Vector(origin),Vector((0,0,1)),Vector((-1,0,0))),
            'right': Plane(Vector(origin),Vector((0,0,-1)),Vector((1,0,0))),
            'top': Plane(Vector(origin),Vector((1,0,0)),Vector((0,1,0))),
            'bottom': Plane(Vector(origin),Vector((1,0,0)),Vector((0,-1,0)))
        }

        if namedPlanes.has_key(stdName):
            return namedPlanes[stdName]
        else:
            raise ValueError("Supported names are %s " % str(namedPlanes.keys()) )

    @classmethod
    def XY(cls,origin=(0,0,0),xDir=Vector(1,0,0)):
        return Plane.named('XY',origin)

    @classmethod
    def YZ(cls,origin=(0,0,0),xDir=Vector(1,0,0)):
        return Plane.named('YZ',origin)

    @classmethod
    def XZ(cls,origin=(0,0,0),xDir=Vector(1,0,0)):
        return Plane.named('XZ',origin)

    @classmethod
    def front(cls,origin=(0,0,0),xDir=Vector(1,0,0)):
        return Plane.named('front',origin)

    @classmethod
    def back(cls,origin=(0,0,0),xDir=Vector(1,0,0)):
        return Plane.named('back',origin)

    @classmethod
    def left(cls,origin=(0,0,0),xDir=Vector(1,0,0)):
        return Plane.named('left',origin)

    @classmethod
    def right(cls,origin=(0,0,0),xDir=Vector(1,0,0)):
        return Plane.named('right',origin)

    @classmethod
    def top(cls,origin=(0,0,0),xDir=Vector(1,0,0)):
        return Plane.named('top',origin)

    @classmethod
    def bottom(cls,origin=(0,0,0),xDir=Vector(1,0,0)):
        return Plane.named('bottom',origin)

    def __init__(self, origin, xDir, normal ):
        """
            Create a Plane with an arbitrary orientation

            TODO: project x and y vectors so they work even if not orthogonal
            :param origin: the origin
            :type origin: a three-tuple of the origin, in global coordinates
            :param xDir: a vector representing the xDirection.
            :type xDir: a three-tuple representing a vector, or a FreeCAD Vector
            :param normal: the normal direction for the new plane
            :type normal: a FreeCAD Vector
            :raises: ValueError if the specified xDir is not orthogonal to the provided normal.
            :return: a plane in the global space, with the xDirection of the plane in the specified direction.

        """
        self.xDir = xDir.normalize()
        self.yDir = normal.cross(self.xDir).normalize()
        self.zDir = normal.normalize()

        #stupid freeCAD!!!!! multiply has a bug that changes the original also!
        self.invZDir = self.zDir.multiply(-1.0)

        self.setOrigin3d(origin)


    def setOrigin3d(self,originVector):
        """
            Move the origin of the plane, leaving its orientation and xDirection unchanged.
            :param originVector: the new center of the plane, *global* coordinates
            :type originVector: a FreeCAD Vector.
            :return: void

        """
        self.origin = originVector
        self._calcTransforms()

    def setOrigin2d(self,x,y):
        """
            Set a new origin based of the plane. The plane's orientation and xDrection are unaffected.

            :param float x: offset in the x direction
            :param float y: offset in the y direction
            :return: void

            the new coordinates are  specified in terms of the current 2-d system. As an example::
                p = Plane.XY()
                p.setOrigin2d(2,2)
                p.setOrigin2d(2,2)

            results in a plane with its origin at (x,y)=(4,4) in global coordinates. The both operations were relative to
            local coordinates of the plane.

        """
        self.setOrigin3d(self.toWorldCoords((x,y)))


    def isWireInside(self,baseWire,testWire):
        """
            Determine if testWire is inside baseWire, after both wires are projected into the current plane

            :param baseWire: a reference wire
            :type baseWire: a FreeCAD wire
            :param testWire: another wire
            :type testWire: a FreeCAD wire
            :return: True if testWire is inside baseWire, otherwise False

            If either wire does not lie in the current plane, it is projected into the plane first.

            *WARNING*:  This method is not 100% reliable. It uses bounding box tests, but needs
            more work to check for cases when curves are complex.

            Future Enhancements:
                * Discretizing points along each curve to provide a more reliable test

        """
        #TODO: also use a set of points along the wire to test as well.
        #TODO: would it be more efficient to create objects in the local coordinate system, and then transform to global
        #coordinates upon extrusion?

        tBaseWire = baseWire.transformGeometry(self.fG)
        tTestWire = testWire.transformGeometry(self.fG)

        #these bounding boxes will have z=0, since we transformed them into the space of the plane
        bb = tBaseWire.BoundingBox()
        tb = tTestWire.BoundingBox()

        #findOutsideBox actually inspects both ways, here we only want to
        #know if one is inside the other
        x = BoundBox.findOutsideBox2D(bb,tb)
        return x == bb

    def toLocalCoords(self,obj):
        """
            Project the provided coordinates onto this plane.

            :param obj: an object or vector to convert
            :type vector: a vector or shape
            :return: an object of the same type as the input, but converted to local coordinates


            Most of the time, the z-coordinate returned will be zero, because most operations
            based on a plane are all 2-d. Occasionally, though, 3-d points outside of the current plane are transformed.
            One such example is :py:meth:`Workplane.box`, where 3-d corners of a box are transformed to orient the box in space
            correctly.

        """
        if isinstance(obj,Vector):
            return Vector(self.fG.multiply(obj.wrapped))
        elif isinstance(obj,Shape):
            return obj.transformShape(self.rG)
        else:
            raise ValueError("Dont know how to convert type %s to local coordinates" % str(type(obj)))


    def toWorldCoords(self, tuplePoint):
        """
            Convert a point in local coordinates to global coordinates.

            :param tuplePoint: point in local coordinates to convert
            :type tuplePoint: a 2 or three tuple of float. the third value is taken to be zero if not supplied
            :return: a 3-tuple in global coordinates


        """
        if len(tuplePoint) == 2:
            v = Vector(tuplePoint[0], tuplePoint[1], 0)
        else:
            v = Vector(tuplePoint[0],tuplePoint[1],tuplePoint[2])
        return Vector(self.rG.multiply(v.wrapped))


    def rotated(self,rotate=(0,0,0)):
        """
        returns a copy of this plane, rotated about the specified axes, as measured from horizontal

        Since the z axis is always normal the plane, rotating around Z will always produce a plane
        that is parallel to this one

        the origin of the workplane is unaffected by the rotation.

        rotations are done in order x,y,z. if you need a different order, manually chain together multiple .rotate()
        commands

        :param rotate: Vector [xDegrees,yDegrees,zDegrees]
        :return: a copy of this plane rotated as requested
        """

        if rotate.__class__.__name__ != 'Vector':
            rotate = Vector(rotate)
        #convert to radians
        rotate = rotate.multiply(math.pi / 180.0 )

        #compute rotation matrix
        m = FreeCAD.Base.Matrix()
        m.rotateX(rotate.x)
        m.rotateY(rotate.y)
        m.rotateZ(rotate.z)

        #compute the new plane
        newXdir = Vector(m.multiply(self.xDir.wrapped))
        newZdir = Vector(m.multiply(self.zDir.wrapped))

        newP= Plane(self.origin,newXdir,newZdir)
        return newP

    def rotateShapes(self,listOfShapes,rotationMatrix):
        """
            rotate the listOfShapes by the rotationMatrix supplied.
            @param listOfShapes is a list of shape objects
            @param rotationMatrix is a geom.Matrix object.
            returns a list of shape objects rotated according to the rotationMatrix
        """

        #compute rotation matrix ( global --> local --> rotate  --> global )
        #rm = self.plane.fG.multiply(matrix).multiply(self.plane.rG)
        rm = self.computeTransform(rotationMatrix)


        #There might be a better way, but to do this rotation takes 3 steps
        #transform geometry to local coordinates
        #then rotate about x
        #then transform back to global coordiante

        resultWires = []
        for w in listOfShapes:
            mirrored = w.transformGeometry(rotationMatrix.wrapped)
            resultWires.append(mirrored)

        return resultWires


    def _calcTransforms(self):
        """
            Computes transformation martrices to convert betwene local and global coordinates
        """
        #r is the forward transformation matrix from world to local coordinates
        #ok i will be really honest-- i cannot understand exactly why this works
        #something bout the order of the transaltion and the rotation.
        # the double-inverting is strange, and i dont understand it.
        r = FreeCAD.Base.Matrix()

        #forward transform must rotate and adjust for origin
        (r.A11, r.A12, r.A13 ) = (self.xDir.x, self.xDir.y, self.xDir.z )
        (r.A21, r.A22, r.A23 ) = (self.yDir.x, self.yDir.y, self.yDir.z )
        (r.A31, r.A32, r.A33 ) = (self.zDir.x, self.zDir.y, self.zDir.z )

        invR = r.inverse()
        (invR.A14,invR.A24,invR.A34) = (self.origin.x,self.origin.y,self.origin.z)

        ( self.rG,self.fG ) = ( invR,invR.inverse() )

    def computeTransform(self,tMatrix):
        """
            Computes the 2-d projection of the supplied matrix
        """

        rm = self.fG.multiply(tMatrix.wrapped).multiply(self.rG)
        return Matrix(rm)

class BoundBox(object):
    "A BoundingBox for an object or set of objects. Wraps the FreeCAD one"
    def __init__(self,bb):
        self.wrapped = bb
        self.xmin = bb.XMin
        self.xmax = bb.XMax
        self.xlen = bb.XLength
        self.ymin = bb.YMin
        self.ymax = bb.YMax
        self.ylen = bb.YLength
        self.zmin = bb.ZMin
        self.zmax = bb.ZMax
        self.zlen = bb.ZLength
        self.center = Vector(bb.Center)
        self.DiagonalLength = bb.DiagonalLength

    def add(self,obj):
        """
            returns a modified (expanded) bounding box

            obj can be one of several things:
               1. a 3-tuple corresponding to x,y, and z amounts to add
               2. a vector, containing the x,y,z values to add
               3. another bounding box, where a new box will be created that encloses both

            this bounding box is not changed
        """
        tmp = FreeCAD.Base.BoundBox(self.wrapped)
        if type(obj) is tuple:
            tmp.add(obj[0],obj[1],obj[2])
        elif type(obj) is Vector:
            tmp.add(obj.fV)
        elif type(obj) is BoundBox:
            tmp.add(obj.wrapped)

        return BoundBox(tmp)

    @classmethod
    def findOutsideBox2D(cls,b1, b2):
        """
            compares bounding boxes. returns none if neither is inside the other. returns
            the outer one if either is outside the other

            BoundBox.isInside works in 3d, but this is a 2d bounding box, so it doesnt work correctly
            plus, there was all kinds of rounding error in the built-in implementation i do not understand.
            Here we assume that the b
        """
        bb1 = b1.wrapped
        bb2 = b2.wrapped
        if bb1.XMin < bb2.XMin and\
           bb1.XMax > bb2.XMax and\
           bb1.YMin < bb2.YMin and\
           bb1.YMax > bb2.YMax:
            return b1

        if bb2.XMin < bb1.XMin and\
           bb2.XMax > bb1.XMax and\
           bb2.YMin < bb1.YMin and\
           bb2.YMax > bb1.YMax:
            return b2

        return None

    def isInside(self,anotherBox):
        """
            is the provided bounding box inside this one?
        """
        return self.wrapped.isInside(anotherBox.wrapped)
