.. _cadquery_reference:

CadQuery Scripts and Object Output
======================================

CadQuery scripts are pure Python scripts, that may follow a few conventions.

If you are using CadQuery as a library, there are no constraints.

If you are using CadQuery scripts inside of a CadQuery execution environment
like `CQ-editor <https://github.com/CadQuery/CQ-editor>`_, there are a few conventions you need to be aware of:

  * cadquery is usually imported as 'cq' at the top of a script
  * to return an object to the execution environment (like CQ-editor) for rendering, you need to call the show_object() method

Each script generally has three sections:

 * Variable Assignments and metadata definitions
 * CadQuery and other Python code
 * object export or rendering, via the show_object() function


see the :ref:`cqgi` section for more details.