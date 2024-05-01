from unittest import TestCase, main
from typing import Optional, Union, List, Tuple, cast
from cadquery import Workplane
from cadquery.occ_impl.shapes import Vertex
from math import atan, sqrt, fabs, degrees


class TestCase3D(TestCase):

    def assertAlmostEqualVertices(
            self,
            first: Workplane,
            second: Union[Workplane, List[Tuple[float, float, float]]],
            places: Optional[int] = None,
            msg: Optional[str] = None,
            delta: Optional[float] = None
    ):
        first = sorted([cast(Vertex, x).toTuple() for x in first.vertices().objects])
        if isinstance(second, Workplane):
            second = sorted([cast(Vertex, x).toTuple() for x in second.vertices().objects])
        else:
            second = sorted(second)

        # print('['+', '.join([str(x) for x in first])+']')
        # print('['+', '.join([str(x) for x in second])+']')

        self.assertEqual(len(first), len(second))

        for f, s in zip(first, second):
            distance: float = fabs(sqrt((f[0] - s[0]) ** 2 + (f[1] - s[1]) ** 2 + (f[2] - s[2]) ** 2))
            message = msg or f'{f} != {s} with distance {distance}'
            self.assertAlmostEqual(distance, 0.0, places=places, msg=message, delta=delta)


class TestChamfer(TestCase3D):

    def test_symmetric_chamfer_all(self):
        obj1 = Workplane().box(10, 10, 10).chamfer(1)
        obj2 = obj1.rotate((0, 0, 0), (1, 0, 0), 90)
        self.assertAlmostEqualVertices(obj1, obj2)

    def test_asymmetric_chamfer_x_1(self):
        obj1 = Workplane().box(10, 10, 10).faces("<X").chamfer(1, 2)
        obj2 = Workplane().box(8, 10, 10).faces("<X").workplane().rect(10, 10).extrude(2, taper=degrees(atan(0.5))).translate((1, 0, 0))
        self.assertAlmostEqualVertices(obj1, obj2)

    def test_asymmetric_chamfer_x_2(self):
        obj1 = Workplane().box(10, 10, 10).faces(">X").chamfer(1, 2)
        obj2 = Workplane().box(8, 10, 10).faces(">X").workplane().rect(10, 10).extrude(2, taper=degrees(atan(0.5))).translate((-1, 0, 0))
        self.assertAlmostEqualVertices(obj1, obj2)

    def test_asymmetric_chamfer_y_1(self):
        obj1 = Workplane().box(10, 10, 10).faces("<Y").chamfer(1, 2)
        obj2 = Workplane().box(10, 8, 10).faces("<Y").workplane().rect(10, 10).extrude(2, taper=degrees(atan(0.5))).translate((0, 1, 0))
        self.assertAlmostEqualVertices(obj1, obj2)

    def test_asymmetric_chamfer_y_2(self):
        obj1 = Workplane().box(10, 10, 10).faces(">Y").chamfer(1, 2)
        obj2 = Workplane().box(10, 8, 10).faces(">Y").workplane().rect(10, 10).extrude(2, taper=degrees(atan(0.5))).translate((0, -1, 0))
        self.assertAlmostEqualVertices(obj1, obj2)

    def test_asymmetric_chamfer_z_1(self):
        obj1 = Workplane().box(10, 10, 10).faces("<Z").chamfer(1, 2)
        obj2 = Workplane().box(10, 10, 8).faces("<Z").workplane().rect(10, 10).extrude(2, taper=degrees(atan(0.5))).translate((0, 0, 1))
        self.assertAlmostEqualVertices(obj1, obj2)

    def test_asymmetric_chamfer_z_2(self):
        obj1 = Workplane().box(10, 10, 10).faces(">Z").chamfer(1, 2)
        obj2 = Workplane().box(10, 10, 8).faces(">Z").workplane().rect(10, 10).extrude(2, taper=degrees(atan(0.5))).translate((0, 0, -1))
        self.assertAlmostEqualVertices(obj1, obj2)

    def test_asymmetric_chamfer_xy_1(self):
        obj1 = Workplane().box(10, 10, 10).faces("<Y or <X").edges("|Z").chamfer(1, 2)
        obj2 = Workplane().polyline([
            (5, 5), (5, -3), (4, -5), (-3, -5), (-5, -3), (-5, 4), (-3, 5)
        ]).close().extrude(5, both=True)
        self.assertAlmostEqualVertices(obj1, obj2)

    def test_asymmetric_chamfer_x_z(self):
        obj1 = Workplane().box(10, 10, 10).faces("<X").edges("|Z").chamfer(1, 2)
        obj2 = Workplane().polyline([
            (-3.0, -5.0), (-5.0, -4.0), (-5.0, 4.0), (-3.0, 5.0), (5.0, 5.0), (5.0, -5.0)
        ]).close().extrude(5, both=True)
        self.assertAlmostEqualVertices(obj1, obj2)

    def test_asymmetric_chamfer_x_z_edges(self):
        obj1 = Workplane().box(10, 10, 10).faces("<X").edges("|Z").edges().edges().chamfer(1, 2)
        obj2 = Workplane().polyline([
            (-3.0, -5.0), (-5.0, -4.0), (-5.0, 4.0), (-3.0, 5.0), (5.0, 5.0), (5.0, -5.0)
        ]).close().extrude(5, both=True)
        self.assertAlmostEqualVertices(obj1, obj2)

    def test_cylinder_symmetric(self):
        obj1 = Workplane().circle(10).extrude(10, both=True).faces("|Z").chamfer(1, 2)
        self.assertAlmostEqualVertices(obj1, [
            (9.0, 0.0, -10.0), (9.0, 0.0, 10.0), (10.0, 0.0, -8.0), (10.0, 0.0, 0.0), (10.0, 0.0, 8.0)
        ])


if __name__ == "__main__":
    main()
