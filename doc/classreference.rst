.. _classreference:

*************************
CadQuery Class Summary
*************************

This page documents all of the methods and functions of the CadQuery classes, organized alphabetically.

.. seealso::

    For a listing organized by functional area, see the :ref:`apireference`

.. currentmodule:: cadquery

Core Classes
---------------------

.. autosummary::

    Sketch
    Workplane
    Assembly
    Constraint

Topological Classes
----------------------

.. autosummary::
    
    Shape
    Vertex
    Edge
    cadquery.occ_impl.shapes.Mixin1D
    Wire
    Face
    Shell
    cadquery.occ_impl.shapes.Mixin3D
    Solid
    Compound

Geometry Classes
------------------

.. autosummary::

    Vector
    Matrix
    Plane
    Location

Selector Classes
---------------------

.. currentmodule:: cadquery.selectors
.. autosummary::

    Selector
    NearestToPointSelector
    BoxSelector
    BaseDirSelector
    ParallelDirSelector
    DirectionSelector
    PerpendicularDirSelector
    TypeSelector
    RadiusNthSelector
    CenterNthSelector
    DirectionMinMaxSelector
    DirectionNthSelector
    LengthNthSelector
    AreaNthSelector
    BinarySelector
    AndSelector
    SumSelector
    SubtractSelector
    InverseSelector
    StringSyntaxSelector


Class Details
---------------

.. automodule:: cadquery
   :show-inheritance: 
   :members:
   :special-members:

.. autoclass:: cadquery.occ_impl.shapes.Mixin1D
   :show-inheritance: 
   :members:

.. autoclass:: cadquery.occ_impl.shapes.Mixin3D
   :show-inheritance: 
   :members:

.. automodule:: cadquery.selectors
   :show-inheritance: 
   :members:
