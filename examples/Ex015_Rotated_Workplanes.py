import cadquery as cq

# 1.  Establishes a workplane that an object can be built on.
# 1a. Uses the named plane orientation "front" to define the workplane, meaning
#     that the positive Z direction is "up", and the negative Z direction
#     is "down".
# 2.  Creates a plain box to base future geometry on with the box() function.
# 3.  Selects the top-most Z face of the box.
# 4.  Creates a new workplane and then moves and rotates it with the
#     transformed function.
# 5.  Creates a for-construction rectangle that only exists to use for placing
#     other geometry.
# 6.  Selects the vertices of the for-construction rectangle.
# 7.  Places holes at the center of each selected vertex.
# 7a. Since the workplane is rotated, this results in angled holes in the face.
result = (
    cq.Workplane("front")
    .box(4.0, 4.0, 0.25)
    .faces(">Z")
    .workplane()
    .transformed(offset=(0, -1.5, 1.0), rotate=(60, 0, 0))
    .rect(1.5, 1.5, forConstruction=True)
    .vertices()
    .hole(0.25)
)

# Displays the result of this script
show_object(result)
