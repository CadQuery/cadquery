#File: Ex008_Polygon_Creation.py
#To use this example file, you need to first follow the "Using CadQuery From Inside FreeCAD"
#instructions here: https://github.com/dcowden/cadquery#installing----using-cadquery-from-inside-freecad

#You run this example by typing the following in the FreeCAD python console, making sure to change
#the path to this example, and the name of the example appropriately.
#import sys
#sys.path.append('/home/user/Downloads/cadquery/examples/FreeCAD')
#import Ex008_Polygon_Creation

#If you need to reload the part after making a change, you can use the following lines within the FreeCAD console.
#reload(Ex008_Polygon_Creation)

#You'll need to delete the original shape that was created, and the new shape should be named sequentially
# (Shape001, etc).

#You can also tie these blocks of code to macros, buttons, and keybindings in FreeCAD for quicker access.
#You can get a more information on this example at
# http://parametricparts.com/docs/examples.html#an-extruded-prismatic-solid

import cadquery
import Part

#The dimensions of the model. These can be modified rather than changing the box's code directly.
width = 3.0
height = 4.0
thickness = 0.25
polygon_sides = 6
polygon_dia = 1.0

#Create a plate with two polygons cut through it
result = cadquery.Workplane("front").box(width, height, thickness).pushPoints([(0, 0.75), (0, -0.75)]) \
    .polygon(polygon_sides, polygon_dia).cutThruAll()

#Boiler plate code to render our solid in FreeCAD's GUI
Part.show(result.toFreecad())