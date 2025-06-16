from asyncio import (
    new_event_loop,
    set_event_loop,
    run_coroutine_threadsafe,
    AbstractEventLoop,
)
from concurrent.futures import Future
from typing import Optional
from threading import Thread
from itertools import chain
from webbrowser import open_new_tab

from typish import instance_of

from trame.app import get_server
from trame.app.core import Server
from trame.widgets import html, vtk as vtk_widgets, client
from trame.ui.html import DivLayout

from . import Shape
from .vis import style, Showable, ShapeLike, _split_showables

from vtkmodules.vtkRenderingCore import (
    vtkRenderer,
    vtkRenderWindow,
    vtkRenderWindowInteractor,
    vtkProp3D,
)


from vtkmodules.vtkInteractionWidgets import vtkOrientationMarkerWidget
from vtkmodules.vtkRenderingAnnotation import vtkAxesActor

from vtkmodules.vtkInteractionStyle import vtkInteractorStyleTrackballCamera

FULL_SCREEN = "position:absolute; left:0; top:0; width:100vw; height:100vh;"


class Figure:

    server: Server
    win: vtkRenderWindow
    ren: vtkRenderer
    view: vtk_widgets.VtkRemoteView
    shapes: dict[ShapeLike, list[vtkProp3D]]
    actors: list[vtkProp3D]
    loop: AbstractEventLoop
    thread: Thread
    empty: bool
    last: Optional[
        tuple[
            list[ShapeLike], list[vtkProp3D], Optional[list[vtkProp3D]], list[vtkProp3D]
        ]
    ]

    _instance = None
    _initialized: bool = False

    def __new__(cls, *args, **kwargs):

        if not cls._instance:
            cls._instance = object.__new__(cls)

        return cls._instance

    def __init__(self, port: int = 18081):

        if self._initialized:
            return

        self.loop = new_event_loop()
        set_event_loop(self.loop)

        # vtk boilerplate
        renderer = vtkRenderer()
        win = vtkRenderWindow()
        w, h = win.GetScreenSize()
        win.SetSize(w, h)
        win.AddRenderer(renderer)
        win.OffScreenRenderingOn()

        inter = vtkRenderWindowInteractor()
        inter.SetInteractorStyle(vtkInteractorStyleTrackballCamera())
        inter.SetRenderWindow(win)

        # background
        renderer.SetBackground(1, 1, 1)
        renderer.GradientBackgroundOn()

        # axes
        axes = vtkAxesActor()
        axes.SetDragable(0)

        orient_widget = vtkOrientationMarkerWidget()

        orient_widget.SetOrientationMarker(axes)
        orient_widget.SetViewport(0.9, 0.0, 1.0, 0.2)
        orient_widget.SetZoom(1.1)
        orient_widget.SetInteractor(inter)
        orient_widget.SetCurrentRenderer(renderer)
        orient_widget.EnabledOn()
        orient_widget.InteractiveOff()

        self.axes = axes
        self.orient_widget = orient_widget
        self.win = win
        self.ren = renderer

        self.shapes = {}
        self.actors = []

        # server
        server = get_server("CQ-server")
        server.client_type = "vue3"

        # layout
        with DivLayout(server):
            client.Style("body { margin: 0; }")

            with html.Div(style=FULL_SCREEN):
                self.view = vtk_widgets.VtkRemoteView(
                    win, interactive_ratio=1, interactive_quality=100
                )

        server.state.flush()

        self.server = server
        self.loop = new_event_loop()

        def _run_loop():
            set_event_loop(self.loop)
            self.loop.run_forever()

        self.thread = Thread(target=_run_loop, daemon=True)
        self.thread.start()

        coro = server.start(
            thread=True,
            exec_mode="coroutine",
            port=port,
            open_browser=False,
            show_connection_info=False,
        )

        if coro:
            self._run(coro)

        # prevent reinitialization
        self._initialized = True

        # view is initialized as empty
        self.empty = True
        self.last = None

        # open webbrowser
        open_new_tab(f"http://localhost:{port}")

    def _run(self, coro) -> Future:

        return run_coroutine_threadsafe(coro, self.loop)

    def show(self, *showables: Showable | vtkProp3D | list[vtkProp3D], **kwargs):
        """
        Show objects.
        """

        # split objects
        shapes, vecs, locs, props = _split_showables(showables)

        pts = style(vecs, **kwargs)
        axs = style(locs, **kwargs)

        for s in shapes:
            # do not show markers by default
            if "markersize" not in kwargs:
                kwargs["markersize"] = 0

            actors = style(s, **kwargs)
            self.shapes[s] = actors

            for actor in actors:
                self.ren.AddActor(actor)

        for prop in chain(props, axs):
            self.actors.append(prop)
            self.ren.AddActor(prop)

        if vecs:
            self.actors.append(*pts)
            self.ren.AddActor(*pts)

        # store to enable pop
        self.last = (shapes, axs, pts if vecs else None, props)

        async def _show():
            self.view.update()

        self._run(_show())

        # zoom to fit on 1st object added
        if self.empty:
            self.fit()
            self.empty = False

        return self

    def fit(self):
        """
        Update view to fit all objects.
        """

        async def _show():
            self.ren.ResetCamera()
            self.view.update()

        self._run(_show())

        return self

    def clear(self, *shapes: Shape | vtkProp3D):
        """
        Clear specified objects. If no arguments are passed, clears all objects.
        """

        async def _clear():

            if len(shapes) == 0:
                self.ren.RemoveAllViewProps()

                self.actors.clear()
                self.shapes.clear()

            for s in shapes:
                if instance_of(s, ShapeLike):
                    for a in self.shapes[s]:
                        self.ren.RemoveActor(a)

                    del self.shapes[s]
                else:
                    self.actors.remove(s)
                    self.ren.RemoveActor(s)

            self.view.update()

        # reset last, bc we don't want to keep track of what was removed
        self.last = None
        future = self._run(_clear())
        future.result()

        return self

    def pop(self):
        """
        Clear the last showable.
        """

        async def _pop():

            (shapes, axs, pts, props) = self.last

            for s in shapes:
                for act in self.shapes.pop(s):
                    self.ren.RemoveActor(act)

            for act in chain(axs, props):
                self.ren.RemoveActor(act)
                self.actors.remove(act)

            if pts:
                self.ren.RemoveActor(*pts)
                self.actors.remove(*pts)

            self.view.update()

        self._run(_pop())

        return self
