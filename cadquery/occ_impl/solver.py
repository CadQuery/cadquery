from typing import Tuple, Union, Any, Callable, List, Optional, Dict
from nptyping import NDArray as Array

from numpy import array, eye, zeros, pi
import nlopt

from OCP.gp import gp_Vec, gp_Pln, gp_Dir, gp_Pnt, gp_Trsf, gp_Quaternion

from .geom import Location

DOF6 = Tuple[float, float, float, float, float, float]
ConstraintMarker = Union[gp_Pln, gp_Dir, gp_Pnt]
Constraint = Tuple[
    Tuple[ConstraintMarker, ...], Tuple[Optional[ConstraintMarker], ...], Optional[Any]
]

NDOF = 6
DIR_SCALING = 1e2
DIFF_EPS = 1e-10
TOL = 1e-12
MAXITER = 2000


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
            ms1, ms2, d = v
            if ms2:
                for m1, m2 in zip(ms1, ms2):
                    self.constraints.append((k, ((m1,), (m2,), d)))
            else:
                raise NotImplementedError(
                    "Single marker constraints are not implemented"
                )

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
        Callable[[Array[(Any,), float], Array[(Any,), float]], None],
    ]:
        def pt_cost(
            m1: gp_Pnt,
            m2: gp_Pnt,
            t1: gp_Trsf,
            t2: gp_Trsf,
            val: Optional[float] = None,
        ) -> float:

            val = 0 if val is None else val

            return val - (m1.Transformed(t1).XYZ() - m2.Transformed(t2).XYZ()).Modulus()

        def dir_cost(
            m1: gp_Dir,
            m2: gp_Dir,
            t1: gp_Trsf,
            t2: gp_Trsf,
            val: Optional[float] = None,
        ) -> float:

            val = pi if val is None else val

            return DIR_SCALING * (val - m1.Transformed(t1).Angle(m2.Transformed(t2)))

        def pnt_pln_cost(
            m1: gp_Pnt,
            m2: gp_Pln,
            t1: gp_Trsf,
            t2: gp_Trsf,
            val: Optional[float] = None,
        ) -> float:

            val = 0 if val is None else val

            m2_located = m2.Transformed(t2)
            # offset in the plane's normal direction by val:
            m2_located.Translate(gp_Vec(m2_located.Axis().Direction()).Multiplied(val))
            return m2_located.Distance(m1.Transformed(t1))

        def f(x):
            """
            Function to be minimized
            """

            constraints = self.constraints
            ne = self.ne

            rv = 0

            transforms = [
                self._build_transform(*x[NDOF * i : NDOF * (i + 1)]) for i in range(ne)
            ]

            for i, ((k1, k2), (ms1, ms2, d)) in enumerate(constraints):
                t1 = transforms[k1] if k1 not in self.locked else gp_Trsf()
                t2 = transforms[k2] if k2 not in self.locked else gp_Trsf()

                for m1, m2 in zip(ms1, ms2):
                    if isinstance(m1, gp_Pnt) and isinstance(m2, gp_Pnt):
                        rv += pt_cost(m1, m2, t1, t2, d) ** 2
                    elif isinstance(m1, gp_Dir):
                        rv += dir_cost(m1, m2, t1, t2, d) ** 2
                    elif isinstance(m1, gp_Pnt) and isinstance(m2, gp_Pln):
                        rv += pnt_pln_cost(m1, m2, t1, t2, d) ** 2
                    else:
                        raise NotImplementedError(f"{m1,m2}")

            return rv

        def grad(x, rv):

            constraints = self.constraints
            ne = self.ne

            delta = DIFF_EPS * eye(NDOF)

            rv[:] = 0

            transforms = [
                self._build_transform(*x[NDOF * i : NDOF * (i + 1)]) for i in range(ne)
            ]

            transforms_delta = [
                self._build_transform(*(x[NDOF * i : NDOF * (i + 1)] + delta[j, :]))
                for i in range(ne)
                for j in range(NDOF)
            ]

            for i, ((k1, k2), (ms1, ms2, d)) in enumerate(constraints):
                t1 = transforms[k1] if k1 not in self.locked else gp_Trsf()
                t2 = transforms[k2] if k2 not in self.locked else gp_Trsf()

                for m1, m2 in zip(ms1, ms2):
                    if isinstance(m1, gp_Pnt) and isinstance(m2, gp_Pnt):
                        tmp = pt_cost(m1, m2, t1, t2, d)

                        for j in range(NDOF):

                            t1j = transforms_delta[k1 * NDOF + j]
                            t2j = transforms_delta[k2 * NDOF + j]

                            if k1 not in self.locked:
                                tmp1 = pt_cost(m1, m2, t1j, t2, d)
                                rv[k1 * NDOF + j] += 2 * tmp * (tmp1 - tmp) / DIFF_EPS

                            if k2 not in self.locked:
                                tmp2 = pt_cost(m1, m2, t1, t2j, d)
                                rv[k2 * NDOF + j] += 2 * tmp * (tmp2 - tmp) / DIFF_EPS

                    elif isinstance(m1, gp_Dir):
                        tmp = dir_cost(m1, m2, t1, t2, d)

                        for j in range(NDOF):

                            t1j = transforms_delta[k1 * NDOF + j]
                            t2j = transforms_delta[k2 * NDOF + j]

                            if k1 not in self.locked:
                                tmp1 = dir_cost(m1, m2, t1j, t2, d)
                                rv[k1 * NDOF + j] += 2 * tmp * (tmp1 - tmp) / DIFF_EPS

                            if k2 not in self.locked:
                                tmp2 = dir_cost(m1, m2, t1, t2j, d)
                                rv[k2 * NDOF + j] += 2 * tmp * (tmp2 - tmp) / DIFF_EPS

                    elif isinstance(m1, gp_Pnt) and isinstance(m2, gp_Pln):
                        tmp = pnt_pln_cost(m1, m2, t1, t2, d)

                        for j in range(NDOF):

                            t1j = transforms_delta[k1 * NDOF + j]
                            t2j = transforms_delta[k2 * NDOF + j]

                            if k1 not in self.locked:
                                tmp1 = pnt_pln_cost(m1, m2, t1j, t2, d)
                                rv[k1 * NDOF + j] += 2 * tmp * (tmp1 - tmp) / DIFF_EPS

                            if k2 not in self.locked:
                                tmp2 = pnt_pln_cost(m1, m2, t1, t2j, d)
                                rv[k2 * NDOF + j] += 2 * tmp * (tmp2 - tmp) / DIFF_EPS
                    else:
                        raise NotImplementedError(f"{m1,m2}")

        return f, grad

    def solve(self) -> Tuple[List[Location], Dict[str, Any]]:

        x0 = array([el for el in self.entities]).ravel()
        f, grad = self._cost()

        def func(x, g):

            if g.size > 0:
                grad(x, g)

            return f(x)

        opt = nlopt.opt(nlopt.LD_CCSAQ, len(x0))
        opt.set_min_objective(func)

        opt.set_ftol_abs(0)
        opt.set_ftol_rel(0)
        opt.set_xtol_rel(TOL)
        opt.set_xtol_abs(TOL * 1e-3)
        opt.set_maxeval(MAXITER)

        x = opt.optimize(x0)
        result = {
            "cost": opt.last_optimum_value(),
            "iters": opt.get_numevals(),
            "status": opt.last_optimize_result(),
        }

        locs = [
            Location(self._build_transform(*x[NDOF * i : NDOF * (i + 1)]))
            for i in range(self.ne)
        ]
        return locs, result
