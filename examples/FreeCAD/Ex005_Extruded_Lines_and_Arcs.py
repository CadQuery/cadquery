#File: Ex005_Extruded_Lines_and_Arcs.py
#To use this example file, you need to first follow the "Using CadQuery From Inside FreeCAD"
#instructions here: https://github.com/dcowden/cadquery#installing----using-cadquery-from-inside-freecad

#You run this example by typing the following in the FreeCAD python console, making sure to change
#the path to this example, and the name of the example appropriately.
#import sys
#sys.path.append('/home/user/Downloads/cadquery/examples/FreeCAD')
#import Ex005_Extruded_Lines_and_Arcs

#If you need to reload the part after making a change, you can use the following lines within the FreeCAD console.
#reload(Ex005_Extruded_Lines_and_Arcs)

#You'll need to delete the original shape that was created, and the new shape should be named sequentially
#(Shape001, etc).

#You can also tie these blocks of code to macros, buttons, and keybindings in FreeCAD for quicker access.
#You can get a more information on this example at
# http://parametricparts.com/docs/examples.html#an-extruded-prismatic-solid

import cadquery
import Part

#The dimensions of the model. These can be modified rather than changing the box's code directly.
width = 2.0
thickness = 0.25

#Extrude a plate outline made of lines and an arc
result = cadquery.Workplane("front").lineTo(width, 0).lineTo(width, 1.0).threePointArc((1.0, 1.5),(0.0, 1.0)) \
    .close().extrude(thickness)

#Boiler plate code to render our solid in FreeCAD's GUI
Part.show(result.toFreecad())