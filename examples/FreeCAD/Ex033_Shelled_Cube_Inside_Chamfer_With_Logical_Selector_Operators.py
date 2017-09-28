# Example using advanced logical operators in string selectors to select only
# the inside edges on a shelled cube to chamfer.
import cadquery as cq

result = cq.Workplane("XY").box(2, 2, 2).\
    faces(">Z").shell(-0.2).\
    faces(">Z").edges("not(<X or >X or <Y or >Y)").\
    chamfer(0.125)

show_object(result)
