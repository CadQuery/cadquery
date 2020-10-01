from functools import reduce
from typing import Union, Optional, List, Dict, Any, overload, Tuple, Iterator, cast
from typing_extensions import Literal
from uuid import uuid1 as uuid

from .cq import Workplane
from .occ_impl.shapes import Shape, Face, Edge
from .occ_impl.geom import Location, Vector
from .occ_impl.assembly import Color
from .occ_impl.solver import (
    ConstraintSolver,
    ConstraintMarker,
    Constraint as ConstraintPOD,
)
from .occ_impl.exporters.assembly import exportAssembly, exportCAF


AssemblyObjects = Union[Shape, Workplane, None]
ConstraintKinds = Literal["Plane", "Point", "Axis"]
ExportLiterals = Literal["STEP", "XML"]


class Constraint(object):
    """
    Geometrical constraint between two shapes of an assembly.
    """

    objects: Tuple[str, ...]
    args: Tuple[Shape, ...]
    sublocs: Tuple[Location, ...]
    kind: ConstraintKinds
    param: Any

    def __init__(
        self,
        objects: Tuple[str, ...],
        args: Tuple[Shape, ...],
        sublocs: Tuple[Location, ...],
        kind: ConstraintKinds,
        param: Any = None,
    ):
        """
        Construct a constraint.
        
        :param objects: object names refernced in the constraint
        :param args: subshapes (e.g. faces or edges) of the objects
        :param sublocs: locations of the objects (only relevant if the objects are nested in a sub-assembly)
        :param kind: constraint kind
        :param param: optional arbitrary paramter passed to the solver
        """

        self.objects = objects
        self.args = args
        self.sublocs = sublocs
        self.kind = kind
        self.param = param

    def _getAxis(self, arg: Shape) -> Vector:

        if isinstance(arg, Face):
            rv = arg.normalAt()
        elif isinstance(arg, Edge) and arg.geomType() != "CIRCLE":
            rv = arg.tangentAt()
        elif isinstance(arg, Edge) and arg.geomType() == "CIRCLE":
            rv = arg.normal()
        else:
            raise ValueError(f"Cannot construct Axis for {arg}")

        return rv

    def toPOD(self) -> ConstraintPOD:
        """
        Convert the constraint to a representation used by the solver.
        """

        rv: List[Tuple[ConstraintMarker, ...]] = []

        for arg, loc in zip(self.args, self.sublocs):

            arg = arg.located(loc * arg.location())

            if self.kind == "Axis":
                rv.append((self._getAxis(arg).toDir(),))
            elif self.kind == "Point":
                rv.append((arg.Center().toPnt(),))
            elif self.kind == "Plane":
                rv.append((self._getAxis(arg).toDir(), arg.Center().toPnt()))
            else:
                raise ValueError(f"Unknown constraint kind {self.kind}")

        rv.append(self.param)

        return cast(ConstraintPOD, tuple(rv))


class Assembly(object):
    """Nested assembly of Workplane and Shape objects defining their relative positions.
    """

    loc: Location
    name: str
    color: Optional[Color]
    metadata: Dict[str, Any]

    obj: AssemblyObjects
    parent: Optional["Assembly"]
    children: List["Assembly"]

    objects: Dict[str, "Assembly"]
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
        
        
        To create an empty assembly use::
            
            assy = Assembly(None)
            
        To create one constraint a root object::
            
            b = Workplane().box(1,1,1)
            assy = Assembly(b, Location(Vector(0,0,1)), name="root")
            
        """

        self.obj = obj
        self.loc = loc if loc else Location()
        self.name = name if name else str(uuid())
        self.color = color if color else None
        self.parent = None

        self.children = []
        self.constraints = []
        self.objects = {self.name: self}

    def _copy(self) -> "Assembly":
        """
        Make a deep copy of an assembly
        """

        rv = self.__class__(self.obj, self.loc, self.name, self.color)

        for ch in self.children:
            ch_copy = ch._copy()
            ch_copy.parent = rv

            rv.children.append(ch_copy)
            rv.objects[ch_copy.name] = ch_copy
            rv.objects.update(ch_copy.objects)

        return rv

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
        """
        add a subassembly to the current assembly.
        """

        if isinstance(arg, Assembly):

            subassy = arg._copy()

            subassy.loc = kwargs["loc"] if kwargs.get("loc") else arg.loc
            subassy.name = kwargs["name"] if kwargs.get("name") else arg.name
            subassy.color = kwargs["color"] if kwargs.get("color") else arg.color
            subassy.parent = self

            self.children.append(subassy)
            self.objects[subassy.name] = subassy
            self.objects.update(subassy.objects)

        else:
            assy = Assembly(arg, **kwargs)
            assy.parent = self

            self.add(assy)

        return self

    def _query(self, q: str) -> Tuple[str, Optional[Shape]]:
        """
        Execute a selector query on the assembly. 
        The query is expected to be in the following format:
        
            name@kind@args
            
        for example:
        
            obj_name@faces@>Z
        
        """

        name, kind, arg = q.split("@")

        tmp = Workplane()
        obj = self.objects[name].obj

        if isinstance(obj, (Workplane, Shape)):
            tmp.add(obj)
            res = getattr(tmp, kind)(arg)

        return name, res.val() if isinstance(res.val(), Shape) else None

    def _subloc(self, name: str) -> Tuple[Location, str]:
        """
        Calculate relative location of an object in a subassembly.
        
        Returns the relative posiitons as well as the name of the top assembly.
        """

        rv = Location()
        obj = self.objects[name]
        name_out = name

        if obj not in self.children and obj is not self:
            locs = []
            while not obj.parent is self:
                locs.append(obj.loc)
                obj = cast(Assembly, obj.parent)
                name_out = obj.name

            rv = reduce(lambda l1, l2: l1 * l2, locs)

        return (rv, name_out)

    @overload
    def constrain(
        self, q1: str, q2: str, kind: ConstraintKinds, param: Any = None
    ) -> "Assembly":
        ...

    @overload
    def constrain(
        self,
        id1: str,
        s1: Shape,
        id2: str,
        s2: Shape,
        kind: ConstraintKinds,
        param: Any = None,
    ) -> "Assembly":
        ...

    def constrain(self, *args, param=None):
        """
        Define a new constraint.
        """

        if len(args) == 3:
            q1, q2, kind = args
            id1, s1 = self._query(q1)
            id2, s2 = self._query(q2)
        elif len(args) == 4:
            q1, q2, kind, param = args
            id1, s1 = self._query(q1)
            id2, s2 = self._query(q2)
        elif len(args) == 5:
            id1, s1, id2, s2, kind = args
        elif len(args) == 6:
            id1, s1, id2, s2, kind, param = args
        else:
            raise ValueError(f"Incompatibile arguments: {args}")

        loc1, id1_top = self._subloc(id1)
        loc2, id2_top = self._subloc(id2)
        self.constraints.append(
            Constraint((id1_top, id2_top), (s1, s2), (loc1, loc2), kind, param)
        )

        return self

    def solve(self) -> "Assembly":
        """
        Solve the constraints.
        """

        # get all entities and number them
        ents = {}

        i = 0
        lock_ix = 0
        for c in self.constraints:
            for name in c.objects:
                if name not in ents:
                    ents[name] = i
                    if name == self.name:
                        lock_ix = i
                    i += 1

        locs = [self.objects[n].loc for n in ents]

        # construct the constraint mapping
        constraints = []
        for c in self.constraints:
            constraints.append(((ents[c.objects[0]], ents[c.objects[1]]), c.toPOD()))

        # instantiate the solver
        solver = ConstraintSolver(locs, constraints, locked=[lock_ix])

        # solve
        locs_new = solver.solve()

        # update positions
        for loc_new, n in zip(locs_new, ents):
            self.objects[n].loc = loc_new

        return self

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
