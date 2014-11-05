#File: Ex021_Splitting_an_Object.py
#To use this example file, you need to first follow the "Using CadQuery From Inside FreeCAD"
#instructions here: https://github.com/dcowden/cadquery#installing----using-cadquery-from-inside-freecad

#You run this example by typing the following in the FreeCAD python console, making sure to change
#the path to this example, and the name of the example appropriately.
#import sys
#sys.path.append('/home/user/Downloads/cadquery/examples/FreeCAD')
#import Ex021_Splitting_an_Object

#If you need to reload the part after making a change, you can use the following lines within the FreeCAD console.
#reload(Ex021_Splitting_an_Object)

#You'll need to delete the original shape that was created, and the new shape should be named sequentially
# (Shape001, etc).

#You can also tie these blocks of code to macros, buttons, and keybindings in FreeCAD for quicker access.
#You can get a more information on this example at
# http://parametricparts.com/docs/examples.html#an-extruded-prismatic-solid

import cadquery
import Part

#Create a simple block with a hole through it that we can split
c = cadquery.Workplane("XY").box(1, 1, 1).faces(">Z").workplane().circle(0.25).cutThruAll()

#Cut the block in half sideways
result = c.faces(">Y").workplane(-0.5).split(keepTop=True)

#Boiler plate code to render our solid in FreeCAD's GUI
Part.show(result.toFreecad())
