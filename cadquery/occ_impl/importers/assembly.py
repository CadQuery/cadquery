from OCP.TCollection import TCollection_ExtendedString
from OCP.Quantity import Quantity_Color, Quantity_ColorRGBA
from OCP.TDocStd import TDocStd_Document
from OCP.IFSelect import IFSelect_RetDone
from OCP.STEPCAFControl import STEPCAFControl_Reader
from OCP.XCAFDoc import XCAFDoc_DocumentTool, XCAFDoc_ColorGen, XCAFDoc_ColorSurf
from OCP.TDF import TDF_Label, TDF_LabelSequence

import cadquery as cq
from ..assembly import AssemblyProtocol

def importStep(path: str) -> AssemblyProtocol:
    """
    Import a step file into an assembly.
    """

    # The assembly that is being built from the step file
    assy = cq.Assembly()

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

    def process_label(label, parent_location=None):
        """
        Recursive function that allows us to process the hierarchy of the assembly as represented
        in the step file.
        """

        # Handle reference labels
        if shape_tool.IsReference_s(label):
            ref_label = TDF_Label()
            shape_tool.GetReferredShape_s(label, ref_label)
            process_label(ref_label, parent_location)
            return

        # Process components
        comp_labels = TDF_LabelSequence()
        shape_tool.GetComponents_s(label, comp_labels)
        for i in range(comp_labels.Length()):
            sub_label = comp_labels.Value(i + 1)

            # The component level holds the location for its shapes
            loc = shape_tool.GetLocation_s(sub_label)
            if loc:
                location = cq.Location(loc)

                # Make sure that the location object is actually doing something interesting
                # This is done because the location may have to go through multiple levels of
                # components before the shapes are found. This allows the top-level component
                # to specify the location/rotation of the shapes.
                if location.toTuple()[0] == (0, 0, 0) and location.toTuple()[1] == (
                    0,
                    0,
                    0,
                ):
                    location = parent_location
            else:
                location = parent_location

            process_label(sub_label, location)

        # Check to see if we have an endpoint shape
        if shape_tool.IsSimpleShape_s(label):
            shape = shape_tool.GetShape_s(label)

            # Process the color for the shape, which could be of different types
            color = Quantity_Color()
            if color_tool.GetColor_s(label, XCAFDoc_ColorSurf, color):
                r = color.Red()
                g = color.Green()
                b = color.Blue()
                cq_color = cq.Color(r, g, b)
            elif color_tool.GetColor_s(label, XCAFDoc_ColorGen, color):
                r = color.Red()
                g = color.Green()
                b = color.Blue()
                cq_color = cq.Color(r, g, b)
            else:
                cq_color = cq.Color(0.5, 0.5, 0.5)

            # Handle the location if it was passed down form a parent component
            if parent_location is not None:
                assy.add(cq.Shape.cast(shape), color=cq_color, loc=parent_location)
            else:
                assy.add(cq.Shape.cast(shape), color=cq_color)

    # Grab the labels, which should hold the assembly parent
    labels = TDF_LabelSequence()
    shape_tool.GetFreeShapes(labels)

    # Make sure that we are working with an assembly
    if shape_tool.IsAssembly_s(labels.Value(1)):
        # Start the recursive processing of the assembly
        process_label(labels.Value(1))

    else:
        raise ValueError("Step file does not contain an assembly")

    return assy
