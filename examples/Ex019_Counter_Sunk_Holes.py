import cadquery as cq

# Create a plate with 4 counter-sunk holes in it.
# 1.  Establishes a workplane using an XY object instead of a named plane.
# 2.  Creates a plain box to base future geometry on with the box() function.
# 3.  Selects the top-most face of the box and established a workplane on that.
# 4.  Draws a for-construction rectangle on the workplane which only exists for
#     placing other geometry.
# 5.  Selects the corner vertices of the rectangle and places a counter-sink
#     hole, using each vertex as the center of a hole using the cskHole()
#     function.
# 5a. When the depth of the counter-sink hole is set to None, the hole will be
#     cut through.
result = (
    cq.Workplane(cq.Plane.XY())
    .box(4, 2, 0.5)
    .faces(">Z")
    .workplane()
    .rect(3.5, 1.5, forConstruction=True)
    .vertices()
    .cskHole(0.125, 0.25, 82.0, depth=None)
)

# Displays the result of this script
show_object(result)
