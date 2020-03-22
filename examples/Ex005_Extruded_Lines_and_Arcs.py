import cadquery as cq

# These can be modified rather than hardcoding values for each dimension.
width = 2.0  # Overall width of the plate
thickness = 0.25  # Thickness of the plate

# Extrude a plate outline made of lines and an arc
# 1.  Establishes a workplane that an object can be built on.
# 1a. Uses the named plane orientation "front" to define the workplane, meaning
#     that the positive Z direction is "up", and the negative Z direction
#     is "down".
# 2.  Draws a line from the origin to an X position of the plate's width.
# 2a. The starting point of a 2D drawing like this will be at the center of the
#     workplane (0, 0) unless the moveTo() function moves the starting point.
# 3.  A line is drawn from the last position straight up in the Y direction
#     1.0 millimeters.
# 4.  An arc is drawn from the last point, through point (1.0, 1.5) which is
#     half-way back to the origin in the X direction and 0.5 mm above where
#     the last line ended at. The arc then ends at (0.0, 1.0), which is 1.0 mm
#     above (in the Y direction) where our first line started from.
# 5.  An arc is drawn from the last point that ends on (-0.5, 1.0), the sag of
#     the curve 0.2 determines that the curve is concave with the midpoint 0.1 mm
#     from the arc baseline. If the sag was -0.2 the arc would be convex.
#     This convention is valid when the profile is drawn counterclockwise.
#     The reverse is true if the profile is drawn clockwise.
#     Clockwise:        +sag => convex,  -sag => concave
#     Counterclockwise: +sag => concave, -sag => convex
# 6.  An arc is drawn from the last point that ends on (-0.7, -0.2), the arc is
#     determined by the radius of -1.5 mm.
#     Clockwise:        +radius => convex,  -radius => concave
#     Counterclockwise: +radius => concave, -radius => convex
# 7.  close() is called to automatically draw the last line for us and close
#     the sketch so that it can be extruded.
# 7a. Without the close(), the 2D sketch will be left open and the extrude
#     operation will provide unpredictable results.
# 8.  The 2D sketch is extruded into a solid object of the specified thickness.
result = (
    cq.Workplane("front")
    .lineTo(width, 0)
    .lineTo(width, 1.0)
    .threePointArc((1.0, 1.5), (0.0, 1.0))
    .sagittaArc((-0.5, 1.0), 0.2)
    .radiusArc((-0.7, -0.2), -1.5)
    .close()
    .extrude(thickness)
)

# Displays the result of this script
show_object(result)
