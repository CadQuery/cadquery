.. _installation:

Installing CadQuery
===================================

CadQuery is based on `FreeCAD <http://sourceforge.net/apps/mediawiki/free-cad/index.php?title=Main_Page>`_,
which is turn based on the open-source `OpenCascade <http://www.opencascade.com/>`_ modelling kernel.

Prerequisites--FreeCAD and Python 2.6 or 2.7
----------------------------------------------
CadQuery requires FreeCAD and Python version 2.6.x or 2.7.x  *Python 3.x is NOT supported*

Ubuntu Command Line Installation
------------------------------------------

On Ubuntu, you can type::

        sudo apt-get install -y freecad freecad-doc
        pip install cadquery

This `Unix Installation Video <http://youtu.be/InZu8jgaYCA>`_ will walk you through the installation


Installation: Other Platforms
------------------------------------------

   1. Install FreeCAD using the appropriate installer for your platform, on `www.freecadweb.org <http://www.freecadweb.org/wiki/?title=Download>`_
   2. pip install cadquery

This `Windows Installation video <https://www.youtube.com/watch?v=dWw4Y_ah-8k>`_ will walk you through the installation on Windows

Test Your Installation
------------------------

If all has gone well, you can open a command line/prompt, and type::

      $python
      $import cadquery
      $cadquery.Workplane('XY').box(1,2,3).toSvg()

Adding a Nicer GUI via the cadquery-freecad-module
--------------------------------------------------------

If you prefer to have a GUI available, your best option is to use
`The CadQuery Freecad Module <https://github.com/jmwright/cadquery-freecad-module>`_.

Simply extract cadquery-freecad-module into your FreeCAD installation. You'll end up
with a cadquery workbench that allows you to interactively run scripts, and then see the results in the FreeCAD GUI

If you are using Ubuntu, you can also install it via this ppa:

https://code.launchpad.net/~freecad-community/+archive/ubuntu/ppa/+packages


Zero Step  Install
-------------------------------------------------

If you would like to use cadquery with no installation all, you can
use `ParametricParts.com <https://www.parametricparts.com>`_, a web-based platform that runs cadquery scripts

It is free, and allows running and viewing cadquery scripts in your web browser or mobile phone


