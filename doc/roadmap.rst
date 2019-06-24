.. _roadmap:


RoadMap:  Planned Features
==============================

**CadQuery is not even close to finished!!!**

Many features are planned for later versions.  This page tracks them.  If you find that you need features
not listed here, let us know!

Core
--------------------

end(n)
    allows moving backwards a fixed number of parents in the chain, eg end(3) is same as end().end().end()

Improved iteration tools for plugin developers
    make it easier to iterate over points and wires for plugins

More parameter types ( String? )

face.outerWire
    allow selecting the outerWire of a face, so that it can be used for reference geometry or offsets

Selectors
--------------------

tagged entities
    support tagging entities when they are created, so they can be selected later on using that tag.
    ideally, tags are propagated to features that are created from these features ( ie, an edge tagged with 'foo'
    that is later extruded into a face means that face would be tagged with 'foo' as well )


Workplanes
--------------------

rotated workplanes
    support creation of workplanes at an angle to another plane or face

workplane local rotations
    rotate the coordinate system of a workplane by an angle.

make a workplane from a wire
    useful to select outer wire and then operate from there, to allow offsets

2-d operations
-------------------

offsets
    offset profiles, including circles, rects, and other profiles.

ellipses
    create ellipses and portions of ellipses

regular polygons
    several construction methods:
        * number of sides and side length
        * number of sides inscribed in circle
        * number of sides circumscribed by circle

arc construction using relative measures
    instead of forcing use of absolute workplane coordinates

tangent arcs
    after a line

centerpoint arcs
    including portions of arcs as well as with end points specified

trimming
    ability to use construction geometry to trim other entities

construction lines
    especially centerlines

2-d fillets
    for a rectangle, or for consecutive selected lines

2-d chamfers
    based on rectangles, polygons, polylines, or adjacent selected lines

mirror around centerline
    using centerline construction geometry

midpoint selection
    select midpoints of lines, arcs

face center
    explicit selection of face center

manipulate spline control points
    so that the shape of a spline can be more accurately controlled

feature snap
    project geometry in the rest of the part into the work plane, so that
    they can be selected and used as references for other features.

polyline edges
    allow polyline to be combined with other edges/curves

3-d operations
---------------------

rotation/transform that return a copy
    The current rotateAboutCenter and translate method modify the object, rather than returning a copy

primitive creation
    Need primitive creation for:
        * cone
        * cylinder
        * torus
        * wedge

extrude/cut up to surface
    allow a cut or extrude to terminate at another surface, rather than either through all or a fixed distance


Algorithms
---------------------

Wire Discretization
    Sample wires at point interval to improve closet wire computations


