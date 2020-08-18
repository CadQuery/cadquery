from typing import Tuple, Mapping, Union, Any, Callable, List
from nptyping import NDArray as Array

from numpy import zeros, array
from scipy.optimize import least_squares

from OCP.gp import gp_Dir, gp_Pnt

from .geom import Location

DOF6 = Tuple[float, float, float, float, float, float]
ConstraintMarker = Union[gp_Dir, gp_Pnt]


class ConstraintSolver(object):

    entities: Mapping[int, DOF6]
    constraints: Mapping[
        Tuple[int, int],
        Tuple[Tuple[ConstraintMarker, ...], Tuple[ConstraintMarker, ...]],
    ]

    def _jacobianSparsity(self) -> Array[(Any, Any), float]:

        rv = zeros((len(self.constraints), 6 * len(self.entities)))

        for i, (k1, k2) in enumerate(self.constraints):
            rv[i, 6 * k1 : 6 * (k1 + 1)] = 1
            rv[i, 6 * k2 : 6 * (k2 + 1)] = 1

        return rv

    def _cost(self) -> Callable[[Array[(Any,), float]], Array[(Any,), float]]:
        def f(x):

            rv = zeros(len(self.constraints))

            return rv

        return f

    def solve(self) -> List[Location]:

        x0 = array([el for el in self.entities.values()]).ravel()

        res = least_squares(self._cost(), x0, jac_sparsity=self._jacobianSparsity())

        return res.x
