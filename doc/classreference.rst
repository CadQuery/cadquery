.. _classreference:

*************************
CadQuery Class Summary
*************************

This page documents all of the methods and functions of the CadQuery classes, organized alphabatically.

.. seealso::

    For a listing organized by functional area, see the :ref:`apireference`

.. module:: cadquery

Core Classes
---------------------

.. currentmodule:: cadquery.CQ
.. autosummary::

    CQ
    Workplane

Topological Classes
----------------------

.. currentmodule:: cadquery.freecad_impl.shapes
.. autosummary::

    Shape
    Vertex
    Edge
    Wire
    Face
    Shell
    Solid
    Compound

Geometry Classes
------------------

.. currentmodule:: cadquery.freecad_impl.geom
.. autosummary::

    Vector
    Matrix
    Plane

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
    DirectionMinMaxSelector
    BinarySelector
    AndSelector
    SumSelector
    SubtractSelector
    InverseSelector
    StringSyntaxSelector

.. currentmodule:: cadquery

Class Details
---------------

.. autoclass:: cadquery.CQ.CQ
   :members:

.. autoclass:: cadquery.CQ.Workplane
   :members:

.. automodule:: cadquery.selectors
   :members:

.. automodule:: cadquery.freecad_impl.geom
   :members:

.. automodule:: cadquery.freecad_impl.shapes
   :members:
