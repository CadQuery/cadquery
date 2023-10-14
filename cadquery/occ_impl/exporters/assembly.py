import os.path
import uuid

from tempfile import TemporaryDirectory
from shutil import make_archive
from itertools import chain
from typing import Optional
from typing_extensions import Literal

from vtkmodules.vtkIOExport import vtkJSONSceneExporter, vtkVRMLExporter
from vtkmodules.vtkRenderingCore import vtkRenderer, vtkRenderWindow

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
from OCP.RWGltf import RWGltf_CafWriter
from OCP.TColStd import TColStd_IndexedDataMapOfStringString
from OCP.Message import Message_ProgressRange
from OCP.Interface import Interface_Static

from ..assembly import AssemblyProtocol, toCAF, toVTK, toFusedCAF
from ..geom import Location


class ExportModes:
    DEFAULT = "default"
    FUSED = "fused"


STEPExportModeLiterals = Literal["default", "fused"]


def exportAssembly(
    assy: AssemblyProtocol,
    path: str,
    mode: STEPExportModeLiterals = "default",
    **kwargs
) -> bool:
    """
    Export an assembly to a STEP file.

    kwargs is used to provide optional keyword arguments to configure the exporter.

    :param assy: assembly
    :param path: Path and filename for writing
    :param mode: STEP export mode. The options are "default", and "fused" (a single fused compound).
        It is possible that fused mode may exhibit low performance.
    :param fuzzy_tol: OCCT fuse operation tolerance setting used only for fused assembly export.
    :type fuzzy_tol: float
    :param glue: Enable gluing mode for improved performance during fused assembly export.
        This option should only be used for non-intersecting shapes or those that are only touching or partially overlapping.
        Note that when glue is enabled, the resulting fused shape may be invalid if shapes are intersecting in an incompatible way.
        Defaults to False.
    :type glue: bool
    :param write_pcurves: Enable or disable writing parametric curves to the STEP file. Default True.
        If False, writes STEP file without pcurves. This decreases the size of the resulting STEP file.
    :type write_pcurves: bool
    :param precision_mode: Controls the uncertainty value for STEP entities. Specify -1, 0, or 1. Default 0.
        See OCCT documentation.
    :type precision_mode: int
    """

    # Handle the extra settings for the STEP export
    pcurves = 1
    if "write_pcurves" in kwargs and not kwargs["write_pcurves"]:
        pcurves = 0
    precision_mode = kwargs["precision_mode"] if "precision_mode" in kwargs else 0
    fuzzy_tol = kwargs["fuzzy_tol"] if "fuzzy_tol" in kwargs else None
    glue = kwargs["glue"] if "glue" in kwargs else False

    # Use the assembly name if the user set it
    assembly_name = assy.name if assy.name else str(uuid.uuid1())

    # Handle the doc differently based on which mode we are using
    if mode == "fused":
        _, doc = toFusedCAF(assy, glue, fuzzy_tol)
    else:  # Includes "default"
        _, doc = toCAF(assy, True)

    session = XSControl_WorkSession()
    writer = STEPCAFControl_Writer(session, False)
    writer.SetColorMode(True)
    writer.SetLayerMode(True)
    writer.SetNameMode(True)
    Interface_Static.SetIVal_s("write.surfacecurve.mode", pcurves)
    Interface_Static.SetIVal_s("write.precision.mode", precision_mode)
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


def _vtkRenderWindow(
    assy: AssemblyProtocol, tolerance: float = 1e-3, angularTolerance: float = 0.1
) -> vtkRenderWindow:
    """
    Convert an assembly to a vtkRenderWindow. Used by vtk based exporters.
    """

    renderer = toVTK(assy, tolerance=tolerance, angularTolerance=angularTolerance)
    renderWindow = vtkRenderWindow()
    renderWindow.AddRenderer(renderer)

    renderer.ResetCamera()
    renderer.SetBackground(1, 1, 1)

    return renderWindow


def exportVTKJS(assy: AssemblyProtocol, path: str):
    """
    Export an assembly to a zipped vtkjs. NB: .zip extensions is added to path.
    """

    renderWindow = _vtkRenderWindow(assy)

    with TemporaryDirectory() as tmpdir:

        exporter = vtkJSONSceneExporter()
        exporter.SetFileName(tmpdir)
        exporter.SetRenderWindow(renderWindow)
        exporter.Write()
        make_archive(path, "zip", tmpdir)


def exportVRML(
    assy: AssemblyProtocol,
    path: str,
    tolerance: float = 1e-3,
    angularTolerance: float = 0.1,
):
    """
    Export an assembly to a vrml file using vtk.
    """

    exporter = vtkVRMLExporter()
    exporter.SetFileName(path)
    exporter.SetRenderWindow(_vtkRenderWindow(assy, tolerance, angularTolerance))
    exporter.Write()


def exportGLTF(
    assy: AssemblyProtocol,
    path: str,
    binary: Optional[bool] = None,
    tolerance: float = 1e-3,
    angularTolerance: float = 0.1,
):
    """
    Export an assembly to a gltf file.
    """

    # If the caller specified the binary option, respect it
    if binary is None:
        # Handle the binary option for GLTF export based on file extension
        binary = True
        path_parts = path.split(".")

        # Binary will be the default if the user specified a non-standard file extension
        if len(path_parts) > 0 and path_parts[-1] == "gltf":
            binary = False

    # map from CadQuery's right-handed +Z up coordinate system to glTF's right-handed +Y up coordinate system
    # https://registry.khronos.org/glTF/specs/2.0/glTF-2.0.html#coordinate-system-and-units
    orig_loc = assy.loc
    assy.loc *= Location((0, 0, 0), (1, 0, 0), -90)

    _, doc = toCAF(assy, True, True, tolerance, angularTolerance)

    writer = RWGltf_CafWriter(TCollection_AsciiString(path), binary)
    result = writer.Perform(
        doc, TColStd_IndexedDataMapOfStringString(), Message_ProgressRange()
    )

    # restore coordinate system after exporting
    assy.loc = orig_loc

    return result
