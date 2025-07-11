from typing import (
    Union,
    Any,
    Optional,
    Literal,
    Type,
)
from dataclasses import dataclass
from math import radians, pi
from abc import ABC, abstractmethod

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

# Type definitions
NoneType = type(None)

DOF6 = tuple[tuple[float, float, float], tuple[float, float, float]]
ConstraintMarker = Union[gp_Pln, gp_Dir, gp_Pnt, gp_Lin, None]

UnaryConstraintKind = Literal["Fixed", "FixedPoint", "FixedAxis", "FixedRotation"]
BinaryConstraintKind = Literal["Plane", "Point", "Axis", "PointInPlane", "PointOnLine"]
ConstraintKind = Union[UnaryConstraintKind, BinaryConstraintKind]

# Constants for solver
NDOF_V = 3  # Number of degrees of freedom for translation
NDOF_Q = 3  # Number of degrees of freedom for rotation
NDOF = 6  # Total degrees of freedom
DIR_SCALING = 1e2  # Scaling factor for directions
DIFF_EPS = 1e-10  # Epsilon for finite differences
TOL = 1e-12  # Tolerance for convergence
MAXITER = 2000  # Maximum number of iterations

# Helper functions for constraint cost calculations
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


def loc_to_dof6(loc: Location) -> DOF6:
    """Convert a Location to a 6-DOF representation (translation and rotation)."""
    Tr = loc.wrapped.Transformation()
    v = Tr.TranslationPart()
    q = Tr.GetRotation()

    alpha_2 = (1 - q.W()) / (1 + q.W())
    a = (alpha_2 + 1) * q.X() / 2
    b = (alpha_2 + 1) * q.Y() / 2
    c = (alpha_2 + 1) * q.Z() / 2

    return (v.X(), v.Y(), v.Z()), (a, b, c)


def getDir(arg: Shape) -> gp_Dir:
    if isinstance(arg, Face):
        rv = arg.normalAt()
    elif isinstance(arg, Edge) and arg.geomType() != "CIRCLE":
        rv = arg.tangentAt()
    elif isinstance(arg, Edge) and arg.geomType() == "CIRCLE":
        rv = arg.normal()
    else:
        raise ValueError(f"Cannot construct Axis for {arg}")

    return rv.toDir()


def getPln(arg: Shape) -> gp_Pln:
    if isinstance(arg, Face):
        rv = gp_Pln(getPnt(arg), arg.normalAt().toDir())
    elif isinstance(arg, (Edge, Wire)):
        normal = arg.normal()
        origin = arg.Center()
        plane = Plane(origin, normal=normal)
        rv = plane.toPln()
    else:
        raise ValueError(f"Cannot construct a plane for {arg}.")

    return rv


def getPnt(arg: Shape) -> gp_Pnt:
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


def getLin(arg: Shape) -> gp_Lin:
    if isinstance(arg, (Edge, Wire)):
        center = arg.Center()
        tangent = arg.tangentAt()
    else:
        raise ValueError(f"Cannot construct a plane for {arg}.")

    return gp_Lin(center.toPnt(), tangent.toDir())


@dataclass
class CostParams:
    """Parameters passed to constraint cost functions.
    
    This class standardizes the parameters passed to all constraint cost functions,
    making them compatible with any number of objects involved in the constraint.
    """

    problem: ca.Opti
    markers: list[Union[gp_Pnt, gp_Dir, gp_Pln, gp_Lin, None]]
    initial_translations: list[ca.DM]  # T0 values for each object
    initial_rotations: list[ca.DM]  # R0 values for each object
    translations: list[ca.MX]  # T values for each object
    rotations: list[ca.MX]  # R values for each object
    param: Optional[Any] = None  # Optional constraint-specific parameter
    scale: float = 1.0  # Scale factor for the optimization

    def __post_init__(self):
        """Validate that all lists have the same length."""
        n_objects = len(self.markers)
        if not all(
            len(lst) == n_objects
            for lst in [
                self.initial_translations,
                self.initial_rotations,
                self.translations,
                self.rotations,
            ]
        ):
            raise ValueError("All parameter lists must have the same length")


class BaseConstraint(ABC):
    """Base class for all constraints."""

    kind: ConstraintKind
    _registry: dict[ConstraintKind, Type["BaseConstraint"]] = {}

    def __init_subclass__(cls, **kwargs):
        """Register constraint classes by their kind."""
        super().__init_subclass__(**kwargs)
        if hasattr(cls, "kind"):
            BaseConstraint._registry[cls.kind] = cls

    def __init__(
        self,
        objects: tuple[str, ...],
        args: tuple[Shape, ...],
        sublocs: tuple[Location, ...],
        param: Any = None,
    ):
        """
        Initialize a constraint.

        :param objects: Tuple of object names involved in the constraint
        :param args: Tuple of shapes involved in the constraint
        :param sublocs: Tuple of locations for each object
        :param param: Optional constraint-specific parameter
        """
        self.objects = objects
        self.args = args
        self.sublocs = sublocs
        self.param = param

    @classmethod
    def get_constraint_class(cls, kind: ConstraintKind) -> Type["BaseConstraint"]:
        """Get the constraint class for a given kind."""
        return cls._registry[kind]


class ConstraintSpec(BaseConstraint, ABC):
    """
    Geometrical constraint specification between two shapes of an assembly.
    """

    objects: tuple[str, ...]  # Names of objects involved in the constraint
    args: tuple[Shape, ...]  # Shapes involved in the constraint
    sublocs: tuple[Location, ...]  # Locations of objects in the constraint
    kind: ConstraintKind  # Type of constraint
    param: Any  # Constraint-specific parameter
    arity: int = 0  # Number of objects involved in the constraint
    marker_types: tuple[
        Type[ConstraintMarker], ...
    ] = ()  # Types of geometric markers needed
    param_type: Optional[Any] = None  # Type of the constraint parameter

    def __init__(
        self,
        objects: tuple[str, ...],
        args: tuple[Shape, ...],
        sublocs: tuple[Location, ...],
        param: Any = None,
    ):
        super().__init__(objects, args, sublocs, param)
        self._validate(args)
        self.validate_param(param)
        self.param = self.convert_param(param)

    @staticmethod
    @abstractmethod
    def cost(params: CostParams) -> float:
        """Cost function for the constraint.
        
        :param params: CostParams object containing the necessary parameters
        :return: float value of the cost function
        """
        pass

    @abstractmethod
    def get_markers(self) -> tuple[ConstraintMarker, ...]:
        """Get the geometric markers for this constraint.
        
        :return: tuple of geometric markers
        """
        pass

    def get_param(self) -> Optional[Any]:
        """Get the parameter for this constraint.
        
        :return: constraint parameter or None if not applicable
        """
        return self.param

    def validate_param(self, param: Any) -> None:
        """Validate the constraint parameter.
        
        :param param: Parameter to validate
        :raises ValueError: If parameter is invalid
        """
        pass

    def convert_param(self, param: Any) -> Any:
        """Convert the parameter to the required type.
        
        :param param: Parameter to convert
        :return: Converted parameter
        """
        return param

    def _validate(self, args: tuple[Shape, ...]) -> None:
        """Validate arguments for the constraint.
        
        Args:
            args: tuple of shapes to validate
            
        Raises:
            ValueError: If number of arguments doesn't match arity or if arguments are of wrong type
        """
        # Validate number of arguments matches constraint arity
        if self.arity != len(args):
            raise ValueError(
                f"Invalid number of entities for constraint {self.kind}. "
                f"Provided {len(args)}, required {self.arity}."
            )

        # Define validation functions for each marker type
        MARKER_VALIDATORS = {
            gp_Pnt: getPnt,  # Point validation
            gp_Dir: getDir,  # Direction validation
            gp_Pln: getPln,  # Plane validation
            gp_Lin: getLin,  # Line validation
            NoneType: lambda _: True,  # No validation needed for None markers
        }

        # Validate each argument against its expected marker type
        for arg, marker_type in zip(args, self.marker_types):
            try:
                MARKER_VALIDATORS[marker_type](arg)
            except ValueError:
                raise ValueError(
                    f"Unsupported entity {arg} for constraint {self.kind}. "
                    f"Expected type: {marker_type.__name__}"
                )


class CompoundConstraintSpec(BaseConstraint, ABC):
    """Base class for compound constraints that consist of multiple simple constraints."""

    kind: ConstraintKind

    @abstractmethod
    def expand(self) -> list[ConstraintSpec]:
        """Expand the compound constraint into its constituent simple constraints."""
        pass


class PointConstraint(ConstraintSpec):
    """Point constraint between two points."""

    arity = 2
    marker_types = (gp_Pnt, gp_Pnt)
    kind = "Point"
    param_type = Optional[float]  # Distance between points

    def validate_param(self, param: Optional[float]) -> None:
        """Validate that the parameter is a numeric distance.
        
        :param param: Optional distance between points
        :raises ValueError: If parameter is not numeric
        """
        if param is not None and not isinstance(param, (int, float)):
            raise ValueError(
                f"Point constraint parameter must be numeric, got {type(param)}"
            )

    def get_markers(self) -> tuple[ConstraintMarker, ...]:
        """Get the geometric markers for this constraint."""
        # apply sublocation
        args = tuple(
            arg.located(loc * arg.location())
            for arg, loc in zip(self.args, self.sublocs)
        )

        return (getPnt(args[0]), getPnt(args[1]))

    @staticmethod
    def cost(params: CostParams) -> float:
        """Cost function for Point constraint.
        
        Minimizes the distance between two points.
        If val is provided, enforces that distance to be val.
        """
        m1, m2 = params.markers
        if not isinstance(m1, gp_Pnt) or not isinstance(m2, gp_Pnt):
            raise TypeError("Point constraint requires two points as markers")

        T1_0, T2_0 = params.initial_translations
        R1_0, R2_0 = params.initial_rotations
        T1, T2 = params.translations
        R1, R2 = params.rotations
        val = 0 if params.param is None else params.param
        scale = params.scale

        m1_dm = ca.DM((m1.X(), m1.Y(), m1.Z()))
        m2_dm = ca.DM((m2.X(), m2.Y(), m2.Z()))

        point_error = (
            Transform(m1_dm, T1_0 + T1, R1_0 + R1)
            - Transform(m2_dm, T2_0 + T2, R2_0 + R2)
        ) / scale

        if val == 0:
            return ca.sumsqr(point_error)

        return (ca.sumsqr(point_error) - (val / scale) ** 2) ** 2


class AxisConstraint(ConstraintSpec):
    """Axis constraint between two axes."""

    arity = 2
    marker_types = (gp_Dir, gp_Dir)
    kind = "Axis"
    param_type = Optional[float]  # Angle between axes in degrees

    def validate_param(self, param: Optional[float]) -> None:
        """Validate that the parameter is a numeric angle.
        
        :param param: Optional angle between axes in degrees
        :raises ValueError: If parameter is not numeric
        """
        if param is not None and not isinstance(param, (int, float)):
            raise ValueError(
                f"Axis constraint parameter must be numeric, got {type(param)}"
            )

    def convert_param(self, param: Optional[float]) -> Optional[float]:
        """Convert angle from degrees to radians.
        
        :param param: Angle in degrees
        :return: Angle in radians
        """
        return radians(param) if param is not None else None

    def get_markers(self) -> tuple[ConstraintMarker, ...]:
        """Get the geometric markers for this constraint."""
        # apply sublocation
        args = tuple(
            arg.located(loc * arg.location())
            for arg, loc in zip(self.args, self.sublocs)
        )

        return (getDir(args[0]), getDir(args[1]))

    @staticmethod
    def cost(params: CostParams) -> float:
        """Cost function for Axis constraint.
        
        Minimizes the angle between two axes.
        If val is provided, enforces that angle to be val.
        """
        m1, m2 = params.markers
        if not isinstance(m1, gp_Dir) or not isinstance(m2, gp_Dir):
            raise TypeError("Axis constraint requires two directions as markers")

        R1_0, R2_0 = params.initial_rotations
        R1, R2 = params.rotations
        val = pi if params.param is None else params.param

        m1_dm = ca.DM((m1.X(), m1.Y(), m1.Z()))
        m2_dm = ca.DM((m2.X(), m2.Y(), m2.Z()))

        d1, d2 = (Rotate(m1_dm, R1_0 + R1), Rotate(m2_dm, R2_0 + R2))

        if val == 0:
            axis_error = d1 - d2
            return ca.sumsqr(axis_error)

        elif val == pi:
            axis_error = d1 + d2
            return ca.sumsqr(axis_error)

        axis_error = ca.dot(d1, d2) - ca.cos(val)
        return axis_error ** 2


class PointInPlaneConstraint(ConstraintSpec):
    """Point in plane constraint."""

    arity = 2
    marker_types = (gp_Pnt, gp_Pln)
    kind = "PointInPlane"
    param_type = Optional[float]  # Distance from point to plane

    def validate_param(self, param: Optional[float]) -> None:
        """Validate that the parameter is a numeric distance.
        
        :param param: Optional distance from point to plane
        :raises ValueError: If parameter is not numeric
        """
        if param is not None and not isinstance(param, (int, float)):
            raise ValueError(
                f"PointInPlane constraint parameter must be numeric, got {type(param)}"
            )

    def get_markers(self) -> tuple[ConstraintMarker, ...]:
        """Get the geometric markers for this constraint."""
        # apply sublocation
        args = tuple(
            arg.located(loc * arg.location())
            for arg, loc in zip(self.args, self.sublocs)
        )

        return (getPnt(args[0]), getPln(args[1]))

    @staticmethod
    def cost(params: CostParams) -> float:
        """Cost function for PointInPlane constraint.
        
        Minimizes the distance between a point and a plane.
        If val is provided, enforces that distance to be val.
        """
        m1, m2 = params.markers
        if not isinstance(m1, gp_Pnt) or not isinstance(m2, gp_Pln):
            raise TypeError(
                "PointInPlane constraint requires a point and a plane as markers"
            )

        T1_0, T2_0 = params.initial_translations
        R1_0, R2_0 = params.initial_rotations
        T1, T2 = params.translations
        R1, R2 = params.rotations
        val = 0 if params.param is None else params.param
        scale = params.scale

        m1_dm = ca.DM((m1.X(), m1.Y(), m1.Z()))

        m2_dir = m2.Axis().Direction()
        m2_pnt = m2.Axis().Location().Translated(val * gp_Vec(m2_dir))

        m2_dir_dm = ca.DM((m2_dir.X(), m2_dir.Y(), m2_dir.Z()))
        m2_pnt_dm = ca.DM((m2_pnt.X(), m2_pnt.Y(), m2_pnt.Z()))

        plane_error = (
            ca.dot(
                Rotate(m2_dir_dm, R2_0 + R2),
                Transform(m2_pnt_dm, T2_0 + T2, R2_0 + R2)
                - Transform(m1_dm, T1_0 + T1, R1_0 + R1),
            )
            / scale
        )

        return plane_error ** 2


class PointOnLineConstraint(ConstraintSpec):
    """Point on line constraint."""

    arity = 2
    marker_types = (gp_Pnt, gp_Lin)
    kind = "PointOnLine"
    param_type = Optional[float]  # Distance from point to line

    def validate_param(self, param: Optional[float]) -> None:
        """Validate that the parameter is a numeric distance.
        
        :param param: Optional distance from point to line
        :raises ValueError: If parameter is not numeric
        """
        if param is not None and not isinstance(param, (int, float)):
            raise ValueError(
                f"PointOnLine constraint parameter must be numeric, got {type(param)}"
            )

    def get_markers(self) -> tuple[ConstraintMarker, ...]:
        """Get the geometric markers for this constraint."""
        # apply sublocation
        args = tuple(
            arg.located(loc * arg.location())
            for arg, loc in zip(self.args, self.sublocs)
        )

        return (getPnt(args[0]), getLin(args[1]))

    @staticmethod
    def cost(params: CostParams) -> float:
        """Cost function for PointOnLine constraint.
        
        Minimizes the distance between a point and a line.
        If val is provided, enforces that distance to be val.
        """
        m1, m2 = params.markers
        if not isinstance(m1, gp_Pnt) or not isinstance(m2, gp_Lin):
            raise TypeError(
                "PointOnLine constraint requires a point and a line as markers"
            )

        T1_0, T2_0 = params.initial_translations
        R1_0, R2_0 = params.initial_rotations
        T1, T2 = params.translations
        R1, R2 = params.rotations
        val = 0 if params.param is None else params.param
        scale = params.scale

        m1_dm = ca.DM((m1.X(), m1.Y(), m1.Z()))

        m2_dir = m2.Direction()
        m2_pnt = m2.Location()

        m2_dir_dm = ca.DM((m2_dir.X(), m2_dir.Y(), m2_dir.Z()))
        m2_pnt_dm = ca.DM((m2_pnt.X(), m2_pnt.Y(), m2_pnt.Z()))

        d = Transform(m1_dm, T1_0 + T1, R1_0 + R1) - Transform(
            m2_pnt_dm, T2_0 + T2, R2_0 + R2
        )
        n = Rotate(m2_dir_dm, R2_0 + R2)

        line_error = (d - n * ca.dot(d, n)) / scale

        if val == 0:
            return ca.sumsqr(line_error)

        return (ca.sumsqr(line_error) - val) ** 2


class FixedConstraint(ConstraintSpec):
    """Fixed constraint."""

    arity = 1
    marker_types = (NoneType,)
    kind = "Fixed"
    param_type = None  # No parameters allowed

    def validate_param(self, param: None) -> None:
        """Validate that no parameter is provided.
        
        :param param: Must be None
        :raises ValueError: If parameter is not None
        """
        if param is not None:
            raise ValueError("Fixed constraint cannot have parameters")

    def get_markers(self) -> tuple[ConstraintMarker, ...]:
        """Get the geometric markers for this constraint."""
        return (None,)

    @staticmethod
    def cost(params: CostParams) -> float:
        """Cost function for Fixed constraint.
        
        This is a dummy cost function as fixed constraints are handled at the variable level.
        Returns 0.0 to satisfy the type system.
        """
        m1 = params.markers[0]
        if m1 is not None:
            raise TypeError("Fixed constraint should have no markers")
        return 0.0


class FixedPointConstraint(ConstraintSpec):
    """Fixed point constraint."""

    arity = 1
    marker_types = (gp_Pnt,)
    kind = "FixedPoint"
    param_type = tuple[float, float, float]  # 3D coordinates (x, y, z)

    def validate_param(self, param: tuple[float, float, float]) -> None:
        """Validate that the parameter is a 3D point.
        
        :param param: 3D coordinates (x, y, z)
        :raises ValueError: If parameter is not a 3D point
        """
        if (
            not isinstance(param, (tuple, list))
            or len(param) != 3
            or not all(isinstance(x, (int, float)) for x in param)
        ):
            raise ValueError(
                "FixedPoint constraint parameter must be tuple/list of 3 numbers"
            )

    def get_markers(self) -> tuple[ConstraintMarker, ...]:
        """Get the geometric markers for this constraint."""
        # apply sublocation
        args = tuple(
            arg.located(loc * arg.location())
            for arg, loc in zip(self.args, self.sublocs)
        )

        return (getPnt(args[0]),)

    @staticmethod
    def cost(params: CostParams) -> float:
        """Cost function for FixedPoint constraint.
        
        Fixes a point at a specific location in space.
        """
        m1 = params.markers[0]
        if not isinstance(m1, gp_Pnt):
            raise TypeError("FixedPoint constraint requires a point as marker")

        T1_0 = params.initial_translations[0]
        R1_0 = params.initial_rotations[0]
        T1 = params.translations[0]
        R1 = params.rotations[0]
        val = params.param
        scale = params.scale

        m1_dm = ca.DM((m1.X(), m1.Y(), m1.Z()))

        point_error = (Transform(m1_dm, T1_0 + T1, R1_0 + R1) - ca.DM(val)) / scale

        return ca.sumsqr(point_error)


class FixedAxisConstraint(ConstraintSpec):
    """Fixed axis constraint."""

    arity = 1
    marker_types = (gp_Dir,)
    kind = "FixedAxis"
    param_type = tuple[float, float, float]  # 3D direction vector (x, y, z)

    def validate_param(self, param: tuple[float, float, float]) -> None:
        """Validate that the parameter is a 3D direction vector.
        
        :param param: 3D direction vector (x, y, z)
        :raises ValueError: If parameter is not a 3D vector
        """
        if (
            not isinstance(param, (tuple, list))
            or len(param) != 3
            or not all(isinstance(x, (int, float)) for x in param)
        ):
            raise ValueError(
                "FixedAxis constraint parameter must be tuple/list of 3 numbers"
            )

    def get_markers(self) -> tuple[ConstraintMarker, ...]:
        """Get the geometric markers for this constraint."""
        # apply sublocation
        args = tuple(
            arg.located(loc * arg.location())
            for arg, loc in zip(self.args, self.sublocs)
        )

        return (getDir(args[0]),)

    @staticmethod
    def cost(params: CostParams) -> float:
        """Cost function for FixedAxis constraint.
        
        Fixes an axis in a specific direction.
        """
        m1 = params.markers[0]
        if not isinstance(m1, gp_Dir):
            raise TypeError("FixedAxis constraint requires a direction as marker")

        R1_0 = params.initial_rotations[0]
        R1 = params.rotations[0]
        val = params.param

        m1_dm = ca.DM((m1.X(), m1.Y(), m1.Z()))
        m_val = ca.DM(val) / ca.norm_2(ca.DM(val))

        axis_error = Rotate(m1_dm, R1_0 + R1) - m_val

        return ca.sumsqr(axis_error)


class FixedRotationConstraint(ConstraintSpec):
    """Fixed rotation constraint."""

    arity = 1
    marker_types = (NoneType,)
    kind = "FixedRotation"
    param_type = tuple[float, float, float]  # 3D rotation angles in degrees (x, y, z)

    def validate_param(self, param: tuple[float, float, float]) -> None:
        """Validate that the parameter is a 3D rotation vector.
        
        :param param: 3D rotation angles in degrees (x, y, z)
        :raises ValueError: If parameter is not a 3D vector
        """
        if (
            not isinstance(param, (tuple, list))
            or len(param) != 3
            or not all(isinstance(x, (int, float)) for x in param)
        ):
            raise ValueError(
                "FixedRotation constraint parameter must be tuple/list of 3 numbers"
            )

    def convert_param(
        self, param: Optional[tuple[float, float, float]]
    ) -> Optional[tuple[float, float, float]]:
        """Convert rotation angles from degrees to radians.
        
        :param param: Rotation angles in degrees
        :return: Rotation angles in radians
        """
        if param is None:
            return None
        x, y, z = param
        return (radians(x), radians(y), radians(z))

    def get_markers(self) -> tuple[ConstraintMarker, ...]:
        """Get the geometric markers for this constraint."""
        return (None,)

    @staticmethod
    def cost(params: CostParams) -> float:
        """Cost function for FixedRotation constraint.
        
        Fixes the rotation of an object using Euler angles.
        """
        m1 = params.markers[0]
        if m1 is not None:
            raise TypeError("FixedRotation constraint should have no markers")

        R1_0 = params.initial_rotations[0]
        R1 = params.rotations[0]
        val = (0.0, 0.0, 0.0) if params.param is None else tuple(params.param)

        q = gp_Quaternion()
        q.SetEulerAngles(gp_Extrinsic_XYZ, *val)
        q_dm = ca.DM((q.W(), q.X(), q.Y(), q.Z()))

        rotation_error = 1 - ca.dot(ca.vertcat(*Quaternion(R1_0 + R1)), q_dm) ** 2

        return rotation_error


class PlaneConstraint(CompoundConstraintSpec):
    """Plane constraint (compound of Axis and Point constraints)."""

    kind: ConstraintKind = "Plane"

    def expand(self) -> list[ConstraintSpec]:
        """Expand into Axis and Point constraints."""
        # Create Axis constraint
        axis_constraint = AxisConstraint(
            objects=self.objects, args=self.args, sublocs=self.sublocs, param=self.param
        )

        # Create Point constraint
        point_constraint = PointConstraint(
            objects=self.objects,
            args=self.args,
            sublocs=self.sublocs,
            param=0,  # Distance between points should be 0
        )

        return [axis_constraint, point_constraint]


# Actual solver class
class ConstraintSolver(object):
    opti: ca.Opti
    variables: list[tuple[ca.MX, ca.MX]]
    initial_points: list[tuple[ca.MX, ca.MX]]
    constraints: list[BaseConstraint]
    locked: list[int]
    ne: int
    nc: int
    scale: float
    object_indices: dict[str, int]

    def __init__(
        self,
        entities: list[Location],
        constraints: list[BaseConstraint],
        object_indices: dict[str, int],
        locked: list[int] = [],
        scale: float = 1,
    ):
        """
        Initialize the constraint solver.

        :param entities: list of locations for each entity
        :param constraints: list of constraint specifications
        :param object_indices: dictionary mapping object names to their indices
        :param locked: list of indices of locked entities
        :param scale: Scale factor for the optimization
        """
        self.scale = scale
        self.opti = opti = ca.Opti()
        self.object_indices = object_indices
        self.variables = [
            (scale * opti.variable(NDOF_V), opti.variable(NDOF_Q))
            if i not in locked
            else (opti.parameter(NDOF_V), opti.parameter(NDOF_Q))
            for i, _ in enumerate(entities)
        ]
        self.initial_points = [
            (opti.parameter(NDOF_V), opti.parameter(NDOF_Q)) for _ in entities
        ]

        # initialize, add the unit quaternion constraints and handle locked
        for i, ((T, R), (T0, R0), loc) in enumerate(
            zip(self.variables, self.initial_points, entities)
        ):
            T0val, R0val = loc_to_dof6(loc)

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

    def _build_transform(self, T: ca.MX, R: ca.MX) -> gp_Trsf:
        """Build a transformation from translation and rotation vectors."""
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

    def solve(self, verbosity: int = 0) -> tuple[list[Location], dict[str, Any]]:
        """
        Solve the constraints.

        :param verbosity: Verbosity level for the solver
        :return: tuple of (list of new locations, solver results)
        """
        suppress_banner = "yes" if verbosity == 0 else "no"

        opti = self.opti
        variables = self.variables
        initial_points = self.initial_points

        # Construct a penalty term to prevent large transformations
        penalty = 0.0
        for translation, rotation in variables:
            penalty += ca.sumsqr(ca.vertcat(translation / self.scale, rotation))

        # Initialize the objective function
        objective = 0.0

        # Expand all constraints (including compound ones) into simple constraints
        expanded_constraints = []
        for constraint in self.constraints:
            if isinstance(constraint, CompoundConstraintSpec):
                expanded_constraints.extend(constraint.expand())
            elif isinstance(constraint, ConstraintSpec):
                expanded_constraints.append(constraint)
            else:
                raise ValueError(f"Invalid constraint type: {type(constraint)}")

        # Process each constraint and add its cost to the objective
        for constraint in expanded_constraints:
            # Get indices of objects involved in the constraint
            object_indices = [self.object_indices[obj] for obj in constraint.objects]

            # Get the markers and parameters from the constraint
            markers = constraint.get_markers()
            params = constraint.get_param()

            # Collect the relevant variables and initial points for each object
            initial_translations: list[ca.DM] = []
            initial_rotations: list[ca.DM] = []
            current_translations: list[ca.MX] = []
            current_rotations: list[ca.MX] = []

            for obj_idx in object_indices:
                initial_translations.append(initial_points[obj_idx][0])  # Translation
                initial_rotations.append(initial_points[obj_idx][1])  # Rotation
                current_translations.append(variables[obj_idx][0])  # Translation
                current_rotations.append(variables[obj_idx][1])  # Rotation

            # Compute constraint cost
            constraint_cost = constraint.cost(
                CostParams(
                    problem=opti,
                    markers=list(markers),
                    initial_translations=initial_translations,
                    initial_rotations=initial_rotations,
                    translations=current_translations,
                    rotations=current_rotations,
                    param=params,
                    scale=self.scale
                    if constraint.kind
                    in ["Point", "PointInPlane", "PointOnLine", "FixedPoint"]
                    else 1,
                )
            )

            if constraint_cost is not None:
                objective += constraint_cost

        # Add the penalty term to the objective and minimize
        opti.minimize(objective + 1e-16 * penalty)

        # Configure and run the solver
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
                "print_level": verbosity,
                "sb": suppress_banner,
                "print_timing_statistics": "no",
                "linear_solver": "mumps",
            },
        )
        sol = opti.solve_limited()

        result = sol.stats()
        result["opti"] = opti  # this might be removed in the future

        # Convert the solution to locations
        locs = [
            Location(self._build_transform(T + T0, R + R0))
            for (T, R), (T0, R0) in zip(variables, initial_points)
        ]

        return locs, result
