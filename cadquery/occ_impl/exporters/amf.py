import xml.etree.cElementTree as ET


class AmfWriter(object):
    def __init__(self, tessellation):

        self.units = "mm"
        self.tessellation = tessellation

    def writeAmf(self, outFile):
        amf = ET.Element("amf", units=self.units)
        # TODO: if result is a compound, we need to loop through them
        object = ET.SubElement(amf, "object", id="0")
        mesh = ET.SubElement(object, "mesh")
        vertices = ET.SubElement(mesh, "vertices")
        volume = ET.SubElement(mesh, "volume")

        # add vertices
        for v in self.tessellation[0]:
            vtx = ET.SubElement(vertices, "vertex")
            coord = ET.SubElement(vtx, "coordinates")
            x = ET.SubElement(coord, "x")
            x.text = str(v.x)
            y = ET.SubElement(coord, "y")
            y.text = str(v.y)
            z = ET.SubElement(coord, "z")
            z.text = str(v.z)

        # add triangles
        for t in self.tessellation[1]:
            triangle = ET.SubElement(volume, "triangle")
            v1 = ET.SubElement(triangle, "v1")
            v1.text = str(t[0])
            v2 = ET.SubElement(triangle, "v2")
            v2.text = str(t[1])
            v3 = ET.SubElement(triangle, "v3")
            v3.text = str(t[2])

        amf = ET.ElementTree(amf).write(outFile, xml_declaration=True)
