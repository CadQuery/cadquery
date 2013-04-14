.. _apireference:

***********************
CadQuery API Reference
***********************

.. automodule:: cadfile.cadutils.cadquery

.. seealso::
  This page lists api methods grouped by functional area.
  Use :ref:`classreference` to see methods alphabetically by class.
  Don't see a method you want? see :ref:`extending`

Primary Objects
----------------

The CadQuery API is made up of 3 main objects:

* **CQ** -  Basic Selection, and 3d operations
* **Workplane** -- Draw in 2-d to make 3d features
* **Selector** -- Filter and select things

The sections below list methods of these objects grouped by **functional area**

Initialization
----------------

Creating new workplanes and object chains

.. autosummary::
    CQ
    Workplane
    CQ.workplane


.. _2dOperations:

2-d Operations
-----------------

Creating 2-d constructs that can be used to create 3 d features

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

Methods that create 3d features

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
	CQ.shell
	CQ.fillet
	CQ.split
	CQ.rotateAboutCenter
	CQ.translate


Iteration Methods
------------------

Methods that allow iteration over the stack or objects

.. autosummary::
    Workplane.each
    Workplane.eachpoint


.. _stackMethods:

Stack Methods
-----------------

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

Objects that filter and select CAD objects

.. autosummary::
	NearestToPointSelector
	ParallelDirSelector
	DirectionSelector
	PerpendicularDirSelector
	TypeSelector
	DirectionMinMaxSelector
	StringSyntaxSelector
