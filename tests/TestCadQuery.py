"""
    This module tests cadquery creation and manipulation functions

"""
#system modules
import math,sys,os.path,time

#my modules
from cadquery import *
from cadquery import exporters
from tests import (
    BaseTest,
    writeStringToFile,
    makeUnitCube,
    readFileAsString,
    makeUnitSquareWire,
    makeCube,
)
from cadquery.freecad_impl import suppress_stdout_stderr

#where unit test output will be saved
import sys
if sys.platform.startswith("win"):
    OUTDIR = "c:/temp"
else:
    OUTDIR = "/tmp"
SUMMARY_FILE = os.path.join(OUTDIR,"testSummary.html")

SUMMARY_TEMPLATE="""<html>
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

TEST_RESULT_TEMPLATE="""
    <div class="testResult"><h3>%(name)s</h3>
    %(svg)s
    </div>
    <!--TEST_CONTENT-->
"""

#clean up any summary file that is in the output directory.
#i know, this sux, but there is no other way to do this in 2.6, as we cannot do class fixutres till 2.7
writeStringToFile(SUMMARY_TEMPLATE,SUMMARY_FILE)


class TestCadQuery(BaseTest):

    def tearDown(self):
        """
            Update summary with data from this test.
            This is a really hackey way of doing it-- we get a startup event from module load,
            but there is no way in unittest to get a single shutdown event-- except for stuff in 2.7 and above

            So what we do here is to read the existing file, stick in more content, and leave it
        """
        svgFile = os.path.join(OUTDIR,self._testMethodName + ".svg")

        #all tests do not produce output
        if os.path.exists(svgFile):
            existingSummary = readFileAsString(SUMMARY_FILE)
            svgText = readFileAsString(svgFile)
            svgText = svgText.replace('<?xml version="1.0" encoding="UTF-8" standalone="no"?>',"")

            #now write data into the file
            #the content we are replacing it with also includes the marker, so it can be replaced again
            existingSummary = existingSummary.replace("<!--TEST_CONTENT-->", TEST_RESULT_TEMPLATE % (
            dict(svg=svgText, name=self._testMethodName)))

            writeStringToFile(existingSummary,SUMMARY_FILE)

    def saveModel(self, shape):
        """
            shape must be a CQ object
            Save models in SVG, STEP and STL format
        """

        with suppress_stdout_stderr():
            shape.exportSvg(os.path.join(OUTDIR,self._testMethodName + ".svg"))
            shape.val().exportStep(os.path.join(OUTDIR,self._testMethodName + ".step"))
            shape.val().exportStl(os.path.join(OUTDIR,self._testMethodName + ".stl"))

    def testToFreeCAD(self):
        """
        Tests to make sure that a CadQuery object is converted correctly to a FreeCAD object.
        """
        r = Workplane('XY').rect(5, 5).extrude(5)

        r = r.toFreecad()

        self.assertEqual(12, len(r.Edges))

    def testToSVG(self):
        """
        Tests to make sure that a CadQuery object is converted correctly to SVG
        """
        r = Workplane('XY').rect(5, 5).extrude(5)

        r_str = r.toSvg()

        # Make sure that a couple of sections from the SVG output make sense
        self.assertTrue(r_str.index('path d=" M 2.35965 -2.27987 L 4.0114 -3.23936 "') > 0)

    def testCubePlugin(self):
        """
        Tests a plugin that combines cubes together with a base
        :return:
        """
        #make the plugin method
        def makeCubes(self,length):
            #self refers to the CQ or Workplane object

            #inner method that creates a cube
            def _singleCube(pnt):
                #pnt is a location in local coordinates
                #since we're using eachpoint with useLocalCoordinates=True
                return Solid.makeBox(length,length,length,pnt)

            #use CQ utility method to iterate over the stack, call our
            #method, and convert to/from local coordinates.
            return self.eachpoint(_singleCube,True)

        #link the plugin in
        Workplane.makeCubes = makeCubes

        #call it
        result = Workplane("XY").box(6.0,8.0,0.5).faces(">Z").rect(4.0,4.0,forConstruction=True).vertices()
        result = result.makeCubes(1.0)
        result = result.combineSolids()
        self.saveModel(result)
        self.assertEqual(1,result.solids().size() )


    def testCylinderPlugin(self):
        """
            Tests a cylinder plugin.
            The plugin creates cylinders of the specified radius and height for each item on the stack

            This is a very short plugin that illustrates just about the simplest possible
            plugin
        """

        def cylinders(self,radius,height):

            def _cyl(pnt):
                #inner function to build a cylinder
                return Solid.makeCylinder(radius,height,pnt)

            #combine all the cylinders into a single compound
            r = self.eachpoint(_cyl,True).combineSolids()
            return r
        Workplane.cyl = cylinders

        #now test. here we want weird workplane to see if the objects are transformed right
        s = Workplane(Plane(Vector((0,0,0)),Vector((1,-1,0)),Vector((1,1,0)))).rect(2.0,3.0,forConstruction=True).vertices() \
            .cyl(0.25,0.5)
        self.assertEqual(1,s.solids().size() )
        self.saveModel(s)

    def testPolygonPlugin(self):
        """
            Tests a plugin to make regular polygons around points on the stack

            Demonstratings using eachpoint to allow working in local coordinates
            to create geometry
        """
        def rPoly(self,nSides,diameter):

            def _makePolygon(center):
                #pnt is a vector in local coordinates
                angle = 2.0 *math.pi / nSides
                pnts = []
                for i in range(nSides+1):
                    pnts.append( center + Vector((diameter / 2.0 * math.cos(angle*i)),(diameter / 2.0 * math.sin(angle*i)),0))
                return Wire.makePolygon(pnts)

            return self.eachpoint(_makePolygon,True)

        Workplane.rPoly = rPoly

        s = Workplane("XY").box(4.0,4.0,0.25).faces(">Z").workplane().rect(2.0,2.0,forConstruction=True).vertices()\
            .rPoly(5,0.5).cutThruAll()

        self.assertEqual(26,s.faces().size()) #6 base sides, 4 pentagons, 5 sides each = 26
        self.saveModel(s)


    def testPointList(self):
        """
        Tests adding points and using them
        """
        c = CQ(makeUnitCube())

        s = c.faces(">Z").workplane().pushPoints([(-0.3, 0.3), (0.3, 0.3), (0, 0)])
        self.assertEqual(3, s.size())
        #TODO: is the ability to iterate over points with circle really worth it?
        #maybe we should just require using all() and a loop for this. the semantics and
        #possible combinations got too hard ( ie, .circle().circle() ) was really odd
        body = s.circle(0.05).cutThruAll()
        self.saveModel(body)
        self.assertEqual(9, body.faces().size())

        # Test the case when using eachpoint with only a blank workplane
        def callback_fn(pnt):
            self.assertEqual((0.0, 0.0), (pnt.x, pnt.y))

        r = Workplane('XY')
        r.objects = []
        r.eachpoint(callback_fn)


    def testWorkplaneFromFace(self):
        s = CQ(makeUnitCube()).faces(">Z").workplane() #make a workplane on the top face
        r = s.circle(0.125).cutBlind(-2.0)
        self.saveModel(r)
        #the result should have 7 faces
        self.assertEqual(7,r.faces().size() )
        self.assertEqual(type(r.val()), Solid)
        self.assertEqual(type(r.first().val()),Solid)

    def testFrontReference(self):
        s = CQ(makeUnitCube()).faces("front").workplane() #make a workplane on the top face
        r = s.circle(0.125).cutBlind(-2.0)
        self.saveModel(r)
        #the result should have 7 faces
        self.assertEqual(7,r.faces().size() )
        self.assertEqual(type(r.val()), Solid)
        self.assertEqual(type(r.first().val()),Solid)

    def testMirror(self):
        box = Workplane("XY").box(1, 1, 5)
        box2 = box.mirror()
        box3 = box.mirror("XZ")
        box4 = box.mirror("YZ")

        # Box 2 (XY mirror)
        startPoint2 = box2.faces("<Y").edges("<X").first().val().startPoint().toTuple()
        endPoint2 = box2.faces("<Y").edges("<X").first().val().endPoint().toTuple()
        self.assertEqual(-0.5, startPoint2[0])
        self.assertEqual(-0.5, startPoint2[1])
        self.assertEqual(2.5, startPoint2[2])
        self.assertEqual(-0.5, endPoint2[0])
        self.assertEqual(-0.5, endPoint2[1])
        self.assertEqual(-2.5, endPoint2[2])

        # Box 3 (XZ mirror)
        startPoint3 = box3.faces("<Y").edges("<X").first().val().startPoint().toTuple()
        endPoint3 = box3.faces("<Y").edges("<X").first().val().endPoint().toTuple()
        self.assertEqual(-0.5, startPoint3[0])
        self.assertEqual(-0.5, startPoint3[1])
        self.assertEqual(-2.5, startPoint3[2])
        self.assertEqual(-0.5, endPoint3[0])
        self.assertEqual(-0.5, endPoint3[1])
        self.assertEqual(2.5, endPoint3[2])

        # Box 4 (YZ mirror)
        startPoint4 = box4.faces("<Y").edges("<X").first().val().startPoint().toTuple()
        endPoint4 = box4.faces("<Y").edges("<X").first().val().endPoint().toTuple()
        self.assertEqual(-0.5, startPoint4[0])
        self.assertEqual(-0.5, startPoint4[1])
        self.assertEqual(-2.5, startPoint4[2])
        self.assertEqual(-0.5, endPoint4[0])
        self.assertEqual(-0.5, endPoint4[1])
        self.assertEqual(2.5, endPoint4[2])

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


    def testLoft(self):
        """
            Test making a lofted solid
        :return:
        """
        s = Workplane("XY").circle(4.0).workplane(5.0).rect(2.0,2.0).loft()
        self.saveModel(s)
        #the result should have 7 faces
        self.assertEqual(1,s.solids().size())

        #the resulting loft had a split on the side, not sure why really, i expected only 3 faces
        self.assertEqual(7,s.faces().size() )

    def testLoftCombine(self):
        """
            test combining a lof with another feature
        :return:
        """
        s = Workplane("front").box(4.0,4.0,0.25).faces(">Z").circle(1.5)\
        .workplane(offset=3.0).rect(0.75,0.5).loft(combine=True)
        self.saveModel(s)
        #self.assertEqual(1,s.solids().size() )
        #self.assertEqual(8,s.faces().size() )

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

        #Test revolve without any options for making a cylinder
        result = Workplane("XY").rect(rectangle_width, rectangle_length, False).revolve()
        self.assertEqual(3, result.faces().size())
        self.assertEqual(2, result.vertices().size())
        self.assertEqual(3, result.edges().size())

        #Test revolve when only setting the angle to revolve through
        result = Workplane("XY").rect(rectangle_width, rectangle_length, False).revolve(angle_degrees)
        self.assertEqual(3, result.faces().size())
        self.assertEqual(2, result.vertices().size())
        self.assertEqual(3, result.edges().size())
        result = Workplane("XY").rect(rectangle_width, rectangle_length, False).revolve(270.0)
        self.assertEqual(5, result.faces().size())
        self.assertEqual(6, result.vertices().size())
        self.assertEqual(9, result.edges().size())

        #Test when passing revolve the angle and the axis of revolution's start point
        result = Workplane("XY").rect(rectangle_width, rectangle_length).revolve(angle_degrees,(-5,-5))
        self.assertEqual(3, result.faces().size())
        self.assertEqual(2, result.vertices().size())
        self.assertEqual(3, result.edges().size())
        result = Workplane("XY").rect(rectangle_width, rectangle_length).revolve(270.0,(-5,-5))
        self.assertEqual(5, result.faces().size())
        self.assertEqual(6, result.vertices().size())
        self.assertEqual(9, result.edges().size())

        #Test when passing revolve the angle and both the start and ends of the axis of revolution
        result = Workplane("XY").rect(rectangle_width, rectangle_length).revolve(angle_degrees,(-5, -5),(-5, 5))
        self.assertEqual(3, result.faces().size())
        self.assertEqual(2, result.vertices().size())
        self.assertEqual(3, result.edges().size())
        result = Workplane("XY").rect(rectangle_width, rectangle_length).revolve(270.0,(-5, -5),(-5, 5))
        self.assertEqual(5, result.faces().size())
        self.assertEqual(6, result.vertices().size())
        self.assertEqual(9, result.edges().size())

        #Testing all of the above without combine
        result = Workplane("XY").rect(rectangle_width, rectangle_length).revolve(angle_degrees,(-5,-5),(-5,5), False)
        self.assertEqual(3, result.faces().size())
        self.assertEqual(2, result.vertices().size())
        self.assertEqual(3, result.edges().size())
        result = Workplane("XY").rect(rectangle_width, rectangle_length).revolve(270.0,(-5,-5),(-5,5), False)
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

        result = Workplane("XY").rect(rectangle_width, rectangle_length, True)\
            .revolve(angle_degrees, (20, 0), (20, 10))
        self.assertEqual(4, result.faces().size())
        self.assertEqual(4, result.vertices().size())
        self.assertEqual(6, result.edges().size())

    def testRevolveCone(self):
        """
        Test creating a solid from a revolved triangle
        :return:
        """
        result = Workplane("XY").lineTo(0,10).lineTo(5,0).close().revolve()
        self.assertEqual(2, result.faces().size())
        self.assertEqual(2, result.vertices().size())
        self.assertEqual(3, result.edges().size())

    def testSweep(self):
        """
        Tests the operation of sweeping a wire(s) along a path
        """
        pts = [
            (0, 1),
            (1, 2),
            (2, 4)
        ]

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
        result = Workplane("XY").circle(0.1).sweep(path)
        self.assertEqual(5, result.faces().size())
        self.assertEqual(7, result.edges().size())

        # Arc path
        path = Workplane("XZ").threePointArc((1.0, 1.5),(0.0, 1.0))

        # Test defaults
        result = Workplane("XY").circle(0.1).sweep(path)
        self.assertEqual(3, result.faces().size())
        self.assertEqual(3, result.edges().size())

    def testTwistExtrude(self):
        """
        Tests extrusion while twisting through an angle.
        """
        profile = Workplane('XY').rect(10, 10)
        r = profile.twistExtrude(10, 45, False)

        self.assertEqual(6, r.faces().size())

    def testTwistExtrudeCombine(self):
        """
        Tests extrusion while twisting through an angle, combining with other solids.
        """
        profile = Workplane('XY').rect(10, 10)
        r = profile.twistExtrude(10, 45)

        self.assertEqual(6, r.faces().size())

    def testRectArray(self):
        NUMX=3
        NUMY=3
        s = Workplane("XY").box(40,40,5,centered=(True,True,True)).faces(">Z").workplane().rarray(8.0,8.0,NUMX,NUMY,True).circle(2.0).extrude(2.0)
        #s = Workplane("XY").box(40,40,5,centered=(True,True,True)).faces(">Z").workplane().circle(2.0).extrude(2.0)
        self.saveModel(s)
        self.assertEqual(6+NUMX*NUMY*2,s.faces().size()) #6 faces for the box, 2 faces for each cylinder

    def testNestedCircle(self):
        s = Workplane("XY").box(40,40,5).pushPoints([(10,0),(0,10)]).circle(4).circle(2).extrude(4)
        self.saveModel(s)
        self.assertEqual(14,s.faces().size() )

    def testLegoBrick(self):
        #test making a simple lego brick
        #which of the below

        #inputs
        lbumps = 8
        wbumps = 2

        #lego brick constants
        P = 8.0             #nominal pitch
        c = 0.1             #clearance on each brick side
        H = 1.2 * P         #nominal height of a brick
        bumpDiam = 4.8      #the standard bump diameter
        t  =  ( P - ( 2*c) - bumpDiam ) / 2.0 # the nominal thickness of the walls, normally 1.5

        postDiam = P - t  #works out to 6.5
        total_length = lbumps*P - 2.0*c
        total_width = wbumps*P - 2.0*c

        #build the brick
        s = Workplane("XY").box(total_length,total_width,H) #make the base
        s = s.faces("<Z").shell(-1.0* t) #shell inwards not outwards
        s = s.faces(">Z").workplane().rarray(P,P,lbumps,wbumps,True).circle(bumpDiam/2.0).extrude(1.8) # make the bumps on the top

        #add posts on the bottom. posts are different diameter depending on geometry
        #solid studs for 1 bump, tubes for multiple, none for 1x1
        tmp = s.faces("<Z").workplane(invert=True) #this is cheating a little-- how to select the inner face from the shell?

        if lbumps > 1 and wbumps > 1:
            tmp = tmp.rarray(P,P,lbumps - 1,wbumps - 1,center=True).circle(postDiam/2.0).circle(bumpDiam/2.0).extrude(H-t)
        elif lbumps > 1:
            tmp = tmp.rarray(P,P,lbumps - 1,1,center=True).circle(t).extrude(H-t)
        elif wbumps > 1:
            tmp = tmp.rarray(P,P,1,wbumps -1,center=True).circle(t).extrude(H-t)

        self.saveModel(s)

    def testAngledHoles(self):
        s = Workplane("front").box(4.0,4.0,0.25).faces(">Z").workplane().transformed(offset=Vector(0,-1.5,1.0),rotate=Vector(60,0,0))\
        .rect(1.5,1.5,forConstruction=True).vertices().hole(0.25)
        self.saveModel(s)
        self.assertEqual(10,s.faces().size())

    def testTranslateSolid(self):
        c = CQ(makeUnitCube())
        self.assertAlmostEqual(0.0,c.faces("<Z").vertices().item(0).val().Z, 3 )

        #TODO: it might be nice to provide a version of translate that modifies the existing geometry too
        d = c.translate(Vector(0,0,1.5))
        self.assertAlmostEqual(1.5,d.faces("<Z").vertices().item(0).val().Z, 3 )

    def testTranslateWire(self):
        c = CQ(makeUnitSquareWire())
        self.assertAlmostEqual(0.0,c.edges().vertices().item(0).val().Z, 3 )
        d = c.translate(Vector(0,0,1.5))
        self.assertAlmostEqual(1.5,d.edges().vertices().item(0).val().Z, 3 )

    def testSolidReferencesCombine(self):
        "test that solid references are updated correctly"
        c = CQ( makeUnitCube())                                   #the cube is the context solid
        self.assertEqual(6,c.faces().size())        #cube has six faces

        r = c.faces('>Z').workplane().circle(0.125).extrude(0.5,True)     #make a boss, not updating the original
        self.assertEqual(8,r.faces().size())                  #just the boss faces
        self.assertEqual(8,c.faces().size())                  #original is modified too

    def testSolidReferencesCombineTrue(self):
        s = Workplane(Plane.XY())
        r = s.rect(2.0,2.0).extrude(0.5)
        self.assertEqual(6,r.faces().size() ) #the result of course has 6 faces
        self.assertEqual(0,s.faces().size() ) # the original workplane does not, because it did not have a solid initially

        t = r.faces(">Z").workplane().rect(0.25,0.25).extrude(0.5,True)
        self.assertEqual(11,t.faces().size()) #of course the result has 11 faces
        self.assertEqual(11,r.faces().size()) #r does as well. the context solid for r was updated since combine was true
        self.saveModel(r)

    def testSolidReferenceCombineFalse(self):
        s = Workplane(Plane.XY())
        r = s.rect(2.0,2.0).extrude(0.5)
        self.assertEqual(6,r.faces().size() ) #the result of course has 6 faces
        self.assertEqual(0,s.faces().size() ) # the original workplane does not, because it did not have a solid initially

        t = r.faces(">Z").workplane().rect(0.25,0.25).extrude(0.5,False)
        self.assertEqual(6,t.faces().size()) #result has 6 faces, becuase it was not combined with the original
        self.assertEqual(6,r.faces().size()) #original is unmodified as well
        #subseuent opertions use that context solid afterwards

    def testSimpleWorkplane(self):
        """
            A simple square part with a hole in it
        """
        s = Workplane(Plane.XY())
        r = s.rect(2.0,2.0).extrude(0.5)\
            .faces(">Z").workplane()\
            .circle(0.25).cutBlind(-1.0)

        self.saveModel(r)
        self.assertEqual(7,r.faces().size() )

    def testMultiFaceWorkplane(self):
        """
        Test Creation of workplane from multiple co-planar face
        selection.
        """
        s = Workplane('XY').box(1,1,1).faces('>Z').rect(1,0.5).cutBlind(-0.2)

        w = s.faces('>Z').workplane()
        o = w.objects[0] # origin of the workplane
        self.assertAlmostEqual(o.x, 0., 3)
        self.assertAlmostEqual(o.y, 0., 3)
        self.assertAlmostEqual(o.z, 0.5, 3)

    def testTriangularPrism(self):
        s = Workplane("XY").lineTo(1,0).lineTo(1,1).close().extrude(0.2)
        self.saveModel(s)

    def testMultiWireWorkplane(self):
        """
            A simple square part with a hole in it-- but this time done as a single extrusion
            with two wires, as opposed to s cut
        """
        s = Workplane(Plane.XY())
        r = s.rect(2.0,2.0).circle(0.25).extrude(0.5)

        self.saveModel(r)
        self.assertEqual(7,r.faces().size() )

    def testConstructionWire(self):
        """
            Tests a wire with several holes, that are based on the vertices of a square
            also tests using a workplane plane other than XY
        """
        s = Workplane(Plane.YZ())
        r = s.rect(2.0,2.0).rect(1.3,1.3,forConstruction=True).vertices().circle(0.125).extrude(0.5)
        self.saveModel(r)
        self.assertEqual(10,r.faces().size() ) # 10 faces-- 6 plus 4 holes, the vertices of the second rect.

    def testTwoWorkplanes(self):
        """
            Tests a model that uses more than one workplane
        """
        #base block
        s = Workplane(Plane.XY())

        #TODO: this syntax is nice, but the iteration might not be worth
        #the complexity.
        #the simpler and slightly longer version would be:
        #    r = s.rect(2.0,2.0).rect(1.3,1.3,forConstruction=True).vertices()
        #    for c in r.all():
        #           c.circle(0.125).extrude(0.5,True)
        r = s.rect(2.0,2.0).rect(1.3,1.3,forConstruction=True).vertices().circle(0.125).extrude(0.5)

        #side hole, blind deep 1.9
        t = r.faces(">Y").workplane().circle(0.125).cutBlind(-1.9)
        self.saveModel(t)
        self.assertEqual(12,t.faces().size() )

    def testCut(self):
        """
        Tests the cut function by itself to catch the case where a Solid object is passed.
        """
        s = Workplane(Plane.XY())
        currentS = s.rect(2.0,2.0).extrude(0.5)
        toCut = s.rect(1.0,1.0).extrude(0.5)

        currentS.cut(toCut.val())

        self.assertEqual(10,currentS.faces().size())

    def testIntersect(self):
        """
        Tests the intersect function.
        """
        s = Workplane(Plane.XY())
        currentS = s.rect(2.0, 2.0).extrude(0.5)
        toIntersect = s.rect(1.0, 1.0).extrude(1)

        currentS.intersect(toIntersect.val())

        self.assertEqual(6, currentS.faces().size())
        bb = currentS.val().BoundingBox()
        self.assertListEqual([bb.xlen, bb.ylen, bb.zlen], [1, 1, 0.5])

    def testBoundingBox(self):
        """
        Tests the boudingbox center of a model
        """
        result0 = (Workplane("XY")
                    .moveTo(10,0)
                    .lineTo(5,0)
                    .threePointArc((3.9393,0.4393),(3.5,1.5))
                    .threePointArc((3.0607,2.5607),(2,3))
                    .lineTo(1.5,3)
                    .threePointArc((0.4393,3.4393),(0,4.5))
                    .lineTo(0,13.5)
                    .threePointArc((0.4393,14.5607),(1.5,15))
                    .lineTo(28,15)
                    .lineTo(28,13.5)
                    .lineTo(24,13.5)
                    .lineTo(24,11.5)
                    .lineTo(27,11.5)
                    .lineTo(27,10)
                    .lineTo(22,10)
                    .lineTo(22,13.2)
                    .lineTo(14.5,13.2)
                    .lineTo(14.5,10)
                    .lineTo(12.5,10 )
                    .lineTo(12.5,13.2)
                    .lineTo(5.5,13.2)
                    .lineTo(5.5,2)
                    .threePointArc((5.793,1.293),(6.5,1))
                    .lineTo(10,1)
                    .close())

        result = result0.extrude(100)
        bb_center = result.val().BoundingBox().center
        self.saveModel(result)
        self.assertAlmostEqual(14.0, bb_center.x, 3)
        self.assertAlmostEqual(7.5, bb_center.y, 3)
        self.assertAlmostEqual(50.0, bb_center.z, 3)

    def testCutThroughAll(self):
        """
            Tests a model that uses more than one workplane
        """
        #base block
        s = Workplane(Plane.XY())
        r = s.rect(2.0,2.0).rect(1.3,1.3,forConstruction=True).vertices().circle(0.125).extrude(0.5)

        #side hole, thru all
        t = r.faces(">Y").workplane().circle(0.125).cutThruAll()
        self.saveModel(t)
        self.assertEqual(11,t.faces().size() )

    def testCutToFaceOffsetNOTIMPLEMENTEDYET(self):
        """
            Tests cutting up to a given face, or an offset from a face
        """
        #base block
        s = Workplane(Plane.XY())
        r = s.rect(2.0,2.0).rect(1.3,1.3,forConstruction=True).vertices().circle(0.125).extrude(0.5)

        #side hole, up to 0.1 from the last face
        try:
            t = r.faces(">Y").workplane().circle(0.125).cutToOffsetFromFace(r.faces().mminDist(Dir.Y),0.1)
            self.assertEqual(10,t.faces().size() ) #should end up being a blind hole
            with suppress_stdout_stderr():
                t.first().val().exportStep('c:/temp/testCutToFace.STEP')
        except:
            pass
            #Not Implemented Yet

    def testWorkplaneOnExistingSolid(self):
        "Tests extruding on an existing solid"
        c = CQ( makeUnitCube()).faces(">Z").workplane().circle(0.25).circle(0.125).extrude(0.25)
        self.saveModel(c)
        self.assertEqual(10,c.faces().size() )


    def testWorkplaneCenterMove(self):
        #this workplane is centered at x=0.5,y=0.5, the center of the upper face
        s = Workplane("XY").box(1,1,1).faces(">Z").workplane().center(-0.5,-0.5) # move the center to the corner

        t = s.circle(0.25).extrude(0.2) # make a boss
        self.assertEqual(9,t.faces().size() )
        self.saveModel(t)


    def testBasicLines(self):
        "Make a triangluar boss"
        global OUTDIR
        s = Workplane(Plane.XY())

        #TODO:  extrude() should imply wire() if not done already
        #most users dont understand what a wire is, they are just drawing

        r = s.lineTo(1.0,0).lineTo(0,1.0).close().wire().extrude(0.25)
        with suppress_stdout_stderr():
            r.val().exportStep(os.path.join(OUTDIR, 'testBasicLinesStep1.STEP'))

        self.assertEqual(0,s.faces().size()) #no faces on the original workplane
        self.assertEqual(5,r.faces().size() ) # 5 faces on newly created object

        #now add a circle through a side face
        r.faces("+XY").workplane().circle(0.08).cutThruAll()
        self.assertEqual(6,r.faces().size())
        with suppress_stdout_stderr():
            r.val().exportStep(os.path.join(OUTDIR, 'testBasicLinesXY.STEP'))

        #now add a circle through a top
        r.faces("+Z").workplane().circle(0.08).cutThruAll()
        self.assertEqual(9,r.faces().size())
        with suppress_stdout_stderr():
            r.val().exportStep(os.path.join(OUTDIR, 'testBasicLinesZ.STEP'))

        self.saveModel(r)

    def test2DDrawing(self):
        """
        Draw things like 2D lines and arcs, should be expanded later to include all 2D constructs
        """
        s = Workplane(Plane.XY())
        r = s.lineTo(1.0, 0.0) \
             .lineTo(1.0, 1.0) \
             .threePointArc((1.0, 1.5), (0.0, 1.0)) \
             .lineTo(0.0, 0.0) \
             .moveTo(1.0, 0.0) \
             .lineTo(2.0, 0.0) \
             .lineTo(2.0, 2.0) \
             .threePointArc((2.0, 2.5), (0.0, 2.0)) \
             .lineTo(-2.0, 2.0) \
             .lineTo(-2.0, 0.0) \
             .close()

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
        self.assertEqual((1.0, 1.0),
                         (r.vertices(selectors.NearestToPointSelector((0.0, 0.0, 0.0)))\
                          .first().val().X,
                          r.vertices(selectors.NearestToPointSelector((0.0, 0.0, 0.0)))\
                          .first().val().Y))

    def testLargestDimension(self):
        """
        Tests the largestDimension function when no solids are on the stack and when there are
        """
        r = Workplane('XY').box(1, 1, 1)
        dim = r.largestDimension()

        self.assertAlmostEqual(8.66025403784, dim)

        r = Workplane('XY')
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
        #draw half the profile of the bottle
        p = s.center(-L/2.0,0).vLine(w/2.0).threePointArc((L/2.0, w/2.0 + t),(L,w/2.0)).vLine(-w/2.0).mirrorX()\
            .extrude(30.0,True)

        #make the neck
        p.faces(">Z").workplane().circle(3.0).extrude(2.0,True)  #.edges().fillet(0.05)

        #make a shell
        p.faces(">Z").shell(0.3)
        self.saveModel(p)


    def testSplineShape(self):
        """
            Tests making a shape with an edge that is a spline
        """
        s = Workplane(Plane.XY())
        sPnts = [
            (2.75,1.5),
            (2.5,1.75),
            (2.0,1.5),
            (1.5,1.0),
            (1.0,1.25),
            (0.5,1.0),
            (0,1.0)
        ]
        r = s.lineTo(3.0,0).lineTo(3.0,1.0).spline(sPnts).close()
        r = r.extrude(0.5)
        self.saveModel(r)

    def testSimpleMirror(self):
        """
            Tests a simple mirroring operation
        """
        s = Workplane("XY").lineTo(2, 2).threePointArc((3, 1), (2, 0)) \
            .mirrorX().extrude(0.25)
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
            (0, t/2),
            (r/2-1.5*t, r/2-t),
            (s/2, r/2-t),
            (s/2, r/2),
            (r/2, r/2),
            (r/2, s/2),
            (r/2-t, s/2),
            (r/2-t, r/2-1.5*t),
            (t/2, 0)
        ]

        r = Workplane("XY").polyline(points).mirrorX()

        self.assertEqual(1, r.wires().size())
        self.assertEqual(18, r.edges().size())

    # def testChainedMirror(self):
    #     """
    #     Tests whether or not calling mirrorX().mirrorY() works correctly
    #     """
    #     r = 20
    #     s = 7
    #     t = 1.5
    #
    #     points = [
    #         (0, t/2),
    #         (r/2-1.5*t, r/2-t),
    #         (s/2, r/2-t),
    #         (s/2, r/2),
    #         (r/2, r/2),
    #         (r/2, s/2),
    #         (r/2-t, s/2),
    #         (r/2-t, r/2-1.5*t),
    #         (t/2, 0)
    #     ]
    #
    #     r = Workplane("XY").polyline(points).mirrorX().mirrorY()
    #
    #     self.assertEquals(1, r.wires().size())
    #     self.assertEquals(32, r.edges().size())

    #TODO: Re-work testIbeam test below now that chaining works
    #TODO: Add toLocalCoords and toWorldCoords tests

    def testIbeam(self):
        """
            Make an ibeam. demonstrates fancy mirroring
        """
        s = Workplane(Plane.XY())
        L = 100.0
        H = 20.0
        W = 20.0

        t = 1.0
        #TODO: for some reason doing 1/4 of the profile and mirroring twice ( .mirrorX().mirrorY() )
        #did not work, due to a bug in freecad-- it was losing edges when creating a composite wire.
        #i just side-stepped it for now

        pts = [
            (0, H/2.0),
            (W/2.0, H/2.0),
            (W/2.0, (H/2.0 - t)),
            (t/2.0, (H/2.0-t)),
            (t/2.0, (t - H/2.0)),
            (W/2.0, (t - H/2.0)),
            (W/2.0, H / -2.0),
            (0, H/-2.0)
        ]
        r = s.polyline(pts).mirrorY()  #these other forms also work
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
        c = CQ( makeUnitCube()).faces(">Z").workplane().circle(0.25).extrude(0.25,True).edges("|Z").fillet(0.2)
        self.saveModel(c)
        self.assertEqual(12,c.faces().size() )

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
        pnts = [
            (-1.0, -1.0), (0.0, 0.0), (1.0, 1.0)
        ]
        c.faces(">Z").workplane().pushPoints(pnts).cboreHole(0.1, 0.25, 0.25, 0.75)
        self.assertEqual(18, c.faces().size())
        self.saveModel(c)

        # Tests the case where the depth of the cboreHole is not specified
        c2 = CQ(makeCube(3.0))
        pnts = [
            (-1.0, -1.0), (0.0, 0.0), (1.0, 1.0)
        ]
        c2.faces(">Z").workplane().pushPoints(pnts).cboreHole(0.1, 0.25, 0.25)
        self.assertEqual(15, c2.faces().size())

    def testCounterSinks(self):
        """
            Tests countersinks
        """
        s = Workplane(Plane.XY())
        result = s.rect(2.0, 4.0).extrude(0.5).faces(">Z").workplane()\
            .rect(1.5, 3.5, forConstruction=True).vertices().cskHole(0.125, 0.25, 82, depth=None)
        self.saveModel(result)

    def testSplitKeepingHalf(self):
        """
        Tests splitting a solid
        """

        #drill a hole in the side
        c = CQ(makeUnitCube()).faces(">Z").workplane().circle(0.25).cutThruAll()

        self.assertEqual(7, c.faces().size())

        #now cut it in half sideways
        c.faces(">Y").workplane(-0.5).split(keepTop=True)
        self.saveModel(c)
        self.assertEqual(8, c.faces().size())

    def testSplitKeepingBoth(self):
        """
        Tests splitting a solid
        """

        #drill a hole in the side
        c = CQ(makeUnitCube()).faces(">Z").workplane().circle(0.25).cutThruAll()
        self.assertEqual(7, c.faces().size())

        #now cut it in half sideways
        result = c.faces(">Y").workplane(-0.5).split(keepTop=True, keepBottom=True)

        #stack will have both halves, original will be unchanged
        self.assertEqual(2, result.solids().size())  # two solids are on the stack, eac
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

        #stack will have both halves, original will be unchanged
        self.assertEqual(1, result.solids().size())  # one solid is on the stack
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
        s = Workplane("XY").box(2, 2, 2).faces("+Z").shell(0.05)
        self.saveModel(s)
        self.assertEqual(23, s.faces().size())


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
        s = Workplane("XY").rect(4.0, 4.0, forConstruction=True).vertices().box(0.25, 0.25, 0.25, combine=True)
        #1 object, 4 solids because the object is a compound
        self.assertEqual(1, s.solids().size())
        self.assertEqual(1, s.size())
        self.saveModel(s)

        s = Workplane("XY").rect(4.0, 4.0, forConstruction=True).vertices().box(0.25, 0.25, 0.25, combine=False)
        #4 objects, 4 solids, because each is a separate solid
        self.assertEqual(4, s.size())
        self.assertEqual(4, s.solids().size())

    def testBoxCombine(self):
        s = Workplane("XY").box(4, 4, 0.5).faces(">Z").workplane().rect(3, 3, forConstruction=True).vertices().box(0.25, 0.25, 0.25, combine=True)

        self.saveModel(s)
        self.assertEqual(1, s.solids().size())  # we should have one big solid
        self.assertEqual(26, s.faces().size())  # should have 26 faces. 6 for the box, and 4x5 for the smaller cubes

    def testSphereDefaults(self):
        s = Workplane("XY").sphere(10)
        #self.saveModel(s) # Until FreeCAD fixes their sphere operation
        self.assertEqual(1, s.solids().size())
        self.assertEqual(1, s.faces().size())

    def testSphereCustom(self):
        s = Workplane("XY").sphere(10, angle1=0, angle2=90, angle3=360, centered=(False, False, False))
        self.saveModel(s)
        self.assertEqual(1, s.solids().size())
        self.assertEqual(2, s.faces().size())

    def testSpherePointList(self):
        s = Workplane("XY").rect(4.0, 4.0, forConstruction=True).vertices().sphere(0.25, combine=False)
        #self.saveModel(s) # Until FreeCAD fixes their sphere operation
        self.assertEqual(4, s.solids().size())
        self.assertEqual(4, s.faces().size())

    def testSphereCombine(self):
        s = Workplane("XY").rect(4.0, 4.0, forConstruction=True).vertices().sphere(0.25, combine=True)
        #self.saveModel(s) # Until FreeCAD fixes their sphere operation
        self.assertEqual(1, s.solids().size())
        self.assertEqual(4, s.faces().size())

    def testQuickStartXY(self):
        s = Workplane(Plane.XY()).box(2, 4, 0.5).faces(">Z").workplane().rect(1.5, 3.5, forConstruction=True)\
        .vertices().cskHole(0.125, 0.25, 82, depth=None)
        self.assertEqual(1, s.solids().size())
        self.assertEqual(14, s.faces().size())
        self.saveModel(s)

    def testQuickStartYZ(self):
        s = Workplane(Plane.YZ()).box(2, 4, 0.5).faces(">X").workplane().rect(1.5, 3.5, forConstruction=True)\
            .vertices().cskHole(0.125, 0.25, 82, depth=None)
        self.assertEqual(1, s.solids().size())
        self.assertEqual(14, s.faces().size())
        self.saveModel(s)

    def testQuickStartXZ(self):
        s = Workplane(Plane.XZ()).box(2, 4, 0.5).faces(">Y").workplane().rect(1.5, 3.5, forConstruction=True)\
                                 .vertices().cskHole(0.125, 0.25, 82, depth=None)
        self.assertEqual(1, s.solids().size())
        self.assertEqual(14, s.faces().size())
        self.saveModel(s)

    def testDoubleTwistedLoft(self):
        s = Workplane("XY").polygon(8, 20.0).workplane(offset=4.0).transformed(rotate=Vector(0, 0, 15.0)).polygon(8, 20).loft()
        s2 = Workplane("XY").polygon(8, 20.0).workplane(offset=-4.0).transformed(rotate=Vector(0, 0, 15.0)).polygon(8, 20).loft()
        #self.assertEquals(10,s.faces().size())
        #self.assertEquals(1,s.solids().size())
        s3 = s.combineSolids(s2)
        self.saveModel(s3)

    def testTwistedLoft(self):
        s = Workplane("XY").polygon(8,20.0).workplane(offset=4.0).transformed(rotate=Vector(0,0,15.0)).polygon(8,20).loft()
        self.assertEqual(10,s.faces().size())
        self.assertEqual(1,s.solids().size())
        self.saveModel(s)

    def testUnions(self):
        #duplicates a memory problem of some kind reported when combining lots of objects
        s = Workplane("XY").rect(0.5,0.5).extrude(5.0)
        o = []
        beginTime = time.time()
        for i in range(15):
            t = Workplane("XY").center(10.0*i,0).rect(0.5,0.5).extrude(5.0)
            o.append(t)

        #union stuff
        for oo in o:
            s  = s.union(oo)
        print("Total time %0.3f" % (time.time() - beginTime))

        #Test unioning a Solid object
        s = Workplane(Plane.XY())
        currentS = s.rect(2.0,2.0).extrude(0.5)
        toUnion = s.rect(1.0,1.0).extrude(1.0)

        currentS.union(toUnion.val(), combine=False)

        #TODO: When unioning and combining is figured out, uncomment the following assert
        #self.assertEqual(10,currentS.faces().size())

    def testCombine(self):
        s = Workplane(Plane.XY())
        objects1 = s.rect(2.0,2.0).extrude(0.5).faces('>Z').rect(1.0,1.0).extrude(0.5)

        objects1.combine()

        self.assertEqual(11, objects1.faces().size())


    def testCombineSolidsInLoop(self):
        #duplicates a memory problem of some kind reported when combining lots of objects
        s = Workplane("XY").rect(0.5,0.5).extrude(5.0)
        o = []
        beginTime = time.time()
        for i in range(15):
            t = Workplane("XY").center(10.0*i,0).rect(0.5,0.5).extrude(5.0)
            o.append(t)

        #append the 'good way'
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
        s = Workplane("XY").moveTo(0,0).line(5,0).line(5,0).line(0,10).\
            line(-10,0).close().extrude(10)

        self.assertEqual(6, s.faces().size())

        # test removal of splitter caused by union operation
        s = Workplane("XY").box(10,10,10).union(Workplane("XY").box(20,10,10))

        self.assertEqual(6, s.faces().size())

        # test removal of splitter caused by extrude+combine operation
        s = Workplane("XY").box(10,10,10).faces(">Y").\
            workplane().rect(5,10,5).extrude(20)

        self.assertEqual(10, s.faces().size())

        # test removal of splitter caused by double hole operation
        s = Workplane("XY").box(10,10,10).faces(">Z").workplane().\
            hole(3,5).faces(">Z").workplane().hole(3,10)

        self.assertEqual(7, s.faces().size())

        # test removal of splitter caused by cutThruAll
        s = Workplane("XY").box(10,10,10).faces(">Y").workplane().\
            rect(10,5).cutBlind(-5).faces(">Z").workplane().\
            center(0,2.5).rect(5,5).cutThruAll()

        self.assertEqual(18, s.faces().size())

        # test removal of splitter with box
        s = Workplane("XY").box(5,5,5).box(10,5,2)

        self.assertEqual(14, s.faces().size())

    def testNoClean(self):
        """
        Test the case when clean is disabled.
        """
        # test disabling autoSimplify
        s = Workplane("XY").moveTo(0,0).line(5,0).line(5,0).line(0,10).\
            line(-10,0).close().extrude(10, clean=False)
        self.assertEqual(7, s.faces().size())

        s = Workplane("XY").box(10,10,10).\
            union(Workplane("XY").box(20,10,10), clean=False)
        self.assertEqual(14, s.faces().size())

        s = Workplane("XY").box(10,10,10).faces(">Y").\
            workplane().rect(5,10,5).extrude(20, clean=False)

        self.assertEqual(12, s.faces().size())

    def testExplicitClean(self):
        """
        Test running of `clean()` method explicitly.
        """
        s = Workplane("XY").moveTo(0,0).line(5,0).line(5,0).line(0,10).\
            line(-10,0).close().extrude(10,clean=False).clean()
        self.assertEqual(6, s.faces().size())

    def testPlanes(self):
        """
        Test other planes other than the normal ones (XY, YZ)
        """
        # ZX plane
        s = Workplane(Plane.ZX())
        result = s.rect(2.0, 4.0).extrude(0.5).faces(">Z").workplane()\
            .rect(1.5, 3.5, forConstruction=True).vertices().cskHole(0.125, 0.25, 82, depth=None)
        self.saveModel(result)

        # YX plane
        s = Workplane(Plane.YX())
        result = s.rect(2.0, 4.0).extrude(0.5).faces(">Z").workplane()\
            .rect(1.5, 3.5, forConstruction=True).vertices().cskHole(0.125, 0.25, 82, depth=None)
        self.saveModel(result)

        # YX plane
        s = Workplane(Plane.YX())
        result = s.rect(2.0, 4.0).extrude(0.5).faces(">Z").workplane()\
            .rect(1.5, 3.5, forConstruction=True).vertices().cskHole(0.125, 0.25, 82, depth=None)
        self.saveModel(result)

        # ZY plane
        s = Workplane(Plane.ZY())
        result = s.rect(2.0, 4.0).extrude(0.5).faces(">Z").workplane()\
            .rect(1.5, 3.5, forConstruction=True).vertices().cskHole(0.125, 0.25, 82, depth=None)
        self.saveModel(result)

        # front plane
        s = Workplane(Plane.front())
        result = s.rect(2.0, 4.0).extrude(0.5).faces(">Z").workplane()\
            .rect(1.5, 3.5, forConstruction=True).vertices().cskHole(0.125, 0.25, 82, depth=None)
        self.saveModel(result)

        # back plane
        s = Workplane(Plane.back())
        result = s.rect(2.0, 4.0).extrude(0.5).faces(">Z").workplane()\
            .rect(1.5, 3.5, forConstruction=True).vertices().cskHole(0.125, 0.25, 82, depth=None)
        self.saveModel(result)

        # left plane
        s = Workplane(Plane.left())
        result = s.rect(2.0, 4.0).extrude(0.5).faces(">Z").workplane()\
            .rect(1.5, 3.5, forConstruction=True).vertices().cskHole(0.125, 0.25, 82, depth=None)
        self.saveModel(result)

        # right plane
        s = Workplane(Plane.right())
        result = s.rect(2.0, 4.0).extrude(0.5).faces(">Z").workplane()\
            .rect(1.5, 3.5, forConstruction=True).vertices().cskHole(0.125, 0.25, 82, depth=None)
        self.saveModel(result)

        # top plane
        s = Workplane(Plane.top())
        result = s.rect(2.0, 4.0).extrude(0.5).faces(">Z").workplane()\
            .rect(1.5, 3.5, forConstruction=True).vertices().cskHole(0.125, 0.25, 82, depth=None)
        self.saveModel(result)

        # bottom plane
        s = Workplane(Plane.bottom())
        result = s.rect(2.0, 4.0).extrude(0.5).faces(">Z").workplane()\
            .rect(1.5, 3.5, forConstruction=True).vertices().cskHole(0.125, 0.25, 82, depth=None)
        self.saveModel(result)

    def testIsIndide(self):
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

        #for some reason shell doesnt work on this simple shape. how disappointing!
        td = 50.0
        bd = 20.0
        h = 10.0
        t = 1.0
        s1 = Workplane("XY").circle(bd).workplane(offset=h).circle(td).loft()
        s2 = Workplane("XY").workplane(offset=t).circle(bd-(2.0*t)).workplane(offset=(h-t)).circle(td-(2.0*t)).loft()
        s3 = s1.cut(s2)
        self.saveModel(s3)


    def testEnclosure(self):
        """
            Builds an electronics enclosure
            Original FreeCAD script: 81 source statements ,not including variables
            This script: 34
        """

        #parameter definitions
        p_outerWidth = 100.0 #Outer width of box enclosure
        p_outerLength = 150.0 #Outer length of box enclosure
        p_outerHeight = 50.0 #Outer height of box enclosure

        p_thickness =  3.0 #Thickness of the box walls
        p_sideRadius =  10.0 #Radius for the curves around the sides of the bo
        p_topAndBottomRadius =  2.0 #Radius for the curves on the top and bottom edges of the box

        p_screwpostInset = 12.0 #How far in from the edges the screwposts should be place.
        p_screwpostID = 4.0 #nner Diameter of the screwpost holes, should be roughly screw diameter not including threads
        p_screwpostOD = 10.0 #Outer Diameter of the screwposts.\nDetermines overall thickness of the posts

        p_boreDiameter = 8.0 #Diameter of the counterbore hole, if any
        p_boreDepth = 1.0 #Depth of the counterbore hole, if
        p_countersinkDiameter = 0.0 #Outer diameter of countersink.  Should roughly match the outer diameter of the screw head
        p_countersinkAngle = 90.0 #Countersink angle (complete angle between opposite sides, not from center to one side)
        p_flipLid = True #Whether to place the lid with the top facing down or not.
        p_lipHeight =  1.0 #Height of lip on the underside of the lid.\nSits inside the box body for a snug fit.

        #outer shell
        oshell = Workplane("XY").rect(p_outerWidth,p_outerLength).extrude(p_outerHeight + p_lipHeight)

        #weird geometry happens if we make the fillets in the wrong order
        if p_sideRadius > p_topAndBottomRadius:
            oshell.edges("|Z").fillet(p_sideRadius)
            oshell.edges("#Z").fillet(p_topAndBottomRadius)
        else:
            oshell.edges("#Z").fillet(p_topAndBottomRadius)
            oshell.edges("|Z").fillet(p_sideRadius)

        #inner shell
        ishell = oshell.faces("<Z").workplane(p_thickness,True)\
            .rect((p_outerWidth - 2.0* p_thickness),(p_outerLength - 2.0*p_thickness))\
            .extrude((p_outerHeight - 2.0*p_thickness),False) #set combine false to produce just the new boss
        ishell.edges("|Z").fillet(p_sideRadius - p_thickness)

        #make the box outer box
        box = oshell.cut(ishell)

        #make the screwposts
        POSTWIDTH = (p_outerWidth - 2.0*p_screwpostInset)
        POSTLENGTH = (p_outerLength  -2.0*p_screwpostInset)

        postCenters = box.faces(">Z").workplane(-p_thickness)\
            .rect(POSTWIDTH,POSTLENGTH,forConstruction=True)\
            .vertices()

        for v in postCenters.all():
           v.circle(p_screwpostOD/2.0).circle(p_screwpostID/2.0)\
                .extrude((-1.0)*(p_outerHeight + p_lipHeight -p_thickness ),True)

        #split lid into top and bottom parts
        (lid,bottom) = box.faces(">Z").workplane(-p_thickness -p_lipHeight ).split(keepTop=True,keepBottom=True).all()  #splits into two solids

        #translate the lid, and subtract the bottom from it to produce the lid inset
        lowerLid = lid.translate((0,0,-p_lipHeight))
        cutlip = lowerLid.cut(bottom).translate((p_outerWidth + p_thickness ,0,p_thickness - p_outerHeight + p_lipHeight))

        #compute centers for counterbore/countersink or counterbore
        topOfLidCenters = cutlip.faces(">Z").workplane().rect(POSTWIDTH,POSTLENGTH,forConstruction=True).vertices()

        #add holes of the desired type
        if p_boreDiameter > 0 and p_boreDepth > 0:
            topOfLid = topOfLidCenters.cboreHole(p_screwpostID,p_boreDiameter,p_boreDepth,(2.0)*p_thickness)
        elif p_countersinkDiameter > 0 and p_countersinkAngle > 0:
            topOfLid = topOfLidCenters.cskHole(p_screwpostID,p_countersinkDiameter,p_countersinkAngle,(2.0)*p_thickness)
        else:
            topOfLid= topOfLidCenters.hole(p_screwpostID,(2.0)*p_thickness)

        #flip lid upside down if desired
        if p_flipLid:
            topOfLid.rotateAboutCenter((1,0,0),180)

        #return the combined result
        result =topOfLid.union(bottom)

        self.saveModel(result)

    def testExtrude(self):
        """
        Test symmetric extrude
        """
        r = 1.
        h = 1.
        decimal_places = 9.

        #extrude symmetrically
        s = Workplane("XY").circle(r).extrude(h,both=True)

        top_face = s.faces(">Z")
        bottom_face = s.faces("<Z")

        #calculate the distance between the top and the bottom face
        delta = top_face.val().Center().sub(bottom_face.val().Center())

        self.assertTupleAlmostEquals(delta.toTuple(),
                                     (0.,0.,2.*h),
                                     decimal_places)
