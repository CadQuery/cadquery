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

        # test the case of multiple objects at the same distance
        el = c.edges("<Z").vals()
        self.assertEqual(4, len(el))

    def testMinDistance(self):
        c = CQ(makeUnitCube())

        #should select the topmost face
        self.assertEqual(1, c.faces("<Z").size())
        self.assertEqual(4, c.faces("<Z").vertices().size())

        #vertices should all be at z=1, if this is the top face
        self.assertEqual(4, len(c.faces("<Z").vertices().vals() ))
        for v in c.faces("<Z").vertices().vals():
            self.assertAlmostEqual(0.0,v.Z,3)

        # test the case of multiple objects at the same distance
        el = c.edges("<Z").vals()
        self.assertEqual(4, len(el))
        
    def testNthDistance(self):
        c = Workplane('XY').pushPoints([(-2,0),(2,0)]).box(1,1,1)
        
        #2nd face
        val = c.faces(selectors.DirectionNthSelector(Vector(1,0,0),1)).val()
        self.assertAlmostEqual(val.Center().x,-1.5)
        
        #2nd face with inversed selection vector
        val = c.faces(selectors.DirectionNthSelector(Vector(-1,0,0),1)).val()
        self.assertAlmostEqual(val.Center().x,1.5)
        
        #2nd last face
        val = c.faces(selectors.DirectionNthSelector(Vector(1,0,0),-2)).val()
        self.assertAlmostEqual(val.Center().x,1.5)
        
        #Last face
        val = c.faces(selectors.DirectionNthSelector(Vector(1,0,0),-1)).val()
        self.assertAlmostEqual(val.Center().x,2.5)
        
        #check if the selected face if normal to the specified Vector
        self.assertAlmostEqual(val.normalAt().cross(Vector(1,0,0)).Length,0.0)
        
        #repeat the test using string based selector
        
        #2nd face
        val = c.faces('>(1,0,0)[1]').val()
        self.assertAlmostEqual(val.Center().x,-1.5)
        val = c.faces('>X[1]').val()
        self.assertAlmostEqual(val.Center().x,-1.5)
        
        #2nd face with inversed selection vector
        val = c.faces('>(-1,0,0)[1]').val()
        self.assertAlmostEqual(val.Center().x,1.5)
        val = c.faces('<X[1]').val()
        self.assertAlmostEqual(val.Center().x,1.5)
        
        #2nd last face
        val = c.faces('>X[-2]').val()
        self.assertAlmostEqual(val.Center().x,1.5)
        
        #Last face
        val = c.faces('>X[-1]').val()
        self.assertAlmostEqual(val.Center().x,2.5)
        
        #check if the selected face if normal to the specified Vector
        self.assertAlmostEqual(val.normalAt().cross(Vector(1,0,0)).Length,0.0)
        
        #test selection of multiple faces with the same distance
        c = Workplane('XY')\
            .box(1,4,1,centered=(False,True,False)).faces('<Z')\
            .box(2,2,2,centered=(True,True,False)).faces('>Z')\
            .box(1,1,1,centered=(True,True,False))
        
        #select 2nd from the bottom (NB python indexing is 0-based)
        vals = c.faces('>Z[1]').vals()
        self.assertEqual(len(vals),2)
        
        val = c.faces('>Z[1]').val()
        self.assertAlmostEqual(val.Center().z,1)
        
        #do the same but by selecting 3rd from the top
        vals = c.faces('<Z[2]').vals()
        self.assertEqual(len(vals),2)
        
        val = c.faces('<Z[2]').val()
        self.assertAlmostEqual(val.Center().z,1)
        
        #do the same but by selecting 2nd last from the bottom
        vals = c.faces('<Z[-2]').vals()
        self.assertEqual(len(vals),2)
        
        val = c.faces('<Z[-2]').val()
        self.assertAlmostEqual(val.Center().z,1)
        
        #verify that <Z[-1] is equivalent to <Z
        val1 = c.faces('<Z[-1]').val()
        val2 = c.faces('<Z').val()
        self.assertTupleAlmostEquals(val1.Center().toTuple(),
                                     val2.Center().toTuple(),
                                     3)
        
        #verify that >Z[-1] is equivalent to >Z
        val1 = c.faces('>Z[-1]').val()
        val2 = c.faces('>Z').val()
        self.assertTupleAlmostEquals(val1.Center().toTuple(),
                                     val2.Center().toTuple(),
                                     3)
        
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

            # this time box points are swapped
            vl = c.vertices(selectors.BoxSelector(d[1], d[0])).vals()
            self.assertEqual(1, len(vl))
            v = vl[0]
            self.assertTupleAlmostEquals(d[2], (v.X, v.Y, v.Z), 3)

        # test multiple vertices selection
        vl = c.vertices(selectors.BoxSelector((-0.1, -0.1, 0.9),(0.1, 1.1, 1.1))).vals()
        self.assertEqual(2, len(vl))
        vl = c.vertices(selectors.BoxSelector((-0.1, -0.1, -0.1),(0.1, 1.1, 1.1))).vals()
        self.assertEqual(4, len(vl))

        # test edge selection
        test_data_edges = [
            # box point0,       box point1,       edge center
            ((0.4, -0.1, -0.1), (0.6, 0.1, 0.1), (0.5, 0.0, 0.0)),
            ((-0.1, -0.1, 0.4), (0.1, 0.1, 0.6), (0.0, 0.0, 0.5)),
            ((0.9, 0.9, 0.4), (1.1, 1.1, 0.6), (1.0, 1.0, 0.5)),
            ((0.4, 0.9, 0.9), (0.6, 1.1, 1.1,), (0.5, 1.0, 1.0))
        ]

        for d in test_data_edges:
            el = c.edges(selectors.BoxSelector(d[0], d[1])).vals()
            self.assertEqual(1, len(el))
            ec = el[0].Center()
            self.assertTupleAlmostEquals(d[2], (ec.x, ec.y, ec.z), 3)

            # test again by swapping box points
            el = c.edges(selectors.BoxSelector(d[1], d[0])).vals()
            self.assertEqual(1, len(el))
            ec = el[0].Center()
            self.assertTupleAlmostEquals(d[2], (ec.x, ec.y, ec.z), 3)

        # test multiple edge selection
        el = c.edges(selectors.BoxSelector((-0.1, -0.1, -0.1), (0.6, 0.1, 0.6))).vals()
        self.assertEqual(2, len(el))
        el = c.edges(selectors.BoxSelector((-0.1, -0.1, -0.1), (1.1, 0.1, 0.6))).vals()
        self.assertEqual(3, len(el))

        # test face selection
        test_data_faces = [
            # box point0,       box point1,       face center
            ((0.4, -0.1, 0.4), (0.6, 0.1, 0.6), (0.5, 0.0, 0.5)),
            ((0.9, 0.4, 0.4), (1.1, 0.6, 0.6), (1.0, 0.5, 0.5)),
            ((0.4, 0.4, 0.9), (0.6, 0.6, 1.1), (0.5, 0.5, 1.0)),
            ((0.4, 0.4, -0.1), (0.6, 0.6, 0.1), (0.5, 0.5, 0.0))
        ]

        for d in test_data_faces:
            fl = c.faces(selectors.BoxSelector(d[0], d[1])).vals()
            self.assertEqual(1, len(fl))
            fc = fl[0].Center()
            self.assertTupleAlmostEquals(d[2], (fc.x, fc.y, fc.z), 3)

            # test again by swapping box points
            fl = c.faces(selectors.BoxSelector(d[1], d[0])).vals()
            self.assertEqual(1, len(fl))
            fc = fl[0].Center()
            self.assertTupleAlmostEquals(d[2], (fc.x, fc.y, fc.z), 3)

        # test multiple face selection
        fl = c.faces(selectors.BoxSelector((0.4, 0.4, 0.4), (0.6, 1.1, 1.1))).vals()
        self.assertEqual(2, len(fl))
        fl = c.faces(selectors.BoxSelector((0.4, 0.4, 0.4), (1.1, 1.1, 1.1))).vals()
        self.assertEqual(3, len(fl))

        # test boundingbox option
        el = c.edges(selectors.BoxSelector((-0.1, -0.1, -0.1), (1.1, 0.1, 0.6), True)).vals()
        self.assertEqual(1, len(el))
        fl = c.faces(selectors.BoxSelector((0.4, 0.4, 0.4), (1.1, 1.1, 1.1), True)).vals()
        self.assertEqual(0, len(fl))
        fl = c.faces(selectors.BoxSelector((-0.1, 0.4, -0.1), (1.1, 1.1, 1.1), True)).vals()
        self.assertEqual(1, len(fl))

    def testAndSelector(self):
        c = CQ(makeUnitCube())

        S = selectors.StringSyntaxSelector
        BS = selectors.BoxSelector

        el = c.edges(selectors.AndSelector(S('|X'), BS((-2,-2,0.1), (2,2,2)))).vals()
        self.assertEqual(2, len(el))

        # test 'and' (intersection) operator
        el = c.edges(S('|X') & BS((-2,-2,0.1), (2,2,2))).vals()
        self.assertEqual(2, len(el))
        
        # test using extended string syntax
        v = c.vertices(">X and >Y").vals()
        self.assertEqual(2, len(v))

    def testSumSelector(self):
        c = CQ(makeUnitCube())

        S = selectors.StringSyntaxSelector

        fl = c.faces(selectors.SumSelector(S(">Z"), S("<Z"))).vals()
        self.assertEqual(2, len(fl))
        el = c.edges(selectors.SumSelector(S("|X"), S("|Y"))).vals()
        self.assertEqual(8, len(el))

        # test the sum operator
        fl = c.faces(S(">Z") + S("<Z")).vals()
        self.assertEqual(2, len(fl))
        el = c.edges(S("|X") + S("|Y")).vals()
        self.assertEqual(8, len(el))
        
        # test using extended string syntax
        fl = c.faces(">Z or <Z").vals()
        self.assertEqual(2, len(fl))
        el = c.edges("|X or |Y").vals()
        self.assertEqual(8, len(el))

    def testSubtractSelector(self):
        c = CQ(makeUnitCube())

        S = selectors.StringSyntaxSelector

        fl = c.faces(selectors.SubtractSelector(S("#Z"), S(">X"))).vals()
        self.assertEqual(3, len(fl))

        # test the subtract operator
        fl = c.faces(S("#Z") - S(">X")).vals()
        self.assertEqual(3, len(fl))
        
        # test using extended string syntax
        fl = c.faces("#Z exc >X").vals()
        self.assertEqual(3, len(fl))

    def testInverseSelector(self):
        c = CQ(makeUnitCube())

        S = selectors.StringSyntaxSelector

        fl = c.faces(selectors.InverseSelector(S('>Z'))).vals()
        self.assertEqual(5, len(fl))
        el = c.faces('>Z').edges(selectors.InverseSelector(S('>X'))).vals()
        self.assertEqual(3, len(el))

        # test invert operator
        fl = c.faces(-S('>Z')).vals()
        self.assertEqual(5, len(fl))
        el = c.faces('>Z').edges(-S('>X')).vals()
        self.assertEqual(3, len(el))
        
        # test using extended string syntax
        fl = c.faces('not >Z').vals()
        self.assertEqual(5, len(fl))
        el = c.faces('>Z').edges('not >X').vals()
        self.assertEqual(3, len(el))
        
    def testComplexStringSelector(self):
        c = CQ(makeUnitCube())
        
        v = c.vertices('(>X and >Y) or (<X and <Y)').vals()
        self.assertEqual(4, len(v))
        

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
        
    def testGrammar(self):
        """
        Test if reasonable string selector expressions parse without an error
        """
        
        gram = selectors._expression_grammar

        expressions = ['+X ',
                       '-Y',
                       '|(1,0,0)',
                       '#(1.,1.4114,-0.532)',
                       '%Plane',
                       '>XZ',
                       '<Z[-2]',
                       '>(1,4,55.)[20]',
                       '|XY',
                       '<YZ[0]',
                       'front',
                       'back',
                       'left',
                       'right',
                       'top',
                       'bottom',
                       'not |(1,1,0) and >(0,0,1) or XY except >(1,1,1)[-1]',
                       '(not |(1,1,0) and >(0,0,1)) exc XY and (Z or X)',
                       'not ( <X or >X or <Y or >Y )']

        for e in expressions: gram.parseString(e,parseAll=True)
        