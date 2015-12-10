.. _3d_cad_primer:


CadQuery Concepts
===================================


3D BREP Topology Concepts
---------------------------
Before talking about CadQuery, it makes sense to talk a little about 3D CAD Topology. CadQuery is based upon the
OpenCascade kernel, which is uses Boundary Representations ( BREP ) for objects.  This just means that objects
are defined by their enclosing surfaces.

When working in a BREP system, these fundamental constructs exist to define a shape ( working up the food chain):

   :vertex: a single point in space
   :edge: a connection between two or more vertices along a particular path ( called a curve )
   :wire: a collection of edges that are connected together.
   :face: a set of edges or wires that enclose a surface
   :shell: a collection of faces that are connected together along some of their edges
   :solid: a shell that has a closed interior
   :compound: a collection of solids

When using CadQuery, all of these objects are created, hopefully with the least possible work. In the actual CAD
kernel, there are another set of Geometrical constructs involved as well. For example, an arc-shaped edge will
hold a reference to an underlying curve that is a full cricle, and each linear edge holds underneath it the equation
for a line.  CadQuery shields you from these constructs.


CQ, the CadQuery Object
---------------------------

The CadQuery object wraps a BREP feature, and provides functionality around it.  Typical examples include rotating,
transforming, combining objects, and creating workplanes.

See :ref:`apireference` to learn more.


Workplanes
---------------------------

Workplanes represent a plane in space, from which other features can be located. They have a center point and a local
coordinate system.

The most common way to create a workplane is to locate one on the face of a solid.  You can also create new workplanes
in space, or relative to other planes using offsets or rotations.

The most powerful feature of workplanes is that they allow you to work in 2D space in the coordinate system of the
workplane, and then build 3D features based on local coordinates.  This makes scripts much easier to create and maintain.

See :py:class:`cadquery.Workplane` to learn more


2D Construction
---------------------------

Once you create a workplane, you can work in 2D, and then later use the features you create to make 3D objects.
You'll find all of the 2D constructs you expect-- circles, lines, arcs, mirroring, points, etc.

See :ref:`2dOperations` to learn more.


3D Construction
---------------------------

You can construct 3D primatives such as boxes, spheres, wedges, and cylinders directly. You can also sweep, extrude,
and loft 2D geometry to form 3D features.  Of course the basic primitive operations are also available.

See :ref:`3doperations` to learn more.



Selectors
---------------------------

Selectors allow you to select one or more features, for use to define new features.  As an example, you might
extrude a box, and then select the top face as the location for a new feture.  Or, you might extrude a box, and
then select all of the vertical edges so that you can apply a fillet to them.

You can select Vertices, Edges, Faces, Solids, and Wires using selectors.

Think of selectors as the equivalent of your hand and mouse, were you to build an object using a conventional CAD system.

You can learn more about selectors :ref:`selectors`


Construction Geometry
---------------------------
Construction geometry are features that are not part of the object, but are only defined to aid in building the object.
A common example might be to define a rectangle, and then use the corners to define a the location of a set of holes.

Most CadQuery construction methods provide a forConstruction keyword, which creates a feature that will only be used
to locate other features


The Stack
---------------------------

As you work in CadQuery, each operation returns a new CadQuery object with the result of that operations. Each CadQuery
object has a list of objects, and a reference to its parent.

You can always go backwards to older operations by removing the current object from the stack.  For example::

    CQ(someObject).faces(">Z").first().vertices()

returns a CadQuery object that contains all of the vertices on highest face of someObject. But you can always move
backwards in the stack to get the face as well::

    CQ(someObject).faces(">Z").first().vertices().end() #returns the same as CQ(someObject).faces(">Z").first()

You can browse stack access methods here :ref:`stackMethods`


Chaining
---------------------------

All CadQuery methods return another CadQuery object, so that you can chain the methods together fluently. Use
the core CQ methods to get at the objects that were created.


The Context Solid
---------------------------

Most of the time, you are building a single object, and adding features to that single object.  CadQuery watches
your operations, and defines the first solid object created as the 'context solid'.  After that, any features
you create are automatically combined ( unless you specify otherwise) with that solid.  This happens even if the
solid was created  a long way up in the stack.  For example::

    Workplane('XY').box(1,2,3).faces(">Z").circle(0.25).extrude()

Will create a 1x2x3 box, with a cylindrical boss extending from the top face.  It was not necessary to manually
combine the cylinder created by extruding the circle with the box, because the default behavior for extrude is
to combine the result with the context solid. The hole() method works similarly-- CadQuery presumes that you want
to subtract the hole from the context solid.

If you want to avoid this, you can specified combine=False, and CadQuery will create the solid separately.


Iteration
---------------------------

CAD models often have repeated geometry, and its really annoying to resort to for loops to construct features.
Many CadQuery methods operate automatically on each element on the stack, so that you don't have to write loops.
For example, this::

    Workplane('XY').box(1,2,3).faces(">Z").vertices().circle(0.5)

Will actually create 4 circles, because vertices() selects 4 vertices of a rectangular face, and the circle() method
iterates on each member of the stack.

This is really useful to remember  when you author your own plugins. :py:meth:`cadquery.CQ.Workplane.each` is useful for this purpose.


