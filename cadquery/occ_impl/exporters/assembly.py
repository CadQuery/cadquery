from typing import Iterable
from typing_extensions import Protocol

from OCP.TDocStd import TDocStd_Document
from OCP.TCollection import TCollection_ExtendedString
from OCP.XCAFDoc import XCAFDoc_DocumentTool
from OCP.TDataStd import TDataStd_Name
from OCP.XSControl import XSControl_WorkSession
from OCP.STEPCAFControl import STEPCAFControl_Writer
from OCP.STEPControl import STEPControl_StepModelType
from OCP.IFSelect import IFSelect_ReturnStatus

from ..geom import Location
from ..shapes import Shape, Compound


class AssemblyProtocol(Protocol):
    @property
    def loc(self) -> Location:
        ...

    @property
    def name(self) -> str:
        ...

    @property
    def shapes(self) -> Iterable[Shape]:
        ...

    @property
    def children(self) -> Iterable["AssemblyProtocol"]:
        ...


def exportAssembly(assy: AssemblyProtocol, path) -> bool:

    # prepare a doc
    doc = TDocStd_Document(TCollection_ExtendedString("CQ assy"))
    tool = XCAFDoc_DocumentTool.ShapeTool_s(doc.Main())

    # add root
    root = tool.NewShape()
    TDataStd_Name.Set_s(root, TCollection_ExtendedString(assy.name))

    if assy.shapes:
        tool.SetShape(root, Compound.makeCompound(assy.shapes).moved(assy.loc).wrapped)

    def processChildren(parent, children):

        for ch in children:
            ch_node = tool.AddComponent(
                parent, Compound.makeCompound(ch.shapes).moved(ch.loc).wrapped
            )
            TDataStd_Name.Set_s(ch_node, TCollection_ExtendedString(ch.name))

            if ch.children:
                processChildren(ch_node, ch.children)

    processChildren(root, assy.children)

    tool.UpdateAssemblies()

    session = XSControl_WorkSession()
    writer = STEPCAFControl_Writer(session, False)
    writer.Transfer(doc, STEPControl_StepModelType.STEPControl_AsIs)

    status = writer.Write(path)

    return status == IFSelect_ReturnStatus.IFSelect_RetDone
