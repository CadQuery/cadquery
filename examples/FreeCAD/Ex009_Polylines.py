#File: Ex009_Polylines.py
#To use this example file, you need to first follow the "Using CadQuery From Inside FreeCAD"
#instructions here: https://github.com/dcowden/cadquery#installing----using-cadquery-from-inside-freecad

#You run this example by typing the following in the FreeCAD python console, making sure to change
#the path to this example, and the name of the example appropriately.
#import sys
#sys.path.append('/home/user/Downloads/cadquery/examples/FreeCAD')
#import Ex009_Polylines

#If you need to reload the part after making a change, you can use the following lines within the FreeCAD console.
#reload(Ex009_Polylines)

#You'll need to delete the original shape that was created, and the new shape should be named sequentially
# (Shape001, etc).

#You can also tie these blocks of code to macros, buttons, and keybindings in FreeCAD for quicker access.
#You can get a more information on this example at
# http://parametricparts.com/docs/examples.html#an-extruded-prismatic-solid

import cadquery
import Part

#Set up our Length, Height, Width, and thickness that will be used to define the locations that the polyline
#is drawn to/thru
(L, H, W, t) = (100.0, 20.0, 20.0, 1.0)

#Define the locations that the polyline will be drawn to/thru
pts = [
    (0, H/2.0),
    (W/2.0, H/2.0),
    (W/2.0, (H/2.0 - t)),
    (t/2.0, (H/2.0-t)),
    (t/2.0, (t - H/2.0)),
    (W/2.0, (t - H/2.0)),
    (W/2.0, H/-2.0),
    (0, H/-2.0)
]

#We generate half of the I-beam outline and then mirror it to create the full I-beam
result = cadquery.Workplane("front").polyline(pts).mirrorY().extrude(L)

#Boiler plate code to render our solid in FreeCAD's GUI
Part.show(result.toFreecad())