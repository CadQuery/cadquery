.. _what_is_cadquery:

*********************
Introduction
*********************

What is CadQuery
========================================

CadQuery is an intuitive, easy-to-use language for building parametric 3D CAD models.  It has several goals:

    * Build models with scripts that are as close as possible to how you'd describe the object to a human.

    * Create parametric models that can be very easily customized by end users

    * Output high quality CAD formats like STEP and AMF in addition to traditional STL

    * Provide a non-proprietary, plain text model format that can be edited and executed with only a web browser


CadQuery is a Python module that provides a high-level wrapper around the
(`FreeCAD <http://sourceforge.net/apps/mediawiki/free-cad/index.php?title=Main_Page>`_) python libraries.

Where does the name CadQuery come from?
========================================

CadQuery is inspired by ( `jQuery <http://www.jquery.com>`_ ), a popular framework that
revolutionized web development involving javascript.

CadQuery is for 3D CAD  what jQuery is for javascript.
If you are familiar with how jQuery, you will probably recognize several jQuery features that CadQuery uses:

    * A fluent api to create clean, easy to read code

    * Ability to use the library along side other python libraries

    * Clear and complete documentation, with plenty of samples.


Why ParametricParts instead of OpenSCAD?
============================================

CadQuery is based on FreeCAD,which is in turn based on the OpenCascade modelling kernel. CadQuery/FreeCAD scripts
share many features with OpenSCAD, another open source, script based, parametric model generator.

The primary advantage of OpenSCAD is the large number of already existing model libaries  that exist already. So why not simply use OpenSCAD?

CadQuery scripts run from ParametricParts.com have several key advantages over OpenSCAD ( including the various web-based SCAD solutions):

    1. **The scripts use a standard programming language**, python, and thus can benefit from the associated infrastructure.
       This includes many standard libraries and IDEs

    2. **More powerful CAD kernel** OpenCascade is much more powerful than CGAL. Features supported natively
       by OCC include NURBS, splines, surface sewing, STL repair, STEP import/export,  and other complex operations,
       in addition to the standard CSG operations supported by CGAL

    3. **Ability to import/export STEP** We think the ability to begin with a STEP model, created in a CAD package,
       and then add parametric features is key.  This is possible in OpenSCAD using STL, but STL is a lossy format

    4. **Less Code and easier scripting**  CadQuery scripts require less code to create most objects, because it is possible to locate
       features based on the position of other features, workplanes, vertices, etc.

    5. **Better Performance**  CadQuery scripts can build STL, STEP, and AMF faster than OpenSCAD.

