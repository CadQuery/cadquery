"""
    Copyright (C) 2011-2013  Parametric Products Intellectual Holdings, LLC

    This file is part of CadQuery.

    CadQuery is free software; you can redistribute it and/or
    modify it under the terms of the GNU Lesser General Public
    License as published by the Free Software Foundation; either
    version 2.1 of the License, or (at your option) any later version.

    CadQuery is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
    Lesser General Public License for more details.

    You should have received a copy of the GNU Lesser General Public
    License along with this library; If not, see <http://www.gnu.org/licenses/>

    An exporter should provide functionality to accept a shape, and return
    a string containing the model content.
"""
import cadquery

from .verutil import fc_import
FreeCAD = fc_import("FreeCAD")
import tempfile,os,StringIO

Drawing = fc_import("FreeCAD.Drawing")
#_FCVER = freecad_version()
#if _FCVER>=(0,13):
    #import Drawing as FreeCADDrawing #It's in FreeCAD lib path
#elif _FCVER>=(0,12):
    #import FreeCAD.Drawing as FreeCADDrawing
#else:
    #raise RuntimeError, "Invalid freecad version: %s" % str(".".join(_FCVER))


try:
    import xml.etree.cElementTree as ET
except ImportError:
    import xml.etree.ElementTree as ET

class ExportTypes:
    STL = "STL"
    STEP = "STEP"
    AMF = "AMF"
    SVG = "SVG"
    TJS = "TJS"

class UNITS:
    MM = "mm"
    IN = "in"


def toString(shape,exportType,tolerance=0.1):
	s= StringIO.StringIO()
	exportShape(shape,exportType,s,tolerance)
	return s.getvalue()

def exportShape(shape,exportType,fileLike,tolerance=0.1):
    """
        :param shape:  the shape to export. it can be a shape object, or a cadquery object. If a cadquery
        object, the first value is exported
        :param exportFormat: the exportFormat to use
        :param tolerance: the tolerance, in model units
        :param fileLike: a file like object to which the content will be written.
        The object should be already open and ready to write. The caller is responsible
        for closing the object
    """


    if isinstance(shape,cadquery.CQ):
        shape = shape.val()

    if exportType == ExportTypes.TJS:
        #tessellate the model
        tess = shape.tessellate(tolerance)

        mesher = JsonMesh() #warning: needs to be changed to remove buildTime and exportTime!!!
        #add vertices
        for vec in tess[0]:
            mesher.addVertex(vec.x, vec.y, vec.z)

        #add faces
        for f in tess[1]:
            mesher.addTriangleFace(f[0],f[1], f[2])
        fileLike.write( mesher.toJson())
    elif exportType == ExportTypes.SVG:
        fileLike.write(getSVG(shape.wrapped))
    elif exportType == ExportTypes.AMF:
        tess = shape.tessellate(tolerance)
        aw = AmfWriter(tess).writeAmf(fileLike)
    else:

        #all these types required writing to a file and then
        #re-reading. this is due to the fact that FreeCAD writes these
        (h, outFileName) = tempfile.mkstemp()
        #weird, but we need to close this file. the next step is going to write to
        #it from c code, so it needs to be closed.
        os.close(h)

        if exportType == ExportTypes.STEP:
            shape.exportStep(outFileName)
        elif exportType == ExportTypes.STL:
            shape.wrapped.exportStl(outFileName)
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
    with open(fileName,'r') as f:
        res = f.read()

    os.remove(fileName)
    return res


def guessUnitOfMeasure(shape):
    """
        Guess the unit of measure of a shape.
    """
    bb = shape.BoundBox

    dimList = [ bb.XLength, bb.YLength,bb.ZLength ]
    #no real part would likely be bigger than 10 inches on any side
    if max(dimList) > 10:
        return UNITS.MM

    #no real part would likely be smaller than 0.1 mm on all dimensions
    if min(dimList) < 0.1:
        return UNITS.IN

    #no real part would have the sum of its dimensions less than about 5mm
    if sum(dimList) < 10:
        return UNITS.IN

    return UNITS.MM


class AmfWriter(object):
    def __init__(self,tessellation):

        self.units = "mm"
        self.tessellation = tessellation

    def writeAmf(self,outFile):
        amf = ET.Element('amf',units=self.units)
        #TODO: if result is a compound, we need to loop through them
        object = ET.SubElement(amf,'object',id="0")
        mesh = ET.SubElement(object,'mesh')
        vertices = ET.SubElement(mesh,'vertices')
        volume = ET.SubElement(mesh,'volume')

        #add vertices
        for v in self.tessellation[0]:
            vtx = ET.SubElement(vertices,'vertex')
            coord = ET.SubElement(vtx,'coordinates')
            x = ET.SubElement(coord,'x')
            x.text = str(v.x)
            y = ET.SubElement(coord,'y')
            y.text = str(v.y)
            z = ET.SubElement(coord,'z')
            z.text = str(v.z)

        #add triangles
        for t in self.tessellation[1]:
            triangle = ET.SubElement(volume,'triangle')
            v1 = ET.SubElement(triangle,'v1')
            v1.text = str(t[0])
            v2 = ET.SubElement(triangle,'v2')
            v2.text = str(t[1])
            v3 = ET.SubElement(triangle,'v3')
            v3.text = str(t[2])


        ET.ElementTree(amf).write(outFile,encoding='ISO-8859-1')

"""
    Objects that represent
    three.js JSON object notation
    https://github.com/mrdoob/three.js/wiki/JSON-Model-format-3.0
"""
class JsonMesh(object):
    def __init__(self):

        self.vertices = [];
        self.faces = [];
        self.nVertices = 0;
        self.nFaces = 0;

    def addVertex(self,x,y,z):
        self.nVertices += 1;
        self.vertices.extend([x,y,z]);

    #add triangle composed of the three provided vertex indices
    def addTriangleFace(self, i,j,k):
        #first position means justa simple triangle
        self.nFaces += 1;
        self.faces.extend([0,int(i),int(j),int(k)]);

    """
        Get a json model from this model.
        For now we'll forget about colors, vertex normals, and all that stuff
    """
    def toJson(self):
        return JSON_TEMPLATE % {
            'vertices' : str(self.vertices),
            'faces' : str(self.faces),
            'nVertices': self.nVertices,
            'nFaces' : self.nFaces
        };


def getPaths(freeCadSVG):
    """
        freeCad svg is worthless-- except for paths, which are fairly useful
        this method accepts svg from fReeCAD and returns a list of strings suitable for inclusion in a path element
        returns two lists-- one list of visible lines, and one list of hidden lines

        HACK ALERT!!!!!
        FreeCAD does not give a way to determine which lines are hidden and which are not
        the only way to tell is that hidden lines are in a <g> with 0.15 stroke and visible are 0.35 stroke.
        so we actually look for that as a way to parse.

        to make it worse, elementTree xpath attribute selectors do not work in python 2.6, and we
        cannot use python 2.7 due to freecad. So its necessary to look for the pure strings! ick!
    """

    hiddenPaths = []
    visiblePaths = []
    if len(freeCadSVG) > 0:
        #yuk, freecad returns svg fragments. stupid stupid
        fullDoc = "<root>%s</root>" % freeCadSVG
        e = ET.ElementTree(ET.fromstring(fullDoc))
        segments = e.findall("//g")
        for s in segments:
            paths = s.findall("path")

            if s.get("stroke-width") == "0.15": #hidden line HACK HACK HACK
                mylist = hiddenPaths
            else:
                mylist = visiblePaths

            for p in paths:
                mylist.append(p.get("d"))
        return (hiddenPaths,visiblePaths)
    else:
        return ([],[])

def getSVG(shape,opts=None):
    """
        Export a shape to SVG
    """

    d = {'width':800,'height':240,'marginLeft':200,'marginTop':20}

    if opts:
        d.update(opts)

    #need to guess the scale and the coordinate center
    uom = guessUnitOfMeasure(shape)

    width=float(d['width'])
    height=float(d['height'])
    marginLeft=float(d['marginLeft'])
    marginTop=float(d['marginTop'])

    #TODO:  provide option to give 3 views
    viewVector = FreeCAD.Base.Vector(-1.75,1.1,5)
    (visibleG0,visibleG1,hiddenG0,hiddenG1) = Drawing.project(shape,viewVector)

    (hiddenPaths,visiblePaths) = getPaths(Drawing.projectToSVG(shape,viewVector,"ShowHiddenLines")) #this param is totally undocumented!

    #get bounding box -- these are all in 2-d space
    bb = visibleG0.BoundBox
    bb.add(visibleG1.BoundBox)
    bb.add(hiddenG0.BoundBox)
    bb.add(hiddenG1.BoundBox)

    #width pixels for x, height pixesl for y
    unitScale = min( width / bb.XLength * 0.75 , height / bb.YLength * 0.75 )

    #compute amount to translate-- move the top left into view
    (xTranslate,yTranslate) = ( (0 - bb.XMin) + marginLeft/unitScale ,(0- bb.YMax) - marginTop/unitScale)

    #compute paths ( again -- had to strip out freecad crap )
    hiddenContent = ""
    for p in hiddenPaths:
        hiddenContent += PATHTEMPLATE % p

    visibleContent = ""
    for p in visiblePaths:
        visibleContent += PATHTEMPLATE % p

    svg =  SVG_TEMPLATE % (
        {
            "unitScale" : str(unitScale),
            "strokeWidth" : str(1.0/unitScale),
            "hiddenContent" :  hiddenContent ,
            "visibleContent" :visibleContent,
            "xTranslate" : str(xTranslate),
            "yTranslate" : str(yTranslate),
            "width" : str(width),
            "height" : str(height),
            "textboxY" :str(height - 30),
            "uom" : str(uom)
        }
    )
    #svg = SVG_TEMPLATE % (
    #    {"content": projectedContent}
    #)
    return svg


def exportSVG(shape, fileName):
    """
        accept a cadquery shape, and export it to the provided file
        TODO: should use file-like objects, not a fileName, and/or be able to return a string instead
        export a view of a part to svg
    """

    svg = getSVG(shape.val().wrapped)
    f = open(fileName,'w')
    f.write(svg)
    f.close()



JSON_TEMPLATE= """\
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

PATHTEMPLATE="\t\t\t<path d=\"%s\" />\n"

