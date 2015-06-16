__author__ = 'dcowden'

"""
    Tests for CadQuery Selectors

    These tests do not construct any solids, they test only selectors that query
    an existing solid

"""

import math
import unittest,sys
import os.path

#my modules
from tests import BaseTest,makeUnitCube,makeUnitSquareWire
from cadquery import *
from cadquery import selectors

class TestCQSelectors(BaseTest):


    def testWorkplaneCenter(self):
        "Test Moving workplane center"
        s = Workplane(Plane.XY())

        #current point and world point should be equal
        self.assertTupleAlmostEquals((0.0,0.0,0.0),s.plane.origin.toTuple(),3)

        #move origin and confirm center moves
        s.center(-2.0,-2.0)

        #current point should be 0,0, but

        self.assertTupleAlmostEquals((-2.0,-2.0,0.0),s.plane.origin.toTuple(),3)


    def testVertices(self):
        t = makeUnitSquareWire() # square box
        c = CQ(t)

        self.assertEqual(4,c.vertices().size() )
        self.assertEqual(4,c.edges().size() )
        self.assertEqual(0,c.vertices().edges().size() ) #no edges on any vertices
        self.assertEqual(4,c.edges().vertices().size() ) #but selecting all edges still yields all vertices
        self.assertEqual(1,c.wires().size()) #just one wire
        self.assertEqual(0,c.faces().size())
        self.assertEqual(0,c.vertices().faces().size()) #odd combinations all work but yield no results
        self.assertEqual(0,c.edges().faces().size())
        self.assertEqual(0,c.edges().vertices().faces().size())

    def testEnd(self):
        c = CQ(makeUnitSquareWire())
        self.assertEqual(4,c.vertices().size() ) #4 because there are 4 vertices
        self.assertEqual(1,c.vertices().end().size() ) #1 because we started with 1 wire

    def testAll(self):
        "all returns a list of CQ objects, so that you can iterate over them individually"
        c = CQ(makeUnitCube())
        self.assertEqual(6,c.faces().size())
        self.assertEqual(6,len(c.faces().all()))
        self.assertEqual(4,c.faces().all()[0].vertices().size() )

    def testFirst(self):
        c = CQ( makeUnitCube())
        self.assertEqual(type(c.vertices().first().val()),Vertex)
        self.assertEqual(type(c.vertices().first().first().first().val()),Vertex)

    def testCompounds(self):
        c = CQ(makeUnitSquareWire())
        self.assertEqual(0,c.compounds().size() )
        self.assertEqual(0,c.shells().size() )
        self.assertEqual(0,c.solids().size() )

    def testSolid(self):
        c = CQ(makeUnitCube())
        #make sure all the counts are right for a cube
        self.assertEqual(1,c.solids().size() )
        self.assertEqual(6,c.faces().size() )
        self.assertEqual(12,c.edges().size())
        self.assertEqual(8,c.vertices().size() )
        self.assertEqual(0,c.compounds().size())

        #now any particular face should result in 4 edges and four vertices
        self.assertEqual(4,c.faces().first().edges().size() )
        self.assertEqual(1,c.faces().first().size() )
        self.assertEqual(4,c.faces().first().vertices().size() )

        self.assertEqual(4,c.faces().last().edges().size() )



    def testFaceTypesFilter(self):
        "Filters by face type"
        c = CQ(makeUnitCube())
        self.assertEqual(c.faces().size(), c.faces('%PLANE').size())
        self.assertEqual(c.faces().size(), c.faces('%plane').size())
        self.assertEqual(0, c.faces('%sphere').size())
        self.assertEqual(0, c.faces('%cone').size())
        self.assertEqual(0, c.faces('%SPHERE').size())

    def testPerpendicularDirFilter(self):
        c = CQ(makeUnitCube())

        self.assertEqual(8,c.edges("#Z").size() ) #8 edges are perp. to z
        self.assertEqual(4, c.faces("#Z").size()) #4 faces are perp to z too!

    def testFaceDirFilter(self):
        c = CQ(makeUnitCube())
        #a cube has one face in each direction
        self.assertEqual(1, c.faces("+Z").size())
        self.assertEqual(1, c.faces("-Z").size())
        self.assertEqual(1, c.faces("+X").size())
        self.assertEqual(1, c.faces("X").size())     #should be same as +X
        self.assertEqual(1, c.faces("-X").size())
        self.assertEqual(1, c.faces("+Y").size())
        self.assertEqual(1, c.faces("-Y").size())
        self.assertEqual(0, c.faces("XY").size())

    def testParallelPlaneFaceFilter(self):
        c = CQ(makeUnitCube())

        #faces parallel to Z axis
        self.assertEqual(2, c.faces("|Z").size())
        #TODO: provide short names for ParallelDirSelector
        self.assertEqual(2, c.faces(selectors.ParallelDirSelector(Vector((0,0,1)))).size()) #same thing as above
        self.assertEqual(2, c.faces(selectors.ParallelDirSelector(Vector((0,0,-1)))).size()) #same thing as above

        #just for fun, vertices on faces parallel to z
        self.assertEqual(8, c.faces("|Z").vertices().size())

    def testParallelEdgeFilter(self):
        c = CQ(makeUnitCube())
        self.assertEqual(4, c.edges("|Z").size())
        self.assertEqual(4, c.edges("|X").size())
        self.assertEqual(4, c.edges("|Y").size())

    def testMaxDistance(self):
        c = CQ(makeUnitCube())

        #should select the topmost face
        self.assertEqual(1, c.faces(">Z").size())
        self.assertEqual(4, c.faces(">Z").vertices().size())

        #vertices should all be at z=1, if this is the top face
        self.assertEqual(4, len(c.faces(">Z").vertices().vals() ))
        for v in c.faces(">Z").vertices().vals():
            self.assertAlmostEqual(1.0,v.Z,3)

    def testMinDistance(self):
        c = CQ(makeUnitCube())

        #should select the topmost face
        self.assertEqual(1, c.faces("<Z").size())
        self.assertEqual(4, c.faces("<Z").vertices().size())

        #vertices should all be at z=1, if this is the top face
        self.assertEqual(4, len(c.faces("<Z").vertices().vals() ))
        for v in c.faces("<Z").vertices().vals():
            self.assertAlmostEqual(0.0,v.Z,3)

    def testNearestTo(self):
        c = CQ(makeUnitCube())

        #nearest vertex to origin is (0,0,0)
        t = (0.1,0.1,0.1)

        v = c.vertices(selectors.NearestToPointSelector(t)).vals()[0]
        self.assertTupleAlmostEquals((0.0,0.0,0.0),(v.X,v.Y,v.Z),3)

        t = (0.1,0.1,0.2)
        #nearest edge is the vertical side edge, 0,0,0 -> 0,0,1
        e = c.edges(selectors.NearestToPointSelector(t)).vals()[0]
        v = c.edges(selectors.NearestToPointSelector(t)).vertices().vals()
        self.assertEqual(2,len(v))

        #nearest solid is myself
        s = c.solids(selectors.NearestToPointSelector(t)).vals()
        self.assertEqual(1,len(s))

    def testBox(self):
        c = CQ(makeUnitCube())

        # test vertice selection
        test_data_vertices = [
            # box point0,       box point1,     selected vertice
            ((0.9, 0.9, 0.9), (1.1, 1.1, 1.1), (1.0, 1.0, 1.0)),
            ((-0.1, 0.9, 0.9), (0.9, 1.1, 1.1), (0.0, 1.0, 1.0)),
            ((-0.1, -0.1, 0.9), (0.1, 0.1, 1.1), (0.0, 0.0, 1.0)),
            ((-0.1, -0.1, -0.1), (0.1, 0.1, 0.1), (0.0, 0.0, 0.0)),
            ((0.9, -0.1, -0.1), (1.1, 0.1, 0.1), (1.0, 0.0, 0.0)),
            ((0.9, 0.9, -0.1), (1.1, 1.1, 0.1), (1.0, 1.0, 0.0)),
            ((-0.1, 0.9, -0.1), (0.1, 1.1, 0.1), (0.0, 1.0, 0.0)),
            ((0.9, -0.1, 0.9), (1.1, 0.1, 1.1), (1.0, 0.0, 1.0))
        ]

        for d in test_data_vertices:
            vl = c.vertices(selectors.BoxSelector(d[0], d[1])).vals()
            self.assertEqual(1, len(vl))
            v = vl[0]
            self.assertTupleAlmostEquals(d[2], (v.X, v.Y, v.Z), 3)

    def testFaceCount(self):
        c = CQ(makeUnitCube())
        self.assertEqual( 6, c.faces().size() )
        self.assertEqual( 2, c.faces("|Z").size() )

    def testVertexFilter(self):
        "test selecting vertices on a face"
        c = CQ(makeUnitCube())

        #TODO: filters work ok, but they are in global coordinates which sux. it would be nice
        #if they were available in coordinates local to the selected face

        v2 = c.faces("+Z").vertices("<XY")
        self.assertEqual(1,v2.size() ) #another way
        #make sure the vertex is the right one

        self.assertTupleAlmostEquals((0.0,0.0,1.0),v2.val().toTuple() ,3)
