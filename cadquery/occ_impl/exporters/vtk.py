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

    # extract edges
    extr = vtkExtractCellsByType()
    extr.SetInputDataObject(data)

    extr.AddCellType(VTK_LINE)
    extr.AddCellType(VTK_POLY_LINE)
    extr.AddCellType(VTK_VERTEX)
    extr.Update()
    data_edges = extr.GetOutput()

    # extract faces
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
) -> tuple[str, str]:

    writer_edges = vtkXMLPolyDataWriter()
    writer_edges.SetWriteToOutputString(True)

    writer_faces = vtkXMLPolyDataWriter()
    writer_faces.SetWriteToOutputString(True)

    # extract edges and faces
    data = shape.toVtkPolyData(tolerance, angularTolerance, True)
    data_edges, data_faces = extractEdgesFaces(data)

    # separate edges and faces
    writer_edges.SetInputData(data_edges)
    writer_edges.Write()
    writer_faces.SetInputData(data_faces)
    writer_faces.Write()

    return writer_edges.GetOutputString(), writer_faces.GetOutputString()
