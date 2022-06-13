from os import PathLike
import xml.etree.cElementTree as ET
from typing import IO, BinaryIO

from pyecma376_2 import package_model, zip_package


class ThreeMFWriter(object):
    def __init__(self, tessellation):

        self.unit = "millimeter"
        self.tessellation = tessellation

    def write3mf(self, outfile: PathLike | str | IO):
        with zip_package.ZipPackageWriter(outfile) as writer:

            with writer.open_part(
                "/3D/3dmodel.model",
                "application/vnd.ms-package.3dmanufacturing-3dmodel+xml",
            ) as part_io:
                self._write_3d(part_io)

            # Write the packages root relationships
            writer.write_relationships(
                [
                    package_model.OPCRelationship(
                        "rel-1",
                        "http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel",
                        "/3D/3dmodel.model",
                        package_model.OPCTargetMode.INTERNAL,
                    ),
                ]
            )

    def _write_3d(self, out: BinaryIO):
        model = ET.Element(
            "model",
            {
                "xml:lang": "en-US",
                "xmlns": "http://schemas.microsoft.com/3dmanufacturing/core/2015/02",
            },
            unit=self.unit,
        )

        # TODO: Add meta data
        meta = ET.SubElement(model, "metadata", name="Application")
        meta.text = "CadQuery 3MF Exporter"

        resources = ET.SubElement(model, "resources")

        # TODO: repeat for all solids
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

        ET.ElementTree(model).write(out, xml_declaration=True, encoding="utf-8")
        return out
