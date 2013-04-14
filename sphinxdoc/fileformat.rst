.. _cadquery_reference:

********************************
ModelScript Format Reference
********************************

ParametricParts ModelScripts define a parametric 3D model that can be executed and customized by an end user.
CadQuery scripts are pure python scripts that follow a standard format.  Each script contains these main components:

    :MetaData:
        *(Mandatory)* Defines the attributes that describe the model, such as version and unit of measure

    :Parameters:
        *(Optional)* Defines parameters and their default values, which can be
        manipulated by users to customize the object.  Parameters are defined by creating local variables
        of a particular class type. Presets and groups organize parameters to make them easier to use

    :build script:
        *(Mandatory)* Constructs the model once parameter values are collected and the model is validated.
        The script must return a solid object, or a cadquery solid

The Script Life-cycle
----------------------

CadQuery scripts have the following lifecycle when they are executed by a user via the web interface:

    1.  **Load Script**  If it is valid, the parameters and MetaData
        are loaded.  A number of special objects are automatically available to your script

    2.  **Display Model to User**  The parameters and default values are displayed to the user.
        The model is rendered and displayed to the user using the default values

    3.  **User selects new parameter values** , either by selecting
        preset combinations, or by providing values for each parameter

    4.  **Build the model**  If validation is successful, the model is re-built, and the preview window is updated

    5.  **User downloads**  If the user chooses to download the model as STL, STEP, or  AMF, the model is re-built
        again for download.


A Full Example Script
----------------------

This script demonstrates all of the model elements available. Each is briefly introduced in the sample text,
and then described in more detail after the sample::

    """
        Comments and Copyright Statement
    """

    #
    # metadata describes your model
    #
    UOM = "mm"
    VERSION = 1.0

    #
    # parameter definitions. Valid parameter types are FloatParam,IntParam,and BooleanParam
    # each paraemter can have min and max values, a description, and a set of named preset values
    #
    p_diam = FloatParam(min=1.0,max=500.0,presets={'default':40.0,'small':2.0,'big':200.0},group="Basics", desc="Diameter");

    #
    # build the model based on user selected parameter values.
    # Must return a FreeCAD solid before exiting.
    #
    def build():
        return Part.makeSphere(p_diam.value);


Each section of the script is described in more detail below

Metadata
----------------

Model metadata is provided by setting a dictionary variable called METADATA  in the script.  You can provide
any metadata you choose, but only these values are currently used:

:UOM:
    The unit of measure of your model. in and mm are common values, but others are allowed.
    Some model formats like AMF can accept units of measure, which streamlines the printing process. **[OPTIONAL]**

:VERSION:
    The script format version.  Valid versions are established by ParametricParts, currently only version 1.0 is
    valid.  If omitted, the latest version is assumed.  **[OPTIONAL]**


Other metadata fields may be added in the future.

Parameters
----------------

Model parameters provide the flexibility users need to customize your model.  Parameters are optional, but most
users will expect at least a couple of parameters for your model to qualify as 'parametric'.


Parameters can be named whatever you would like. By convention, it is common to name them *p_<name>*, indicating
"parameter".


Each parameter has a particular type ( Float, Integer, Boolean ).  Parameters also have optional attributes, which are
provided as keyword arguments:

:desc:
    A description of the parameter, displayed to the user if help is needed [Optional]

:min:
    The minimum value ( not applicable to Boolean ) [Optional]

:max:
    The maximum value ( not applicable to  Boolean ) [Optional]

:presets:
    A dictionary containing key-value pairs. Each key is the name of a preset, and the value is the value the
    parameter will take when the preset is selected by the user.


    When a model defines presets, the user is presented with a choice of available presets in a drop-down-list.
    Selecting a preset changes the values of all parameters to their associated values.

    If it exists, the special preset named 'default' will be used to populate the default values when the user
    is initially presented with the model.

    When the model is built, the parameters are checked to ensure they meet the constraints. If they do not,
    an error occurs.

:group:
    If provided, parameters will be grouped together when displayed to the user. Any ungrouped parameters
    will display in a special group named `default`. Groups help divide a long list of parameters to make
    them easier to understand.  Examples might include 'basics' and 'advanced'


Build Method
-----------------------

The heart of your model is the build method. Your build method must be called 'build'::

    def build():
        return Workplane("XY").box(1,1,1)

Your build method use any combination of FreeCAD, python, and CadQuery to construct objects.
You must return one of two things:

    1. A CadQuery object, or
    2. A FreeCAD object

In your build script,you retrieve the values of the parameters by using ``<parameter_name>.value``.

The following modules are available when your script runs:

Scripts Using CadQuery  Syntax
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

    :python syntax:
        Python loops, dictionaries, lists, and other standard language structures are available.

    :math:
        Python's math package is imported for you to use

    :FloatParam,IntegerParam,BooleanParam:
        Parameter types used to declare parameters

    :Workplane:
        The CadQuery workplane object, which is the typical starting point for most scripts

    :CQ:
        The CadQuery object, in case you need to decorate a normal FreeCAD object

    :Plane:
        The CadQuery Plane object, in case you need to create non-standard planes


.. warning::

    Though your script is a standard python script, it does **not** run in a standard python environment.

    For security reasons, most python packages, like sys, os, import, and urllib are restricted.


FreeCAD Build Scripts
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

It is recommended that you use CadQuery for your model scripts-- the syntax is much shorter and more convienient.

But if you are willing to write more code, you can get access to all of the features that the FreeCAD library provides.

When your script executes, these FreeCAD objects are in scope as well:

    :Part:
        FreeCAD.Part
    :Vector:
        FreeCAD.Base.Vector
    :Base:
        FreeCAD.Base

**If you use a FreeCAD build script, your build method must return a FreeCAD shape object.**

Should you choose to write your model with the lower-level FreeCAD scripts, you may find this documentation useful:

http://sourceforge.net/apps/mediawiki/free-cad/index.php?title=FreeCAD_API

