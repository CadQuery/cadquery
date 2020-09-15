from typing import Tuple, Union, Any, Callable, List, Optional
from nptyping import NDArray as Array

from numpy import zeros, array, full, inf

from scipy.optimize import least_squares

from OCP.gp import gp_Vec, gp_Dir, gp_Pnt, gp_Trsf, gp_Quaternion

from .geom import Location

DOF6 = Tuple[float, float, float, float, float, float]
ConstraintMarker = Union[gp_Dir, gp_Pnt]
Constraint = Tuple[Tuple[ConstraintMarker, ...], Tuple[Optional[ConstraintMarker], ...]]

NDOF = 6


class ConstraintSolver(object):

    entities: List[DOF6]
    constraints: List[Tuple[Tuple[int, Optional[int]], Constraint]]
    locked: List[int]
    ne: int
    nc: int

    def __init__(
        self,
        entities: List[Location],
        constraints: List[Tuple[Tuple[int, int], Constraint]],
        locked: List[int] = [],
    ):

        self.entities = [self._locToDOF6(loc) for loc in entities]
        self.constraints = []

        # decompose inot simple constraints
        for k, v in constraints:
            e1, e2 = v
            if e2:
                for m1, m2 in zip(e1, e2):
                    self.constraints.append((k, ((m1,), (m2,))))
            else:
                for m1 in e1:
                    self.constraints.append((k, ((m1,), (None,))))

        self.ne = len(entities)
        self.locked = locked
        self.nc = len(self.constraints)

    @staticmethod
    def _locToDOF6(loc: Location) -> DOF6:

        T = loc.wrapped.Transformation()
        v = T.TranslationPart()
        q = T.GetRotation()

        alpha_2 = (1 - q.W()) / (1 + q.W())
        a = (alpha_2 + 1) * q.X() / 2
        b = (alpha_2 + 1) * q.Y() / 2
        c = (alpha_2 + 1) * q.Z() / 2

        return (v.X(), v.Y(), v.Z(), a, b, c)

    def _jacobianSparsity(self) -> Array[(Any, Any), float]:

        rv = zeros((self.nc, NDOF * self.ne))

        for i, ((k1, k2), ((m1,), (m2,))) in enumerate(self.constraints):

            k1_active = 1 if k1 not in self.locked else 0
            k2_active = 1 if k2 not in self.locked else 0

            rv[i, NDOF * k1 : NDOF * (k1 + 1)] = k1_active

            if k2:
                rv[i, NDOF * k2 : NDOF * (k2 + 1)] = k2_active

        return rv

    def _build_transform(
        self, x: float, y: float, z: float, a: float, b: float, c: float
    ) -> gp_Trsf:

        rv = gp_Trsf()
        m = a ** 2 + b ** 2 + c ** 2

        rv.SetRotation(
            gp_Quaternion(
                2 * a / (m + 1), 2 * b / (m + 1), 2 * c / (m + 1), (1 - m) / (m + 1),
            )
        )

        rv.SetTranslationPart(gp_Vec(x, y, z))

        return rv

    def _cost(self) -> Callable[[Array[(Any,), float]], Array[(Any,), float]]:
        def f(x):

            constraints = self.constraints
            nc = self.nc
            ne = self.ne

            rv = zeros(nc)

            transforms = [
                self._build_transform(*x[NDOF * i : NDOF * (i + 1)]) for i in range(ne)
            ]

            for i, ((k1, k2), (ms1, ms2)) in enumerate(constraints):
                t1 = transforms[k1] if k1 not in self.locked else gp_Trsf()
                t2 = transforms[k2] if k2 not in self.locked else gp_Trsf()

                for m1, m2 in zip(ms1, ms2):
                    if isinstance(m1, gp_Pnt):
                        rv[i] += (
                            m1.Transformed(t1).XYZ() - m2.Transformed(t2).XYZ()
                        ).Modulus()
                    elif isinstance(m1, gp_Dir):
                        rv[i] += m1.Transformed(t1).Angle(m2.Transformed(t2))
                    else:
                        raise NotImplementedError(f"{m1,m2}")

            return rv

        return f

    def _bounds(self) -> Tuple[Array[(Any,), float], Array[(Any,), float]]:

        bmin = full((NDOF * self.ne,), -inf)
        bmax = full((NDOF * self.ne,), +inf)

        for i in self.locked:
            bmin[NDOF * i : (NDOF * i + NDOF)] = self.entities[i]
            bmax[NDOF * i : (NDOF * i + NDOF)] = (
                bmin[NDOF * i : (NDOF * i + NDOF)] + 1e-9
            )

        return bmin, bmax

    def solve(self) -> List[Location]:

        x0 = array([el for el in self.entities]).ravel()
        res = least_squares(
            self._cost(),
            x0,
            jac="2-point",
            jac_sparsity=self._jacobianSparsity(),
            method="dogbox",
            ftol=None,
            gtol=1e-6,
            xtol=None,
            verbose=2,
        )
        x = res.x

        return [
            Location(self._build_transform(*x[NDOF * i : NDOF * (i + 1)]))
            for i in range(self.ne)
        ]
