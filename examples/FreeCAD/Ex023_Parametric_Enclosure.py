import cadquery as cq

# Parameter definitions
p_outerWidth = 100.0  # Outer width of box enclosure
p_outerLength = 150.0  # Outer length of box enclosure
p_outerHeight = 50.0  # Outer height of box enclosure

p_thickness = 3.0  # Thickness of the box walls
p_sideRadius = 10.0  # Radius for the curves around the sides of the bo
p_topAndBottomRadius = 2.0  # Radius for the curves on the top and bottom edges

p_screwpostInset = 12.0  # How far in from the edges the screwposts should be
p_screwpostID = 4.0  # Inner diameter of the screwpost holes, should be roughly screw diameter not including threads
p_screwpostOD = 10.0  # Outer diameter of the screwposts. Determines overall thickness of the posts

p_boreDiameter = 8.0  # Diameter of the counterbore hole, if any
p_boreDepth = 1.0  # Depth of the counterbore hole, if
p_countersinkDiameter = 0.0  # Outer diameter of countersink. Should roughly match the outer diameter of the screw head
p_countersinkAngle = 90.0  # Countersink angle (complete angle between opposite sides, not from center to one side)
p_lipHeight = 1.0  # Height of lip on the underside of the lid. Sits inside the box body for a snug fit.

# Outer shell
oshell = cq.Workplane("XY").rect(p_outerWidth, p_outerLength) \
                                 .extrude(p_outerHeight + p_lipHeight)

# Weird geometry happens if we make the fillets in the wrong order
if p_sideRadius > p_topAndBottomRadius:
    oshell.edges("|Z").fillet(p_sideRadius)
    oshell.edges("#Z").fillet(p_topAndBottomRadius)
else:
    oshell.edges("#Z").fillet(p_topAndBottomRadius)
    oshell.edges("|Z").fillet(p_sideRadius)

# Inner shell
ishell = oshell.faces("<Z").workplane(p_thickness, True)\
    .rect((p_outerWidth - 2.0 * p_thickness), (p_outerLength - 2.0 * p_thickness))\
    .extrude((p_outerHeight - 2.0 * p_thickness), False) # Set combine false to produce just the new boss
ishell.edges("|Z").fillet(p_sideRadius - p_thickness)

# Make the box outer box
box = oshell.cut(ishell)

# Make the screwposts
POSTWIDTH = (p_outerWidth - 2.0 * p_screwpostInset)
POSTLENGTH = (p_outerLength - 2.0 * p_screwpostInset)

postCenters = box.faces(">Z").workplane(-p_thickness)\
    .rect(POSTWIDTH, POSTLENGTH, forConstruction=True)\
    .vertices()

for v in postCenters.all():
    v.circle(p_screwpostOD / 2.0).circle(p_screwpostID / 2.0)\
     .extrude((-1.0) * ((p_outerHeight + p_lipHeight) - (2.0 * p_thickness)), True)

# Split lid into top and bottom parts
(lid, bottom) = box.faces(">Z").workplane(-p_thickness - p_lipHeight).split(keepTop=True, keepBottom=True).all()

# Translate the lid, and subtract the bottom from it to produce the lid inset
lowerLid = lid.translate((0, 0, -p_lipHeight))
cutlip = lowerLid.cut(bottom).translate((p_outerWidth + p_thickness, 0, p_thickness - p_outerHeight + p_lipHeight))

# Compute centers for counterbore/countersink or counterbore
topOfLidCenters = cutlip.faces(">Z").workplane().rect(POSTWIDTH, POSTLENGTH, forConstruction=True).vertices()

# Add holes of the desired type
if p_boreDiameter > 0 and p_boreDepth > 0:
    topOfLid = topOfLidCenters.cboreHole(p_screwpostID, p_boreDiameter, p_boreDepth, (2.0) * p_thickness)
elif p_countersinkDiameter > 0 and p_countersinkAngle > 0:
    topOfLid = topOfLidCenters.cskHole(p_screwpostID, p_countersinkDiameter, p_countersinkAngle, (2.0) * p_thickness)
else:
    topOfLid= topOfLidCenters.hole(p_screwpostID, 2.0 * p_thickness)

# Return the combined result
result = topOfLid.combineSolids(bottom)

# Displays the result of this script
show_object(result)
