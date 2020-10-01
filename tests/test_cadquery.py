"""
    This module tests cadquery creation and manipulation functions

"""
# system modules
import math, os.path, time, tempfile
from random import choice
from random import random
from random import randrange

from pytest import approx, raises

# my modules

from cadquery import *
from cadquery import exporters
from cadquery import occ_impl
from tests import (
    BaseTest,
    writeStringToFile,
    makeUnitCube,
    readFileAsString,
    makeUnitSquareWire,
    makeCube,
)

# where unit test output will be saved
OUTDIR = tempfile.gettempdir()
SUMMARY_FILE = os.path.join(OUTDIR, "testSummary.html")

SUMMARY_TEMPLATE = """<html>
    <head>
        <style type="text/css">
            .testResult{
                background: #eeeeee;
                margin: 50px;
                border: 1px solid black;
            }
        </style>
    </head>
    <body>
        <!--TEST_CONTENT-->
    </body>
</html>"""

TEST_RESULT_TEMPLATE = """
    <div class="testResult"><h3>%(name)s</h3>
    %(svg)s
    </div>
    <!--TEST_CONTENT-->
"""

# clean up any summary file that is in the output directory.
# i know, this sux, but there is no other way to do this in 2.6, as we cannot do class fixutres till 2.7
writeStringToFile(SUMMARY_TEMPLATE, SUMMARY_FILE)


class TestCadQuery(BaseTest):
    def tearDown(self):
        """
            Update summary with data from this test.
            This is a really hackey way of doing it-- we get a startup event from module load,
            but there is no way in unittest to get a single shutdown event-- except for stuff in 2.7 and above

            So what we do here is to read the existing file, stick in more content, and leave it
        """
        svgFile = os.path.join(OUTDIR, self._testMethodName + ".svg")

        # all tests do not produce output
        if os.path.exists(svgFile):
            existingSummary = readFileAsString(SUMMARY_FILE)
            svgText = readFileAsString(svgFile)
            svgText = svgText.replace(
                '<?xml version="1.0" encoding="UTF-8" standalone="no"?>', ""
            )

            # now write data into the file
            # the content we are replacing it with also includes the marker, so it can be replaced again
            existingSummary = existingSummary.replace(
                "<!--TEST_CONTENT-->",
                TEST_RESULT_TEMPLATE % (dict(svg=svgText, name=self._testMethodName)),
            )

            writeStringToFile(existingSummary, SUMMARY_FILE)

    def saveModel(self, shape):
        """
            shape must be a CQ object
            Save models in SVG and STEP format
        """
        shape.exportSvg(os.path.join(OUTDIR, self._testMethodName + ".svg"))
        shape.val().exportStep(os.path.join(OUTDIR, self._testMethodName + ".step"))

    def testToOCC(self):
        """
        Tests to make sure that a CadQuery object is converted correctly to a OCC object.
        """
        r = Workplane("XY").rect(5, 5).extrude(5)

        r = r.toOCC()

        import OCP

        self.assertEqual(type(r), OCP.TopoDS.TopoDS_Compound)

    def testToSVG(self):
        """
        Tests to make sure that a CadQuery object is converted correctly to SVG
        """
        r = Workplane("XY").rect(5, 5).extrude(5)

        r_str = r.toSvg()

        # Make sure that a couple of sections from the SVG output make sense
        self.assertTrue(r_str.index('path d="M') > 0)
        self.assertTrue(
            r_str.index('line x1="30" y1="-30" x2="58" y2="-15" stroke-width="3"') > 0
        )

    def testCubePlugin(self):
        """
        Tests a plugin that combines cubes together with a base
        :return:
        """
        # make the plugin method

        def makeCubes(self, length):
            # self refers to the CQ or Workplane object

            # create the solid
            s = Solid.makeBox(length, length, length, Vector(0, 0, 0))

            # use CQ utility method to iterate over the stack an position the cubes
            return self.eachpoint(lambda loc: s.located(loc), True)

        # link the plugin in
        Workplane.makeCubes = makeCubes

        # call it
        result = (
            Workplane("XY")
            .box(6.0, 8.0, 0.5)
            .faces(">Z")
            .rect(4.0, 4.0, forConstruction=True)
            .vertices()
        )
        result = result.makeCubes(1.0)
        result = result.combineSolids()
        self.saveModel(result)
        self.assertEqual(1, result.solids().size())

    def testCylinderPlugin(self):
        """
            Tests a cylinder plugin.
            The plugin creates cylinders of the specified radius and height for each item on the stack

            This is a very short plugin that illustrates just about the simplest possible
            plugin
        """

        def cylinders(self, radius, height):

            # construct a cylinder at (0,0,0)
            c = Solid.makeCylinder(radius, height, Vector(0, 0, 0))

            # combine all the cylinders into a single compound
            r = self.eachpoint(lambda loc: c.located(loc), True).combineSolids()
            return r

        Workplane.cyl = cylinders

        # now test. here we want weird workplane to see if the objects are transformed right
        s = (
            Workplane(Plane(Vector((0, 0, 0)), Vector((1, -1, 0)), Vector((1, 1, 0))))
            .rect(2.0, 3.0, forConstruction=True)
            .vertices()
            .cyl(0.25, 0.5)
        )
        self.assertEqual(4, s.solids().size())
        self.saveModel(s)

    def testPolygonPlugin(self):
        """
            Tests a plugin to make regular polygons around points on the stack

            Demonstratings using eachpoint to allow working in local coordinates
            to create geometry
        """

        def rPoly(self, nSides, diameter):
            def _makePolygon(loc):
                # pnt is a vector in local coordinates
                angle = 2.0 * math.pi / nSides
                pnts = []
                for i in range(nSides + 1):
                    pnts.append(
                        Vector(
                            (diameter / 2.0 * math.cos(angle * i)),
                            (diameter / 2.0 * math.sin(angle * i)),
                            0,
                        )
                    )
                return Wire.makePolygon(pnts).located(loc)

            return self.eachpoint(_makePolygon, True)

        Workplane.rPoly = rPoly

        s = (
            Workplane("XY")
            .box(4.0, 4.0, 0.25)
            .faces(">Z")
            .workplane()
            .rect(2.0, 2.0, forConstruction=True)
            .vertices()
            .rPoly(5, 0.5)
            .cutThruAll()
        )

        # 6 base sides, 4 pentagons, 5 sides each = 26
        self.assertEqual(26, s.faces().size())
        self.saveModel(s)

    def testPointList(self):
        """
        Tests adding points and using them
        """
        c = CQ(makeUnitCube())

        s = c.faces(">Z").workplane().pushPoints([(-0.3, 0.3), (0.3, 0.3), (0, 0)])
        self.assertEqual(3, s.size())
        # TODO: is the ability to iterate over points with circle really worth it?
        # maybe we should just require using all() and a loop for this. the semantics and
        # possible combinations got too hard ( ie, .circle().circle() ) was really odd
        body = s.circle(0.05).cutThruAll()
        self.saveModel(body)
        self.assertEqual(9, body.faces().size())

        # Test the case when using eachpoint with only a blank workplane
        def callback_fn(loc):
            self.assertEqual(
                Vector(0, 0, 0), Vector(loc.wrapped.Transformation().TranslationPart())
            )

        r = Workplane("XY")
        r.objects = []
        r.eachpoint(callback_fn)

    def testWorkplaneFromFace(self):
        # make a workplane on the top face
        s = CQ(makeUnitCube()).faces(">Z").workplane()
        r = s.circle(0.125).cutBlind(-2.0)
        self.saveModel(r)
        # the result should have 7 faces
        self.assertEqual(7, r.faces().size())
        self.assertEqual(type(r.val()), Compound)
        self.assertEqual(type(r.first().val()), Compound)

    def testFrontReference(self):
        # make a workplane on the top face
        s = CQ(makeUnitCube()).faces("front").workplane()
        r = s.circle(0.125).cutBlind(-2.0)
        self.saveModel(r)
        # the result should have 7 faces
        self.assertEqual(7, r.faces().size())
        self.assertEqual(type(r.val()), Compound)
        self.assertEqual(type(r.first().val()), Compound)

    def testRotate(self):
        """Test solid rotation at the CQ object level."""
        box = Workplane("XY").box(1, 1, 5)
        box.rotate((0, 0, 0), (1, 0, 0), 90)
        startPoint = box.faces("<Y").edges("<X").first().val().startPoint().toTuple()
        endPoint = box.faces("<Y").edges("<X").first().val().endPoint().toTuple()

        self.assertEqual(-0.5, startPoint[0])
        self.assertEqual(-0.5, startPoint[1])
        self.assertEqual(-2.5, startPoint[2])
        self.assertEqual(-0.5, endPoint[0])
        self.assertEqual(-0.5, endPoint[1])
        self.assertEqual(2.5, endPoint[2])

    def testPlaneRotateZNormal(self):
        """
        Rotation of a plane in the Z direction should never alter its normal.

        This test creates random planes. The plane is rotated a random angle in
        the Z-direction to verify that the resulting plane maintains the same
        normal.

        The test also checks that the random origin is unaltered after
        rotation.
        """
        for _ in range(100):
            angle = (random() - 0.5) * 720
            xdir = Vector(random(), random(), random()).normalized()
            rdir = Vector(random(), random(), random()).normalized()
            zdir = xdir.cross(rdir).normalized()
            origin = (random(), random(), random())
            plane = Plane(origin=origin, xDir=xdir, normal=zdir)
            rotated = plane.rotated((0, 0, angle))
            assert rotated.zDir.toTuple() == approx(zdir.toTuple())
            assert rotated.origin.toTuple() == approx(origin)

    def testPlaneRotateConcat(self):
        """
        Test the result of a well-known concatenated rotation example.
        """
        xdir = (1, 0, 0)
        normal = (0, 0, 1)
        k = 2.0 ** 0.5 / 2.0
        origin = (2, -1, 1)
        plane = Plane(origin=origin, xDir=xdir, normal=normal)
        plane = plane.rotated((0, 0, 45))
        assert plane.xDir.toTuple() == approx((k, k, 0))
        assert plane.yDir.toTuple() == approx((-k, k, 0))
        assert plane.zDir.toTuple() == approx((0, 0, 1))
        plane = plane.rotated((0, 45, 0))
        assert plane.xDir.toTuple() == approx((0.5, 0.5, -k))
        assert plane.yDir.toTuple() == approx((-k, k, 0))
        assert plane.zDir.toTuple() == approx((0.5, 0.5, k))
        assert plane.origin.toTuple() == origin

    def testPlaneRotateConcatRandom(self):
        """
        Rotation of a plane in a given direction should never alter that
        direction.

        This test creates a plane and rotates it a random angle in a given
        direction. After the rotation, the direction of the resulting plane
        in the rotation-direction should be constant.

        The test also checks that the origin is unaltered after all rotations.
        """
        origin = (2, -1, 1)
        plane = Plane(origin=origin, xDir=(1, 0, 0), normal=(0, 0, 1))
        for _ in range(100):
            before = {
                0: plane.xDir.toTuple(),
                1: plane.yDir.toTuple(),
                2: plane.zDir.toTuple(),
            }
            angle = (random() - 0.5) * 720
            direction = randrange(3)
            rotation = [0, 0, 0]
            rotation[direction] = angle
            plane = plane.rotated(rotation)
            after = {
                0: plane.xDir.toTuple(),
                1: plane.yDir.toTuple(),
                2: plane.zDir.toTuple(),
            }
            assert before[direction] == approx(after[direction])
        assert plane.origin.toTuple() == origin

    def testLoft(self):
        """
            Test making a lofted solid
        :return:
        """
        s = Workplane("XY").circle(4.0).workplane(5.0).rect(2.0, 2.0).loft()
        self.saveModel(s)
        # the result should have 7 faces
        self.assertEqual(1, s.solids().size())

        # the resulting loft had a split on the side, not sure why really, i expected only 3 faces
        self.assertEqual(7, s.faces().size())

    def testLoftWithOneWireRaisesValueError(self):
        s = Workplane("XY").circle(5)
        with self.assertRaises(ValueError) as cm:
            s.loft()
        err = cm.exception
        self.assertEqual(str(err), "More than one wire is required")

    def testLoftCombine(self):
        """
            test combining a lof with another feature
        :return:
        """
        s = (
            Workplane("front")
            .box(4.0, 4.0, 0.25)
            .faces(">Z")
            .circle(1.5)
            .workplane(offset=3.0)
            .rect(0.75, 0.5)
            .loft(combine=True)
        )
        self.saveModel(s)
        # self.assertEqual(1,s.solids().size() )
        # self.assertEqual(8,s.faces().size() )

    def testRevolveCylinder(self):
        """
        Test creating a solid using the revolve operation.
        :return:
        """
        # The dimensions of the model. These can be modified rather than changing the
        # shape's code directly.
        rectangle_width = 10.0
        rectangle_length = 10.0
        angle_degrees = 360.0

        # Test revolve without any options for making a cylinder
        result = (
            Workplane("XY").rect(rectangle_width, rectangle_length, False).revolve()
        )
        self.assertEqual(3, result.faces().size())
        self.assertEqual(2, result.vertices().size())
        self.assertEqual(3, result.edges().size())

        # Test revolve when only setting the angle to revolve through
        result = (
            Workplane("XY")
            .rect(rectangle_width, rectangle_length, False)
            .revolve(angle_degrees)
        )
        self.assertEqual(3, result.faces().size())
        self.assertEqual(2, result.vertices().size())
        self.assertEqual(3, result.edges().size())
        result = (
            Workplane("XY")
            .rect(rectangle_width, rectangle_length, False)
            .revolve(270.0)
        )
        self.assertEqual(5, result.faces().size())
        self.assertEqual(6, result.vertices().size())
        self.assertEqual(9, result.edges().size())

        # Test when passing revolve the angle and the axis of revolution's start point
        result = (
            Workplane("XY")
            .rect(rectangle_width, rectangle_length)
            .revolve(angle_degrees, (-5, -5))
        )
        self.assertEqual(3, result.faces().size())
        self.assertEqual(2, result.vertices().size())
        self.assertEqual(3, result.edges().size())
        result = (
            Workplane("XY")
            .rect(rectangle_width, rectangle_length)
            .revolve(270.0, (-5, -5))
        )
        self.assertEqual(5, result.faces().size())
        self.assertEqual(6, result.vertices().size())
        self.assertEqual(9, result.edges().size())

        # Test when passing revolve the angle and both the start and ends of the axis of revolution
        result = (
            Workplane("XY")
            .rect(rectangle_width, rectangle_length)
            .revolve(angle_degrees, (-5, -5), (-5, 5))
        )
        self.assertEqual(3, result.faces().size())
        self.assertEqual(2, result.vertices().size())
        self.assertEqual(3, result.edges().size())
        result = (
            Workplane("XY")
            .rect(rectangle_width, rectangle_length)
            .revolve(270.0, (-5, -5), (-5, 5))
        )
        self.assertEqual(5, result.faces().size())
        self.assertEqual(6, result.vertices().size())
        self.assertEqual(9, result.edges().size())

        # Testing all of the above without combine
        result = (
            Workplane("XY")
            .rect(rectangle_width, rectangle_length)
            .revolve(angle_degrees, (-5, -5), (-5, 5), False)
        )
        self.assertEqual(3, result.faces().size())
        self.assertEqual(2, result.vertices().size())
        self.assertEqual(3, result.edges().size())
        result = (
            Workplane("XY")
            .rect(rectangle_width, rectangle_length)
            .revolve(270.0, (-5, -5), (-5, 5), False)
        )
        self.assertEqual(5, result.faces().size())
        self.assertEqual(6, result.vertices().size())
        self.assertEqual(9, result.edges().size())

    def testRevolveDonut(self):
        """
        Test creating a solid donut shape with square walls
        :return:
        """
        # The dimensions of the model. These can be modified rather than changing the
        # shape's code directly.
        rectangle_width = 10.0
        rectangle_length = 10.0
        angle_degrees = 360.0

        result = (
            Workplane("XY")
            .rect(rectangle_width, rectangle_length, True)
            .revolve(angle_degrees, (20, 0), (20, 10))
        )
        self.assertEqual(4, result.faces().size())
        self.assertEqual(4, result.vertices().size())
        self.assertEqual(6, result.edges().size())

    def testRevolveCone(self):
        """
        Test creating a solid from a revolved triangle
        :return:
        """
        result = Workplane("XY").lineTo(0, 10).lineTo(5, 0).close().revolve()
        self.assertEqual(2, result.faces().size())
        self.assertEqual(2, result.vertices().size())
        self.assertEqual(2, result.edges().size())

    def testSpline(self):
        """
        Tests construction of splines
        """
        pts = [(0, 0), (0, 1), (1, 2), (2, 4)]

        # Spline path - just a smoke test
        path = Workplane("XZ").spline(pts).val()

        # Closed spline
        path_closed = Workplane("XZ").spline(pts, periodic=True).val()
        self.assertTrue(path_closed.IsClosed())

        # attempt to build a valid face
        w = Wire.assembleEdges([path_closed,])
        f = Face.makeFromWires(w)
        self.assertTrue(f.isValid())

        # attempt to build an invalid face
        w = Wire.assembleEdges([path,])
        f = Face.makeFromWires(w)
        self.assertFalse(f.isValid())

        # Spline with explicit tangents
        path_const = Workplane("XZ").spline(pts, tangents=((0, 1), (1, 0))).val()
        self.assertFalse(path.tangentAt(0) == path_const.tangentAt(0))
        self.assertFalse(path.tangentAt(1) == path_const.tangentAt(1))

        # test include current
        path1 = Workplane("XZ").spline(pts[1:], includeCurrent=True).val()
        self.assertAlmostEqual(path.Length(), path1.Length())

        # test tangents and offset plane
        pts = [(0, 0), (-1, 1), (-2, 0), (-1, 0)]
        tangents = [(0, 1), (1, 0)]

        path2 = Workplane("XY", (0, 0, 10)).spline(pts, tangents=tangents)
        self.assertAlmostEqual(path2.val().tangentAt(0).z, 0)

    def testRotatedEllipse(self):
        def rotatePoint(x, y, alpha):
            # rotation matrix
            a = alpha * DEG2RAD
            r = ((math.cos(a), math.sin(a)), (-math.sin(a), math.cos(a)))
            return ((x * r[0][0] + y * r[1][0]), (x * r[0][1] + y * r[1][1]))

        def ellipsePoints(r1, r2, a):
            return (r1 * math.cos(a * DEG2RAD), r2 * math.sin(a * DEG2RAD))

        DEG2RAD = math.pi / 180.0
        p0 = (10, 20)
        a1, a2 = 30, -60
        r1, r2 = 20, 10
        ra = 25

        sx_rot, sy_rot = rotatePoint(*ellipsePoints(r1, r2, a1), ra)
        ex_rot, ey_rot = rotatePoint(*ellipsePoints(r1, r2, a2), ra)

        # startAtCurrent=False, sense = 1
        ellipseArc1 = (
            Workplane("XY")
            .moveTo(*p0)
            .ellipseArc(
                r1, r2, startAtCurrent=False, angle1=a1, angle2=a2, rotation_angle=ra
            )
        )
        start = ellipseArc1.vertices().objects[0]
        end = ellipseArc1.vertices().objects[1]

        self.assertTupleAlmostEquals(
            (start.X, start.Y), (p0[0] + sx_rot, p0[1] + sy_rot), 3
        )
        self.assertTupleAlmostEquals(
            (end.X, end.Y), (p0[0] + ex_rot, p0[1] + ey_rot), 3
        )

        # startAtCurrent=True, sense = 1
        ellipseArc2 = (
            Workplane("XY")
            .moveTo(*p0)
            .ellipseArc(
                r1, r2, startAtCurrent=True, angle1=a1, angle2=a2, rotation_angle=ra
            )
        )
        start = ellipseArc2.vertices().objects[0]
        end = ellipseArc2.vertices().objects[1]

        self.assertTupleAlmostEquals(
            (start.X, start.Y), (p0[0] + sx_rot - sx_rot, p0[1] + sy_rot - sy_rot), 3
        )
        self.assertTupleAlmostEquals(
            (end.X, end.Y), (p0[0] + ex_rot - sx_rot, p0[1] + ey_rot - sy_rot), 3
        )

        # startAtCurrent=False, sense = -1
        ellipseArc3 = (
            Workplane("XY")
            .moveTo(*p0)
            .ellipseArc(
                r1,
                r2,
                startAtCurrent=False,
                angle1=a1,
                angle2=a2,
                rotation_angle=ra,
                sense=-1,
            )
        )
        start = ellipseArc3.vertices().objects[0]
        end = ellipseArc3.vertices().objects[1]

        # swap start and end points for coparison due to different sense
        self.assertTupleAlmostEquals(
            (start.X, start.Y), (p0[0] + ex_rot, p0[1] + ey_rot), 3
        )
        self.assertTupleAlmostEquals(
            (end.X, end.Y), (p0[0] + sx_rot, p0[1] + sy_rot), 3
        )

        # startAtCurrent=True, sense = -1
        ellipseArc4 = (
            Workplane("XY")
            .moveTo(*p0)
            .ellipseArc(
                r1,
                r2,
                startAtCurrent=True,
                angle1=a1,
                angle2=a2,
                rotation_angle=ra,
                sense=-1,
                makeWire=True,
            )
        )

        self.assertEqual(len(ellipseArc4.ctx.pendingWires), 1)

        start = ellipseArc4.vertices().objects[0]
        end = ellipseArc4.vertices().objects[1]

        # swap start and end points for coparison due to different sense
        self.assertTupleAlmostEquals(
            (start.X, start.Y), (p0[0] + ex_rot - ex_rot, p0[1] + ey_rot - ey_rot), 3
        )
        self.assertTupleAlmostEquals(
            (end.X, end.Y), (p0[0] + sx_rot - ex_rot, p0[1] + sy_rot - ey_rot), 3
        )

    def testEllipseArcsClockwise(self):
        ellipseArc = (
            Workplane("XY")
            .moveTo(10, 15)
            .ellipseArc(5, 4, -10, 190, 45, sense=-1, startAtCurrent=False)
        )
        sp = ellipseArc.val().startPoint()
        ep = ellipseArc.val().endPoint()
        self.assertTupleAlmostEquals(
            (sp.x, sp.y), (7.009330014275797, 11.027027582524015), 3
        )
        self.assertTupleAlmostEquals(
            (ep.x, ep.y), (13.972972417475985, 17.990669985724203), 3
        )

        ellipseArc = (
            ellipseArc.ellipseArc(5, 4, -10, 190, 315, sense=-1)
            .ellipseArc(5, 4, -10, 190, 225, sense=-1)
            .ellipseArc(5, 4, -10, 190, 135, sense=-1)
        )
        ep = ellipseArc.val().endPoint()
        self.assertTupleAlmostEquals((sp.x, sp.y), (ep.x, ep.y), 3)

    def testEllipseArcsCounterClockwise(self):
        ellipseArc = (
            Workplane("XY")
            .moveTo(10, 15)
            .ellipseArc(5, 4, -10, 190, 45, startAtCurrent=False)
        )
        sp = ellipseArc.val().startPoint()
        ep = ellipseArc.val().endPoint()
        self.assertTupleAlmostEquals(
            (sp.x, sp.y), (13.972972417475985, 17.990669985724203), 3
        )
        self.assertTupleAlmostEquals(
            (ep.x, ep.y), (7.009330014275797, 11.027027582524015), 3
        )

        ellipseArc = (
            ellipseArc.ellipseArc(5, 4, -10, 190, 135)
            .ellipseArc(5, 4, -10, 190, 225)
            .ellipseArc(5, 4, -10, 190, 315)
        )
        ep = ellipseArc.val().endPoint()
        self.assertTupleAlmostEquals((sp.x, sp.y), (ep.x, ep.y), 3)

    def testEllipseCenterAndMoveTo(self):
        # Whether we start from a center() call or a moveTo call, it should be the same ellipse Arc
        p0 = (10, 20)
        a1, a2 = 30, -60
        r1, r2 = 20, 10
        ra = 25

        ellipseArc1 = (
            Workplane("XY")
            .moveTo(*p0)
            .ellipseArc(
                r1, r2, startAtCurrent=False, angle1=a1, angle2=a2, rotation_angle=ra
            )
        )
        sp1 = ellipseArc1.val().startPoint()
        ep1 = ellipseArc1.val().endPoint()

        ellipseArc2 = (
            Workplane("XY")
            .moveTo(*p0)
            .ellipseArc(
                r1, r2, startAtCurrent=False, angle1=a1, angle2=a2, rotation_angle=ra
            )
        )
        sp2 = ellipseArc2.val().startPoint()
        ep2 = ellipseArc2.val().endPoint()

        self.assertTupleAlmostEquals(sp1.toTuple(), sp2.toTuple(), 3)
        self.assertTupleAlmostEquals(ep1.toTuple(), ep2.toTuple(), 3)

    def testMakeEllipse(self):
        el = Wire.makeEllipse(
            1, 2, Vector(0, 0, 0), Vector(0, 0, 1), Vector(1, 0, 0), 0, 90, 45, True,
        )

        self.assertTrue(el.IsClosed())
        self.assertTrue(el.isValid())

    def testSweep(self):
        """
        Tests the operation of sweeping a wire(s) along a path
        """
        pts = [(0, 0), (0, 1), (1, 2), (2, 4)]

        # Spline path
        path = Workplane("XZ").spline(pts)

        # Test defaults
        result = Workplane("XY").circle(1.0).sweep(path)
        self.assertEqual(3, result.faces().size())
        self.assertEqual(3, result.edges().size())

        # Test with makeSolid False
        result = Workplane("XY").circle(1.0).sweep(path, makeSolid=False)
        self.assertEqual(1, result.faces().size())
        self.assertEqual(3, result.edges().size())

        # Test with isFrenet True
        result = Workplane("XY").circle(1.0).sweep(path, isFrenet=True)
        self.assertEqual(3, result.faces().size())
        self.assertEqual(3, result.edges().size())

        # Test with makeSolid False and isFrenet True
        result = Workplane("XY").circle(1.0).sweep(path, makeSolid=False, isFrenet=True)
        self.assertEqual(1, result.faces().size())
        self.assertEqual(3, result.edges().size())

        # Test rectangle with defaults
        result = Workplane("XY").rect(1.0, 1.0).sweep(path)
        self.assertEqual(6, result.faces().size())
        self.assertEqual(12, result.edges().size())

        # Polyline path
        path = Workplane("XZ").polyline(pts)

        # Test defaults
        result = Workplane("XY").circle(0.1).sweep(path, transition="transformed")
        self.assertEqual(5, result.faces().size())
        self.assertEqual(7, result.edges().size())

        # Polyline path and one inner profiles
        path = Workplane("XZ").polyline(pts)

        # Test defaults
        result = (
            Workplane("XY")
            .circle(0.2)
            .circle(0.1)
            .sweep(path, transition="transformed")
        )
        self.assertEqual(8, result.faces().size())
        self.assertEqual(14, result.edges().size())

        # Polyline path and different transition settings
        for t in ("transformed", "right", "round"):
            path = Workplane("XZ").polyline(pts)

            result = (
                Workplane("XY")
                .circle(0.2)
                .rect(0.2, 0.1)
                .rect(0.1, 0.2)
                .sweep(path, transition=t)
            )
            self.assertTrue(result.solids().val().isValid())

        # Polyline path and multiple inner profiles
        path = Workplane("XZ").polyline(pts)

        # Test defaults
        result = (
            Workplane("XY")
            .circle(0.2)
            .rect(0.2, 0.1)
            .rect(0.1, 0.2)
            .circle(0.1)
            .sweep(path)
        )
        self.assertTrue(result.solids().val().isValid())

        # Arc path
        path = Workplane("XZ").threePointArc((1.0, 1.5), (0.0, 1.0))

        # Test defaults
        result = Workplane("XY").circle(0.1).sweep(path)
        self.assertEqual(3, result.faces().size())
        self.assertEqual(3, result.edges().size())

    def testMultisectionSweep(self):
        """
        Tests the operation of sweeping along a list of wire(s) along a path
        """

        # X axis line length 20.0
        path = Workplane("XZ").moveTo(-10, 0).lineTo(10, 0)

        # Sweep a circle from diameter 2.0 to diameter 1.0 to diameter 2.0 along X axis length 10.0 + 10.0
        defaultSweep = (
            Workplane("YZ")
            .workplane(offset=-10.0)
            .circle(2.0)
            .workplane(offset=10.0)
            .circle(1.0)
            .workplane(offset=10.0)
            .circle(2.0)
            .sweep(path, multisection=True)
        )

        # We can sweep thrue different shapes
        recttocircleSweep = (
            Workplane("YZ")
            .workplane(offset=-10.0)
            .rect(2.0, 2.0)
            .workplane(offset=8.0)
            .circle(1.0)
            .workplane(offset=4.0)
            .circle(1.0)
            .workplane(offset=8.0)
            .rect(2.0, 2.0)
            .sweep(path, multisection=True)
        )

        circletorectSweep = (
            Workplane("YZ")
            .workplane(offset=-10.0)
            .circle(1.0)
            .workplane(offset=7.0)
            .rect(2.0, 2.0)
            .workplane(offset=6.0)
            .rect(2.0, 2.0)
            .workplane(offset=7.0)
            .circle(1.0)
            .sweep(path, multisection=True)
        )

        # Placement of the Shape is important otherwise could produce unexpected shape
        specialSweep = (
            Workplane("YZ")
            .circle(1.0)
            .workplane(offset=10.0)
            .rect(2.0, 2.0)
            .sweep(path, multisection=True)
        )

        # Switch to an arc for the path : line l=5.0 then half circle r=4.0 then line l=5.0
        path = (
            Workplane("XZ")
            .moveTo(-5, 4)
            .lineTo(0, 4)
            .threePointArc((4, 0), (0, -4))
            .lineTo(-5, -4)
        )

        # Placement of different shapes should follow the path
        # cylinder r=1.5 along first line
        # then sweep allong arc from r=1.5 to r=1.0
        # then cylinder r=1.0 along last line
        arcSweep = (
            Workplane("YZ")
            .workplane(offset=-5)
            .moveTo(0, 4)
            .circle(1.5)
            .workplane(offset=5)
            .circle(1.5)
            .moveTo(0, -8)
            .circle(1.0)
            .workplane(offset=-5)
            .circle(1.0)
            .sweep(path, multisection=True)
        )

        # Test and saveModel
        self.assertEqual(1, defaultSweep.solids().size())
        self.assertEqual(1, circletorectSweep.solids().size())
        self.assertEqual(1, recttocircleSweep.solids().size())
        self.assertEqual(1, specialSweep.solids().size())
        self.assertEqual(1, arcSweep.solids().size())
        self.saveModel(defaultSweep)

    def testTwistExtrude(self):
        """
        Tests extrusion while twisting through an angle.
        """
        profile = Workplane("XY").rect(10, 10)
        r = profile.twistExtrude(10, 45, False)

        self.assertEqual(6, r.faces().size())

    def testTwistExtrudeCombine(self):
        """
        Tests extrusion while twisting through an angle, combining with other solids.
        """
        profile = Workplane("XY").rect(10, 10)
        r = profile.twistExtrude(10, 45)

        self.assertEqual(6, r.faces().size())

    def testRectArray(self):
        NUMX = 3
        NUMY = 3
        s = (
            Workplane("XY")
            .box(40, 40, 5, centered=(True, True, True))
            .faces(">Z")
            .workplane()
            .rarray(8.0, 8.0, NUMX, NUMY, True)
            .circle(2.0)
            .extrude(2.0)
        )
        # s = Workplane("XY").box(40,40,5,centered=(True,True,True)).faces(">Z").workplane().circle(2.0).extrude(2.0)
        self.saveModel(s)
        # 6 faces for the box, 2 faces for each cylinder
        self.assertEqual(6 + NUMX * NUMY * 2, s.faces().size())

        with raises(ValueError):
            Workplane().rarray(0, 0, NUMX, NUMY, True)

    def testPolarArray(self):
        radius = 10

        # Test for proper number of elements
        s = Workplane("XY").polarArray(radius, 0, 180, 1)
        self.assertEqual(1, s.size())
        s = Workplane("XY").polarArray(radius, 0, 180, 6)
        self.assertEqual(6, s.size())

        to_x = lambda l: l.wrapped.Transformation().TranslationPart().X()
        to_y = lambda l: l.wrapped.Transformation().TranslationPart().Y()
        to_angle = (
            lambda l: l.wrapped.Transformation().GetRotation().GetRotationAngle()
            * 180.0
            / math.pi
        )

        # Test for proper placement when fill == True
        s = Workplane("XY").polarArray(radius, 0, 180, 3)
        self.assertAlmostEqual(0, to_y(s.objects[1]))
        self.assertAlmostEqual(radius, to_x(s.objects[1]))

        # Test for proper placement when angle to fill is multiple of 360 deg
        s = Workplane("XY").polarArray(radius, 0, 360, 4)
        self.assertAlmostEqual(0, to_y(s.objects[1]))
        self.assertAlmostEqual(radius, to_x(s.objects[1]))

        # Test for proper placement when fill == False
        s = Workplane("XY").polarArray(radius, 0, 90, 3, fill=False)
        self.assertAlmostEqual(0, to_y(s.objects[1]))
        self.assertAlmostEqual(radius, to_x(s.objects[1]))

        # Test for proper operation of startAngle
        s = Workplane("XY").polarArray(radius, 90, 180, 3)
        self.assertAlmostEqual(radius, to_x(s.objects[0]))
        self.assertAlmostEqual(0, to_y(s.objects[0]))

        # Test for local rotation
        s = Workplane().polarArray(radius, 0, 180, 3)
        self.assertAlmostEqual(0, to_angle(s.objects[0]))
        self.assertAlmostEqual(90, to_angle(s.objects[1]))

        s = Workplane().polarArray(radius, 0, 180, 3, rotate=False)
        self.assertAlmostEqual(0, to_angle(s.objects[0]))
        self.assertAlmostEqual(0, to_angle(s.objects[1]))

    def testNestedCircle(self):
        s = (
            Workplane("XY")
            .box(40, 40, 5)
            .pushPoints([(10, 0), (0, 10)])
            .circle(4)
            .circle(2)
            .extrude(4)
        )
        self.saveModel(s)
        self.assertEqual(14, s.faces().size())

    def testConcentricEllipses(self):
        concentricEllipses = (
            Workplane("XY").center(10, 20).ellipse(100, 10).center(0, 0).ellipse(50, 5)
        )
        v = concentricEllipses.vertices().objects[0]
        self.assertTupleAlmostEquals((v.X, v.Y), (10 + 50, 20), 3)

    def testLegoBrick(self):
        # test making a simple lego brick
        # which of the below

        # inputs
        lbumps = 8
        wbumps = 2

        # lego brick constants
        P = 8.0  # nominal pitch
        c = 0.1  # clearance on each brick side
        H = 1.2 * P  # nominal height of a brick
        bumpDiam = 4.8  # the standard bump diameter
        # the nominal thickness of the walls, normally 1.5
        t = (P - (2 * c) - bumpDiam) / 2.0

        postDiam = P - t  # works out to 6.5
        total_length = lbumps * P - 2.0 * c
        total_width = wbumps * P - 2.0 * c

        # build the brick
        s = Workplane("XY").box(total_length, total_width, H)  # make the base
        s = s.faces("<Z").shell(-1.0 * t)  # shell inwards not outwards
        s = (
            s.faces(">Z")
            .workplane()
            .rarray(P, P, lbumps, wbumps, True)
            .circle(bumpDiam / 2.0)
            .extrude(1.8)
        )  # make the bumps on the top

        # add posts on the bottom. posts are different diameter depending on geometry
        # solid studs for 1 bump, tubes for multiple, none for 1x1
        # this is cheating a little-- how to select the inner face from the shell?
        tmp = s.faces("<Z").workplane(invert=True)

        if lbumps > 1 and wbumps > 1:
            tmp = (
                tmp.rarray(P, P, lbumps - 1, wbumps - 1, center=True)
                .circle(postDiam / 2.0)
                .circle(bumpDiam / 2.0)
                .extrude(H - t)
            )
        elif lbumps > 1:
            tmp = tmp.rarray(P, P, lbumps - 1, 1, center=True).circle(t).extrude(H - t)
        elif wbumps > 1:
            tmp = tmp.rarray(P, P, 1, wbumps - 1, center=True).circle(t).extrude(H - t)

        self.saveModel(s)

    def testAngledHoles(self):
        s = (
            Workplane("front")
            .box(4.0, 4.0, 0.25)
            .faces(">Z")
            .workplane()
            .transformed(offset=Vector(0, -1.5, 1.0), rotate=Vector(60, 0, 0))
            .rect(1.5, 1.5, forConstruction=True)
            .vertices()
            .hole(0.25)
        )
        self.saveModel(s)
        self.assertEqual(10, s.faces().size())

    def testTranslateSolid(self):
        c = CQ(makeUnitCube())
        self.assertAlmostEqual(0.0, c.faces("<Z").vertices().item(0).val().Z, 3)

        # TODO: it might be nice to provide a version of translate that modifies the existing geometry too
        d = c.translate(Vector(0, 0, 1.5))
        self.assertAlmostEqual(1.5, d.faces("<Z").vertices().item(0).val().Z, 3)

    def testTranslateWire(self):
        c = CQ(makeUnitSquareWire())
        self.assertAlmostEqual(0.0, c.edges().vertices().item(0).val().Z, 3)
        d = c.translate(Vector(0, 0, 1.5))
        self.assertAlmostEqual(1.5, d.edges().vertices().item(0).val().Z, 3)

    def testSolidReferencesCombine(self):
        "test that solid references are preserved correctly"
        c = CQ(makeUnitCube())  # the cube is the context solid
        self.assertEqual(6, c.faces().size())  # cube has six faces

        r = (
            c.faces(">Z").workplane().circle(0.125).extrude(0.5, True)
        )  # make a boss, not updating the original
        self.assertEqual(8, r.faces().size())  # just the boss faces
        self.assertEqual(6, c.faces().size())  # original is not modified

    def testSolidReferencesCombineTrue(self):
        s = Workplane(Plane.XY())
        r = s.rect(2.0, 2.0).extrude(0.5)
        # the result of course has 6 faces
        self.assertEqual(6, r.faces().size())
        # the original workplane does not, because it did not have a solid initially
        self.assertEqual(0, s.faces().size())

        t = r.faces(">Z").workplane().rect(0.25, 0.25).extrude(0.5, True)
        # of course the result has 11 faces
        self.assertEqual(11, t.faces().size())
        # r (being the parent) remains unmodified
        self.assertEqual(6, r.faces().size())
        self.saveModel(r)

    def testSolidReferenceCombineFalse(self):
        s = Workplane(Plane.XY())
        r = s.rect(2.0, 2.0).extrude(0.5)
        # the result of course has 6 faces
        self.assertEqual(6, r.faces().size())
        # the original workplane does not, because it did not have a solid initially
        self.assertEqual(0, s.faces().size())

        t = r.faces(">Z").workplane().rect(0.25, 0.25).extrude(0.5, False)
        # result has 6 faces, becuase it was not combined with the original
        self.assertEqual(6, t.faces().size())
        self.assertEqual(6, r.faces().size())  # original is unmodified as well
        # subseuent opertions use that context solid afterwards

    def testSimpleWorkplane(self):
        """
            A simple square part with a hole in it
        """
        s = Workplane(Plane.XY())
        r = (
            s.rect(2.0, 2.0)
            .extrude(0.5)
            .faces(">Z")
            .workplane()
            .circle(0.25)
            .cutBlind(-1.0)
        )

        self.saveModel(r)
        self.assertEqual(7, r.faces().size())

    def testMultiFaceWorkplane(self):
        """
        Test Creation of workplane from multiple co-planar face
        selection.
        """
        s = Workplane("XY").box(1, 1, 1).faces(">Z").rect(1, 0.5).cutBlind(-0.2)

        w = s.faces(">Z").workplane()
        o = w.val()  # origin of the workplane
        self.assertAlmostEqual(o.x, 0.0, 3)
        self.assertAlmostEqual(o.y, 0.0, 3)
        self.assertAlmostEqual(o.z, 0.5, 3)

    def testTriangularPrism(self):
        s = Workplane("XY").lineTo(1, 0).lineTo(1, 1).close().extrude(0.2)
        self.saveModel(s)

    def testMultiWireWorkplane(self):
        """
            A simple square part with a hole in it-- but this time done as a single extrusion
            with two wires, as opposed to s cut
        """
        s = Workplane(Plane.XY())
        r = s.rect(2.0, 2.0).circle(0.25).extrude(0.5)

        self.saveModel(r)
        self.assertEqual(7, r.faces().size())

    def testConstructionWire(self):
        """
            Tests a wire with several holes, that are based on the vertices of a square
            also tests using a workplane plane other than XY
        """
        s = Workplane(Plane.YZ())
        r = (
            s.rect(2.0, 2.0)
            .rect(1.3, 1.3, forConstruction=True)
            .vertices()
            .circle(0.125)
            .extrude(0.5)
        )
        self.saveModel(r)
        # 10 faces-- 6 plus 4 holes, the vertices of the second rect.
        self.assertEqual(10, r.faces().size())

    def testTwoWorkplanes(self):
        """
            Tests a model that uses more than one workplane
        """
        # base block
        s = Workplane(Plane.XY())

        # TODO: this syntax is nice, but the iteration might not be worth
        # the complexity.
        # the simpler and slightly longer version would be:
        #    r = s.rect(2.0,2.0).rect(1.3,1.3,forConstruction=True).vertices()
        #    for c in r.all():
        #           c.circle(0.125).extrude(0.5,True)
        r = (
            s.rect(2.0, 2.0)
            .rect(1.3, 1.3, forConstruction=True)
            .vertices()
            .circle(0.125)
            .extrude(0.5)
        )

        # side hole, blind deep 1.9
        t = r.faces(">Y").workplane().circle(0.125).cutBlind(-1.9)
        self.saveModel(t)
        self.assertEqual(12, t.faces().size())

    def testCut(self):
        """
        Tests the cut function by itself to catch the case where a Solid object is passed.
        """
        s = Workplane(Plane.XY())
        currentS = s.rect(2.0, 2.0).extrude(0.5)
        toCut = s.rect(1.0, 1.0).extrude(0.5)

        resS = currentS.cut(toCut.val())

        self.assertEqual(10, resS.faces().size())

        with self.assertRaises(ValueError):
            currentS.cut(toCut.faces().val())

    def testIntersect(self):
        """
        Tests the intersect function.
        """
        s = Workplane(Plane.XY())
        currentS = s.rect(2.0, 2.0).extrude(0.5)
        toIntersect = s.rect(1.0, 1.0).extrude(1)

        resS = currentS.intersect(toIntersect.val())

        self.assertEqual(6, resS.faces().size())
        self.assertAlmostEqual(resS.val().Volume(), 0.5)

        resS = currentS.intersect(toIntersect)

        self.assertEqual(6, resS.faces().size())
        self.assertAlmostEqual(resS.val().Volume(), 0.5)

        b1 = Workplane("XY").box(1, 1, 1)
        b2 = Workplane("XY", origin=(0, 0, 0.5)).box(1, 1, 1)
        resS = b1.intersect(b2)

        self.assertAlmostEqual(resS.val().Volume(), 0.5)

        with self.assertRaises(ValueError):
            b1.intersect(b2.faces().val())

    def testBoundingBox(self):
        """
        Tests the boudingbox center of a model
        """
        result0 = (
            Workplane("XY")
            .moveTo(10, 0)
            .lineTo(5, 0)
            .threePointArc((3.9393, 0.4393), (3.5, 1.5))
            .threePointArc((3.0607, 2.5607), (2, 3))
            .lineTo(1.5, 3)
            .threePointArc((0.4393, 3.4393), (0, 4.5))
            .lineTo(0, 13.5)
            .threePointArc((0.4393, 14.5607), (1.5, 15))
            .lineTo(28, 15)
            .lineTo(28, 13.5)
            .lineTo(24, 13.5)
            .lineTo(24, 11.5)
            .lineTo(27, 11.5)
            .lineTo(27, 10)
            .lineTo(22, 10)
            .lineTo(22, 13.2)
            .lineTo(14.5, 13.2)
            .lineTo(14.5, 10)
            .lineTo(12.5, 10)
            .lineTo(12.5, 13.2)
            .lineTo(5.5, 13.2)
            .lineTo(5.5, 2)
            .threePointArc((5.793, 1.293), (6.5, 1))
            .lineTo(10, 1)
            .close()
        )
        result = result0.extrude(100)
        bb_center = result.val().BoundingBox().center
        self.saveModel(result)
        self.assertAlmostEqual(14.0, bb_center.x, 3)
        self.assertAlmostEqual(7.5, bb_center.y, 3)
        self.assertAlmostEqual(50.0, bb_center.z, 3)

        # The following will raise with the default tolerance of TOL 1e-2
        bb = result.val().BoundingBox(tolerance=1e-3)
        self.assertAlmostEqual(0.0, bb.xmin, 2)
        self.assertAlmostEqual(28, bb.xmax, 2)
        self.assertAlmostEqual(0.0, bb.ymin, 2)
        self.assertAlmostEqual(15.0, bb.ymax, 2)
        self.assertAlmostEqual(0.0, bb.zmin, 2)
        self.assertAlmostEqual(100.0, bb.zmax, 2)

    def testCutThroughAll(self):
        """
            Tests a model that uses more than one workplane
        """
        # base block
        s = Workplane(Plane.XY())
        r = (
            s.rect(2.0, 2.0)
            .rect(1.3, 1.3, forConstruction=True)
            .vertices()
            .circle(0.125)
            .extrude(0.5)
        )

        # thru all without explicit face selection
        t = r.circle(0.5).cutThruAll()
        self.assertEqual(11, t.faces().size())

        # side hole, thru all
        t = t.faces(">Y").workplane().circle(0.125).cutThruAll()
        self.saveModel(t)
        self.assertEqual(13, t.faces().size())

    def testCutToFaceOffsetNOTIMPLEMENTEDYET(self):
        """
            Tests cutting up to a given face, or an offset from a face
        """
        # base block
        s = Workplane(Plane.XY())
        r = (
            s.rect(2.0, 2.0)
            .rect(1.3, 1.3, forConstruction=True)
            .vertices()
            .circle(0.125)
            .extrude(0.5)
        )

        # side hole, up to 0.1 from the last face
        try:
            t = (
                r.faces(">Y")
                .workplane()
                .circle(0.125)
                .cutToOffsetFromFace(r.faces().mminDist(Dir.Y), 0.1)
            )
            # should end up being a blind hole
            self.assertEqual(10, t.faces().size())
            t.first().val().exportStep("c:/temp/testCutToFace.STEP")
        except:
            pass
            # Not Implemented Yet

    def testWorkplaneOnExistingSolid(self):
        "Tests extruding on an existing solid"
        c = (
            CQ(makeUnitCube())
            .faces(">Z")
            .workplane()
            .circle(0.25)
            .circle(0.125)
            .extrude(0.25)
        )
        self.saveModel(c)
        self.assertEqual(10, c.faces().size())

    def testWorkplaneCenterMove(self):
        # this workplane is centered at x=0.5,y=0.5, the center of the upper face
        s = (
            Workplane("XY").box(1, 1, 1).faces(">Z").workplane().center(-0.5, -0.5)
        )  # move the center to the corner

        t = s.circle(0.25).extrude(0.2)  # make a boss
        self.assertEqual(9, t.faces().size())
        self.saveModel(t)

    def testBasicLines(self):
        "Make a triangluar boss"
        global OUTDIR
        s = Workplane(Plane.XY())

        # TODO:  extrude() should imply wire() if not done already
        # most users dont understand what a wire is, they are just drawing

        r = s.lineTo(1.0, 0).lineTo(0, 1.0).close().wire().extrude(0.25)
        r.val().exportStep(os.path.join(OUTDIR, "testBasicLinesStep1.STEP"))

        # no faces on the original workplane
        self.assertEqual(0, s.faces().size())
        # 5 faces on newly created object
        self.assertEqual(5, r.faces().size())

        # now add a circle through a side face
        r1 = r.faces("+XY").workplane().circle(0.08).cutThruAll()
        self.assertEqual(6, r1.faces().size())
        r1.val().exportStep(os.path.join(OUTDIR, "testBasicLinesXY.STEP"))

        # now add a circle through a top
        r2 = r1.faces("+Z").workplane().circle(0.08).cutThruAll()
        self.assertEqual(9, r2.faces().size())
        r2.val().exportStep(os.path.join(OUTDIR, "testBasicLinesZ.STEP"))

        self.saveModel(r2)

    def test2DDrawing(self):
        """
        Draw things like 2D lines and arcs, should be expanded later to include all 2D constructs
        """
        s = Workplane(Plane.XY())
        r = (
            s.lineTo(1.0, 0.0)
            .lineTo(1.0, 1.0)
            .threePointArc((1.0, 1.5), (0.0, 1.0))
            .lineTo(0.0, 0.0)
            .moveTo(1.0, 0.0)
            .lineTo(2.0, 0.0)
            .lineTo(2.0, 2.0)
            .threePointArc((2.0, 2.5), (0.0, 2.0))
            .lineTo(-2.0, 2.0)
            .lineTo(-2.0, 0.0)
            .close()
        )

        self.assertEqual(1, r.wires().size())

        # Test the *LineTo functions
        s = Workplane(Plane.XY())
        r = s.hLineTo(1.0).vLineTo(1.0).hLineTo(0.0).close()

        self.assertEqual(1, r.wire().size())
        self.assertEqual(4, r.edges().size())

        # Test the *Line functions
        s = Workplane(Plane.XY())
        r = s.hLine(1.0).vLine(1.0).hLine(-1.0).close()

        self.assertEqual(1, r.wire().size())
        self.assertEqual(4, r.edges().size())

        # Test the move function
        s = Workplane(Plane.XY())
        r = s.move(1.0, 1.0).hLine(1.0).vLine(1.0).hLine(-1.0).close()

        self.assertEqual(1, r.wire().size())
        self.assertEqual(4, r.edges().size())
        self.assertEqual(
            (1.0, 1.0),
            (
                r.vertices(selectors.NearestToPointSelector((0.0, 0.0, 0.0)))
                .first()
                .val()
                .X,
                r.vertices(selectors.NearestToPointSelector((0.0, 0.0, 0.0)))
                .first()
                .val()
                .Y,
            ),
        )

        # Test the sagittaArc and radiusArc functions
        a1 = Workplane(Plane.YZ()).threePointArc((5, 1), (10, 0))
        a2 = Workplane(Plane.YZ()).sagittaArc((10, 0), -1)
        a3 = Workplane(Plane.YZ()).threePointArc((6, 2), (12, 0))
        a4 = Workplane(Plane.YZ()).radiusArc((12, 0), -10)

        assert a1.edges().first().val().geomType() == "CIRCLE"
        assert a2.edges().first().val().geomType() == "CIRCLE"
        assert a3.edges().first().val().geomType() == "CIRCLE"
        assert a4.edges().first().val().geomType() == "CIRCLE"

        assert a1.edges().first().val().Length() == a2.edges().first().val().Length()
        assert a3.edges().first().val().Length() == a4.edges().first().val().Length()

    def testPolarLines(self):
        """
        Draw some polar lines and check expected results
        """

        # Test the PolarLine* functions
        s = Workplane(Plane.XY())
        r = (
            s.polarLine(10, 45)
            .polarLineTo(10, -45)
            .polarLine(10, -180)
            .polarLine(-10, -90)
            .close()
        )

        # a single wire, 5 edges
        self.assertEqual(1, r.wires().size())
        self.assertEqual(5, r.wires().edges().size())

    def testLargestDimension(self):
        """
        Tests the largestDimension function when no solids are on the stack and when there are
        """
        r = Workplane("XY").box(1, 1, 1)
        dim = r.largestDimension()

        self.assertAlmostEqual(1.76, dim, 1)

        r = Workplane("XY").rect(1, 1).extrude(1)
        dim = r.largestDimension()

        self.assertAlmostEqual(1.76, dim, 1)

        r = Workplane("XY")
        dim = r.largestDimension()

        self.assertEqual(-1, dim)

    def testOccBottle(self):
        """
        Make the OCC bottle example.
        """

        L = 20.0
        w = 6.0
        t = 3.0

        s = Workplane(Plane.XY())
        # draw half the profile of the bottle
        p = (
            s.center(-L / 2.0, 0)
            .vLine(w / 2.0)
            .threePointArc((L / 2.0, w / 2.0 + t), (L, w / 2.0))
            .vLine(-w / 2.0)
            .mirrorX()
            .extrude(30.0, True)
        )

        # make the neck
        p.faces(">Z").workplane().circle(3.0).extrude(
            2.0, True
        )  # .edges().fillet(0.05)

        # make a shell
        p.faces(">Z").shell(0.3)
        self.saveModel(p)

    def testSplineShape(self):
        """
            Tests making a shape with an edge that is a spline
        """
        s = Workplane(Plane.XY())
        sPnts = [
            (2.75, 1.5),
            (2.5, 1.75),
            (2.0, 1.5),
            (1.5, 1.0),
            (1.0, 1.25),
            (0.5, 1.0),
            (0, 1.0),
        ]
        r = s.lineTo(3.0, 0).lineTo(3.0, 1.0).spline(sPnts).close()
        r = r.extrude(0.5)
        self.saveModel(r)

    def testSimpleMirror(self):
        """
            Tests a simple mirroring operation
        """
        s = (
            Workplane("XY")
            .lineTo(2, 2)
            .threePointArc((3, 1), (2, 0))
            .mirrorX()
            .extrude(0.25)
        )
        self.assertEqual(6, s.faces().size())
        self.saveModel(s)

    def testUnorderedMirror(self):
        """
        Tests whether or not a wire can be mirrored if its mirror won't connect to it
        """
        r = 20
        s = 7
        t = 1.5

        points = [
            (0, 0),
            (0, t / 2),
            (r / 2 - 1.5 * t, r / 2 - t),
            (s / 2, r / 2 - t),
            (s / 2, r / 2),
            (r / 2, r / 2),
            (r / 2, s / 2),
            (r / 2 - t, s / 2),
            (r / 2 - t, r / 2 - 1.5 * t),
            (t / 2, 0),
        ]

        r = Workplane("XY").polyline(points).mirrorX()

        self.assertEqual(1, r.wires().size())
        self.assertEqual(18, r.edges().size())

        # try the same with includeCurrent=True
        r = Workplane("XY").polyline(points[1:], includeCurrent=True).mirrorX()

        self.assertEqual(1, r.wires().size())
        self.assertEqual(18, r.edges().size())

    def testChainedMirror(self):
        """
        Tests whether or not calling mirrorX().mirrorY() works correctly
        """
        r = 20
        s = 7
        t = 1.5

        points = [
            (0, t / 2),
            (r / 2 - 1.5 * t, r / 2 - t),
            (s / 2, r / 2 - t),
            (s / 2, r / 2),
            (r / 2, r / 2),
            (r / 2, s / 2),
            (r / 2 - t, s / 2),
            (r / 2 - t, r / 2 - 1.5 * t),
            (t / 2, 0),
        ]

        r = Workplane("XY").polyline(points).mirrorX().mirrorY().extrude(1).faces(">Z")

        self.assertEqual(1, r.wires().size())
        self.assertEqual(32, r.edges().size())

    # TODO: Re-work testIbeam test below now that chaining works
    # TODO: Add toLocalCoords and toWorldCoords tests

    def testIbeam(self):
        """
            Make an ibeam. demonstrates fancy mirroring
        """
        s = Workplane(Plane.XY())
        L = 100.0
        H = 20.0
        W = 20.0

        t = 1.0
        # TODO: for some reason doing 1/4 of the profile and mirroring twice ( .mirrorX().mirrorY() )
        # did not work, due to a bug in freecad-- it was losing edges when creating a composite wire.
        # i just side-stepped it for now

        pts = [
            (0, 0),
            (0, H / 2.0),
            (W / 2.0, H / 2.0),
            (W / 2.0, (H / 2.0 - t)),
            (t / 2.0, (H / 2.0 - t)),
            (t / 2.0, (t - H / 2.0)),
            (W / 2.0, (t - H / 2.0)),
            (W / 2.0, H / -2.0),
            (0, H / -2.0),
        ]
        r = s.polyline(pts).mirrorY()  # these other forms also work
        res = r.extrude(L)
        self.saveModel(res)

    def testCone(self):
        """
        Tests that a simple cone works
        """
        s = Solid.makeCone(0, 1.0, 2.0)
        t = CQ(s)
        self.saveModel(t)
        self.assertEqual(2, t.faces().size())

    def testFillet(self):
        """
        Tests filleting edges on a solid
        """
        c = (
            CQ(makeUnitCube())
            .faces(">Z")
            .workplane()
            .circle(0.25)
            .extrude(0.25, True)
            .edges("|Z")
            .fillet(0.2)
        )
        self.saveModel(c)
        self.assertEqual(12, c.faces().size())

    def testChamfer(self):
        """
        Test chamfer API with a box shape
        """
        cube = CQ(makeUnitCube()).faces(">Z").chamfer(0.1)
        self.saveModel(cube)
        self.assertEqual(10, cube.faces().size())

    def testChamferAsymmetrical(self):
        """
        Test chamfer API with a box shape for asymmetrical lengths
        """
        cube = CQ(makeUnitCube()).faces(">Z").chamfer(0.1, 0.2)
        self.saveModel(cube)
        self.assertEqual(10, cube.faces().size())

        # test if edge lengths are different
        edge = cube.edges(">Z").vals()[0]
        self.assertAlmostEqual(0.6, edge.Length(), 3)
        edge = cube.edges("|Z").vals()[0]
        self.assertAlmostEqual(0.9, edge.Length(), 3)

    def testChamferCylinder(self):
        """
        Test chamfer API with a cylinder shape
        """
        cylinder = Workplane("XY").circle(1).extrude(1).faces(">Z").chamfer(0.1)
        self.saveModel(cylinder)
        self.assertEqual(4, cylinder.faces().size())

    def testCounterBores(self):
        """
        Tests making a set of counterbored holes in a face
        """
        c = CQ(makeCube(3.0))
        pnts = [(-1.0, -1.0), (0.0, 0.0), (1.0, 1.0)]
        c = c.faces(">Z").workplane().pushPoints(pnts).cboreHole(0.1, 0.25, 0.25, 0.75)
        self.assertEqual(18, c.faces().size())
        self.saveModel(c)

        # Tests the case where the depth of the cboreHole is not specified
        c2 = CQ(makeCube(3.0))
        c2 = c2.faces(">Z").workplane().pushPoints(pnts).cboreHole(0.1, 0.25, 0.25)
        self.assertEqual(15, c2.faces().size())

    def testCounterSinks(self):
        """
            Tests countersinks
        """
        s = Workplane(Plane.XY())
        result = (
            s.rect(2.0, 4.0)
            .extrude(0.5)
            .faces(">Z")
            .workplane()
            .rect(1.5, 3.5, forConstruction=True)
            .vertices()
            .cskHole(0.125, 0.25, 82, depth=None)
        )
        self.saveModel(result)

    def testSplitKeepingHalf(self):
        """
        Tests splitting a solid
        """

        # drill a hole in the side
        c = CQ(makeUnitCube()).faces(">Z").workplane().circle(0.25).cutThruAll()

        self.assertEqual(7, c.faces().size())

        # now cut it in half sideways
        result = c.faces(">Y").workplane(-0.5).split(keepTop=True)
        self.saveModel(result)
        self.assertEqual(8, result.faces().size())

    def testSplitKeepingBoth(self):
        """
        Tests splitting a solid
        """

        # drill a hole in the side
        c = CQ(makeUnitCube()).faces(">Z").workplane().circle(0.25).cutThruAll()
        self.assertEqual(7, c.faces().size())

        # now cut it in half sideways
        result = c.faces(">Y").workplane(-0.5).split(keepTop=True, keepBottom=True)

        # stack will have both halves, original will be unchanged
        # two solids are on the stack, eac
        self.assertEqual(2, result.solids().size())
        self.assertEqual(8, result.solids().item(0).faces().size())
        self.assertEqual(8, result.solids().item(1).faces().size())

    def testSplitKeepingBottom(self):
        """
        Tests splitting a solid improperly
        """
        # Drill a hole in the side
        c = CQ(makeUnitCube()).faces(">Z").workplane().circle(0.25).cutThruAll()
        self.assertEqual(7, c.faces().size())

        # Now cut it in half sideways
        result = c.faces(">Y").workplane(-0.5).split(keepTop=False, keepBottom=True)

        # stack will have both halves, original will be unchanged
        # one solid is on the stack
        self.assertEqual(1, result.solids().size())
        self.assertEqual(8, result.solids().item(0).faces().size())

    def testBoxDefaults(self):
        """
        Tests creating a single box
        """
        s = Workplane("XY").box(2, 3, 4)
        self.assertEqual(1, s.solids().size())
        self.saveModel(s)

    def testSimpleShell(self):
        """
            Create s simple box
        """
        s1 = Workplane("XY").box(2, 2, 2).faces("+Z").shell(0.05)
        self.saveModel(s1)
        self.assertEqual(23, s1.faces().size())

        s2 = (
            Workplane()
            .ellipse(4, 2)
            .extrude(4)
            .faces(">Z")
            .shell(+2, kind="intersection")
        )
        self.assertEqual(5, s2.faces().size())

        s3 = Workplane().ellipse(4, 2).extrude(4).faces(">Z").shell(+2, kind="arc")
        self.assertEqual(6, s3.faces().size())

    def testClosedShell(self):
        """
            Create a hollow box
        """
        s1 = Workplane("XY").box(2, 2, 2).shell(-0.1)
        self.assertEqual(12, s1.faces().size())
        self.assertTrue(s1.val().isValid())

        s2 = Workplane("XY").box(2, 2, 2).shell(0.1)
        self.assertEqual(32, s2.faces().size())
        self.assertTrue(s2.val().isValid())

        pts = [(1.0, 0.0), (0.3, 0.2), (0.0, 0.0), (0.3, -0.1), (1.0, -0.03)]

        s3 = Workplane().polyline(pts).close().extrude(1).shell(-0.05)
        self.assertTrue(s3.val().isValid())

    def testOpenCornerShell(self):
        s = Workplane("XY").box(1, 1, 1)
        s1 = s.faces("+Z")
        s1.add(s.faces("+Y")).add(s.faces("+X"))
        self.saveModel(s1.shell(0.2))

        # Tests the list option variation of add
        s1 = s.faces("+Z")
        s1.add(s.faces("+Y")).add([s.faces("+X")])

        # Tests the raw object option variation of add
        s1 = s.faces("+Z")
        s1.add(s.faces("+Y")).add(s.faces("+X").val().wrapped)

    def testTopFaceFillet(self):
        s = Workplane("XY").box(1, 1, 1).faces("+Z").edges().fillet(0.1)
        self.assertEqual(s.faces().size(), 10)
        self.saveModel(s)

    def testBoxPointList(self):
        """
        Tests creating an array of boxes
        """
        s = (
            Workplane("XY")
            .rect(4.0, 4.0, forConstruction=True)
            .vertices()
            .box(0.25, 0.25, 0.25, combine=True)
        )
        # 1 object, 4 solids because the object is a compound
        self.assertEqual(4, s.solids().size())
        self.assertEqual(1, s.size())
        self.saveModel(s)

        s = (
            Workplane("XY")
            .rect(4.0, 4.0, forConstruction=True)
            .vertices()
            .box(0.25, 0.25, 0.25, combine=False)
        )
        # 4 objects, 4 solids, because each is a separate solid
        self.assertEqual(4, s.size())
        self.assertEqual(4, s.solids().size())

    def testBoxCombine(self):
        s = (
            Workplane("XY")
            .box(4, 4, 0.5)
            .faces(">Z")
            .workplane()
            .rect(3, 3, forConstruction=True)
            .vertices()
            .box(0.25, 0.25, 0.25, combine=True)
        )

        self.saveModel(s)
        self.assertEqual(1, s.solids().size())  # we should have one big solid
        # should have 26 faces. 6 for the box, and 4x5 for the smaller cubes
        self.assertEqual(26, s.faces().size())

    def testSphereDefaults(self):
        s = Workplane("XY").sphere(10)
        self.saveModel(s)  # Until FreeCAD fixes their sphere operation
        self.assertEqual(1, s.solids().size())
        self.assertEqual(1, s.faces().size())

    def testSphereCustom(self):
        s = Workplane("XY").sphere(
            10, angle1=0, angle2=90, angle3=360, centered=(False, False, False)
        )
        self.saveModel(s)
        self.assertEqual(1, s.solids().size())
        self.assertEqual(2, s.faces().size())

    def testSpherePointList(self):
        s = (
            Workplane("XY")
            .rect(4.0, 4.0, forConstruction=True)
            .vertices()
            .sphere(0.25, combine=False)
        )
        # self.saveModel(s) # Until FreeCAD fixes their sphere operation
        self.assertEqual(4, s.solids().size())
        self.assertEqual(4, s.faces().size())

    def testSphereCombine(self):
        s = (
            Workplane("XY")
            .rect(4.0, 4.0, forConstruction=True)
            .vertices()
            .sphere(2.25, combine=True)
        )
        # self.saveModel(s) # Until FreeCAD fixes their sphere operation
        self.assertEqual(1, s.solids().size())
        self.assertEqual(4, s.faces().size())

    def testWedgeDefaults(self):
        s = Workplane("XY").wedge(10, 10, 10, 5, 5, 5, 5)
        self.saveModel(s)
        self.assertEqual(1, s.solids().size())
        self.assertEqual(5, s.faces().size())
        self.assertEqual(5, s.vertices().size())

    def testWedgeCentering(self):
        s = Workplane("XY").wedge(
            10, 10, 10, 5, 5, 5, 5, centered=(False, False, False)
        )
        # self.saveModel(s)
        self.assertEqual(1, s.solids().size())
        self.assertEqual(5, s.faces().size())
        self.assertEqual(5, s.vertices().size())

    def testWedgePointList(self):
        s = (
            Workplane("XY")
            .rect(4.0, 4.0, forConstruction=True)
            .vertices()
            .wedge(10, 10, 10, 5, 5, 5, 5, combine=False)
        )
        # self.saveModel(s)
        self.assertEqual(4, s.solids().size())
        self.assertEqual(20, s.faces().size())
        self.assertEqual(20, s.vertices().size())

    def testWedgeCombined(self):
        s = (
            Workplane("XY")
            .rect(4.0, 4.0, forConstruction=True)
            .vertices()
            .wedge(10, 10, 10, 5, 5, 5, 5, combine=True)
        )
        # self.saveModel(s)
        self.assertEqual(1, s.solids().size())
        self.assertEqual(12, s.faces().size())
        self.assertEqual(16, s.vertices().size())

    def testQuickStartXY(self):
        s = (
            Workplane(Plane.XY())
            .box(2, 4, 0.5)
            .faces(">Z")
            .workplane()
            .rect(1.5, 3.5, forConstruction=True)
            .vertices()
            .cskHole(0.125, 0.25, 82, depth=None)
        )
        self.assertEqual(1, s.solids().size())
        self.assertEqual(14, s.faces().size())
        self.saveModel(s)

    def testQuickStartYZ(self):
        s = (
            Workplane(Plane.YZ())
            .box(2, 4, 0.5)
            .faces(">X")
            .workplane()
            .rect(1.5, 3.5, forConstruction=True)
            .vertices()
            .cskHole(0.125, 0.25, 82, depth=None)
        )
        self.assertEqual(1, s.solids().size())
        self.assertEqual(14, s.faces().size())
        self.saveModel(s)

    def testQuickStartXZ(self):
        s = (
            Workplane(Plane.XZ())
            .box(2, 4, 0.5)
            .faces(">Y")
            .workplane()
            .rect(1.5, 3.5, forConstruction=True)
            .vertices()
            .cskHole(0.125, 0.25, 82, depth=None)
        )
        self.assertEqual(1, s.solids().size())
        self.assertEqual(14, s.faces().size())
        self.saveModel(s)

    def testDoubleTwistedLoft(self):
        s = (
            Workplane("XY")
            .polygon(8, 20.0)
            .workplane(offset=4.0)
            .transformed(rotate=Vector(0, 0, 15.0))
            .polygon(8, 20)
            .loft()
        )
        s2 = (
            Workplane("XY")
            .polygon(8, 20.0)
            .workplane(offset=-4.0)
            .transformed(rotate=Vector(0, 0, 15.0))
            .polygon(8, 20)
            .loft()
        )
        # self.assertEquals(10,s.faces().size())
        # self.assertEquals(1,s.solids().size())
        s3 = s.combineSolids(s2)
        self.saveModel(s3)

    def testTwistedLoft(self):
        s = (
            Workplane("XY")
            .polygon(8, 20.0)
            .workplane(offset=4.0)
            .transformed(rotate=Vector(0, 0, 15.0))
            .polygon(8, 20)
            .loft()
        )
        self.assertEqual(10, s.faces().size())
        self.assertEqual(1, s.solids().size())
        self.saveModel(s)

    def testUnions(self):
        # duplicates a memory problem of some kind reported when combining lots of objects
        s = Workplane("XY").rect(0.5, 0.5).extrude(5.0)
        o = []
        beginTime = time.time()
        for i in range(15):
            t = Workplane("XY").center(10.0 * i, 0).rect(0.5, 0.5).extrude(5.0)
            o.append(t)

        # union stuff
        for oo in o:
            s = s.union(oo)
        print("Total time %0.3f" % (time.time() - beginTime))

        # Test unioning a Solid object
        s = Workplane(Plane.XY())
        currentS = s.rect(2.0, 2.0).extrude(0.5)
        toUnion = s.rect(1.0, 1.0).extrude(1.0)

        resS = currentS.union(toUnion)

        self.assertEqual(11, resS.faces().size())

        with self.assertRaises(ValueError):
            resS.union(toUnion.faces().val())

    def testCombine(self):
        s = Workplane(Plane.XY())
        objects1 = s.rect(2.0, 2.0).extrude(0.5).faces(">Z").rect(1.0, 1.0).extrude(0.5)

        objects1.combine()

        self.assertEqual(11, objects1.faces().size())

    def testCombineSolidsInLoop(self):
        # duplicates a memory problem of some kind reported when combining lots of objects
        s = Workplane("XY").rect(0.5, 0.5).extrude(5.0)
        o = []
        beginTime = time.time()
        for i in range(15):
            t = Workplane("XY").center(10.0 * i, 0).rect(0.5, 0.5).extrude(5.0)
            o.append(t)

        # append the 'good way'
        for oo in o:
            s.add(oo)
        s = s.combineSolids()

        print("Total time %0.3f" % (time.time() - beginTime))

        self.saveModel(s)

    def testClean(self):
        """
        Tests the `clean()` method which is called automatically.
        """

        # make a cube with a splitter edge on one of the faces
        # autosimplify should remove the splitter
        s = (
            Workplane("XY")
            .moveTo(0, 0)
            .line(5, 0)
            .line(5, 0)
            .line(0, 10)
            .line(-10, 0)
            .close()
            .extrude(10)
        )

        self.assertEqual(6, s.faces().size())

        # test removal of splitter caused by union operation
        s = Workplane("XY").box(10, 10, 10).union(Workplane("XY").box(20, 10, 10))

        self.assertEqual(6, s.faces().size())

        # test removal of splitter caused by extrude+combine operation
        s = (
            Workplane("XY")
            .box(10, 10, 10)
            .faces(">Y")
            .workplane()
            .rect(5, 10, 5)
            .extrude(20)
        )

        self.assertEqual(10, s.faces().size())

        # test removal of splitter caused by double hole operation
        s = (
            Workplane("XY")
            .box(10, 10, 10)
            .faces(">Z")
            .workplane()
            .hole(3, 5)
            .faces(">Z")
            .workplane()
            .hole(3, 10)
        )

        self.assertEqual(7, s.faces().size())

        # test removal of splitter caused by cutThruAll
        s = (
            Workplane("XY")
            .box(10, 10, 10)
            .faces(">Y")
            .workplane()
            .rect(10, 5)
            .cutBlind(-5)
            .faces(">Z")
            .workplane()
            .center(0, 2.5)
            .rect(5, 5)
            .cutThruAll()
        )

        self.assertEqual(18, s.faces().size())

        # test removal of splitter with box
        s = Workplane("XY").box(5, 5, 5).box(10, 5, 2)

        self.assertEqual(14, s.faces().size())

    def testNoClean(self):
        """
        Test the case when clean is disabled.
        """
        # test disabling autoSimplify
        s = (
            Workplane("XY")
            .moveTo(0, 0)
            .line(5, 0)
            .line(5, 0)
            .line(0, 10)
            .line(-10, 0)
            .close()
            .extrude(10, clean=False)
        )
        self.assertEqual(7, s.faces().size())

        s = (
            Workplane("XY")
            .box(10, 10, 10)
            .union(Workplane("XY").box(20, 10, 10), clean=False)
        )
        self.assertEqual(14, s.faces().size())

        s = (
            Workplane("XY")
            .box(10, 10, 10)
            .faces(">Y")
            .workplane()
            .rect(5, 10, 5)
            .extrude(20, clean=False)
        )

        self.assertEqual(12, s.faces().size())

    def testExplicitClean(self):
        """
        Test running of `clean()` method explicitly.
        """
        s = (
            Workplane("XY")
            .moveTo(0, 0)
            .line(5, 0)
            .line(5, 0)
            .line(0, 10)
            .line(-10, 0)
            .close()
            .extrude(10, clean=False)
            .clean()
        )
        self.assertEqual(6, s.faces().size())

    def testPlanes(self):
        """
        Test other planes other than the normal ones (XY, YZ)
        """
        # ZX plane
        s = Workplane(Plane.ZX())
        result = (
            s.rect(2.0, 4.0)
            .extrude(0.5)
            .faces(">Z")
            .workplane()
            .rect(1.5, 3.5, forConstruction=True)
            .vertices()
            .cskHole(0.125, 0.25, 82, depth=None)
        )
        self.saveModel(result)

        # YX plane
        s = Workplane(Plane.YX())
        result = (
            s.rect(2.0, 4.0)
            .extrude(0.5)
            .faces(">Z")
            .workplane()
            .rect(1.5, 3.5, forConstruction=True)
            .vertices()
            .cskHole(0.125, 0.25, 82, depth=None)
        )
        self.saveModel(result)

        # YX plane
        s = Workplane(Plane.YX())
        result = (
            s.rect(2.0, 4.0)
            .extrude(0.5)
            .faces(">Z")
            .workplane()
            .rect(1.5, 3.5, forConstruction=True)
            .vertices()
            .cskHole(0.125, 0.25, 82, depth=None)
        )
        self.saveModel(result)

        # ZY plane
        s = Workplane(Plane.ZY())
        result = (
            s.rect(2.0, 4.0)
            .extrude(0.5)
            .faces(">Z")
            .workplane()
            .rect(1.5, 3.5, forConstruction=True)
            .vertices()
            .cskHole(0.125, 0.25, 82, depth=None)
        )
        self.saveModel(result)

        # front plane
        s = Workplane(Plane.front())
        result = (
            s.rect(2.0, 4.0)
            .extrude(0.5)
            .faces(">Z")
            .workplane()
            .rect(1.5, 3.5, forConstruction=True)
            .vertices()
            .cskHole(0.125, 0.25, 82, depth=None)
        )
        self.saveModel(result)

        # back plane
        s = Workplane(Plane.back())
        result = (
            s.rect(2.0, 4.0)
            .extrude(0.5)
            .faces(">Z")
            .workplane()
            .rect(1.5, 3.5, forConstruction=True)
            .vertices()
            .cskHole(0.125, 0.25, 82, depth=None)
        )
        self.saveModel(result)

        # left plane
        s = Workplane(Plane.left())
        result = (
            s.rect(2.0, 4.0)
            .extrude(0.5)
            .faces(">Z")
            .workplane()
            .rect(1.5, 3.5, forConstruction=True)
            .vertices()
            .cskHole(0.125, 0.25, 82, depth=None)
        )
        self.saveModel(result)

        # right plane
        s = Workplane(Plane.right())
        result = (
            s.rect(2.0, 4.0)
            .extrude(0.5)
            .faces(">Z")
            .workplane()
            .rect(1.5, 3.5, forConstruction=True)
            .vertices()
            .cskHole(0.125, 0.25, 82, depth=None)
        )
        self.saveModel(result)

        # top plane
        s = Workplane(Plane.top())
        result = (
            s.rect(2.0, 4.0)
            .extrude(0.5)
            .faces(">Z")
            .workplane()
            .rect(1.5, 3.5, forConstruction=True)
            .vertices()
            .cskHole(0.125, 0.25, 82, depth=None)
        )
        self.saveModel(result)

        # bottom plane
        s = Workplane(Plane.bottom())
        result = (
            s.rect(2.0, 4.0)
            .extrude(0.5)
            .faces(">Z")
            .workplane()
            .rect(1.5, 3.5, forConstruction=True)
            .vertices()
            .cskHole(0.125, 0.25, 82, depth=None)
        )
        self.saveModel(result)

    def testIsInside(self):
        """
        Testing if one box is inside of another.
        """
        box1 = Workplane(Plane.XY()).box(10, 10, 10)
        box2 = Workplane(Plane.XY()).box(5, 5, 5)

        self.assertFalse(box2.val().BoundingBox().isInside(box1.val().BoundingBox()))
        self.assertTrue(box1.val().BoundingBox().isInside(box2.val().BoundingBox()))

    def testCup(self):
        """
            UOM = "mm"

            #
            # PARAMETERS and PRESETS
            # These parameters can be manipulated by end users
            #
            bottomDiameter = FloatParam(min=10.0,presets={'default':50.0,'tumbler':50.0,'shot':35.0,'tea':50.0,'saucer':100.0},group="Basics", desc="Bottom diameter")
            topDiameter = FloatParam(min=10.0,presets={'default':85.0,'tumbler':85.0,'shot':50.0,'tea':51.0,'saucer':400.0 },group="Basics", desc="Top diameter")
            thickness = FloatParam(min=0.1,presets={'default':2.0,'tumbler':2.0,'shot':2.66,'tea':2.0,'saucer':2.0},group="Basics", desc="Thickness")
            height = FloatParam(min=1.0,presets={'default':80.0,'tumbler':80.0,'shot':59.0,'tea':125.0,'saucer':40.0},group="Basics", desc="Overall height")
            lipradius = FloatParam(min=1.0,presets={'default':1.0,'tumbler':1.0,'shot':0.8,'tea':1.0,'saucer':1.0},group="Basics", desc="Lip Radius")
            bottomThickness = FloatParam(min=1.0,presets={'default':5.0,'tumbler':5.0,'shot':10.0,'tea':10.0,'saucer':5.0},group="Basics", desc="BottomThickness")

            #
            # Your build method. It must return a solid object
            #
            def build():
                br = bottomDiameter.value / 2.0
                tr = topDiameter.value / 2.0
                t = thickness.value
                s1 = Workplane("XY").circle(br).workplane(offset=height.value).circle(tr).loft()
                s2 = Workplane("XY").workplane(offset=bottomThickness.value).circle(br - t ).workplane(offset=height.value - t ).circle(tr - t).loft()

                cup = s1.cut(s2)
                cup.faces(">Z").edges().fillet(lipradius.value)
                return cup
        """

        # for some reason shell doesnt work on this simple shape. how disappointing!
        td = 50.0
        bd = 20.0
        h = 10.0
        t = 1.0
        s1 = Workplane("XY").circle(bd).workplane(offset=h).circle(td).loft()
        s2 = (
            Workplane("XY")
            .workplane(offset=t)
            .circle(bd - (2.0 * t))
            .workplane(offset=(h - t))
            .circle(td - (2.0 * t))
            .loft()
        )
        s3 = s1.cut(s2)
        self.saveModel(s3)

    def testEnclosure(self):
        """
            Builds an electronics enclosure
            Original FreeCAD script: 81 source statements ,not including variables
            This script: 34
        """

        # parameter definitions
        p_outerWidth = 100.0  # Outer width of box enclosure
        p_outerLength = 150.0  # Outer length of box enclosure
        p_outerHeight = 50.0  # Outer height of box enclosure

        p_thickness = 3.0  # Thickness of the box walls
        p_sideRadius = 10.0  # Radius for the curves around the sides of the bo
        # Radius for the curves on the top and bottom edges of the box
        p_topAndBottomRadius = 2.0

        # How far in from the edges the screwposts should be place.
        p_screwpostInset = 12.0
        # nner Diameter of the screwpost holes, should be roughly screw diameter not including threads
        p_screwpostID = 4.0
        # Outer Diameter of the screwposts.\nDetermines overall thickness of the posts
        p_screwpostOD = 10.0

        p_boreDiameter = 8.0  # Diameter of the counterbore hole, if any
        p_boreDepth = 1.0  # Depth of the counterbore hole, if
        # Outer diameter of countersink.  Should roughly match the outer diameter of the screw head
        p_countersinkDiameter = 0.0
        # Countersink angle (complete angle between opposite sides, not from center to one side)
        p_countersinkAngle = 90.0
        # Whether to place the lid with the top facing down or not.
        p_flipLid = True
        # Height of lip on the underside of the lid.\nSits inside the box body for a snug fit.
        p_lipHeight = 1.0

        # outer shell
        oshell = (
            Workplane("XY")
            .rect(p_outerWidth, p_outerLength)
            .extrude(p_outerHeight + p_lipHeight)
        )

        # weird geometry happens if we make the fillets in the wrong order
        if p_sideRadius > p_topAndBottomRadius:
            oshell = (
                oshell.edges("|Z")
                .fillet(p_sideRadius)
                .edges("#Z")
                .fillet(p_topAndBottomRadius)
            )
        else:
            oshell = (
                oshell.edges("#Z")
                .fillet(p_topAndBottomRadius)
                .edges("|Z")
                .fillet(p_sideRadius)
            )

        # inner shell
        ishell = (
            oshell.faces("<Z")
            .workplane(p_thickness, True)
            .rect(
                (p_outerWidth - 2.0 * p_thickness), (p_outerLength - 2.0 * p_thickness)
            )
            .extrude((p_outerHeight - 2.0 * p_thickness), False)
        )  # set combine false to produce just the new boss
        ishell = ishell.edges("|Z").fillet(p_sideRadius - p_thickness)

        # make the box outer box
        box = oshell.cut(ishell)

        # make the screwposts
        POSTWIDTH = p_outerWidth - 2.0 * p_screwpostInset
        POSTLENGTH = p_outerLength - 2.0 * p_screwpostInset

        box = (
            box.faces(">Z")
            .workplane(-p_thickness)
            .rect(POSTWIDTH, POSTLENGTH, forConstruction=True)
            .vertices()
            .circle(p_screwpostOD / 2.0)
            .circle(p_screwpostID / 2.0)
            .extrude((-1.0) * (p_outerHeight + p_lipHeight - p_thickness), True)
        )

        # split lid into top and bottom parts
        (lid, bottom) = (
            box.faces(">Z")
            .workplane(-p_thickness - p_lipHeight)
            .split(keepTop=True, keepBottom=True)
            .all()
        )  # splits into two solids

        # translate the lid, and subtract the bottom from it to produce the lid inset
        lowerLid = lid.translate((0, 0, -p_lipHeight))
        cutlip = lowerLid.cut(bottom).translate(
            (p_outerWidth + p_thickness, 0, p_thickness - p_outerHeight + p_lipHeight)
        )

        # compute centers for counterbore/countersink or counterbore
        topOfLidCenters = (
            cutlip.faces(">Z")
            .workplane()
            .rect(POSTWIDTH, POSTLENGTH, forConstruction=True)
            .vertices()
        )

        # add holes of the desired type
        if p_boreDiameter > 0 and p_boreDepth > 0:
            topOfLid = topOfLidCenters.cboreHole(
                p_screwpostID, p_boreDiameter, p_boreDepth, (2.0) * p_thickness
            )
        elif p_countersinkDiameter > 0 and p_countersinkAngle > 0:
            topOfLid = topOfLidCenters.cskHole(
                p_screwpostID,
                p_countersinkDiameter,
                p_countersinkAngle,
                (2.0) * p_thickness,
            )
        else:
            topOfLid = topOfLidCenters.hole(p_screwpostID, (2.0) * p_thickness)

        # flip lid upside down if desired
        if p_flipLid:
            topOfLid.rotateAboutCenter((1, 0, 0), 180)

        # return the combined result
        result = topOfLid.union(bottom)

        self.saveModel(result)

    def testExtrude(self):
        """
        Test extrude
        """
        r = 1.0
        h = 1.0
        decimal_places = 9.0

        # extrude in one direction
        s = Workplane("XY").circle(r).extrude(h, both=False)

        top_face = s.faces(">Z")
        bottom_face = s.faces("<Z")

        # calculate the distance between the top and the bottom face
        delta = top_face.val().Center().sub(bottom_face.val().Center())

        self.assertTupleAlmostEquals(delta.toTuple(), (0.0, 0.0, h), decimal_places)

        # extrude symmetrically
        s = Workplane("XY").circle(r).extrude(h, both=True)

        self.assertTrue(len(s.val().Solids()) == 1)

        top_face = s.faces(">Z")
        bottom_face = s.faces("<Z")

        # calculate the distance between the top and the bottom face
        delta = top_face.val().Center().sub(bottom_face.val().Center())

        self.assertTupleAlmostEquals(
            delta.toTuple(), (0.0, 0.0, 2.0 * h), decimal_places
        )

    def testTaperedExtrudeCutBlind(self):

        h = 1.0
        r = 1.0
        t = 5

        # extrude with a positive taper
        s = Workplane("XY").circle(r).extrude(h, taper=t)

        top_face = s.faces(">Z")
        bottom_face = s.faces("<Z")

        # top and bottom face area
        delta = top_face.val().Area() - bottom_face.val().Area()

        self.assertTrue(delta < 0)

        # extrude with a negative taper
        s = Workplane("XY").circle(r).extrude(h, taper=-t)

        top_face = s.faces(">Z")
        bottom_face = s.faces("<Z")

        # top and bottom face area
        delta = top_face.val().Area() - bottom_face.val().Area()

        self.assertTrue(delta > 0)

        # cut a tapered hole
        s = (
            Workplane("XY")
            .rect(2 * r, 2 * r)
            .extrude(2 * h)
            .faces(">Z")
            .workplane()
            .rect(r, r)
            .cutBlind(-h, taper=t)
        )

        middle_face = s.faces(">Z[-2]")

        self.assertTrue(middle_face.val().Area() < 1)

    def testClose(self):
        # Close without endPoint and startPoint coincide.
        # Create a half-circle
        a = Workplane(Plane.XY()).sagittaArc((10, 0), 2).close().extrude(2)

        # Close when endPoint and startPoint coincide.
        # Create a double half-circle
        b = (
            Workplane(Plane.XY())
            .sagittaArc((10, 0), 2)
            .sagittaArc((0, 0), 2)
            .close()
            .extrude(2)
        )

        # The b shape shall have twice the volume of the a shape.
        self.assertAlmostEqual(a.val().Volume() * 2.0, b.val().Volume())

        # Testcase 3 from issue #238
        thickness = 3.0
        length = 10.0
        width = 5.0

        obj1 = (
            Workplane("XY", origin=(0, 0, -thickness / 2))
            .moveTo(length / 2, 0)
            .threePointArc((0, width / 2), (-length / 2, 0))
            .threePointArc((0, -width / 2), (length / 2, 0))
            .close()
            .extrude(thickness)
        )

        os_x = 8.0  # Offset in X
        os_y = -19.5  # Offset in Y

        obj2 = (
            Workplane("YZ", origin=(os_x, os_y, -thickness / 2))
            .moveTo(os_x + length / 2, os_y)
            .sagittaArc((os_x - length / 2, os_y), width / 2)
            .sagittaArc((os_x + length / 2, os_y), width / 2)
            .close()
            .extrude(thickness)
        )

        # The obj1 shape shall have the same volume as the obj2 shape.
        self.assertAlmostEqual(obj1.val().Volume(), obj2.val().Volume())

    def testText(self):

        box = Workplane("XY").box(4, 4, 0.5)

        obj1 = (
            box.faces(">Z")
            .workplane()
            .text(
                "CQ 2.0",
                0.5,
                -0.05,
                cut=True,
                halign="left",
                valign="bottom",
                font="Sans",
            )
        )

        # combined object should have smaller volume
        self.assertGreater(box.val().Volume(), obj1.val().Volume())

        obj2 = (
            box.faces(">Z")
            .workplane()
            .text("CQ 2.0", 0.5, 0.05, cut=False, combine=True, font="Sans")
        )

        # combined object should have bigger volume
        self.assertLess(box.val().Volume(), obj2.val().Volume())

        # verify that the number of top faces is correct (NB: this is font specific)
        self.assertEqual(len(obj2.faces(">Z").vals()), 5)

        obj3 = (
            box.faces(">Z")
            .workplane()
            .text(
                "CQ 2.0",
                0.5,
                0.05,
                cut=False,
                combine=False,
                halign="right",
                valign="top",
                font="Sans",
            )
        )

        # verify that the number of solids is correct
        self.assertEqual(len(obj3.solids().vals()), 5)

    def testParametricCurve(self):

        from math import sin, cos, pi

        k = 4
        r = 1

        func = lambda t: (
            r * (k + 1) * cos(t) - r * cos((k + 1) * t),
            r * (k + 1) * sin(t) - r * sin((k + 1) * t),
        )

        res_open = Workplane("XY").parametricCurve(func).extrude(3)

        # open profile generates an invalid solid
        self.assertFalse(res_open.solids().val().isValid())

        res_closed = (
            Workplane("XY").parametricCurve(func, start=0, stop=2 * pi).extrude(3)
        )

        # closed profile will generate a valid solid with 3 faces
        self.assertTrue(res_closed.solids().val().isValid())
        self.assertEqual(len(res_closed.faces().vals()), 3)

    def testMakeShellSolid(self):

        c0 = math.sqrt(2) / 4
        vertices = [[c0, -c0, c0], [c0, c0, -c0], [-c0, c0, c0], [-c0, -c0, -c0]]
        faces_ixs = [[0, 1, 2, 0], [1, 0, 3, 1], [2, 3, 0, 2], [3, 2, 1, 3]]

        faces = []
        for ixs in faces_ixs:
            lines = []
            for v1, v2 in zip(ixs, ixs[1:]):
                lines.append(
                    Edge.makeLine(Vector(*vertices[v1]), Vector(*vertices[v2]))
                )
            wire = Wire.combine(lines)[0]
            faces.append(Face.makeFromWires(wire))

        shell = Shell.makeShell(faces)
        solid = Solid.makeSolid(shell)

        self.assertTrue(shell.isValid())
        self.assertTrue(solid.isValid())

        self.assertEqual(len(solid.Vertices()), 4)
        self.assertEqual(len(solid.Faces()), 4)

    def testIsInsideSolid(self):
        # test solid
        model = Workplane("XY").box(10, 10, 10)
        solid = model.val()  # get first object on stack

        self.assertTrue(solid.isInside((0, 0, 0)))
        self.assertFalse(solid.isInside((10, 10, 10)))
        self.assertTrue(solid.isInside((Vector(3, 3, 3))))
        self.assertFalse(solid.isInside((Vector(30.0, 30.0, 30.0))))

        self.assertTrue(solid.isInside((0, 0, 4.99), tolerance=0.1))
        self.assertTrue(solid.isInside((0, 0, 5)))  # check point on surface
        self.assertTrue(solid.isInside((0, 0, 5.01), tolerance=0.1))
        self.assertFalse(solid.isInside((0, 0, 5.1), tolerance=0.1))

        # test compound solid
        model = Workplane("XY").box(10, 10, 10)
        model = model.moveTo(50, 50).box(10, 10, 10)
        solid = model.val()

        self.assertTrue(solid.isInside((0, 0, 0)))
        self.assertTrue(solid.isInside((50, 50, 0)))
        self.assertFalse(solid.isInside((50, 56, 0)))

        # make sure raises on non solid
        model = Workplane("XY").rect(10, 10)
        solid = model.val()
        with self.assertRaises(AttributeError):
            solid.isInside((0, 0, 0))

        # test solid with an internal void
        void = Workplane("XY").box(10, 10, 10)
        model = Workplane("XY").box(100, 100, 100).cut(void)
        solid = model.val()

        self.assertFalse(solid.isInside((0, 0, 0)))
        self.assertTrue(solid.isInside((40, 40, 40)))
        self.assertFalse(solid.isInside((55, 55, 55)))

    def testWorkplaneCenterOptions(self):
        """
        Test options for specifiying origin of workplane
        """
        decimal_places = 9

        pts = [(0, 0), (90, 0), (90, 30), (30, 30), (30, 60), (0.0, 60)]

        r = Workplane("XY").polyline(pts).close().extrude(10.0)

        origin = (
            r.faces(">Z")
            .workplane(centerOption="ProjectedOrigin")
            .plane.origin.toTuple()
        )
        self.assertTupleAlmostEquals(origin, (0.0, 0.0, 10.0), decimal_places)

        origin = (
            r.faces(">Z").workplane(centerOption="CenterOfMass").plane.origin.toTuple()
        )
        self.assertTupleAlmostEquals(origin, (37.5, 22.5, 10.0), decimal_places)

        origin = (
            r.faces(">Z")
            .workplane(centerOption="CenterOfBoundBox")
            .plane.origin.toTuple()
        )
        self.assertTupleAlmostEquals(origin, (45.0, 30.0, 10.0), decimal_places)

        origin = (
            r.faces(">Z")
            .workplane(centerOption="ProjectedOrigin", origin=(30, 10, 20))
            .plane.origin.toTuple()
        )
        self.assertTupleAlmostEquals(origin, (30.0, 10.0, 10.0), decimal_places)

        origin = (
            r.faces(">Z")
            .workplane(centerOption="ProjectedOrigin", origin=Vector(30, 10, 20))
            .plane.origin.toTuple()
        )
        self.assertTupleAlmostEquals(origin, (30.0, 10.0, 10.0), decimal_places)

        with self.assertRaises(ValueError):
            origin = r.faces(">Z").workplane(centerOption="undefined")

        # test case where plane origin is shifted with center call
        r = (
            r.faces(">Z")
            .workplane(centerOption="ProjectedOrigin")
            .center(30, 0)
            .hole(90)
        )

        origin = (
            r.faces(">Z")
            .workplane(centerOption="ProjectedOrigin")
            .plane.origin.toTuple()
        )
        self.assertTupleAlmostEquals(origin, (30.0, 0.0, 10.0), decimal_places)

        origin = (
            r.faces(">Z")
            .workplane(centerOption="ProjectedOrigin", origin=(0, 0, 0))
            .plane.origin.toTuple()
        )
        self.assertTupleAlmostEquals(origin, (0.0, 0.0, 10.0), decimal_places)

        # make sure projection works in all directions
        r = Workplane("YZ").polyline(pts).close().extrude(10.0)

        origin = (
            r.faces(">X")
            .workplane(centerOption="ProjectedOrigin")
            .plane.origin.toTuple()
        )
        self.assertTupleAlmostEquals(origin, (10.0, 0.0, 0.0), decimal_places)

        origin = (
            r.faces(">X").workplane(centerOption="CenterOfMass").plane.origin.toTuple()
        )
        self.assertTupleAlmostEquals(origin, (10.0, 37.5, 22.5), decimal_places)

        origin = (
            r.faces(">X")
            .workplane(centerOption="CenterOfBoundBox")
            .plane.origin.toTuple()
        )
        self.assertTupleAlmostEquals(origin, (10.0, 45.0, 30.0), decimal_places)

        r = Workplane("XZ").polyline(pts).close().extrude(10.0)

        origin = (
            r.faces("<Y")
            .workplane(centerOption="ProjectedOrigin")
            .plane.origin.toTuple()
        )
        self.assertTupleAlmostEquals(origin, (0.0, -10.0, 0.0), decimal_places)

        origin = (
            r.faces("<Y").workplane(centerOption="CenterOfMass").plane.origin.toTuple()
        )
        self.assertTupleAlmostEquals(origin, (37.5, -10.0, 22.5), decimal_places)

        origin = (
            r.faces("<Y")
            .workplane(centerOption="CenterOfBoundBox")
            .plane.origin.toTuple()
        )
        self.assertTupleAlmostEquals(origin, (45.0, -10.0, 30.0), decimal_places)

    def testFindSolid(self):

        r = Workplane("XY").pushPoints([(-2, 0), (2, 0)]).box(1, 1, 1, combine=False)

        # there should be two solids on the stack
        self.assertEqual(len(r.objects), 2)
        self.assertTrue(isinstance(r.val(), Solid))

        # find solid should return a compund of two solids
        s = r.findSolid()
        self.assertEqual(len(s.Solids()), 2)
        self.assertTrue(isinstance(s, Compound))

    def testSlot2D(self):

        decimal_places = 9

        # Ensure it produces a solid with the correct volume
        result = Workplane("XY").slot2D(4, 1, 0).extrude(1)
        self.assertAlmostEqual(result.val().Volume(), 3.785398163, decimal_places)

        # Test for proper expected behaviour when cutting
        box = Workplane("XY").box(5, 5, 1)
        result = box.faces(">Z").workplane().slot2D(4, 1, 0).cutThruAll()
        self.assertAlmostEqual(result.val().Volume(), 21.214601837, decimal_places)
        result = box.faces(">Z").workplane().slot2D(4, 1, 0).cutBlind(-0.5)
        self.assertAlmostEqual(result.val().Volume(), 23.107300918, decimal_places)

        # Test to see if slot is rotated correctly
        result = Workplane("XY").slot2D(4, 1, 45).extrude(1)
        point = result.faces(">Z").edges(">X").first().val().startPoint().toTuple()
        self.assertTupleAlmostEquals(
            point, (0.707106781, 1.414213562, 1.0), decimal_places
        )

    def test_assembleEdges(self):

        # Plate with 5 sides and 2 bumps, one side is not co-planar with the other sides
        # Passes an open wire to assembleEdges so that IsDone is true but Error returns 2 to test the warning functionality.
        edge_points = [
            [-7.0, -7.0, 0.0],
            [-3.0, -10.0, 3.0],
            [7.0, -7.0, 0.0],
            [7.0, 7.0, 0.0],
            [-7.0, 7.0, 0.0],
        ]
        edge_wire = Workplane("XY").polyline(
            [(-7.0, -7.0), (7.0, -7.0), (7.0, 7.0), (-7.0, 7.0)]
        )
        edge_wire = edge_wire.add(
            Workplane("YZ")
            .workplane()
            .transformed(offset=Vector(0, 0, -7), rotate=Vector(45, 0, 0))
            .spline([(-7.0, 0.0), (3, -3), (7.0, 0.0)])
        )
        edge_wire = [o.vals()[0] for o in edge_wire.all()]
        edge_wire = Wire.assembleEdges(edge_wire)

        # Embossed star, need to change optional parameters to obtain nice looking result.
        r1 = 3.0
        r2 = 10.0
        fn = 6
        edge_points = [
            [r1 * math.cos(i * math.pi / fn), r1 * math.sin(i * math.pi / fn)]
            if i % 2 == 0
            else [r2 * math.cos(i * math.pi / fn), r2 * math.sin(i * math.pi / fn)]
            for i in range(2 * fn + 1)
        ]
        edge_wire = Workplane("XY").polyline(edge_points)
        edge_wire = [o.vals()[0] for o in edge_wire.all()]
        edge_wire = Wire.assembleEdges(edge_wire)

        # Points on hexagonal pattern coordinates, use of pushpoints.
        r1 = 1.0
        fn = 6
        edge_points = [
            [r1 * math.cos(i * 2 * math.pi / fn), r1 * math.sin(i * 2 * math.pi / fn)]
            for i in range(fn + 1)
        ]
        surface_points = [
            [0.25, 0, 0.75],
            [-0.25, 0, 0.75],
            [0, 0.25, 0.75],
            [0, -0.25, 0.75],
            [0, 0, 2],
        ]
        edge_wire = Workplane("XY").polyline(edge_points)
        edge_wire = [o.vals()[0] for o in edge_wire.all()]
        edge_wire = Wire.assembleEdges(edge_wire)

        # Gyroïd, all edges are splines on different workplanes.
        edge_points = [
            [[3.54, 3.54], [1.77, 0.0], [3.54, -3.54]],
            [[-3.54, -3.54], [0.0, -1.77], [3.54, -3.54]],
            [[-3.54, -3.54], [0.0, -1.77], [3.54, -3.54]],
            [[-3.54, -3.54], [-1.77, 0.0], [-3.54, 3.54]],
            [[3.54, 3.54], [0.0, 1.77], [-3.54, 3.54]],
            [[3.54, 3.54], [0.0, 1.77], [-3.54, 3.54]],
        ]
        plane_list = ["XZ", "XY", "YZ", "XZ", "YZ", "XY"]
        offset_list = [-3.54, 3.54, 3.54, 3.54, -3.54, -3.54]
        edge_wire = (
            Workplane(plane_list[0])
            .workplane(offset=-offset_list[0])
            .spline(edge_points[0])
        )
        for i in range(len(edge_points) - 1):
            edge_wire = edge_wire.add(
                Workplane(plane_list[i + 1])
                .workplane(offset=-offset_list[i + 1])
                .spline(edge_points[i + 1])
            )
        edge_wire = [o.vals()[0] for o in edge_wire.all()]
        edge_wire = Wire.assembleEdges(edge_wire)

    def testTag(self):

        # test tagging
        result = (
            Workplane("XY")
            .pushPoints([(-2, 0), (2, 0)])
            .box(1, 1, 1, combine=False)
            .tag("2 solids")
            .union(Workplane("XY").box(6, 1, 1))
        )
        self.assertEqual(len(result.objects), 1)
        result = result._getTagged("2 solids")
        self.assertEqual(len(result.objects), 2)

    def testCopyWorkplane(self):

        obj0 = Workplane("XY").box(1, 1, 10).faces(">Z").workplane()
        obj1 = Workplane("XY").copyWorkplane(obj0).box(1, 1, 1)
        self.assertTupleAlmostEquals((0, 0, 5), obj1.val().Center().toTuple(), 9)

    def testWorkplaneFromTagged(self):

        # create a flat, wide base. Extrude one object 4 units high, another
        # object ontop of it 6 units high. Go back to base plane. Extrude an
        # object 11 units high. Assert that top face is 11 units high.
        result = (
            Workplane("XY")
            .box(10, 10, 1, centered=(True, True, False))
            .faces(">Z")
            .workplane()
            .tag("base")
            .center(3, 0)
            .rect(2, 2)
            .extrude(4)
            .faces(">Z")
            .workplane()
            .circle(1)
            .extrude(6)
            .workplaneFromTagged("base")
            .center(-3, 0)
            .circle(1)
            .extrude(11)
        )
        self.assertTupleAlmostEquals(
            result.faces(">Z").val().Center().toTuple(), (-3, 0, 12), 9
        )

    def testTagSelectors(self):

        result0 = Workplane("XY").box(1, 1, 1).tag("box").sphere(1)
        # result is currently a sphere
        self.assertEqual(1, result0.faces().size())
        # a box has 8 vertices
        self.assertEqual(8, result0.vertices(tag="box").size())
        # 6 faces
        self.assertEqual(6, result0.faces(tag="box").size())
        # 12 edges
        self.assertEqual(12, result0.edges(tag="box").size())
        # 6 wires
        self.assertEqual(6, result0.wires(tag="box").size())

        # create two solids, tag them, join to one solid
        result1 = (
            Workplane("XY")
            .pushPoints([(1, 0), (-1, 0)])
            .box(1, 1, 1)
            .tag("boxes")
            .sphere(1)
        )
        self.assertEqual(1, result1.solids().size())
        self.assertEqual(2, result1.solids(tag="boxes").size())
        self.assertEqual(1, result1.shells().size())
        self.assertEqual(2, result1.shells(tag="boxes").size())

        # create 4 individual objects, tag it, then combine to one compound
        result2 = (
            Workplane("XY")
            .rect(4, 4)
            .vertices()
            .box(1, 1, 1, combine=False)
            .tag("4 objs")
        )
        result2 = result2.newObject([Compound.makeCompound(result2.objects)])
        self.assertEqual(1, result2.compounds().size())
        self.assertEqual(0, result2.compounds(tag="4 objs").size())

    def test_interpPlate(self):
        """
        Tests the interpPlate() functionnalites
        Numerical values of Areas and Volumes were obtained with the Area() and Volume() functions on a Linux machine under Debian 10 with python 3.7.
        """

        # example from PythonOCC core_geometry_geomplate.py, use of thickness = 0 returns 2D surface.
        thickness = 0
        edge_points = [
            [0.0, 0.0, 0.0],
            [0.0, 10.0, 0.0],
            [0.0, 10.0, 10.0],
            [0.0, 0.0, 10.0],
        ]
        surface_points = [[5.0, 5.0, 5.0]]
        plate_0 = Workplane("XY").interpPlate(edge_points, surface_points, thickness)
        self.assertTrue(plate_0.val().isValid())
        self.assertAlmostEqual(plate_0.val().Area(), 141.218823892, 1)

        # Plate with 5 sides and 2 bumps, one side is not co-planar with the other sides
        thickness = 0.1
        edge_points = [
            [-7.0, -7.0, 0.0],
            [-3.0, -10.0, 3.0],
            [7.0, -7.0, 0.0],
            [7.0, 7.0, 0.0],
            [-7.0, 7.0, 0.0],
        ]
        edge_wire = Workplane("XY").polyline(
            [(-7.0, -7.0), (7.0, -7.0), (7.0, 7.0), (-7.0, 7.0)]
        )
        # edge_wire = edge_wire.add(Workplane('YZ').workplane().transformed(offset=Vector(0, 0, -7), rotate=Vector(45, 0, 0)).polyline([(-7.,0.), (3,-3), (7.,0.)]))
        # In CadQuery Sept-2019 it worked with rotate=Vector(0, 45, 0). In CadQuery Dec-2019 rotate=Vector(45, 0, 0) only closes the wire.
        edge_wire = edge_wire.add(
            Workplane("YZ")
            .workplane()
            .transformed(offset=Vector(0, 0, -7), rotate=Vector(45, 0, 0))
            .spline([(-7.0, 0.0), (3, -3), (7.0, 0.0)])
        )
        surface_points = [[-3.0, -3.0, -3.0], [3.0, 3.0, 3.0]]
        plate_1 = Workplane("XY").interpPlate(edge_wire, surface_points, thickness)
        self.assertTrue(plate_1.val().isValid())
        self.assertAlmostEqual(plate_1.val().Volume(), 26.124970206, 3)

        # Embossed star, need to change optional parameters to obtain nice looking result.
        r1 = 3.0
        r2 = 10.0
        fn = 6
        thickness = 0.1
        edge_points = [
            [r1 * math.cos(i * math.pi / fn), r1 * math.sin(i * math.pi / fn)]
            if i % 2 == 0
            else [r2 * math.cos(i * math.pi / fn), r2 * math.sin(i * math.pi / fn)]
            for i in range(2 * fn + 1)
        ]
        edge_wire = Workplane("XY").polyline(edge_points)
        r2 = 4.5
        surface_points = [
            [r2 * math.cos(i * math.pi / fn), r2 * math.sin(i * math.pi / fn), 1.0]
            for i in range(2 * fn)
        ] + [[0.0, 0.0, -2.0]]
        plate_2 = Workplane("XY").interpPlate(
            edge_wire,
            surface_points,
            thickness,
            combine=True,
            clean=True,
            degree=3,
            nbPtsOnCur=15,
            nbIter=2,
            anisotropy=False,
            tol2d=0.00001,
            tol3d=0.0001,
            tolAng=0.01,
            tolCurv=0.1,
            maxDeg=8,
            maxSegments=49,
        )
        self.assertTrue(plate_2.val().isValid())
        self.assertAlmostEqual(plate_2.val().Volume(), 10.956054314, 0)

        # Points on hexagonal pattern coordinates, use of pushpoints.
        r1 = 1.0
        N = 3
        ca = math.cos(30.0 * math.pi / 180.0)
        sa = math.sin(30.0 * math.pi / 180.0)
        # EVEN ROWS
        pts = [
            (-3.0, -3.0),
            (-1.267949, -3.0),
            (0.464102, -3.0),
            (2.196152, -3.0),
            (-3.0, 0.0),
            (-1.267949, 0.0),
            (0.464102, 0.0),
            (2.196152, 0.0),
            (-2.133974, -1.5),
            (-0.401923, -1.5),
            (1.330127, -1.5),
            (3.062178, -1.5),
            (-2.133975, 1.5),
            (-0.401924, 1.5),
            (1.330127, 1.5),
            (3.062178, 1.5),
        ]
        # Spike surface
        thickness = 0.1
        fn = 6
        edge_points = [
            [
                r1 * math.cos(i * 2 * math.pi / fn + 30 * math.pi / 180),
                r1 * math.sin(i * 2 * math.pi / fn + 30 * math.pi / 180),
            ]
            for i in range(fn + 1)
        ]
        surface_points = [
            [
                r1 / 4 * math.cos(i * 2 * math.pi / fn + 30 * math.pi / 180),
                r1 / 4 * math.sin(i * 2 * math.pi / fn + 30 * math.pi / 180),
                0.75,
            ]
            for i in range(fn + 1)
        ] + [[0, 0, 2]]
        edge_wire = Workplane("XY").polyline(edge_points)
        plate_3 = (
            Workplane("XY")
            .pushPoints(pts)
            .interpPlate(
                edge_wire,
                surface_points,
                thickness,
                combine=False,
                clean=False,
                degree=2,
                nbPtsOnCur=20,
                nbIter=2,
                anisotropy=False,
                tol2d=0.00001,
                tol3d=0.0001,
                tolAng=0.01,
                tolCurv=0.1,
                maxDeg=8,
                maxSegments=9,
            )
        )
        self.assertTrue(plate_3.val().isValid())
        self.assertAlmostEqual(plate_3.val().Volume(), 0.45893954685189414, 1)

        # Gyroïd, all edges are splines on different workplanes.
        thickness = 0.1
        edge_points = [
            [[3.54, 3.54], [1.77, 0.0], [3.54, -3.54]],
            [[-3.54, -3.54], [0.0, -1.77], [3.54, -3.54]],
            [[-3.54, -3.54], [0.0, -1.77], [3.54, -3.54]],
            [[-3.54, -3.54], [-1.77, 0.0], [-3.54, 3.54]],
            [[3.54, 3.54], [0.0, 1.77], [-3.54, 3.54]],
            [[3.54, 3.54], [0.0, 1.77], [-3.54, 3.54]],
        ]
        plane_list = ["XZ", "XY", "YZ", "XZ", "YZ", "XY"]
        offset_list = [-3.54, 3.54, 3.54, 3.54, -3.54, -3.54]
        edge_wire = (
            Workplane(plane_list[0])
            .workplane(offset=-offset_list[0])
            .spline(edge_points[0])
        )
        for i in range(len(edge_points) - 1):
            edge_wire = edge_wire.add(
                Workplane(plane_list[i + 1])
                .workplane(offset=-offset_list[i + 1])
                .spline(edge_points[i + 1])
            )
        surface_points = [[0, 0, 0]]
        plate_4 = Workplane("XY").interpPlate(edge_wire, surface_points, thickness)
        self.assertTrue(plate_4.val().isValid())
        self.assertAlmostEqual(plate_4.val().Volume(), 7.760559490, 3)

    def testTangentArcToPoint(self):

        # create a simple shape with tangents of straight edges and see if it has the correct area
        s0 = (
            Workplane("XY")
            .hLine(1)
            .tangentArcPoint((1, 1), relative=False)
            .hLineTo(0)
            .tangentArcPoint((0, 0), relative=False)
            .close()
            .extrude(1)
        )
        area0 = s0.faces(">Z").val().Area()
        self.assertAlmostEqual(area0, (1 + math.pi * 0.5 ** 2), 4)

        # test relative coords
        s1 = (
            Workplane("XY")
            .hLine(1)
            .tangentArcPoint((0, 1), relative=True)
            .hLineTo(0)
            .tangentArcPoint((0, -1), relative=True)
            .close()
            .extrude(1)
        )
        self.assertTupleAlmostEquals(
            s1.val().Center().toTuple(), s0.val().Center().toTuple(), 4
        )
        self.assertAlmostEqual(s1.val().Volume(), s0.val().Volume(), 4)

        # consecutive tangent arcs
        s1 = (
            Workplane("XY")
            .vLine(2)
            .tangentArcPoint((1, 0))
            .tangentArcPoint((1, 0))
            .tangentArcPoint((1, 0))
            .vLine(-2)
            .close()
            .extrude(1)
        )
        self.assertAlmostEqual(
            s1.faces(">Z").val().Area(), 2 * 3 + 0.5 * math.pi * 0.5 ** 2, 4
        )

        # tangentArc on the end of a spline
        # spline will be a simple arc of a circle, then finished off with a
        # tangentArcPoint
        angles = [idx * 1.5 * math.pi / 10 for idx in range(10)]
        pts = [(math.sin(a), math.cos(a)) for a in angles]
        s2 = (
            Workplane("XY")
            .spline(pts)
            .tangentArcPoint((0, 1), relative=False)
            .close()
            .extrude(1)
        )
        # volume should almost be pi, but not accurately because we need to
        # start with a spline
        self.assertAlmostEqual(s2.val().Volume(), math.pi, 1)
        # assert local coords are mapped to global correctly
        arc0 = Workplane("XZ", origin=(1, 1, 1)).hLine(1).tangentArcPoint((1, 1)).val()
        self.assertTupleAlmostEquals(arc0.endPoint().toTuple(), (3, 1, 2), 4)

        # tangentArcPoint with 3-tuple argument
        w0 = Workplane("XY").lineTo(1, 1).tangentArcPoint((1, 1, 1)).wire()
        zmax = w0.val().BoundingBox().zmax
        self.assertAlmostEqual(zmax, 1, 1)

    def test_findFromEdge(self):
        part = Workplane("XY", origin=(1, 1, 1)).hLine(1)
        found_edge = part._findFromEdge(useLocalCoords=False)
        self.assertTupleAlmostEquals(found_edge.startPoint().toTuple(), (1, 1, 1), 3)
        self.assertTupleAlmostEquals(found_edge.Center().toTuple(), (1.5, 1, 1), 3)
        self.assertTupleAlmostEquals(found_edge.endPoint().toTuple(), (2, 1, 1), 3)
        found_edge = part._findFromEdge(useLocalCoords=True)
        self.assertTupleAlmostEquals(found_edge.endPoint().toTuple(), (1, 0, 0), 3)
        # check _findFromEdge can find a spline
        pts = [(0, 0), (0, 1), (1, 2), (2, 4)]
        spline0 = Workplane("XZ").spline(pts)._findFromEdge()
        self.assertTupleAlmostEquals((2, 0, 4), spline0.endPoint().toTuple(), 3)
        # check method fails if no edge is present
        part2 = Workplane("XY").box(1, 1, 1)
        with self.assertRaises(RuntimeError):
            part2._findFromEdge()
        with self.assertRaises(RuntimeError):
            part2._findFromEdge(useLocalCoords=True)

    def testMakeHelix(self):

        h = 10
        pitch = 1.5
        r = 1.2
        obj = Wire.makeHelix(pitch, h, r)

        bb = obj.BoundingBox()
        self.assertAlmostEqual(bb.zlen, h, 1)

    def testUnionCompound(self):

        box1 = Workplane("XY").box(10, 20, 30)
        box2 = Workplane("YZ").box(10, 20, 30)
        shape_to_cut = Workplane("XY").box(15, 15, 15).translate((8, 8, 8))

        list_of_shapes = []
        for o in box1.all():
            list_of_shapes.extend(o.vals())
        for o in box2.all():
            list_of_shapes.extend(o.vals())

        obj = Workplane("XY").newObject(list_of_shapes).cut(shape_to_cut)

        assert obj.val().isValid()

    def testSection(self):

        box = Workplane("XY", origin=(1, 2, 3)).box(1, 1, 1)

        s1 = box.section()
        s2 = box.section(0.5)

        self.assertAlmostEqual(s1.faces().val().Area(), 1)
        self.assertAlmostEqual(s2.faces().val().Area(), 1)

        line = Workplane("XY").hLine(1)

        with self.assertRaises(ValueError):
            line.section()

    def testGlue(self):

        box1 = Workplane("XY").rect(1, 1).extrude(2)
        box2 = Workplane("XY", origin=(0, 1, 0)).rect(1, 1).extrude(1)
        res = box1.union(box2, glue=True)

        self.assertEqual(res.faces().size(), 8)

        obj = obj = (
            Workplane("XY").rect(1, 1).extrude(2).moveTo(0, 2).rect(1, 1).extrude(2)
        )
        res = obj.union(box2, glue=True)

        self.assertEqual(res.faces().size(), 10)

    def testFuzzyBoolOp(self):

        eps = 1e-3

        box1 = Workplane("XY").box(1, 1, 1)
        box2 = Workplane("XY", origin=(1 + eps, 0.0)).box(1, 1, 1)
        box3 = Workplane("XY", origin=(2, 0, 0)).box(1, 1, 1)

        res = box1.union(box2)
        res_fuzzy = box1.union(box2, tol=eps)
        res_fuzzy2 = box1.union(box3).union(box2, tol=eps)

        self.assertEqual(res.solids().size(), 2)
        self.assertEqual(res_fuzzy.solids().size(), 1)
        self.assertEqual(res_fuzzy2.solids().size(), 1)

    def testLocatedMoved(self):

        box = Solid.makeBox(1, 1, 1, Vector(-0.5, -0.5, -0.5))
        loc = Location(Vector(1, 1, 1))

        box1 = box.located(loc)

        self.assertTupleAlmostEquals(box1.Center().toTuple(), (1, 1, 1), 6)
        self.assertTupleAlmostEquals(box.Center().toTuple(), (0, 0, 0), 6)

        box.locate(loc)

        self.assertTupleAlmostEquals(box.Center().toTuple(), (1, 1, 1), 6)

        box2 = box.moved(loc)

        self.assertTupleAlmostEquals(box.Center().toTuple(), (1, 1, 1), 6)
        self.assertTupleAlmostEquals(box2.Center().toTuple(), (2, 2, 2), 6)

        box.move(loc)

        self.assertTupleAlmostEquals(box.Center().toTuple(), (2, 2, 2), 6)

    def testNullShape(self):

        from OCP.TopoDS import TopoDS_Shape

        s = TopoDS_Shape()

        # make sure raises on non solid
        with self.assertRaises(ValueError):
            r = occ_impl.shapes.downcast(s)

    def testCenterOfBoundBox(self):

        obj = Workplane().pushPoints([(0, 0), (2, 2)]).box(1, 1, 1)
        c = obj.workplane(centerOption="CenterOfBoundBox").plane.origin

        self.assertTupleAlmostEquals(c.toTuple(), (1, 1, 0), 6)

    def testOffset2D(self):

        w1 = Workplane().rect(1, 1).offset2D(0.5, "arc")
        self.assertEqual(w1.edges().size(), 8)

        w2 = Workplane().rect(1, 1).offset2D(0.5, "tangent")
        self.assertEqual(w2.edges().size(), 4)

        w3 = Workplane().rect(1, 1).offset2D(0.5, "intersection")
        self.assertEqual(w3.edges().size(), 4)

        w4 = Workplane().pushPoints([(0, 0), (0, 5)]).rect(1, 1).offset2D(-0.5)
        self.assertEqual(w4.wires().size(), 0)

        w5 = Workplane().pushPoints([(0, 0), (0, 5)]).rect(1, 1).offset2D(-0.25)
        self.assertEqual(w5.wires().size(), 2)

        r = 20
        s = 7
        t = 1.5

        points = [
            (0, t / 2),
            (r / 2 - 1.5 * t, r / 2 - t),
            (s / 2, r / 2 - t),
            (s / 2, r / 2),
            (r / 2, r / 2),
            (r / 2, s / 2),
            (r / 2 - t, s / 2),
            (r / 2 - t, r / 2 - 1.5 * t),
            (t / 2, 0),
        ]

        s = (
            Workplane("XY")
            .polyline(points)
            .mirrorX()
            .mirrorY()
            .offset2D(-0.9)
            .extrude(1)
        )
        self.assertEqual(s.solids().size(), 4)

    def testConsolidateWires(self):

        w1 = Workplane().lineTo(0, 1).lineTo(1, 1).consolidateWires()
        self.assertEqual(w1.size(), 1)

        w1 = Workplane().consolidateWires()
        self.assertEqual(w1.size(), 0)

    def testLocationAt(self):

        r = 1
        e = Wire.makeHelix(r, r, r).Edges()[0]

        locs_frenet = e.locations([0, 1], frame="frenet")

        T1 = locs_frenet[0].wrapped.Transformation()
        T2 = locs_frenet[1].wrapped.Transformation()

        self.assertAlmostEqual(T1.TranslationPart().X(), r, 6)
        self.assertAlmostEqual(T2.TranslationPart().X(), r, 6)
        self.assertAlmostEqual(
            T1.GetRotation().GetRotationAngle(), -T2.GetRotation().GetRotationAngle(), 6
        )

        ga = e._geomAdaptor()

        locs_corrected = e.locations(
            [ga.FirstParameter(), ga.LastParameter()],
            mode="parameter",
            frame="corrected",
        )

        T3 = locs_corrected[0].wrapped.Transformation()
        T4 = locs_corrected[1].wrapped.Transformation()

        self.assertAlmostEqual(T3.TranslationPart().X(), r, 6)
        self.assertAlmostEqual(T4.TranslationPart().X(), r, 6)

    def testNormal(self):

        circ = Workplane().circle(1).edges().val()
        n = circ.normal()

        self.assertTupleAlmostEquals(n.toTuple(), (0, 0, 1), 6)

        ell = Workplane().ellipse(1, 2).edges().val()
        n = ell.normal()

        self.assertTupleAlmostEquals(n.toTuple(), (0, 0, 1), 6)

        with self.assertRaises(ValueError):
            edge = Workplane().rect(1, 2).edges().val()
            n = edge.normal()
