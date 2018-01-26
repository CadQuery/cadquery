.. _cadquery_reference:

CadQuery Scripts and Object Output
======================================

CadQuery scripts are pure python scripts, that may follow a few conventions.

If you are using cadquery as a library, there are no constraints.

If you are using cadquery scripts inside of a cadquery execution environment,
like `The CadQuery Freecad Module <https://github.com/jmwright/cadquery-freecad-module>`_ or
`Jupyter notebooks <https://mybinder.org/v2/gh/RustyVermeer/tryCQ/master>`_, there are a few conventions you need to be aware of:

  * cadquery is imported as 'cq'
  * to return an object to the container, you need to call the show_object() method.

Each script generally has three sections:

 * Variable Assignments and metadata definitions
 * cadquery and other python code
 * object exports, via the export_object() function


see the :ref:`cqgi` section for more details.