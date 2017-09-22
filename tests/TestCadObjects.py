#system modules
import sys
import unittest
from math import pi, sin, sqrt, radians
from tests import BaseTest
import FreeCAD
import Part


from cadquery import *

class TestCadObjects(BaseTest):

    def testVectorConstructors(self):
        v1 = Vector(1, 2, 3)
        v2 = Vector((1, 2, 3))
        v3 = Vector(FreeCAD.Base.Vector(1, 2, 3))

        for v in [v1, v2, v3]:
            self.assertTupleAlmostEquals((1, 2, 3), v.toTuple(), 4)

    def testVertex(self):
        """
            Tests basic vertex functions
        """
        v = Vertex(Part.Vertex(1, 1, 1))
        self.assertEqual(1, v.X)
        self.assertEquals(Vector, type(v.Center()))

    def testBasicBoundingBox(self):
        v = Vertex(Part.Vertex(1, 1, 1))
        v2 = Vertex(Part.Vertex(2, 2, 2))
        self.assertEquals(BoundBox, type(v.BoundingBox()))
        self.assertEquals(BoundBox, type(v2.BoundingBox()))

        bb1 = v.BoundingBox().add(v2.BoundingBox())

        self.assertEquals(bb1.xlen, 1.0)

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
        pass

    def testCombinedCenterOfBoundBox(self):
        pass

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

        self.assertEquals(4, len(s.val().Solids()))
        self.assertTupleAlmostEquals((0.0, 0.0, 0.25), s.val().Center().toTuple(), 3)

    def testDot(self):
        v1 = Vector(2, 2, 2)
        v2 = Vector(1, -1, 1)
        self.assertEquals(2.0, v1.dot(v2))

    def testVectorAdd(self):
        result = Vector(1, 2, 0) + Vector(0, 0, 3)
        self.assertTupleAlmostEquals((1.0, 2.0, 3.0), result.toTuple(), 3)

    def testTranslate(self):
        e = Shape.cast(Part.makeCircle(2.0, FreeCAD.Base.Vector(1, 2, 3)))
        e2 = e.translate(Vector(0, 0, 1))

        self.assertTupleAlmostEquals((1.0, 2.0, 4.0), e2.Center().toTuple(), 3)

    def testVertices(self):
        e = Shape.cast(Part.makeLine((0, 0, 0), (1, 1, 0)))
        self.assertEquals(2, len(e.Vertices()))

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
