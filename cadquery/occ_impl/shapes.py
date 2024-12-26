from typing import (
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
    Literal,
    Protocol,
)

from io import BytesIO

from vtkmodules.vtkCommonDataModel import vtkPolyData
from vtkmodules.vtkFiltersCore import vtkTriangleFilter, vtkPolyDataNormals

from .geom import Vector, VectorLike, BoundBox, Plane, Location, Matrix
from .shape_protocols import geom_LUT_FACE, geom_LUT_EDGE, Shapes, Geoms

from ..selectors import (
    Selector,
    StringSyntaxSelector,
)

from ..utils import multimethod

# change default OCCT logging level
from OCP.Message import Message, Message_Gravity

for printer in Message.DefaultMessenger_s().Printers():
    printer.SetTraceLevel(Message_Gravity.Message_Fail)

import OCP.TopAbs as ta  # Topology type enum
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
from OCP.TColgp import TColgp_HArray1OfPnt, TColgp_HArray2OfPnt, TColgp_Array1OfPnt

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

from OCP.TopExp import TopExp  # Topology explorer

# used for getting underlying geometry -- is this equivalent to brep adaptor?
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
    GeomAPI_ProjectPointOnCurve,
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
    BRepAlgoAPI_Check,
)

from OCP.Geom import (
    Geom_BezierCurve,
    Geom_ConicalSurface,
    Geom_CylindricalSurface,
    Geom_Surface,
    Geom_Plane,
    Geom_BSplineCurve,
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

from OCP.TopTools import (
    TopTools_IndexedDataMapOfShapeListOfShape,
    TopTools_ListOfShape,
    TopTools_MapOfShape,
    TopTools_IndexedMapOfShape,
)


from OCP.ShapeFix import ShapeFix_Shape, ShapeFix_Solid, ShapeFix_Face

from OCP.STEPControl import STEPControl_Writer, STEPControl_AsIs

from OCP.BRepMesh import BRepMesh_IncrementalMesh
from OCP.StlAPI import StlAPI_Writer

from OCP.ShapeUpgrade import ShapeUpgrade_UnifySameDomain

from OCP.BRepTools import BRepTools, BRepTools_WireExplorer

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
from OCP.Graphic3d import (
    Graphic3d_HTA_LEFT,
    Graphic3d_HTA_CENTER,
    Graphic3d_HTA_RIGHT,
    Graphic3d_VTA_BOTTOM,
    Graphic3d_VTA_CENTER,
    Graphic3d_VTA_TOP,
)

from OCP.NCollection import NCollection_Utf8String

from OCP.BRepFeat import BRepFeat_MakeDPrism

from OCP.BRepClass3d import BRepClass3d_SolidClassifier, BRepClass3d

from OCP.TCollection import TCollection_AsciiString

from OCP.TopLoc import TopLoc_Location

from OCP.GeomAbs import (
    GeomAbs_Shape,
    GeomAbs_C0,
    GeomAbs_G2,
    GeomAbs_C2,
    GeomAbs_Intersection,
    GeomAbs_JoinType,
    GeomAbs_IsoType,
    GeomAbs_CurveType,
)
from OCP.BRepOffsetAPI import BRepOffsetAPI_MakeFilling
from OCP.BRepOffset import BRepOffset_MakeOffset, BRepOffset_Mode

from OCP.BOPAlgo import BOPAlgo_GlueEnum

from OCP.IFSelect import IFSelect_ReturnStatus

from OCP.TopAbs import TopAbs_ShapeEnum, TopAbs_Orientation

from OCP.ShapeAnalysis import ShapeAnalysis_FreeBounds, ShapeAnalysis_Wire
from OCP.TopTools import TopTools_HSequenceOfShape

from OCP.GCPnts import (
    GCPnts_AbscissaPoint,
    GCPnts_QuasiUniformAbscissa,
    GCPnts_QuasiUniformDeflection,
)

from OCP.GeomFill import (
    GeomFill_Frenet,
    GeomFill_CorrectedFrenet,
    GeomFill_TrihedronLaw,
)

from OCP.BRepProj import BRepProj_Projection
from OCP.BRepExtrema import BRepExtrema_DistShapeShape

from OCP.IVtkOCC import IVtkOCC_Shape, IVtkOCC_ShapeMesher
from OCP.IVtkVTK import IVtkVTK_ShapeData

# for catching exceptions
from OCP.Standard import Standard_NoSuchObject, Standard_Failure

from OCP.Prs3d import Prs3d_IsoAspect
from OCP.Quantity import Quantity_Color
from OCP.Aspect import Aspect_TOL_SOLID

from OCP.Interface import Interface_Static

from OCP.ShapeCustom import ShapeCustom, ShapeCustom_RestrictionParameters

from OCP.BRepAlgo import BRepAlgo

from OCP.ChFi2d import ChFi2d_FilletAPI  # For Wire.Fillet()

from OCP.GeomConvert import GeomConvert_ApproxCurve

from OCP.Approx import Approx_ParametrizationType

from OCP.LProp3d import LProp3d_CLProps

from OCP.BinTools import BinTools

from OCP.Adaptor3d import Adaptor3d_IsoCurve, Adaptor3d_Curve

from OCP.GeomAdaptor import GeomAdaptor_Surface

from math import pi, sqrt, inf, radians, cos

import warnings

from ..utils import deprecate

Real = Union[float, int]

TOLERANCE = 1e-6
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

ancestors_LUT = {
    "Vertex": ta.TopAbs_EDGE,
    "Edge": ta.TopAbs_WIRE,
    "Wire": ta.TopAbs_FACE,
    "Face": ta.TopAbs_SHELL,
    "Shell": ta.TopAbs_SOLID,
}

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
        # NB downcast is needed to handle TopoDS_Shape types
        tr = constructor_LUT[t](downcast(obj))
        tr.forConstruction = forConstruction

        return tr

    def exportStl(
        self,
        fileName: str,
        tolerance: float = 1e-3,
        angularTolerance: float = 0.1,
        ascii: bool = False,
        relative: bool = True,
        parallel: bool = True,
    ) -> bool:
        """
        Exports a shape to a specified STL file.

        :param fileName: The path and file name to write the STL output to.
        :param tolerance: A linear deflection setting which limits the distance between a curve and its tessellation.
            Setting this value too low will result in large meshes that can consume computing resources.
            Setting the value too high can result in meshes with a level of detail that is too low.
            Default is 1e-3, which is a good starting point for a range of cases.
        :param angularTolerance: Angular deflection setting which limits the angle between subsequent segments in a polyline. Default is 0.1.
        :param ascii: Export the file as ASCII (True) or binary (False) STL format.  Default is binary.
        :param relative: If True, tolerance will be scaled by the size of the edge being meshed. Default is True.
            Setting this value to True may cause large features to become faceted, or small features dense.
        :param parallel: If True, OCCT will use parallel processing to mesh the shape. Default is True.
        """
        # The constructor used here automatically calls mesh.Perform(). https://dev.opencascade.org/doc/refman/html/class_b_rep_mesh___incremental_mesh.html#a3a383b3afe164161a3aa59a492180ac6
        BRepMesh_IncrementalMesh(
            self.wrapped, tolerance, relative, angularTolerance, parallel
        )

        writer = StlAPI_Writer()
        writer.ASCIIMode = ascii

        return writer.Write(self.wrapped, fileName)

    def exportStep(self, fileName: str, **kwargs) -> IFSelect_ReturnStatus:
        """
        Export this shape to a STEP file.

        kwargs is used to provide optional keyword arguments to configure the exporter.

        :param fileName: Path and filename for writing.
        :param write_pcurves: Enable or disable writing parametric curves to the STEP file. Default True.

            If False, writes STEP file without pcurves. This decreases the size of the resulting STEP file.
        :type write_pcurves: bool
        :param precision_mode: Controls the uncertainty value for STEP entities. Specify -1, 0, or 1. Default 0.
            See OCCT documentation.
        :type precision_mode: int
        """

        # Handle the extra settings for the STEP export
        pcurves = 1
        if "write_pcurves" in kwargs and not kwargs["write_pcurves"]:
            pcurves = 0
        precision_mode = kwargs["precision_mode"] if "precision_mode" in kwargs else 0

        writer = STEPControl_Writer()
        Interface_Static.SetIVal_s("write.surfacecurve.mode", pcurves)
        Interface_Static.SetIVal_s("write.precision.mode", precision_mode)
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

    def exportBin(self, f: Union[str, BytesIO]) -> bool:
        """
        Export this shape to a binary BREP file.
        """

        rv = BinTools.Write_s(self.wrapped, f)

        return True if rv is None else rv

    @classmethod
    def importBin(cls, f: Union[str, BytesIO]) -> "Shape":
        """
        Import shape from a binary BREP file.
        """
        s = TopoDS_Shape()

        BinTools.Read_s(s, f)

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
        | Edge:   LINE, CIRCLE, ELLIPSE, HYPERBOLA, PARABOLA, BEZIER,
        |         BSPLINE, OFFSET, OTHER
        | Face:   PLANE, CYLINDER, CONE, SPHERE, TORUS, BEZIER, BSPLINE,
        |         REVOLUTION, EXTRUSION, OFFSET, OTHER
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

        :param tolerance: Tolerance value passed to :class:`BoundBox`
        :returns: A :class:`BoundBox` object for this Shape
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

    @staticmethod
    def matrixOfInertia(obj: "Shape") -> List[List[float]]:
        """
        Calculates the matrix of inertia of an object.
        Since the part's density is unknown, this result is inertia/density with units of [1/length].
        :param obj: Compute the matrix of inertia of this object
        """
        Properties = GProp_GProps()
        calc_function = shape_properties_LUT[shapetype(obj.wrapped)]

        if calc_function:
            calc_function(obj.wrapped, Properties)
            moi = Properties.MatrixOfInertia()
            return [[moi.Value(i, j) for j in range(1, 4)] for i in range(1, 4)]

        raise NotImplementedError

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

    def _entities(self, topo_type: Shapes) -> Iterable[TopoDS_Shape]:

        shape_set = TopTools_IndexedMapOfShape()
        TopExp.MapShapes_s(self.wrapped, inverse_shape_LUT[topo_type], shape_set)

        return tcast(Iterable[TopoDS_Shape], shape_set)

    def _entitiesFrom(
        self, child_type: Shapes, parent_type: Shapes
    ) -> Dict["Shape", List["Shape"]]:

        res = TopTools_IndexedDataMapOfShapeListOfShape()

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

    def _filter(
        self, selector: Optional[Union[Selector, str]], objs: Iterable["Shape"]
    ) -> "Shape":

        selectorObj: Selector
        if selector:
            if isinstance(selector, str):
                selectorObj = StringSyntaxSelector(selector)
            else:
                selectorObj = selector
            selected = selectorObj.filter(list(objs))
        else:
            selected = list(objs)

        if len(selected) == 1:
            rv = selected[0]
        else:
            rv = Compound.makeCompound(selected)

        return rv

    def vertices(self, selector: Optional[Union[Selector, str]] = None) -> "Shape":
        """
        Select vertices.
        """

        return self._filter(selector, map(Shape.cast, self._entities("Vertex")))

    def edges(self, selector: Optional[Union[Selector, str]] = None) -> "Shape":
        """
        Select edges.
        """

        return self._filter(selector, map(Shape.cast, self._entities("Edge")))

    def wires(self, selector: Optional[Union[Selector, str]] = None) -> "Shape":
        """
        Select wires.
        """

        return self._filter(selector, map(Shape.cast, self._entities("Wire")))

    def faces(self, selector: Optional[Union[Selector, str]] = None) -> "Shape":
        """
        Select faces.
        """

        return self._filter(selector, map(Shape.cast, self._entities("Face")))

    def shells(self, selector: Optional[Union[Selector, str]] = None) -> "Shape":
        """
        Select shells.
        """

        return self._filter(selector, map(Shape.cast, self._entities("Shell")))

    def solids(self, selector: Optional[Union[Selector, str]] = None) -> "Shape":
        """
        Select solids.
        """

        return self._filter(selector, map(Shape.cast, self._entities("Solid")))

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
        self: T, startVector: VectorLike, endVector: VectorLike, angleDegrees: float
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
            gp_Ax1(
                Vector(startVector).toPnt(),
                (Vector(endVector) - Vector(startVector)).toDir(),
            ),
            radians(angleDegrees),
        )

        return self._apply_transform(Tr)

    def translate(self: T, vector: VectorLike) -> T:
        """
        Translates this shape through a transformation.
        """

        T = gp_Trsf()
        T.SetTranslation(Vector(vector).wrapped)

        return self._apply_transform(T)

    def scale(self, factor: float) -> "Shape":
        """
        Scales this shape through a transformation.
        """

        T = gp_Trsf()
        T.SetScale(gp_Pnt(), factor)

        return self._apply_transform(T)

    def copy(self: T, mesh: bool = False) -> T:
        """
        Creates a new object that is a copy of this object.

        :param mesh: should I copy the triangulation too (default: False)
        :returns: a copy of the object
        """

        return self.__class__(BRepBuilderAPI_Copy(self.wrapped, True, mesh).Shape())

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
        Apply a location in absolute sense to self.
        """

        self.wrapped.Location(loc.wrapped)

        return self

    def located(self: T, loc: Location) -> T:
        """
        Apply a location in absolute sense to a copy of self.
        """

        r = self.__class__(self.wrapped.Located(loc.wrapped))
        r.forConstruction = self.forConstruction

        return r

    @multimethod
    def move(self: T, loc: Location) -> T:
        """
        Apply a location in relative sense (i.e. update current location) to self.
        """

        self.wrapped.Move(loc.wrapped)

        return self

    @move.register
    def move(
        self: T,
        x: Real = 0,
        y: Real = 0,
        z: Real = 0,
        rx: Real = 0,
        ry: Real = 0,
        rz: Real = 0,
    ) -> T:
        """
        Apply translation and rotation in relative sense (i.e. update current location) to self.
        """

        self.wrapped.Move(Location(x, y, z, rx, ry, rz).wrapped)

        return self

    @move.register
    def move(self: T, loc: VectorLike) -> T:
        """
        Apply a VectorLike in relative sense (i.e. update current location) to self.
        """

        self.wrapped.Move(Location(loc).wrapped)

        return self

    @multimethod
    def moved(self: T, loc: Location) -> T:
        """
        Apply a location in relative sense (i.e. update current location) to a copy of self.
        """

        r = self.__class__(self.wrapped.Moved(loc.wrapped))
        r.forConstruction = self.forConstruction

        return r

    @moved.register
    def moved(self: T, loc1: Location, loc2: Location, *locs: Location) -> T:
        """
        Apply multiple locations.
        """

        return self.moved((loc1, loc2) + locs)

    @moved.register
    def moved(self: T, locs: Sequence[Location]) -> T:
        """
        Apply multiple locations.
        """

        rv = []

        for l in locs:
            rv.append(self.wrapped.Moved(l.wrapped))

        return _compound_or_shape(rv)

    @moved.register
    def moved(
        self: T,
        x: Real = 0,
        y: Real = 0,
        z: Real = 0,
        rx: Real = 0,
        ry: Real = 0,
        rz: Real = 0,
    ) -> T:
        """
        Apply translation and rotation in relative sense to a copy of self.
        """

        return self.moved(Location(x, y, z, rx, ry, rz))

    @moved.register
    def moved(self: T, loc: VectorLike) -> T:
        """
        Apply a VectorLike in relative sense to a copy of self.
        """

        return self.moved(Location(loc))

    @moved.register
    def moved(self: T, loc1: VectorLike, loc2: VectorLike, *locs: VectorLike) -> T:
        """
        Apply multiple VectorLikes in relative sense to a copy of self.
        """

        return self.moved(
            (Location(loc1), Location(loc2)) + tuple(Location(loc) for loc in locs)
        )

    @moved.register
    def moved(self: T, loc: Sequence[VectorLike]) -> T:
        """
        Apply multiple VectorLikes in relative sense to a copy of self.
        """

        return self.moved(tuple(Location(l) for l in loc))

    def __hash__(self) -> int:

        return self.hashCode()

    def __eq__(self, other) -> bool:

        return self.isSame(other) if isinstance(other, Shape) else False

    def _bool_op(
        self,
        args: Iterable["Shape"],
        tools: Iterable["Shape"],
        op: Union[BRepAlgoAPI_BooleanOperation, BRepAlgoAPI_Splitter],
        parallel: bool = True,
    ) -> "Shape":
        """
        Generic boolean operation

        :param parallel: Sets the SetRunParallel flag, which enables parallel execution of boolean operations in OCC kernel
        """

        arg = TopTools_ListOfShape()
        for obj in args:
            arg.Append(obj.wrapped)

        tool = TopTools_ListOfShape()
        for obj in tools:
            tool.Append(obj.wrapped)

        op.SetArguments(arg)
        op.SetTools(tool)

        op.SetRunParallel(parallel)
        op.Build()

        return Shape.cast(op.Shape())

    def cut(self, *toCut: "Shape", tol: Optional[float] = None) -> "Shape":
        """
        Remove the positional arguments from this Shape.

        :param tol: Fuzzy mode tolerance
        """

        cut_op = BRepAlgoAPI_Cut()

        if tol:
            cut_op.SetFuzzyValue(tol)

        return self._bool_op((self,), toCut, cut_op)

    def fuse(
        self, *toFuse: "Shape", glue: bool = False, tol: Optional[float] = None
    ) -> "Shape":
        """
        Fuse the positional arguments with this Shape.

        :param glue: Sets the glue option for the algorithm, which allows
            increasing performance of the intersection of the input shapes
        :param tol: Fuzzy mode tolerance
        """

        fuse_op = BRepAlgoAPI_Fuse()
        if glue:
            fuse_op.SetGlue(BOPAlgo_GlueEnum.BOPAlgo_GlueShift)
        if tol:
            fuse_op.SetFuzzyValue(tol)

        rv = self._bool_op((self,), toFuse, fuse_op)

        return rv

    def intersect(self, *toIntersect: "Shape", tol: Optional[float] = None) -> "Shape":
        """
        Intersection of the positional arguments and this Shape.

        :param tol: Fuzzy mode tolerance
        """

        intersect_op = BRepAlgoAPI_Common()

        if tol:
            intersect_op.SetFuzzyValue(tol)

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

        :param point: Base point for defining a line
        :param axis: Axis on which the line rests
        :param tol: Intersection tolerance
        :param direction: Valid values: "AlongAxis", "Opposite";
            If specified, will ignore all faces that are not in the specified direction
            including the face where the point lies if it is the case
        :returns: A list of intersected faces sorted by distance from point
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

    def distance(self, other: "Shape") -> float:
        """
        Minimal distance between two shapes
        """

        return BRepExtrema_DistShapeShape(self.wrapped, other.wrapped).Value()

    def distances(self, *others: "Shape") -> Iterator[float]:
        """
        Minimal distances to between self and other shapes
        """

        dist_calc = BRepExtrema_DistShapeShape()
        dist_calc.LoadS1(self.wrapped)

        for s in others:
            dist_calc.LoadS2(s.wrapped)
            dist_calc.Perform()

            yield dist_calc.Value()

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
            if poly is None:
                continue
            Trsf = loc.Transformation()
            reverse = (
                True
                if f.wrapped.Orientation() == TopAbs_Orientation.TopAbs_REVERSED
                else False
            )

            # add vertices
            vertices += [
                Vector(v.X(), v.Y(), v.Z())
                for v in (
                    poly.Node(i).Transformed(Trsf) for i in range(1, poly.NbNodes() + 1)
                )
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

    def toSplines(
        self: T, degree: int = 3, tolerance: float = 1e-3, nurbs: bool = False
    ) -> T:
        """
        Approximate shape with b-splines of the specified degree.

        :param degree: Maximum degree.
        :param tolerance: Approximation tolerance.
        :param nurbs: Use rational splines.
        """

        params = ShapeCustom_RestrictionParameters()

        result = ShapeCustom.BSplineRestriction_s(
            self.wrapped,
            tolerance,  # 3D tolerance
            tolerance,  # 2D tolerance
            degree,
            1,  # dumy value, degree is leading
            ga.GeomAbs_C0,
            ga.GeomAbs_C0,
            True,  # set degree to be leading
            not nurbs,
            params,
        )

        return self.__class__(result)

    def toVtkPolyData(
        self,
        tolerance: Optional[float] = None,
        angularTolerance: Optional[float] = None,
        normals: bool = False,
    ) -> vtkPolyData:
        """
        Convert shape to vtkPolyData
        """

        vtk_shape = IVtkOCC_Shape(self.wrapped)
        shape_data = IVtkVTK_ShapeData()
        shape_mesher = IVtkOCC_ShapeMesher()

        drawer = vtk_shape.Attributes()
        drawer.SetUIsoAspect(Prs3d_IsoAspect(Quantity_Color(), Aspect_TOL_SOLID, 1, 0))
        drawer.SetVIsoAspect(Prs3d_IsoAspect(Quantity_Color(), Aspect_TOL_SOLID, 1, 0))

        if tolerance:
            drawer.SetDeviationCoefficient(tolerance)

        if angularTolerance:
            drawer.SetDeviationAngle(angularTolerance)

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

    def __iter__(self) -> Iterator["Shape"]:
        """
        Iterate over subshapes.

        """

        it = TopoDS_Iterator(self.wrapped)

        while it.More():
            yield Shape.cast(it.Value())
            it.Next()

    def ancestors(self, shape: "Shape", kind: Shapes) -> "Compound":
        """
        Iterate over ancestors, i.e. shapes of same kind within shape that contain self.

        """

        shape_map = TopTools_IndexedDataMapOfShapeListOfShape()

        TopExp.MapShapesAndAncestors_s(
            shape.wrapped, shapetype(self.wrapped), inverse_shape_LUT[kind], shape_map
        )

        return Compound.makeCompound(
            Shape.cast(s) for s in shape_map.FindFromKey(self.wrapped)
        )

    def siblings(self, shape: "Shape", kind: Shapes, level: int = 1) -> "Compound":
        """
        Iterate over siblings, i.e. shapes within shape that share subshapes of kind with self.

        """

        shape_map = TopTools_IndexedDataMapOfShapeListOfShape()
        TopExp.MapShapesAndAncestors_s(
            shape.wrapped, inverse_shape_LUT[kind], shapetype(self.wrapped), shape_map,
        )
        exclude = TopTools_MapOfShape()

        def _siblings(shapes, level):

            rv = set()

            for s in shapes:
                exclude.Add(s.wrapped)

            for s in shapes:

                rv.update(
                    Shape.cast(el)
                    for child in s._entities(kind)
                    for el in shape_map.FindFromKey(child)
                    if not exclude.Contains(el)
                )

            return rv if level == 1 else _siblings(rv, level - 1)

        return Compound.makeCompound(_siblings([self], level))

    def __add__(self, other: "Shape") -> "Shape":
        """
        Fuse self and other.
        """

        return fuse(self, other)

    def __sub__(self, other: "Shape") -> "Shape":
        """
        Subtract other from self.
        """

        return cut(self, other)

    def __mul__(self, other: "Shape") -> "Shape":
        """
        Intersect self and other.
        """

        return intersect(self, other)

    def __truediv__(self, other: "Shape") -> "Shape":
        """
        Split self with other.
        """

        return split(self, other)

    def export(
        self: T,
        fname: str,
        tolerance: float = 0.1,
        angularTolerance: float = 0.1,
        opt: Optional[Dict[str, Any]] = None,
    ):
        """
        Export Shape to file.
        """

        from .exporters import export  # imported here to prevent circular imports

        export(
            self, fname, tolerance=tolerance, angularTolerance=angularTolerance, opt=opt
        )


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
        Create a vertex
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


ParamMode = Literal["length", "parameter"]
FrameMode = Literal["frenet", "corrected"]


class Mixin1DProtocol(ShapeProtocol, Protocol):
    def _approxCurve(self) -> Geom_BSplineCurve:
        ...

    def _geomAdaptor(self) -> Union[BRepAdaptor_Curve, BRepAdaptor_CompCurve]:
        ...

    def _curve_and_param(
        self, d: float, mode: ParamMode
    ) -> Tuple[Union[BRepAdaptor_Curve, BRepAdaptor_CompCurve], float]:
        ...

    def paramAt(self, d: float) -> float:
        ...

    def positionAt(self, d: float, mode: ParamMode = "length",) -> Vector:
        ...

    def locationAt(
        self,
        d: float,
        mode: ParamMode = "length",
        frame: FrameMode = "frenet",
        planar: bool = False,
    ) -> Location:
        ...

    def curvatureAt(
        self, d: float, mode: ParamMode = "length", resolution: float = 1e-6,
    ) -> float:
        ...


T1D = TypeVar("T1D", bound=Mixin1DProtocol)


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

    def _approxCurve(self: Mixin1DProtocol) -> Geom_BSplineCurve:
        """
        Approximate curve adaptor into a real b-spline. Meant for handling of
        BRepAdaptor_CompCurve.
        """

        rv = GeomConvert_ApproxCurve(
            self._geomAdaptor(), TOLERANCE, GeomAbs_C2, MaxSegments=100, MaxDegree=3
        ).Curve()

        return rv

    def paramAt(self: Mixin1DProtocol, d: Union[Real, Vector]) -> float:
        """
        Compute parameter value at the specified normalized distance or a point.

        :param d: normalized distance [0, 1] or a point
        :return: parameter value
        """

        curve = self._geomAdaptor()

        if isinstance(d, Vector):
            # handle comp curves (i.e. wire adaptors)
            if isinstance(curve, BRepAdaptor_Curve):
                curve_ = curve.Curve().Curve()  # get the underlying curve object
            else:
                curve_ = self._approxCurve()  # approximate the adaptor as a real curve

            rv = GeomAPI_ProjectPointOnCurve(
                d.toPnt(), curve_, curve.FirstParameter(), curve.LastParameter(),
            ).LowerDistanceParameter()

        else:
            l = GCPnts_AbscissaPoint.Length_s(curve)
            rv = GCPnts_AbscissaPoint(curve, l * d, curve.FirstParameter()).Parameter()

        return rv

    def tangentAt(
        self: Mixin1DProtocol, locationParam: float = 0.5, mode: ParamMode = "length",
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

    def _curve_and_param(
        self: Mixin1DProtocol, d: float, mode: ParamMode
    ) -> Tuple[Union[BRepAdaptor_Curve, BRepAdaptor_CompCurve], float]:
        """
        Helper that reurns the curve and u value
        """

        curve = self._geomAdaptor()

        if mode == "length":
            param = self.paramAt(d)
        else:
            param = d

        return curve, param

    def positionAt(
        self: Mixin1DProtocol, d: float, mode: ParamMode = "length",
    ) -> Vector:
        """
        Generate a position along the underlying curve.

        :param d: distance or parameter value
        :param mode: position calculation mode (default: length)
        :return: A Vector on the underlying curve located at the specified d value.
        """

        curve, param = self._curve_and_param(d, mode)

        return Vector(curve.Value(param))

    def positions(
        self: Mixin1DProtocol, ds: Iterable[float], mode: ParamMode = "length",
    ) -> List[Vector]:
        """
        Generate positions along the underlying curve.

        :param ds: distance or parameter values
        :param mode: position calculation mode (default: length)
        :return: A list of Vector objects.
        """

        return [self.positionAt(d, mode) for d in ds]

    def sample(
        self: Mixin1DProtocol, n: Union[int, float]
    ) -> Tuple[List[Vector], List[float]]:
        """
        Sample a curve based on a number of points or deflection.

        :param n: Number of positions or deflection
        :return: A list of Vectors and a list of parameters.
        """

        gcpnts: Union[GCPnts_QuasiUniformAbscissa, GCPnts_QuasiUniformDeflection]

        if isinstance(n, int):
            crv = self._geomAdaptor()
            gcpnts = GCPnts_QuasiUniformAbscissa(crv, n + 1 if crv.IsClosed() else n)
        else:
            crv = self._geomAdaptor()
            gcpnts = GCPnts_QuasiUniformDeflection(crv, n)

        N_pts = gcpnts.NbPoints()

        params = [
            gcpnts.Parameter(i)
            for i in range(1, N_pts if crv.IsClosed() else N_pts + 1)
        ]
        pnts = [Vector(crv.Value(p)) for p in params]

        return pnts, params

    def locationAt(
        self: Mixin1DProtocol,
        d: float,
        mode: ParamMode = "length",
        frame: FrameMode = "frenet",
        planar: bool = False,
    ) -> Location:
        """
        Generate a location along the underlying curve.

        :param d: distance or parameter value
        :param mode: position calculation mode (default: length)
        :param frame: moving frame calculation method (default: frenet)
        :param planar: planar mode
        :return: A Location object representing local coordinate system at the specified distance.
        """

        curve, param = self._curve_and_param(d, mode)

        law: GeomFill_TrihedronLaw
        if frame == "frenet":
            law = GeomFill_Frenet()
        else:
            law = GeomFill_CorrectedFrenet()

        law.SetCurve(curve)

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
        mode: ParamMode = "length",
        frame: FrameMode = "frenet",
        planar: bool = False,
    ) -> List[Location]:
        """
        Generate locations along the curve.

        :param ds: distance or parameter values
        :param mode: position calculation mode (default: length)
        :param frame: moving frame calculation method (default: frenet)
        :param planar: planar mode
        :return: A list of Location objects representing local coordinate systems at the specified distances.
        """

        return [self.locationAt(d, mode, frame, planar) for d in ds]

    def project(
        self: T1D, face: "Face", d: VectorLike, closest: bool = True
    ) -> Union[T1D, List[T1D]]:
        """
        Project onto a face along the specified direction
        """

        bldr = BRepProj_Projection(self.wrapped, face.wrapped, Vector(d).toDir())
        shapes = Compound(bldr.Shape())

        # select the closest projection if requested
        rv: Union[T1D, List[T1D]]

        if closest:

            dist_calc = BRepExtrema_DistShapeShape()
            dist_calc.LoadS1(self.wrapped)

            min_dist = inf

            for el in shapes:
                dist_calc.LoadS2(el.wrapped)
                dist_calc.Perform()
                dist = dist_calc.Value()

                if dist < min_dist:
                    min_dist = dist
                    rv = tcast(T1D, el)

        else:
            rv = [tcast(T1D, el) for el in shapes]

        return rv

    def curvatureAt(
        self: Mixin1DProtocol,
        d: float,
        mode: ParamMode = "length",
        resolution: float = 1e-6,
    ) -> float:
        """
        Calculate mean curvature along the underlying curve.

        :param d: distance or parameter value
        :param mode: position calculation mode (default: length)
        :param resolution: resolution of the calculation (default: 1e-6)
        :return: mean curvature value at the specified d value.
        """

        curve, param = self._curve_and_param(d, mode)

        props = LProp3d_CLProps(curve, param, 2, resolution)

        return props.Curvature()

    def curvatures(
        self: Mixin1DProtocol,
        ds: Iterable[float],
        mode: ParamMode = "length",
        resolution: float = 1e-6,
    ) -> List[float]:
        """
        Calculate mean curvatures along the underlying curve.

        :param d: distance or parameter values
        :param mode: position calculation mode (default: length)
        :param resolution: resolution of the calculation (default: 1e-6)
        :return: mean curvature value at the specified d value.
        """

        return [self.curvatureAt(d, mode, resolution) for d in ds]


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

    def trim(self, u0: Real, u1: Real) -> "Edge":
        """
        Trim the edge in the parametric space to (u0, u1).

        NB: this operation is done on the base geometry.
        """

        bldr = BRepBuilderAPI_MakeEdge(self._geomAdaptor().Curve().Curve(), u0, u1)

        return self.__class__(bldr.Shape())

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
                circle_gp, radians(angle1), radians(angle2), orientation
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
            correction_angle = radians(90.0)
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
                radians(angle1) - correction_angle,
                radians(angle2) - correction_angle,
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
    def makeThreePointArc(
        cls, v1: VectorLike, v2: VectorLike, v3: VectorLike
    ) -> "Edge":
        """
        Makes a three point arc through the provided points

        :param cls:
        :param v1: start vector
        :param v2: middle vector
        :param v3: end vector
        :return: an edge object through the three points
        """
        circle_geom = GC_MakeArcOfCircle(
            Vector(v1).toPnt(), Vector(v2).toPnt(), Vector(v3).toPnt()
        ).Value()

        return cls(BRepBuilderAPI_MakeEdge(circle_geom).Edge())

    @classmethod
    def makeTangentArc(cls, v1: VectorLike, v2: VectorLike, v3: VectorLike) -> "Edge":
        """
        Makes a tangent arc from point v1, in the direction of v2 and ends at v3.

        :param cls:
        :param v1: start vector
        :param v2: tangent vector
        :param v3: end vector
        :return: an edge
        """
        circle_geom = GC_MakeArcOfCircle(
            Vector(v1).toPnt(), Vector(v2).wrapped, Vector(v3).toPnt()
        ).Value()

        return cls(BRepBuilderAPI_MakeEdge(circle_geom).Edge())

    @classmethod
    def makeLine(cls, v1: VectorLike, v2: VectorLike) -> "Edge":
        """
        Create a line between two points

        :param v1: Vector that represents the first point
        :param v2: Vector that represents the second point
        :return: A linear edge between the two provided points
        """
        return cls(
            BRepBuilderAPI_MakeEdge(Vector(v1).toPnt(), Vector(v2).toPnt()).Edge()
        )

    @classmethod
    def makeBezier(cls, points: List[Vector]) -> "Edge":
        """
        Create a cubic Bézier Curve from the points.

        :param points: a list of Vectors that represent the points.
            The edge will pass through the first and the last point,
            and the inner points are Bézier control points.
        :return: An edge
        """

        # Convert to a TColgp_Array1OfPnt
        arr = TColgp_Array1OfPnt(1, len(points))
        for i, v in enumerate(points):
            arr.SetValue(i + 1, Vector(v).toPnt())

        bez = Geom_BezierCurve(arr)

        return cls(BRepBuilderAPI_MakeEdge(bez).Edge())


class Wire(Shape, Mixin1D):
    """
    A series of connected, ordered Edges, that typically bounds a Face
    """

    wrapped: TopoDS_Wire

    def _nbEdges(self) -> int:
        """
        Number of edges.
        """

        sa = ShapeAnalysis_Wire()
        sa.Load(self.wrapped)

        return sa.NbEdges()

    def _geomAdaptor(self) -> Union[BRepAdaptor_Curve, BRepAdaptor_CompCurve]:
        """
        Return the underlying geometry.
        """

        rv: Union[BRepAdaptor_Curve, BRepAdaptor_CompCurve]

        if self._nbEdges() == 1:
            rv = self.Edges()[-1]._geomAdaptor()
        else:
            rv = BRepAdaptor_CompCurve(self.wrapped)

        return rv

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

        BRepBuilderAPI_MakeWire::Error() values:

        * BRepBuilderAPI_WireDone = 0
        * BRepBuilderAPI_EmptyWire = 1
        * BRepBuilderAPI_DisconnectedWire = 2
        * BRepBuilderAPI_NonManifoldWire = 3
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
    def makeCircle(
        cls, radius: float, center: VectorLike, normal: VectorLike
    ) -> "Wire":
        """
        Makes a Circle centered at the provided point, having normal in the provided direction

        :param radius: floating point radius of the circle, must be > 0
        :param center: vector representing the center of the circle
        :param normal: vector representing the direction of the plane the circle should lie in
        """

        circle_edge = Edge.makeCircle(radius, center, normal)
        w = cls.assembleEdges([circle_edge])
        return w

    @classmethod
    def makeEllipse(
        cls,
        x_radius: float,
        y_radius: float,
        center: VectorLike,
        normal: VectorLike,
        xDir: VectorLike,
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
            w = w.rotate(center, Vector(center) + Vector(normal), rotation_angle)

        return w

    @classmethod
    def makePolygon(
        cls,
        listOfVertices: Iterable[VectorLike],
        forConstruction: bool = False,
        close: bool = False,
    ) -> "Wire":
        """
        Construct a polygonal wire from points.
        """

        wire_builder = BRepBuilderAPI_MakePolygon()

        for v in listOfVertices:
            wire_builder.Add(Vector(v).toPnt())

        if close:
            wire_builder.Close()

        w = cls(wire_builder.Wire())
        w.forConstruction = forConstruction

        return w

    @classmethod
    def makeHelix(
        cls,
        pitch: float,
        height: float,
        radius: float,
        center: VectorLike = Vector(0, 0, 0),
        dir: VectorLike = Vector(0, 0, 1),
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
                gp_Ax3(Vector(center).toPnt(), Vector(dir).toDir()), radius
            )
        else:
            geom_surf = Geom_ConicalSurface(
                gp_Ax3(Vector(center).toPnt(), Vector(dir).toDir()),
                radians(angle),
                radius,
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
        """Attempt to stitch wires"""

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

    def fillet(
        self, radius: float, vertices: Optional[Iterable[Vertex]] = None
    ) -> "Wire":
        """
        Apply 2D or 3D fillet to a wire

        :param radius: the radius of the fillet, must be > zero
        :param vertices: the vertices to delete (where the fillet will be applied).  By default
          all vertices are deleted except ends of open wires.
        :return: A wire with filleted corners
        """

        edges = list(self)
        all_vertices = self.Vertices()
        n_edges = len(edges)
        n_vertices = len(all_vertices)

        newEdges = []
        currentEdge = edges[0]

        verticesSet = set(vertices) if vertices else set()

        for i in range(n_edges):
            if i == n_edges - 1 and not self.IsClosed():
                break
            nextEdge = edges[(i + 1) % n_edges]

            # Create a plane that is spanned by currentEdge and nextEdge
            currentDir = currentEdge.tangentAt(1)
            nextDir = nextEdge.tangentAt(0)
            normalDir = currentDir.cross(nextDir)

            # Check conditions for skipping fillet:
            #  1. The edges are parallel
            #  2. The vertex is not in the vertices white list
            if normalDir.Length == 0 or (
                all_vertices[(i + 1) % n_vertices] not in verticesSet
                and bool(verticesSet)
            ):
                newEdges.append(currentEdge)
                currentEdge = nextEdge
                continue

            # Prepare for using ChFi2d_FilletAPI
            pointInPlane = currentEdge.Center().toPnt()
            cornerPlane = gp_Pln(pointInPlane, normalDir.toDir())

            filletMaker = ChFi2d_FilletAPI(
                currentEdge.wrapped, nextEdge.wrapped, cornerPlane
            )

            ok = filletMaker.Perform(radius)
            if not ok:
                raise ValueError(f"Failed fillet at vertex {i+1}!")

            # Get the result of the fillet operation
            thePoint = next(iter(nextEdge)).Center().toPnt()
            res_arc = filletMaker.Result(
                thePoint, currentEdge.wrapped, nextEdge.wrapped
            )

            newEdges.append(currentEdge)
            newEdges.append(Edge(res_arc))

            currentEdge = nextEdge

        # Add the last edge unless we are closed, since then
        # currentEdge is the first edge, which was already added
        # (and clipped)
        if not self.IsClosed():
            newEdges.append(currentEdge)

        return Wire.assembleEdges(newEdges)

    def Vertices(self) -> List[Vertex]:
        """
        Ordered list of vertices of the wire.
        """

        rv = []

        exp = BRepTools_WireExplorer(self.wrapped)
        rv.append(Vertex(exp.CurrentVertex()))

        while exp.More():
            exp.Next()
            rv.append(Vertex(exp.CurrentVertex()))

        # handle closed wires correclty
        if self.IsClosed():
            rv = rv[:-1]

        return rv

    def __iter__(self) -> Iterator[Edge]:
        """
        Iterate over edges in an ordered way.

        """

        exp = BRepTools_WireExplorer(self.wrapped)

        while exp.Current():
            yield Edge(exp.Current())
            exp.Next()


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

    @multimethod
    def normalAt(self, locationVector: Optional[VectorLike] = None) -> Vector:
        """
        Computes the normal vector at the desired location on the face.

        :returns: a vector representing the direction
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
            projector = GeomAPI_ProjectPointOnSurf(
                Vector(locationVector).toPnt(), surface
            )

            u, v = projector.LowerDistanceParameters()

        p = gp_Pnt()
        vn = gp_Vec()
        BRepGProp_Face(self.wrapped).Normal(u, v, p, vn)

        return Vector(vn).normalized()

    @normalAt.register
    def normalAt(self, u: Real, v: Real) -> Tuple[Vector, Vector]:
        """
        Computes the normal vector at the desired location in the u,v parameter space.

        :returns: a vector representing the normal direction and the position
        :param u: the u parametric location to compute the normal at.
        :param v: the v parametric location to compute the normal at.
        """

        p = gp_Pnt()
        vn = gp_Vec()
        BRepGProp_Face(self.wrapped).Normal(u, v, p, vn)

        return Vector(vn).normalized(), Vector(p)

    def normals(
        self, us: Iterable[Real], vs: Iterable[Real]
    ) -> Tuple[List[Vector], List[Vector]]:
        """
        Computes the normal vectors at the desired locations in the u,v parameter space.

        :returns: a tuple of list of vectors representing the normal directions and the positions
        :param us: the u parametric locations to compute the normal at.
        :param vs: the v parametric locations to compute the normal at.
        """

        rv_n = []
        rv_p = []

        p = gp_Pnt()
        vn = gp_Vec()
        BGP = BRepGProp_Face(self.wrapped)

        for u, v in zip(us, vs):
            BGP.Normal(u, v, p, vn)

            rv_n.append(Vector(vn).normalized())
            rv_p.append(Vector(p))

        return rv_n, rv_p

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
        edges: Iterable[Union[Edge, Wire]],
        constraints: Iterable[Union[Edge, Wire, VectorLike, gp_Pnt]],
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
        Returns a surface enclosed by a closed polygon defined by 'edges' and 'constraints'.

        :param edges: edges
        :type edges: list of edges or wires
        :param constraints: constraints
        :type constraints: list of points or edges
        :param continuity: OCC.Core.GeomAbs continuity condition
        :param degree: >=2
        :param nbPtsOnCur: number of points on curve >= 15
        :param nbIter: number of iterations >= 2
        :param anisotropy: bool Anisotropy
        :param tol2d: 2D tolerance >0
        :param tol3d: 3D tolerance >0
        :param tolAng: angular tolerance
        :param tolCurv: tolerance for curvature >0
        :param maxDeg: highest polynomial degree >= 2
        :param maxSegments: greatest number of segments >= 2
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

        # outer edges
        for el in edges:
            if isinstance(el, Edge):
                n_sided.Add(el.wrapped, continuity)
            else:
                for el_edge in el.Edges():
                    n_sided.Add(el_edge.wrapped, continuity)

        # (inner) constraints
        for c in constraints:
            if isinstance(c, gp_Pnt):
                n_sided.Add(c)
            elif isinstance(c, Vector):
                n_sided.Add(c.toPnt())
            elif isinstance(c, tuple):
                n_sided.Add(Vector(c).toPnt())
            elif isinstance(c, Edge):
                n_sided.Add(c.wrapped, GeomAbs_C0, False)
            elif isinstance(c, Wire):
                for e in c.Edges():
                    n_sided.Add(e.wrapped, GeomAbs_C0, False)
            else:
                raise ValueError(f"Invalid constraint {c}")

        # build, fix and return
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
        makeRuledSurface(Edge|Wire,Edge|Wire) -- Make a ruled surface
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

    def thicken(self, thickness: float) -> "Solid":
        """
        Return a thickened face
        """

        builder = BRepOffset_MakeOffset()

        builder.Initialize(
            self.wrapped,
            thickness,
            1.0e-6,
            BRepOffset_Mode.BRepOffset_Skin,
            False,
            False,
            GeomAbs_Intersection,
            True,
        )  # The last True is important to make a solid

        builder.MakeOffsetShape()

        return Solid(builder.Shape())

    @classmethod
    def constructOn(cls, f: "Face", outer: "Wire", *inner: "Wire") -> "Face":

        bldr = BRepBuilderAPI_MakeFace(f._geomAdaptor(), outer.wrapped)

        for w in inner:
            bldr.Add(TopoDS.Wire_s(w.wrapped))

        return cls(bldr.Face()).fix()

    def project(self, other: "Face", d: VectorLike) -> "Face":

        outer_p = tcast(Wire, self.outerWire().project(other, d))
        inner_p = (tcast(Wire, w.project(other, d)) for w in self.innerWires())

        return self.constructOn(other, outer_p, *inner_p)

    def toArcs(self, tolerance: float = 1e-3) -> "Face":
        """
        Approximate planar face with arcs and straight line segments.

        :param tolerance: Approximation tolerance.
        """

        return self.__class__(BRepAlgo.ConvertFace_s(self.wrapped, tolerance))

    def trim(self, u0: Real, u1: Real, v0: Real, v1: Real, tol: Real = 1e-6) -> "Face":
        """
        Trim the face in the parametric space to (u0, u1).

        NB: this operation is done on the base geometry.
        """

        bldr = BRepBuilderAPI_MakeFace(self._geomAdaptor(), u0, u1, v0, v1, tol)

        return self.__class__(bldr.Shape())

    def isoline(self, param: Real, direction: Literal["u", "v"] = "v") -> Edge:
        """
        Construct an isoline.
        """

        u1, u2, v1, v2 = self._uvBounds()

        if direction == "u":
            iso = GeomAbs_IsoType.GeomAbs_IsoU
            p1, p2 = v1, v2
        else:
            iso = GeomAbs_IsoType.GeomAbs_IsoV
            p1, p2 = u1, u2

        adaptor = Adaptor3d_IsoCurve(
            GeomAdaptor_Surface(self._geomAdaptor()), iso, param
        )

        return Edge(_adaptor_curve_to_edge(adaptor, p1, p2))

    def isolines(
        self, params: Iterable[Real], direction: Literal["u", "v"] = "v"
    ) -> List[Edge]:
        """
        Construct multiple isolines.
        """

        return [self.isoline(p, direction) for p in params]


class Shell(Shape):
    """
    the outer boundary of a surface
    """

    wrapped: TopoDS_Shell

    @classmethod
    def makeShell(cls, listOfFaces: Iterable[Face]) -> "Shell":
        """
        Makes a shell from faces.
        """

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
                radians(taper),
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
    @deprecate()
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
        Returns a plate surface that is 'thickness' thick, enclosed by 'surf_edge_pts' points, and going through 'surf_pts' points.

        :param surf_edges:
            list of [x,y,z] float ordered coordinates
            or list of ordered or unordered wires
        :param surf_pts: list of [x,y,z] float coordinates (uses only edges if [])
        :param thickness: thickness may be negative or positive depending on direction, (returns 2D surface if 0)
        :param degree: >=2
        :param nbPtsOnCur: number of points on curve >= 15
        :param nbIter: number of iterations >= 2
        :param anisotropy: bool Anisotropy
        :param tol2d: 2D tolerance >0
        :param tol3d: 3D tolerance >0
        :param tolAng: angular tolerance
        :param tolCurv: tolerance for curvature >0
        :param maxDeg: highest polynomial degree >= 2
        :param maxSegments: greatest number of segments >= 2
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
            return face.thicken(thickness)

        else:  # Return 2D surface only
            return face

    @staticmethod
    def isSolid(obj: Shape) -> bool:
        """
        Returns true if the object is a solid, false otherwise
        """
        if hasattr(obj, "ShapeType"):
            if obj.ShapeType() == "Solid" or (
                obj.ShapeType() == "Compound" and len(obj.Solids()) > 0
            ):
                return True
        return False

    @classmethod
    def makeSolid(cls, shell: Shell) -> "Solid":
        """
        Makes a solid from a single shell.
        """

        return cls(ShapeFix_Solid().SolidFromShell(shell.wrapped))

    @classmethod
    def makeBox(
        cls,
        length: float,
        width: float,
        height: float,
        pnt: VectorLike = Vector(0, 0, 0),
        dir: VectorLike = Vector(0, 0, 1),
    ) -> "Solid":
        """
        makeBox(length,width,height,[pnt,dir]) -- Make a box located in pnt with the dimensions (length,width,height)
        By default pnt=Vector(0,0,0) and dir=Vector(0,0,1)
        """
        return cls(
            BRepPrimAPI_MakeBox(
                gp_Ax2(Vector(pnt).toPnt(), Vector(dir).toDir()), length, width, height
            ).Shape()
        )

    @classmethod
    def makeCone(
        cls,
        radius1: float,
        radius2: float,
        height: float,
        pnt: VectorLike = Vector(0, 0, 0),
        dir: VectorLike = Vector(0, 0, 1),
        angleDegrees: float = 360,
    ) -> "Solid":
        """
        Make a cone with given radii and height
        By default pnt=Vector(0,0,0),
        dir=Vector(0,0,1) and angle=360
        """
        return cls(
            BRepPrimAPI_MakeCone(
                gp_Ax2(Vector(pnt).toPnt(), Vector(dir).toDir()),
                radius1,
                radius2,
                height,
                radians(angleDegrees),
            ).Shape()
        )

    @classmethod
    def makeCylinder(
        cls,
        radius: float,
        height: float,
        pnt: VectorLike = Vector(0, 0, 0),
        dir: VectorLike = Vector(0, 0, 1),
        angleDegrees: float = 360,
    ) -> "Solid":
        """
        makeCylinder(radius,height,[pnt,dir,angle]) --
        Make a cylinder with a given radius and height
        By default pnt=Vector(0,0,0),dir=Vector(0,0,1) and angle=360
        """
        return cls(
            BRepPrimAPI_MakeCylinder(
                gp_Ax2(Vector(pnt).toPnt(), Vector(dir).toDir()),
                radius,
                height,
                radians(angleDegrees),
            ).Shape()
        )

    @classmethod
    def makeTorus(
        cls,
        radius1: float,
        radius2: float,
        pnt: VectorLike = Vector(0, 0, 0),
        dir: VectorLike = Vector(0, 0, 1),
        angleDegrees1: float = 0,
        angleDegrees2: float = 360,
    ) -> "Solid":
        """
        makeTorus(radius1,radius2,[pnt,dir,angle1,angle2,angle]) --
        Make a torus with a given radii and angles
        By default pnt=Vector(0,0,0),dir=Vector(0,0,1),angle1=0
        ,angle1=360 and angle=360
        """
        return cls(
            BRepPrimAPI_MakeTorus(
                gp_Ax2(Vector(pnt).toPnt(), Vector(dir).toDir()),
                radius1,
                radius2,
                radians(angleDegrees1),
                radians(angleDegrees2),
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
        pnt: VectorLike = Vector(0, 0, 0),
        dir: VectorLike = Vector(0, 0, 1),
    ) -> "Solid":
        """
        Make a wedge located in pnt
        By default pnt=Vector(0,0,0) and dir=Vector(0,0,1)
        """

        return cls(
            BRepPrimAPI_MakeWedge(
                gp_Ax2(Vector(pnt).toPnt(), Vector(dir).toDir()),
                dx,
                dy,
                dz,
                xmin,
                zmin,
                xmax,
                zmax,
            ).Solid()
        )

    @classmethod
    def makeSphere(
        cls,
        radius: float,
        pnt: VectorLike = Vector(0, 0, 0),
        dir: VectorLike = Vector(0, 0, 1),
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
                gp_Ax2(Vector(pnt).toPnt(), Vector(dir).toDir()),
                radius,
                radians(angleDegrees1),
                radians(angleDegrees2),
                radians(angleDegrees3),
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
        vecCenter: VectorLike,
        vecNormal: VectorLike,
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

        :param outerWire: the outermost wire
        :param innerWires: a list of inner wires
        :param vecCenter: the center point about which to rotate.  the axis of rotation is defined by
            vecNormal, located at vecCenter.
        :param vecNormal: a vector along which to extrude the wires
        :param angleDegrees: the angle to rotate through while extruding
        :return: a Solid object
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
        cls,
        face: Face,
        vecCenter: VectorLike,
        vecNormal: VectorLike,
        angleDegrees: Real,
    ) -> "Solid":

        return cls.extrudeLinearWithRotation(
            face.outerWire(), face.innerWires(), vecCenter, vecNormal, angleDegrees
        )

    @multimethod
    def extrudeLinear(
        cls,
        outerWire: Wire,
        innerWires: List[Wire],
        vecNormal: VectorLike,
        taper: Real = 0,
    ) -> "Solid":
        """
        Attempt to extrude the list of wires into a prismatic solid in the provided direction

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
    def extrudeLinear(
        cls, face: Face, vecNormal: VectorLike, taper: Real = 0,
    ) -> "Solid":

        if taper == 0:
            prism_builder: Any = BRepPrimAPI_MakePrism(
                face.wrapped, Vector(vecNormal).wrapped, True
            )
        else:
            faceNormal = face.normalAt()
            d = 1 if vecNormal.getAngle(faceNormal) < radians(90.0) else -1

            # Divided by cos of taper angle to ensure the height chosen by the user is respected
            prism_builder = LocOpe_DPrism(
                face.wrapped,
                (d * vecNormal.Length) / cos(radians(taper)),
                d * radians(taper),
            )

        return cls(prism_builder.Shape())

    @multimethod
    def revolve(
        cls,
        outerWire: Wire,
        innerWires: List[Wire],
        angleDegrees: Real,
        axisStart: VectorLike,
        axisEnd: VectorLike,
    ) -> "Solid":
        """
        Attempt to revolve the list of wires into a solid in the provided direction

        :param outerWire: the outermost wire
        :param innerWires: a list of inner wires
        :param angleDegrees: the angle to revolve through.
        :type angleDegrees: float, anything less than 360 degrees will leave the shape open
        :param axisStart: the start point of the axis of rotation
        :param axisEnd: the end point of the axis of rotation
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
        cls, face: Face, angleDegrees: Real, axisStart: VectorLike, axisEnd: VectorLike,
    ) -> "Solid":

        v1 = Vector(axisStart)
        v2 = Vector(axisEnd)
        v2 = v2 - v1
        revol_builder = BRepPrimAPI_MakeRevol(
            face.wrapped, gp_Ax1(v1.toPnt(), v2.toDir()), radians(angleDegrees), True
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
        Attempt to sweep the list of wires into a prismatic solid along the provided path

        :param outerWire: the outermost wire
        :param innerWires: a list of inner wires
        :param path: The wire to sweep the face resulting from the wires over
        :param makeSolid: return Solid or Shell (default True)
        :param isFrenet: Frenet mode (default False)
        :param mode: additional sweep mode parameters
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

    def outerShell(self) -> Shell:
        """
        Returns outer shell.
        """

        return Shell(BRepClass3d.OuterShell_s(self.wrapped))

    def innerShells(self) -> List[Shell]:
        """
        Returns inner shells.
        """

        outer = self.outerShell()

        return [s for s in self.Shells() if not s.isSame(outer)]


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
        if halign == "left":
            theHAlign = Graphic3d_HTA_LEFT
        elif halign == "center":
            theHAlign = Graphic3d_HTA_CENTER
        else:  # halign == "right"
            theHAlign = Graphic3d_HTA_RIGHT

        if valign == "bottom":
            theVAlign = Graphic3d_VTA_BOTTOM
        elif valign == "center":
            theVAlign = Graphic3d_VTA_CENTER
        else:  # valign == "top":
            theVAlign = Graphic3d_VTA_TOP

        text_flat = Shape(
            builder.Perform(
                font_i,
                NCollection_Utf8String(text),
                theHAlign=theHAlign,
                theVAlign=theVAlign,
            )
        )

        if height != 0:
            vecNormal = text_flat.Faces()[0].normalAt() * height

            text_3d = BRepPrimAPI_MakePrism(text_flat.wrapped, vecNormal.wrapped)
            rv = cls(text_3d.Shape()).transformShape(position.rG)
        else:
            rv = text_flat.transformShape(position.rG)

        return rv

    def __bool__(self) -> bool:
        """
        Check if empty.
        """

        return TopoDS_Iterator(self.wrapped).More()

    def cut(self, *toCut: "Shape", tol: Optional[float] = None) -> "Compound":
        """
        Remove the positional arguments from this Shape.

        :param tol: Fuzzy mode tolerance
        """

        cut_op = BRepAlgoAPI_Cut()

        if tol:
            cut_op.SetFuzzyValue(tol)

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

    def intersect(
        self, *toIntersect: "Shape", tol: Optional[float] = None
    ) -> "Compound":
        """
        Intersection of the positional arguments and this Shape.

        :param tol: Fuzzy mode tolerance
        """

        intersect_op = BRepAlgoAPI_Common()

        if tol:
            intersect_op.SetFuzzyValue(tol)

        return tcast(Compound, self._bool_op(self, toIntersect, intersect_op))

    def ancestors(self, shape: "Shape", kind: Shapes) -> "Compound":
        """
        Iterate over ancestors, i.e. shapes of same kind within shape that contain elements of self.

        """

        shape_map = TopTools_IndexedDataMapOfShapeListOfShape()
        shapetypes = set(shapetype(ch.wrapped) for ch in self)

        for t in shapetypes:
            TopExp.MapShapesAndAncestors_s(
                shape.wrapped, t, inverse_shape_LUT[kind], shape_map
            )

        return Compound.makeCompound(
            Shape.cast(a) for s in self for a in shape_map.FindFromKey(s.wrapped)
        )

    def siblings(self, shape: "Shape", kind: Shapes, level: int = 1) -> "Compound":
        """
        Iterate over siblings, i.e. shapes within shape that share subshapes of kind with the elements of self.

        """

        shape_map = TopTools_IndexedDataMapOfShapeListOfShape()
        shapetypes = set(shapetype(ch.wrapped) for ch in self)

        for t in shapetypes:
            TopExp.MapShapesAndAncestors_s(
                shape.wrapped, inverse_shape_LUT[kind], t, shape_map,
            )

        exclude = TopTools_MapOfShape()

        def _siblings(shapes, level):

            rv = set()

            for s in shapes:
                exclude.Add(s.wrapped)

            for s in shapes:
                rv.update(
                    Shape.cast(el)
                    for child in s._entities(kind)
                    for el in shape_map.FindFromKey(child)
                    if not exclude.Contains(el)
                )

            return rv if level == 1 else _siblings(rv, level - 1)

        return Compound.makeCompound(_siblings(self, level))


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


#%% utilities


def _get(s: Shape, ts: Union[Shapes, Tuple[Shapes, ...]]) -> Iterable[Shape]:
    """
    Get desired shapes or raise an error.
    """

    # convert input into tuple
    if isinstance(ts, tuple):
        types = ts
    else:
        types = (ts,)

    # validate the underlying shape, compounds are unpacked
    t = s.ShapeType()

    if t in types:
        yield s
    elif t == "Compound":
        for el in s:
            if el.ShapeType() in ts:
                yield el
            else:
                raise ValueError(
                    f"Required type(s): {types}; encountered {el.ShapeType()}"
                )
    else:
        raise ValueError(f"Required type(s): {types}; encountered {t}")


def _get_one(s: Shape, ts: Union[Shapes, Tuple[Shapes, ...]]) -> Shape:
    """
    Get one shape or raise an error.
    """

    # convert input into tuple
    if isinstance(ts, tuple):
        types = ts
    else:
        types = (ts,)

    # validate the underlying shape, compounds are unpacked
    t = s.ShapeType()

    if t in types:
        rv = s
    elif t == "Compound":
        for el in s:
            if el.ShapeType() in ts:
                rv = el
                break
            else:
                raise ValueError(
                    f"Required type(s): {types}, encountered {el.ShapeType()}"
                )
    else:
        raise ValueError(f"Required type(s): {types}; encountered {t}")

    return rv


def _get_one_wire(s: Shape) -> Wire:
    """
    Get one wire or edge and convert to wire.
    """

    rv = _get_one(s, ("Wire", "Edge"))

    if isinstance(rv, Wire):
        return rv
    else:
        return Wire.assembleEdges((rv,))


def _get_wires(s: Shape) -> Iterable[Shape]:
    """
    Get wires or wires from edges.
    """

    t = s.ShapeType()

    if t == "Wire":
        yield s
    elif t == "Edge":
        yield Wire.assembleEdges((tcast(Edge, s),))
    elif t == "Compound":
        for el in s:
            yield from _get_wires(el)
    else:
        raise ValueError(f"Required type(s): Edge, Wire; encountered {t}")


def _get_edges(s: Shape) -> Iterable[Shape]:
    """
    Get wires or wires from edges.
    """

    t = s.ShapeType()

    if t == "Edge":
        yield s
    elif t == "Wire":
        yield from _get_edges(s.edges())
    elif t == "Compound":
        for el in s:
            yield from _get_edges(el)
    else:
        raise ValueError(f"Required type(s): Edge, Wire; encountered {t}")


def _get_wire_lists(s: Sequence[Shape]) -> List[List[Union[Wire, Vertex]]]:
    """
    Get lists of wires for sweeping or lofting.
    """

    wire_lists: List[List[Union[Wire, Vertex]]] = []

    ix_last = len(s) - 1

    for i, el in enumerate(s):
        if i == 0:

            try:
                wire_lists = [[w] for w in _get_wires(el)]
            except ValueError:
                # if no wires were detected, try vertices
                wire_lists = [[v] for v in el.Vertices()]

            # if not faces and vertices were detected return an empty list
            if not wire_lists:
                break

        elif i == ix_last:

            try:
                for wire_list, w in zip(wire_lists, _get_wires(el)):
                    wire_list.append(w)
            except ValueError:
                for wire_list, v in zip(wire_lists, el.Vertices()):
                    wire_list.append(v)

        else:
            for wire_list, w in zip(wire_lists, _get_wires(el)):
                wire_list.append(w)

    return wire_lists


def _get_face_lists(s: Sequence[Shape]) -> List[List[Union[Face, Vertex]]]:
    """
    Get lists of faces for sweeping or lofting. First and last shape can be a vertex.
    """

    face_lists: List[List[Union[Face, Vertex]]] = []

    ix_last = len(s) - 1

    for i, el in enumerate(s):
        if i == 0:

            face_lists = [[f] for f in el.Faces()]

            # if no faces were detected, try vertices
            if not face_lists and not el.edges():
                face_lists = [[v] for v in el.Vertices()]

            # if not faces and vertices were detected return an empty list
            if not face_lists:
                break

        elif i == ix_last:

            # try to add faces
            faces = el.Faces()

            if len(faces) == len(face_lists):
                for face_list, f in zip(face_lists, faces):
                    face_list.append(f)
            else:
                for face_list, v in zip(face_lists, el.Vertices()):
                    face_list.append(v)

        else:
            for face_list, f in zip(face_lists, el.Faces()):
                face_list.append(f)

    # check if the result makes sense - needed in loft to switch to wire mode
    if any(
        isinstance(el[0], Vertex) and isinstance(el[1], Vertex) for el in face_lists
    ):
        return []

    return face_lists


def _normalize(s: Shape) -> Shape:
    """
    Apply some normalizations:
    - Shell with only one Face -> Face.
    - Compound with only one element -> element.
    """

    t = s.ShapeType()
    rv = s

    if t == "Shell":
        faces = s.Faces()
        if len(faces) == 1 and not BRep_Tool.IsClosed_s(s.wrapped):
            rv = faces[0]
    elif t == "Compound":
        objs = list(s)
        if len(objs) == 1:
            rv = objs[0]

    return rv


def _compound_or_shape(s: Union[TopoDS_Shape, List[TopoDS_Shape]]) -> Shape:
    """
    Convert a list of TopoDS_Shape to a Shape or a Compound.
    """

    if isinstance(s, TopoDS_Shape):
        rv = _normalize(Shape.cast(s))
    elif len(s) == 1:
        rv = _normalize(Shape.cast(s[0]))
    else:
        rv = Compound.makeCompound([_normalize(Shape.cast(el)) for el in s])

    return rv


def _pts_to_harray(pts: Sequence[VectorLike]) -> TColgp_HArray1OfPnt:
    """
    Convert a sequence of Vecotor to a TColgp harray (OCCT specific).
    """

    rv = TColgp_HArray1OfPnt(1, len(pts))

    for i, p in enumerate(pts):
        rv.SetValue(i + 1, Vector(p).toPnt())

    return rv


def _floats_to_harray(vals: Sequence[float]) -> TColStd_HArray1OfReal:
    """
    Convert a sequence of floats to a TColstd harray (OCCT specific).
    """

    rv = TColStd_HArray1OfReal(1, len(vals))

    for i, val in enumerate(vals):
        rv.SetValue(i + 1, val)

    return rv


def _shapes_to_toptools_list(s: Iterable[Shape]) -> TopTools_ListOfShape:
    """
    Convert an iterable of Shape to a TopTools list (OCCT specific).
    """

    rv = TopTools_ListOfShape()

    for el in s:
        rv.Append(el.wrapped)

    return rv


def _toptools_list_to_shapes(tl: TopTools_ListOfShape) -> List[Shape]:
    """
    Convert a TopTools list (OCCT specific) to a compound.
    """

    return [_normalize(Shape.cast(el)) for el in tl]


_geomabsshape_dict = dict(
    C0=GeomAbs_Shape.GeomAbs_C0,
    C1=GeomAbs_Shape.GeomAbs_C1,
    C2=GeomAbs_Shape.GeomAbs_C2,
    C3=GeomAbs_Shape.GeomAbs_C3,
    CN=GeomAbs_Shape.GeomAbs_CN,
    G1=GeomAbs_Shape.GeomAbs_G1,
    G2=GeomAbs_Shape.GeomAbs_G2,
)


def _to_geomabshape(name: str) -> GeomAbs_Shape:
    """
    Convert a literal to GeomAbs_Shape enum (OCCT specific).
    """

    return _geomabsshape_dict[name.upper()]


_parametrization_dict = dict(
    uniform=Approx_ParametrizationType.Approx_IsoParametric,
    chordal=Approx_ParametrizationType.Approx_ChordLength,
    centripetal=Approx_ParametrizationType.Approx_Centripetal,
)


def _to_parametrization(name: str) -> Approx_ParametrizationType:
    """
    Convert a literal to Approx_ParametrizationType enum (OCCT specific).
    """

    return _parametrization_dict[name.lower()]


def _adaptor_curve_to_edge(crv: Adaptor3d_Curve, p1: float, p2: float) -> TopoDS_Edge:

    GCT = GeomAbs_CurveType

    t = crv.GetType()

    if t == GCT.GeomAbs_BSplineCurve:
        bldr = BRepBuilderAPI_MakeEdge(crv.BSpline(), p1, p2)
    elif t == GCT.GeomAbs_BezierCurve:
        bldr = BRepBuilderAPI_MakeEdge(crv.Bezier(), p1, p2)
    elif t == GCT.GeomAbs_Circle:
        bldr = BRepBuilderAPI_MakeEdge(crv.Circle(), p1, p2)
    elif t == GCT.GeomAbs_Line:
        bldr = BRepBuilderAPI_MakeEdge(crv.Line(), p1, p2)
    elif t == GCT.GeomAbs_Ellipse:
        bldr = BRepBuilderAPI_MakeEdge(crv.Ellipse(), p1, p2)
    elif t == GCT.GeomAbs_Hyperbola:
        bldr = BRepBuilderAPI_MakeEdge(crv.Hyperbola(), p1, p2)
    elif t == GCT.GeomAbs_Parabola:
        bldr = BRepBuilderAPI_MakeEdge(crv.Parabola(), p1, p2)
    elif t == GCT.GeomAbs_OffsetCurve:
        bldr = BRepBuilderAPI_MakeEdge(crv.OffsetCurve(), p1, p2)
    else:
        raise ValueError(r"{t} is not a supported curve type")

    return bldr.Edge()


#%% alternative constructors


@multimethod
def wire(*s: Shape) -> Shape:
    """
    Build wire from edges.
    """

    builder = BRepBuilderAPI_MakeWire()

    edges = _shapes_to_toptools_list(e for el in s for e in _get_edges(el))
    builder.Add(edges)

    return _compound_or_shape(builder.Shape())


@wire.register
def wire(s: Sequence[Shape]) -> Shape:

    return wire(*s)


@multimethod
def face(*s: Shape) -> Shape:
    """
    Build face from edges or wires.
    """

    from OCP.BOPAlgo import BOPAlgo_Tools

    ws = Compound.makeCompound(w for el in s for w in _get_wires(el)).wrapped
    rv = TopoDS_Compound()

    status = BOPAlgo_Tools.WiresToFaces_s(ws, rv)

    if not status:
        raise ValueError("Face construction failed")

    return _get_one(_compound_or_shape(rv), "Face")


@face.register
def face(s: Sequence[Shape]) -> Shape:
    """
    Build face from a sequence of edges or wires.
    """

    return face(*s)


@multimethod
def shell(*s: Shape, tol: float = 1e-6) -> Shape:
    """
    Build shell from faces.
    """

    builder = BRepBuilderAPI_Sewing(tol)

    for el in s:
        for f in _get(el, "Face"):
            builder.Add(f.wrapped)

    builder.Perform()

    sewed = builder.SewedShape()

    # for one face sewing will not produce a shell
    if sewed.ShapeType() == TopAbs_ShapeEnum.TopAbs_FACE:
        rv = TopoDS_Shell()

        builder = TopoDS_Builder()
        builder.MakeShell(rv)
        builder.Add(rv, sewed)

    else:
        rv = sewed

    return _compound_or_shape(rv)


@shell.register
def shell(s: Sequence[Shape], tol: float = 1e-6) -> Shape:
    """
    Build shell from a sequence of faces.
    """

    return shell(*s, tol=tol)


@multimethod
def solid(s1: Shape, *sn: Shape, tol: float = 1e-6) -> Shape:
    """
    Build solid from faces or shells.
    """

    builder = ShapeFix_Solid()

    # get both Shells and Faces
    s = [s1, *sn]
    shells_faces = [f for el in s for f in _get(el, ("Shell", "Face"))]

    # if no shells are present, use faces to construct them
    shells = [el.wrapped for el in shells_faces if el.ShapeType() == "Shell"]
    if not shells:
        faces = [el for el in shells_faces]
        shells = [shell(*faces, tol=tol).wrapped]

    rvs = [builder.SolidFromShell(sh) for sh in shells]

    return _compound_or_shape(rvs)


@solid.register
def solid(
    s: Sequence[Shape], inner: Optional[Sequence[Shape]] = None, tol: float = 1e-6
) -> Shape:
    """
    Build solid from a sequence of faces.
    """

    builder = BRepBuilderAPI_MakeSolid()
    builder.Add(shell(*s, tol=tol).wrapped)

    if inner:
        for sh in _get(shell(*inner, tol=tol), "Shell"):
            builder.Add(sh.wrapped)

    # fix orientations
    sf = ShapeFix_Solid(builder.Solid())
    sf.Perform()

    return _compound_or_shape(sf.Solid())


@multimethod
def compound(*s: Shape) -> Shape:
    """
    Build compound from shapes.
    """

    rv = TopoDS_Compound()

    builder = TopoDS_Builder()
    builder.MakeCompound(rv)

    for el in s:
        builder.Add(rv, el.wrapped)

    return Compound(rv)


@compound.register
def compound(s: Sequence[Shape]) -> Shape:
    """
    Build compound from a sequence of shapes.
    """

    return compound(*s)


#%% primitives


@multimethod
def vertex(x: Real, y: Real, z: Real) -> Shape:
    """
    Construct a vertex from coordinates.
    """

    return _compound_or_shape(BRepBuilderAPI_MakeVertex(gp_Pnt(x, y, z)).Vertex())


@vertex.register
def vertex(p: VectorLike):
    """
    Construct a vertex from VectorLike.
    """

    return _compound_or_shape(BRepBuilderAPI_MakeVertex(Vector(p).toPnt()).Vertex())


def segment(p1: VectorLike, p2: VectorLike) -> Shape:
    """
    Construct a segment from two points.
    """

    return _compound_or_shape(
        BRepBuilderAPI_MakeEdge(Vector(p1).toPnt(), Vector(p2).toPnt()).Edge()
    )


def polyline(*pts: VectorLike) -> Shape:
    """
    Construct a polyline from points.
    """

    builder = BRepBuilderAPI_MakePolygon()

    for p in pts:
        builder.Add(Vector(p).toPnt())

    return _compound_or_shape(builder.Wire())


def polygon(*pts: VectorLike) -> Shape:
    """
    Construct a polygon (closed polyline) from points.
    """

    builder = BRepBuilderAPI_MakePolygon()

    for p in pts:
        builder.Add(Vector(p).toPnt())

    builder.Close()

    return _compound_or_shape(builder.Wire())


def rect(w: float, h: float) -> Shape:
    """
    Construct a rectangle.
    """

    return polygon(
        (-w / 2, -h / 2, 0), (w / 2, -h / 2, 0), (w / 2, h / 2, 0), (-w / 2, h / 2, 0)
    )


@multimethod
def spline(*pts: VectorLike, tol: float = 1e-6, periodic: bool = False) -> Shape:
    """
    Construct a spline from points.
    """

    data = _pts_to_harray(pts)

    builder = GeomAPI_Interpolate(data, periodic, tol)
    builder.Perform()

    return _compound_or_shape(BRepBuilderAPI_MakeEdge(builder.Curve()).Edge())


@spline.register
def spline(
    pts: Sequence[VectorLike],
    tgts: Optional[Sequence[VectorLike]] = None,
    params: Optional[Sequence[float]] = None,
    tol: float = 1e-6,
    periodic: bool = False,
    scale: bool = True,
) -> Shape:
    """
    Construct a spline from a sequence points.
    """

    data = _pts_to_harray(pts)

    if params is not None:
        args = (data, _floats_to_harray(params), periodic, tol)
    else:
        args = (data, periodic, tol)

    builder = GeomAPI_Interpolate(*args)

    if tgts is not None:
        builder.Load(Vector(tgts[0]).wrapped, Vector(tgts[1]).wrapped, scale)

    builder.Perform()

    return _compound_or_shape(BRepBuilderAPI_MakeEdge(builder.Curve()).Edge())


def circle(r: float) -> Shape:
    """
    Construct a circle.
    """

    return _compound_or_shape(
        BRepBuilderAPI_MakeEdge(
            gp_Circ(gp_Ax2(Vector().toPnt(), Vector(0, 0, 1).toDir()), r)
        ).Edge()
    )


def ellipse(r1: float, r2: float) -> Shape:
    """
    Construct an ellipse.
    """

    return _compound_or_shape(
        BRepBuilderAPI_MakeEdge(
            gp_Elips(gp_Ax2(Vector().toPnt(), Vector(0, 0, 1).toDir()), r1, r2)
        ).Edge()
    )


@multimethod
def plane(w: Real, l: Real) -> Shape:
    """
    Construct a finite planar face.
    """

    pln_geom = gp_Pln(Vector(0, 0, 0).toPnt(), Vector(0, 0, 1).toDir())

    return _compound_or_shape(
        BRepBuilderAPI_MakeFace(pln_geom, -w / 2, w / 2, -l / 2, l / 2).Face()
    )


@plane.register
def plane() -> Shape:
    """
    Construct an infinite planar face.

    This is a crude approximation. Truly infinite faces in OCCT do not work as
    expected in all contexts.
    """

    INF = 1e60

    pln_geom = gp_Pln(Vector(0, 0, 0).toPnt(), Vector(0, 0, 1).toDir())

    return _compound_or_shape(
        BRepBuilderAPI_MakeFace(pln_geom, -INF, INF, -INF, INF).Face()
    )


def box(w: float, l: float, h: float) -> Shape:
    """
    Construct a solid box.
    """

    return _compound_or_shape(
        BRepPrimAPI_MakeBox(
            gp_Ax2(Vector(-w / 2, -l / 2, 0).toPnt(), Vector(0, 0, 1).toDir()), w, l, h
        ).Shape()
    )


def cylinder(d: float, h: float) -> Shape:
    """
    Construct a solid cylinder.
    """

    return _compound_or_shape(
        BRepPrimAPI_MakeCylinder(
            gp_Ax2(Vector(0, 0, 0).toPnt(), Vector(0, 0, 1).toDir()), d / 2, h, 2 * pi
        ).Shape()
    )


def sphere(d: float) -> Shape:
    """
    Construct a solid sphere.
    """

    return _compound_or_shape(
        BRepPrimAPI_MakeSphere(
            gp_Ax2(Vector(0, 0, 0).toPnt(), Vector(0, 0, 1).toDir()), d / 2,
        ).Shape()
    )


def torus(d1: float, d2: float) -> Shape:
    """
    Construct a solid torus.
    """

    return _compound_or_shape(
        BRepPrimAPI_MakeTorus(
            gp_Ax2(Vector(0, 0, 0).toPnt(), Vector(0, 0, 1).toDir()),
            d1 / 2,
            d2 / 2,
            0,
            2 * pi,
        ).Shape()
    )


@multimethod
def cone(d1: Real, d2: Real, h: Real) -> Shape:
    """
    Construct a partial solid cone.
    """

    return _compound_or_shape(
        BRepPrimAPI_MakeCone(
            gp_Ax2(Vector(0, 0, 0).toPnt(), Vector(0, 0, 1).toDir()),
            d1 / 2,
            d2 / 2,
            h,
            2 * pi,
        ).Shape()
    )


@cone.register
def cone(d: Real, h: Real) -> Shape:
    """
    Construct a full solid cone.
    """

    return cone(d, 0, h)


@multimethod
def text(
    txt: str,
    size: Real,
    font: str = "Arial",
    path: Optional[str] = None,
    kind: Literal["regular", "bold", "italic"] = "regular",
    halign: Literal["center", "left", "right"] = "center",
    valign: Literal["center", "top", "bottom"] = "center",
) -> Shape:
    """
    Create a flat text.
    """

    builder = Font_BRepTextBuilder()

    font_kind = {
        "regular": Font_FA_Regular,
        "bold": Font_FA_Bold,
        "italic": Font_FA_Italic,
    }[kind]

    mgr = Font_FontMgr.GetInstance_s()

    if path and mgr.CheckFont(TCollection_AsciiString(path).ToCString()):
        font_t = Font_SystemFont(TCollection_AsciiString(path))
        font_t.SetFontPath(font_kind, TCollection_AsciiString(path))
        mgr.RegisterFont(font_t, True)

    else:
        font_t = mgr.FindFont(TCollection_AsciiString(font), font_kind)

    font_i = StdPrs_BRepFont(
        NCollection_Utf8String(font_t.FontName().ToCString()), font_kind, float(size),
    )

    if halign == "left":
        theHAlign = Graphic3d_HTA_LEFT
    elif halign == "center":
        theHAlign = Graphic3d_HTA_CENTER
    else:
        theHAlign = Graphic3d_HTA_RIGHT

    if valign == "bottom":
        theVAlign = Graphic3d_VTA_BOTTOM
    elif valign == "center":
        theVAlign = Graphic3d_VTA_CENTER
    else:
        theVAlign = Graphic3d_VTA_TOP

    rv = builder.Perform(
        font_i, NCollection_Utf8String(txt), theHAlign=theHAlign, theVAlign=theVAlign
    )

    return clean(compound(_compound_or_shape(rv).faces()).fuse())


@text.register
def text(
    txt: str,
    size: Real,
    spine: Shape,
    planar: bool = False,
    font: str = "Arial",
    path: Optional[str] = None,
    kind: Literal["regular", "bold", "italic"] = "regular",
    halign: Literal["center", "left", "right"] = "center",
    valign: Literal["center", "top", "bottom"] = "center",
) -> Shape:
    """
    Create a text on a spine.
    """

    spine = _get_one_wire(spine)
    L = spine.Length()

    rv = []
    for el in text(txt, size, font, path, kind, halign, valign):
        pos = el.BoundingBox().center.x

        # position
        rv.append(
            el.moved(-pos)
            .moved(rx=-90 if planar else 0, ry=-90)
            .moved(spine.locationAt(pos / L))
        )

    return _normalize(compound(rv))


@text.register
def text(
    txt: str,
    size: Real,
    spine: Shape,
    base: Shape,
    font: str = "Arial",
    path: Optional[str] = None,
    kind: Literal["regular", "bold", "italic"] = "regular",
    halign: Literal["center", "left", "right"] = "center",
    valign: Literal["center", "top", "bottom"] = "center",
) -> Shape:
    """
    Create a text on a spine and a base surface.
    """

    base = _get_one(base, "Face")

    tmp = text(txt, size, spine, False, font, path, kind, halign, valign)

    rv = []
    for f in tmp.faces():
        rv.append(f.project(base, f.normalAt()))

    return _normalize(compound(rv))


#%% ops


def _bool_op(
    s1: Shape,
    s2: Shape,
    builder: Union[BRepAlgoAPI_BooleanOperation, BRepAlgoAPI_Splitter],
    tol: float = 0.0,
    parallel: bool = True,
):

    arg = TopTools_ListOfShape()
    arg.Append(s1.wrapped)

    tool = TopTools_ListOfShape()
    tool.Append(s2.wrapped)

    builder.SetArguments(arg)
    builder.SetTools(tool)

    builder.SetRunParallel(parallel)
    builder.SetUseOBB(True)

    if tol:
        builder.SetFuzzyValue(tol)

    builder.Build()


def fuse(s1: Shape, s2: Shape, tol: float = 0.0) -> Shape:
    """
    Fuse two shapes.
    """

    builder = BRepAlgoAPI_Fuse()
    _bool_op(s1, s2, builder, tol)

    return _compound_or_shape(builder.Shape())


def cut(s1: Shape, s2: Shape, tol: float = 0.0) -> Shape:
    """
    Subtract two shapes.
    """

    builder = BRepAlgoAPI_Cut()
    _bool_op(s1, s2, builder, tol)

    return _compound_or_shape(builder.Shape())


def intersect(s1: Shape, s2: Shape, tol: float = 0.0) -> Shape:
    """
    Intersect two shapes.
    """

    builder = BRepAlgoAPI_Common()
    _bool_op(s1, s2, builder, tol)

    return _compound_or_shape(builder.Shape())


def split(s1: Shape, s2: Shape) -> Shape:
    """
    Split one shape with another.
    """

    builder = BRepAlgoAPI_Splitter()
    _bool_op(s1, s2, builder)

    return _compound_or_shape(builder.Shape())


def clean(s: Shape) -> Shape:
    """
    Clean superfluous edges and faces.
    """

    builder = ShapeUpgrade_UnifySameDomain(s.wrapped, True, True, True)
    builder.AllowInternalEdges(False)
    builder.Build()

    return _compound_or_shape(builder.Shape())


def fill(s: Shape, constraints: Sequence[Union[Shape, VectorLike]] = ()) -> Shape:
    """
    Fill edges/wire possibly obeying constraints.
    """

    builder = BRepOffsetAPI_MakeFilling()

    for e in _get_edges(s):
        builder.Add(e.wrapped, GeomAbs_C0)

    for c in constraints:
        if isinstance(c, Shape):
            for e in _get_edges(c):
                builder.Add(e.wrapped, GeomAbs_C0, False)
        else:
            builder.Add(Vector(c).toPnt())

    builder.Build()

    return _compound_or_shape(builder.Shape())


def cap(
    s: Shape, ctx: Shape, constraints: Sequence[Union[Shape, VectorLike]] = ()
) -> Shape:
    """
    Fill edges/wire possibly obeying constraints and try to connect smoothly to the context shape.
    """

    builder = BRepOffsetAPI_MakeFilling()
    builder.SetResolParam(2, 15, 5)

    for e in _get_edges(s):
        f = _get_one(e.ancestors(ctx, "Face"), "Face")
        builder.Add(e.wrapped, f.wrapped, GeomAbs_G2, True)

    for c in constraints:
        if isinstance(c, Shape):
            for e in _get_edges(c):
                builder.Add(e.wrapped, GeomAbs_C0, False)
        else:
            builder.Add(Vector(c).toPnt())

    builder.Build()

    return _compound_or_shape(builder.Shape())


def fillet(s: Shape, e: Shape, r: float) -> Shape:
    """
    Fillet selected edges in a given shell or solid.
    """

    builder = BRepFilletAPI_MakeFillet(_get_one(s, ("Shell", "Solid")).wrapped,)

    for el in _get_edges(e.edges()):
        builder.Add(r, el.wrapped)

    builder.Build()

    return _compound_or_shape(builder.Shape())


def chamfer(s: Shape, e: Shape, d: float) -> Shape:
    """
    Chamfer selected edges in a given shell or solid.
    """

    builder = BRepFilletAPI_MakeChamfer(_get_one(s, ("Shell", "Solid")).wrapped,)

    for el in _get_edges(e.edges()):
        builder.Add(d, el.wrapped)

    builder.Build()

    return _compound_or_shape(builder.Shape())


def extrude(s: Shape, d: VectorLike) -> Shape:
    """
    Extrude a shape.
    """

    results = []

    for el in _get(s, ("Vertex", "Edge", "Wire", "Face")):

        builder = BRepPrimAPI_MakePrism(el.wrapped, Vector(d).wrapped)
        builder.Build()

        results.append(builder.Shape())

    return _compound_or_shape(results)


def revolve(s: Shape, p: VectorLike, d: VectorLike, a: float = 360):
    """
    Revolve a shape.
    """

    results = []
    ax = gp_Ax1(Vector(p).toPnt(), Vector(d).toDir())

    for el in _get(s, ("Vertex", "Edge", "Wire", "Face")):

        builder = BRepPrimAPI_MakeRevol(el.wrapped, ax, radians(a))
        builder.Build()

        results.append(builder.Shape())

    return _compound_or_shape(results)


def offset(
    s: Shape, t: float, cap=True, both: bool = False, tol: float = 1e-6
) -> Shape:
    """
    Offset or thicken faces or shells.
    """

    def _offset(t):

        results = []

        for el in _get(s, ("Face", "Shell")):

            builder = BRepOffset_MakeOffset()

            builder.Initialize(
                el.wrapped,
                t,
                tol,
                BRepOffset_Mode.BRepOffset_Skin,
                False,
                False,
                GeomAbs_Intersection,
                cap,
            )

            builder.MakeOffsetShape()

            results.append(builder.Shape())

        return results

    if both:
        results_pos = _offset(t)
        results_neg = _offset(-t)

        results_both = [
            Shape(el1) + Shape(el2) for el1, el2 in zip(results_pos, results_neg)
        ]

        if len(results_both) == 1:
            rv = results_both[0]
        else:
            rv = Compound.makeCompound(results_both)

    else:
        results = _offset(t)
        rv = _compound_or_shape(results)

    return rv


@multimethod
def sweep(
    s: Shape, path: Shape, aux: Optional[Shape] = None, cap: bool = False
) -> Shape:
    """
    Sweep edge, wire or face along a path. For faces cap has no effect.
    Do not mix faces with other types.
    """

    spine = _get_one_wire(path)

    results = []

    def _make_builder():

        rv = BRepOffsetAPI_MakePipeShell(spine.wrapped)
        if aux:
            rv.SetMode(_get_one_wire(aux).wrapped, True)
        else:
            rv.SetMode(False)

        return rv

    # try to get faces
    faces = s.Faces()

    # if faces were supplied
    if faces:
        for f in faces:
            tmp = sweep(f.outerWire(), path, aux, True)

            # if needed subtract two sweeps
            inner_wires = f.innerWires()
            if inner_wires:
                tmp -= sweep(compound(inner_wires), path, aux, True)

            results.append(tmp.wrapped)

    # otherwise sweep wires
    else:
        for w in _get_wires(s):
            builder = _make_builder()

            builder.Add(w.wrapped, False, False)
            builder.Build()

            if cap:
                builder.MakeSolid()

            results.append(builder.Shape())

    return _compound_or_shape(results)


@sweep.register
def sweep(
    s: Sequence[Shape], path: Shape, aux: Optional[Shape] = None, cap: bool = False
) -> Shape:
    """
    Sweep edges, wires or faces along a path, multiple sections are supported.
    For faces cap has no effect. Do not mix faces with other types.
    """

    spine = _get_one_wire(path)

    results = []

    def _make_builder():

        rv = BRepOffsetAPI_MakePipeShell(spine.wrapped)
        if aux:
            rv.SetMode(_get_one_wire(aux).wrapped, True)
        else:
            rv.SetMode(False)

        return rv

    # try to construct sweeps using faces
    for el in _get_face_lists(s):
        # build outer part
        builder = _make_builder()

        for f in el:
            builder.Add(f.outerWire().wrapped, False, False)

        builder.Build()
        builder.MakeSolid()

        # build inner parts
        builders_inner = []

        # initialize builders
        for w in el[0].innerWires():
            builder_inner = _make_builder()
            builder_inner.Add(w.wrapped, False, False)
            builders_inner.append(builder_inner)

        # add remaining sections
        for f in el[1:]:
            for builder_inner, w in zip(builders_inner, f.innerWires()):
                builder_inner.Add(w.wrapped, False, False)

        # actually build
        inner_parts = []

        for builder_inner in builders_inner:
            builder_inner.Build()
            builder_inner.MakeSolid()
            inner_parts.append(Shape(builder_inner.Shape()))

        results.append((Shape(builder.Shape()) - compound(inner_parts)).wrapped)

    # if no faces were provided try with wires
    if not results:
        # construct sweeps
        for el in _get_wire_lists(s):
            builder = _make_builder()

            for w in el:
                builder.Add(w.wrapped, False, False)

            builder.Build()

            if cap:
                builder.MakeSolid()

            results.append(builder.Shape())

    return _compound_or_shape(results)


@multimethod
def loft(
    s: Sequence[Shape],
    cap: bool = False,
    ruled: bool = False,
    continuity: Literal["C1", "C2", "C3"] = "C2",
    parametrization: Literal["uniform", "chordal", "centripetal"] = "uniform",
    degree: int = 3,
    compat: bool = True,
    smoothing: bool = False,
    weights: Tuple[float, float, float] = (1, 1, 1),
) -> Shape:
    """
    Loft edges, wires or faces. For faces cap has no effect. Do not mix faces with other types.
    """

    results = []

    def _make_builder(cap):
        rv = BRepOffsetAPI_ThruSections(cap, ruled)
        rv.SetMaxDegree(degree)
        rv.CheckCompatibility(compat)
        rv.SetContinuity(_to_geomabshape(continuity))
        rv.SetParType(_to_parametrization(parametrization))
        rv.SetSmoothing(smoothing)
        rv.SetCriteriumWeight(*weights)

        return rv

    # try to construct lofts using faces
    for el in _get_face_lists(s):
        # build outer part
        builder = _make_builder(True)

        # used to check if building inner parts makes sense
        has_vertex = False

        for f in el:
            if isinstance(f, Face):
                builder.AddWire(f.outerWire().wrapped)
            else:
                builder.AddVertex(f.wrapped)
                has_vertex = True

        builder.Build()
        builder.Check()

        builders_inner = []

        # only initialize inner builders if no vertex was encountered
        if not has_vertex:
            # initialize builders
            for w in el[0].innerWires():
                builder_inner = _make_builder(True)

                builder_inner.AddWire(w.wrapped)
                builders_inner.append(builder_inner)

            # add remaining sections
            for f in el[1:]:
                for builder_inner, w in zip(builders_inner, f.innerWires()):
                    builder_inner.AddWire(w.wrapped)

        # actually build
        inner_parts = []

        for builder_inner in builders_inner:
            builder_inner.Build()
            builder_inner.Check()
            inner_parts.append(Shape(builder_inner.Shape()))

        results.append((Shape(builder.Shape()) - compound(inner_parts)).wrapped)

    # otherwise construct using wires
    if not results:
        for el in _get_wire_lists(s):
            builder = _make_builder(cap)

            for w in el:
                if isinstance(w, Wire):
                    builder.AddWire(w.wrapped)
                else:
                    builder.AddVertex(w.wrapped)

            builder.Build()
            builder.Check()

            results.append(builder.Shape())

    return _compound_or_shape(results)


@loft.register
def loft(
    *s: Shape,
    cap: bool = False,
    ruled: bool = False,
    continuity: Literal["C1", "C2", "C3"] = "C2",
    parametrization: Literal["uniform", "chordal", "centripetal"] = "uniform",
    degree: int = 3,
    compat: bool = True,
    smoothing: bool = False,
    weights: Tuple[float, float, float] = (1, 1, 1),
) -> Shape:
    """
    Variadic loft overload.
    """

    return loft(s, cap, ruled, continuity, parametrization, degree, compat)


#%% diagnotics


def check(s: Shape, results: Optional[List[Tuple[List[Shape], Any]]] = None) -> bool:
    """
    Check if a shape is valid.
    """

    analyzer = BRepAlgoAPI_Check(s.wrapped)
    analyzer.SetRunParallel(True)
    analyzer.SetUseOBB(True)

    analyzer.Perform()

    rv = analyzer.IsValid()

    # output detailed results if requested
    if results is not None:
        results.clear()

        for r in analyzer.Result():
            results.append(
                (_toptools_list_to_shapes(r.GetFaultyShapes1()), r.GetCheckStatus())
            )

    return rv
