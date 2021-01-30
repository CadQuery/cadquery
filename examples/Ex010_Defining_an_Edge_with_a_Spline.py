import cadquery as cq

# 1.  Establishes a workplane to create the spline on to extrude.
# 1a. Uses the X and Y origins to define the workplane, meaning that the
# positive Z direction is "up", and the negative Z direction is "down".
s = cq.Workplane("XY")

# The points that the spline will pass through
sPnts = [
    (2.75, 1.5),
    (2.5, 1.75),
    (2.0, 1.5),
    (1.5, 1.0),
    (1.0, 1.25),
    (0.5, 1.0),
    (0, 1.0),
]

# 2.  Generate our plate with the spline feature and make sure it is a
#     closed entity
r = s.lineTo(3.0, 0).lineTo(3.0, 1.0).spline(sPnts, includeCurrent=True).close()

# 3.  Extrude to turn the wire into a plate
result = r.extrude(0.5)

# Displays the result of this script
show_object(result)
