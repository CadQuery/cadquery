from typing import Union, Optional, List, Mapping, Any, overload, Tuple
from typing_extensions import Literal
from uuid import uuid1 as uuid

from .cq import Workplane
from .occ_impl.shapes import Shape
from .occ_impl.geom import Location


AssemblyObjects = Union[Shape, Workplane, None]
ConstraintKinds = Literal["Plane", "Point", "Axis"]


class Constraint(object):

    objects: Tuple[Shape, ...]
    args: Tuple[Shape, ...]
    kind: ConstraintKinds


class Assembly(object):

    loc: Location
    name: str
    metadata: Mapping[str, Any]

    obj: AssemblyObjects
    parent: Optional["Assembly"]
    children: List["Assembly"]

    objects: Mapping[str, AssemblyObjects]
    constraints: List[Constraint]

    def __init__(
        self,
        obj: AssemblyObjects,
        loc: Optional[Location] = None,
        name: Optional[str] = None,
    ):

        self.obj = obj
        self.loc = loc if loc else Location()
        self.name = name if name else str(uuid())

        self.objects = {self.name: self.obj}

    @overload
    def add(self, obj: "Assembly"):
        ...

    @overload
    def add(
        self,
        obj: AssemblyObjects,
        loc: Optional[Location] = None,
        name: Optional[str] = None,
    ):
        ...

    def add(self, arg, **kwargs):

        if isinstance(arg, Assembly):
            self.children.append(arg)
            self.objects[arg.name] = arg.obj
            self.objects.update(arg.objects)

        else:
            self.add(Assembly(arg, **kwargs))

    @overload
    def constrain(self, query: str):
        ...

    @overload
    def constrain(self, q1: str, q2: str, kind: ConstraintKinds):
        ...

    @overload
    def constrain(
        self, id1: str, s1: Shape, id2: str, s2: Shape, kind: ConstraintKinds
    ):
        ...

    def constrain(self, *args):

        raise NotImplementedError

    def solve(self):

        raise NotImplementedError

    def save(self, path: str):

        raise NotImplementedError

    def load(self, path: str):

        raise NotImplementedError

    @property
    def shapes(self) -> List[Shape]:

        rv: List[Shape] = []

        if isinstance(self.obj, Shape):
            rv = [self.obj]
        elif isinstance(self.obj, Workplane):
            rv = [el for el in self.obj.vals() if isinstance(el, Shape)]

        return rv
