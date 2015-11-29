.. _cadquery_reference:

CadQuery Scripts and Object Output
======================================

CadQuery scripts are pure python scripts that follow a standard format.

Each script generally has three sections:

 * Variable Assignments
 * cadquery and other python code
 * object exports, via the export_object() function

Execution Environments
-----------------------
When your script runs, the container does not know which objects you wish to yeild for output.
Further, what 'output' means is different depending on the execution environment.

Most containers supply an export_object() method that allows you to export an object.

There are three execution environments:

   1. **Native Library**. In this context, there is no execution environment. Your scripts will only generate output
      when you manually invoke a method to save your object to disk, for example using the exporters library

   1. **cadquery-freecad-module**. In this context, exporting an object means displaying it on the screen, and
      registering it with FreeCAD for further manipulation.

   2. **parametricparts.com** In this context, exporting an object means exporting it into a format chosen by the
      user executing the script.

Variable Substitution
-----------------------

When a cadquery script runs, the values of the variables assume their hard-coded values.

Some execution environments, such as the `The CadQuery Freecad Module <https://github.com/jmwright/cadquery-freecad-module>`_
 or `parametricParts.com <https://www.parametricparts.com>`_ , may subsitute other values supplied by a user of your script.

 When this happens, your script will not know the difference: variables will appear to have been initialized the same
 as they had be before.

