
import cadquery
from .shapes import Shape

import sys
import os
import urllib as urlreader
import tempfile

from OCC.STEPControl import STEPControl_Reader
import OCC.IFSelect


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

    # Check to see what type of file we're working with
    if importType == ImportTypes.STEP:
        return importStep(fileName)


# Loads a STEP file into a CQ.Workplane object
def importStep(fileName):
    """
        Accepts a file name and loads the STEP file into a cadquery shape
        :param fileName: The path and name of the STEP file to be imported
    """
    # Now read and return the shape
    reader = STEPControl_Reader()
    readStatus = reader.ReadFile(fileName)
    if readStatus != OCC.IFSelect.IFSelect_RetDone:
        raise ValueError("STEP File could not be loaded")
    for i in range(reader.NbRootsForTransfer()):
        reader.TransferRoot(i+1)

    occ_shapes = []
    for i in range(reader.NbShapes()):
        occ_shapes.append(reader.Shape(i + 1))

    # Make sure that we extract all the solids
    solids = []
    for shape in occ_shapes:
        solids.append(Shape.cast(shape))

    return cadquery.Workplane("XY").newObject(solids)

# Loads a STEP file from an URL into a CQ.Workplane object


def importStepFromURL(url):
    # Now read and return the shape
    try:
        webFile = urlreader.urlopen(url)
        tempFile = tempfile.NamedTemporaryFile(suffix='.step', delete=False)
        tempFile.write(webFile.read())
        webFile.close()
        tempFile.close()

        return importStep(tempFile.name)
    except:
        raise ValueError("STEP File from the URL: " +
                         url + " Could not be loaded")
