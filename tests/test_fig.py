from cadquery import Workplane, Assembly, Sketch, Vector, Location
from cadquery.func import box
from cadquery.vis import vtkAxesActor, ctrlPts
from cadquery.fig import Figure

from pytest import fixture, mark


@fixture(scope="module")
def fig():
    return Figure()


@mark.gui
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

    # individual showables
    fig.show(s, wp, assy, sk, ctrl_pts, v, loc, act)

    # fit
    fig.fit()

    # clear
    fig.clear()

    # lists of showables
    fig.show(s.Edges()).show([Vector(), Vector(0, 1)])

    # displaying nonsense does not throw
    fig.show("a").show(["a", 1234])

    # pop
    fig.show(s, color="red")
    fig.pop()
