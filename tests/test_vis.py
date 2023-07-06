from cadquery import Workplane, Assembly, Sketch
from cadquery.vis import show, show_object

import cadquery.occ_impl.exporters.assembly as assembly
import cadquery.vis as vis

from vtkmodules.vtkRenderingCore import vtkRenderWindow, vtkRenderWindowInteractor

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
    monkeypatch.setattr(assembly, "vtkRenderWindow", FakeWindow)

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
