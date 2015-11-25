What is a CadQuery?
========================================

CadQuery is an intuitive, easy-to-use python based language for building parametric 3D CAD models.  CadQuery is for 3D CAD what jQuery is for javascript.  Imagine selecting Faces of a 3d object the same way you select DOM objects with JQuery!

CadQuery has several goals:

* Build models with scripts that are as close as possible to how you'd describe the object to a human.
* Create parametric models that can be very easily customized by end users
* Output high quality CAD formats like STEP and AMF in addition to traditional STL
* Provide a non-proprietary, plain text model format that can be edited and executed with only a web browser

Using CadQuery, you can write short, simple scripts that produce high quality CAD models.  It is easy to make many different objects using a single script that can be customized.

Getting Started With CadQuery
========================================

The easiest way to get started with CadQuery is to Install FreeCAD ( version 14 recommended )  (http://www.freecadweb.org/) , and then to use our CadQuery-FreeCAD plugin here:

https://github.com/jmwright/cadquery-freecad-module


It includes the latest version of cadquery alreadby bundled, and has super-easy installation on Mac, Windows, and Unix.

It has tons of awesome features like integration with FreeCAD so you can see your objects, code-autocompletion, an examples bundle, and script saving/loading. Its definitely the best way to kick the tires!


Recently Added Features
========================================

* 12/5/14 -- New FreeCAD/CadQuery Module!  https://github.com/jmwright/cadquery-freecad-module
* 10/25/14 -- Added Revolution Feature ( thanks Jeremy ! )


Why CadQuery instead of OpenSCAD?
========================================

CadQuery is based on OpenCasCade.  CadQuery shares many features with OpenSCAD, another open source, script based, parametric model generator.

The primary advantage of OpenSCAD is the large number of already existing model libaries  that exist already. So why not simply use OpenSCAD?

CadQuery scripts have several key advantages over OpenSCAD:

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

License
========

CadQuery is licensed under the terms of the LGPLv3. http://www.gnu.org/copyleft/lesser.html

Where is the GUI?
==================

If you would like IDE support, you can use CadQuery inside of FreeCAD. There's an excellent plugin module here https://github.com/jmwright/cadquery-freecad-module

CadQuery also provides the backbone of http://parametricparts.com, so the easiest way to see it in action is to review the samples and objects there.

Installing -- FreeStanding Installation
========================================

Use these steps if you would like to write CadQuery scripts as a python API.  In this case, FreeCAD is used only as a CAD kernel.

1. install FreeCAD, version 0.14 or greater for your platform.  http://sourceforge.net/projects/free-cad/.

2. adjust your path if necessary.  FreeCAD bundles a python interpreter, but you'll probably want to use your own, 
   preferably one that has virtualenv available.  To use FreeCAD from any python interpreter, just append the FreeCAD
   lib directory to your path. On  (*Nix)::
   
        import sys
		sys.path.append('/usr/lib/freecad/lib')
		
   or on Windows::
     
	    import sys
		sys.path.append('/c/apps/FreeCAD/bin')
		
   *NOTE* FreeCAD on Windows will not work with python 2.7-- you must use pthon 2.6.X!!!!
   
3. install cadquery::

		pip install cadquery

3. test your installation::

		from cadquery import *
		box = Workplane("XY").box(1,2,3)
		exporters.toString(box,'STL')
		
You're up and running!
		
Installing -- Using CadQuery from Inside FreeCAD
=================================================

Use the Excellent CadQuery-FreeCAD plugin here:
   https://github.com/jmwright/cadquery-freecad-module

It includes a distribution of the latest version of cadquery.

Where does the name CadQuery come from?
========================================

CadQuery is inspired by ( `jQuery <http://www.jquery.com>`_ ), a popular framework that
revolutionized web development involving javascript.

If you are familiar with how jQuery, you will probably recognize several jQuery features that CadQuery uses:

* A fluent api to create clean, easy to read code
* Language features that make selection and iteration incredibly easy
* 
* Ability to use the library along side other python libraries
* Clear and complete documentation, with plenty of samples.

