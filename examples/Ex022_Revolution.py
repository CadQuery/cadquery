import cadquery as cq

# The dimensions of the model. These can be modified rather than changing the
# shape's code directly.
rectangle_width = 10.0
rectangle_length = 10.0
angle_degrees = 360.0

# Revolve a cylinder from a rectangle
# Switch comments around in this section to try the revolve operation with different parameters
result = cq.Workplane("XY").rect(rectangle_width, rectangle_length, False).revolve()
# result = cq.Workplane("XY").rect(rectangle_width, rectangle_length, False).revolve(angle_degrees)
# result = cq.Workplane("XY").rect(rectangle_width, rectangle_length).revolve(angle_degrees,(-5,-5))
# result = cq.Workplane("XY").rect(rectangle_width, rectangle_length).revolve(angle_degrees,(-5, -5),(-5, 5))
# result = cq.Workplane("XY").rect(rectangle_width, rectangle_length).revolve(angle_degrees,(-5,-5),(-5,5), False)

# Revolve a donut with square walls
# result = cq.Workplane("XY").rect(rectangle_width, rectangle_length, True).revolve(angle_degrees, (20, 0), (20, 10))

# Displays the result of this script
show_object(result)
