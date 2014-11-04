#File: Ex003_Pillow_Block_With_Counterbored_Holes.py
#To use this example file, you need to first follow the "Using CadQuery From Inside FreeCAD"
#instructions here: https://github.com/dcowden/cadquery#installing----using-cadquery-from-inside-freecad

#You run this example by typing the following in the FreeCAD python console, making sure to change
#the path to this example, and the name of the example appropriately.
#import sys
#sys.path.append('/home/user/Downloads/cadquery/examples/FreeCAD')
#import Ex003_Pillow_Block_With_Counterbored_Holes

#If you need to reload the part after making a change, you can use the following lines within the FreeCAD console.
#reload(Ex003_Pillow_Block_With_Counterbored_Holes)

#You'll need to delete the original shape that was created, and the new shape should be named sequentially
# (Shape001, etc).

#You can also tie these blocks of code to macros, buttons, and keybindings in FreeCAD for quicker access.
#You can get a more in-depth explanation of this example at http://parametricparts.com/docs/quickstart.html

import cadquery
import Part

#The dimensions of the box. These can be modified rather than changing the box's code directly.
length = 80.0
height = 60.0
thickness = 10.0
center_hole_dia = 22.0
cbore_hole_diameter = 2.4
cbore_diameter = 4.4
cbore_depth = 2.1

#Create a 3D box based on the dimension variables above and add 4 counterbored holes
result = cadquery.Workplane("XY").box(length, height, thickness) \
    .faces(">Z").workplane().hole(center_hole_dia) \
    .faces(">Z").workplane() \
    .rect(length - 8.0, height - 8.0, forConstruction = True) \
    .vertices().cboreHole(cbore_hole_diameter, cbore_diameter, cbore_depth)

#Boiler plate code to render our solid in FreeCAD's GUI
Part.show(result.toFreecad())