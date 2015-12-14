.. _selector_reference:

String Selectors Reference
=============================


CadQuery selector strings allow filtering various types of object lists. Most commonly, Edges, Faces, and Vertices are
used, but all objects types can be filtered.

String selectors are simply shortcuts for using the full object equivalents. If you pass one of the
string patterns in, CadQuery will automatically use the associated selector object.

    * :py:meth:`cadquery.CQ.faces`
    * :py:meth:`cadquery.CQ.edges`
    * :py:meth:`cadquery.CQ.vertices`
    * :py:meth:`cadquery.CQ.solids`
    * :py:meth:`cadquery.CQ.shells`

.. note::

    String selectors are shortcuts to concrete selector classes, which you can use or extend. See
    :ref:`classreference` for more details

    If you find that the built-in selectors are not sufficient, you can easily plug in your own.
    See :ref:`extending` to see how.


Combining Selectors
==========================

Selectors can be combined arithmetically and logically, so that it is possible to do intersection, union, and other
combinations.  For example::

    box = cadquery.Workplane("XY").box(10,10,10)

    s = selectors.StringSyntaxSelector

    ### select all edges on right and left faces
    #box = box.edges((s("|Z") + s("|Y"))).fillet(1)

    ### select all edges on top and bottom
    #box = box.edges(-s("|Z")).fillet(1)
    #box = box.edges(s('|X')+s('Y')).fillet(1)
    box = box.faces(s('>Z')+s('<Z')).fillet(1)


or for another example::

    # select diagonal edges
    box = box.faces(s('>Z')+s('<Z')).edges(-s('|X')-s('Y')).fillet(1)

.. _filteringfaces:

Filtering Faces
----------------

All types of filters work on faces.  In most cases, the selector refers to the direction of the **normal vector**
of the face.

.. warning::

    If a face is not planar, selectors are evaluated at the center of mass of the face. This can lead
    to results that are quite unexpected.

The axis used in the listing below are for illustration: any axis would work similarly in each case.

=========   ======================================  =======================================================  ==========================
Selector    Selects                                 Selector Class                                           # objects returned
=========   ======================================  =======================================================  ==========================
+Z          Faces with normal in +z direction       :py:class:`cadquery.DirectionSelector`                   0 or 1
\|Z         Faces parallel to xy plane              :py:class:`cadquery.ParallelDirSelector`                 0..many
-X          Faces with  normal in neg x direction   :py:class:`cadquery.DirectionSelector`                   0..many
#Z          Faces perpendicular to z direction      :py:class:`cadquery.PerpendicularDirSelector`            0..many
%Plane      Faces of type plane                     :py:class:`cadquery.TypeSelector`                        0..many
>Y          Face farthest in the positive y dir     :py:class:`cadquery.DirectionMinMaxSelector`             0 or 1
<Y          Face farthest in the negative y dir     :py:class:`cadquery.DirectionMinMaxSelector`             0 or 1
=========   ======================================  =======================================================  ==========================


.. _filteringedges:

Filtering Edges
----------------

Some filter types are not supported for edges.  The selector usually refers to the **direction** of the edge.

.. warning::

    Non-linear edges are not selected for any selectors except type (%). Non-linear edges are never returned
    when these filters are applied.

The axis used in the listing below are for illustration: any axis would work similarly in each case.


=========   ====================================    =======================================================     ==========================
Selector    Selects                                 Selector Class                                              # objects returned
=========   ====================================    =======================================================     ==========================
+Z          Edges aligned in the Z direction        :py:class:`cadquery.DirectionSelector`                      0..many
\|Z         Edges parallel to z direction           :py:class:`cadquery.ParallelDirSelector`                    0..many
-X          Edges aligned in neg x direction        :py:class:`cadquery.DirectionSelector`                      0..many
#Z          Edges perpendicular to z direction      :py:class:`cadquery.PerpendicularDirSelector`               0..many
%Line       Edges of type line                      :py:class:`cadquery.TypeSelector`                           0..many
>Y          Edges farthest in the positive y dir    :py:class:`cadquery.DirectionMinMaxSelector`                0 or 1
<Y          Edges farthest in the negative y dir    :py:class:`cadquery.DirectionMinMaxSelector`                0 or 1
=========   ====================================    =======================================================     ==========================


.. _filteringvertices:

Filtering Vertices
-------------------

Only a few of the filter types apply to vertices. The location of the vertex is the subject of the filter

=========   =======================================    =======================================================     ==========================
Selector    Selects                                    Selector Class                                              # objects returned
=========   =======================================    =======================================================     ==========================
>Y          Vertices farthest in the positive y dir    :py:class:`cadquery.DirectionMinMaxSelector`                0 or 1
<Y          Vertices farthest in the negative y dir    :py:class:`cadquery.DirectionMinMaxSelector`                0 or 1
=========   =======================================    =======================================================     ==========================

Future Enhancements
--------------------

    * Support direct vectors inline, such as \|(x,y,z)
    * Support multiple selectors separated by spaces, which unions the results, such as "+Z +Y to select both z and y-most faces