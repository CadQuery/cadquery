from typing import Tuple, Union, Any, Callable, List, Optional, Literal, Iterable
from nptyping import NDArray as Array
from itertools import accumulate, chain
from math import sin, cos

from numpy import array
from numpy.linalg import norm
from scipy.optimize import minimize
from OCP.gp import gp_Vec2d

from .geom import Location
from .shapes import Geoms


SegmentDOF = Tuple[float, float, float, float]  # p1 p2
ArcDOF = Tuple[float, float, float, float, float]  # p r a1 a2
DOF = Union[SegmentDOF, ArcDOF]

ConstraintKind = Literal["Fixed", "Coincident", "Angle", "Length"]
Constraint = Tuple[Tuple[int, Optional[int]], ConstraintKind, Optional[Any]]


class SketchConstraintSolver(object):

    entities: List[DOF]
    constraints: List[Constraint]
    geoms: List[Geoms]
    ne: int
    nc: int
    ixs: List[int]

    def __init__(
        self,
        entities: Iterable[DOF],
        constraints: Iterable[Constraint],
        geoms: Iterable[Geoms],
    ):

        self.entities = list(entities)
        self.constraints = list(constraints)
        self.geoms = list(geoms)

        self.ne = len(entities)
        self.nc = len(self.constraints)

        # indices of x corresponding to the entities
        self.ixs = [0] + list(accumulate(len(e) for e in self.entities))

    def _cost(
        self,
    ) -> Tuple[
        Callable[[Array[(Any,), float]], float],
        Callable[[Array[(Any,), float]], Array[(Any,), float]],
    ]:
        def invalid_args(*t):

            return ValueError("Invalid argument types {t}")

        def arc_first(x):

            return array((x[0] + x[2] * sin(x[3]), x[1] + x[2] * cos(x[3])))

        def arc_last(x):

            return array((x[0] + x[2] * sin(x[4]), x[1] + x[2] * cos(x[4])))

        def arc_first_tangent(x):

            return array((cos(x[3]), sin(x[3])))

        def arc_last_tangent(x):

            return array((cos(x[4]), sin(x[4])))

        def fixed_cost(x, t, val):

            return norm(x - val)

        def coincident_cost(x1, t1, x2, t2, val):

            if t1 == "LINE" and t2 == "LINE":
                v1 = x1[2:]
                v2 = x2[:2]
            elif t1 == "LINE" and t2 == "CRICLE":
                v1 = x1[2:]
                v2 = arc_first(x2)
            elif t1 == "CIRCLE" and t2 == "LINE":
                v1 = arc_last(x1)
                v2 = x2[:2]
            elif t1 == "CIRCLE" and t2 == "CRICLE":
                v1 = arc_last(x1)
                v2 = arc_first(x1)
            else:
                raise invalid_args(t1, t2)

            return norm(v1 - v2)

        def angle_cost(x1, t1, x2, t2, val):

            if t1 == "LINE" and t2 == "LINE":
                v1 = gp_Vec2d(*(x1[2:] - x1[:2]))
                v2 = gp_Vec2d(*(x2[2:] - x2[:2]))
            elif t1 == "LINE" and t2 == "CRICLE":
                v1 = gp_Vec2d(*(x1[2:] - x1[:2]))
                v2 = arc_first_tangent(x2)
            elif t1 == "CIRCLE" and t2 == "LINE":
                v1 = arc_last_tangent(x1)
                v2 = gp_Vec2d(*(x2[2:] - x2[:2]))
            elif t1 == "CIRCLE" and t2 == "CRICLE":
                v1 = arc_last_tangent(x1)
                v2 = arc_first_tangent(x2)
            else:
                raise invalid_args(t1, t2)

            return v2.Angle(v1) - val

        def length_cost(x, t, val):

            rv = 0

            if t == "LINE":
                rv = norm(x[2:] - x[:2]) - val
            elif t == "CIRCLE":
                rv = norm(x[1] * (x[4] - x[3])) - val
            else:
                raise invalid_args(t)

            return rv

        # dicitonary of individual constraint cost functions
        costs = dict(
            Fixed=fixed_cost,
            Coincident=coincident_cost,
            Angle=angle_cost,
            Length=length_cost,
        )

        ixs = self.ixs
        constraints = self.constraints
        geoms = self.geoms

        def f(x):
            """
            Function to be minimized
            """

            rv = 0

            for i, ((e1, e2), kind, val) in enumerate(constraints):

                cost = costs[kind]

                # build arguments for the specific constraint
                args = (x[ixs[e1] : ixs[e1 + 1]], geoms[e1])
                if e2 is not None:
                    args += (x[ixs[e2] : ixs[e2 + 1]], geoms[e2])
                args += (val,)

                # evaluate
                rv += cost(*args) ** 2

            return rv

        return f

    def solve(self) -> List[Location]:

        x0 = array(list(chain.from_iterable(self.entities))).ravel()
        f = self._cost()

        res = minimize(f, x0, method="BFGS")

        x = res.x
        ixs = self.ixs

        return [x[i1:i2] for i1, i2 in zip(ixs, ixs[1:])]
