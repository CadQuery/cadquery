from cadquery.occ_impl.shapes import Location, Plane
import pytest
import itertools

def test_Plane_from_Location():
    originalloc = Location(x=3, y=5, z=6, rx=15, ry=25, rz=40)
    originalpl = Plane((3, 5, 6), (2, 4, 7), (9, 8, 1))
    
    plforth = Plane(originalloc)
    locforth = Location(originalpl)
    
    locback = Location(plforth)
    plback = Plane(locforth)
    
    locraws = list()
    for loc in (originalloc, locback):
        loc = loc.toTuple()
        loc = tuple(itertools.chain(*loc))
        locraws.append(loc)
        
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
    
    assert locraws[0] == pytest.approx(locraws[1])
    assert plraws[0] == pytest.approx(plraws[1])
