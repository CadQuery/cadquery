#system modules
import sys
import unittest
from tests import BaseTest
from OCC.gp import gp_Vec, gp_Pnt, gp_Ax2, gp_Circ, gp_DZ
from OCC.BRepBuilderAPI import (BRepBuilderAPI_MakeVertex,
                                BRepBuilderAPI_MakeEdge,
                                BRepBuilderAPI_MakeFace)
                                
from OCC.GC import GC_MakeCircle

from cadquery import *

class TestCadObjects(BaseTest):
    
    def _make_circle(self):
        
        circle = gp_Circ(gp_Ax2(gp_Pnt(1, 2, 3),gp_DZ()),
                         2.)
        return Shape.cast(BRepBuilderAPI_MakeEdge(circle).Edge())

    def testVectorConstructors(self):
        v1 = Vector(1, 2, 3)
        v2 = Vector((1, 2, 3))
        v3 = Vector(gp_Vec(1, 2, 3))

        for v in [v1, v2, v3]:
            self.assertTupleAlmostEquals((1, 2, 3), v.toTuple(), 4)

    def testVertex(self):
        """
            Tests basic vertex functions
        """
        v = Vertex.makeVertex(1, 1, 1)
        self.assertEqual(1, v.X)
        self.assertEquals(Vector, type(v.Center()))

    def testBasicBoundingBox(self):
        v = Vertex.makeVertex(1, 1, 1)
        v2 = Vertex.makeVertex(2, 2, 2)
        self.assertEquals(BoundBox, type(v.BoundingBox()))
        self.assertEquals(BoundBox, type(v2.BoundingBox()))

        bb1 = v.BoundingBox().add(v2.BoundingBox())

        self.assertAlmostEquals(bb1.xlen, 1.0, 1) #OCC uses some approximations

    def testEdgeWrapperCenter(self):
        e = self._make_circle()
        
        self.assertTupleAlmostEquals((1.0, 2.0, 3.0), e.Center().toTuple(), 3)

    def testEdgeWrapperMakeCircle(self):
        halfCircleEdge = Edge.makeCircle(radius=10, pnt=(0, 0, 0), dir=(0, 0, 1), angle1=0, angle2=180)       

        #self.assertTupleAlmostEquals((0.0, 5.0, 0.0), halfCircleEdge.CenterOfBoundBox(0.0001).toTuple(),3)
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
        e = Edge.makeCircle(2,(1,2,3))
        e2 = e.translate(Vector(0, 0, 1))

        self.assertTupleAlmostEquals((1.0, 2.0, 4.0), e2.Center().toTuple(), 3)

    def testVertices(self):
        e = Shape.cast(BRepBuilderAPI_MakeEdge(gp_Pnt(0, 0, 0),
                                               gp_Pnt(1, 1, 0)).Edge())
        self.assertEquals(2, len(e.Vertices()))

if __name__ == '__main__':
    unittest.main()
