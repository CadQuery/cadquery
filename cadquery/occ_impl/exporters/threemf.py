from os import PathLike
import xml.etree.cElementTree as ET
from typing import IO, Union
from zipfile import ZipFile, ZIP_DEFLATED, ZIP_STORED

try:
    import zlib

    COMPRESSION = ZIP_DEFLATED
except:
    COMPRESSION = ZIP_STORED


class CONTENT_TYPES(object):
    MODEL = "application/vnd.ms-package.3dmanufacturing-3dmodel+xml"
    RELATION = "application/vnd.openxmlformats-package.relationships+xml"


class SCHEMAS(object):
    CONTENT_TYPES = "http://schemas.openxmlformats.org/package/2006/content-types"
    RELATION = "http://schemas.openxmlformats.org/package/2006/relationships"
    CORE = "http://schemas.microsoft.com/3dmanufacturing/core/2015/02"
    MODEL = "http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"


class ThreeMFWriter(object):
    def __init__(self, tessellation):

        self.unit = "millimeter"
        self.tessellation = tessellation

    def write3mf(self, outfile: Union[PathLike, str, IO[bytes]]):
        with ZipFile(outfile, "w", COMPRESSION) as zf:
            zf.writestr("_rels/.rels", self._write_relationships())
            zf.writestr("[Content_Types].xml", self._write_content_types())
            zf.writestr("3D/3dmodel.model", self._write_3d())

    def _write_3d(self) -> str:
        model = ET.Element(
            "model", {"xml:lang": "en-US", "xmlns": SCHEMAS.CORE,}, unit=self.unit,
        )

        # TODO: Add meta data
        meta = ET.SubElement(model, "metadata", name="Application")
        meta.text = "CadQuery 3MF Exporter"

        resources = ET.SubElement(model, "resources")

        object = ET.SubElement(resources, "object", id="0", type="model")
        mesh = ET.SubElement(object, "mesh")

        # add vertices
        vertices = ET.SubElement(mesh, "vertices")
        for v in self.tessellation[0]:
            ET.SubElement(vertices, "vertex", x=str(v.x), y=str(v.y), z=str(v.z))

        # add triangles
        volume = ET.SubElement(mesh, "triangles")
        for t in self.tessellation[1]:
            ET.SubElement(volume, "triangle", v1=str(t[0]), v2=str(t[1]), v3=str(t[2]))

        build = ET.SubElement(model, "build")
        ET.SubElement(build, "item", objectid="0")

        return ET.tostring(model, xml_declaration=True, encoding="utf-8")

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
