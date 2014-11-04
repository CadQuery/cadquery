#File: Ex007_Using_Point_Lists.py
#To use this example file, you need to first follow the "Using CadQuery From Inside FreeCAD"
#instructions here: https://github.com/dcowden/cadquery#installing----using-cadquery-from-inside-freecad

#You run this example by typing the following in the FreeCAD python console, making sure to change
#the path to this example, and the name of the example appropriately.
#import sys
#sys.path.append('/home/user/Downloads/cadquery/examples/FreeCAD')
#import Ex007_Using_Point_Lists

#If you need to reload the part after making a change, you can use the following lines within the FreeCAD console.
#reload(Ex007_Using_Point_Lists)

#You'll need to delete the original shape that was created, and the new shape should be named sequentially
# (Shape001, etc).

#You can also tie these blocks of code to macros, buttons, and keybindings in FreeCAD for quicker access.
#You can get a more information on this example at
# http://parametricparts.com/docs/examples.html#an-extruded-prismatic-solid

import cadquery
import Part

#The dimensions of the model. These can be modified rather than changing the box's code directly.
plate_radius = 2.0
hole_pattern_radius = 0.25
thickness = 0.125

#Make the plate with 4 holes in it at various points
r = cadquery.Workplane("front").circle(plate_radius)        # Make the base
r = r.pushPoints([(1.5, 0), (0, 1.5), (-1.5, 0), (0, -1.5)])   # Now four points are on the stack
r = r.circle(hole_pattern_radius)                        	# Circle will operate on all four points
result = r.extrude(thickness)

#Boiler plate code to render our solid in FreeCAD's GUI
Part.show(result.toFreecad())