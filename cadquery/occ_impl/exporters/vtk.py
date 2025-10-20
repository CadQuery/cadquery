from vtkmodules.vtkIOXML import vtkXMLPolyDataWriter
from ..shapes import Shape
from pathlib import Path


def exportVTP(
    shape: Shape,
    fname: Path | str,
    tolerance: float = 0.1,
    angularTolerance: float = 0.1,
):
    if isinstance(fname, str):
        fname = Path(fname)

    writer = vtkXMLPolyDataWriter()
    writer.SetFileName(str(fname))
    writer.SetInputData(shape.toVtkPolyData(tolerance, angularTolerance))
    writer.Write()


def toString(
    shape: Shape, tolerance: float = 1e-3, angularTolerance: float = 0.1
) -> str:

    writer = vtkXMLPolyDataWriter()
    writer.SetWriteToOutputString(True)
    writer.SetInputData(shape.toVtkPolyData(tolerance, angularTolerance, True))
    writer.Write()

    return writer.GetOutputString()
