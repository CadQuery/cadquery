from typing import Iterable, Tuple, Dict
from typing_extensions import Protocol

from OCP.TDocStd import TDocStd_Document
from OCP.TCollection import TCollection_ExtendedString
from OCP.XCAFDoc import XCAFDoc_DocumentTool
from OCP.TDataStd import TDataStd_Name
from OCP.TDF import TDF_Label
from OCP.TopLoc import TopLoc_Location

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

    def traverse(self) -> Iterable[Tuple[str, "AssemblyProtocol"]]:
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

    # add leafs and subassemblies
    subassys: Dict[str, Tuple[TDF_Label, Location]] = {}
    for k, v in assy.traverse():
        # leaf part
        lab = tool.NewShape()
        tool.SetShape(lab, Compound.makeCompound(v.shapes).wrapped)
        setName(lab, f"{k}_part", tool)

        # assy part
        subassy = tool.NewShape()
        tool.AddComponent(subassy, lab, TopLoc_Location())
        setName(subassy, k, tool)

        subassys[k] = (subassy, v.loc)

        for ch in v.children:
            tool.AddComponent(
                subassy, subassys[ch.name][0], subassys[ch.name][1].wrapped
            )

    tool.AddComponent(top, subassys[assy.name][0], assy.loc.wrapped)
    tool.UpdateAssemblies()

    return top, doc
