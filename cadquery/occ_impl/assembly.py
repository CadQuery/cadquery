from typing import (
    Union,
    Iterable,
    Iterator,
    Tuple,
    Dict,
    Optional,
    Any,
    List,
    cast,
)
from typing_extensions import Protocol
from math import degrees, radians
from dataclasses import dataclass

from OCP.TDocStd import TDocStd_Document
from OCP.TCollection import (
    TCollection_ExtendedString,
    TCollection_AsciiString,
)
from OCP.XCAFDoc import (
    XCAFDoc_DocumentTool,
    XCAFDoc_ColorType,
    XCAFDoc_ColorGen,
)
from OCP.XCAFApp import XCAFApp_Application
from OCP.TDataStd import TDataStd_Name
from OCP.TDF import TDF_Label
from OCP.TopLoc import TopLoc_Location
from OCP.BRepAlgoAPI import BRepAlgoAPI_Fuse
from OCP.TopTools import TopTools_ListOfShape
from OCP.BOPAlgo import BOPAlgo_GlueEnum, BOPAlgo_MakeConnected
from OCP.TopoDS import TopoDS_Shape
from OCP.gp import gp_EulerSequence

from vtkmodules.util.vtkConstants import VTK_LINE, VTK_VERTEX
from vtkmodules.vtkRenderingCore import (
    vtkActor,
    vtkPolyDataMapper as vtkMapper,
    vtkRenderer,
    vtkAssembly,
)
from vtkmodules.vtkFiltersExtraction import vtkExtractCellsByType
from vtkmodules.vtkCommonDataModel import VTK_TRIANGLE

from .geom import Location
from .shapes import Shape, Solid, Compound
from .exporters.vtk import toString
from ..cq import Workplane
from ..materials import Material, Color

# Default colors
DEFAULT_COLOR = Color(1.0, 1.0, 1.0, 1.0)  # White
DEFAULT_EDGE_COLOR = Color(0.0, 0.0, 0.0, 1.0)  # Black

# type definitions
AssemblyObjects = Union[Shape, Workplane, None]


@dataclass
class AssemblyElement:
    """A dataclass representing an element in an assembly iterator."""

    shape: Shape
    name: str
    location: Location
    color: Optional[Color] = None
    material: Optional[Material] = None


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
    def material(self) -> Optional[Material]:
        ...

    @property
    def obj(self) -> AssemblyObjects:
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

    def traverse(self) -> Iterable[Tuple[str, "AssemblyProtocol"]]:
        ...

    def __iter__(
        self,
        loc: Optional[Location] = None,
        name: Optional[str] = None,
        color: Optional[Color] = None,
        material: Optional[Material] = None,
    ) -> Iterator[AssemblyElement]:
        ...


def setName(l: TDF_Label, name: str, tool):
    """Set the name of a label in the document."""
    TDataStd_Name.Set_s(l, TCollection_ExtendedString(name))


def setColor(l: TDF_Label, color: Color, tool):
    """Set the color of a label in the document."""
    tool.SetColor(l, color.to_occ_rgba(), XCAFDoc_ColorType.XCAFDoc_ColorSurf)


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
    mtool = XCAFDoc_DocumentTool.MaterialTool_s(doc.Main())
    vmtool = XCAFDoc_DocumentTool.VisMaterialTool_s(doc.Main())

    # used to store labels with unique part-color-material combinations
    unique_objs: Dict[
        Tuple[Optional[Color], Optional[Material], AssemblyObjects], TDF_Label
    ] = {}
    # used to cache unique, possibly meshed, compounds; allows to avoid redundant meshing operations if same object is referenced multiple times in an assy
    compounds: Dict[AssemblyObjects, Compound] = {}

    def _toCAF(el, ancestor, color, material) -> TDF_Label:

        # create a subassy
        subassy = tool.NewShape()
        setName(subassy, el.name, tool)

        # define the current color and material
        current_color = el.color if el.color else color
        current_material: Optional[Material] = el.material if el.material else material

        # add a leaf with the actual part if needed
        if el.obj:
            # get/register unique parts referenced in the assy
            key0 = (current_color, current_material, el.obj)  # (color, material, shape)
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

                # handle materials
                if current_material:
                    # Assign color directly to the shape
                    if current_material.color:
                        ctool.SetColor(
                            lab,
                            current_material.color.to_occ_rgba(),
                            XCAFDoc_ColorType.XCAFDoc_ColorSurf,
                        )

                    # Convert material to OCCT format and add to document
                    mat, vis_mat = (
                        current_material.to_occ_material(),
                        current_material.to_occ_vis_material(),
                    )

                    # Create material label
                    mat_lab = mtool.AddMaterial(
                        mat.GetName(),
                        mat.GetDescription(),
                        mat.GetDensity(),
                        mat.GetDensName(),
                        mat.GetDensValType(),
                    )
                    mtool.SetMaterial(lab, mat_lab)

                    # Add visualization material to the document
                    vis_mat_lab = vmtool.AddMaterial(
                        vis_mat, TCollection_AsciiString(current_material.name)
                    )
                    vmtool.SetShapeMaterial(lab, vis_mat_lab)

            tool.AddComponent(subassy, lab, TopLoc_Location())

        # handle colors when *not* exporting to STEP
        if not coloredSTEP and current_color:
            setColor(subassy, current_color, ctool)

        # add children recursively
        for child in el.children:
            _toCAF(child, subassy, current_color, current_material)

        if ancestor:
            tool.AddComponent(ancestor, subassy, el.loc.wrapped)
            rv = subassy
        else:
            # update the top level location
            rv = TDF_Label()  # NB: additional label is needed to apply the location
            tool.SetLocation(subassy, assy.loc.wrapped, rv)
            setName(rv, assy.name, tool)

        return rv

    # process the whole assy recursively
    top = _toCAF(assy, None, None, None)

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
    color: Color = DEFAULT_COLOR,
    edgecolor: Color = DEFAULT_EDGE_COLOR,
    edges: bool = True,
    linewidth: float = 2,
    tolerance: float = 1e-3,
    angularTolerance: float = 0.1,
) -> vtkAssembly:
    """
    Convert an assembly to a VTK assembly with both solid faces and edges.
    
    Args:
        assy: The assembly to convert
        color: Default color for faces (white if None)
        edgecolor: Default color for edges (black if None) 
        edges: Whether to show edges
        linewidth: Width of edge lines
        tolerance: Linear tolerance for tessellation
        angularTolerance: Angular tolerance for tessellation in degrees
        
    Returns:
        A VTK assembly containing both faces and edges for each element
    """

    rv = vtkAssembly()

    for element in assy:
        trans, rot = _loc2vtk(element.location)

        data = element.shape.toVtkPolyData(tolerance, angularTolerance)

        # Extract edges (lines and vertices)
        extr = vtkExtractCellsByType()
        extr.SetInputDataObject(data)
        extr.AddCellType(VTK_LINE)
        extr.AddCellType(VTK_VERTEX)
        extr.Update()
        data_edges = extr.GetOutput()

        # Extract faces (triangles)
        extr = vtkExtractCellsByType()
        extr.SetInputDataObject(data)
        extr.AddCellType(VTK_TRIANGLE)
        extr.Update()
        data_faces = extr.GetOutput()

        # Remove normals from edges since they're not needed
        data_edges.GetPointData().RemoveArray("Normals")

        # Create actor for faces with material/color
        mapper = vtkMapper()
        mapper.AddInputDataObject(data_faces)

        actor = vtkActor()
        actor.SetMapper(mapper)
        actor.SetPosition(*trans)
        actor.SetOrientation(*rot)

        # Apply material or color
        if element.material:
            element.material.apply_to_vtk_actor(actor)
        else:
            # Apply color directly
            use_color = element.color if element.color else color
            prop = actor.GetProperty()
            prop.SetColor(*use_color.rgb())
            prop.SetOpacity(use_color.alpha)

        rv.AddPart(actor)

        if not edges:
            continue

        # Create actor for edges
        mapper = vtkMapper()
        mapper.AddInputDataObject(data_edges)

        actor = vtkActor()
        actor.SetMapper(mapper)
        actor.SetPosition(*trans)
        actor.SetOrientation(*rot)
        actor.GetProperty().SetLineWidth(linewidth)

        # Apply edge color directly
        prop = actor.GetProperty()
        prop.SetColor(*edgecolor.rgb())
        prop.SetOpacity(edgecolor.alpha)

        rv.AddPart(actor)

    return rv


def toVTK(
    assy: AssemblyProtocol,
    color: Color = DEFAULT_COLOR,
    tolerance: float = 1e-3,
    angularTolerance: float = 0.1,
    *,
    edges: bool = True,
) -> vtkRenderer:
    """
    Convert an assembly to a VTK renderer with both solid faces and edges.
    
    Args:
        assy: The assembly to convert
        color: Default color for faces (white if None)
        tolerance: Linear tolerance for tessellation
        angularTolerance: Angular tolerance for tessellation in degrees
        
    Returns:
        A VTK renderer containing both faces and edges for each element
    """

    renderer = vtkRenderer()

    for element in assy:
        trans, rot = _loc2vtk(element.location)

        data = element.shape.toVtkPolyData(tolerance, angularTolerance)

        # Extract edges (lines and vertices)
        extr = vtkExtractCellsByType()
        extr.SetInputDataObject(data)
        extr.AddCellType(VTK_LINE)
        extr.AddCellType(VTK_VERTEX)
        extr.Update()
        data_edges = extr.GetOutput()

        # Extract faces (triangles)
        extr = vtkExtractCellsByType()
        extr.SetInputDataObject(data)
        extr.AddCellType(VTK_TRIANGLE)
        extr.Update()
        data_faces = extr.GetOutput()

        # Remove normals from edges since they're not needed
        data_edges.GetPointData().RemoveArray("Normals")

        # Create actor for faces with material/color
        mapper = vtkMapper()
        mapper.AddInputDataObject(data_faces)

        actor = vtkActor()
        actor.SetMapper(mapper)
        actor.SetPosition(*trans)
        actor.SetOrientation(*rot)

        # Apply material or color
        if element.material:
            element.material.apply_to_vtk_actor(actor)
        else:
            # Apply color directly
            use_color = element.color if element.color else color
            prop = actor.GetProperty()
            prop.SetColor(*use_color.rgb())
            prop.SetOpacity(use_color.alpha)

        renderer.AddActor(actor)

        if not edges:
            continue

        # Create actor for edges
        mapper = vtkMapper()
        mapper.AddInputDataObject(data_edges)

        actor = vtkActor()
        actor.SetMapper(mapper)
        actor.SetPosition(*trans)
        actor.SetOrientation(*rot)

        renderer.AddActor(actor)

    return renderer


def toJSON(
    assy: AssemblyProtocol, color: Color = DEFAULT_COLOR, tolerance: float = 1e-3,
) -> List[Dict[str, Any]]:
    """
    Export an object to a structure suitable for converting to VTK.js JSON.
    """

    rv = []

    for element in assy:
        val: Any = {}

        data = toString(element.shape, tolerance)
        trans, rot = element.location.toTuple()

        val["shape"] = data
        val["color"] = element.color.rgba() if element.color else color.rgba()
        val["position"] = trans
        val["orientation"] = tuple(radians(r) for r in rot)

        # Add material properties if available
        if element.material:
            val["material"] = {
                "name": element.material.name,
                "description": element.material.description,
                "density": element.material.density,
            }
            if element.material.pbr:
                val["material"]["pbr"] = {
                    "base_color": element.material.pbr.base_color.rgba(),
                    "metallic": element.material.pbr.metallic,
                    "roughness": element.material.pbr.roughness,
                    "refraction_index": element.material.pbr.refraction_index,
                }

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

    for element in assy:
        shapes.append(element.shape.moved(element.location).copy())
        colors.append(element.color)

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
                color_tool.SetColor(cur_lbl, color.to_occ_rgba(), XCAFDoc_ColorGen)

            # Handle any modified faces
            modded_list = fuse_op.Modified(face.wrapped)

            for mod in modded_list:
                # Add the face as a subshape and set its color to match the parent assembly component
                cur_lbl = shape_tool.AddSubShape(top_level_lbl, mod)
                if color and not cur_lbl.IsNull() and not fuse_op.IsDeleted(mod):
                    color_tool.SetColor(cur_lbl, color.to_occ_rgba(), XCAFDoc_ColorGen)

            # Handle any generated faces
            gen_list = fuse_op.Generated(face.wrapped)

            for gen in gen_list:
                # Add the face as a subshape and set its color to match the parent assembly component
                cur_lbl = shape_tool.AddSubShape(top_level_lbl, gen)
                if color and not cur_lbl.IsNull():
                    color_tool.SetColor(cur_lbl, color.to_occ_rgba(), XCAFDoc_ColorGen)

    return top_level_lbl, doc


def imprint(assy: AssemblyProtocol) -> Tuple[Shape, Dict[Shape, Tuple[str, ...]]]:
    """
    Imprint all the solids and construct a dictionary mapping imprinted solids to names from the input assy.
    """

    # make the id map
    id_map = {}

    for element in assy:
        for s in element.shape.moved(element.location).Solids():
            id_map[s] = element.name

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
