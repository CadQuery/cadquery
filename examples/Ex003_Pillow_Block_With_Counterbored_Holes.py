import cadquery as cq

# These can be modified rather than hardcoding values for each dimension.
length = 80.0  # Length of the block
width = 100.0  # Width of the block
thickness = 10.0  # Thickness of the block
center_hole_dia = 22.0  # Diameter of center hole in block
cbore_hole_diameter = 2.4  # Bolt shank/threads clearance hole diameter
cbore_inset = 12.0  # How far from the edge the cbored holes are set
cbore_diameter = 4.4  # Bolt head pocket hole diameter
cbore_depth = 2.1  # Bolt head pocket hole depth

# Create a 3D block based on the dimensions above and add a 22mm center hold
# and 4 counterbored holes for bolts
# 1.  Establishes a workplane that an object can be built on.
# 1a. Uses the X and Y origins to define the workplane, meaning that the
#     positive Z direction is "up", and the negative Z direction is "down".
# 2.  The highest(max) Z face is selected and a new workplane is created on it.
# 3.  The new workplane is used to drill a hole through the block.
# 3a. The hole is automatically centered in the workplane.
# 4.  The highest(max) Z face is selected and a new workplane is created on it.
# 5.  A for-construction rectangle is created on the workplane based on the
#     block's overall dimensions.
# 5a. For-construction objects are used only to place other geometry, they
#     do not show up in the final displayed geometry.
# 6.  The vertices of the rectangle (corners) are selected, and a counter-bored
#     hole is placed at each of the vertices (all 4 of them at once).
result = (
    cq.Workplane("XY")
    .box(length, width, thickness)
    .faces(">Z")
    .workplane()
    .hole(center_hole_dia)
    .faces(">Z")
    .workplane()
    .rect(length - cbore_inset, width - cbore_inset, forConstruction=True)
    .vertices()
    .cboreHole(cbore_hole_diameter, cbore_diameter, cbore_depth)
    .edges("|Z")
    .fillet(2.0)
)

# Displays the result of this script
show_object(result)
