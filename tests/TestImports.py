"""
    Tests basic workplane functionality
"""
#core modules

#my modules
from cadquery.freecad_impl import verutil
from tests import BaseTest

class TestVersionsForImport(BaseTest):
    """Test version checks."""

    def test_013_version(self):
        """Make sure various 0.13 Version calls work correctly"""
        self.assertEquals(verutil._figure_out_version(
            ['0', '13', '2055 (Git)',
                'git://git.code.sf.net/p/free-cad/code',
                '2013/04/18 13:48:49', 'master',
                '3511a807a30cf41909aaf12a1efe1db6c53db577']),
            (0,13,2055))
        self.assertEquals(verutil._figure_out_version(
            ['0', '13', '12345']),
            (0,13,12345))
        self.assertEquals(verutil._figure_out_version(
            ['0', '13', 'SOMETAGTHATBREAKSSTUFF']),
            (0,13,0))




