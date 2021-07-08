from typing import Union, Optional, List, Dict, Callable, overload, Tuple, Iterable, Any
from typing_extensions import Literal
from math import tan, sin, cos, pi, radians
from itertools import product

from .selectors import StringSyntaxSelector

from .occ_impl.shapes import Shape, Face, Edge, Wire, Compound
from .occ_impl.geom import Location, Vector

Modes = Literal["a", "s"]
Point = Union[Vector, Tuple[float, float]]


class Sketch(object):

    parent: Any

    _faces: Compound
    _wires: List[Wire]
    _edges: List[Edge]

    _selection: List[Union[Shape, Location]]

    _tags: Dict[str, Shape]

    def __init__(self, parent: Any = None):

        self.parent = parent

        self._faces = Compound.makeCompound(())
        self._wires = []
        self._edges = []

        self._selection = []
        self._tags = {}

    # face construction
    def face(
        self,
        b: Union[Wire, Iterable[Edge]],
        angle: float = 0,
        mode: Modes = "a",
        tag: Optional[str] = None,
    ) -> "Sketch":

        if isinstance(b, Wire):
            res = Face.makeFromWires(b)
        elif isinstance(b, Iterable):
            res = Face.makeFromWires(Wire.assembleEdges(b))
        else:
            raise ValueError(f"Unsupported argument {b}")

        res = res.rotate(Vector(), Vector(0, 0, 1), angle)

        return self.each(lambda l: res.located(l), mode, tag)

    def rect(
        self,
        w: float,
        h: float,
        angle: float = 0,
        mode: Modes = "a",
        tag: Optional[str] = None,
    ) -> "Sketch":

        res = Face.makePlane(w, h).rotate(Vector(), Vector(0, 0, 1), angle)

        return self.each(lambda l: res.located(l), mode, tag)

    def circle(
        self, r: float, mode: Modes = "a", tag: Optional[str] = None
    ) -> "Sketch":

        res = Face.makeFromWires(Wire.makeCircle(r, Vector(), Vector(0, 0, 1)))

        return self.each(lambda l: res.located(l), mode, tag)

    def ellipse(
        self,
        a1: float,
        a2: float,
        angle: float = 0,
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
        w: float,
        h: float,
        a1: float,
        a2: Optional[float] = None,
        angle: float = 0,
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
        w: float,
        h: float,
        angle: float = 0,
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

        w = Wire.assembleEdges((e1, e2, e3, e4))

        return self.face(w, angle, mode, tag)

    def regularPolygon(
        self,
        r: float,
        n: int,
        angle: float = 0,
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
        angle: float = 0,
        mode: Modes = "a",
        tag: Optional[str] = None,
    ) -> "Sketch":

        w = Wire.makePolygon(pts)

        return self.face(w, angle, mode, tag)

    # distribute locations

    def rarray(self, xs: float, ys: float, nx: int, ny: int) -> "Sketch":

        locs = []

        offset = Vector((nx - 1) * xs, (ny - 1) * ys) * 0.5
        for i, j in product(range(nx), range(ny)):
            locs.append(Location(Vector(i * xs, j * ys) - offset))

        selection = self._selection if self._selection else (Vector(),)

        return self.push(Location(el.Center()) * l for l in locs for el in selection)

    def parray(
        self, r: float, a1: float, a2: float, n: int, rotate: bool = True
    ) -> "Sketch":

        if n < 2:
            raise ValueError(f"At least 2 elements required, requested {n}")

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

        selection = self._selection if self._selection else (Vector(),)

        return self.push(Location(el.Center()) * l for l in locs for el in selection)

    def distribute(
        self, n: int, start: float = 0, stop: float = 1, rotate: bool = True
    ) -> "Sketch":

        params = [start + i * (stop - start) / (n - 1) for i in range(n)]

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

    def push(self, locs: Iterable[Location]) -> "Sketch":

        self._selection = list(locs)

        return self

    def each(
        self,
        callback: Callable[[Location], Union[Face, "Sketch"]],
        mode: Modes = "a",
        tag: Optional[str] = None,
    ) -> "Sketch":

        res: List[Union[Face, "Sketch"]] = []

        if self._selection:
            for el in self._selection:
                if isinstance(el, Location):
                    loc = el
                elif isinstance(el, Shape):
                    loc = Location(el.Center())
                else:
                    raise ValueError(f"Invalid selection: {el}")

                res.append(callback(loc))
        else:
            res.append(callback(Location()))

        if tag:
            self._tags[tag] = res

        if mode == "a":
            self._faces = self._faces.fuse(*res)
        elif mode == "s":
            self._faces = self._faces.cut(*res)
        elif mode == "c":
            if not tag:
                raise ValueError("No tag specified - the geometry will be unreachable")
        else:
            raise ValueError(f"Invalid mode: {mode}")

        return self

    # modifiers

    def offset(
        self, d: float, mode: Modes = "a", tag: Optional[str] = None
    ) -> "Sketch":

        rv = (el.offset2D(d) for el in self._selection if isinstance(el, Wire))

        for el in rv:
            self.face(el, mode=mode, tag=tag)

        return self

    def fillet(self, d: float) -> "Sketch":

        self._faces = Compound.makeCompound(
            el.fillet2D(d, self._selection) for el in self._faces
        )

        return self

    def chamfer(self, d: float) -> "Sketch":

        self._faces = Compound.makeCompound(
            el.chamfer2D(d, self._selection) for el in self._faces
        )

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
                rv.extend(getattr(el, kind)())
        else:
            rv.extend(getattr(self._faces, kind)())

        self._selection = StringSyntaxSelector(s).filter(rv) if s else rv

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
                self.faces.remove(obj)
            elif isinstance(obj, Wire):
                self.wires.remove(obj)
            else:
                self.edges.remove(obj)

        self._selection = []

        return self

    # edge based interface

    @overload
    def segment(self, p1: Point, p2: Point, tag: Optional[str] = None) -> "Sketch":
        ...

    @overload
    def segment(self, p2: Point, tag: Optional[str] = None) -> "Sketch":
        ...

    @overload
    def segment(self, l: float, a: float, tag: Optional[str] = None) -> "Sketch":
        ...

    @overload
    def arc(
        self, p1: Point, p2: Point, r: float, tag: Optional[str] = None
    ) -> "Sketch":
        ...

    @overload
    def arc(self, p2: Point, a: float, tag: Optional[str] = None) -> "Sketch":
        ...

    @overload
    def arc(
        self, c: Point, r: float, a1: float, a2: float, tag: Optional[str] = None
    ) -> "Sketch":
        ...

    def spline(self, pts: Iterable[Point], tag: Optional[str] = None) -> "Sketch":
        ...

    def close(self, tag: Optional[str] = None) -> "Sketch":
        ...

    def assemble(self, mode: Modes = "a", tag: Optional[str] = None) -> "Sketch":
        ...

    # constraints
    @overload
    def constrain(self, tag: str, constraint: str, arg: Any) -> "Sketch":
        ...

    @overload
    def constrain(self, tag1: str, tag2: str, constraint: str, arg: Any) -> "Sketch":
        ...

    def solve(self) -> "Sketch":
        ...

    # misc

    def finalize(self) -> Any:

        return self.parent
