.. _selector_reference:

*************************
CadQuery String Selectors
*************************

.. automodule:: cadquery

CadQuery selector strings allow filtering various types of object lists. Most commonly, Edges, Faces, and Vertices are
used, but all objects types can be filtered.

String selectors are used as arguments to the various selection methods:

    * :py:meth:`CQ.faces`
    * :py:meth:`CQ.edges`
    * :py:meth:`CQ.vertices`
    * :py:meth:`CQ.solids`
    * :py:meth:`CQ.shells`

.. note::

    String selectors are shortcuts to concrete selector classes, which you can use or extend. See
    :ref:`classreference` for more details

    If you find that the built-in selectors are not sufficient, you can easily plug in your own.
    See :ref:`extending` to see how.



.. _filteringfaces:

Filtering Faces
----------------

All types of filters work on faces.  In most cases, the selector refers to the direction of the **normal vector**
of the face.

.. warning::

    If a face is not planar, selectors are evaluated at the center of mass of the face. This can lead
    to results that are quite unexpected.

The axis used in the listing below are for illustration: any axis would work similarly in each case.

=========   ====================================        ======================================  ==========================
Selector    Selector Class                              Selects                                 # objects returned
=========   ====================================        ======================================  ==========================
+Z          :py:class:`DirectionSelector`               Faces with normal in +z direction       0 or 1
\|Z         :py:class:`ParallelDirSelector`             Faces parallel to xy plane              0..many
-X          :py:class:`DirectionSelector`               Faces with  normal in neg x direction   0..many
#Z          :py:class:`PerpendicularDirSelector`        Faces perpendicular to z direction      0..many
%Plane      :py:class:`TypeSelector`                    Faces of type plane                     0..many
>Y          :py:class:`DirectionMinMaxSelector`         Face farthest in the positive y dir     0 or 1
<Y          :py:class:`DirectionMinMaxSelector`         Face farthest in the negative y dir     0 or 1
=========   ====================================        ======================================  ==========================


.. _filteringedges:

Filtering Edges
----------------

Some filter types are not supported for edges.  The selector usually refers to the **direction** of the edge.

.. warning::

    Non-linear edges are not selected for any selectors except type (%). Non-linear edges are never returned
    when these filters are applied.

The axis used in the listing below are for illustration: any axis would work similarly in each case.



=========   ====================================        =====================================   ==========================
Selector    Selector Class                              Selects                                 # objects returned
=========   ====================================        =====================================   ==========================
+Z          :py:class:`DirectionSelector`               Edges aligned in the Z direction        0..many
\|Z         :py:class:`ParallelDirSelector`             Edges parallel to z direction           0..many
-X          :py:class:`DirectionSelector`               Edges aligned in neg x direction        0..many
#Z          :py:class:`PerpendicularDirSelector`        Edges perpendicular to z direction      0..many
%Line       :py:class:`TypeSelector`                    Edges type line                         0..many
>Y          :py:class:`DirectionMinMaxSelector`         Edges farthest in the positive y dir    0 or 1
<Y          :py:class:`DirectionMinMaxSelector`         Edges farthest in the negative y dir    0 or 1
=========   ====================================        =====================================   ==========================


.. _filteringvertices:

Filtering Vertices
-------------------

Only a few of the filter types apply to vertices. The location of the vertex is the subject of the filter

=========   ====================================        =====================================   ==========================
Selector    Selector Class                              Selects                                 # objects returned
=========   ====================================        =====================================   ==========================
>Y          :py:class:`DirectionMinMaxSelector`         Edges farthest in the positive y dir    0 or 1
<Y          :py:class:`DirectionMinMaxSelector`         Edges farthest in the negative y dir    0 or 1
=========   ====================================        =====================================   ==========================

Future Enhancements
--------------------

    * Support direct vectors inline, such as \|(x,y,z)
    * Support multiple selectors separated by spaces, which unions the results, such as "+Z +Y to select both z and y-most faces