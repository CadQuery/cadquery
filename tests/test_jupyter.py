from tests import BaseTest

import cadquery

class TestJupyter(BaseTest):
    def test_repr_html(self):
        cube = cadquery.Workplane('XY').box(1, 1, 1)
        shape = cube.val()
        self.assertIsInstance(shape, cadquery.occ_impl.shapes.Solid)

        # Test no exception on rendering to html
        html = shape._repr_html_()
        # TODO: verification improvement: test for valid html
