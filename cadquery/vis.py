from . import Shape, Workplane, Assembly, Sketch, Compound, Color, Vector, Location
from .occ_impl.exporters.assembly import _vtkRenderWindow
from .occ_impl.assembly import _loc2vtk

from typing import Union, Any, List, Tuple

from typish import instance_of

from OCP.TopoDS import TopoDS_Shape

from vtkmodules.vtkInteractionWidgets import vtkOrientationMarkerWidget
from vtkmodules.vtkRenderingAnnotation import vtkAxesActor
from vtkmodules.vtkInteractionStyle import vtkInteractorStyleTrackballCamera
from vtkmodules.vtkRenderingCore import (
    vtkMapper,
    vtkRenderWindowInteractor,
    vtkActor,
    vtkPolyDataMapper,
    vtkAssembly,
)
from vtkmodules.vtkCommonCore import vtkPoints
from vtkmodules.vtkCommonDataModel import vtkCellArray, vtkPolyData
from vtkmodules.vtkCommonColor import vtkNamedColors


DEFAULT_COLOR = [1, 0.8, 0, 1]
DEFAULT_PT_SIZE = 7.5
DEFAULT_PT_COLOR = "darkviolet"

ShapeLike = Union[Shape, Workplane, Assembly, Sketch, TopoDS_Shape]
Showable = Union[ShapeLike, List[ShapeLike], Vector, List[Vector]]


def _to_assy(*objs: ShapeLike, alpha: float = 1) -> Assembly:

    assy = Assembly(
        color=Color(DEFAULT_COLOR[0], DEFAULT_COLOR[1], DEFAULT_COLOR[2], alpha)
    )

    for obj in objs:
        if isinstance(obj, (Shape, Workplane, Assembly)):
            assy.add(obj)
        elif isinstance(obj, Sketch):
            assy.add(Compound.makeCompound(obj))
        elif isinstance(obj, TopoDS_Shape):
            assy.add(Shape(obj))
        else:
            raise ValueError(f"{obj} has unsupported type {type(obj)}")

    return assy


def _split_showables(
    objs,
) -> Tuple[List[ShapeLike], List[Vector], List[Location], List[vtkActor]]:
    """
    Split into showables and others.
    """

    rv_s: List[ShapeLike] = []
    rv_v: List[Vector] = []
    rv_l: List[Location] = []
    rv_a: List[vtkActor] = []

    for el in objs:
        if instance_of(el, ShapeLike):
            rv_s.append(el)
        elif isinstance(el, Vector):
            rv_v.append(el)
        elif isinstance(el, Location):
            rv_l.append(el)
        elif isinstance(el, vtkActor):
            rv_a.append(el)
        elif isinstance(el, list):
            tmp1, tmp2, tmp3, tmp4 = _split_showables(el)  # split recursively

            rv_s.extend(tmp1)
            rv_v.extend(tmp2)
            rv_l.extend(tmp3)
            rv_a.extend(tmp4)

    return rv_s, rv_v, rv_l, rv_a


def _to_vtk_pts(
    vecs: List[Vector], size: float = DEFAULT_PT_SIZE, color: str = DEFAULT_PT_COLOR
) -> vtkActor:
    """
    Convert Vectors to vtkActor.
    """

    rv = vtkActor()

    mapper = vtkPolyDataMapper()
    points = vtkPoints()
    verts = vtkCellArray()
    data = vtkPolyData()

    data.SetPoints(points)
    data.SetVerts(verts)

    for v in vecs:
        ix = points.InsertNextPoint(*v.toTuple())
        verts.InsertNextCell(1)
        verts.InsertCellPoint(ix)

    mapper.SetInputData(data)

    rv.SetMapper(mapper)

    rv.GetProperty().SetColor(vtkNamedColors().GetColor3d(color))
    rv.GetProperty().SetPointSize(size)

    return rv


def _to_vtk_axs(locs: List[Location], scale: float = 0.1) -> vtkActor:
    """
    Convert Locations to vtkActor.
    """

    rv = vtkAssembly()

    for l in locs:
        trans, rot = _loc2vtk(l)
        ax = vtkAxesActor()
        ax.SetAxisLabels(0)

        ax.SetPosition(*trans)
        ax.SetOrientation(*rot)
        ax.SetScale(scale)

        rv.AddPart(ax)

    return rv


def show(
    *objs: Showable,
    scale: float = 0.2,
    alpha: float = 1,
    tolerance: float = 1e-3,
    edges: bool = False,
    **kwrags: Any,
):
    """
    Show CQ objects using VTK.
    """

    # split objects
    shapes, vecs, locs, acts = _split_showables(objs)

    # construct the assy
    assy = _to_assy(*shapes, alpha=alpha)

    # construct the points and locs
    pts = _to_vtk_pts(vecs)
    axs = _to_vtk_axs(locs, scale=scale)

    # create a VTK window
    win = _vtkRenderWindow(assy, tolerance=tolerance)

    win.SetWindowName("CQ viewer")

    # get renderer and actor
    if edges:
        ren = win.GetRenderers().GetFirstRenderer()
        for act in ren.GetActors():
            act.GetProperty().EdgeVisibilityOn()

    # rendering related settings
    win.SetMultiSamples(16)
    vtkMapper.SetResolveCoincidentTopologyToPolygonOffset()
    vtkMapper.SetResolveCoincidentTopologyPolygonOffsetParameters(1, 0)
    vtkMapper.SetResolveCoincidentTopologyLineOffsetParameters(-1, 0)

    # create a VTK interactor
    inter = vtkRenderWindowInteractor()
    inter.SetInteractorStyle(vtkInteractorStyleTrackballCamera())
    inter.SetRenderWindow(win)

    # construct an axes indicator
    axes = vtkAxesActor()
    axes.SetDragable(0)

    tp = axes.GetXAxisCaptionActor2D().GetCaptionTextProperty()
    tp.SetColor(0, 0, 0)

    axes.GetYAxisCaptionActor2D().GetCaptionTextProperty().ShallowCopy(tp)
    axes.GetZAxisCaptionActor2D().GetCaptionTextProperty().ShallowCopy(tp)

    # add to an orientation widget
    orient_widget = vtkOrientationMarkerWidget()
    orient_widget.SetOrientationMarker(axes)
    orient_widget.SetViewport(0.9, 0.0, 1.0, 0.2)
    orient_widget.SetZoom(1.1)
    orient_widget.SetInteractor(inter)
    orient_widget.EnabledOn()
    orient_widget.InteractiveOff()

    # use gradient background
    renderer = win.GetRenderers().GetFirstRenderer()
    renderer.GradientBackgroundOn()

    # use FXXAA
    renderer.UseFXAAOn()

    # set camera
    camera = renderer.GetActiveCamera()
    camera.Roll(-35)
    camera.Elevation(-45)
    renderer.ResetCamera()

    # add pts and locs
    renderer.AddActor(pts)
    renderer.AddActor(axs)

    # add other vtk actors
    for a in acts:
        renderer.AddActor(a)

    # initialize and set size
    inter.Initialize()
    win.SetSize(*win.GetScreenSize())
    win.SetPosition(-10, 0)

    # show and return
    win.Render()
    inter.Start()


# alias
show_object = show
