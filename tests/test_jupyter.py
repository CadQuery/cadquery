from tests import BaseTest

import cadquery as cq
from cadquery.occ_impl.jupyter_tools import display


class TestJupyter(BaseTest):
    def test_repr_javascript(self):
        cube = cq.Workplane("XY").box(1, 1, 1)
        assy = cq.Assembly().add(cube)
        shape = cube.val()

        self.assertIsInstance(shape, cq.occ_impl.shapes.Solid)

        # Test no exception on rendering to js
        js1 = shape._repr_javascript_()
        js2 = cube._repr_javascript_()
        js3 = assy._repr_javascript_()

        assert "function render" in js1
        assert "function render" in js2
        assert "function render" in js3

    def test_display_error(self):

        with self.assertRaises(ValueError):
            display(cq.Vector())
