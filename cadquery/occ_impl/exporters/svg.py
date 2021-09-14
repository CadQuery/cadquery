import io as StringIO

from ..shapes import Shape, Compound, TOLERANCE
from ..geom import BoundBox


from OCP.gp import gp_Ax2, gp_Pnt, gp_Dir
from OCP.BRepLib import BRepLib
from OCP.HLRBRep import HLRBRep_Algo, HLRBRep_HLRToShape
from OCP.HLRAlgo import HLRAlgo_Projector
from OCP.GCPnts import GCPnts_QuasiUniformDeflection

DISCRETIZATION_TOLERANCE = 1e-3

SVG_TEMPLATE = """<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<svg
   xmlns:svg="http://www.w3.org/2000/svg"
   xmlns="http://www.w3.org/2000/svg"
   width="%(width)s"
   height="%(height)s"

>
    <g transform="scale(%(unitScale)s, -%(unitScale)s)   translate(%(xTranslate)s,%(yTranslate)s)" stroke-width="%(strokeWidth)s"  fill="none">
       <!-- hidden lines -->
       <g  stroke="rgb(%(hiddenColor)s)" fill="none" stroke-dasharray="%(strokeWidth)s,%(strokeWidth)s" >
%(hiddenContent)s
       </g>

       <!-- solid lines -->
       <g  stroke="rgb(%(strokeColor)s)" fill="none">
%(visibleContent)s
       </g>
    </g>
    %(axesIndicator)s
</svg>
"""

# The axes indicator - needs to be replaced with something dynamic eventually
AXES_TEMPLATE = """<g transform="translate(20,%(textboxY)s)" stroke="rgb(0,0,255)">
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
    </g>"""

PATHTEMPLATE = '\t\t\t<path d="%s" />\n'


class UNITS:
    MM = "mm"
    IN = "in"


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


def makeSVGedge(e):
    """
    Creates an SVG edge from a OCCT edge.
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
    Collects the visible and hidden edges from the CadQuery object.
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
    Export a shape to SVG text.

    :param shape: A CadQuery shape object to convert to an SVG string.
    :type Shape: Vertex, Edge, Wire, Face, Shell, Solid, or Compound.
    :param opts: An options dictionary that influences the SVG that is output.
    :type opts: Dictionary, keys are as follows:
        width: Document width of the resulting image.
        height: Document height of the resulting image.
        marginLeft: Inset margin from the left side of the document.
        marginTop: Inset margin from the top side of the document.
        projectionDir: Direction the camera will view the shape from.
        showAxes: Whether or not to show the axes indicator, which will only be
                  visible when the projectionDir is also at the default.
        strokeWidth: Width of the line that visible edges are drawn with.
        strokeColor: Color of the line that visible edges are drawn with.
        hiddenColor: Color of the line that hidden edges are drawn with.
        showHidden: Whether or not to show hidden lines.
    """

    # Available options and their defaults
    d = {
        "width": 800,
        "height": 240,
        "marginLeft": 200,
        "marginTop": 20,
        "projectionDir": (-1.75, 1.1, 5),
        "showAxes": True,
        "strokeWidth": -1.0,  # -1 = calculated based on unitScale
        "strokeColor": (0, 0, 0),  # RGB 0-255
        "hiddenColor": (160, 160, 160),  # RGB 0-255
        "showHidden": True,
    }

    if opts:
        d.update(opts)

    # need to guess the scale and the coordinate center
    uom = guessUnitOfMeasure(shape)

    width = float(d["width"])
    height = float(d["height"])
    marginLeft = float(d["marginLeft"])
    marginTop = float(d["marginTop"])
    projectionDir = tuple(d["projectionDir"])
    showAxes = bool(d["showAxes"])
    strokeWidth = float(d["strokeWidth"])
    strokeColor = tuple(d["strokeColor"])
    hiddenColor = tuple(d["hiddenColor"])
    showHidden = bool(d["showHidden"])

    hlr = HLRBRep_Algo()
    hlr.Add(shape.wrapped)

    projector = HLRAlgo_Projector(gp_Ax2(gp_Pnt(), gp_Dir(*projectionDir)))

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

    # get bounding box -- these are all in 2D space
    bb = Compound.makeCompound(hidden + visible).BoundingBox()

    # width pixels for x, height pixels for y
    unitScale = min(width / bb.xlen * 0.75, height / bb.ylen * 0.75)

    # compute amount to translate-- move the top left into view
    (xTranslate, yTranslate) = (
        (0 - bb.xmin) + marginLeft / unitScale,
        (0 - bb.ymax) - marginTop / unitScale,
    )

    # If the user did not specify a stroke width, calculate it based on the unit scale
    if strokeWidth == -1.0:
        strokeWidth = 1.0 / unitScale

    # compute paths
    hiddenContent = ""

    # Prevent hidden paths from being added if the user disabled them
    if showHidden:
        for p in hiddenPaths:
            hiddenContent += PATHTEMPLATE % p

    visibleContent = ""
    for p in visiblePaths:
        visibleContent += PATHTEMPLATE % p

    # If the caller wants the axes indicator and is using the default direction, add in the indicator
    if showAxes and projectionDir == (-1.75, 1.1, 5):
        axesIndicator = AXES_TEMPLATE % (
            {"unitScale": str(unitScale), "textboxY": str(height - 30), "uom": str(uom)}
        )
    else:
        axesIndicator = ""

    svg = SVG_TEMPLATE % (
        {
            "unitScale": str(unitScale),
            "strokeWidth": str(strokeWidth),
            "strokeColor": ",".join([str(x) for x in strokeColor]),
            "hiddenColor": ",".join([str(x) for x in hiddenColor]),
            "hiddenContent": hiddenContent,
            "visibleContent": visibleContent,
            "xTranslate": str(xTranslate),
            "yTranslate": str(yTranslate),
            "width": str(width),
            "height": str(height),
            "textboxY": str(height - 30),
            "uom": str(uom),
            "axesIndicator": axesIndicator,
        }
    )

    return svg


def exportSVG(shape, fileName: str, opts=None):
    """
    Accept a cadquery shape, and export it to the provided file
    TODO: should use file-like objects, not a fileName, and/or be able to return a string instead
    export a view of a part to svg
    """

    svg = getSVG(shape.val(), opts)
    f = open(fileName, "w")
    f.write(svg)
    f.close()
