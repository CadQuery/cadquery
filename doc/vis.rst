.. _vis:

===========================
Visualization
===========================


Pure Python
===========

Since version 2.5 CadQuery support visualization without any external tools. Those facilities are based on the VTK library
and are not tied to any external tool.

.. code-block:: python

    from cadquery import *
    from cadquery.vis import show

    w = Workplane().sphere(1).split(keepTop=True) - Workplane().sphere(0.5)

    # Show the result
    show(w, alpha=0.5)


..  image:: _static/show.PNG


One can visualize objects of type :class:`~cadquery.Workplane`, :class:`~cadquery.Sketch`, :class:`~cadquery.Assembly`, :class:`~cadquery.Shape`, 
:class:`~cadquery.Vector`, :class:`~cadquery.Location` and lists thereof.


.. code-block:: python

   adquery import *
   from cadquery.occ_impl.shapes import *
   from cadquery.vis import show

   w = Workplane().sphere(0.5).split(keepTop=True)
   sk = Sketch().rect(1.5, 1.5)
   sh = torus(5, 0.5)

   r = rect(2, 2)
   c = circle(2)

   N = 50
   params = [i/N for i in range(N)]

   vecs = r.positions(params)
   locs = c.locations(params)

   # Render the solid
   show(w, sk, sh, vecs, locs)


..  image:: _static/show_demo.PNG


Additionally it is possibly to integrate with other libraries using VTK and display any `vtkProp` object.


.. code-block:: python

    from cadquery.vis import show
    from cadquery.occ_impl.shapes import torus

    from vtkmodules.vtkRenderingAnnotation import vtkAnnotatedCubeActor


    a = vtkAnnotatedCubeActor()
    t = torus(5,1)

    show(t, a)

..  image:: _static/show_vtk.PNG


Note that currently the show functions is blocking.


Jupyter/JupterLab
=================

There is also more limited support for displaying :class:`~cadquery.Workplane`, :class:`~cadquery.Sketch`, :class:`~cadquery.Assembly`,
:class:`~cadquery.Shape` in Jupyter and JupyterLab. This functionality is implemented using VTK.js.

.. code-block:: python

    from cadquery import *

    w = Workplane().sphere(1).split(keepTop=True)

    w

..  image:: _static/show_jupyter.PNG

