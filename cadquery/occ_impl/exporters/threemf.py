from datetime import datetime
from os import PathLike
import xml.etree.cElementTree as ET
from typing import IO, List, Literal, Tuple, Union
from zipfile import ZipFile, ZIP_DEFLATED, ZIP_STORED

from ...cq import Compound, Shape, Vector


class CONTENT_TYPES(object):
    MODEL = "application/vnd.ms-package.3dmanufacturing-3dmodel+xml"
    RELATION = "application/vnd.openxmlformats-package.relationships+xml"


class SCHEMAS(object):
    CONTENT_TYPES = "http://schemas.openxmlformats.org/package/2006/content-types"
    RELATION = "http://schemas.openxmlformats.org/package/2006/relationships"
    CORE = "http://schemas.microsoft.com/3dmanufacturing/core/2015/02"
    MODEL = "http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"


Unit = Literal["micron", "millimeter", "centimeter", "meter", "inch", "foot"]


class ThreeMFWriter(object):
    def __init__(
        self,
        shape: Shape,
        tolerance: float,
        angularTolerance: float,
        unit: Unit = "millimeter",
    ):
        """
        Initialize the writer.
        Used to write the given Shape to a 3MF file.
        """
        self.unit = unit

        if isinstance(shape, Compound):
            shapes = list(shape)
        else:
            shapes = [shape]

        tessellations = [s.tessellate(tolerance, angularTolerance) for s in shapes]
        # Remove shapes that did not tesselate
        self.tessellations = [t for t in tessellations if all(t)]

    def write3mf(
        self, outfile: Union[PathLike, str, IO[bytes]],
    ):
        """ 
        Write to the given file. 
        """

        try:
            import zlib

            compression = ZIP_DEFLATED
        except ImportError:
            compression = ZIP_STORED

        with ZipFile(outfile, "w", compression) as zf:
            zf.writestr("_rels/.rels", self._write_relationships())
            zf.writestr("[Content_Types].xml", self._write_content_types())
            zf.writestr("3D/3dmodel.model", self._write_3d())

    def _write_3d(self) -> str:

        no_meshes = len(self.tessellations)

        model = ET.Element(
            "model", {"xml:lang": "en-US", "xmlns": SCHEMAS.CORE,}, unit=self.unit,
        )

        # Add meta data
        ET.SubElement(
            model, "metadata", name="Application"
        ).text = "CadQuery 3MF Exporter"
        ET.SubElement(
            model, "metadata", name="CreationDate"
        ).text = datetime.now().isoformat()

        resources = ET.SubElement(model, "resources")

        # Add all meshes to resources
        for i, tessellation in enumerate(self.tessellations):
            self._add_mesh(resources, str(i), tessellation)

        # Create a component of all meshes
        comp_object = ET.SubElement(
            resources,
            "object",
            id=str(no_meshes),
            name=f"CadQuery Component",
            type="model",
        )
        components = ET.SubElement(comp_object, "components")

        # Add all meshes to the component
        for i in range(no_meshes):
            ET.SubElement(
                components, "component", objectid=str(i),
            )

        # Add the component to the build
        build = ET.SubElement(model, "build")
        ET.SubElement(build, "item", objectid=str(no_meshes))

        return ET.tostring(model, xml_declaration=True, encoding="utf-8")

    def _add_mesh(
        self,
        to: ET.Element,
        id: str,
        tessellation: Tuple[List[Vector], List[Tuple[int, int, int]]],
    ):
        object = ET.SubElement(
            to, "object", id=id, name=f"CadQuery Shape {id}", type="model"
        )
        mesh = ET.SubElement(object, "mesh")

        # add vertices
        vertices = ET.SubElement(mesh, "vertices")
        for v in tessellation[0]:
            ET.SubElement(vertices, "vertex", x=str(v.x), y=str(v.y), z=str(v.z))

        # add triangles
        volume = ET.SubElement(mesh, "triangles")
        for t in tessellation[1]:
            ET.SubElement(volume, "triangle", v1=str(t[0]), v2=str(t[1]), v3=str(t[2]))

    def _write_content_types(self) -> str:

        root = ET.Element("Types")
        root.set("xmlns", SCHEMAS.CONTENT_TYPES)
        ET.SubElement(
            root,
            "Override",
            PartName="/3D/3dmodel.model",
            ContentType=CONTENT_TYPES.MODEL,
        )
        ET.SubElement(
            root,
            "Override",
            PartName="/_rels/.rels",
            ContentType=CONTENT_TYPES.RELATION,
        )

        return ET.tostring(root, xml_declaration=True, encoding="utf-8")

    def _write_relationships(self) -> str:

        root = ET.Element("Relationships")
        root.set("xmlns", SCHEMAS.RELATION)
        ET.SubElement(
            root,
            "Relationship",
            Target="/3D/3dmodel.model",
            Id="rel-1",
            Type=SCHEMAS.MODEL,
            TargetMode="Internal",
        )

        return ET.tostring(root, xml_declaration=True, encoding="utf-8")
