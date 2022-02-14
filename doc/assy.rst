.. _assytutorial:

**********
Assemblies
**********

Assembly tutorial
-----------------

The purpose of this section is to demonstrate how to use the assembly and constraints
functionality to build a realistic model. It will be a enclosure door assembly made out of 20x20 v-slot profiles.


Defining parameters
===================

We want to start with defining the model parameters to allow for easy dimension changes later:

.. code-block:: python

    import cadquery as cq
    
    # Parameters
    H = 400
    W = 200
    D = 350
    
    PROFILE = cq.importers.importDXF("vslot-2020_1.dxf").wires()
    
    SLOT_D = 5
    PANEL_T = 3
    
    HANDLE_D = 20
    HANDLE_L = 50
    HANDLE_W = 4
    
It is interesting to note that the v-slot profile is imported from a DXF file.
This way it is very easy to change to other aluminum extrusion type, e.g. Item or Bosch.
Vendors usually provide DXF files.

Defining reusable components
============================

Next we want to define functions generating the assembly components based on the specified parameters.

.. code-block:: python

    def make_vslot(l):
    
        return PROFILE.toPending().extrude(l)
    
    
    def make_connector():
    
        rv = (
            cq.Workplane()
            .box(20, 20, 20)
            .faces("<X")
            .workplane()
            .cboreHole(6, 15, 18)
            .faces("<Z")
            .workplane(centerOption="CenterOfMass")
            .cboreHole(6, 15, 18)
        )
    
        # tag mating faces
        rv.faces(">X").tag("X").end()
        rv.faces(">Z").tag("Z").end()
    
        return rv
    
    
    def make_panel(w, h, t, cutout):
    
        rv = (
            cq.Workplane("XZ")
            .rect(w, h)
            .extrude(t)
            .faces(">Y")
            .vertices()
            .rect(2*cutout,2*cutout)
            .cutThruAll()
            .faces("<Y")
            .workplane()
            .pushPoints([(-w / 3, HANDLE_L / 2), (-w / 3, -HANDLE_L / 2)])
            .hole(3)
        )
    
        # tag mating edges
        rv.faces(">Y").edges("%CIRCLE").edges(">Z").tag("hole1")
        rv.faces(">Y").edges("%CIRCLE").edges("<Z").tag("hole2")
    
        return rv
    
    
    def make_handle(w, h, r):
    
        pts = ((0, 0), (w, 0), (w, h), (0, h))
    
        path = cq.Workplane().polyline(pts)
    
        rv = (
            cq.Workplane("YZ")
            .rect(r, r)
            .sweep(path, transition="round")
            .tag("solid")
            .faces("<X")
            .workplane()
            .faces("<X", tag="solid")
            .hole(r / 1.5)
        )
        
        # tag mating faces
        rv.faces("<X").faces(">Y").tag("mate1")
        rv.faces("<X").faces("<Y").tag("mate2")
    
        return rv
        
Initial assembly
================

Next we want to instantiate all the components and add them to the assembly.

.. code-block:: python
   
    # define the elements
    door = (
        cq.Assembly()
        .add(make_vslot(H), name="left")
        .add(make_vslot(H), name="right")
        .add(make_vslot(W), name="top")
        .add(make_vslot(W), name="bottom")
        .add(make_connector(), name="con_tl", color=cq.Color("black"))
        .add(make_connector(), name="con_tr", color=cq.Color("black"))
        .add(make_connector(), name="con_bl", color=cq.Color("black"))
        .add(make_connector(), name="con_br", color=cq.Color("black"))
        .add(
            make_panel(W + SLOT_D, H + SLOT_D, PANEL_T, SLOT_D),
            name="panel",
            color=cq.Color(0, 0, 1, 0.2),
        )
        .add(
            make_handle(HANDLE_D, HANDLE_L, HANDLE_W),
            name="handle",
            color=cq.Color("yellow"),
        )
    )
    
Constraints definition
======================

Then we want to define all the constraints

.. code-block:: python

    # define the constraints
    (
        door
        # left profile
        .constrain("left@faces@<Z", "con_bl?Z", "Plane")
        .constrain("left@faces@<X", "con_bl?X", "Axis")
        .constrain("left@faces@>Z", "con_tl?Z", "Plane")
        .constrain("left@faces@<X", "con_tl?X", "Axis")
        # top
        .constrain("top@faces@<Z", "con_tl?X", "Plane")
        .constrain("top@faces@<Y", "con_tl@faces@>Y", "Axis")
        # bottom
        .constrain("bottom@faces@<Y", "con_bl@faces@>Y", "Axis")
        .constrain("bottom@faces@>Z", "con_bl?X", "Plane")
        # right connectors
        .constrain("top@faces@>Z", "con_tr@faces@>X", "Plane")
        .constrain("bottom@faces@<Z", "con_br@faces@>X", "Plane")
        .constrain("left@faces@>Z", "con_tr?Z", "Axis")
        .constrain("left@faces@<Z", "con_br?Z", "Axis")
        # right profile
        .constrain("right@faces@>Z", "con_tr@faces@>Z", "Plane")
        .constrain("right@faces@<X", "left@faces@<X", "Axis")
        # panel
        .constrain("left@faces@>X[-4]", "panel@faces@<X", "Plane")
        .constrain("left@faces@>Z", "panel@faces@>Z", "Axis")
        # handle
        .constrain("panel?hole1", "handle?mate1", "Plane")
        .constrain("panel?hole2", "handle?mate2", "Point")
    )
    
Should you need to do something unusual that is not possible with the string
based selectors (e.g. use :py:class:`cadquery.selectors.BoxSelector` or a user-defined selector class),
it is possible to pass :py:class:`cadquery.Shape` objects to the :py:meth:`cadquery.Assembly.constrain` method directly. For example, the above

.. code-block:: python

    .constrain('part1@faces@>Z','part3@faces@<Z','Axis')

is equivalent to

.. code-block:: python

    .constrain('part1',part1.faces('>z').val(),'part3',part3.faces('<Z').val(),'Axis')

This method requires a :py:class:`cadquery.Shape` object, so remember to use the :py:meth:`cadquery.Workplane.val`
method to pass a single :py:class:`cadquery.Shape` and not the whole :py:class:`cadquery.Workplane` object.

Final result
============

Below is the complete code including the final solve step.

.. cadquery::
    :height: 600px

    import cadquery as cq
    
    # Parameters
    H = 400
    W = 200
    D = 350
    
    PROFILE = cq.importers.importDXF("vslot-2020_1.dxf").wires()
    
    SLOT_D = 6
    PANEL_T = 3
    
    HANDLE_D = 20
    HANDLE_L = 50
    HANDLE_W = 4
    
    
    def make_vslot(l):
    
        return PROFILE.toPending().extrude(l)
    
    
    def make_connector():
    
        rv = (
            cq.Workplane()
            .box(20, 20, 20)
            .faces("<X")
            .workplane()
            .cboreHole(6, 15, 18)
            .faces("<Z")
            .workplane(centerOption="CenterOfMass")
            .cboreHole(6, 15, 18)
        )
    
        # tag mating faces
        rv.faces(">X").tag("X").end()
        rv.faces(">Z").tag("Z").end()
    
        return rv
    
    
    def make_panel(w, h, t, cutout):
    
        rv = (
            cq.Workplane("XZ")
            .rect(w, h)
            .extrude(t)
            .faces(">Y")
            .vertices()
            .rect(2*cutout,2*cutout)
            .cutThruAll()
            .faces("<Y")
            .workplane()
            .pushPoints([(-w / 3, HANDLE_L / 2), (-w / 3, -HANDLE_L / 2)])
            .hole(3)
        )
    
        # tag mating edges
        rv.faces(">Y").edges("%CIRCLE").edges(">Z").tag("hole1")
        rv.faces(">Y").edges("%CIRCLE").edges("<Z").tag("hole2")
    
        return rv
    
    
    def make_handle(w, h, r):
    
        pts = ((0, 0), (w, 0), (w, h), (0, h))
    
        path = cq.Workplane().polyline(pts)
    
        rv = (
            cq.Workplane("YZ")
            .rect(r, r)
            .sweep(path, transition="round")
            .tag("solid")
            .faces("<X")
            .workplane()
            .faces("<X", tag="solid")
            .hole(r / 1.5)
        )
        
        # tag mating faces
        rv.faces("<X").faces(">Y").tag("mate1")
        rv.faces("<X").faces("<Y").tag("mate2")
    
        return rv
    
    
    # define the elements
    door = (
        cq.Assembly()
        .add(make_vslot(H), name="left")
        .add(make_vslot(H), name="right")
        .add(make_vslot(W), name="top")
        .add(make_vslot(W), name="bottom")
        .add(make_connector(), name="con_tl", color=cq.Color("black"))
        .add(make_connector(), name="con_tr", color=cq.Color("black"))
        .add(make_connector(), name="con_bl", color=cq.Color("black"))
        .add(make_connector(), name="con_br", color=cq.Color("black"))
        .add(
            make_panel(W + 2*SLOT_D, H + 2*SLOT_D, PANEL_T, SLOT_D),
            name="panel",
            color=cq.Color(0, 0, 1, 0.2),
        )
        .add(
            make_handle(HANDLE_D, HANDLE_L, HANDLE_W),
            name="handle",
            color=cq.Color("yellow"),
        )
    )
    
    # define the constraints
    (
        door
        # left profile
        .constrain("left@faces@<Z", "con_bl?Z", "Plane")
        .constrain("left@faces@<X", "con_bl?X", "Axis")
        .constrain("left@faces@>Z", "con_tl?Z", "Plane")
        .constrain("left@faces@<X", "con_tl?X", "Axis")
        # top
        .constrain("top@faces@<Z", "con_tl?X", "Plane")
        .constrain("top@faces@<Y", "con_tl@faces@>Y", "Axis")
        # bottom
        .constrain("bottom@faces@<Y", "con_bl@faces@>Y", "Axis")
        .constrain("bottom@faces@>Z", "con_bl?X", "Plane")
        # right connectors
        .constrain("top@faces@>Z", "con_tr@faces@>X", "Plane")
        .constrain("bottom@faces@<Z", "con_br@faces@>X", "Plane")
        .constrain("left@faces@>Z", "con_tr?Z", "Axis")
        .constrain("left@faces@<Z", "con_br?Z", "Axis")
        # right profile
        .constrain("right@faces@>Z", "con_tr@faces@>Z", "Plane")
        .constrain("right@faces@<X", "left@faces@<X", "Axis")
        # panel
        .constrain("left@faces@>X[-4]", "panel@faces@<X", "Plane")
        .constrain("left@faces@>Z", "panel@faces@>Z", "Axis")
        # handle
        .constrain("panel?hole1", "handle?mate1", "Plane")
        .constrain("panel?hole2", "handle?mate2", "Point")
    )
    
    # solve
    door.solve()
    
    show_object(door,name='door')


Data export
===========

The resulting assembly can be exported as a STEP file or in a internal OCCT XML format.


STEP can be loaded in all CAD tool, e.g. in FreeCAD and the XML be used in other applications using OCCT.

.. code-block:: python
   :linenos:

    door.save('door.step')
    door.save('door.xml')
    
In the case of STEP colors are preserved but not transparency.

..  image:: _static/door_assy_freecad.png


Object locations
----------------

Objects can be added to an assembly with initial locations supplied, such as:

.. cadquery::

    import cadquery as cq

    cone = cq.Solid.makeCone(1, 0, 2)

    assy = cq.Assembly()
    assy.add(
        cone,
        loc=cq.Location(cq.Vector(0, 0, 0), cq.Vector(1, 0, 0), 180),
        name="cone0",
        color=cq.Color("green")
    )
    assy.add(cone, name="cone1", color=cq.Color("blue"))

    show_object(assy)


As an alternative to the user calculating locations, constraints and the method
:meth:`~cadquery.Assembly.solve` can be used to position objects in an assembly.

If initial locations and the method :meth:`~cadquery.Assembly.solve` are used the solver will
overwrite these initial locations with it's solution, however initial locations can still affect the
final solution. In an underconstrained system the solver may not move an object if it does not
contribute to the cost function, or if multiple solutions exist (ie. multiple instances
where the cost function is at a minimum) initial locations can cause the solver to converge on one
particular solution. For very complicated assemblies setting approximately correct initial locations
can also reduce the computational time requred.


Constraints
-----------

Constraints are often a better representation of the real world relationship the user wants to
model than directly supplying locations. In the above example the real world relationship is that
the bottom face of each cone should touch, which can be modelled with a Plane constraint. When the
user provides explicit locations (instead of constraints) then they are also reponsible for updating
them when, for example, the location of ``cone1`` changes.

When at least one constraint is supplied and the method :meth:`~cadquery.Assembly.solve` is run, an
optimization problem is set up. Each constraint provides a cost function that depends on the
position and orientation (represented by a :class:`~cadquery.Location`) of the two objects specified
when creating the constraint. The solver varies the location of the assembly's children and attempts
to minimize the sum of all cost functions. Hence by reading the formulae of the cost functions
below, you can understand exactly what each constraint does.


Point
=====

The Point constraint is a frequently used constraint that minimizes the distance between two points.
Some example uses are centering faces or aligning verticies, but it is also useful with dummy
vertices to create offsets between two parts.

The cost function is:

.. math::

  ( param - \lvert \vec{ c_1 } - \vec{ c_2 } \rvert ) ^2

Where:

- :math:`param` is the parameter of the constraint, which defaults to 0,
- :math:`\vec{ c_i }` is the center of the ith object, and
- :math:`\lvert \vec{ v } \rvert` is the modulus of :math:`\vec{ v }`, ie. the length of
  :math:`\vec{ v }`.

When creating a Point constraint, the ``param`` argument can be used to specify a desired offset
between the two centers. This offset does not have a direction associated with it, if you want to
specify an offset in a specific direction then you should use a dummy :class:`~cadquery.Vertex`.

The Point constraint uses the :meth:`~cadquery.occ_impl.Shape.Center` to find the center of the
argument. Hence it will work with all subclasses of :class:`~caquery.occ_impl.Shape`.

.. cadquery::

    import cadquery as cq

    # Use the Point constraint to position boxes relative to an arc
    line = cq.Edge.makeCircle(radius=10, angle1=0, angle2=90)
    box = cq.Workplane().box(1, 1, 1)

    assy = cq.Assembly()
    assy.add(line, name="line")
    
    # position the red box on the center of the arc
    assy.add(box, name="box0", color=cq.Color("red"))
    assy.constrain("line", "box0", "Point")
    
    # position the green box at a normalized distance of 0.8 along the arc
    position0 = line.positionAt(0.8)
    assy.add(box, name="box1", color=cq.Color("green"))
    assy.constrain(
        "line", cq.Vertex.makeVertex(*position0.toTuple()), "box1", box.val(), "Point",
    )
    
    # position the orange box 2 units in any direction from the green box
    assy.add(box, name="box2", color=cq.Color("orange"))
    assy.constrain(
        "line",
        cq.Vertex.makeVertex(*position0.toTuple()),
        "box2",
        box.val(),
        "Point",
        param=2,
    )

    # position the blue box offset 2 units in the x direction from the green box
    position1 = position0 + cq.Vector(2, 0, 0)
    assy.add(box, name="box3", color=cq.Color("blue"))
    assy.constrain(
        "line", cq.Vertex.makeVertex(*position1.toTuple()), "box3", box.val(), "Point",
    )
    
    assy.solve()
    show_object(assy)


Axis
====

The Axis constraint minimizes the angle between two vectors. It is frequently used to align faces
and control the rotation of an object.

The cost function is:

.. math::
    ( k_{ dir } \times ( param - \vec{ d_1 } \angle \vec{ d_2 } ) ^2


Where:

- :math:`k_{ dir }` is a scaling factor for directional constraints,
- :math:`param` is the parameter of the constraint, which defaults to :math:`\pi` radians,
- :math:`\vec{d_i}` is the direction created from the ith object argument as described below, and
- :math:`\vec{ d_1 } \angle \vec{ d_2 }` is the angle in radians between :math:`\vec{ d_1 }` and
  :math:`\vec{ d_2 }`.


The argument ``param`` defaults to :math:`\pi` radians, which sets the two directions opposite
to each other. This represents what is often called a "mate" relationship, where the external faces
of two objects touch.


.. cadquery::

    import cadquery as cq

    cone = cq.Solid.makeCone(1, 0, 2)

    assy = cq.Assembly()
    assy.add(cone, name="cone0", color=cq.Color("green"))
    assy.add(cone, name="cone1", color=cq.Color("blue"))
    assy.constrain("cone0@faces@<Z", "cone1@faces@<Z", "Axis")
    
    assy.solve()
    show_object(assy)


If the ``param`` argument is set to zero, then the two objects will point in the same direction.
This is often used when one object goes through another, such as a pin going into a hole in a plate:


.. cadquery::

    import cadquery as cq

    plate = cq.Workplane().box(10, 10, 1).faces(">Z").workplane().hole(2)
    cone = cq.Solid.makeCone(0.8, 0, 4)
    
    assy = cq.Assembly()
    assy.add(plate, name="plate", color=cq.Color("green"))
    assy.add(cone, name="cone", color=cq.Color("blue"))
    # place the center of the flat face of the cone in the center of the upper face of the plate
    assy.constrain("plate@faces@>Z", "cone@faces@<Z", "Point")
    
    # set both the flat face of the cone and the upper face of the plate to point in the same direction
    assy.constrain("plate@faces@>Z", "cone@faces@<Z", "Axis", param=0)
    
    assy.solve()
    show_object(assy)


In creating an Axis constraint, a direction vector is extracted in one of three different ways,
depending on the object's type.

:class:`~cadquery.Face`:
  Using :meth:`~cadquery.Face.normalAt`

:class:`~cadquery.Edge` and :meth:`~cadquery.Shape.geomType` is ``"CIRCLE"``:
  Using :meth:`~cadquery.Mixin1D.normal`

:class:`~cadquery.Edge` and :meth:`~cadquery.Shape.geomType` is not ``"CIRCLE"``:
  Using :meth:`~cadquery.Mixin1D.tangentAt`

Using any other type of object will raise a :exc:`ValueError`. By far the most common use case
is to define an Axis constraint from a :class:`~cadquery.Face`.


.. cadquery::

    import cadquery as cq
    from math import cos, sin, pi

    # Create a sinusoidal surface:
    surf = cq.Workplane().parametricSurface(
        lambda u, v: (u, v, 5 * sin(pi * u / 10) * cos(pi * v / 10)),
        N=40,
        start=0,
        stop=20,
    )

    # Create a cone with a small, flat tip:
    cone = (
        cq.Workplane()
        .add(cq.Solid.makeCone(1, 0.1, 2))
        # tag the tip for easy reference in the constraint:
        .faces(">Z")
        .tag("tip")
        .end()
    )

    assy = cq.Assembly()
    assy.add(surf, name="surf", color=cq.Color("lightgray"))
    assy.add(cone, name="cone", color=cq.Color("green"))
    # set the Face on the tip of the cone to point in
    # the opposite direction of the center of the surface:
    assy.constrain("surf", "cone?tip", "Axis")
    # to make the example clearer, move the cone to the center of the face:
    assy.constrain("surf", "cone?tip", "Point")
    assy.solve()

    show_object(assy)


Plane
=====

The Plane constraint is simply a combination of both the Point and Axis constraints. It is a
convenient shortcut for a commonly used combination of constraints. It can be used to shorten the
previous example from the two constraints to just one:

.. code-block:: diff

    assy = cq.Assembly()
    assy.add(surf, name="surf", color=cq.Color("lightgray"))
    assy.add(cone, name="cone", color=cq.Color("green"))
    -# set the Face on the tip of the cone to point in
    -# the opposite direction of the center of the surface:
    -assy.constrain("surf", "cone?tip", "Axis")
    -# to make the example clearer, move the cone to the center of the face:
    -assy.constrain("surf", "cone?tip", "Point")
    +assy.constrain("surf", "cone?tip", "Plane")
    assy.solve()

    show_object(assy)


The result of this code is identical to the above two constraint example.

For the cost function of Plane, please see the Point and Axis sections. The ``param`` argument is applied to Axis and should be left as the default value for a "mate" style
constraint (two surfaces touching) or can be set to ``0`` for a through surface constraint (see
description in the Axis constraint section).


PointInPlane
============

PointInPlane positions the center of the first object within the plane defined by the second object.
The cost function is:

.. math::

    \operatorname{dist}( \vec{ c }, p_\text{ offset } ) ^2


Where:

- :math:`\vec{ c }` is the center of the first argument,
- :math:`p_\text{ offset }` is a plane created from the second object, offset in the plane's normal
  direction by ``param``, and
- :math:`\operatorname{dist}( \vec{ a }, b)` is the distance between point :math:`\vec{ a }` and
  plane :math:`b`.

    
.. cadquery::

    import cadquery as cq

    # Create an L-shaped object:
    bracket = (
        cq.Workplane("YZ")
        .hLine(1)
        .vLine(0.1)
        .hLineTo(0.2)
        .vLineTo(1)
        .hLineTo(0)
        .close()
        .extrude(1)
        # tag some faces for easy reference:
        .faces(">Y[1]")
        .tag("inner_vert")
        .end()
        .faces(">Z[1]")
        .tag("inner_horiz")
        .end()
    )

    box = cq.Workplane().box(0.5, 0.5, 0.5)

    assy = cq.Assembly()
    assy.add(bracket, name="bracket", color=cq.Color("gray"))
    assy.add(box, name="box", color=cq.Color("green"))

    # lock bracket orientation:
    assy.constrain("bracket@faces@>Z", "box@faces@>Z", "Axis", param=0)
    assy.constrain("bracket@faces@>X", "box@faces@>X", "Axis", param=0)

    # constrain the bottom of the box to be on the plane defined by inner_horiz:
    assy.constrain("box@faces@<Z", "bracket?inner_horiz", "PointInPlane")
    # constrain the side of the box to be 0.2 units from the plane defined by inner_vert
    assy.constrain("box@faces@<Y", "bracket?inner_vert", "PointInPlane", param=0.2)
    # constrain the end of the box to be 0.1 units inside the end of the bracket
    assy.constrain("box@faces@>X", "bracket@faces@>X", "PointInPlane", param=-0.1)

    assy.solve()
    show_object(assy)


PointOnLine
===========

PointOnLine positions the center of the first object on the line defined by the second object.
The cost function is:

.. math::

   ( param - \operatorname{dist}(\vec{ c }, l ) )^2


Where:

- :math:`\vec{ c }` is the center of the first argument,
- :math:`l` is a line created from the second object
- :math:`param` is the parameter of the constraint, which defaults to 0,
- :math:`\operatorname{dist}( \vec{ a }, b)` is the distance between point :math:`\vec{ a }` and
  line :math:`b`.


.. cadquery::

    import cadquery as cq

    b1 = cq.Workplane().box(1,1,1)
    b2 = cq.Workplane().sphere(0.15)

    assy = (
        cq.Assembly()
        .add(b1,name='b1')
        .add(b2, loc=cq.Location(cq.Vector(0,0,4)), name='b2', color=cq.Color('red'))
    )

    # fix the position of b1
    assy.constrain('b1','Fixed')
    # b2 on one of the edges of b1
    assy.constrain('b2','b1@edges@>>Z and >>Y','PointOnLine')
    # b2 on another of the edges of b1
    assy.constrain('b2','b1@edges@>>Z and >>X','PointOnLine')
    # effectively b2 will be constrained to be on the intersection of the two edges

    assy.solve()
    show_object(assy)


FixedPoint
==========

FixedPoint fixes the position of the given argument to be equal to the given point specified via the parameter of the constraint. This constraint locks all translational degrees of freedom of the argument.
The cost function is:

.. math::

   \left\lVert \vec{ c } - \vec{param} \right\rVert ^2


Where:

- :math:`\vec{ c }` is the center of the argument,
- :math:`param` is the parameter of the constraint - tuple specifying the target position,
- :math:`\operatorname{dist}( \vec{ a }, b)` is the distance between point :math:`\vec{ a }` and
  line :math:`b`.


.. cadquery::

    import cadquery as cq

    b1 = cq.Workplane().box(1,1,1)
    b2 = cq.Workplane().sphere(0.15)

    assy = (
        cq.Assembly()
        .add(b1,name='b1')
        .add(b2, loc=cq.Location(cq.Vector(0,0,4)), name='b2', color=cq.Color('red'))
    )

    # fix the position of b1
    assy.constrain('b1','Fixed')
    # b2 on one of the edges of b1
    assy.constrain('b2','b1@edges@>>Z and >>Y','PointOnLine')
    # b2 on another of the edges of b1
    assy.constrain('b2','b1@edges@>>Z and >>X','PointOnLine')
    # effectively b2 will be constrained to be on the intersection of the two edges

    assy.solve()
    show_object(assy)


FixedRotation
=============

FixedRotation fixes the rotation of the given argument to be equal to the value specified via the parameter of the constraint. The argument is rotated about it's origin firstly by the Z angle, then Y and finally X.

This constraint locks all rotational degrees of freedom of the argument.
The cost function is:

.. math::

   \left\lVert \vec{ R } - \vec{param} \right\rVert ^2


Where:

- :math:`\vec{ R }` vector of the rotation angles of the rotation applied to the argument,
- :math:`param` is the parameter of the constraint - tuple specifying the target rotation.


.. cadquery::

    import cadquery as cq

    b1 = cq.Workplane().box(1,1,1)
    b2 = cq.Workplane().rect(0.1, 0.1).extrude(1,taper=-15)

    assy = (
        cq.Assembly()
        .add(b1,name='b1')
        .add(b2, loc=cq.Location(cq.Vector(0,0,4)), name='b2', color=cq.Color('red'))
    )

    # fix the position of b1
    assy.constrain('b1','Fixed')
    # fix b2 bottom face position (but not rotation)
    assy.constrain('b2@faces@<Z','FixedPoint',(0,0,0.5))
    # fix b2 rotational degrees of freedom too
    assy.constrain('b2','FixedRotation',(45,0,45))

    assy.solve()
    show_object(assy)


FixedAxis
=========

FixedAxis fixes the orientation of the given argument's normal or tangent to be equal to the orientation of the vector specified via the parameter of the constraint. This constraint locks two rotational degrees of freedom of the argument.
The cost function is:

.. math::

   ( \vec{ a } \angle \vec{ param } ) ^2


Where:

- :math:`\vec{ a }` normal or tangent vector of the argument,
- :math:`param` is the parameter of the constraint - tuple specifying the target direction.


.. cadquery::

    import cadquery as cq

    b1 = cq.Workplane().box(1,1,1)
    b2 = cq.Workplane().rect(0.1, 0.1).extrude(1,taper=-15)

    assy = (
        cq.Assembly()
        .add(b1,name='b1')
        .add(b2, loc=cq.Location(cq.Vector(0,0,4)), name='b2', color=cq.Color('red'))
    )

    # fix the position of b1
    assy.constrain('b1','Fixed')
    # fix b2 bottom face position (but not rotation)
    assy.constrain('b2@faces@<Z','FixedPoint',(0,0,0.5))
    # fix b2 some rotational degrees of freedom too
    assy.constrain('b2@faces@>Z','FixedAxis',(1,0,2))

    assy.solve()
    show_object(assy)


Assembly colors
---------------

Aside from RGBA values, the :class:`~cadquery.Color` class can be instantiated from a text name. Valid names are
listed along with a color sample below:

.. raw:: html

    <div class="color-grid" style="display:grid;grid-gap:10px;grid-template-columns:repeat(auto-fill, minmax(200px,1fr));">
      <div style="background-color:rgba(222,239,255,1.0);padding:10px;border-radius:5px;color:rgba(0,0,0);">aliceblue</div>
      <div style="background-color:rgba(243,211,173,1.0);padding:10px;border-radius:5px;color:rgba(0,0,0);">antiquewhite</div>
      <div style="background-color:rgba(255,220,180,1.0);padding:10px;border-radius:5px;color:rgba(0,0,0);">antiquewhite1</div>
      <div style="background-color:rgba(218,188,153,1.0);padding:10px;border-radius:5px;color:rgba(0,0,0);">antiquewhite2</div>
      <div style="background-color:rgba(155,134,110,1.0);padding:10px;border-radius:5px;color:rgba(0,0,0);">antiquewhite3</div>
      <div style="background-color:rgba(65,57,47,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">antiquewhite4</div>
      <div style="background-color:rgba(54,255,167,1.0);padding:10px;border-radius:5px;color:rgba(0,0,0);">aquamarine1</div>
      <div style="background-color:rgba(46,218,144,1.0);padding:10px;border-radius:5px;color:rgba(0,0,0);">aquamarine2</div>
      <div style="background-color:rgba(15,65,44,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">aquamarine4</div>
      <div style="background-color:rgba(222,255,255,1.0);padding:10px;border-radius:5px;color:rgba(0,0,0);">azure</div>
      <div style="background-color:rgba(190,218,218,1.0);padding:10px;border-radius:5px;color:rgba(0,0,0);">azure2</div>
      <div style="background-color:rgba(135,155,155,1.0);padding:10px;border-radius:5px;color:rgba(0,0,0);">azure3</div>
      <div style="background-color:rgba(57,65,65,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">azure4</div>
      <div style="background-color:rgba(68,10,68,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">beet</div>
      <div style="background-color:rgba(232,232,182,1.0);padding:10px;border-radius:5px;color:rgba(0,0,0);">beige</div>
      <div style="background-color:rgba(255,197,140,1.0);padding:10px;border-radius:5px;color:rgba(0,0,0);">bisque</div>
      <div style="background-color:rgba(218,169,120,1.0);padding:10px;border-radius:5px;color:rgba(0,0,0);">bisque2</div>
      <div style="background-color:rgba(155,120,87,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">bisque3</div>
      <div style="background-color:rgba(65,52,37,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">bisque4</div>
      <div style="background-color:rgba(0,0,0,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">black</div>
      <div style="background-color:rgba(255,211,155,1.0);padding:10px;border-radius:5px;color:rgba(0,0,0);">blanchedalmond</div>
      <div style="background-color:rgba(0,0,255,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">blue</div>
      <div style="background-color:rgba(0,0,255,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">blue1</div>
      <div style="background-color:rgba(0,0,218,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">blue2</div>
      <div style="background-color:rgba(0,0,155,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">blue3</div>
      <div style="background-color:rgba(0,0,65,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">blue4</div>
      <div style="background-color:rgba(64,6,193,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">blueviolet</div>
      <div style="background-color:rgba(95,5,5,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">brown</div>
      <div style="background-color:rgba(255,13,13,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">brown1</div>
      <div style="background-color:rgba(218,11,11,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">brown2</div>
      <div style="background-color:rgba(155,8,8,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">brown3</div>
      <div style="background-color:rgba(65,4,4,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">brown4</div>
      <div style="background-color:rgba(186,122,61,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">burlywood</div>
      <div style="background-color:rgba(255,166,83,1.0);padding:10px;border-radius:5px;color:rgba(0,0,0);">burlywood1</div>
      <div style="background-color:rgba(218,142,72,1.0);padding:10px;border-radius:5px;color:rgba(0,0,0);">burlywood2</div>
      <div style="background-color:rgba(155,102,52,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">burlywood3</div>
      <div style="background-color:rgba(65,43,23,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">burlywood4</div>
      <div style="background-color:rgba(29,87,89,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">cadetblue</div>
      <div style="background-color:rgba(80,232,255,1.0);padding:10px;border-radius:5px;color:rgba(0,0,0);">cadetblue1</div>
      <div style="background-color:rgba(68,199,218,1.0);padding:10px;border-radius:5px;color:rgba(0,0,0);">cadetblue2</div>
      <div style="background-color:rgba(49,142,155,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">cadetblue3</div>
      <div style="background-color:rgba(22,60,65,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">cadetblue4</div>
      <div style="background-color:rgba(54,255,0,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">chartreuse</div>
      <div style="background-color:rgba(54,255,0,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">chartreuse1</div>
      <div style="background-color:rgba(46,218,0,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">chartreuse2</div>
      <div style="background-color:rgba(33,155,0,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">chartreuse3</div>
      <div style="background-color:rgba(15,65,0,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">chartreuse4</div>
      <div style="background-color:rgba(164,36,3,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">chocolate</div>
      <div style="background-color:rgba(255,54,4,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">chocolate1</div>
      <div style="background-color:rgba(218,46,3,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">chocolate2</div>
      <div style="background-color:rgba(155,33,3,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">chocolate3</div>
      <div style="background-color:rgba(65,15,1,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">chocolate4</div>
      <div style="background-color:rgba(255,54,20,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">coral</div>
      <div style="background-color:rgba(255,42,23,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">coral1</div>
      <div style="background-color:rgba(218,36,20,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">coral2</div>
      <div style="background-color:rgba(155,26,15,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">coral3</div>
      <div style="background-color:rgba(65,12,7,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">coral4</div>
      <div style="background-color:rgba(32,76,215,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">cornflowerblue</div>
      <div style="background-color:rgba(255,239,182,1.0);padding:10px;border-radius:5px;color:rgba(0,0,0);">cornsilk1</div>
      <div style="background-color:rgba(218,205,155,1.0);padding:10px;border-radius:5px;color:rgba(0,0,0);">cornsilk2</div>
      <div style="background-color:rgba(155,147,112,1.0);padding:10px;border-radius:5px;color:rgba(0,0,0);">cornsilk3</div>
      <div style="background-color:rgba(65,62,47,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">cornsilk4</div>
      <div style="background-color:rgba(0,255,255,1.0);padding:10px;border-radius:5px;color:rgba(0,0,0);">cyan</div>
      <div style="background-color:rgba(0,255,255,1.0);padding:10px;border-radius:5px;color:rgba(0,0,0);">cyan1</div>
      <div style="background-color:rgba(0,218,218,1.0);padding:10px;border-radius:5px;color:rgba(0,0,0);">cyan2</div>
      <div style="background-color:rgba(0,155,155,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">cyan3</div>
      <div style="background-color:rgba(0,65,65,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">cyan4</div>
      <div style="background-color:rgba(122,60,0,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">darkgoldenrod</div>
      <div style="background-color:rgba(255,123,1,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">darkgoldenrod1</div>
      <div style="background-color:rgba(218,106,1,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">darkgoldenrod2</div>
      <div style="background-color:rgba(155,76,0,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">darkgoldenrod3</div>
      <div style="background-color:rgba(65,33,0,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">darkgoldenrod4</div>
      <div style="background-color:rgba(0,32,0,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">darkgreen</div>
      <div style="background-color:rgba(129,120,37,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">darkkhaki</div>
      <div style="background-color:rgba(23,37,7,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">darkolivegreen</div>
      <div style="background-color:rgba(150,255,41,1.0);padding:10px;border-radius:5px;color:rgba(0,0,0);">darkolivegreen1</div>
      <div style="background-color:rgba(128,218,35,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">darkolivegreen2</div>
      <div style="background-color:rgba(92,155,26,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">darkolivegreen3</div>
      <div style="background-color:rgba(39,65,11,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">darkolivegreen4</div>
      <div style="background-color:rgba(255,66,0,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">darkorange</div>
      <div style="background-color:rgba(255,54,0,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">darkorange1</div>
      <div style="background-color:rgba(218,46,0,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">darkorange2</div>
      <div style="background-color:rgba(155,33,0,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">darkorange3</div>
      <div style="background-color:rgba(65,15,0,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">darkorange4</div>
      <div style="background-color:rgba(81,8,153,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">darkorchid</div>
      <div style="background-color:rgba(132,12,255,1.0);padding:10px;border-radius:5px;color:rgba(0,0,0);">darkorchid1</div>
      <div style="background-color:rgba(113,10,218,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">darkorchid2</div>
      <div style="background-color:rgba(82,8,155,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">darkorchid3</div>
      <div style="background-color:rgba(35,4,65,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">darkorchid4</div>
      <div style="background-color:rgba(207,77,49,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">darksalmon</div>
      <div style="background-color:rgba(70,128,70,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">darkseagreen</div>
      <div style="background-color:rgba(135,255,135,1.0);padding:10px;border-radius:5px;color:rgba(0,0,0);">darkseagreen1</div>
      <div style="background-color:rgba(116,218,116,1.0);padding:10px;border-radius:5px;color:rgba(0,0,0);">darkseagreen2</div>
      <div style="background-color:rgba(83,155,83,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">darkseagreen3</div>
      <div style="background-color:rgba(36,65,36,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">darkseagreen4</div>
      <div style="background-color:rgba(16,11,65,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">darkslateblue</div>
      <div style="background-color:rgba(7,19,19,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">darkslategray</div>
      <div style="background-color:rgba(78,255,255,1.0);padding:10px;border-radius:5px;color:rgba(0,0,0);">darkslategray1</div>
      <div style="background-color:rgba(67,218,218,1.0);padding:10px;border-radius:5px;color:rgba(0,0,0);">darkslategray2</div>
      <div style="background-color:rgba(48,155,155,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">darkslategray3</div>
      <div style="background-color:rgba(21,65,65,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">darkslategray4</div>
      <div style="background-color:rgba(0,157,162,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">darkturquoise</div>
      <div style="background-color:rgba(75,0,166,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">darkviolet</div>
      <div style="background-color:rgba(255,1,74,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">deeppink</div>
      <div style="background-color:rgba(218,1,63,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">deeppink2</div>
      <div style="background-color:rgba(155,1,46,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">deeppink3</div>
      <div style="background-color:rgba(65,0,20,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">deeppink4</div>
      <div style="background-color:rgba(0,132,255,1.0);padding:10px;border-radius:5px;color:rgba(0,0,0);">deepskyblue1</div>
      <div style="background-color:rgba(0,113,218,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">deepskyblue2</div>
      <div style="background-color:rgba(0,82,155,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">deepskyblue3</div>
      <div style="background-color:rgba(0,35,65,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">deepskyblue4</div>
      <div style="background-color:rgba(3,71,255,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">dodgerblue1</div>
      <div style="background-color:rgba(2,60,218,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">dodgerblue2</div>
      <div style="background-color:rgba(2,44,155,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">dodgerblue3</div>
      <div style="background-color:rgba(1,19,65,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">dodgerblue4</div>
      <div style="background-color:rgba(113,4,4,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">firebrick</div>
      <div style="background-color:rgba(255,7,7,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">firebrick1</div>
      <div style="background-color:rgba(218,6,6,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">firebrick2</div>
      <div style="background-color:rgba(155,4,4,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">firebrick3</div>
      <div style="background-color:rgba(65,2,2,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">firebrick4</div>
      <div style="background-color:rgba(255,243,222,1.0);padding:10px;border-radius:5px;color:rgba(0,0,0);">floralwhite</div>
      <div style="background-color:rgba(4,65,4,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">forestgreen</div>
      <div style="background-color:rgba(182,182,182,1.0);padding:10px;border-radius:5px;color:rgba(0,0,0);">gainsboro</div>
      <div style="background-color:rgba(239,239,255,1.0);padding:10px;border-radius:5px;color:rgba(0,0,0);">ghostwhite</div>
      <div style="background-color:rgba(255,173,0,1.0);padding:10px;border-radius:5px;color:rgba(0,0,0);">gold</div>
      <div style="background-color:rgba(255,173,0,1.0);padding:10px;border-radius:5px;color:rgba(0,0,0);">gold1</div>
      <div style="background-color:rgba(218,148,0,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">gold2</div>
      <div style="background-color:rgba(155,106,0,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">gold3</div>
      <div style="background-color:rgba(65,45,0,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">gold4</div>
      <div style="background-color:rgba(178,95,3,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">goldenrod</div>
      <div style="background-color:rgba(255,135,4,1.0);padding:10px;border-radius:5px;color:rgba(0,0,0);">goldenrod1</div>
      <div style="background-color:rgba(218,116,4,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">goldenrod2</div>
      <div style="background-color:rgba(155,83,3,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">goldenrod3</div>
      <div style="background-color:rgba(65,36,1,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">goldenrod4</div>
      <div style="background-color:rgba(134,134,134,1.0);padding:10px;border-radius:5px;color:rgba(0,0,0);">gray</div>
      <div style="background-color:rgba(0,0,0,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">gray0</div>
      <div style="background-color:rgba(0,0,0,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">gray1</div>
      <div style="background-color:rgba(2,2,2,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">gray10</div>
      <div style="background-color:rgba(2,2,2,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">gray11</div>
      <div style="background-color:rgba(3,3,3,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">gray12</div>
      <div style="background-color:rgba(3,3,3,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">gray13</div>
      <div style="background-color:rgba(4,4,4,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">gray14</div>
      <div style="background-color:rgba(4,4,4,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">gray15</div>
      <div style="background-color:rgba(5,5,5,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">gray16</div>
      <div style="background-color:rgba(6,6,6,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">gray17</div>
      <div style="background-color:rgba(6,6,6,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">gray18</div>
      <div style="background-color:rgba(7,7,7,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">gray19</div>
      <div style="background-color:rgba(0,0,0,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">gray2</div>
      <div style="background-color:rgba(8,8,8,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">gray20</div>
      <div style="background-color:rgba(9,9,9,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">gray21</div>
      <div style="background-color:rgba(10,10,10,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">gray22</div>
      <div style="background-color:rgba(11,11,11,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">gray23</div>
      <div style="background-color:rgba(11,11,11,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">gray24</div>
      <div style="background-color:rgba(13,13,13,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">gray25</div>
      <div style="background-color:rgba(13,13,13,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">gray26</div>
      <div style="background-color:rgba(15,15,15,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">gray27</div>
      <div style="background-color:rgba(16,16,16,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">gray28</div>
      <div style="background-color:rgba(17,17,17,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">gray29</div>
      <div style="background-color:rgba(0,0,0,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">gray3</div>
      <div style="background-color:rgba(18,18,18,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">gray30</div>
      <div style="background-color:rgba(19,19,19,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">gray31</div>
      <div style="background-color:rgba(21,21,21,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">gray32</div>
      <div style="background-color:rgba(22,22,22,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">gray33</div>
      <div style="background-color:rgba(24,24,24,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">gray34</div>
      <div style="background-color:rgba(25,25,25,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">gray35</div>
      <div style="background-color:rgba(27,27,27,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">gray36</div>
      <div style="background-color:rgba(28,28,28,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">gray37</div>
      <div style="background-color:rgba(30,30,30,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">gray38</div>
      <div style="background-color:rgba(31,31,31,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">gray39</div>
      <div style="background-color:rgba(0,0,0,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">gray4</div>
      <div style="background-color:rgba(33,33,33,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">gray40</div>
      <div style="background-color:rgba(36,36,36,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">gray41</div>
      <div style="background-color:rgba(37,37,37,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">gray42</div>
      <div style="background-color:rgba(39,39,39,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">gray43</div>
      <div style="background-color:rgba(41,41,41,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">gray44</div>
      <div style="background-color:rgba(43,43,43,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">gray45</div>
      <div style="background-color:rgba(45,45,45,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">gray46</div>
      <div style="background-color:rgba(47,47,47,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">gray47</div>
      <div style="background-color:rgba(49,49,49,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">gray48</div>
      <div style="background-color:rgba(52,52,52,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">gray49</div>
      <div style="background-color:rgba(1,1,1,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">gray5</div>
      <div style="background-color:rgba(54,54,54,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">gray50</div>
      <div style="background-color:rgba(56,56,56,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">gray51</div>
      <div style="background-color:rgba(59,59,59,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">gray52</div>
      <div style="background-color:rgba(61,61,61,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">gray53</div>
      <div style="background-color:rgba(64,64,64,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">gray54</div>
      <div style="background-color:rgba(66,66,66,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">gray55</div>
      <div style="background-color:rgba(70,70,70,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">gray56</div>
      <div style="background-color:rgba(72,72,72,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">gray57</div>
      <div style="background-color:rgba(75,75,75,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">gray58</div>
      <div style="background-color:rgba(77,77,77,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">gray59</div>
      <div style="background-color:rgba(1,1,1,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">gray6</div>
      <div style="background-color:rgba(81,81,81,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">gray60</div>
      <div style="background-color:rgba(84,84,84,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">gray61</div>
      <div style="background-color:rgba(87,87,87,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">gray62</div>
      <div style="background-color:rgba(90,90,90,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">gray63</div>
      <div style="background-color:rgba(93,93,93,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">gray64</div>
      <div style="background-color:rgba(97,97,97,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">gray65</div>
      <div style="background-color:rgba(99,99,99,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">gray66</div>
      <div style="background-color:rgba(103,103,103,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">gray67</div>
      <div style="background-color:rgba(106,106,106,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">gray68</div>
      <div style="background-color:rgba(110,110,110,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">gray69</div>
      <div style="background-color:rgba(1,1,1,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">gray7</div>
      <div style="background-color:rgba(114,114,114,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">gray70</div>
      <div style="background-color:rgba(117,117,117,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">gray71</div>
      <div style="background-color:rgba(122,122,122,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">gray72</div>
      <div style="background-color:rgba(125,125,125,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">gray73</div>
      <div style="background-color:rgba(129,129,129,1.0);padding:10px;border-radius:5px;color:rgba(0,0,0);">gray74</div>
      <div style="background-color:rgba(132,132,132,1.0);padding:10px;border-radius:5px;color:rgba(0,0,0);">gray75</div>
      <div style="background-color:rgba(137,137,137,1.0);padding:10px;border-radius:5px;color:rgba(0,0,0);">gray76</div>
      <div style="background-color:rgba(140,140,140,1.0);padding:10px;border-radius:5px;color:rgba(0,0,0);">gray77</div>
      <div style="background-color:rgba(145,145,145,1.0);padding:10px;border-radius:5px;color:rgba(0,0,0);">gray78</div>
      <div style="background-color:rgba(148,148,148,1.0);padding:10px;border-radius:5px;color:rgba(0,0,0);">gray79</div>
      <div style="background-color:rgba(1,1,1,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">gray8</div>
      <div style="background-color:rgba(153,153,153,1.0);padding:10px;border-radius:5px;color:rgba(0,0,0);">gray80</div>
      <div style="background-color:rgba(159,159,159,1.0);padding:10px;border-radius:5px;color:rgba(0,0,0);">gray81</div>
      <div style="background-color:rgba(162,162,162,1.0);padding:10px;border-radius:5px;color:rgba(0,0,0);">gray82</div>
      <div style="background-color:rgba(167,167,167,1.0);padding:10px;border-radius:5px;color:rgba(0,0,0);">gray83</div>
      <div style="background-color:rgba(176,176,176,1.0);padding:10px;border-radius:5px;color:rgba(0,0,0);">gray85</div>
      <div style="background-color:rgba(180,180,180,1.0);padding:10px;border-radius:5px;color:rgba(0,0,0);">gray86</div>
      <div style="background-color:rgba(186,186,186,1.0);padding:10px;border-radius:5px;color:rgba(0,0,0);">gray87</div>
      <div style="background-color:rgba(190,190,190,1.0);padding:10px;border-radius:5px;color:rgba(0,0,0);">gray88</div>
      <div style="background-color:rgba(195,195,195,1.0);padding:10px;border-radius:5px;color:rgba(0,0,0);">gray89</div>
      <div style="background-color:rgba(2,2,2,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">gray9</div>
      <div style="background-color:rgba(199,199,199,1.0);padding:10px;border-radius:5px;color:rgba(0,0,0);">gray90</div>
      <div style="background-color:rgba(205,205,205,1.0);padding:10px;border-radius:5px;color:rgba(0,0,0);">gray91</div>
      <div style="background-color:rgba(211,211,211,1.0);padding:10px;border-radius:5px;color:rgba(0,0,0);">gray92</div>
      <div style="background-color:rgba(215,215,215,1.0);padding:10px;border-radius:5px;color:rgba(0,0,0);">gray93</div>
      <div style="background-color:rgba(222,222,222,1.0);padding:10px;border-radius:5px;color:rgba(0,0,0);">gray94</div>
      <div style="background-color:rgba(226,226,226,1.0);padding:10px;border-radius:5px;color:rgba(0,0,0);">gray95</div>
      <div style="background-color:rgba(237,237,237,1.0);padding:10px;border-radius:5px;color:rgba(0,0,0);">gray97</div>
      <div style="background-color:rgba(243,243,243,1.0);padding:10px;border-radius:5px;color:rgba(0,0,0);">gray98</div>
      <div style="background-color:rgba(248,248,248,1.0);padding:10px;border-radius:5px;color:rgba(0,0,0);">gray99</div>
      <div style="background-color:rgba(0,255,0,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">green</div>
      <div style="background-color:rgba(0,255,0,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">green1</div>
      <div style="background-color:rgba(0,218,0,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">green2</div>
      <div style="background-color:rgba(0,155,0,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">green3</div>
      <div style="background-color:rgba(0,65,0,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">green4</div>
      <div style="background-color:rgba(106,255,7,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">greenyellow</div>
      <div style="background-color:rgba(222,255,222,1.0);padding:10px;border-radius:5px;color:rgba(0,0,0);">honeydew</div>
      <div style="background-color:rgba(190,218,190,1.0);padding:10px;border-radius:5px;color:rgba(0,0,0);">honeydew2</div>
      <div style="background-color:rgba(135,155,135,1.0);padding:10px;border-radius:5px;color:rgba(0,0,0);">honeydew3</div>
      <div style="background-color:rgba(57,65,57,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">honeydew4</div>
      <div style="background-color:rgba(255,36,116,1.0);padding:10px;border-radius:5px;color:rgba(0,0,0);">hotpink</div>
      <div style="background-color:rgba(255,39,116,1.0);padding:10px;border-radius:5px;color:rgba(0,0,0);">hotpink1</div>
      <div style="background-color:rgba(218,36,98,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">hotpink2</div>
      <div style="background-color:rgba(155,29,71,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">hotpink3</div>
      <div style="background-color:rgba(65,10,31,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">hotpink4</div>
      <div style="background-color:rgba(155,27,27,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">indianred</div>
      <div style="background-color:rgba(255,36,36,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">indianred1</div>
      <div style="background-color:rgba(218,31,31,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">indianred2</div>
      <div style="background-color:rgba(155,23,23,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">indianred3</div>
      <div style="background-color:rgba(65,10,10,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">indianred4</div>
      <div style="background-color:rgba(255,255,222,1.0);padding:10px;border-radius:5px;color:rgba(0,0,0);">ivory</div>
      <div style="background-color:rgba(218,218,190,1.0);padding:10px;border-radius:5px;color:rgba(0,0,0);">ivory2</div>
      <div style="background-color:rgba(155,155,135,1.0);padding:10px;border-radius:5px;color:rgba(0,0,0);">ivory3</div>
      <div style="background-color:rgba(65,65,57,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">ivory4</div>
      <div style="background-color:rgba(222,201,66,1.0);padding:10px;border-radius:5px;color:rgba(0,0,0);">khaki</div>
      <div style="background-color:rgba(255,235,70,1.0);padding:10px;border-radius:5px;color:rgba(0,0,0);">khaki1</div>
      <div style="background-color:rgba(218,201,59,1.0);padding:10px;border-radius:5px;color:rgba(0,0,0);">khaki2</div>
      <div style="background-color:rgba(155,144,43,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">khaki3</div>
      <div style="background-color:rgba(65,60,19,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">khaki4</div>
      <div style="background-color:rgba(201,201,243,1.0);padding:10px;border-radius:5px;color:rgba(0,0,0);">lavender</div>
      <div style="background-color:rgba(255,222,232,1.0);padding:10px;border-radius:5px;color:rgba(0,0,0);">lavenderblush1</div>
      <div style="background-color:rgba(218,190,199,1.0);padding:10px;border-radius:5px;color:rgba(0,0,0);">lavenderblush2</div>
      <div style="background-color:rgba(155,135,142,1.0);padding:10px;border-radius:5px;color:rgba(0,0,0);">lavenderblush3</div>
      <div style="background-color:rgba(65,57,60,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">lavenderblush4</div>
      <div style="background-color:rgba(51,248,0,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">lawngreen</div>
      <div style="background-color:rgba(255,243,155,1.0);padding:10px;border-radius:5px;color:rgba(0,0,0);">lemonchiffon1</div>
      <div style="background-color:rgba(218,207,132,1.0);padding:10px;border-radius:5px;color:rgba(0,0,0);">lemonchiffon2</div>
      <div style="background-color:rgba(155,148,95,1.0);padding:10px;border-radius:5px;color:rgba(0,0,0);">lemonchiffon3</div>
      <div style="background-color:rgba(65,63,41,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">lemonchiffon4</div>
      <div style="background-color:rgba(106,175,201,1.0);padding:10px;border-radius:5px;color:rgba(0,0,0);">lightblue</div>
      <div style="background-color:rgba(132,220,255,1.0);padding:10px;border-radius:5px;color:rgba(0,0,0);">lightblue1</div>
      <div style="background-color:rgba(113,188,218,1.0);padding:10px;border-radius:5px;color:rgba(0,0,0);">lightblue2</div>
      <div style="background-color:rgba(82,134,155,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">lightblue3</div>
      <div style="background-color:rgba(35,57,65,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">lightblue4</div>
      <div style="background-color:rgba(222,55,55,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">lightcoral</div>
      <div style="background-color:rgba(190,255,255,1.0);padding:10px;border-radius:5px;color:rgba(0,0,0);">lightcyan</div>
      <div style="background-color:rgba(190,255,255,1.0);padding:10px;border-radius:5px;color:rgba(0,0,0);">lightcyan1</div>
      <div style="background-color:rgba(162,218,218,1.0);padding:10px;border-radius:5px;color:rgba(0,0,0);">lightcyan2</div>
      <div style="background-color:rgba(116,155,155,1.0);padding:10px;border-radius:5px;color:rgba(0,0,0);">lightcyan3</div>
      <div style="background-color:rgba(49,65,65,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">lightcyan4</div>
      <div style="background-color:rgba(218,184,56,1.0);padding:10px;border-radius:5px;color:rgba(0,0,0);">lightgoldenrod</div>
      <div style="background-color:rgba(255,213,65,1.0);padding:10px;border-radius:5px;color:rgba(0,0,0);">lightgoldenrod1</div>
      <div style="background-color:rgba(218,182,56,1.0);padding:10px;border-radius:5px;color:rgba(0,0,0);">lightgoldenrod2</div>
      <div style="background-color:rgba(155,131,41,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">lightgoldenrod3</div>
      <div style="background-color:rgba(65,55,18,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">lightgoldenrod4</div>
      <div style="background-color:rgba(243,243,164,1.0);padding:10px;border-radius:5px;color:rgba(0,0,0);">lightgoldenrodyellow</div>
      <div style="background-color:rgba(166,166,166,1.0);padding:10px;border-radius:5px;color:rgba(0,0,0);">lightgray</div>
      <div style="background-color:rgba(255,119,135,1.0);padding:10px;border-radius:5px;color:rgba(0,0,0);">lightpink</div>
      <div style="background-color:rgba(255,107,123,1.0);padding:10px;border-radius:5px;color:rgba(0,0,0);">lightpink1</div>
      <div style="background-color:rgba(218,92,106,1.0);padding:10px;border-radius:5px;color:rgba(0,0,0);">lightpink2</div>
      <div style="background-color:rgba(155,66,76,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">lightpink3</div>
      <div style="background-color:rgba(65,29,33,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">lightpink4</div>
      <div style="background-color:rgba(255,89,49,1.0);padding:10px;border-radius:5px;color:rgba(0,0,0);">lightsalmon1</div>
      <div style="background-color:rgba(218,76,42,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">lightsalmon2</div>
      <div style="background-color:rgba(155,55,31,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">lightsalmon3</div>
      <div style="background-color:rgba(65,24,13,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">lightsalmon4</div>
      <div style="background-color:rgba(3,113,102,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">lightseagreen</div>
      <div style="background-color:rgba(61,157,243,1.0);padding:10px;border-radius:5px;color:rgba(0,0,0);">lightskyblue</div>
      <div style="background-color:rgba(110,193,255,1.0);padding:10px;border-radius:5px;color:rgba(0,0,0);">lightskyblue1</div>
      <div style="background-color:rgba(94,166,218,1.0);padding:10px;border-radius:5px;color:rgba(0,0,0);">lightskyblue2</div>
      <div style="background-color:rgba(67,119,155,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">lightskyblue3</div>
      <div style="background-color:rgba(29,50,65,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">lightskyblue4</div>
      <div style="background-color:rgba(58,41,255,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">lightslateblue</div>
      <div style="background-color:rgba(47,62,81,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">lightslategray</div>
      <div style="background-color:rgba(110,140,186,1.0);padding:10px;border-radius:5px;color:rgba(0,0,0);">lightsteelblue</div>
      <div style="background-color:rgba(150,192,255,1.0);padding:10px;border-radius:5px;color:rgba(0,0,0);">lightsteelblue1</div>
      <div style="background-color:rgba(128,164,218,1.0);padding:10px;border-radius:5px;color:rgba(0,0,0);">lightsteelblue2</div>
      <div style="background-color:rgba(92,117,155,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">lightsteelblue3</div>
      <div style="background-color:rgba(39,50,65,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">lightsteelblue4</div>
      <div style="background-color:rgba(255,255,190,1.0);padding:10px;border-radius:5px;color:rgba(0,0,0);">lightyellow</div>
      <div style="background-color:rgba(218,218,162,1.0);padding:10px;border-radius:5px;color:rgba(0,0,0);">lightyellow2</div>
      <div style="background-color:rgba(155,155,116,1.0);padding:10px;border-radius:5px;color:rgba(0,0,0);">lightyellow3</div>
      <div style="background-color:rgba(65,65,49,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">lightyellow4</div>
      <div style="background-color:rgba(8,155,8,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">limegreen</div>
      <div style="background-color:rgba(243,222,201,1.0);padding:10px;border-radius:5px;color:rgba(0,0,0);">linen</div>
      <div style="background-color:rgba(255,0,255,1.0);padding:10px;border-radius:5px;color:rgba(0,0,0);">magenta</div>
      <div style="background-color:rgba(255,0,255,1.0);padding:10px;border-radius:5px;color:rgba(0,0,0);">magenta1</div>
      <div style="background-color:rgba(218,0,218,1.0);padding:10px;border-radius:5px;color:rgba(0,0,0);">magenta2</div>
      <div style="background-color:rgba(155,0,155,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">magenta3</div>
      <div style="background-color:rgba(65,0,65,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">magenta4</div>
      <div style="background-color:rgba(110,7,29,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">maroon</div>
      <div style="background-color:rgba(255,8,114,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">maroon1</div>
      <div style="background-color:rgba(218,7,98,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">maroon2</div>
      <div style="background-color:rgba(155,5,71,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">maroon3</div>
      <div style="background-color:rgba(65,2,31,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">maroon4</div>
      <div style="background-color:rgba(0,0,133,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">matrablue</div>
      <div style="background-color:rgba(81,81,81,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">matragray</div>
      <div style="background-color:rgba(33,155,102,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">mediumaquamarine</div>
      <div style="background-color:rgba(125,23,166,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">mediumorchid</div>
      <div style="background-color:rgba(190,33,255,1.0);padding:10px;border-radius:5px;color:rgba(0,0,0);">mediumorchid1</div>
      <div style="background-color:rgba(162,29,218,1.0);padding:10px;border-radius:5px;color:rgba(0,0,0);">mediumorchid2</div>
      <div style="background-color:rgba(116,21,155,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">mediumorchid3</div>
      <div style="background-color:rgba(49,9,65,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">mediumorchid4</div>
      <div style="background-color:rgba(74,41,180,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">mediumpurple</div>
      <div style="background-color:rgba(103,56,255,1.0);padding:10px;border-radius:5px;color:rgba(0,0,0);">mediumpurple1</div>
      <div style="background-color:rgba(88,48,218,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">mediumpurple2</div>
      <div style="background-color:rgba(63,35,155,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">mediumpurple3</div>
      <div style="background-color:rgba(27,16,65,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">mediumpurple4</div>
      <div style="background-color:rgba(11,114,42,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">mediumseagreen</div>
      <div style="background-color:rgba(50,35,218,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">mediumslateblue</div>
      <div style="background-color:rgba(0,243,82,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">mediumspringgreen</div>
      <div style="background-color:rgba(16,162,153,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">mediumturquoise</div>
      <div style="background-color:rgba(145,1,59,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">mediumvioletred</div>
      <div style="background-color:rgba(2,2,41,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">midnightblue</div>
      <div style="background-color:rgba(232,255,243,1.0);padding:10px;border-radius:5px;color:rgba(0,0,0);">mintcream</div>
      <div style="background-color:rgba(255,197,192,1.0);padding:10px;border-radius:5px;color:rgba(0,0,0);">mistyrose</div>
      <div style="background-color:rgba(218,169,164,1.0);padding:10px;border-radius:5px;color:rgba(0,0,0);">mistyrose2</div>
      <div style="background-color:rgba(155,120,117,1.0);padding:10px;border-radius:5px;color:rgba(0,0,0);">mistyrose3</div>
      <div style="background-color:rgba(65,52,50,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">mistyrose4</div>
      <div style="background-color:rgba(255,197,117,1.0);padding:10px;border-radius:5px;color:rgba(0,0,0);">moccasin</div>
      <div style="background-color:rgba(255,186,106,1.0);padding:10px;border-radius:5px;color:rgba(0,0,0);">navajowhite1</div>
      <div style="background-color:rgba(218,159,90,1.0);padding:10px;border-radius:5px;color:rgba(0,0,0);">navajowhite2</div>
      <div style="background-color:rgba(155,114,65,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">navajowhite3</div>
      <div style="background-color:rgba(65,48,28,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">navajowhite4</div>
      <div style="background-color:rgba(0,0,55,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">navyblue</div>
      <div style="background-color:rgba(250,232,201,1.0);padding:10px;border-radius:5px;color:rgba(0,0,0);">oldlace</div>
      <div style="background-color:rgba(37,68,4,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">olivedrab</div>
      <div style="background-color:rgba(134,255,12,1.0);padding:10px;border-radius:5px;color:rgba(0,0,0);">olivedrab1</div>
      <div style="background-color:rgba(114,218,10,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">olivedrab2</div>
      <div style="background-color:rgba(82,155,8,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">olivedrab3</div>
      <div style="background-color:rgba(36,65,4,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">olivedrab4</div>
      <div style="background-color:rgba(255,95,0,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">orange</div>
      <div style="background-color:rgba(255,95,0,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">orange1</div>
      <div style="background-color:rgba(218,82,0,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">orange2</div>
      <div style="background-color:rgba(155,59,0,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">orange3</div>
      <div style="background-color:rgba(65,26,0,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">orange4</div>
      <div style="background-color:rgba(255,15,0,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">orangered</div>
      <div style="background-color:rgba(255,15,0,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">orangered1</div>
      <div style="background-color:rgba(218,13,0,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">orangered2</div>
      <div style="background-color:rgba(155,9,0,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">orangered3</div>
      <div style="background-color:rgba(65,4,0,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">orangered4</div>
      <div style="background-color:rgba(178,41,171,1.0);padding:10px;border-radius:5px;color:rgba(0,0,0);">orchid</div>
      <div style="background-color:rgba(255,57,243,1.0);padding:10px;border-radius:5px;color:rgba(0,0,0);">orchid1</div>
      <div style="background-color:rgba(218,49,207,1.0);padding:10px;border-radius:5px;color:rgba(0,0,0);">orchid2</div>
      <div style="background-color:rgba(155,36,148,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">orchid3</div>
      <div style="background-color:rgba(65,16,63,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">orchid4</div>
      <div style="background-color:rgba(218,205,102,1.0);padding:10px;border-radius:5px;color:rgba(0,0,0);">palegoldenrod</div>
      <div style="background-color:rgba(80,245,80,1.0);padding:10px;border-radius:5px;color:rgba(0,0,0);">palegreen</div>
      <div style="background-color:rgba(82,255,82,1.0);padding:10px;border-radius:5px;color:rgba(0,0,0);">palegreen1</div>
      <div style="background-color:rgba(71,218,71,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">palegreen2</div>
      <div style="background-color:rgba(51,155,51,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">palegreen3</div>
      <div style="background-color:rgba(22,65,22,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">palegreen4</div>
      <div style="background-color:rgba(109,218,218,1.0);padding:10px;border-radius:5px;color:rgba(0,0,0);">paleturquoise</div>
      <div style="background-color:rgba(126,255,255,1.0);padding:10px;border-radius:5px;color:rgba(0,0,0);">paleturquoise1</div>
      <div style="background-color:rgba(107,218,218,1.0);padding:10px;border-radius:5px;color:rgba(0,0,0);">paleturquoise2</div>
      <div style="background-color:rgba(77,155,155,1.0);padding:10px;border-radius:5px;color:rgba(0,0,0);">paleturquoise3</div>
      <div style="background-color:rgba(33,65,65,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">paleturquoise4</div>
      <div style="background-color:rgba(180,41,74,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">palevioletred</div>
      <div style="background-color:rgba(255,56,103,1.0);padding:10px;border-radius:5px;color:rgba(0,0,0);">palevioletred1</div>
      <div style="background-color:rgba(218,48,88,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">palevioletred2</div>
      <div style="background-color:rgba(155,35,63,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">palevioletred3</div>
      <div style="background-color:rgba(65,16,27,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">palevioletred4</div>
      <div style="background-color:rgba(255,220,169,1.0);padding:10px;border-radius:5px;color:rgba(0,0,0);">papayawhip</div>
      <div style="background-color:rgba(255,178,123,1.0);padding:10px;border-radius:5px;color:rgba(0,0,0);">peachpuff</div>
      <div style="background-color:rgba(218,152,106,1.0);padding:10px;border-radius:5px;color:rgba(0,0,0);">peachpuff2</div>
      <div style="background-color:rgba(155,109,76,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">peachpuff3</div>
      <div style="background-color:rgba(65,47,33,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">peachpuff4</div>
      <div style="background-color:rgba(155,59,12,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">peru</div>
      <div style="background-color:rgba(255,134,152,1.0);padding:10px;border-radius:5px;color:rgba(0,0,0);">pink</div>
      <div style="background-color:rgba(255,117,142,1.0);padding:10px;border-radius:5px;color:rgba(0,0,0);">pink1</div>
      <div style="background-color:rgba(218,101,122,1.0);padding:10px;border-radius:5px;color:rgba(0,0,0);">pink2</div>
      <div style="background-color:rgba(155,72,87,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">pink3</div>
      <div style="background-color:rgba(65,31,38,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">pink4</div>
      <div style="background-color:rgba(184,89,184,1.0);padding:10px;border-radius:5px;color:rgba(0,0,0);">plum</div>
      <div style="background-color:rgba(255,126,255,1.0);padding:10px;border-radius:5px;color:rgba(0,0,0);">plum1</div>
      <div style="background-color:rgba(218,107,218,1.0);padding:10px;border-radius:5px;color:rgba(0,0,0);">plum2</div>
      <div style="background-color:rgba(155,77,155,1.0);padding:10px;border-radius:5px;color:rgba(0,0,0);">plum3</div>
      <div style="background-color:rgba(65,33,65,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">plum4</div>
      <div style="background-color:rgba(110,190,201,1.0);padding:10px;border-radius:5px;color:rgba(0,0,0);">powderblue</div>
      <div style="background-color:rgba(89,3,222,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">purple</div>
      <div style="background-color:rgba(83,7,255,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">purple1</div>
      <div style="background-color:rgba(72,6,218,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">purple2</div>
      <div style="background-color:rgba(52,4,155,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">purple3</div>
      <div style="background-color:rgba(23,2,65,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">purple4</div>
      <div style="background-color:rgba(255,0,0,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">red</div>
      <div style="background-color:rgba(255,0,0,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">red1</div>
      <div style="background-color:rgba(218,0,0,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">red2</div>
      <div style="background-color:rgba(155,0,0,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">red3</div>
      <div style="background-color:rgba(65,0,0,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">red4</div>
      <div style="background-color:rgba(128,70,70,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">rosybrown</div>
      <div style="background-color:rgba(255,135,135,1.0);padding:10px;border-radius:5px;color:rgba(0,0,0);">rosybrown1</div>
      <div style="background-color:rgba(218,116,116,1.0);padding:10px;border-radius:5px;color:rgba(0,0,0);">rosybrown2</div>
      <div style="background-color:rgba(155,83,83,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">rosybrown3</div>
      <div style="background-color:rgba(65,36,36,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">rosybrown4</div>
      <div style="background-color:rgba(13,36,192,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">royalblue</div>
      <div style="background-color:rgba(16,46,255,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">royalblue1</div>
      <div style="background-color:rgba(14,39,218,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">royalblue2</div>
      <div style="background-color:rgba(10,29,155,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">royalblue3</div>
      <div style="background-color:rgba(5,13,65,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">royalblue4</div>
      <div style="background-color:rgba(65,15,1,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">saddlebrown</div>
      <div style="background-color:rgba(243,55,42,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">salmon</div>
      <div style="background-color:rgba(255,66,36,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">salmon1</div>
      <div style="background-color:rgba(218,56,31,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">salmon2</div>
      <div style="background-color:rgba(155,41,22,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">salmon3</div>
      <div style="background-color:rgba(65,18,10,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">salmon4</div>
      <div style="background-color:rgba(230,94,29,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">sandybrown</div>
      <div style="background-color:rgba(6,65,24,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">seagreen</div>
      <div style="background-color:rgba(22,255,88,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">seagreen1</div>
      <div style="background-color:rgba(19,218,75,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">seagreen2</div>
      <div style="background-color:rgba(14,155,55,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">seagreen3</div>
      <div style="background-color:rgba(6,65,24,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">seagreen4</div>
      <div style="background-color:rgba(255,232,218,1.0);padding:10px;border-radius:5px;color:rgba(0,0,0);">seashell</div>
      <div style="background-color:rgba(218,199,186,1.0);padding:10px;border-radius:5px;color:rgba(0,0,0);">seashell2</div>
      <div style="background-color:rgba(155,142,132,1.0);padding:10px;border-radius:5px;color:rgba(0,0,0);">seashell3</div>
      <div style="background-color:rgba(65,60,56,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">seashell4</div>
      <div style="background-color:rgba(89,21,6,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">sienna</div>
      <div style="background-color:rgba(255,56,16,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">sienna1</div>
      <div style="background-color:rgba(218,48,13,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">sienna2</div>
      <div style="background-color:rgba(155,35,10,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">sienna3</div>
      <div style="background-color:rgba(65,16,4,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">sienna4</div>
      <div style="background-color:rgba(61,157,211,1.0);padding:10px;border-radius:5px;color:rgba(0,0,0);">skyblue</div>
      <div style="background-color:rgba(61,157,255,1.0);padding:10px;border-radius:5px;color:rgba(0,0,0);">skyblue1</div>
      <div style="background-color:rgba(53,134,218,1.0);padding:10px;border-radius:5px;color:rgba(0,0,0);">skyblue2</div>
      <div style="background-color:rgba(38,97,155,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">skyblue3</div>
      <div style="background-color:rgba(17,41,65,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">skyblue4</div>
      <div style="background-color:rgba(36,26,155,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">slateblue</div>
      <div style="background-color:rgba(57,40,255,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">slateblue1</div>
      <div style="background-color:rgba(49,34,218,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">slateblue2</div>
      <div style="background-color:rgba(36,25,155,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">slateblue3</div>
      <div style="background-color:rgba(16,11,65,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">slateblue4</div>
      <div style="background-color:rgba(41,55,71,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">slategray</div>
      <div style="background-color:rgba(144,193,255,1.0);padding:10px;border-radius:5px;color:rgba(0,0,0);">slategray1</div>
      <div style="background-color:rgba(123,166,218,1.0);padding:10px;border-radius:5px;color:rgba(0,0,0);">slategray2</div>
      <div style="background-color:rgba(88,119,155,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">slategray3</div>
      <div style="background-color:rgba(38,50,65,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">slategray4</div>
      <div style="background-color:rgba(255,243,243,1.0);padding:10px;border-radius:5px;color:rgba(0,0,0);">snow</div>
      <div style="background-color:rgba(218,207,207,1.0);padding:10px;border-radius:5px;color:rgba(0,0,0);">snow2</div>
      <div style="background-color:rgba(155,148,148,1.0);padding:10px;border-radius:5px;color:rgba(0,0,0);">snow3</div>
      <div style="background-color:rgba(65,63,63,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">snow4</div>
      <div style="background-color:rgba(0,255,54,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">springgreen</div>
      <div style="background-color:rgba(0,218,46,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">springgreen2</div>
      <div style="background-color:rgba(0,155,33,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">springgreen3</div>
      <div style="background-color:rgba(0,65,15,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">springgreen4</div>
      <div style="background-color:rgba(15,56,116,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">steelblue</div>
      <div style="background-color:rgba(31,122,255,1.0);padding:10px;border-radius:5px;color:rgba(0,0,0);">steelblue1</div>
      <div style="background-color:rgba(27,105,218,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">steelblue2</div>
      <div style="background-color:rgba(19,75,155,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">steelblue3</div>
      <div style="background-color:rgba(9,32,65,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">steelblue4</div>
      <div style="background-color:rgba(164,116,66,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">tan</div>
      <div style="background-color:rgba(255,95,19,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">tan1</div>
      <div style="background-color:rgba(218,82,16,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">tan2</div>
      <div style="background-color:rgba(155,59,12,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">tan3</div>
      <div style="background-color:rgba(65,26,6,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">tan4</div>
      <div style="background-color:rgba(10,68,68,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">teal</div>
      <div style="background-color:rgba(175,132,175,1.0);padding:10px;border-radius:5px;color:rgba(0,0,0);">thistle</div>
      <div style="background-color:rgba(255,192,255,1.0);padding:10px;border-radius:5px;color:rgba(0,0,0);">thistle1</div>
      <div style="background-color:rgba(218,164,218,1.0);padding:10px;border-radius:5px;color:rgba(0,0,0);">thistle2</div>
      <div style="background-color:rgba(155,117,155,1.0);padding:10px;border-radius:5px;color:rgba(0,0,0);">thistle3</div>
      <div style="background-color:rgba(65,50,65,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">thistle4</div>
      <div style="background-color:rgba(255,31,16,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">tomato</div>
      <div style="background-color:rgba(255,31,16,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">tomato1</div>
      <div style="background-color:rgba(218,27,13,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">tomato2</div>
      <div style="background-color:rgba(155,19,10,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">tomato3</div>
      <div style="background-color:rgba(65,9,4,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">tomato4</div>
      <div style="background-color:rgba(13,190,160,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">turquoise</div>
      <div style="background-color:rgba(0,232,255,1.0);padding:10px;border-radius:5px;color:rgba(0,0,0);">turquoise1</div>
      <div style="background-color:rgba(0,199,218,1.0);padding:10px;border-radius:5px;color:rgba(0,0,0);">turquoise2</div>
      <div style="background-color:rgba(0,142,155,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">turquoise3</div>
      <div style="background-color:rgba(0,60,65,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">turquoise4</div>
      <div style="background-color:rgba(218,56,218,1.0);padding:10px;border-radius:5px;color:rgba(0,0,0);">violet</div>
      <div style="background-color:rgba(160,3,71,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">violetred</div>
      <div style="background-color:rgba(255,12,77,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">violetred1</div>
      <div style="background-color:rgba(218,10,66,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">violetred2</div>
      <div style="background-color:rgba(155,8,47,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">violetred3</div>
      <div style="background-color:rgba(65,4,21,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">violetred4</div>
      <div style="background-color:rgba(232,186,114,1.0);padding:10px;border-radius:5px;color:rgba(0,0,0);">wheat</div>
      <div style="background-color:rgba(255,203,125,1.0);padding:10px;border-radius:5px;color:rgba(0,0,0);">wheat1</div>
      <div style="background-color:rgba(218,175,107,1.0);padding:10px;border-radius:5px;color:rgba(0,0,0);">wheat2</div>
      <div style="background-color:rgba(155,125,77,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">wheat3</div>
      <div style="background-color:rgba(65,53,33,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">wheat4</div>
      <div style="background-color:rgba(255,255,255,1.0);padding:10px;border-radius:5px;color:rgba(0,0,0);">white</div>
      <div style="background-color:rgba(232,232,232,1.0);padding:10px;border-radius:5px;color:rgba(0,0,0);">whitesmoke</div>
      <div style="background-color:rgba(255,255,0,1.0);padding:10px;border-radius:5px;color:rgba(0,0,0);">yellow</div>
      <div style="background-color:rgba(255,255,0,1.0);padding:10px;border-radius:5px;color:rgba(0,0,0);">yellow1</div>
      <div style="background-color:rgba(218,218,0,1.0);padding:10px;border-radius:5px;color:rgba(0,0,0);">yellow2</div>
      <div style="background-color:rgba(155,155,0,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">yellow3</div>
      <div style="background-color:rgba(65,65,0,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">yellow4</div>
      <div style="background-color:rgba(82,155,8,1.0);padding:10px;border-radius:5px;color:rgba(255,255,255);">yellowgreen</div>
    </div>
