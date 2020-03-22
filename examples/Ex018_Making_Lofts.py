import cadquery as cq

# Create a lofted section between a rectangle and a circular section.
# 1.  Establishes a workplane that an object can be built on.
# 1a. Uses the named plane orientation "front" to define the workplane, meaning
#     that the positive Z direction is "up", and the negative Z direction
#     is "down".
# 2.  Creates a plain box to base future geometry on with the box() function.
# 3.  Selects the top-most Z face of the box.
# 4.  Draws a 2D circle at the center of the the top-most face of the box.
# 5.  Creates a workplane 3 mm above the face the circle was drawn on.
# 6.  Draws a 2D circle on the new, offset workplane.
# 7.  Creates a loft between the circle and the rectangle.
result = (
    cq.Workplane("front")
    .box(4.0, 4.0, 0.25)
    .faces(">Z")
    .circle(1.5)
    .workplane(offset=3.0)
    .rect(0.75, 0.5)
    .loft(combine=True)
)

# Displays the result of this script
show_object(result)
