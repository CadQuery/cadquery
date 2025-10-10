from cadquery.occ_impl.shapes import Location, Plane, Vector
import pytest
import itertools


# Conversion can betriggered from explicit constructor, or from property
@pytest.mark.parametrize(
    ["useproperty",],
    [
        (False,),
        (True,),
    ],
)
# Create different test cases from different initial plane.
# Testing the different components is mainly useful for debugging if things
# do not work.
# Arguments to Plane.__init__ along with expected rotations in a converted
# Location object are given here.
@pytest.mark.parametrize(
    ["plargs", "expectedrot"],
    [
        # Default plane
        (((3, 5, 6),), (0, 0, 0),),
        # Just xDir specified, but never parallel to the default normal
        (((3, 5, 6), (1, 0, 0),), (0, 0, 0),),
        (((3, 5, 6), (0, 1, 0),), (0, 0, 90),),
        # xDir and normal specified.
        # Omit normals, that were included as default, and once which
        # have no component orthogonal to xDir
        (((3, 5, 6), (1, 0, 0), (0, 1, 0),), (-90, 0, 0),),
        (((3, 5, 6), (0, 1, 0), (1, 0, 0),), (90, 0, 90),),
        # JUst xDir, but with multiple vector components
        (((3, 5, 6), (1, 1, 0),), (0, 0, 45),),
        (((3, 5, 6), (1, 0, 1),), (0, -45, 0),),
        (((3, 5, 6), (0, 1, 1),), (0, -45, 90),),
        # Multiple components in xdir and normal
        # Starting from here, there are no known golden Location rotations,
        # as normal is made orthogonal to xDir and as rotational angles
        # are non-trivial.
        (((3, 5, 6), (1, 1, 0), (1, 0, 1),), None,),
        (((3, 5, 6), (1, 1, 0), (0, 1, 1),), None,),
        (((3, 5, 6), (1, 0, 1), (1, 1, 0),), None,),
        (((3, 5, 6), (1, 0, 1), (0, 1, 1),), None,),
        (((3, 5, 6), (0, 1, 1), (1, 1, 0),), None,),
        (((3, 5, 6), (0, 1, 1), (1, 0, 1),), None,),
        # Same, but introduce negative directions
        (((3, 5, 6), (-1, 1, 0), (-1, 0, -1),), None,),
        (((3, 5, 6), (1, -1, 0), (0, -1, -1),), None,),
        (((3, 5, 6), (1, 0, -1), (1, -1, 0),), None,),
        (((3, 5, 6), (1, 0, -1), (0, -1, 1),), None,),
        (((3, 5, 6), (0, -1, -1), (-1, 1, 0),), None,),
        (((3, 5, 6), (0, -1, -1), (1, 0, -1),), None,),
        # Vectors with random non-trivial directions
        (((3, 5, 6), (2, 4, 7), (9, 8, 1),), None,),
    ]
)
def test_Plane_from_Location(plargs, expectedrot, useproperty):
    # Test conversion between Plane and Location by converting multiple
    # times between them, such that two Plane and two Location can be
    # compared respectively.

    # If there are three things in plargs, ensure that xDir and normal are
    # orthogonal. That should be ensured by an exception in Plane.__init__.
    # This here makes the normal orthogonal to xDir by subtracting its
    # projection on xDir.
    # If no normal is given, the default normal is assumed.
    # Packed and unpacked arguments to Plane are kept the same.
    if len(plargs) == 1:
        (origin,) = plargs
    elif len(plargs) == 2:
        plargs = (*plargs, (0, 0, 1),)
    # If len(plargs) was 2, it is now 3, and the normal still needs to be
    # made orthogonal to xDir.
    if len(plargs) == 3:
        origin, xDir, normal = plargs
        xDir = Vector(xDir)
        normal = Vector(normal)
        normal -= normal.projectToLine(xDir)
        xDir = xDir.toTuple()
        normal = normal.toTuple()
        plargs = (origin, xDir, normal,)

    # Start from random Plane with classical __init__
    # Use keyword arguments on purpose, as they still need to work after
    # having @multidispatch added to that __init__.
    # Test that on cases, where plargs has three elements and was unpacked.
    if len(plargs) == 3:
        originalpl = Plane(origin=origin, xDir=xDir, normal=normal)
    else:
        originalpl = Plane(*plargs)

    # Convert back and forth, such that comparable pairs are created.
    # Depending on test fixture, call constructor directly or use properties
    if useproperty:
        locforth = originalpl.location
        plback = locforth.plane
        locback = plback.location
    else:
        locforth = Location(originalpl)
        plback = Plane.fromLocation(locforth)
        locback = Location(plback)

    # Create raw locations, which are flat tuples of raw numbers, suitable for
    # assertion with pytest.approx
    locraws = list()
    for loc in (locforth, locback):
        loc = loc.toTuple()
        loc = tuple(itertools.chain(*loc))
        locraws.append(loc)

    # Same for planes
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

    # Assert the properties of the location object.
    # Asserting on one Location is enough, as equality to the other one is
    # asserted below.
    # First, its origin shall be the same
    assert locraws[0][0:3] == pytest.approx(origin)
    # Then rotations are asserted from manual values
    if expectedrot is not None:
        assert locraws[0][3:6] == pytest.approx(expectedrot)

    # Assert that pairs of PLane or Location are equal after conversion
    assert locraws[0] == pytest.approx(locraws[1])
    assert plraws[0] == pytest.approx(plraws[1])
