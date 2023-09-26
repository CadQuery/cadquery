from typing import Optional, Literal, Sequence
from typing_extensions import Protocol, Self

from .geom import Vector, BoundBox

import OCP.GeomAbs as ga

geom_LUT_FACE = {
    ga.GeomAbs_Plane: "PLANE",
    ga.GeomAbs_Cylinder: "CYLINDER",
    ga.GeomAbs_Cone: "CONE",
    ga.GeomAbs_Sphere: "SPHERE",
    ga.GeomAbs_Torus: "TORUS",
    ga.GeomAbs_BezierSurface: "BEZIER",
    ga.GeomAbs_BSplineSurface: "BSPLINE",
    ga.GeomAbs_SurfaceOfRevolution: "REVOLUTION",
    ga.GeomAbs_SurfaceOfExtrusion: "EXTRUSION",
    ga.GeomAbs_OffsetSurface: "OFFSET",
    ga.GeomAbs_OtherSurface: "OTHER",
}

geom_LUT_EDGE = {
    ga.GeomAbs_Line: "LINE",
    ga.GeomAbs_Circle: "CIRCLE",
    ga.GeomAbs_Ellipse: "ELLIPSE",
    ga.GeomAbs_Hyperbola: "HYPERBOLA",
    ga.GeomAbs_Parabola: "PARABOLA",
    ga.GeomAbs_BezierCurve: "BEZIER",
    ga.GeomAbs_BSplineCurve: "BSPLINE",
    ga.GeomAbs_OffsetCurve: "OFFSET",
    ga.GeomAbs_OtherCurve: "OTHER",
}

Shapes = Literal[
    "Vertex", "Edge", "Wire", "Face", "Shell", "Solid", "CompSolid", "Compound"
]

Geoms = Literal[
    "Vertex",
    "Wire",
    "Shell",
    "Solid",
    "Compound",
    "PLANE",
    "CYLINDER",
    "CONE",
    "SPHERE",
    "TORUS",
    "BEZIER",
    "BSPLINE",
    "REVOLUTION",
    "EXTRUSION",
    "OFFSET",
    "OTHER",
    "LINE",
    "CIRCLE",
    "ELLIPSE",
    "HYPERBOLA",
    "PARABOLA",
]


class ShapeProtocol(Protocol):
    def ShapeType(self) -> Shapes:
        ...

    def geomType(self) -> Geoms:
        ...

    def Center(self) -> Vector:
        ...

    def Area(self) -> float:
        ...

    def BoundingBox(self, tolerance: Optional[float] = None) -> BoundBox:
        ...


class Shape1DProtocol(ShapeProtocol, Protocol):
    def tangentAt(
        self, p: float = 0.5, mode: Literal["length", "parameter"] = "length"
    ) -> Vector:
        ...

    def radius(self) -> float:
        ...

    def Length(self) -> float:
        ...


class FaceProtocol(ShapeProtocol, Protocol):
    def normalAt(self, v: Optional[Vector] = None) -> Vector:
        ...

    @classmethod
    def makeFromWires(cls, w: ShapeProtocol, ws: Sequence[ShapeProtocol]) -> Self:
        ...
