"""
    Tests interpPlate functionality
"""

import cadquery as cq

class TestinterpPlate(BaseTest):
    
    def plate_0(self):
        # example from PythonOCC core_geometry_geomplate.py, use of thickness = 0 returns 2D surface.
        thickness = 0
        edge_points = [[0.,0.,0.], [0.,10.,0.], [0.,10.,10.], [0.,0.,10.]]
        surface_points = [[5.,5.,5.]]
        plate_0 = cq.Workplane('XY').interpPlate(edge_points, surface_points, thickness)
                
        return plate_0


    def plate_1(self):   
        # Plate with 5 sides and 2 bumps, one side is not co-planar with the other sides
        thickness = 0.1
        edge_points = [[-7.,-7.,0.], [-3.,-10.,3.], [7.,-7.,0.], [7.,7.,0.], [-7.,7.,0.]]
        edge_wire = cq.Workplane('XY').polyline([(-7.,-7.), (7.,-7.), (7.,7.), (-7.,7.)])
        #edge_wire = edge_wire.add(cq.Workplane('YZ').workplane().transformed(offset=cq.Vector(0, 0, -7), rotate=cq.Vector(45, 0, 0)).polyline([(-7.,0.), (3,-3), (7.,0.)])) 
        edge_wire = edge_wire.add(cq.Workplane('YZ').workplane().transformed(offset=cq.Vector(0, 0, -7), rotate=cq.Vector(45, 0, 0)).spline([(-7.,0.), (3,-3), (7.,0.)])) # In CadQuery Sept-2019 it worked with rotate=cq.Vector(0, 45, 0). In CadQuery Dec-2019 rotate=cq.Vector(45, 0, 0) only closes the wire. 
        surface_points = [[-3.,-3.,-3.], [3.,3.,3.]]
        plate_1 = cq.Workplane('XY').interpPlate(edge_wire, surface_points, thickness)
        
        return plate_1


    def plate_2(self):
        # Embossed star, need to change optional parameters to obtain nice looking result.
        r1=3.
        r2=10.
        fn=6
        thickness = 0.1
        edge_points = [[r1*cos(i * pi/fn), r1*sin(i * pi/fn)]    if i%2==0  else   [r2*cos(i * pi/fn), r2*sin(i * pi/fn)]  for i in range(2*fn+1)]
        edge_wire = cq.Workplane('XY').polyline(edge_points)
        r2=4.5
        surface_points = [[r2*cos(i * pi/fn), r2*sin(i * pi/fn), 1.]  for i in range(2*fn)] + [[0.,0.,-2.]]
        plate_2 = cq.Workplane('XY').interpPlate(edge_wire, surface_points, thickness, combine=True, clean=True, Degree=3, NbPtsOnCur=15, NbIter=2, Anisotropie=False, Tol2d=0.00001, Tol3d=0.0001, TolAng=0.01, TolCurv=0.1, MaxDeg=8, MaxSegments=49)
        plate_2 = plate_2.translate((0,2*12,0))
        
        return plate_2


    def plate_3(self):
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
        be = cq.Workplane('XY').interpPlate(edge_wire, surface_points, thickness, combine=True, clean=True, Degree=2, NbPtsOnCur=20, NbIter=2, Anisotropie=False, Tol2d=0.00001, Tol3d=0.0001, TolAng=0.01, TolCurv=0.1, MaxDeg=8, MaxSegments=9)
        # Pattern on sphere
        def face(pos): # If pushpoints is used directly with interpPlate --> crash! Use with each()
            return be.rotate((0,0,0),(0,0,1), 30).translate(pos).val()
        plate_3 = cq.Workplane('XY').pushPoints(pts).each(face)
        plate_3 = plate_3.translate((0,4*11,0))
        
        return plate_3


    def plate_4(self):
        # Gyroïd, all edges are splines on different workplanes.
        thickness = 0.1
        edge_points =  [[[3.54, 3.54], [1.77, 0.0], [3.54, -3.54]], [[-3.54, -3.54], [0.0, -1.77], [3.54, -3.54]], [[-3.54, -3.54], [0.0, -1.77], [3.54, -3.54]], [[-3.54, -3.54], [-1.77, 0.0], [-3.54, 3.54]], [[3.54, 3.54], [0.0, 1.77], [-3.54, 3.54]], [[3.54, 3.54], [0.0, 1.77], [-3.54, 3.54]]]
        plane_list =  ['XZ', 'XY', 'YZ', 'XZ', 'YZ', 'XY']
        offset_list =  [-3.54, 3.54, 3.54, 3.54, -3.54, -3.54]
        edge_wire = cq.Workplane(plane_list[0]).workplane(offset=-offset_list[0]).spline(edge_points[0])
        for i in range(len(edge_points)-1):
            edge_wire = edge_wire.add(cq.Workplane(plane_list[i+1]).workplane(offset=-offset_list[i+1]).spline(edge_points[i+1]))
        surface_points = [[0,0,0]]
        plate_4 = cq.Workplane('XY').interpPlate(edge_wire, surface_points, thickness)
        plate_4 = plate_4.translate((0,5*12,0))
        
        return plate_4


