from OCP.TCollection import TCollection_ExtendedString
from OCP.Quantity import Quantity_Color, Quantity_ColorRGBA
from OCP.TDocStd import TDocStd_Document
from OCP.IFSelect import IFSelect_RetDone
from OCP.STEPCAFControl import STEPCAFControl_Reader
from OCP.XCAFDoc import (
    XCAFDoc_DocumentTool,
    XCAFDoc_ColorGen,
    XCAFDoc_ColorSurf,
    XCAFDoc_GraphNode,
)
from OCP.TDF import TDF_Label, TDF_LabelSequence, TDF_AttributeIterator, TDF_DataSet
from OCP.TDataStd import TDataStd_Name

import cadquery as cq
from ..assembly import AssemblyProtocol


def importStep(assy: AssemblyProtocol, path: str):
    """
    Import a step file into an assembly.

    :param assy: An Assembly object that will be packed with the contents of the STEP file.
    :param path: Path and filename to the STEP file to read.

    :return: None
    """

    # Document that the step file will be read into
    doc = TDocStd_Document(TCollection_ExtendedString("XmlOcaf"))

    # Create and configure a STEP reader
    step_reader = STEPCAFControl_Reader()
    step_reader.SetColorMode(True)
    step_reader.SetNameMode(True)
    step_reader.SetLayerMode(True)
    step_reader.SetSHUOMode(True)

    # Read the STEP file
    status = step_reader.ReadFile(path)
    if status != IFSelect_RetDone:
        raise ValueError(f"Error reading STEP file: {path}")

    # Transfer the contents of the STEP file to the document
    step_reader.Transfer(doc)

    # Shape and color tools for extracting XCAF data
    shape_tool = XCAFDoc_DocumentTool.ShapeTool_s(doc.Main())
    color_tool = XCAFDoc_DocumentTool.ColorTool_s(doc.Main())
    layer_tool = XCAFDoc_DocumentTool.LayerTool_s(doc.Main())

    def _process_simple_shape(label, parent_location=None, parent_name=None):
        shape = shape_tool.GetShape_s(label)

        # Tracks the RGB color value and whether or not it was found
        cq_color = None

        # Load the name of the part in the assembly, if it is present
        name = None
        if parent_name is not None and parent_name != assy.name:
            name = parent_name
        else:
            name_attr = TDataStd_Name()
            label.FindAttribute(TDataStd_Name.GetID_s(), name_attr)
            name = str(name_attr.Get().ToExtString())

        # Process the color for the shape, which could be of different types
        color = Quantity_Color()
        cq_color = cq.Color(0.50, 0.50, 0.50)
        if color_tool.GetColor_s(label, XCAFDoc_ColorSurf, color):
            r = color.Red()
            g = color.Green()
            b = color.Blue()
            cq_color = cq.Color(r, g, b)

        # Handle the location if it was passed down form a parent component
        if parent_location is not None:
            assy.add(
                cq.Shape.cast(shape),
                name=name,
                color=cq_color,
                loc=cq.Location(parent_location),
            )
        else:
            assy.add(cq.Shape.cast(shape), name=name, color=cq_color)

        # Check all the attributes of all the children to find the subshapes and any names
        for j in range(label.NbChildren()):
            child_label = label.FindChild(j + 1)
            attr_iterator = TDF_AttributeIterator(child_label)
            while attr_iterator.More():
                current_attr = attr_iterator.Value()

                # Get the type name of the attribute so that we can decide how to handle it
                if current_attr.DynamicType().Name() == "TNaming_NamedShape":
                    # Save the shape so that we can add it to the subshape data
                    cur_shape = current_attr.Get()

                    # Find the layer name, if there is one set for this shape
                    layers = TDF_LabelSequence()
                    layer_tool.GetLayers(child_label, layers)
                    for i in range(1, layers.Length() + 1):
                        lbl = layers.Value(i)
                        name_attr = TDataStd_Name()
                        lbl.FindAttribute(TDataStd_Name.GetID_s(), name_attr)

                        # Extract the layer name for the shape here
                        layer_name = name_attr.Get().ToExtString()

                        # Add the layer as a subshape entry on the assembly
                        assy.addSubshape(cur_shape, layer=layer_name)

                    # Find the subshape color, if there is one set for this shape
                    color = Quantity_ColorRGBA()
                    # Extract the color, if present on the shape
                    if color_tool.GetColor(cur_shape, XCAFDoc_ColorSurf, color):
                        rgb = color.GetRGB()
                        cq_color = cq.Color(
                            rgb.Red(), rgb.Green(), rgb.Blue(), color.Alpha()
                        )

                        # Save the color info via the assembly subshape mechanism
                        assy.addSubshape(cur_shape, color=cq_color)
                elif current_attr.DynamicType().Name() == "XCAFDoc_GraphNode":
                    # Step up one level to try to get the name from the parent
                    lbl = current_attr.GetFather(1).Label()

                    # Step through and search for the name attribute
                    it = TDF_AttributeIterator(lbl)
                    while it.More():
                        new_attr = it.Value()
                        if new_attr.DynamicType().Name() == "TDataStd_Name":
                            # Save this as the name of the subshape
                            assy.addSubshape(
                                cur_shape, name=new_attr.Get().ToExtString(),
                            )
                        it.Next()

                attr_iterator.Next()

    def process_label(label, parent_location=None, parent_name=None):
        """
        Recursive function that allows us to process the hierarchy of the assembly as represented
        in the step file.
        """

        # Handle reference labels
        if shape_tool.IsReference_s(label):
            ref_label = TDF_Label()
            shape_tool.GetReferredShape_s(label, ref_label)
            process_label(ref_label, parent_location, parent_name)

            return

        # See if this is an assembly (or sub-assembly)
        if shape_tool.IsAssembly_s(label):
            name_attr = TDataStd_Name()
            label.FindAttribute(TDataStd_Name.GetID_s(), name_attr)
            name = name_attr.Get().ToExtString()

            # Recursively process its components (children)
            comp_labels = TDF_LabelSequence()
            shape_tool.GetComponents_s(label, comp_labels)

            for i in range(comp_labels.Length()):
                sub_label = comp_labels.Value(i + 1)
                # Get the location of the sub-label, if it exists
                loc = shape_tool.GetLocation_s(sub_label)

                # Pass down the location or other context as needed
                # Add the parent location if it exists
                if parent_location is not None:
                    loc = parent_location * loc

                process_label(sub_label, loc, name)

            return

        # Check to see if we have an endpoint shape and process it
        if shape_tool.IsSimpleShape_s(label):
            _process_simple_shape(label, parent_location, parent_name)

    # Get the shapes in the assembly
    labels = TDF_LabelSequence()
    shape_tool.GetFreeShapes(labels)

    # Use the first label to pull the top-level assembly information
    name_attr = TDataStd_Name()
    labels.Value(1).FindAttribute(TDataStd_Name.GetID_s(), name_attr)
    assy.name = str(name_attr.Get().ToExtString())

    # Make sure there is a top-level assembly
    if shape_tool.IsTopLevel(labels.Value(1)) and shape_tool.IsAssembly_s(
        labels.Value(1)
    ):
        process_label(labels.Value(1))
    else:
        raise ValueError("Step file does not contain an assembly")
