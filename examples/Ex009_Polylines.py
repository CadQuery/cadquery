import cadquery as cq

# These can be modified rather than hardcoding values for each dimension.
# Define up our Length, Height, Width, and thickness of the beam
(L, H, W, t) = (100.0, 20.0, 20.0, 1.0)

# Define the points that the polyline will be drawn to/thru
pts = [
    (0, H / 2.0),
    (W / 2.0, H / 2.0),
    (W / 2.0, (H / 2.0 - t)),
    (t / 2.0, (H / 2.0 - t)),
    (t / 2.0, (t - H / 2.0)),
    (W / 2.0, (t - H / 2.0)),
    (W / 2.0, H / -2.0),
    (0, H / -2.0),
]

# We generate half of the I-beam outline and then mirror it to create the full
# I-beam.
# 1.  Establishes a workplane that an object can be built on.
# 1a. Uses the named plane orientation "front" to define the workplane, meaning
#     that the positive Z direction is "up", and the negative Z direction
#     is "down".
# 2.  moveTo() is used to move the first point from the origin (0, 0) to
#     (0, 10.0), with 10.0 being half the height (H/2.0). If this is not done
#     the first line will start from the origin, creating an extra segment that
#     will cause the extrude to have an invalid shape.
# 3.  The polyline function takes a list of points and generates the lines
#     through all the points at once.
# 3.  Only half of the I-beam profile has been drawn so far. That half is
#     mirrored around the Y-axis to create the complete I-beam profile.
# 4.  The I-beam profile is extruded to the final length of the beam.
result = cq.Workplane("front").polyline(pts).mirrorY().extrude(L)

# Displays the result of this script
show_object(result)
