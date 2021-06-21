# system modules
import math
import unittest
from tests import BaseTest
from OCP.gp import gp_Vec, gp_Pnt, gp_Ax2, gp_Circ, gp_Elips, gp, gp_XYZ, gp_Trsf
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeEdge

from cadquery import *

DEG2RAD = math.pi / 180
RAD2DEG = 180 / math.pi


class TestCadObjects(BaseTest):
    def _make_circle(self):

        circle = gp_Circ(gp_Ax2(gp_Pnt(1, 2, 3), gp.DZ_s()), 2.0)
        return Shape.cast(BRepBuilderAPI_MakeEdge(circle).Edge())

    def _make_ellipse(self):

        ellipse = gp_Elips(gp_Ax2(gp_Pnt(1, 2, 3), gp.DZ_s()), 4.0, 2.0)
        return Shape.cast(BRepBuilderAPI_MakeEdge(ellipse).Edge())

    def testVectorConstructors(self):
        v1 = Vector(1, 2, 3)
        v2 = Vector((1, 2, 3))
        v3 = Vector(gp_Vec(1, 2, 3))
        v4 = Vector([1, 2, 3])
        v5 = Vector(gp_XYZ(1, 2, 3))

        for v in [v1, v2, v3, v4, v5]:
            self.assertTupleAlmostEquals((1, 2, 3), v.toTuple(), 4)

        v6 = Vector((1, 2))
        v7 = Vector([1, 2])
        v8 = Vector(1, 2)

        for v in [v6, v7, v8]:
            self.assertTupleAlmostEquals((1, 2, 0), v.toTuple(), 4)

        v9 = Vector()
        self.assertTupleAlmostEquals((0, 0, 0), v9.toTuple(), 4)

        v9.x = 1.0
        v9.y = 2.0
        v9.z = 3.0
        self.assertTupleAlmostEquals((1, 2, 3), (v9.x, v9.y, v9.z), 4)

    def testVertex(self):
        """
            Tests basic vertex functions
        """
        v = Vertex.makeVertex(1, 1, 1)
        self.assertEqual(1, v.X)
        self.assertEqual(Vector, type(v.Center()))

    def testBasicBoundingBox(self):
        v = Vertex.makeVertex(1, 1, 1)
        v2 = Vertex.makeVertex(2, 2, 2)
        self.assertEqual(BoundBox, type(v.BoundingBox()))
        self.assertEqual(BoundBox, type(v2.BoundingBox()))

        bb1 = v.BoundingBox().add(v2.BoundingBox())

        # OCC uses some approximations
        self.assertAlmostEqual(bb1.xlen, 1.0, 1)

    def testEdgeWrapperCenter(self):
        e = self._make_circle()

        self.assertTupleAlmostEquals((1.0, 2.0, 3.0), e.Center().toTuple(), 3)

    def testEdgeWrapperEllipseCenter(self):
        e = self._make_ellipse()
        w = Wire.assembleEdges([e])
        self.assertTupleAlmostEquals(
            (1.0, 2.0, 3.0), Face.makeFromWires(w).Center().toTuple(), 3
        )

    def testEdgeWrapperMakeCircle(self):
        halfCircleEdge = Edge.makeCircle(
            radius=10, pnt=(0, 0, 0), dir=(0, 0, 1), angle1=0, angle2=180
        )

        # self.assertTupleAlmostEquals((0.0, 5.0, 0.0), halfCircleEdge.CenterOfBoundBox(0.0001).toTuple(),3)
        self.assertTupleAlmostEquals(
            (10.0, 0.0, 0.0), halfCircleEdge.startPoint().toTuple(), 3
        )
        self.assertTupleAlmostEquals(
            (-10.0, 0.0, 0.0), halfCircleEdge.endPoint().toTuple(), 3
        )

    def testEdgeWrapperMakeTangentArc(self):
        tangent_arc = Edge.makeTangentArc(
            Vector(1, 1),  # starts at 1, 1
            Vector(0, 1),  # tangent at start of arc is in the +y direction
            Vector(2, 1),  # arc curves 180 degrees and ends at 2, 1
        )
        self.assertTupleAlmostEquals((1, 1, 0), tangent_arc.startPoint().toTuple(), 3)
        self.assertTupleAlmostEquals((2, 1, 0), tangent_arc.endPoint().toTuple(), 3)
        self.assertTupleAlmostEquals(
            (0, 1, 0), tangent_arc.tangentAt(locationParam=0).toTuple(), 3
        )
        self.assertTupleAlmostEquals(
            (1, 0, 0), tangent_arc.tangentAt(locationParam=0.5).toTuple(), 3
        )
        self.assertTupleAlmostEquals(
            (0, -1, 0), tangent_arc.tangentAt(locationParam=1).toTuple(), 3
        )

    def testEdgeWrapperMakeEllipse1(self):
        # Check x_radius > y_radius
        x_radius, y_radius = 20, 10
        angle1, angle2 = -75.0, 90.0
        arcEllipseEdge = Edge.makeEllipse(
            x_radius=x_radius,
            y_radius=y_radius,
            pnt=(0, 0, 0),
            dir=(0, 0, 1),
            angle1=angle1,
            angle2=angle2,
        )

        start = (
            x_radius * math.cos(angle1 * DEG2RAD),
            y_radius * math.sin(angle1 * DEG2RAD),
            0.0,
        )
        end = (
            x_radius * math.cos(angle2 * DEG2RAD),
            y_radius * math.sin(angle2 * DEG2RAD),
            0.0,
        )
        self.assertTupleAlmostEquals(start, arcEllipseEdge.startPoint().toTuple(), 3)
        self.assertTupleAlmostEquals(end, arcEllipseEdge.endPoint().toTuple(), 3)

    def testEdgeWrapperMakeEllipse2(self):
        # Check x_radius < y_radius
        x_radius, y_radius = 10, 20
        angle1, angle2 = 0.0, 45.0
        arcEllipseEdge = Edge.makeEllipse(
            x_radius=x_radius,
            y_radius=y_radius,
            pnt=(0, 0, 0),
            dir=(0, 0, 1),
            angle1=angle1,
            angle2=angle2,
        )

        start = (
            x_radius * math.cos(angle1 * DEG2RAD),
            y_radius * math.sin(angle1 * DEG2RAD),
            0.0,
        )
        end = (
            x_radius * math.cos(angle2 * DEG2RAD),
            y_radius * math.sin(angle2 * DEG2RAD),
            0.0,
        )
        self.assertTupleAlmostEquals(start, arcEllipseEdge.startPoint().toTuple(), 3)
        self.assertTupleAlmostEquals(end, arcEllipseEdge.endPoint().toTuple(), 3)

    def testEdgeWrapperMakeCircleWithEllipse(self):
        # Check x_radius == y_radius
        x_radius, y_radius = 20, 20
        angle1, angle2 = 15.0, 60.0
        arcEllipseEdge = Edge.makeEllipse(
            x_radius=x_radius,
            y_radius=y_radius,
            pnt=(0, 0, 0),
            dir=(0, 0, 1),
            angle1=angle1,
            angle2=angle2,
        )

        start = (
            x_radius * math.cos(angle1 * DEG2RAD),
            y_radius * math.sin(angle1 * DEG2RAD),
            0.0,
        )
        end = (
            x_radius * math.cos(angle2 * DEG2RAD),
            y_radius * math.sin(angle2 * DEG2RAD),
            0.0,
        )
        self.assertTupleAlmostEquals(start, arcEllipseEdge.startPoint().toTuple(), 3)
        self.assertTupleAlmostEquals(end, arcEllipseEdge.endPoint().toTuple(), 3)

    def testFaceWrapperMakePlane(self):
        mplane = Face.makePlane(10, 10)

        self.assertTupleAlmostEquals((0.0, 0.0, 1.0), mplane.normalAt().toTuple(), 3)

    def testCenterOfBoundBox(self):
        pass

    def testCombinedCenterOfBoundBox(self):
        pass

    def testCompoundCenter(self):
        """
        Tests whether or not a proper weighted center can be found for a compound
        """

        def cylinders(self, radius, height):

            c = Solid.makeCylinder(radius, height, Vector())

            # Combine all the cylinders into a single compound
            r = self.eachpoint(lambda loc: c.located(loc), True).combineSolids()

            return r

        Workplane.cyl = cylinders

        # Now test. here we want weird workplane to see if the objects are transformed right
        s = (
            Workplane("XY")
            .rect(2.0, 3.0, forConstruction=True)
            .vertices()
            .cyl(0.25, 0.5)
        )

        self.assertEqual(4, len(s.val().Solids()))
        self.assertTupleAlmostEquals((0.0, 0.0, 0.25), s.val().Center().toTuple(), 3)

    def testDot(self):
        v1 = Vector(2, 2, 2)
        v2 = Vector(1, -1, 1)
        self.assertEqual(2.0, v1.dot(v2))

    def testVectorAdd(self):
        result = Vector(1, 2, 0) + Vector(0, 0, 3)
        self.assertTupleAlmostEquals((1.0, 2.0, 3.0), result.toTuple(), 3)

    def testVectorOperators(self):
        result = Vector(1, 1, 1) + Vector(2, 2, 2)
        self.assertEqual(Vector(3, 3, 3), result)

        result = Vector(1, 2, 3) - Vector(3, 2, 1)
        self.assertEqual(Vector(-2, 0, 2), result)

        result = Vector(1, 2, 3) * 2
        self.assertEqual(Vector(2, 4, 6), result)

        result = Vector(2, 4, 6) / 2
        self.assertEqual(Vector(1, 2, 3), result)

        self.assertEqual(Vector(-1, -1, -1), -Vector(1, 1, 1))

        self.assertEqual(0, abs(Vector(0, 0, 0)))
        self.assertEqual(1, abs(Vector(1, 0, 0)))
        self.assertEqual((1 + 4 + 9) ** 0.5, abs(Vector(1, 2, 3)))

    def testVectorEquals(self):
        a = Vector(1, 2, 3)
        b = Vector(1, 2, 3)
        c = Vector(1, 2, 3.000001)
        self.assertEqual(a, b)
        self.assertEqual(a, c)

    def testVectorProject(self):
        """
        Test method to project vector to plane.
        """
        decimal_places = 9

        normal = Vector(1, 2, 3)
        base = Vector(5, 7, 9)
        x_dir = Vector(1, 0, 0)

        # test passing Plane object
        point = Vector(10, 11, 12).projectToPlane(Plane(base, x_dir, normal))
        self.assertTupleAlmostEquals(
            point.toTuple(), (59 / 7, 55 / 7, 51 / 7), decimal_places
        )

    def testMatrixCreationAndAccess(self):
        def matrix_vals(m):
            return [[m[r, c] for c in range(4)] for r in range(4)]

        # default constructor creates a 4x4 identity matrix
        m = Matrix()
        identity = [
            [1.0, 0.0, 0.0, 0.0],
            [0.0, 1.0, 0.0, 0.0],
            [0.0, 0.0, 1.0, 0.0],
            [0.0, 0.0, 0.0, 1.0],
        ]
        self.assertEqual(identity, matrix_vals(m))

        vals4x4 = [
            [1.0, 0.0, 0.0, 1.0],
            [0.0, 1.0, 0.0, 2.0],
            [0.0, 0.0, 1.0, 3.0],
            [0.0, 0.0, 0.0, 1.0],
        ]
        vals4x4_tuple = tuple(tuple(r) for r in vals4x4)

        # test constructor with 16-value input
        m = Matrix(vals4x4)
        self.assertEqual(vals4x4, matrix_vals(m))
        m = Matrix(vals4x4_tuple)
        self.assertEqual(vals4x4, matrix_vals(m))

        # test constructor with 12-value input (the last 4 are an implied
        # [0,0,0,1])
        m = Matrix(vals4x4[:3])
        self.assertEqual(vals4x4, matrix_vals(m))
        m = Matrix(vals4x4_tuple[:3])
        self.assertEqual(vals4x4, matrix_vals(m))

        # Test 16-value input with invalid values for the last 4
        invalid = [
            [1.0, 0.0, 0.0, 1.0],
            [0.0, 1.0, 0.0, 2.0],
            [0.0, 0.0, 1.0, 3.0],
            [1.0, 2.0, 3.0, 4.0],
        ]
        with self.assertRaises(ValueError):
            Matrix(invalid)

        # Test input with invalid size / nested types
        with self.assertRaises(TypeError):
            Matrix([[1, 2, 3, 4], [1, 2, 3], [1, 2, 3, 4]])
        with self.assertRaises(TypeError):
            Matrix([1, 2, 3])

        # Invalid sub-type
        with self.assertRaises(TypeError):
            Matrix([[1, 2, 3, 4], "abc", [1, 2, 3, 4]])

        # test out-of-bounds access
        m = Matrix()
        with self.assertRaises(IndexError):
            m[0, 4]
        with self.assertRaises(IndexError):
            m[4, 0]
        with self.assertRaises(IndexError):
            m["ab"]

        # test __repr__ and __str__ methods
        m = Matrix(vals4x4)
        mRepr = "Matrix([[1.0, 0.0, 0.0, 1.0],\n        [0.0, 1.0, 0.0, 2.0],\n        [0.0, 0.0, 1.0, 3.0],\n        [0.0, 0.0, 0.0, 1.0]])"
        mStr = "Matrix: [[1.0, 0.0, 0.0, 1.0],\n         [0.0, 1.0, 0.0, 2.0],\n         [0.0, 0.0, 1.0, 3.0],\n         [0.0, 0.0, 0.0, 1.0]]"
        self.assertEqual(repr(m),mRepr)
        self.assertEqual(str(m),mStr)
        self.assertEqual(str(eval(repr(m))),mStr)

    def testTranslate(self):
        e = Edge.makeCircle(2, (1, 2, 3))
        e2 = e.translate(Vector(0, 0, 1))

        self.assertTupleAlmostEquals((1.0, 2.0, 4.0), e2.Center().toTuple(), 3)

    def testVertices(self):
        e = Shape.cast(BRepBuilderAPI_MakeEdge(gp_Pnt(0, 0, 0), gp_Pnt(1, 1, 0)).Edge())
        self.assertEqual(2, len(e.Vertices()))

    def testPlaneEqual(self):
        # default orientation
        self.assertEqual(
            Plane(origin=(0, 0, 0), xDir=(1, 0, 0), normal=(0, 0, 1)),
            Plane(origin=(0, 0, 0), xDir=(1, 0, 0), normal=(0, 0, 1)),
        )
        # moved origin
        self.assertEqual(
            Plane(origin=(2, 1, -1), xDir=(1, 0, 0), normal=(0, 0, 1)),
            Plane(origin=(2, 1, -1), xDir=(1, 0, 0), normal=(0, 0, 1)),
        )
        # moved x-axis
        self.assertEqual(
            Plane(origin=(0, 0, 0), xDir=(1, 1, 0), normal=(0, 0, 1)),
            Plane(origin=(0, 0, 0), xDir=(1, 1, 0), normal=(0, 0, 1)),
        )
        # moved z-axis
        self.assertEqual(
            Plane(origin=(0, 0, 0), xDir=(1, 0, 0), normal=(0, 1, 1)),
            Plane(origin=(0, 0, 0), xDir=(1, 0, 0), normal=(0, 1, 1)),
        )

    def testPlaneNotEqual(self):
        # type difference
        for value in [None, 0, 1, "abc"]:
            self.assertNotEqual(
                Plane(origin=(0, 0, 0), xDir=(1, 0, 0), normal=(0, 0, 1)), value
            )
        # origin difference
        self.assertNotEqual(
            Plane(origin=(0, 0, 0), xDir=(1, 0, 0), normal=(0, 0, 1)),
            Plane(origin=(0, 0, 1), xDir=(1, 0, 0), normal=(0, 0, 1)),
        )
        # x-axis difference
        self.assertNotEqual(
            Plane(origin=(0, 0, 0), xDir=(1, 0, 0), normal=(0, 0, 1)),
            Plane(origin=(0, 0, 0), xDir=(1, 1, 0), normal=(0, 0, 1)),
        )
        # z-axis difference
        self.assertNotEqual(
            Plane(origin=(0, 0, 0), xDir=(1, 0, 0), normal=(0, 0, 1)),
            Plane(origin=(0, 0, 0), xDir=(1, 0, 0), normal=(0, 1, 1)),
        )

    def testLocation(self):

        # Vector
        loc1 = Location(Vector(0, 0, 1))

        T = loc1.wrapped.Transformation().TranslationPart()
        self.assertTupleAlmostEquals((T.X(), T.Y(), T.Z()), (0, 0, 1), 6)

        # rotation + translation
        loc2 = Location(Vector(0, 0, 1), Vector(0, 0, 1), 45)

        angle = loc2.wrapped.Transformation().GetRotation().GetRotationAngle() * RAD2DEG
        self.assertAlmostEqual(45, angle)

        # gp_Trsf
        T = gp_Trsf()
        T.SetTranslation(gp_Vec(0, 0, 1))
        loc3 = Location(T)

        assert (
            loc1.wrapped.Transformation().TranslationPart().Z()
            == loc3.wrapped.Transformation().TranslationPart().Z()
        )

    def testEdgeWrapperRadius(self):

        # get a radius from a simple circle
        e0 = Edge.makeCircle(2.4)
        self.assertAlmostEqual(e0.radius(), 2.4)

        # radius of an arc
        e1 = Edge.makeCircle(1.8, pnt=(5, 6, 7), dir=(1, 1, 1), angle1=20, angle2=30)
        self.assertAlmostEqual(e1.radius(), 1.8)

        # test value errors
        e2 = Edge.makeEllipse(10, 20)
        with self.assertRaises(ValueError):
            e2.radius()

        # radius from a wire
        w0 = Wire.makeCircle(10, Vector(1, 2, 3), (-1, 0, 1))
        self.assertAlmostEqual(w0.radius(), 10)

        # radius from a wire with multiple edges
        rad = 2.3
        pnt = (7, 8, 9)
        direction = (1, 0.5, 0.1)
        w1 = Wire.assembleEdges(
            [
                Edge.makeCircle(rad, pnt, direction, 0, 10),
                Edge.makeCircle(rad, pnt, direction, 10, 25),
                Edge.makeCircle(rad, pnt, direction, 25, 230),
            ]
        )
        self.assertAlmostEqual(w1.radius(), rad)

        # test value error from wire
        w2 = Wire.makePolygon([Vector(-1, 0, 0), Vector(0, 1, 0), Vector(1, -1, 0),])
        with self.assertRaises(ValueError):
            w2.radius()

        # (I think) the radius of a wire is the radius of it's first edge.
        # Since this is stated in the docstring better make sure.
        no_rad = Wire.assembleEdges(
            [
                Edge.makeLine(Vector(0, 0, 0), Vector(0, 1, 0)),
                Edge.makeCircle(1.0, angle1=90, angle2=270),
            ]
        )
        with self.assertRaises(ValueError):
            no_rad.radius()
        yes_rad = Wire.assembleEdges(
            [
                Edge.makeCircle(1.0, angle1=90, angle2=270),
                Edge.makeLine(Vector(0, -1, 0), Vector(0, 1, 0)),
            ]
        )
        self.assertAlmostEqual(yes_rad.radius(), 1.0)
        many_rad = Wire.assembleEdges(
            [
                Edge.makeCircle(1.0, angle1=0, angle2=180),
                Edge.makeCircle(3.0, pnt=Vector(2, 0, 0), angle1=180, angle2=359),
            ]
        )
        self.assertAlmostEqual(many_rad.radius(), 1.0)


if __name__ == "__main__":
    unittest.main()
