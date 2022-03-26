from typing import (
    List,
    Tuple,
    Union,
    Any,
    Callable,
    Optional,
    Dict,
    Literal,
    cast as tcast,
    Type,
)
from nptyping import NDArray as Array
from math import radians
from typish import instance_of, get_type
from numpy import array, eye, pi
import nlopt

from OCP.gp import (
    gp_Vec,
    gp_Pln,
    gp_Dir,
    gp_Pnt,
    gp_Trsf,
    gp_Quaternion,
    gp_XYZ,
    gp_Lin,
    gp_Intrinsic_XYZ,
)
from OCP.BRepTools import BRepTools
from OCP.Precision import Precision

from .geom import Location, Vector, Plane
from .shapes import Shape, Face, Edge, Wire
from ..types import Real

# type definitions

NoneType = type(None)

DOF6 = Tuple[float, float, float, float, float, float]
ConstraintMarker = Union[gp_Pln, gp_Dir, gp_Pnt, gp_Lin, None]

UnaryConstraintKind = Literal[
    "Fixed", "FixedPoint", "FixedAxis", "FixedRotation", "FixedRotationAxis"
]
BinaryConstraintKind = Literal["Plane", "Point", "Axis", "PointInPlane", "PointOnLine"]
ConstraintKind = Literal[
    "Plane",
    "Point",
    "Axis",
    "PointInPlane",
    "Fixed",
    "FixedPoint",
    "FixedAxis",
    "PointOnLine",
    "FixedRotation",
    "FixedRotationAxis",
]

# (arity, marker types, param type, conversion func)
ConstraintInvariants = {
    "Point": (2, (gp_Pnt, gp_Pnt), Real, None),
    "Axis": (
        2,
        (gp_Dir, gp_Dir),
        Real,
        lambda x: radians(x) if x is not None else None,
    ),
    "PointInPlane": (2, (gp_Pnt, gp_Pln), Real, None),
    "PointOnLine": (2, (gp_Pnt, gp_Lin), Real, None),
    "Fixed": (1, (None,), Type[None], None),
    "FixedPoint": (1, (gp_Pnt,), Tuple[Real, Real, Real], None),
    "FixedAxis": (1, (gp_Dir,), Tuple[Real, Real, Real], None),
    "FixedRotationAxis": (
        1,
        (None,),
        Tuple[int, Real],
        lambda x: (x[0], radians(x[1])),
    ),
}

# translation table for compound constraints {name : (name, ...), converter}
CompoundConstraints: Dict[
    ConstraintKind, Tuple[Tuple[ConstraintKind, ...], Callable[[Any], Tuple[Any, ...]]]
] = {
    "Plane": (("Axis", "Point"), lambda x: (radians(x) if x is not None else None, 0)),
    "FixedRotation": (
        ("FixedRotationAxis", "FixedRotationAxis", "FixedRotationAxis"),
        lambda x: tuple(enumerate(map(radians, x))),
    ),
}

# constraint POD type
Constraint = Tuple[
    Tuple[ConstraintMarker, ...], ConstraintKind, Optional[Any],
]

NDOF = 6
DIR_SCALING = 1e2
DIFF_EPS = 1e-10
TOL = 1e-12
MAXITER = 2000

# high-level constraint class - to be used by clients


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

        # validate
        if not instance_of(kind, ConstraintKind):
            raise ValueError(f"Unknown constraint {kind}.")

        if kind in CompoundConstraints:
            kinds, convert_compound = CompoundConstraints[kind]
            for k, p in zip(kinds, convert_compound(param)):
                self._validate(args, k, p)
        else:
            self._validate(args, kind, param)

            # convert here for simple constraints
            convert = ConstraintInvariants[kind][-1]
            param = convert(param) if convert else param

        # store
        self.objects = objects
        self.args = args
        self.sublocs = sublocs
        self.kind = kind
        self.param = param

    def _validate(self, args: Tuple[Shape, ...], kind: ConstraintKind, param: Any):

        arity, marker_types, param_type, converter = ConstraintInvariants[kind]

        # check arity
        if arity != len(args):
            raise ValueError(
                f"Invalid number of entities for constraint {kind}. Provided {len(args)}, required {arity}."
            )

        # check arguments
        arg_check: Dict[Any, Callable[[Shape], Any]] = {
            gp_Pnt: self._getPnt,
            gp_Dir: self._getAxis,
            gp_Pln: self._getPln,
            gp_Lin: self._getLin,
            None: lambda x: True,  # dummy check for None marker
        }

        for a, t in zip(args, tcast(Tuple[Type[ConstraintMarker], ...], marker_types)):
            try:
                arg_check[t](a)
            except ValueError:
                raise ValueError(f"Unsupported entity {a} for constraint {kind}.")

        # check parameter
        if not instance_of(param, param_type) and param is not None:
            raise ValueError(
                f"Unsupported argument types {get_type(param)}, required {param_type}."
            )

        # check parameter conversion
        try:
            if param is not None and converter:
                converter(param)
        except Exception as e:
            raise ValueError(f"Exception {e} occured in the parameter conversion")

    def _getAxis(self, arg: Shape) -> gp_Dir:

        if isinstance(arg, Face):
            rv = arg.normalAt()
        elif isinstance(arg, Edge) and arg.geomType() != "CIRCLE":
            rv = arg.tangentAt()
        elif isinstance(arg, Edge) and arg.geomType() == "CIRCLE":
            rv = arg.normal()
        else:
            raise ValueError(f"Cannot construct Axis for {arg}")

        return rv.toDir()

    def _getPln(self, arg: Shape) -> gp_Pln:

        if isinstance(arg, Face):
            rv = gp_Pln(self._getPnt(arg), arg.normalAt().toDir())
        elif isinstance(arg, (Edge, Wire)):
            normal = arg.normal()
            origin = arg.Center()
            plane = Plane(origin, normal=normal)
            rv = plane.toPln()
        else:
            raise ValueError(f"Cannot construct a plane for {arg}.")

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

    def _getLin(self, arg: Shape) -> gp_Lin:

        if isinstance(arg, (Edge, Wire)):
            center = arg.Center()
            tangent = arg.tangentAt()
        else:
            raise ValueError(f"Cannot construct a plane for {arg}.")

        return gp_Lin(center.toPnt(), tangent.toDir())

    def toPODs(self) -> Tuple[Constraint, ...]:
        """
        Convert the constraint to a representation used by the solver.

        NB: Compound constraints are decomposed into simple ones.
        """

        # apply sublocation
        args = tuple(
            arg.located(loc * arg.location())
            for arg, loc in zip(self.args, self.sublocs)
        )

        markers: List[Tuple[ConstraintMarker, ...]]

        # convert to marker objects
        if self.kind == "Axis":
            markers = [(self._getAxis(args[0]), self._getAxis(args[1]),)]

        elif self.kind == "Point":
            markers = [(self._getPnt(args[0]), self._getPnt(args[1]))]

        elif self.kind == "Plane":
            markers = [
                (self._getAxis(args[0]), self._getAxis(args[1]),),
                (self._getPnt(args[0]), self._getPnt(args[1])),
            ]

        elif self.kind == "PointInPlane":
            markers = [(self._getPnt(args[0]), self._getPln(args[1]))]

        elif self.kind == "PointOnLine":
            markers = [(self._getPnt(args[0]), self._getLin(args[1]))]

        elif self.kind == "Fixed":
            markers = [(None,)]

        elif self.kind == "FixedPoint":
            markers = [(self._getPnt(args[0]),)]

        elif self.kind == "FixedAxis":
            markers = [(self._getAxis(args[0]),)]

        elif self.kind == "FixedRotation":
            markers = [(None,), (None,), (None,)]

        elif self.kind == "FixedRotationAxis":
            markers = [(None,)]

        else:
            raise ValueError(f"Unknown constraint kind {self.kind}")

        # specify kinds of the simple constraint
        if self.kind in CompoundConstraints:
            kinds, converter = CompoundConstraints[self.kind]
            params = converter(self.param,)
        else:
            kinds = (self.kind,)
            params = (self.param,)

        # builds the tuple and return
        return tuple(zip(markers, kinds, params))


# Cost functions of simple constraints


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


def point_on_line_cost(
    m1: gp_Pnt, m2: gp_Lin, t1: gp_Trsf, t2: gp_Trsf, val: Optional[float] = None,
) -> float:

    val = 0 if val is None else val

    m2_located = m2.Transformed(t2)

    return val - m2_located.Distance(m1.Transformed(t1))


def fixed_cost(m1: Type[None], t1: gp_Trsf, val: Optional[Type[None]] = None):

    return 0


def fixed_point_cost(m1: gp_Pnt, t1: gp_Trsf, val: Tuple[float, float, float]):

    return (m1.Transformed(t1).XYZ() - gp_XYZ(*val)).Modulus()


def fixed_axis_cost(m1: gp_Dir, t1: gp_Trsf, val: Tuple[float, float, float]):

    return DIR_SCALING * (m1.Transformed(t1).Angle(gp_Dir(*val)))


def fixed_rotation_axis_cost(m1: gp_Dir, t1: gp_Trsf, val: Tuple[int, float]):

    ix, v0 = val
    v = t1.GetRotation().GetEulerAngles(gp_Intrinsic_XYZ)[ix]

    return v - v0


# dictionary of individual constraint cost functions
costs: Dict[str, Callable[..., float]] = dict(
    Point=point_cost,
    Axis=axis_cost,
    PointInPlane=point_in_plane_cost,
    PointOnLine=point_on_line_cost,
    Fixed=fixed_cost,
    FixedPoint=fixed_point_cost,
    FixedAxis=fixed_axis_cost,
    FixedRotationAxis=fixed_rotation_axis_cost,
)

# Actual solver class


class ConstraintSolver(object):

    entities: List[DOF6]
    constraints: List[Tuple[Tuple[int, ...], Constraint]]
    locked: List[int]
    ne: int
    nc: int

    def __init__(
        self,
        entities: List[Location],
        constraints: List[Tuple[Tuple[int, ...], Constraint]],
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

        constraints = self.constraints
        ne = self.ne
        delta = DIFF_EPS * eye(NDOF)

        def f(x):
            """
            Function to be minimized
            """

            rv = 0

            transforms = [
                self._build_transform(*x[NDOF * i : NDOF * (i + 1)]) for i in range(ne)
            ]

            for ks, (ms, kind, params) in constraints:
                ts = tuple(
                    transforms[k] if k not in self.locked else gp_Trsf() for k in ks
                )
                cost = costs[kind]

                rv += cost(*ms, *ts, params) ** 2

            return rv

        def grad(x, rv):

            rv[:] = 0

            transforms = [
                self._build_transform(*x[NDOF * i : NDOF * (i + 1)]) for i in range(ne)
            ]

            transforms_delta = [
                self._build_transform(*(x[NDOF * i : NDOF * (i + 1)] + delta[j, :]))
                for i in range(ne)
                for j in range(NDOF)
            ]

            for ks, (ms, kind, params) in constraints:
                ts = tuple(
                    transforms[k] if k not in self.locked else gp_Trsf() for k in ks
                )
                cost = costs[kind]

                tmp_0 = cost(*ms, *ts, params)

                for ix, k in enumerate(ks):
                    if k in self.locked:
                        continue

                    for j in range(NDOF):
                        tkj = transforms_delta[k * NDOF + j]

                        ts_kj = ts[:ix] + (tkj,) + ts[ix + 1 :]
                        tmp_kj = cost(*ms, *ts_kj, params)

                        rv[k * NDOF + j] += 2 * tmp_0 * (tmp_kj - tmp_0) / DIFF_EPS

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
