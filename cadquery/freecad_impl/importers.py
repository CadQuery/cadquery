"""
    Copyright (C) 2011-2015  Parametric Products Intellectual Holdings, LLC

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

    An exporter should provide functionality to accept a shape, and return
    a string containing the model content.
"""
import cadquery
from .shapes import Shape

import FreeCAD
import Part

class ImportTypes:
    STEP = "STEP"

class UNITS:
    MM = "mm"
    IN = "in"


def importShape(importType, fileName):
    """
    Imports a file based on the type (STEP, STL, etc)
    :param importType: The type of file that we're importing
    :param fileName: THe name of the file that we're importing
    """

    #Check to see what type of file we're working with
    if importType == ImportTypes.STEP:
        return importStep(fileName)


#Loads a STEP file into a CQ.Workplane object
def importStep(fileName):
    """
        Accepts a file name and loads the STEP file into a cadquery shape
        :param fileName: The path and name of the STEP file to be imported
    """

    #Now read and return the shape
    try:
        rshape = Part.read(fileName)

        #Make sure that we extract all the solids
        solids = []
        for solid in rshape.Solids:
            solids.append(Shape.cast(solid))

        return cadquery.Workplane("XY").newObject(solids)
    except:
        raise ValueError("STEP File Could not be loaded")
