from typing import Iterable, Tuple, Dict, overload, Optional, Any, List
from typing_extensions import Protocol
from math import degrees
from itertools import groupby
import re

from OCP.TDocStd import TDocStd_Document
from OCP.TCollection import TCollection_ExtendedString
from OCP.XCAFDoc import XCAFDoc_DocumentTool, XCAFDoc_ColorType
from OCP.XCAFApp import XCAFApp_Application
from OCP.TDataStd import TDataStd_Name
from OCP.TDF import TDF_Label
from OCP.TopLoc import TopLoc_Location
from OCP.Quantity import Quantity_ColorRGBA
from OCP.BRepBuilderAPI import BRepBuilderAPI_Copy

from vtkmodules.vtkRenderingCore import (
    vtkActor,
    vtkPolyDataMapper as vtkMapper,
    vtkRenderer,
)

from .geom import Location
from .shapes import Shape, Compound
from .exporters.vtk import toString


class Color(object):
    """
    Wrapper for the OCCT color object Quantity_ColorRGBA.
    """

    wrapped: Quantity_ColorRGBA

    @overload
    def __init__(self, name: str):
        """
        Construct a Color from a name.

        :param name: name of the color, e.g. green
        """
        ...

    @overload
    def __init__(self, r: float, g: float, b: float, a: float = 0):
        """
        Construct a Color from RGB(A) values.

        :param r: red value, 0-1
        :param g: green value, 0-1
        :param b: blue value, 0-1
        :param a: alpha value, 0-1 (default: 0)
        """
        ...

    @overload
    def __init__(self):
        """
        Construct a Color with default value.
        """
        ...

    def __init__(self, *args, **kwargs):

        if len(args) == 0:
            self.wrapped = Quantity_ColorRGBA()
        elif len(args) == 1:
            self.wrapped = Quantity_ColorRGBA()
            exists = Quantity_ColorRGBA.ColorFromName_s(args[0], self.wrapped)
            if not exists:
                raise ValueError(f"Unknown color name: {args[0]}")
        elif len(args) == 3:
            r, g, b = args
            self.wrapped = Quantity_ColorRGBA(r, g, b, 1)
            if kwargs.get("a"):
                self.wrapped.SetAlpha(kwargs.get("a"))
        elif len(args) == 4:
            r, g, b, a = args
            self.wrapped = Quantity_ColorRGBA(r, g, b, a)
        else:
            raise ValueError(f"Unsupported arguments: {args}, {kwargs}")

    def toTuple(self) -> Tuple[float, float, float, float]:
        """
        Convert Color to RGB tuple.
        """
        a = self.wrapped.Alpha()
        rgb = self.wrapped.GetRGB()

        return (rgb.Red(), rgb.Green(), rgb.Blue(), a)


class AssemblyProtocol(Protocol):
    @property
    def loc(self) -> Location:
        ...

    @property
    def name(self) -> str:
        ...

    @property
    def parent(self) -> Optional["AssemblyProtocol"]:
        ...

    @property
    def color(self) -> Optional[Color]:
        ...

    @property
    def shapes(self) -> Iterable[Shape]:
        ...

    @property
    def children(self) -> Iterable["AssemblyProtocol"]:
        ...

    def traverse(self) -> Iterable[Tuple[str, "AssemblyProtocol"]]:
        ...

    def _flatten(self) -> Dict[str, "AssemblyProtocol"]:
        ...


def setName(l: TDF_Label, name: str):

    TDataStd_Name.Set_s(l, TCollection_ExtendedString(name))


def setColor(l: TDF_Label, color: Color, tool):

    tool.SetColor(l, color.wrapped, XCAFDoc_ColorType.XCAFDoc_ColorSurf)


def toCAF(
    assy: AssemblyProtocol,
    coloredSTEP: bool = False,
    mesh: bool = False,
    tolerance: float = 1e-3,
    angularTolerance: float = 0.1,
) -> Tuple[TDF_Label, TDocStd_Document]:

    # prepare a doc
    app = XCAFApp_Application.GetApplication_s()

    doc = TDocStd_Document(TCollection_ExtendedString("XmlOcaf"))
    app.InitDocument(doc)

    tool = XCAFDoc_DocumentTool.ShapeTool_s(doc.Main())
    tool.SetAutoNaming_s(True)
    ctool = XCAFDoc_DocumentTool.ColorTool_s(doc.Main())

    # add root
    top = tool.NewShape()
    TDataStd_Name.Set_s(top, TCollection_ExtendedString("CQ assembly"))

    # make compound, group by hashCode
    shape_names = {}
    shape_colors = {}
    assy_compounds = {}
    default_color = Color().toTuple()  # used in sorting; not assigned explicitly

    # (optional) naming convention pattern when shape referenced by multiple instances
    pat_shape_name = re.compile(r"^(\w+?)[:(_+\d)\d]")

    assy_flat = sorted(
        list(assy._flatten().values()),
        key=lambda assy: [s.hashCode() for s in assy.shapes],
    )
    for hashcodes, g0 in groupby(
        assy_flat, key=lambda assy: [s.hashCode() for s in assy.shapes]
    ):

        assys0 = list(g0)

        if not hashcodes:
            compound = None
        else:
            compound = Compound.makeCompound(assys0[0].shapes)
            if mesh:
                compound.mesh(tolerance, angularTolerance)

            # handle colors - this logic is needed for proper STEP export
            if coloredSTEP:

                assy_names = set([a.name for a in assys0])

                if len(assy_names) > 1:
                    i = 0
                    name_prefixes = []
                    # sample names that share common shape
                    while assy_names and i < 20:
                        if m := pat_shape_name.match(assy_names.pop()):
                            name_prefixes.append(m.group(1))
                        i += 1
                    if len(name_prefixes) == i and len(set(name_prefixes)) == 1:
                        # apply common prefix
                        shape_name = f"{name_prefixes[0]}_part"
                    else:
                        # common name prefix not found
                        shape_name = str(compound.hashCode())

                else:
                    shape_name = f"{assy_names.pop()}_part"

                colors = []
                for a in assys0:
                    color = a.color
                    tmp = a
                    while not color and tmp.parent:
                        tmp = tmp.parent
                        color = tmp.color

                    colors.append(color)

                # group by colors
                assys_colors0 = sorted(
                    zip(assys0, colors),
                    key=lambda x: x[1].toTuple() if x[1] else default_color,
                )
                for k_color, g1 in groupby(
                    assys_colors0,
                    key=lambda x: x[1].toTuple() if x[1] else default_color,
                ):

                    compound = Compound(
                        BRepBuilderAPI_Copy(compound.wrapped, True, mesh).Shape()
                    )

                    assys_colors1 = list(g1)
                    for a, _ in assys_colors1:
                        assy_compounds[a.name] = compound

                    shape_names[compound] = shape_name
                    shape_colors[compound] = assys_colors1[0][1]

            else:
                for a in assys0:
                    assy_compounds[a.name] = compound

    # add leaf nodes and subassemblies
    subassys: Dict[str, Tuple[TDF_Label, Location]] = {}

    for k, v in assy.traverse():

        # assy part
        subassy = tool.NewShape()

        if compound := assy_compounds.get(v.name, None):
            if coloredSTEP:
                if tool.FindShape(compound.wrapped).IsNull():

                    label = tool.NewShape()
                    tool.SetShape(label, compound.wrapped)
                    setName(label, shape_names[compound])
                    if color := shape_colors[compound]:
                        setColor(label, color, ctool)

                else:
                    label = tool.NewShape()
                    tool.SetShape(label, compound.wrapped)
                    setName(label, shape_names[compound])
            else:
                label = tool.NewShape()
                tool.SetShape(label, compound.wrapped)
                setName(label, f"{k}_part")
                if v.color:
                    setColor(subassy, v.color, ctool)

            tool.AddComponent(subassy, label, TopLoc_Location())

        else:
            if v.color:
                setColor(subassy, v.color, ctool)

        setName(subassy, k)
        subassys[k] = (subassy, v.loc)

        for ch in v.children:
            tool.AddComponent(
                subassy, subassys[ch.name][0], subassys[ch.name][1].wrapped
            )

    tool.AddComponent(top, subassys[assy.name][0], assy.loc.wrapped)
    tool.UpdateAssemblies()

    return top, doc


def toVTK(
    assy: AssemblyProtocol,
    renderer: vtkRenderer = vtkRenderer(),
    loc: Location = Location(),
    color: Tuple[float, float, float, float] = (1.0, 1.0, 1.0, 1.0),
    tolerance: float = 1e-3,
    angularTolerance: float = 0.1,
) -> vtkRenderer:

    loc = loc * assy.loc
    trans, rot = loc.toTuple()

    if assy.color:
        color = assy.color.toTuple()

    if assy.shapes:
        data = Compound.makeCompound(assy.shapes).toVtkPolyData(
            tolerance, angularTolerance
        )

        mapper = vtkMapper()
        mapper.SetInputData(data)

        actor = vtkActor()
        actor.SetMapper(mapper)
        actor.SetPosition(*trans)
        actor.SetOrientation(*map(degrees, rot))
        actor.GetProperty().SetColor(*color[:3])
        actor.GetProperty().SetOpacity(color[3])

        renderer.AddActor(actor)

    for child in assy.children:
        renderer = toVTK(child, renderer, loc, color, tolerance, angularTolerance)

    return renderer


def toJSON(
    assy: AssemblyProtocol,
    loc: Location = Location(),
    color: Tuple[float, float, float, float] = (1.0, 1.0, 1.0, 1.0),
    tolerance: float = 1e-3,
) -> List[Dict[str, Any]]:

    loc = loc * assy.loc
    trans, rot = loc.toTuple()

    if assy.color:
        color = assy.color.toTuple()

    rv = []

    if assy.shapes:
        val: Any = {}

        data = toString(Compound.makeCompound(assy.shapes), tolerance)

        val["shape"] = data
        val["color"] = color
        val["position"] = trans
        val["orientation"] = rot

        rv.append(val)

    for child in assy.children:
        rv.extend(toJSON(child, loc, color, tolerance))

    return rv
