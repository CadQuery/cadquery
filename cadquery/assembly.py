from typing import Union, Optional, List, Mapping, Any, overload, Tuple, Iterator, cast
from typing_extensions import Literal
from uuid import uuid1 as uuid

from .cq import Workplane
from .occ_impl.shapes import Shape
from .occ_impl.geom import Location
from .occ_impl.assembly import Color
from .occ_impl.exporters.assembly import exportAssembly, exportCAF


AssemblyObjects = Union[Shape, Workplane, None]
ConstraintKinds = Literal["Plane", "Point", "Axis"]
ExportLiterals = Literal["STEP", "XML"]


class Constraint(object):

    objects: Tuple[Shape, ...]
    args: Tuple[Shape, ...]
    kind: ConstraintKinds


class Assembly(object):
    """Nested assembly of Workplane and Shape objects defining their relative positions.
    """

    loc: Location
    name: str
    color: Optional[Color]
    metadata: Mapping[str, Any]

    obj: AssemblyObjects
    parent: Optional["Assembly"]
    children: List["Assembly"]

    objects: Mapping[str, AssemblyObjects]
    constraints: List[Constraint]

    def __init__(
        self,
        obj: AssemblyObjects = None,
        loc: Optional[Location] = None,
        name: Optional[str] = None,
        color: Optional[Color] = None,
    ):
        """
        construct an assembly

        :param obj: root object of the assembly (deafault: None)
        :param loc: location of the root object (deafault: None, interpreted as identity transformation)
        :param name: unique name of the root object (default: None, reasulting in an UUID being generated)
        :param color: color of the added object (default: None)
        :return: An Assembly object.
        
        
        To create an empt assembly use::
            
            assy = Assembly(None)
            
        To create one containt a root object::
            
            b = Workplane().box(1,1,1)
            assy = Assembly(b, Location(Vector(0,0,1)), name="root")
            
        """

        self.obj = obj
        self.loc = loc if loc else Location()
        self.name = name if name else str(uuid())
        self.color = color if color else None
        self.parent = None

        self.children = []
        self.objects = {self.name: self.obj}

    @overload
    def add(
        self,
        obj: "Assembly",
        loc: Optional[Location] = None,
        name: Optional[str] = None,
        color: Optional[Color] = None,
    ) -> "Assembly":
        """
        add a subassembly to the current assembly.
        
        :param obj: subassembly to be added
        :param loc: location of the root object (deafault: None, resulting in the location stored in the subassembly being used)
        :param name: unique name of the root object (default: None, resulting in the name stored in the subassembly being used)
        :param color: color of the added object (default: None, resulting in the color stored in the subassembly being used)
        """
        ...

    @overload
    def add(
        self,
        obj: AssemblyObjects,
        loc: Optional[Location] = None,
        name: Optional[str] = None,
        color: Optional[Color] = None,
    ) -> "Assembly":
        """
        add a subassembly to the current assembly with explicit location and name
        
        :param obj: object to be added as a subassembly
        :param loc: location of the root object (deafault: None, interpreted as identity transformation)
        :param name: unique name of the root object (default: None, resulting in an UUID being generated)
        :param color: color of the added object (default: None)
        """
        ...

    def add(self, arg, **kwargs):

        if isinstance(arg, Assembly):

            subassy = Assembly(
                arg.obj,
                kwargs["loc"] if kwargs.get("loc") else arg.loc,
                kwargs["name"] if kwargs.get("name") else arg.name,
                kwargs["color"] if kwargs.get("color") else arg.color,
            )

            subassy.children.extend(arg.children)
            subassy.objects[subassy.name] = subassy.obj
            subassy.objects.update(arg.objects)

            self.children.append(subassy)
            self.objects[subassy.name] = subassy.obj
            self.objects.update(subassy.objects)

            arg.parent = self

        else:
            assy = Assembly(arg, **kwargs)
            assy.parent = self

            self.add(assy)

        return self

    @overload
    def constrain(self, query: str) -> "Assembly":
        ...

    @overload
    def constrain(self, q1: str, q2: str, kind: ConstraintKinds) -> "Assembly":
        ...

    @overload
    def constrain(
        self, id1: str, s1: Shape, id2: str, s2: Shape, kind: ConstraintKinds
    ) -> "Assembly":
        ...

    def constrain(self, *args):

        raise NotImplementedError

    def solve(self) -> "Assembly":

        raise NotImplementedError

    def save(
        self, path: str, exportType: Optional[ExportLiterals] = None
    ) -> "Assembly":
        """
        save as STEP or OCCT native XML file
        
        :param path: filepath
        :param exportType: export format (deafault: None, results in format being inferred form the path)
        """

        if exportType is None:
            t = path.split(".")[-1].upper()
            if t in ("STEP", "XML"):
                exportType = cast(ExportLiterals, t)
            else:
                raise ValueError("Unknown extension, specify export type explicitly")

        if exportType == "STEP":
            exportAssembly(self, path)
        elif exportType == "XML":
            exportCAF(self, path)
        else:
            raise ValueError(f"Unknown format: {exportType}")

        return self

    @classmethod
    def load(cls, path: str) -> "Assembly":

        raise NotImplementedError

    @property
    def shapes(self) -> List[Shape]:
        """
        List of Shape objects in the .obj field
        """

        rv: List[Shape] = []

        if isinstance(self.obj, Shape):
            rv = [self.obj]
        elif isinstance(self.obj, Workplane):
            rv = [el for el in self.obj.vals() if isinstance(el, Shape)]

        return rv

    def traverse(self) -> Iterator[Tuple[str, "Assembly"]]:
        """
        Yield (name, child) pairs in a bottom-up manner
        """

        for ch in self.children:
            for el in ch.traverse():
                yield el

        yield (self.name, self)
