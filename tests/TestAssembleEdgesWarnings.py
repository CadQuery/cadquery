"""
    Tests assembleEdges warnings functionality
"""

import cadquery as cq

class TestAssembleEdgesWarning(BaseTest):
    
    def plate(self):

        # Plate with 5 sides and 2 bumps, one side is not co-planar with the other sides
        thickness = 0.1
        edge_points = [[-7.,-7.,0.], [-3.,-10.,3.], [7.,-7.,0.], [7.,7.,0.], [-7.,7.,0.]]
        edge_wire = cq.Workplane('XY').polyline([(-7.,-7.), (7.,-7.), (7.,7.), (-7.,7.)])
        edge_wire = edge_wire.add(cq.Workplane('XY').workplane().transformed(offset=cq.Vector(0, 0, -7), rotate=cq.Vector(0, 45, 0)).spline([(-7.,0.), (3,-3), (7.,0.)])) # Triggers BRepBuilderAPI_MakeWire error ('YZ' is correct)
        edge_wire = [o.vals()[0] for o in edge_wire.all()]
        edge_wire = cq.Wire.assembleEdges(edge_wire)
        
        return edge_wire
