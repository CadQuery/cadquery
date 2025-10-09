from cadquery.occ_impl.shapes import Location, Plane, Vector
import pytest
import itertools

#Conversion can betriggered from explicit constructor, or from property
@pytest.mark.parametrize(
    ["useproperty",],
    [
        (False,),
        (True,),
    ]
)
#Create different test cases from different initial plane.
#Testing the different components is mainly useful for debugging if things
#do not work.
@pytest.mark.parametrize(
    ["plargs",],
    [
        #Default plane
        (((3, 5, 6),),),
        #Just xDir specified
        (((3, 5, 6), (1, 0, 0),),),
        (((3, 5, 6), (0, 1, 0),),),
        #xDir and normal specified.
        #Omit normals, that were included as default, and once which
        #have no component orthogonal to xDir
        (((3, 5, 6), (1, 0, 0), (0, 1, 0),),),
        (((3, 5, 6), (0, 1, 0), (1, 0, 0),),),
        #JUst xDir, but with multiple vector components
        (((3, 5, 6), (1, 1, 0),),),
        (((3, 5, 6), (1, 0, 1),),),
        (((3, 5, 6), (0, 1, 1),),),
        #Multiple components in xdir and normal
        (((3, 5, 6), (1, 1, 0), (1, 0, 1),),),
        (((3, 5, 6), (1, 1, 0), (0, 1, 1),),),
        (((3, 5, 6), (1, 0, 1), (1, 1, 0),),),
        (((3, 5, 6), (1, 0, 1), (0, 1, 1),),),
        (((3, 5, 6), (0, 1, 1), (1, 1, 0),),),
        (((3, 5, 6), (0, 1, 1), (1, 0, 1),),),
        #Same, but introduce negative directions
        (((3, 5, 6), (-1, 1, 0), (-1, 0, -1),),),
        (((3, 5, 6), (1, -1, 0), (0, -1, -1),),),
        (((3, 5, 6), (1, 0, -1), (1, -1, 0),),),
        (((3, 5, 6), (1, 0, -1), (0, -1, 1),),),
        (((3, 5, 6), (0, -1, -1), (-1, 1, 0),),),
        (((3, 5, 6), (0, -1, -1), (1, 0, -1),),),
        #Vectors with random non-trivial directions
        (((3, 5, 6), (2, 4, 7), (9, 8, 1),),),
    ]
)
def test_Plane_from_Location(plargs, useproperty):
    #Test conversion between Plane and Location by converting multiple
    #times between them, such that two Plane and two Location can be
    #compared respectively.
    
    #If there are three things in plargs, ensure that xDir and normal are
    #orthogonal. That should be ensured by an exception in Plane.__init__.
    #This here makes the normal orthogonal to xDir by subtracting its
    #projection on xDir.
    #If no normal is given, the default normal is assumed.
    if len(plargs) == 2:
        plargs = (*plargs, (0, 0, 1))
    if len(plargs) == 3:
        origin, xDir, normal = plargs
        xDir = Vector(xDir)
        normal = Vector(normal)
        normal -= normal.projectToLine(xDir)
        plargs = (origin, xDir, normal)
    
    #Start from random Plane with classical __init__
    originalpl = Plane(*plargs)
    
    #Convert back and forth, such that comparable pairs are created.
    #Depending on test fixture, call constructor directly or use properties
    if useproperty:
        locforth = originalpl.location
        plback = locforth.plane
        locback = plback.location
    else:
        locforth = Location(originalpl)
        plback = Plane(locforth)
        locback = Location(plback)
    
    #Create raw locations, which are flat tuples of raw numbers, suitable for
    #assertion with pytes.approx
    locraws = list()
    for loc in (locforth, locback):
        loc = loc.toTuple()
        loc = tuple(itertools.chain(*loc))
        locraws.append(loc)
        
    #Same for planes
    plraws = list()
    for pl in (originalpl, plback):
        pl = (
            pl.origin.toTuple(),
            pl.xDir.toTuple(),
            pl.yDir.toTuple(),
            pl.zDir.toTuple(),
        )
        pl = tuple(itertools.chain(*pl))
        plraws.append(pl)
    
    #Perform assertions
    assert locraws[0] == pytest.approx(locraws[1])
    assert plraws[0] == pytest.approx(plraws[1])
