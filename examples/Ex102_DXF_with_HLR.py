from cadquery import Workplane, exporters

viewpoint = {
    "top": (0, 0, 1),
    "left": (1, 0, 0),
    "front": (0, 1, 0),
    "ortho": (1, 1, 1),
}


def exportDXF3rdAngleProjection(my_part: Workplane, prefix: str) -> None:
    for name, direction in viewpoint.items():
        exporters.exportDXFProjection(
            my_part, (0, 0, 0), direction, f"{prefix}{name}.dxf", doc_units=6,
        )


def exportSVG3rdAngleProjection(my_part, prefix: str) -> None:
    for name, direction in viewpoint.items():
        exporters.exportSVG(
            my_part, f"{prefix}{name}.svg", opts={"projectionDir": direction,},
        )


# Build the part
width = 10
depth = 10
height = 10
hole_dia = 3.0

baseplate = Workplane("XY").box(width, depth, height).edges("|Z").fillet(2.0)  #
drilled = baseplate.faces(">Z").workplane().cskHole(hole_dia, hole_dia * 2, 82.0)  #

# Expected DXF output to be identical to SVG output
exportSVG3rdAngleProjection(drilled, "")
exportDXF3rdAngleProjection(drilled, "")
exportDXF3rdAngleProjection(drilled.val(), "shape_")
