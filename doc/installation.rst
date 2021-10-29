.. _installation:

Installing CadQuery
===================================

CadQuery 2 is based on
`OCP <https://github.com/CadQuery/OCP>`_,
which is a set of Python bindings for the open-source `OpenCascade <http://www.opencascade.com/>`_ modelling kernel.

Anaconda or Miniconda (Python 3.x editions), Python 3.x
----------------------------------------------
CadQuery requires OCP and Python version 3.x

Command Line Installation
------------------------------------------

CadQuery development moves very quickly, so you will need to choose whether you want the latest features or an older, probably more stable, version of CadQuery.

To get the latest features (recommended), once you have Anaconda or Miniconda installed, activate the [conda environment](https://conda.io/projects/conda/en/latest/user-guide/tasks/manage-environments.html) you want to use and type::

        conda install -c cadquery -c conda-forge cadquery=master

If you want an older, more stable version of CadQuery, once you have Anaconda or Miniconda installed, activate the [conda environment](https://conda.io/projects/conda/en/latest/user-guide/tasks/manage-environments.html) you want to use and type::

        conda install -c conda-forge -c cadquery cadquery=2

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

CQ-editor relies on Anaconda/Miniconda as well, and the README explains how to set up an environment that will run CQ-editor. However, if you are running the master branch (latest features) of CadQuery, you will want to install CQ-editor into your activated Anaconda environment with the following::

        conda install -c cadquery -c conda-forge cq-editor=master


