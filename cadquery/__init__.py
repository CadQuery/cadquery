# these items point to the OCC implementation
from .occ_impl.geom import Plane, BoundBox, Vector, Matrix
from .occ_impl.shapes import Shape, Vertex, Edge, Face, Wire, Solid, Shell, Compound, sortWiresByBuildOrder
from .occ_impl import exporters
from .occ_impl import importers

# these items are the common implementation

# the order of these matter
from .selectors import *
from .cq import *


__all__ = [
    'CQ', 'Workplane', 'plugins', 'selectors', 'Plane', 'BoundBox', 'Matrix', 'Vector', 'sortWiresByBuildOrder',
    'Shape', 'Vertex', 'Edge', 'Wire', 'Face', 'Solid', 'Shell', 'Compound', 'exporters', 'importers',
    'NearestToPointSelector', 'ParallelDirSelector', 'DirectionSelector', 'PerpendicularDirSelector',
    'TypeSelector', 'DirectionMinMaxSelector', 'StringSyntaxSelector', 'Selector', 'plugins'
]

__version__ = "2.0.0dev"
