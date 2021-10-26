.. _sketchtutorial:

**********
Sketch
**********

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

    from cadquery import *

    result = (
       cq.Sketch()
       .trapezoid(4,3,90)
        .vertices()
        .circle(.5,mode='s')
        .reset()
        .vertices()
        .fillet(.25)
        .reset()
        .reset()
        .rarray(.6,1,5,1).slot(1.5,0.4,mode='s',angle=90)
    )

Note that selectors are implemented, but selection has to be explicitly reset. Sketch
class does not implement history and all modifications happen in-place.


Edge-based API
==============

If needed one can construct sketches by placing individual edges.

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
using `assemble`. Afterwards, face based operations can be applied.

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
========================

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

    result.solve()
    result.assemble()

Following constraints are implemented.

* `Fixed`
* `Coincident`
* `Angle`
* `Length`
* `Distance`
* `Radius`
* `Orientation`
* `ArcAngle`

Workplane integration
---------------------

Once created, a sketch can be used to construct various features on a workplane.
Supported operations include `extrude`, `twistExtrude`, `revolve`, `sweep`, `cutBlind`
and `cutThruAll`.

Sketches can be created as separate entities and reused, but also crated ad-hoc
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
        .extrude(2)
    )

Sketch API is available after the `sketch` call and original `workplane`.

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
        .box(5,5,.5)
        .faces('>X')
        .workplane()
        .transformed((0,0,-90))
        .placeSketch(s)
        .cutThruAll()
        )

    show_object(result)
