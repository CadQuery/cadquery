from cadquery import Vector, BoundBox, Plane

import OCC.Core.TopAbs as ta  # Tolopolgy type enum
import OCC.Core.GeomAbs as ga  # Geometry type enum

from OCC.Core.gp import (gp_Vec, gp_Pnt, gp_Ax1, gp_Ax2, gp_Ax3, gp_Dir, gp_Circ,
                    gp_Trsf, gp_Pln, gp_GTrsf, gp_Pnt2d, gp_Dir2d)

# collection of pints (used for spline construction)
from OCC.Core.TColgp import TColgp_HArray1OfPnt
from OCC.Core.BRepAdaptor import BRepAdaptor_Curve, BRepAdaptor_Surface
from OCC.Core.BRepBuilderAPI import (BRepBuilderAPI_MakeVertex,
                                BRepBuilderAPI_MakeEdge,
                                BRepBuilderAPI_MakeFace,
                                BRepBuilderAPI_MakePolygon,
                                BRepBuilderAPI_MakeWire,
                                BRepBuilderAPI_Copy,
                                BRepBuilderAPI_GTransform,
                                BRepBuilderAPI_Transform,
                                BRepBuilderAPI_Transformed,
                                BRepBuilderAPI_RightCorner,
                                BRepBuilderAPI_RoundCorner)
# properties used to store mass calculation result
from OCC.Core.GProp import GProp_GProps
from OCC.Core.BRepGProp import BRepGProp_Face, \
    brepgprop_LinearProperties,  \
    brepgprop_SurfaceProperties, \
    brepgprop_VolumeProperties  # used for mass calculation
from OCC.Core.BRepLProp import BRepLProp_CLProps  # local curve properties

from OCC.Core.BRepPrimAPI import (BRepPrimAPI_MakeBox,  # TODO list functions/used for making primitives
                             BRepPrimAPI_MakeCone,
                             BRepPrimAPI_MakeCylinder,
                             BRepPrimAPI_MakeTorus,
                             BRepPrimAPI_MakeWedge,
                             BRepPrimAPI_MakePrism,
                             BRepPrimAPI_MakeRevol,
                             BRepPrimAPI_MakeSphere)

from OCC.Core.TopExp import TopExp_Explorer  # Toplogy explorer
from OCC.Core.BRepTools import (BRepTools_WireExplorer,  # might be needed for iterating thorugh wires
                           breptools_UVBounds)
# used for getting underlying geoetry -- is this equvalent to brep adaptor?
from OCC.Core.BRep import BRep_Tool, BRep_Tool_Degenerated

from OCC.Core.TopoDS import (topods_Vertex,  # downcasting functions
                        topods_Edge,
                        topods_Wire,
                        topods_Face,
                        topods_Shell,
                        topods_Compound,
                        topods_Solid)

from OCC.Core.TopoDS import (TopoDS_Shell,
                        TopoDS_Compound,
                        TopoDS_Builder)

from OCC.Core.GC import GC_MakeArcOfCircle  # geometry construction
from OCC.Core.GCE2d import GCE2d_MakeSegment
from OCC.Core.GeomAPI import (GeomAPI_Interpolate,
                         GeomAPI_ProjectPointOnSurf)

from OCC.Core.BRepFill import brepfill_Shell, brepfill_Face

from OCC.Core.BRepAlgoAPI import (BRepAlgoAPI_Common,
                             BRepAlgoAPI_Fuse,
                             BRepAlgoAPI_Cut)

from OCC.Core.GeomLProp import GeomLProp_SLProps

from OCC.Core.Geom import Geom_ConicalSurface, Geom_CylindricalSurface
from OCC.Core.Geom2d import Geom2d_Line

from OCC.Core.BRepLib import breplib_BuildCurves3d

from OCC.Core.BRepOffsetAPI import (BRepOffsetAPI_ThruSections,
                               BRepOffsetAPI_MakePipe,
                               BRepOffsetAPI_MakePipeShell,
                               BRepOffsetAPI_MakeThickSolid)

from OCC.Core.BRepFilletAPI import (BRepFilletAPI_MakeChamfer,
                               BRepFilletAPI_MakeFillet)

from OCC.Core.TopTools import (TopTools_IndexedDataMapOfShapeListOfShape,
                          TopTools_ListOfShape)

from OCC.Core.TopExp import topexp_MapShapesAndAncestors

from OCC.Core.TopTools import TopTools_HSequenceOfShape, Handle_TopTools_HSequenceOfShape

from OCC.Core.ShapeAnalysis import ShapeAnalysis_FreeBounds

from OCC.Core.ShapeFix import ShapeFix_Wire, ShapeFix_Face

from OCC.Core.STEPControl import STEPControl_Writer, STEPControl_AsIs

from OCC.Core.BRepMesh import BRepMesh_IncrementalMesh
from OCC.Core.StlAPI import StlAPI_Writer

from OCC.Core.TopTools import TopTools_DataMapOfShapeListOfShape, TopTools_ListIteratorOfListOfShape

from OCC.Core.ShapeUpgrade import ShapeUpgrade_UnifySameDomain

from OCC.Core.BRepTools import breptools_Write

from OCC.Core.Visualization import Tesselator

from OCC.Core.LocOpe import LocOpe_DPrism

from OCC.Core.BRepCheck import BRepCheck_Analyzer

from OCC.Core.Addons import (text_to_brep,
                             Font_FA_Regular,
                             Font_FA_Italic,
                             Font_FA_Bold)

from OCC.Core.BRepFeat import BRepFeat_MakePrism, BRepFeat_MakeDPrism


from math import pi, sqrt
from functools import reduce

TOLERANCE = 1e-6
DEG2RAD = 2 * pi / 360.
HASH_CODE_MAX = int(1e+6)  # required by OCC.Core.HashCode

shape_LUT = \
    {ta.TopAbs_VERTEX: 'Vertex',
     ta.TopAbs_EDGE: 'Edge',
     ta.TopAbs_WIRE: 'Wire',
     ta.TopAbs_FACE: 'Face',
     ta.TopAbs_SHELL: 'Shell',
     ta.TopAbs_SOLID: 'Solid',
     ta.TopAbs_COMPOUND: 'Compound'}

shape_properties_LUT = \
    {ta.TopAbs_VERTEX: None,
     ta.TopAbs_EDGE: brepgprop_LinearProperties,
     ta.TopAbs_WIRE: brepgprop_LinearProperties,
     ta.TopAbs_FACE: brepgprop_SurfaceProperties,
     ta.TopAbs_SHELL: brepgprop_SurfaceProperties,
     ta.TopAbs_SOLID: brepgprop_VolumeProperties,
     ta.TopAbs_COMPOUND: brepgprop_VolumeProperties}

inverse_shape_LUT = {v: k for k, v in shape_LUT.items()}

downcast_LUT = \
    {ta.TopAbs_VERTEX: topods_Vertex,
     ta.TopAbs_EDGE: topods_Edge,
     ta.TopAbs_WIRE: topods_Wire,
     ta.TopAbs_FACE: topods_Face,
     ta.TopAbs_SHELL: topods_Shell,
     ta.TopAbs_SOLID: topods_Solid,
     ta.TopAbs_COMPOUND: topods_Compound}

geom_LUT = \
    {ta.TopAbs_VERTEX: 'Vertex',
     ta.TopAbs_EDGE: BRepAdaptor_Curve,
     ta.TopAbs_WIRE: 'Wire',
     ta.TopAbs_FACE: BRepAdaptor_Surface,
     ta.TopAbs_SHELL: 'Shell',
     ta.TopAbs_SOLID: 'Solid',
     ta.TopAbs_COMPOUND: 'Compound'}

geom_LUT_FACE = \
    {ga.GeomAbs_Plane : 'PLANE',
     ga.GeomAbs_Cylinder : 'CYLINDER',
     ga.GeomAbs_Cone : 'CONE',
     ga.GeomAbs_Sphere : 'SPHERE',
     ga.GeomAbs_Torus : 'TORUS',
     ga.GeomAbs_BezierSurface : 'BEZIER',
     ga.GeomAbs_BSplineSurface : 'BSPLINE',
     ga.GeomAbs_SurfaceOfRevolution : 'REVOLUTION',
     ga.GeomAbs_SurfaceOfExtrusion : 'EXTRUSION',
     ga.GeomAbs_OffsetSurface : 'OFFSET',
     ga.GeomAbs_OtherSurface : 'OTHER'}

geom_LUT_EDGE = \
    {ga.GeomAbs_Line : 'LINE',
     ga.GeomAbs_Circle : 'CIRCLE',
     ga.GeomAbs_Ellipse : 'ELLIPSE',
     ga.GeomAbs_Hyperbola : 'HYPERBOLA',
     ga.GeomAbs_Parabola : 'PARABOLA',
     ga.GeomAbs_BezierCurve : 'BEZIER',
     ga.GeomAbs_BSplineCurve : 'BSPLINE',
     ga.GeomAbs_OtherCurve : 'OTHER'}


def downcast(topods_obj):
    '''
    Downcasts a TopoDS object to suitable specialized type
    '''

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

        upgrader = ShapeUpgrade_UnifySameDomain(
            self.wrapped, True, True, True)
        upgrader.Build()

        return self.cast(upgrader.Shape())

    @classmethod
    def cast(cls, obj, forConstruction=False):
        "Returns the right type of wrapper, given a FreeCAD object"
        '''
        if type(obj) == FreeCAD.Base.Vector:
            return Vector(obj)
        '''  # FIXME to be removed?
        tr = None

        # define the shape lookup table for casting
        constructor_LUT = {ta.TopAbs_VERTEX: Vertex,
                           ta.TopAbs_EDGE: Edge,
                           ta.TopAbs_WIRE: Wire,
                           ta.TopAbs_FACE: Face,
                           ta.TopAbs_SHELL: Shell,
                           ta.TopAbs_SOLID: Solid,
                           ta.TopAbs_COMPOUND: Compound}

        t = obj.ShapeType()
        # NB downcast is nedded to handly TopoDS_Shape types
        tr = constructor_LUT[t](downcast(obj))
        tr.forConstruction = forConstruction
        # TODO move this to Compound constructor?
        '''
           #compound of solids, lets return a solid instead
            if len(obj.Solids) > 1:
                tr = Solid(obj)
            elif len(obj.Solids) == 1:
                tr = Solid(obj.Solids[0])
            elif len(obj.Wires) > 0:
                tr = Wire(obj)
            else:
                tr = Compound(obj)
        else:
            raise ValueError("cast:unknown shape type %s" % s)
        '''

        return tr

    # TODO: all these should move into the exporters folder.
    # we dont need a bunch of exporting code stored in here!
    #
    def exportStl(self, fileName, precision=1e-5):

        mesh = BRepMesh_IncrementalMesh(self.wrapped, precision, True)
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

        return breptools_Write(self.wrapped, fileName)

    def exportShape(self, fileName, fileFormat):
        pass

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

    def isType(self, obj, strType):  # TODO why here?
        """
            Returns True if the shape is the specified type, false otherwise

            contrast with ShapeType, which will raise an exception
            if the provide object is not a shape at all
        """
        if hasattr(obj, 'ShapeType'):
            return obj.ShapeType == strType
        else:
            return False

    def hashCode(self):
        return self.wrapped.HashCode(HASH_CODE_MAX)

    def isNull(self):
        return self.wrapped.IsNull()

    def isSame(self, other):
        return self.wrapped.IsSame(other.wrapped)

    def isEqual(self, other):
        return self.wrapped.IsEqual(other.wrapped)

    def isValid(self):  # seems to be not used in the codebase -- remove?
        return BRepCheck_Analyzer(self.wrapped).IsValid()

    def BoundingBox(self, tolerance=0.1):  # need to implement that in GEOM
        return BoundBox._fromTopoDS(self.wrapped)

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
        T.SetMirror(gp_Ax2(gp_Pnt(*basePointVector.toTuple()),
                           mirrorPlaneNormalVector))

        return self._apply_transform(T)

    @staticmethod
    def _center_of_mass(shape):

        Properties = GProp_GProps()
        brepgprop_VolumeProperties(shape,
                                   Properties)

        return Vector(Properties.CentreOfMass())

    def Center(self):
        '''
        Center of mass
        '''

        return Shape.centerOfMass(self)

    def CenterOfBoundBox(self, tolerance=0.1):
        return self.BoundingBox(self.wrapped).center

    @staticmethod
    def CombinedCenter(objects):  # TODO
        """
        Calculates the center of mass of multiple objects.

        :param objects: a list of objects with mass
        """
        total_mass = sum(Shape.computeMass(o) for o in objects)
        weighted_centers = [Shape.centerOfMass(o).multiply(
            Shape.computeMass(o)) for o in objects]

        sum_wc = weighted_centers[0]
        for wc in weighted_centers[1:]:
            sum_wc = sum_wc.add(wc)

        return Vector(sum_wc.multiply(1. / total_mass))

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
            raise NotImplemented

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
            raise NotImplemented

    @staticmethod
    def CombinedCenterOfBoundBox(objects, tolerance=0.1):  # TODO
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

        return Vector(sum_wc.multiply(1. / total_mass))

    def Closed(self):
        return self.wrapped.Closed()

    def ShapeType(self):
        return shape_LUT[self.wrapped.ShapeType()]

    def _entities(self, topo_type):

        out = {}  # using dict to prevent duplicates

        explorer = TopExp_Explorer(self.wrapped, inverse_shape_LUT[topo_type])

        while explorer.More():
            item = explorer.Current()
            out[item.__hash__()] = item  # some implementations use __hash__
            explorer.Next()

        return list(out.values())

    def Vertices(self):

        return [Vertex(i) for i in self._entities('Vertex')]

    def Edges(self):
        return [Edge(i) for i in self._entities('Edge') if not BRep_Tool_Degenerated(i)]

    def Compounds(self):
        return [Compound(i) for i in self._entities('Compound')]

    def Wires(self):
        return [Wire(i) for i in self._entities('Wire')]

    def Faces(self):
        return [Face(i) for i in self._entities('Face')]

    def Shells(self):
        return [Shell(i) for i in self._entities('Shell')]

    def Solids(self):
        return [Solid(i) for i in self._entities('Solid')]

    def Area(self):
        Properties = GProp_GProps()
        brepgprop_SurfaceProperties(self.wrapped,
                                    Properties)

        return Properties.Mass()

    def Volume(self):
        # when density == 1, mass == volume
        return Shape.computeMass(self)

    def _apply_transform(self, T):

        return Shape.cast(BRepBuilderAPI_Transform(self.wrapped,
                                                   T,
                                                   True).Shape())

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
        T.SetRotation(gp_Ax1(startVector.toPnt(),
                             (endVector - startVector).toDir()),
                      angleDegrees * DEG2RAD)

        return self._apply_transform(T)

    def translate(self, vector):

        if type(vector) == tuple:
            vector = Vector(vector)

        T = gp_Trsf()
        T.SetTranslation(vector.wrapped)

        return self._apply_transform(T)

    def scale(self, factor):

        T = gp_Trsf()
        T.SetScale(gp_Pnt(),
                   factor)

        return self._apply_transform(T)

    def copy(self):

        return Shape.cast(BRepBuilderAPI_Copy(self.wrapped).Shape())

    def transformShape(self, tMatrix):
        """
            tMatrix is a matrix object.
            returns a copy of the ojbect, transformed by the provided matrix,
            with all objects keeping their type
        """

        r = Shape.cast(BRepBuilderAPI_Transform(self.wrapped,
                                                tMatrix.wrapped).Shape())
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
        r = Shape.cast(BRepBuilderAPI_GTransform(self.wrapped,
                                                 gp_GTrsf(tMatrix.wrapped),
                                                 True).Shape())
        r.forConstruction = self.forConstruction

        return r

    def __hash__(self):
        return self.hashCode()

    def cut(self, toCut):
        """
        Remove a shape from another one
        """
        return Shape.cast(BRepAlgoAPI_Cut(self.wrapped,
                                          toCut.wrapped).Shape())

    def fuse(self, toFuse):
        """
        Fuse shapes together
        """

        fuse_op = BRepAlgoAPI_Fuse(self.wrapped, toFuse.wrapped)
        fuse_op.RefineEdges()
        fuse_op.FuseEdges()
        # fuse_op.SetFuzzyValue(TOLERANCE)
        fuse_op.Build()

        return Shape.cast(fuse_op.Shape())

    def intersect(self, toIntersect):
        """
        Construct shape intersection
        """
        return Shape.cast(BRepAlgoAPI_Common(self.wrapped,
                                             toIntersect.wrapped).Shape())

    def _repr_html_(self):
        """
        Jupyter 3D representation support
        """

        from .jupyter_tools import x3d_display
        return x3d_display(self.wrapped, export_edges=True)


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

        geom_point = BRep_Tool.Pnt(self.wrapped)
        return (geom_point.X(),
                geom_point.Y(),
                geom_point.Z())

    def Center(self):
        """
            The center of a vertex is itself!
        """
        return Vector(self.toTuple())

    @classmethod
    def makeVertex(cls, x, y, z):

        return cls(BRepBuilderAPI_MakeVertex(gp_Pnt(x, y, z)
                                             ).Vertex())


class Mixin1D(object):

    def Length(self):

        Properties = GProp_GProps()
        brepgprop_LinearProperties(self.wrapped, Properties)

        return Properties.Mass()

    def IsClosed(self):

        return BRep_Tool.IsClosed(self.wrapped)


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
        umid = (1-locationParam)*umin + locationParam*umax

        # TODO what are good parameters for those?
        curve_props = BRepLProp_CLProps(curve, 2, curve.Tolerance())
        curve_props.SetParameter(umid)

        if curve_props.IsTangentDefined():
            dir_handle = gp_Dir()  # this is awkward due to C++ pass by ref in the API
            curve_props.Tangent(dir_handle)

            return Vector(dir_handle)

    def Center(self):

        Properties = GProp_GProps()
        brepgprop_LinearProperties(self.wrapped,
                                   Properties)

        return Vector(Properties.CentreOfMass())

    @classmethod
    def makeCircle(cls, radius, pnt=Vector(0, 0, 0), dir=Vector(0, 0, 1), angle1=360.0, angle2=360):
        """

        """
        pnt = Vector(pnt)
        dir = Vector(dir)

        circle_gp = gp_Circ(gp_Ax2(pnt.toPnt(),
                                   dir.toDir()),
                            radius)

        if angle1 == angle2:  # full circle case
            return cls(BRepBuilderAPI_MakeEdge(circle_gp).Edge())
        else:  # arc case
            circle_geom = GC_MakeArcOfCircle(circle_gp,
                                             angle1 * DEG2RAD,
                                             angle2 * DEG2RAD,
                                             True).Value()
            return cls(BRepBuilderAPI_MakeEdge(circle_geom).Edge())

    @classmethod
    def makeSpline(cls, listOfVector, tangents=None, periodic=False,
                   tol = 1e-6):
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
            pnts.SetValue(ix+1, v.toPnt())

        spline_builder = GeomAPI_Interpolate(pnts, periodic, tol)
        if tangents:
          v1,v2 = tangents
          spline_builder.Load(v1.wrapped,v2.wrapped)

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
        circle_geom = GC_MakeArcOfCircle(v1.toPnt(),
                                         v2.toPnt(),
                                         v3.toPnt()).Value()

        return cls(BRepBuilderAPI_MakeEdge(circle_geom).Edge())

    @classmethod
    def makeLine(cls, v1, v2):
        """
            Create a line between two points
            :param v1: Vector that represents the first point
            :param v2: Vector that represents the second point
            :return: A linear edge between the two provided points
        """
        return cls(BRepBuilderAPI_MakeEdge(v1.toPnt(),
                                           v2.toPnt()).Edge())


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
            :param listOfEdges: a list of Edge objects
            :return: a wire with the edges assembled
        """
        wire_builder = BRepBuilderAPI_MakeWire()
        for edge in listOfEdges:
            wire_builder.Add(edge.wrapped)

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
    def makePolygon(cls, listOfVertices, forConstruction=False):
        # convert list of tuples into Vectors.
        wire_builder = BRepBuilderAPI_MakePolygon()

        for v in listOfVertices:
            wire_builder.Add(v.toPnt())

        w = cls(wire_builder.Wire())
        w.forConstruction = forConstruction

        return w

    @classmethod
    def makeHelix(cls, pitch, height, radius, center=Vector(0, 0, 0),
                  dir=Vector(0, 0, 1), angle=360.0, lefthand=False):
        """
        Make a helix with a given pitch, height and radius
        By default a cylindrical surface is used to create the helix. If
        the fourth parameter is set (the apex given in degree) a conical surface is used instead'
        """

        # 1. build underlying cylindrical/conical surface
        if angle == 360.:
            geom_surf = Geom_CylindricalSurface(gp_Ax3(center.toPnt(), dir.toDir()),
                                                radius)
        else:
            geom_surf = Geom_ConicalSurface(gp_Ax3(center.toPnt(), dir.toDir()),
                                            angle * DEG2RAD,  # TODO why no orientation?
                                            radius)

        # 2. construct an semgent in the u,v domain
        if lefthand:
            geom_line = Geom2d_Line(gp_Pnt2d(0.0, 0.0), gp_Dir2d(-2 * pi, pitch))
        else:
            geom_line = Geom2d_Line(gp_Pnt2d(0.0, 0.0), gp_Dir2d(2 * pi, pitch))

        # 3. put it together into a wire
        n_turns = height / pitch
        u_start = geom_line.Value(0.)
        u_stop = geom_line.Value(sqrt(n_turns * ((2 * pi)**2 + pitch**2)))
        geom_seg = GCE2d_MakeSegment(u_start, u_stop).Value()

        e = BRepBuilderAPI_MakeEdge(geom_seg, geom_surf).Edge()

        # 4. Convert to wire and fix building 3d geom from 2d geom
        w = BRepBuilderAPI_MakeWire(e).Wire()
        breplib_BuildCurves3d(w)

        return cls(w)

    def stitch(self, other):
        """Attempt to stich wires"""

        wire_builder = BRepBuilderAPI_MakeWire()
        wire_builder.Add(topods_Wire(self.wrapped))
        wire_builder.Add(topods_Wire(other.wrapped))
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
        return BRep_Tool.Surface(self.wrapped)  # BRepAdaptor_Surface(self.wrapped)

    def _uvBounds(self):

        return breptools_UVBounds(self.wrapped)

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
            projector = GeomAPI_ProjectPointOnSurf(locationVector.toPnt(),
                                                   surface)

            u, v = projector.LowerDistanceParameters()

        p = gp_Pnt()
        vn = gp_Vec()
        BRepGProp_Face(self.wrapped).Normal(u, v, p, vn)

        return Vector(vn)

    def Center(self):

        Properties = GProp_GProps()
        brepgprop_SurfaceProperties(self.wrapped,
                                    Properties)

        return Vector(Properties.CentreOfMass())

    @classmethod
    def makePlane(cls, length, width, basePnt=(0, 0, 0), dir=(0, 0, 1)):
        basePnt = Vector(basePnt)
        dir = Vector(dir)

        pln_geom = gp_Pln(basePnt.toPnt(), dir.toDir())

        return cls(BRepBuilderAPI_MakeFace(pln_geom,
                                           -width * 0.5,
                                           width * 0.5,
                                           -length * 0.5,
                                           length * 0.5).Face())

    @classmethod
    def makeRuledSurface(cls, edgeOrWire1, edgeOrWire2, dist=None):
        """
        'makeRuledSurface(Edge|Wire,Edge|Wire) -- Make a ruled surface
        Create a ruled surface out of two edges or wires. If wires are used then
        these must have the same number of edges
        """

        if isinstance(edgeOrWire1, Wire):
            return cls.cast(brepfill_Shell(edgeOrWire1.wrapped,
                                           edgeOrWire1.wrapped))
        else:
            return cls.cast(brepfill_Face(edgeOrWire1.wrapped,
                                          edgeOrWire1.wrapped))

    @classmethod
    def makeFromWires(cls, outerWire, innerWires=[]):
        '''
        Makes a planar face from one or more wires
        '''
        face_builder = BRepBuilderAPI_MakeFace(outerWire.wrapped,
                                               True)  # True is for planar only

        for w in innerWires:
            face_builder.Add(w.wrapped)
        face_builder.Build()
        f = face_builder.Face()

        sf = ShapeFix_Face(f)  # fix wire orientation
        sf.FixOrientation()

        return cls(sf.Face())


class Shell(Shape):
    """
    the outer boundary of a surface
    """

    @classmethod
    def makeShell(cls, listOfFaces):

        shell_wrapped = TopoDS_Shell()
        shell_builder = TopoDS_Builder()
        shell_builder.MakeShell(shell_wrapped)

        for face in listOfFaces:
            shell_builder.Add(face.wrapped)

        return cls(shell_wrapped)


class Mixin3D(object):

    def tessellate(self, tolerance):
        tess = Tesselator(self.wrapped)
        tess.Compute(compute_edges=True, mesh_quality=tolerance)

        vertices = []
        indexes  = []

        # add vertices
        for i_vert in range(tess.ObjGetVertexCount()):
            xyz = tess.GetVertex(i_vert)
            vertices.append(Vector(*xyz))

        # add triangles
        for i_tr in range(tess.ObjGetTriangleCount()):
            indexes.append(tess.GetTriangleIndex(i_tr))

        return vertices, indexes

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
        topexp_MapShapesAndAncestors(self.wrapped,
                                     ta.TopAbs_EDGE,
                                     ta.TopAbs_FACE,
                                     edge_face_map)

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
            chamfer_builder.Add(d1,
                                d2,
                                e,
                                topods_Face(face))  # NB: edge_face_map return a generic TopoDS_Shape
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

        shell_builder = BRepOffsetAPI_MakeThickSolid(self.wrapped,
                                                     occ_faces_list,
                                                     thickness,
                                                     tolerance)

        shell_builder.Build()

        return self.__class__(shell_builder.Shape())


class Solid(Shape, Mixin3D):
    """
    a single solid
    """

    @classmethod
    def isSolid(cls, obj):
        """
            Returns true if the object is a FreeCAD solid, false otherwise
        """
        if hasattr(obj, 'ShapeType'):
            if obj.ShapeType == 'Solid' or \
                    (obj.ShapeType == 'Compound' and len(obj.Solids) > 0):
                return True
        return False

    @classmethod
    def makeBox(cls, length, width, height, pnt=Vector(0, 0, 0), dir=Vector(0, 0, 1)):
        """
        makeBox(length,width,height,[pnt,dir]) -- Make a box located in pnt with the dimensions (length,width,height)
        By default pnt=Vector(0,0,0) and dir=Vector(0,0,1)'
        """
        return cls(BRepPrimAPI_MakeBox(gp_Ax2(pnt.toPnt(),
                                              dir.toDir()),
                                       length,
                                       width,
                                       height).Shape())

    @classmethod
    def makeCone(cls, radius1, radius2, height, pnt=Vector(0, 0, 0), dir=Vector(0, 0, 1), angleDegrees=360):
        """
        Make a cone with given radii and height
        By default pnt=Vector(0,0,0),
        dir=Vector(0,0,1) and angle=360'
        """
        return cls(BRepPrimAPI_MakeCone(gp_Ax2(pnt.toPnt(),
                                               dir.toDir()),
                                        radius1,
                                        radius2,
                                        height,
                                        angleDegrees * DEG2RAD).Shape())

    @classmethod
    def makeCylinder(cls, radius, height, pnt=Vector(0, 0, 0), dir=Vector(0, 0, 1), angleDegrees=360):
        """
        makeCylinder(radius,height,[pnt,dir,angle]) --
        Make a cylinder with a given radius and height
        By default pnt=Vector(0,0,0),dir=Vector(0,0,1) and angle=360'
        """
        return cls(BRepPrimAPI_MakeCylinder(gp_Ax2(pnt.toPnt(),
                                                   dir.toDir()),
                                            radius,
                                            height,
                                            angleDegrees * DEG2RAD).Shape())

    @classmethod
    def makeTorus(cls, radius1, radius2, pnt=None, dir=None, angleDegrees1=None, angleDegrees2=None):
        """
        makeTorus(radius1,radius2,[pnt,dir,angle1,angle2,angle]) --
        Make a torus with agiven radii and angles
        By default pnt=Vector(0,0,0),dir=Vector(0,0,1),angle1=0
        ,angle1=360 and angle=360'
        """
        return cls(BRepPrimAPI_MakeTorus(gp_Ax2(pnt.toPnt(),
                                                dir.toDir()),
                                         radius1,
                                         radius2,
                                         angleDegrees1 * DEG2RAD,
                                         angleDegrees2 * DEG2RAD).Shape())

    @classmethod
    def makeLoft(cls, listOfWire, ruled=False):
        """
            makes a loft from a list of wires
            The wires will be converted into faces when possible-- it is presumed that nobody ever actually
            wants to make an infinitely thin shell for a real FreeCADPart.
        """
        # the True flag requests building a solid instead of a shell.
        loft_builder = BRepOffsetAPI_ThruSections(True, ruled)

        for w in listOfWire:
            loft_builder.AddWire(w.wrapped)

        loft_builder.Build()

        return cls(loft_builder.Shape())

    @classmethod
    def makeWedge(cls, xmin, ymin, zmin, z2min, x2min, xmax, ymax, zmax, z2max, x2max, pnt=Vector(0, 0, 0), dir=Vector(0, 0, 1)):
        """
        Make a wedge located in pnt
        By default pnt=Vector(0,0,0) and dir=Vector(0,0,1)
        """
        return cls(BRepPrimAPI_MakeWedge(gp_Ax2(pnt.toPnt(),
                                                dir.toDir()),
                                         xmin,
                                         ymin,
                                         zmin,
                                         z2min,
                                         x2min,
                                         xmax,
                                         ymax,
                                         zmax,
                                         z2max,
                                         x2max).Solid())

    @classmethod
    def makeSphere(cls, radius, pnt=Vector(0, 0, 0), dir=Vector(0, 0, 1), angleDegrees1=0, angleDegrees2=90, angleDegrees3=360):
        """
        Make a sphere with a given radius
        By default pnt=Vector(0,0,0), dir=Vector(0,0,1), angle1=0, angle2=90 and angle3=360
        """
        return cls(BRepPrimAPI_MakeSphere(gp_Ax2(pnt.toPnt(),
                                                 dir.toDir()),
                                          radius,
                                          angleDegrees1 * DEG2RAD,
                                          angleDegrees2 * DEG2RAD,
                                          angleDegrees3 * DEG2RAD).Shape())

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
    def extrudeLinearWithRotation(cls, outerWire, innerWires, vecCenter, vecNormal, angleDegrees):
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
        straight_spine_w = Wire.combine([straight_spine_e, ]).wrapped

        # make an auxliliary spine
        pitch = 360. / angleDegrees * vecNormal.Length
        radius = 1
        aux_spine_w = Wire.makeHelix(pitch,
                                     vecNormal.Length,
                                     radius,
                                     center=vecCenter,
                                     dir=vecNormal).wrapped

        # extrude the outer wire
        outer_solid = cls._extrudeAuxSpine(outerWire.wrapped,
                                           straight_spine_w,
                                           aux_spine_w)

        # extrude inner wires
        inner_solids = [cls._extrudeAuxSpine(w.wrapped,
                                             straight_spine_w.
                                             aux_spine_w) for w in innerWires]

        # combine dthe inner solids into compund
        inner_comp = TopoDS_Compound()
        comp_builder = TopoDS_Builder()
        comp_builder.MakeCompound(inner_comp)  # TODO this could be not needed

        for i in inner_solids:
            comp_builder.Add(inner_comp, i)

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

        if taper==0:
            face = Face.makeFromWires(outerWire, innerWires)
            prism_builder = BRepPrimAPI_MakePrism(
                face.wrapped, vecNormal.wrapped, True)
        else:
            face = Face.makeFromWires(outerWire)
            faceNormal = face.normalAt()
            d = 1 if vecNormal.getAngle(faceNormal)<90 * DEG2RAD else -1
            prism_builder = LocOpe_DPrism(face.wrapped,
                                          d * vecNormal.Length,
                                          d * taper * DEG2RAD)

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
        revol_builder = BRepPrimAPI_MakeRevol(face.wrapped,
                                              gp_Ax1(v1.toPnt(), v2.toDir()),
                                              angleDegrees * DEG2RAD,
                                              True)

        return cls(revol_builder.Shape())

    _transModeDict = {'transformed' : BRepBuilderAPI_Transformed,
                      'round' : BRepBuilderAPI_RoundCorner,
                      'right' : BRepBuilderAPI_RightCorner}

    @classmethod
    def sweep(cls, outerWire, innerWires, path, makeSolid=True, isFrenet=False,
              transitionMode='transformed'):
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
        if path.ShapeType() == 'Edge':
            path = Wire.assembleEdges([path, ])

        shapes = []
        for w in [outerWire]+innerWires:
            builder = BRepOffsetAPI_MakePipeShell(path.wrapped)
            builder.SetMode(isFrenet)
            builder.SetTransitionMode(cls._transModeDict[transitionMode])
            builder.Add(w.wrapped)

            builder.Build()
            if makeSolid:
                builder.MakeSolid()

            shapes.append(cls(builder.Shape()))

        rv,inner_shapes = shapes[0],shapes[1:]

        if inner_shapes:
            inner_shapes = reduce(lambda a,b: a.fuse(b),inner_shapes)
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
        if path.ShapeType() == 'Edge':
            path = Wire.assembleEdges([path, ])

        builder = BRepOffsetAPI_MakePipeShell(path.wrapped)

        for p in profiles:
            builder.Add(p.wrapped)

        builder.SetMode(isFrenet)
        builder.Build()

        if makeSolid:
            builder.MakeSolid()

        return cls(builder.Shape())

    def dprism(self, basis, profiles, depth=None, taper=0, thruAll=True,
              additive=True):
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
            face = Face.makeFromWires(p[0],p[1:])
            feat = BRepFeat_MakeDPrism(shape,
                                       face.wrapped,
                                       basis,
                                       taper*DEG2RAD,
                                       additive,
                                       False)

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

    @classmethod
    def makeCompound(cls, listOfShapes):
        """
        Create a compound out of a list of shapes
        """
        comp = TopoDS_Compound()
        comp_builder = TopoDS_Builder()
        comp_builder.MakeCompound(comp)  # TODO this could be not needed

        for s in listOfShapes:
            comp_builder.Add(comp, s.wrapped)

        return cls(comp)

    @classmethod
    def makeText(cls, text, size, height, font="Arial", kind='regular',
                 position=Plane.XY()):
        """
        Create a 3D text
        """

        font_kind = {'regular' : Font_FA_Regular,
                     'bold'    : Font_FA_Bold,
                     'italic'  : Font_FA_Italic}[kind]

        text_flat = Shape(text_to_brep(text, font, font_kind, size, False))
        vecNormal = text_flat.Faces()[0].normalAt()*height

        text_3d = BRepPrimAPI_MakePrism(text_flat.wrapped, vecNormal.wrapped)

        return cls(text_3d.Shape()).transformShape(position.rG)

# TODO this is likely not needed if sing PythonOCC.Core.correclty but we will see


def sortWiresByBuildOrder(wireList, result=[]):
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
        return [wireList, ]

    # make a Face
    face = Face.makeFromWires(wireList[0], wireList[1:])

    # use FixOrientation
    outer_inner_map = TopTools_DataMapOfShapeListOfShape()
    sf = ShapeFix_Face(face.wrapped)  # fix wire orientation
    sf.FixOrientation(outer_inner_map)

    # Iterate through the Inner:Outer Mapping
    all_wires = face.Wires()
    result = {w: outer_inner_map.Find(
        w.wrapped) for w in all_wires if outer_inner_map.IsBound(w.wrapped)}

    # construct the result
    rv = []
    for k, v in result.items():
        tmp = [k, ]

        iterator = TopTools_ListIteratorOfListOfShape(v)
        while iterator.More():
            tmp.append(Wire(iterator.Value()))
            iterator.Next()

        rv.append(tmp)

    return rv
