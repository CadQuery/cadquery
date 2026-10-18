.. _debugging:

Debugging CadQuery Models
=========================

A CadQuery model is written as a chain of operations. This makes the code compact, but it also means that a failure can appear far away from its cause: an error raised by ``chamfer`` may actually come from a selector that returned the wrong edges several steps earlier.

The techniques below make such problems easier to find.

Split the chain
---------------

The simplest technique is to break the chain into smaller steps, so that an exception points at the step that actually failed. For example:

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

Export intermediate results
---------------------------

Another useful technique is to export the intermediate shapes and open them in an external CAD viewer, so that each step of the chain can be inspected visually:

.. code-block:: python

    base = cq.Workplane("XY").box(2, 2, 2)
    base.export("step1.step")

    base = base.faces(">Z").workplane().hole(1)
    base.export("step2.step")

The available exporters are described in :ref:`importexport`, and the possibilities for displaying objects in a notebook or in a GUI are described in :ref:`vis`.

Getting help
------------

If a model cannot be made to work, it helps to reduce it to the smallest example that still fails, and to include that example together with the complete traceback when asking for help on the CadQuery Discord server or in an issue.
