.. _installation:

Installing CadQuery
===================================

CadQuery 2.0 is based on
`PythonOCC <http://www.pythonocc.org/>`_,
which is a set of Python bindings for the open-source `OpenCascade <http://www.opencascade.com/>`_ modelling kernel.

Anaconda or Miniconda (Python 3.x editions), Python 3.x
----------------------------------------------
CadQuery requires PythonOCC and Python version 3.x

Command Line Installation
------------------------------------------

Once you have Anaconda or Miniconda installed, activate the environment you want to use and type::

        conda install -c pythonocc -c oce -c conda-forge -c dlr-sc -c CadQuery cadquery-occ

Test Your Installation
------------------------

If all has gone well, you can open a command line/prompt, and type::

      $ python
      $ import cadquery
      $ cadquery.Workplane('XY').box(1,2,3).toSvg()

You should see raw SVG output displayed on the command line if the CadQuery installation was successful.

Adding a Nicer GUI via CQ-editor
--------------------------------------------------------

If you prefer to have a GUI available, your best option is to use
`CQ-editor <https://github.com/CadQuery/CQ-editor>`_.

CQ-editor relies on Anaconda/Miniconda as well, and the README explains how to set up an environment that will run CQ-editor.


