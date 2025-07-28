from OCP.TCollection import TCollection_ExtendedString
from OCP.Quantity import Quantity_ColorRGBA
from OCP.TDF import TDF_Label, TDF_LabelSequence, TDF_AttributeIterator
from OCP.IFSelect import IFSelect_RetDone
from OCP.TDocStd import TDocStd_Document
from OCP.TDataStd import TDataStd_Name
from OCP.STEPCAFControl import STEPCAFControl_Reader
from OCP.XCAFDoc import XCAFDoc_ColorSurf
from OCP.XCAFDoc import XCAFDoc_DocumentTool

import cadquery as cq
from ..assembly import AssemblyProtocol


def importStep(assy: AssemblyProtocol, path: str):
    """
    Import a step file into an assembly.

    :param assy: An Assembly object that will be packed with the contents of the STEP file.
    :param path: Path and filename to the STEP file to read.

    :return: None
    """

    def _process_label(lbl: TDF_Label):
        """
        Recursive method to process the assembly in a top-down manner.
        """
        # If we have an assembly, extract all of the information out of it that we can
        if shape_tool.IsAssembly_s(lbl):
            # Instantiate the new assembly
            new_assy = cq.Assembly()

            # Look for components
            comp_labels = TDF_LabelSequence()
            shape_tool.GetComponents_s(lbl, comp_labels)

            for i in range(comp_labels.Length()):
                comp_label = comp_labels.Value(i + 1)

                # Get the location of the component label
                loc = shape_tool.GetLocation_s(comp_label)
                cq_loc = cq.Location(loc) if loc else None

                if shape_tool.IsReference_s(comp_label):
                    ref_label = TDF_Label()
                    shape_tool.GetReferredShape_s(comp_label, ref_label)

                    # Find the name of this referenced part
                    ref_name_attr = TDataStd_Name()
                    if ref_label.FindAttribute(TDataStd_Name.GetID_s(), ref_name_attr):
                        ref_name = str(ref_name_attr.Get().ToExtString())

                    if shape_tool.IsAssembly_s(ref_label):
                        # Recursively process subassemblies
                        sub_assy = _process_label(ref_label)

                        # Add the appropriate attributes to the subassembly
                        if sub_assy:
                            if cq_loc:
                                new_assy.add(sub_assy, name=f"{ref_name}", loc=cq_loc)
                            else:
                                new_assy.add(sub_assy, name=f"{ref_name}")
                    elif shape_tool.IsSimpleShape_s(ref_label):
                        # A single shape needs to be added to the assembly
                        final_shape = shape_tool.GetShape_s(ref_label)
                        cq_shape = cq.Shape.cast(final_shape)

                        # Find the subshape color, if there is one set for this shape
                        color = Quantity_ColorRGBA()
                        # Extract the color, if present on the shape
                        if color_tool.GetColor(final_shape, XCAFDoc_ColorSurf, color):
                            rgb = color.GetRGB()
                            cq_color = cq.Color(
                                rgb.Red(), rgb.Green(), rgb.Blue(), color.Alpha()
                            )
                        else:
                            cq_color = None

                        if cq_loc:
                            new_assy.add(
                                cq_shape, name=f"{ref_name}", loc=cq_loc, color=cq_color
                            )
                        else:
                            new_assy.add(cq_shape, name=f"{ref_name}", color=cq_color)

                        # Search for subshape names, layers and colors
                        for j in range(ref_label.NbChildren()):
                            child_label = ref_label.FindChild(j + 1)

                            # Iterate through all the attributes looking for subshapes
                            attr_iterator = TDF_AttributeIterator(child_label)
                            while attr_iterator.More():
                                current_attr = attr_iterator.Value()

                                # TNaming_NamedShape is used to store and manage references to
                                # topological shapes, and its attributes can be accessed directly.
                                # XCAFDoc_GraphNode contains a graph of labels, and so we must
                                # follow the branch back to a father.
                                if (
                                    current_attr.DynamicType().Name()
                                    == "XCAFDoc_GraphNode"
                                ):
                                    # Step up one level to try to get the name from the parent
                                    lbl = current_attr.GetFather(1).Label()

                                    # Step through and search for the name attribute
                                    it = TDF_AttributeIterator(lbl)
                                    while it.More():
                                        new_attr = it.Value()
                                        if (
                                            new_attr.DynamicType().Name()
                                            == "TDataStd_Name"
                                        ):
                                            # Save this as the name of the subshape
                                            assy.addSubshape(
                                                cur_shape,
                                                name=new_attr.Get().ToExtString(),
                                            )
                                            break
                                        it.Next()
                                elif (
                                    current_attr.DynamicType().Name()
                                    == "TNaming_NamedShape"
                                ):
                                    # Save the shape so that we can add it to the subshape data
                                    cur_shape = current_attr.Get()

                                    # Find the layer name, if there is one set for this shape
                                    layers = TDF_LabelSequence()
                                    layer_tool.GetLayers(child_label, layers)
                                    for i in range(1, layers.Length() + 1):
                                        lbl = layers.Value(i)
                                        name_attr = TDataStd_Name()
                                        lbl.FindAttribute(
                                            TDataStd_Name.GetID_s(), name_attr
                                        )

                                        # Extract the layer name for the shape here
                                        layer_name = name_attr.Get().ToExtString()

                                        # Add the layer as a subshape entry on the assembly
                                        assy.addSubshape(cur_shape, layer=layer_name)

                                    # Find the subshape color, if there is one set for this shape
                                    color = Quantity_ColorRGBA()
                                    # Extract the color, if present on the shape
                                    if color_tool.GetColor(
                                        cur_shape, XCAFDoc_ColorSurf, color
                                    ):
                                        rgb = color.GetRGB()
                                        cq_color = cq.Color(
                                            rgb.Red(),
                                            rgb.Green(),
                                            rgb.Blue(),
                                            color.Alpha(),
                                        )

                                        # Save the color info via the assembly subshape mechanism
                                        assy.addSubshape(cur_shape, color=cq_color)

                                attr_iterator.Next()

            return new_assy
        elif shape_tool.IsSimpleShape_s(lbl):
            shape = shape_tool.GetShape_s(lbl)
            return cq.Shape.cast(shape)
        else:
            return None

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

    # Collect all the labels representing shapes in the document
    labels = TDF_LabelSequence()
    shape_tool.GetFreeShapes(labels)
    if labels.Length() == 0:
        raise ValueError("No assembly found in STEP file")

    # Get the top-level label, which should represent an assembly
    top_level_label = labels.Value(1)

    # Make sure there is a top-level assembly
    if shape_tool.IsTopLevel(top_level_label) and shape_tool.IsAssembly_s(
        top_level_label
    ):
        # Set the name of the top-level assembly to match the top-level label
        name_attr = TDataStd_Name()
        top_level_label.FindAttribute(TDataStd_Name.GetID_s(), name_attr)
        assy.name = str(name_attr.Get().ToExtString())

        # Start the recursive processing of labels
        whole_assy = _process_label(top_level_label)

        if whole_assy and hasattr(whole_assy, "children"):
            # Check to see if there is an extra top-level node. This is done because
            # cq.Assembly.export adds an extra top-level node which will cause a cascade of
            # extras on successive round-trips. exportStepMeta does not add the extra top-level
            # node and so does not exhibit this behavior.
            if assy.name == whole_assy.children[0].name:
                whole_assy = whole_assy.children[0]

            # Copy all of the children over to the main assembly object
            for child in whole_assy.children:
                assy.add(child, name=child.name, color=child.color, loc=child.loc)
        elif whole_assy:
            assy.add(whole_assy)
    else:
        raise ValueError("Step file does not contain an assembly")
