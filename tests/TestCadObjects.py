#system modules
import sys
import unittest
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

if __name__ == '__main__':
    unittest.main()
