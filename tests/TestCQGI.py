"""
    Tests CQGI functionality
"""


from cadquery import cqgi
from tests import BaseTest

TESTSCRIPT = """
height=2.0
width=3.0
(a,b) = (1.0,1.0)
foo="bar"

result =  "%s|%s|%s|%s" % ( str(height) , str(width) , foo , str(a) )
build_object(result)
"""

class TestCQGI(BaseTest):


    def test_parser(self):
        model = cqgi.CQModel(TESTSCRIPT)
        metadata = model.metadata
        self.assertEquals( len(metadata.parameters) , 5 )

    def test_build_with_empty_params(self):
        model = cqgi.CQModel(TESTSCRIPT)
        result = model.build({}) #building with no params should have no affect on the output
        self.assertTrue(result.success)
        self.assertTrue(len(result.results) == 1)
        self.assertTrue(result.results[0] == "2.0|3.0|bar|1.0")

    def test_build_with_different_params(self):
        model = cqgi.CQModel(TESTSCRIPT)
        result = model.build({ 'height':3.0})
        self.assertTrue(result.results[0] == "3.0|3.0|bar|1.0")