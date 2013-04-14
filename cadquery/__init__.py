#these items are the common implementation
from .CQ import CQ
from .workplane import Workplane
from . import plugins
from . import selectors

#these items point to the freecad implementation
from .freecad_impl.geom import Plane,BoundBox,Vector
from .freecad_impl.shapes import Shape,Vertex,Edge,Wire,Solid,Shell,Compound
from .freecad_impl.exporters import SvgExporter, AmfExporter, JsonExporter

__all__ = [
	'CQ','Workplane','plugins','selectors','Plane','BoundBox',
	'Shape','Vertex','Edge','Wire','Solid','Shell','Compound',
	'SvgExporter','AmfExporter','JsonExporter',
	'plugins'
]

__version__ = 0.9