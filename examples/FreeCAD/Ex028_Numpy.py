# NOTE: This example may not run correctly in some revisions of FreeCAD 0.16
import numpy as np
import cadquery as cq

# Square side and offset in x and y.
side = 10
offset = 5

# Define the locations that the polyline will be drawn to/thru.
# The polyline is defined as numpy.array so that operations like translation
# of all points are simplified.
pts = np.array([
    (0, 0),
    (side, 0),
    (side, side),
    (0, side),
    (0, 0)
]) + [offset, offset]

result = cq.Workplane('XY') \
    .polyline(pts).close().extrude(2) \
    .faces('+Z').workplane().circle(side / 2).extrude(1)

# Render the solid
show_object(result)
