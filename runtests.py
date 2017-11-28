#!/usr/bin/env python
import sys
from tests import *
import cadquery
import unittest

#if you are on python 2.7, you can use.
#   python -m unittest discover -s tests -p "Test*" --verbose
#but this is required for python 2.6.6 on windows. FreeCAD0.12 will not load
#on py 2.7.x on win
suite = unittest.TestSuite()

suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestCQGI.TestCQGI))
suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestCadObjects.TestCadObjects))
suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestWorkplanes.TestWorkplanes))
suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestCQSelectors.TestCQSelectors))
suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestCadQuery.TestCadQuery))
suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestExporters.TestExporters))
suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestImporters.TestImporters))
suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestLogging.TestLogging))
unittest.TextTestRunner().run(suite)
