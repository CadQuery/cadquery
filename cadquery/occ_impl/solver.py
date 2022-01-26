from typing import (
    List,
    Tuple,
    Union,
    Any,
    Callable,
    List,
    Optional,
    Dict,
    Literal,
    cast,
)
from nptyping import NDArray as Array
from math import radians

from numpy import array, eye, zeros, pi
import nlopt

from OCP.gp import gp_Vec, gp_Pln, gp_Dir, gp_Pnt, gp_Trsf, gp_Quaternion
from OCP.BRepTools import BRepTools
from OCP.Precision import Precision

from .geom import Location, Vector, Plane
from .shapes import Shape, Face, Edge, Wire
from ..types import Real

#%% type definitions

NoneType = type(None)

DOF6 = Tuple[float, float, float, float, float, float]
ConstraintMarker = Union[gp_Pln, gp_Dir, gp_Pnt]

ConstraintKind = Literal["Plane", "Point", "Axis", "PointInPlane"]

# (arity, marker types, param type, conversion func)
ConstraintInvariants = {
    "Point": (2, (gp_Pnt, gp_Pnt), Real, None),
    "Axis": (2, (gp_Dir, gp_Dir), Real, radians),
    "PointInPlane": (2, (gp_Pnt, gp_Pln), Real, radians),
    "Plane": ["Point", "Axis"],
}

# translation table for compound constraints {name : (name, ...)}
CompoundConstraints = {"Plane": ["Point", "Axis"]}

Constraint = Tuple[
    Tuple[
        Union[Tuple[ConstraintMarker, ConstraintMarker], Tuple[ConstraintMarker]], ...
    ],
    ConstraintKind,
    Optional[Any],
]

Constraint = Tuple[
    Tuple[ConstraintMarker, ...], Tuple[Optional[ConstraintMarker], ...], Optional[Any]
]

NDOF = 6
DIR_SCALING = 1e2
DIFF_EPS = 1e-10
TOL = 1e-12
MAXITER = 2000

#%% high-level constraint class - to be used by clients


class ConstraintSpec(object):
    """
    Geometrical constraint specification between two shapes of an assembly.
    """

    objects: Tuple[str, ...]
    args: Tuple[Shape, ...]
    sublocs: Tuple[Location, ...]
    kind: ConstraintKind
    param: Any

    def __init__(
        self,
        objects: Tuple[str, ...],
        args: Tuple[Shape, ...],
        sublocs: Tuple[Location, ...],
        kind: ConstraintKind,
        param: Any = None,
    ):
        """
        Construct a constraint.

        :param objects: object names referenced in the constraint
        :param args: subshapes (e.g. faces or edges) of the objects
        :param sublocs: locations of the objects (only relevant if the objects are nested in a sub-assembly)
        :param kind: constraint kind
        :param param: optional arbitrary parameter passed to the solver
        """

        self.objects = objects
        self.args = args
        self.sublocs = sublocs
        self.kind = kind
        self.param = param

    def _getAxis(self, arg: Shape) -> Vector:

        if isinstance(arg, Face):
            rv = arg.normalAt()
        elif isinstance(arg, Edge) and arg.geomType() != "CIRCLE":
            rv = arg.tangentAt()
        elif isinstance(arg, Edge) and arg.geomType() == "CIRCLE":
            rv = arg.normal()
        else:
            raise ValueError(f"Cannot construct Axis for {arg}")

        return rv

    def _getPln(self, arg: Shape) -> gp_Pln:

        if isinstance(arg, Face):
            rv = gp_Pln(self._getPnt(arg), arg.normalAt().toDir())
        elif isinstance(arg, (Edge, Wire)):
            normal = arg.normal()
            origin = arg.Center()
            plane = Plane(origin, normal=normal)
            rv = plane.toPln()
        else:
            raise ValueError(f"Can not construct a plane for {arg}.")

        return rv

    def _getPnt(self, arg: Shape) -> gp_Pnt:

        # check for infinite face
        if isinstance(arg, Face) and any(
            Precision.IsInfinite_s(x) for x in BRepTools.UVBounds_s(arg.wrapped)
        ):
            # fall back to gp_Pln center
            pln = arg.toPln()
            center = Vector(pln.Location())
        else:
            center = arg.Center()

        return center.toPnt()

    def toPOD(self) -> Constraint:
        """
        Convert the constraint to a representation used by the solver.
        """

        # convert to marker objects
        if self.kind == "Axis":
            args = (
                self._getAxis(self.args[0]).toDir(),
                self._getAxis(self.args[1]).toDir(),
            )

        elif self.kind == "Point":
            args = (self._getPnt(self.args[0]), self._getPnt(self.args[1]))

        elif self.kind == "Plane":
            args = (
                (
                    self._getAxis(self.args[0]).toDir(),
                    self._getAxis(self.args[1]).toDir(),
                ),
                (self._getPnt(self.args[0]), self._getPnt(self.args[1])),
            )

        elif self.kind == "PointInPlane":
            args = (self._getPnt(self.args[0]), self._getPln(self.args[1]))

        else:
            raise ValueError(f"Unknown constraint kind {self.kind}")

        # apply sublocation
        for ix, loc in enumerate(self.sublocs):
            args[ix] = args[ix].located(loc * args[ix].location())

        return (args, self.kind, self.param)

    def toSimplePOD(self, c: Constraint) -> List[Constraint]:
        """
        Convert a complex constraint into listo of simple ones
        """

        kind = c[1]

        if kind not in CompoundConstraints:
            raise ValueError(f"{kind} is not a compound constraint")

        return [((m,), k, a) for m, k, a in zip(c[0], CompoundConstraints[kind], c[1])]


#%% Cost functions of simple constraints


def point_cost(
    m1: gp_Pnt, m2: gp_Pnt, t1: gp_Trsf, t2: gp_Trsf, val: Optional[float] = None,
) -> float:

    val = 0 if val is None else val

    return val - (m1.Transformed(t1).XYZ() - m2.Transformed(t2).XYZ()).Modulus()


def axis_cost(
    m1: gp_Dir, m2: gp_Dir, t1: gp_Trsf, t2: gp_Trsf, val: Optional[float] = None,
) -> float:

    val = pi if val is None else val

    return DIR_SCALING * (val - m1.Transformed(t1).Angle(m2.Transformed(t2)))


def point_in_plane_cost(
    m1: gp_Pnt, m2: gp_Pln, t1: gp_Trsf, t2: gp_Trsf, val: Optional[float] = None,
) -> float:

    val = 0 if val is None else val

    m2_located = m2.Transformed(t2)
    # offset in the plane's normal direction by val:
    m2_located.Translate(gp_Vec(m2_located.Axis().Direction()).Multiplied(val))
    return m2_located.Distance(m1.Transformed(t1))


# dictionary of individual constraint cost functions
costs: Dict[str, Callable[..., float]] = dict(
    Point=point_cost, Axis=axis_cost, PointInPlane=point_in_plane_cost
)

#%% Actual solver class


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
        self.constraints = constraints

        # additional book-keeping
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
                        rv += point_cost(m1, m2, t1, t2, d) ** 2
                    elif isinstance(m1, gp_Dir):
                        rv += axis_cost(m1, m2, t1, t2, d) ** 2
                    elif isinstance(m1, gp_Pnt) and isinstance(m2, gp_Pln):
                        rv += point_in_plane_cost(m1, m2, t1, t2, d) ** 2
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
                        tmp = point_cost(m1, m2, t1, t2, d)

                        for j in range(NDOF):

                            t1j = transforms_delta[k1 * NDOF + j]
                            t2j = transforms_delta[k2 * NDOF + j]

                            if k1 not in self.locked:
                                tmp1 = point_cost(m1, m2, t1j, t2, d)
                                rv[k1 * NDOF + j] += 2 * tmp * (tmp1 - tmp) / DIFF_EPS

                            if k2 not in self.locked:
                                tmp2 = point_cost(m1, m2, t1, t2j, d)
                                rv[k2 * NDOF + j] += 2 * tmp * (tmp2 - tmp) / DIFF_EPS

                    elif isinstance(m1, gp_Dir):
                        tmp = axis_cost(m1, m2, t1, t2, d)

                        for j in range(NDOF):

                            t1j = transforms_delta[k1 * NDOF + j]
                            t2j = transforms_delta[k2 * NDOF + j]

                            if k1 not in self.locked:
                                tmp1 = axis_cost(m1, m2, t1j, t2, d)
                                rv[k1 * NDOF + j] += 2 * tmp * (tmp1 - tmp) / DIFF_EPS

                            if k2 not in self.locked:
                                tmp2 = axis_cost(m1, m2, t1, t2j, d)
                                rv[k2 * NDOF + j] += 2 * tmp * (tmp2 - tmp) / DIFF_EPS

                    elif isinstance(m1, gp_Pnt) and isinstance(m2, gp_Pln):
                        tmp = point_in_plane_cost(m1, m2, t1, t2, d)

                        for j in range(NDOF):

                            t1j = transforms_delta[k1 * NDOF + j]
                            t2j = transforms_delta[k2 * NDOF + j]

                            if k1 not in self.locked:
                                tmp1 = point_in_plane_cost(m1, m2, t1j, t2, d)
                                rv[k1 * NDOF + j] += 2 * tmp * (tmp1 - tmp) / DIFF_EPS

                            if k2 not in self.locked:
                                tmp2 = point_in_plane_cost(m1, m2, t1, t2j, d)
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
