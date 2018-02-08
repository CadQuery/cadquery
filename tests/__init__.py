from cadquery import *
import unittest
import sys
import os
from contextlib import contextmanager

import FreeCAD

import Part as P
from FreeCAD import Vector as V


def readFileAsString(fileName):
    f= open(fileName, 'r')
    s = f.read()
    f.close()
    return s


def writeStringToFile(strToWrite, fileName):
    f = open(fileName, 'w')
    f.write(strToWrite)
    f.close()


def makeUnitSquareWire():
    return Solid.cast(P.makePolygon([V(0, 0, 0), V(1, 0, 0), V(1, 1, 0), V(0, 1, 0), V(0, 0, 0)]))


def makeUnitCube():
    return makeCube(1.0)


def makeCube(size):
    return Solid.makeBox(size, size, size)


def toTuple(v):
    """convert a vector or a vertex to a 3-tuple: x,y,z"""
    pnt = v
    if type(v) == FreeCAD.Base.Vector:
        return (v.Point.x, v.Point.y, v.Point.z)
    elif type(v) == Vector:
        return v.toTuple()
    else:
        raise RuntimeError("dont know how to convert type %s to tuple" % str(type(v)) )


class BaseTest(unittest.TestCase):

    def assertTupleAlmostEquals(self, expected, actual, places=7):
        for i, j in zip(actual, expected):
            self.assertAlmostEqual(i, j, places)


__all__ = [
    'TestCQGI',
    'TestCQSelectors',
    'TestCQSelectors',
    'TestCadObjects',
    'TestCadQuery',
    'TestExporters',
    'TestImporters',
    'TestLogging',
    'TestWorkplanes',
]
