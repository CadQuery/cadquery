from typing import Union, Optional, List, Dict, Callable, overload, Tuple, Iterable, Any
from typing_extensions import Literal

from .occ_impl.shapes import Shape, Face, Edge, Wire
from .occ_impl.geom import Location, Vector

Modes = Literal["a", "s", "o", "c"]
Point = Union[Vector, Tuple[float, float]]


class Sketch(object):

    parent: Any

    faces: List[Face]
    wires: List[Wire]
    edges: List[Edge]

    selection: List[Union[Shape, Location]]

    tags: Dict[str, Shape]

    def __init__(self, parent: Any = None):

        self.parent = parent

        self.faces = []
        self.wires = []
        self.edges = []

        self.selection = []
        self.tags = {}

    # face construction

    def rect(
        self,
        w: float,
        h: float,
        angle: float = 0,
        mode: Modes = "a",
        tag: Optional[str] = None,
    ) -> "Sketch":
        ...

    def circle(
        self, r: float, mode: Modes = "a", tag: Optional[str] = None
    ) -> "Sketch":
        ...

    def ellipse(
        self,
        a1: float,
        a2: float,
        angle: float = 0,
        mode: Modes = "a",
        tag: Optional[str] = None,
    ) -> "Sketch":
        ...

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
        ...

    def slot(
        self,
        w: float,
        h: float,
        angle: float = 0,
        mode: Modes = "a",
        tag: Optional[str] = None,
    ) -> "Sketch":
        ...

    @overload
    def polygon(
        self, r: float, n: int, mode: Modes = "a", tag: Optional[str] = None
    ) -> "Sketch":
        ...

    @overload
    def polygon(
        self,
        pts: Iterable[Point],
        angle: float = 0,
        mode: Modes = "a",
        tag: Optional[str] = None,
    ) -> "Sketch":
        ...

    # distribute locations

    def rarray(self, xs: float, ys: float, nx: int, ny: int) -> "Sketch":
        ...

    def parray(
        self, r: float, a1: float, a2: float, n: int, rotate: bool = True
    ) -> "Sketch":
        ...

    def distribute(self, n: int, rotate: bool = True) -> "Sketch":
        ...

    def push(self, locs: Iterable[Location]) -> "Sketch":
        ...

    def each(
        self, callback: Callable[[Location], "Sketch"], mode: Modes = "a"
    ) -> "Sketch":
        ...

    # modifiers

    def offset(
        self, d: float, mode: Modes = "a", tag: Optional[str] = None
    ) -> "Sketch":
        ...

    def fillet(self, d: float) -> "Sketch":
        ...

    def chamfer(self, d: float) -> "Sketch":
        ...

    # selection

    def faces(self, s: str) -> "Sketch":
        ...

    def wires(self, s: str) -> "Sketch":
        ...

    def edges(self, s: str) -> "Sketch":
        ...

    def vertices(self, s: str) -> "Sketch":
        ...

    def reset(self) -> "Sketch":

        self.selection = []
        return self

    def delete(self) -> "Sketch":

        for obj in self.selection:
            if isinstance(obj, Face):
                self.faces.remove(obj)
            elif isinstance(obj, Wire):
                self.wires.remove(obj)
            else:
                self.edges.remove(obj)

        self.selection = []

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

    # misc

    def finalize(self) -> Any:

        return self.parent
