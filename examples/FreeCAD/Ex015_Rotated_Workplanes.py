#File: Ex015_Rotated_Workplanes.py
#To use this example file, you need to first follow the "Using CadQuery From Inside FreeCAD"
#instructions here: https://github.com/dcowden/cadquery#installing----using-cadquery-from-inside-freecad

#You run this example by typing the following in the FreeCAD python console, making sure to change
#the path to this example, and the name of the example appropriately.
#import sys
#sys.path.append('/home/user/Downloads/cadquery/examples/FreeCAD')
#import Ex015_Rotated_Workplanes

#If you need to reload the part after making a change, you can use the following lines within the FreeCAD console.
#reload(Ex015_Rotated_Workplanes)

#You'll need to delete the original shape that was created, and the new shape should be named sequentially
# (Shape001, etc).

#You can also tie these blocks of code to macros, buttons, and keybindings in FreeCAD for quicker access.
#You can get a more information on this example at
# http://parametricparts.com/docs/examples.html#an-extruded-prismatic-solid

import cadquery
from cadquery import Vector
import Part

#Create a rotated workplane and put holes in each corner of a rectangle on that workplane, producing angled holes
#in the face
result = cadquery.Workplane("front").box(4.0, 4.0, 0.25).faces(">Z").workplane()  \
    .transformed(offset=Vector(0, -1.5, 1.0), rotate=Vector(60, 0, 0)) \
    .rect(1.5, 1.5, forConstruction=True).vertices().hole(0.25)

#Boiler plate code to render our solid in FreeCAD's GUI
Part.show(result.toFreecad())
