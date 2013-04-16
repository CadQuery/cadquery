"""
	Copyright (C) 2011-2013  Parametric Products Intellectual Holdings, LLC

	This file is part of CadQuery.
	
	CadQuery is free software; you can redistribute it and/or
	modify it under the terms of the GNU Lesser General Public
	License as published by the Free Software Foundation; either
	version 2.1 of the License, or (at your option) any later version.

	CadQuery is distributed in the hope that it will be useful,
	but WITHOUT ANY WARRANTY; without even the implied warranty of
	MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
	Lesser General Public License for more details.

	You should have received a copy of the GNU Lesser General Public
	License along with this library; If not, see <http://www.gnu.org/licenses/>
"""

class CQContext(object):
    """
        A shared context for modeling.

        All objects in the same CQ chain share a reference to this same object instance
        which allows for shared state when needed,
    """
    def __init__(self):
        self.pendingWires = []   #a list of wires that have been created and need to be extruded
        self.pendingEdges = []   #a list of pending edges that have been created and need to be joined into wires
        self.firstPoint = None    #a reference to the first point for a set of edges. used to determine how to behave when close() is called
        self.tolerance = 0.0001  #user specified tolerance

class CQ(object):
    """
    Provides enhanced functionality for a wrapped CAD primitive.

    Examples include feature selection, feature creation, 2d drawing
    using work planes, and 3d opertations like fillets, shells, and splitting
    """

    def __init__(self,obj):
        """
        Construct a new cadquery (CQ) object that wraps a CAD primitive.

        :param obj: Object to Wrap.
        :type obj: A CAD Primitive ( wire,vertex,face,solid,edge )
        """
        self.objects = []
        self.ctx = CQContext()
        self.parent = None

        if obj: #guarded because sometimes None for internal use
            self.objects.append(obj)

    def newObject(self,objlist):
        """
        Make a new CQ object.

        :param objlist: The stack of objects to use
        :param newContextSolid: an optional new solid to become the new context solid

        :type objlist: a list of CAD primitives ( wire,face,edge,solid,vertex,etc )

        The parent of the new object will be set to the current object,
        to preserve the chain correctly.

        Custom plugins and subclasses should use this method to create new CQ objects
        correctly.
        """
        r = CQ(None) #create a completely blank one
        r.parent = self
        r.ctx = self.ctx #context solid remains the same
        r.objects = list(objlist)
        return r

    def _collectProperty(self,propName):
        """
            Collects all of the values for propName,
            for all items on the stack.
            FreeCAD objects do not implement id correclty,
            so hashCode is used to ensure we dont add the same
            object multiple times.

            One weird use case is that the stack could have a solid reference object
            on it.  This is meant to be a reference to the most recently modified version
            of the context solid, whatever it is.
        """
        all = {}
        for o in self.objects:

            #tricky-- if an object is a compound of solids,
            #do not return all of the solids underneath-- typically
            #then we'll keep joining to ourself
            if propName == 'Solids' and isinstance(o, Solid) and o.ShapeType() =='Compound':
                for i in getattr(o,'Compounds')():
                    all[i.hashCode()] = i
            else:
                if hasattr(o,propName):
                    for i in getattr(o,propName)():
                        all[i.hashCode()] = i

        return list(all.values())

    def split(self,keepTop=False,keepBottom=False):
        """
            Splits a solid on the stack into two parts, optionally keeping the separate parts.

            :param boolean keepTop: True to keep the top, False or None to discard it
            :param boolean keepBottom: True to keep the bottom, False or None to discard it
            :raises: ValueError if keepTop and keepBottom are both false.
            :raises: ValueError if there is not a solid in the current stack or the parent chain
            :returns: CQ object with the desired objects on the stack.

            The most common operation splits a solid and keeps one half. This sample creates  split bushing::

                #drill a hole in the side
                c = Workplane().box(1,1,1).faces(">Z").workplane().circle(0.25).cutThruAll()F
                #now cut it in half sideways
                c.faces(">Y").workplane(-0.5).split(keepTop=True)

        """

        solid = self.findSolid()

        if (not keepTop) and (not keepBottom):
            raise ValueError("You have to keep at least one half")

        maxDim = solid.BoundingBox().DiagonalLength * 10.0
        topCutBox = self.rect(maxDim,maxDim)._extrude(maxDim)
        bottomCutBox = self.rect(maxDim,maxDim)._extrude(-maxDim)

        top = solid.cut(bottomCutBox)
        bottom = solid.cut(topCutBox)

        if keepTop and keepBottom:
            #put both on the stack, leave original unchanged
            return self.newObject([top,bottom])
        else:
            # put the one we are keeping on the stack, and also update the context solid
            #to the one we kept
            if keepTop:
                solid.wrapped = top.wrapped
                return self.newObject([top])
            else:
                solid.wrapped = bottom.wrapped
                return self.newObject([bottom])


    def combineSolids(self,otherCQToCombine=None):
        """
            !!!DEPRECATED!!! use union()
            Combines all solids on the current stack, and any context object, together
            into a single object.

            After the operation, the returned solid is also the context solid.

            :param otherCQToCombine: another cadquery to combine.
            :return: a cQ object with the resulting combined solid on the stack.

            Most of the time, both objects will contain a single solid, which is
            combined and returned on the stack of the new object.

        """
        #loop through current stack objects, and combine them
        #TODO: combine other types of objects as well, like edges and wires
        toCombine = self.solids().vals()

        if otherCQToCombine:
            for obj in otherCQToCombine.solids().vals():
                toCombine.append(obj)

        if len(toCombine) < 1:
            raise ValueError("Cannot Combine: at least one solid required!")

        #get context solid
        ctxSolid = self.findSolid(searchStack=False,searchParents=True) #we dont want to find our own objects

        if ctxSolid is None:
            ctxSolid = toCombine.pop(0)

        #now combine them all. make sure to save a reference to the ctxSolid pointer!
        s = ctxSolid
        for tc in toCombine:
            s = s.fuse(tc)

        ctxSolid.wrapped = s.wrapped
        return self.newObject([s])

    def all(self):
        """
        Return a list of all CQ objects on the stack.

        useful when you need to operate on the elements
        individually.

        Contrast with vals, which returns the underlying
        objects for all of the items on the stack

        """
        return [self.newObject([o]) for o in self.objects]

    def size(self):
        """
         Return the number of objects currently on the stack

        """
        return len(self.objects)

    def vals(self):
        """
        get the values in the current list

        :rtype: list of FreeCAD objects
        :returns: the values of the objects on the stack.

        Contrast with :py:meth:`all`, which returns CQ objects for all of the items on the stack

        """
        res = []
        return self.objects

    def add(self,obj):
        """
            adds an object or a list of objects to the stack


            :param obj: an object to add
            :type obj: a CQ object, CAD primitive, or list of CAD primitives
            :return: a CQ object with the requested operation performed

            If an CQ object, the values of that object's stack are added. If a list of cad primitives,
            they are all added. If a single CAD primitive it is added

            Used in rare cases when you need to combine the results of several CQ results
            into a single CQ object. Shelling is one common example

        """
        if type(obj) == list:
            self.objects.extend(obj)
        elif type(obj) == CQ or type(obj) == Workplane:
            self.objects.extend(obj.objects)
        else:
            self.objects.append(obj)
        return self

    def val(self):
        """
        Return the first value on the stack

        :return: the first value on the stack.
        :rtype: A FreeCAD object or a SolidReference
        """
        return self.objects[0]



    def workplane(self,offset=0.0,invert=False):
        """

        Creates a new 2-D workplane, located relative to the first face on the stack.

        :param offset:  offset for the work plane in the Z direction. Default
        :param invert:  invert the Z direction from that of the face.
        :type offset: float or None=0.0
        :type invert: boolean or None=False
        :rtype: Workplane object ( which is a subclass of CQ )

        The first element on the stack must be a face, or a vertex.  If a vertex, then the parent item on the
        chain immediately before the vertex must be a face.

        The result will be a 2-d working plane
        with a new coordinate system set up as follows:

           * The origin will be located in the *center* of the face, if a face was selected. If a vertex was
             selected, the origin will be at the vertex, and located on the face.
           * The Z direction will be normal to the plane of the face,computed
             at the center point.
           * The X direction will be parallel to the x-y plane. If the workplane is  parallel to the global
             x-y plane, the x direction of the workplane will co-incide with the global x direction.

        Most commonly, the selected face will be planar, and the workplane lies in the same plane
        of the face ( IE, offset=0).  Occasionally, it is useful to define a face offset from
        an existing surface, and even more rarely to define a workplane based on a face that is not planar.

        To create a workplane without first having a face, use the Workplane() method.

        Future Enhancements:
          * Allow creating workplane from planar wires
          * Allow creating workplane based on an arbitrary point on a face, not just the center.
            For now you can work around by creating a workplane and then offsetting the center afterwards.

        """
        obj = self.objects[0]

        def _computeXdir(normal):
            xd = Vector(0,0,1).cross(normal)
            if xd.Length < self.ctx.tolerance:
                #this face is parallel with the x-y plane, so choose x to be in global coordinates
                xd = Vector(1,0,0)
            return xd

        faceToBuildOn = None
        center = None
        #if isinstance(obj,Vertex):
        #    f = self.parent.objects[0]
        #    if f != None and isinstance(f,Face):
        #        center = obj.Center()
        #        normal = f.normalAt(center)
        #        xDir = _computeXdir(normal)
        #    else:
        #        raise ValueError("If a vertex is selected, a face must be the immediate parent")
        if isinstance(obj,Face):
            faceToBuildOn = obj
            center = obj.Center()
            normal = obj.normalAt(center)
            xDir = _computeXdir(normal)
        else:
            if hasattr(obj,'Center'):
                center = obj.Center()
                normal = self.plane.zDir
                xDir = self.plane.xDir
            else:
                raise ValueError ("Needs a face or a vertex or point on a work plane")

        #invert if requested
        if invert:
            normal = normal.multiply(-1.0)

        #offset origin if desired
        offsetVector = normal.normalize().multiply(offset)
        offsetCenter = center.add(offsetVector)

        #make the new workplane
        plane = Plane(offsetCenter, xDir, normal)
        s = Workplane(plane)
        s.parent = self
        s.ctx = self.ctx

        #a new workplane has the center of the workplane on the stack
        return s

    def first(self):
        """
        Return the first item on the stack
        :returns: the first item on the stack.
        :rtype: a CQ object
        """
        return self.newObject(self.objects[0:1])

    def item(self,i):
        """

        Return the ith item on the stack.
        :rtype: a CQ object
        """
        return self.newObject([self.objects[i]])

    def last(self):
        """
        Return the last item on the stack.
        :rtype: a CQ object
        """
        return self.newObject([self.objects[-1]])

    def end(self):
        """
        Return the parent of this CQ element
        :rtype: a CQ object
        :raises: ValueError if there are no more parents in the chain.

        For example::

            CQ(obj).faces("+Z").vertices().end()

        will return the same as::

            CQ(obj).faces("+Z")

        """
        if self.parent:
            return self.parent
        else:
            raise ValueError("Cannot End the chain-- no parents!")



    def  findSolid(self,searchStack=True,searchParents=True):
        """
        Finds the first solid object in the chain, searching from the current node
        backwards through parents until one is found.

        :param searchStack: should objects on the stack be searched first.
        :param searchParents: should parents be searched?
        :raises: ValueError if no solid is found in the current object or its parents, and errorOnEmpty is True

        This function is very important for chains that are modifying a single parent object, most often
        a solid.

        Most of the time, a chain defines or selects a solid, and then modifies it using workplanes
        or other operations.

        Plugin Developers should make use of this method to find the solid that should be modified, if the
        plugin implements a unary operation, or if the operation will automatically merge its results with an
        object already on the stack.
        """
        #notfound = ValueError("Cannot find a Valid Solid to Operate on!")

        if searchStack:
            for s in self.objects:
                if type(s) == Solid:
                    return s

        if searchParents and self.parent is not None:
            return self.parent.findSolid(searchStack=True,searchParents=searchParents)

        return None

    def _selectObjects(self,objType,selector=None):
        """
            Filters objects of the selected type with the specified selector,and returns results

            :param objType: the type of object we are searching for
            :type objType: string: (Vertex|Edge|Wire|Solid|Shell|Compound|CompSolid)
            :return: a CQ object with the selected objects on the stack.

            **Implementation Note**: This is the base implmentation of the vertices,edges,faces,solids,shells,
            and other similar selector methods.  It is a useful extension point for plugin developers to make
            other selector methods.
        """
        toReturn = self._collectProperty(objType) #all of the faces from all objects on the stack, in a single list

        if selector is not None:
            if type(selector) == str:
                selectorObj = StringSyntaxSelector(selector)
            else:
                selectorObj = selector
            toReturn = selectorObj.filter(toReturn)

        return self.newObject(toReturn)

    def vertices(self,selector=None):
        """
        Select the vertices of objects on the stack, optionally filtering the selection. If there are multiple objects
        on the stack, the vertices of all objects are collected and a list of all the distinct vertices is returned.

        :param selector:
        :type selector:  None, a Selector object, or a string selector expression.
        :return: a CQ object whos stack contains  the *distinct* vertices of *all* objects on the current stack,
           after being filtered by the selector, if provided

        If there are no vertices for any objects on the current stack, an empty CQ object is returned

        The typical use is to select the vertices of a single object on the stack. For example::

           Workplane().box(1,1,1).faces("+Z").vertices().size()

        returns 4, because the topmost face of cube will contain four vertices. While this::

           Workplane().box(1,1,1).faces().vertices().size()

        returns 8, because a cube has a total of 8 vertices

        **Note** Circles are peculiar, they have a single vertex at the center!

        :py:class:`StringSyntaxSelector`

        """
        return self._selectObjects('Vertices',selector)

    def faces(self,selector=None):
        """
        Select the faces of objects on the stack, optionally filtering the selection. If there are multiple objects
        on the stack, the faces of all objects are collected and a list of all the distinct faces is returned.

        :param selector: A selector
        :type selector:  None, a Selector object, or a string selector expression.
        :return: a CQ object whos stack contains all of the *distinct* faces of *all* objects on the current stack,
            filtered by the provided selector.

        If there are no vertices for any objects on the current stack, an empty CQ object is returned

        The typical use is to select the faces of a single object on the stack. For example::

           CQ(aCube).faces("+Z").size()

        returns 1, because a cube has one face with a normal in the +Z direction. Similarly::

           CQ(aCube).faces().size()

        returns 6, because a cube has a total of 6 faces, And::

            CQ(aCube).faces("|Z").size()

        returns 2, because a cube has 2 faces having normals parallel to the z direction

        See more about selectors HERE
        """
        return self._selectObjects('Faces',selector)

    def edges(self,selector=None):
        """
        Select the edges of objects on the stack, optionally filtering the selection. If there are multiple objects
        on the stack, the edges of all objects are collected and a list of all the distinct edges is returned.

        :param selector: A selector
        :type selector:  None, a Selector object, or a string selector expression.
        :return: a CQ object whos stack contains all of the *distinct* edges of *all* objects on the current stack,
            filtered by the provided selector.

        If there are no edges for any objects on the current stack, an empty CQ object is returned

        The typical use is to select the edges of a single object on the stack. For example::

           CQ(aCube).faces("+Z").edges().size()

        returns 4, because a cube has one face with a normal in the +Z direction. Similarly::

           CQ(aCube).edges().size()

        returns 12, because a cube has a total of 12 edges, And::

            CQ(aCube).edges("|Z").size()

        returns 4, because a cube has 4 edges parallel to the z direction

        See more about selectors HERE
        """
        return self._selectObjects('Edges',selector)

    def wires(self,selector=None):
        """
        Select the wires of objects on the stack, optionally filtering the selection. If there are multiple objects
        on the stack, the wires of all objects are collected and a list of all the distinct wires is returned.

        :param selector: A selector
        :type selector:  None, a Selector object, or a string selector expression.
        :return: a CQ object whos stack contains all of the *distinct* wires of *all* objects on the current stack,
            filtered by the provided selector.

        If there are no wires for any objects on the current stack, an empty CQ object is returned

        The typical use is to select the wires of a single object on the stack. For example::

           CQ(aCube).faces("+Z").wires().size()

        returns 1, because a face typically only has one outer wire

        See more about selectors HERE
        """
        return self._selectObjects('Wires',selector)

    def solids(self,selector=None):
        """
        Select the solids of objects on the stack, optionally filtering the selection. If there are multiple objects
        on the stack, the solids of all objects are collected and a list of all the distinct solids is returned.

        :param selector: A selector
        :type selector:  None, a Selector object, or a string selector expression.
        :return: a CQ object whos stack contains all of the *distinct* solids of *all* objects on the current stack,
            filtered by the provided selector.

        If there are no solids for any objects on the current stack, an empty CQ object is returned

        The typical use is to select the  a single object on the stack. For example::

           CQ(aCube).solids().size()

        returns 1, because a cube consists of one solid.

        It is possible for single CQ object ( or even a single CAD primitive ) to contain multiple solids.

        See more about selectors HERE
        """
        return self._selectObjects('Solids',selector)

    def shells(self,selector=None):
        """
        Select the shells of objects on the stack, optionally filtering the selection. If there are multiple objects
        on the stack, the shells of all objects are collected and a list of all the distinct shells is returned.

        :param selector: A selector
        :type selector:  None, a Selector object, or a string selector expression.
        :return: a CQ object whos stack contains all of the *distinct* solids of *all* objects on the current stack,
            filtered by the provided selector.

        If there are no shells for any objects on the current stack, an empty CQ object is returned

        Most solids will have a single shell, which represents the outer surface. A shell will typically be
        composed of multiple faces.

        See more about selectors HERE
        """
        return self._selectObjects('Shells',selector)

    def compounds(self,selector=None):
        """
        Select compounds on the stack, optionally filtering the selection. If there are multiple objects
        on the stack, they are collected and a list of all the distinct compounds is returned.

        :param selector: A selector
        :type selector:  None, a Selector object, or a string selector expression.
        :return: a CQ object whos stack contains all of the *distinct* solids of *all* objects on the current stack,
            filtered by the provided selector.

        A compound contains multiple CAD primitives that resulted from a single operation, such as a union, cut,
        split, or fillet.  Compounds can contain multiple edges, wires, or solids.

        See more about selectors HERE
        """
        return self._selectObjects('Compounds',selector)

    def toSvg(self,opts=None):
        """
            Returns svg text that represents the first item on the stack.

            for testing purposes.

            :param options: svg formatting options
            :type options: dictionary, width and height
            :return: a string that contains SVG that represents this item.
        """
        return SVGexporter.getSVG(self.val().wrapped,opts)

    def exportSvg(self,fileName):
        """
            Exports the first item on the stack as an SVG file

            For testing purposes mainly.

            :param fileName: the filename to export
            :type fileName: String, absolute path to the file

        """
        SVGexporter.exportSVG(self.val().wrapped,fileName)

    def rotateAboutCenter(self,axisEndPoint,angleDegrees):
        """
            Rotates all items on the stack by the specified angle, about the specified axis

            The center of rotation is a vector starting at the center of the object on the stack,
            and ended at the specified point.

            :param axisEndPoint: the second point of axis of rotation
            :type axisEndPoint: a three-tuple in global coordinates
            :param angleDegrees: the rotation angle, in degrees
            :type angleDegrees: float
            :returns: a CQ object, with all items rotated.

            WARNING: This version returns the same cq object instead of a new one-- the
            old object is not accessible.

            Future Enhancements:
                * A version of this method that returns a transformed copy, rather than modifying
                  the originals
                * This method doesnt expose a very good interface, becaues the axis of rotation
                  could be inconsistent between multiple objects.  This is because the beginning
                  of the axis is variable, while the end is fixed. This is fine when operating on
                  one object, but is not cool for multiple.

        """

        #center point is the first point in the vector
        endVec = Vector(axisEndPoint)

        def _rot(obj):
            startPt = obj.Center()
            endPt = startPt + endVec
            obj.rotate(startPt,endPt,angleDegrees)

        return self.each(_rot,False)

    def translate(self,vec):
        """
            Returns a copy of  all of the items on the stack by the specified distance

            :param tupleDistance: distance to move, in global coordinates
            :type  tupleDistance: a 3-tuple of float
            :returns: a CQ object

            WARNING: the underlying objects are modified, not copied.

            Future Enhancements:
                A version of this method that returns a transformed copy instead
                of modifying the originals.
        """
        return self.newObject([o.translate(vec) for o in self.objects])


    def shell(self,thickness):
        """
            Remove the selected faces to create a shell of the specified thickness.

            To shell, first create a solid, and *in the same chain* select the faces you wish to remove.

            :param thickness: a positive float, representing the thickness of the desired shell. Negative values shell inwards,
                positive values shell outwards.
            :raises: ValueError if the current stack contains objects that are not faces of a solid further
                 up in the chain.
            :returns: a CQ object with the resulting shelled solid selected.

            This example will create a hollowed out unit cube, where the top most face is open,
            and all other walls are 0.2 units thick::

                Workplane().box(1,1,1).faces("+Z").shell(0.2)

            Shelling is one of the cases where you may need to use the add method to select several faces. For
            example, this example creates a 3-walled corner, by removing three faces of a cube::

                s = Workplane().box(1,1,1)
                s1 = s.faces("+Z")
                s1.add(s.faces("+Y")).add(s.faces("+X"))
                self.saveModel(s1.shell(0.2))

            This fairly yucky syntax for selecting multiple faces is planned for improvement

            **Note**:  When sharp edges are shelled inwards, they remain sharp corners, but **outward** shells are
            automatically filleted, because an outward offset from a corner generates a radius


            Future Enhancements:
                Better selectors to make it easier to select multiple faces

        """
        solidRef = self.findSolid()

        for f in self.objects:
            if type(f) != Face:
                raise ValueError ("Shelling requires that faces be selected")

        s = solidRef.shell(self.objects,thickness)
        solidRef.wrapped = s.wrapped
        return self.newObject([s])


    def fillet(self,radius):
        """
            Fillets a solid on the selected edges.

            The edges on the stack are filleted. The solid to which the edges belong must be in the parent chain
            of the selected edges.

            :param radius: the radius of the fillet, must be > zero
            :type radius: positive float
            :raises: ValueError if at least one edge is not selected
            :raises: ValueError if the solid containing the edge is not in the chain
            :returns: cq object with the resulting solid selected.

            This example will create a unit cube, with the top edges filleted::

                s = Workplane().box(1,1,1).faces("+Z").edges().fillet(0.1)
        """
        #TODO: we will need much better edge selectors for this to work
        #TODO: ensure that edges selected actually belong to the solid in the chain, otherwise, fe segfault

        solid = self.findSolid()

        edgeList = self.edges().vals()
        if len(edgeList) < 1:
            raise ValueError ("Fillets requires that edges be selected")

        s = solid.fillet(radius,edgeList)
        solid.wrapped = s.wrapped
        return self.newObject([s])

