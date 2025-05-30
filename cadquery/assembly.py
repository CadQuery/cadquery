from functools import reduce
from typing import (
    Union,
    Optional,
    List,
    Dict,
    Any,
    overload,
    Tuple,
    Iterator,
    cast,
    get_args,
)
from typing_extensions import Literal
from typish import instance_of
from uuid import uuid1 as uuid

from .cq import Workplane
from .occ_impl.shapes import Shape, Compound
from .occ_impl.geom import Location
from .occ_impl.assembly import Color
from .occ_impl.solver import (
    ConstraintKind,
    ConstraintSolver,
    ConstraintSpec as Constraint,
    UnaryConstraintKind,
    BinaryConstraintKind,
)
from .occ_impl.exporters.assembly import (
    exportAssembly,
    exportCAF,
    exportVTKJS,
    exportVRML,
    exportGLTF,
    STEPExportModeLiterals,
)

from .selectors import _expression_grammar as _selector_grammar
from .utils import deprecate

# type definitions
AssemblyObjects = Union[Shape, Workplane, None]
ExportLiterals = Literal["STEP", "XML", "GLTF", "VTKJS", "VRML", "STL"]

PATH_DELIM = "/"

# entity selector grammar definition
def _define_grammar():

    from pyparsing import (
        Literal as Literal,
        Word,
        Optional,
        alphas,
        alphanums,
        delimitedList,
    )

    Separator = Literal("@").suppress()
    TagSeparator = Literal("?").suppress()

    Name = delimitedList(
        Word(alphas, alphanums + "_"), PATH_DELIM, combine=True
    ).setResultsName("name")
    Tag = Word(alphas, alphanums + "_").setResultsName("tag")
    Selector = _selector_grammar.setResultsName("selector")

    SelectorType = (
        Literal("solids") | Literal("faces") | Literal("edges") | Literal("vertices")
    ).setResultsName("selector_kind")

    return (
        Name
        + Optional(TagSeparator + Tag)
        + Optional(Separator + SelectorType + Separator + Selector)
    )


_grammar = _define_grammar()


class Assembly(object):
    """Nested assembly of Workplane and Shape objects defining their relative positions."""

    loc: Location
    name: str
    color: Optional[Color]
    metadata: Dict[str, Any]

    obj: AssemblyObjects
    parent: Optional["Assembly"]
    children: List["Assembly"]

    objects: Dict[str, "Assembly"]
    constraints: List[Constraint]

    # Allows metadata to be stored for exports
    _subshape_names: dict[Shape, str]
    _subshape_colors: dict[Shape, Color]
    _subshape_layers: dict[Shape, str]

    _solve_result: Optional[Dict[str, Any]]

    def __init__(
        self,
        obj: AssemblyObjects = None,
        loc: Optional[Location] = None,
        name: Optional[str] = None,
        color: Optional[Color] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """
        construct an assembly

        :param obj: root object of the assembly (default: None)
        :param loc: location of the root object (default: None, interpreted as identity transformation)
        :param name: unique name of the root object (default: None, resulting in an UUID being generated)
        :param color: color of the added object (default: None)
        :param metadata: a store for user-defined metadata (default: None)
        :return: An Assembly object.


        To create an empty assembly use::

            assy = Assembly(None)

        To create one constraint a root object::

            b = Workplane().box(1, 1, 1)
            assy = Assembly(b, Location(Vector(0, 0, 1)), name="root")

        """

        self.obj = obj
        self.loc = loc if loc else Location()
        self.name = name if name else str(uuid())
        self.color = color if color else None
        self.metadata = metadata if metadata else {}
        self.parent = None

        self.children = []
        self.constraints = []
        self.objects = {self.name: self}

        self._solve_result = None

        self._subshape_names = {}
        self._subshape_colors = {}
        self._subshape_layers = {}

    def _copy(self) -> "Assembly":
        """
        Make a deep copy of an assembly
        """

        rv = self.__class__(self.obj, self.loc, self.name, self.color, self.metadata)

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
        Add a subassembly to the current assembly.

        :param obj: subassembly to be added
        :param loc: location of the root object (default: None, resulting in the location stored in
          the subassembly being used)
        :param name: unique name of the root object (default: None, resulting in the name stored in
          the subassembly being used)
        :param color: color of the added object (default: None, resulting in the color stored in the
          subassembly being used)
        """
        ...

    @overload
    def add(
        self,
        obj: AssemblyObjects,
        loc: Optional[Location] = None,
        name: Optional[str] = None,
        color: Optional[Color] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> "Assembly":
        """
        Add a subassembly to the current assembly with explicit location and name.

        :param obj: object to be added as a subassembly
        :param loc: location of the root object (default: None, interpreted as identity
          transformation)
        :param name: unique name of the root object (default: None, resulting in an UUID being
          generated)
        :param color: color of the added object (default: None)
        :param metadata: a store for user-defined metadata (default: None)
        """
        ...

    def add(self, arg, **kwargs):
        """
        Add a subassembly to the current assembly.
        """

        if isinstance(arg, Assembly):

            # enforce unique names
            name = kwargs["name"] if kwargs.get("name") else arg.name
            if name in self.objects:
                raise ValueError("Unique name is required")

            subassy = arg._copy()

            subassy.loc = kwargs["loc"] if kwargs.get("loc") else arg.loc
            subassy.name = kwargs["name"] if kwargs.get("name") else arg.name
            subassy.color = kwargs["color"] if kwargs.get("color") else arg.color
            subassy.metadata = (
                kwargs["metadata"] if kwargs.get("metadata") else arg.metadata
            )
            subassy.parent = self

            self.children.append(subassy)
            self.objects.update(subassy._flatten())

        else:
            assy = self.__class__(arg, **kwargs)
            assy.parent = self

            self.add(assy)

        return self

    def remove(self, name: str) -> "Assembly":
        """
        Remove a part/subassembly from the current assembly.

        :param name: Name of the part/subassembly to be removed
        :return: The modified assembly

        *NOTE* This method can cause problems with deeply nested assemblies and does not remove
        constraints associated with the removed part/subassembly.
        """

        # Make sure the part/subassembly is actually part of the assembly
        if name not in self.objects:
            raise ValueError(f"No object with name '{name}' found in the assembly")

        # Get the part/assembly to be removed
        to_remove = self.objects[name]

        # Remove the part/assembly from the parent's children list
        if to_remove.parent:
            to_remove.parent.children.remove(to_remove)

        # Remove the part/assembly from the assembly's object dictionary
        del self.objects[name]

        # Remove all descendants from the objects dictionary
        for descendant_name in to_remove._flatten().keys():
            if descendant_name in self.objects:
                del self.objects[descendant_name]

        # Update the parent reference
        to_remove.parent = None

        return self

    def _query(self, q: str) -> Tuple[str, Optional[Shape]]:
        """
        Execute a selector query on the assembly.
        The query is expected to be in the following format:

            name[?tag][@kind@args]

        valid example include:

            obj_name @ faces @ >Z
            obj_name?tag1@faces@>Z
            obj_name ? tag
            obj_name

        """

        tmp: Workplane
        res: Workplane

        query = _grammar.parseString(q, True)
        name: str = query.name

        obj = self.objects[name].obj

        if isinstance(obj, Workplane) and query.tag:
            tmp = obj._getTagged(query.tag)
        elif isinstance(obj, (Workplane, Shape)):
            tmp = Workplane().add(obj)
        else:
            raise ValueError("Workplane or Shape required to define a constraint")

        if query.selector:
            res = getattr(tmp, query.selector_kind)(query.selector)
        else:
            res = tmp

        val = res.val()

        return name, val if isinstance(val, Shape) else None

    def _subloc(self, name: str) -> Tuple[Location, str]:
        """
        Calculate relative location of an object in a subassembly.

        Returns the relative positions as well as the name of the top assembly.
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

            # This must reduce in the order of (parent, ..., child)
            rv = reduce(lambda l1, l2: l2 * l1, locs)

        return (rv, name_out)

    @overload
    def constrain(
        self, q1: str, q2: str, kind: ConstraintKind, param: Any = None
    ) -> "Assembly":
        ...

    @overload
    def constrain(self, q1: str, kind: ConstraintKind, param: Any = None) -> "Assembly":
        ...

    @overload
    def constrain(
        self,
        id1: str,
        s1: Shape,
        id2: str,
        s2: Shape,
        kind: ConstraintKind,
        param: Any = None,
    ) -> "Assembly":
        ...

    @overload
    def constrain(
        self, id1: str, s1: Shape, kind: ConstraintKind, param: Any = None,
    ) -> "Assembly":
        ...

    def constrain(self, *args, param=None):
        """
        Define a new constraint.
        """

        # dispatch on arguments
        if len(args) == 2:
            q1, kind = args
            id1, s1 = self._query(q1)
        elif len(args) == 3 and instance_of(args[1], UnaryConstraintKind):
            q1, kind, param = args
            id1, s1 = self._query(q1)
        elif len(args) == 3:
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
            raise ValueError(f"Incompatible arguments: {args}")

        # handle unary and binary constraints
        if instance_of(kind, UnaryConstraintKind):
            loc1, id1_top = self._subloc(id1)
            c = Constraint((id1_top,), (s1,), (loc1,), kind, param)
        elif instance_of(kind, BinaryConstraintKind):
            loc1, id1_top = self._subloc(id1)
            loc2, id2_top = self._subloc(id2)
            c = Constraint((id1_top, id2_top), (s1, s2), (loc1, loc2), kind, param)
        else:
            raise ValueError(f"Unknown constraint: {kind}")

        self.constraints.append(c)

        return self

    def solve(self, verbosity: int = 0) -> "Assembly":
        """
        Solve the constraints.
        """

        # Get all entities and number them. First entity is marked as locked
        ents = {}

        i = 0
        locked: List[int] = []

        for c in self.constraints:
            for name in c.objects:
                if name not in ents:
                    ents[name] = i
                    i += 1
                if (c.kind == "Fixed" or name == self.name) and ents[
                    name
                ] not in locked:
                    locked.append(ents[name])

        # Lock the first occurring entity if needed.
        if not locked:
            unary_objects = [
                c.objects[0]
                for c in self.constraints
                if instance_of(c.kind, UnaryConstraintKind)
            ]
            binary_objects = [
                c.objects[0]
                for c in self.constraints
                if instance_of(c.kind, BinaryConstraintKind)
            ]
            for b in binary_objects:
                if b not in unary_objects:
                    locked.append(ents[b])
                    break

        # Lock the first occurring entity if needed.
        if not locked:
            locked.append(0)

        locs = [self.objects[n].loc for n in ents]

        # construct the constraint mapping
        constraints = []
        for c in self.constraints:
            ixs = tuple(ents[obj] for obj in c.objects)
            pods = c.toPODs()

            for pod in pods:
                constraints.append((ixs, pod))

        # check if any constraints were specified
        if not constraints:
            raise ValueError("At least one constraint required")

        # check if at least two entities are present
        if len(ents) < 2:
            raise ValueError("At least two entities need to be constrained")

        # instantiate the solver
        scale = self.toCompound().BoundingBox().DiagonalLength
        solver = ConstraintSolver(locs, constraints, locked=locked, scale=scale)

        # solve
        locs_new, self._solve_result = solver.solve(verbosity)

        # update positions

        # find the inverse root loc
        loc_root_inv = Location()

        if self.obj:
            for loc_new, n in zip(locs_new, ents):
                if n == self.name:
                    loc_root_inv = loc_new.inverse
                    break

        # update the positions
        for loc_new, n in zip(locs_new, ents):
            if n != self.name:
                self.objects[n].loc = loc_root_inv * loc_new

        return self

    @deprecate()
    def save(
        self,
        path: str,
        exportType: Optional[ExportLiterals] = None,
        mode: STEPExportModeLiterals = "default",
        tolerance: float = 0.1,
        angularTolerance: float = 0.1,
        **kwargs,
    ) -> "Assembly":
        """
        Save assembly to a file.

        :param path: Path and filename for writing.
        :param exportType: export format (default: None, results in format being inferred form the path)
        :param mode: STEP only - See :meth:`~cadquery.occ_impl.exporters.assembly.exportAssembly`.
        :param tolerance: the deflection tolerance, in model units. Only used for glTF, VRML. Default 0.1.
        :param angularTolerance: the angular tolerance, in radians. Only used for glTF, VRML. Default 0.1.
        :param \\**kwargs: Additional keyword arguments.  Only used for STEP, glTF and STL.
            See :meth:`~cadquery.occ_impl.exporters.assembly.exportAssembly`.
        :param ascii: STL only - Sets whether or not STL export should be text or binary
        :type ascii: bool
        """

        # Make sure the export mode setting is correct
        if mode not in get_args(STEPExportModeLiterals):
            raise ValueError(f"Unknown assembly export mode {mode} for STEP")

        if exportType is None:
            t = path.split(".")[-1].upper()
            if t in ("STEP", "XML", "VRML", "VTKJS", "GLTF", "GLB", "STL"):
                exportType = cast(ExportLiterals, t)
            else:
                raise ValueError("Unknown extension, specify export type explicitly")

        if exportType == "STEP":
            exportAssembly(self, path, mode, **kwargs)
        elif exportType == "XML":
            exportCAF(self, path)
        elif exportType == "VRML":
            exportVRML(self, path, tolerance, angularTolerance)
        elif exportType == "GLTF" or exportType == "GLB":
            exportGLTF(self, path, None, tolerance, angularTolerance)
        elif exportType == "VTKJS":
            exportVTKJS(self, path)
        elif exportType == "STL":
            # Handle the ascii setting for STL export
            export_ascii = False
            if "ascii" in kwargs:
                export_ascii = bool(kwargs.get("ascii"))

            self.toCompound().exportStl(path, tolerance, angularTolerance, export_ascii)
        else:
            raise ValueError(f"Unknown format: {exportType}")

        return self

    def export(
        self,
        path: str,
        exportType: Optional[ExportLiterals] = None,
        mode: STEPExportModeLiterals = "default",
        tolerance: float = 0.1,
        angularTolerance: float = 0.1,
        **kwargs,
    ) -> "Assembly":
        """
        Save assembly to a file.

        :param path: Path and filename for writing.
        :param exportType: export format (default: None, results in format being inferred form the path)
        :param mode: STEP only - See :meth:`~cadquery.occ_impl.exporters.assembly.exportAssembly`.
        :param tolerance: the deflection tolerance, in model units. Only used for glTF, VRML. Default 0.1.
        :param angularTolerance: the angular tolerance, in radians. Only used for glTF, VRML. Default 0.1.
        :param \\**kwargs: Additional keyword arguments.  Only used for STEP, glTF and STL.
            See :meth:`~cadquery.occ_impl.exporters.assembly.exportAssembly`.
        :param ascii: STL only - Sets whether or not STL export should be text or binary
        :type ascii: bool
        """

        # Make sure the export mode setting is correct
        if mode not in get_args(STEPExportModeLiterals):
            raise ValueError(f"Unknown assembly export mode {mode} for STEP")

        if exportType is None:
            t = path.split(".")[-1].upper()
            if t in ("STEP", "XML", "VRML", "VTKJS", "GLTF", "GLB", "STL"):
                exportType = cast(ExportLiterals, t)
            else:
                raise ValueError("Unknown extension, specify export type explicitly")

        if exportType == "STEP":
            exportAssembly(self, path, mode, **kwargs)
        elif exportType == "XML":
            exportCAF(self, path)
        elif exportType == "VRML":
            exportVRML(self, path, tolerance, angularTolerance)
        elif exportType == "GLTF" or exportType == "GLB":
            exportGLTF(self, path, None, tolerance, angularTolerance)
        elif exportType == "VTKJS":
            exportVTKJS(self, path)
        elif exportType == "STL":
            # Handle the ascii setting for STL export
            export_ascii = False
            if "ascii" in kwargs:
                export_ascii = bool(kwargs.get("ascii"))

            self.toCompound().exportStl(path, tolerance, angularTolerance, export_ascii)
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

    def _flatten(self, parents=[]):
        """
        Generate a dict with all ancestors with keys indicating parent-child relations.
        """

        rv = {}

        for ch in self.children:
            rv.update(ch._flatten(parents=parents + [self.name]))

        rv[PATH_DELIM.join(parents + [self.name])] = self

        return rv

    def __iter__(
        self,
        loc: Optional[Location] = None,
        name: Optional[str] = None,
        color: Optional[Color] = None,
    ) -> Iterator[Tuple[Shape, str, Location, Optional[Color]]]:
        """
        Assembly iterator yielding shapes, names, locations and colors.
        """

        name = f"{name}/{self.name}" if name else self.name
        loc = loc * self.loc if loc else self.loc
        color = self.color if self.color else color

        if self.obj:
            yield self.obj if isinstance(self.obj, Shape) else Compound.makeCompound(
                s for s in self.obj.vals() if isinstance(s, Shape)
            ), name, loc, color

        for ch in self.children:
            yield from ch.__iter__(loc, name, color)

    def toCompound(self) -> Compound:
        """
        Returns a Compound made from this Assembly (including all children) with the
        current Locations applied. Usually this method would only be used after solving.
        """

        shapes = self.shapes
        shapes.extend((child.toCompound() for child in self.children))

        return Compound.makeCompound(shapes).locate(self.loc)

    def _repr_javascript_(self):
        """
        Jupyter 3D representation support
        """

        from .occ_impl.jupyter_tools import display

        return display(self)._repr_javascript_()

    def addSubshape(
        self,
        s: Shape,
        name: Optional[str] = None,
        color: Optional[Color] = None,
        layer: Optional[str] = None,
    ) -> "Assembly":
        """
        Handles name, color and layer metadata for subshapes.

        :param s: The subshape to add metadata to.
        :param name: The name to assign to the subshape.
        :param color: The color to assign to the subshape.
        :param layer: The layer to assign to the subshape.
        :return: The modified assembly.
        """

        # Handle any metadata we were passed
        if name:
            self._subshape_names[s] = name
        if color:
            self._subshape_colors[s] = color
        if layer:
            self._subshape_layers[s] = layer

        return self
