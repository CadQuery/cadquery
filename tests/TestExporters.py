"""
    Tests basic workplane functionality
"""
#from __future__ import unicode_literals

#core modules
import io

#my modules
from cadquery import *
from cadquery import exporters
from tests import BaseTest

class TestExporters(BaseTest):

    def _exportBox(self,eType,stringsToFind):
        """
            Exports a test object, and then looks for
            all of the supplied strings to be in the result
            returns the result in case the case wants to do more checks also
        """
        p = Workplane("XY").box(1,2,3)

        if eType == exporters.ExportTypes.AMF:
            s = io.BytesIO()
            exporters.exportShape(p,eType,s,0.1)
            result = s.getvalue()
            for q in stringsToFind:
                self.assertTrue(result.decode().find(q) > -1 )
        else:
            s = io.StringIO()
            exporters.exportShape(p,eType,s,0.1)
            result = s.getvalue()
            for q in stringsToFind:
                self.assertTrue(q in result)

        return result

    def testSTL(self):
        self._exportBox(exporters.ExportTypes.STL,['facet normal'])

    def testSVG(self):
        self._exportBox(exporters.ExportTypes.SVG,['<svg','<g transform'])

    def testAMF(self):
        self._exportBox(exporters.ExportTypes.AMF,['<amf units','</object>'])

    def testSTEP(self):
        self._exportBox(exporters.ExportTypes.STEP,['FILE_SCHEMA'])

    def testTJS(self):
        self._exportBox(exporters.ExportTypes.TJS,['vertices','formatVersion','faces'])
