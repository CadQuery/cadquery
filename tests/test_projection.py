import cadquery as cq
from cadquery.occ_impl.exporters.svg import exportSVG
from cadquery.occ_impl.shapes import Compound, projectToViewpoint
from cadquery import Workplane

viewpoint = {
    "top": (0, 0, 1),
    "left": (1, 0, 0),
    "front": (0, 1, 0),
    "ortho": (1, 1, 1),
}


def exportDXF3rdAngleProjection(my_part: Workplane, prefix: str) -> None:
    for name, direction in viewpoint.items():
        visible_edges, hidden_edges = projectToViewpoint(my_part.val(), direction)
        cq.exporters.exportDXF(
            Compound.makeCompound(visible_edges), f"{prefix}{name}.dxf", doc_units=6,
        )


def exportSVG3rdAngleProjection(my_part, prefix: str) -> None:
    for name, direction in viewpoint.items():
        exportSVG(
            my_part, f"{prefix}{name}.svg", opts={"projectionDir": direction,},
        )


if __name__ == "__main__":
    # Build the part
    width = 10
    depth = 10
    height = 10

    # !!! Test projection of fillets to arc segments in DXF. !!!
    baseplate = cq.Workplane("XY").box(width, depth, height).edges("|Z").fillet(2.0)  #

    hole_dia = 3.0

    # !!! Test projection of countersunk to arc segments in DXF. !!!
    drilled = baseplate.faces(">Z").workplane().cskHole(hole_dia, hole_dia * 2, 82.0)  #

    # Expected DXF output to be identical to SVG output
    exportSVG3rdAngleProjection(drilled, "")
    exportDXF3rdAngleProjection(drilled, "")
