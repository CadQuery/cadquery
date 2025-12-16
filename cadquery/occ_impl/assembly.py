from typing import (
    Union,
    Iterable,
    Iterator,
    Tuple,
    Dict,
    overload,
    Optional,
    Any,
    List,
    cast,
)
from typing_extensions import Protocol, Self
from math import degrees, radians

from OCP.TCollection import TCollection_HAsciiString
from OCP.TDocStd import TDocStd_Document
from OCP.TCollection import TCollection_ExtendedString
from OCP.XCAFDoc import (
    XCAFDoc_DocumentTool,
    XCAFDoc_ColorType,
    XCAFDoc_ColorGen,
    XCAFDoc_Material,
    XCAFDoc_VisMaterial,
)
from OCP.XCAFApp import XCAFApp_Application
from OCP.BinXCAFDrivers import BinXCAFDrivers
from OCP.XmlXCAFDrivers import XmlXCAFDrivers
from OCP.TDataStd import TDataStd_Name
from OCP.TDF import TDF_Label
from OCP.TopLoc import TopLoc_Location
from OCP.Quantity import (
    Quantity_ColorRGBA,
    Quantity_Color,
    Quantity_TOC_sRGB,
    Quantity_TOC_RGB,
)
from OCP.BRepAlgoAPI import BRepAlgoAPI_Fuse
from OCP.TopTools import TopTools_ListOfShape
from OCP.BOPAlgo import BOPAlgo_GlueEnum, BOPAlgo_MakeConnected
from OCP.TopoDS import TopoDS_Shape
from OCP.gp import gp_EulerSequence

from vtkmodules.vtkRenderingCore import (
    vtkActor,
    vtkPolyDataMapper as vtkMapper,
    vtkRenderer,
    vtkProp3D,
)

from vtkmodules.vtkFiltersExtraction import vtkExtractCellsByType
from vtkmodules.vtkCommonDataModel import VTK_TRIANGLE, VTK_LINE, VTK_VERTEX

from .geom import Location
from .shapes import Shape, Solid, Compound
from .exporters.vtk import toString
from ..cq import Workplane
from ..utils import BiDict

# type definitions
AssemblyObjects = Union[Shape, Workplane, None]


class Material(object):
    """
    Wrapper for the OCCT material classes XCAFDoc_Material and XCAFDoc_VisMaterial.
    XCAFDoc_Material is focused on physical material properties and
    XCAFDoc_VisMaterial is for visual properties to be used when rendering.
    """

    wrapped: XCAFDoc_Material
    wrapped_vis: XCAFDoc_VisMaterial

    def __init__(self, name: str | None = None, **kwargs):
        """
        Can be passed an arbitrary string name for the material along with keyword
        arguments defining some other characteristics of the material. If nothing is
        passed, arbitrary defaults are used.
        """

        # Create the default material object and prepare to set a few defaults
        self.wrapped = XCAFDoc_Material()

        # Default values in case the user did not set any others
        aName = "Default"
        aDescription = "Default material with properties similar to low carbon steel"
        aDensity = 7.85
        aDensityName = "Mass density"
        aDensityTypeName = "g/cm^3"

        # See if there are any non-defaults to be set
        if name:
            aName = name
        if "description" in kwargs.keys():
            aDescription = kwargs["description"]
        if "density" in kwargs.keys():
            aDensity = kwargs["density"]
        if "densityUnit" in kwargs.keys():
            aDensityTypeName = kwargs["densityUnit"]

        # Set the properties on the material object
        self.wrapped.Set(
            TCollection_HAsciiString(aName),
            TCollection_HAsciiString(aDescription),
            aDensity,
            TCollection_HAsciiString(aDensityName),
            TCollection_HAsciiString(aDensityTypeName),
        )

        # Create the default visual material object and allow it to be used just with
        # the OCC layer, for now. When this material class is expanded to include visual
        # attributes, the OCC docs say that XCAFDoc_VisMaterialTool should be used to
        # manage those attributes on the XCAFDoc_VisMaterial class.
        self.wrapped_vis = XCAFDoc_VisMaterial()

    @property
    def name(self) -> str:
        """
        Get the string name of the material.
        """
        return self.wrapped.GetName().ToCString()

    @property
    def description(self) -> str:
        """
        Get the string description of the material.
        """
        return self.wrapped.GetDescription().ToCString()

    @property
    def density(self) -> float:
        """
        Get the density value of the material.
        """
        return self.wrapped.GetDensity()

    @property
    def densityUnit(self) -> str:
        """
        Get the units that the material density is defined in.
        """
        return self.wrapped.GetDensValType().ToCString()

    def toTuple(self) -> Tuple[str, str, float, str]:
        """
        Convert Material to a tuple.
        """
        name = self.name
        description = self.description
        density = self.density
        densityUnit = self.densityUnit

        return (name, description, density, densityUnit)

    def __hash__(self):
        """
        Create a unique hash for this material via its tuple.
        """
        return hash(self.toTuple())

    def __eq__(self, other):
        """
        Check equality of this material against another via its tuple.
        """
        return self.toTuple() == other.toTuple()

    def __getstate__(self) -> Tuple[str, str, float, str]:
        """
        Allows pickling.
        """
        return self.toTuple()

    def __setstate__(self, data: Tuple[str, str, float, str]):
        """
        Allows pickling.
        """
        self.wrapped = XCAFDoc_Material()
        self.wrapped.Set(
            TCollection_HAsciiString(data[0]),
            TCollection_HAsciiString(data[1]),
            data[2],
            TCollection_HAsciiString("Mass density"),
            TCollection_HAsciiString(data[3]),
        )


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
    def __init__(self, r: float, g: float, b: float, a: float = 0, srgb: bool = True):
        """
        Construct a Color from RGB(A) values.

        :param r: red value, 0-1
        :param g: green value, 0-1
        :param b: blue value, 0-1
        :param a: alpha value, 0-1 (default: 0)
        :param srgb: srgb/linear rgb switch, bool (default: True)
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
            self.wrapped = Quantity_ColorRGBA(
                Quantity_Color(r, g, b, Quantity_TOC_sRGB), 1
            )
            if kwargs.get("a"):
                self.wrapped.SetAlpha(kwargs.get("a"))
        elif len(args) == 4:
            r, g, b, a = args
            self.wrapped = Quantity_ColorRGBA(
                Quantity_Color(r, g, b, Quantity_TOC_sRGB), a
            )
        elif len(args) == 5:
            r, g, b, a, srgb = args
            self.wrapped = Quantity_ColorRGBA(
                Quantity_Color(
                    r, g, b, Quantity_TOC_sRGB if srgb else Quantity_TOC_RGB
                ),
                a,
            )
        else:
            raise ValueError(f"Unsupported arguments: {args}, {kwargs}")

    def __hash__(self):

        return hash(self.toTuple())

    def __eq__(self, other):

        return self.toTuple() == other.toTuple()

    def toTuple(self) -> Tuple[float, float, float, float]:
        """
        Convert Color to RGB tuple.
        """
        a = self.wrapped.Alpha()
        rgb = self.wrapped.GetRGB().Values(Quantity_TOC_sRGB)

        return (*rgb, a)

    def __getstate__(self) -> Tuple[float, float, float, float]:

        return self.toTuple()

    def __setstate__(self, data: Tuple[float, float, float, float]):

        self.wrapped = Quantity_ColorRGBA(*data)


class AssemblyProtocol(Protocol):
    def __init__(
        self,
        obj: AssemblyObjects = None,
        loc: Optional[Location] = None,
        name: Optional[str] = None,
        color: Optional[Color] = None,
    ):
        ...

    @property
    def loc(self) -> Location:
        ...

    @loc.setter
    def loc(self, value: Location) -> None:
        ...

    @property
    def name(self) -> str:
        ...

    @name.setter
    def name(self, value: str) -> None:
        ...

    @property
    def parent(self) -> Optional["AssemblyProtocol"]:
        ...

    @property
    def color(self) -> Optional[Color]:
        ...

    @color.setter
    def color(self, value: Optional[Color]) -> None:
        ...

    @property
    def obj(self) -> AssemblyObjects:
        ...

    @obj.setter
    def obj(self, value: AssemblyObjects) -> None:
        ...

    @property
    def objects(self) -> Dict[str, Self]:
        ...

    @property
    def shapes(self) -> Iterable[Shape]:
        ...

    @property
    def children(self) -> Iterable["AssemblyProtocol"]:
        ...

    @property
    def _subshape_names(self) -> BiDict[Shape, str]:
        ...

    @property
    def _subshape_colors(self) -> BiDict[Shape, Color]:
        ...

    @property
    def _subshape_layers(self) -> BiDict[Shape, str]:
        ...

    @overload
    def add(
        self,
        obj: Self,
        loc: Optional[Location] = None,
        name: Optional[str] = None,
        color: Optional[Color] = None,
    ) -> Self:
        ...

    @overload
    def add(
        self,
        obj: AssemblyObjects,
        loc: Optional[Location] = None,
        name: Optional[str] = None,
        color: Optional[Color] = None,
        material: Optional[Union[Material, str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Self:
        ...

    def add(
        self,
        obj: Union[Self, AssemblyObjects],
        loc: Optional[Location] = None,
        name: Optional[str] = None,
        color: Optional[Color] = None,
        material: Optional[Union[Material, str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> Self:
        """
        Add a subassembly to the current assembly.
        """
        ...

    def addSubshape(
        self,
        s: Shape,
        name: Optional[str] = None,
        color: Optional[Color] = None,
        layer: Optional[str] = None,
    ) -> Self:
        ...

    def traverse(self) -> Iterable[Tuple[str, "AssemblyProtocol"]]:
        ...

    def __iter__(
        self,
        loc: Optional[Location] = None,
        name: Optional[str] = None,
        color: Optional[Color] = None,
    ) -> Iterator[Tuple[Shape, str, Location, Optional[Color]]]:
        ...

    def __getitem__(self, name: str) -> Self | Shape:
        ...

    def __contains__(self, name: str) -> bool:
        ...


def setName(l: TDF_Label, name: str, tool):

    TDataStd_Name.Set_s(l, TCollection_ExtendedString(name))


def setColor(l: TDF_Label, color: Color, tool):

    tool.SetColor(l, color.wrapped, XCAFDoc_ColorType.XCAFDoc_ColorSurf)


def setMaterial(l: TDF_Label, material: Material, tool):

    tool.SetMaterial(
        l,
        TCollection_HAsciiString(material.name),
        TCollection_HAsciiString(material.description),
        material.density,
        TCollection_HAsciiString("MassDensity"),
        TCollection_HAsciiString(material.densityUnit),
    )


def toCAF(
    assy: AssemblyProtocol,
    coloredSTEP: bool = False,
    mesh: bool = False,
    tolerance: float = 1e-3,
    angularTolerance: float = 0.1,
    binary: bool = True,
) -> Tuple[TDF_Label, TDocStd_Document]:

    # prepare a doc
    app = XCAFApp_Application.GetApplication_s()

    if binary:
        BinXCAFDrivers.DefineFormat_s(app)
        doc = TDocStd_Document(TCollection_ExtendedString("BinXCAF"))
    else:
        XmlXCAFDrivers.DefineFormat_s(app)
        doc = TDocStd_Document(TCollection_ExtendedString("XmlXCAF"))

    app.InitDocument(doc)

    tool = XCAFDoc_DocumentTool.ShapeTool_s(doc.Main())
    tool.SetAutoNaming_s(False)
    ctool = XCAFDoc_DocumentTool.ColorTool_s(doc.Main())
    ltool = XCAFDoc_DocumentTool.LayerTool_s(doc.Main())
    mtool = XCAFDoc_DocumentTool.MaterialTool_s(doc.Main())

    # used to store labels with unique part-color combinations
    unique_objs: Dict[Tuple[Color | None, AssemblyObjects], TDF_Label] = {}
    # used to cache unique, possibly meshed, compounds; allows to avoid redundant meshing operations if same object is referenced multiple times in an assy
    compounds: Dict[AssemblyObjects, Compound] = {}

    def _toCAF(el: AssemblyProtocol, ancestor: TDF_Label | None) -> TDF_Label:

        # create a subassy if needed
        if el.children:
            subassy = tool.NewShape()
            setName(subassy, el.name, tool)

        # define the current color
        current_color = el.color if el.color else None

        # define the current material
        current_material = el.material if el.material else None

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
                setName(lab, f"{el.name}_part" if el.children else el.name, tool)
                unique_objs[key0] = lab

                # handle colors when exporting to STEP
                if coloredSTEP and current_color:
                    setColor(lab, current_color, ctool)

                # Handle materials when exporting to STEP
                if current_material:
                    setMaterial(lab, current_material, mtool)

            # handle subshape names/colors/layers
            subshape_colors = el._subshape_colors
            subshape_names = el._subshape_names
            subshape_layers = el._subshape_layers

            for k in (
                subshape_colors.keys() | subshape_names.keys() | subshape_layers.keys()
            ):

                subshape_label = tool.AddSubShape(lab, k.wrapped)

                # Sanity check, this is in principle enforced when calling addSubshape
                assert not subshape_label.IsNull(), "Invalid subshape"

                # Set the name
                if k in subshape_names:
                    TDataStd_Name.Set_s(
                        subshape_label, TCollection_ExtendedString(subshape_names[k]),
                    )

                # Set the individual subshape color
                if k in subshape_colors:
                    ctool.SetColor(
                        subshape_label, subshape_colors[k].wrapped, XCAFDoc_ColorGen,
                    )

                # Also add a layer to hold the subshape label data
                if k in subshape_layers:
                    layer_label = ltool.AddLayer(
                        TCollection_ExtendedString(subshape_layers[k])
                    )
                    ltool.SetLayer(subshape_label, layer_label)

            if el.children:
                lab = tool.AddComponent(subassy, lab, TopLoc_Location())
                setName(lab, f"{el.name}_part", tool)
            elif ancestor is not None:
                lab = tool.AddComponent(ancestor, lab, el.loc.wrapped)
                setName(lab, f"{el.name}", tool)

        # handle colors when *not* exporting to STEP
        if not coloredSTEP and current_color:
            if el.children:
                setColor(subassy, current_color, ctool)

            if el.obj:
                setColor(lab, current_color, ctool)

        # add children recursively
        for child in el.children:
            _toCAF(child, subassy)

        # final rv construction
        if ancestor and el.children:
            tool.AddComponent(ancestor, subassy, el.loc.wrapped)
            rv = subassy
        elif ancestor:
            rv = ancestor
        elif el.children:
            # update the top level location
            rv = TDF_Label()  # NB: additional label is needed to apply the location

            # set location, if location is identity return subassy
            tool.SetLocation(subassy, assy.loc.wrapped, rv)
            setName(rv, assy.name, tool)
        elif el.obj:
            # only root with an object
            rv = tool.NewShape()

            lab = tool.AddComponent(rv, lab, el.loc.wrapped)
            setName(lab, f"{el.name}", tool)
        else:
            raise ValueError("Cannot convert an empty assembly to CAF")

        return rv

    # process the whole assy recursively
    top = _toCAF(assy, None)

    tool.UpdateAssemblies()

    return top, doc


def _loc2vtk(
    loc: Location,
) -> Tuple[Tuple[float, float, float], Tuple[float, float, float]]:
    """
    Convert location to t,rot pair following vtk conventions
    """

    T = loc.wrapped.Transformation()

    trans = T.TranslationPart().Coord()
    rot = tuple(
        map(degrees, T.GetRotation().GetEulerAngles(gp_EulerSequence.gp_Intrinsic_ZXY),)
    )

    return trans, (rot[1], rot[2], rot[0])


def toVTKAssy(
    assy: AssemblyProtocol,
    color: Tuple[float, float, float, float] = (1.0, 1.0, 1.0, 1.0),
    edgecolor: Tuple[float, float, float, float] = (0.0, 0.0, 0.0, 0.0),
    edges: bool = True,
    linewidth: float = 2,
    tolerance: float = 1e-3,
    angularTolerance: float = 0.1,
) -> List[vtkProp3D]:

    rv: List[vtkProp3D] = []

    for shape, _, loc, col_ in assy:

        col = col_.toTuple() if col_ else color

        trans, rot = _loc2vtk(loc)

        data = shape.toVtkPolyData(tolerance, angularTolerance)

        # extract faces
        extr = vtkExtractCellsByType()
        extr.SetInputDataObject(data)

        extr.AddCellType(VTK_LINE)
        extr.AddCellType(VTK_VERTEX)
        extr.Update()
        data_edges = extr.GetOutput()

        # extract edges
        extr = vtkExtractCellsByType()
        extr.SetInputDataObject(data)

        extr.AddCellType(VTK_TRIANGLE)
        extr.Update()
        data_faces = extr.GetOutput()

        # remove normals from edges
        data_edges.GetPointData().RemoveArray("Normals")

        # add both to the vtkAssy
        mapper = vtkMapper()
        mapper.AddInputDataObject(data_faces)

        actor = vtkActor()
        actor.SetMapper(mapper)
        actor.SetPosition(*trans)
        actor.SetOrientation(*rot)
        actor.GetProperty().SetColor(*col[:3])
        actor.GetProperty().SetOpacity(col[3])

        rv.append(actor)

        mapper = vtkMapper()
        mapper.AddInputDataObject(data_edges)

        actor = vtkActor()
        actor.SetMapper(mapper)
        actor.SetPosition(*trans)
        actor.SetOrientation(*rot)
        actor.GetProperty().SetLineWidth(linewidth)
        actor.SetVisibility(edges)
        actor.GetProperty().SetColor(*edgecolor[:3])

        rv.append(actor)

    return rv


def toVTK(
    assy: AssemblyProtocol,
    color: Tuple[float, float, float, float] = (1.0, 1.0, 1.0, 1.0),
    tolerance: float = 1e-3,
    angularTolerance: float = 0.1,
) -> vtkRenderer:

    renderer = vtkRenderer()

    for shape, _, loc, col_ in assy:

        col = col_.toTuple() if col_ else color

        trans, rot = _loc2vtk(loc)

        data = shape.toVtkPolyData(tolerance, angularTolerance)

        # extract faces
        extr = vtkExtractCellsByType()
        extr.SetInputDataObject(data)

        extr.AddCellType(VTK_LINE)
        extr.AddCellType(VTK_VERTEX)
        extr.Update()
        data_edges = extr.GetOutput()

        # extract edges
        extr = vtkExtractCellsByType()
        extr.SetInputDataObject(data)

        extr.AddCellType(VTK_TRIANGLE)
        extr.Update()
        data_faces = extr.GetOutput()

        # remove normals from edges
        data_edges.GetPointData().RemoveArray("Normals")

        # add both to the renderer
        mapper = vtkMapper()
        mapper.AddInputDataObject(data_faces)

        actor = vtkActor()
        actor.SetMapper(mapper)
        actor.SetPosition(*trans)
        actor.SetOrientation(*rot)
        actor.GetProperty().SetColor(*col[:3])
        actor.GetProperty().SetOpacity(col[3])

        renderer.AddActor(actor)

        mapper = vtkMapper()
        mapper.AddInputDataObject(data_edges)

        actor = vtkActor()
        actor.SetMapper(mapper)
        actor.SetPosition(*trans)
        actor.SetOrientation(*rot)

        renderer.AddActor(actor)

    return renderer


def toJSON(
    assy: AssemblyProtocol,
    color: Tuple[float, float, float, float] = (1.0, 1.0, 1.0, 1.0),
    tolerance: float = 1e-3,
) -> List[Dict[str, Any]]:
    """
    Export an object to a structure suitable for converting to VTK.js JSON.
    """

    rv = []

    for shape, _, loc, col_ in assy:

        val: Any = {}

        data = toString(shape, tolerance)
        trans, rot = loc.toTuple()

        val["shape"] = data
        val["color"] = col_.toTuple() if col_ else color
        val["position"] = trans
        val["orientation"] = tuple(radians(r) for r in rot)

        rv.append(val)

    return rv


def toFusedCAF(
    assy: AssemblyProtocol, glue: bool = False, tol: Optional[float] = None,
) -> Tuple[TDF_Label, TDocStd_Document]:
    """
    Converts the assembly to a fused compound and saves that within the document
    to be exported in a way that preserves the face colors. Because of the use of
    boolean operations in this method, performance may be slow in some cases.

    :param assy: Assembly that is being converted to a fused compound for the document.
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

    # Walk the entire assembly, collecting the located shapes and colors
    shapes: List[Shape] = []
    colors = []

    for shape, _, loc, color in assy:
        shapes.append(shape.moved(loc).copy())
        colors.append(color)

    # Initialize with a dummy value for mypy
    top_level_shape = cast(TopoDS_Shape, None)

    # If the tools are empty, it means we only had a single shape and do not need to fuse
    if not shapes:
        raise Exception(f"Error: Assembly {assy.name} has no shapes.")
    elif len(shapes) == 1:
        # There is only one shape and we only need to make sure it is a Compound
        # This seems to be needed to be able to add subshapes (i.e. faces) correctly
        sh = shapes[0]
        if sh.ShapeType() != "Compound":
            top_level_shape = Compound.makeCompound((sh,)).wrapped
        elif sh.ShapeType() == "Compound":
            sh = sh.fuse(glue=glue, tol=tol)
            top_level_shape = Compound.makeCompound((sh,)).wrapped
            shapes = [sh]
    else:
        # Set the shape lists up so that the fuse operation can be performed
        args.Append(shapes[0].wrapped)

        for shape in shapes[1:]:
            tools.Append(shape.wrapped)

        # Allow the caller to configure the fuzzy and glue settings
        if tol:
            fuse_op.SetFuzzyValue(tol)
        if glue:
            fuse_op.SetGlue(BOPAlgo_GlueEnum.BOPAlgo_GlueShift)

        fuse_op.SetArguments(args)
        fuse_op.SetTools(tools)
        fuse_op.Build()

        top_level_shape = fuse_op.Shape()

    # Add the fused shape as the top level object in the document
    top_level_lbl = shape_tool.AddShape(top_level_shape, False)
    TDataStd_Name.Set_s(top_level_lbl, TCollection_ExtendedString(assy.name))

    # Walk the assembly->part->shape->face hierarchy and add subshapes for all the faces
    for color, shape in zip(colors, shapes):
        for face in shape.Faces():
            # See if the face can be treated as-is
            cur_lbl = shape_tool.AddSubShape(top_level_lbl, face.wrapped)
            if color and not cur_lbl.IsNull() and not fuse_op.IsDeleted(face.wrapped):
                color_tool.SetColor(cur_lbl, color.wrapped, XCAFDoc_ColorGen)

            # Handle any modified faces
            modded_list = fuse_op.Modified(face.wrapped)

            for mod in modded_list:
                # Add the face as a subshape and set its color to match the parent assembly component
                cur_lbl = shape_tool.AddSubShape(top_level_lbl, mod)
                if color and not cur_lbl.IsNull() and not fuse_op.IsDeleted(mod):
                    color_tool.SetColor(cur_lbl, color.wrapped, XCAFDoc_ColorGen)

            # Handle any generated faces
            gen_list = fuse_op.Generated(face.wrapped)

            for gen in gen_list:
                # Add the face as a subshape and set its color to match the parent assembly component
                cur_lbl = shape_tool.AddSubShape(top_level_lbl, gen)
                if color and not cur_lbl.IsNull():
                    color_tool.SetColor(cur_lbl, color.wrapped, XCAFDoc_ColorGen)

    return top_level_lbl, doc


def imprint(assy: AssemblyProtocol) -> Tuple[Shape, Dict[Shape, Tuple[str, ...]]]:
    """
    Imprint all the solids and construct a dictionary mapping imprinted solids to names from the input assy.
    """

    # make the id map
    id_map = {}

    for obj, name, loc, _ in assy:
        for s in obj.moved(loc).Solids():
            id_map[s] = name

    # connect topologically
    bldr = BOPAlgo_MakeConnected()
    bldr.SetRunParallel(True)
    bldr.SetUseOBB(True)

    for obj in id_map:
        bldr.AddArgument(obj.wrapped)

    bldr.Perform()
    res = Shape(bldr.Shape())

    # make the connected solid -> id map
    origins: Dict[Shape, Tuple[str, ...]] = {}

    for s in res.Solids():
        ids = tuple(id_map[Solid(el)] for el in bldr.GetOrigins(s.wrapped))
        # if GetOrigins yields nothing, solid was not modified
        origins[s] = ids if ids else (id_map[s],)

    return res, origins
