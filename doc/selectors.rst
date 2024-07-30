.. _selector_reference:

Selectors Reference
===================


CadQuery selector strings allow filtering various types of object lists. Most commonly, Edges, Faces, and Vertices are
used, but all objects types can be filtered.

Object lists are created by using the following methods, which each collect a type of shape:

    * :py:meth:`cadquery.Workplane.vertices`
    * :py:meth:`cadquery.Workplane.edges`
    * :py:meth:`cadquery.Workplane.faces`
    * :py:meth:`cadquery.Workplane.shells`
    * :py:meth:`cadquery.Workplane.solids`

Each of these methods accepts either a Selector object or a string. String selectors are simply
shortcuts for using the full object equivalents. If you pass one of the string patterns in,
CadQuery will automatically use the associated selector object.


.. note::

    String selectors are simply shortcuts to concrete selector classes, which you can use or
    extend. For a full description of how each selector class works, see :ref:`classreference`.

    If you find that the built-in selectors are not sufficient, you can easily plug in your own.
    See :ref:`extending` to see how.


Combining Selectors
--------------------------

Selectors can be combined logically, currently defined operators include **and**, **or**, **not** and **exc[ept]** (set difference).  For example:

.. cadquery::

    result = cq.Workplane("XY").box(2, 2, 2).edges("|Z and >Y").chamfer(0.2)

Much more complex expressions are possible as well:

.. cadquery::

    result = (
        cq.Workplane("XY")
        .box(2, 2, 2)
        .faces(">Z")
        .shell(-0.2)
        .faces(">Z")
        .edges("not(<X or >X or <Y or >Y)")
        .chamfer(0.1)
    )

.. _filteringfaces:

Filtering Faces
----------------

All types of string selectors work on faces.  In most cases, the selector refers to the direction
of the **normal vector** of the face.

.. warning::

    If a face is not planar, selectors are evaluated at the center of mass of the face. This can lead
    to results that are quite unexpected.

The axis used in the listing below are for illustration: any axis would work similarly in each case.

=========   =========================================  =======================================================
Selector    Selects                                    Selector Class
=========   =========================================  =======================================================
+Z          Faces with normal in +z direction          :py:class:`cadquery.DirectionSelector`
\|Z         Faces with normal parallel to z dir        :py:class:`cadquery.ParallelDirSelector`
-X          Faces with normal in neg x direction       :py:class:`cadquery.DirectionSelector`
#Z          Faces with normal orthogonal to z dir      :py:class:`cadquery.PerpendicularDirSelector`
%Plane      Faces of type plane                        :py:class:`cadquery.TypeSelector`
>Y          Face farthest in the positive y dir        :py:class:`cadquery.DirectionMinMaxSelector`
<Y          Face farthest in the negative y dir        :py:class:`cadquery.DirectionMinMaxSelector`
>Y[-2]      2nd farthest Face **normal** to the y dir  :py:class:`cadquery.DirectionNthSelector`
<Y[0]       1st closest Face **normal** to the y dir   :py:class:`cadquery.DirectionNthSelector`
>>Y[-2]     2nd farthest Face in the y dir             :py:class:`cadquery.CenterNthSelector`
<<Y[0]      1st closest Face in the y dir              :py:class:`cadquery.CenterNthSelector`
=========   =========================================  =======================================================


.. _filteringedges:

Filtering Edges
----------------

The selector usually refers to the **direction** of the edge.

.. warning::

    Non-linear edges are not selected for any string selectors except type (%) and center (>>).
    Non-linear edges are never returned when these filters are applied.

The axis used in the listing below are for illustration: any axis would work similarly in each case.


========  ====================================================  =============================================
Selector  Selects                                               Selector Class
========  ====================================================  =============================================
+Z        Edges aligned in the Z direction                      :py:class:`cadquery.DirectionSelector`
\|Z       Edges parallel to z direction                         :py:class:`cadquery.ParallelDirSelector`
-X        Edges aligned in neg x direction                      :py:class:`cadquery.DirectionSelector`
#Z        Edges perpendicular to z direction                    :py:class:`cadquery.PerpendicularDirSelector`
%Line     Edges of type line                                    :py:class:`cadquery.TypeSelector`
>Y        Edges farthest in the positive y dir                  :py:class:`cadquery.DirectionMinMaxSelector`
<Y        Edges farthest in the negative y dir                  :py:class:`cadquery.DirectionMinMaxSelector`
>Y[1]     2nd closest **parallel** edge in the positive y dir   :py:class:`cadquery.DirectionNthSelector`
<Y[-2]    2nd farthest **parallel** edge in the negative y dir  :py:class:`cadquery.DirectionNthSelector`
>>Y[-2]   2nd farthest edge in the y dir                        :py:class:`cadquery.CenterNthSelector`
<<Y[0]    1st closest edge in the y dir                         :py:class:`cadquery.CenterNthSelector`
========  ====================================================  =============================================


.. _filteringvertices:

Filtering Vertices
-------------------

Only a few of the filter types apply to vertices. The location of the vertex is the subject of the filter.

=========   =======================================    =======================================================
Selector    Selects                                    Selector Class
=========   =======================================    =======================================================
>Y          Vertices farthest in the positive y dir    :py:class:`cadquery.DirectionMinMaxSelector`
<Y          Vertices farthest in the negative y dir    :py:class:`cadquery.DirectionMinMaxSelector`
>>Y[-2]     2nd farthest vertex in the y dir           :py:class:`cadquery.CenterNthSelector`
<<Y[0]      1st closest vertex in the y dir            :py:class:`cadquery.CenterNthSelector`
=========   =======================================    =======================================================

User-defined Directions
-----------------------

It is possible to use user defined vectors as a basis for the selectors. For example:

.. cadquery::

    result = cq.Workplane("XY").box(10, 10, 10)

    # chamfer only one edge
    result = result.edges(">(-1, 1, 0)").chamfer(1)


Topological Selectors
---------------------

Is is also possible to use topological relations to select objects. Currently
the following methods are supported:

    * :py:meth:`cadquery.Workplane.ancestors`
    * :py:meth:`cadquery.Workplane.siblings`

Ancestors allows to select all objects containing currently selected object.

.. cadquery::

    result = cq.Workplane("XY").box(10, 10, 10).faces(">Z").edges("<Y")

    result = result.ancestors("Face")

Siblings allows to select all objects of the same type as selection that are connected
via the specfied kind of elements.

.. cadquery::

    result = cq.Workplane("XY").box(10, 10, 10).faces(">Z")

    result = result.siblings("Edge")


Using selectors with Shape and Sketch objects
---------------------------------------------

It is possible to use selectors with :py:class:`cadquery.Shape` and :py:class:`cadquery.Sketch`
objects. This includes chaining and combining.

.. cadquery::

    box = cq.Solid.makeBox(1,2,3)

    # select top and bottom wires
    result = box.faces(">Z or <Z").wires()




Additional special methods
--------------------------

:py:class:`cadquery.Workplane` and :py:class:`cadquery.Sketch` provide the following special methods that can be used
for quick prototyping of selectors when implementing a complete selector via subclassing of
:py:class:`cadquery.Selector` is not desirable.

    * :py:meth:`cadquery.Workplane.filter`
    * :py:meth:`cadquery.Workplane.sort`
    * :py:meth:`cadquery.Workplane.__getitem__`
    * :py:meth:`cadquery.Sketch.filter`
    * :py:meth:`cadquery.Sketch.sort`
    * :py:meth:`cadquery.Sketch.__getitem__`

For example, one could use those methods for selecting objects within a certain range of volumes.

.. cadquery::

    from cadquery.occ_impl.shapes import box

    result = (
        cq.Workplane()
        .add([box(1,1,i+1).moved(x=2*i) for i in range(5)])
    )

    # select boxes with volume <= 3
    result = result.filter(lambda s: s.Volume() <= 3)


The same can be achieved using sorting.

.. cadquery::

    from cadquery.occ_impl.shapes import box

    result = (
        cq.Workplane()
        .add([box(1,1,i+1).moved(x=2*i) for i in range(5)])
    )

    # select boxes with volume <= 3
    result = result.sort(lambda s: s.Volume())[:3]
