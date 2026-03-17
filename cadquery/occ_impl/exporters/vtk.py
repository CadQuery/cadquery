from vtkmodules.vtkIOXML import vtkXMLPolyDataWriter
from vtkmodules.vtkFiltersCore import vtkAppendPolyData
from vtkmodules.vtkCommonDataModel import vtkPolyData
from vtkmodules.vtkFiltersExtraction import vtkExtractCellsByType

from vtkmodules.vtkCommonDataModel import (
    VTK_TRIANGLE,
    VTK_LINE,
    VTK_VERTEX,
    VTK_POLY_LINE,
)

from ..shapes import Shape

def extractEdgesFaces(data: vtkPolyData) -> tuple[vtkPolyData, vtkPolyData]:
    """Helper for edges and faces extraction"""

    # extract faces
    extr = vtkExtractCellsByType()
    extr.SetInputDataObject(data)

    extr.AddCellType(VTK_LINE)
    extr.AddCellType(VTK_POLY_LINE)
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

    return data_edges, data_faces


def exportVTP(
    shape: Shape, fname: str, tolerance: float = 0.1, angularTolerance: float = 0.1
):

    writer = vtkXMLPolyDataWriter()
    writer.SetFileName(fname)
    writer.SetInputData(shape.toVtkPolyData(tolerance, angularTolerance))
    writer.Write()


def toString(
    shape: Shape, tolerance: float = 1e-3, angularTolerance: float = 0.1
) -> str:

    writer = vtkXMLPolyDataWriter()
    writer.SetWriteToOutputString(True)

    # extract edges and faces
    data = shape.toVtkPolyData(tolerance, angularTolerance, True)
    data_edges, data_faces = extractEdgesFaces(data)

    ap = vtkAppendPolyData()
    ap.AddInputData(data_edges)
    ap.AddInputData(data_faces)

    data_final = ap.GetOutput()

    # combine again
    writer.SetInputData(data_final)
    writer.Write()

    return writer.GetOutputString()
