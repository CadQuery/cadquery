import cadquery as cq

# 1.  Establishes a workplane that an object can be built on.
# 1a. Uses the named plane orientation "front" to define the workplane, meaning
#     that the positive Z direction is "up", and the negative Z direction
#     is "down".
# 2.  Creates a 3D box that will have geometry based off it later.
result = cq.Workplane("front").box(3, 2, 0.5)

# 3.  The lowest face in the X direction is selected with the <X selector.
# 4. A new workplane is created
# 4a.The workplane is offset from the object surface so that it is not touching
#    the original box.
result = result.faces("<X").workplane(offset=0.75)

# 5. Creates a thin disc on the offset workplane that is floating near the box.
result = result.circle(1.0).extrude(0.5)

# Displays the result of this script
show_object(result)
