from cadquery import Workplane, exporters
from ezdxf import units

# Map each view name to its projection direction and the world-space direction
# that should appear upward in the projected view.
viewpoints = {
    "top": ((0, 0, 1), (0, 1, 0)),
    "left": ((1, 0, 0), (0, 0, 1)),
    "front": ((0, 1, 0), (0, 0, 1)),
    "ortho": ((1, 1, 1), (0, 0, 1)),
}


def exportDXF3rdAngleProjection(my_part) -> None:
    for name, (direction, up) in viewpoints.items():
        exporters.exportDXFProjection(
            my_part, f"{name}.dxf", direction, up=up, doc_units=units.CM,
        )


def exportSVG3rdAngleProjection(my_part) -> None:
    for name, (direction, up) in viewpoints.items():
        exporters.exportSVG(
            my_part,
            f"{name}.svg",
            opts={"projectionDir": direction, "up": up, "showHidden": False},
        )


# Build the part
width = 10
depth = 10
height = 10
hole_dia = 3.0

baseplate = Workplane("XY").box(width, depth, height).edges("|Z").fillet(2.0)
drilled = baseplate.faces(">Z").workplane().cskHole(hole_dia, hole_dia * 2, 82.0)

# Export equivalent visible-edge projections to SVG and DXF.
exportSVG3rdAngleProjection(drilled)
exportDXF3rdAngleProjection(drilled)
