"""
    Tests AssembleEdges functionality
"""

import cadquery as cq
from tests import BaseTest

class TestAssembleEdges(BaseTest):
    
    def edge_wire_1(self):   
        # Plate with 5 sides and 2 bumps, one side is not co-planar with the other sides
        thickness = 0.1
        edge_points = [[-7.,-7.,0.], [-3.,-10.,3.], [7.,-7.,0.], [7.,7.,0.], [-7.,7.,0.]]
        edge_wire = cq.Workplane('XY').polyline([(-7.,-7.), (7.,-7.), (7.,7.), (-7.,7.)])
        edge_wire = edge_wire.add(cq.Workplane('YZ').workplane().transformed(offset=cq.Vector(0, 0, -7), rotate=cq.Vector(45, 0, 0)).spline([(-7.,0.), (3,-3), (7.,0.)])) 
        edge_wire = [o.vals()[0] for o in edge_wire.all()]
        edge_wire = cq.Wire.assembleEdges(edge_wire)
        
        return edge_wire


    def edge_wire_2(self):
        # Embossed star, need to change optional parameters to obtain nice looking result.
        r1=3.
        r2=10.
        fn=6
        thickness = 0.1
        edge_points = [[r1*cos(i * pi/fn), r1*sin(i * pi/fn)]    if i%2==0  else   [r2*cos(i * pi/fn), r2*sin(i * pi/fn)]  for i in range(2*fn+1)]
        edge_wire = cq.Workplane('XY').polyline(edge_points)
        edge_wire = [o.vals()[0] for o in edge_wire.all()]
        edge_wire = cq.Wire.assembleEdges(edge_wire)
               
        return edge_wire


    def edge_wire_3(self):
        # Points on hexagonal pattern coordinates, use of pushpoints.
        r1 = 1.
        N = 3
        ca = cos(30. * pi/180.)
        sa = sin(30. * pi/180.)
        # EVEN ROWS
        x_p = np.arange(-N*r1, N*r1, ca*2*r1)
        y_p = np.arange(-N*r1, N*r1, 3*r1)
        x_p, y_p = np.meshgrid(x_p, y_p)
        xy_p_even = [(x,y) for x,y in zip(x_p.flatten(), y_p.flatten())]
        # ODD ROWS
        x_p = np.arange(-(N-0.5)*r1*ca, (N+1.5)*r1*ca, ca*2*r1)
        y_p = np.arange(-(N-2+sa)*r1, (N+1+sa)*r1, 3*r1)
        x_p, y_p = np.meshgrid(x_p, y_p)
        xy_p_odd = [(x,y) for x,y in zip(x_p.flatten(), y_p.flatten())]
        pts = xy_p_even + xy_p_odd
        # Spike surface
        thickness = 0.1
        fn = 6
        edge_points = [[r1*cos(i * 2*pi/fn), r1*sin(i * 2*pi/fn)] for i in range(fn+1)]
        surface_points = [[0.25,0,0.75], [-0.25,0,0.75], [0,0.25,0.75], [0,-0.25,0.75], [0,0,2]]
        edge_wire = cq.Workplane('XY').polyline(edge_points)
        edge_wire = [o.vals()[0] for o in edge_wire.all()]
        edge_wire = cq.Wire.assembleEdges(edge_wire)
               
        return edge_wire


    def edge_wire_4(self):
        # Gyroïd, all edges are splines on different workplanes.
        thickness = 0.1
        edge_points =  [[[3.54, 3.54], [1.77, 0.0], [3.54, -3.54]], [[-3.54, -3.54], [0.0, -1.77], [3.54, -3.54]], [[-3.54, -3.54], [0.0, -1.77], [3.54, -3.54]], [[-3.54, -3.54], [-1.77, 0.0], [-3.54, 3.54]], [[3.54, 3.54], [0.0, 1.77], [-3.54, 3.54]], [[3.54, 3.54], [0.0, 1.77], [-3.54, 3.54]]]
        plane_list =  ['XZ', 'XY', 'YZ', 'XZ', 'YZ', 'XY']
        offset_list =  [-3.54, 3.54, 3.54, 3.54, -3.54, -3.54]
        edge_wire = cq.Workplane(plane_list[0]).workplane(offset=-offset_list[0]).spline(edge_points[0])
        for i in range(len(edge_points)-1):
            edge_wire = edge_wire.add(cq.Workplane(plane_list[i+1]).workplane(offset=-offset_list[i+1]).spline(edge_points[i+1]))
        edge_wire = [o.vals()[0] for o in edge_wire.all()]
        edge_wire = cq.Wire.assembleEdges(edge_wire)
               
        return edge_wire


