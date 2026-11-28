.. _debugging:

Debugging CadQuery Models
=========================

CadQuery can be used at three levels: the fluent API (:class:`~cadquery.Workplane`
and :class:`~cadquery.Sketch` method chains), the free function API
(:class:`~cadquery.Shape` and the functions in :mod:`cadquery.func`), and the
OCCT API exposed through OCP. The techniques below apply to all three, although
some of them are only relevant when working with the fluent API.

A failure can appear far away from its cause: in the fluent API an error raised
by ``chamfer`` may actually come from a selector that returned the wrong edges
several steps earlier, and in the free function API a shape can be silently
invalid without any exception being raised.

The techniques below make such problems easier to find.

Split the chain
---------------

When using the fluent API, the simplest technique is to break the chain into
smaller steps, so that an exception points at the step that actually failed.
For example:

.. code-block:: python

    result = (
        cq.Workplane("XY")
        .box(2, 2, 2)
        .faces(">Z")
        .edges()
        .chamfer(0.1)
    )

can be rewritten as:

.. code-block:: python

    base = cq.Workplane("XY").box(2, 2, 2)
    top = base.faces(">Z")
    edges = top.edges()
    result = edges.chamfer(0.1)

Inspect the chain without breaking it
-------------------------------------

:py:meth:`cadquery.Workplane.invoke` and :py:meth:`cadquery.Sketch.invoke`
execute a callable in the middle of a chain and return the current object,
unless the callable returns a new one. This makes it possible to print
intermediate results, or to enter the debugger, without rewriting the chain:

.. code-block:: python

    result = (
        cq.Workplane("XY")
        .box(2, 2, 2)
        .faces(">Z")
        .invoke(lambda w: print(w.size()))   # how many faces were selected?
        .edges()
        .invoke(breakpoint)                  # callables without arguments are supported
        .chamfer(0.1)
    )

Inspect the selection
---------------------

Several methods of :py:class:`cadquery.Workplane` return information about the objects that are currently selected, without changing the model:

* ``size()`` -- the number of objects on the stack.
* ``vals()`` -- the underlying OCCT objects on the stack.
* ``all()`` -- the objects on the stack, each wrapped in its own ``Workplane``.
* ``val()`` -- the first object on the stack.
* ``first()`` and ``last()`` -- the first and the last object on the stack.

Printing the number of selected objects is often enough to locate the problem:

.. code-block:: python

    edges = base.faces(">Z").edges()
    print(edges.size())     # how many edges did the selector find?

A result of ``0`` means that the selector matched nothing, which is a common cause of a later failure.

Selectors that match nothing
----------------------------

A selector that does not match anything returns an empty selection silently; the error only appears when the next operation cannot work with an empty list. Typical causes are:

* the direction in the selector does not correspond to any face or edge of the object being filtered;
* the previous step already narrowed the selection to a different type of object, so the new selector has nothing to filter;
* for non-planar faces the selector is evaluated at the center of mass of the face, which can give unexpected results (see :ref:`filteringfaces`).

Common error messages
---------------------

Some errors are raised by CadQuery itself instead of the modelling kernel, and their text points directly at the problem:

* ``Cannot find a solid on the stack or in the parent chain`` -- raised by :py:meth:`cadquery.Workplane.findSolid`, which is used by operations that modify an existing solid, such as ``fillet``, ``chamfer`` and ``shell``. It means that the current chain no longer contains a solid for the operation to modify, usually because a selection replaced it.

Check the shape itself
----------------------

The result of an operation can also be checked directly, without exporting or displaying it:

.. code-block:: python

    shape = result.val()
    print(shape.isValid())        # False if OCCT reports a defect
    print(shape.Volume())
    print(shape.BoundingBox())

``isValid()`` runs the OCCT ``BRepCheck_Analyzer`` on the shape and all of its sub-shapes, and is a quick way to detect a model that is geometrically broken even though no exception was raised. ``Volume()`` and ``BoundingBox()`` are useful to confirm that the result has the expected size and position.

Visualize intermediate results
------------------------------

Since version 2.4 CadQuery can display objects itself, so intermediate results do
not have to be exported and opened in an external viewer. :meth:`cadquery.vis.show`
accepts :class:`~cadquery.Workplane`, :class:`~cadquery.Sketch`,
:class:`~cadquery.Assembly`, :class:`~cadquery.Shape` and lists thereof, as well
as :class:`~cadquery.Vector` and :class:`~cadquery.Location` objects. The latter
are useful to display selections or the locations generated along a curve:

.. code-block:: python

    from cadquery.vis import show

    base = cq.Workplane("XY").box(2, 2, 2)
    top_edges = base.faces(">Z").edges()

    show(base, top_edges, alpha=0.5)

.. code-block:: python

    from cadquery.func import circle

    c = circle(1)

    # show the curve together with locations along it
    show(c, c.locations([0.1, 0.5, 0.9]))

The available visualization facilities are described in :ref:`vis`. When working
in a Python REPL or in IPython, :meth:`cadquery.fig.show` is more convenient
because it is non-blocking.

Getting help
------------

If a model cannot be made to work, it helps to reduce it to the smallest example that still fails, and to include that example together with the complete traceback when asking for help on the CadQuery Discord server or in an issue.
