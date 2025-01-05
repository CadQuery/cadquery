from cadquery import Workplane, Assembly, Sketch, Location, Vector
from cadquery.vis import show, show_object, vtkAxesActor

import cadquery.vis as vis

from vtkmodules.vtkRenderingCore import vtkRenderWindow, vtkRenderWindowInteractor
from vtkmodules.vtkRenderingAnnotation import vtkAnnotatedCubeActor

from pytest import fixture


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


def test_show(wp, assy, sk, monkeypatch):

    # use some dummy vtk objects
    monkeypatch.setattr(vis, "vtkRenderWindowInteractor", FakeInteractor)
    monkeypatch.setattr(vis, "vtkRenderWindow", FakeWindow)

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
