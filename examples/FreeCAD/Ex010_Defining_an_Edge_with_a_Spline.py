#File: Ex010_Defining_an_Edge_with_a_Spline.py
#To use this example file, you need to first follow the "Using CadQuery From Inside FreeCAD"
#instructions here: https://github.com/dcowden/cadquery#installing----using-cadquery-from-inside-freecad

#You run this example by typing the following in the FreeCAD python console, making sure to change
#the path to this example, and the name of the example appropriately.
#import sys
#sys.path.append('/home/user/Downloads/cadquery/examples/FreeCAD')
#import Ex010_Defining_an_Edge_with_a_Spline

#If you need to reload the part after making a change, you can use the following lines within the FreeCAD console.
#reload(Ex010_Defining_an_Edge_with_a_Spline)

#You'll need to delete the original shape that was created, and the new shape should be named sequentially
# (Shape001, etc).

#You can also tie these blocks of code to macros, buttons, and keybindings in FreeCAD for quicker access.
#You can get a more information on this example at
# http://parametricparts.com/docs/examples.html#an-extruded-prismatic-solid

import cadquery
import Part

#The workplane we want to create the spline on to extrude
s = cadquery.Workplane("XY")

#The points that the spline will pass through
sPnts = [
    (2.75, 1.5),
    (2.5, 1.75),
    (2.0, 1.5),
    (1.5, 1.0),
    (1.0, 1.25),
    (0.5, 1.0),
    (0, 1.0)
]

#Generate our plate with the spline feature and make sure it's a closed entity
r = s.lineTo(3.0, 0).lineTo(3.0, 1.0).spline(sPnts).close()

#Extrude to turn the wire into a plate
result = r.extrude(0.5)

#Boiler plate code to render our solid in FreeCAD's GUI
Part.show(result.toFreecad())