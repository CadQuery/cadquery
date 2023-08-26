from typing import Optional
from OCP.TopExp import TopExp_Explorer


from OCP.TopAbs import (
    TopAbs_COMPOUND,
    TopAbs_COMPSOLID,
    TopAbs_SOLID,
    TopAbs_SHELL,
    TopAbs_FACE,
    TopAbs_WIRE,
    TopAbs_EDGE,
    TopAbs_VERTEX,
    TopAbs_SHAPE,
)
from cadquery.occ_impl.shapes import (
    Shape,
    Shapes,
)


ENUM_MAPPING = {
    "Compound": TopAbs_COMPOUND,
    "CompSolid": TopAbs_COMPSOLID,
    "Solid": TopAbs_SOLID,
    "Shell": TopAbs_SHELL,
    "Face": TopAbs_FACE,
    "Wire": TopAbs_WIRE,
    "Edge": TopAbs_EDGE,
    "Vertex": TopAbs_VERTEX,
    "Shape": TopAbs_SHAPE,
}


class ShapeExplorer:
    def __init__(self, shape: Shape) -> None:
        self.shape = shape.wrapped
        self.explorer = TopExp_Explorer()

    def search(
        self, shape_type: Shapes, not_from: Optional[Shapes] = None,
    ):
        """
        Searchs all the shapes of type `shape_type` in the shape. If `not_from` is specified, will avoid all the shapes
        that are attached to the type `not_from`
        """
        to_avoid = TopAbs_SHAPE if not_from is None else ENUM_MAPPING[not_from]
        self.explorer.Init(self.shape, ENUM_MAPPING[shape_type], to_avoid)

        collection = []
        while self.explorer.More():
            shape = Shape.cast(self.explorer.Current())
            collection.append(shape)
            self.explorer.Next()

        return list(set(collection))  # the 'set' is used to remove duplicates


class ConnectedShapesExplorer:
    def __init__(self, base_shape, child_shape) -> None:
        self.base_shape = base_shape
        self.child_shape = child_shape
        self.explorer = ShapeExplorer(base_shape)

    def _connected_by_vertices(self, shape, by_all=False):
        child_vertices = self.child_shape.Vertices()
        shape_vertices = shape.Vertices()

        if by_all:
            return all(v in child_vertices for v in shape_vertices)
        else:
            return any(v in child_vertices for v in shape_vertices)

    def search(self, shape_type: Shapes, include_child_shape=False):
        candidate_shapes = self.explorer.search(shape_type)
        if not include_child_shape:
            child_shapes = ShapeExplorer(self.child_shape).search(shape_type)
            candidate_shapes = [
                shape for shape in candidate_shapes if shape not in child_shapes
            ]

        connected_shapes = []
        for shape in candidate_shapes:
            if self._connected_by_vertices(shape):
                connected_shapes.append(shape)
        return connected_shapes


if __name__ == "__main__":
    import cadquery as cq
    from jupyter_cadquery.viewer.client import show

    box = cq.Workplane().box(10, 10, 10).faces(">Z").connected("Edge", True)

    show(
        box,
        height=800,
        cad_width=1500,
        reset_camera=False,
        default_edgecolor=(255, 255, 255),
        zoom=1,
        axes=True,
        axes0=True,
        render_edges=True,
    )
