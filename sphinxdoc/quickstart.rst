
.. module:: cadfile.cadutils.cadquery

.. _quickstart:

***********************
ModelScript QuickStart
***********************

Want a quick glimpse of Parametric Parts ModelScripts?  You're at the right place!
This quickstart will demonstrate the basics of ModelScripts using a simple example

Prerequisites
=============

**WebGL Capable Browser**

        CadQuery renders models in your browser using WebGL-- which is supported by most browsers *except for IE*
        You can follow along without IE, but you will not be able to see the model dynamically rendered


What we'll accomplish
=====================

Our finished object will look like this:

..  image:: quickstart.png


**We would like our block to have these features:**

    1. It should be sized to hold a single 608 ( 'skate' ) bearing, in the center of the block.
    2. It should have counter sunk holes for M2 socket head cap screws at the corners
    3. The length and width of the block should be configurable by the user to any reasonable size.

A human would describe this as:

     "A rectangular block 80mm x 60mm x 30mm , with countersunk holes for M2 socket head cap screws
     at the corners, and a circular pocket 22mm in diameter in the middle for a bearing"

Human descriptions are very elegant, right?
Hopefully our finished script will not be too much more complex than this human-oriented description.

Let's see how we do.

Start a new Model
==================================

CadQuery comes with an online, interactive default model as a starting point.   Lets open up that tool
`here <http://www.parametricparts.com/parts/create>`_

You should see the dynamic model creator page, which will display a sample model:

        ..  image:: quickstart-1.png

Take a minute to play with this model. Here are a few things to try:

1.  Use the mouse to rotate the block
2.  Play with the view controls under the image
3.  change the length ( the only available parameter),
    and use the preview button to re-display the updated model
4.  Change the preset value to `short`
5.  Edit the model script itself. Change the hard-coded width and thickness values and click 'update script'
    to re-display the model.

At this point, you should have some idea how to interact with the sample model, so lets get to work on the project.

Modify MetaData and Parameters
==============================

Each model has metadata that describes the model's properties. The default Unit of Measure (UOM) will work:

.. code-block:: python
   :linenos:
   :emphasize-lines: 1

    UOM = "mm"


Next, lets set up the parameters.  Parameters are `placeholders` that users can modify separately from the script itself.
The default model  has a single parameter, ``length``.  Lets add a ``height`` parameter too

.. code-block:: python
   :linenos:
   :emphasize-lines: 4

    UOM = "mm"

    length = FloatParam(min=30.0,max=200.0,presets={'default':80.0,'short':30.0},desc="Length of the block")
    height =  FloatParam(min=30.0,max=200.0,presets={'default':60.0,'short':30.0},desc="Height of the block")
    thickness = 10.0

    def build():
        return Workplane("XY").box(length.value,height.value,thickness)

We've set the minimum values to 30 mm, since that's about as small as it could be while having room for a bearing 22mm
in diameter.  We've also set the default values to be those we'd like to start with: 80mm for the length and 60mm for the
height.

Now, modify the build script to use your width value to make the block  by changing ``height`` to
``height.value``

.. code-block:: python
   :linenos:
   :emphasize-lines: 3

    ...
    def build():
        return Workplane("XY").box(length.value,height.value,thickness)

The value property always returns the ``user-adjusted`` value of the parameter.  That's good enough for now.
Click "Save Changes" and you should see your 80x60x10mm base plate, like this:

        ..  image:: quickstart-2.png

If you'd like to come back to this model later, the url bar links to the newly created part.

Now lets move on and make this boring plate into a pillow block.


Add the Holes
================

Our pillow block needs to have a 22mm diameter hole in the center of this block to hold the bearing.

This modification will do the trick:

.. code-block:: python
   :linenos:
   :emphasize-lines: 3

    ...
    def build():
        return Workplane("XY").box(length.value,height.value,thickness).faces(">Z").workplane().hole(22.0)

Rebuild your model by clicking "Save Model" at the bottom. Your block should look like this:

        ..  image:: quickstart-3.png


The code is pretty compact, and works like this:
    * :py:meth:`Workplane.faces` selects the top-most face in the Z direction, and
    * :py:meth:`Workplane.workplane` begins a new workplane located on this face
    * :py:meth:`Workplane.hole` drills a hole through the part 22mm in diamter

.. note::

    Don't worry about the CadQuery syntax now.. you can learn all about it in the :ref:`apireference` later.

More Holes
============

Ok, that hole was not too hard, but what about the counter-bored holes in the corners?

An M2 Socket head cap screw has these dimensions:

  * **Head Diameter** : 3.8 mm
  * **Head height**  : 2.0 mm
  * **Clearance Hole** : 2.4 mm
  * **CounterBore diameter** : 4.4 mm

The centers of these holes should be 4mm from the edges of the block. And,
we want the block to work correctly even when the block is re-sized by the user.

**Don't tell me** we'll have to repeat the steps above 8 times to get counter-bored holes?

Good news!-- we can get the job done with just two lines of code. Here's the code we need:

.. code-block:: python
   :linenos:
   :emphasize-lines: 4-5

    ...
    def build():
        return Workplane("XY").box(length.value,height.value,thickness).faces(">Z").workplane().hole(22.0) \
            .faces(">Z").workplane() \
            .rect(length.value-8.0,height.value-8.0,forConstruction=True) \
            .vertices().cboreHole(2.4,4.4,2.1)

You should see something like this:

        ..  image:: quickstart-4.png

Lets Break that down a bit
^^^^^^^^^^^^^^^^^^^^^^^^^^


**Line 4** selects the top-most face of the block, and creates a workplane on the top that face, which we'll use to
define the centers of the holes in the corners:

.. code-block:: python
   :linenos:
   :emphasize-lines: 4

    ...
    def build():
        return Workplane("XY").box(length.value,height.value,thickness).faces(">Z").workplane().hole(22.0) \
            .faces(">Z").workplane() \
            .rect(length.value-8.0,width.value-8.0,forConstruction=True) \
            .vertices().cboreHole(2.4,4.4,2.1)


**Line 5** draws a rectangle 8mm smaller than the overall length and width of the block,which we will use to
locate the corner holes:

.. code-block:: python
   :linenos:
   :emphasize-lines: 5

    ...
    def build():
        return Workplane("XY").box(length.value,height.value,thickness).faces(">Z").workplane().hole(22.0) \
            .faces(">Z").workplane() \
            .rect(length.value-8.0,width.value-8.0,forConstruction=True) \
            .vertices().cboreHole(2.4,4.4,2.1)

There are a couple of things to note about this line:

    1. The :py:meth:`Workplane.rect` function draws a rectangle.  **forConstruction=True**
       tells CadQuery that this rectangle will not form a part of the solid,
       but we are just using it to help define some other geometry.
    2. The center point of a workplane on a face is always at the center of the face, which works well here
    3. Unless you specifiy otherwise, a rectangle is drawn with its center on the current workplane center-- in
       this case, the center of the top face of the block. So this rectangle will be centered on the face


**Line 6** selects the corners of the rectangle, and makes the holes:

.. code-block:: python
   :linenos:
   :emphasize-lines: 6

    ...
    def build():
        return Workplane("XY").box(length.value,height.value,thickness).faces(">Z").workplane().hole(22.0) \
            .faces(">Z").workplane() \
            .rect(length.value-8.0,width.value-8.0,forConstruction=True) \
            .vertices().cboreHole(2.4,4.4,2.1)

Notes about this line:

    1. The :py:meth:`CQ.vertices` function selects the corners of the rectangle
    2. The :py:meth:`Workplane.cboreHole` function is a handy CadQuery function that makes a counterbored hole
    3. ``cboreHole``, like most other CadQuery functions, operate on the values on the stack.  In this case, since
       selected the four vertices before calling the function, the function operates on each of the four points--
       which results in a counterbore hole at the corners.

Presets
===========

Almost done.  This model is pretty easy to configure, but we can make it even easier by providing users with a few
'out of the box' options to choose from.  Lets provide two preset options:

  * **Small** : 30 mm x 40mm
  * **Square-Medium**  : 50 mm x 50mm

We can do that using the preset dictionaries in the parameter definition:

.. code-block:: python
   :linenos:
   :emphasize-lines: 2-3

    ...
    length = FloatParam(min=10.0,max=500.0,presets={'default':100.0,'small':30.0,'square-medium':50},desc="Length of the box")
    height =  FloatParam(min=30.0,max=200.0,presets={'default':60.0,'small':40.0,'square-medium':50},desc="Height of the block")

Now save the model and have a look at the preset DDLB-- you'll see that you can easily switch between these
configurations:

        ..  image:: quickstart-5.png


Done!
============

And... We're done! Congratulations, you just made a parametric, 3d model with 15 lines of code.Users can use this
model to generate pillow blocks in any size they would like

For completeness, Here's a copy of the finished model:

.. code-block:: python
   :linenos:

        UOM = "mm"

        length = FloatParam(min=10.0,max=500.0,presets={'default':100.0,'small':30.0,'square-medium':50},desc="Length of the box")
        height =  FloatParam(min=30.0,max=200.0,presets={'default':60.0,'small':40.0,'square-medium':50},desc="Height of the block")

        width = 40.0
        thickness = 10.0

        def build():
            return Workplane("XY").box(length.value,height.value,thickness).faces(">Z").workplane().hole(22.0) \
                .faces(">Z").workplane() \
                .rect(length.value-8.0,height.value-8.0,forConstruction=True) \
                .vertices().cboreHole(2.4,4.4,2.1)


Want to learn more?
====================

   * The :ref:`examples` contains lots of examples demonstrating cadquery features
   * The :ref:`cadquery_reference` describes the file format in detail
   * The :ref:`apireference` is a good overview of language features grouped by function
   * The :ref:`classreference` is the hard-core listing of all functions available.