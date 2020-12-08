"""
    Tests basic workplane functionality
"""
# core modules

# my modules
from cadquery import *
from tests import BaseTest, toTuple

xAxis_ = Vector(1, 0, 0)
yAxis_ = Vector(0, 1, 0)
zAxis_ = Vector(0, 0, 1)
xInvAxis_ = Vector(-1, 0, 0)
yInvAxis_ = Vector(0, -1, 0)
zInvAxis_ = Vector(0, 0, -1)


class TestWorkplanes(BaseTest):
    def testYZPlaneOrigins(self):
        # xy plane-- with origin at x=0.25
        base = Vector(0.25, 0, 0)
        p = Plane(base, Vector(0, 1, 0), Vector(1, 0, 0))

        # origin is always (0,0,0) in local coordinates
        self.assertTupleAlmostEquals((0, 0, 0), p.toLocalCoords(p.origin).toTuple(), 2)

        # (0,0,0) is always the original base in global coordinates
        self.assertTupleAlmostEquals(
            base.toTuple(), p.toWorldCoords((0, 0)).toTuple(), 2
        )

    def testXYPlaneOrigins(self):
        base = Vector(0, 0, 0.25)
        p = Plane(base, Vector(1, 0, 0), Vector(0, 0, 1))

        # origin is always (0,0,0) in local coordinates
        self.assertTupleAlmostEquals((0, 0, 0), p.toLocalCoords(p.origin).toTuple(), 2)

        # (0,0,0) is always the original base in global coordinates
        self.assertTupleAlmostEquals(
            toTuple(base), p.toWorldCoords((0, 0)).toTuple(), 2
        )

    def testXZPlaneOrigins(self):
        base = Vector(0, 0.25, 0)
        p = Plane(base, Vector(0, 0, 1), Vector(0, 1, 0))

        # (0,0,0) is always the original base in global coordinates
        self.assertTupleAlmostEquals(
            toTuple(base), p.toWorldCoords((0, 0)).toTuple(), 2
        )

        # origin is always (0,0,0) in local coordinates
        self.assertTupleAlmostEquals((0, 0, 0), p.toLocalCoords(p.origin).toTuple(), 2)

    def testPlaneBasics(self):
        p = Plane.XY()
        # local to world
        self.assertTupleAlmostEquals(
            (1.0, 1.0, 0), p.toWorldCoords((1, 1)).toTuple(), 2
        )
        self.assertTupleAlmostEquals(
            (-1.0, -1.0, 0), p.toWorldCoords((-1, -1)).toTuple(), 2
        )

        # world to local
        self.assertTupleAlmostEquals(
            (-1.0, -1.0), p.toLocalCoords(Vector(-1, -1, 0)).toTuple(), 2
        )
        self.assertTupleAlmostEquals(
            (1.0, 1.0), p.toLocalCoords(Vector(1, 1, 0)).toTuple(), 2
        )

        p = Plane.YZ()
        self.assertTupleAlmostEquals(
            (0, 1.0, 1.0), p.toWorldCoords((1, 1)).toTuple(), 2
        )

        # world to local
        self.assertTupleAlmostEquals(
            (1.0, 1.0), p.toLocalCoords(Vector(0, 1, 1)).toTuple(), 2
        )

        p = Plane.XZ()
        r = p.toWorldCoords((1, 1)).toTuple()
        self.assertTupleAlmostEquals((1.0, 0.0, 1.0), r, 2)

        # world to local
        self.assertTupleAlmostEquals(
            (1.0, 1.0), p.toLocalCoords(Vector(1, 0, 1)).toTuple(), 2
        )

    def testOffsetPlanes(self):
        "Tests that a plane offset from the origin works ok too"
        p = Plane.XY(origin=(10.0, 10.0, 0))

        self.assertTupleAlmostEquals(
            (11.0, 11.0, 0.0), p.toWorldCoords((1.0, 1.0)).toTuple(), 2
        )
        self.assertTupleAlmostEquals(
            (2.0, 2.0), p.toLocalCoords(Vector(12.0, 12.0, 0)).toTuple(), 2
        )

        # TODO test these offsets in the other dimensions too
        p = Plane.YZ(origin=(0, 2, 2))
        self.assertTupleAlmostEquals(
            (0.0, 5.0, 5.0), p.toWorldCoords((3.0, 3.0)).toTuple(), 2
        )
        self.assertTupleAlmostEquals(
            (10, 10.0, 0.0), p.toLocalCoords(Vector(0.0, 12.0, 12.0)).toTuple(), 2
        )

        p = Plane.XZ(origin=(2, 0, 2))
        r = p.toWorldCoords((1.0, 1.0)).toTuple()
        self.assertTupleAlmostEquals((3.0, 0.0, 3.0), r, 2)
        self.assertTupleAlmostEquals(
            (10.0, 10.0), p.toLocalCoords(Vector(12.0, 0.0, 12.0)).toTuple(), 2
        )

    def testXYPlaneBasics(self):
        p = Plane.named("XY")
        self.assertTupleAlmostEquals(p.zDir.toTuple(), zAxis_.toTuple(), 4)
        self.assertTupleAlmostEquals(p.xDir.toTuple(), xAxis_.toTuple(), 4)
        self.assertTupleAlmostEquals(p.yDir.toTuple(), yAxis_.toTuple(), 4)

    def testYZPlaneBasics(self):
        p = Plane.named("YZ")
        self.assertTupleAlmostEquals(p.zDir.toTuple(), xAxis_.toTuple(), 4)
        self.assertTupleAlmostEquals(p.xDir.toTuple(), yAxis_.toTuple(), 4)
        self.assertTupleAlmostEquals(p.yDir.toTuple(), zAxis_.toTuple(), 4)

    def testZXPlaneBasics(self):
        p = Plane.named("ZX")
        self.assertTupleAlmostEquals(p.zDir.toTuple(), yAxis_.toTuple(), 4)
        self.assertTupleAlmostEquals(p.xDir.toTuple(), zAxis_.toTuple(), 4)
        self.assertTupleAlmostEquals(p.yDir.toTuple(), xAxis_.toTuple(), 4)

    def testXZPlaneBasics(self):
        p = Plane.named("XZ")
        self.assertTupleAlmostEquals(p.zDir.toTuple(), yInvAxis_.toTuple(), 4)
        self.assertTupleAlmostEquals(p.xDir.toTuple(), xAxis_.toTuple(), 4)
        self.assertTupleAlmostEquals(p.yDir.toTuple(), zAxis_.toTuple(), 4)

    def testYXPlaneBasics(self):
        p = Plane.named("YX")
        self.assertTupleAlmostEquals(p.zDir.toTuple(), zInvAxis_.toTuple(), 4)
        self.assertTupleAlmostEquals(p.xDir.toTuple(), yAxis_.toTuple(), 4)
        self.assertTupleAlmostEquals(p.yDir.toTuple(), xAxis_.toTuple(), 4)

    def testZYPlaneBasics(self):
        p = Plane.named("ZY")
        self.assertTupleAlmostEquals(p.zDir.toTuple(), xInvAxis_.toTuple(), 4)
        self.assertTupleAlmostEquals(p.xDir.toTuple(), zAxis_.toTuple(), 4)
        self.assertTupleAlmostEquals(p.yDir.toTuple(), yAxis_.toTuple(), 4)

    def test_mirror(self):
        """Create a unit box and mirror it so that it doubles in size"""
        b2 = Workplane().box(1, 1, 1)
        b2 = b2.mirror("XY", (0, 0, 0.5), union=True)
        bbBox = b2.findSolid().BoundingBox()
        assert [bbBox.xlen, bbBox.ylen, bbBox.zlen] == [1.0, 1.0, 2]
        self.assertAlmostEqual(b2.findSolid().Volume(), 2, 5)

    def test_all_planes(self):
        b2 = Workplane().box(1, 1, 1)
        for p in ["XY", "YX", "XZ", "ZX", "YZ", "ZY"]:
            b2 = b2.mirror(p)
            bbBox = b2.findSolid().BoundingBox()
            assert [bbBox.xlen, bbBox.ylen, bbBox.zlen] == [1.0, 1.0, 1.0]
            self.assertAlmostEqual(b2.findSolid().Volume(), 1, 5)

    def test_bad_plane_input(self):
        b2 = Workplane().box(1, 1, 1)
        with self.assertRaises(ValueError) as context:
            b2.mirror(b2.edges())
            self.assertTrue("Face required, got" in str(context.exception))

    def test_mirror_axis(self):
        """Create a unit box and mirror it so that it doubles in size"""
        b2 = Workplane().box(1, 1, 1)
        b2 = b2.mirror((0, 0, 1), (0, 0, 0.5), union=True)
        bbBox = b2.findSolid().BoundingBox()
        assert [bbBox.xlen, bbBox.ylen, bbBox.zlen] == [1.0, 1.0, 2]
        self.assertAlmostEqual(b2.findSolid().Volume(), 2, 5)

    def test_mirror_workplane(self):
        """Create a unit box and mirror it so that it doubles in size"""
        b2 = Workplane().box(1, 1, 1)

        # double in Z plane
        b2 = b2.mirror(b2.faces(">Z"), union=True)
        bbBox = b2.findSolid().BoundingBox()
        assert [bbBox.xlen, bbBox.ylen, bbBox.zlen] == [1.0, 1.0, 2]
        self.assertAlmostEqual(b2.findSolid().Volume(), 2, 5)

        # double in Y plane
        b2 = b2.mirror(b2.faces(">Y"), union=True)
        bbBox = b2.findSolid().BoundingBox()
        assert [bbBox.xlen, bbBox.ylen, bbBox.zlen] == [1.0, 2.0, 2]
        self.assertAlmostEqual(b2.findSolid().Volume(), 4, 5)

        # double in X plane
        b2 = b2.mirror(b2.faces(">X"), union=True)
        bbBox = b2.findSolid().BoundingBox()
        assert [bbBox.xlen, bbBox.ylen, bbBox.zlen] == [2.0, 2.0, 2]
        self.assertAlmostEqual(b2.findSolid().Volume(), 8, 5)

    def test_mirror_equivalence(self):
        """test that the plane string, plane normal and face object perform a mirror operation in the same way"""
        boxes = []
        boxDims = 1
        for i in range(3):  # create 3 sets of identical boxes
            boxTmp = Workplane("XY").box(boxDims, boxDims, boxDims)
            boxTmp = boxTmp.translate([i * 2, 0, boxDims / 2])
            boxes.append(boxTmp)

        # 3 different types of plane definition
        planeArg = ["XY", (0, 0, 1), boxes[0].faces("<Z")]
        planeOffset = (0, 0, 0.5)  # use the safe offset for each
        boxResults = []  # store the resulting mirrored objects
        for b, p in zip(boxes, planeArg):
            boxResults.append(b.mirror(p, planeOffset, union=True))

        # all resulting boxes should be equal to each other
        for i in range(len(boxResults) - 1):
            curBoxDims = boxResults[i].findSolid().BoundingBox()  # get bbox dims
            nextBoxDims = boxResults[i + 1].findSolid().BoundingBox()  # get bbox dims
            cbd = (curBoxDims.xlen, curBoxDims.ylen, curBoxDims.zlen)
            nbd = (nextBoxDims.xlen, nextBoxDims.ylen, nextBoxDims.zlen)
            self.assertTupleAlmostEquals(cbd, nbd, 4)
            self.assertAlmostEqual(
                boxResults[i].findSolid().Volume(),
                boxResults[i + 1].findSolid().Volume(),
                5,
            )

    def test_mirror_face(self):
        """Create a triangle and mirror into a unit box"""
        r = Workplane("XY").line(0, 1).line(1, -1).close().extrude(1)

        bbBox = r.findSolid().BoundingBox()
        self.assertTupleAlmostEquals(
            (bbBox.xlen, bbBox.ylen, bbBox.zlen), (1.0, 1.0, 1.0), 4
        )
        self.assertAlmostEqual(r.findSolid().Volume(), 0.5, 5)

        r = r.mirror(r.faces().objects[1], union=True)
        bbBox = r.findSolid().BoundingBox()
        self.assertTupleAlmostEquals(
            (bbBox.xlen, bbBox.ylen, bbBox.zlen), (1.0, 1.0, 1.0), 4
        )
        self.assertAlmostEqual(r.findSolid().Volume(), 1.0, 5)
