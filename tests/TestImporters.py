"""
    Tests file importers such as STEP
"""
#core modules
import StringIO

from cadquery import *
from cadquery import exporters
from cadquery import importers
from tests import BaseTest

#where unit test output will be saved
import sys
if sys.platform.startswith("win"):
    OUTDIR = "c:/temp"
else:
    OUTDIR = "/tmp"

class TestImporters(BaseTest):

	def importBox(importType,fileName):
		"""
		Exports a simple box to a STEP file and then imports it again
		:param importType: The type of file we're importing (STEP, STL, etc)
		:param fileName: The path and name of the file to write to
		"""
		#We're importing a STEP file
		if importType == ImportTypes.STEP:
			#We first need to build a simple shape to export
			shape = Workplane("XY").box(1,2,3).val

			#Export the shape to a temporary file
			shape.exportStep(fileName)

			# Reimport the shape from the new STEP file
			importedShape = importShape(importType,fileName)

	def testSTEP(self):
		"""
		Tests STEP file import
		"""
		importBox(ImportTypes.STEP, OUTDIR + "/tempSTEP.step")

if __name__ == '__main__':
	testSTEP()
