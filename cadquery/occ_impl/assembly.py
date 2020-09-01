from typing import Iterable, Tuple
from typing_extensions import Protocol

from OCP.TDocStd import TDocStd_Document
from OCP.TCollection import TCollection_ExtendedString
from OCP.XCAFDoc import XCAFDoc_DocumentTool
from OCP.TDataStd import TDataStd_Name
from OCP.TDF import TDF_Label

from .geom import Location
from .shapes import Shape, Compound


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


def setName(l: TDF_Label, name, tool):

    origin = l

    if tool.IsReference_s(l):
        origin = TDF_Label()
        tool.GetReferredShape_s(l, origin)
    else:
        origin = l

    TDataStd_Name.Set_s(origin, TCollection_ExtendedString(name))


def toCAF(assy: AssemblyProtocol) -> Tuple[TDF_Label, TDocStd_Document]:

    # prepare a doc
    doc = TDocStd_Document(TCollection_ExtendedString("XmlOcaf"))
    tool = XCAFDoc_DocumentTool.ShapeTool_s(doc.Main())
    tool.SetAutoNaming_s(False)

    # add root
    top = tool.NewShape()
    TDataStd_Name.Set_s(top, TCollection_ExtendedString("CQ assembly"))

    root = tool.AddComponent(
        top, Compound.makeCompound(assy.shapes).moved(assy.loc).wrapped, True
    )
    setName(root, assy.name, tool)
    tool.UpdateAssemblies()

    def processChildren(parent, children):

        if tool.IsReference_s(parent):
            parent_ref, parent = parent, TDF_Label()
            tool.GetReferredShape_s(parent_ref, parent)

        for ch in children:
            ch_node = tool.AddComponent(
                parent, Compound.makeCompound(ch.shapes).moved(ch.loc).wrapped, True
            )

            setName(ch_node, ch.name, tool)
            tool.UpdateAssemblies()

            if ch.children:
                processChildren(ch_node, ch.children)

    processChildren(root, assy.children)
    tool.UpdateAssemblies()

    return root, doc
