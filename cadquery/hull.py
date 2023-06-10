from typing import List, Tuple, Union, Iterable, Set
from math import pi, sin, cos, atan2, sqrt, inf, degrees
from numpy import lexsort, argmin, argmax

from .occ_impl.shapes import Edge, Wire
from .occ_impl.geom import Vector


"""
Convex hull for line segments and circular arcs based on
Yue, Y., Murray, J. L., Corney, J. R., & Clark, D. E. R. (1999).
Convex hull of a planar set of straight and circular line segments. Engineering Computations.

"""

Arcs = List["Arc"]
Points = List["Point"]
Entity = Union["Arc", "Point"]
Hull = List[Union["Arc", "Point", "Segment"]]


class Point:

    x: float
    y: float

    def __init__(self, x: float, y: float):

        self.x = x
        self.y = y

    def __repr__(self):

        return f"( {self.x},{self.y} )"

    def __hash__(self):

        return hash((self.x, self.y))

    def __eq__(self, other):

        return (self.x, self.y) == (other.x, other.y)


class Segment:

    a: Point
    b: Point

    def __init__(self, a: Point, b: Point):

        self.a = a
        self.b = b


class Arc:

    c: Point
    s: Point
    e: Point
    r: float
    a1: float
    a2: float
    ac: float

    def __init__(self, c: Point, r: float, a1: float, a2: float):

        self.c = c
        self.r = r
        self.a1 = a1
        self.a2 = a2

        self.s = Point(c.x + r * cos(a1), c.y + r * sin(a1))
        self.e = Point(c.x + r * cos(a2), c.y + r * sin(a2))
        self.ac = 2 * pi - (a1 - a2)


def atan2p(x, y):

    rv = atan2(y, x)

    if rv < 0:
        rv = (2 * pi + rv) % (2 * pi)

    return rv


def convert_and_validate(edges: Iterable[Edge]) -> Tuple[List[Arc], List[Point]]:

    arcs: Set[Arc] = set()
    points: Set[Point] = set()

    for e in edges:
        gt = e.geomType()

        if gt == "LINE":
            p1 = e.startPoint()
            p2 = e.endPoint()

            points.update((Point(p1.x, p1.y), Point(p2.x, p2.y)))

        elif gt == "CIRCLE":
            c = e.arcCenter()
            r = e.radius()
            a1, a2 = e._bounds()

            arc = Arc(Point(c.x, c.y), r, a1, a2)
            arcs.add(arc)
            points.update((arc.s, arc.e))

        else:
            raise ValueError(f"Unsupported geometry {gt}")

    return list(arcs), list(points)


def select_lowest_point(points: Points) -> Tuple[Point, int]:

    x = []
    y = []

    for p in points:
        x.append(p.x)
        y.append(p.y)

    # select the lowest point
    ixs = lexsort((x, y))

    return points[ixs[0]], ixs[0]


def select_lowest_arc(arcs: Arcs) -> Tuple[Point, Arc]:

    x = []
    y = []

    for a in arcs:

        if a.a1 < 1.5 * pi and a.a2 > 1.5 * pi:
            x.append(a.c.x)
            y.append(a.c.y - a.r)
        else:
            p, _ = select_lowest_point([a.s, a.e])
            x.append(p.x)
            y.append(p.y)

    ixs = lexsort((x, y))

    return Point(x[ixs[0]], y[ixs[0]]), arcs[ixs[0]]


def select_lowest(arcs: Arcs, points: Points) -> Entity:

    rv: Entity

    p_lowest = select_lowest_point(points) if points else None
    a_lowest = select_lowest_arc(arcs) if arcs else None

    if p_lowest is None and a_lowest:
        rv = a_lowest[1]
    elif p_lowest is not None and a_lowest is None:
        rv = p_lowest[0]
    elif p_lowest and a_lowest:
        _, ix = select_lowest_point([p_lowest[0], a_lowest[0]])
        rv = p_lowest[0] if ix == 0 else a_lowest[1]
    else:
        raise ValueError("No entities specified")

    return rv


def pt_pt(p1: Point, p2: Point) -> Tuple[float, Segment]:

    angle = 0

    dx, dy = p2.x - p1.x, p2.y - p1.y

    if (dx, dy) != (0, 0):
        angle = atan2p(dx, dy)

    return angle, Segment(p1, p2)


def _pt_arc(p: Point, a: Arc) -> Tuple[float, float, float, float]:

    x, y = p.x, p.y

    r = a.r
    xc, yc = a.c.x, a.c.y
    dx, dy = x - xc, y - yc
    l = sqrt(dx ** 2 + dy ** 2)
    ld = l ** 2 - r ** 2
    if (ld < 0.001):
        return x, y, x, y

    x1 = r ** 2 / l ** 2 * dx - r / l ** 2 * sqrt(l ** 2 - r ** 2) * dy + xc
    y1 = r ** 2 / l ** 2 * dy + r / l ** 2 * sqrt(l ** 2 - r ** 2) * dx + yc
    x2 = r ** 2 / l ** 2 * dx + r / l ** 2 * sqrt(l ** 2 - r ** 2) * dy + xc
    y2 = r ** 2 / l ** 2 * dy - r / l ** 2 * sqrt(l ** 2 - r ** 2) * dx + yc

    return x1, y1, x2, y2

def pt_arc(angle: float, p: Point, a: Arc) -> Tuple[float, Segment]:

    x, y = p.x, p.y
    x1, y1, x2, y2 = _pt_arc(p, a)

    if ((x1, y1) == (x2, y2)):
        return inf, Segment(Point(inf, inf), Point(inf, inf))

    angles = atan2p(x1 - x, y1 - y), atan2p(x2 - x, y2 - y)
    points = Point(x1, y1), Point(x2, y2)
    ix = int(argmin([a + 2*pi if a < angle else a for a in angles]))

    return angles[ix], Segment(p, points[ix])


def arc_pt(angle: float, a: Arc, p: Point) -> Tuple[float, Segment]:

    x, y = p.x, p.y
    x1, y1, x2, y2 = _pt_arc(p, a)

    if ((x1, y1) == (x2, y2)):
        return inf, Segment(Point(inf, inf), Point(inf, inf))

    angles = atan2p(x - x1, y - y1), atan2p(x - x2, y - y2)
    points = Point(x1, y1), Point(x2, y2)

    ix = int(argmax([a + 2*pi if a < angle else a for a in angles]))

    return angles[ix], Segment(points[ix], p)


def arc_arc(angle: float, a1: Arc, a2: Arc) -> Tuple[float, Segment]:

    r1 = a1.r
    xc1, yc1 = a1.c.x, a1.c.y

    r2 = a2.r
    xc2, yc2 = a2.c.x, a2.c.y

    # construct tangency points for a related point-circle problem
    if r1 > r2:
        arc_tmp = Arc(a1.c, r1 - r2, a1.a1, a1.a2)
        xtmp1, ytmp1, xtmp2, ytmp2 = _pt_arc(a2.c, arc_tmp)

        delta_r = r1 - r2

        dx1 = (xtmp1 - xc1) / delta_r
        dy1 = (ytmp1 - yc1) / delta_r

        dx2 = (xtmp2 - xc1) / delta_r
        dy2 = (ytmp2 - yc1) / delta_r

    elif r1 < r2:
        arc_tmp = Arc(a2.c, r2 - r1, a2.a1, a2.a2)
        xtmp1, ytmp1, xtmp2, ytmp2 = _pt_arc(a1.c, arc_tmp)

        delta_r = r2 - r1

        dx1 = (xtmp1 - xc2) / delta_r
        dy1 = (ytmp1 - yc2) / delta_r

        dx2 = (xtmp2 - xc2) / delta_r
        dy2 = (ytmp2 - yc2) / delta_r

    else:
        dx = xc2 - xc1
        dy = yc2 - yc1
        l = sqrt(dx ** 2 + dy ** 2)

        dx /= l
        dy /= l

        dx1 = -dy
        dy1 = dx
        dx2 = dy
        dy2 = -dx

    # construct the tangency points and angles
    x11 = xc1 + dx1 * r1
    y11 = yc1 + dy1 * r1
    x12 = xc1 + dx2 * r1
    y12 = yc1 + dy2 * r1

    x21 = xc2 + dx1 * r2
    y21 = yc2 + dy1 * r2
    x22 = xc2 + dx2 * r2
    y22 = yc2 + dy2 * r2

    a1_out = atan2p(x21 - x11, y21 - y11)
    a2_out = atan2p(x22 - x12, y22 - y12)

    # select the feasible angle
    a11 = (atan2p(x11 - xc1, y11 - yc1) + pi / 2) % (2 * pi)
    a21 = (atan2p(x12 - xc1, y12 - yc1) + pi / 2) % (2 * pi)

    ix = int(argmin((abs(a11 - a1_out), abs(a21 - a2_out))))
    angles = (a1_out, a2_out)
    segments = (
        Segment(Point(x11, y11), Point(x21, y21)),
        Segment(Point(x12, y12), Point(x22, y22)),
    )

    segment_angle = atan2p(segments[ix].b.x - xc2, segments[ix].b.y - yc2)
    if (segment_angle < a2.a1 or segment_angle > a2.a2):
        return inf, Segment(Point(inf, inf), Point(inf, inf))

    return angles[ix], segments[ix]


def get_angle(angle: float, current: Entity, e: Entity) -> Tuple[float, Segment]:
    def center(e: Entity):
        if isinstance(e, Point):
            return e
        return e.c
    if center(current) == center(e):
        if (isinstance(current, Arc) and isinstance(e, Arc)):
            if (current.s == e.e and not e.s == current.e):
                return pt_pt(current.e, e.s)
            if (e.s == current.e and not current.s == e.e):
                return (current.a2 + pi) % (2 * pi), Segment(Point(inf, inf), Point(inf, inf))
        return inf, Segment(Point(inf, inf), Point(inf, inf))

    if isinstance(current, Point):
        if isinstance(e, Point):
            return pt_pt(current, e)
        else:
            return pt_arc(angle, current, e)
    else:
        if isinstance(e, Point):
            return arc_pt(angle, current, e)
        else:
            return arc_arc(angle, current, e)


def update_hull(
    current_e: Entity,
    ix: int,
    entities: List[Entity],
    angles: List[float],
    segments: List[Segment],
    hull: Hull,
) -> Tuple[Entity, float, bool]:

    next_e = entities[ix]
    connecting_seg = segments[ix]

    if isinstance(next_e, Point):
        entities.pop(ix)

    hull.extend((connecting_seg, next_e))

    return next_e, angles[ix], next_e is hull[0]


def finalize_hull(hull: Hull) -> Wire:

    rv = []

    for el_p, el, el_n in zip(hull, hull[1:], hull[2:]):

        if isinstance(el, Segment):
            if (not inf in [el.a.x, el.a.y, el.b.x, el.b.y]):
                rv.append(Edge.makeLine(Vector(el.a.x, el.a.y), Vector(el.b.x, el.b.y)))
        elif (
            isinstance(el, Arc)
            and isinstance(el_p, Segment)
            and isinstance(el_n, Segment)
        ):
            a1 = degrees(atan2p(el_p.b.x - el.c.x, el_p.b.y - el.c.y))
            a2 = degrees(atan2p(el_n.a.x - el.c.x, el_n.a.y - el.c.y))

            if (a1 != a2):
                rv.append(
                    Edge.makeCircle(el.r, Vector(el.c.x, el.c.y), angle1=a1, angle2=a2)
                )

    el1 = hull[1]
    if isinstance(el, Segment) and isinstance(el_n, Arc) and isinstance(el1, Segment):
        a1 = degrees(atan2p(el.b.x - el_n.c.x, el.b.y - el_n.c.y))
        a2 = degrees(atan2p(el1.a.x - el_n.c.x, el1.a.y - el_n.c.y))

        rv.append(
            Edge.makeCircle(el_n.r, Vector(el_n.c.x, el_n.c.y), angle1=a1, angle2=a2)
        )

    return Wire.assembleEdges(rv)


def find_hull(edges: Iterable[Edge]) -> Wire:

    # initialize the hull
    rv: Hull = []

    # split into arcs and points
    arcs, points = convert_and_validate(edges)

    # select the starting element
    start = select_lowest(arcs, points)
    rv.append(start)

    # initialize
    entities: List[Entity] = []
    entities.extend(arcs)
    entities.extend(points)

    current_e = start
    current_angle = 0.0
    finished = False

    iterations = 0

    # march around
    while not finished and iterations < len(entities):
        iterations += 1

        angles = []
        segments = []

        for e in entities:
            angle, segment = get_angle(current_angle, current_e, e)
            angles.append(angle if angle >= current_angle else inf)
            segments.append(segment)

        next_ix = int(argmin(angles))
        current_e, current_angle, finished = update_hull(
            current_e, next_ix, entities, angles, segments, rv
        )

    # convert back to Edges and return
    return finalize_hull(rv)
