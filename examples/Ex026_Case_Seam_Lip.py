import cadquery as cq
from cadquery.selectors import AreaNthSelector

case_bottom = (
    cq.Workplane("XY")
    .rect(20, 20)
    .extrude(10)  # solid 20x20x10 box
    .edges("|Z or <Z")
    .fillet(2)  # rounding all edges except 4 edges of the top face
    .faces(">Z")
    .shell(2)  # shell of thickness 2 with top face open
    .faces(">Z")
    .wires(AreaNthSelector(-1))  # selecting top outer wire
    .toPending()
    .workplane()
    .offset2D(-1)  # creating centerline wire of case seam face
    .extrude(1)  # covering the sell with temporary "lid"
    .faces(">Z[-2]")
    .wires(AreaNthSelector(0))  # selecting case crossection wire
    .toPending()
    .workplane()
    .cutBlind(2)  # cutting through the "lid" leaving a lip on case seam surface
)

# similar process repeated for the top part
# but instead of "growing" an inner lip
# material is removed inside case seam centerline
# to create an outer lip
case_top = (
    cq.Workplane("XY")
    .move(25)
    .rect(20, 20)
    .extrude(5)
    .edges("|Z or >Z")
    .fillet(2)
    .faces("<Z")
    .shell(2)
    .faces("<Z")
    .wires(AreaNthSelector(-1))
    .toPending()
    .workplane()
    .offset2D(-1)
    .cutBlind(-1)
)

show_object(case_bottom)
show_object(case_top, options={"alpha": 0.5})
