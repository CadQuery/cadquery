#system modules
from __future__ import division
import sys
import unittest
from math import pi, sin, sqrt, radians
from tests import BaseTest
import FreeCAD
import Part
from copy import copy

from cadquery import *

class TestCadObjects(BaseTest):

    def testVectorConstructors(self):
        # Assert 3 ints represents x, y, z respectively
        #   (why?, this is assumed for all other assertions)
        v = Vector(1, 2, 3)
        self.assertEqual((v.x, v.y, v.z), (1, 2, 3))

        # --- Positive Cases
        # empty
        self.assertEquals(Vector(), Vector(0, 0, 0))
        # tuples
        self.assertEquals(Vector((1, 2, 3)), Vector(1, 2, 3))
        self.assertEquals(Vector((1, 2)), Vector(1, 2, 0))
        self.assertEquals(Vector((1,)), Vector(1, 0, 0))
        # lists
        self.assertEquals(Vector([1, 2, 3]), Vector(1, 2, 3))
        self.assertEquals(Vector([1, 2]), Vector(1, 2, 0))
        self.assertEquals(Vector([1]), Vector(1, 0, 0))
        # < 3 numbers
        self.assertEquals(Vector(1, 2), Vector(1, 2, 0))
        self.assertEquals(Vector(1), Vector(1, 0, 0))
        # wrappers
        self.assertEquals(Vector(Vector(1, 2, 3)), Vector(1, 2, 3))
        self.assertEquals(Vector(FreeCAD.Base.Vector(1, 2, 3)), Vector(1, 2, 3))
        # named coords
        self.assertEquals(Vector(x=1, y=2, z=3), Vector(1, 2, 3))
        self.assertEquals(Vector(x=1), Vector(1, 0, 0))
        self.assertEquals(Vector(y=2), Vector(0, 2, 0))
        self.assertEquals(Vector(z=3), Vector(0, 0, 3))

        # --- Negative Cases
        with self.assertRaises(ValueError):
            Vector('blah')  # invalid type
        with self.assertRaises(ValueError):
            Vector(1, 2, 3, 4)
        with self.assertRaises(ValueError):
            Vector((1, 2, 3, 4))
        with self.assertRaises(ValueError):
            Vector([1, 2, 3, 4])
        with self.assertRaises(ValueError):
            # mixing listed and named args not supported
            Vector(1, 2, z=3)
        with self.assertRaises(ValueError):
            # non-numeric as first parameter
            Vector(FreeCAD.Base.Vector(1, 2, 3), 1)

    def testVectorCopy(self):
        a = Vector(1, 2, 3)
        b = copy(a)
        # assert copy is equal
        self.assertEqual(a.toTuple(), (1, 2, 3))
        self.assertEqual(b.toTuple(), (1, 2, 3))
        # assert changes to original don't effect copy
        a.x = 100
        self.assertEqual(a.toTuple(), (100, 2, 3))
        self.assertEqual(b.toTuple(), (1, 2, 3))

    def testVertex(self):
        """
            Tests basic vertex functions
        """
        # Tests casting a vertex
        vc = Vertex.cast(Part.Vertex(1, 1, 1))
        self.assertEqual(1, vc.X)
        self.assertEqual(Vector, type(vc.Center()))

        # Tests vertex instantiation
        v = Vertex(Part.Vertex(1, 1, 1))
        self.assertEqual(1, v.X)
        self.assertEqual(Vector, type(v.Center()))

    def testFace(self):
        """
        Test basic face functions, cast and instantiation
        """
        edge1 = Part.makeLine((0, 0, 0), (0, 10, 0))
        edge2 = Part.makeLine((0, 10, 0), (10, 10, 0))
        edge3 = Part.makeLine((10, 10, 0), (10, 0, 0))
        edge4 = Part.makeLine((10, 0, 0), (0, 0, 0))
        wire1 = Part.Wire([edge1,edge2,edge3,edge4])
        face1 = Part.Face(wire1)

        mplanec = Face.cast(face1)
        mplane = Face(face1)

        self.assertTupleAlmostEquals((5.0, 5.0, 0.0), mplane.Center().toTuple(), 3)

    def testShapeProps(self):
        """
        Tests miscellaneous properties of the shape object
        """
        e = Shape(Part.makeCircle(2.0, FreeCAD.Base.Vector(1, 2, 3)))

        # Geometry type
        self.assertEqual(e.geomType(), 'Edge')

        # Dynamic type checking
        self.assertTrue(e.isType(e, 'Edge'))
        self.assertFalse(e.isType(None, 'Edge'))

        # Checking null objects
        self.assertFalse(e.isNull())

        # Checking for sameness
        self.assertTrue(e.isSame(e))

        # Checking for equality
        self.assertTrue(e.isEqual(e))

        # Checking for shape validity
        self.assertTrue(e.isValid())

        # Testing whether shape is closed
        self.assertTrue(e.Closed())

        # Trying to get the area of the circular edge
        with self.assertRaises(ValueError):
            e.Area()

        # Getting the area of the square face
        mplane = Face.makePlane(10.0, 10.0)
        self.assertAlmostEqual(100.0, mplane.Area(), 3)

        # Getting the center of a solid
        s = Solid.makeCylinder(10.0, 10.0)
        self.assertTupleAlmostEquals((0.0, 0.0, 5.0), s.Center().toTuple(), 3)

    def testBasicBoundingBox(self):
        v = Vertex(Part.Vertex(1, 1, 1))
        v2 = Vertex(Part.Vertex(2, 2, 2))
        self.assertEqual(BoundBox, type(v.BoundingBox()))
        self.assertEqual(BoundBox, type(v2.BoundingBox()))

        bb1 = v.BoundingBox().add(v2.BoundingBox())

        self.assertEqual(bb1.xlen, 1.0)

    def testEdgeWrapperCenter(self):
        e = Edge(Part.makeCircle(2.0, FreeCAD.Base.Vector(1, 2, 3)))

        self.assertTupleAlmostEquals((1.0, 2.0, 3.0), e.Center().toTuple(), 3)

    def testEdgeWrapperMakeCircle(self):
        halfCircleEdge = Edge.makeCircle(radius=10, pnt=(0, 0, 0), dir=(0, 0, 1), angle1=0, angle2=180)

        self.assertTupleAlmostEquals((0.0, 5.0, 0.0), halfCircleEdge.CenterOfBoundBox(0.0001).toTuple(),3)
        self.assertTupleAlmostEquals((10.0, 0.0, 0.0), halfCircleEdge.startPoint().toTuple(), 3)
        self.assertTupleAlmostEquals((-10.0, 0.0, 0.0), halfCircleEdge.endPoint().toTuple(), 3)

    def testFaceWrapperMakePlane(self):
        mplane = Face.makePlane(10,10)

        self.assertTupleAlmostEquals((0.0, 0.0, 1.0), mplane.normalAt().toTuple(), 3)

    def testCenterOfBoundBox(self):
        """
        Tests whether or not a proper geometric center can be found for an object
        """
        def cylinders(self, radius, height):
            def _cyl(pnt):
                # Inner function to build a cylinder
                return Solid.makeCylinder(radius, height, pnt)

            # Combine all the cylinders into a single compound
            r = self.eachpoint(_cyl, True).combineSolids()

            return r

        Workplane.cyl = cylinders

        # One solid in the compound
        s = Workplane("XY").pushPoints([(0.0, 0.0, 0.0)]).cyl(0.25, 0.5)
        self.assertEqual(1, len(s.val().Solids()))
        self.assertTupleAlmostEquals((0.0, 0.0, 0.25), s.val().CenterOfBoundBox().toTuple(), 2)

    def testCombinedCenterOfBoundBox(self):
        """
        Tests whether or not a proper geometric center can be found for multiple
        objects in a compound.
        """
        def cylinders(self, radius, height):
            def _cyl(pnt):
                # Inner function to build a cylinder
                return Solid.makeCylinder(radius, height, pnt)

            # Combine all the cylinders into a single compound
            r = self.eachpoint(_cyl, True).combineSolids()

            return r

        Workplane.cyl = cylinders

        # Multiple solids in the compound
        s = Workplane("XY").rect(2.0, 3.0, forConstruction=True).vertices().cyl(0.25, 0.5)
        self.assertEqual(4, len(s.val().Solids()))
        self.assertTupleAlmostEquals((0.0, 0.0, 0.25), s.val().CenterOfBoundBox().toTuple(), 2)

    def testCenter(self):
        """
        Tests finding the center of shapes and solids
        """
        circle = Workplane("XY").circle(10.0)
        cylinder = circle.extrude(10.0)

        self.assertTupleAlmostEquals((0.0, 0.0, 0.0), circle.val().Center().toTuple(), 3)
        self.assertTupleAlmostEquals((0.0, 0.0, 5.0), cylinder.val().Center().toTuple(), 3)

    def testCompoundCenter(self):
        """
        Tests whether or not a proper weighted center can be found for a compound
        """
        def cylinders(self, radius, height):
            def _cyl(pnt):
                # Inner function to build a cylinder
                return Solid.makeCylinder(radius, height, pnt)

            # Combine all the cylinders into a single compound
            r = self.eachpoint(_cyl, True).combineSolids()

            return r

        Workplane.cyl = cylinders

        # Now test. here we want weird workplane to see if the objects are transformed right
        s = Workplane("XY").rect(2.0, 3.0, forConstruction=True).vertices().cyl(0.25, 0.5)

        self.assertEqual(4, len(s.val().Solids()))
        self.assertTupleAlmostEquals((0.0, 0.0, 0.25), s.val().Center().toTuple(), 3)

    def testDot(self):
        v1 = Vector(2, 2, 2)
        v2 = Vector(1, -1, 1)
        self.assertEqual(2.0, v1.dot(v2))

    def testVectorAdd(self):
        result = Vector(1, 2, 0) + Vector(0, 0, 3)
        self.assertIsInstance(result, Vector)
        self.assertTupleAlmostEquals((1.0, 2.0, 3.0), result.toTuple(), 3)

    def testVectorArithmeticOverides(self):
        V = lambda x,y,z: Vector(x,y,z)
        self.assertEqual(V(1,2,3) + V(4,5,6), V(5,7,9))  # addition
        self.assertEqual(V(1,2,3) - V(5,4,3), V(-4,-2,0))  # subtraction
        self.assertEqual((V(1,2,3) * 2).toTuple(), (2,4,6))  # multiplication
        self.assertEqual((V(1,2,3) / 2).toTuple(), (0.5,1,1.5))  # division

    def testVectorBoolCast(self):
        # zero vector
        self.assertEqual(bool(Vector(0,0,0)), False)
        # positive axes
        self.assertEqual(bool(Vector(1,0,0)), True)
        self.assertEqual(bool(Vector(0,1,0)), True)
        self.assertEqual(bool(Vector(0,0,1)), True)
        # negative axes
        self.assertEqual(bool(Vector(-1,0,0)), True)
        self.assertEqual(bool(Vector(0,-1,0)), True)
        self.assertEqual(bool(Vector(0,0,-1)), True)

    def testVectorDivideByZero(self):
        with self.assertRaises(ZeroDivisionError):
            Vector(1, 2, 3) / 0

    def testVectorLength(self):
        calc_length = lambda v: sqrt(v.x**2 + v.y**2 + v.z**2)
        vectors = [
            Vector(0,0,0), Vector(1,2,3), Vector(-1,-5,10),
        ]
        for v in vectors:
            expected = calc_length(v)
            self.assertEqual(v.Length, expected)
            self.assertEqual(abs(v), expected)

    def testVectorSub(self):
        result = Vector(1, 2, 3) - Vector(6, 5, 4)
        self.assertIsInstance(result, Vector)
        self.assertTupleAlmostEquals((-5, -3, -1), result.toTuple())

    def testVectorEquality(self):
        v1 = Vector(1, 2, 3)
        v2 = Vector(1, 2, 3)  # same value as v1, different id
        v3 = Vector(1, 2, 4)
        self.assertEqual(v1 == v2, True)
        self.assertEqual(v1 != v2, False)
        self.assertEqual(v1 == v3, False)
        self.assertEqual(v1 != v3, True)

    def testVectorCoords(self):
        (x, y, z) = (1, 2, 3)
        v = Vector(x, y, z)
        for (coord, init_val) in (('x', x), ('y', y), ('z', z)):
            new_val = init_val + 10
            self.assertEqual(getattr(v, coord), init_val)
            setattr(v, coord, new_val)
            self.assertEqual(getattr(v, coord), new_val)
            setattr(v, coord, init_val)

    def testVectorNegative(self):
        v = Vector(1, -2, 3)
        self.assertEqual(-v, Vector(-1, 2, -3))

    def testShapeInit(self):
        """
        Tests whether a Shape object can be instantiated without
        throwing an error.
        """
        e = Shape(Part.makeCircle(2.0, FreeCAD.Base.Vector(1, 2, 3)))

    def testPlaneEqual(self):
        # default orientation
        self.assertEqual(
            Plane(origin=(0,0,0), xDir=(1,0,0), normal=(0,0,1)),
            Plane(origin=(0,0,0), xDir=(1,0,0), normal=(0,0,1))
        )
        # moved origin
        self.assertEqual(
            Plane(origin=(2,1,-1), xDir=(1,0,0), normal=(0,0,1)),
            Plane(origin=(2,1,-1), xDir=(1,0,0), normal=(0,0,1))
        )
        # moved x-axis
        self.assertEqual(
            Plane(origin=(0,0,0), xDir=(1,1,0), normal=(0,0,1)),
            Plane(origin=(0,0,0), xDir=(1,1,0), normal=(0,0,1))
        )
        # moved z-axis
        self.assertEqual(
            Plane(origin=(0,0,0), xDir=(1,0,0), normal=(0,1,1)),
            Plane(origin=(0,0,0), xDir=(1,0,0), normal=(0,1,1))
        )

    def testPlaneNotEqual(self):
        # type difference
        for value in [None, 0, 1, 'abc']:
            self.assertNotEqual(
                Plane(origin=(0,0,0), xDir=(1,0,0), normal=(0,0,1)),
                value
            )
        # origin difference
        self.assertNotEqual(
            Plane(origin=(0,0,0), xDir=(1,0,0), normal=(0,0,1)),
            Plane(origin=(0,0,1), xDir=(1,0,0), normal=(0,0,1))
        )
        # x-axis difference
        self.assertNotEqual(
            Plane(origin=(0,0,0), xDir=(1,0,0), normal=(0,0,1)),
            Plane(origin=(0,0,0), xDir=(1,1,0), normal=(0,0,1))
        )
        # z-axis difference
        self.assertNotEqual(
            Plane(origin=(0,0,0), xDir=(1,0,0), normal=(0,0,1)),
            Plane(origin=(0,0,0), xDir=(1,0,0), normal=(0,1,1))
        )

    def testTranslate(self):
        e = Shape.cast(Part.makeCircle(2.0, FreeCAD.Base.Vector(1, 2, 3)))
        e2 = e.translate(Vector(0, 0, 1))

        self.assertTupleAlmostEquals((1.0, 2.0, 4.0), e2.Center().toTuple(), 3)

    def testScale(self):
        """
        Tests scaling a shape and whether the dimensions are correct afterwards
        """
        e = Shape.cast(Part.makeCircle(2.0, FreeCAD.Base.Vector(1, 2, 3)))
        e2 = e.scale(0.5)

        self.assertAlmostEquals(2.0, e2.BoundingBox(tolerance=0.0001).xlen, 3)
        self.assertAlmostEquals(2.0, e2.BoundingBox(tolerance=0.0001).ylen, 3)

    def testCopy(self):
        """
        Tests making a copy of a shape object and whether the new one has the
        same properties as the original.
        """
        e = Shape.cast(Part.makeCircle(2.0, FreeCAD.Base.Vector(1, 2, 3)))
        e2 = e.copy()

        self.assertEquals(e.BoundingBox().xlen, e2.BoundingBox().xlen)
        self.assertEquals(e.BoundingBox().ylen, e2.BoundingBox().ylen)

    def testRuledSurface(self):
        """
        Tests making a ruled surface from two edges/wires.
        """
        edge1 = Shape(Part.makeLine((0, 0, 5), (0, 10, 5)))
        edge2 = Shape(Part.makeLine((5, 5, 0), (10, 10, 0)))

        surf1 = Face.makeRuledSurface(edge1, edge2)

        self.assertEquals(surf1.ShapeType(), 'Face')
        self.assertTrue(surf1.isValid())

    def testCut(self):
        """
        Tests cutting one face from another.
        """
        # Face 1
        edge1 = Part.makeLine((0, 0, 0), (0, 10, 0))
        edge2 = Part.makeLine((0, 10, 0), (10, 10, 0))
        edge3 = Part.makeLine((10, 10, 0), (10, 0, 0))
        edge4 = Part.makeLine((10, 0, 0), (0, 0, 0))
        wire1 = Part.Wire([edge1,edge2,edge3,edge4])
        face1 = Part.Face(wire1)
        cqFace1 = Face(face1)

        # Face 2 (face to cut out of face 1)
        edge1 = Part.makeLine((0, 0, 0), (0, 5, 0))
        edge2 = Part.makeLine((0, 5, 0), (5, 5, 0))
        edge3 = Part.makeLine((5, 5, 0), (5, 0, 0))
        edge4 = Part.makeLine((5, 0, 0), (0, 0, 0))
        wire1 = Part.Wire([edge1,edge2,edge3,edge4])
        face2 = Part.Face(wire1)
        cqFace2 = Face(face2)

        # Face resulting from cut
        cqFace3 = cqFace1.cut(cqFace2)

        self.assertEquals(len(cqFace3.Faces()), 1)
        self.assertEquals(len(cqFace3.Edges()), 6)

    def testFuse(self):
        """
        Tests fusing one face to another.
        """
        # Face 1
        edge1 = Part.makeLine((0, 0, 0), (0, 10, 0))
        edge2 = Part.makeLine((0, 10, 0), (10, 10, 0))
        edge3 = Part.makeLine((10, 10, 0), (10, 0, 0))
        edge4 = Part.makeLine((10, 0, 0), (0, 0, 0))
        wire1 = Part.Wire([edge1,edge2,edge3,edge4])
        face1 = Part.Face(wire1)
        cqFace1 = Face(face1)

        # Face 2 (face to cut out of face 1)
        edge1 = Part.makeCircle(4.0)
        wire1 = Part.Wire([edge1])
        face2 = Part.Face(wire1)
        cqFace2 = Face(face2)

        # Face resulting from fuse
        cqFace3 = cqFace1.fuse(cqFace2)

        self.assertEquals(len(cqFace3.Faces()), 3)
        self.assertEquals(len(cqFace3.Edges()), 8)

    def testIntersect(self):
        """
        Tests finding the intersection of two faces.
        """
        # Face 1
        edge1 = Part.makeLine((0, 0, 0), (0, 10, 0))
        edge2 = Part.makeLine((0, 10, 0), (10, 10, 0))
        edge3 = Part.makeLine((10, 10, 0), (10, 0, 0))
        edge4 = Part.makeLine((10, 0, 0), (0, 0, 0))
        wire1 = Part.Wire([edge1,edge2,edge3,edge4])
        face1 = Part.Face(wire1)
        cqFace1 = Face(face1)

        # Face 2 (face to cut out of face 1)
        edge1 = Part.makeCircle(4.0)
        wire1 = Part.Wire([edge1])
        face2 = Part.Face(wire1)
        cqFace2 = Face(face2)

        # Face resulting from the intersection
        cqFace3 = cqFace1.intersect(cqFace2)

        self.assertEquals(len(cqFace3.Faces()), 1)
        self.assertEquals(len(cqFace3.Edges()), 3)

    def testVertices(self):
        e = Shape.cast(Part.makeLine((0, 0, 0), (1, 1, 0)))
        self.assertEqual(2, len(e.Vertices()))

    def testWireMakeHelixDefault(self):
        (pitch, height, radius) = (1., 5., 2.)
        wire = Wire.makeHelix(pitch=pitch, height=height, radius=radius)

        edge = wire.Edges()[0]
        # Assert: helix length is correct
        # expectation, default is a cylindrical helix
        helix_horiz = (((2 * pi) * radius) * (height / pitch))
        helix_vert = height
        self.assertAlmostEqual(edge.Length(), sqrt(helix_horiz**2 + helix_vert**2), 4)

        # Assert: bounding box is accurate
        #   mainly checking that helix is in the positive Z direction.
        #   not happy with the accuracy of BoundingBox (see places=2 below), but that's out of cadquery's scope
        bb = edge.BoundingBox()
        self.assertTupleAlmostEquals((bb.xmin, bb.xmax), (-radius, radius), 2)
        self.assertTupleAlmostEquals((bb.ymin, bb.ymax), (-radius, radius), 2)
        self.assertTupleAlmostEquals((bb.zmin, bb.zmax), (0, height), 3)

    def testWireMakeHelixConical(self):
        # helix is an upside-down cone
        #   - beginning with a radius of `radius`
        #   - ending with a radius of `radius + height*sin(30)`
        (pitch, height, radius, angle) = (0.1, 5., 2., 30.)
        wire = Wire.makeHelix(
            pitch=pitch, height=height, radius=radius,
            angle=angle, lefthand=True, heightstyle=True,
        )  # left hand, just for goood measure

        edge = wire.Edges()[0]
        # Assert: bounding box is accurate
        # note: small pitch increases accuracy of bounding box, but it's still atrocious
        bb = edge.BoundingBox()
        end_radius = radius + height * sin(radians(angle))
        self.assertTupleAlmostEquals((bb.xmin, bb.xmax), (-end_radius, end_radius), 0)
        self.assertTupleAlmostEquals((bb.ymin, bb.ymax), (-end_radius, end_radius), 0)
        self.assertTupleAlmostEquals((bb.zmin, bb.zmax), (0, height), 3)


if __name__ == '__main__':
    unittest.main()
