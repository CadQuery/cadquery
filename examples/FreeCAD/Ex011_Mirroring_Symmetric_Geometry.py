#File: Ex011_Mirroring_Symmetric_Geometry.py
#To use this example file, you need to first follow the "Using CadQuery From Inside FreeCAD"
#instructions here: https://github.com/dcowden/cadquery#installing----using-cadquery-from-inside-freecad

#You run this example by typing the following in the FreeCAD python console, making sure to change
#the path to this example, and the name of the example appropriately.
#import sys
#sys.path.append('/home/user/Downloads/cadquery/examples/FreeCAD')
#import Ex011_Mirroring_Symmetric_Geometry

#If you need to reload the part after making a change, you can use the following lines within the FreeCAD console.
#reload(Ex011_Mirroring_Symmetric_Geometry)

#You'll need to delete the original shape that was created, and the new shape should be named sequentially
# (Shape001, etc).

#You can also tie these blocks of code to macros, buttons, and keybindings in FreeCAD for quicker access.
#You can get a more information on this example at
# http://parametricparts.com/docs/examples.html#an-extruded-prismatic-solid

import cadquery
import Part

#1.0 is the distance, not coordinate
r = cadquery.Workplane("front").hLine(1.0)

#hLineTo allows using xCoordinate not distance
r = r.vLine(0.5).hLine(-0.25).vLine(-0.25).hLineTo(0.0)

#Mirror the geometry and extrude
result = r.mirrorY().extrude(0.25)

#Boiler plate code to render our solid in FreeCAD's GUI
Part.show(result.toFreecad())
