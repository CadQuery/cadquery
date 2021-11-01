.. _roadmap:


RoadMap:  Planned Features
==============================

**CadQuery is not even close to finished!!!**

Many features are planned for later versions.  This page tracks them.  If you find that you need features
not listed here, let us know!


Workplanes
--------------------

rotated workplanes
    support creation of workplanes at an angle to another plane or face

workplane local rotations
    rotate the coordinate system of a workplane by an angle.

make a workplane from a wire
    useful to select outer wire and then operate from there, to allow offsets
    
Assemblies
----------

implement more constraints
    in plane, on axis, parallel to vector


2D operations
-------------------

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

2D fillets
    for a rectangle, or for consecutive selected lines

2D chamfers
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

3D operations
---------------------

rotation/transform that return a copy
    The current rotateAboutCenter and translate method modify the object, rather than returning a copy

primitive creation
    Need primitive creation for:
        * cone
        * torus
        * wedge
