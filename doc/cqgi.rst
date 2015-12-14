.. _cqgi:

The CadQuery Gateway Interface
====================================


CadQuery is first and foremost designed as a library, which can be used as a part of any project.
In this context, there is no need for a standard script format or gateway api.

Though the embedded use case is the most common, several tools have been created which run
cadquery scripts on behalf of the user, and then render the result of the script visually.

These execution environments (EE) generally accept a script and user input values for
script parameters, and then display the resulting objects visually to the user.

Today, three execution environments exist:

 * `The CadQuery Freecad Module <https://github.com/jmwright/cadquery-freecad-module>`_, which runs scripts
   inside of the FreeCAD IDE, and displays objects in the display window
 *  the cq-directive, which is used to execute scripts inside of sphinx-doc,
    producing documented examples that include both a script and an SVG representation of the object that results
 * `ParametricParts.com <https://www.parametricparts.com>`_, which provides a web-based way to prompt user input for
    variables, and then display the result output in a web page.

The CQGI is distributed with cadquery, and standardizes the interface between execution environments and cadquery scripts.


The Script Side
-----------------

CQGI compliant containers provide an execution environment for scripts. The environment includes:

 * the cadquery library is automatically imported as 'cq'.
 * the :py:meth:`cadquery.cqgi.ScriptCallback.build_object()` method is defined that should be used to export a shape to the execution environment

Scripts must call build_output at least once. Invoking build_object more than once will send multiple objects to
the container.  An error will occur if the script does not return an object using the build_object() method.

Future enhancements will include several other methods, used to provide more metadata for the execution environment:
  * :py:meth:`cadquery.cqgi.ScriptCallback.add_error()`, indicates an error with an input parameter
  * :py:meth:`cadquery.cqgi.ScriptCallback.describe_parameter()`, provides extra information about a parameter in the script,


The execution environment side
-------------------------------

CQGI makes it easy to run cadquery scripts in a standard way. To run a script from an execution environment,
run code like this::

    from cadquery import cqgi

    user_script = ...
    build_result = cqgi.parse(user_script).build()

The :py:meth:`cadquery.cqgi.parse()` method returns a :py:class:`cadquery.cqgi.CQModel` object.

Calling :py:meth:`cadquery.cqgi.CQModel.build()` returns a :py:class:`cadquery.cqgi.BuildResult` object,
,which includes the script execution time, and a success flag.

If the script was successful, the results property will include a list of results returned by the script.

If the script failed, the exception property contains the exception object.

If you have a way to get inputs from a user, you can override any of the constants defined in the user script
with new values::

    from cadquery import cqgi

    user_script = ...
    build_result = cqgi.parse(user_script).build({ 'param': 2 } )

If a parameter called 'param' is defined in the model, it will be assigned the value 2 before the script runs.
An error will occur if a value is provided that is not defined in the model, or if the value provided cannot
be assigned to a variable with the given name.

More about script variables
-----------------------------

CQGI uses the following rules to find input variables for a script:

  * only top-level statements are considered
  * only assignments of constant values to a local name are considered.

For example, in the following script::

      h = 1.0
      w = 2.0
      foo = 'bar'

      def some_function():
          x = 1

h, w, and foo will be overridable script variables, but x is not.

You can list the variables defined in the model by using the return value of the parse method::

       model = cqgi.parse(user_script)

       //a dictionary of InputParameter objects
       parameters = model.metadata.parameters

The key of the dictionary is a string , and the value is a :py:class:`cadquery.cqgi.InputParameter` object
See the CQGI API docs for more details.

Future enhancments will include a safer sandbox to prevent malicious scripts.

Important CQGI Methods
-------------------------

These are the most important Methods and classes of the CQGI

.. currentmodule:: cadquery.cqgi

.. autosummary::
    parse
    CQModel.build
    BuildResult
    ScriptCallback.build_object

Complete CQGI api
-----------------

.. automodule:: cadquery.cqgi
   :members:

