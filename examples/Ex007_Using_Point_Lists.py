import cadquery as cq

# These can be modified rather than hardcoding values for each dimension.
plate_radius = 2.0  # The radius of the plate that will be extruded
hole_pattern_radius = 0.25  # Radius of circle where the holes will be placed
thickness = 0.125  # The thickness of the plate that will be extruded

# Make a plate with 4 holes in it at various points in a polar arrangement from
# the center of the workplane.
# 1.  Establishes a workplane that an object can be built on.
# 1a. Uses the named plane orientation "front" to define the workplane, meaning
#     that the positive Z direction is "up", and the negative Z direction
#     is "down".
# 2.  A 2D circle is drawn that will become though outer profile of the plate.
r = cq.Workplane("front").circle(plate_radius)

# 3. Push 4 points on the stack that will be used as the center points of the
#    holes.
r = r.pushPoints([(1.5, 0), (0, 1.5), (-1.5, 0), (0, -1.5)])

# 4. This circle() call will operate on all four points, putting a circle at
#    each one.
r = r.circle(hole_pattern_radius)

# 5.  All 2D geometry is extruded to the specified thickness of the plate.
# 5a. The small hole circles are enclosed in the outer circle of the plate and
#     so it is assumed that we want them to be cut out of the plate.  A
#     separate cut operation is not needed.
result = r.extrude(thickness)

# Displays the result of this script
show_object(result)
