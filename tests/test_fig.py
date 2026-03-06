from cadquery import Workplane, Assembly, Sketch, Vector, Location
from cadquery.func import box
from cadquery.vis import vtkAxesActor, ctrlPts
from cadquery.fig import Figure

from pytest import fixture, mark

from sys import platform


@fixture(scope="module")
def fig():
    return Figure()


@mark.gui
@mark.skipif(platform != "win32", reason="CI with UI only works on win for now")
def test_fig(fig):

    # showables
    s = box(1, 1, 1)
    wp = Workplane().box(1, 1, 1)
    assy = Assembly().add(box(1, 1, 1))
    sk = Sketch().rect(1, 1)
    ctrl_pts = ctrlPts(sk.val().toNURBS())
    v = Vector()
    loc = Location()
    act = vtkAxesActor()

    showables = (s, s.copy(), wp, assy, sk, ctrl_pts, v, loc, act)

    # individual showables
    fig.show(*showables)

    # fit
    fig.fit()

    # views
    fig.iso()
    fig.up()
    fig.front()
    fig.side()

    # clear
    fig.clear()

    # clear with an arg
    for showable in showables:
        fig.show(showable)

    for el in (s, wp, assy, sk, ctrl_pts):
        fig.clear(el)

    # show multiple showables at once
    fig.clear()
    fig.show(*showables)

    # more than one Solid showable -> more than 2 actors
    assert len(list(fig.actors.values())[-1]) > 2

    # lists of showables
    fig.show(s.Edges()).show([Vector(), Vector(0, 1)])

    # displaying nonsense does not throw
    fig.show("a").show(["a", 1234])

    # pop
    for el in showables:
        fig.show(el, color="red")
        fig.pop()

    # test singleton behavior of fig
    fig2 = Figure()
    assert fig is fig2

    # test onSelection
    fig.onVisibility(fig.state.actors[0])

    # test onVisbility
    fig.onSelection([fig.state.actors[0]])
