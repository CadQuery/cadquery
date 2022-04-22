import math

from typing import overload, Sequence, Union, Tuple, Type, Optional

from OCP.gp import (
    gp_Vec,
    gp_Ax1,
    gp_Ax3,
    gp_Pnt,
    gp_Dir,
    gp_Pln,
    gp_Trsf,
    gp_GTrsf,
    gp_XYZ,
    gp_EulerSequence,
    gp,
)
from OCP.Bnd import Bnd_Box
from OCP.BRepBndLib import BRepBndLib
from OCP.BRepMesh import BRepMesh_IncrementalMesh
from OCP.TopoDS import TopoDS_Shape
from OCP.TopLoc import TopLoc_Location

TOL = 1e-2


class Vector(object):
    """Create a 3-dimensional vector

    :param args: a 3D vector, with x-y-z parts.

    you can either provide:
        * nothing (in which case the null vector is return)
        * a gp_Vec
        * a vector ( in which case it is copied )
        * a 3-tuple
        * a 2-tuple (z assumed to be 0)
        * three float values: x, y, and z
        * two float values: x,y
    """

    _wrapped: gp_Vec

    @overload
    def __init__(self, x: float, y: float, z: float) -> None:
        ...

    @overload
    def __init__(self, x: float, y: float) -> None:
        ...

    @overload
    def __init__(self, v: "Vector") -> None:
        ...

    @overload
    def __init__(self, v: Sequence[float]) -> None:
        ...

    @overload
    def __init__(self, v: Union[gp_Vec, gp_Pnt, gp_Dir, gp_XYZ]) -> None:
        ...

    @overload
    def __init__(self) -> None:
        ...

    def __init__(self, *args):
        if len(args) == 3:
            fV = gp_Vec(*args)
        elif len(args) == 2:
            fV = gp_Vec(*args, 0)
        elif len(args) == 1:
            if isinstance(args[0], Vector):
                fV = gp_Vec(args[0].wrapped.XYZ())
            elif isinstance(args[0], (tuple, list)):
                arg = args[0]
                if len(arg) == 3:
                    fV = gp_Vec(*arg)
                elif len(arg) == 2:
                    fV = gp_Vec(*arg, 0)
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
    def x(self) -> float:
        return self.wrapped.X()

    @x.setter
    def x(self, value: float) -> None:
        self.wrapped.SetX(value)

    @property
    def y(self) -> float:
        return self.wrapped.Y()

    @y.setter
    def y(self, value: float) -> None:
        self.wrapped.SetY(value)

    @property
    def z(self) -> float:
        return self.wrapped.Z()

    @z.setter
    def z(self, value: float) -> None:
        self.wrapped.SetZ(value)

    @property
    def Length(self) -> float:
        return self.wrapped.Magnitude()

    @property
    def wrapped(self) -> gp_Vec:
        return self._wrapped

    def toTuple(self) -> Tuple[float, float, float]:
        return (self.x, self.y, self.z)

    def cross(self, v: "Vector") -> "Vector":
        return Vector(self.wrapped.Crossed(v.wrapped))

    def dot(self, v: "Vector") -> float:
        return self.wrapped.Dot(v.wrapped)

    def sub(self, v: "Vector") -> "Vector":
        return Vector(self.wrapped.Subtracted(v.wrapped))

    def __sub__(self, v: "Vector") -> "Vector":
        return self.sub(v)

    def add(self, v: "Vector") -> "Vector":
        return Vector(self.wrapped.Added(v.wrapped))

    def __add__(self, v: "Vector") -> "Vector":
        return self.add(v)

    def multiply(self, scale: float) -> "Vector":
        """Return a copy multiplied by the provided scalar"""
        return Vector(self.wrapped.Multiplied(scale))

    def __mul__(self, scale: float) -> "Vector":
        return self.multiply(scale)

    def __truediv__(self, denom: float) -> "Vector":
        return self.multiply(1.0 / denom)

    def __rmul__(self, scale: float) -> "Vector":
        return self.multiply(scale)

    def normalized(self) -> "Vector":
        """Return a normalized version of this vector"""
        return Vector(self.wrapped.Normalized())

    def Center(self) -> "Vector":
        """Return the vector itself

        The center of myself is myself.
        Provided so that vectors, vertices, and other shapes all support a
        common interface, when Center() is requested for all objects on the
        stack.
        """
        return self

    def getAngle(self, v: "Vector") -> float:
        return self.wrapped.Angle(v.wrapped)

    def getSignedAngle(self, v: "Vector") -> float:
        return self.wrapped.AngleWithRef(v.wrapped, gp_Vec(0, 0, -1))

    def distanceToLine(self):
        raise NotImplementedError("Have not needed this yet, but OCCT supports it!")

    def projectToLine(self, line: "Vector") -> "Vector":
        """
        Returns a new vector equal to the projection of this Vector onto the line
        represented by Vector <line>

        :param args: Vector

        Returns the projected vector.
        """
        lineLength = line.Length

        return line * (self.dot(line) / (lineLength * lineLength))

    def distanceToPlane(self):
        raise NotImplementedError("Have not needed this yet, but OCCT supports it!")

    def projectToPlane(self, plane: "Plane") -> "Vector":
        """
        Vector is projected onto the plane provided as input.

        :param args: Plane object

        Returns the projected vector.
        """
        base = plane.origin
        normal = plane.zDir

        return self - normal * (((self - base).dot(normal)) / normal.Length ** 2)

    def __neg__(self) -> "Vector":
        return self * -1

    def __abs__(self) -> float:
        return self.Length

    def __repr__(self) -> str:
        return "Vector: " + str((self.x, self.y, self.z))

    def __str__(self) -> str:
        return "Vector: " + str((self.x, self.y, self.z))

    def __eq__(self, other: "Vector") -> bool:  # type: ignore[override]
        return self.wrapped.IsEqual(other.wrapped, 0.00001, 0.00001)

    def toPnt(self) -> gp_Pnt:

        return gp_Pnt(self.wrapped.XYZ())

    def toDir(self) -> gp_Dir:

        return gp_Dir(self.wrapped.XYZ())

    def transform(self, T: "Matrix") -> "Vector":

        # to gp_Pnt to obey cq transformation convention (in OCP.vectors do not translate)
        pnt = self.toPnt()
        pnt_t = pnt.Transformed(T.wrapped.Trsf())

        return Vector(gp_Vec(pnt_t.XYZ()))


class Matrix:
    """A 3d , 4x4 transformation matrix.

    Used to move geometry in space.

    The provided "matrix" parameter may be None, a gp_GTrsf, or a nested list of
    values.

    If given a nested list, it is expected to be of the form:

        [[m11, m12, m13, m14],
         [m21, m22, m23, m24],
         [m31, m32, m33, m34]]

    A fourth row may be given, but it is expected to be: [0.0, 0.0, 0.0, 1.0]
    since this is a transform matrix.
    """

    wrapped: gp_GTrsf

    @overload
    def __init__(self) -> None:
        ...

    @overload
    def __init__(self, matrix: Union[gp_GTrsf, gp_Trsf]) -> None:
        ...

    @overload
    def __init__(self, matrix: Sequence[Sequence[float]]) -> None:
        ...

    def __init__(self, matrix=None):

        if matrix is None:
            self.wrapped = gp_GTrsf()
        elif isinstance(matrix, gp_GTrsf):
            self.wrapped = matrix
        elif isinstance(matrix, gp_Trsf):
            self.wrapped = gp_GTrsf(matrix)
        elif isinstance(matrix, (list, tuple)):
            # Validate matrix size & 4x4 last row value
            valid_sizes = all(
                (isinstance(row, (list, tuple)) and (len(row) == 4)) for row in matrix
            ) and len(matrix) in (3, 4)
            if not valid_sizes:
                raise TypeError(
                    "Matrix constructor requires 2d list of 4x3 or 4x4, but got: {!r}".format(
                        matrix
                    )
                )
            elif (len(matrix) == 4) and (tuple(matrix[3]) != (0, 0, 0, 1)):
                raise ValueError(
                    "Expected the last row to be [0,0,0,1], but got: {!r}".format(
                        matrix[3]
                    )
                )

            # Assign values to matrix
            self.wrapped = gp_GTrsf()
            [
                self.wrapped.SetValue(i + 1, j + 1, e)
                for i, row in enumerate(matrix[:3])
                for j, e in enumerate(row)
            ]

        else:
            raise TypeError("Invalid param to matrix constructor: {}".format(matrix))

    def rotateX(self, angle: float):

        self._rotate(gp.OX_s(), angle)

    def rotateY(self, angle: float):

        self._rotate(gp.OY_s(), angle)

    def rotateZ(self, angle: float):

        self._rotate(gp.OZ_s(), angle)

    def _rotate(self, direction: gp_Ax1, angle: float):

        new = gp_Trsf()
        new.SetRotation(direction, angle)

        self.wrapped = self.wrapped * gp_GTrsf(new)

    def inverse(self) -> "Matrix":

        return Matrix(self.wrapped.Inverted())

    @overload
    def multiply(self, other: Vector) -> Vector:
        ...

    @overload
    def multiply(self, other: "Matrix") -> "Matrix":
        ...

    def multiply(self, other):

        if isinstance(other, Vector):
            return other.transform(self)

        return Matrix(self.wrapped.Multiplied(other.wrapped))

    def transposed_list(self) -> Sequence[float]:
        """Needed by the cqparts gltf exporter"""

        trsf = self.wrapped
        data = [[trsf.Value(i, j) for j in range(1, 5)] for i in range(1, 4)] + [
            [0.0, 0.0, 0.0, 1.0]
        ]

        return [data[j][i] for i in range(4) for j in range(4)]

    def __getitem__(self, rc: Tuple[int, int]) -> float:
        """Provide Matrix[r, c] syntax for accessing individual values. The row
        and column parameters start at zero, which is consistent with most
        python libraries, but is counter to gp_GTrsf(), which is 1-indexed.
        """
        if not isinstance(rc, tuple) or (len(rc) != 2):
            raise IndexError("Matrix subscript must provide (row, column)")
        (r, c) = rc
        if (0 <= r <= 3) and (0 <= c <= 3):
            if r < 3:
                return self.wrapped.Value(r + 1, c + 1)
            else:
                # gp_GTrsf doesn't provide access to the 4th row because it has
                # an implied value as below:
                return [0.0, 0.0, 0.0, 1.0][c]
        else:
            raise IndexError("Out of bounds access into 4x4 matrix: {!r}".format(rc))

    def __repr__(self) -> str:
        """
        Generate a valid python expression representing this Matrix
        """
        matrix_transposed = self.transposed_list()
        matrix_str = ",\n        ".join(str(matrix_transposed[i::4]) for i in range(4))
        return f"Matrix([{matrix_str}])"


class Plane(object):
    """A 2D coordinate system in space

    A 2D coordinate system in space, with the x-y axes on the plane, and a
    particular point as the origin.

    A plane allows the use of 2D coordinates, which are later converted to
    global, 3d coordinates when the operations are complete.

    Frequently, it is not necessary to create work planes, as they can be
    created automatically from faces.
    """

    xDir: Vector
    yDir: Vector
    zDir: Vector
    _origin: Vector

    lcs: gp_Ax3
    rG: Matrix
    fG: Matrix

    # equality tolerances
    _eq_tolerance_origin = 1e-6
    _eq_tolerance_dot = 1e-6

    @classmethod
    def named(cls: Type["Plane"], stdName: str, origin=(0, 0, 0)) -> "Plane":
        """Create a predefined Plane based on the conventional names.

        :param stdName: one of (XY|YZ|ZX|XZ|YX|ZY|front|back|left|right|top|bottom)
        :type stdName: string
        :param origin: the desired origin, specified in global coordinates
        :type origin: 3-tuple of the origin of the new plane, in global coordinates.

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
            "XY": Plane(origin, (1, 0, 0), (0, 0, 1)),
            "YZ": Plane(origin, (0, 1, 0), (1, 0, 0)),
            "ZX": Plane(origin, (0, 0, 1), (0, 1, 0)),
            "XZ": Plane(origin, (1, 0, 0), (0, -1, 0)),
            "YX": Plane(origin, (0, 1, 0), (0, 0, -1)),
            "ZY": Plane(origin, (0, 0, 1), (-1, 0, 0)),
            "front": Plane(origin, (1, 0, 0), (0, 0, 1)),
            "back": Plane(origin, (-1, 0, 0), (0, 0, -1)),
            "left": Plane(origin, (0, 0, 1), (-1, 0, 0)),
            "right": Plane(origin, (0, 0, -1), (1, 0, 0)),
            "top": Plane(origin, (1, 0, 0), (0, 1, 0)),
            "bottom": Plane(origin, (1, 0, 0), (0, -1, 0)),
        }

        try:
            return namedPlanes[stdName]
        except KeyError:
            raise ValueError("Supported names are {}".format(list(namedPlanes.keys())))

    @classmethod
    def XY(cls, origin=(0, 0, 0), xDir=Vector(1, 0, 0)):
        plane = Plane.named("XY", origin)
        plane._setPlaneDir(xDir)
        return plane

    @classmethod
    def YZ(cls, origin=(0, 0, 0), xDir=Vector(0, 1, 0)):
        plane = Plane.named("YZ", origin)
        plane._setPlaneDir(xDir)
        return plane

    @classmethod
    def ZX(cls, origin=(0, 0, 0), xDir=Vector(0, 0, 1)):
        plane = Plane.named("ZX", origin)
        plane._setPlaneDir(xDir)
        return plane

    @classmethod
    def XZ(cls, origin=(0, 0, 0), xDir=Vector(1, 0, 0)):
        plane = Plane.named("XZ", origin)
        plane._setPlaneDir(xDir)
        return plane

    @classmethod
    def YX(cls, origin=(0, 0, 0), xDir=Vector(0, 1, 0)):
        plane = Plane.named("YX", origin)
        plane._setPlaneDir(xDir)
        return plane

    @classmethod
    def ZY(cls, origin=(0, 0, 0), xDir=Vector(0, 0, 1)):
        plane = Plane.named("ZY", origin)
        plane._setPlaneDir(xDir)
        return plane

    @classmethod
    def front(cls, origin=(0, 0, 0), xDir=Vector(1, 0, 0)):
        plane = Plane.named("front", origin)
        plane._setPlaneDir(xDir)
        return plane

    @classmethod
    def back(cls, origin=(0, 0, 0), xDir=Vector(-1, 0, 0)):
        plane = Plane.named("back", origin)
        plane._setPlaneDir(xDir)
        return plane

    @classmethod
    def left(cls, origin=(0, 0, 0), xDir=Vector(0, 0, 1)):
        plane = Plane.named("left", origin)
        plane._setPlaneDir(xDir)
        return plane

    @classmethod
    def right(cls, origin=(0, 0, 0), xDir=Vector(0, 0, -1)):
        plane = Plane.named("right", origin)
        plane._setPlaneDir(xDir)
        return plane

    @classmethod
    def top(cls, origin=(0, 0, 0), xDir=Vector(1, 0, 0)):
        plane = Plane.named("top", origin)
        plane._setPlaneDir(xDir)
        return plane

    @classmethod
    def bottom(cls, origin=(0, 0, 0), xDir=Vector(1, 0, 0)):
        plane = Plane.named("bottom", origin)
        plane._setPlaneDir(xDir)
        return plane

    def __init__(
        self,
        origin: Union[Tuple[float, float, float], Vector],
        xDir: Optional[Union[Tuple[float, float, float], Vector]] = None,
        normal: Union[Tuple[float, float, float], Vector] = (0, 0, 1),
    ):
        """
        Create a Plane with an arbitrary orientation

        :param origin: the origin in global coordinates
        :param xDir: an optional vector representing the xDirection.
        :param normal: the normal direction for the plane
        :raises ValueError: if the specified xDir is not orthogonal to the provided normal
        """
        zDir = Vector(normal)
        if zDir.Length == 0.0:
            raise ValueError("normal should be non null")

        self.zDir = zDir.normalized()

        if xDir is None:
            ax3 = gp_Ax3(Vector(origin).toPnt(), Vector(normal).toDir())
            xDir = Vector(ax3.XDirection())
        else:
            xDir = Vector(xDir)
            if xDir.Length == 0.0:
                raise ValueError("xDir should be non null")
        self._setPlaneDir(xDir)
        self.origin = Vector(origin)

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

    def __repr__(self):
        return f"Plane(origin={str(self.origin.toTuple())}, xDir={str(self.xDir.toTuple())}, normal={str(self.zDir.toTuple())})"

    @property
    def origin(self) -> Vector:
        return self._origin

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

        The new coordinates are specified in terms of the current 2D system.
        As an example:

        p = Plane.XY()
        p.setOrigin2d(2, 2)
        p.setOrigin2d(2, 2)

        results in a plane with its origin at (x, y) = (4, 4) in global
        coordinates. Both operations were relative to local coordinates of the
        plane.
        """
        self.origin = self.toWorldCoords((x, y))

    def toLocalCoords(self, obj):
        """Project the provided coordinates onto this plane

        :param obj: an object or vector to convert
        :type vector: a vector or shape
        :return: an object of the same type, but converted to local coordinates


        Most of the time, the z-coordinate returned will be zero, because most
        operations based on a plane are all 2D. Occasionally, though, 3D
        points outside of the current plane are transformed. One such example is
        :py:meth:`Workplane.box`, where 3D corners of a box are transformed to
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
                    type(obj)
                )
            )

    def toWorldCoords(self, tuplePoint) -> Vector:
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
        # NB: this is not a geometric Vector
        rotate = Vector(rotate)
        # Convert to radians.
        rotate = rotate.multiply(math.pi / 180.0)

        # Compute rotation matrix.
        T1 = gp_Trsf()
        T1.SetRotation(
            gp_Ax1(gp_Pnt(*(0, 0, 0)), gp_Dir(*self.xDir.toTuple())), rotate.x
        )
        T2 = gp_Trsf()
        T2.SetRotation(
            gp_Ax1(gp_Pnt(*(0, 0, 0)), gp_Dir(*self.yDir.toTuple())), rotate.y
        )
        T3 = gp_Trsf()
        T3.SetRotation(
            gp_Ax1(gp_Pnt(*(0, 0, 0)), gp_Dir(*self.zDir.toTuple())), rotate.z
        )
        T = Matrix(gp_GTrsf(T1 * T2 * T3))

        # Compute the new plane.
        newXdir = self.xDir.transform(T)
        newZdir = self.zDir.transform(T)

        return Plane(self.origin, newXdir, newZdir)

    def mirrorInPlane(self, listOfShapes, axis="X"):

        local_coord_system = gp_Ax3(
            self.origin.toPnt(), self.zDir.toDir(), self.xDir.toDir()
        )
        T = gp_Trsf()

        if axis == "X":
            T.SetMirror(gp_Ax1(self.origin.toPnt(), local_coord_system.XDirection()))
        elif axis == "Y":
            T.SetMirror(gp_Ax1(self.origin.toPnt(), local_coord_system.YDirection()))
        else:
            raise NotImplementedError

        resultWires = []
        for w in listOfShapes:
            mirrored = w.transformShape(Matrix(T))

            # attempt stitching of the wires
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

        forwardT = gp_Trsf()
        inverseT = gp_Trsf()

        global_coord_system = gp_Ax3()
        local_coord_system = gp_Ax3(
            gp_Pnt(*self.origin.toTuple()),
            gp_Dir(*self.zDir.toTuple()),
            gp_Dir(*self.xDir.toTuple()),
        )

        forwardT.SetTransformation(global_coord_system, local_coord_system)
        forward.wrapped = gp_GTrsf(forwardT)

        inverseT.SetTransformation(local_coord_system, global_coord_system)
        inverse.wrapped = gp_GTrsf(inverseT)

        self.lcs = local_coord_system
        self.rG = inverse
        self.fG = forward

    @property
    def location(self) -> "Location":

        return Location(self)

    def toPln(self) -> gp_Pln:

        return gp_Pln(gp_Ax3(self.origin.toPnt(), self.zDir.toDir(), self.xDir.toDir()))


class BoundBox(object):
    """A BoundingBox for an object or set of objects. Wraps the OCP one"""

    wrapped: Bnd_Box

    xmin: float
    xmax: float
    xlen: float

    ymin: float
    ymax: float
    ylen: float

    zmin: float
    zmax: float
    zlen: float

    center: Vector
    DiagonalLength: float

    def __init__(self, bb: Bnd_Box) -> None:
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

        self.center = Vector((XMax + XMin) / 2, (YMax + YMin) / 2, (ZMax + ZMin) / 2)

        self.DiagonalLength = self.wrapped.SquareExtent() ** 0.5

    def add(
        self,
        obj: Union[Tuple[float, float, float], Vector, "BoundBox"],
        tol: Optional[float] = None,
    ) -> "BoundBox":
        """Returns a modified (expanded) bounding box

        obj can be one of several things:
            1. a 3-tuple corresponding to x,y, and z amounts to add
            2. a vector, containing the x,y,z values to add
            3. another bounding box, where a new box will be created that
               encloses both.

        This bounding box is not changed.
        """

        tol = TOL if tol is None else tol  # tol = TOL (by default)

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
    def findOutsideBox2D(bb1: "BoundBox", bb2: "BoundBox") -> Optional["BoundBox"]:
        """Compares bounding boxes

        Compares bounding boxes. Returns none if neither is inside the other.
        Returns the outer one if either is outside the other.

        BoundBox.isInside works in 3d, but this is a 2d bounding box, so it
        doesn't work correctly plus, there was all kinds of rounding error in
        the built-in implementation i do not understand.
        """

        if (
            bb1.xmin < bb2.xmin
            and bb1.xmax > bb2.xmax
            and bb1.ymin < bb2.ymin
            and bb1.ymax > bb2.ymax
        ):
            return bb1

        if (
            bb2.xmin < bb1.xmin
            and bb2.xmax > bb1.xmax
            and bb2.ymin < bb1.ymin
            and bb2.ymax > bb1.ymax
        ):
            return bb2

        return None

    @classmethod
    def _fromTopoDS(
        cls: Type["BoundBox"],
        shape: TopoDS_Shape,
        tol: Optional[float] = None,
        optimal: bool = True,
    ):
        """
        Constructs a bounding box from a TopoDS_Shape
        """
        tol = TOL if tol is None else tol  # tol = TOL (by default)
        bbox = Bnd_Box()

        if optimal:
            BRepBndLib.AddOptimal_s(
                shape, bbox
            )  # this is 'exact' but expensive - not yet wrapped by PythonOCC
        else:
            mesh = BRepMesh_IncrementalMesh(shape, tol, True)
            mesh.Perform()
            # this is adds +margin but is faster
            BRepBndLib.Add_s(shape, bbox, True)

        return cls(bbox)

    def isInside(self, b2: "BoundBox") -> bool:
        """Is the provided bounding box inside this one?"""
        if (
            b2.xmin > self.xmin
            and b2.ymin > self.ymin
            and b2.zmin > self.zmin
            and b2.xmax < self.xmax
            and b2.ymax < self.ymax
            and b2.zmax < self.zmax
        ):
            return True
        else:
            return False


class Location(object):
    """Location in 3D space. Depending on usage can be absolute or relative.

    This class wraps the TopLoc_Location class from OCCT. It can be used to move Shape
    objects in both relative and absolute manner. It is the preferred type to locate objects
    in CQ.
    """

    wrapped: TopLoc_Location

    @overload
    def __init__(self) -> None:
        """Empty location with not rotation or translation with respect to the original location."""
        ...

    @overload
    def __init__(self, t: Vector) -> None:
        """Location with translation t with respect to the original location."""
        ...

    @overload
    def __init__(self, t: Plane) -> None:
        """Location corresponding to the location of the Plane t."""
        ...

    @overload
    def __init__(self, t: Plane, v: Vector) -> None:
        """Location corresponding to the angular location of the Plane t with translation v."""
        ...

    @overload
    def __init__(self, t: TopLoc_Location) -> None:
        """Location wrapping the low-level TopLoc_Location object t"""
        ...

    @overload
    def __init__(self, t: gp_Trsf) -> None:
        """Location wrapping the low-level gp_Trsf object t"""
        ...

    @overload
    def __init__(self, t: Vector, ax: Vector, angle: float) -> None:
        """Location with translation t and rotation around ax by angle
        with respect to the original location."""
        ...

    def __init__(self, *args):

        T = gp_Trsf()

        if len(args) == 0:
            pass
        elif len(args) == 1:
            t = args[0]

            if isinstance(t, Vector):
                T.SetTranslationPart(t.wrapped)
            elif isinstance(t, Plane):
                cs = gp_Ax3(t.origin.toPnt(), t.zDir.toDir(), t.xDir.toDir())
                T.SetTransformation(cs)
                T.Invert()
            elif isinstance(t, TopLoc_Location):
                self.wrapped = t
                return
            elif isinstance(t, gp_Trsf):
                T = t
            elif isinstance(t, (tuple, list)):
                raise TypeError(
                    "A tuple or list is not a valid parameter, use a Vector instead."
                )
            else:
                raise TypeError("Unexpected parameters")
        elif len(args) == 2:
            t, v = args
            cs = gp_Ax3(v.toPnt(), t.zDir.toDir(), t.xDir.toDir())
            T.SetTransformation(cs)
            T.Invert()
        else:
            t, ax, angle = args
            T.SetRotation(gp_Ax1(Vector().toPnt(), ax.toDir()), angle * math.pi / 180.0)
            T.SetTranslationPart(t.wrapped)

        self.wrapped = TopLoc_Location(T)

    @property
    def inverse(self) -> "Location":

        return Location(self.wrapped.Inverted())

    def __mul__(self, other: "Location") -> "Location":

        return Location(self.wrapped * other.wrapped)

    def toTuple(self) -> Tuple[Tuple[float, float, float], Tuple[float, float, float]]:
        """Convert the location to a translation, rotation tuple."""

        T = self.wrapped.Transformation()
        trans = T.TranslationPart()
        rot = T.GetRotation()

        rv_trans = (trans.X(), trans.Y(), trans.Z())
        rv_rot = rot.GetEulerAngles(gp_EulerSequence.gp_Extrinsic_XYZ)

        return rv_trans, rv_rot
