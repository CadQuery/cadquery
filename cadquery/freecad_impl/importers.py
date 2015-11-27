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

import sys

if sys.version > '3':
    PY3 = True
    import urllib.request as urlreader
    import urllib.parse as urlparse
else:
    PY3 = False
    import urllib as urlreader
    import urlparse
    
def isURL(filename):
    schemeSpecifier = urlparse.urlparse(filename).scheme
    if schemeSpecifier == 'http' or schemeSpecifier == 'https' or schemeSpecifier == 'ftp':
        return True
    else:
        return False

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

    if isURL(fileName):
        url = fileName
        webFile = urlreader.urlopen(url)
        localFileName = url.split('/')[-1]
        localFile = open(localFileName, 'w')
        if PY3:
            localFile.write(webFile.read().decode('utf-8'))
        else:
            localFile.write(webFile.read())    
        webFile.close()
        localFile.close()
        fileName = localFileName
        
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
