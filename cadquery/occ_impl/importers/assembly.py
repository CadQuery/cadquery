from typing import cast
from path import Path

from OCP.TopoDS import TopoDS_Shape
from OCP.TCollection import TCollection_ExtendedString
from OCP.Quantity import Quantity_ColorRGBA
from OCP.TDF import TDF_Label, TDF_LabelSequence
from OCP.IFSelect import IFSelect_RetDone
from OCP.TDocStd import TDocStd_Document
from OCP.TDataStd import TDataStd_Name, TDataStd_TreeNode
from OCP.STEPCAFControl import STEPCAFControl_Reader
from OCP.XCAFDoc import (
    XCAFDoc_ColorSurf,
    XCAFDoc_DocumentTool,
    XCAFDoc_ColorTool,
    XCAFDoc,
    XCAFDoc_ColorType,
    XCAFDoc_Material,
)
from OCP.TDocStd import TDocStd_Application
from OCP.XmlXCAFDrivers import XmlXCAFDrivers
from OCP.BinXCAFDrivers import BinXCAFDrivers
from OCP.Interface import Interface_Static
from OCP.PCDM import PCDM_ReaderStatus

from ..assembly import AssemblyProtocol, Color, Material
from ..geom import Location
from ..shapes import Shape


def _get_name(label: TDF_Label) -> str:
    """
    Helper to get the name of a given label.
    """

    rv = ""

    name_attr = TDataStd_Name()
    if label.IsAttribute(TDataStd_Name.GetID_s()):
        label.FindAttribute(TDataStd_Name.GetID_s(), name_attr)
        rv = str(name_attr.Get().ToExtString())

    return rv


def _get_material(label: TDF_Label) -> Material:
    """
    Helper to get the material for a given label.
    """

    rv = None

    material_ref_guid = XCAFDoc.MaterialRefGUID_s()

    if label.IsAttribute(material_ref_guid):
        attr = TDataStd_TreeNode()
        label.FindAttribute(material_ref_guid, attr)
        material_label = attr.Father().Label()

        material_attr = XCAFDoc_Material()

        if material_label.FindAttribute(XCAFDoc_Material.GetID_s(), material_attr):
            name = material_attr.GetName().ToCString()
            description = material_attr.GetDescription().ToCString()
            density = material_attr.GetDensity()
            density_unit = material_attr.GetDensValType().ToCString()

            rv = Material(
                name=name,
                description=description,
                density=density,
                densityUnit=density_unit,
            )

    return rv


def _get_ref_color(label: TDF_Label) -> Color | None:
    """
    Helper to get the instance color of a given label.
    """

    color_ref_guid = XCAFDoc.ColorRefGUID_s(XCAFDoc_ColorType.XCAFDoc_ColorSurf)

    color_ref_guid_generic = XCAFDoc.ColorRefGUID_s(XCAFDoc_ColorType.XCAFDoc_ColorGen)

    attr = TDataStd_TreeNode()

    if label.IsAttribute(color_ref_guid):
        label.FindAttribute(color_ref_guid, attr)
        color_label = attr.Father().Label()
        color = Quantity_ColorRGBA()

        XCAFDoc_ColorTool.GetColor_s(color_label, color)

        rgb = color.GetRGB()
        rv = Color(rgb.Red(), rgb.Green(), rgb.Blue(), color.Alpha(), False)

    elif label.IsAttribute(color_ref_guid_generic):
        label.FindAttribute(color_ref_guid_generic, attr)
        color_label = attr.Father().Label()
        color = Quantity_ColorRGBA()

        XCAFDoc_ColorTool.GetColor_s(color_label, color)

        rgb = color.GetRGB()
        rv = Color(rgb.Red(), rgb.Green(), rgb.Blue(), color.Alpha(), False)

    else:
        rv = None

    return rv


def _get_shape_color(s: TopoDS_Shape, color_tool: XCAFDoc_ColorTool) -> Color | None:
    """
    Helper to get the shape color of a given shape.
    """

    color = Quantity_ColorRGBA()

    # Extract the color, if present on the shape
    if color_tool.GetColor(s, XCAFDoc_ColorSurf, color):
        rgb = color.GetRGB()
        rv = Color(rgb.Red(), rgb.Green(), rgb.Blue(), color.Alpha(), False)
    else:
        rv = None

    return rv


def importStep(assy: AssemblyProtocol, path: str):
    """
    Import a step file into an assembly.

    :param assy: An Assembly object that will be packed with the contents of the STEP file.
    :param path: Path and filename to the STEP file to read.

    :return: None
    """

    # Create and configure a STEP reader
    step_reader = STEPCAFControl_Reader()
    step_reader.SetColorMode(True)
    step_reader.SetNameMode(True)
    step_reader.SetLayerMode(True)
    step_reader.SetSHUOMode(True)

    Interface_Static.SetIVal_s("read.stepcaf.subshapes.name", 1)

    # Read the STEP file
    status = step_reader.ReadFile(path)
    if status != IFSelect_RetDone:
        raise ValueError(f"Error reading STEP file: {path}")

    # Document that the step file will be read into
    doc = TDocStd_Document(TCollection_ExtendedString("XmXCAF"))

    # Transfer the contents of the STEP file to the document
    step_reader.Transfer(doc)

    _importDoc(doc, assy)


def importXbf(assy: AssemblyProtocol, path: str):
    """
    Import an xbf file into an assembly.

    :param assy: An Assembly object that will be packed with the contents of the STEP file.
    :param path: Path and filename to the xbf file to read.

    :return: None
    """

    app = TDocStd_Application()
    BinXCAFDrivers.DefineFormat_s(app)

    dirname, fname = Path(path).absolute().splitpath()
    doc = cast(
        TDocStd_Document,
        app.Retrieve(
            TCollection_ExtendedString(dirname), TCollection_ExtendedString(fname)
        ),
    )

    status = app.GetRetrieveStatus()
    assert (
        status == PCDM_ReaderStatus.PCDM_RS_OK
    ), f"Opening of file {path} failed: {status}"

    _importDoc(doc, assy)


def importXml(assy: AssemblyProtocol, path: str):
    """
    Import an xcaf xml file into an assembly.

    :param assy: An Assembly object that will be packed with the contents of the STEP file.
    :param path: Path and filename to the xml file to read.

    :return: None
    """

    app = TDocStd_Application()
    XmlXCAFDrivers.DefineFormat_s(app)

    dirname, fname = Path(path).absolute().splitpath()
    doc = cast(
        TDocStd_Document,
        app.Retrieve(
            TCollection_ExtendedString(dirname), TCollection_ExtendedString(fname)
        ),
    )

    status = app.GetRetrieveStatus()
    assert (
        status == PCDM_ReaderStatus.PCDM_RS_OK
    ), f"Opening of file {path} failed: {status}"

    _importDoc(doc, assy)


def _importDoc(doc: TDocStd_Document, assy: AssemblyProtocol):
    def _process_label(lbl: TDF_Label, parent: AssemblyProtocol):
        """
        Recursive method to process the assembly in a top-down manner.
        """

        # Look for components
        comp_labels = TDF_LabelSequence()
        shape_tool.GetComponents_s(lbl, comp_labels)

        for i in range(comp_labels.Length()):
            comp_label = comp_labels.Value(i + 1)
            comp_name = _get_name(comp_label)

            # Get the location of the component label
            loc = shape_tool.GetLocation_s(comp_label)
            cq_loc = Location(loc) if loc else Location()

            if shape_tool.IsReference_s(comp_label):
                ref_label = TDF_Label()
                shape_tool.GetReferredShape_s(comp_label, ref_label)

                # get (if it exists the color of the comp label)
                color = _get_ref_color(comp_label)
                material = _get_material(comp_label)

                if shape_tool.IsAssembly_s(ref_label):
                    # Find the name of this referenced part
                    ref_name = _get_name(ref_label)

                    sub_assy = assy.__class__(name=ref_name)

                    # Recursively process subassemblies
                    _ = _process_label(ref_label, sub_assy)

                    # Add the subassy
                    parent.add(sub_assy, name=ref_name, loc=cq_loc, color=color)

                elif shape_tool.IsSimpleShape_s(ref_label):
                    # Find the name of this referenced part
                    ref_name = _get_name(comp_label)

                    # A single shape needs to be added to the assembly
                    final_shape = shape_tool.GetShape_s(ref_label)
                    cq_shape = Shape.cast(final_shape)

                    # If the instance has no color, try to find the referenced shape color
                    if color is None:
                        color = _get_shape_color(final_shape, color_tool)

                    if material is None:
                        material = _get_material(ref_label)

                    # this if/else is needed to handle different structures of STEP files
                    # "*"/"*_part" based naming is the default structure produced by CQ
                    # with an object and child nodes at the same time
                    if ref_name.endswith("_part"):
                        parent.obj = cq_shape
                        parent.loc = cq_loc
                        parent.color = color

                        # change the current assy to handle subshape data
                        current = parent
                    else:
                        tmp = assy.__class__(
                            cq_shape, loc=cq_loc, name=comp_name, color=color, material=material
                        )
                        parent.add(tmp)

                        # change the current assy to handle subshape data
                        current = cast(AssemblyProtocol, parent[comp_name])

                    # iterate over subshape and handle names, layers and colors
                    subshape_labels = TDF_LabelSequence()
                    shape_tool.GetSubShapes_s(ref_label, subshape_labels)

                    for child_label in subshape_labels:

                        # Save the shape so that we can add it to the subshape data
                        cur_shape: TopoDS_Shape = shape_tool.GetShape_s(child_label)

                        # Handle subshape name
                        child_name = _get_name(child_label)

                        if child_name:
                            current.addSubshape(
                                Shape.cast(cur_shape), name=child_name,
                            )

                        # Find the layer name, if there is one set for this shape
                        layers = TDF_LabelSequence()
                        layer_tool.GetLayers(child_label, layers)

                        for lbl in layers:
                            # Extract the layer name for the shape here
                            layer_name = _get_name(lbl)

                            # Add the layer as a subshape entry on the assembly
                            current.addSubshape(Shape.cast(cur_shape), layer=layer_name)

                        # Find the subshape color, if there is one set for this shape

                        # try the instance first
                        color = _get_ref_color(child_label)
                        material = _get_material(child_label)

                        if color:
                            # Save the color info via the assembly subshape mechanism
                            current.addSubshape(Shape.cast(cur_shape), color=color)

        return parent

    # Shape and color tools for extracting XCAF data
    shape_tool = XCAFDoc_DocumentTool.ShapeTool_s(doc.Main())
    color_tool = XCAFDoc_DocumentTool.ColorTool_s(doc.Main())
    layer_tool = XCAFDoc_DocumentTool.LayerTool_s(doc.Main())

    # Collect all the labels representing shapes in the document
    labels = TDF_LabelSequence()
    shape_tool.GetFreeShapes(labels)

    # Get the top-level label, which should represent an assembly
    top_level_label = labels.Value(1)

    cq_color = _get_ref_color(top_level_label)

    # Get the reference if needed
    if shape_tool.IsReference_s(top_level_label):
        tmp = TDF_Label()
        shape_tool.GetReferredShape_s(top_level_label, tmp)
        top_level_label = tmp

    # Make sure there is a top-level assembly
    if shape_tool.IsTopLevel(top_level_label) and shape_tool.IsAssembly_s(
        top_level_label
    ):
        # Set the name of the top-level assembly to match the top-level label
        name_attr = TDataStd_Name()
        top_level_label.FindAttribute(TDataStd_Name.GetID_s(), name_attr)

        # Manipulation of .objects is needed to maintain consistency
        assy.objects.pop(assy.name)
        assy.name = str(name_attr.Get().ToExtString())
        assy.objects[assy.name] = assy

        if cq_color:
            assy.color = cq_color

        # Get the location of the top-level component
        loc = shape_tool.GetLocation_s(top_level_label)
        cq_loc = Location(loc)

        if not cq_loc.wrapped.IsIdentity() and cq_loc.toTuple() == (
            (0, 0, 0),
            (0, 0, 0),
        ):
            assy.loc = Location()
        else:
            assy.loc = cq_loc

        # Start the recursive processing of labels
        imported_assy = assy.__class__()
        _process_label(top_level_label, imported_assy)

        # Handle a possible extra top-level node. This is done because cq.Assembly.export
        # adds an extra top-level node which will cause a cascade of
        # extras on successive round-trips. exportStepMeta does not add the extra top-level
        # node and so does not exhibit this behavior.
        if assy.name in imported_assy:
            imported_assy = cast(AssemblyProtocol, imported_assy[assy.name])
            # comp_labels = TDF_LabelSequence()
            # shape_tool.GetComponents_s(top_level_label, comp_labels)
            # comp_label = comp_labels.Value(1)
            # breakpoint()
            assy.loc = imported_assy.loc

        # Copy all of the children over to the main assembly object
        for child in imported_assy.children:
            assy.add(child, name=child.name, color=child.color, loc=child.loc)

    else:
        raise ValueError("Step file does not contain an assembly")
