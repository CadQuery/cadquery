.. _freefuncapi:

*****************
Free function API
*****************

.. warning:: The free function API is experimental and may change.

For situations when more freedom in crating individaul objects is required a free function API is provided.
This API has no hidden state, but may result in more verbose code. One can still use selectors as methods, but all other operations are implemented as free functions.
Placement of objects and cration of patterns can be achieved using

Tutorial
--------

The purpose of this section is to demonstrate how to construct Shape objects using the free function API.


.. cadquery::
    :height: 600px

    from cadquery.occ_impl.shapes import *

    dh = 1
    r = 1

    # construct edges
    edge1 = circle(r)
    edge2 = circle(2*r).moved(z=dh)
    edge3 = circle(r).moved(z=1.5*dh)

    # loft the side face
    side = loft(edge1, edge2, edge3)

    # bottom face
    bottom = fill(side.edges('<Z'))

    # top face with continous curvature
    top = cap(side.edges('>Z'), side, [(0,0,1.75*dh)])

    # assemble into a solid
    s = solid(side, bottom, top)

    # construct the final result
    result = s.moved(Location(-3*r, 0, 0), Locations(3*r, 0, 0))


The code above builts non-trivial object by sequentially constructing individual faces, assembling them into a solid and finally generating a pattern.