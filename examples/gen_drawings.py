from dataclasses import astuple, dataclass
from subprocess import run as run_cmd

import cadquery as cq
import ezdxf
from cadquery import Workplane
from ezdxf import transform
from ezdxf.addons import Importer


def makePart(
    width: int = 80,
    depth: int = 80,
    height: int = 60,
    hole_dia: float = 30.0,
) -> Workplane:
    baseplate = Workplane("XY").box(width, depth, height).edges("|Z").fillet(10.0)
    drilled = baseplate.faces(">Z").workplane().cskHole(hole_dia, hole_dia * 2, 82.0)
    return drilled


def git_version() -> str:
    try:
        result = run_cmd(
            ["git", "describe", "--tags", "--dirty"], capture_output=True, text=True
        )
    except RuntimeError:
        return "DrawingNumber"

    return result.stdout.rstrip()


def rename_layer(doc, old: str, new: str) -> None:
    """
    Rename the layer in the DXF document.

    Note: Works only for layers with an entry in the layer table,
    layers can be used without such an entry.
    """
    if old not in doc.layers:
        raise ValueError('Old layer "{}" does not exist.'.format(old))
    if new in doc.layers:
        raise ValueError('New layer "{}" does already exist.'.format(new))

    def rename_layer_table_entry() -> None:
        layer = doc.layers.get(old)
        layer.dxf.name = new
        # this is an internal API call, renaming table entries isn't implemented (yet)
        doc.layers.replace(old, layer)

    def rename_entities_layer_attribute() -> None:
        # layer names are case insensitive
        old_lower = old.lower()
        # iterate over all entities of modelspace, paperspace layouts
        # and block definitions
        for e in doc.chain_layouts_and_blocks():
            if e.get_dxf_attrib("layer", "0").lower() == old_lower:
                e.dxf.layer = new

    rename_layer_table_entry()
    rename_entities_layer_attribute()


@dataclass
class Projection:
    direction: tuple
    up: tuple


@dataclass
class CADDrawingPosition:
    x: int
    y: int


def exportDXF1stAngleProjection(my_part: cq.Workplane, prefix: str) -> None:
    viewpoint = {
        "top": Projection((0, 0, 1), (1, 0, 0)),
        "left": Projection((1, 0, 0), (0, 0, -1)),
        "front": Projection((0, 1, 0), (1, 0, 0)),
        "ortho": Projection((1, 1, 1), (0, 0, 1)),
    }

    for name, r in viewpoint.items():
        cq.exporters.exportDXFProjection(
            my_part,
            f"{prefix}{name}.dxf",
            r.direction,
            up=r.up,
            doc_units=6,
            is_hidden=False,
        )

        cq.exporters.exportDXFProjection(
            # Compound.makeCompound(hidden_edges),
            my_part,
            f"{prefix}{name}-hidden.dxf",
            r.direction,
            up=r.up,
            doc_units=6,
            is_hidden=True,
        )


if __name__ == "__main__":
    # Step 1: Make a 3D part
    drilled = makePart()

    # Step 2: generate 2D drawings, and write them to working directory
    exportDXF1stAngleProjection(drilled, "")

    # Step 3: Import the Titlecard template, and fill in the metadata
    output_filename = "testing.dxf"
    with open("templates/A3_Landscape.dxf", "r") as f:
        target = f.read()

    # Note(antonysigma): I would love to have SI units as strong types in
    # Python, similar to C++11 user literals.
    density_polycarbonate = 2800.0  # gram per meter^3

    mass = drilled.val().Volume() * (1e-3**3) * density_polycarbonate
    target = (
        target.replace("FC-Title", "Corner cube for Al extrusion")
        .replace("Subtitle", "Material: polycarbonate")
        .replace("AuthorName", "Antony C. Chan")
        .replace("CreationDate", "2019-21-31")
        .replace("FC-Scale", "1:1")
        .replace("Weight", f"{mass:0.3g}")
        .replace("SheetNumber", "1/1")
        .replace("DrawingNumber", git_version())
    )
    with open(output_filename, "w") as f:
        f.write(target)

    # Step 4: Add new layers representing various projections
    final_document = ezdxf.readfile(output_filename)

    dx, dy = 140, -100
    target_positions = {
        "top": CADDrawingPosition(dx, dy),
        "left": CADDrawingPosition(dx, dy - 100),
        "front": CADDrawingPosition(dx + 150, dy),
        "ortho": CADDrawingPosition(dx + 200, dy - 90),
    }

    for is_hidden_lines in (False, True):
        for view, point in target_positions.items():
            src = ezdxf.readfile(
                f"{view}-hidden.dxf" if is_hidden_lines else f"{view}.dxf"
            )

            # Thicken the lines
            assert "0" in src.layers
            src.layers.get("0").dxf.lineweight = 35 if not is_hidden_lines else 18

            # Rename the layer from "0" to meaningul values. Useful for toggling
            # visibility for each projection in the DXF editor GUI.
            layer_name = view if not is_hidden_lines else f"{view}-hidden"
            rename_layer(src, "0", layer_name)
            if view == "ortho":
                # Orthogonal projection interferes with the titlecard. Shrink
                # it. Don't forget to annotate the new scale manually in the
                # document.
                transform.scale_uniform(src.modelspace(), 0.5)

            # Move the projection to the desired XY coordinates
            transform.translate(src.modelspace(), astuple(point))

            # Append the projection to the document
            importer = Importer(src, final_document)
            importer.import_modelspace()
            importer.finalize()

            # Render hidden edges as dotted lines
            if is_hidden_lines:
                final_document.layers.get(layer_name).dxf.linetype = "DASHED"

    final_document.saveas(output_filename)
