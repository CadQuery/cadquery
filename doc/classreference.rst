.. _classreference:

*************************
CadQuery Class Reference
*************************

This page documents all of the methods and functions of the CadQuery classes, organized alphabatically.

.. seealso::

    For a listing organized by functional area, see the :ref:`apireference`

.. automodule:: cadquery

Core Classes
---------------------

.. autosummary::
    CQ
    Plane
    Workplane

Primitives
-----------------

.. autosummary::

    Plane
    Vector
    Solid
    Shell
    Wire
    Edge
    Vertex
	


Selectors
---------------------

.. autosummary::
	NearestToPointSelector
	ParallelDirSelector
	DirectionSelector
	PerpendicularDirSelector
	TypeSelector
	DirectionMinMaxSelector
	StringSyntaxSelector

Geometry Classes
------------------

.. autoclass:: Vector
    :members:

.. autoclass:: Plane
    :members:

Shape Base Class
-------------------

All objects inherit from Shape, which as basic manipulation methods:

.. autoclass:: Shape
    :members:

Primitive Classes
--------------------

.. autoclass:: Solid
    :members:


.. autoclass:: Shell
    :members:


.. autoclass:: Wire
   :members:


.. autoclass:: Edge
    :members:


.. autoclass:: Vertex
    :members:	
	
	
Core Classes
------------------------

.. autoclass:: CQ
     :members:

.. autoclass:: Plane
     :members:

.. autoclass:: Workplane
   :members:
   :inherited-members:

   
Selector Classes
------------------------
   
.. autoclass:: Selector
   :members:

.. autoclass:: NearestToPointSelector
   :members:

.. autoclass:: ParallelDirSelector
   :members:

.. autoclass:: DirectionSelector
   :members:

.. autoclass:: PerpendicularDirSelector
   :members:

.. autoclass:: TypeSelector
   :members:

.. autoclass:: DirectionMinMaxSelector
   :members:

.. autoclass:: StringSyntaxSelector
   :members: