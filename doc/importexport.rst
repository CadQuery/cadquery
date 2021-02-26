.. _importexport:

******************************
Importing and Exporting Files
******************************

Introduction
============

The purpose of this section is to explain how to import external file formats into CadQuery, and export files from 
it as well. While the external file formats can be used to interchange CAD model data with out software, CadQuery 
does not support any formats that carry parametric data with them at this time. The only format that is fully 
parametric is CadQuery's own Python format. Below are lists of the import and export file formats that CadQuery 
supports.

Import Formats
###############

* DXF
* STEP

Export Formats
###############

* DXF
* SVG
* STEP
* STL
* AMF
* TJS
* VRML

Notes on the Formats
#######################

* DXF is useful for importing complex 2D profiles that would be tedious to create using CadQuery's 2D operations. An example is that the 2D profiles of aluminum extrusion are often provided in DXF format. This can be imported and extruded to create the length of extrusion that is needed in a design.
* STEP files are useful for interchanging model data with other CAD and analysis systems, such as FreeCAD.
* STL and AMF files are mesh-based formats which are typically used in additive manufacturing (i.e. 3D printing). AMF files support more features, but are not as widely supported as STL files.
* TJS is short for ThreeJS, and is a JSON format that is useful for displaying 3D models in web browsers. The TJS format is used to display embedded 3D examples within the CadQuery documentation.
* VRML is a format for representing interactive 3D objects in a web browser.

Importing DXF
##############

DXF files can be imported using the :py:meth:`importers.importDXF` method. There are 3 parameters that can be 
passed this method to control how the DXF is handled.

* *fileName* - The path and name of the DXF file to be imported.
* *tol* - The tolerance used for merging edges into wires (default: 1e-6).
* *exclude* - A list of layer names not to import (default: []).

Importing a DXF profile with default settings and using it within a CadQuery script is shown in the following code.

.. code-block:: python

    import cadquery as cq

    result = (
        cq.importers.importDXF('/path/to/dxf/circle.dxf')
        .wires().toPending()
        .extrude(10)
        )

Note the use of the :py:meth:`Workplane.wires` and :py:meth:`Workplane.toPending` methods to make the DXF profile 
ready for use during subsequent operations. Calling toPending() tells CadQuery to make the edges/wires available 
to the next operation that is called in the chain.

Importing STEP
###############

STEP files can be imported using the :py:meth:`importers.importStep` method (note the capitalization of "Step"). 
There are no parameters for this method other than the file path to import.

.. code-block:: python

    import cadquery as cq

    result = cq.importers.importStep('/path/to/step/block.stp')

Exporting SVG
##############

The SVG exporter has several options which can be useful for getting the desired final output. Those 
options are as follows.

* *width* - Document width of the resulting image.
* *height* - Document height of the resulting image.
* *marginLeft* - Inset margin from the left side of the document.
* *marginTop* - Inset margin from the top side of the document.
* *projectionDir* - Direction the camera will view the shape from.
* *showAxes* - Whether or not to show the axes indicator, which will only be visible when the projectionDir is also at the default.
* *strokeWidth* - Width of the line that visible edges are drawn with.
* *strokeColor* - Color of the line that visible edges are drawn with.
* *hiddenColor* - Color of the line that hidden edges are drawn with.
* *showHidden* - Whether or not to show hidden lines.

The options are passed to the exporter in a dictionary, and can be left out to force the SVG to be created with default options. 
Below are a few examples.

Without options:

.. code-block:: python

    import cadquery as cq
    from cadquery import exporters

    result = cq.Workplane().box(10, 10, 10)

    exporters.export(result, '/path/to/file/box.svg')

Results in:

..  image:: _static/importexport/box_default_options.svg

Note that the exporters API figured out the format type from the file extension. The format 
type can be set explicitly by using :py:class:`exporters.ExportTypes`.

The following is an example of using options to alter the resulting SVG output by passing in the opt parameter.

.. code-block:: python

    import cadquery as cq
    from cadquery import exporters

    result = cq.Workplane().box(10, 10, 10)

    exporters.export(
                result,
                '/path/to/file/box_custom_options.svg',
                opt={
                    "width": 300,
                    "height": 300,
                    "marginLeft": 10,
                    "marginTop": 10,
                    "showAxes": False,
                    "projectionDir": (0.5, 0.5, 0.5),
                    "strokeWidth": 0.25,
                    "strokeColor": (255, 0, 0),
                    "hiddenColor": (0, 0, 255),
                    "showHidden": True,
                },
            )

Which results in the following image:

..  image:: _static/importexport/box_custom_options.svg

Exporting STL
##############

The STL exporter is capable of adjusting the quality of the resulting STL, and accepts the following options.

* ** - 
* ** - 
* ** - 

Exporting Other Formats
########################
