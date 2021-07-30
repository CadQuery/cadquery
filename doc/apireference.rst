.. _apireference:

***********************
CadQuery API Reference
***********************

The CadQuery API is made up of 2 main objects:

* **Workplane** -- Wraps a topological entity and provides a 2-D modelling context.
* **Selector** -- Filter and select things

This page lists  methods of these objects grouped by **functional area**

.. seealso::
  This page lists api methods grouped by functional area.
  Use :ref:`classreference` to see methods alphabetically by class.


Initialization
----------------

.. currentmodule:: cadquery

Creating new workplanes and object chains

.. autosummary::
    Workplane


.. _2dOperations:

2-d Operations
-----------------

Creating 2-d constructs that can be used to create 3 d features.

All 2-d operations require a **Workplane** object to be created.

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

3-d Operations
-----------------

Some 3-d operations also require an active 2-d workplane, but some do not.

3-d operations that require a 2-d workplane to be active:

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
	Workplane.union
	Workplane.combine
	Workplane.intersect
	Workplane.loft
	Workplane.sweep
	Workplane.twistExtrude
	Workplane.revolve
	Workplane.text
	

3-d operations that do NOT require a 2-d workplane to be active:

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
