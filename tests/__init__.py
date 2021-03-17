from cadquery import *
from OCP.gp import gp_Vec
import unittest
import sys
import os


def readFileAsString(fileName):
    f = open(fileName, "r")
    s = f.read()
    f.close()
    return s


def writeStringToFile(strToWrite, fileName):
    f = open(fileName, "w")
    f.write(strToWrite)
    f.close()


def makeUnitSquareWire():
    V = Vector
    return Wire.makePolygon(
        [V(0, 0, 0), V(1, 0, 0), V(1, 1, 0), V(0, 1, 0), V(0, 0, 0)]
    )


def makeUnitCube(centered=True):
    return makeCube(1.0, centered)


def makeCube(size, xycentered=True):
    if xycentered:
        return Workplane().rect(size, size).extrude(size).val()
    else:
        return Solid.makeBox(size, size, size)


def toTuple(v):
    """convert a vector or a vertex to a 3-tuple: x,y,z"""
    if type(v) == gp_Vec:
        return (v.X(), v.Y(), v.Z())
    elif type(v) == Vector:
        return v.toTuple()
    else:
        raise RuntimeError("dont know how to convert type %s to tuple" % str(type(v)))


class BaseTest(unittest.TestCase):
    def assertTupleAlmostEquals(self, expected, actual, places, msg=None):
        for i, j in zip(actual, expected):
            self.assertAlmostEqual(i, j, places, msg=msg)


__all__ = [
    "TestCadObjects",
    "TestCadQuery",
    "TestCQGI",
    "TestCQSelectors",
    "TestCQSelectors",
    "TestExporters",
    "TestImporters",
    "TestJupyter",
    "TestWorkplanes",
]
