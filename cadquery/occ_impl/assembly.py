from typing import Union, Iterable, Tuple, Dict, overload, Optional, Any, List
from typing_extensions import Protocol
from math import degrees

from OCP.TDocStd import TDocStd_Document
from OCP.TCollection import TCollection_ExtendedString
from OCP.XCAFDoc import XCAFDoc_DocumentTool, XCAFDoc_ColorType, XCAFDoc_ColorGen
from OCP.XCAFApp import XCAFApp_Application
from OCP.TDataStd import TDataStd_Name
from OCP.TDF import TDF_Label
from OCP.TopLoc import TopLoc_Location
from OCP.Quantity import Quantity_ColorRGBA
from OCP.TopoDS import TopoDS_Compound
from OCP.BRep import BRep_Tool, BRep_Builder
from OCP.BRepAlgoAPI import BRepAlgoAPI_Fuse
from OCP.TopTools import TopTools_ListOfShape
from OCP.BOPAlgo import BOPAlgo_GlueEnum

from vtkmodules.vtkRenderingCore import (
    vtkActor,
    vtkPolyDataMapper as vtkMapper,
    vtkRenderer,
)

from .geom import Location
from .shapes import Shape, Compound, Solid
from .exporters.vtk import toString
from ..cq import Workplane

# type definitions
AssemblyObjects = Union[Shape, Workplane, None]


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

    @loc.setter
    def loc(self, value: Location) -> None:
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


def setName(l: TDF_Label, name: str, tool):

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
    tool.SetAutoNaming_s(False)
    ctool = XCAFDoc_DocumentTool.ColorTool_s(doc.Main())

    # used to store labels with unique part-color combinations
    unique_objs: Dict[Tuple[Color, AssemblyObjects], TDF_Label] = {}
    # used to cache unique, possibly meshed, compounds; allows to avoid redundant meshing operations if same object is referenced multiple times in an assy
    compounds: Dict[AssemblyObjects, Compound] = {}

    def _toCAF(el, ancestor, color) -> TDF_Label:

        # create a subassy
        subassy = tool.NewShape()
        setName(subassy, el.name, tool)

        # define the current color
        current_color = el.color if el.color else color

        # add a leaf with the actual part if needed
        if el.obj:
            # get/register unique parts referenced in the assy
            key0 = (current_color, el.obj)  # (color, shape)
            key1 = el.obj  # shape

            if key0 in unique_objs:
                lab = unique_objs[key0]
            else:
                lab = tool.NewShape()
                if key1 in compounds:
                    compound = compounds[key1].copy(mesh)
                else:
                    compound = Compound.makeCompound(el.shapes)
                    if mesh:
                        compound.mesh(tolerance, angularTolerance)

                    compounds[key1] = compound

                tool.SetShape(lab, compound.wrapped)
                setName(lab, f"{el.name}_part", tool)
                unique_objs[key0] = lab

                # handle colors when exporting to STEP
                if coloredSTEP and current_color:
                    setColor(lab, current_color, ctool)

            tool.AddComponent(subassy, lab, TopLoc_Location())

        # handle colors when *not* exporting to STEP
        if not coloredSTEP and current_color:
            setColor(subassy, current_color, ctool)

        # add children recursively
        for child in el.children:
            _toCAF(child, subassy, current_color)

        if ancestor:
            # add the current subassy to the higher level assy
            tool.AddComponent(ancestor, subassy, el.loc.wrapped)

        return subassy

    # process the whole assy recursively
    top = _toCAF(assy, None, None)

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
    """
    Export an object to a structure suitable for converting to VTK.js JSON.
    """

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


def toSimplifiedCAF(assy: AssemblyProtocol, assy_name: str) -> TDocStd_Document:
    """
    Converts the assembly to a compound and saves that within the document
    to be exported.

    :param assy: Assembly that is being converted to a compound for the document.
    :param assy_name: Label that is applied to the top level object in the document.
    """

    # Prepare a document
    app = XCAFApp_Application.GetApplication_s()
    doc = TDocStd_Document(TCollection_ExtendedString("XmlOcaf"))
    app.InitDocument(doc)

    # Shape and color tools
    shape_tool = XCAFDoc_DocumentTool.ShapeTool_s(doc.Main())
    color_tool = XCAFDoc_DocumentTool.ColorTool_s(doc.Main())
    shape_tool.SetAutoNaming_s(False)

    # Convert the assembly to a compound
    shape_list = []
    for part in assy.children:
        for shape in part.shapes:
            # Make sure that we only add solids
            if isinstance(shape, Solid):
                shape_list.append(shape)
    comp = Compound.makeCompound(shape_list).wrapped

    # Add the top level shape, have it broken apart into an assembly and set the top-level name
    top_level_lbl = shape_tool.AddShape(comp, True)
    TDataStd_Name.Set_s(top_level_lbl, TCollection_ExtendedString(assy_name))

    # Assign names and colors based on the assembly
    for part in assy.children:
        for shape in part.shapes:
            # Make sure that we only trying to set the names and colors for solids
            if isinstance(shape, Solid):
                cur_lbl = shape_tool.FindShape(shape.wrapped)
                TDataStd_Name.Set_s(cur_lbl, TCollection_ExtendedString(part.name))
                color_tool.SetColor(cur_lbl, part.color.wrapped, XCAFDoc_ColorGen)

    return doc


def toFusedCAF(assy: AssemblyProtocol, assy_name: str, glue: Optional[bool] = False, tol: Optional[float] = None) -> TDocStd_Document:
    """
    Converts the assembly to a fused compound and saves that within the document
    to be exported in a way that preserves the face colors. Because of the use of
    boolean operations in this method, performance may be slow in some cases.

    :param assy: Assembly that is being converted to a fused compound for the document.
    :param assy_name: Label that is applied to the top level object in the document.
    """

    # Prepare the document
    app = XCAFApp_Application.GetApplication_s()
    doc = TDocStd_Document(TCollection_ExtendedString("XmlOcaf"))
    app.InitDocument(doc)

    # Shape and color tools
    shape_tool = XCAFDoc_DocumentTool.ShapeTool_s(doc.Main())
    color_tool = XCAFDoc_DocumentTool.ColorTool_s(doc.Main())

    # To fuse the parts of the assembly together
    fuse_op = BRepAlgoAPI_Fuse()
    args = TopTools_ListOfShape()
    tools = TopTools_ListOfShape()

    # If there is only one solid, there is no reason to fuse, and it will likely cause problems anyway
    top_level_shape = None
    if len(assy.children) == 1 and len(assy.children[0].shapes) == 1:
        top_level_shape = assy.children[0].shapes[0].wrapped
    else:
        # Add base shape(s)
        for shape in assy.children[0].shapes:
            args.Append(shape.wrapped)

        # Add all other shapes as tools
        i = 0
        for child in assy.children:
            # Make sure we add the assembly parts other than the base
            if i == 0:
                i += 1
                continue

            for shape in child.shapes:
                tools.Append(shape.wrapped)

            i += 1

        # Allow the caller to configure the fuzzy and glue settings
        if tol:
            fuse_op.SetFuzzyValue(tol)
        if glue:
            fuse_op.SetGlue(BOPAlgo_GlueEnum.BOPAlgo_GlueShift)

        fuse_op.SetArguments(args)
        fuse_op.SetTools(tools)
        fuse_op.Build()

        top_level_shape = fuse_op.Shape()

    # If the top level shape is still none, something is wrong
    if top_level_shape == None or top_level_shape.IsNull():
        raise Exception("Error: The top level shape of assembly " + assy_name + " is not valid.")

    # Add the fused shape as the top level object in the document
    top_level_lbl = shape_tool.AddShape(top_level_shape, False)
    TDataStd_Name.Set_s(top_level_lbl, TCollection_ExtendedString(assy_name))

    # Walk the assembly->part->shape->face hierarchy and add subshapes for all the faces
    for part in assy.children:
        for shape in part.shapes:
            for face in shape.Faces():
                # Check for modified faces
                modded_list = fuse_op.Modified(face.wrapped)

                # If there are no modified faces associated with this face, treat it as-is
                if modded_list.Size() == 0:
                    # Avoid adding the shape if there are no faces
                    if shape_tool.IsSubShape(top_level_lbl, face.wrapped):
                        # Add the face as a subshape
                        cur_lbl = shape_tool.AddSubShape(top_level_lbl, face.wrapped)

                        # Set the subshape's color to match the parent assembly component
                        color_tool.SetColor(cur_lbl, part.color.wrapped, XCAFDoc_ColorGen)
                # If there are modified faces based on this face, step through all of them and add
                # them separately as subshapes
                else:
                    for mod in modded_list:
                        # Add the face as a subshape and set its color to match the parent assembly component
                        cur_lbl = shape_tool.AddSubShape(top_level_lbl, mod)
                        color_tool.SetColor(
                            cur_lbl, part.color.wrapped, XCAFDoc_ColorGen
                        )

                # Handle generated faces
                gen_list = fuse_op.Generated(face.wrapped)
                if gen_list.Size() > 0:
                    for gen in gen_list:
                        # Add the face as a subshape and set its color to match the parent assembly component
                        cur_lbl = shape_tool.AddSubShape(top_level_lbl, gen)
                        color_tool.SetColor(
                            cur_lbl, part.color.wrapped, XCAFDoc_ColorGen
                        )
    return doc
