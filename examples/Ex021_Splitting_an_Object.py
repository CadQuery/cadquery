import cadquery as cq

# Create a simple block with a hole through it that we can split.
# 1.  Establishes a workplane that an object can be built on.
# 1a. Uses the X and Y origins to define the workplane, meaning that the
#     positive Z direction is "up", and the negative Z direction is "down".
# 2.  Creates a plain box to base future geometry on with the box() function.
# 3.  Selects the top-most face of the box and establishes a workplane on it
#     that new geometry can be built on.
# 4.  Draws a 2D circle on the new workplane and then uses it to cut a hole
#     all the way through the box.
c = cq.Workplane("XY").box(1, 1, 1).faces(">Z").workplane().circle(0.25).cutThruAll()

# 5.  Selects the face furthest away from the origin in the +Y axis direction.
# 6.  Creates an offset workplane that is set in the center of the object.
# 6a. One possible improvement to this script would be to make the dimensions
#     of the box variables, and then divide the Y-axis dimension by 2.0 and
#     use that to create the offset workplane.
# 7.  Uses the embedded workplane to split the object, keeping only the "top"
#     portion.
result = c.faces(">Y").workplane(-0.5).split(keepTop=True)

# Displays the result of this script
show_object(result)
