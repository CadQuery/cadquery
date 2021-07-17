from typing import Tuple, Union, Any, Callable, List, Optional, Literal, Iterable
from nptyping import NDArray as Array
from itertools import accumulate, chain

from numpy import array
from numpy.linalg import norm
from scipy.optimize import minimize
from OCP.gp import gp_Vec2d

from .geom import Location


SegmentDOF = Tuple[float, float, float, float]  # p1 p2
ArcDOF = Tuple[float, float, float, float, float]  # p r a1 a2
DOF = Union[SegmentDOF, ArcDOF]

ConstraintKind = Literal["Fixed", "Coincident", "Angle", "Length"]
Constraint = Tuple[Tuple[int, Optional[int]], ConstraintKind, Optional[Any]]


class SketchConstraintSolver(object):

    entities: List[DOF]
    constraints: List[Constraint]
    ne: int
    nc: int
    ixs: List[int]

    def __init__(self, entities: Iterable[DOF], constraints: Iterable[Constraint]):

        self.entities = list(entities)
        self.constraints = list(constraints)

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
        def fixed_cost(x, val):

            return norm(x - val)

        def coincident_cost(x1, x2):

            return norm(x1[2:] - x2[:2])

        def angle_cost(x1, x2, val):

            v1 = gp_Vec2d(*(x1[2:] - x1[:2]))
            v2 = gp_Vec2d(*(x2[2:] - x2[:2]))

            a = v2.Angle(v1)

            return a - val

        def length_cost(x1, x2, val):

            return norm(x2 - x1) - val

        # dicitonary of individual constraint cost functions
        costs = dict(
            Fixed=fixed_cost,
            Coincident=coincident_cost,
            Angle=angle_cost,
            Length=length_cost,
        )

        ixs = self.ixs

        def f(x):
            """
            Function to be minimized
            """

            constraints = self.constraints

            rv = 0

            for i, ((e1, e2), kind, val) in enumerate(constraints):

                cost = costs[kind]

                # build arguments for the specific constraint
                args = (x[ixs[e1] : ixs[e1 + 1]],)
                if e2 is not None:
                    args += (x[ixs[e2] : ixs[e2 + 1]],)
                if val is not None:
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
