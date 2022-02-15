from typing import (
    Type,
    Optional,
    Tuple,
    Union,
    Iterable,
    List,
    Sequence,
    Iterator,
    Dict,
    Any,
    overload,
    TypeVar,
    cast as tcast,
)
from typing_extensions import Literal, Protocol

from io import BytesIO

from vtkmodules.vtkCommonDataModel import vtkPolyData
from vtkmodules.vtkFiltersCore import vtkTriangleFilter, vtkPolyDataNormals

from .geom import Vector, BoundBox, Plane, Location, Matrix

from ..utils import cqmultimethod as multimethod

import OCP.TopAbs as ta  # Tolopolgy type enum
import OCP.GeomAbs as ga  # Geometry type enum

from OCP.Precision import Precision

from OCP.gp import (
    gp_Vec,
    gp_Pnt,
    gp_Ax1,
    gp_Ax2,
    gp_Ax3,
    gp_Dir,
    gp_Circ,
    gp_Trsf,
    gp_Pln,
    gp_Pnt2d,
    gp_Dir2d,
    gp_Elips,
)

# Array of points (used for B-spline construction):
from OCP.TColgp import TColgp_HArray1OfPnt, TColgp_HArray2OfPnt

# Array of vectors (used for B-spline interpolation):
from OCP.TColgp import TColgp_Array1OfVec

# Array of booleans (used for B-spline interpolation):
from OCP.TColStd import TColStd_HArray1OfBoolean

# Array of floats (used for B-spline interpolation):
from OCP.TColStd import TColStd_HArray1OfReal

from OCP.BRepAdaptor import (
    BRepAdaptor_Curve,
    BRepAdaptor_CompCurve,
    BRepAdaptor_Surface,
    BRepAdaptor_HCurve,
    BRepAdaptor_HCompCurve,
)

from OCP.BRepBuilderAPI import (
    BRepBuilderAPI_MakeVertex,
    BRepBuilderAPI_MakeEdge,
    BRepBuilderAPI_MakeFace,
    BRepBuilderAPI_MakePolygon,
    BRepBuilderAPI_MakeWire,
    BRepBuilderAPI_Sewing,
    BRepBuilderAPI_Copy,
    BRepBuilderAPI_GTransform,
    BRepBuilderAPI_Transform,
    BRepBuilderAPI_Transformed,
    BRepBuilderAPI_RightCorner,
    BRepBuilderAPI_RoundCorner,
    BRepBuilderAPI_MakeSolid,
)

# properties used to store mass calculation result
from OCP.GProp import GProp_GProps
from OCP.BRepGProp import BRepGProp_Face, BRepGProp  # used for mass calculation

from OCP.BRepPrimAPI import (
    BRepPrimAPI_MakeBox,
    BRepPrimAPI_MakeCone,
    BRepPrimAPI_MakeCylinder,
    BRepPrimAPI_MakeTorus,
    BRepPrimAPI_MakeWedge,
    BRepPrimAPI_MakePrism,
    BRepPrimAPI_MakeRevol,
    BRepPrimAPI_MakeSphere,
)
from OCP.BRepIntCurveSurface import BRepIntCurveSurface_Inter

from OCP.TopExp import TopExp_Explorer  # Toplogy explorer

# used for getting underlying geoetry -- is this equivalent to brep adaptor?
from OCP.BRep import BRep_Tool, BRep_Builder

from OCP.TopoDS import (
    TopoDS,
    TopoDS_Shape,
    TopoDS_Builder,
    TopoDS_Compound,
    TopoDS_Iterator,
    TopoDS_Wire,
    TopoDS_Face,
    TopoDS_Edge,
    TopoDS_Vertex,
    TopoDS_Solid,
    TopoDS_Shell,
    TopoDS_CompSolid,
)

from OCP.GC import GC_MakeArcOfCircle, GC_MakeArcOfEllipse  # geometry construction
from OCP.GCE2d import GCE2d_MakeSegment
from OCP.gce import gce_MakeLin, gce_MakeDir
from OCP.GeomAPI import (
    GeomAPI_Interpolate,
    GeomAPI_ProjectPointOnSurf,
    GeomAPI_PointsToBSpline,
    GeomAPI_PointsToBSplineSurface,
)

from OCP.BRepFill import BRepFill

from OCP.BRepAlgoAPI import (
    BRepAlgoAPI_Common,
    BRepAlgoAPI_Fuse,
    BRepAlgoAPI_Cut,
    BRepAlgoAPI_BooleanOperation,
    BRepAlgoAPI_Splitter,
)

from OCP.Geom import (
    Geom_ConicalSurface,
    Geom_CylindricalSurface,
    Geom_Surface,
    Geom_Plane,
)
from OCP.Geom2d import Geom2d_Line

from OCP.BRepLib import BRepLib, BRepLib_FindSurface

from OCP.BRepOffsetAPI import (
    BRepOffsetAPI_ThruSections,
    BRepOffsetAPI_MakePipeShell,
    BRepOffsetAPI_MakeThickSolid,
    BRepOffsetAPI_MakeOffset,
)

from OCP.BRepFilletAPI import (
    BRepFilletAPI_MakeChamfer,
    BRepFilletAPI_MakeFillet,
    BRepFilletAPI_MakeFillet2d,
)

from OCP.TopTools import TopTools_IndexedDataMapOfShapeListOfShape, TopTools_ListOfShape

from OCP.TopExp import TopExp

from OCP.ShapeFix import ShapeFix_Shape, ShapeFix_Solid, ShapeFix_Face

from OCP.STEPControl import STEPControl_Writer, STEPControl_AsIs

from OCP.BRepMesh import BRepMesh_IncrementalMesh
from OCP.StlAPI import StlAPI_Writer

from OCP.ShapeUpgrade import ShapeUpgrade_UnifySameDomain

from OCP.BRepTools import BRepTools

from OCP.LocOpe import LocOpe_DPrism

from OCP.BRepCheck import BRepCheck_Analyzer

from OCP.Font import (
    Font_FontMgr,
    Font_FA_Regular,
    Font_FA_Italic,
    Font_FA_Bold,
    Font_SystemFont,
)

from OCP.StdPrs import StdPrs_BRepFont, StdPrs_BRepTextBuilder as Font_BRepTextBuilder

from OCP.NCollection import NCollection_Utf8String

from OCP.BRepFeat import BRepFeat_MakeDPrism

from OCP.BRepClass3d import BRepClass3d_SolidClassifier

from OCP.TCollection import TCollection_AsciiString

from OCP.TopLoc import TopLoc_Location

from OCP.GeomAbs import (
    GeomAbs_Shape,
    GeomAbs_C0,
    GeomAbs_Intersection,
    GeomAbs_JoinType,
)
from OCP.BRepOffsetAPI import BRepOffsetAPI_MakeFilling
from OCP.BRepOffset import BRepOffset_MakeOffset, BRepOffset_Skin

from OCP.BOPAlgo import BOPAlgo_GlueEnum

from OCP.IFSelect import IFSelect_ReturnStatus

from OCP.TopAbs import TopAbs_ShapeEnum, TopAbs_Orientation

from OCP.ShapeAnalysis import ShapeAnalysis_FreeBounds
from OCP.TopTools import TopTools_HSequenceOfShape

from OCP.GCPnts import GCPnts_AbscissaPoint

from OCP.GeomFill import (
    GeomFill_Frenet,
    GeomFill_CorrectedFrenet,
    GeomFill_TrihedronLaw,
)

from OCP.IVtkOCC import IVtkOCC_Shape, IVtkOCC_ShapeMesher
from OCP.IVtkVTK import IVtkVTK_ShapeData

# for catching exceptions
from OCP.Standard import Standard_NoSuchObject, Standard_Failure

from math import pi, sqrt
import warnings

Real = Union[float, int]

TOLERANCE = 1e-6
DEG2RAD = 2 * pi / 360.0
HASH_CODE_MAX = 2147483647  # max 32bit signed int, required by OCC.Core.HashCode

shape_LUT = {
    ta.TopAbs_VERTEX: "Vertex",
    ta.TopAbs_EDGE: "Edge",
    ta.TopAbs_WIRE: "Wire",
    ta.TopAbs_FACE: "Face",
    ta.TopAbs_SHELL: "Shell",
    ta.TopAbs_SOLID: "Solid",
    ta.TopAbs_COMPSOLID: "CompSolid",
    ta.TopAbs_COMPOUND: "Compound",
}

shape_properties_LUT = {
    ta.TopAbs_VERTEX: None,
    ta.TopAbs_EDGE: BRepGProp.LinearProperties_s,
    ta.TopAbs_WIRE: BRepGProp.LinearProperties_s,
    ta.TopAbs_FACE: BRepGProp.SurfaceProperties_s,
    ta.TopAbs_SHELL: BRepGProp.SurfaceProperties_s,
    ta.TopAbs_SOLID: BRepGProp.VolumeProperties_s,
    ta.TopAbs_COMPOUND: BRepGProp.VolumeProperties_s,
}

inverse_shape_LUT = {v: k for k, v in shape_LUT.items()}

downcast_LUT = {
    ta.TopAbs_VERTEX: TopoDS.Vertex_s,
    ta.TopAbs_EDGE: TopoDS.Edge_s,
    ta.TopAbs_WIRE: TopoDS.Wire_s,
    ta.TopAbs_FACE: TopoDS.Face_s,
    ta.TopAbs_SHELL: TopoDS.Shell_s,
    ta.TopAbs_SOLID: TopoDS.Solid_s,
    ta.TopAbs_COMPSOLID: TopoDS.CompSolid_s,
    ta.TopAbs_COMPOUND: TopoDS.Compound_s,
}

geom_LUT = {
    ta.TopAbs_VERTEX: "Vertex",
    ta.TopAbs_EDGE: BRepAdaptor_Curve,
    ta.TopAbs_WIRE: "Wire",
    ta.TopAbs_FACE: BRepAdaptor_Surface,
    ta.TopAbs_SHELL: "Shell",
    ta.TopAbs_SOLID: "Solid",
    ta.TopAbs_SOLID: "CompSolid",
    ta.TopAbs_COMPOUND: "Compound",
}

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
VectorLike = Union[Vector, Tuple[float, float, float]]
T = TypeVar("T", bound="Shape")


def shapetype(obj: TopoDS_Shape) -> TopAbs_ShapeEnum:

    if obj.IsNull():
        raise ValueError("Null TopoDS_Shape object")

    return obj.ShapeType()


def downcast(obj: TopoDS_Shape) -> TopoDS_Shape:
    """
    Downcasts a TopoDS object to suitable specialized type
    """

    f_downcast: Any = downcast_LUT[shapetype(obj)]
    rv = f_downcast(obj)

    return rv


def fix(obj: TopoDS_Shape) -> TopoDS_Shape:
    """
    Fix a TopoDS object to suitable specialized type
    """

    sf = ShapeFix_Shape(obj)
    sf.Perform()

    return downcast(sf.Shape())


class Shape(object):
    """
    Represents a shape in the system. Wraps TopoDS_Shape.
    """

    wrapped: TopoDS_Shape
    forConstruction: bool

    def __init__(self, obj: TopoDS_Shape):
        self.wrapped = downcast(obj)

        self.forConstruction = False
        # Helps identify this solid through the use of an ID
        self.label = ""

    def clean(self: T) -> T:
        """Experimental clean using ShapeUpgrade"""

        upgrader = ShapeUpgrade_UnifySameDomain(self.wrapped, True, True, True)
        upgrader.AllowInternalEdges(False)
        upgrader.Build()

        return self.__class__(upgrader.Shape())

    def fix(self: T) -> T:
        """Try to fix shape if not valid"""
        if not self.isValid():
            fixed = fix(self.wrapped)

            return self.__class__(fixed)

        return self

    @classmethod
    def cast(cls, obj: TopoDS_Shape, forConstruction: bool = False) -> "Shape":
        "Returns the right type of wrapper, given a OCCT object"

        tr = None

        # define the shape lookup table for casting
        constructor_LUT = {
            ta.TopAbs_VERTEX: Vertex,
            ta.TopAbs_EDGE: Edge,
            ta.TopAbs_WIRE: Wire,
            ta.TopAbs_FACE: Face,
            ta.TopAbs_SHELL: Shell,
            ta.TopAbs_SOLID: Solid,
            ta.TopAbs_COMPSOLID: CompSolid,
            ta.TopAbs_COMPOUND: Compound,
        }

        t = shapetype(obj)
        # NB downcast is needed to handly TopoDS_Shape types
        tr = constructor_LUT[t](downcast(obj))
        tr.forConstruction = forConstruction

        return tr

    def exportStl(
        self, fileName: str, tolerance: float = 1e-3, angularTolerance: float = 0.1
    ) -> bool:
        """
        Exports a shape to a specified STL file.

        :param fileName: The path and file name to write the STL output to.
        :type fileName: fileName
        :param tolerance: A linear deflection setting which limits the distance between a curve and its tessellation. Setting this value too low will result in large meshes that can consume computing resources. Setting the value too high can result in meshes with a level of detail that is too low. Default is 0.1, which is good starting point for a range of cases.
        :type tolerance: float
        :param angularTolerance: - Angular deflection setting which limits the angle between subsequent segments in a polyline. Default is 0.1.
        :type angularTolerance: float
        """

        mesh = BRepMesh_IncrementalMesh(self.wrapped, tolerance, True, angularTolerance)
        mesh.Perform()

        writer = StlAPI_Writer()

        return writer.Write(self.wrapped, fileName)

    def exportStep(self, fileName: str) -> IFSelect_ReturnStatus:
        """
        Export this shape to a STEP file
        """

        writer = STEPControl_Writer()
        writer.Transfer(self.wrapped, STEPControl_AsIs)

        return writer.Write(fileName)

    def exportBrep(self, f: Union[str, BytesIO]) -> bool:
        """
        Export this shape to a BREP file
        """

        rv = BRepTools.Write_s(self.wrapped, f)

        return True if rv is None else rv

    @classmethod
    def importBrep(cls, f: Union[str, BytesIO]) -> "Shape":
        """
        Import shape from a BREP file
        """
        s = TopoDS_Shape()
        builder = BRep_Builder()

        BRepTools.Read_s(s, f, builder)

        if s.IsNull():
            raise ValueError(f"Could not import {f}")

        return cls.cast(s)

    def geomType(self) -> Geoms:
        """
        Gets the underlying geometry type.

        Implementations can return any values desired, but the values the user
        uses in type filters should correspond to these.

        As an example, if a user does::

            CQ(object).faces("%mytype")

        The expectation is that the geomType attribute will return 'mytype'

        The return values depend on the type of the shape:

        | Vertex:  always 'Vertex'
        | Edge:   LINE, ARC, CIRCLE, SPLINE
        | Face:   PLANE, SPHERE, CONE
        | Solid:  'Solid'
        | Shell:  'Shell'
        | Compound: 'Compound'
        | Wire:   'Wire'

        :returns: A string according to the geometry type
        """

        tr: Any = geom_LUT[shapetype(self.wrapped)]

        if isinstance(tr, str):
            rv = tr
        elif tr is BRepAdaptor_Curve:
            rv = geom_LUT_EDGE[tr(self.wrapped).GetType()]
        else:
            rv = geom_LUT_FACE[tr(self.wrapped).GetType()]

        return tcast(Geoms, rv)

    def hashCode(self) -> int:
        """
        Returns a hashed value denoting this shape. It is computed from the
        TShape and the Location. The Orientation is not used.
        """
        return self.wrapped.HashCode(HASH_CODE_MAX)

    def isNull(self) -> bool:
        """
        Returns true if this shape is null. In other words, it references no
        underlying shape with the potential to be given a location and an
        orientation.
        """
        return self.wrapped.IsNull()

    def isSame(self, other: "Shape") -> bool:
        """
        Returns True if other and this shape are same, i.e. if they share the
        same TShape with the same Locations. Orientations may differ. Also see
        :py:meth:`isEqual`
        """
        return self.wrapped.IsSame(other.wrapped)

    def isEqual(self, other: "Shape") -> bool:
        """
        Returns True if two shapes are equal, i.e. if they share the same
        TShape with the same Locations and Orientations. Also see
        :py:meth:`isSame`.
        """
        return self.wrapped.IsEqual(other.wrapped)

    def isValid(self) -> bool:
        """
        Returns True if no defect is detected on the shape S or any of its
        subshapes. See the OCCT docs on BRepCheck_Analyzer::IsValid for a full
        description of what is checked.
        """
        return BRepCheck_Analyzer(self.wrapped).IsValid()

    def BoundingBox(
        self, tolerance: Optional[float] = None
    ) -> BoundBox:  # need to implement that in GEOM
        """
        Create a bounding box for this Shape.

        :param tolerance: Tolerance value passed to :py:class:`BoundBox`
        :returns: A :py:class:`BoundBox` object for this Shape
        """
        return BoundBox._fromTopoDS(self.wrapped, tol=tolerance)

    def mirror(
        self,
        mirrorPlane: Union[
            Literal["XY", "YX", "XZ", "ZX", "YZ", "ZY"], VectorLike
        ] = "XY",
        basePointVector: VectorLike = (0, 0, 0),
    ) -> "Shape":
        """
        Applies a mirror transform to this Shape. Does not duplicate objects
        about the plane.

        :param mirrorPlane: The direction of the plane to mirror about - one of
            'XY', 'XZ' or 'YZ'
        :param basePointVector: The origin of the plane to mirror about
        :returns: The mirrored shape
        """
        if isinstance(mirrorPlane, str):
            if mirrorPlane == "XY" or mirrorPlane == "YX":
                mirrorPlaneNormalVector = gp_Dir(0, 0, 1)
            elif mirrorPlane == "XZ" or mirrorPlane == "ZX":
                mirrorPlaneNormalVector = gp_Dir(0, 1, 0)
            elif mirrorPlane == "YZ" or mirrorPlane == "ZY":
                mirrorPlaneNormalVector = gp_Dir(1, 0, 0)
        else:
            if isinstance(mirrorPlane, tuple):
                mirrorPlaneNormalVector = gp_Dir(*mirrorPlane)
            elif isinstance(mirrorPlane, Vector):
                mirrorPlaneNormalVector = mirrorPlane.toDir()

        if isinstance(basePointVector, tuple):
            basePointVector = Vector(basePointVector)

        T = gp_Trsf()
        T.SetMirror(gp_Ax2(gp_Pnt(*basePointVector.toTuple()), mirrorPlaneNormalVector))

        return self._apply_transform(T)

    @staticmethod
    def _center_of_mass(shape: "Shape") -> Vector:

        Properties = GProp_GProps()
        BRepGProp.VolumeProperties_s(shape.wrapped, Properties)

        return Vector(Properties.CentreOfMass())

    def Center(self) -> Vector:
        """
        :returns: The point of the center of mass of this Shape
        """

        return Shape.centerOfMass(self)

    def CenterOfBoundBox(self, tolerance: Optional[float] = None) -> Vector:
        """
        :param tolerance: Tolerance passed to the :py:meth:`BoundingBox` method
        :returns: Center of the bounding box of this shape
        """
        return self.BoundingBox(tolerance=tolerance).center

    @staticmethod
    def CombinedCenter(objects: Iterable["Shape"]) -> Vector:
        """
        Calculates the center of mass of multiple objects.

        :param objects: A list of objects with mass
        """
        total_mass = sum(Shape.computeMass(o) for o in objects)
        weighted_centers = [
            Shape.centerOfMass(o).multiply(Shape.computeMass(o)) for o in objects
        ]

        sum_wc = weighted_centers[0]
        for wc in weighted_centers[1:]:
            sum_wc = sum_wc.add(wc)

        return Vector(sum_wc.multiply(1.0 / total_mass))

    @staticmethod
    def computeMass(obj: "Shape") -> float:
        """
        Calculates the 'mass' of an object.

        :param obj: Compute the mass of this object
        """
        Properties = GProp_GProps()
        calc_function = shape_properties_LUT[shapetype(obj.wrapped)]

        if calc_function:
            calc_function(obj.wrapped, Properties)
            return Properties.Mass()
        else:
            raise NotImplementedError

    @staticmethod
    def centerOfMass(obj: "Shape") -> Vector:
        """
        Calculates the center of 'mass' of an object.

        :param obj: Compute the center of mass of this object
        """
        Properties = GProp_GProps()
        calc_function = shape_properties_LUT[shapetype(obj.wrapped)]

        if calc_function:
            calc_function(obj.wrapped, Properties)
            return Vector(Properties.CentreOfMass())
        else:
            raise NotImplementedError

    @staticmethod
    def CombinedCenterOfBoundBox(objects: List["Shape"]) -> Vector:
        """
        Calculates the center of a bounding box of multiple objects.

        :param objects: A list of objects
        """
        total_mass = len(objects)

        weighted_centers = []
        for o in objects:
            weighted_centers.append(BoundBox._fromTopoDS(o.wrapped).center)

        sum_wc = weighted_centers[0]
        for wc in weighted_centers[1:]:
            sum_wc = sum_wc.add(wc)

        return Vector(sum_wc.multiply(1.0 / total_mass))

    def Closed(self) -> bool:
        """
        :returns: The closedness flag
        """
        return self.wrapped.Closed()

    def ShapeType(self) -> Shapes:
        return tcast(Shapes, shape_LUT[shapetype(self.wrapped)])

    def _entities(self, topo_type: Shapes) -> List[TopoDS_Shape]:

        out = {}  # using dict to prevent duplicates

        explorer = TopExp_Explorer(self.wrapped, inverse_shape_LUT[topo_type])

        while explorer.More():
            item = explorer.Current()
            out[
                item.HashCode(HASH_CODE_MAX)
            ] = item  # needed to avoid pseudo-duplicate entities
            explorer.Next()

        return list(out.values())

    def _entitiesFrom(
        self, child_type: Shapes, parent_type: Shapes
    ) -> Dict["Shape", List["Shape"]]:

        res = TopTools_IndexedDataMapOfShapeListOfShape()

        TopTools_IndexedDataMapOfShapeListOfShape()
        TopExp.MapShapesAndAncestors_s(
            self.wrapped,
            inverse_shape_LUT[child_type],
            inverse_shape_LUT[parent_type],
            res,
        )

        out: Dict[Shape, List[Shape]] = {}
        for i in range(1, res.Extent() + 1):
            out[Shape.cast(res.FindKey(i))] = [
                Shape.cast(el) for el in res.FindFromIndex(i)
            ]

        return out

    def Vertices(self) -> List["Vertex"]:
        """
        :returns: All the vertices in this Shape
        """

        return [Vertex(i) for i in self._entities("Vertex")]

    def Edges(self) -> List["Edge"]:
        """
        :returns: All the edges in this Shape
        """

        return [
            Edge(i)
            for i in self._entities("Edge")
            if not BRep_Tool.Degenerated_s(TopoDS.Edge_s(i))
        ]

    def Compounds(self) -> List["Compound"]:
        """
        :returns: All the compounds in this Shape
        """

        return [Compound(i) for i in self._entities("Compound")]

    def Wires(self) -> List["Wire"]:
        """
        :returns: All the wires in this Shape
        """

        return [Wire(i) for i in self._entities("Wire")]

    def Faces(self) -> List["Face"]:
        """
        :returns: All the faces in this Shape
        """

        return [Face(i) for i in self._entities("Face")]

    def Shells(self) -> List["Shell"]:
        """
        :returns: All the shells in this Shape
        """

        return [Shell(i) for i in self._entities("Shell")]

    def Solids(self) -> List["Solid"]:
        """
        :returns: All the solids in this Shape
        """

        return [Solid(i) for i in self._entities("Solid")]

    def CompSolids(self) -> List["CompSolid"]:
        """
        :returns: All the compsolids in this Shape
        """

        return [CompSolid(i) for i in self._entities("CompSolid")]

    def Area(self) -> float:
        """
        :returns: The surface area of all faces in this Shape
        """
        Properties = GProp_GProps()
        BRepGProp.SurfaceProperties_s(self.wrapped, Properties)

        return Properties.Mass()

    def Volume(self) -> float:
        """
        :returns: The volume of this Shape
        """
        # when density == 1, mass == volume
        return Shape.computeMass(self)

    def _apply_transform(self: T, Tr: gp_Trsf) -> T:

        return self.__class__(BRepBuilderAPI_Transform(self.wrapped, Tr, True).Shape())

    def rotate(
        self: T, startVector: Vector, endVector: Vector, angleDegrees: float
    ) -> T:
        """
        Rotates a shape around an axis.

        :param startVector: start point of rotation axis
        :type startVector: either a 3-tuple or a Vector
        :param endVector: end point of rotation axis
        :type endVector: either a 3-tuple or a Vector
        :param angleDegrees:  angle to rotate, in degrees
        :returns: a copy of the shape, rotated
        """
        if type(startVector) == tuple:
            startVector = Vector(startVector)

        if type(endVector) == tuple:
            endVector = Vector(endVector)

        Tr = gp_Trsf()
        Tr.SetRotation(
            gp_Ax1(startVector.toPnt(), (endVector - startVector).toDir()),
            angleDegrees * DEG2RAD,
        )

        return self._apply_transform(Tr)

    def translate(self: T, vector: Vector) -> T:
        """
        Translates this shape through a transformation.
        """

        if type(vector) == tuple:
            vector = Vector(vector)

        T = gp_Trsf()
        T.SetTranslation(vector.wrapped)

        return self._apply_transform(T)

    def scale(self, factor: float) -> "Shape":
        """
        Scales this shape through a transformation.
        """

        T = gp_Trsf()
        T.SetScale(gp_Pnt(), factor)

        return self._apply_transform(T)

    def copy(self: T) -> T:
        """
        Creates a new object that is a copy of this object.
        """

        return self.__class__(BRepBuilderAPI_Copy(self.wrapped).Shape())

    def transformShape(self, tMatrix: Matrix) -> "Shape":
        """
        Transforms this Shape by tMatrix. Also see :py:meth:`transformGeometry`.

        :param tMatrix: The transformation matrix
        :returns: a copy of the object, transformed by the provided matrix,
            with all objects keeping their type
        """

        r = Shape.cast(
            BRepBuilderAPI_Transform(self.wrapped, tMatrix.wrapped.Trsf()).Shape()
        )
        r.forConstruction = self.forConstruction

        return r

    def transformGeometry(self, tMatrix: Matrix) -> "Shape":
        """
        Transforms this shape by tMatrix.

        WARNING: transformGeometry will sometimes convert lines and circles to
        splines, but it also has the ability to handle skew and stretching
        transformations.

        If your transformation is only translation and rotation, it is safer to
        use :py:meth:`transformShape`, which doesn't change the underlying type
        of the geometry, but cannot handle skew transformations.

        :param tMatrix: The transformation matrix
        :returns: a copy of the object, but with geometry transformed instead
            of just rotated.
        """
        r = Shape.cast(
            BRepBuilderAPI_GTransform(self.wrapped, tMatrix.wrapped, True).Shape()
        )
        r.forConstruction = self.forConstruction

        return r

    def location(self) -> Location:
        """
        Return the current location
        """

        return Location(self.wrapped.Location())

    def locate(self: T, loc: Location) -> T:
        """
        Apply a location in absolute sense to self
        """

        self.wrapped.Location(loc.wrapped)

        return self

    def located(self: T, loc: Location) -> T:
        """
        Apply a location in absolute sense to a copy of self
        """

        r = self.__class__(self.wrapped.Located(loc.wrapped))
        r.forConstruction = self.forConstruction

        return r

    def move(self: T, loc: Location) -> T:
        """
        Apply a location in relative sense (i.e. update current location) to self
        """

        self.wrapped.Move(loc.wrapped)

        return self

    def moved(self: T, loc: Location) -> T:
        """
        Apply a location in relative sense (i.e. update current location) to a copy of self
        """

        r = self.__class__(self.wrapped.Moved(loc.wrapped))
        r.forConstruction = self.forConstruction

        return r

    def __hash__(self) -> int:

        return self.hashCode()

    def __eq__(self, other) -> bool:

        return self.isSame(other) if isinstance(other, Shape) else False

    def _bool_op(
        self,
        args: Iterable["Shape"],
        tools: Iterable["Shape"],
        op: Union[BRepAlgoAPI_BooleanOperation, BRepAlgoAPI_Splitter],
    ) -> "Shape":
        """
        Generic boolean operation
        """

        arg = TopTools_ListOfShape()
        for obj in args:
            arg.Append(obj.wrapped)

        tool = TopTools_ListOfShape()
        for obj in tools:
            tool.Append(obj.wrapped)

        op.SetArguments(arg)
        op.SetTools(tool)

        op.SetRunParallel(True)
        op.Build()

        return Shape.cast(op.Shape())

    def cut(self, *toCut: "Shape") -> "Shape":
        """
        Remove the positional arguments from this Shape.
        """

        cut_op = BRepAlgoAPI_Cut()

        return self._bool_op((self,), toCut, cut_op)

    def fuse(
        self, *toFuse: "Shape", glue: bool = False, tol: Optional[float] = None
    ) -> "Shape":
        """
        Fuse the positional arguments with this Shape.

        :param glue: Sets the glue option for the algorithm, which allows
            increasing performance of the intersection of the input shapes
        :param tol: Additional tolerance
        """

        fuse_op = BRepAlgoAPI_Fuse()
        if glue:
            fuse_op.SetGlue(BOPAlgo_GlueEnum.BOPAlgo_GlueShift)
        if tol:
            fuse_op.SetFuzzyValue(tol)

        rv = self._bool_op((self,), toFuse, fuse_op)

        return rv

    def intersect(self, *toIntersect: "Shape") -> "Shape":
        """
        Intersection of the positional arguments and this Shape.
        """

        intersect_op = BRepAlgoAPI_Common()

        return self._bool_op((self,), toIntersect, intersect_op)

    def facesIntersectedByLine(
        self,
        point: VectorLike,
        axis: VectorLike,
        tol: float = 1e-4,
        direction: Optional[Literal["AlongAxis", "Opposite"]] = None,
    ):
        """
        Computes the intersections between the provided line and the faces of this Shape

        :point: Base point for defining a line
        :axis: Axis on which the line rest
        :tol: Intersection tolerance
        :direction: Valid values : "AlongAxis", "Opposite", if specified will ignore all faces that are not in the specified direction
        including the face where the :point: lies if it is the case

        :returns: A list of intersected faces sorted by distance from :point:
        """

        oc_point = (
            gp_Pnt(*point.toTuple()) if isinstance(point, Vector) else gp_Pnt(*point)
        )
        oc_axis = (
            gp_Dir(Vector(axis).wrapped)
            if not isinstance(axis, Vector)
            else gp_Dir(axis.wrapped)
        )

        line = gce_MakeLin(oc_point, oc_axis).Value()
        shape = self.wrapped

        intersectMaker = BRepIntCurveSurface_Inter()
        intersectMaker.Init(shape, line, tol)

        faces_dist = []  # using a list instead of a dictionary to be able to sort it
        while intersectMaker.More():
            interPt = intersectMaker.Pnt()
            interDirMk = gce_MakeDir(oc_point, interPt)

            distance = oc_point.SquareDistance(interPt)

            # interDir is not done when `oc_point` and `oc_axis` have the same coord
            if interDirMk.IsDone():
                interDir: Any = interDirMk.Value()
            else:
                interDir = None

            if direction == "AlongAxis":
                if (
                    interDir is not None
                    and not interDir.IsOpposite(oc_axis, tol)
                    and distance > tol
                ):
                    faces_dist.append((intersectMaker.Face(), distance))

            elif direction == "Opposite":
                if (
                    interDir is not None
                    and interDir.IsOpposite(oc_axis, tol)
                    and distance > tol
                ):
                    faces_dist.append((intersectMaker.Face(), distance))

            elif direction is None:
                faces_dist.append(
                    (intersectMaker.Face(), abs(distance))
                )  # will sort all intersected faces by distance whatever the direction is
            else:
                raise ValueError(
                    "Invalid direction specification.\nValid specification are 'AlongAxis' and 'Opposite'."
                )

            intersectMaker.Next()

        faces_dist.sort(key=lambda x: x[1])
        faces = [face[0] for face in faces_dist]

        return [Face(face) for face in faces]

    def split(self, *splitters: "Shape") -> "Shape":
        """
        Split this shape with the positional arguments.
        """

        split_op = BRepAlgoAPI_Splitter()

        return self._bool_op((self,), splitters, split_op)

    def mesh(self, tolerance: float, angularTolerance: float = 0.1):
        """
        Generate triangulation if none exists.
        """

        if not BRepTools.Triangulation_s(self.wrapped, tolerance):
            BRepMesh_IncrementalMesh(self.wrapped, tolerance, True, angularTolerance)

    def tessellate(
        self, tolerance: float, angularTolerance: float = 0.1
    ) -> Tuple[List[Vector], List[Tuple[int, int, int]]]:

        self.mesh(tolerance, angularTolerance)

        vertices: List[Vector] = []
        triangles: List[Tuple[int, int, int]] = []
        offset = 0

        for f in self.Faces():

            loc = TopLoc_Location()
            poly = BRep_Tool.Triangulation_s(f.wrapped, loc)
            Trsf = loc.Transformation()
            reverse = (
                True
                if f.wrapped.Orientation() == TopAbs_Orientation.TopAbs_REVERSED
                else False
            )

            # add vertices
            vertices += [
                Vector(v.X(), v.Y(), v.Z())
                for v in (v.Transformed(Trsf) for v in poly.Nodes())
            ]

            # add triangles
            triangles += [
                (
                    t.Value(1) + offset - 1,
                    t.Value(3) + offset - 1,
                    t.Value(2) + offset - 1,
                )
                if reverse
                else (
                    t.Value(1) + offset - 1,
                    t.Value(2) + offset - 1,
                    t.Value(3) + offset - 1,
                )
                for t in poly.Triangles()
            ]

            offset += poly.NbNodes()

        return vertices, triangles

    def toVtkPolyData(
        self, tolerance: float, angularTolerance: float = 0.1, normals: bool = True
    ) -> vtkPolyData:
        """
        Convert shape to vtkPolyData
        """

        vtk_shape = IVtkOCC_Shape(self.wrapped)
        shape_data = IVtkVTK_ShapeData()
        shape_mesher = IVtkOCC_ShapeMesher(
            tolerance, angularTolerance, theNbUIsos=0, theNbVIsos=0
        )

        shape_mesher.Build(vtk_shape, shape_data)

        rv = shape_data.getVtkPolyData()

        # convert to triangles and split edges
        t_filter = vtkTriangleFilter()
        t_filter.SetInputData(rv)
        t_filter.Update()

        rv = t_filter.GetOutput()

        # compute normals
        if normals:
            n_filter = vtkPolyDataNormals()
            n_filter.SetComputePointNormals(True)
            n_filter.SetComputeCellNormals(True)
            n_filter.SetFeatureAngle(360)
            n_filter.SetInputData(rv)
            n_filter.Update()

            rv = n_filter.GetOutput()

        return rv

    def _repr_javascript_(self):
        """
        Jupyter 3D representation support
        """

        from .jupyter_tools import display

        return display(self)._repr_javascript_()


class ShapeProtocol(Protocol):
    @property
    def wrapped(self) -> TopoDS_Shape:
        ...

    def __init__(self, wrapped: TopoDS_Shape) -> None:
        ...

    def Faces(self) -> List["Face"]:
        ...

    def geomType(self) -> Geoms:
        ...


class Vertex(Shape):
    """
    A Single Point in Space
    """

    wrapped: TopoDS_Vertex

    def __init__(self, obj: TopoDS_Shape, forConstruction: bool = False):
        """
        Create a vertex from a FreeCAD Vertex
        """
        super(Vertex, self).__init__(obj)

        self.forConstruction = forConstruction
        self.X, self.Y, self.Z = self.toTuple()

    def toTuple(self) -> Tuple[float, float, float]:

        geom_point = BRep_Tool.Pnt_s(self.wrapped)
        return (geom_point.X(), geom_point.Y(), geom_point.Z())

    def Center(self) -> Vector:
        """
        The center of a vertex is itself!
        """
        return Vector(self.toTuple())

    @classmethod
    def makeVertex(cls, x: float, y: float, z: float) -> "Vertex":

        return cls(BRepBuilderAPI_MakeVertex(gp_Pnt(x, y, z)).Vertex())


class Mixin1DProtocol(ShapeProtocol, Protocol):
    def _geomAdaptor(self) -> Union[BRepAdaptor_Curve, BRepAdaptor_CompCurve]:
        ...

    def _geomAdaptorH(
        self,
    ) -> Tuple[
        Union[BRepAdaptor_Curve, BRepAdaptor_CompCurve],
        Union[BRepAdaptor_HCurve, BRepAdaptor_HCompCurve],
    ]:
        ...

    def paramAt(self, d: float) -> float:
        ...

    def positionAt(
        self, d: float, mode: Literal["length", "parameter"] = "length",
    ) -> Vector:
        ...

    def locationAt(
        self,
        d: float,
        mode: Literal["length", "parameter"] = "length",
        frame: Literal["frenet", "corrected"] = "frenet",
        planar: bool = False,
    ) -> Location:
        ...


class Mixin1D(object):
    def _bounds(self: Mixin1DProtocol) -> Tuple[float, float]:

        curve = self._geomAdaptor()
        return curve.FirstParameter(), curve.LastParameter()

    def startPoint(self: Mixin1DProtocol) -> Vector:
        """

        :return: a vector representing the start point of this edge

        Note, circles may have the start and end points the same
        """

        curve = self._geomAdaptor()
        umin = curve.FirstParameter()

        return Vector(curve.Value(umin))

    def endPoint(self: Mixin1DProtocol) -> Vector:
        """

        :return: a vector representing the end point of this edge.

        Note, circles may have the start and end points the same
        """

        curve = self._geomAdaptor()
        umax = curve.LastParameter()

        return Vector(curve.Value(umax))

    def paramAt(self: Mixin1DProtocol, d: float) -> float:
        """
        Compute parameter value at the specified normalized distance.

        :param d: normalized distance [0, 1]
        :return: parameter value
        """

        curve = self._geomAdaptor()

        l = GCPnts_AbscissaPoint.Length_s(curve)
        return GCPnts_AbscissaPoint(curve, l * d, curve.FirstParameter()).Parameter()

    def tangentAt(
        self: Mixin1DProtocol,
        locationParam: float = 0.5,
        mode: Literal["length", "parameter"] = "length",
    ) -> Vector:
        """
        Compute tangent vector at the specified location.

        :param locationParam: distance or parameter value (default: 0.5)
        :param mode: position calculation mode (default: parameter)
        :return: tangent vector
        """

        curve = self._geomAdaptor()

        tmp = gp_Pnt()
        res = gp_Vec()

        if mode == "length":
            param = self.paramAt(locationParam)
        else:
            param = locationParam

        curve.D1(param, tmp, res)

        return Vector(gp_Dir(res))

    def normal(self: Mixin1DProtocol) -> Vector:
        """
        Calculate the normal Vector. Only possible for planar curves.

        :return: normal vector
        """

        curve = self._geomAdaptor()
        gtype = self.geomType()

        if gtype == "CIRCLE":
            circ = curve.Circle()
            rv = Vector(circ.Axis().Direction())
        elif gtype == "ELLIPSE":
            ell = curve.Ellipse()
            rv = Vector(ell.Axis().Direction())
        else:
            fs = BRepLib_FindSurface(self.wrapped, OnlyPlane=True)
            surf = fs.Surface()

            if isinstance(surf, Geom_Plane):
                pln = surf.Pln()
                rv = Vector(pln.Axis().Direction())
            else:
                raise ValueError("Normal not defined")

        return rv

    def Center(self: Mixin1DProtocol) -> Vector:

        Properties = GProp_GProps()
        BRepGProp.LinearProperties_s(self.wrapped, Properties)

        return Vector(Properties.CentreOfMass())

    def Length(self: Mixin1DProtocol) -> float:

        return GCPnts_AbscissaPoint.Length_s(self._geomAdaptor())

    def radius(self: Mixin1DProtocol) -> float:
        """
        Calculate the radius.

        Note that when applied to a Wire, the radius is simply the radius of the first edge.

        :return: radius
        :raises ValueError: if kernel can not reduce the shape to a circular edge
        """
        geom = self._geomAdaptor()
        try:
            circ = geom.Circle()
        except (Standard_NoSuchObject, Standard_Failure) as e:
            raise ValueError("Shape could not be reduced to a circle") from e
        return circ.Radius()

    def IsClosed(self: Mixin1DProtocol) -> bool:

        return BRep_Tool.IsClosed_s(self.wrapped)

    def positionAt(
        self: Mixin1DProtocol,
        d: float,
        mode: Literal["length", "parameter"] = "length",
    ) -> Vector:
        """Generate a position along the underlying curve.
        :param d: distance or parameter value
        :param mode: position calculation mode (default: length)
        :return: A Vector on the underlying curve located at the specified d value.
        """

        curve = self._geomAdaptor()

        if mode == "length":
            param = self.paramAt(d)
        else:
            param = d

        return Vector(curve.Value(param))

    def positions(
        self: Mixin1DProtocol,
        ds: Iterable[float],
        mode: Literal["length", "parameter"] = "length",
    ) -> List[Vector]:
        """Generate positions along the underlying curve
        :param ds: distance or parameter values
        :param mode: position calculation mode (default: length)
        :return: A list of Vector objects.
        """

        return [self.positionAt(d, mode) for d in ds]

    def locationAt(
        self: Mixin1DProtocol,
        d: float,
        mode: Literal["length", "parameter"] = "length",
        frame: Literal["frenet", "corrected"] = "frenet",
        planar: bool = False,
    ) -> Location:
        """Generate a location along the underlying curve.
        :param d: distance or parameter value
        :param mode: position calculation mode (default: length)
        :param frame: moving frame calculation method (default: frenet)
        :param planar: planar mode
        :return: A Location object representing local coordinate system at the specified distance.
        """

        curve, curveh = self._geomAdaptorH()

        if mode == "length":
            param = self.paramAt(d)
        else:
            param = d

        law: GeomFill_TrihedronLaw
        if frame == "frenet":
            law = GeomFill_Frenet()
        else:
            law = GeomFill_CorrectedFrenet()

        law.SetCurve(curveh)

        tangent, normal, binormal = gp_Vec(), gp_Vec(), gp_Vec()

        law.D0(param, tangent, normal, binormal)
        pnt = curve.Value(param)

        T = gp_Trsf()
        if planar:
            T.SetTransformation(
                gp_Ax3(pnt, gp_Dir(0, 0, 1), gp_Dir(normal.XYZ())), gp_Ax3()
            )
        else:
            T.SetTransformation(
                gp_Ax3(pnt, gp_Dir(tangent.XYZ()), gp_Dir(normal.XYZ())), gp_Ax3()
            )

        return Location(TopLoc_Location(T))

    def locations(
        self: Mixin1DProtocol,
        ds: Iterable[float],
        mode: Literal["length", "parameter"] = "length",
        frame: Literal["frenet", "corrected"] = "frenet",
        planar: bool = False,
    ) -> List[Location]:
        """Generate location along the curve
        :param ds: distance or parameter values
        :param mode: position calculation mode (default: length)
        :param frame: moving frame calculation method (default: frenet)
        :param planar: planar mode
        :return: A list of Location objects representing local coordinate systems at the specified distances.
        """

        return [self.locationAt(d, mode, frame, planar) for d in ds]


class Edge(Shape, Mixin1D):
    """
    A trimmed curve that represents the border of a face
    """

    wrapped: TopoDS_Edge

    def _geomAdaptor(self) -> BRepAdaptor_Curve:
        """
        Return the underlying geometry
        """

        return BRepAdaptor_Curve(self.wrapped)

    def _geomAdaptorH(self) -> Tuple[BRepAdaptor_Curve, BRepAdaptor_HCurve]:
        """
        Return the underlying geometry
        """

        curve = self._geomAdaptor()

        return curve, BRepAdaptor_HCurve(curve)

    def close(self) -> Union["Edge", "Wire"]:
        """
        Close an Edge
        """
        rv: Union[Wire, Edge]

        if not self.IsClosed():
            rv = Wire.assembleEdges((self,)).close()
        else:
            rv = self

        return rv

    def arcCenter(self) -> Vector:
        """
        Center of an underlying circle or ellipse geometry.
        """

        g = self.geomType()
        a = self._geomAdaptor()

        if g == "CIRCLE":
            rv = Vector(a.Circle().Position().Location())
        elif g == "ELLIPSE":
            rv = Vector(a.Ellipse().Position().Location())
        else:
            raise ValueError(f"{g} has no arc center")

        return rv

    @classmethod
    def makeCircle(
        cls,
        radius: float,
        pnt: VectorLike = Vector(0, 0, 0),
        dir: VectorLike = Vector(0, 0, 1),
        angle1: float = 360.0,
        angle2: float = 360,
        orientation=True,
    ) -> "Edge":
        pnt = Vector(pnt)
        dir = Vector(dir)

        circle_gp = gp_Circ(gp_Ax2(pnt.toPnt(), dir.toDir()), radius)

        if angle1 == angle2:  # full circle case
            return cls(BRepBuilderAPI_MakeEdge(circle_gp).Edge())
        else:  # arc case
            circle_geom = GC_MakeArcOfCircle(
                circle_gp, angle1 * DEG2RAD, angle2 * DEG2RAD, orientation
            ).Value()
            return cls(BRepBuilderAPI_MakeEdge(circle_geom).Edge())

    @classmethod
    def makeEllipse(
        cls,
        x_radius: float,
        y_radius: float,
        pnt: VectorLike = Vector(0, 0, 0),
        dir: VectorLike = Vector(0, 0, 1),
        xdir: VectorLike = Vector(1, 0, 0),
        angle1: float = 360.0,
        angle2: float = 360.0,
        sense: Literal[-1, 1] = 1,
    ) -> "Edge":
        """
        Makes an Ellipse centered at the provided point, having normal in the provided direction.

        :param cls:
        :param x_radius: x radius of the ellipse (along the x-axis of plane the ellipse should lie in)
        :param y_radius: y radius of the ellipse (along the y-axis of plane the ellipse should lie in)
        :param pnt: vector representing the center of the ellipse
        :param dir: vector representing the direction of the plane the ellipse should lie in
        :param angle1: start angle of arc
        :param angle2: end angle of arc (angle2 == angle1 return closed ellipse = default)
        :param sense: clockwise (-1) or counter clockwise (1)
        :return: an Edge
        """

        pnt_p = Vector(pnt).toPnt()
        dir_d = Vector(dir).toDir()
        xdir_d = Vector(xdir).toDir()

        ax1 = gp_Ax1(pnt_p, dir_d)
        ax2 = gp_Ax2(pnt_p, dir_d, xdir_d)

        if y_radius > x_radius:
            # swap x and y radius and rotate by 90° afterwards to create an ellipse with x_radius < y_radius
            correction_angle = 90.0 * DEG2RAD
            ellipse_gp = gp_Elips(ax2, y_radius, x_radius).Rotated(
                ax1, correction_angle
            )
        else:
            correction_angle = 0.0
            ellipse_gp = gp_Elips(ax2, x_radius, y_radius)

        if angle1 == angle2:  # full ellipse case
            ellipse = cls(BRepBuilderAPI_MakeEdge(ellipse_gp).Edge())
        else:  # arc case
            # take correction_angle into account
            ellipse_geom = GC_MakeArcOfEllipse(
                ellipse_gp,
                angle1 * DEG2RAD - correction_angle,
                angle2 * DEG2RAD - correction_angle,
                sense == 1,
            ).Value()
            ellipse = cls(BRepBuilderAPI_MakeEdge(ellipse_geom).Edge())

        return ellipse

    @classmethod
    def makeSpline(
        cls,
        listOfVector: List[Vector],
        tangents: Optional[Sequence[Vector]] = None,
        periodic: bool = False,
        parameters: Optional[Sequence[float]] = None,
        scale: bool = True,
        tol: float = 1e-6,
    ) -> "Edge":
        """
        Interpolate a spline through the provided points.

        :param listOfVector: a list of Vectors that represent the points
        :param tangents: tuple of Vectors specifying start and finish tangent
        :param periodic: creation of periodic curves
        :param parameters: the value of the parameter at each interpolation point. (The interpolated
          curve is represented as a vector-valued function of a scalar parameter.) If periodic ==
          True, then len(parameters) must be len(intepolation points) + 1, otherwise len(parameters)
          must be equal to len(interpolation points).
        :param scale: whether to scale the specified tangent vectors before interpolating. Each
          tangent is scaled, so it's length is equal to the derivative of the Lagrange interpolated
          curve. I.e., set this to True, if you want to use only the direction of the tangent
          vectors specified by ``tangents``, but not their magnitude.
        :param tol: tolerance of the algorithm (consult OCC documentation). Used to check that the
          specified points are not too close to each other, and that tangent vectors are not too
          short. (In either case interpolation may fail.)
        :return: an Edge
        """
        pnts = TColgp_HArray1OfPnt(1, len(listOfVector))
        for ix, v in enumerate(listOfVector):
            pnts.SetValue(ix + 1, v.toPnt())

        if parameters is None:
            spline_builder = GeomAPI_Interpolate(pnts, periodic, tol)
        else:
            if len(parameters) != (len(listOfVector) + periodic):
                raise ValueError(
                    "There must be one parameter for each interpolation point "
                    "(plus one if periodic), or none specified. Parameter count: "
                    f"{len(parameters)}, point count: {len(listOfVector)}"
                )
            parameters_array = TColStd_HArray1OfReal(1, len(parameters))
            for p_index, p_value in enumerate(parameters):
                parameters_array.SetValue(p_index + 1, p_value)

            spline_builder = GeomAPI_Interpolate(pnts, parameters_array, periodic, tol)

        if tangents:
            if len(tangents) == 2 and len(listOfVector) != 2:
                # Specify only initial and final tangent:
                t1, t2 = tangents
                spline_builder.Load(t1.wrapped, t2.wrapped, scale)
            else:
                if len(tangents) != len(listOfVector):
                    raise ValueError(
                        f"There must be one tangent for each interpolation point, "
                        f"or just two end point tangents. Tangent count: "
                        f"{len(tangents)}, point count: {len(listOfVector)}"
                    )

                # Specify a tangent for each interpolation point:
                tangents_array = TColgp_Array1OfVec(1, len(tangents))
                tangent_enabled_array = TColStd_HArray1OfBoolean(1, len(tangents))
                for t_index, t_value in enumerate(tangents):
                    tangent_enabled_array.SetValue(t_index + 1, t_value is not None)
                    tangent_vec = t_value if t_value is not None else Vector()
                    tangents_array.SetValue(t_index + 1, tangent_vec.wrapped)

                spline_builder.Load(tangents_array, tangent_enabled_array, scale)

        spline_builder.Perform()
        if not spline_builder.IsDone():
            raise ValueError("B-spline interpolation failed")

        spline_geom = spline_builder.Curve()

        return cls(BRepBuilderAPI_MakeEdge(spline_geom).Edge())

    @classmethod
    def makeSplineApprox(
        cls,
        listOfVector: List[Vector],
        tol: float = 1e-3,
        smoothing: Optional[Tuple[float, float, float]] = None,
        minDeg: int = 1,
        maxDeg: int = 6,
    ) -> "Edge":
        """
        Approximate a spline through the provided points.

        :param listOfVector: a list of Vectors that represent the points
        :param tol: tolerance of the algorithm (consult OCC documentation).
        :param smoothing: optional tuple of 3 weights use for variational smoothing (default: None)
        :param minDeg: minimum spline degree. Enforced only when smothing is None (default: 1)
        :param maxDeg: maximum spline degree (default: 6)
        :return: an Edge
        """
        pnts = TColgp_HArray1OfPnt(1, len(listOfVector))
        for ix, v in enumerate(listOfVector):
            pnts.SetValue(ix + 1, v.toPnt())

        if smoothing:
            spline_builder = GeomAPI_PointsToBSpline(
                pnts, *smoothing, DegMax=maxDeg, Tol3D=tol
            )
        else:
            spline_builder = GeomAPI_PointsToBSpline(
                pnts, DegMin=minDeg, DegMax=maxDeg, Tol3D=tol
            )

        if not spline_builder.IsDone():
            raise ValueError("B-spline approximation failed")

        spline_geom = spline_builder.Curve()

        return cls(BRepBuilderAPI_MakeEdge(spline_geom).Edge())

    @classmethod
    def makeThreePointArc(cls, v1: Vector, v2: Vector, v3: Vector) -> "Edge":
        """
        Makes a three point arc through the provided points
        :param cls:
        :param v1: start vector
        :param v2: middle vector
        :param v3: end vector
        :return: an edge object through the three points
        """
        circle_geom = GC_MakeArcOfCircle(v1.toPnt(), v2.toPnt(), v3.toPnt()).Value()

        return cls(BRepBuilderAPI_MakeEdge(circle_geom).Edge())

    @classmethod
    def makeTangentArc(cls, v1: Vector, v2: Vector, v3: Vector) -> "Edge":
        """
        Makes a tangent arc from point v1, in the direction of v2 and ends at
        v3.
        :param cls:
        :param v1: start vector
        :param v2: tangent vector
        :param v3: end vector
        :return: an edge
        """
        circle_geom = GC_MakeArcOfCircle(v1.toPnt(), v2.wrapped, v3.toPnt()).Value()

        return cls(BRepBuilderAPI_MakeEdge(circle_geom).Edge())

    @classmethod
    def makeLine(cls, v1: Vector, v2: Vector) -> "Edge":
        """
        Create a line between two points
        :param v1: Vector that represents the first point
        :param v2: Vector that represents the second point
        :return: A linear edge between the two provided points
        """
        return cls(BRepBuilderAPI_MakeEdge(v1.toPnt(), v2.toPnt()).Edge())


class Wire(Shape, Mixin1D):
    """
    A series of connected, ordered Edges, that typically bounds a Face
    """

    wrapped: TopoDS_Wire

    def _geomAdaptor(self) -> BRepAdaptor_CompCurve:
        """
        Return the underlying geometry
        """

        return BRepAdaptor_CompCurve(self.wrapped)

    def _geomAdaptorH(self) -> Tuple[BRepAdaptor_CompCurve, BRepAdaptor_HCompCurve]:
        """
        Return the underlying geometry
        """

        curve = self._geomAdaptor()

        return curve, BRepAdaptor_HCompCurve(curve)

    def close(self) -> "Wire":
        """
        Close a Wire
        """

        if not self.IsClosed():
            e = Edge.makeLine(self.endPoint(), self.startPoint())
            rv = Wire.combine((self, e))[0]
        else:
            rv = self

        return rv

    @classmethod
    def combine(
        cls, listOfWires: Iterable[Union["Wire", Edge]], tol: float = 1e-9
    ) -> List["Wire"]:
        """
        Attempt to combine a list of wires and edges into a new wire.
        :param cls:
        :param listOfWires:
        :param tol: default 1e-9
        :return: List[Wire]
        """

        edges_in = TopTools_HSequenceOfShape()
        wires_out = TopTools_HSequenceOfShape()

        for e in Compound.makeCompound(listOfWires).Edges():
            edges_in.Append(e.wrapped)

        ShapeAnalysis_FreeBounds.ConnectEdgesToWires_s(edges_in, tol, False, wires_out)

        return [cls(el) for el in wires_out]

    @classmethod
    def assembleEdges(cls, listOfEdges: Iterable[Edge]) -> "Wire":
        """
        Attempts to build a wire that consists of the edges in the provided list
        :param cls:
        :param listOfEdges: a list of Edge objects. The edges are not to be consecutive.
        :return: a wire with the edges assembled
        :BRepBuilderAPI_MakeWire::Error() values
            :BRepBuilderAPI_WireDone = 0
            :BRepBuilderAPI_EmptyWire = 1
            :BRepBuilderAPI_DisconnectedWire = 2
            :BRepBuilderAPI_NonManifoldWire = 3
        """
        wire_builder = BRepBuilderAPI_MakeWire()

        occ_edges_list = TopTools_ListOfShape()
        for e in listOfEdges:
            occ_edges_list.Append(e.wrapped)
        wire_builder.Add(occ_edges_list)

        wire_builder.Build()

        if not wire_builder.IsDone():
            w = (
                "BRepBuilderAPI_MakeWire::Error(): returns the construction status. BRepBuilderAPI_WireDone if the wire is built, or another value of the BRepBuilderAPI_WireError enumeration indicating why the construction failed = "
                + str(wire_builder.Error())
            )
            warnings.warn(w)

        return cls(wire_builder.Wire())

    @classmethod
    def makeCircle(cls, radius: float, center: Vector, normal: Vector) -> "Wire":
        """
        Makes a Circle centered at the provided point, having normal in the provided direction
        :param radius: floating point radius of the circle, must be > 0
        :param center: vector representing the center of the circle
        :param normal: vector representing the direction of the plane the circle should lie in
        :return:
        """

        circle_edge = Edge.makeCircle(radius, center, normal)
        w = cls.assembleEdges([circle_edge])
        return w

    @classmethod
    def makeEllipse(
        cls,
        x_radius: float,
        y_radius: float,
        center: Vector,
        normal: Vector,
        xDir: Vector,
        angle1: float = 360.0,
        angle2: float = 360.0,
        rotation_angle: float = 0.0,
        closed: bool = True,
    ) -> "Wire":
        """
        Makes an Ellipse centered at the provided point, having normal in the provided direction
        :param x_radius: floating point major radius of the ellipse (x-axis), must be > 0
        :param y_radius: floating point minor radius of the ellipse (y-axis), must be > 0
        :param center: vector representing the center of the circle
        :param normal: vector representing the direction of the plane the circle should lie in
        :param angle1: start angle of arc
        :param angle2: end angle of arc
        :param rotation_angle: angle to rotate the created ellipse / arc
        :return: Wire
        """

        ellipse_edge = Edge.makeEllipse(
            x_radius, y_radius, center, normal, xDir, angle1, angle2
        )

        if angle1 != angle2 and closed:
            line = Edge.makeLine(ellipse_edge.endPoint(), ellipse_edge.startPoint())
            w = cls.assembleEdges([ellipse_edge, line])
        else:
            w = cls.assembleEdges([ellipse_edge])

        if rotation_angle != 0.0:
            w = w.rotate(center, center + normal, rotation_angle)

        return w

    @classmethod
    def makePolygon(
        cls, listOfVertices: Iterable[Vector], forConstruction: bool = False,
    ) -> "Wire":
        # convert list of tuples into Vectors.
        wire_builder = BRepBuilderAPI_MakePolygon()

        for v in listOfVertices:
            wire_builder.Add(v.toPnt())

        w = cls(wire_builder.Wire())
        w.forConstruction = forConstruction

        return w

    @classmethod
    def makeHelix(
        cls,
        pitch: float,
        height: float,
        radius: float,
        center: Vector = Vector(0, 0, 0),
        dir: Vector = Vector(0, 0, 1),
        angle: float = 360.0,
        lefthand: bool = False,
    ) -> "Wire":
        """
        Make a helix with a given pitch, height and radius
        By default a cylindrical surface is used to create the helix. If
        the fourth parameter is set (the apex given in degree) a conical surface is used instead'
        """

        # 1. build underlying cylindrical/conical surface
        if angle == 360.0:
            geom_surf: Geom_Surface = Geom_CylindricalSurface(
                gp_Ax3(center.toPnt(), dir.toDir()), radius
            )
        else:
            geom_surf = Geom_ConicalSurface(
                gp_Ax3(center.toPnt(), dir.toDir()), angle * DEG2RAD, radius
            )

        # 2. construct an segment in the u,v domain
        if lefthand:
            geom_line = Geom2d_Line(gp_Pnt2d(0.0, 0.0), gp_Dir2d(-2 * pi, pitch))
        else:
            geom_line = Geom2d_Line(gp_Pnt2d(0.0, 0.0), gp_Dir2d(2 * pi, pitch))

        # 3. put it together into a wire
        n_turns = height / pitch
        u_start = geom_line.Value(0.0)
        u_stop = geom_line.Value(n_turns * sqrt((2 * pi) ** 2 + pitch ** 2))
        geom_seg = GCE2d_MakeSegment(u_start, u_stop).Value()

        e = BRepBuilderAPI_MakeEdge(geom_seg, geom_surf).Edge()

        # 4. Convert to wire and fix building 3d geom from 2d geom
        w = BRepBuilderAPI_MakeWire(e).Wire()
        BRepLib.BuildCurves3d_s(w, 1e-6, MaxSegment=2000)  # NB: preliminary values

        return cls(w)

    def stitch(self, other: "Wire") -> "Wire":
        """Attempt to stich wires"""

        wire_builder = BRepBuilderAPI_MakeWire()
        wire_builder.Add(TopoDS.Wire_s(self.wrapped))
        wire_builder.Add(TopoDS.Wire_s(other.wrapped))
        wire_builder.Build()

        return self.__class__(wire_builder.Wire())

    def offset2D(
        self, d: float, kind: Literal["arc", "intersection", "tangent"] = "arc"
    ) -> List["Wire"]:
        """Offsets a planar wire"""

        kind_dict = {
            "arc": GeomAbs_JoinType.GeomAbs_Arc,
            "intersection": GeomAbs_JoinType.GeomAbs_Intersection,
            "tangent": GeomAbs_JoinType.GeomAbs_Tangent,
        }

        offset = BRepOffsetAPI_MakeOffset()
        offset.Init(kind_dict[kind])
        offset.AddWire(self.wrapped)
        offset.Perform(d)

        obj = downcast(offset.Shape())

        if isinstance(obj, TopoDS_Compound):
            rv = [self.__class__(el.wrapped) for el in Compound(obj)]
        else:
            rv = [self.__class__(obj)]

        return rv

    def fillet2D(self, radius: float, vertices: Iterable[Vertex]) -> "Wire":
        """
        Apply 2D fillet to a wire
        """

        f = Face.makeFromWires(self)

        return f.fillet2D(radius, vertices).outerWire()

    def chamfer2D(self, d: float, vertices: Iterable[Vertex]) -> "Wire":
        """
        Apply 2D chamfer to a wire
        """

        f = Face.makeFromWires(self)

        return f.chamfer2D(d, vertices).outerWire()


class Face(Shape):
    """
    a bounded surface that represents part of the boundary of a solid
    """

    wrapped: TopoDS_Face

    def _geomAdaptor(self) -> Geom_Surface:
        """
        Return the underlying geometry
        """
        return BRep_Tool.Surface_s(self.wrapped)

    def _uvBounds(self) -> Tuple[float, float, float, float]:

        return BRepTools.UVBounds_s(self.wrapped)

    def normalAt(self, locationVector: Optional[Vector] = None) -> Vector:
        """
        Computes the normal vector at the desired location on the face.

        :returns: a  vector representing the direction
        :param locationVector: the location to compute the normal at. If none, the center of the face is used.
        :type locationVector: a vector that lies on the surface.
        """
        # get the geometry
        surface = self._geomAdaptor()

        if locationVector is None:
            u0, u1, v0, v1 = self._uvBounds()
            u = 0.5 * (u0 + u1)
            v = 0.5 * (v0 + v1)
        else:
            # project point on surface
            projector = GeomAPI_ProjectPointOnSurf(locationVector.toPnt(), surface)

            u, v = projector.LowerDistanceParameters()

        p = gp_Pnt()
        vn = gp_Vec()
        BRepGProp_Face(self.wrapped).Normal(u, v, p, vn)

        return Vector(vn)

    def Center(self) -> Vector:

        Properties = GProp_GProps()
        BRepGProp.SurfaceProperties_s(self.wrapped, Properties)

        return Vector(Properties.CentreOfMass())

    def outerWire(self) -> Wire:

        return Wire(BRepTools.OuterWire_s(self.wrapped))

    def innerWires(self) -> List[Wire]:

        outer = self.outerWire()

        return [w for w in self.Wires() if not w.isSame(outer)]

    @classmethod
    def makeNSidedSurface(
        cls,
        edges: Iterable[Edge],
        points: Iterable[gp_Pnt],
        continuity: GeomAbs_Shape = GeomAbs_C0,
        degree: int = 3,
        nbPtsOnCur: int = 15,
        nbIter: int = 2,
        anisotropy: bool = False,
        tol2d: float = 0.00001,
        tol3d: float = 0.0001,
        tolAng: float = 0.01,
        tolCurv: float = 0.1,
        maxDeg: int = 8,
        maxSegments: int = 9,
    ) -> "Face":
        """
        Returns a surface enclosed by a closed polygon defined by 'edges' and going through 'points'.
        :param points
        :type points: list of gp_Pnt
        :param edges
        :type edges: list of Edge
        :param continuity=GeomAbs_C0
        :type continuity: OCC.Core.GeomAbs continuity condition
        :param Degree = 3 (OCCT default)
        :type Degree: Integer >= 2
        :param NbPtsOnCur = 15 (OCCT default)
        :type: NbPtsOnCur Integer >= 15
        :param NbIter = 2 (OCCT default)
        :type: NbIterInteger >= 2
        :param Anisotropie = False (OCCT default)
        :type Anisotropie: Boolean
        :param: Tol2d = 0.00001 (OCCT default)
        :type Tol2d: float > 0
        :param Tol3d = 0.0001 (OCCT default)
        :type Tol3dReal: float > 0
        :param TolAng = 0.01 (OCCT default)
        :type TolAngReal: float > 0
        :param TolCurv = 0.1 (OCCT default)
        :type TolCurvReal: float > 0
        :param MaxDeg = 8 (OCCT default)
        :type MaxDegInteger: Integer >= 2 (?)
        :param MaxSegments = 9 (OCCT default)
        :type MaxSegments: Integer >= 2 (?)
        """

        n_sided = BRepOffsetAPI_MakeFilling(
            degree,
            nbPtsOnCur,
            nbIter,
            anisotropy,
            tol2d,
            tol3d,
            tolAng,
            tolCurv,
            maxDeg,
            maxSegments,
        )
        for edge in edges:
            n_sided.Add(edge.wrapped, continuity)
        for pt in points:
            n_sided.Add(pt)
        n_sided.Build()
        face = n_sided.Shape()
        return Face(face).fix()

    @classmethod
    def makePlane(
        cls,
        length: Optional[float] = None,
        width: Optional[float] = None,
        basePnt: VectorLike = (0, 0, 0),
        dir: VectorLike = (0, 0, 1),
    ) -> "Face":
        basePnt = Vector(basePnt)
        dir = Vector(dir)

        pln_geom = gp_Pln(basePnt.toPnt(), dir.toDir())

        if length and width:
            pln_shape = BRepBuilderAPI_MakeFace(
                pln_geom, -width * 0.5, width * 0.5, -length * 0.5, length * 0.5
            ).Face()
        else:
            pln_shape = BRepBuilderAPI_MakeFace(pln_geom).Face()

        return cls(pln_shape)

    @overload
    @classmethod
    def makeRuledSurface(cls, edgeOrWire1: Edge, edgeOrWire2: Edge) -> "Face":
        ...

    @overload
    @classmethod
    def makeRuledSurface(cls, edgeOrWire1: Wire, edgeOrWire2: Wire) -> "Face":
        ...

    @classmethod
    def makeRuledSurface(cls, edgeOrWire1, edgeOrWire2):
        """
        'makeRuledSurface(Edge|Wire,Edge|Wire) -- Make a ruled surface
        Create a ruled surface out of two edges or wires. If wires are used then
        these must have the same number of edges
        """

        if isinstance(edgeOrWire1, Wire):
            return cls.cast(BRepFill.Shell_s(edgeOrWire1.wrapped, edgeOrWire2.wrapped))
        else:
            return cls.cast(BRepFill.Face_s(edgeOrWire1.wrapped, edgeOrWire2.wrapped))

    @classmethod
    def makeFromWires(cls, outerWire: Wire, innerWires: List[Wire] = []) -> "Face":
        """
        Makes a planar face from one or more wires
        """

        if innerWires and not outerWire.IsClosed():
            raise ValueError("Cannot build face(s): outer wire is not closed")

        # check if wires are coplanar
        ws = Compound.makeCompound([outerWire] + innerWires)
        if not BRepLib_FindSurface(ws.wrapped, OnlyPlane=True).Found():
            raise ValueError("Cannot build face(s): wires not planar")

        # fix outer wire
        sf_s = ShapeFix_Shape(outerWire.wrapped)
        sf_s.Perform()
        wo = TopoDS.Wire_s(sf_s.Shape())

        face_builder = BRepBuilderAPI_MakeFace(wo, True)

        for w in innerWires:
            if not w.IsClosed():
                raise ValueError("Cannot build face(s): inner wire is not closed")
            face_builder.Add(w.wrapped)

        face_builder.Build()

        if not face_builder.IsDone():
            raise ValueError(f"Cannot build face(s): {face_builder.Error()}")

        face = face_builder.Face()

        sf_f = ShapeFix_Face(face)
        sf_f.FixOrientation()
        sf_f.Perform()

        return cls(sf_f.Result())

    @classmethod
    def makeSplineApprox(
        cls,
        points: List[List[Vector]],
        tol: float = 1e-2,
        smoothing: Optional[Tuple[float, float, float]] = None,
        minDeg: int = 1,
        maxDeg: int = 3,
    ) -> "Face":
        """
        Approximate a spline surface through the provided points.

        :param points: a 2D list of Vectors that represent the points
        :param tol: tolerance of the algorithm (consult OCC documentation).
        :param smoothing: optional tuple of 3 weights use for variational smoothing (default: None)
        :param minDeg: minimum spline degree. Enforced only when smothing is None (default: 1)
        :param maxDeg: maximum spline degree (default: 6)
        :return: an Face
        """
        points_ = TColgp_HArray2OfPnt(1, len(points), 1, len(points[0]))

        for i, vi in enumerate(points):
            for j, v in enumerate(vi):
                points_.SetValue(i + 1, j + 1, v.toPnt())

        if smoothing:
            spline_builder = GeomAPI_PointsToBSplineSurface(
                points_, *smoothing, DegMax=maxDeg, Tol3D=tol
            )
        else:
            spline_builder = GeomAPI_PointsToBSplineSurface(
                points_, DegMin=minDeg, DegMax=maxDeg, Tol3D=tol
            )

        if not spline_builder.IsDone():
            raise ValueError("B-spline approximation failed")

        spline_geom = spline_builder.Surface()

        return cls(BRepBuilderAPI_MakeFace(spline_geom, Precision.Confusion_s()).Face())

    def fillet2D(self, radius: float, vertices: Iterable[Vertex]) -> "Face":
        """
        Apply 2D fillet to a face
        """

        fillet_builder = BRepFilletAPI_MakeFillet2d(self.wrapped)

        for v in vertices:
            fillet_builder.AddFillet(v.wrapped, radius)

        fillet_builder.Build()

        return self.__class__(fillet_builder.Shape())

    def chamfer2D(self, d: float, vertices: Iterable[Vertex]) -> "Face":
        """
        Apply 2D chamfer to a face
        """

        chamfer_builder = BRepFilletAPI_MakeFillet2d(self.wrapped)
        edge_map = self._entitiesFrom("Vertex", "Edge")

        for v in vertices:
            edges = edge_map[v]
            if len(edges) < 2:
                raise ValueError("Cannot chamfer at this location")

            e1, e2 = edges

            chamfer_builder.AddChamfer(
                TopoDS.Edge_s(e1.wrapped), TopoDS.Edge_s(e2.wrapped), d, d
            )

        chamfer_builder.Build()

        return self.__class__(chamfer_builder.Shape()).fix()

    def toPln(self) -> gp_Pln:
        """
        Convert this face to a gp_Pln.

        Note the Location of the resulting plane may not equal the center of this face,
        however the resulting plane will still contain the center of this face.
        """

        adaptor = BRepAdaptor_Surface(self.wrapped)
        return adaptor.Plane()


class Shell(Shape):
    """
    the outer boundary of a surface
    """

    wrapped: TopoDS_Shell

    @classmethod
    def makeShell(cls, listOfFaces: Iterable[Face]) -> "Shell":

        shell_builder = BRepBuilderAPI_Sewing()

        for face in listOfFaces:
            shell_builder.Add(face.wrapped)

        shell_builder.Perform()
        s = shell_builder.SewedShape()

        return cls(s)


TS = TypeVar("TS", bound=ShapeProtocol)


class Mixin3D(object):
    def fillet(self: Any, radius: float, edgeList: Iterable[Edge]) -> Any:
        """
        Fillets the specified edges of this solid.
        :param radius: float > 0, the radius of the fillet
        :param edgeList:  a list of Edge objects, which must belong to this solid
        :return: Filleted solid
        """
        nativeEdges = [e.wrapped for e in edgeList]

        fillet_builder = BRepFilletAPI_MakeFillet(self.wrapped)

        for e in nativeEdges:
            fillet_builder.Add(radius, e)

        return self.__class__(fillet_builder.Shape())

    def chamfer(
        self: Any, length: float, length2: Optional[float], edgeList: Iterable[Edge]
    ) -> Any:
        """
        Chamfers the specified edges of this solid.
        :param length: length > 0, the length (length) of the chamfer
        :param length2: length2 > 0, optional parameter for asymmetrical chamfer. Should be `None` if not required.
        :param edgeList:  a list of Edge objects, which must belong to this solid
        :return: Chamfered solid
        """
        nativeEdges = [e.wrapped for e in edgeList]

        # make a edge --> faces mapping
        edge_face_map = TopTools_IndexedDataMapOfShapeListOfShape()
        TopExp.MapShapesAndAncestors_s(
            self.wrapped, ta.TopAbs_EDGE, ta.TopAbs_FACE, edge_face_map
        )

        # note: we prefer 'length' word to 'radius' as opposed to FreeCAD's API
        chamfer_builder = BRepFilletAPI_MakeChamfer(self.wrapped)

        if length2:
            d1 = length
            d2 = length2
        else:
            d1 = length
            d2 = length

        for e in nativeEdges:
            face = edge_face_map.FindFromKey(e).First()
            chamfer_builder.Add(
                d1, d2, e, TopoDS.Face_s(face)
            )  # NB: edge_face_map return a generic TopoDS_Shape
        return self.__class__(chamfer_builder.Shape())

    def shell(
        self: Any,
        faceList: Optional[Iterable[Face]],
        thickness: float,
        tolerance: float = 0.0001,
        kind: Literal["arc", "intersection"] = "arc",
    ) -> Any:
        """
        Make a shelled solid of self.

        :param faceList: List of faces to be removed, which must be part of the solid. Can
          be an empty list.
        :param thickness: Floating point thickness. Positive shells outwards, negative
          shells inwards.
        :param tolerance: Modelling tolerance of the method, default=0.0001.
        :return: A shelled solid.
        """

        kind_dict = {
            "arc": GeomAbs_JoinType.GeomAbs_Arc,
            "intersection": GeomAbs_JoinType.GeomAbs_Intersection,
        }

        occ_faces_list = TopTools_ListOfShape()
        shell_builder = BRepOffsetAPI_MakeThickSolid()

        if faceList:
            for f in faceList:
                occ_faces_list.Append(f.wrapped)

        shell_builder.MakeThickSolidByJoin(
            self.wrapped,
            occ_faces_list,
            thickness,
            tolerance,
            Intersection=True,
            Join=kind_dict[kind],
        )
        shell_builder.Build()

        if faceList:
            rv = self.__class__(shell_builder.Shape())

        else:  # if no faces provided a watertight solid will be constructed
            s1 = self.__class__(shell_builder.Shape()).Shells()[0].wrapped
            s2 = self.Shells()[0].wrapped

            # s1 can be outer or inner shell depending on the thickness sign
            if thickness > 0:
                sol = BRepBuilderAPI_MakeSolid(s1, s2)
            else:
                sol = BRepBuilderAPI_MakeSolid(s2, s1)

            # fix needed for the orientations
            rv = self.__class__(sol.Shape()).fix()

        return rv

    def isInside(
        self: ShapeProtocol, point: VectorLike, tolerance: float = 1.0e-6
    ) -> bool:
        """
        Returns whether or not the point is inside a solid or compound
        object within the specified tolerance.

        :param point: tuple or Vector representing 3D point to be tested
        :param tolerance: tolerance for inside determination, default=1.0e-6
        :return: bool indicating whether or not point is within solid
        """
        if isinstance(point, Vector):
            point = point.toTuple()

        solid_classifier = BRepClass3d_SolidClassifier(self.wrapped)
        solid_classifier.Perform(gp_Pnt(*point), tolerance)

        return solid_classifier.State() == ta.TopAbs_IN or solid_classifier.IsOnAFace()

    @multimethod
    def dprism(
        self: TS,
        basis: Optional[Face],
        profiles: List[Wire],
        depth: Optional[Real] = None,
        taper: Real = 0,
        upToFace: Optional[Face] = None,
        thruAll: bool = True,
        additive: bool = True,
    ) -> "Solid":
        """
        Make a prismatic feature (additive or subtractive)

        :param basis: face to perform the operation on
        :param profiles: list of profiles
        :param depth: depth of the cut or extrusion
        :param upToFace: a face to extrude until
        :param thruAll: cut thruAll
        :return: a Solid object
        """

        sorted_profiles = sortWiresByBuildOrder(profiles)
        faces = [Face.makeFromWires(p[0], p[1:]) for p in sorted_profiles]

        return self.dprism(basis, faces, depth, taper, upToFace, thruAll, additive)

    @dprism.register
    def dprism(
        self: TS,
        basis: Optional[Face],
        faces: List[Face],
        depth: Optional[Real] = None,
        taper: Real = 0,
        upToFace: Optional[Face] = None,
        thruAll: bool = True,
        additive: bool = True,
    ) -> "Solid":

        shape: Union[TopoDS_Shape, TopoDS_Solid] = self.wrapped
        for face in faces:
            feat = BRepFeat_MakeDPrism(
                shape,
                face.wrapped,
                basis.wrapped if basis else TopoDS_Face(),
                taper * DEG2RAD,
                additive,
                False,
            )

            if upToFace is not None:
                feat.Perform(upToFace.wrapped)
            elif thruAll or depth is None:
                feat.PerformThruAll()
            else:
                feat.Perform(depth)

            shape = feat.Shape()

        return self.__class__(shape)


class Solid(Shape, Mixin3D):
    """
    a single solid
    """

    wrapped: TopoDS_Solid

    @classmethod
    def interpPlate(
        cls,
        surf_edges,
        surf_pts,
        thickness,
        degree=3,
        nbPtsOnCur=15,
        nbIter=2,
        anisotropy=False,
        tol2d=0.00001,
        tol3d=0.0001,
        tolAng=0.01,
        tolCurv=0.1,
        maxDeg=8,
        maxSegments=9,
    ) -> Union["Solid", Face]:
        """
        Returns a plate surface that is 'thickness' thick, enclosed by 'surf_edge_pts' points,  and going through 'surf_pts' points.

        :param surf_edges
        :type 1 surf_edges: list of [x,y,z] float ordered coordinates
        :type 2 surf_edges: list of ordered or unordered CadQuery wires
        :param surf_pts = [] (uses only edges if [])
        :type surf_pts: list of [x,y,z] float coordinates
        :param thickness = 0 (returns 2D surface if 0)
        :type thickness: float (may be negative or positive depending on thickening direction)
        :param Degree = 3 (OCCT default)
        :type Degree: Integer >= 2
        :param NbPtsOnCur = 15 (OCCT default)
        :type: NbPtsOnCur Integer >= 15
        :param NbIter = 2 (OCCT default)
        :type: NbIterInteger >= 2
        :param Anisotropie = False (OCCT default)
        :type Anisotropie: Boolean
        :param: Tol2d = 0.00001 (OCCT default)
        :type Tol2d: float > 0
        :param Tol3d = 0.0001 (OCCT default)
        :type Tol3dReal: float > 0
        :param TolAng = 0.01 (OCCT default)
        :type TolAngReal: float > 0
        :param TolCurv = 0.1 (OCCT default)
        :type TolCurvReal: float > 0
        :param MaxDeg = 8 (OCCT default)
        :type MaxDegInteger: Integer >= 2 (?)
        :param MaxSegments = 9 (OCCT default)
        :type MaxSegments: Integer >= 2 (?)
        """

        # POINTS CONSTRAINTS: list of (x,y,z) points, optional.
        pts_array = [gp_Pnt(*pt) for pt in surf_pts]

        # EDGE CONSTRAINTS
        # If a list of wires is provided, make a closed wire
        if not isinstance(surf_edges, list):
            surf_edges = [o.vals()[0] for o in surf_edges.all()]
            surf_edges = Wire.assembleEdges(surf_edges)
            w = surf_edges.wrapped

        # If a list of (x,y,z) points provided, build closed polygon
        if isinstance(surf_edges, list):
            e_array = [Vector(*e) for e in surf_edges]
            wire_builder = BRepBuilderAPI_MakePolygon()
            for e in e_array:  # Create polygon from edges
                wire_builder.Add(e.toPnt())
            wire_builder.Close()
            w = wire_builder.Wire()

        edges = [i for i in Shape(w).Edges()]

        # MAKE SURFACE
        continuity = GeomAbs_C0  # Fixed, changing to anything else crashes.
        face = Face.makeNSidedSurface(
            edges,
            pts_array,
            continuity,
            degree,
            nbPtsOnCur,
            nbIter,
            anisotropy,
            tol2d,
            tol3d,
            tolAng,
            tolCurv,
            maxDeg,
            maxSegments,
        )

        # THICKEN SURFACE
        if (
            abs(thickness) > 0
        ):  # abs() because negative values are allowed to set direction of thickening
            solid = BRepOffset_MakeOffset()
            solid.Initialize(
                face.wrapped,
                thickness,
                1.0e-5,
                BRepOffset_Skin,
                False,
                False,
                GeomAbs_Intersection,
                True,
            )  # The last True is important to make solid
            solid.MakeOffsetShape()
            return cls(solid.Shape())
        else:  # Return 2D surface only
            return face

    @staticmethod
    def isSolid(obj: Shape) -> bool:
        """
        Returns true if the object is a solid, false otherwise
        """
        if hasattr(obj, "ShapeType"):
            if obj.ShapeType == "Solid" or (
                obj.ShapeType == "Compound" and len(obj.Solids()) > 0
            ):
                return True
        return False

    @classmethod
    def makeSolid(cls, shell: Shell) -> "Solid":

        return cls(ShapeFix_Solid().SolidFromShell(shell.wrapped))

    @classmethod
    def makeBox(
        cls,
        length: float,
        width: float,
        height: float,
        pnt: Vector = Vector(0, 0, 0),
        dir: Vector = Vector(0, 0, 1),
    ) -> "Solid":
        """
        makeBox(length,width,height,[pnt,dir]) -- Make a box located in pnt with the dimensions (length,width,height)
        By default pnt=Vector(0,0,0) and dir=Vector(0,0,1)'
        """
        return cls(
            BRepPrimAPI_MakeBox(
                gp_Ax2(pnt.toPnt(), dir.toDir()), length, width, height
            ).Shape()
        )

    @classmethod
    def makeCone(
        cls,
        radius1: float,
        radius2: float,
        height: float,
        pnt: Vector = Vector(0, 0, 0),
        dir: Vector = Vector(0, 0, 1),
        angleDegrees: float = 360,
    ) -> "Solid":
        """
        Make a cone with given radii and height
        By default pnt=Vector(0,0,0),
        dir=Vector(0,0,1) and angle=360'
        """
        return cls(
            BRepPrimAPI_MakeCone(
                gp_Ax2(pnt.toPnt(), dir.toDir()),
                radius1,
                radius2,
                height,
                angleDegrees * DEG2RAD,
            ).Shape()
        )

    @classmethod
    def makeCylinder(
        cls,
        radius: float,
        height: float,
        pnt: Vector = Vector(0, 0, 0),
        dir: Vector = Vector(0, 0, 1),
        angleDegrees: float = 360,
    ) -> "Solid":
        """
        makeCylinder(radius,height,[pnt,dir,angle]) --
        Make a cylinder with a given radius and height
        By default pnt=Vector(0,0,0),dir=Vector(0,0,1) and angle=360'
        """
        return cls(
            BRepPrimAPI_MakeCylinder(
                gp_Ax2(pnt.toPnt(), dir.toDir()), radius, height, angleDegrees * DEG2RAD
            ).Shape()
        )

    @classmethod
    def makeTorus(
        cls,
        radius1: float,
        radius2: float,
        pnt: Vector = Vector(0, 0, 0),
        dir: Vector = Vector(0, 0, 1),
        angleDegrees1: float = 0,
        angleDegrees2: float = 360,
    ) -> "Solid":
        """
        makeTorus(radius1,radius2,[pnt,dir,angle1,angle2,angle]) --
        Make a torus with a given radii and angles
        By default pnt=Vector(0,0,0),dir=Vector(0,0,1),angle1=0
        ,angle1=360 and angle=360'
        """
        return cls(
            BRepPrimAPI_MakeTorus(
                gp_Ax2(pnt.toPnt(), dir.toDir()),
                radius1,
                radius2,
                angleDegrees1 * DEG2RAD,
                angleDegrees2 * DEG2RAD,
            ).Shape()
        )

    @classmethod
    def makeLoft(cls, listOfWire: List[Wire], ruled: bool = False) -> "Solid":
        """
        makes a loft from a list of wires
        The wires will be converted into faces when possible-- it is presumed that nobody ever actually
        wants to make an infinitely thin shell for a real FreeCADPart.
        """
        # the True flag requests building a solid instead of a shell.
        if len(listOfWire) < 2:
            raise ValueError("More than one wire is required")
        loft_builder = BRepOffsetAPI_ThruSections(True, ruled)

        for w in listOfWire:
            loft_builder.AddWire(w.wrapped)

        loft_builder.Build()

        return cls(loft_builder.Shape())

    @classmethod
    def makeWedge(
        cls,
        dx: float,
        dy: float,
        dz: float,
        xmin: float,
        zmin: float,
        xmax: float,
        zmax: float,
        pnt: Vector = Vector(0, 0, 0),
        dir: Vector = Vector(0, 0, 1),
    ) -> "Solid":
        """
        Make a wedge located in pnt
        By default pnt=Vector(0,0,0) and dir=Vector(0,0,1)
        """

        return cls(
            BRepPrimAPI_MakeWedge(
                gp_Ax2(pnt.toPnt(), dir.toDir()), dx, dy, dz, xmin, zmin, xmax, zmax
            ).Solid()
        )

    @classmethod
    def makeSphere(
        cls,
        radius: float,
        pnt: Vector = Vector(0, 0, 0),
        dir: Vector = Vector(0, 0, 1),
        angleDegrees1: float = 0,
        angleDegrees2: float = 90,
        angleDegrees3: float = 360,
    ) -> "Shape":
        """
        Make a sphere with a given radius
        By default pnt=Vector(0,0,0), dir=Vector(0,0,1), angle1=0, angle2=90 and angle3=360
        """
        return cls(
            BRepPrimAPI_MakeSphere(
                gp_Ax2(pnt.toPnt(), dir.toDir()),
                radius,
                angleDegrees1 * DEG2RAD,
                angleDegrees2 * DEG2RAD,
                angleDegrees3 * DEG2RAD,
            ).Shape()
        )

    @classmethod
    def _extrudeAuxSpine(
        cls, wire: TopoDS_Wire, spine: TopoDS_Wire, auxSpine: TopoDS_Wire
    ) -> TopoDS_Shape:
        """
        Helper function for extrudeLinearWithRotation
        """
        extrude_builder = BRepOffsetAPI_MakePipeShell(spine)
        extrude_builder.SetMode(auxSpine, False)  # auxiliary spine
        extrude_builder.Add(wire)
        extrude_builder.Build()
        extrude_builder.MakeSolid()
        return extrude_builder.Shape()

    @multimethod
    def extrudeLinearWithRotation(
        cls,
        outerWire: Wire,
        innerWires: List[Wire],
        vecCenter: Vector,
        vecNormal: Vector,
        angleDegrees: Real,
    ) -> "Solid":
        """
        Creates a 'twisted prism' by extruding, while simultaneously rotating around the extrusion vector.

        Though the signature may appear to be similar enough to extrudeLinear to merit combining them, the
        construction methods used here are different enough that they should be separate.

        At a high level, the steps followed are:
        (1) accept a set of wires
        (2) create another set of wires like this one, but which are transformed and rotated
        (3) create a ruledSurface between the sets of wires
        (4) create a shell and compute the resulting object

        :param outerWire: the outermost wire, a cad.Wire
        :param innerWires: a list of inner wires, a list of cad.Wire
        :param vecCenter: the center point about which to rotate.  the axis of rotation is defined by
               vecNormal, located at vecCenter. ( a cad.Vector )
        :param vecNormal: a vector along which to extrude the wires ( a cad.Vector )
        :param angleDegrees: the angle to rotate through while extruding
        :return: a cad.Solid object
        """
        # make straight spine
        straight_spine_e = Edge.makeLine(vecCenter, vecCenter.add(vecNormal))
        straight_spine_w = Wire.combine([straight_spine_e,])[0].wrapped

        # make an auxiliary spine
        pitch = 360.0 / angleDegrees * vecNormal.Length
        radius = 1
        aux_spine_w = Wire.makeHelix(
            pitch, vecNormal.Length, radius, center=vecCenter, dir=vecNormal
        ).wrapped

        # extrude the outer wire
        outer_solid = cls._extrudeAuxSpine(
            outerWire.wrapped, straight_spine_w, aux_spine_w
        )

        # extrude inner wires
        inner_solids = [
            cls._extrudeAuxSpine(w.wrapped, straight_spine_w, aux_spine_w)
            for w in innerWires
        ]

        # combine the inner solids into compound
        inner_comp = Compound._makeCompound(inner_solids)

        # subtract from the outer solid
        return cls(BRepAlgoAPI_Cut(outer_solid, inner_comp).Shape())

    @classmethod
    @extrudeLinearWithRotation.register
    def extrudeLinearWithRotation(
        cls, face: Face, vecCenter: Vector, vecNormal: Vector, angleDegrees: Real,
    ) -> "Solid":

        return cls.extrudeLinearWithRotation(
            face.outerWire(), face.innerWires(), vecCenter, vecNormal, angleDegrees
        )

    @multimethod
    def extrudeLinear(
        cls,
        outerWire: Wire,
        innerWires: List[Wire],
        vecNormal: Vector,
        taper: Real = 0,
    ) -> "Solid":
        """
        Attempt to extrude the list of wires  into a prismatic solid in the provided direction

        :param outerWire: the outermost wire
        :param innerWires: a list of inner wires
        :param vecNormal: a vector along which to extrude the wires
        :param taper: taper angle, default=0
        :return: a Solid object

        The wires must not intersect

        Extruding wires is very non-trivial.  Nested wires imply very different geometry, and
        there are many geometries that are invalid. In general, the following conditions must be met:

        * all wires must be closed
        * there cannot be any intersecting or self-intersecting wires
        * wires must be listed from outside in
        * more than one levels of nesting is not supported reliably

        This method will attempt to sort the wires, but there is much work remaining to make this method
        reliable.
        """

        if taper == 0:
            face = Face.makeFromWires(outerWire, innerWires)
        else:
            face = Face.makeFromWires(outerWire)

        return cls.extrudeLinear(face, vecNormal, taper)

    @classmethod
    @extrudeLinear.register
    def extrudeLinear(cls, face: Face, vecNormal: Vector, taper: Real = 0,) -> "Solid":

        if taper == 0:
            prism_builder: Any = BRepPrimAPI_MakePrism(
                face.wrapped, vecNormal.wrapped, True
            )
        else:
            faceNormal = face.normalAt()
            d = 1 if vecNormal.getAngle(faceNormal) < 90 * DEG2RAD else -1
            prism_builder = LocOpe_DPrism(
                face.wrapped, d * vecNormal.Length, d * taper * DEG2RAD
            )

        return cls(prism_builder.Shape())

    @multimethod
    def revolve(
        cls,
        outerWire: Wire,
        innerWires: List[Wire],
        angleDegrees: Real,
        axisStart: Vector,
        axisEnd: Vector,
    ) -> "Solid":
        """
        Attempt to revolve the list of wires into a solid in the provided direction

        :param outerWire: the outermost wire
        :param innerWires: a list of inner wires
        :param angleDegrees: the angle to revolve through.
        :type angleDegrees: float, anything less than 360 degrees will leave the shape open
        :param axisStart: the start point of the axis of rotation
        :type axisStart: tuple, a two tuple
        :param axisEnd: the end point of the axis of rotation
        :type axisEnd: tuple, a two tuple
        :return: a Solid object

        The wires must not intersect

        * all wires must be closed
        * there cannot be any intersecting or self-intersecting wires
        * wires must be listed from outside in
        * more than one levels of nesting is not supported reliably
        * the wire(s) that you're revolving cannot be centered

        This method will attempt to sort the wires, but there is much work remaining to make this method
        reliable.
        """
        face = Face.makeFromWires(outerWire, innerWires)

        return cls.revolve(face, angleDegrees, axisStart, axisEnd)

    @classmethod
    @revolve.register
    def revolve(
        cls, face: Face, angleDegrees: Real, axisStart: Vector, axisEnd: Vector,
    ) -> "Solid":

        v1 = Vector(axisStart)
        v2 = Vector(axisEnd)
        v2 = v2 - v1
        revol_builder = BRepPrimAPI_MakeRevol(
            face.wrapped, gp_Ax1(v1.toPnt(), v2.toDir()), angleDegrees * DEG2RAD, True
        )

        return cls(revol_builder.Shape())

    _transModeDict = {
        "transformed": BRepBuilderAPI_Transformed,
        "round": BRepBuilderAPI_RoundCorner,
        "right": BRepBuilderAPI_RightCorner,
    }

    @classmethod
    def _setSweepMode(
        cls,
        builder: BRepOffsetAPI_MakePipeShell,
        path: Union[Wire, Edge],
        mode: Union[Vector, Wire, Edge],
    ) -> bool:

        rotate = False

        if isinstance(mode, Vector):
            ax = gp_Ax2()
            ax.SetLocation(path.startPoint().toPnt())
            ax.SetDirection(mode.toDir())
            builder.SetMode(ax)
            rotate = True
        elif isinstance(mode, (Wire, Edge)):
            builder.SetMode(cls._toWire(mode).wrapped, True)

        return rotate

    @staticmethod
    def _toWire(p: Union[Edge, Wire]) -> Wire:

        if isinstance(p, Edge):
            rv = Wire.assembleEdges([p,])
        else:
            rv = p

        return rv

    @multimethod
    def sweep(
        cls,
        outerWire: Wire,
        innerWires: List[Wire],
        path: Union[Wire, Edge],
        makeSolid: bool = True,
        isFrenet: bool = False,
        mode: Union[Vector, Wire, Edge, None] = None,
        transitionMode: Literal["transformed", "round", "right"] = "transformed",
    ) -> "Shape":
        """
        Attempt to sweep the list of wires  into a prismatic solid along the provided path

        :param outerWire: the outermost wire
        :param innerWires: a list of inner wires
        :param path: The wire to sweep the face resulting from the wires over
        :param boolean makeSolid: return Solid or Shell (default True)
        :param boolean isFrenet: Frenet mode (default False)
        :param mode: additional sweep mode parameters.
        :param transitionMode:
            handling of profile orientation at C1 path discontinuities.
            Possible values are {'transformed','round', 'right'} (default: 'right').
        :return: a Solid object
        """
        p = cls._toWire(path)

        shapes = []
        for w in [outerWire] + innerWires:
            builder = BRepOffsetAPI_MakePipeShell(p.wrapped)

            translate = False
            rotate = False

            # handle sweep mode
            if mode:
                rotate = cls._setSweepMode(builder, path, mode)
            else:
                builder.SetMode(isFrenet)

            builder.SetTransitionMode(cls._transModeDict[transitionMode])

            builder.Add(w.wrapped, translate, rotate)

            builder.Build()
            if makeSolid:
                builder.MakeSolid()

            shapes.append(Shape.cast(builder.Shape()))

        rv, inner_shapes = shapes[0], shapes[1:]

        if inner_shapes:
            rv = rv.cut(*inner_shapes)

        return rv

    @classmethod
    @sweep.register
    def sweep(
        cls,
        face: Face,
        path: Union[Wire, Edge],
        makeSolid: bool = True,
        isFrenet: bool = False,
        mode: Union[Vector, Wire, Edge, None] = None,
        transitionMode: Literal["transformed", "round", "right"] = "transformed",
    ) -> "Shape":

        return cls.sweep(
            face.outerWire(),
            face.innerWires(),
            path,
            makeSolid,
            isFrenet,
            mode,
            transitionMode,
        )

    @classmethod
    def sweep_multi(
        cls,
        profiles: Iterable[Union[Wire, Face]],
        path: Union[Wire, Edge],
        makeSolid: bool = True,
        isFrenet: bool = False,
        mode: Union[Vector, Wire, Edge, None] = None,
    ) -> "Solid":
        """
        Multi section sweep. Only single outer profile per section is allowed.

        :param profiles: list of profiles
        :param path: The wire to sweep the face resulting from the wires over
        :param mode: additional sweep mode parameters.
        :return: a Solid object
        """
        if isinstance(path, Edge):
            w = Wire.assembleEdges([path,]).wrapped
        else:
            w = path.wrapped

        builder = BRepOffsetAPI_MakePipeShell(w)

        translate = False
        rotate = False

        if mode:
            rotate = cls._setSweepMode(builder, path, mode)
        else:
            builder.SetMode(isFrenet)

        for p in profiles:
            w = p.wrapped if isinstance(p, Wire) else p.outerWire().wrapped
            builder.Add(w, translate, rotate)

        builder.Build()

        if makeSolid:
            builder.MakeSolid()

        return cls(builder.Shape())


class CompSolid(Shape, Mixin3D):
    """
    a single compsolid
    """

    wrapped: TopoDS_CompSolid


class Compound(Shape, Mixin3D):
    """
    a collection of disconnected solids
    """

    wrapped: TopoDS_Compound

    @staticmethod
    def _makeCompound(listOfShapes: Iterable[TopoDS_Shape]) -> TopoDS_Compound:

        comp = TopoDS_Compound()
        comp_builder = TopoDS_Builder()
        comp_builder.MakeCompound(comp)

        for s in listOfShapes:
            comp_builder.Add(comp, s)

        return comp

    def remove(self, shape: Shape):
        """
        Remove the specified shape.
        """

        comp_builder = TopoDS_Builder()
        comp_builder.Remove(self.wrapped, shape.wrapped)

    @classmethod
    def makeCompound(cls, listOfShapes: Iterable[Shape]) -> "Compound":
        """
        Create a compound out of a list of shapes
        """

        return cls(cls._makeCompound((s.wrapped for s in listOfShapes)))

    @classmethod
    def makeText(
        cls,
        text: str,
        size: float,
        height: float,
        font: str = "Arial",
        fontPath: Optional[str] = None,
        kind: Literal["regular", "bold", "italic"] = "regular",
        halign: Literal["center", "left", "right"] = "center",
        valign: Literal["center", "top", "bottom"] = "center",
        position: Plane = Plane.XY(),
    ) -> "Shape":
        """
        Create a 3D text
        """

        font_kind = {
            "regular": Font_FA_Regular,
            "bold": Font_FA_Bold,
            "italic": Font_FA_Italic,
        }[kind]

        mgr = Font_FontMgr.GetInstance_s()

        if fontPath and mgr.CheckFont(TCollection_AsciiString(fontPath).ToCString()):
            font_t = Font_SystemFont(TCollection_AsciiString(fontPath))
            font_t.SetFontPath(font_kind, TCollection_AsciiString(fontPath))
            mgr.RegisterFont(font_t, True)

        else:
            font_t = mgr.FindFont(TCollection_AsciiString(font), font_kind)

        builder = Font_BRepTextBuilder()
        font_i = StdPrs_BRepFont(
            NCollection_Utf8String(font_t.FontName().ToCString()),
            font_kind,
            float(size),
        )
        text_flat = Shape(builder.Perform(font_i, NCollection_Utf8String(text)))

        bb = text_flat.BoundingBox()

        t = Vector()

        if halign == "center":
            t.x = -bb.xlen / 2
        elif halign == "right":
            t.x = -bb.xlen

        if valign == "center":
            t.y = -bb.ylen / 2
        elif valign == "top":
            t.y = -bb.ylen

        text_flat = text_flat.translate(t)

        vecNormal = text_flat.Faces()[0].normalAt() * height

        text_3d = BRepPrimAPI_MakePrism(text_flat.wrapped, vecNormal.wrapped)

        return cls(text_3d.Shape()).transformShape(position.rG)

    def __iter__(self) -> Iterator[Shape]:
        """
        Iterate over subshapes.

        """

        it = TopoDS_Iterator(self.wrapped)

        while it.More():
            yield Shape.cast(it.Value())
            it.Next()

    def __bool__(self) -> bool:
        """
        Check if empty.
        """

        return TopoDS_Iterator(self.wrapped).More()

    def cut(self, *toCut: Shape) -> "Compound":
        """
        Remove a shape from another one
        """

        cut_op = BRepAlgoAPI_Cut()

        return tcast(Compound, self._bool_op(self, toCut, cut_op))

    def fuse(
        self, *toFuse: Shape, glue: bool = False, tol: Optional[float] = None
    ) -> "Compound":
        """
        Fuse shapes together
        """

        fuse_op = BRepAlgoAPI_Fuse()
        if glue:
            fuse_op.SetGlue(BOPAlgo_GlueEnum.BOPAlgo_GlueShift)
        if tol:
            fuse_op.SetFuzzyValue(tol)

        args = tuple(self) + toFuse

        if len(args) <= 1:
            rv: Shape = args[0]
        else:
            rv = self._bool_op(args[:1], args[1:], fuse_op)

        # fuse_op.RefineEdges()
        # fuse_op.FuseEdges()

        return tcast(Compound, rv)

    def intersect(self, *toIntersect: Shape) -> "Compound":
        """
        Construct shape intersection
        """

        intersect_op = BRepAlgoAPI_Common()

        return tcast(Compound, self._bool_op(self, toIntersect, intersect_op))


def sortWiresByBuildOrder(wireList: List[Wire]) -> List[List[Wire]]:
    """Tries to determine how wires should be combined into faces.

    Assume:
        The wires make up one or more faces, which could have 'holes'
        Outer wires are listed ahead of inner wires
        there are no wires inside wires inside wires
        ( IE, islands -- we can deal with that later on )
        none of the wires are construction wires

    Compute:
        one or more sets of wires, with the outer wire listed first, and inner
        ones

    Returns, list of lists.
    """

    # check if we have something to sort at all
    if len(wireList) < 2:
        return [
            wireList,
        ]

    # make a Face, NB: this might return a compound of faces
    faces = Face.makeFromWires(wireList[0], wireList[1:])

    rv = []
    for face in faces.Faces():
        rv.append([face.outerWire(),] + face.innerWires())

    return rv


def wiresToFaces(wireList: List[Wire]) -> List[Face]:
    """
    Convert wires to a list of faces.
    """

    return Face.makeFromWires(wireList[0], wireList[1:]).Faces()


def edgesToWires(edges: Iterable[Edge], tol: float = 1e-6) -> List[Wire]:
    """
    Convert edges to a list of wires.
    """

    edges_in = TopTools_HSequenceOfShape()
    wires_out = TopTools_HSequenceOfShape()

    for e in edges:
        edges_in.Append(e.wrapped)
    ShapeAnalysis_FreeBounds.ConnectEdgesToWires_s(edges_in, tol, False, wires_out)

    return [Wire(el) for el in wires_out]
