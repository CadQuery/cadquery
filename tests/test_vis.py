from cadquery import Workplane, Assembly, Sketch, Location, Vector
from cadquery.func import circle, sweep, spline, plane, torus
from cadquery.vis import show, show_object, vtkAxesActor, ctrlPts, style

import cadquery.vis as vis

from vtkmodules.vtkRenderingCore import (
    vtkRenderWindow,
    vtkRenderWindowInteractor,
    vtkWindowToImageFilter,
    vtkActor,
    vtkAssembly,
)
from vtkmodules.vtkRenderingAnnotation import vtkAnnotatedCubeActor
from vtkmodules.vtkIOImage import vtkPNGWriter

from pytest import fixture, raises
from path import Path


@fixture(scope="module")
def tmpdir(tmp_path_factory):
    return Path(tmp_path_factory.mktemp("screenshots"))


@fixture
def wp():

    return Workplane().box(1, 1, 1)


@fixture
def assy(wp):

    return Assembly().add(wp)


@fixture
def sk():

    return Sketch().circle(1.0)


class FakeInteractor(vtkRenderWindowInteractor):
    def Start(self):

        pass

    def Initialize(self):

        pass


class FakeWindow(vtkRenderWindow):
    def Render(*args):

        pass

    def SetSize(*args):

        pass

    def GetScreenSize(*args):

        return 1, 1

    def SetPosition(*args):

        pass

    def SetOffScreenRendering(*args):

        pass


class FakeWin2Img(vtkWindowToImageFilter):
    def Update(*args):

        pass


class FakePNGWriter(vtkPNGWriter):
    def Write(*args):

        pass


@fixture
def patch_vtk(monkeypatch):
    """
    Fixture needed to not show anything during testing / prevent crashes in CI.
    """

    # use some dummy vtk objects
    monkeypatch.setattr(vis, "vtkRenderWindowInteractor", FakeInteractor)
    monkeypatch.setattr(vis, "vtkRenderWindow", FakeWindow)
    monkeypatch.setattr(vis, "vtkWindowToImageFilter", FakeWin2Img)
    monkeypatch.setattr(vis, "vtkPNGWriter", FakePNGWriter)


def test_show(wp, assy, sk, patch_vtk):

    # simple smoke test
    show(wp)
    show(wp.val())
    show(wp.val().wrapped)
    show(assy)
    show(sk)
    show(wp, sk, assy, wp.val())
    show(Vector())
    show(Location())
    show([Vector, Vector, Location])
    show([wp, assy])
    show()

    # show with edges
    show(wp, edges=True)

    show_object(wp)
    show_object(wp.val())
    show_object(assy)
    show_object(sk)
    show_object(wp, sk, assy, wp.val())
    show_object()

    # for compatibility with CQ-editor
    show_object(wp, "a")

    # for now a workaround to be compatible with more complicated CQ-editor invocations
    show(1)

    # show a raw vtkProp
    show(vtkAxesActor(), [vtkAnnotatedCubeActor()])


def test_screenshot(wp, tmpdir, patch_vtk):

    # smoke test for now
    with tmpdir:
        show(wp, interact=False, screenshot="img.png", trihedron=False, gradient=False)


def test_ctrlPts():

    c = circle(1)

    # non-NURBS objects throw
    with raises(ValueError):
        ctrlPts(c)

    # control points of a curve
    a1 = ctrlPts(c.toNURBS())
    assert isinstance(a1, vtkActor)

    # control points of a non-periodic curve
    a2 = ctrlPts(c.trim(0, 1).toNURBS())
    assert isinstance(a2, vtkActor)

    # non-NURBS objects throw
    with raises(ValueError):
        ctrlPts(plane(1, 1))

    # control points of a surface
    a3 = ctrlPts(sweep(c.trim(0, 1), spline((0, 0, 0), (0, 0, 1))))
    assert isinstance(a3, vtkActor)

    # control points of a u,v periodic surface
    a4 = ctrlPts(torus(5, 1).faces().toNURBS())
    assert isinstance(a4, vtkActor)


def test_style(wp, assy):

    t = torus(10, 1)
    e = t.Edges()[0]
    pts = e.sample(10)[0]
    locs = e.locations([0, 0.5, 0.75])

    # Shape
    act = style(t, color="red", alpha=0.5, tubes=True, spheres=True)
    assert isinstance(act, (vtkActor, vtkAssembly))

    # Assy
    act = style(assy, color="red", alpha=0.5, tubes=True, spheres=True)
    assert isinstance(act, (vtkActor, vtkAssembly))

    # Workplane
    act = style(wp, color="red", alpha=0.5, tubes=True, spheres=True)
    assert isinstance(act, (vtkActor, vtkAssembly))

    # Shape
    act = style(e)
    assert isinstance(act, (vtkActor, vtkAssembly))

    # Sketch
    act = style(Sketch().circle(1))
    assert isinstance(act, (vtkActor, vtkAssembly))

    # list[Vector]
    act = style(pts)
    assert isinstance(act, (vtkActor, vtkAssembly))

    # list[Location]
    act = style(locs)
    assert isinstance(act, (vtkActor, vtkAssembly))

    # vtkAssembly
    act = style(style(t))
    assert isinstance(act, (vtkActor, vtkAssembly))

    # vtkActor
    act = style(ctrlPts(e.toNURBS()))
    assert isinstance(act, (vtkActor, vtkAssembly))


def test_camera_position(wp, patch_vtk):

    show(wp, position=(0, 0, 1), focus=(0, 0.1, 0))
    show(wp, focus=(0, 0.1, 0))
    show(wp, position=(0, 0, 1))
