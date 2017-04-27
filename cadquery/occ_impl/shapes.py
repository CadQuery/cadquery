from cadquery import Vector, BoundBox
import FreeCAD
import Part as FreeCADPart

import OCC.TopAbs as ta #Tolopolgy type enum
import OCC.GeomAbs as ga #Geometry type enum

from OCC.gp import gp_Vec, gp_Pnt, gp_Ax2, gp_Dir, gp_Circ, gp_Trsf
from OCC.TColgp import TColgp_Array1OfPnt #collection of pints (used for spline construction)
from OCC.BRepAdaptor import BRepAdaptor_Curve, BRepAdaptor_Surface
from OCC.BRepBuilderAPI import BRepBuilderAPI_Transform #used for mirror op
from OCC.BRepBuilderAPI import (BRepBuilderAPI_MakeVertex,
                                BRepBuilderAPI_MakeEdge,
                                BRepBuilderAPI_MakeFace)
from OCC.GProp import GProp_GProps #properties used to store mass calculation result
from OCC.BRepGProp import  brepgprop_LinearProperties,  \
                           brepgprop_SurfaceProperties, \
                           brepgprop_VolumeProperties #used for mass calculation
from OCC.BRepLProp import BRepLProp_CLProps #local curve properties
from OCC.BRepPrimAPI import * #TODO list functions/used for making primitives
from OCC.TopExp import TopExp_Explorer #Toplogy explorer
from OCC.BRepTools import BRepTools_WireExplorer #might be needed for iterating thorugh wires

from OCC.BRep import BRep_Tool #used for getting underlying geoetry -- is this equvalent to brep adaptor?

from OCC.TopoDS import (topods_Vertex, #downcasting functions
                        topods_Edge,
                        topods_Wire,
                        topods_Face,
                        topods_Shell,
                        topods_Compound,
                        topods_Solid)
                        
from OCC.GC import GC_MakeArcOfCircle #geometry construction
from OCC.GeomAPI import GeomAPI_PointsToBSpline

from math import pi

DEG2RAD = 2*pi / 360.
HASH_CODE_MAX = int(1e+6) #required by OCC HashCode

shape_LUT  = \
            {ta.TopAbs_VERTEX    : 'Vertex',
             ta.TopAbs_EDGE      : 'Edge',
             ta.TopAbs_WIRE      : 'Wire',
             ta.TopAbs_FACE      : 'Face',
             ta.TopAbs_SHELL     : 'Shell',
             ta.TopAbs_SOLID     : 'Solid',
             ta.TopAbs_COMPOUND  : 'Compound'}

inverse_shape_LUT  = {v:k for k,v in shape_LUT.iteritems()}

downcast_LUT = \
            {ta.TopAbs_VERTEX    : topods_Vertex,
             ta.TopAbs_EDGE      : topods_Edge,
             ta.TopAbs_WIRE      : topods_Wire,
             ta.TopAbs_FACE      : topods_Face,
             ta.TopAbs_SHELL     : topods_Shell,
             ta.TopAbs_SOLID     : topods_Solid,
             ta.TopAbs_COMPOUND  : topods_Compound}

geom_LUT  = \
            {ta.TopAbs_VERTEX    : 'Vertex',
             ta.TopAbs_EDGE      : BRepAdaptor_Curve,
             ta.TopAbs_WIRE      : 'Wire',
             ta.TopAbs_FACE      : BRepAdaptor_Surface,
             ta.TopAbs_SHELL     : 'Shell',
             ta.TopAbs_SOLID     : 'Solid',
             ta.TopAbs_COMPOUND  : 'Compound'}

#TODO there are many more geometry types, what to do with those?             
geom_LUT_EDGE_FACE = \
    {ga.GeomAbs_Arc            : 'ARC',
     ga.GeomAbs_Line           : 'CIRCLE',
     ga.GeomAbs_Line           : 'LINE',
     ga.GeomAbs_BSplineCurve   : 'SPLINE',  #BSpline or Bezier?
     ga.GeomAbs_Plane          : 'PLANE',
     ga.GeomAbs_Sphere         : 'SPHERE',
     ga.GeomAbs_Cone           : 'CONE',
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

    @classmethod
    def cast(cls, obj, forConstruction=False):
        "Returns the right type of wrapper, given a FreeCAD object"
        if type(obj) == FreeCAD.Base.Vector:
            return Vector(obj)
        tr = None

        #define the shape lookup table for casting
        constructor_LUT = {ta.TopAbs_VERTEX    : Vertex,
                           ta.TopAbs_EDGE      : Edge,
                           ta.TopAbs_WIRE      : Wire,
                           ta.TopAbs_FACE      : Face,
                           ta.TopAbs_SHELL     : Shell,
                           ta.TopAbs_SOLID     : Solid,
                           ta.TopAbs_COMPOUND  : Compound}

        t = obj.ShapeType()
        tr = constructor_LUT[t](downcast(obj)) #NB downcast is nedded to handly TopoDS_Shape types
        tr.forConstruction = forConstruction
        #TODO move this to Compound constructor?
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
    def exportStl(self, fileName):
        pass
    
    def exportStep(self, fileName):
        pass

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
        

    def isType(self, obj, strType): #TODO why here?
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

    def isValid(self): #seems to be not used in the codebase -- remove?
        raise NotImplemented

    def BoundingBox(self, tolerance=0.1): #need to implement that in GEOM
        return BoundBox._fromTopoDS(self.wrapped)

    def mirror(self, mirrorPlane="XY", basePointVector=(0, 0, 0)):
        
        if mirrorPlane == "XY" or mirrorPlane== "YX":
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
    
        return Shape._center_of_mass(self.wrapped)

    def CenterOfBoundBox(self, tolerance = 0.1):
        return self.BoundingBox(self.wrapped).center
    
    @staticmethod
    def CombinedCenter(objects): #TODO
        """
        Calculates the center of mass of multiple objects.

        :param objects: a list of objects with mass
        """
        total_mass = sum(Shape.computeMass(o) for o in objects)
        weighted_centers = [o.wrapped.CenterOfMass.multiply(Shape.computeMass(o)) for o in objects]

        sum_wc = weighted_centers[0]
        for wc in weighted_centers[1:] :
            sum_wc = sum_wc.add(wc)

        return Vector(sum_wc.multiply(1./total_mass))

    @staticmethod
    def computeMass(object): #TODO
        """
        Calculates the 'mass' of an object. in FreeCAD < 15, all objects had a mass.
        in FreeCAD >=15, faces no longer have mass, but instead have area.
        """
        if object.wrapped.ShapeType == 'Face':
          return object.wrapped.Area
        else:
          return object.wrapped.Mass

    @staticmethod
    def CombinedCenterOfBoundBox(objects, tolerance = 0.1): #TODO
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
        for wc in weighted_centers[1:] :
            sum_wc = sum_wc.add(wc)

        return Vector(sum_wc.multiply(1./total_mass))

    def Closed(self):
        return self.wrapped.Closed()

    def ShapeType(self):
        return shape_LUT[self.wrapped.ShapeType()]
        
        
    def _entities(self,topo_type):
        
        out = {} #using dict to prevent duplicates
        
        explorer = TopExp_Explorer(self.wrapped, inverse_shape_LUT[topo_type])
        
        while explorer.More():
            item = explorer.Current()
            out[item.__hash__()] = item # some implementations use __hash__
            explorer.Next()
            
        return out.values()

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

    def Length(self):
        raise NotImplementedError
        
    def _apply_transform(self,T):
        
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
                             (endVector - startVector).toAx()),
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
        return Shape.cast(self.wrapped.copy())

    def transformShape(self, tMatrix):
        """
            tMatrix is a matrix object.
            returns a copy of the ojbect, transformed by the provided matrix,
            with all objects keeping their type
        """
        tmp = self.wrapped.copy()
        tmp.transformShape(tMatrix)
        r = Shape.cast(tmp)
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
        tmp = self.wrapped.copy()
        tmp = tmp.transformGeometry(tMatrix)
        return Shape.cast(tmp)

    def __hash__(self):
        return self.hashCode()


class Vertex(Shape):
    """
    A Single Point in Space
    """

    def __init__(self, obj, forConstruction=False):
        """
            Create a vertex from a FreeCAD Vertex
        """
        super(Vertex,self).__init__(obj)

        self.forConstruction = forConstruction
        self.X, self.Y, self.Y = self.toTuple()

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
    def makeVertex(cls,x,y,z):
        
        return cls(BRepBuilderAPI_MakeVertex(gp_Pnt(x,y,z)
                                            ).Vertex())


class Edge(Shape):
    """
    A trimmed curve that represents the border of a face
    """

    def __init__(self, obj):
        """
            An Edge
        """
        super(Edge,self).__init__(obj)
        

        self.edgetypes = {
            FreeCADPart.Line: 'LINE',
            FreeCADPart.ArcOfCircle: 'ARC',
            FreeCADPart.Circle: 'CIRCLE'
        }

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
            umid = 0.5*(umin+umax)
        
        curve_props = BRepLProp_CLProps(curve, 2, curve.Tolerance) #TODO what are good parameters for those?
        curve_props.SetParameter(umid)
        
        if curve_props.IsTangentDefined():
            dir_handle = gp_Dir() #this is awkward due to C++ pass by ref in the API
            curve_props.Tangent(dir_handle)
            
            return Vector(dir_handle)

    @classmethod
    def makeCircle(cls, radius, pnt=(0, 0, 0), dir=(0, 0, 1), angle1=360.0, angle2=360):
        """
        
        """
        circle_gp = gp_Circ(gp_Ax2(gp_Pnt(*pnt),
                                   gp_Dir(*dir)),
                            radius)
                            
        if angle1 == angle2: #full circle case
            return cls(BRepBuilderAPI_MakeEdge(circle_gp).Edge())
        else: #arc case
            circle_geom = GC_MakeArcOfCircle(circle_gp,
                                             angle1*DEG2RAD,
                                             angle2*DEG2RAD,
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
        pnts = TColgp_Array1OfPnt(0,len(listOfVector)-1)
        for ix,v in enumerate(listOfVector): pnts.SetValue(ix,v.toPnt())

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


class Wire(Shape):
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
        return Shape.cast(FreeCADPart.Wire([w.wrapped for w in listOfWires]))

    @classmethod
    def assembleEdges(cls, listOfEdges):
        """
            Attempts to build a wire that consists of the edges in the provided list
            :param cls:
            :param listOfEdges: a list of Edge objects
            :return: a wire with the edges assembled
        """
        fCEdges = [a.wrapped for a in listOfEdges]

        wa = Wire(FreeCADPart.Wire(fCEdges))
        return wa

    @classmethod
    def makeCircle(cls, radius, center, normal):
        """
            Makes a Circle centered at the provided point, having normal in the provided direction
            :param radius: floating point radius of the circle, must be > 0
            :param center: vector representing the center of the circle
            :param normal: vector representing the direction of the plane the circle should lie in
            :return:
        """
        w = Wire(FreeCADPart.Wire([FreeCADPart.makeCircle(radius, center.wrapped, normal.wrapped)]))
        return w

    @classmethod
    def makePolygon(cls, listOfVertices, forConstruction=False):
        # convert list of tuples into Vectors.
        w = Wire(FreeCADPart.makePolygon([i.wrapped for i in listOfVertices]))
        w.forConstruction = forConstruction
        return w

    @classmethod
    def makeHelix(cls, pitch, height, radius, angle=360.0):
        """
        Make a helix with a given pitch, height and radius
        By default a cylindrical surface is used to create the helix. If
        the fourth parameter is set (the apex given in degree) a conical surface is used instead'
        """
        return Wire(FreeCADPart.makeHelix(pitch, height, radius, angle))

    def clean(self):
        """This method is not implemented yet."""
        return self

class Face(Shape):
    """
    a bounded surface that represents part of the boundary of a solid
    """
    def __init__(self, obj):

        super(Face,self).__init__(obj)

        self.facetypes = {
            # TODO: bezier,bspline etc
            FreeCADPart.Plane: 'PLANE',
            FreeCADPart.Sphere: 'SPHERE',
            FreeCADPart.Cone: 'CONE'
        }


    def geomType(self):
        t = type(self.wrapped.Surface)
        if self.facetypes.has_key(t):
            return self.facetypes[t]
        else:
            return "Unknown Face Surface Type: %s" % str(t)

    def normalAt(self, locationVector=None):
        """
            Computes the normal vector at the desired location on the face.

            :returns: a  vector representing the direction
            :param locationVector: the location to compute the normal at. If none, the center of the face is used.
            :type locationVector: a vector that lies on the surface.
        """
        if locationVector == None:
            locationVector = self.Center()
        (u, v) = self.wrapped.Surface.parameter(locationVector.wrapped)

        return Vector(self.wrapped.normalAt(u, v).normalize())

    @classmethod
    def makePlane(cls, length, width, basePnt=(0, 0, 0), dir=(0, 0, 1)):
        basePnt = Vector(basePnt)
        dir = Vector(dir)
        return Face(FreeCADPart.makePlane(length, width, basePnt.wrapped, dir.wrapped))

    @classmethod
    def makeRuledSurface(cls, edgeOrWire1, edgeOrWire2, dist=None):
        """
        'makeRuledSurface(Edge|Wire,Edge|Wire) -- Make a ruled surface
        Create a ruled surface out of two edges or wires. If wires are used then
        these must have the same
        """
        return Shape.cast(FreeCADPart.makeRuledSurface(edgeOrWire1.obj, edgeOrWire2.obj, dist))

    def cut(self, faceToCut):
        "Remove a face from another one"
        return Shape.cast(self.obj.cut(faceToCut.obj))

    def fuse(self, faceToJoin):
        return Shape.cast(self.obj.fuse(faceToJoin.obj))

    def intersect(self, faceToIntersect):
        """
        computes the intersection between the face and the supplied one.
        The result could be a face or a compound of faces
        """
        return Shape.cast(self.obj.common(faceToIntersect.obj))


class Shell(Shape):
    """
    the outer boundary of a surface
    """

    @classmethod
    def makeShell(cls, listOfFaces):
        return Shell(FreeCADPart.makeShell([i.obj for i in listOfFaces]))


class Solid(Shape):
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
        return Shape.cast(FreeCADPart.makeBox(length, width, height, pnt.wrapped, dir.wrapped))

    @classmethod
    def makeCone(cls, radius1, radius2, height, pnt=Vector(0, 0, 0), dir=Vector(0, 0, 1), angleDegrees=360):
        """
        Make a cone with given radii and height
        By default pnt=Vector(0,0,0),
        dir=Vector(0,0,1) and angle=360'
        """
        return Shape.cast(FreeCADPart.makeCone(radius1, radius2, height, pnt.wrapped, dir.wrapped, angleDegrees))

    @classmethod
    def makeCylinder(cls, radius, height, pnt=Vector(0, 0, 0), dir=Vector(0, 0, 1), angleDegrees=360):
        """
        makeCylinder(radius,height,[pnt,dir,angle]) --
        Make a cylinder with a given radius and height
        By default pnt=Vector(0,0,0),dir=Vector(0,0,1) and angle=360'
        """
        return Shape.cast(FreeCADPart.makeCylinder(radius, height, pnt.wrapped, dir.wrapped, angleDegrees))

    @classmethod
    def makeTorus(cls, radius1, radius2, pnt=None, dir=None, angleDegrees1=None, angleDegrees2=None):
        """
        makeTorus(radius1,radius2,[pnt,dir,angle1,angle2,angle]) --
        Make a torus with agiven radii and angles
        By default pnt=Vector(0,0,0),dir=Vector(0,0,1),angle1=0
        ,angle1=360 and angle=360'
        """
        return Shape.cast(FreeCADPart.makeTorus(radius1, radius2, pnt, dir, angleDegrees1, angleDegrees2))

    @classmethod
    def sweep(cls, profileWire, pathWire):
        """
        make a solid by sweeping the profileWire along the specified path
        :param cls:
        :param profileWire:
        :param pathWire:
        :return:
        """
        # needs to use freecad wire.makePipe or makePipeShell
        # needs to allow free-space wires ( those not made from a workplane )

    @classmethod
    def makeLoft(cls, listOfWire, ruled=False):
        """
            makes a loft from a list of wires
            The wires will be converted into faces when possible-- it is presumed that nobody ever actually
            wants to make an infinitely thin shell for a real FreeCADPart.
        """
        # the True flag requests building a solid instead of a shell.

        return Shape.cast(FreeCADPart.makeLoft([i.wrapped for i in listOfWire], True, ruled))

    @classmethod
    def makeWedge(cls, xmin, ymin, zmin, z2min, x2min, xmax, ymax, zmax, z2max, x2max, pnt=None, dir=None):
        """
        Make a wedge located in pnt
        By default pnt=Vector(0,0,0) and dir=Vector(0,0,1)
        """
        return Shape.cast(
            FreeCADPart.makeWedge(xmin, ymin, zmin, z2min, x2min, xmax, ymax, zmax, z2max, x2max, pnt, dir))

    @classmethod
    def makeSphere(cls, radius, pnt=None, dir=None, angleDegrees1=None, angleDegrees2=None, angleDegrees3=None):
        """
        Make a sphere with a given radius
        By default pnt=Vector(0,0,0), dir=Vector(0,0,1), angle1=0, angle2=90 and angle3=360
        """
        return Shape.cast(FreeCADPart.makeSphere(radius, pnt.wrapped, dir.wrapped, angleDegrees1, angleDegrees2, angleDegrees3))

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

        # from this point down we are dealing with FreeCAD wires not cad.wires
        startWires = [outerWire.wrapped] + [i.wrapped for i in innerWires]
        endWires = []
        p1 = vecCenter.wrapped
        p2 = vecCenter.add(vecNormal).wrapped

        # make translated and rotated copy of each wire
        for w in startWires:
            w2 = w.copy()
            w2.translate(vecNormal.wrapped)
            w2.rotate(p1, p2, angleDegrees)
            endWires.append(w2)

        # make a ruled surface for each set of wires
        sides = []
        for w1, w2 in zip(startWires, endWires):
            rs = FreeCADPart.makeRuledSurface(w1, w2)
            sides.append(rs)

        #make faces for the top and bottom
        startFace = FreeCADPart.Face(startWires)
        endFace = FreeCADPart.Face(endWires)

        #collect all the faces from the sides
        faceList = [startFace]
        for s in sides:
            faceList.extend(s.Faces)
        faceList.append(endFace)

        shell = FreeCADPart.makeShell(faceList)
        solid = FreeCADPart.makeSolid(shell)
        return Shape.cast(solid)

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
        #the work around is to extrude each and then join the resulting solids, which seems to work

        #FreeCAD allows this in one operation, but others might not
        freeCADWires = [outerWire.wrapped]
        for w in innerWires:
            freeCADWires.append(w.wrapped)

        f = FreeCADPart.Face(freeCADWires)
        result = f.extrude(vecNormal.wrapped)

        return Shape.cast(result)

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
        freeCADWires = [outerWire.wrapped]

        for w in innerWires:
            freeCADWires.append(w.wrapped)

        f = FreeCADPart.Face(freeCADWires)

        rotateCenter = FreeCAD.Base.Vector(axisStart)
        rotateAxis = FreeCAD.Base.Vector(axisEnd)

        #Convert our axis end vector into to something FreeCAD will understand (an axis specification vector)
        rotateAxis = rotateCenter.sub(rotateAxis)

        #FreeCAD wants a rotation center and then an axis to rotate around rather than an axis of rotation
        result = f.revolve(rotateCenter, rotateAxis, angleDegrees)

        return Shape.cast(result)

    @classmethod
    def sweep(cls, outerWire, innerWires, path, makeSolid=True, isFrenet=False):
        """
        Attempt to sweep the list of wires  into a prismatic solid along the provided path

        :param outerWire: the outermost wire
        :param innerWires: a list of inner wires
        :param path: The wire to sweep the face resulting from the wires over
        :return: a Solid object
        """

        # FreeCAD allows this in one operation, but others might not
        freeCADWires = [outerWire.wrapped]
        for w in innerWires:
            freeCADWires.append(w.wrapped)

        # f = FreeCADPart.Face(freeCADWires)
        wire = FreeCADPart.Wire([path.wrapped])
        result = wire.makePipeShell(freeCADWires, makeSolid, isFrenet)

        return Shape.cast(result)

    def tessellate(self, tolerance):
        return self.wrapped.tessellate(tolerance)

    def intersect(self, toIntersect):
        """
        computes the intersection between this solid and the supplied one
        The result could be a face or a compound of faces
        """
        return Shape.cast(self.wrapped.common(toIntersect.wrapped))

    def cut(self, solidToCut):
        "Remove a solid from another one"
        return Shape.cast(self.wrapped.cut(solidToCut.wrapped))

    def fuse(self, solidToJoin):
        return Shape.cast(self.wrapped.fuse(solidToJoin.wrapped))

    def clean(self):
        """Clean faces by removing splitter edges."""
        r = self.wrapped.removeSplitter()
        # removeSplitter() returns a generic Shape type, cast to actual type of object
        r = FreeCADPart.cast_to_shape(r)
        return Shape.cast(r)

    def fillet(self, radius, edgeList):
        """
        Fillets the specified edges of this solid.
        :param radius: float > 0, the radius of the fillet
        :param edgeList:  a list of Edge objects, which must belong to this solid
        :return: Filleted solid
        """
        nativeEdges = [e.wrapped for e in edgeList]
        return Shape.cast(self.wrapped.makeFillet(radius, nativeEdges))

    def chamfer(self, length, length2, edgeList):
        """
        Chamfers the specified edges of this solid.
        :param length: length > 0, the length (length) of the chamfer
        :param length2: length2 > 0, optional parameter for asymmetrical chamfer. Should be `None` if not required.
        :param edgeList:  a list of Edge objects, which must belong to this solid
        :return: Chamfered solid
        """
        nativeEdges = [e.wrapped for e in edgeList]
        # note: we prefer 'length' word to 'radius' as opposed to FreeCAD's API
        if length2:
            return Shape.cast(self.wrapped.makeChamfer(length, length2, nativeEdges))
        else:
            return Shape.cast(self.wrapped.makeChamfer(length, nativeEdges))

    def shell(self, faceList, thickness, tolerance=0.0001):
        """
            make a shelled solid of given  by removing the list of faces

        :param faceList: list of face objects, which must be part of the solid.
        :param thickness: floating point thickness. positive shells outwards, negative shells inwards
        :param tolerance: modelling tolerance of the method, default=0.0001
        :return: a shelled solid

            **WARNING**  The underlying FreeCAD implementation can very frequently have problems
            with shelling complex geometries!
        """
        nativeFaces = [f.wrapped for f in faceList]
        return Shape.cast(self.wrapped.makeThickness(nativeFaces, thickness, tolerance))


class Compound(Shape):
    """
    a collection of disconnected solids
    """

    def Center(self):
        return self.Center()

    @classmethod
    def makeCompound(cls, listOfShapes):
        """
        Create a compound out of a list of shapes
        """
        solids = [s.wrapped for s in listOfShapes]
        c = FreeCADPart.Compound(solids)
        return Shape.cast(c)

    def fuse(self, toJoin):
        return Shape.cast(self.wrapped.fuse(toJoin.wrapped))

    def tessellate(self, tolerance):
        return self.wrapped.tessellate(tolerance)

    def clean(self):
        """This method is not implemented yet."""
        return self