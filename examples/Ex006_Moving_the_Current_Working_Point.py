import cadquery as cq

# These can be modified rather than hardcoding values for each dimension.
circle_radius = 3.0  # The outside radius of the plate
thickness = 0.25  # The thickness of the plate

# Make a plate with two cutouts in it by moving the workplane center point
# 1.  Establishes a workplane that an object can be built on.
# 1a. Uses the named plane orientation "front" to define the workplane, meaning
#     that the positive Z direction is "up", and the negative Z direction
#     is "down".
# 1b. The initial workplane center point is the center of the circle, at (0,0).
# 2.  A circle is created at the center of the workplane
# 2a. Notice that circle() takes a radius and not a diameter
result = cq.Workplane("front").circle(circle_radius)

# 3.  The work center is movide to (1.5, 0.0) by calling center().
# 3a. The new center is specified relative to the previous center,not
#     relative to global coordinates.
# 4.  A 0.5mm x 0.5mm 2D square is drawn inside the circle.
# 4a. The plate has not been extruded yet, only 2D geometry is being created.
result = result.center(1.5, 0.0).rect(0.5, 0.5)

# 5.  The work center is moved again, this time to (-1.5, 1.5).
# 6.  A 2D circle is created at that new center with a radius of 0.25mm.
result = result.center(-1.5, 1.5).circle(0.25)

# 7.  All 2D geometry is extruded to the specified thickness of the plate.
# 7a. The small circle and the square are enclosed in the outer circle of the
#      plate and so it is assumed that we want them to be cut out of the plate.
#      A separate cut operation is not needed.
result = result.extrude(thickness)

# Displays the result of this script
show_object(result)
