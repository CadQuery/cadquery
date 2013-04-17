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


#these items point to the freecad implementation
from .freecad_impl.geom import Plane,BoundBox,Vector,Matrix,sortWiresByBuildOrder
from .freecad_impl.shapes import Shape,Vertex,Edge,Face,Wire,Solid,Shell,Compound
from .freecad_impl import exporters

#these items are the common implementation

#the order of these matter
from . import selectors
from .CQ import CQ,CQContext,Workplane


__all__ = [
	'CQ','Workplane','plugins','selectors','Plane','BoundBox','Matrix','Vector','sortWiresByBuildOrder',
	'Shape','Vertex','Edge','Wire','Solid','Shell','Compound','exporters',
	'plugins'
]

__version__ = 0.9