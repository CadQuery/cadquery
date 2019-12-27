import cadquery as cq

# Create a block with holes in each corner of a rectangle on that workplane.
# 1.  Establishes a workplane that an object can be built on.
# 1a. Uses the named plane orientation "front" to define the workplane, meaning
#     that the positive Z direction is "up", and the negative Z direction
#     is "down".
# 2.  Creates a plain box to base future geometry on with the box() function.
# 3.  Selects the top-most Z face of the box.
# 4.  Creates a new workplane to build new geometry on.
# 5.  Creates a for-construction rectangle that only exists to use for placing
#     other geometry.
# 6.  Selects the vertices of the for-construction rectangle.
# 7.  Places holes at the center of each selected vertex.
result = (
    cq.Workplane("front")
    .box(2, 2, 0.5)
    .faces(">Z")
    .workplane()
    .rect(1.5, 1.5, forConstruction=True)
    .vertices()
    .hole(0.125)
)

# Displays the result of this script
show_object(result)
