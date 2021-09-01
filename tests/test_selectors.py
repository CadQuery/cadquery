__author__ = "dcowden"

"""
    Tests for CadQuery Selectors

    These tests do not construct any solids, they test only selectors that query
    an existing solid

"""

import math
import unittest
import sys
import os.path

# my modules
from tests import BaseTest, makeUnitCube, makeUnitSquareWire
from cadquery import *
from cadquery import selectors


class TestCQSelectors(BaseTest):
    def testWorkplaneCenter(self):
        "Test Moving workplane center"
        s = Workplane(Plane.XY())

        # current point and world point should be equal
        self.assertTupleAlmostEquals((0.0, 0.0, 0.0), s.plane.origin.toTuple(), 3)

        # move origin and confirm center moves
        s = s.center(-2.0, -2.0)

        # current point should be 0,0, but

        self.assertTupleAlmostEquals((-2.0, -2.0, 0.0), s.plane.origin.toTuple(), 3)

    def testVertices(self):
        t = makeUnitSquareWire()  # square box
        c = CQ(t)

        self.assertEqual(4, c.vertices().size())
        self.assertEqual(4, c.edges().size())
        self.assertEqual(0, c.vertices().edges().size())  # no edges on any vertices
        # but selecting all edges still yields all vertices
        self.assertEqual(4, c.edges().vertices().size())
        self.assertEqual(1, c.wires().size())  # just one wire
        self.assertEqual(0, c.faces().size())
        # odd combinations all work but yield no results
        self.assertEqual(0, c.vertices().faces().size())
        self.assertEqual(0, c.edges().faces().size())
        self.assertEqual(0, c.edges().vertices().faces().size())

    def testEnd(self):
        c = CQ(makeUnitSquareWire())
        # 4 because there are 4 vertices
        self.assertEqual(4, c.vertices().size())
        # 1 because we started with 1 wire
        self.assertEqual(1, c.vertices().end().size())

    def testAll(self):
        "all returns a list of CQ objects, so that you can iterate over them individually"
        c = CQ(makeUnitCube())
        self.assertEqual(6, c.faces().size())
        self.assertEqual(6, len(c.faces().all()))
        self.assertEqual(4, c.faces().all()[0].vertices().size())

    def testFirst(self):
        c = CQ(makeUnitCube())
        self.assertEqual(type(c.vertices().first().val()), Vertex)
        self.assertEqual(type(c.vertices().first().first().first().val()), Vertex)

    def testCompounds(self):
        c = CQ(makeUnitSquareWire())
        self.assertEqual(0, c.compounds().size())
        self.assertEqual(0, c.shells().size())
        self.assertEqual(0, c.solids().size())

    def testSolid(self):
        c = CQ(makeUnitCube(False))
        # make sure all the counts are right for a cube
        self.assertEqual(1, c.solids().size())
        self.assertEqual(6, c.faces().size())
        self.assertEqual(12, c.edges().size())
        self.assertEqual(8, c.vertices().size())
        self.assertEqual(0, c.compounds().size())

        # now any particular face should result in 4 edges and four vertices
        self.assertEqual(4, c.faces().first().edges().size())
        self.assertEqual(1, c.faces().first().size())
        self.assertEqual(4, c.faces().first().vertices().size())

        self.assertEqual(4, c.faces().last().edges().size())

    def testFaceTypesFilter(self):
        "Filters by face type"
        c = CQ(makeUnitCube())
        self.assertEqual(c.faces().size(), c.faces("%PLANE").size())
        self.assertEqual(c.faces().size(), c.faces("%plane").size())
        self.assertEqual(0, c.faces("%sphere").size())
        self.assertEqual(0, c.faces("%cone").size())
        self.assertEqual(0, c.faces("%SPHERE").size())

    def testEdgeTypesFilter(self):
        "Filters by edge type"
        c = Workplane().ellipse(3, 4).circle(1).extrude(1)
        self.assertEqual(2, c.edges("%Ellipse").size())
        self.assertEqual(2, c.edges("%circle").size())
        self.assertEqual(2, c.edges("%LINE").size())
        self.assertEqual(0, c.edges("%Bspline").size())
        self.assertEqual(0, c.edges("%Offset").size())
        self.assertEqual(0, c.edges("%HYPERBOLA").size())

    def testPerpendicularDirFilter(self):
        c = CQ(makeUnitCube())

        perp_edges = c.edges("#Z")
        self.assertEqual(8, perp_edges.size())  # 8 edges are perp. to z
        # dot product of perpendicular vectors is zero
        for e in perp_edges.vals():
            self.assertAlmostEqual(e.tangentAt(0).dot(Vector(0, 0, 1)), 0.0)
        perp_faces = c.faces("#Z")
        self.assertEqual(4, perp_faces.size())  # 4 faces are perp to z too!
        for f in perp_faces.vals():
            self.assertAlmostEqual(f.normalAt(None).dot(Vector(0, 0, 1)), 0.0)

    def testFaceDirFilter(self):
        c = CQ(makeUnitCube())
        # a cube has one face in each direction
        self.assertEqual(1, c.faces("+Z").size())
        self.assertTupleAlmostEquals(
            (0, 0, 1), c.faces("+Z").val().Center().toTuple(), 3
        )
        self.assertEqual(1, c.faces("-Z").size())
        self.assertTupleAlmostEquals(
            (0, 0, 0), c.faces("-Z").val().Center().toTuple(), 3
        )
        self.assertEqual(1, c.faces("+X").size())
        self.assertTupleAlmostEquals(
            (0.5, 0, 0.5), c.faces("+X").val().Center().toTuple(), 3
        )
        self.assertEqual(1, c.faces("-X").size())
        self.assertTupleAlmostEquals(
            (-0.5, 0, 0.5), c.faces("-X").val().Center().toTuple(), 3
        )
        self.assertEqual(1, c.faces("+Y").size())
        self.assertTupleAlmostEquals(
            (0, 0.5, 0.5), c.faces("+Y").val().Center().toTuple(), 3
        )
        self.assertEqual(1, c.faces("-Y").size())
        self.assertTupleAlmostEquals(
            (0, -0.5, 0.5), c.faces("-Y").val().Center().toTuple(), 3
        )
        self.assertEqual(0, c.faces("XY").size())
        self.assertEqual(1, c.faces("X").size())  # should be same as +X
        self.assertEqual(c.faces("+X").val().Center(), c.faces("X").val().Center())
        self.assertNotEqual(c.faces("+X").val().Center(), c.faces("-X").val().Center())

    def testBaseDirSelector(self):
        # BaseDirSelector isn't intended to be instantiated, use subclass
        # ParallelDirSelector to test the code in BaseDirSelector
        loose_selector = ParallelDirSelector(Vector(0, 0, 1), tolerance=10)

        c = Workplane(makeUnitCube(centered=True))

        # BaseDirSelector should filter out everything but Faces and Edges with
        # geomType LINE
        self.assertNotEqual(c.vertices().size(), 0)
        self.assertEqual(c.vertices(loose_selector).size(), 0)

        # This has an edge that is not a LINE
        c_curves = Workplane().sphere(1)
        self.assertNotEqual(c_curves.edges(), 0)
        self.assertEqual(c_curves.edges(loose_selector).size(), 0)

        # this has a Face that is not a PLANE
        face_dir = c_curves.faces().val().normalAt(None)
        self.assertNotEqual(c_curves.faces(), 0)
        self.assertEqual(
            c_curves.faces(ParallelDirSelector(face_dir, tolerance=10)).size(), 0
        )

        self.assertNotEqual(c.solids().size(), 0)
        self.assertEqual(c.solids(loose_selector).size(), 0)

        comp = Workplane(makeUnitCube()).workplane().move(10, 10).box(1, 1, 1)
        self.assertNotEqual(comp.compounds().size(), 0)
        self.assertEqual(comp.compounds(loose_selector).size(), 0)

    def testParallelPlaneFaceFilter(self):
        c = CQ(makeUnitCube(centered=False))

        # faces parallel to Z axis
        # these two should produce the same behaviour:
        for s in ["|Z", selectors.ParallelDirSelector(Vector(0, 0, 1))]:
            parallel_faces = c.faces(s)
            self.assertEqual(2, parallel_faces.size())
            for f in parallel_faces.vals():
                self.assertAlmostEqual(abs(f.normalAt(None).dot(Vector(0, 0, 1))), 1)
        self.assertEqual(
            2, c.faces(selectors.ParallelDirSelector(Vector((0, 0, -1)))).size()
        )  # same thing as above

        # just for fun, vertices on faces parallel to z
        self.assertEqual(8, c.faces("|Z").vertices().size())

        # check that the X & Y center of these faces is the same as the box (ie. we haven't selected the wrong face)
        faces = c.faces(selectors.ParallelDirSelector(Vector((0, 0, 1)))).vals()
        for f in faces:
            c = f.Center()
            self.assertAlmostEqual(c.x, 0.5)
            self.assertAlmostEqual(c.y, 0.5)

    def testParallelEdgeFilter(self):
        c = CQ(makeUnitCube())
        for sel, vec in zip(
            ["|X", "|Y", "|Z"], [Vector(1, 0, 0), Vector(0, 1, 0), Vector(0, 0, 1)]
        ):
            edges = c.edges(sel)
            # each direction should have 4 edges
            self.assertEqual(4, edges.size())
            # each edge should be parallel with vec and have a cross product with a length of 0
            for e in edges.vals():
                self.assertAlmostEqual(e.tangentAt(0).cross(vec).Length, 0.0)

    def testCenterNthSelector(self):
        sel = selectors.CenterNthSelector

        nothing = Workplane()
        self.assertEqual(nothing.solids().size(), 0)
        with self.assertRaises(ValueError):
            nothing.solids(sel(Vector(0, 0, 1), 0))

        c = Workplane(makeUnitCube(centered=True))

        bottom_face = c.faces(sel(Vector(0, 0, 1), 0))
        self.assertEqual(bottom_face.size(), 1)
        self.assertTupleAlmostEquals((0, 0, 0), bottom_face.val().Center().toTuple(), 3)

        side_faces = c.faces(sel(Vector(0, 0, 1), 1))
        self.assertEqual(side_faces.size(), 4)
        for f in side_faces.vals():
            self.assertAlmostEqual(0.5, f.Center().z)

        top_face = c.faces(sel(Vector(0, 0, 1), 2))
        self.assertEqual(top_face.size(), 1)
        self.assertTupleAlmostEquals((0, 0, 1), top_face.val().Center().toTuple(), 3)

        with self.assertRaises(IndexError):
            c.faces(sel(Vector(0, 0, 1), 3))

        left_face = c.faces(sel(Vector(1, 0, 0), 0))
        self.assertEqual(left_face.size(), 1)
        self.assertTupleAlmostEquals(
            (-0.5, 0, 0.5), left_face.val().Center().toTuple(), 3
        )

        middle_faces = c.faces(sel(Vector(1, 0, 0), 1))
        self.assertEqual(middle_faces.size(), 4)
        for f in middle_faces.vals():
            self.assertAlmostEqual(0, f.Center().x)

        right_face = c.faces(sel(Vector(1, 0, 0), 2))
        self.assertEqual(right_face.size(), 1)
        self.assertTupleAlmostEquals(
            (0.5, 0, 0.5), right_face.val().Center().toTuple(), 3
        )

        with self.assertRaises(IndexError):
            c.faces(sel(Vector(1, 0, 0), 3))

        # lower corner faces
        self.assertEqual(c.faces(sel(Vector(1, 1, 1), 0)).size(), 3)
        # upper corner faces
        self.assertEqual(c.faces(sel(Vector(1, 1, 1), 1)).size(), 3)
        with self.assertRaises(IndexError):
            c.faces(sel(Vector(1, 1, 1), 2))

        for idx, z_val in zip([0, 1, 2], [0, 0.5, 1]):
            edges = c.edges(sel(Vector(0, 0, 1), idx))
            self.assertEqual(edges.size(), 4)
            for e in edges.vals():
                self.assertAlmostEqual(z_val, e.Center().z)
        with self.assertRaises(IndexError):
            c.edges(sel(Vector(0, 0, 1), 3))

        for idx, z_val in zip([0, 1], [0, 1]):
            vertices = c.vertices(sel(Vector(0, 0, 1), idx))
            self.assertEqual(vertices.size(), 4)
            for e in vertices.vals():
                self.assertAlmostEqual(z_val, e.Z)
        with self.assertRaises(IndexError):
            c.vertices(sel(Vector(0, 0, 1), 3))

        # test string version
        face1 = c.faces(">>X[-1]")
        face2 = c.faces("<<(2,0,1)[0]")
        face3 = c.faces("<<X[0]")
        face4 = c.faces(">>X")

        self.assertTrue(face1.val().isSame(face2.val()))
        self.assertTrue(face1.val().isSame(face3.val()))
        self.assertTrue(face1.val().isSame(face4.val()))

        prism = Workplane().rect(2, 2).extrude(1, taper=30)

        # CenterNth disregards orientation
        edges1 = prism.edges(">>Z[-2]")
        self.assertEqual(len(edges1.vals()), 4)

        # DirectionNth does not
        with self.assertRaises(ValueError):
            prism.edges(">Z[-2]")

        # select a non-linear edge
        part = (
            Workplane()
            .rect(10, 10, centered=False)
            .extrude(1)
            .faces(">Z")
            .workplane(centerOption="CenterOfMass")
            .move(-3, 0)
            .hole(2)
        )
        hole = part.faces(">Z").edges(sel(Vector(1, 0, 0), 1))
        # have we selected a single hole?
        self.assertEqual(1, hole.size())
        self.assertAlmostEqual(1, hole.val().radius())

        # can we select a non-planar face?
        hole_face = part.faces(sel(Vector(1, 0, 0), 1))
        self.assertEqual(hole_face.size(), 1)
        self.assertNotEqual(hole_face.val().geomType(), "PLANE")

        # select solids
        box0 = Workplane().box(1, 1, 1, centered=(True, True, True))
        box1 = Workplane("XY", origin=(10, 10, 10)).box(
            1, 1, 1, centered=(True, True, True)
        )
        part = box0.add(box1)
        self.assertEqual(part.solids().size(), 2)
        for direction in [(0, 0, 1), (0, 1, 0), (1, 0, 0)]:
            box0_selected = part.solids(sel(Vector(direction), 0))
            self.assertEqual(1, box0_selected.size())
            self.assertTupleAlmostEquals(
                (0, 0, 0), box0_selected.val().Center().toTuple(), 3
            )
            box1_selected = part.solids(sel(Vector(direction), 1))
            self.assertEqual(1, box0_selected.size())
            self.assertTupleAlmostEquals(
                (10, 10, 10), box1_selected.val().Center().toTuple(), 3
            )

    def testMaxDistance(self):
        c = CQ(makeUnitCube())

        # should select the topmost face
        self.assertEqual(1, c.faces(">Z").size())
        self.assertEqual(4, c.faces(">Z").vertices().size())

        # vertices should all be at z=1, if this is the top face
        self.assertEqual(4, len(c.faces(">Z").vertices().vals()))
        for v in c.faces(">Z").vertices().vals():
            self.assertAlmostEqual(1.0, v.Z, 3)

        # test the case of multiple objects at the same distance
        el = c.edges(">Z").vals()
        self.assertEqual(4, len(el))
        for e in el:
            self.assertAlmostEqual(e.Center().z, 1)

    def testMinDistance(self):
        c = CQ(makeUnitCube())

        # should select the bottom face
        self.assertEqual(1, c.faces("<Z").size())
        self.assertEqual(4, c.faces("<Z").vertices().size())

        # vertices should all be at z=0, if this is the bottom face
        self.assertEqual(4, len(c.faces("<Z").vertices().vals()))
        for v in c.faces("<Z").vertices().vals():
            self.assertAlmostEqual(0.0, v.Z, 3)

        # test the case of multiple objects at the same distance
        el = c.edges("<Z").vals()
        self.assertEqual(4, len(el))
        for e in el:
            self.assertAlmostEqual(e.Center().z, 0)

    def testNthDistance(self):
        c = Workplane("XY").pushPoints([(-2, 0), (2, 0)]).box(1, 1, 1)

        # 2nd face
        val = c.faces(selectors.DirectionNthSelector(Vector(1, 0, 0), 1)).val()
        self.assertAlmostEqual(val.Center().x, -1.5)

        # 2nd face with inversed selection vector
        val = c.faces(selectors.DirectionNthSelector(Vector(-1, 0, 0), 1)).val()
        self.assertAlmostEqual(val.Center().x, 1.5)

        # 2nd last face
        val = c.faces(selectors.DirectionNthSelector(Vector(1, 0, 0), -2)).val()
        self.assertAlmostEqual(val.Center().x, 1.5)

        # Last face
        val = c.faces(selectors.DirectionNthSelector(Vector(1, 0, 0), -1)).val()
        self.assertAlmostEqual(val.Center().x, 2.5)

        # check if the selected face if normal to the specified Vector
        self.assertAlmostEqual(val.normalAt().cross(Vector(1, 0, 0)).Length, 0.0)

        # repeat the test using string based selector

        # 2nd face
        val = c.faces(">(1,0,0)[1]").val()
        self.assertAlmostEqual(val.Center().x, -1.5)
        val = c.faces(">X[1]").val()
        self.assertAlmostEqual(val.Center().x, -1.5)

        # 2nd face with inversed selection vector
        val = c.faces(">(-1,0,0)[1]").val()
        self.assertAlmostEqual(val.Center().x, 1.5)
        val = c.faces("<X[1]").val()
        self.assertAlmostEqual(val.Center().x, 1.5)

        # 2nd last face
        val = c.faces(">X[-2]").val()
        self.assertAlmostEqual(val.Center().x, 1.5)

        # Last face
        val = c.faces(">X[-1]").val()
        self.assertAlmostEqual(val.Center().x, 2.5)

        # check if the selected face if normal to the specified Vector
        self.assertAlmostEqual(val.normalAt().cross(Vector(1, 0, 0)).Length, 0.0)

        # test selection of multiple faces with the same distance
        c = (
            Workplane("XY")
            .box(1, 4, 1, centered=(False, True, False))
            .faces("<Z")
            .box(2, 2, 2, centered=(True, True, False))
            .faces(">Z")
            .box(1, 1, 1, centered=(True, True, False))
        )

        # select 2nd from the bottom (NB python indexing is 0-based)
        vals = c.faces(">Z[1]").vals()
        self.assertEqual(len(vals), 2)

        val = c.faces(">Z[1]").val()
        self.assertAlmostEqual(val.Center().z, 1)

        # do the same but by selecting 3rd from the top
        vals = c.faces("<Z[2]").vals()
        self.assertEqual(len(vals), 2)

        val = c.faces("<Z[2]").val()
        self.assertAlmostEqual(val.Center().z, 1)

        # do the same but by selecting 2nd last from the bottom
        vals = c.faces("<Z[-2]").vals()
        self.assertEqual(len(vals), 2)

        val = c.faces("<Z[-2]").val()
        self.assertAlmostEqual(val.Center().z, 1)

        # note that .val() will return the workplane center if the objects list
        # is empty, so to make sure this test fails with a selector that
        # selects nothing, use .vals()[0]
        # verify that <Z[-1] is equivalent to <Z
        val1 = c.faces("<Z[-1]").vals()[0]
        val2 = c.faces("<Z").vals()[0]
        self.assertTupleAlmostEquals(
            val1.Center().toTuple(), val2.Center().toTuple(), 3
        )

        # verify that >Z[-1] is equivalent to >Z
        val1 = c.faces(">Z[-1]").vals()[0]
        val2 = c.faces(">Z").vals()[0]
        self.assertTupleAlmostEquals(
            val1.Center().toTuple(), val2.Center().toTuple(), 3
        )

        # DirectionNthSelector should not select faces that are not perpendicular
        twisted_boxes = (
            Workplane()
            .box(1, 1, 1, centered=(True, True, False))
            .transformed(rotate=(45, 0, 0), offset=(0, 0, 3))
            .box(1, 1, 1)
        )
        self.assertTupleAlmostEquals(
            twisted_boxes.faces(">Z[-1]").val().Center().toTuple(), (0, 0, 1), 3
        )
        # this should select a face on the upper/rotated cube, not the lower/unrotated cube
        self.assertGreater(twisted_boxes.faces("<(0, 1, 1)[-1]").val().Center().z, 1)
        # verify that >Z[-1] is equivalent to >Z
        self.assertTupleAlmostEquals(
            twisted_boxes.faces(">(0, 1, 1)[0]").vals()[0].Center().toTuple(),
            twisted_boxes.faces("<(0, 1, 1)[-1]").vals()[0].Center().toTuple(),
            3,
        )

    def testNearestTo(self):
        c = CQ(makeUnitCube(centered=False))

        # nearest vertex to origin is (0,0,0)
        t = (0.1, 0.1, 0.1)

        v = c.vertices(selectors.NearestToPointSelector(t)).vals()[0]
        self.assertTupleAlmostEquals((0.0, 0.0, 0.0), (v.X, v.Y, v.Z), 3)

        t = (0.1, 0.1, 0.2)
        # nearest edge is the vertical side edge, 0,0,0 -> 0,0,1
        e = c.edges(selectors.NearestToPointSelector(t)).vals()[0]
        v = c.edges(selectors.NearestToPointSelector(t)).vertices().vals()
        self.assertEqual(2, len(v))

        # nearest solid is myself
        s = c.solids(selectors.NearestToPointSelector(t)).vals()
        self.assertEqual(1, len(s))

    def testBox(self):
        c = CQ(makeUnitCube(centered=False))

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
            ((0.9, -0.1, 0.9), (1.1, 0.1, 1.1), (1.0, 0.0, 1.0)),
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
        vl = c.vertices(
            selectors.BoxSelector((-0.1, -0.1, 0.9), (0.1, 1.1, 1.1))
        ).vals()
        self.assertEqual(2, len(vl))
        vl = c.vertices(
            selectors.BoxSelector((-0.1, -0.1, -0.1), (0.1, 1.1, 1.1))
        ).vals()
        self.assertEqual(4, len(vl))

        # test edge selection
        test_data_edges = [
            # box point0,       box point1,       edge center
            ((0.4, -0.1, -0.1), (0.6, 0.1, 0.1), (0.5, 0.0, 0.0)),
            ((-0.1, -0.1, 0.4), (0.1, 0.1, 0.6), (0.0, 0.0, 0.5)),
            ((0.9, 0.9, 0.4), (1.1, 1.1, 0.6), (1.0, 1.0, 0.5)),
            ((0.4, 0.9, 0.9), (0.6, 1.1, 1.1,), (0.5, 1.0, 1.0),),
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
            ((0.4, 0.4, -0.1), (0.6, 0.6, 0.1), (0.5, 0.5, 0.0)),
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
        el = c.edges(
            selectors.BoxSelector((-0.1, -0.1, -0.1), (1.1, 0.1, 0.6), True)
        ).vals()
        self.assertEqual(1, len(el))
        fl = c.faces(
            selectors.BoxSelector((0.4, 0.4, 0.4), (1.1, 1.1, 1.1), True)
        ).vals()
        self.assertEqual(0, len(fl))
        fl = c.faces(
            selectors.BoxSelector((-0.1, 0.4, -0.1), (1.1, 1.1, 1.1), True)
        ).vals()
        self.assertEqual(1, len(fl))

    def testRadiusNthSelector(self):

        # test the key method behaves
        rad = 2.3
        arc = Edge.makeCircle(radius=rad)
        sel = selectors.RadiusNthSelector(0)
        self.assertAlmostEqual(rad, sel.key(arc), 3)
        line = Edge.makeLine(Vector(0, 0, 0), Vector(1, 1, 1))
        with self.assertRaises(ValueError):
            sel.key(line)
        solid = makeUnitCube()
        with self.assertRaises(ValueError):
            sel.key(solid)

        part = (
            Workplane()
            .box(10, 10, 1)
            .edges(">(1, 1, 0) and |Z")
            .fillet(1)
            .edges(">(-1, 1, 0) and |Z")
            .fillet(1)
            .edges(">(-1, -1, 0) and |Z")
            .fillet(2)
            .edges(">(1, -1, 0) and |Z")
            .fillet(3)
            .faces(">Z")
        )
        # smallest radius is 1.0
        self.assertAlmostEqual(
            part.edges(selectors.RadiusNthSelector(0)).val().radius(), 1.0
        )
        # there are two edges with the smallest radius
        self.assertEqual(len(part.edges(selectors.RadiusNthSelector(0)).vals()), 2)
        # next radius is 2.0
        self.assertAlmostEqual(
            part.edges(selectors.RadiusNthSelector(1)).val().radius(), 2.0
        )
        # largest radius is 3.0
        self.assertAlmostEqual(
            part.edges(selectors.RadiusNthSelector(-1)).val().radius(), 3.0
        )
        # accessing index 3 should be an IndexError
        with self.assertRaises(IndexError):
            part.edges(selectors.RadiusNthSelector(3))
        # reversed
        self.assertAlmostEqual(
            part.edges(selectors.RadiusNthSelector(0, directionMax=False))
            .val()
            .radius(),
            3.0,
        )

        # test the selector on wires
        wire_circles = (
            Workplane()
            .circle(2)
            .moveTo(10, 0)
            .circle(2)
            .moveTo(20, 0)
            .circle(4)
            .consolidateWires()
        )
        self.assertEqual(
            len(wire_circles.wires(selectors.RadiusNthSelector(0)).vals()), 2
        )
        self.assertEqual(
            len(wire_circles.wires(selectors.RadiusNthSelector(1)).vals()), 1
        )
        self.assertAlmostEqual(
            wire_circles.wires(selectors.RadiusNthSelector(0)).val().radius(), 2
        )
        self.assertAlmostEqual(
            wire_circles.wires(selectors.RadiusNthSelector(1)).val().radius(), 4
        )

    def testLengthNthSelector_EmptyEdgesList(self):
        """
        LengthNthSelector should raise ValueError when
        applied to an empty list
        """
        with self.assertRaises(ValueError):
            Workplane().edges(selectors.LengthNthSelector(0))

    def testLengthNthSelector_Faces(self):
        """
        LengthNthSelector should produce empty list when applied
        to list of unsupported Shapes (Faces)
        """
        with self.assertRaises(IndexError):
            Workplane().box(1, 1, 1).faces(selectors.LengthNthSelector(0))

    def testLengthNthSelector_EdgesOfUnitCube(self):
        """
        Selecting all edges of unit cube
        """
        w1 = Workplane(makeUnitCube()).edges(selectors.LengthNthSelector(0))
        self.assertEqual(
            12,
            w1.size(),
            msg="Failed to select edges of a unit cube: wrong number of edges",
        )

    def testLengthNthSelector_EdgesOf123Cube(self):
        """
        Selecting 4 edges of length 2 belonging to 1x2x3 box
        """
        w1 = Workplane().box(1, 2, 3).edges(selectors.LengthNthSelector(1))
        self.assertEqual(
            4,
            w1.size(),
            msg="Failed to select edges of length 2 belonging to 1x2x3 box: wrong number of edges",
        )
        self.assertTupleAlmostEquals(
            (2, 2, 2, 2),
            (edge.Length() for edge in w1.vals()),
            5,
            msg="Failed to select edges of length 2 belonging to 1x2x3 box: wrong length",
        )

    def testLengthNthSelector_PlateWithHoles(self):
        """
        Creating 10x10 plate with 4 holes (dia=1)
        and using LengthNthSelector to select hole rims
        and plate perimeter wire on the top surface/
        """
        w2 = (
            Workplane()
            .box(10, 10, 1)
            .faces(">Z")
            .workplane()
            .rarray(4, 4, 2, 2)
            .hole(1)
            .faces(">Z")
        )

        hole_rims = w2.wires(selectors.LengthNthSelector(0))

        self.assertEqual(4, hole_rims.size())
        self.assertEqual(
            4, hole_rims.size(), msg="Failed to select hole rims: wrong N edges",
        )

        hole_circumference = math.pi * 1
        self.assertTupleAlmostEquals(
            [hole_circumference] * 4,
            (edge.Length() for edge in hole_rims.vals()),
            5,
            msg="Failed to select hole rims: wrong length",
        )

        plate_perimeter = w2.wires(selectors.LengthNthSelector(1))

        self.assertEqual(
            1,
            plate_perimeter.size(),
            msg="Failed to select plate perimeter wire: wrong N wires",
        )

        self.assertAlmostEqual(
            10 * 4,
            plate_perimeter.val().Length(),
            5,
            msg="Failed to select plate perimeter wire: wrong length",
        )

    def testLengthNthSelector_UnsupportedShapes(self):
        """
        No length defined for a face, shell, solid or compound
        """
        w0 = Workplane().rarray(2, 2, 2, 1).box(1, 1, 1)
        for val in [w0.faces().val(), w0.shells().val(), w0.compounds().val()]:
            with self.assertRaises(ValueError):
                selectors.LengthNthSelector(0).key(val)

    def testLengthNthSelector_UnitEdgeAndWire(self):
        """
        Checks that key() method of LengthNthSelector
        calculates lengths of unit edge correctly
        """
        unit_edge = Edge.makeLine(Vector(0, 0, 0), Vector(0, 0, 1))
        self.assertAlmostEqual(1, selectors.LengthNthSelector(0).key(unit_edge), 5)

        unit_edge = Wire.assembleEdges([unit_edge])
        self.assertAlmostEqual(1, selectors.LengthNthSelector(0).key(unit_edge), 5)

    def testAreaNthSelector_Vertices(self):
        """
        Using AreaNthSelector on unsupported Shapes (Vertices)
        should produce empty list
        """
        with self.assertRaises(IndexError):
            Workplane("XY").box(10, 10, 10).vertices(selectors.AreaNthSelector(0))

    def testAreaNthSelector_Edges(self):
        """
        Using AreaNthSelector on unsupported Shapes (Edges)
        should produce empty list
        """
        with self.assertRaises(IndexError):
            Workplane("XY").box(10, 10, 10).edges(selectors.AreaNthSelector(0))

    def testAreaNthSelector_NestedWires(self):
        """
        Tests key parts of case seam leap creation algorithm
        (see example 26)

        - Selecting top outer wire
        - Applying Offset2D and extruding a "lid"
        - Selecting the innermost of three wires in preparation to
          cut through the lid and leave a lip on the case seam
        """
        # selecting top outermost wire of square box
        wp = (
            Workplane("XY")
            .rect(50, 50)
            .extrude(50)
            .faces(">Z")
            .shell(-5, "intersection")
            .faces(">Z")
            .wires(selectors.AreaNthSelector(-1))
        )

        self.assertEqual(
            len(wp.vals()),
            1,
            msg="Failed to select top outermost wire of the box: wrong N wires",
        )
        self.assertAlmostEqual(
            Face.makeFromWires(wp.val()).Area(),
            50 * 50,
            msg="Failed to select top outermost wire of the box: wrong wire area",
        )

        # preparing to add an inside lip to the box
        wp = wp.toPending().workplane().offset2D(-2).extrude(1).faces(">Z[-2]")
        # workplane now has 2 faces selected:
        # a square and a thin rectangular frame

        wp_outer_wire = wp.wires(selectors.AreaNthSelector(-1))
        self.assertEqual(
            len(wp_outer_wire.vals()),
            1,
            msg="Failed to select outermost wire of 2 faces: wrong N wires",
        )
        self.assertAlmostEqual(
            Face.makeFromWires(wp_outer_wire.val()).Area(),
            50 * 50,
            msg="Failed to select outermost wire of 2 faces: wrong area",
        )

        wp_mid_wire = wp.wires(selectors.AreaNthSelector(1))
        self.assertEqual(
            len(wp_mid_wire.vals()),
            1,
            msg="Failed to select middle wire of 2 faces: wrong N wires",
        )
        self.assertAlmostEqual(
            Face.makeFromWires(wp_mid_wire.val()).Area(),
            (50 - 2 * 2) * (50 - 2 * 2),
            msg="Failed to select middle wire of 2 faces: wrong area",
        )

        wp_inner_wire = wp.wires(selectors.AreaNthSelector(0))
        self.assertEqual(
            len(wp_inner_wire.vals()),
            1,
            msg="Failed to select inner wire of 2 faces: wrong N wires",
        )
        self.assertAlmostEqual(
            Face.makeFromWires(wp_inner_wire.val()).Area(),
            (50 - 5 * 2) * (50 - 5 * 2),
            msg="Failed to select inner wire of 2 faces: wrong area",
        )

    def testAreaNthSelector_NonplanarWire(self):
        """
        AreaNthSelector should raise ValueError when
        used on non-planar wires so that they are ignored by
        _NthSelector.

        Non-planar wires in stack should not prevent selection of
        planar wires.
        """
        wp = Workplane("XY").circle(10).extrude(50)

        with self.assertRaises(IndexError):
            wp.wires(selectors.AreaNthSelector(1))

        cylinder_flat_ends = wp.wires(selectors.AreaNthSelector(0))
        self.assertEqual(
            len(cylinder_flat_ends.vals()),
            2,
            msg="Failed to select cylinder flat end wires: wrong N wires",
        )
        self.assertTupleAlmostEquals(
            [math.pi * 10 ** 2] * 2,
            [Face.makeFromWires(wire).Area() for wire in cylinder_flat_ends.vals()],
            5,
            msg="Failed to select cylinder flat end wires: wrong area",
        )

    def testAreaNthSelector_Faces(self):
        """
        Selecting two faces of 10x20x30 box with intermediate area.
        """
        wp = Workplane("XY").box(10, 20, 30).faces(selectors.AreaNthSelector(1))

        self.assertEqual(
            len(wp.vals()),
            2,
            msg="Failed to select two faces of 10-20-30 box "
            "with intermediate area: wrong N faces",
        )
        self.assertTupleAlmostEquals(
            (wp.vals()[0].Area(), wp.vals()[1].Area()),
            (10 * 30, 10 * 30),
            7,
            msg="Failed to select two faces of 10-20-30 box "
            "with intermediate area: wrong area",
        )

    def testAreaNthSelector_Shells(self):
        """
        Selecting one of three shells with the smallest surface area
        """

        sizes_iter = iter([10.0, 20.0, 30.0])

        def next_box_shell(loc):
            size = next(sizes_iter)
            return Workplane().box(size, size, size).val().located(loc)

        workplane_shells = Workplane().rarray(10, 1, 3, 1).eachpoint(next_box_shell)

        selected_shells = workplane_shells.shells(selectors.AreaNthSelector(0))

        self.assertEqual(
            len(selected_shells.vals()),
            1,
            msg="Failed to select the smallest shell: wrong N shells",
        )
        self.assertAlmostEqual(
            selected_shells.val().Area(),
            10 * 10 * 6,
            msg="Failed to select the smallest shell: wrong area",
        )

    def testAreaNthSelector_Solids(self):
        """
        Selecting 2 of 3 solids by surface area
        """

        sizes_iter = iter([10.0, 20.0, 20.0])

        def next_box(loc):
            size = next(sizes_iter)
            return Workplane().box(size, size, size).val().located(loc)

        workplane_solids = Workplane().rarray(30, 1, 3, 1).eachpoint(next_box)

        selected_solids = workplane_solids.solids(selectors.AreaNthSelector(1))

        self.assertEqual(
            len(selected_solids.vals()),
            2,
            msg="Failed to select two larger solids: wrong N shells",
        )
        self.assertTupleAlmostEquals(
            [20 * 20 * 6] * 2,
            [solid.Area() for solid in selected_solids.vals()],
            5,
            msg="Failed to select two larger solids: wrong area",
        )

    def testAndSelector(self):
        c = CQ(makeUnitCube())

        S = selectors.StringSyntaxSelector
        BS = selectors.BoxSelector

        el = c.edges(
            selectors.AndSelector(S("|X"), BS((-2, -2, 0.1), (2, 2, 2)))
        ).vals()
        self.assertEqual(2, len(el))

        # test 'and' (intersection) operator
        el = c.edges(S("|X") & BS((-2, -2, 0.1), (2, 2, 2))).vals()
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

        fl = c.faces(selectors.InverseSelector(S(">Z"))).vals()
        self.assertEqual(5, len(fl))
        el = c.faces(">Z").edges(selectors.InverseSelector(S(">X"))).vals()
        self.assertEqual(3, len(el))

        # test invert operator
        fl = c.faces(-S(">Z")).vals()
        self.assertEqual(5, len(fl))
        el = c.faces(">Z").edges(-S(">X")).vals()
        self.assertEqual(3, len(el))

        # test using extended string syntax
        fl = c.faces("not >Z").vals()
        self.assertEqual(5, len(fl))
        el = c.faces(">Z").edges("not >X").vals()
        self.assertEqual(3, len(el))

    def testComplexStringSelector(self):
        c = CQ(makeUnitCube())

        v = c.vertices("(>X and >Y) or (<X and <Y)").vals()
        self.assertEqual(4, len(v))

    def testFaceCount(self):
        c = CQ(makeUnitCube())
        self.assertEqual(6, c.faces().size())
        self.assertEqual(2, c.faces("|Z").size())

    def testVertexFilter(self):
        "test selecting vertices on a face"
        c = CQ(makeUnitCube(centered=False))

        # TODO: filters work ok, but they are in global coordinates which sux. it would be nice
        # if they were available in coordinates local to the selected face

        v2 = c.faces("+Z").vertices("<XY")
        self.assertEqual(1, v2.size())  # another way
        # make sure the vertex is the right one

        self.assertTupleAlmostEquals((0.0, 0.0, 1.0), v2.val().toTuple(), 3)

    def testGrammar(self):
        """
        Test if reasonable string selector expressions parse without an error
        """

        gram = selectors._expression_grammar

        expressions = [
            "+X ",
            "-Y",
            "|(1,0,0)",
            "|(-1, -0.1 , 2. )",
            "#(1.,1.4114,-0.532)",
            "%Plane",
            ">XZ",
            "<Z[-2]",
            "<<Z[2]",
            ">>(1,1,0)",
            ">(1,4,55.)[20]",
            "|XY",
            "<YZ[0]",
            "front",
            "back",
            "left",
            "right",
            "top",
            "bottom",
            "not |(1,1,0) and >(0,0,1) or XY except >(1,1,1)[-1]",
            "(not |(1,1,0) and >(0,0,1)) exc XY and (Z or X)",
            "not ( <X or >X or <Y or >Y )",
        ]

        for e in expressions:
            gram.parseString(e, parseAll=True)
