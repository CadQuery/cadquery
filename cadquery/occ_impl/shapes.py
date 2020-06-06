from .geom import Vector, BoundBox, Plane

import OCP.TopAbs as ta  # Tolopolgy type enum
import OCP.GeomAbs as ga  # Geometry type enum

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

# collection of pints (used for spline construction)
from OCP.TColgp import TColgp_HArray1OfPnt
from OCP.BRepAdaptor import BRepAdaptor_Curve, BRepAdaptor_Surface
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
)

# properties used to store mass calculation result
from OCP.GProp import GProp_GProps
from OCP.BRepGProp import BRepGProp_Face, BRepGProp  # used for mass calculation
from OCP.BRepLProp import BRepLProp_CLProps  # local curve properties

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

from OCP.TopExp import TopExp_Explorer  # Toplogy explorer

# used for getting underlying geoetry -- is this equvalent to brep adaptor?
from OCP.BRep import BRep_Tool

from OCP.TopoDS import TopoDS, TopoDS_Builder, TopoDS_Compound, TopoDS_Iterator

from OCP.GC import GC_MakeArcOfCircle, GC_MakeArcOfEllipse  # geometry construction
from OCP.GCE2d import GCE2d_MakeSegment
from OCP.GeomAPI import GeomAPI_Interpolate, GeomAPI_ProjectPointOnSurf

from OCP.BRepFill import BRepFill

from OCP.BRepAlgoAPI import BRepAlgoAPI_Common, BRepAlgoAPI_Fuse, BRepAlgoAPI_Cut

from OCP.Geom import Geom_ConicalSurface, Geom_CylindricalSurface
from OCP.Geom2d import Geom2d_Line

from OCP.BRepLib import BRepLib

from OCP.BRepOffsetAPI import (
    BRepOffsetAPI_ThruSections,
    BRepOffsetAPI_MakePipeShell,
    BRepOffsetAPI_MakeThickSolid,
)

from OCP.BRepFilletAPI import BRepFilletAPI_MakeChamfer, BRepFilletAPI_MakeFillet

from OCP.TopTools import TopTools_IndexedDataMapOfShapeListOfShape, TopTools_ListOfShape

from OCP.TopExp import TopExp

from OCP.ShapeFix import ShapeFix_Shape, ShapeFix_Solid

from OCP.STEPControl import STEPControl_Writer, STEPControl_AsIs

from OCP.BRepMesh import BRepMesh_IncrementalMesh
from OCP.StlAPI import StlAPI_Writer

from OCP.ShapeUpgrade import ShapeUpgrade_UnifySameDomain

from OCP.BRepTools import BRepTools

from OCP.LocOpe import LocOpe_DPrism

from OCP.BRepCheck import BRepCheck_Analyzer

from OCP.Font import (
    Font_FontMgr,
    Font_BRepTextBuilder,
    Font_FA_Regular,
    Font_FA_Italic,
    Font_FA_Bold,
)

from OCP.BRepFeat import BRepFeat_MakeDPrism

from OCP.BRepClass3d import BRepClass3d_SolidClassifier

from OCP.TCollection import TCollection_AsciiString

from OCP.TopLoc import TopLoc_Location

from OCP.GeomAbs import GeomAbs_C0
from OCP.GeomAbs import GeomAbs_Intersection
from OCP.BRepOffsetAPI import BRepOffsetAPI_MakeFilling
from OCP.BRepOffset import BRepOffset_MakeOffset, BRepOffset_Skin

from OCP.BOPAlgo import BOPAlgo_GlueEnum

from math import pi, sqrt
from functools import reduce
import warnings

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
    ta.TopAbs_COMPOUND: TopoDS.Compound_s,
}

geom_LUT = {
    ta.TopAbs_VERTEX: "Vertex",
    ta.TopAbs_EDGE: BRepAdaptor_Curve,
    ta.TopAbs_WIRE: "Wire",
    ta.TopAbs_FACE: BRepAdaptor_Surface,
    ta.TopAbs_SHELL: "Shell",
    ta.TopAbs_SOLID: "Solid",
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
    ga.GeomAbs_OtherCurve: "OTHER",
}


def downcast(topods_obj):
    """
    Downcasts a TopoDS object to suitable specialized type
    """

    return downcast_LUT[topods_obj.ShapeType()](topods_obj)


class Shape(object):
    """
        Represents a shape in the system.
        Wrappers the FreeCAD api
    """

    def __init__(self, obj):
        self.wrapped = downcast(obj)
        self.forConstruction = False

        # Helps identify this solid through the use of an ID
        self.label = ""

    def clean(self):
        """Experimental clean using ShapeUpgrade"""

        upgrader = ShapeUpgrade_UnifySameDomain(self.wrapped, True, True, True)
        upgrader.AllowInternalEdges(False)
        upgrader.Build()

        return self.cast(upgrader.Shape())

    def fix(self):
        """Try to fix shape if not valid"""
        if not BRepCheck_Analyzer(self.wrapped).IsValid():
            sf = ShapeFix_Shape(self.wrapped)
            sf.Perform()
            fixed = downcast(sf.Shape())

            return self.cast(fixed)

        return self

    @classmethod
    def cast(cls, obj, forConstruction=False):
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
            ta.TopAbs_COMPOUND: Compound,
        }

        t = obj.ShapeType()
        # NB downcast is nedded to handly TopoDS_Shape types
        tr = constructor_LUT[t](downcast(obj))
        tr.forConstruction = forConstruction

        return tr

    def exportStl(self, fileName, precision=1e-3, angularPrecision=0.1):

        mesh = BRepMesh_IncrementalMesh(self.wrapped, precision, True, angularPrecision)
        mesh.Perform()

        writer = StlAPI_Writer()

        return writer.Write(self.wrapped, fileName)

    def exportStep(self, fileName):

        writer = STEPControl_Writer()
        writer.Transfer(self.wrapped, STEPControl_AsIs)

        return writer.Write(fileName)

    def exportBrep(self, fileName):
        """
        Export given shape to a BREP file
        """

        return BRepTools.Write_s(self.wrapped, fileName)

    def geomType(self):
        """
            Gets the underlying geometry type
            :return: a string according to the geometry type.

            Implementations can return any values desired, but the
            values the user uses in type filters should correspond to these.

            As an example, if a user does::

                CQ(object).faces("%mytype")

            The expectation is that the geomType attribute will return 'mytype'

            The return values depend on the type of the shape:

            Vertex:  always 'Vertex'
            Edge:   LINE, ARC, CIRCLE, SPLINE
            Face:   PLANE, SPHERE, CONE
            Solid:  'Solid'
            Shell:  'Shell'
            Compound: 'Compound'
            Wire:   'Wire'
        """

        tr = geom_LUT[self.wrapped.ShapeType()]

        if type(tr) is str:
            return tr
        elif tr is BRepAdaptor_Curve:
            return geom_LUT_EDGE[tr(self.wrapped).GetType()]
        else:
            return geom_LUT_FACE[tr(self.wrapped).GetType()]

    def hashCode(self):
        return self.wrapped.HashCode(HASH_CODE_MAX)

    def isNull(self):
        return self.wrapped.IsNull()

    def isSame(self, other):
        return self.wrapped.IsSame(other.wrapped)

    def isEqual(self, other):
        return self.wrapped.IsEqual(other.wrapped)

    def isValid(self):
        return BRepCheck_Analyzer(self.wrapped).IsValid()

    def BoundingBox(self, tolerance=None):  # need to implement that in GEOM
        return BoundBox._fromTopoDS(self.wrapped, tol=tolerance)

    def mirror(self, mirrorPlane="XY", basePointVector=(0, 0, 0)):

        if mirrorPlane == "XY" or mirrorPlane == "YX":
            mirrorPlaneNormalVector = gp_Dir(0, 0, 1)
        elif mirrorPlane == "XZ" or mirrorPlane == "ZX":
            mirrorPlaneNormalVector = gp_Dir(0, 1, 0)
        elif mirrorPlane == "YZ" or mirrorPlane == "ZY":
            mirrorPlaneNormalVector = gp_Dir(1, 0, 0)

        if type(basePointVector) == tuple:
            basePointVector = Vector(basePointVector)

        T = gp_Trsf()
        T.SetMirror(gp_Ax2(gp_Pnt(*basePointVector.toTuple()), mirrorPlaneNormalVector))

        return self._apply_transform(T)

    @staticmethod
    def _center_of_mass(shape):

        Properties = GProp_GProps()
        BRepGProp.VolumeProperties_s(shape, Properties)

        return Vector(Properties.CentreOfMass())

    def Center(self):
        """
        Center of mass
        """

        return Shape.centerOfMass(self)

    def CenterOfBoundBox(self, tolerance=0.1):
        return self.BoundingBox().center

    @staticmethod
    def CombinedCenter(objects):
        """
        Calculates the center of mass of multiple objects.

        :param objects: a list of objects with mass
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
    def computeMass(obj):
        """
        Calculates the 'mass' of an object.
        """
        Properties = GProp_GProps()
        calc_function = shape_properties_LUT[obj.wrapped.ShapeType()]

        if calc_function:
            calc_function(obj.wrapped, Properties)
            return Properties.Mass()
        else:
            raise NotImplementedError

    @staticmethod
    def centerOfMass(obj):
        """
        Calculates the 'mass' of an object.
        """
        Properties = GProp_GProps()
        calc_function = shape_properties_LUT[obj.wrapped.ShapeType()]

        if calc_function:
            calc_function(obj.wrapped, Properties)
            return Vector(Properties.CentreOfMass())
        else:
            raise NotImplementedError

    @staticmethod
    def CombinedCenterOfBoundBox(objects, tolerance=0.1):
        """
        Calculates the center of BoundBox of multiple objects.

        :param objects: a list of objects with mass 1
        """
        total_mass = len(objects)

        weighted_centers = []
        for o in objects:
            o.wrapped.tessellate(tolerance)
            weighted_centers.append(o.wrapped.BoundBox.Center.multiply(1.0))

        sum_wc = weighted_centers[0]
        for wc in weighted_centers[1:]:
            sum_wc = sum_wc.add(wc)

        return Vector(sum_wc.multiply(1.0 / total_mass))

    def Closed(self):
        return self.wrapped.Closed()

    def ShapeType(self):
        return shape_LUT[self.wrapped.ShapeType()]

    def _entities(self, topo_type):

        out = {}  # using dict to prevent duplicates

        explorer = TopExp_Explorer(self.wrapped, inverse_shape_LUT[topo_type])

        while explorer.More():
            item = explorer.Current()
            out[
                item.HashCode(HASH_CODE_MAX)
            ] = item  # needed to avoid pseudo-duplicate entities
            explorer.Next()

        return list(out.values())

    def Vertices(self):

        return [Vertex(i) for i in self._entities("Vertex")]

    def Edges(self):
        return [
            Edge(i)
            for i in self._entities("Edge")
            if not BRep_Tool.Degenerated_s(TopoDS.Edge_s(i))
        ]

    def Compounds(self):
        return [Compound(i) for i in self._entities("Compound")]

    def Wires(self):
        return [Wire(i) for i in self._entities("Wire")]

    def Faces(self):
        return [Face(i) for i in self._entities("Face")]

    def Shells(self):
        return [Shell(i) for i in self._entities("Shell")]

    def Solids(self):
        return [Solid(i) for i in self._entities("Solid")]

    def Area(self):
        Properties = GProp_GProps()
        BRepGProp.SurfaceProperties_s(self.wrapped, Properties)

        return Properties.Mass()

    def Volume(self):
        # when density == 1, mass == volume
        return Shape.computeMass(self)

    def _apply_transform(self, T):

        return Shape.cast(BRepBuilderAPI_Transform(self.wrapped, T, True).Shape())

    def rotate(self, startVector, endVector, angleDegrees):
        """
        Rotates a shape around an axis
        :param startVector: start point of rotation axis  either a 3-tuple or a Vector
        :param endVector:  end point of rotation axis, either a 3-tuple or a Vector
        :param angleDegrees:  angle to rotate, in degrees
        :return: a copy of the shape, rotated
        """
        if type(startVector) == tuple:
            startVector = Vector(startVector)

        if type(endVector) == tuple:
            endVector = Vector(endVector)

        T = gp_Trsf()
        T.SetRotation(
            gp_Ax1(startVector.toPnt(), (endVector - startVector).toDir()),
            angleDegrees * DEG2RAD,
        )

        return self._apply_transform(T)

    def translate(self, vector):

        if type(vector) == tuple:
            vector = Vector(vector)

        T = gp_Trsf()
        T.SetTranslation(vector.wrapped)

        return self._apply_transform(T)

    def scale(self, factor):

        T = gp_Trsf()
        T.SetScale(gp_Pnt(), factor)

        return self._apply_transform(T)

    def copy(self):

        return Shape.cast(BRepBuilderAPI_Copy(self.wrapped).Shape())

    def transformShape(self, tMatrix):
        """
            tMatrix is a matrix object.
            returns a copy of the ojbect, transformed by the provided matrix,
            with all objects keeping their type
        """

        r = Shape.cast(
            BRepBuilderAPI_Transform(self.wrapped, tMatrix.wrapped.Trsf()).Shape()
        )
        r.forConstruction = self.forConstruction

        return r

    def transformGeometry(self, tMatrix):
        """
            tMatrix is a matrix object.

            returns a copy of the object, but with geometry transformed insetad of just
            rotated.

            WARNING: transformGeometry will sometimes convert lines and circles to splines,
            but it also has the ability to handle skew and stretching transformations.

            If your transformation is only translation and rotation, it is safer to use transformShape,
            which doesnt change the underlying type of the geometry, but cannot handle skew transformations
        """
        r = Shape.cast(
            BRepBuilderAPI_GTransform(self.wrapped, tMatrix.wrapped, True).Shape()
        )
        r.forConstruction = self.forConstruction

        return r

    def __hash__(self):
        return self.hashCode()

    def _bool_op(self, args, tools, op):
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

    def cut(self, *toCut):
        """
        Remove a shape from another one
        """

        cut_op = BRepAlgoAPI_Cut()

        return self._bool_op((self,), toCut, cut_op)

    def fuse(self, *toFuse, glue=False, tol=None):
        """
        Fuse shapes together
        """

        fuse_op = BRepAlgoAPI_Fuse()
        if glue:
            fuse_op.SetGlue(BOPAlgo_GlueEnum.BOPAlgo_GlueShift)
        if tol:
            fuse_op.SetFuzzyValue(tol)

        rv = self._bool_op((self,), toFuse, fuse_op)

        return rv

    def intersect(self, *toIntersect):
        """
        Construct shape intersection
        """

        intersect_op = BRepAlgoAPI_Common()

        return self._bool_op((self,), toIntersect, intersect_op)

    def _repr_html_(self):
        """
        Jupyter 3D representation support
        """

        from .jupyter_tools import display

        return display(self)


class Vertex(Shape):
    """
    A Single Point in Space
    """

    def __init__(self, obj, forConstruction=False):
        """
            Create a vertex from a FreeCAD Vertex
        """
        super(Vertex, self).__init__(obj)

        self.forConstruction = forConstruction
        self.X, self.Y, self.Z = self.toTuple()

    def toTuple(self):

        geom_point = BRep_Tool.Pnt_s(self.wrapped)
        return (geom_point.X(), geom_point.Y(), geom_point.Z())

    def Center(self):
        """
            The center of a vertex is itself!
        """
        return Vector(self.toTuple())

    @classmethod
    def makeVertex(cls, x, y, z):

        return cls(BRepBuilderAPI_MakeVertex(gp_Pnt(x, y, z)).Vertex())


class Mixin1D(object):
    def Length(self):

        Properties = GProp_GProps()
        BRepGProp.LinearProperties_s(self.wrapped, Properties)

        return Properties.Mass()

    def IsClosed(self):

        return BRep_Tool.IsClosed_s(self.wrapped)


class Edge(Shape, Mixin1D):
    """
    A trimmed curve that represents the border of a face
    """

    def _geomAdaptor(self):
        """
        Return the underlying geometry
        """
        return BRepAdaptor_Curve(self.wrapped)

    def startPoint(self):
        """

            :return: a vector representing the start poing of this edge

            Note, circles may have the start and end points the same
        """

        curve = self._geomAdaptor()
        umin = curve.FirstParameter()

        return Vector(curve.Value(umin))

    def endPoint(self):
        """

            :return: a vector representing the end point of this edge.

            Note, circles may have the start and end points the same

        """

        curve = self._geomAdaptor()
        umax = curve.LastParameter()

        return Vector(curve.Value(umax))

    def tangentAt(self, locationParam=0.5):
        """
        Compute tangent vector at the specified location.
        :param locationParam: location to use in [0,1]
        :return: tangent vector
        """

        curve = self._geomAdaptor()

        umin, umax = curve.FirstParameter(), curve.LastParameter()
        umid = (1 - locationParam) * umin + locationParam * umax

        curve_props = BRepLProp_CLProps(curve, 2, curve.Tolerance())
        curve_props.SetParameter(umid)

        if curve_props.IsTangentDefined():
            dir_handle = gp_Dir()  # this is awkward due to C++ pass by ref in the API
            curve_props.Tangent(dir_handle)

            return Vector(dir_handle)

    def Center(self):

        Properties = GProp_GProps()
        BRepGProp.LinearProperties_s(self.wrapped, Properties)

        return Vector(Properties.CentreOfMass())

    @classmethod
    def makeCircle(
        cls, radius, pnt=Vector(0, 0, 0), dir=Vector(0, 0, 1), angle1=360.0, angle2=360
    ):
        """

        """
        pnt = Vector(pnt)
        dir = Vector(dir)

        circle_gp = gp_Circ(gp_Ax2(pnt.toPnt(), dir.toDir()), radius)

        if angle1 == angle2:  # full circle case
            return cls(BRepBuilderAPI_MakeEdge(circle_gp).Edge())
        else:  # arc case
            circle_geom = GC_MakeArcOfCircle(
                circle_gp, angle1 * DEG2RAD, angle2 * DEG2RAD, True
            ).Value()
            return cls(BRepBuilderAPI_MakeEdge(circle_geom).Edge())

    @classmethod
    def makeEllipse(
        cls,
        x_radius,
        y_radius,
        pnt=Vector(0, 0, 0),
        dir=Vector(0, 0, 1),
        xdir=Vector(1, 0, 0),
        angle1=360.0,
        angle2=360.0,
        sense=1,
    ):
        """
        Makes an Ellipse centered at the provided point, having normal in the provided direction
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

        pnt = Vector(pnt).toPnt()
        dir = Vector(dir).toDir()
        xdir = Vector(xdir).toDir()

        ax1 = gp_Ax1(pnt, dir)
        ax2 = gp_Ax2(pnt, dir, xdir)

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
    def makeSpline(cls, listOfVector, tangents=None, periodic=False, tol=1e-6):
        """
        Interpolate a spline through the provided points.
        :param cls:
        :param listOfVector: a list of Vectors that represent the points
        :param tangents: tuple of Vectors specifying start and finish tangent
        :param periodic: creation of peridic curves
        :param tol: tolerance of the algorithm (consult OCC documentation)
        :return: an Edge
        """
        pnts = TColgp_HArray1OfPnt(1, len(listOfVector))
        for ix, v in enumerate(listOfVector):
            pnts.SetValue(ix + 1, v.toPnt())

        spline_builder = GeomAPI_Interpolate(pnts, periodic, tol)
        if tangents:
            v1, v2 = tangents
            spline_builder.Load(v1.wrapped, v2.wrapped)

        spline_builder.Perform()
        spline_geom = spline_builder.Curve()

        return cls(BRepBuilderAPI_MakeEdge(spline_geom).Edge())

    @classmethod
    def makeThreePointArc(cls, v1, v2, v3):
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
    def makeTangentArc(cls, v1, v2, v3):
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
    def makeLine(cls, v1, v2):
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

    @classmethod
    def combine(cls, listOfWires):
        """
        Attempt to combine a list of wires into a new wire.
        the wires are returned in a list.
        :param cls:
        :param listOfWires:
        :return:
        """

        wire_builder = BRepBuilderAPI_MakeWire()
        for wire in listOfWires:
            wire_builder.Add(wire.wrapped)

        return cls(wire_builder.Wire())

    @classmethod
    def assembleEdges(cls, listOfEdges):
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

        for e in listOfEdges:
            wire_builder.Add(e.wrapped)

        wire_builder.Build()

        if not wire_builder.IsDone():
            w = (
                "BRepBuilderAPI_MakeWire::Error(): returns the construction status. BRepBuilderAPI_WireDone if the wire is built, or another value of the BRepBuilderAPI_WireError enumeration indicating why the construction failed = "
                + str(wire_builder.Error())
            )
            warnings.warn(w)

        return cls(wire_builder.Wire())

    @classmethod
    def makeCircle(cls, radius, center, normal):
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
        x_radius,
        y_radius,
        center,
        normal,
        xDir,
        angle1=360.0,
        angle2=360.0,
        rotation_angle=0.0,
        closed=True,
    ):
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
    def makePolygon(cls, listOfVertices, forConstruction=False):
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
        pitch,
        height,
        radius,
        center=Vector(0, 0, 0),
        dir=Vector(0, 0, 1),
        angle=360.0,
        lefthand=False,
    ):
        """
        Make a helix with a given pitch, height and radius
        By default a cylindrical surface is used to create the helix. If
        the fourth parameter is set (the apex given in degree) a conical surface is used instead'
        """

        # 1. build underlying cylindrical/conical surface
        if angle == 360.0:
            geom_surf = Geom_CylindricalSurface(
                gp_Ax3(center.toPnt(), dir.toDir()), radius
            )
        else:
            geom_surf = Geom_ConicalSurface(
                gp_Ax3(center.toPnt(), dir.toDir()), angle * DEG2RAD, radius
            )

        # 2. construct an semgent in the u,v domain
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
        BRepLib.BuildCurves3d_s(w)

        return cls(w)

    def stitch(self, other):
        """Attempt to stich wires"""

        wire_builder = BRepBuilderAPI_MakeWire()
        wire_builder.Add(TopoDS.Wire_s(self.wrapped))
        wire_builder.Add(TopoDS.Wire_s(other.wrapped))
        wire_builder.Build()

        return self.__class__(wire_builder.Wire())


class Face(Shape):
    """
    a bounded surface that represents part of the boundary of a solid
    """

    def _geomAdaptor(self):
        """
        Return the underlying geometry
        """
        return BRep_Tool.Surface_s(self.wrapped)

    def _uvBounds(self):

        return BRepTools.UVBounds_s(self.wrapped)

    def normalAt(self, locationVector=None):
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

    def Center(self):

        Properties = GProp_GProps()
        BRepGProp.SurfaceProperties_s(self.wrapped, Properties)

        return Vector(Properties.CentreOfMass())

    def outerWire(self):

        return self.cast(BRepTools.OuterWire_s(self.wrapped))

    def innerWires(self):

        outer = self.outerWire()

        return [w for w in self.Wires() if not w.isSame(outer)]

    @classmethod
    def makeNSidedSurface(
        cls,
        edges,
        points,
        continuity=GeomAbs_C0,
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
    ):
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
        return cls.cast(face).fix()

    @classmethod
    def makePlane(cls, length=None, width=None, basePnt=(0, 0, 0), dir=(0, 0, 1)):
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

    @classmethod
    def makeRuledSurface(cls, edgeOrWire1, edgeOrWire2, dist=None):
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
    def makeFromWires(cls, outerWire, innerWires=[]):
        """
        Makes a planar face from one or more wires
        """

        face_builder = BRepBuilderAPI_MakeFace(outerWire.wrapped, True)

        for w in innerWires:
            face_builder.Add(w.wrapped)

        face_builder.Build()
        face = face_builder.Shape()

        return cls.cast(face).fix()


class Shell(Shape):
    """
    the outer boundary of a surface
    """

    @classmethod
    def makeShell(cls, listOfFaces):

        shell_builder = BRepBuilderAPI_Sewing()

        for face in listOfFaces:
            shell_builder.Add(face.wrapped)

        shell_builder.Perform()
        s = shell_builder.SewedShape()

        return cls.cast(s)


class Mixin3D(object):
    def tessellate(self, tolerance):

        import faulthandler

        faulthandler.enable()

        if not BRepTools.Triangulation_s(self.wrapped, tolerance):
            BRepMesh_IncrementalMesh(self.wrapped, tolerance, True)

        vertices = []
        triangles = []
        offset = 0

        for f in self.Faces():

            loc = TopLoc_Location()
            poly = BRep_Tool.Triangulation_s(f.wrapped, loc)
            Trsf = loc.Transformation()

            # add vertices
            vertices += [
                Vector(v.X(), v.Y(), v.Z())
                for v in (v.Transformed(Trsf) for v in poly.Nodes())
            ]

            # add triangles
            triangles += [
                tuple(el + offset for el in t.Get()) for t in poly.Triangles()
            ]

            offset += poly.NbNodes()

        return vertices, triangles

    def fillet(self, radius, edgeList):
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

    def chamfer(self, length, length2, edgeList):
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

    def shell(self, faceList, thickness, tolerance=0.0001):
        """
            make a shelled solid of given  by removing the list of faces

        :param faceList: list of face objects, which must be part of the solid.
        :param thickness: floating point thickness. positive shells outwards, negative shells inwards
        :param tolerance: modelling tolerance of the method, default=0.0001
        :return: a shelled solid
        """

        occ_faces_list = TopTools_ListOfShape()
        for f in faceList:
            occ_faces_list.Append(f.wrapped)

        shell_builder = BRepOffsetAPI_MakeThickSolid(
            self.wrapped, occ_faces_list, thickness, tolerance
        )

        shell_builder.Build()

        return self.__class__(shell_builder.Shape())

    def isInside(self, point, tolerance=1.0e-6):
        """
        Returns whether or not the point is inside a solid or compound
        object within the specified tolerance.

        :param point: tuple or Vector representing 3D point to be tested
        :param tolerance: tolerence for inside determination, default=1.0e-6
        :return: bool indicating whether or not point is within solid
        """
        if isinstance(point, Vector):
            point = point.toTuple()

        solid_classifier = BRepClass3d_SolidClassifier(self.wrapped)
        solid_classifier.Perform(gp_Pnt(*point), tolerance)

        return solid_classifier.State() == ta.TopAbs_IN or solid_classifier.IsOnAFace()


class Solid(Shape, Mixin3D):
    """
    a single solid
    """

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
    ):
        """
        Returns a plate surface that is 'thickness' thick, enclosed by 'surf_edge_pts' points,  and going through 'surf_pts' points.

        :param surf_edges
        :type 1 surf_edges: list of [x,y,z] float ordered coordinates
        :type 2 surf_edges: list of ordered or unordered CadQuery wires
        :param surf_pts = [] (uses only edges if [])
        :type surf_pts: list of [x,y,z] float coordinates
        :param thickness = 0 (returns 2D surface if 0)
        :type thickness: float (may be negative or positive depending on thicknening direction)
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

    @classmethod
    def isSolid(cls, obj):
        """
            Returns true if the object is a FreeCAD solid, false otherwise
        """
        if hasattr(obj, "ShapeType"):
            if obj.ShapeType == "Solid" or (
                obj.ShapeType == "Compound" and len(obj.Solids) > 0
            ):
                return True
        return False

    @classmethod
    def makeSolid(cls, shell):

        return cls(ShapeFix_Solid().SolidFromShell(shell.wrapped))

    @classmethod
    def makeBox(cls, length, width, height, pnt=Vector(0, 0, 0), dir=Vector(0, 0, 1)):
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
        radius1,
        radius2,
        height,
        pnt=Vector(0, 0, 0),
        dir=Vector(0, 0, 1),
        angleDegrees=360,
    ):
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
        cls, radius, height, pnt=Vector(0, 0, 0), dir=Vector(0, 0, 1), angleDegrees=360
    ):
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
        radius1,
        radius2,
        pnt=None,
        dir=None,
        angleDegrees1=None,
        angleDegrees2=None,
    ):
        """
        makeTorus(radius1,radius2,[pnt,dir,angle1,angle2,angle]) --
        Make a torus with agiven radii and angles
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
    def makeLoft(cls, listOfWire, ruled=False):
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
        dx,
        dy,
        dz,
        xmin,
        zmin,
        xmax,
        zmax,
        pnt=Vector(0, 0, 0),
        dir=Vector(0, 0, 1),
    ):
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
        radius,
        pnt=Vector(0, 0, 0),
        dir=Vector(0, 0, 1),
        angleDegrees1=0,
        angleDegrees2=90,
        angleDegrees3=360,
    ):
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
    def _extrudeAuxSpine(cls, wire, spine, auxSpine):
        """
        Helper function for extrudeLinearWithRotation
        """
        extrude_builder = BRepOffsetAPI_MakePipeShell(spine)
        extrude_builder.SetMode(auxSpine, False)  # auxiliary spine
        extrude_builder.Add(wire)
        extrude_builder.Build()
        extrude_builder.MakeSolid()
        return extrude_builder.Shape()

    @classmethod
    def extrudeLinearWithRotation(
        cls, outerWire, innerWires, vecCenter, vecNormal, angleDegrees
    ):
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
        straight_spine_w = Wire.combine([straight_spine_e,]).wrapped

        # make an auxliliary spine
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
            cls._extrudeAuxSpine(w.wrapped, straight_spine_w.aux_spine_w)
            for w in innerWires
        ]

        # combine the inner solids into compund
        inner_comp = Compound._makeCompound(inner_solids)

        # subtract from the outer solid
        return cls(BRepAlgoAPI_Cut(outer_solid, inner_comp).Shape())

    @classmethod
    def extrudeLinear(cls, outerWire, innerWires, vecNormal, taper=0):
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
            prism_builder = BRepPrimAPI_MakePrism(face.wrapped, vecNormal.wrapped, True)
        else:
            face = Face.makeFromWires(outerWire)
            faceNormal = face.normalAt()
            d = 1 if vecNormal.getAngle(faceNormal) < 90 * DEG2RAD else -1
            prism_builder = LocOpe_DPrism(
                face.wrapped, d * vecNormal.Length, d * taper * DEG2RAD
            )

        return cls(prism_builder.Shape())

    @classmethod
    def revolve(cls, outerWire, innerWires, angleDegrees, axisStart, axisEnd):
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
    def sweep(
        cls,
        outerWire,
        innerWires,
        path,
        makeSolid=True,
        isFrenet=False,
        transitionMode="transformed",
    ):
        """
        Attempt to sweep the list of wires  into a prismatic solid along the provided path

        :param outerWire: the outermost wire
        :param innerWires: a list of inner wires
        :param path: The wire to sweep the face resulting from the wires over
        :param boolean makeSolid: return Solid or Shell (defualt True)
        :param boolean isFrenet: Frenet mode (default False)
        :param transitionMode:
            handling of profile orientation at C1 path discontinuities.
            Possible values are {'transformed','round', 'right'} (default: 'right').
        :return: a Solid object
        """
        if path.ShapeType() == "Edge":
            path = Wire.assembleEdges([path,])

        shapes = []
        for w in [outerWire] + innerWires:
            builder = BRepOffsetAPI_MakePipeShell(path.wrapped)
            builder.SetMode(isFrenet)
            builder.SetTransitionMode(cls._transModeDict[transitionMode])
            builder.Add(w.wrapped)

            builder.Build()
            if makeSolid:
                builder.MakeSolid()

            shapes.append(cls(builder.Shape()))

        rv, inner_shapes = shapes[0], shapes[1:]

        if inner_shapes:
            inner_shapes = reduce(lambda a, b: a.fuse(b), inner_shapes)
            rv = rv.cut(inner_shapes)

        return rv

    @classmethod
    def sweep_multi(cls, profiles, path, makeSolid=True, isFrenet=False):
        """
        Multi section sweep. Only single outer profile per section is allowed.

        :param profiles: list of profiles
        :param path: The wire to sweep the face resulting from the wires over
        :return: a Solid object
        """
        if path.ShapeType() == "Edge":
            path = Wire.assembleEdges([path,])

        builder = BRepOffsetAPI_MakePipeShell(path.wrapped)

        for p in profiles:
            builder.Add(p.wrapped)

        builder.SetMode(isFrenet)
        builder.Build()

        if makeSolid:
            builder.MakeSolid()

        return cls(builder.Shape())

    def dprism(self, basis, profiles, depth=None, taper=0, thruAll=True, additive=True):
        """
        Make a prismatic feature (additive or subtractive)

        :param basis: face to perfrom the operation on
        :param profiles: list of profiles
        :param depth: depth of the cut or extrusion
        :param thruAll: cut thruAll
        :return: a Solid object
        """

        sorted_profiles = sortWiresByBuildOrder(profiles)
        shape = self.wrapped
        basis = basis.wrapped
        for p in sorted_profiles:
            face = Face.makeFromWires(p[0], p[1:])
            feat = BRepFeat_MakeDPrism(
                shape, face.wrapped, basis, taper * DEG2RAD, additive, False
            )

            if thruAll:
                feat.PerformThruAll()
            else:
                feat.Perform(depth)

            shape = feat.Shape()

        return self.__class__(shape)


class Compound(Shape, Mixin3D):
    """
    a collection of disconnected solids
    """

    @staticmethod
    def _makeCompound(listOfShapes):

        comp = TopoDS_Compound()
        comp_builder = TopoDS_Builder()
        comp_builder.MakeCompound(comp)

        for s in listOfShapes:
            comp_builder.Add(comp, s)

        return comp

    @classmethod
    def makeCompound(cls, listOfShapes):
        """
        Create a compound out of a list of shapes
        """

        return cls(cls._makeCompound((s.wrapped for s in listOfShapes)))

    @classmethod
    def makeText(
        cls,
        text,
        size,
        height,
        font="Arial",
        kind="regular",
        halign="center",
        valign="center",
        position=Plane.XY(),
    ):
        """
        Create a 3D text
        """

        font_kind = {
            "regular": Font_FA_Regular,
            "bold": Font_FA_Bold,
            "italic": Font_FA_Italic,
        }[kind]

        mgr = Font_FontMgr.GetInstance_s()
        font = mgr.FindFont(TCollection_AsciiString(font), font_kind)

        builder = Font_BRepTextBuilder()
        text_flat = Shape(
            builder.Perform(font.FontName().ToCString(), size, font_kind, text)
        )

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

    def __iter__(self):
        """
        Iterate over subshapes.    

        """

        it = TopoDS_Iterator(self.wrapped)

        while it.More():
            yield Shape.cast(it.Value())
            it.Next()

    def cut(self, *toCut):
        """
        Remove a shape from another one
        """

        cut_op = BRepAlgoAPI_Cut()

        return self._bool_op(self, toCut, cut_op)

    def fuse(self, *toFuse, glue=False, tol=None):
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
            rv = self
        else:
            rv = self._bool_op(args[:1], args[1:], fuse_op)

        # fuse_op.RefineEdges()
        # fuse_op.FuseEdges()

        return rv

    def intersect(self, *toIntersect):
        """
        Construct shape intersection
        """

        intersect_op = BRepAlgoAPI_Common()

        return self._bool_op(self, toIntersect, intersect_op)


def sortWiresByBuildOrder(wireList, result={}):
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
