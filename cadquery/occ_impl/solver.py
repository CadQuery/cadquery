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

from math import radians, pi
from typish import instance_of, get_type

import casadi as ca

from OCP.gp import (
    gp_Vec,
    gp_Pln,
    gp_Dir,
    gp_Pnt,
    gp_Trsf,
    gp_Quaternion,
    gp_Lin,
    gp_Extrinsic_XYZ,
)

from OCP.BRepTools import BRepTools
from OCP.Precision import Precision

from .geom import Location, Vector, Plane
from .shapes import Shape, Face, Edge, Wire
from ..types import Real

# type definitions

NoneType = type(None)

DOF6 = Tuple[Tuple[float, float, float], Tuple[float, float, float]]
ConstraintMarker = Union[gp_Pln, gp_Dir, gp_Pnt, gp_Lin, None]

UnaryConstraintKind = Literal["Fixed", "FixedPoint", "FixedAxis", "FixedRotation"]
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
    "FixedRotation": (
        1,
        (None,),
        Tuple[Real, Real, Real],
        lambda x: tuple(map(radians, x)),
    ),
}

# translation table for compound constraints {name : (name, ...), converter}
CompoundConstraints: Dict[
    ConstraintKind, Tuple[Tuple[ConstraintKind, ...], Callable[[Any], Tuple[Any, ...]]]
] = {
    "Plane": (("Axis", "Point"), lambda x: (radians(x) if x is not None else None, 0)),
}

# constraint POD type
Constraint = Tuple[
    Tuple[ConstraintMarker, ...], ConstraintKind, Optional[Any],
]

NDOF_V = 3
NDOF_Q = 3
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
def Quaternion(R):

    m = ca.sumsqr(R)

    u = 2 * R / (1 + m)
    s = (1 - m) / (1 + m)

    return s, u


def Rotate(v, R):

    s, u = Quaternion(R)

    return 2 * ca.dot(u, v) * u + (s ** 2 - ca.dot(u, u)) * v + 2 * s * ca.cross(u, v)


def Transform(v, T, R):

    return Rotate(v, R) + T


def point_cost(
    problem,
    m1: gp_Pnt,
    m2: gp_Pnt,
    T1_0,
    R1_0,
    T2_0,
    R2_0,
    T1,
    R1,
    T2,
    R2,
    val: Optional[float] = None,
    scale: float = 1,
) -> float:

    val = 0 if val is None else val

    m1_dm = ca.DM((m1.X(), m1.Y(), m1.Z()))
    m2_dm = ca.DM((m2.X(), m2.Y(), m2.Z()))

    dummy = (
        Transform(m1_dm, T1_0 + T1, R1_0 + R1) - Transform(m2_dm, T2_0 + T2, R2_0 + R2)
    ) / scale

    if val == 0:
        return ca.sumsqr(dummy)

    return (ca.sumsqr(dummy) - (val / scale) ** 2) ** 2


def axis_cost(
    problem,
    m1: gp_Dir,
    m2: gp_Dir,
    T1_0,
    R1_0,
    T2_0,
    R2_0,
    T1,
    R1,
    T2,
    R2,
    val: Optional[float] = None,
    scale: float = 1,
) -> float:

    val = pi if val is None else val

    m1_dm = ca.DM((m1.X(), m1.Y(), m1.Z()))
    m2_dm = ca.DM((m2.X(), m2.Y(), m2.Z()))

    d1, d2 = (Rotate(m1_dm, R1_0 + R1), Rotate(m2_dm, R2_0 + R2))

    if val == 0:
        dummy = d1 - d2

        return ca.sumsqr(dummy)

    elif val == pi:
        dummy = d1 + d2

        return ca.sumsqr(dummy)

    dummy = ca.dot(d1, d2) - ca.cos(val)

    return dummy ** 2


def point_in_plane_cost(
    problem,
    m1: gp_Pnt,
    m2: gp_Pln,
    T1_0,
    R1_0,
    T2_0,
    R2_0,
    T1,
    R1,
    T2,
    R2,
    val: Optional[float] = None,
    scale: float = 1,
) -> float:

    val = 0 if val is None else val

    m1_dm = ca.DM((m1.X(), m1.Y(), m1.Z()))

    m2_dir = m2.Axis().Direction()
    m2_pnt = m2.Axis().Location().Translated(val * gp_Vec(m2_dir))

    m2_dir_dm = ca.DM((m2_dir.X(), m2_dir.Y(), m2_dir.Z()))
    m2_pnt_dm = ca.DM((m2_pnt.X(), m2_pnt.Y(), m2_pnt.Z()))

    dummy = (
        ca.dot(
            Rotate(m2_dir_dm, R2_0 + R2),
            Transform(m2_pnt_dm, T2_0 + T2, R2_0 + R2)
            - Transform(m1_dm, T1_0 + T1, R1_0 + R1),
        )
        / scale
    )

    return dummy ** 2


def point_on_line_cost(
    problem,
    m1: gp_Pnt,
    m2: gp_Lin,
    T1_0,
    R1_0,
    T2_0,
    R2_0,
    T1,
    R1,
    T2,
    R2,
    val: Optional[float] = None,
    scale: float = 1,
) -> float:

    val = 0 if val is None else val

    m1_dm = ca.DM((m1.X(), m1.Y(), m1.Z()))

    m2_dir = m2.Direction()
    m2_pnt = m2.Location()

    m2_dir_dm = ca.DM((m2_dir.X(), m2_dir.Y(), m2_dir.Z()))
    m2_pnt_dm = ca.DM((m2_pnt.X(), m2_pnt.Y(), m2_pnt.Z()))

    d = Transform(m1_dm, T1_0 + T1, R1_0 + R1) - Transform(
        m2_pnt_dm, T2_0 + T2, R2_0 + R2
    )
    n = Rotate(m2_dir_dm, R2_0 + R2)

    dummy = (d - n * ca.dot(d, n)) / scale

    if val == 0:
        return ca.sumsqr(dummy)

    return (ca.sumsqr(dummy) - val) ** 2


# dummy cost, fixed constraint is handled on variable level
def fixed_cost(
    problem,
    m1: Type[None],
    T1_0,
    R1_0,
    T1,
    R1,
    val: Optional[Type[None]] = None,
    scale: float = 1,
):

    return None


def fixed_point_cost(
    problem,
    m1: gp_Pnt,
    T1_0,
    R1_0,
    T1,
    R1,
    val: Tuple[float, float, float],
    scale: float = 1,
):

    m1_dm = ca.DM((m1.X(), m1.Y(), m1.Z()))

    dummy = (Transform(m1_dm, T1_0 + T1, R1_0 + R1) - ca.DM(val)) / scale

    return ca.sumsqr(dummy)


def fixed_axis_cost(
    problem,
    m1: gp_Dir,
    T1_0,
    R1_0,
    T1,
    R1,
    val: Tuple[float, float, float],
    scale: float = 1,
):

    m1_dm = ca.DM((m1.X(), m1.Y(), m1.Z()))
    m_val = ca.DM(val) / ca.norm_2(ca.DM(val))

    dummy = Rotate(m1_dm, R1_0 + R1) - m_val

    return ca.sumsqr(dummy)


def fixed_rotation_cost(
    problem,
    m1: Type[None],
    T1_0,
    R1_0,
    T1,
    R1,
    val: Tuple[float, float, float],
    scale: float = 1,
):

    q = gp_Quaternion()
    q.SetEulerAngles(gp_Extrinsic_XYZ, *val)
    q_dm = ca.DM((q.W(), q.X(), q.Y(), q.Z()))

    dummy = 1 - ca.dot(ca.vertcat(*Quaternion(R1_0 + R1)), q_dm) ** 2

    return dummy


# dictionary of individual constraint cost functions
costs: Dict[str, Callable[..., float]] = dict(
    Point=point_cost,
    Axis=axis_cost,
    PointInPlane=point_in_plane_cost,
    PointOnLine=point_on_line_cost,
    Fixed=fixed_cost,
    FixedPoint=fixed_point_cost,
    FixedAxis=fixed_axis_cost,
    FixedRotation=fixed_rotation_cost,
)

scaling: Dict[str, bool] = dict(
    Point=True,
    Axis=False,
    PointInPlane=True,
    PointOnLine=True,
    Fixed=False,
    FixedPoint=True,
    FixedAxis=False,
    FixedRotation=False,
)

# Actual solver class


class ConstraintSolver(object):

    opti: ca.Opti
    variables: List[Tuple[ca.MX, ca.MX]]
    starting_points: List[Tuple[ca.MX, ca.MX]]
    constraints: List[Tuple[Tuple[int, ...], Constraint]]
    locked: List[int]
    ne: int
    nc: int
    scale: float

    def __init__(
        self,
        entities: List[Location],
        constraints: List[Tuple[Tuple[int, ...], Constraint]],
        locked: List[int] = [],
        scale: float = 1,
    ):

        self.scale = scale
        self.opti = opti = ca.Opti()
        self.variables = [
            (scale * opti.variable(NDOF_V), opti.variable(NDOF_Q))
            if i not in locked
            else (opti.parameter(NDOF_V), opti.parameter(NDOF_Q))
            for i, _ in enumerate(entities)
        ]
        self.start_points = [
            (opti.parameter(NDOF_V), opti.parameter(NDOF_Q)) for _ in entities
        ]

        # initialize, add the unit quaternion constraints and handle locked
        for i, ((T, R), (T0, R0), loc) in enumerate(
            zip(self.variables, self.start_points, entities)
        ):
            T0val, R0val = self._locToDOF6(loc)

            opti.set_value(T0, T0val)
            opti.set_value(R0, R0val)

            if i in locked:
                opti.set_value(T, (0, 0, 0))
                opti.set_value(R, (0, 0, 0))
            else:
                opti.set_initial(T, (0.0, 0.0, 0.0))
                opti.set_initial(R, (1e-2, 1e-2, 1e-2))

        self.constraints = constraints

        # additional book-keeping
        self.ne = len(entities)
        self.locked = locked
        self.nc = len(self.constraints)

    @staticmethod
    def _locToDOF6(loc: Location) -> DOF6:

        Tr = loc.wrapped.Transformation()
        v = Tr.TranslationPart()
        q = Tr.GetRotation()

        alpha_2 = (1 - q.W()) / (1 + q.W())
        a = (alpha_2 + 1) * q.X() / 2
        b = (alpha_2 + 1) * q.Y() / 2
        c = (alpha_2 + 1) * q.Z() / 2

        return (v.X(), v.Y(), v.Z()), (a, b, c)

    def _build_transform(self, T: ca.MX, R: ca.MX) -> gp_Trsf:

        opti = self.opti

        rv = gp_Trsf()

        a, b, c = opti.value(R)
        m = a ** 2 + b ** 2 + c ** 2

        rv.SetRotation(
            gp_Quaternion(
                2 * a / (m + 1), 2 * b / (m + 1), 2 * c / (m + 1), (1 - m) / (m + 1),
            )
        )
        rv.SetTranslationPart(gp_Vec(*opti.value(T)))

        return rv

    def solve(self) -> Tuple[List[Location], Dict[str, Any]]:

        opti = self.opti

        constraints = self.constraints
        variables = self.variables
        start_points = self.start_points

        # construct a penalty term
        penalty = 0.0

        for T, R in variables:
            penalty += ca.sumsqr(ca.vertcat(T / self.scale, R))

        # construct the objective
        objective = 0.0
        for ks, (ms, kind, params) in constraints:

            # select the relevant variables and starting points
            s_ks: List[ca.DM] = []
            v_ks: List[ca.MX] = []

            for k in ks:
                s_ks.extend(start_points[k])
                v_ks.extend(variables[k])

            c = costs[kind](
                opti,
                *ms,
                *s_ks,
                *v_ks,
                params,
                scale=self.scale if scaling[kind] else 1,
            )

            if c is not None:
                objective += c

        opti.minimize(objective + 1e-16 * penalty)

        # solve
        opti.solver(
            "ipopt",
            {"print_time": False},
            {
                "acceptable_obj_change_tol": 1e-12,
                "acceptable_iter": 1,
                "tol": 1e-14,
                "hessian_approximation": "exact",
                "nlp_scaling_method": "none",
                "honor_original_bounds": "yes",
                "bound_relax_factor": 0,
                "print_level": 5,
                "print_timing_statistics": "no",
                "linear_solver": "mumps",
            },
        )
        sol = opti.solve_limited()

        result = sol.stats()
        result["opti"] = opti  # this might be removed in the future

        locs = [
            Location(self._build_transform(T + T0, R + R0))
            for (T, R), (T0, R0) in zip(variables, start_points)
        ]

        return locs, result
