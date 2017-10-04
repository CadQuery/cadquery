# This example is meant to be used from within the CadQuery module of FreeCAD.
import cadquery
import FreeCAD

# Create a new document that we can draw our model on
newDoc = FreeCAD.newDocument()

# Shows a 1x1x1 FreeCAD cube in the display
initialBox = newDoc.addObject("Part::Box", "initialBox")
newDoc.recompute()

# Make a CQ object
cqBox = cadquery.CQ(cadquery.Solid(initialBox.Shape))

# Extrude a peg
newThing = cqBox.faces(">Z").workplane().circle(0.5).extrude(0.25)

# Add a FreeCAD object to the tree and then store a CQ object in it
nextShape = newDoc.addObject("Part::Feature", "nextShape")
nextShape.Shape = newThing.val().wrapped

# Rerender the doc to see what the new solid looks like
newDoc.recompute()
