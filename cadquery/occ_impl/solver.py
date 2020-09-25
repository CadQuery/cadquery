from typing import Tuple, Union, Any, Callable, List, Optional
from nptyping import NDArray as Array

from numpy import array, eye, zeros
from scipy.optimize import minimize

from OCP.gp import gp_Vec, gp_Dir, gp_Pnt, gp_Trsf, gp_Quaternion

from .geom import Location

DOF6 = Tuple[float, float, float, float, float, float]
ConstraintMarker = Union[gp_Dir, gp_Pnt]
Constraint = Tuple[Tuple[ConstraintMarker, ...], Tuple[Optional[ConstraintMarker], ...]]

NDOF = 6
DIR_SCALING = 1e3
DIFF_EPS = 1e-8


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

        # decompose into simple constraints
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

    def _cost(
        self,
    ) -> Tuple[
        Callable[[Array[(Any,), float]], float],
        Callable[[Array[(Any,), float]], Array[(Any,), float]],
    ]:
        def pt_cost(m1: gp_Pnt, m2: gp_Pnt, t1: gp_Trsf, t2: gp_Trsf) -> float:

            return (m1.Transformed(t1).XYZ() - m2.Transformed(t2).XYZ()).SquareModulus()

        def dir_cost(
            m1: gp_Dir, m2: gp_Dir, t1: gp_Trsf, t2: gp_Trsf, val: float = -1
        ) -> float:

            return DIR_SCALING * (val - m1.Transformed(t1).Dot(m2.Transformed(t2))) ** 2

        def f(x):

            constraints = self.constraints
            ne = self.ne

            rv = 0

            transforms = [
                self._build_transform(*x[NDOF * i : NDOF * (i + 1)]) for i in range(ne)
            ]

            for i, ((k1, k2), (ms1, ms2)) in enumerate(constraints):
                t1 = transforms[k1] if k1 not in self.locked else gp_Trsf()
                t2 = transforms[k2] if k2 not in self.locked else gp_Trsf()

                for m1, m2 in zip(ms1, ms2):
                    if isinstance(m1, gp_Pnt):
                        rv += pt_cost(m1, m2, t1, t2)
                    elif isinstance(m1, gp_Dir):
                        rv += dir_cost(m1, m2, t1, t2)
                    else:
                        raise NotImplementedError(f"{m1,m2}")

            return rv

        def jac(x):

            constraints = self.constraints
            ne = self.ne

            delta = DIFF_EPS * eye(NDOF)

            rv = zeros(NDOF * ne)

            transforms = [
                self._build_transform(*x[NDOF * i : NDOF * (i + 1)]) for i in range(ne)
            ]

            transforms_delta = [
                self._build_transform(*(x[NDOF * i : NDOF * (i + 1)] + delta[j, :]))
                for i in range(ne)
                for j in range(NDOF)
            ]

            for i, ((k1, k2), (ms1, ms2)) in enumerate(constraints):
                t1 = transforms[k1] if k1 not in self.locked else gp_Trsf()
                t2 = transforms[k2] if k2 not in self.locked else gp_Trsf()

                for m1, m2 in zip(ms1, ms2):
                    if isinstance(m1, gp_Pnt):
                        tmp = pt_cost(m1, m2, t1, t2)

                        for j in range(NDOF):

                            t1j = transforms_delta[k1 * NDOF + j]
                            t2j = transforms_delta[k2 * NDOF + j]

                            if k1 not in self.locked:
                                tmp1 = pt_cost(m1, m2, t1j, t2)
                                rv[k1 * NDOF + j] += (tmp1 - tmp) / DIFF_EPS

                            if k2 not in self.locked:
                                tmp2 = pt_cost(m1, m2, t1, t2j)
                                rv[k2 * NDOF + j] += (tmp2 - tmp) / DIFF_EPS

                    elif isinstance(m1, gp_Dir):
                        tmp = dir_cost(m1, m2, t1, t2)

                        for j in range(NDOF):

                            t1j = transforms_delta[k1 * NDOF + j]
                            t2j = transforms_delta[k2 * NDOF + j]

                            if k1 not in self.locked:
                                tmp1 = dir_cost(m1, m2, t1j, t2)
                                rv[k1 * NDOF + j] += (tmp1 - tmp) / DIFF_EPS

                            if k2 not in self.locked:
                                tmp2 = dir_cost(m1, m2, t1, t2j)
                                rv[k2 * NDOF + j] += (tmp2 - tmp) / DIFF_EPS
                    else:
                        raise NotImplementedError(f"{m1,m2}")

            return rv

        return f, jac

    def solve(self) -> List[Location]:

        x0 = array([el for el in self.entities]).ravel()
        f, jac = self._cost()

        res = minimize(
            f,
            x0,
            jac=jac,
            method="L-BFGS-B",
            options=dict(disp=True, ftol=1e-14, maxiter=1000),
        )

        x = res.x
        print(res.message)

        return [
            Location(self._build_transform(*x[NDOF * i : NDOF * (i + 1)]))
            for i in range(self.ne)
        ]
