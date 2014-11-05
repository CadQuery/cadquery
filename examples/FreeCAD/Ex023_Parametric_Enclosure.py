#File: Ex023_Parametric_Enclosure.py
#To use this example file, you need to first follow the "Using CadQuery From Inside FreeCAD"
#instructions here: https://github.com/dcowden/cadquery#installing----using-cadquery-from-inside-freecad

#You run this example by typing the following in the FreeCAD python console, making sure to change
#the path to this example, and the name of the example appropriately.
#import sys
#sys.path.append('/home/user/Downloads/cadquery/examples/FreeCAD')
#import Ex023_Parametric_Enclosure

#If you need to reload the part after making a change, you can use the following lines within the FreeCAD console.
#reload(Ex023_Parametric_Enclosure)

#You'll need to delete the original shape that was created, and the new shape should be named sequentially
# (Shape001, etc).

#You can also tie these blocks of code to macros, buttons, and keybindings in FreeCAD for quicker access.
#You can get a more information on this example at
# http://parametricparts.com/docs/examples.html#an-extruded-prismatic-solid

import cadquery
import Part

#Parameter definitions
p_outerWidth = 100.0  # Outer width of box enclosure
p_outerLength = 150.0  # Outer length of box enclosure
p_outerHeight = 50.0  # Outer height of box enclosure

p_thickness = 3.0  # Thickness of the box walls
p_sideRadius = 10.0  # Radius for the curves around the sides of the bo
p_topAndBottomRadius = 2.0  # Radius for the curves on the top and bottom edges of the box

p_screwpostInset = 12.0  # How far in from the edges the screwposts should be placed
p_screwpostID = 4.0  # Inner diameter of the screwpost holes, should be roughly screw diameter not including threads
p_screwpostOD = 10.0  # Outer diameter of the screwposts. Determines overall thickness of the posts

p_boreDiameter = 8.0  # Diameter of the counterbore hole, if any
p_boreDepth = 1.0  # Depth of the counterbore hole, if
p_countersinkDiameter = 0.0  # Outer diameter of countersink. Should roughly match the outer diameter of the screw head
p_countersinkAngle = 90.0  # Countersink angle (complete angle between opposite sides, not from center to one side)
p_flipLid = True  # Whether to place the lid with the top facing down or not.
p_lipHeight = 1.0  # Height of lip on the underside of the lid. Sits inside the box body for a snug fit.

#Outer shell
oshell = cadquery.Workplane("XY").rect(p_outerWidth, p_outerLength).extrude(p_outerHeight + p_lipHeight)

#Weird geometry happens if we make the fillets in the wrong order
if p_sideRadius > p_topAndBottomRadius:
    oshell.edges("|Z").fillet(p_sideRadius)
    oshell.edges("#Z").fillet(p_topAndBottomRadius)
else:
    oshell.edges("#Z").fillet(p_topAndBottomRadius)
    oshell.edges("|Z").fillet(p_sideRadius)

#Inner shell
ishell = oshell.faces("<Z").workplane(p_thickness, True)\
    .rect((p_outerWidth - 2.0 * p_thickness),(p_outerLength - 2.0 * p_thickness))\
    .extrude((p_outerHeight - 2.0 * p_thickness), False) # Set combine false to produce just the new boss
ishell.edges("|Z").fillet(p_sideRadius - p_thickness)

#Make the box outer box
box = oshell.cut(ishell)

#Make the screwposts
POSTWIDTH = (p_outerWidth - 2.0 * p_screwpostInset)
POSTLENGTH = (p_outerLength - 2.0 * p_screwpostInset)

postCenters = box.faces(">Z").workplane(-p_thickness)\
    .rect(POSTWIDTH, POSTLENGTH, forConstruction=True)\
    .vertices()

for v in postCenters.all():
   v.circle(p_screwpostOD / 2.0).circle(p_screwpostID / 2.0)\
        .extrude((-1.0) * ((p_outerHeight + p_lipHeight) - (2.0 * p_thickness)), True)

#Split lid into top and bottom parts
(lid, bottom) = box.faces(">Z").workplane(-p_thickness - p_lipHeight).split(keepTop=True, keepBottom=True).all()

#Translate the lid, and subtract the bottom from it to produce the lid inset
lowerLid = lid.translate((0, 0, -p_lipHeight))
cutlip = lowerLid.cut(bottom).translate((p_outerWidth + p_thickness, 0, p_thickness - p_outerHeight + p_lipHeight))

#Compute centers for counterbore/countersink or counterbore
topOfLidCenters = cutlip.faces(">Z").workplane().rect(POSTWIDTH, POSTLENGTH, forConstruction=True).vertices()

#Add holes of the desired type
if p_boreDiameter > 0 and p_boreDepth > 0:
    topOfLid = topOfLidCenters.cboreHole(p_screwpostID, p_boreDiameter, p_boreDepth, (2.0) * p_thickness)
elif p_countersinkDiameter > 0 and p_countersinkAngle > 0:
    topOfLid = topOfLidCenters.cskHole(p_screwpostID, p_countersinkDiameter, p_countersinkAngle, (2.0) * p_thickness)
else:
    topOfLid= topOfLidCenters.hole(p_screwpostID, 2.0 * p_thickness)

#Flip lid upside down if desired
if p_flipLid:
    topOfLid.rotateAboutCenter((1, 0, 0), 180)

#Return the combined result
result = topOfLid.combineSolids(bottom)

#Boiler plate code to render our solid in FreeCAD's GUI
Part.show(result.toFreecad())
