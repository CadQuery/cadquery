from typing import (
    Union,
    Optional,
    List,
    Dict,
    Callable,
    Tuple,
    Iterable,
    Iterator,
    Any,
    Sequence,
    TypeVar,
    cast as tcast,
)
from typing_extensions import Literal
from math import tan, sin, cos, pi, radians, remainder
from itertools import product, chain
from multimethod import multimethod
from typish import instance_of, get_type

from .hull import find_hull
from .selectors import StringSyntaxSelector, Selector
from .types import Real

from .occ_impl.shapes import Shape, Face, Edge, Wire, Compound, Vertex, edgesToWires
from .occ_impl.geom import Location, Vector
from .occ_impl.importers.dxf import _importDXF
from .occ_impl.sketch_solver import (
    SketchConstraintSolver,
    ConstraintKind,
    ConstraintInvariants,
    DOF,
    arc_first,
    arc_last,
    arc_point,
)

Modes = Literal["a", "s", "i", "c"]  # add, subtract, intersect, construct
Point = Union[Vector, Tuple[Real, Real]]
TOL = 1e-6

T = TypeVar("T", bound="Sketch")
SketchVal = Union[Shape, Location]


class Constraint(object):

    tags: Tuple[str, ...]
    args: Tuple[Edge, ...]
    kind: ConstraintKind
    param: Any

    def __init__(
        self,
        tags: Tuple[str, ...],
        args: Tuple[Edge, ...],
        kind: ConstraintKind,
        param: Any = None,
    ):

        # validate based on the solver provided spec
        if kind not in ConstraintInvariants:
            raise ValueError(f"Unknown constraint {kind}.")

        arity, types, param_type, converter = ConstraintInvariants[kind]

        if arity != len(tags):
            raise ValueError(
                f"Invalid number of entities for constraint {kind}. Provided {len(tags)}, required {arity}."
            )

        if any(e.geomType() not in types for e in args):
            raise ValueError(
                f"Unsupported geometry types {[e.geomType() for e in args]} for constraint {kind}."
            )

        if not instance_of(param, param_type):
            raise ValueError(
                f"Unsupported argument types {get_type(param)}, required {param_type}."
            )

        # if all is fine store everything and possibly convert the params
        self.tags = tags
        self.args = args
        self.kind = kind
        self.param = tcast(Any, converter)(param) if converter else param


class Sketch(object):
    """
    2D sketch. Supports faces, edges and edges with constraints based construction.
    """

    parent: Any
    locs: List[Location]

    _faces: Compound
    _wires: List[Wire]
    _edges: List[Edge]

    _selection: List[SketchVal]
    _constraints: List[Constraint]

    _tags: Dict[str, Sequence[SketchVal]]

    _solve_status: Optional[Dict[str, Any]]

    def __init__(self: T, parent: Any = None, locs: Iterable[Location] = (Location(),)):
        """
        Construct an empty sketch.
        """

        self.parent = parent
        self.locs = list(locs)

        self._faces = Compound.makeCompound(())
        self._wires = []
        self._edges = []

        self._selection = []
        self._constraints = []

        self._tags = {}

        self._solve_status = None

    def __iter__(self) -> Iterator[Face]:
        """
        Iterate over faces-locations combinations.
        """

        return iter(f for l in self.locs for f in self._faces.moved(l).Faces())

    def _tag(self: T, val: Sequence[Union[Shape, Location]], tag: str):

        self._tags[tag] = val

    # face construction
    def face(
        self: T,
        b: Union[Wire, Iterable[Edge], Compound, T],
        angle: Real = 0,
        mode: Modes = "a",
        tag: Optional[str] = None,
        ignore_selection: bool = False,
    ) -> T:
        """
        Construct a face from a wire or edges.
        """

        res: Union[Face, Sketch, Compound]

        if isinstance(b, Wire):
            res = Face.makeFromWires(b)
        elif isinstance(b, (Sketch, Compound)):
            res = b
        elif isinstance(b, Iterable):
            wires = edgesToWires(tcast(Iterable[Edge], b))
            res = Face.makeFromWires(*(wires[0], wires[1:]))
        else:
            raise ValueError(f"Unsupported argument {b}")

        if angle != 0:
            res = res.moved(Location(Vector(), Vector(0, 0, 1), angle))

        return self.each(lambda l: res.moved(l), mode, tag, ignore_selection)

    def importDXF(
        self: T,
        filename: str,
        tol: float = 1e-6,
        exclude: List[str] = [],
        angle: Real = 0,
        mode: Modes = "a",
        tag: Optional[str] = None,
    ) -> T:
        """
        Import a DXF file and construct face(s)
        """

        res = Compound.makeCompound(_importDXF(filename, tol, exclude))

        return self.face(res, angle, mode, tag)

    def rect(
        self: T,
        w: Real,
        h: Real,
        angle: Real = 0,
        mode: Modes = "a",
        tag: Optional[str] = None,
    ) -> T:
        """
        Construct a rectangular face.
        """

        res = Face.makePlane(h, w).rotate(Vector(), Vector(0, 0, 1), angle)

        return self.each(lambda l: res.located(l), mode, tag)

    def circle(self: T, r: Real, mode: Modes = "a", tag: Optional[str] = None) -> T:
        """
        Construct a circular face.
        """

        res = Face.makeFromWires(Wire.makeCircle(r, Vector(), Vector(0, 0, 1)))

        return self.each(lambda l: res.located(l), mode, tag)

    def ellipse(
        self: T,
        a1: Real,
        a2: Real,
        angle: Real = 0,
        mode: Modes = "a",
        tag: Optional[str] = None,
    ) -> T:
        """
        Construct an elliptical face.
        """

        res = Face.makeFromWires(
            Wire.makeEllipse(
                a1, a2, Vector(), Vector(0, 0, 1), Vector(1, 0, 0), rotation_angle=angle
            )
        )

        return self.each(lambda l: res.located(l), mode, tag)

    def trapezoid(
        self: T,
        w: Real,
        h: Real,
        a1: Real,
        a2: Optional[float] = None,
        angle: Real = 0,
        mode: Modes = "a",
        tag: Optional[str] = None,
    ) -> T:
        """
        Construct a trapezoidal face.
        """

        v1 = Vector(-w / 2, -h / 2)
        v2 = Vector(w / 2, -h / 2)
        v3 = Vector(-w / 2 + h / tan(radians(a1)), h / 2)
        v4 = Vector(w / 2 - h / tan(radians(a2) if a2 else radians(a1)), h / 2)

        return self.polygon((v1, v2, v4, v3, v1), angle, mode, tag)

    def slot(
        self: T,
        w: Real,
        h: Real,
        angle: Real = 0,
        mode: Modes = "a",
        tag: Optional[str] = None,
    ) -> T:
        """
        Construct a slot-shaped face.
        """

        p1 = Vector(-w / 2, h / 2)
        p2 = Vector(w / 2, h / 2)
        p3 = Vector(-w / 2, -h / 2)
        p4 = Vector(w / 2, -h / 2)
        p5 = Vector(-w / 2 - h / 2, 0)
        p6 = Vector(w / 2 + h / 2, 0)

        e1 = Edge.makeLine(p1, p2)
        e2 = Edge.makeThreePointArc(p2, p6, p4)
        e3 = Edge.makeLine(p4, p3)
        e4 = Edge.makeThreePointArc(p3, p5, p1)

        wire = Wire.assembleEdges((e1, e2, e3, e4))

        return self.face(wire, angle, mode, tag)

    def regularPolygon(
        self: T,
        r: Real,
        n: int,
        angle: Real = 0,
        mode: Modes = "a",
        tag: Optional[str] = None,
    ) -> T:
        """
        Construct a regular polygonal face.
        """

        pts = [
            Vector(r * sin(i * 2 * pi / n), r * cos(i * 2 * pi / n))
            for i in range(n + 1)
        ]

        return self.polygon(pts, angle, mode, tag)

    def polygon(
        self: T,
        pts: Iterable[Point],
        angle: Real = 0,
        mode: Modes = "a",
        tag: Optional[str] = None,
    ) -> T:
        """
        Construct a polygonal face.
        """

        w = Wire.makePolygon(p if isinstance(p, Vector) else Vector(*p) for p in pts)

        return self.face(w, angle, mode, tag)

    # distribute locations

    def rarray(self: T, xs: Real, ys: Real, nx: int, ny: int) -> T:
        """
        Generate a rectangular array of locations.
        """

        if nx < 1 or ny < 1:
            raise ValueError(f"At least 1 elements required, requested {nx}, {ny}")

        locs = []

        offset = Vector((nx - 1) * xs, (ny - 1) * ys) * 0.5
        for i, j in product(range(nx), range(ny)):
            locs.append(Location(Vector(i * xs, j * ys) - offset))

        if self._selection:
            selection: Sequence[Union[Shape, Location, Vector]] = self._selection
        else:
            selection = [Vector()]

        return self.push(
            (l * el if isinstance(el, Location) else l * Location(el.Center()))
            for l in locs
            for el in selection
        )

    def parray(self: T, r: Real, a1: Real, da: Real, n: int, rotate: bool = True) -> T:
        """
        Generate a polar array of locations.
        """

        if n < 1:
            raise ValueError(f"At least 1 element required, requested {n}")

        locs = []

        if abs(remainder(da, 360)) < TOL:
            angle = da / n
        else:
            angle = da / (n - 1) if n > 1 else a1

        for i in range(0, n):
            phi = a1 + (angle * i)
            x = r * cos(radians(phi))
            y = r * sin(radians(phi))

            loc = Location(Vector(x, y))
            locs.append(loc)

        if self._selection:
            selection: Sequence[Union[Shape, Location, Vector]] = self._selection
        else:
            selection = [Vector()]

        return self.push(
            (
                l
                * el
                * Location(
                    Vector(0, 0), Vector(0, 0, 1), (a1 + (angle * i)) if rotate else 0
                )
            )
            for i, l in enumerate(locs)
            for el in [
                el if isinstance(el, Location) else Location(el.Center())
                for el in selection
            ]
        )

    def distribute(
        self: T, n: int, start: Real = 0, stop: Real = 1, rotate: bool = True
    ) -> T:
        """
        Distribute locations along selected edges or wires.
        """

        if n < 1:
            raise ValueError(f"At least 1 element required, requested {n}")

        if not self._selection:
            raise ValueError("Nothing selected to distribute over")

        if 1 - abs(stop - start) < TOL:
            trimmed = False
        else:
            trimmed = True

        # closed edge or wire parameters
        params_closed = [start + i * (stop - start) / n for i in range(n)]

        # open or trimmed edge or wire parameters
        params_open = [
            start + i * (stop - start) / (n - 1) if n - 1 > 0 else start
            for i in range(n)
        ]

        locs = []
        for el in self._selection:
            if isinstance(el, (Wire, Edge)):
                if el.IsClosed() and not trimmed:
                    params = params_closed
                else:
                    params = params_open

                if rotate:
                    locs.extend(el.locations(params, planar=True,))
                else:
                    locs.extend(Location(v) for v in el.positions(params))
            else:
                raise ValueError(f"Unsupported selection: {el}")

        return self.push(locs)

    def push(
        self: T, locs: Iterable[Union[Location, Point]], tag: Optional[str] = None,
    ) -> T:
        """
        Set current selection to given locations or points.
        """

        self._selection = [
            l if isinstance(l, Location) else Location(Vector(l)) for l in locs
        ]

        if tag:
            self._tag(self._selection[:], tag)

        return self

    def each(
        self: T,
        callback: Callable[[Location], Union[Face, "Sketch", Compound]],
        mode: Modes = "a",
        tag: Optional[str] = None,
        ignore_selection: bool = False,
    ) -> T:
        """
        Apply a callback on all applicable entities.
        """

        res: List[Face] = []
        locs: List[Location] = []

        if self._selection and not ignore_selection:
            for el in self._selection:
                if isinstance(el, Location):
                    loc = el
                else:
                    loc = Location(el.Center())

                locs.append(loc)

        else:
            locs.append(Location())

        for loc in locs:
            tmp = callback(loc)

            if isinstance(tmp, Sketch):
                res.extend(tmp._faces.Faces())
            elif isinstance(tmp, Compound):
                res.extend(tmp.Faces())
            else:
                res.append(tmp)

        if tag:
            self._tag(res, tag)

        if mode == "a":
            self._faces = self._faces.fuse(*res)
        elif mode == "s":
            self._faces = self._faces.cut(*res)
        elif mode == "i":
            self._faces = self._faces.intersect(*res)
        elif mode == "c":
            if not tag:
                raise ValueError("No tag specified - the geometry will be unreachable")
        else:
            raise ValueError(f"Invalid mode: {mode}")

        return self

    # modifiers
    def hull(self: T, mode: Modes = "a", tag: Optional[str] = None) -> T:
        """
        Generate a convex hull from current selection or all objects.
        """

        if self._selection:
            rv = find_hull(el for el in self._selection if isinstance(el, Edge))
        elif self._faces:
            rv = find_hull(el for el in self._faces.Edges())
        elif self._edges or self._wires:
            rv = find_hull(
                chain(self._edges, chain.from_iterable(w.Edges() for w in self._wires))
            )
        else:
            raise ValueError("No objects available for hull construction")

        self.face(rv, mode=mode, tag=tag, ignore_selection=bool(self._selection))

        return self

    def offset(self: T, d: Real, mode: Modes = "a", tag: Optional[str] = None) -> T:
        """
        Offset selected wires or edges.
        """

        rv = (el.offset2D(d) for el in self._selection if isinstance(el, Wire))

        for el in chain.from_iterable(rv):
            self.face(el, mode=mode, tag=tag, ignore_selection=bool(self._selection))

        return self

    def _matchFacesToVertices(self) -> Dict[Face, List[Vertex]]:

        rv = {}

        for f in self._faces.Faces():

            f_vertices = f.Vertices()
            rv[f] = [
                v for v in self._selection if isinstance(v, Vertex) and v in f_vertices
            ]

        return rv

    def fillet(self: T, d: Real) -> T:
        """
        Add a fillet based on current selection.
        """

        f2v = self._matchFacesToVertices()

        self._faces = Compound.makeCompound(
            k.fillet2D(d, v) if v else k for k, v in f2v.items()
        )

        return self

    def chamfer(self: T, d: Real) -> T:
        """
        Add a chamfer based on current selection.
        """

        f2v = self._matchFacesToVertices()

        self._faces = Compound.makeCompound(
            k.chamfer2D(d, v) if v else k for k, v in f2v.items()
        )

        return self

    def clean(self: T) -> T:
        """
        Remove internal wires.
        """

        self._faces = self._faces.clean()

        return self

    # selection

    def _unique(self: T, vals: List[SketchVal]) -> List[SketchVal]:

        tmp = {hash(v): v for v in vals}

        return list(tmp.values())

    def _select(
        self: T,
        s: Optional[Union[str, Selector]],
        kind: Literal["Faces", "Wires", "Edges", "Vertices"],
        tag: Optional[str] = None,
    ) -> T:

        rv = []

        if tag:
            for el in self._tags[tag]:
                rv.extend(getattr(el, kind)())
        elif self._selection:
            for el in self._selection:
                if not isinstance(el, Location):
                    rv.extend(getattr(el, kind)())
        else:
            rv.extend(getattr(self._faces, kind)())
            for el in self._edges:
                rv.extend(getattr(el, kind)())

        if s and isinstance(s, Selector):
            filtered = s.filter(rv)
        elif s and isinstance(s, str):
            filtered = StringSyntaxSelector(s).filter(rv)
        else:
            filtered = rv

        self._selection = self._unique(filtered)

        return self

    def tag(self: T, tag: str) -> T:
        """
        Tag current selection.
        """

        self._tags[tag] = list(self._selection)

        return self

    def select(self: T, *tags: str) -> T:
        """
        Select based on tags.
        """

        self._selection = []

        for tag in tags:
            self._selection.extend(self._tags[tag])

        return self

    def faces(
        self: T, s: Optional[Union[str, Selector]] = None, tag: Optional[str] = None
    ) -> T:
        """
        Select faces.
        """

        return self._select(s, "Faces", tag)

    def wires(
        self: T, s: Optional[Union[str, Selector]] = None, tag: Optional[str] = None
    ) -> T:
        """
        Select wires.
        """

        return self._select(s, "Wires", tag)

    def edges(
        self: T, s: Optional[Union[str, Selector]] = None, tag: Optional[str] = None
    ) -> T:
        """
        Select edges.
        """

        return self._select(s, "Edges", tag)

    def vertices(
        self: T, s: Optional[Union[str, Selector]] = None, tag: Optional[str] = None
    ) -> T:
        """
        Select vertices.
        """

        return self._select(s, "Vertices", tag)

    def reset(self: T) -> T:
        """
        Reset current selection.
        """

        self._selection = []
        return self

    def delete(self: T) -> T:
        """
        Delete selected object.
        """

        for obj in self._selection:
            if isinstance(obj, Face):
                self._faces.remove(obj)
            elif isinstance(obj, Wire):
                self._wires.remove(obj)
            elif isinstance(obj, Edge):
                self._edges.remove(obj)

        self._selection = []

        return self

    # edge based interface

    def _startPoint(self) -> Vector:

        if not self._edges:
            raise ValueError("No free edges available")

        e = self._edges[0]

        return e.startPoint()

    def _endPoint(self) -> Vector:

        if not self._edges:
            raise ValueError("No free edges available")

        e = self._edges[-1]

        return e.endPoint()

    def edge(
        self: T, val: Edge, tag: Optional[str] = None, forConstruction: bool = False
    ) -> T:
        """
        Add an edge to the sketch.
        """

        val.forConstruction = forConstruction
        self._edges.append(val)

        if tag:
            self._tag([val], tag)

        return self

    @multimethod
    def segment(
        self: T,
        p1: Point,
        p2: Point,
        tag: Optional[str] = None,
        forConstruction: bool = False,
    ) -> T:
        """
        Construct a segment.
        """

        val = Edge.makeLine(Vector(p1), Vector(p2))

        return self.edge(val, tag, forConstruction)

    @segment.register
    def segment(
        self: T, p2: Point, tag: Optional[str] = None, forConstruction: bool = False
    ) -> T:

        p1 = self._endPoint()
        val = Edge.makeLine(p1, Vector(p2))

        return self.edge(val, tag, forConstruction)

    @segment.register
    def segment(
        self: T,
        l: Real,
        a: Real,
        tag: Optional[str] = None,
        forConstruction: bool = False,
    ) -> T:

        p1 = self._endPoint()
        d = Vector(l * cos(radians(a)), l * sin(radians(a)))
        val = Edge.makeLine(p1, p1 + d)

        return self.edge(val, tag, forConstruction)

    @multimethod
    def arc(
        self: T,
        p1: Point,
        p2: Point,
        p3: Point,
        tag: Optional[str] = None,
        forConstruction: bool = False,
    ) -> T:
        """
        Construct an arc starting at p1, through p2, ending at p3
        """

        val = Edge.makeThreePointArc(Vector(p1), Vector(p2), Vector(p3))

        return self.edge(val, tag, forConstruction)

    @arc.register
    def arc(
        self: T,
        p2: Point,
        p3: Point,
        tag: Optional[str] = None,
        forConstruction: bool = False,
    ) -> T:

        p1 = self._endPoint()
        val = Edge.makeThreePointArc(Vector(p1), Vector(p2), Vector(p3))

        return self.edge(val, tag, forConstruction)

    @arc.register
    def arc(
        self: T,
        c: Point,
        r: Real,
        a: Real,
        da: Real,
        tag: Optional[str] = None,
        forConstruction: bool = False,
    ) -> T:

        if abs(da) >= 360:
            val = Edge.makeCircle(r, Vector(c), angle1=a, angle2=a, orientation=da > 0)
        else:
            p0 = Vector(c)
            p1 = p0 + r * Vector(cos(radians(a)), sin(radians(a)))
            p2 = p0 + r * Vector(cos(radians(a + da / 2)), sin(radians(a + da / 2)))
            p3 = p0 + r * Vector(cos(radians(a + da)), sin(radians(a + da)))
            val = Edge.makeThreePointArc(p1, p2, p3)

        return self.edge(val, tag, forConstruction)

    @multimethod
    def spline(
        self: T,
        pts: Iterable[Point],
        tangents: Optional[Iterable[Point]],
        periodic: bool,
        tag: Optional[str] = None,
        forConstruction: bool = False,
    ) -> T:
        """
        Construct a spline edge.
        """

        val = Edge.makeSpline(
            [Vector(*p) for p in pts],
            [Vector(*t) for t in tangents] if tangents else None,
            periodic,
        )

        return self.edge(val, tag, forConstruction)

    @spline.register
    def spline(
        self: T,
        pts: Iterable[Point],
        tag: Optional[str] = None,
        forConstruction: bool = False,
    ) -> T:

        return self.spline(pts, None, False, tag, forConstruction)

    def close(self: T, tag: Optional[str] = None) -> T:
        """
        Connect last edge to the first one.
        """

        self.segment(self._endPoint(), self._startPoint(), tag)

        return self

    def assemble(self: T, mode: Modes = "a", tag: Optional[str] = None) -> T:
        """
        Assemble edges into faces.
        """

        return self.face(
            (e for e in self._edges if not e.forConstruction), 0, mode, tag
        )

    # constraints
    @multimethod
    def constrain(self: T, tag: str, constraint: ConstraintKind, arg: Any) -> T:
        """
        Add a constraint.
        """

        self._constraints.append(
            Constraint((tag,), (self._tags[tag][0],), constraint, arg)
        )

        return self

    @constrain.register
    def constrain(
        self: T, tag1: str, tag2: str, constraint: ConstraintKind, arg: Any
    ) -> T:

        self._constraints.append(
            Constraint(
                (tag1, tag2),
                (self._tags[tag1][0], self._tags[tag2][0]),
                constraint,
                arg,
            )
        )

        return self

    def solve(self: T) -> T:
        """
        Solve current constraints and update edge positions.
        """

        entities = []  # list with all degrees of freedom
        e2i = {}  # mapping from tags to indices of entities
        geoms = []  # geometry types

        # fill entities, e2i and geoms
        for i, (k, v) in enumerate(
            filter(lambda kv: isinstance(kv[1][0], Edge), self._tags.items())
        ):

            v0 = tcast(Edge, v[0])

            # dispatch on geom type
            if v0.geomType() == "LINE":
                p1 = v0.startPoint()
                p2 = v0.endPoint()
                ent: DOF = (p1.x, p1.y, p2.x, p2.y)

            elif v0.geomType() == "CIRCLE":
                p = v0.arcCenter()
                p1 = v0.startPoint() - p
                p2 = v0.endPoint() - p
                pm = v0.positionAt(0.5) - p

                a1 = Vector(0, 1).getSignedAngle(p1)
                a2 = p1.getSignedAngle(p2)
                a3 = p1.getSignedAngle(pm)
                if a3 > 0 and a2 < 0:
                    a2 += 2 * pi
                elif a3 < 0 and a2 > 0:
                    a2 -= 2 * pi
                radius = v0.radius()
                ent = (p.x, p.y, radius, a1, a2)

            else:
                continue

            entities.append(ent)
            e2i[k] = i
            geoms.append(v0.geomType())

        # build the POD constraint list
        constraints = []
        for c in self._constraints:
            ix = (e2i[c.tags[0]], e2i[c.tags[1]] if len(c.tags) == 2 else None)
            constraints.append((ix, c.kind, c.param))

        # optimize
        solver = SketchConstraintSolver(entities, constraints, geoms)
        res, self._solve_status = solver.solve()
        self._solve_status["x"] = res

        # translate back the solution - update edges
        for g, (k, i) in zip(geoms, e2i.items()):
            el = res[i]

            # dispatch on geom type
            if g == "LINE":
                p1 = Vector(el[0], el[1])
                p2 = Vector(el[2], el[3])
                e = Edge.makeLine(p1, p2)
            elif g == "CIRCLE":
                p1 = Vector(*arc_first(el))
                p2 = Vector(*arc_point(el, 0.5))
                p3 = Vector(*arc_last(el))
                e = Edge.makeThreePointArc(p1, p2, p3)

            # overwrite the low level object
            self._tags[k][0].wrapped = e.wrapped

        return self

    # misc

    def copy(self: T) -> T:
        """
        Create a partial copy of the sketch.
        """

        rv = self.__class__()
        rv._faces = self._faces.copy()

        return rv

    def moved(self: T, loc: Location) -> T:
        """
        Create a partial copy of the sketch with moved _faces.
        """

        rv = self.__class__()
        rv._faces = self._faces.moved(loc)

        return rv

    def located(self: T, loc: Location) -> T:
        """
        Create a partial copy of the sketch with a new location.
        """

        rv = self.__class__(locs=(loc,))
        rv._faces = self._faces.copy()

        return rv

    def finalize(self) -> Any:
        """
        Finish sketch construction and return the parent
        """

        return self.parent
