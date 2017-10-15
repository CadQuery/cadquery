from cadquery import Vector, BoundBox

import OCC.TopAbs as ta  # Tolopolgy type enum
import OCC.GeomAbs as ga  # Geometry type enum

from OCC.gp import (gp_Vec, gp_Pnt, gp_Ax1, gp_Ax2, gp_Ax3, gp_Dir, gp_Circ,
                    gp_Trsf, gp_Pln, gp_GTrsf, gp_Pnt2d, gp_Dir2d)

# collection of pints (used for spline construction)
from OCC.TColgp import TColgp_Array1OfPnt
from OCC.BRepAdaptor import BRepAdaptor_Curve, BRepAdaptor_Surface
from OCC.BRepBuilderAPI import (BRepBuilderAPI_MakeVertex,
                                BRepBuilderAPI_MakeEdge,
                                BRepBuilderAPI_MakeFace,
                                BRepBuilderAPI_MakePolygon,
                                BRepBuilderAPI_MakeWire,
                                BRepBuilderAPI_Copy,
                                BRepBuilderAPI_GTransform,
                                BRepBuilderAPI_Transform)
# properties used to store mass calculation result
from OCC.GProp import GProp_GProps
from OCC.BRepGProp import BRepGProp_Face, \
    brepgprop_LinearProperties,  \
    brepgprop_SurfaceProperties, \
    brepgprop_VolumeProperties  # used for mass calculation
from OCC.BRepLProp import BRepLProp_CLProps  # local curve properties

from OCC.BRepPrimAPI import (BRepPrimAPI_MakeBox,  # TODO list functions/used for making primitives
                             BRepPrimAPI_MakeCone,
                             BRepPrimAPI_MakeCylinder,
                             BRepPrimAPI_MakeTorus,
                             BRepPrimAPI_MakeWedge,
                             BRepPrimAPI_MakePrism,
                             BRepPrimAPI_MakeRevol,
                             BRepPrimAPI_MakeSphere)

from OCC.TopExp import TopExp_Explorer  # Toplogy explorer
from OCC.BRepTools import (BRepTools_WireExplorer,  # might be needed for iterating thorugh wires
                           breptools_UVBounds)
# used for getting underlying geoetry -- is this equvalent to brep adaptor?
from OCC.BRep import BRep_Tool

from OCC.TopoDS import (topods_Vertex,  # downcasting functions
                        topods_Edge,
                        topods_Wire,
                        topods_Face,
                        topods_Shell,
                        topods_Compound,
                        topods_Solid)

from OCC.TopoDS import (TopoDS_Shell,
                        TopoDS_Compound,
                        TopoDS_Builder)

from OCC.GC import GC_MakeArcOfCircle  # geometry construction
from OCC.GCE2d import GCE2d_MakeSegment
from OCC.GeomAPI import (GeomAPI_PointsToBSpline,
                         GeomAPI_ProjectPointOnSurf)

from OCC.BRepFill import brepfill_Shell, brepfill_Face

from OCC.BRepAlgoAPI import (BRepAlgoAPI_Common,
                             BRepAlgoAPI_Fuse,
                             BRepAlgoAPI_Cut)

from OCC.GeomLProp import GeomLProp_SLProps

from OCC.Geom import Geom_ConicalSurface, Geom_CylindricalSurface
from OCC.Geom2d import Geom2d_Line

from OCC.BRepLib import breplib_BuildCurves3d

from OCC.BRepOffsetAPI import (BRepOffsetAPI_ThruSections,
                               BRepOffsetAPI_MakePipe,
                               BRepOffsetAPI_MakePipeShell,
                               BRepOffsetAPI_MakeThickSolid)

from OCC.BRepFilletAPI import (BRepFilletAPI_MakeChamfer,
                               BRepFilletAPI_MakeFillet)

from OCC.TopTools import (TopTools_IndexedDataMapOfShapeListOfShape,
                          TopTools_ListOfShape)

from OCC.TopExp import topexp_MapShapesAndAncestors

from OCC.TopTools import TopTools_HSequenceOfShape, Handle_TopTools_HSequenceOfShape

from OCC.ShapeAnalysis import ShapeAnalysis_FreeBounds

from OCC.ShapeFix import ShapeFix_Wire, ShapeFix_Face

from OCC.STEPControl import STEPControl_Writer, STEPControl_AsIs

from OCC.BRepMesh import BRepMesh_IncrementalMesh
from OCC.StlAPI import StlAPI_Writer

from OCC.TopTools import TopTools_DataMapOfShapeListOfShape, TopTools_ListIteratorOfListOfShape

from OCC.ShapeUpgrade import ShapeUpgrade_UnifySameDomain

from OCC.BRepTools import breptools_Write

from math import pi, sqrt

TOLERANCE = 1e-6
DEG2RAD = 2 * pi / 360.
HASH_CODE_MAX = int(1e+6)  # required by OCC HashCode

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

# TODO there are many more geometry types, what to do with those?
geom_LUT_EDGE_FACE = \
    {ga.GeomAbs_Arc: 'ARC',
     ga.GeomAbs_Circle: 'CIRCLE',
     ga.GeomAbs_Line: 'LINE',
     ga.GeomAbs_BSplineCurve: 'SPLINE',  # BSpline or Bezier?
     ga.GeomAbs_Plane: 'PLANE',
     ga.GeomAbs_Sphere: 'SPHERE',
     ga.GeomAbs_Cone: 'CONE',
     }


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
            self.wrapped, True, True, False)
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
        else:
            return geom_LUT_EDGE_FACE[tr(self.wrapped).GetType()]

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
        raise NotImplemented

    def BoundingBox(self, tolerance=0.1):  # need to implement that in GEOM
        return BoundBox._fromTopoDS(self.wrapped)

    def mirror(self, mirrorPlane="XY", basePointVector=(0, 0, 0)):

        if mirrorPlane == "XY" or mirrorPlane == "YX":
            mirrorPlaneNormalVector = gp_Vec(0, 0, 1)
        elif mirrorPlane == "XZ" or mirrorPlane == "ZX":
            mirrorPlaneNormalVector = gp_Vec(0, 1, 0)
        elif mirrorPlane == "YZ" or mirrorPlane == "ZY":
            mirrorPlaneNormalVector = gp_Vec(1, 0, 0)

        if type(basePointVector) == tuple:
            basePointVector = Vector(basePointVector)

        T = gp_Trsf()
        T.SetMirror(gp_Ax2(gp_Pnt(*basePointVector.toTuple()),
                           mirrorPlaneNormalVector))

        return Shape.cast(self.wrapped.Transformed(T))

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
        return [Edge(i) for i in self._entities('Edge')]

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
        raise NotImplementedError

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
                      angleDegrees)

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

    def _ipython_display_(self):
        """
        Jupyter 3D representation support
        """

        from . import exporters
        from six import StringIO
        import json
        import pythreejs
        import numpy as np
        
        color='yellow'
        
        out = StringIO() 
        
        exporters.exportShape(self,
                              exporters.ExportTypes.TJS,
                              out)

        contents = out.getvalue()
        out.close()
   
        # Take the string and create a proper json object
        contents = json.loads(contents)
    
        # Vertices and Faces are both flat lists, but the pythreejs module requires list of lists
        old_v = contents['vertices']
        old_f = contents['faces']
    
        # Splits the list up in 3s, to produce a list of lists representing the vertices
        vertices = [old_v[i:i+3] for i in range(0, len(old_v), 3)]
    
        # JSON Schema has first position in the face's list reserved to indicate type.
        # Cadquery returns Triangle mesh, so we know that we must split list into lists of length 4
        # 1st entry to indicate triangle, next 3 to specify vertices
        three_faces = [old_f[i:i+4] for i in range(0, len(old_f), 4)]
        faces = []
    
        # Drop the first entry in the face list
        for entry in three_faces:
            entry.pop(0)
            faces.append(entry)
    
        # Cadquery does not supply face normals in the JSON,
        # and we cannot use THREE.JS built in 'computefaceNormals'
        # (at least, not easily)
        # Instead, we just calculate the face normals ourselves.
        # It is just the cross product of 2 vectors in the triangle.
        # TODO: see if there is a better way to achieve this result
        face_normals = []
    
        for entry in faces:
            v_a = np.asarray(vertices[entry[0]])
            v_b = np.asarray(vertices[entry[1]])
            v_c = np.asarray(vertices[entry[2]])
    
            vec_a = v_b - v_a
            vec_b = v_c - v_a
    
            cross = np.cross(vec_a, vec_b)
    
            face_normals.append([cross[0], cross[1], cross[2]])
    
        # set up geometry
        geom = pythreejs.PlainGeometry(vertices=vertices, faces=faces, faceNormals=face_normals)
        mtl = pythreejs.LambertMaterial(color=color)
        obj = pythreejs.Mesh(geometry=geom, material=mtl)
    
        # set up scene and camera
        cam_dist = 5
        fov = 35
        cam = pythreejs.PerspectiveCamera(
            position=[cam_dist, cam_dist, cam_dist], fov=fov,
            children=[pythreejs.DirectionalLight(color='#ffffff', position=[3, 5, 1], intensity=0.9)])
        scn_chld = [
            obj,
            pythreejs.AmbientLight(color='#dddddd')
        ]
        scn = pythreejs.Scene(children=scn_chld)
    
        render = pythreejs.Renderer(
            camera=cam,
            scene=scn,
            controls=[pythreejs.OrbitControls(controlling=cam)]
            )
    
        return render._ipython_display_()

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

    def tangentAt(self, locationVector=None):
        """
        Compute tangent vector at the specified location.
        :param locationVector: location to use. Use the center point if None
        :return: tangent vector
        """

        curve = self._geomAdaptor()

        if locationVector:
            raise NotImplementedError
        else:
            umin, umax = curve.FirstParameter(), curve.LastParameter()
            umid = 0.5 * (umin + umax)

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
    def makeSpline(cls, listOfVector):
        """
        Interpolate a spline through the provided points.
        :param cls:
        :param listOfVector: a list of Vectors that represent the points
        :return: an Edge
        """
        pnts = TColgp_Array1OfPnt(0, len(listOfVector) - 1)
        for ix, v in enumerate(listOfVector):
            pnts.SetValue(ix, v.toPnt())

        spline_geom = GeomAPI_PointsToBSpline(pnts).Curve()

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
    def makeHelix(cls, pitch, height, radius, center=Vector(0, 0, 0), dir=Vector(0, 0, 1), angle=360.0):
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
        geom_line = Geom2d_Line(gp_Pnt2d(0.0, 0.0), gp_Dir2d(2 * pi, pitch))

        # 3. put it together into a wire
        n_turns = height / pitch
        u_start = geom_line.Value(0.)
        u_stop = geom_line.Value(sqrt(n_turns * ((2 * pi)**2 + pitch**2)))
        geom_seg = GCE2d_MakeSegment(u_start, u_stop).Value()

        e = BRepBuilderAPI_MakeEdge(geom_seg, geom_surf.GetHandle()).Edge()

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
        return self.wrapped.tessellate(tolerance)

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
    def extrudeLinear(cls, outerWire, innerWires, vecNormal):
        """
            Attempt to extrude the list of wires  into a prismatic solid in the provided direction

            :param outerWire: the outermost wire
            :param innerWires: a list of inner wires
            :param vecNormal: a vector along which to extrude the wires
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

        # one would think that fusing faces into a compound and then extruding would work,
        # but it doesnt-- the resulting compound appears to look right, ( right number of faces, etc),
        # but then cutting it from the main solid fails with BRep_NotDone.
        # the work around is to extrude each and then join the resulting solids, which seems to work

        # FreeCAD allows this in one operation, but others might not

        face = Face.makeFromWires(outerWire, innerWires)
        prism_builder = BRepPrimAPI_MakePrism(
            face.wrapped, vecNormal.wrapped, True)

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

    @classmethod
    def sweep(cls, outerWire, innerWires, path, makeSolid=True, isFrenet=False):
        """
        Attempt to sweep the list of wires  into a prismatic solid along the provided path

        :param outerWire: the outermost wire
        :param innerWires: a list of inner wires
        :param path: The wire to sweep the face resulting from the wires over
        :return: a Solid object
        """

        if path.ShapeType() == 'Edge':
            path = Wire.assembleEdges([path, ])

        if makeSolid:
            face = Face.makeFromWires(outerWire, innerWires)

            builder = BRepOffsetAPI_MakePipe(path.wrapped, face.wrapped)

        else:
            builder = BRepOffsetAPI_MakePipeShell(path.wrapped)
            builder.Add(outerWire.wrapped)
            for w in innerWires:
                builder.Add(w.wrapped)

        builder.Build()

        return cls(builder.Shape())


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

# TODO this is likely not needed if sing PythonOCC correclty but we will see


def sortWiresByBuildOrder(wireList, plane, result=[]):
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
