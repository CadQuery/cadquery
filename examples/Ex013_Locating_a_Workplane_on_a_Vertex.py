import cadquery as cq

# 1.  Establishes a workplane that an object can be built on.
# 1a. Uses the named plane orientation "front" to define the workplane, meaning
#     that the positive Z direction is "up", and the negative Z direction
#     is "down".
# 2.  Creates a 3D box that will have a hole placed in it later.
result = cq.Workplane("front").box(3, 2, 0.5)

# 3.  Select the lower left vertex and make a workplane.
# 3a. The top-most Z face is selected using the >Z selector.
# 3b. The lower-left vertex of the faces is selected with the <XY selector.
# 3c. A new workplane is created on the vertex to build future geometry on.
result = result.faces(">Z").vertices("<XY").workplane(centerOption="CenterOfMass")

# 4.  A circle is drawn with the selected vertex as its center.
# 4a. The circle is cut down through the box to cut the corner out.
result = result.circle(1.0).cutThruAll()

# Displays the result of this script
show_object(result)
