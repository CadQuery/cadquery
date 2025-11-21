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

from OCP import GCPnts, BRepAdaptor
from OCP.TDocStd import TDocStd_Document
from OCP.TCollection import TCollection_ExtendedString
from OCP.XCAFDoc import (
    XCAFDoc_DocumentTool,
    XCAFDoc_ColorType,
    XCAFDoc_ColorGen,
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
from OCP.BRep import BRep_Tool
from OCP.BRepAlgoAPI import BRepAlgoAPI_Fuse
from OCP.BRepMesh import BRepMesh_IncrementalMesh
from OCP.TopTools import TopTools_ListOfShape
from OCP.BOPAlgo import BOPAlgo_GlueEnum, BOPAlgo_MakeConnected
from OCP.TopoDS import TopoDS_Shape
from OCP.gp import gp_EulerSequence
from OCP.TopAbs import TopAbs_REVERSED

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
    def _subshape_names(self) -> Dict[Shape, str]:
        ...

    @property
    def _subshape_colors(self) -> Dict[Shape, Color]:
        ...

    @property
    def _subshape_layers(self) -> Dict[Shape, str]:
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
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Self:
        ...

    def add(
        self,
        obj: Union[Self, AssemblyObjects],
        loc: Optional[Location] = None,
        name: Optional[str] = None,
        color: Optional[Color] = None,
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

    def __getitem__(self, name: str) -> Self:
        ...

    def __contains__(self, name: str) -> bool:
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


def toMesh(
    assy: AssemblyProtocol,
    do_imprint: bool = True,
    tolerance: float = 0.1,
    angular_tolerance: float = 0.1,
    scale_factor: float = 1.0,
    include_brep_edges: bool = False,
    include_brep_vertices: bool = False,
):
    """
        Converts an assembly to a custom mesh format defined by the CadQuery team.

        :param do_imprint: Whether or not the assembly should be imprinted
        :param tolerance: Tessellation tolerance for mesh generation
        :param angular_tolerance: Angular tolerance for tessellation
        :param include_brep_edges: Whether to include BRep edge segments
        :param include_brep_vertices: Whether to include BRep vertices
        """

    def _is_interior_face(face, solid, tolerance=0.01):
        """
            Determine if a face is interior to a solid (like a cavity wall).

            This is more robust than just checking face orientation, as it considers
            the geometric relationship between the face and the solid.
            """
        # Get geometric surface and parameter bounds
        surf = BRep_Tool.Surface_s(face.wrapped)
        u_min, u_max, v_min, v_max = face._uvBounds()

        # # Take center point in UV space on the face
        u = (u_min + u_max) * 0.5
        v = (v_min + v_max) * 0.5
        face_pnt = surf.Value(u, v)

        # Determine if the face is most likely inside the solid
        is_inside = solid.isInside((face_pnt.X(), face_pnt.Y(), face_pnt.Z()))

        # Determine if the normal of the face points generally towards to the center of the solid
        is_pointing_inward = False
        face_normal = face.normalAt((face_pnt.X(), face_pnt.Y(), face_pnt.Z()))
        solid_center = solid.Center()

        to_center = gp_Vec(
            face_pnt, gp_Pnt(solid_center.x, solid_center.y, solid_center.z)
        )

        # Dot product: negative = toward, positive = away
        dot = face_normal.dot(cq.Vector(to_center.Normalized()))

        if dot < 0:
            is_pointing_inward = False
        else:
            is_pointing_inward = True

        # If the face seems to be inside the solid and its normal points inwards, it should be an internal face
        is_internal_face = False
        if is_inside and is_pointing_inward:
            is_internal_face = True

        return is_internal_face

    # To keep track of the vertices and triangles in the mesh
    vertices: list[tuple[float, float, float]] = []
    vertex_map: dict[tuple[float, float, float], int] = {}
    solids: List[Solid] = []
    solid_face_triangle = {}
    imprinted_assembly = None
    imprinted_solids_with_orginal_ids = None
    solid_colors = []
    solid_locs = []

    # Imprinted assemblies end up being compounds, whereas you have to step through each of the
    # parts in an assembly and extract the solids.
    if do_imprint:
        # Imprint the assembly and process it as a compound
        (imprinted_assembly, imprinted_solids_with_orginal_ids,) = imprint(assy)

        # Extract the solids from the imprinted assembly because we should not mesh the compound
        for solid in imprinted_assembly.Solids():
            solids.append(solid)

        # Keep track of the colors and location of each of the solids
        solid_colors.append((0.5, 0.5, 0.5, 1.0))
        solid_locs.append(Location())
    else:
        # Step through every child in the assembly and save their solids
        for child in assy.children:
            # Make sure we end up with a base shape
            obj = child.obj

            if isinstance(obj, Workplane):
                val = obj.val()
                if isinstance(val, Solid):
                    solids.append(val)
            elif isinstance(obj, Solid):
                solids.append(obj)
            else:
                continue

            # Use the color set for the assembly component, or use a default color
            if child.color:
                solid_colors.append(child.color.toTuple())
            else:
                solid_colors.append((0.5, 0.5, 0.5, 1.0))

            # Keep track of the location of each of the solids
            solid_locs.append(child.loc)

    # Solid and face IDs need to be unique unless they are a shared face
    solid_idx = 1  # We start at 1 to mimic gmsh
    face_idx = 1  # We start at id of 1 to mimic gmsh

    # Step through all of the collected solids and their respective faces to get the vertices
    for solid in solids:
        # Reset this each time so that we get the correct number of faces per solid
        face_triangles = {}

        # Order the faces in order of area, largest first
        sorted_faces = []
        face_areas = []
        for face in solid.Faces():
            area = face.Area()
            sorted_faces.append((face, area))
            face_areas.append(area)

        # Sort by area (largest first)
        sorted_faces.sort(key=lambda x: x[1], reverse=False)

        # Extract just the sorted faces if you need them separately
        sorted_face_list = [face_info[0] for face_info in sorted_faces]

        # Walk through all the faces
        for face in sorted_face_list:
            # Figure out if the face has a reversed orientation so we can handle the triangles accordingly
            is_reversed = False
            if face.wrapped.Orientation() == TopAbs_REVERSED:
                is_reversed = True

            # Location information of the face to place the vertices and edges correctly
            loc = TopLoc_Location()

            # Perform the tessellation
            BRepMesh_IncrementalMesh(face.wrapped, tolerance, False, angular_tolerance)
            face_mesh = BRep_Tool.Triangulation_s(face.wrapped, loc)

            # If this is not an imprinted assembly, override the location of the triangulation
            if not do_imprint:
                loc = solid_locs[solid_idx - 1].wrapped

            # Save the transformation so that we can place vertices in the correct locations later
            Trsf = loc.Transformation()

            # Pre-process all vertices from the face mesh for better performance
            face_vertices = {}  # Map from face mesh node index to global vertex index
            for node_idx in range(1, face_mesh.NbNodes() + 1):
                node = face_mesh.Node(node_idx)
                v_trsf = node.Transformed(Trsf)
                vertex_coords = (
                    v_trsf.X() * scale_factor,
                    v_trsf.Y() * scale_factor,
                    v_trsf.Z() * scale_factor,
                )

                # Use dictionary for O(1) lookup instead of O(n) list operations
                if vertex_coords in vertex_map:
                    face_vertices[node_idx] = vertex_map[vertex_coords]
                else:
                    global_vertex_idx = len(vertices)
                    vertices.append(vertex_coords)
                    vertex_map[vertex_coords] = global_vertex_idx
                    face_vertices[node_idx] = global_vertex_idx

            # Step through the triangles of the face
            cur_triangles = []
            for i in range(1, face_mesh.NbTriangles() + 1):
                # Get the current triangle and its index vertices
                cur_tri = face_mesh.Triangle(i)
                idx_1, idx_2, idx_3 = cur_tri.Get()

                # Look up pre-processed vertex indices - O(1) operation
                if is_reversed:
                    triangle_vertex_indices = [
                        face_vertices[idx_1],
                        face_vertices[idx_3],
                        face_vertices[idx_2],
                    ]
                else:
                    triangle_vertex_indices = [
                        face_vertices[idx_1],
                        face_vertices[idx_2],
                        face_vertices[idx_3],
                    ]

                cur_triangles.append(triangle_vertex_indices)

            # Save this triangle for the current face
            face_triangles[face_idx] = cur_triangles

            # Move to the next face
            face_idx += 1

        solid_face_triangle[solid_idx] = face_triangles

        # Move to the next solid
        solid_idx += 1

    return {
        "vertices": vertices,
        "solid_face_triangle_vertex_map": solid_face_triangle,
        "solid_colors": solid_colors,
        "imprinted_assembly": imprinted_assembly,
        "imprinted_solids_with_orginal_ids": imprinted_solids_with_orginal_ids,
    }
