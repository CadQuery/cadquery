import cadquery as cq

# These can be modified rather than hardcoding values for each dimension.
width = 3.0  # The width of the plate
height = 4.0  # The height of the plate
thickness = 0.25  # The thickness of the plate
polygon_sides = 6  # The number of sides that the polygonal holes should have
polygon_dia = 1.0  # The diameter of the circle enclosing the polygon points

# Create a plate with two polygons cut through it
# 1.  Establishes a workplane that an object can be built on.
# 1a. Uses the named plane orientation "front" to define the workplane, meaning
#     that the positive Z direction is "up", and the negative Z direction
#     is "down".
# 2.  A 3D box is created in one box() operation to represent the plate.
# 2a. The box is centered around the origin, which creates a result that may
#     be unituitive when the polygon cuts are made.
# 3.  2 points are pushed onto the stack and will be used as centers for the
#     polygonal holes.
# 4.  The two polygons are created, on for each point, with one call to
#     polygon() using the number of sides and the circle that bounds the
#     polygon.
# 5.  The polygons are cut thru all objects that are in the line of extrusion.
# 5a. A face was not selected, and so the polygons are created on the
#     workplane. Since the box was centered around the origin, the polygons end
#     up being in the center of the box. This makes them cut from the center to
#     the outside along the normal (positive direction).
# 6.  The polygons are cut through all objects, starting at the center of the
#     box/plate and going "downward" (opposite of normal) direction. Functions
#     like cutBlind() assume a positive cut direction, but cutThruAll() assumes
#     instead that the cut is made from a max direction and cuts downward from
#     that max through all objects.
result = (
    cq.Workplane("front")
    .box(width, height, thickness)
    .pushPoints([(0, 0.75), (0, -0.75)])
    .polygon(polygon_sides, polygon_dia)
    .cutThruAll()
)

# Displays the result of this script
show_object(result)
