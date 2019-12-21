"""
    Tests interpPlate functionality
"""

import cadquery as cq

class TestinterpPlate(BaseTest):
    
    def plate(self):
        # example from PythonOCC core_geometry_geomplate.py, use of thickness = 0 returns 2D surface.
        thickness = 0
        edge_points = [[0.,0.,0.], [0.,10.,0.], [0.,10.,10.], [0.,0.,10.]]
        surface_points = [[5.,5.,5.]]
        plate_0 = cq.Workplane('XY').interpPlate(edge_points, surface_points, thickness)
                
        return plate_0
