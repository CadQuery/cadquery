.. _cqgi:

The CadQuery Gateway Interface
====================================


CadQuery is first and foremost designed as a library, which can be used as a part of any project.
In this context, there is no need for a standard script format or gateway API.

Though the embedded use case is the most common, several tools have been created which run
cadquery scripts on behalf of the user, and then render the result of the script visually.

These execution environments (EE) generally accept a script and user input values for
script parameters, and then display the resulting objects visually to the user.

Today, three execution environments exist:

 * `CQ-editor <https://github.com/CadQuery/CQ-editor>`_, which runs scripts
   inside of a CadQuery IDE, and displays objects in the display window and includes features like debugging.
 *  The cq-directive, which is used to execute scripts inside of sphinx-doc,
    producing documented examples that include both a script and an SVG representation of the object that results.

The CQGI is distributed with CadQuery, and standardizes the interface between execution environments and CadQuery scripts.


The Script Side
-----------------

CQGI compliant containers provide an execution environment for scripts. The environment includes:

 * the cadquery library is automatically imported as 'cq'.
 * the :py:meth:`cadquery.cqgi.ScriptCallback.show_object()` method is defined that should be used to export a shape to the execution environment
 * the :py:meth:`cadquery.cqgi.ScriptCallBack.debug()` method is defined, which can be used by scripts to debug model output during execution.

Scripts must call show_object at least once. Invoking show_object more than once will send multiple objects to
the container.  An error will occur if the script does not return an object using the show_object() method.

This CQGI compliant script produces a cube with a circle on top, and displays a workplane as well as an intermediate circle as debug output::

    base_cube = cq.Workplane('XY').rect(1.0,1.0).extrude(1.0)
    top_of_cube_plane = base_cube.faces(">Z").workplane()
    debug(top_of_cube_plane, { 'color': 'yellow', } )
    debug(top_of_cube_plane.center, { 'color' : 'blue' } )

    circle=top_of_cube_plane.circle(0.5)
    debug(circle, { 'color': 'red' } )

    show_object( circle.extrude(1.0) )

Note that importing cadquery is not required. 
At the end of this script, one object will be displayed, in addition to a workplane, a point, and a circle

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

The `metadata`p property of the object contains a `cadquery.cqgi.ScriptMetaData` object, which can be used to discover the
user parameters available. This is useful if the execution environment would like to present a GUI to allow the user to change the 
model parameters.  Typically, after collecting new values, the environment will supply them in the build() method.

This code will return a dictionary of parameter values in the model text SCRIPT::
     
     parameters = cqgi.parse(SCRIPT).metadata.parameters

The dictionary you get back is a map where key is the parameter name, and value is an InputParameter object, 
which has a name, type, and default value. 

The type is an object which extends ParameterType-- you can use this to determine what kind of widget to render ( checkbox for boolean, for example ).

The parameter object also has a description, valid values, minimum, and maximum values, if the user has provided them using the
describe_parameter() method.



Calling :py:meth:`cadquery.cqgi.CQModel.build()` returns a :py:class:`cadquery.cqgi.BuildResult` object,
,which includes the script execution time, and a success flag.

If the script was successful, the results property will include a list of results returned by the script,
as well as any debug the script produced

If the script failed, the exception property contains the exception object.

If you have a way to get inputs from a user, you can override any of the constants defined in the user script
with new values::

    from cadquery import cqgi

    user_script = ...
    build_result = cqgi.parse(user_script).build(build_parameters={ 'param': 2 }, build_options={} )

If a parameter called 'param' is defined in the model, it will be assigned the value 2 before the script runs.
An error will occur if a value is provided that is not defined in the model, or if the value provided cannot
be assigned to a variable with the given name.

build_options is used to set server-side settings like timeouts, tessellation tolerances, and other details about
how the model should be built.


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

Future enhancements will include a safer sandbox to prevent malicious scripts.

Automating export to STL
-------------------------
A common use-case for the CQGI is the automation of processing cadquery code into geometry, doing so via the CQGI rather than an export line in the script itself leads to a much tidier environment; you may need to do this as part of an automated-workflow, batch-conversion, exporting to another software for assembly, or running stress simulations on resulting bodies.

The below Python script demonstrates how to open, process, and export an STL file from any valid cadquery script::

      # Load CQGI
      import cadquery.cqgi as cqgi
      import cadquery as cq
      
      # load the cadquery script
      model = cqgi.parse(open("example.py").read())
      
      # run the script and store the result (from the show_object call in the script)
      build_result = model.build()
      
      # test to ensure the process worked.
      if build_result.success:
          # loop through all the shapes returned and export to STL
          for i, result in enumerate(build_result.results):
              cq.exporters.export(result.shape, f"example_output{i}.stl")
      else:
          print(f"BUILD FAILED: {build_result.exception}")



Important CQGI Methods
-------------------------

These are the most important Methods and classes of the CQGI

.. currentmodule:: cadquery.cqgi

.. autosummary::
    parse
    CQModel.build
    BuildResult
    ScriptCallback.show_object

Complete CQGI API
-----------------

.. automodule:: cadquery.cqgi
   :members:

