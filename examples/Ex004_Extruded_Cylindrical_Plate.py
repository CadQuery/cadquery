import cadquery as cq

# These can be modified rather than hardcoding values for each dimension.
circle_radius = 50.0  # Radius of the plate
thickness = 13.0  # Thickness of the plate
rectangle_width = 13.0  # Width of rectangular hole in cylindrical plate
rectangle_length = 19.0  # Length of rectangular hole in cylindrical plate

# Extrude a cylindrical plate with a rectangular hole in the middle of it.
# 1.  Establishes a workplane that an object can be built on.
# 1a. Uses the named plane orientation "front" to define the workplane, meaning
#     that the positive Z direction is "up", and the negative Z direction
#     is "down".
# 2.  The 2D geometry for the outer circle is created at the same time as the
#     rectangle that will create the hole in the center.
# 2a. The circle and the rectangle will be automatically centered on the
#     workplane.
# 2b. Unlike some other functions like the hole(), circle() takes
#     a radius and not a diameter.
# 3.  The circle and rectangle are extruded together, creating a cylindrical
#     plate with a rectangular hole in the center.
# 3a. circle() and rect() could be changed to any other shape to completely
#     change the resulting plate and/or the hole in it.
result = (
    cq.Workplane("front")
    .circle(circle_radius)
    .rect(rectangle_width, rectangle_length)
    .extrude(thickness)
)

# Displays the result of this script
show_object(result)
