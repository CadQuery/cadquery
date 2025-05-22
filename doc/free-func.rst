

*****************
Free function API
*****************

.. warning:: The free function API is experimental and may change.

For situations when more freedom in crafting individual objects is required, a free function API is provided.
This API has no hidden state, but may result in more verbose code. One can still use selectors as methods, but all other operations are implemented as free functions.
Placement of objects and creation of patterns can be achieved using the various overloads of the moved method.

Currently this documentation is incomplete, more examples can be found in the tests.

Tutorial
--------

The purpose of this section is to demonstrate how to construct Shape objects using the free function API.


.. cadquery::
    :height: 600px

    from cadquery.func import *

    dh = 2
    r = 1

    # construct edges
    edge1 = circle(r)
    edge2 = circle(1.5*r).moved(z=dh)
    edge3 = circle(r).moved(z=1.5*dh)

    # loft the side face
    side = loft(edge1, edge2, edge3)

    # bottom face
    bottom = fill(side.edges('<Z'))

    # top face with continuous curvature
    top = cap(side.edges('>Z'), side, [(0,0,1.6*dh)])

    # assemble into a solid
    s = solid(side, bottom, top)

    # construct the final result
    result = s.moved((-3*r, 0, 0), (3*r, 0, 0))


The code above builds a non-trivial object by sequentially constructing individual faces, assembling them into a solid and finally generating a pattern.

It begins with defining few edges.

.. code-block:: python

    edge1 = circle(r)
    edge2 = circle(2*r).moved(z=dh)
    edge3 = circle(r).moved(z=1.5*dh)


Those edges are used to create the side faces of the final solid using :meth:`~cadquery.occ_impl.shapes.loft`.

.. code-block:: python

    side = loft(edge1, edge2, edge3)

Once the side is there, :meth:`~cadquery.occ_impl.shapes.cap` and :meth:`~cadquery.occ_impl.shapes.fill` are used to define the top and bottom faces.
Note that :meth:`~cadquery.occ_impl.shapes.cap` tries to maintain curvature continuity with respect to the context shape. This is not the case for :meth:`~cadquery.occ_impl.shapes.fill`.

.. code-block:: python

    # bottom face
    bottom = fill(side.edges('<Z'))

    # top face with continuous curvature
    top = cap(side.edges('>Z'), side, [(0,0,1.75*dh)])

Next, all the faces are assembled into a solid.

.. code-block:: python

    s = solid(side, bottom, top)

Finally, the solid is duplicated and placed in the desired locations creating the final compound object. Note various usages of :meth:`~cadquery.Shape.moved`.

.. code-block:: python

    result = s.moved((-3*r, 0, 0), (3*r, 0, 0))

In general all the operations are implemented as free functions, with the exception of placement and selection which are strictly related to a specific shape.


Primitives
----------

Various 1D, 2D and 3D primitives are supported.

.. cadquery::

    from cadquery.func import *

    e = segment((0,0), (0,1))

    c = circle(1)

    f = plane(1, 1.5)

    b = box(1, 1, 1)

    result = compound(e, c.move(2), f.move(4), b.move(6))


Boolean operations
------------------

Boolean operations are supported and implemented as operators and free functions.
In general boolean operations are slow and it is advised to avoid them and not to perform the in a loop.
One can for example union multiple solids at once by first combining them into a compound.

.. cadquery::

    from cadquery.func import *

    c1 = cylinder(1, 2)
    c2 = cylinder(0.5, 3)

    f1 = plane(2, 2).move(z=1)
    f2 = plane(1, 1).move(z=1)

    e1 = segment((0,-2.5, 1), (0,2.5,1))

    # union
    r1 = c2 + c1
    r2 = fuse(f1, f2)

    # difference
    r3 = c1 - c2
    r4 = cut(f1, f2)

    # intersection
    r5 = c1*c2
    r6 = intersect(f1, f2)

    # splitting
    r7 = (c1 / f1).solids('<Z')
    r8 = split(f2, e1).faces('<X')

    results = (r1, r2, r3, r4, r5, r6, r7, r8)
    result = compound([el.moved(2*i) for i,el in enumerate(results)])

Note that bool operations work on 2D shapes as well.


Shape construction
------------------

Constructing complex shapes from simple shapes is possible in various contexts.

.. cadquery::

    from cadquery.func import *

    e1 = segment((0,0), (1,0))
    e2 = segment((1,0), (1,1))

    # wire from edges
    r1 = wire(e1, e2)

    c1 = circle(1)

    # face from a planar wire
    r2 = face(c1)

    # solid from faces
    f1 = plane(1,1)
    f2 = f1.moved(z=1)
    f3 = extrude(f1.wires(), (0,0,1))

    r3 = solid(f1,f2,*f3)

    # compound from shapes
    s1 = circle(1).moved(ry=90)
    s2 = plane(1,1).move(rx=90).move(y=2)
    s3 = cone(1,1.5).move(y=4)

    r4 = compound(s1, s2, s3)

    results = (r1, r2, r3, r4,)
    result = compound([el.moved(2*i) for i,el in enumerate(results)])


Operations
----------

Free function API currently supports :meth:`~cadquery.occ_impl.shapes.extrude`, :meth:`~cadquery.occ_impl.shapes.loft`, :meth:`~cadquery.occ_impl.shapes.revolve` and :meth:`~cadquery.occ_impl.shapes.sweep` operations.

.. cadquery::

    from cadquery.func import *

    r = rect(1,0.5)
    f = face(r, circle(0.2).moved(0.2), rect(0.2, 0.4).moved(-0.2))
    c = circle(0.2)
    p = spline([(0,0,0), (0,-1,2)], [(0,0,1), (0,-1,1)])

    # extrude
    s1 = extrude(r, (0,0,2))
    s2 = extrude(fill(r), (0,0,1))

    # sweep
    s3 = sweep(r, p)
    s4 = sweep(f, p)

    # loft
    s5 = loft(r, c.moved(z=2))
    s6 = loft(r, c.moved(z=1), cap=True)\

    # revolve
    s7 = revolve(fill(r), (0.5, 0, 0), (0, 1, 0), 90)

    results = (s1, s2, s3, s4, s5, s6, s7)
    result = compound([el.moved(2*i) for i,el in enumerate(results)])


Placement
---------

Placement and creation of arrays is possible using :meth:`~cadquery.Shape.move` and :meth:`~cadquery.Shape.moved`.

.. cadquery::

    from cadquery.func import *

    locs = [(0,-1,0), (0,1,0)]

    s = sphere(1).moved(locs)
    c = cylinder(1,2).move(rx=15).moved(*locs)

    result = compound(s, c.moved(2))

Text
----

The free function API has extensive text creation capabilities including text on
planar curves and text on surfaces.


.. cadquery::

    from cadquery.func import *

    from math import pi

    # parameters
    D = 5
    H = 2*D
    S = H/10
    TH = S/10
    TXT = "CadQuery"

    # base and spine
    c = cylinder(D, H).moved(rz=-135)
    cf = c.faces("%CYLINDER")
    spine = (c*plane().moved(z=D)).edges().trim(pi/2, pi)

    # planar
    r1 = text(TXT, 1, spine, planar=True).moved(z=-S)

    # normal
    r2 = text(TXT, 1, spine)

    # projected
    r3 = text(TXT, 1, spine, cf).moved(z=S)

    # projected and thickened
    r4 = offset(r3, TH).moved(z=S)

    result = compound(r1, r2, r3, r4)


Adding features manually
------------------------

In certain cases it is desirable to add features such as holes or protrusions manually.
E.g., for complicated shapes it might be beneficial performance-wise because it
avoids boolean operations. One can add or remove faces, add holes to existing faces
and last but not least reconstruct existing solids. 

.. cadquery::
    
    from cadquery.func import *
    
    w = 1
    r = 0.9*w/2
    
    # box
    b = box(w, w, w)
    # bottom face
    b_bot = b.faces('<Z')
    # top faces
    b_top = b.faces('>Z')
    
    # inner face 
    inner = extrude(circle(r), (0,0,w))
    
    # add holes to the bottom and top face
    b_bot_hole = b_bot.addHole(inner.edges('<Z'))
    b_top_hole = b_top.addHole(inner.edges('>Z'))
    
    # construct the final solid
    result = solid(
        b.remove(b_top, b_bot).faces(), #side faces
        b_bot_hole, # bottom with a hole
        inner, # inner cylinder face
        b_top_hole, # top with a hole
    )

If the base shape is more complicated, it is possible to use local sewing that
takes into account on indicated elements of the context shape. This, however,
necessitates a two step approach - first a shell needs to be explicitly sewn
and only then the final solid can be constructed.

.. cadquery::

    from cadquery.func import *
    
    w = 1
    h = 0.1
    r = 0.9*w/2
    
    # box
    b = box(w, w, w)
    # top face
    b_top = b.faces('>Z')
    
    # protrusion
    feat_side = extrude(circle(r).moved(b_top.Center()), (0,0,h))
    feat_top = face(feat_side.edges('>Z'))
    feat = shell(feat_side, feat_top) # sew into a shell
    
    # add hole to the box
    b_top_hole = b_top.addHole(feat.edges('<Z'))
    b = b.replace(b_top, b_top_hole)
    
    # local sewing - only two faces are taken into account
    sh = shell(b_top_hole, feat.faces('<Z'), ctx=(b, feat))
    # construct the final solid
    result = solid(sh)


Mapping onto parametric space
-----------------------------

To complement functionalities described, it is possible to trim edges and faces explicitly using simple rectangular
trims, polygons, splines or arbitrary wires.

.. cadquery::

    from math import pi
    from cadquery.func import cylinder, edgeOn, compound, wire

    # parameters
    d = 1.5
    h = 3
    du = pi
    Nturns = 2

    # construct the base surface
    base = cylinder(d, h).faces("%CYLINDER")

    # rectangular trim
    r1 = base.trim(-pi/2, 0, 0, h/3)

    # polyline trim
    r2 = base.trim((0,0), (pi,0), (pi/2, h/2))

    # construct a pcurve
    pcurve = edgeOn(base, [(pi/2, h/4), (pi, h/4), (pi, h/2), (pi/2, h/2)], periodic=True)

    # pcurve trim
    r3 = base.trim(wire(pcurve))

    result = compound(r1, r2.moved(x=2), r3.moved(x=4))


This in principle allows to model arbitrary shapes in the parametric domain, but often it is more desirable
to work with higher level objects like wires.


.. cadquery::

    from cadquery.func import cylinder, loft, wireOn, segment
    from math import pi

    # parameters
    d = 1.5
    h = 3
    du = pi
    Nturns = 2

    # construct the base surface
    base = cylinder(d, h).faces("%CYLINDER")

    # construct a planar 2D patch for u,v trimming
    uv_patch = loft(
        segment((0, 0), (du, 0)), segment((Nturns * 2 * pi, h), (Nturns * 2 * pi + du, h))
    )

    # map it onto the cylinder
    w = wireOn(base, uv_patch)

    # check that the pcurves were created
    for e in w:
        assert e.hasPCurve(base), "No p-curve on base present"

    # trim the base surface
    result = base.trim(w)


Finally, it is also possible to map complete faces.


.. cadquery::

    from cadquery.func import sphere, text, faceOn

    base = sphere(5).faces()

    result = faceOn(base, text("CadQuery", 1))


