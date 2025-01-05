
Workplane
=========

Most CAD programs use the concept of Workplanes. If you have experience with other CAD programs you will probably
feel comfortable with CadQuery's Workplanes, but if you don't have experience then they are an essential concept to
understand.

Workplanes represent a plane in space, from which other features can be located. They have a center point and a local
coordinate system. Most methods that create an object do so relative to the current workplane.

Usually the first workplane created is the "XY" plane, also known as the "front" plane. Once a solid is defined the most
common way to create a workplane is to select a face on the solid that you intend to modify and create a new workplane
relative to it. You can also create new workplanes anywhere in the world coordinate system, or relative to other planes
using offsets or rotations.

The most powerful feature of workplanes is that they allow you to work in 2D space in the coordinate system of the
workplane, and then CadQuery will transform these points from the workplane coordinate system to the world coordinate
system so your 3D features are located where you intended. This makes scripts much easier to create and maintain.

See :py:class:`cadquery.Workplane` to learn more.


2D Construction
---------------------------

Once you create a workplane, you can work in 2D, and then later use the features you create to make 3D objects.
You'll find all of the 2D constructs you expect -- circles, lines, arcs, mirroring, points, etc.

See :ref:`2dOperations` to learn more.


3D Construction
---------------------------

You can construct 3D primitives such as boxes, wedges, cylinders and spheres directly. You can also sweep, extrude,
and loft 2D geometry to form 3D features.  Of course the basic primitive operations are also available.

See :ref:`3doperations` to learn more.



Selectors
---------------------------

Selectors allow you to select one or more features, in order to define new features.  As an example, you might
extrude a box, and then select the top face as the location for a new feature.  Or, you might extrude a box, and
then select all of the vertical edges so that you can apply a fillet to them.

You can select Vertices, Edges, Faces, Solids, and Wires using selectors.

Think of selectors as the equivalent of your hand and mouse, if you were to build an object using a conventional CAD system.

See :ref:`selectors` to learn more.


Construction Geometry
---------------------------
Construction geometry are features that are not part of the object, but are only defined to aid in building the object.
A common example might be to define a rectangle, and then use the corners to define the location of a set of holes.

Most CadQuery construction methods provide a ``forConstruction`` keyword, which creates a feature that will only be used
to locate other features.


The Stack
---------------------------

As you work in CadQuery, each operation returns a new Workplane object with the result of that
operation. Each Workplane object has a list of objects, and a reference to its parent.

You can always go backwards to older operations by removing the current object from the stack.  For example::

    Workplane(someObject).faces(">Z").first().vertices()

returns a CadQuery object that contains all of the vertices on the highest face of someObject. But you can always move
backwards in the stack to get the face as well::

    Workplane(someObject).faces(">Z").first().vertices().end()

You can browse stack access methods here: :ref:`stackMethods`.


.. _chaining:

Chaining
---------------------------

All Workplane methods return another Workplane object, so that you can chain the methods together
fluently. Use the core Workplane methods to get at the objects that were created.

Each time a new Workplane object is produced during these chained calls, it has a
:attr:`~cadquery.Workplane.parent` attribute that points to the Workplane object that created it.
Several CadQuery methods search this parent chain, for example when searching for the context solid.
You can also give a Workplane object a tag, and further down your chain of calls you can refer back
to this particular object using its tag.


The Context Solid
---------------------------

Most of the time, you are building a single object, and adding features to that single object.  CadQuery watches
your operations, and defines the first solid object created as the 'context solid'.  After that, any features
you create are automatically combined (unless you specify otherwise) with that solid.  This happens even if the
solid was created a long way up in the stack.  For example::

    Workplane("XY").box(1, 2, 3).faces(">Z").circle(0.25).extrude(1)

Will create a 1x2x3 box, with a cylindrical boss extending from the top face.  It was not necessary to manually
combine the cylinder created by extruding the circle with the box, because the default behavior for extrude is
to combine the result with the context solid. The :meth:`~cadquery.Workplane.hole` method works similarly -- CadQuery presumes that you want
to subtract the hole from the context solid.

If you want to avoid this, you can specify ``combine=False``, and CadQuery will create the solid separately.


Iteration
---------------------------

CAD models often have repeated geometry, and it's really annoying to resort to for loops to construct features.
Many CadQuery methods operate automatically on each element on the stack, so that you don't have to write loops.
For example, this::

    Workplane("XY").box(1, 2, 3).faces(">Z").vertices().circle(0.5)

Will actually create 4 circles, because ``vertices()`` selects 4 vertices of a rectangular face, and the ``circle()`` method
iterates on each member of the stack.

This is really useful to remember when you author your own plugins. :py:meth:`cadquery.Workplane.each` is useful for this purpose.


An Introspective Example
------------------------

.. note::
    If you are just beginning with CadQuery then you can leave this example for later.  If you have
    some experience with creating CadQuery models and now you want to read the CadQuery source to
    better understand what your code does, then it is recommended you read this example first.

To demonstrate the above concepts, we can define a more detailed string representations for the
:class:`~cadquery.Workplane`, :class:`~cadquery.Plane` and :class:`~cadquery.CQContext` classes and
patch them in::

    import cadquery as cq


    def tidy_repr(obj):
        """Shortens a default repr string"""
        return repr(obj).split(".")[-1].rstrip(">")


    def _ctx_str(self):
        return (
            tidy_repr(self)
            + ":\n"
            + f"    pendingWires: {self.pendingWires}\n"
            + f"    pendingEdges: {self.pendingEdges}\n"
            + f"    tags: {self.tags}"
        )


    cq.cq.CQContext.__str__ = _ctx_str


    def _plane_str(self):
        return (
            tidy_repr(self)
            + ":\n"
            + f"    origin: {self.origin.toTuple()}\n"
            + f"    z direction: {self.zDir.toTuple()}"
        )


    cq.occ_impl.geom.Plane.__str__ = _plane_str


    def _wp_str(self):
        out = tidy_repr(self) + ":\n"
        out += f"  parent: {tidy_repr(self.parent)}\n" if self.parent else "  no parent\n"
        out += f"  plane: {self.plane}\n"
        out += f"  objects: {self.objects}\n"
        out += f"  modelling context: {self.ctx}"
        return out


    cq.Workplane.__str__ = _wp_str

Now we can make a simple part and examine the :class:`~cadquery.Workplane` and
:class:`~cadquery.cq.CQContext` objects at each step. The final part looks like:

.. cadquery::
    :select: part

    part = (
        cq.Workplane()
        .box(1, 1, 1)
        .tag("base")
        .wires(">Z")
        .toPending()
        .translate((0.1, 0.1, 1.0))
        .toPending()
        .loft()
        .faces(">>X", tag="base")
        .workplane(centerOption="CenterOfMass")
        .circle(0.2)
        .extrude(1)
    )

.. note::
    Some of the modelling process for this part is a bit contrived and not a great example of fluent
    CadQuery techniques.

The start of our chain of calls is::

    part = cq.Workplane()
    print(part)

Which produces the output:

.. code-block:: none

    Workplane object at 0x2760:
      no parent
      plane: Plane object at 0x2850:
        origin: (0.0, 0.0, 0.0)
        z direction: (0.0, 0.0, 1.0)
      objects: []
      modelling context: CQContext object at 0x2730:
        pendingWires: []
        pendingEdges: []
        tags: {}

This is simply an empty :class:`~cadquery.Workplane`. Being the first :class:`~cadquery.Workplane`
in the chain, it does not have a parent. The :attr:`~cadquery.Workplane.plane` attribute contains a
:class:`~cadquery.Plane` object that describes the XY plane.

Now we create a simple box. To keep things short, the ``print(part)`` line will not be shown for the
rest of these code blocks::

    part = part.box(1, 1, 1)

Which produces the output:

.. code-block:: none

    Workplane object at 0xaa90:
      parent: Workplane object at 0x2760
      plane: Plane object at 0x3850:
        origin: (0.0, 0.0, 0.0)
        z direction: (0.0, 0.0, 1.0)
      objects: [<cadquery.occ_impl.shapes.Solid object at 0xbbe0>]
      modelling context: CQContext object at 0x2730:
        pendingWires: []
        pendingEdges: []
        tags: {}

The first thing to note is that this is a different :class:`~cadquery.Workplane` object to the
previous one, and in the :attr:`~cadquery.Workplane.parent` attribute of this
:class:`~cadquery.Workplane` is our previous :class:`~cadquery.Workplane`. Returning a new instance
of :class:`~cadquery.Workplane` is the normal behaviour of most :class:`~cadquery.Workplane` methods
(with some exceptions, as will be shown below) and this is how the `chaining`_ concept is
implemented.

Secondly, the modelling context object is the same as the one in the previous
:class:`~cadquery.Workplane`, and this one modelling context at ``0x2730`` will be shared between
every :class:`Workplane` object in this chain. If we instantiate a new :class:`~cadquery.Workplane`
with ``part2 = cq.Workplane()``, then this ``part2`` would have a different instance of the
:class:`~cadquery.cq.CQContext` attached to it.

Thirdly, in our objects list is a single :class:`~cadquery.Solid` object, which is the box we just
created.

Often when creating models you will find yourself wanting to refer back to a specific
:class:`~cadquery.Workplane` object, perhaps because it is easier to select the feature you want in this
earlier state, or because you want to reuse a plane. Tags offer a way to refer back to a previous
:class:`~cadquery.Workplane`. We can tag the :class:`~cadquery.Workplane` that contains this basic box now::

    part = part.tag("base")

The string representation of ``part`` is now:

.. code-block:: none

    Workplane object at 0xaa90:
      parent: Workplane object at 0x2760
      plane: Plane object at 0x3850:
        origin: (0.0, 0.0, 0.0)
        z direction: (0.0, 0.0, 1.0)
      objects: [<cadquery.occ_impl.shapes.Solid object at 0xbbe0>]
      modelling context: CQContext object at 0x2730:
        pendingWires: []
        pendingEdges: []
        tags: {'base': <cadquery.cq.Workplane object at 0xaa90>}

The :attr:`~cadquery.cq.CQContext.tags` attribute of the modelling context is simply a dict
associating the string name given by the :meth:`~cadquery.Workplane.tag` method to the
:class:`~cadquery.Workplane`. Methods such as :meth:`~cadquery.Workplane.workplaneFromTagged` and
selection methods like :meth:`~cadquery.Workplane.edges` can operate on a tagged
:class:`~cadquery.Workplane`. Note that unlike the ``part = part.box(1, 1, 1)`` step where we went
from ``Workplane object at 0x2760`` to ``Workplane object at 0xaa90``, the
:meth:`~cadquery.Workplane.tag` method has returned the same object at ``0xaa90``. This is unusual
for a :class:`~cadquery.Workplane` method.

The next step is::

    part = part.faces(">>Z")

The output is:

.. code-block:: none

    Workplane object at 0x8c40:
      parent: Workplane object at 0xaa90
      plane: Plane object at 0xac40:
        origin: (0.0, 0.0, 0.0)
        z direction: (0.0, 0.0, 1.0)
      objects: [<cadquery.occ_impl.shapes.Face object at 0x3c10>]
      modelling context: CQContext object at 0x2730:
        pendingWires: []
        pendingEdges: []
        tags: {'base': <cadquery.cq.Workplane object at 0xaa90>}

Our selection method has taken the :class:`~cadquery.Solid` from the
:attr:`~cadquery.Workplane.objects` list of the previous :class:`~cadquery.Workplane`, found the
face with its center furthest in the Z direction, and placed that face into the
:attr:`~cadquery.Workplane.objects` attribute. The :class:`~cadquery.Solid` representing the box we
are modelling is gone, and when a :class:`~cadquery.Workplane` method needs to access that solid it
searches through the parent chain for the nearest solid. This action can also be done by a user
through the :meth:`~cadquery.Workplane.findSolid` method.

Now we want to select the boundary of this :class:`~cadquery.Face` (a :class:`~cadquery.Wire`), so
we use::

    part = part.wires()

The output is now:

.. code-block:: none

    Workplane object at 0x6880:
      parent: Workplane object at 0x8c40
      plane: Plane object at 0x38b0:
        origin: (0.0, 0.0, 0.0)
        z direction: (0.0, 0.0, 1.0)
      objects: [<cadquery.occ_impl.shapes.Wire object at 0xaca0>]
      modelling context: CQContext object at 0x2730:
        pendingWires: []
        pendingEdges: []
        tags: {'base': <cadquery.cq.Workplane object at 0xaa90>}

Modelling operations take their wires and edges from the modelling context's pending lists. In order
to use the :meth:`~cadquery.Workplane.loft` command further down the chain, we need to push this wire
to the modelling context with::

    part = part.toPending()

Now we have:

.. code-block:: none

    Workplane object at 0x6880:
      parent: Workplane object at 0x8c40
      plane: Plane object at 0x38b0:
        origin: (0.0, 0.0, 0.0)
        z direction: (0.0, 0.0, 1.0)
      objects: [<cadquery.occ_impl.shapes.Wire object at 0xaca0>]
      modelling context: CQContext object at 0x2730:
        pendingWires: [<cadquery.occ_impl.shapes.Wire object at 0xaca0>]
        pendingEdges: []
        tags: {'base': <cadquery.cq.Workplane object at 0xaa90>}

The :class:`~cadquery.Wire` object that was only in the :attr:`~cadquery.Workplane.objects`
attribute before is now also in the modelling context's :attr:`~cadquery.cq.CQContext.pendingWires`.
The :meth:`~cadquery.Workplane.toPending` method is also another of the unusual methods that return
the same :class:`~cadquery.Workplane` object instead of a new one.

To set up the other side of the :meth:`~cadquery.Workplane.loft` command further down the chain, we
translate the wire in :attr:`~cadquery.Workplane.objects` by calling::

    part = part.translate((0.1, 0.1, 1.0))

Now the string representation of ``part`` looks like:

.. code-block:: none

    Workplane object at 0x3a00:
      parent: Workplane object at 0x6880
      plane: Plane object at 0xac70:
        origin: (0.0, 0.0, 0.0)
        z direction: (0.0, 0.0, 1.0)
      objects: [<cadquery.occ_impl.shapes.Wire object at 0x35e0>]
      modelling context: CQContext object at 0x2730:
        pendingWires: [<cadquery.occ_impl.shapes.Wire object at 0xaca0>]
        pendingEdges: []
        tags: {'base': <cadquery.cq.Workplane object at 0xaa90>}

It may look similar to the previous step, but the :class:`~cadquery.Wire` object in
:attr:`~cadquery.Workplane.objects` is different. To get this wire into the pending wires list,
again we use::

    part = part.toPending()

The result:

.. code-block:: none

    Workplane object at 0x3a00:
      parent: Workplane object at 0x6880
      plane: Plane object at 0xac70:
        origin: (0.0, 0.0, 0.0)
        z direction: (0.0, 0.0, 1.0)
      objects: [<cadquery.occ_impl.shapes.Wire object at 0x35e0>]
      modelling context: CQContext object at 0x2730:
        pendingWires: [<cadquery.occ_impl.shapes.Wire object at 0xaca0>, <cadquery.occ_impl.shapes.Wire object at 0x7f5c7f5c35e0>]
        pendingEdges: []
        tags: {'base': <cadquery.cq.Workplane object at 0xaa90>}

The modelling context's :attr:`~cadquery.cq.CQContext.pendingWires` attribute now contains the two
wires we want to loft between, and we simply call::

    part = part.loft()

After the loft operation, our Workplane looks quite different:

.. code-block:: none

    Workplane object at 0x32b0:
      parent: Workplane object at 0x3a00
      plane: Plane object at 0x3d60:
        origin: (0.0, 0.0, 0.0)
        z direction: (0.0, 0.0, 1.0)
      objects: [<cadquery.occ_impl.shapes.Compound object at 0xad30>]
      modelling context: CQContext object at 0x2730:
        pendingWires: []
        pendingEdges: []
        tags: {'base': <cadquery.cq.Workplane object at 0xaa90>}

In the :attr:`cq.Workplane.objects` attribute we now have one :class:`~cadquery.Compound` object and the modelling
context's :attr:`~cadquery.cq.CQContext.pendingWires` has been cleared by
:meth:`~cadquery.Workplane.loft`.

.. note::
    To inspect the :class:`~cadquery.Compound` object further you can use
    :meth:`~cadquery.Workplane.val` or :meth:`~cadquery.Workplane.findSolid` to get at the
    :class:`~cadquery.Compound` object, then use :meth:`cadquery.Shape.Solids` to return a list
    of the :class:`~cadquery.Solid` objects contained in the :class:`~cadquery.Compound`, which in
    this example will be a single :class:`~cadquery.Solid` object. For example:

.. code-block:: pycon

    >>> a_compound = part.findSolid()
    >>> a_list_of_solids = a_compound.Solids()
    >>> len(a_list_of_solids)
    1

Now we will create a small cylinder protruding from a face on the original box. We need to set up a
workplane to draw a circle on, so firstly we will select the correct face::

    part = part.faces(">>X", tag="base")

Which results in:

.. code-block:: none

    Workplane object at 0x3f10:
      parent: Workplane object at 0x32b0
      plane: Plane object at 0xefa0:
        origin: (0.0, 0.0, 0.0)
        z direction: (0.0, 0.0, 1.0)
      objects: [<cadquery.occ_impl.shapes.Face object at 0x3af0>]
      modelling context: CQContext object at 0x2730:
        pendingWires: []
        pendingEdges: []
        tags: {'base': <cadquery.cq.Workplane object at 0xaa90>}

We have the desired :class:`~cadquery.Face` in the :attr:`~cadquery.Workplane.objects` attribute,
but the :attr:`~cadquery.Workplane.plane` has not changed yet. To create the new plane we use the
:meth:`Workplane.workplane` method::

    part = part.workplane()

Now:

.. code-block:: none

    Workplane object at 0xe700:
      parent: Workplane object at 0x3f10
      plane: Plane object at 0xe730:
        origin: (0.5, 0.0, 0.0)
        z direction: (1.0, 0.0, 0.0)
      objects: []
      modelling context: CQContext object at 0x2730:
        pendingWires: []
        pendingEdges: []
        tags: {'base': <cadquery.cq.Workplane object at 0xaa90>}

The :attr:`~cadquery.Workplane.objects` list has been cleared and the :class:`~cadquery.Plane`
object has a local Z direction in the global X direction. Since the base of the plane is the side of
the box, the origin is offset in the X direction.

Onto this plane we can draw a circle::

    part = part.circle(0.2)

Now:

.. code-block:: none

    Workplane object at 0xe790:
      parent: Workplane object at 0xe700
      plane: Plane object at 0xaf40:
        origin: (0.5, 0.0, 0.0)
        z direction: (1.0, 0.0, 0.0)
      objects: [<cadquery.occ_impl.shapes.Wire object at 0xe610>]
      modelling context: CQContext object at 0x2730:
        pendingWires: [<cadquery.occ_impl.shapes.Wire object at 0xe610>]
        pendingEdges: []
        tags: {'base': <cadquery.cq.Workplane object at 0xaa90>}

The :meth:`~cadquery.Workplane.circle` method - like all 2D drawing methods - has placed the circle
into both the :attr:`~cadquery.Workplane.objects` attribute (where it will be cleared during the
next modelling step), and the modelling context's pending wires (where it will persist until used by
another :class:`~cadquery.Workplane` method).

The next step is to extrude this circle and create a cylindrical protrusion::

    part = part.extrude(1, clean=False)

Now:

.. code-block:: none

    Workplane object at 0xafd0:
      parent: Workplane object at 0xe790
      plane: Plane object at 0x3e80:
        origin: (0.5, 0.0, 0.0)
        z direction: (1.0, 0.0, 0.0)
      objects: [<cadquery.occ_impl.shapes.Compound object at 0xaaf0>]
      modelling context: CQContext object at 0x2730:
        pendingWires: []
        pendingEdges: []
        tags: {'base': <cadquery.cq.Workplane object at 0xaa90>}

The :meth:`~cadquery.Workplane.extrude` method has cleared all the pending wires and edges. The
:attr:`~cadquery.Workplane.objects` attribute contains the final :class:`~cadquery.Compound` object
that is shown in the 3D view above.


.. note::
  The :meth:`~cadquery.Workplane.extrude` has an argument for ``clean`` which defaults to ``True``.
  This extrudes the pending wires (creating a new :class:`~cadquery.Workplane` object), then runs
  the :meth:`~cadquery.Workplane.clean` method to refine the result, creating another
  :class:`~cadquery.Workplane`. If you were to run the example with the default
  ``clean=True`` then you would see an intermediate
  :class:`~cadquery.Workplane` object in :attr:`~cadquery.Workplane.parent`
  rather than the object from the previous step.

