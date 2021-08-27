.. _extending:

Extending CadQuery
======================


If you find that CadQuery does not suit your needs, you can easily extend it.  CadQuery provides several extension
methods:

   * You can load plugins others have developed. This is by far the easiest way to access other code
   * You can define your own plugins.
   * You can use OCP scripting directly


Using OpenCascade methods
-------------------------

The easiest way to extend CadQuery is to simply use OpenCascade/OCP scripting inside of your build method.  Just about
any valid OCP script will execute just fine. For example, this simple CadQuery script::

    return cq.Workplane("XY").box(1.0,2.0,3.0).val()

is actually equivalent to::

    return cq.Shape.cast(BRepPrimAPI_MakeBox(gp_Ax2(Vector(-0.1, -1.0, -1.5), Vector(0, 0, 1)), 1.0, 2.0, 3.0).Shape())

As long as you return a valid OCP Shape, you can use any OCP methods you like. You can even mix and match the
two. For example, consider this script, which creates a OCP box, but then uses CadQuery to select its faces::

    box = cq.Shape.cast(BRepPrimAPI_MakeBox(gp_Ax2(Vector(-0.1, -1.0, -1.5), Vector(0, 0, 1)), 1.0, 2.0, 3.0).Shape())
    cq = Workplane(box).faces(">Z").size() # returns 6


Extending CadQuery: Plugins
----------------------------

Though you can get a lot done with OpenCascade, the code gets pretty nasty in a hurry. CadQuery shields you from
a lot of the complexity of the OpenCascade API.

You can get the best of both worlds by wrapping your OCP script into a CadQuery plugin.

A CadQuery plugin is simply a function that is attached to the CadQuery :py:meth:`cadquery.CQ` or :py:meth:`cadquery.Workplane` class.
When connected, your plugin can be used in the chain just like the built-in functions.

There are a few key concepts important to understand when building a plugin


The Stack
-------------------

Every CadQuery object has a local stack, which contains a list of items.  The items on the stack will be
one of these types:

   * **A CadQuery SolidReference object**, which holds a reference to a OCP solid
   * **A OCP object**, a Vertex, Edge, Wire, Face, Shell, Solid, or Compound

The stack is available by using self.objects, and will always contain at least one object.

.. note::

    Objects and points on the stack are **always** in global coordinates.  Similarly, any objects you
    create must be created in terms of global coordinates as well!


Preserving the Chain
-----------------------

CadQuery's fluent API relies on the ability to chain calls together one after another. For this to work,
you must return a valid CadQuery object as a return value.  If you choose not to return a CadQuery object,
then your plugin will end the chain. Sometimes this is desired for example :py:meth:`cadquery.Workplane.size`

There are two ways you can safely continue the chain:

   1.  **return self**  If you simply wish to modify the stack contents, you can simply return a reference to
       self.  This approach is destructive, because the contents of the stack are modified, but it is also the
       simplest.
   2.  :py:meth:`cadquery.Workplane.newObject`  Most of the time, you will want to return a new object.  Using newObject will
       return a new CQ or Workplane object having the stack you specify, and will link this object to the
       previous one.  This preserves the original object and its stack.


Helper Methods
-----------------------

When you implement a CadQuery plugin, you are extending CadQuery's base objects.  As a result, you can call any
CadQuery or Workplane methods from inside of your extension.  You can also call a number of internal methods that
are designed to aid in plugin creation:


   * :py:meth:`cadquery.Workplane._makeWireAtPoints` will invoke a factory function you supply for all points on the stack,
     and return a properly constructed cadquery object. This function takes care of registering wires for you
     and everything like that

   * :py:meth:`cadquery.Workplane.newObject` returns a new Workplane object with the provided stack, and with its parent set
     to the current object. The preferred way to continue the chain

   * :py:meth:`cadquery.Workplane.findSolid` returns the first Solid found in the chain, working from the current object upwards
     in the chain. commonly used when your plugin will modify an existing solid, or needs to create objects and
     then combine them onto the 'main' part that is in progress

   * :py:meth:`cadquery.Workplane._addPendingWire` must be called if you add a wire.  This allows the base class to track all the wires
     that are created, so that they can be managed when extrusion occurs.

   * :py:meth:`cadquery.Workplane.wire` gathers up all of the edges that have been drawn ( eg, by line, vline, etc ), and
     attempts to combine them into a single wire, which is returned. This should be used when your plugin creates
     2D edges, and you know it is time to collect them into a single wire.

   * :py:meth:`cadquery.Workplane.plane` provides a reference to the workplane, which allows you to convert between workplane
     coordinates and global coordinates:
     * :py:meth:`cadquery.occ_impl.geom.Plane.toWorldCoords` will convert local coordinates to global ones
     * :py:meth:`cadquery.occ_impl.geom.Plane.toLocalCoords` will convert from global coordinates to local coordinates

Coordinate Systems
-----------------------

Keep in mind that the user may be using a work plane that has created a local coordinate system. Consequently,
the orientation of shapes that you create are often implicitly defined by the user's workplane.

Any objects that you create must be fully defined in *global coordinates*, even though some or all of the users'
inputs may be defined in terms of local coordinates.


Linking in your plugin
-----------------------

Your plugin is a single method, which is attached to the main Workplane or CadQuery object.

Your plugin method's first parameter should be 'self', which will provide a reference to base class functionality.
You can also accept other arguments.

To install it, simply attach it to the CadQuery or Workplane object, like this::

    def _yourFunction(self,arg1,arg):
        do stuff
        return whatever_you_want

    cq.Workplane.yourPlugin = _yourFunction

That's it!

CadQueryExample Plugins
-----------------------
Some core cadquery code is intentionally written exactly like a plugin.
If you are writing your own plugins, have a look at these methods for inspiration:

   * :py:meth:`cadquery.Workplane.polygon`
   * :py:meth:`cadquery.Workplane.cboreHole`


Plugin Example
-----------------------

This ultra simple plugin makes cubes of the specified size for each stack point.

(The cubes are off-center because the boxes have their lower left corner at the reference points.)

.. code-block:: python

        def makeCubes(self,length):
            #self refers to the CQ or Workplane object

            #inner method that creates a cube
            def _singleCube(loc):
                #loc is a location in local coordinates
                #since we're using eachpoint with useLocalCoordinates=True
                return cq.Solid.makeBox(length,length,length,pnt).locate(loc)

            #use CQ utility method to iterate over the stack, call our
            #method, and convert to/from local coordinates.
            return self.eachpoint(_singleCube,True)

        #link the plugin into CadQuery
        cq.Workplane.makeCubes = makeCubes

        #use the plugin
        result = cq.Workplane("XY").box(6.0,8.0,0.5).faces(">Z")\
            .rect(4.0,4.0,forConstruction=True).vertices() \
            .makeCubes(1.0).combineSolids()

