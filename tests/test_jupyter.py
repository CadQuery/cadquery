from tests import BaseTest
from IPython.display import Javascript

import cadquery


class TestJupyter(BaseTest):
    def test_repr_javascript(self):
        cube = cadquery.Workplane("XY").box(1, 1, 1)
        assy = cq.Assembly().add(cube)
        shape = cube.val()

        self.assertIsInstance(shape, cadquery.occ_impl.shapes.Solid)

        # Test no exception on rendering to js
        js1 = shape._repr_javascript_()
        js2 = cube._repr_javascript_()
        js3 = assy._repr_javascript_()

        self.assertIsInstance(js1, Javascript)
        self.assertIsInstance(js2, Javascript)
        self.assertIsInstance(js3, Javascript)
