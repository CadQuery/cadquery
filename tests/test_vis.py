from cadquery import Workplane, Assembly, Sketch
from cadquery.vis import show, show_object

import cadquery.vis as vis

from pytest import fixture, raises


@fixture
def wp():

    return Workplane().box(1, 1, 1)


@fixture
def assy(wp):

    return Assembly().add(wp)


@fixture
def sk():

    return Sketch().circle(1.0)


class FakeInteractor:
    def SetInteractorStyle(self, x):

        pass

    def SetRenderWindow(self, x):

        pass

    def Initialize(self):

        pass

    def Start(self):

        pass


class FakeOrientationWidget:
    def SetOrientationMarker(*args):

        pass

    def SetViewport(*args):

        pass

    def SetZoom(*args):

        pass

    def SetInteractor(*args):

        pass

    def EnabledOn(*args):

        pass

    def InteractiveOff(*args):

        pass


def test_show(wp, assy, sk, monkeypatch):

    # use some dummy vtk objects
    monkeypatch.setattr(vis, "vtkRenderWindowInteractor", FakeInteractor)
    monkeypatch.setattr(vis, "vtkOrientationMarkerWidget", FakeOrientationWidget)

    # simple smoke test
    show(wp)
    show(wp.val())
    show(assy)
    show(sk)
    show(wp, sk, assy, wp.val())
    show()

    with raises(ValueError):
        show(1)

    show_object(wp)
    show_object(wp.val())
    show_object(assy)
    show_object(sk)
    show_object(wp, sk, assy, wp.val())
    show_object()

    with raises(ValueError):
        show_object("a")
