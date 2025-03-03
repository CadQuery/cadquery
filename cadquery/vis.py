from . import (
    Shape,
    Workplane,
    Assembly,
    Sketch,
    Compound,
    Color,
    Vector,
    Location,
    Face,
    Edge,
)
from .occ_impl.assembly import _loc2vtk, toVTKAssy

from typing import Union, Any, List, Tuple, Iterable, cast, Optional

from typish import instance_of

from OCP.TopoDS import TopoDS_Shape
from OCP.Geom import Geom_BSplineSurface

from vtkmodules.vtkInteractionWidgets import vtkOrientationMarkerWidget
from vtkmodules.vtkRenderingAnnotation import vtkAxesActor
from vtkmodules.vtkInteractionStyle import vtkInteractorStyleTrackballCamera
from vtkmodules.vtkRenderingCore import (
    vtkMapper,
    vtkRenderWindowInteractor,
    vtkActor,
    vtkProp3D,
    vtkPolyDataMapper,
    vtkAssembly,
    vtkRenderWindow,
    vtkWindowToImageFilter,
    vtkRenderer,
    vtkPropCollection,
)
from vtkmodules.vtkCommonCore import vtkPoints
from vtkmodules.vtkCommonDataModel import vtkCellArray, vtkPolyData
from vtkmodules.vtkCommonColor import vtkNamedColors
from vtkmodules.vtkIOImage import vtkPNGWriter


DEFAULT_COLOR = (1, 0.8, 0)
DEFAULT_EDGE_COLOR = (0, 0, 0)
DEFAULT_PT_SIZE = 7.5
DEFAULT_PT_COLOR = "darkviolet"
DEFAULT_CTRL_PT_COLOR = "crimson"
DEFAULT_CTRL_PT_SIZE = 7.5

SPECULAR = 0.3
SPECULAR_POWER = 100
SPECULAR_COLOR = vtkNamedColors().GetColor3d("White")

ShapeLike = Union[Shape, Workplane, Assembly, Sketch, TopoDS_Shape]
Showable = Union[
    ShapeLike, List[ShapeLike], Vector, List[Vector], vtkProp3D, List[vtkProp3D]
]


def _to_assy(
    *objs: ShapeLike,
    color: Tuple[float, float, float] = DEFAULT_COLOR,
    alpha: float = 1,
) -> Assembly:
    """
    Convert shapes to Assembly.
    """

    assy = Assembly(color=Color(*color, alpha))

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
) -> Tuple[List[ShapeLike], List[Vector], List[Location], List[vtkProp3D]]:
    """
    Split into showables and others.
    """

    rv_s: List[ShapeLike] = []
    rv_v: List[Vector] = []
    rv_l: List[Location] = []
    rv_a: List[vtkProp3D] = []

    for el in objs:
        if instance_of(el, ShapeLike):
            rv_s.append(el)
        elif isinstance(el, Vector):
            rv_v.append(el)
        elif isinstance(el, Location):
            rv_l.append(el)
        elif isinstance(el, vtkProp3D):
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


def _to_vtk_axs(locs: List[Location], scale: float = 0.1) -> vtkAssembly:
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


def _to_vtk_shapes(
    obj: List[ShapeLike],
    color: Tuple[float, float, float] = DEFAULT_COLOR,
    edgecolor: Tuple[float, float, float] = DEFAULT_EDGE_COLOR,
    edges: bool = True,
    linewidth: float = 2,
    alpha: float = 1,
    tolerance: float = 1e-3,
) -> vtkAssembly:
    """
    Convert Shapes to vtkAssembly.
    """

    return toVTKAssy(
        _to_assy(*obj, color=color, alpha=alpha),
        edgecolor=(*edgecolor, 1),
        edges=edges,
        linewidth=linewidth,
        tolerance=tolerance,
    )


def ctrlPts(
    s: Union[Face, Edge],
    size: float = DEFAULT_CTRL_PT_SIZE,
    color: str = DEFAULT_CTRL_PT_COLOR,
) -> vtkActor:
    """
    Convert Edge or Face to a vtkActor representing control points.
    """

    rv = vtkActor()

    mapper = vtkPolyDataMapper()
    points = vtkPoints()
    cells = vtkCellArray()
    data = vtkPolyData()

    data.SetPoints(points)
    data.SetVerts(cells)
    data.SetLines(cells)

    if isinstance(s, Face):

        if isinstance(s._geomAdaptor(), Geom_BSplineSurface):
            surf = cast(Geom_BSplineSurface, s._geomAdaptor())
        else:
            raise ValueError(
                f"Only NURBS surfaces are supported, encountered {s._geomAdaptor()}"
            )

        Nu = surf.NbUPoles()
        Nv = surf.NbVPoles()

        u_periodic = surf.IsUPeriodic()
        v_periodic = surf.IsVPeriodic()

        # add points
        for i in range(Nu):
            for j in range(Nv):
                pt = surf.Pole(i + 1, j + 1)
                points.InsertNextPoint(pt.X(), pt.Y(), pt.Z())

        # u edges
        for j in range(Nv):
            for i in range(Nu - 1):
                cells.InsertNextCell(2, (Nv * i + j, Nv * (i + 1) + j))

            if u_periodic:
                cells.InsertNextCell(2, (Nv * (i + 1) + j, 0 + j))

        # v edges
        for i in range(Nu):
            for j in range(Nv - 1):
                cells.InsertNextCell(2, (Nv * i + j, Nv * i + j + 1))

            if v_periodic:
                cells.InsertNextCell(2, (Nv * i + j + 1, Nv * i + 0))

    else:

        if s.geomType() == "BSPLINE":
            curve = s._geomAdaptor().BSpline()

        else:
            raise ValueError(
                f"Only NURBS curves are supported, encountered {s.geomType()}"
            )

        for pt in curve.Poles():
            points.InsertNextPoint(pt.X(), pt.Y(), pt.Z())

        N = curve.NbPoles()

        for i in range(N - 1):
            cells.InsertNextCell(2, (i, i + 1))

        if curve.IsPeriodic():
            cells.InsertNextCell(2, (i + 1, 0))

    mapper.SetInputData(data)

    rv.SetMapper(mapper)

    props = rv.GetProperty()
    props.SetColor(vtkNamedColors().GetColor3d(color))
    props.SetPointSize(size)
    props.SetLineWidth(size / 3)
    props.SetRenderPointsAsSpheres(True)

    return rv


def _iterate_actors(obj: Union[vtkProp3D, vtkActor, vtkAssembly]) -> Iterable[vtkActor]:
    """
    Iterate over vtkActors, other props are ignored.
    """
    if isinstance(obj, vtkActor):
        yield obj
    elif isinstance(obj, vtkAssembly):
        coll = vtkPropCollection()
        obj.GetActors(coll)

        coll.InitTraversal()
        for i in range(0, coll.GetNumberOfItems()):
            prop = coll.GetNextProp()
            if isinstance(prop, vtkActor):
                yield prop


def style(
    obj: Showable,
    scale: float = 0.2,
    alpha: float = 1,
    tolerance: float = 1e-2,
    edges: bool = True,
    mesh: bool = False,
    specular: bool = True,
    markersize: float = 5,
    linewidth: float = 2,
    spheres: bool = False,
    tubes: bool = False,
    color: str = "gold",
    edgecolor: str = "black",
    meshcolor: str = "lightgrey",
    vertexcolor: str = "cyan",
    **kwargs,
) -> Union[vtkActor, vtkAssembly]:
    """
    Apply styling to CQ objects. To be used in conjunction with show.
    """

    # styling functions
    def _apply_style(actor):
        props = actor.GetProperty()
        props.SetEdgeColor(vtkNamedColors().GetColor3d(meshcolor))
        props.SetVertexColor(vtkNamedColors().GetColor3d(vertexcolor))
        props.SetPointSize(markersize)
        props.SetLineWidth(linewidth)
        props.SetRenderPointsAsSpheres(spheres)
        props.SetRenderLinesAsTubes(tubes)
        props.SetEdgeVisibility(mesh)

        if specular:
            props.SetSpecular(SPECULAR)
            props.SetSpecularPower(SPECULAR_POWER)
            props.SetSpecularColor(SPECULAR_COLOR)

    def _apply_color(actor):
        props = actor.GetProperty()
        props.SetColor(vtkNamedColors().GetColor3d(color))
        props.SetOpacity(alpha)

    # split showables
    shapes, vecs, locs, actors = _split_showables([obj,])

    # convert to a prop
    rv: Union[vtkActor, vtkAssembly]

    if shapes:
        rv = _to_vtk_shapes(
            shapes,
            color=vtkNamedColors().GetColor3d(color),
            edgecolor=vtkNamedColors().GetColor3d(edgecolor),
            edges=edges,
            linewidth=linewidth,
            alpha=alpha,
            tolerance=tolerance,
        )

        # apply style to every actor
        for a in _iterate_actors(rv):
            _apply_style(a)

    elif vecs:
        rv = _to_vtk_pts(vecs)
        _apply_style(rv)
        _apply_color(rv)
    elif locs:
        rv = _to_vtk_axs(locs, scale=scale)
    else:
        rv = vtkAssembly()

        for p in actors:
            for a in _iterate_actors(p):
                _apply_style(a)
                _apply_color(a)
                rv.AddPart(a)

    return rv


def show(
    *objs: Showable,
    scale: float = 0.2,
    alpha: float = 1,
    tolerance: float = 1e-3,
    edges: bool = False,
    specular: bool = True,
    title: str = "CQ viewer",
    screenshot: Optional[str] = None,
    interact: bool = True,
    zoom: float = 1.0,
    roll: float = -35,
    elevation: float = -45,
    position: Optional[Tuple[float, float, float]] = None,
    focus: Optional[Tuple[float, float, float]] = None,
    width: Union[int, float] = 0.5,
    height: Union[int, float] = 0.5,
    trihedron: bool = True,
    bgcolor: tuple[float, float, float] = (1, 1, 1),
    gradient: bool = True,
    xpos: Union[int, float] = 0,
    ypos: Union[int, float] = 0,
):
    """
    Show CQ objects using VTK. This functions optionally allows to make screenshots.
    """

    # split objects
    shapes, vecs, locs, props = _split_showables(objs)

    # construct the assy
    assy = _to_assy(*shapes, alpha=alpha)

    # construct the points and locs
    pts = _to_vtk_pts(vecs)
    axs = _to_vtk_axs(locs, scale=scale)

    # assy+renderer
    renderer = vtkRenderer()
    renderer.AddActor(toVTKAssy(assy, tolerance=tolerance))

    # VTK window boilerplate
    win = vtkRenderWindow()

    # Render off-screen when not interacting
    if not interact:
        win.SetOffScreenRendering(1)

    win.SetWindowName(title)
    win.AddRenderer(renderer)

    # get renderer and actor
    for act in cast(Iterable[vtkActor], renderer.GetActors()):

        propt = act.GetProperty()

        if edges:
            propt.EdgeVisibilityOn()

        if specular:
            propt.SetSpecular(SPECULAR)
            propt.SetSpecularPower(SPECULAR_POWER)
            propt.SetSpecularColor(SPECULAR_COLOR)

    # rendering related settings
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
    if trihedron:
        orient_widget = vtkOrientationMarkerWidget()
        orient_widget.SetOrientationMarker(axes)
        orient_widget.SetViewport(0.9, 0.0, 1.0, 0.2)
        orient_widget.SetZoom(1.1)
        orient_widget.SetInteractor(inter)
        orient_widget.EnabledOn()
        orient_widget.InteractiveOff()

    # use gradient background
    renderer.SetBackground(*bgcolor)

    if gradient:
        renderer.GradientBackgroundOn()

    # use FXXAA
    renderer.UseFXAAOn()

    # add pts and locs
    renderer.AddActor(pts)
    renderer.AddActor(axs)

    # add other vtk actors
    for p in props:
        renderer.AddActor(p)

    # set camera
    camera = renderer.GetActiveCamera()
    camera.Roll(roll)
    camera.Elevation(elevation)
    camera.Zoom(zoom)

    if position or focus:
        if position:
            camera.SetPosition(*position)
        if focus:
            camera.SetFocalPoint(*focus)
    else:
        renderer.ResetCamera()

    # initialize and set size
    inter.Initialize()

    w, h = win.GetScreenSize()
    win.SetSize(
        int(w * width) if isinstance(width, float) else width,
        int(h * height) if isinstance(height, float) else height,
    )  # is height, width specified as float assume it is relative

    # set position
    win.SetPosition(
        int(w * xpos) if isinstance(xpos, float) else xpos,
        int(h * ypos) if isinstance(ypos, float) else ypos,
    )

    # show and return
    win.Render()

    # make a screenshot
    if screenshot:
        win2image = vtkWindowToImageFilter()
        win2image.SetInput(win)
        win2image.SetInputBufferTypeToRGB()
        win2image.ReadFrontBufferOff()
        win2image.Update()

        writer = vtkPNGWriter()
        writer.SetFileName(screenshot)
        writer.SetInputConnection(win2image.GetOutputPort())
        writer.Write()

    # start interaction
    if interact:
        inter.Start()


# alias
show_object = show
