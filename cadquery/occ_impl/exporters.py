from __future__ import unicode_literals

# from OCP.Visualization import Tesselator

import tempfile
import os
import sys

if sys.version_info.major == 2:
    import cStringIO as StringIO
else:
    import io as StringIO

from .shapes import Shape, Compound, TOLERANCE
from .geom import BoundBox

from OCP.gp import gp_Ax2, gp_Pnt, gp_Dir
from OCP.BRepLib import BRepLib
from OCP.HLRBRep import HLRBRep_Algo, HLRBRep_HLRToShape
from OCP.HLRAlgo import HLRAlgo_Projector
from OCP.GCPnts import GCPnts_QuasiUniformDeflection

try:
    import xml.etree.cElementTree as ET
except ImportError:
    import xml.etree.ElementTree as ET

DISCRETIZATION_TOLERANCE = 1e-3
DEFAULT_DIR = gp_Dir(-1.75, 1.1, 5)


class ExportTypes:
    STL = "STL"
    STEP = "STEP"
    AMF = "AMF"
    SVG = "SVG"
    TJS = "TJS"


class UNITS:
    MM = "mm"
    IN = "in"


def toString(shape, exportType, tolerance=0.1):
    s = StringIO.StringIO()
    exportShape(shape, exportType, s, tolerance)
    return s.getvalue()


def exportShape(shape, exportType, fileLike, tolerance=0.1):
    """
        :param shape:  the shape to export. it can be a shape object, or a cadquery object. If a cadquery
        object, the first value is exported
        :param exportFormat: the exportFormat to use
        :param tolerance: the tolerance, in model units
        :param fileLike: a file like object to which the content will be written.
        The object should be already open and ready to write. The caller is responsible
        for closing the object
    """

    from ..cq import CQ

    def tessellate(shape):

        return shape.tessellate(tolerance)

    if isinstance(shape, CQ):
        shape = shape.val()

    if exportType == ExportTypes.TJS:
        tess = tessellate(shape)
        mesher = JsonMesh()

        # add vertices
        for v in tess[0]:
            mesher.addVertex(v.x, v.y, v.z)

        # add triangles
        for t in tess[1]:
            mesher.addTriangleFace(*t)

        fileLike.write(mesher.toJson())

    elif exportType == ExportTypes.SVG:
        fileLike.write(getSVG(shape))
    elif exportType == ExportTypes.AMF:
        tess = tessellate(shape)
        aw = AmfWriter(tess)
        aw.writeAmf(fileLike)
    else:

        # all these types required writing to a file and then
        # re-reading. this is due to the fact that FreeCAD writes these
        (h, outFileName) = tempfile.mkstemp()
        # weird, but we need to close this file. the next step is going to write to
        # it from c code, so it needs to be closed.
        os.close(h)

        if exportType == ExportTypes.STEP:
            shape.exportStep(outFileName)
        elif exportType == ExportTypes.STL:
            shape.exportStl(outFileName, tolerance)
        else:
            raise ValueError("No idea how i got here")

        res = readAndDeleteFile(outFileName)
        fileLike.write(res)


def readAndDeleteFile(fileName):
    """
        read data from file provided, and delete it when done
        return the contents as a string
    """
    res = ""
    with open(fileName, "r") as f:
        res = "{}".format(f.read())

    os.remove(fileName)
    return res


def guessUnitOfMeasure(shape):
    """
        Guess the unit of measure of a shape.
    """
    bb = BoundBox._fromTopoDS(shape.wrapped)

    dimList = [bb.xlen, bb.ylen, bb.zlen]
    # no real part would likely be bigger than 10 inches on any side
    if max(dimList) > 10:
        return UNITS.MM

    # no real part would likely be smaller than 0.1 mm on all dimensions
    if min(dimList) < 0.1:
        return UNITS.IN

    # no real part would have the sum of its dimensions less than about 5mm
    if sum(dimList) < 10:
        return UNITS.IN

    return UNITS.MM


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


"""
    Objects that represent
    three.js JSON object notation
    https://github.com/mrdoob/three.js/wiki/JSON-Model-format-3.0
"""


class JsonMesh(object):
    def __init__(self):

        self.vertices = []
        self.faces = []
        self.nVertices = 0
        self.nFaces = 0

    def addVertex(self, x, y, z):
        self.nVertices += 1
        self.vertices.extend([x, y, z])

    # add triangle composed of the three provided vertex indices
    def addTriangleFace(self, i, j, k):
        # first position means justa simple triangle
        self.nFaces += 1
        self.faces.extend([0, int(i), int(j), int(k)])

    """
        Get a json model from this model.
        For now we'll forget about colors, vertex normals, and all that stuff
    """

    def toJson(self):
        return JSON_TEMPLATE % {
            "vertices": str(self.vertices),
            "faces": str(self.faces),
            "nVertices": self.nVertices,
            "nFaces": self.nFaces,
        }


def makeSVGedge(e):
    """

    """

    cs = StringIO.StringIO()

    curve = e._geomAdaptor()  # adapt the edge into curve
    start = curve.FirstParameter()
    end = curve.LastParameter()

    points = GCPnts_QuasiUniformDeflection(curve, DISCRETIZATION_TOLERANCE, start, end)

    if points.IsDone():
        point_it = (points.Value(i + 1) for i in range(points.NbPoints()))

        p = next(point_it)
        cs.write("M{},{} ".format(p.X(), p.Y()))

        for p in point_it:
            cs.write("L{},{} ".format(p.X(), p.Y()))

    return cs.getvalue()


def getPaths(visibleShapes, hiddenShapes):
    """

    """

    hiddenPaths = []
    visiblePaths = []

    for s in visibleShapes:
        for e in s.Edges():
            visiblePaths.append(makeSVGedge(e))

    for s in hiddenShapes:
        for e in s.Edges():
            hiddenPaths.append(makeSVGedge(e))

    return (hiddenPaths, visiblePaths)


def getSVG(shape, opts=None):
    """
        Export a shape to SVG
    """

    d = {"width": 800, "height": 240, "marginLeft": 200, "marginTop": 20}

    if opts:
        d.update(opts)

    # need to guess the scale and the coordinate center
    uom = guessUnitOfMeasure(shape)

    width = float(d["width"])
    height = float(d["height"])
    marginLeft = float(d["marginLeft"])
    marginTop = float(d["marginTop"])

    hlr = HLRBRep_Algo()
    hlr.Add(shape.wrapped)

    projector = HLRAlgo_Projector(gp_Ax2(gp_Pnt(), DEFAULT_DIR))

    hlr.Projector(projector)
    hlr.Update()
    hlr.Hide()

    hlr_shapes = HLRBRep_HLRToShape(hlr)

    visible = []

    visible_sharp_edges = hlr_shapes.VCompound()
    if not visible_sharp_edges.IsNull():
        visible.append(visible_sharp_edges)

    visible_smooth_edges = hlr_shapes.Rg1LineVCompound()
    if not visible_smooth_edges.IsNull():
        visible.append(visible_smooth_edges)

    visible_contour_edges = hlr_shapes.OutLineVCompound()
    if not visible_contour_edges.IsNull():
        visible.append(visible_contour_edges)

    hidden = []

    hidden_sharp_edges = hlr_shapes.HCompound()
    if not hidden_sharp_edges.IsNull():
        hidden.append(hidden_sharp_edges)

    hidden_contour_edges = hlr_shapes.OutLineHCompound()
    if not hidden_contour_edges.IsNull():
        hidden.append(hidden_contour_edges)

    # Fix the underlying geometry - otherwise we will get segfaults
    for el in visible:
        BRepLib.BuildCurves3d_s(el, TOLERANCE)
    for el in hidden:
        BRepLib.BuildCurves3d_s(el, TOLERANCE)

    # convert to native CQ objects
    visible = list(map(Shape, visible))
    hidden = list(map(Shape, hidden))
    (hiddenPaths, visiblePaths) = getPaths(visible, hidden)

    # get bounding box -- these are all in 2-d space
    bb = Compound.makeCompound(hidden + visible).BoundingBox()

    # width pixels for x, height pixesl for y
    unitScale = min(width / bb.xlen * 0.75, height / bb.ylen * 0.75)

    # compute amount to translate-- move the top left into view
    (xTranslate, yTranslate) = (
        (0 - bb.xmin) + marginLeft / unitScale,
        (0 - bb.ymax) - marginTop / unitScale,
    )

    # compute paths ( again -- had to strip out freecad crap )
    hiddenContent = ""
    for p in hiddenPaths:
        hiddenContent += PATHTEMPLATE % p

    visibleContent = ""
    for p in visiblePaths:
        visibleContent += PATHTEMPLATE % p

    svg = SVG_TEMPLATE % (
        {
            "unitScale": str(unitScale),
            "strokeWidth": str(1.0 / unitScale),
            "hiddenContent": hiddenContent,
            "visibleContent": visibleContent,
            "xTranslate": str(xTranslate),
            "yTranslate": str(yTranslate),
            "width": str(width),
            "height": str(height),
            "textboxY": str(height - 30),
            "uom": str(uom),
        }
    )
    # svg = SVG_TEMPLATE % (
    #    {"content": projectedContent}
    # )
    return svg


def exportSVG(shape, fileName):
    """
        accept a cadquery shape, and export it to the provided file
        TODO: should use file-like objects, not a fileName, and/or be able to return a string instead
        export a view of a part to svg
    """

    svg = getSVG(shape.val())
    f = open(fileName, "w")
    f.write(svg)
    f.close()


JSON_TEMPLATE = """\
{
    "metadata" :
    {
        "formatVersion" : 3,
        "generatedBy"   : "ParametricParts",
        "vertices"      : %(nVertices)d,
        "faces"         : %(nFaces)d,
        "normals"       : 0,
        "colors"        : 0,
        "uvs"           : 0,
        "materials"     : 1,
        "morphTargets"  : 0
    },

    "scale" : 1.0,

    "materials": [    {
    "DbgColor" : 15658734,
    "DbgIndex" : 0,
    "DbgName" : "Material",
    "colorAmbient" : [0.0, 0.0, 0.0],
    "colorDiffuse" : [0.6400000190734865, 0.10179081114814892, 0.126246120426746],
    "colorSpecular" : [0.5, 0.5, 0.5],
    "shading" : "Lambert",
    "specularCoef" : 50,
    "transparency" : 1.0,
    "vertexColors" : false
    }],

    "vertices": %(vertices)s,

    "morphTargets": [],

    "normals": [],

    "colors": [],

    "uvs": [[]],

    "faces": %(faces)s
}
"""

SVG_TEMPLATE = """<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<svg
   xmlns:svg="http://www.w3.org/2000/svg"
   xmlns="http://www.w3.org/2000/svg"
   width="%(width)s"
   height="%(height)s"

>
    <g transform="scale(%(unitScale)s, -%(unitScale)s)   translate(%(xTranslate)s,%(yTranslate)s)" stroke-width="%(strokeWidth)s"  fill="none">
       <!-- hidden lines -->
       <g  stroke="rgb(160, 160, 160)" fill="none" stroke-dasharray="%(strokeWidth)s,%(strokeWidth)s" >
%(hiddenContent)s
       </g>

       <!-- solid lines -->
       <g  stroke="rgb(0, 0, 0)" fill="none">
%(visibleContent)s
       </g>
    </g>
    <g transform="translate(20,%(textboxY)s)" stroke="rgb(0,0,255)">
        <line x1="30" y1="-30" x2="75" y2="-33" stroke-width="3" stroke="#000000" />
         <text x="80" y="-30" style="stroke:#000000">X </text>

        <line x1="30" y1="-30" x2="30" y2="-75" stroke-width="3" stroke="#000000" />
         <text x="25" y="-85" style="stroke:#000000">Y </text>

        <line x1="30" y1="-30" x2="58" y2="-15" stroke-width="3" stroke="#000000" />
         <text x="65" y="-5" style="stroke:#000000">Z </text>
        <!--
            <line x1="0" y1="0" x2="%(unitScale)s" y2="0" stroke-width="3" />
            <text x="0" y="20" style="stroke:#000000">1  %(uom)s </text>
        -->
    </g>
</svg>
"""

PATHTEMPLATE = '\t\t\t<path d="%s" />\n'
