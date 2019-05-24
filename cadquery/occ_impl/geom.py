import math
        
from OCC.Core.gp import gp_Vec, gp_Ax1, gp_Ax3, gp_Pnt, gp_Dir, gp_Trsf, gp, gp_XYZ
from OCC.Core.Bnd import Bnd_Box
from OCC.Core.BRepBndLib import brepbndlib_Add  # brepbndlib_AddOptimal
from OCC.Core.BRepMesh import BRepMesh_IncrementalMesh

TOL = 1e-2


class Vector(object):
    """Create a 3-dimensional vector

        :param args: a 3-d vector, with x-y-z parts.

        you can either provide:
            * nothing (in which case the null vector is return)
            * a gp_Vec
            * a vector ( in which case it is copied )
            * a 3-tuple
            * a 2-tuple (z assumed to be 0)
            * three float values: x, y, and z
            * two float values: x,y
    """

    def __init__(self, *args):
        if len(args) == 3:
            fV = gp_Vec(*args)
        elif len(args) == 2:
            fV = gp_Vec(*args,0)
        elif len(args) == 1:
            if isinstance(args[0], Vector):
                fV = gp_Vec(args[0].wrapped.XYZ())
            elif isinstance(args[0], (tuple, list)):
                arg = args[0]
                if len(arg)==3:
                    fV = gp_Vec(*arg)
                elif len(arg)==2:
                    fV = gp_Vec(*arg,0)
            elif isinstance(args[0], (gp_Vec, gp_Pnt, gp_Dir)):
                fV = gp_Vec(args[0].XYZ())
            elif isinstance(args[0], gp_XYZ):
                fV = gp_Vec(args[0])
            else:
                raise TypeError("Expected three floats, OCC gp_, or 3-tuple")
        elif len(args) == 0:
            fV = gp_Vec(0, 0, 0)
        else:
            raise TypeError("Expected three floats, OCC gp_, or 3-tuple")

        self._wrapped = fV

    @property
    def x(self):
        return self.wrapped.X()
    
    @x.setter
    def x(self,value):
        self.wrapped.SetX(value)

    @property
    def y(self):
        return self.wrapped.Y()
    
    @y.setter
    def y(self,value):
        self.wrapped.SetY(value)

    @property
    def z(self):
        return self.wrapped.Z()
    
    @z.setter
    def z(self,value):
        self.wrapped.SetZ(value)

    @property
    def Length(self):
        return self.wrapped.Magnitude()

    @property
    def wrapped(self):
        return self._wrapped

    def toTuple(self):
        return (self.x, self.y, self.z)

    # TODO: is it possible to create a dynamic proxy without all this code?
    def cross(self, v):
        return Vector(self.wrapped.Crossed(v.wrapped))

    def dot(self, v):
        return self.wrapped.Dot(v.wrapped)

    def sub(self, v):
        return Vector(self.wrapped.Subtracted(v.wrapped))

    def __sub__(self, v):
        return self.sub(v)

    def add(self, v):
        return Vector(self.wrapped.Added(v.wrapped))

    def __add__(self, v):
        return self.add(v)

    def multiply(self, scale):
        """Return a copy multiplied by the provided scalar"""
        return Vector(self.wrapped.Multiplied(scale))

    def __mul__(self, scale):
        return self.multiply(scale)

    def __truediv__(self, denom):
        return self.multiply(1.0 / denom)

    def normalized(self):
        """Return a normalized version of this vector"""
        return Vector(self.wrapped.Normalized())

    def Center(self):
        """Return the vector itself

        The center of myself is myself.
        Provided so that vectors, vertexes, and other shapes all support a
        common interface, when Center() is requested for all objects on the
        stack.
        """
        return self

    def getAngle(self, v):
        return self.wrapped.Angle(v.wrapped)

    def distanceToLine(self):
        raise NotImplementedError(
            "Have not needed this yet, but FreeCAD supports it!")

    def projectToLine(self):
        raise NotImplementedError(
            "Have not needed this yet, but FreeCAD supports it!")

    def distanceToPlane(self):
        raise NotImplementedError(
            "Have not needed this yet, but FreeCAD supports it!")

    def projectToPlane(self, *args):
        """
        Vector is projected onto the plane provided as input.

        :param args: Plane object or base and normal vectors that define the plane

        This method modifies the vector in place and returns the new vector.
        """
        if len(args) == 2:
            base = args[0]
            normal = args[1]
        else:
            base = args[0].origin
            normal = args[1].zDir

        result = self-normal*(((self-base).dot(normal))/normal.Length**2)

        self.x = result.x
        self.y = result.y
        self.z = result.z

    def __neg__(self):
        return self * -1

    def __abs__(self):
        return self.Length

    def __repr__(self):
        return 'Vector: ' + str((self.x, self.y, self.z))

    def __str__(self):
        return 'Vector: ' + str((self.x, self.y, self.z))

    def __eq__(self, other):
        return self.wrapped.IsEqual(other.wrapped, 0.00001, 0.00001)
    '''
    is not implemented in OCC
    def __ne__(self, other):
        return self.wrapped.__ne__(other)
    '''

    def toPnt(self):

        return gp_Pnt(self.wrapped.XYZ())

    def toDir(self):

        return gp_Dir(self.wrapped.XYZ())

    def transform(self, T):

        # to gp_Pnt to obey cq transformation convention (in OCC.Core.vectors do not translate)
        pnt = self.toPnt()
        pnt_t = pnt.Transformed(T.wrapped)

        return Vector(gp_Vec(pnt_t.XYZ()))


class Matrix:
    """A 3d , 4x4 transformation matrix.

    Used to move geometry in space.

    The provided "matrix" parameter may be None, a gp_Trsf, or a nested list of
    values.

    If given a nested list, it is expected to be of the form:

        [[m11, m12, m13, m14],
         [m21, m22, m23, m24],
         [m31, m32, m33, m34]]

    A fourth row may be given, but it is expected to be: [0.0, 0.0, 0.0, 1.0]
    since this is a transform matrix.
    """

    def __init__(self, matrix=None):

        if matrix is None:
            self.wrapped = gp_Trsf()
        elif isinstance(matrix, gp_Trsf):
            self.wrapped = matrix
        elif isinstance(matrix, (list, tuple)):
            # Validate matrix size & 4x4 last row value
            valid_sizes = all(
                (isinstance(row, (list, tuple)) and (len(row) == 4))
                for row in matrix
            ) and len(matrix) in (3, 4)
            if not valid_sizes:
                raise TypeError("Matrix constructor requires 2d list of 4x3 or 4x4, but got: {!r}".format(matrix))
            elif (len(matrix) == 4) and (tuple(matrix[3]) != (0,0,0,1)):
                raise ValueError("Expected the last row to be [0,0,0,1], but got: {!r}".format(matrix[3]))

            # Assign values to matrix
            self.wrapped = gp_Trsf()
            flattened = [e for row in matrix[:3] for e in row]
            self.wrapped.SetValues(*flattened)
        else:
            raise TypeError(
                    "Invalid param to matrix constructor: {}".format(matrix))

    def rotateX(self, angle):

        self._rotate(gp.OX(),
                     angle)

    def rotateY(self, angle):

        self._rotate(gp.OY(),
                     angle)

    def rotateZ(self, angle):

        self._rotate(gp.OZ(),
                     angle)

    def _rotate(self, direction, angle):

        new = gp_Trsf()
        new.SetRotation(direction,
                        angle)

        self.wrapped = self.wrapped * new

    def inverse(self):

        return Matrix(self.wrapped.Inverted())

    def multiply(self, other):

        if isinstance(other, Vector):
            return other.transform(self)

        return Matrix(self.wrapped.Multiplied(other.wrapped))

    def transposed_list(self):
        """Needed by the cqparts gltf exporter
        """
        
        trsf = self.wrapped
        data = [[trsf.Value(i,j) for j in range(1,5)] for i in range(1,4)] + \
               [[0.,0.,0.,1.]]
        
        return [data[j][i] for i in range(4) for j in range(4)]

    def __getitem__(self, rc):
        """Provide Matrix[r, c] syntax for accessing individual values. The row
        and column parameters start at zero, which is consistent with most
        python libraries, but is counter to gp_Trsf(), which is 1-indexed.
        """
        if not isinstance(rc, tuple) or (len(rc) != 2):
            raise IndexError("Matrix subscript must provide (row, column)")
        (r, c) = rc
        if (0 <= r <= 3) and (0 <= c <= 3):
            if r < 3:
                return self.wrapped.Value(r + 1, c + 1)
            else:
                # gp_Trsf doesn't provide access to the 4th row because it has
                # an implied value as below:
                return [0., 0., 0., 1.][c]
        else:
            raise IndexError("Out of bounds access into 4x4 matrix: {!r}".format(rc))


class Plane(object):
    """A 2D coordinate system in space

    A 2D coordinate system in space, with the x-y axes on the plane, and a
    particular point as the origin.

    A plane allows the use of 2-d coordinates, which are later converted to
    global, 3d coordinates when the operations are complete.

    Frequently, it is not necessary to create work planes, as they can be
    created automatically from faces.
    """

    # equality tolerances
    _eq_tolerance_origin = 1e-6
    _eq_tolerance_dot = 1e-6

    @classmethod
    def named(cls, stdName, origin=(0, 0, 0)):
        """Create a predefined Plane based on the conventional names.

        :param stdName: one of (XY|YZ|ZX|XZ|YX|ZY|front|back|left|right|top|bottom)
        :type stdName: string
        :param origin: the desired origin, specified in global coordinates
        :type origin: 3-tuple of the origin of the new plane, in global coorindates.

        Available named planes are as follows. Direction references refer to
        the global directions.

        =========== ======= ======= ======
        Name        xDir    yDir    zDir
        =========== ======= ======= ======
        XY          +x      +y      +z
        YZ          +y      +z      +x
        ZX          +z      +x      +y
        XZ          +x      +z      -y
        YX          +y      +x      -z
        ZY          +z      +y      -x
        front       +x      +y      +z
        back        -x      +y      -z
        left        +z      +y      -x
        right       -z      +y      +x
        top         +x      -z      +y
        bottom      +x      +z      -y
        =========== ======= ======= ======
        """

        namedPlanes = {
            # origin, xDir, normal
            'XY': Plane(origin, (1, 0, 0), (0, 0, 1)),
            'YZ': Plane(origin, (0, 1, 0), (1, 0, 0)),
            'ZX': Plane(origin, (0, 0, 1), (0, 1, 0)),
            'XZ': Plane(origin, (1, 0, 0), (0, -1, 0)),
            'YX': Plane(origin, (0, 1, 0), (0, 0, -1)),
            'ZY': Plane(origin, (0, 0, 1), (-1, 0, 0)),
            'front': Plane(origin, (1, 0, 0), (0, 0, 1)),
            'back': Plane(origin, (-1, 0, 0), (0, 0, -1)),
            'left': Plane(origin, (0, 0, 1), (-1, 0, 0)),
            'right': Plane(origin, (0, 0, -1), (1, 0, 0)),
            'top': Plane(origin, (1, 0, 0), (0, 1, 0)),
            'bottom': Plane(origin, (1, 0, 0), (0, -1, 0))
        }

        try:
            return namedPlanes[stdName]
        except KeyError:
            raise ValueError('Supported names are {}'.format(
                list(namedPlanes.keys())))

    @classmethod
    def XY(cls, origin=(0, 0, 0), xDir=Vector(1, 0, 0)):
        plane = Plane.named('XY', origin)
        plane._setPlaneDir(xDir)
        return plane

    @classmethod
    def YZ(cls, origin=(0, 0, 0), xDir=Vector(0, 1, 0)):
        plane = Plane.named('YZ', origin)
        plane._setPlaneDir(xDir)
        return plane

    @classmethod
    def ZX(cls, origin=(0, 0, 0), xDir=Vector(0, 0, 1)):
        plane = Plane.named('ZX', origin)
        plane._setPlaneDir(xDir)
        return plane

    @classmethod
    def XZ(cls, origin=(0, 0, 0), xDir=Vector(1, 0, 0)):
        plane = Plane.named('XZ', origin)
        plane._setPlaneDir(xDir)
        return plane

    @classmethod
    def YX(cls, origin=(0, 0, 0), xDir=Vector(0, 1, 0)):
        plane = Plane.named('YX', origin)
        plane._setPlaneDir(xDir)
        return plane

    @classmethod
    def ZY(cls, origin=(0, 0, 0), xDir=Vector(0, 0, 1)):
        plane = Plane.named('ZY', origin)
        plane._setPlaneDir(xDir)
        return plane

    @classmethod
    def front(cls, origin=(0, 0, 0), xDir=Vector(1, 0, 0)):
        plane = Plane.named('front', origin)
        plane._setPlaneDir(xDir)
        return plane

    @classmethod
    def back(cls, origin=(0, 0, 0), xDir=Vector(-1, 0, 0)):
        plane = Plane.named('back', origin)
        plane._setPlaneDir(xDir)
        return plane

    @classmethod
    def left(cls, origin=(0, 0, 0), xDir=Vector(0, 0, 1)):
        plane = Plane.named('left', origin)
        plane._setPlaneDir(xDir)
        return plane

    @classmethod
    def right(cls, origin=(0, 0, 0), xDir=Vector(0, 0, -1)):
        plane = Plane.named('right', origin)
        plane._setPlaneDir(xDir)
        return plane

    @classmethod
    def top(cls, origin=(0, 0, 0), xDir=Vector(1, 0, 0)):
        plane = Plane.named('top', origin)
        plane._setPlaneDir(xDir)
        return plane

    @classmethod
    def bottom(cls, origin=(0, 0, 0), xDir=Vector(1, 0, 0)):
        plane = Plane.named('bottom', origin)
        plane._setPlaneDir(xDir)
        return plane

    def __init__(self, origin, xDir, normal):
        """Create a Plane with an arbitrary orientation

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
        zDir = Vector(normal)
        if (zDir.Length == 0.0):
            raise ValueError('normal should be non null')

        xDir = Vector(xDir)
        if (xDir.Length == 0.0):
            raise ValueError('xDir should be non null')

        self.zDir = zDir.normalized()
        self._setPlaneDir(xDir)
        self.origin = origin

    def _eq_iter(self, other):
        """Iterator to successively test equality"""
        cls = type(self)
        yield isinstance(other, Plane)  # comparison is with another Plane
        # origins are the same
        yield abs(self.origin - other.origin) < cls._eq_tolerance_origin
        # z-axis vectors are parallel (assumption: both are unit vectors)
        yield abs(self.zDir.dot(other.zDir) - 1) < cls._eq_tolerance_dot
        # x-axis vectors are parallel (assumption: both are unit vectors)
        yield abs(self.xDir.dot(other.xDir) - 1) < cls._eq_tolerance_dot

    def __eq__(self, other):
        return all(self._eq_iter(other))

    def __ne__(self, other):
        return not self.__eq__(other)

    @property
    def origin(self):
        return self._origin
# TODO is this property rly needed -- why not handle this in the constructor

    @origin.setter
    def origin(self, value):
        self._origin = Vector(value)
        self._calcTransforms()

    def setOrigin2d(self, x, y):
        """
        Set a new origin in the plane itself

        Set a new origin in the plane itself. The plane's orientation and
        xDrection are unaffected.

        :param float x: offset in the x direction
        :param float y: offset in the y direction
        :return: void

        The new coordinates are specified in terms of the current 2-d system.
        As an example:

        p = Plane.XY()
        p.setOrigin2d(2, 2)
        p.setOrigin2d(2, 2)

        results in a plane with its origin at (x, y) = (4, 4) in global
        coordinates. Both operations were relative to local coordinates of the
        plane.
        """
        self.origin = self.toWorldCoords((x, y))

    def isWireInside(self, baseWire, testWire):
        """Determine if testWire is inside baseWire

        Determine if testWire is inside baseWire, after both wires are projected
        into the current plane.

        :param baseWire: a reference wire
        :type baseWire: a FreeCAD wire
        :param testWire: another wire
        :type testWire: a FreeCAD wire
        :return: True if testWire is inside baseWire, otherwise False

        If either wire does not lie in the current plane, it is projected into
        the plane first.

        *WARNING*:  This method is not 100% reliable. It uses bounding box
        tests, but needs more work to check for cases when curves are complex.

        Future Enhancements:
            * Discretizing points along each curve to provide a more reliable
              test.
        """

        pass

        '''
        # TODO: also use a set of points along the wire to test as well.
        # TODO: would it be more efficient to create objects in the local
        #       coordinate system, and then transform to global
        #       coordinates upon extrusion?

        tBaseWire = baseWire.transformGeometry(self.fG)
        tTestWire = testWire.transformGeometry(self.fG)

        # These bounding boxes will have z=0, since we transformed them into the
        # space of the plane.
        bb = tBaseWire.BoundingBox()
        tb = tTestWire.BoundingBox()

        # findOutsideBox actually inspects both ways, here we only want to
        # know if one is inside the other
        return bb == BoundBox.findOutsideBox2D(bb, tb)
        '''

    def toLocalCoords(self, obj):
        """Project the provided coordinates onto this plane

        :param obj: an object or vector to convert
        :type vector: a vector or shape
        :return: an object of the same type, but converted to local coordinates


        Most of the time, the z-coordinate returned will be zero, because most
        operations based on a plane are all 2-d. Occasionally, though, 3-d
        points outside of the current plane are transformed. One such example is
        :py:meth:`Workplane.box`, where 3-d corners of a box are transformed to
        orient the box in space correctly.

        """
        from .shapes import Shape
        
        if isinstance(obj, Vector):
            return obj.transform(self.fG)
        elif isinstance(obj, Shape):
            return obj.transformShape(self.fG)
        else:
            raise ValueError(
                "Don't know how to convert type {} to local coordinates".format(
                    type(obj)))

    def toWorldCoords(self, tuplePoint):
        """Convert a point in local coordinates to global coordinates

        :param tuplePoint: point in local coordinates to convert.
        :type tuplePoint: a 2 or three tuple of float. The third value is taken to be zero if not supplied.
        :return: a Vector in global coordinates
        """
        if isinstance(tuplePoint, Vector):
            v = tuplePoint
        elif len(tuplePoint) == 2:
            v = Vector(tuplePoint[0], tuplePoint[1], 0)
        else:
            v = Vector(tuplePoint)
        return v.transform(self.rG)

    def rotated(self, rotate=(0, 0, 0)):
        """Returns a copy of this plane, rotated about the specified axes

        Since the z axis is always normal the plane, rotating around Z will
        always produce a plane that is parallel to this one.

        The origin of the workplane is unaffected by the rotation.

        Rotations are done in order x, y, z. If you need a different order,
        manually chain together multiple rotate() commands.

        :param rotate: Vector [xDegrees, yDegrees, zDegrees]
        :return: a copy of this plane rotated as requested.
        """
        rotate = Vector(rotate)
        # Convert to radians.
        rotate = rotate.multiply(math.pi / 180.0)

        # Compute rotation matrix.
        m = Matrix()
        m.rotateX(rotate.x)
        m.rotateY(rotate.y)
        m.rotateZ(rotate.z)

        # Compute the new plane.
        newXdir = self.xDir.transform(m)
        newZdir = self.zDir.transform(m)

        return Plane(self.origin, newXdir, newZdir)

    def rotateShapes(self, listOfShapes, rotationMatrix):
        """Rotate the listOfShapes by the supplied rotationMatrix

        @param listOfShapes is a list of shape objects
        @param rotationMatrix is a geom.Matrix object.
        returns a list of shape objects rotated according to the rotationMatrix.
        """
        # Compute rotation matrix (global --> local --> rotate --> global).
        # rm = self.plane.fG.multiply(matrix).multiply(self.plane.rG)
        # rm = self.computeTransform(rotationMatrix)

        # There might be a better way, but to do this rotation takes 3 steps:
        # - transform geometry to local coordinates
        # - then rotate about x
        # - then transform back to global coordinates.

        # TODO why is it here?

        raise NotImplementedError

        '''
        resultWires = []
        for w in listOfShapes:
            mirrored = w.transformGeometry(rotationMatrix.wrapped)

            # If the first vertex of the second wire is not coincident with the
            # first or last vertices of the first wire we have to fix the wire
            # so that it will mirror correctly.
            if ((mirrored.wrapped.Vertexes[0].X == w.wrapped.Vertexes[0].X and
                 mirrored.wrapped.Vertexes[0].Y == w.wrapped.Vertexes[0].Y and
                 mirrored.wrapped.Vertexes[0].Z == w.wrapped.Vertexes[0].Z) or
                (mirrored.wrapped.Vertexes[0].X == w.wrapped.Vertexes[-1].X and
                 mirrored.wrapped.Vertexes[0].Y == w.wrapped.Vertexes[-1].Y and
                 mirrored.wrapped.Vertexes[0].Z == w.wrapped.Vertexes[-1].Z)):

                resultWires.append(mirrored)
            else:
                # Make sure that our mirrored edges meet up and are ordered
                # properly.
                aEdges = w.wrapped.Edges
                aEdges.extend(mirrored.wrapped.Edges)
                comp = FreeCADPart.Compound(aEdges)
                mirroredWire = comp.connectEdgesToWires(False).Wires[0]

                resultWires.append(cadquery.Shape.cast(mirroredWire))

        return resultWires'''

    def mirrorInPlane(self, listOfShapes, axis='X'):

        local_coord_system = gp_Ax3(self.origin.toPnt(),
                                    self.zDir.toDir(),
                                    self.xDir.toDir())
        T = gp_Trsf()

        if axis == 'X':
            T.SetMirror(gp_Ax1(self.origin.toPnt(),
                               local_coord_system.XDirection()))
        elif axis == 'Y':
            T.SetMirror(gp_Ax1(self.origin.toPnt(),
                               local_coord_system.YDirection()))
        else:
            raise NotImplementedError

        resultWires = []
        for w in listOfShapes:
            mirrored = w.transformShape(Matrix(T))

            # attemp stitching of the wires
            resultWires.append(mirrored)

        return resultWires

    def _setPlaneDir(self, xDir):
        """Set the vectors parallel to the plane, i.e. xDir and yDir"""
        xDir = Vector(xDir)
        self.xDir = xDir.normalized()
        self.yDir = self.zDir.cross(self.xDir).normalized()

    def _calcTransforms(self):
        """Computes transformation matrices to convert between coordinates

        Computes transformation matrices to convert between local and global
        coordinates.
        """
        # r is the forward transformation matrix from world to local coordinates
        # ok i will be really honest, i cannot understand exactly why this works
        # something bout the order of the translation and the rotation.
        # the double-inverting is strange, and I don't understand it.
        forward = Matrix()
        inverse = Matrix()

        global_coord_system = gp_Ax3()
        local_coord_system = gp_Ax3(gp_Pnt(*self.origin.toTuple()),
                                    gp_Dir(*self.zDir.toTuple()),
                                    gp_Dir(*self.xDir.toTuple())
                                    )

        forward.wrapped.SetTransformation(global_coord_system,
                                          local_coord_system)

        inverse.wrapped.SetTransformation(local_coord_system,
                                          global_coord_system)

        # TODO verify if this is OK
        self.lcs = local_coord_system
        self.rG = inverse
        self.fG = forward


class BoundBox(object):
    """A BoundingBox for an object or set of objects. Wraps the OCC.Core.one"""

    def __init__(self, bb):
        self.wrapped = bb
        XMin, YMin, ZMin, XMax, YMax, ZMax = bb.Get()

        self.xmin = XMin
        self.xmax = XMax
        self.xlen = XMax - XMin
        self.ymin = YMin
        self.ymax = YMax
        self.ylen = YMax - YMin
        self.zmin = ZMin
        self.zmax = ZMax
        self.zlen = ZMax - ZMin

        self.center = Vector((XMax + XMin) / 2,
                             (YMax + YMin) / 2,
                             (ZMax + ZMin) / 2)

        self.DiagonalLength = self.wrapped.SquareExtent()**0.5

    def add(self, obj, tol=1e-8):
        """Returns a modified (expanded) bounding box

        obj can be one of several things:
            1. a 3-tuple corresponding to x,y, and z amounts to add
            2. a vector, containing the x,y,z values to add
            3. another bounding box, where a new box will be created that
               encloses both.

        This bounding box is not changed.
        """

        tmp = Bnd_Box()
        tmp.SetGap(tol)
        tmp.Add(self.wrapped)

        if isinstance(obj, tuple):
            tmp.Update(*obj)
        elif isinstance(obj, Vector):
            tmp.Update(*obj.toTuple())
        elif isinstance(obj, BoundBox):
            tmp.Add(obj.wrapped)

        return BoundBox(tmp)

    @staticmethod
    def findOutsideBox2D(bb1, bb2):
        """Compares bounding boxes

        Compares bounding boxes. Returns none if neither is inside the other.
        Returns the outer one if either is outside the other.

        BoundBox.isInside works in 3d, but this is a 2d bounding box, so it
        doesn't work correctly plus, there was all kinds of rounding error in
        the built-in implementation i do not understand.
        """

        if (bb1.XMin < bb2.XMin and
            bb1.XMax > bb2.XMax and
            bb1.YMin < bb2.YMin and
                bb1.YMax > bb2.YMax):
            return bb1

        if (bb2.XMin < bb1.XMin and
            bb2.XMax > bb1.XMax and
            bb2.YMin < bb1.YMin and
                bb2.YMax > bb1.YMax):
            return bb2

        return None

    @classmethod
    def _fromTopoDS(cls, shape, tol=None, optimal=False):
        '''
        Constructs a bounding box from a TopoDS_Shape
        '''
        tol = TOL if tol is None else tol  # tol = TOL (by default)
        bbox = Bnd_Box()
        bbox.SetGap(tol)
        if optimal:
            raise NotImplementedError
            # brepbndlib_AddOptimal(shape, bbox) #this is 'exact' but expensive - not yet wrapped by PythonOCC
        else:
            mesh = BRepMesh_IncrementalMesh(shape, TOL, True)
            mesh.Perform()
            # this is adds +margin but is faster
            brepbndlib_Add(shape, bbox, True)

        return cls(bbox)

    def isInside(self, b2):
        """Is the provided bounding box inside this one?"""
        if (b2.xmin > self.xmin and
            b2.ymin > self.ymin and
            b2.zmin > self.zmin and
            b2.xmax < self.xmax and
            b2.ymax < self.ymax and
            b2.zmax < self.zmax):
            return True
        else:
            return False
