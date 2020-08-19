from typing import Tuple, Mapping, Union, Any, Callable, List
from nptyping import NDArray as Array

from numpy import zeros, array
from scipy.optimize import least_squares

from OCP.gp import gp_Vec, gp_Dir, gp_Pnt, gp_Trsf, gp_Quaternion

from .geom import Location

DOF6 = Tuple[float, float, float, float, float, float]
ConstraintMarker = Union[gp_Dir, gp_Pnt]
Constraint = Tuple[Tuple[ConstraintMarker, ...], Tuple[ConstraintMarker, ...]]


class ConstraintSolver(object):

    entities: Mapping[int, DOF6]
    constraints: Mapping[Tuple[int, int], Constraint]
    ne: int
    nc: int

    def __init__(
        self,
        entities: List[Location],
        constraints: Mapping[Tuple[int, int], Constraint],
    ):

        pass

    def _jacobianSparsity(self) -> Array[(Any, Any), float]:

        rv = zeros((self.nc, 6 * self.ne))

        for i, (k1, k2) in enumerate(self.constraints):
            rv[i, 6 * k1 : 6 * (k1 + 1)] = 1
            rv[i, 6 * k2 : 6 * (k2 + 1)] = 1

        return rv

    def _build_transform(
        self, x: float, y: float, z: float, a: float, b: float, c: float
    ) -> gp_Trsf:

        rv = gp_Trsf()
        m = a ** 2 + b ** 2 + c ** 2

        rv.SetTranslation(gp_Vec(x, y, z))
        rv.SetRotation(
            gp_Quaternion(2 * a / m, 2 * b / m, 2 * c / m, (1 - m) / (m + 1))
        )

        return rv

    def _cost(self) -> Callable[[Array[(Any,), float]], Array[(Any,), float]]:
        def f(x):

            constraints = self.constraints
            nc = self.nc
            ne = self.ne

            rv = zeros(nc)
            transforms = [
                self._build_transform(*x[6 * i : 6 * (i + 1)]) for i in range(ne)
            ]

            for i, ((k1, k2), ms1, ms2) in enumerate(constraints.items()):
                t1 = transforms[k1]
                t2 = transforms[k2]

                for m1, m2 in zip(ms1, ms2):
                    if isinstance(m1, gp_Pnt):
                        rv[i] += (m1.Transformed(t1) - m2.Transformed(t2)).Magnitude()
                    elif isinstance(m1, gp_Dir):
                        rv[i] += m1.Transformed(t1) * m2.Transformed(t2)
                    else:
                        raise NotImplementedError

            return rv

        return f

    def solve(self) -> List[Location]:

        x0 = array([el for el in self.entities.values()]).ravel()

        res = least_squares(self._cost(), x0, jac_sparsity=self._jacobianSparsity())
        x = res.x

        return [
            Location(self._build_transform(*x[6 * i : 6 * (i + 1)]))
            for i in range(self.ne)
        ]
