#File: Ex024_Using_FreeCAD_Solids_as_CQ_Objects.py
#To use this example file, you need to first follow the "Using CadQuery From Inside FreeCAD"
#instructions here: https://github.com/dcowden/cadquery#installing----using-cadquery-from-inside-freecad

#You run this example by typing the following in the FreeCAD python console, making sure to change
#the path to this example, and the name of the example appropriately.
#import sys
#sys.path.append('/home/user/Downloads/cadquery/examples/FreeCAD')
#import Ex024_Using_FreeCAD_Solids_as_CQ_Objects

#If you need to reload the part after making a change, you can use the following lines within the FreeCAD console.
#reload(Ex024_Using_FreeCAD_Solids_as_CQ_Objects)

#You'll need to delete the original shape that was created, and the new shape should be named sequentially
# (Shape001, etc).

#You can also tie these blocks of code to macros, buttons, and keybindings in FreeCAD for quicker access.
#You can get a more information on this example at
# http://parametricparts.com/docs/examples.html#an-extruded-prismatic-solid

import cadquery, FreeCAD, Part

#Create a new document that we can draw our model on
newDoc = FreeCAD.newDocument()

#shows a 1x1x1 FreeCAD cube in the display
initialBox = newDoc.addObject("Part::Box","initialBox")
newDoc.recompute()

#Make a CQ object
cqBox = cadquery.CQ(cadquery.Solid(initialBox.Shape))

#Extrude a peg
newThing = cqBox.faces(">Z").workplane().circle(0.5).extrude(0.25)

#Add a FreeCAD object to the tree and then store a CQ object in it
nextShape = newDoc.addObject("Part::Feature", "nextShape")
nextShape.Shape = newThing.val().wrapped

#Rerender the doc to see what the new solid looks like
newDoc.recompute()
