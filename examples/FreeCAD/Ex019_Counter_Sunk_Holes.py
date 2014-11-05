#File: Ex019_Counter_Sunk_Holes.py
#To use this example file, you need to first follow the "Using CadQuery From Inside FreeCAD"
#instructions here: https://github.com/dcowden/cadquery#installing----using-cadquery-from-inside-freecad

#You run this example by typing the following in the FreeCAD python console, making sure to change
#the path to this example, and the name of the example appropriately.
#import sys
#sys.path.append('/home/user/Downloads/cadquery/examples/FreeCAD')
#import Ex019_Counter_Sunk_Holes

#If you need to reload the part after making a change, you can use the following lines within the FreeCAD console.
#reload(Ex019_Counter_Sunk_Holes)

#You'll need to delete the original shape that was created, and the new shape should be named sequentially
# (Shape001, etc).

#You can also tie these blocks of code to macros, buttons, and keybindings in FreeCAD for quicker access.
#You can get a more information on this example at
# http://parametricparts.com/docs/examples.html#an-extruded-prismatic-solid

import cadquery
import Part

#Create a plate with 4 counter-sunk holes in it
result = cadquery.Workplane(cadquery.Plane.XY()).box(4, 2, 0.5).faces(">Z").workplane() \
    .rect(3.5, 1.5, forConstruction=True)\
    .vertices().cskHole(0.125, 0.25, 82.0, depth=None)

#Boiler plate code to render our solid in FreeCAD's GUI
Part.show(result.toFreecad())
