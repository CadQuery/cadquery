import os.path

from tempfile import TemporaryDirectory
from shutil import make_archive

from vtk import vtkJSONSceneExporter, vtkRenderer, vtkRenderWindow, vtkVRMLExporter

from OCP.XSControl import XSControl_WorkSession
from OCP.STEPCAFControl import STEPCAFControl_Writer
from OCP.STEPControl import STEPControl_StepModelType
from OCP.IFSelect import IFSelect_ReturnStatus
from OCP.XCAFApp import XCAFApp_Application
from OCP.XmlDrivers import (
    XmlDrivers_DocumentStorageDriver,
    XmlDrivers_DocumentRetrievalDriver,
)
from OCP.TCollection import TCollection_ExtendedString, TCollection_AsciiString
from OCP.PCDM import PCDM_StoreStatus

from ..assembly import AssemblyProtocol, toCAF, toVTK


def exportAssembly(assy: AssemblyProtocol, path: str) -> bool:
    """
    Export an assembly to a step a file.
    """

    _, doc = toCAF(assy, True)

    session = XSControl_WorkSession()
    writer = STEPCAFControl_Writer(session, False)
    writer.SetColorMode(True)
    writer.SetLayerMode(True)
    writer.SetNameMode(True)
    writer.Transfer(doc, STEPControl_StepModelType.STEPControl_AsIs)

    status = writer.Write(path)

    return status == IFSelect_ReturnStatus.IFSelect_RetDone


def exportCAF(assy: AssemblyProtocol, path: str) -> bool:
    """
    Export an assembly to a OCAF xml file (internal OCCT format).
    """

    folder, fname = os.path.split(path)
    name, ext = os.path.splitext(fname)
    ext = ext[1:] if ext[0] == "." else ext

    _, doc = toCAF(assy)
    app = XCAFApp_Application.GetApplication_s()

    store = XmlDrivers_DocumentStorageDriver(
        TCollection_ExtendedString("Copyright: Open Cascade, 2001-2002")
    )
    ret = XmlDrivers_DocumentRetrievalDriver()

    app.DefineFormat(
        TCollection_AsciiString("XmlOcaf"),
        TCollection_AsciiString("Xml XCAF Document"),
        TCollection_AsciiString(ext),
        ret,
        store,
    )

    doc.SetRequestedFolder(TCollection_ExtendedString(folder))
    doc.SetRequestedName(TCollection_ExtendedString(name))

    status = app.SaveAs(doc, TCollection_ExtendedString(path))

    app.Close(doc)

    return status == PCDM_StoreStatus.PCDM_SS_OK


def _vtkRenderWindow(assy: AssemblyProtocol) -> vtkRenderWindow:
    """
    Convert an assembly to a vtkRenderWindow. Used by vtk based exporters.
    """

    renderer = vtkRenderer()
    renderWindow = vtkRenderWindow()
    renderWindow.AddRenderer(renderer)
    toVTK(assy, renderer)

    renderer.ResetCamera()
    renderer.SetBackground(1, 1, 1)

    return renderWindow


def exportVTKJS(assy: AssemblyProtocol, path: str):
    """
    Export an assembly to a zipped vtkjs. NB: .zip extensions is added to path.
    """

    renderer = vtkRenderer()
    renderWindow = vtkRenderWindow()
    renderWindow.AddRenderer(renderer)
    toVTK(assy, renderer)

    renderer.ResetCamera()
    renderer.SetBackground(1, 1, 1)

    with TemporaryDirectory() as tmpdir:

        exporter = vtkJSONSceneExporter()
        exporter.SetFileName(tmpdir)
        exporter.SetRenderWindow(renderWindow)
        exporter.Write()
        make_archive(path, "zip", tmpdir)


def exportVRML(assy: AssemblyProtocol, path: str):
    """
    Export an assembly to a vrml file using vtk.
    """

    exporter = vtkVRMLExporter()
    exporter.SetFileName(path)
    exporter.SetRenderWindow(_vtkRenderWindow(assy))
    exporter.Write()
