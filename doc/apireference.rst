.. _apireference:

***********************
CadQuery API Reference
***********************

The CadQuery API is made up of 4 main objects:

* **Sketch** -- Construct 2D sketches
* **Workplane** -- Wraps a topological entity and provides a 2D modelling context.
* **Selector** -- Filter and select things
* **Assembly** -- Combine objects into assemblies.

This page lists  methods of these objects grouped by **functional area**

.. seealso::
  This page lists api methods grouped by functional area.
  Use :ref:`classreference` to see methods alphabetically by class.


Sketch initialization
---------------------

.. currentmodule:: cadquery

Creating new sketches.

.. autosummary::
    Sketch
    Sketch.importDXF
    Workplane.sketch
    Sketch.finalize
    Sketch.copy
    Sketch.located
    Sketch.moved

Sketch selection
----------------

.. currentmodule:: cadquery

Selecting, tagging and manipulating elements.

.. autosummary::
    Sketch.tag
    Sketch.select
    Sketch.reset
    Sketch.delete
    Sketch.faces
    Sketch.edges
    Sketch.vertices

Sketching with faces
--------------------

.. currentmodule:: cadquery

Sketching using the face-based API.

.. autosummary::
    Sketch.face
    Sketch.rect
    Sketch.circle
    Sketch.ellipse
    Sketch.trapezoid
    Sketch.slot
    Sketch.regularPolygon
    Sketch.polygon
    Sketch.rarray
    Sketch.parray
    Sketch.distribute
    Sketch.each
    Sketch.push
    Sketch.hull
    Sketch.offset
    Sketch.fillet
    Sketch.chamfer
    Sketch.clean

Sketching with edges and constraints
------------------------------------

.. currentmodule:: cadquery

Sketching using the edge-based API.

.. autosummary::
    Sketch.edge
    Sketch.segment
    Sketch.arc
    Sketch.spline
    Sketch.close
    Sketch.assemble
    Sketch.constrain
    Sketch.solve


Initialization
--------------

.. currentmodule:: cadquery

Creating new workplanes and object chains

.. autosummary::
    Workplane


.. _2dOperations:

2D Operations
-------------

Creating 2D constructs that can be used to create 3D features.

All 2D operations require a **Workplane** object to be created.

.. currentmodule:: cadquery

.. autosummary::
    Workplane.center
	Workplane.lineTo
	Workplane.line
	Workplane.vLine
	Workplane.vLineTo
	Workplane.hLine
	Workplane.hLineTo
	Workplane.polarLine
	Workplane.polarLineTo
	Workplane.moveTo
	Workplane.move
	Workplane.spline
	Workplane.parametricCurve
	Workplane.parametricSurface
	Workplane.threePointArc
	Workplane.sagittaArc
	Workplane.radiusArc
    Workplane.tangentArcPoint
	Workplane.mirrorY
	Workplane.mirrorX
	Workplane.wire
	Workplane.rect
	Workplane.circle
	Workplane.ellipse
	Workplane.ellipseArc
	Workplane.polyline
	Workplane.close
	Workplane.rarray
	Workplane.polarArray
	Workplane.slot2D
	Workplane.offset2D

.. _3doperations:

3D Operations
-----------------

Some 3D operations also require an active 2D workplane, but some do not.

3D operations that require a 2D workplane to be active:

.. autosummary::
	Workplane.cboreHole
	Workplane.cskHole
	Workplane.hole
	Workplane.extrude
	Workplane.cut
	Workplane.cutBlind
	Workplane.cutThruAll
	Workplane.box
	Workplane.sphere
	Workplane.wedge
	Workplane.cylinder
	Workplane.union
	Workplane.combine
	Workplane.intersect
	Workplane.loft
	Workplane.sweep
	Workplane.twistExtrude
	Workplane.revolve
	Workplane.text
	

3D operations that do NOT require a 2D workplane to be active:

.. autosummary::
	Workplane.shell
	Workplane.fillet
	Workplane.chamfer
	Workplane.split
	Workplane.rotate
	Workplane.rotateAboutCenter
	Workplane.translate
	Workplane.mirror

File Management and Export
---------------------------------

.. autosummary::
    Workplane.toSvg
    Workplane.exportSvg


.. autosummary::
    importers.importStep
    importers.importDXF
    exporters.export


Iteration Methods
------------------

Methods that allow iteration over the stack or objects

.. autosummary::
    Workplane.each
    Workplane.eachpoint


.. _stackMethods:

Stack and Selector Methods
------------------------------

CadQuery methods that operate on the stack

.. autosummary::
	Workplane.all
	Workplane.size
	Workplane.vals
	Workplane.add
	Workplane.val
	Workplane.first
	Workplane.item
	Workplane.last
	Workplane.end
	Workplane.vertices
	Workplane.faces
	Workplane.edges
	Workplane.wires
	Workplane.solids
	Workplane.shells
	Workplane.compounds

.. _selectors:

Selectors
------------------------

Objects that filter and select CAD objects. Selectors are used to select existing geometry
as a basis for further operations.

.. currentmodule:: cadquery.selectors
.. autosummary::

    NearestToPointSelector
    BoxSelector
    BaseDirSelector
    ParallelDirSelector
    DirectionSelector
    DirectionNthSelector
	LengthNthSelector
	AreaNthSelector
    RadiusNthSelector
    PerpendicularDirSelector
    TypeSelector
    DirectionMinMaxSelector
    CenterNthSelector
    BinarySelector
    AndSelector
    SumSelector
    SubtractSelector
    InverseSelector
    StringSyntaxSelector

.. _assembly:
        
Assemblies
----------

Workplane and Shape objects can be connected together into assemblies

.. currentmodule:: cadquery
.. autosummary::

    Assembly
    Assembly.add
    Assembly.save
    Assembly.constrain
    Assembly.solve
    Constraint
    Color
