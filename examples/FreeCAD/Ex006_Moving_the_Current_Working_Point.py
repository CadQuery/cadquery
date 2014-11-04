#File: Ex006_Moving_the_Current_Working_Point.py
#To use this example file, you need to first follow the "Using CadQuery From Inside FreeCAD"
#instructions here: https://github.com/dcowden/cadquery#installing----using-cadquery-from-inside-freecad

#You run this example by typing the following in the FreeCAD python console, making sure to change
#the path to this example, and the name of the example appropriately.
#import sys
#sys.path.append('/home/user/Downloads/cadquery/examples/FreeCAD')
#import Ex006_Moving_the_Current_Working_Point

#If you need to reload the part after making a change, you can use the following lines within the FreeCAD console.
#reload(Ex006_Moving_the_Current_Working_Point)

#You'll need to delete the original shape that was created, and the new shape should be named sequentially
# (Shape001, etc).

#You can also tie these blocks of code to macros, buttons, and keybindings in FreeCAD for quicker access.
#You can get a more information on this example at
# http://parametricparts.com/docs/examples.html#an-extruded-prismatic-solid

import cadquery
import Part

#The dimensions of the model. These can be modified rather than changing the box's code directly.
circle_radius = 3.0
thickness = 0.25

#Make the plate with two cutouts in it
result = cadquery.Workplane("front").circle(circle_radius) # Current point is the center of the circle, at (0,0)
result = result.center(1.5,0.0).rect(0.5,0.5) # New work center is  (1.5,0.0)

result = result.center(-1.5,1.5).circle(0.25) # New work center is ( 0.0,1.5).
#The new center is specified relative to the previous center, not global coordinates!

result = result.extrude(thickness)

#Boiler plate code to render our solid in FreeCAD's GUI
Part.show(result.toFreecad())