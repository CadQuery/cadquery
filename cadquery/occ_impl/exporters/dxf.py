"""DXF export utilities."""

from typing import Any, Dict, List, Literal, Optional, Tuple, Union

import ezdxf
from ezdxf import units, zoom
from ezdxf.entities import factory
from OCP.GeomConvert import GeomConvert
from OCP.gp import gp_Dir
from OCP.GC import GC_MakeArcOfEllipse
from typing_extensions import Self

from ...cq import Face, Plane, Workplane
from ...units import RAD2DEG
from ..shapes import Edge, Shape, Compound
from .utils import toCompound

ApproxOptions = Literal["spline", "arc"]
DxfEntityAttributes = Tuple[
    Literal["ARC", "CIRCLE", "ELLIPSE", "LINE", "SPLINE",], Dict[str, Any]
]


class DxfDocument:
    """Create DXF document from CadQuery objects.

    A wrapper for `ezdxf <https://ezdxf.readthedocs.io/>`_ providing methods for
    converting :class:`cadquery.Workplane` objects to DXF entities.

    The ezdxf document is available as the property ``document``, allowing most
    features of ezdxf to be utilised directly.

    .. rubric:: Example usage

    .. code-block:: python
        :caption: Single layer DXF document

        rectangle = cq.Workplane().rect(10, 20)

        dxf = DxfDocument()
        dxf.add_shape(rectangle)
        dxf.document.saveas("rectangle.dxf")

    .. code-block:: python
        :caption: Multilayer DXF document

        rectangle = cq.Workplane().rect(10, 20)
        circle = cq.Workplane().circle(3)

        dxf = DxfDocument()
        dxf = (
            dxf.add_layer("layer_1", color=2)
            .add_layer("layer_2", color=3)
            .add_shape(rectangle, "layer_1")
            .add_shape(circle, "layer_2")
        )
        dxf.document.saveas("rectangle-with-hole.dxf")
    """

    CURVE_TOLERANCE = 1e-9

    def __init__(
        self,
        dxfversion: str = "AC1027",
        setup: Union[bool, List[str]] = False,
        doc_units: int = units.MM,
        *,
        metadata: Union[Dict[str, str], None] = None,
        approx: Optional[ApproxOptions] = None,
        tolerance: float = 1e-3,
    ):
        """Initialize DXF document.

        :param dxfversion: :attr:`DXF version specifier <ezdxf-stable:ezdxf.document.Drawing.dxfversion>`
            as string, default is "AC1027" respectively "R2013"
        :param setup: setup default styles, ``False`` for no setup, ``True`` to set up
            everything or a list of topics as strings, e.g. ``["linetypes", "styles"]``
            refer to :func:`ezdxf-stable:ezdxf.new`.
        :param doc_units: ezdxf document/modelspace :doc:`units <ezdxf-stable:concepts/units>`
        :param metadata: document :ref:`metadata <ezdxf-stable:ezdxf_metadata>` a dictionary of name value pairs
        :param approx: Approximation strategy for converting :class:`cadquery.Workplane` objects to DXF entities:

            ``None``
                no approximation applied
            ``"spline"``
                all splines approximated as cubic splines
            ``"arc"``
                all curves approximated as arcs and straight segments

        :param tolerance: Approximation tolerance for converting :class:`cadquery.Workplane` objects to DXF entities.
        """
        if metadata is None:
            metadata = {}

        self._DISPATCH_MAP = {
            "LINE": self._dxf_line,
            "CIRCLE": self._dxf_circle,
            "ELLIPSE": self._dxf_ellipse,
        }

        self.approx = approx
        self.tolerance = tolerance

        self.document = ezdxf.new(dxfversion=dxfversion, setup=setup, units=doc_units)  # type: ignore[attr-defined]
        self.msp = self.document.modelspace()

        doc_metadata = self.document.ezdxf_metadata()
        for key, value in metadata.items():
            doc_metadata[key] = value

    def add_layer(
        self, name: str, *, color: int = 7, linetype: str = "CONTINUOUS"
    ) -> Self:
        """Create a layer definition

        Refer to :ref:`ezdxf layers <ezdxf-stable:layer_concept>` and
        :doc:`ezdxf layer tutorial <ezdxf-stable:tutorials/layers>`.

        :param name: layer definition name
        :param color: color index. Standard colors include:
            1 red, 2 yellow, 3 green, 4 cyan, 5 blue, 6 magenta, 7 white/black
        :param linetype: ezdxf :doc:`line type <ezdxf-stable:concepts/linetypes>`
        """
        self.document.layers.add(name, color=color, linetype=linetype)

        return self

    def add_shape(self, workplane: Workplane, layer: str = "") -> Self:
        """Add CadQuery shape to a DXF layer.

        :param workplane: CadQuery Workplane
        :param layer: layer definition name
        """
        plane = workplane.plane
        shape = toCompound(workplane).transformShape(plane.fG)

        general_attributes = {}
        if layer:
            general_attributes["layer"] = layer

        if self.approx == "spline":
            edges = [
                e.toSplines() if e.geomType() == "BSPLINE" else e
                for e in self._ordered_edges(shape)
            ]

        elif self.approx == "arc":
            edges = []

            # this is needed to handle free wires
            for el in shape.Wires():
                edges.extend(
                    self._ordered_edges(Face.makeFromWires(el).toArcs(self.tolerance))
                )

        else:
            edges = self._ordered_edges(shape)

        for edge in edges:
            converter = self._DISPATCH_MAP.get(edge.geomType(), None)

            if converter:
                entity_type, entity_attributes = converter(edge)
                entity = factory.new(
                    entity_type, dxfattribs={**entity_attributes, **general_attributes}
                )
                self.msp.add_entity(entity)  # type: ignore[arg-type]
            else:
                _, entity_attributes = self._dxf_spline(edge, plane)
                entity = ezdxf.math.BSpline(**entity_attributes)  # type: ignore[assignment]
                self.msp.add_spline(
                    dxfattribs=general_attributes
                ).apply_construction_tool(entity)

        zoom.extents(self.msp)

        return self

    @staticmethod
    def _ordered_edges(s: Shape) -> List[Edge]:

        rv: List[Edge] = []

        # iterate over wires and then edges
        for w in s.Wires():
            rv.extend(w)

        # add free edges
        if isinstance(s, Compound):
            rv.extend(e for e in s if isinstance(e, Edge))

        return rv

    @staticmethod
    def _dxf_line(edge: Edge) -> DxfEntityAttributes:
        """Convert a Line to DXF entity attributes.

        :param edge: CadQuery Edge to be converted to a DXF line

        :return: dictionary of DXF entity attributes for creating a line
        """
        return (
            "LINE",
            {"start": edge.startPoint().toTuple(), "end": edge.endPoint().toTuple(),},
        )

    @staticmethod
    def _dxf_circle(edge: Edge) -> DxfEntityAttributes:
        """Convert a Circle to DXF entity attributes.

        :param edge: CadQuery Edge to be converted to a DXF circle

        :return: dictionary of DXF entity attributes for creating either a circle or arc
        """
        geom = edge._geomAdaptor()
        circ = geom.Circle()

        radius = circ.Radius()
        location = circ.Location()

        direction_y = circ.YAxis().Direction()
        direction_z = circ.Axis().Direction()

        dy = gp_Dir(0, 1, 0)

        phi = direction_y.AngleWithRef(dy, direction_z)

        if direction_z.XYZ().Z() > 0:
            a1 = RAD2DEG * (geom.FirstParameter() - phi)
            a2 = RAD2DEG * (geom.LastParameter() - phi)
        else:
            a1 = -RAD2DEG * (geom.LastParameter() - phi) + 180
            a2 = -RAD2DEG * (geom.FirstParameter() - phi) + 180

        if edge.IsClosed():
            return (
                "CIRCLE",
                {
                    "center": (location.X(), location.Y(), location.Z()),
                    "radius": radius,
                },
            )
        else:
            return (
                "ARC",
                {
                    "center": (location.X(), location.Y(), location.Z()),
                    "radius": radius,
                    "start_angle": a1,
                    "end_angle": a2,
                },
            )

    @staticmethod
    def _dxf_ellipse(edge: Edge) -> DxfEntityAttributes:
        """Convert an Ellipse to DXF entity attributes.

        :param edge: CadQuery Edge to be converted to a DXF ellipse

        :return: dictionary of DXF entity attributes for creating an ellipse
        """
        geom = edge._geomAdaptor()
        ellipse = geom.Ellipse()

        r1 = ellipse.MinorRadius()
        r2 = ellipse.MajorRadius()

        c = ellipse.Location()
        xdir = ellipse.XAxis().Direction()
        xax = r2 * xdir.XYZ()

        zdir = ellipse.Axis().Direction()

        if zdir.Z() > 0:
            start_param = geom.FirstParameter()
            end_param = geom.LastParameter()
        else:
            gc = GC_MakeArcOfEllipse(
                ellipse,
                geom.FirstParameter(),
                geom.LastParameter(),
                False,  # reverse Sense
            ).Value()
            start_param = gc.FirstParameter()
            end_param = gc.LastParameter()

        return (
            "ELLIPSE",
            {
                "center": (c.X(), c.Y(), c.Z()),
                "major_axis": (xax.X(), xax.Y(), xax.Z()),
                "ratio": r1 / r2,
                "start_param": start_param,
                "end_param": end_param,
            },
        )

    @classmethod
    def _dxf_spline(cls, edge: Edge, plane: Plane) -> DxfEntityAttributes:
        """Convert a Spline to ezdxf.math.BSpline parameters.

        :param edge: CadQuery Edge to be converted to a DXF spline
        :param plane: CadQuery Plane

        :return: dictionary of ezdxf.math.BSpline parameters
        """
        adaptor = edge._geomAdaptor()
        curve = GeomConvert.CurveToBSplineCurve_s(adaptor.Curve().Curve())

        spline = GeomConvert.SplitBSplineCurve_s(
            curve,
            adaptor.FirstParameter(),
            adaptor.LastParameter(),
            cls.CURVE_TOLERANCE,
        )

        # need to apply the transform on the geometry level
        spline.Transform(adaptor.Trsf())

        order = spline.Degree() + 1
        knots = list(spline.KnotSequence())
        poles = [(p.X(), p.Y(), p.Z()) for p in spline.Poles()]
        weights = (
            [spline.Weight(i) for i in range(1, spline.NbPoles() + 1)]
            if spline.IsRational()
            else None
        )

        if spline.IsPeriodic():
            pad = spline.NbKnots() - spline.LastUKnotIndex()
            poles += poles[:pad]

        return (
            "SPLINE",
            {
                "control_points": poles,
                "order": order,
                "knots": knots,
                "weights": weights,
            },
        )


def exportDXF(
    w: Workplane,
    fname: str,
    approx: Optional[ApproxOptions] = None,
    tolerance: float = 1e-3,
    *,
    doc_units: int = units.MM,
) -> None:
    """
    Export Workplane content to DXF. Works with 2D sections.

    :param w: Workplane to be exported.
    :param fname: Output filename.
    :param approx: Approximation strategy. None means no approximation is applied.
        "spline" results in all splines being approximated as cubic splines. "arc" results
        in all curves being approximated as arcs and straight segments.
    :param tolerance: Approximation tolerance.
    :param doc_units: ezdxf document/modelspace :doc:`units <ezdxf-stable:concepts/units>` (in. = ``1``, mm = ``4``).
    """

    dxf = DxfDocument(approx=approx, tolerance=tolerance, doc_units=doc_units)
    dxf.add_shape(w)
    dxf.document.saveas(fname)
