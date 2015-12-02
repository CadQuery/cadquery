.. _apireference:

***********************
CadQuery API Reference
***********************

The CadQuery API is made up of 3 main objects:

* **CQ** -  An object that wraps a topological entity.
* **Workplane** -- A subclass of CQ, that applies in a 2-D modelling context.
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
    CQ
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
	Workplane.moveTo
	Workplane.move
	Workplane.spline
	Workplane.threePointArc
	Workplane.rotateAndCopy
	Workplane.mirrorY
	Workplane.mirrorX
	Workplane.wire
	Workplane.rect
	Workplane.circle
	Workplane.polyline
	Workplane.close
	Workplane.rarray

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
	Workplane.union
	Workplane.combine

3-d operations that do NOT require a 2-d workplane to be active:

.. autosummary::
	CQ.shell
	CQ.fillet
	CQ.split
	CQ.rotate
	CQ.rotateAboutCenter
	CQ.translate

File Management and Export
---------------------------------

.. autosummary::
    CQ.toSvg
    CQ.exportSvg


.. autosummary::
    importers.importStep
    exporters.exportShape


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
	CQ.all
	CQ.size
	CQ.vals
	CQ.add
	CQ.val
	CQ.first
	CQ.item
	CQ.last
	CQ.end
	CQ.vertices
	CQ.faces
	CQ.edges
	CQ.wires
	CQ.solids
	CQ.shells
	CQ.compounds

.. _selectors:

Selectors
------------------------

Objects that filter and select CAD objects. Selectors are used to select existing geometry
as a basis for futher operations.

.. currentmodule:: cadquery

.. autosummary::

        NearestToPointSelector
        BoxSelector
        BaseDirSelector
        ParallelDirSelector
        DirectionSelector
        PerpendicularDirSelector
        TypeSelector
        DirectionMinMaxSelector
        BinarySelector
        AndSelector
        SumSelector
        SubtractSelector
        InverseSelector
        StringSyntaxSelector
