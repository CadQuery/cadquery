from cadquery.occ_impl.shapes import Location, Plane
import pytest
import itertools

def test_Plane_from_Location():
    
    #Star from random lcation and plane
    originalloc = Location(x=3, y=5, z=6, rx=15, ry=25, rz=40)
    originalpl = Plane((3, 5, 6), (2, 4, 7), (9, 8, 1))
    
    #Convert back and forth, such that comparable pairs are created
    plforth = Plane(originalloc)
    locforth = Location(originalpl)
    locback = Location(plforth)
    plback = Plane(locforth)
    
    #Create raw locations, which are flat tuples of raw numbers, suitable for
    #assertion with pytes.approx
    locraws = list()
    for loc in (originalloc, locback):
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
