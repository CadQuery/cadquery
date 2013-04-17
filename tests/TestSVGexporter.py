__author__ = 'dcowden'

from cadquery import *

import unittest,sys
from tests import MakeTestObjects
import SVGexporter

class TestCadQuery(unittest.TestCase):
    def setUp(self):
        pass

    def testExport(self):
        t = MakeTestObjects.makeCube(20)

        SVGexporter.exportSVG(t,'c:/temp/test.svg')