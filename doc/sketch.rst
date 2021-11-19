.. _sketchtutorial:

******
Sketch
******

Sketch tutorial
---------------

The purpose of this section is to demonstrate how to construct sketches using different
approaches.

Face-based API
==============

The main approach for constructing sketches is based on constructing faces and 
combining them using boolean operations.

.. cadquery::
    :height: 600px

    import cadquery as cq

    result = (
       cq.Sketch()
       .trapezoid(4,3,90)
       .vertices()
       .circle(.5, mode='s')
       .reset()
       .vertices()
       .fillet(.25)
       .reset()
       .rarray(.6,1,5,1).slot(1.5,0.4, mode='s', angle=90)
    )

Note that selectors are implemented, but selection has to be explicitly reset. Sketch
class does not implement history and all modifications happen in-place.

Modes
^^^^^

Every operation from the face API accepts a mode parameter to define how to combine the created object with existing ones. It can be fused (``mode='a'``), cut (``mode='s'``), intersected (``mode='i'``) or just stored for construction (``mode='c'``). In the last case, it is mandatory to specify a ``tag`` in order to be able to refer to the object later on. By default faces are fused together. Note the usage of the subtractive and additive modes in the example above. The additional two are demonstrated below.

.. cadquery::
    :height: 600px

    result = (
       cq.Sketch()
       .rect(1, 2, mode='c', tag='base')
       .vertices(tag='base')
       .circle(.7)
       .reset()
       .edges('|Y', tag='base')
       .ellipse(1.2, 1, mode='i')
       .reset()
       .rect(2, 2, mode='i')
       .clean()
    )


Edge-based API
==============

If needed, one can construct sketches by placing individual edges.

.. cadquery::
    :height: 600px

    import cadquery as cq

    result = (
        cq.Sketch()
        .segment((0.,0),(0.,2.))
        .segment((2.,0))
        .close()
        .arc((.6,.6),0.4,0.,360.)
        .assemble(tag='face')
        .edges('%LINE',tag='face')
        .vertices()
        .chamfer(0.2)
    )

Once the construction is finished it has to be converted to the face-based representation
using :meth:`~cadquery.Sketch.assemble`. Afterwards, face based operations can be applied.


Convex hull
===========

For certain special use-cases convex hull can be constructed from straight segments
and circles.

.. cadquery::
    :height: 600px

    result = (
        cq.Sketch()
        .arc((0,0),1.,0.,360.)
        .arc((1,1.5),0.5,0.,360.)
        .segment((0.,2),(-1,3.))
        .hull()
       )

Constraint-based sketches
=========================

Finally, if desired, geometric constraints can be used to construct sketches. So
far only line segments and arcs can be used in such a use case.

.. cadquery::
    :height: 600px

    import cadquery as cq

    result = (
        cq.Sketch()
        .segment((0,0), (0,3.),"s1")
        .arc((0.,3.), (1.5,1.5), (0.,0.),"a1")
        .constrain("s1","Fixed",None)
        .constrain("s1", "a1","Coincident",None)
        .constrain("a1", "s1","Coincident",None)
        .constrain("s1",'a1', "Angle", 45)
        .solve()
        .assemble()
    )

Following constraints are implemented. Arguments are passed in as one tuple in :meth:`~cadquery.Sketch.constrain`. In this table, `0..1` refers to a float between 0 and 1 where 0 would create a constraint relative to the start of the element, and 1 the end.

.. list-table::
    :widths: 15 10 15 30 30
    :header-rows: 1

    * - Name
      - Arity
      - Entities
      - Arguments
      - Description
    * - FixedPoint
      - 1
      - All
      - `None` for arc center or `0..1` for point on segment/arc
      - Specified point is fixed
    * - Coincident
      - 2
      - All
      - None
      - Specified points coincide
    * - Angle
      - 2
      - All
      - `angle`
      - Angle between the tangents of the two entities is fixed
    * - Length
      - 1
      - All
      - `length`
      - Specified entity has fixed length
    * - Distance
      - 2
      - All
      - `None or 0..1, None or 0..1, distance`
      - Distance between two points is fixed
    * - Radius
      - 1
      - Arc
      - `radius`
      - Specified entity has a fixed radius
    * - Orientation
      - 1
      - Segment
      - `x,y`
      - Specified entity is parallel to `(x,y)`
    * - ArcAngle
      - 1
      - Arc
      - `angle`
      - Specified entity is fixed angular span


Workplane integration
---------------------

Once created, a sketch can be used to construct various features on a workplane.
Supported operations include :meth:`~cadquery.Workplane.extrude`,
:meth:`~cadquery.Workplane.twistExtrude`, :meth:`~cadquery.Workplane.revolve`,
:meth:`~cadquery.Workplane.sweep`, :meth:`~cadquery.Workplane.cutBlind`, :meth:`~cadquery.Workplane.cutThruAll` and :meth:`~cadquery.Workplane.loft`.

Sketches can be created as separate entities and reused, but also created ad-hoc
in one fluent chain of calls as shown below.


Note that the sketch is placed on all locations that are on the top of the stack.

Constructing sketches in-place can be accomplished as follows.

.. cadquery::
    :height: 600px

    import cadquery as cq

    result = (
        cq.Workplane()
        .box(5,5,1)
        .faces('>Z')
        .sketch()
        .regularPolygon(2,3,tag='outer')
        .regularPolygon(1.5,3,mode='s')
        .vertices(tag='outer')
        .fillet(.2)
        .finalize()
        .extrude(.5)
    )

Sketch API is available after the :meth:`~cadquery.Workplane.sketch` call and original `workplane`.

When multiple elements are selected before constructing the sketch, multiple sketches will be created.

.. cadquery::
    :height: 600px

    import cadquery as cq

    result = (
        cq.Workplane()
        .box(5,5,1)
        .faces('>Z')
        .workplane()
        .rarray(2,2,2,2)
        .rect(1.5,1.5)
        .extrude(.5)
        .faces('>Z')
        .sketch()
        .circle(0.4)
        .wires()
        .distribute(6)
        .circle(0.1,mode='a')
        .clean()
        .finalize()
        .cutBlind(-0.5,taper=10)
    )

Sometimes it is desired to reuse existing sketches and place them as-is on a workplane.


.. cadquery::
    :height: 600px

    import cadquery as cq

    s = (
         cq.Sketch()
         .trapezoid(3,1,110)
         .vertices()
         .fillet(0.2)
         )

    result = (
        cq.Workplane()
        .box(5,5,5)
        .faces('>X')
        .workplane()
        .transformed((0,0,-90))
        .placeSketch(s)
        .cutThruAll()
        )

Reusing of existing sketches is needed when using :meth:`~cadquery.Workplane.loft`.

.. cadquery::
    :height: 600px

    from cadquery import Workplane, Sketch, Vector, Location

    s1 = (
         Sketch()
         .trapezoid(3,1,110)
         .vertices()
         .fillet(0.2)
         )

    s2 = (
         Sketch()
         .rect(2,1)
         .vertices()
         .fillet(0.2)
         )

    result = (
        Workplane()
        .placeSketch(s1, s2.moved(Location(Vector(0, 0, 3))))
        .loft()
        )

When lofting only outer wires are taken into account and inner wires are silently ignored.
