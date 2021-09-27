from typing import (
    Union,
    Optional,
    List,
    Dict,
    Callable,
    Tuple,
    Iterable,
    Any,
    Sequence,
    cast as tcast,
)
from typing_extensions import Literal
from math import tan, sin, cos, pi, radians, degrees
from itertools import product, chain
from multimethod import multimethod
from typish import instance_of, get_type

from .hull import find_hull
from .selectors import StringSyntaxSelector

from .occ_impl.shapes import Shape, Face, Edge, Wire, Compound, Vertex, edgesToWires
from .occ_impl.geom import Location, Vector
from .occ_impl.sketch_solver import (
    SketchConstraintSolver,
    ConstraintKind,
    ConstraintInvariants,
    DOF,
)

Modes = Literal["a", "s", "i"]
Real = Union[float, int]
Point = Union[Vector, Tuple[Real, Real]]


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

        arity, types, param_type = ConstraintInvariants[kind]

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

        # if all is fine store everything
        self.tags = tags
        self.args = args
        self.kind = kind
        self.param = param


class Sketch(object):

    parent: Any

    _faces: Compound
    _wires: List[Wire]
    _edges: List[Edge]

    _selection: List[Union[Shape, Location]]
    _constraints: List[Constraint]

    _tags: Dict[str, Sequence[Union[Shape, Location]]]

    _solve_status: Optional[Dict[str, Any]]

    def __init__(self, parent: Any = None):

        self.parent = parent

        self._faces = Compound.makeCompound(())
        self._wires = []
        self._edges = []

        self._selection = []
        self._constraints = []

        self._tags = {}

        self._solve_status = None

    def _tag(self, val: Sequence[Union[Shape, Location]], tag: str):

        self._tags[tag] = val

    # face construction
    def face(
        self,
        b: Union[Wire, Iterable[Edge]],
        angle: Real = 0,
        mode: Modes = "a",
        tag: Optional[str] = None,
        ignore_selection: bool = False,
    ) -> "Sketch":

        if isinstance(b, Wire):
            res = Face.makeFromWires(b)
        elif isinstance(b, Iterable):
            wires = edgesToWires(b)
            res = Face.makeFromWires(*(wires[0], wires[1:]))
        else:
            raise ValueError(f"Unsupported argument {b}")

        res = res.rotate(Vector(), Vector(0, 0, 1), angle)

        return self.each(lambda l: res.located(l), mode, tag, ignore_selection)

    def rect(
        self,
        w: Real,
        h: Real,
        angle: Real = 0,
        mode: Modes = "a",
        tag: Optional[str] = None,
    ) -> "Sketch":

        res = Face.makePlane(w, h).rotate(Vector(), Vector(0, 0, 1), angle)

        return self.each(lambda l: res.located(l), mode, tag)

    def circle(self, r: Real, mode: Modes = "a", tag: Optional[str] = None) -> "Sketch":

        res = Face.makeFromWires(Wire.makeCircle(r, Vector(), Vector(0, 0, 1)))

        return self.each(lambda l: res.located(l), mode, tag)

    def ellipse(
        self,
        a1: Real,
        a2: Real,
        angle: Real = 0,
        mode: Modes = "a",
        tag: Optional[str] = None,
    ) -> "Sketch":

        res = Face.makeFromWires(
            Wire.makeEllipse(
                a1, a2, Vector(), Vector(0, 0, 1), Vector(1, 0, 0), rotation_angle=angle
            )
        )

        return self.each(lambda l: res.located(l), mode, tag)

    def trapezoid(
        self,
        w: Real,
        h: Real,
        a1: Real,
        a2: Optional[float] = None,
        angle: Real = 0,
        mode: Modes = "a",
        tag: Optional[str] = None,
    ) -> "Sketch":

        v1 = Vector(-w / 2, -h / 2)
        v2 = Vector(w / 2, -h / 2)
        v3 = Vector(-w / 2 + h / tan(radians(a1)), h / 2)
        v4 = Vector(w / 2 - h / tan(radians(a2) if a2 else radians(a1)), h / 2)

        return self.polygon((v1, v2, v4, v3, v1), angle, mode, tag)

    def slot(
        self,
        w: Real,
        h: Real,
        angle: Real = 0,
        mode: Modes = "a",
        tag: Optional[str] = None,
    ) -> "Sketch":

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
        self,
        r: Real,
        n: int,
        angle: Real = 0,
        mode: Modes = "a",
        tag: Optional[str] = None,
    ) -> "Sketch":

        pts = [
            Vector(r * sin(i * 2 * pi / n), r * cos(i * 2 * pi / n))
            for i in range(n + 1)
        ]

        return self.polygon(pts, angle, mode, tag)

    def polygon(
        self,
        pts: Iterable[Point],
        angle: Real = 0,
        mode: Modes = "a",
        tag: Optional[str] = None,
    ) -> "Sketch":

        w = Wire.makePolygon(p if isinstance(p, Vector) else Vector(*p) for p in pts)

        return self.face(w, angle, mode, tag)

    # distribute locations

    def rarray(self, xs: Real, ys: Real, nx: int, ny: int) -> "Sketch":

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
            (el * l if isinstance(el, Location) else Location(el.Center())) * l
            for l in locs
            for el in selection
        )

    def parray(
        self, r: Real, a1: Real, a2: Real, n: int, rotate: bool = True
    ) -> "Sketch":

        if n < 1:
            raise ValueError(f"At least 1 elements required, requested {n}")

        x = r * sin(radians(a1))
        y = r * cos(radians(a1))

        if rotate:
            loc = Location(Vector(x, y), Vector(0, 0, 1), -a1)
        else:
            loc = Location(Vector(x, y))

        locs = [loc]

        angle = (a2 - a1) / (n - 1)

        for i in range(1, n):
            phi = a1 + (angle * i)
            x = r * sin(radians(phi))
            y = r * cos(radians(phi))

            if rotate:
                loc = Location(Vector(x, y), Vector(0, 0, 1), -phi)
            else:
                loc = Location(Vector(x, y))

            locs.append(loc)

        if self._selection:
            selection: Sequence[Union[Shape, Location, Vector]] = self._selection
        else:
            selection = [Vector()]

        return self.push(
            (el * l if isinstance(el, Location) else Location(el.Center())) * l
            for l in locs
            for el in selection
        )

    def distribute(
        self, n: int, start: Real = 0, stop: Real = 1, rotate: bool = True
    ) -> "Sketch":

        if not self._selection:
            raise ValueError("Nothing selected to distirbute over")

        params = [start + i * (stop - start) / n for i in range(n + 1)]

        locs = []
        for el in self._selection:
            if isinstance(el, (Wire, Edge)):
                if rotate:
                    locs.extend(el.locations(params, planar=True))
                else:
                    locs.extend(Location(v) for v in el.positions(params))
            else:
                raise ValueError(f"Unsupported selection: {el}")

        return self.push(locs)

    def push(
        self, locs: Iterable[Union[Location, Point]], tag: Optional[str] = None,
    ) -> "Sketch":

        self._selection = [
            l if isinstance(l, Location) else Location(Vector(l)) for l in locs
        ]

        if tag:
            self._tag(self._selection[:], tag)

        return self

    def each(
        self,
        callback: Callable[[Location], Union[Face, "Sketch"]],
        mode: Modes = "a",
        tag: Optional[str] = None,
        ignore_selection: bool = False,
    ) -> "Sketch":

        res: List[Face] = []

        if self._selection and not ignore_selection:
            for el in self._selection:
                if isinstance(el, Location):
                    loc = el
                elif isinstance(el, Shape):
                    loc = Location(el.Center())
                else:
                    raise ValueError(f"Invalid selection: {el}")

                tmp = callback(loc)
                if isinstance(tmp, Sketch):
                    res.extend(tmp._faces.Faces())
                else:
                    res.append(tmp)
        else:
            tmp = callback(Location())
            if isinstance(tmp, Sketch):
                res.extend(tmp._faces.Faces())
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
    def hull(self, mode: Modes = "a", tag: Optional[str] = None) -> "Sketch":

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

    def offset(self, d: Real, mode: Modes = "a", tag: Optional[str] = None) -> "Sketch":

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

    def fillet(self, d: Real) -> "Sketch":

        f2v = self._matchFacesToVertices()

        self._faces = Compound.makeCompound(
            k.fillet2D(d, v) if v else k for k, v in f2v.items()
        )

        return self

    def chamfer(self, d: Real) -> "Sketch":

        f2v = self._matchFacesToVertices()

        self._faces = Compound.makeCompound(
            k.chamfer2D(d, v) if v else k for k, v in f2v.items()
        )

        return self

    def clean(self) -> "Sketch":

        self._faces = self._faces.clean()

        return self

    # selection

    def _select(
        self,
        s: Optional[str],
        kind: Literal["Faces", "Wires", "Edges", "Vertices"],
        tag: Optional[str] = None,
    ) -> "Sketch":

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

        self._selection = StringSyntaxSelector(s).filter(rv) if s else rv

        return self

    def tag(self, tag: str) -> "Sketch":

        self._tags[tag] = list(self._selection)

        return self

    def select(self, *tags: str) -> "Sketch":

        self._selection = []

        for tag in tags:
            self._selection.extend(self._tags[tag])

        return self

    def faces(self, s: Optional[str] = None, tag: Optional[str] = None) -> "Sketch":

        return self._select(s, "Faces", tag)

    def wires(self, s: Optional[str] = None, tag: Optional[str] = None) -> "Sketch":

        return self._select(s, "Wires", tag)

    def edges(self, s: Optional[str] = None, tag: Optional[str] = None) -> "Sketch":

        return self._select(s, "Edges", tag)

    def vertices(self, s: Optional[str] = None, tag: Optional[str] = None) -> "Sketch":

        return self._select(s, "Vertices", tag)

    def reset(self) -> "Sketch":

        self._selection = []
        return self

    def delete(self) -> "Sketch":

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
        self, val: Edge, tag: Optional[str] = None, forConstruction: bool = False
    ) -> "Sketch":

        val.forConstruction = forConstruction
        self._edges.append(val)

        if tag:
            self._tag([val], tag)

        return self

    @multimethod
    def segment(
        self,
        p1: Point,
        p2: Point,
        tag: Optional[str] = None,
        forConstruction: bool = False,
    ) -> "Sketch":

        val = Edge.makeLine(Vector(p1), Vector(p2))

        return self.edge(val, tag, forConstruction)

    @segment.register
    def segment(
        self, p2: Point, tag: Optional[str] = None, forConstruction: bool = False
    ) -> "Sketch":

        p1 = self._endPoint()
        val = Edge.makeLine(p1, Vector(p2))

        return self.edge(val, tag, forConstruction)

    @segment.register
    def segment(
        self,
        l: Real,
        a: Real,
        tag: Optional[str] = None,
        forConstruction: bool = False,
    ) -> "Sketch":

        p1 = self._endPoint()
        d = Vector(l * cos(radians(a)), l * sin(radians(a)))
        val = Edge.makeLine(p1, p1 + d)

        return self.edge(val, tag, forConstruction)

    @multimethod
    def arc(
        self,
        p1: Point,
        p2: Point,
        p3: Point,
        tag: Optional[str] = None,
        forConstruction: bool = False,
    ) -> "Sketch":

        val = Edge.makeThreePointArc(Vector(p1), Vector(p2), Vector(p3))

        return self.edge(val, tag, forConstruction)

    @arc.register
    def arc(
        self,
        p2: Point,
        p3: Point,
        tag: Optional[str] = None,
        forConstruction: bool = False,
    ) -> "Sketch":

        p1 = self._endPoint()
        val = Edge.makeThreePointArc(Vector(p1), Vector(p2), Vector(p3))

        return self.edge(val, tag, forConstruction)

    @arc.register
    def arc(
        self,
        c: Point,
        r: Real,
        a1: Real,
        a2: Real,
        tag: Optional[str] = None,
        forConstruction: bool = False,
    ) -> "Sketch":

        val = Edge.makeCircle(r, Vector(c), angle1=a1, angle2=a2)

        return self.edge(val, tag, forConstruction)

    @multimethod
    def spline(
        self,
        pts: Iterable[Point],
        tangents: Optional[Iterable[Point]],
        periodic: bool,
        tag: Optional[str] = None,
        forConstruction: bool = False,
    ) -> "Sketch":

        val = Edge.makeSpline(
            [Vector(*p) for p in pts],
            [Vector(*t) for t in tangents] if tangents else None,
            periodic,
        )

        return self.edge(val, tag, forConstruction)

    @spline.register
    def spline(
        self,
        pts: Iterable[Point],
        tag: Optional[str] = None,
        forConstruction: bool = False,
    ) -> "Sketch":

        return self.spline(pts, None, False, tag, forConstruction)

    def close(self, tag: Optional[str] = None) -> "Sketch":

        self.segment(self._endPoint(), self._startPoint(), tag)

        return self

    def assemble(self, mode: Modes = "a", tag: Optional[str] = None) -> "Sketch":

        return self.face(
            (e for e in self._edges if not e.forConstruction), 0, mode, tag
        )

    # constraints
    @multimethod
    def constrain(self, tag: str, constraint: ConstraintKind, arg: Any) -> "Sketch":

        self._constraints.append(
            Constraint((tag,), (self._tags[tag][0],), constraint, arg)
        )

    @constrain.register
    def constrain(
        self, tag1: str, tag2: str, constraint: ConstraintKind, arg: Any
    ) -> "Sketch":

        self._constraints.append(
            Constraint(
                (tag1, tag2),
                (self._tags[tag1][0], self._tags[tag2][0]),
                constraint,
                arg,
            )
        )

    def solve(self) -> "Sketch":

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
                a1 = v0.paramAt(0)
                a2 = v0.paramAt(1)
                radius = v0.radius()
                ent = (p.x, p.y, a1, a2, radius)

            else:
                continue

            entities.append(ent)
            e2i[k] = i
            geoms.append(v0.geomType())

        # build the POD constraint list
        constraints = []
        for c in self._constraints:
            ix = (e2i[c.tags[0]], e2i[c.tags[1]] if len(c.tags) == 2 else None)
            constraints.append(
                (ix, c.kind, entities[ix[0]] if c.kind == "Fixed" else c.param,)
            )

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
                p = Vector(el[0], el[1])
                r = el[2]
                a1 = el[3]
                a2 = el[4]
                e = Edge.makeCircle(r, p, angle1=degrees(a2), angle2=degrees(a1))

            # overwrite the low level object
            self._tags[k][0].wrapped = e.wrapped

        return self

    # misc

    def finalize(self) -> Any:

        return self.parent
