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
from uuid import uuid1

from trame.app import get_server
from trame.app.core import Server
from trame.widgets import vtk as vtk_widgets, client, trame, vuetify3 as v3
from trame.ui.vuetify3 import SinglePageWithDrawerLayout
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

from .utils import instance_of

FULL_SCREEN = "position:absolute; left:0; top:0; width:100vw; height:100vh;"


class Figure:

    server: Server
    win: vtkRenderWindow
    ren: vtkRenderer
    view: vtk_widgets.VtkRemoteView
    shapes: dict[ShapeLike, str]
    actors: dict[str, tuple[vtkProp3D, ...]]
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
        self.actors = {}
        self.active = None

        # server
        server = get_server("CQ-server", client_type="vue3")
        self.server = server

        # state
        self.state = self.server.state

        self.state.setdefault("selected", [])
        self.state.setdefault("actors", [])

        # layout
        self.layout = SinglePageWithDrawerLayout(server, show_drawer=False)
        with self.layout as layout:
            client.Style("body { margin: 0; }")

            layout.title.set_text("CQ viewer")
            layout.footer.hide()

            with layout.toolbar:

                BSTYLE = "display: block;"

                v3.VBtn(
                    click=lambda: self._fit(),
                    flat=True,
                    density="compact",
                    icon="mdi-crop-free",
                    style=BSTYLE,
                )

                v3.VBtn(
                    click=lambda: self._view((0, 0, 0), (1, 1, 1), (0, 0, 1)),
                    flat=True,
                    density="compact",
                    icon="mdi-axis-arrow",
                    style=BSTYLE,
                )

                v3.VBtn(
                    click=lambda: self._view((0, 0, 0), (1, 0, 0), (0, 0, 1)),
                    flat=True,
                    density="compact",
                    icon="mdi-axis-x-arrow",
                    style=BSTYLE,
                )

                v3.VBtn(
                    click=lambda: self._view((0, 0, 0), (0, 1, 0), (0, 0, 1)),
                    flat=True,
                    density="compact",
                    icon="mdi-axis-y-arrow",
                    style=BSTYLE,
                )

                v3.VBtn(
                    click=lambda: self._view((0, 0, 0), (0, 0, 1), (0, 1, 0)),
                    flat=True,
                    density="compact",
                    icon="mdi-axis-z-arrow",
                    style=BSTYLE,
                )

                v3.VBtn(
                    click=lambda: self._pop(),
                    flat=True,
                    density="compact",
                    icon="mdi-file-document-remove-outline",
                    style=BSTYLE,
                )

                v3.VBtn(
                    click=lambda: self._clear([]),
                    flat=True,
                    density="compact",
                    icon="mdi-delete-outline",
                    style=BSTYLE,
                )

            with layout.content:
                with v3.VContainer(
                    fluid=True, classes="pa-0 fill-height",
                ):
                    self.view = vtk_widgets.VtkRemoteView(
                        win, interactive_ratio=1, interactive_quality=100
                    )

            with layout.drawer:
                self.tree = trame.GitTree(
                    sources=("actors", []),
                    actives=("selected", []),
                    visibility_change=(self.onVisibility, "[$event]"),
                    actives_change=(self.onSelection, "[$event]"),
                )

        server.state.flush()

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

    def _update_state(self, name: str):
        async def _():

            self.state.dirty(name)
            self.state.flush()

        self._run(_())

    def show(
        self,
        *showables: Showable | vtkProp3D | list[vtkProp3D],
        name: Optional[str] = None,
        **kwargs,
    ):
        """
        Show objects.
        """

        # genreate an uuid
        uuid = str(uuid1())

        # split objects
        shapes, vecs, locs, props = _split_showables(showables)

        pts = style(vecs, **kwargs)
        axs = style(locs, **kwargs)

        # to be added to state
        new_actors = []

        for s in shapes:
            # do not show markers by default
            if "markersize" not in kwargs:
                kwargs["markersize"] = 0

            actors = style(s, **kwargs)
            self.shapes[s] = uuid

            for actor in actors:
                self.ren.AddActor(actor)

            new_actors.extend(actors)

        for prop in chain(props, axs):
            self.ren.AddActor(prop)

            new_actors.append(prop)

        if vecs:
            self.ren.AddActor(*pts)

            new_actors.append(*pts)

        # store to enable pop
        self.last = (shapes, axs, pts if vecs else None, props)

        async def _show():
            self.view.update()

        self._run(_show())

        # zoom to fit on 1st object added
        if self.empty:
            self.fit()
            self.empty = False

        # update actors
        self.state.actors.append(
            {
                "id": uuid,
                "parent": "0",
                "visible": 1,
                "name": f"{name if name else type(showables[0]).__name__} at {id(showables[0]):x}",
            }
        )
        self._update_state("actors")

        self.actors[uuid] = tuple(new_actors)

        return self

    async def _fit(self):
        self.ren.ResetCamera()
        self.view.update()

    def fit(self):
        """
        Update view to fit all objects.
        """

        self._run(self._fit())

        return self

    async def _view(self, foc, pos, up):

        cam = self.ren.GetActiveCamera()

        cam.SetViewUp(*up)
        cam.SetFocalPoint(*foc)
        cam.SetPosition(*pos)

        self.ren.ResetCamera()

        self.view.update()

    def iso(self):

        self._run(self._view((0, 0, 0), (1, 1, 1), (0, 0, 1)))

        return self

    def up(self):

        self._run(self._view((0, 0, 0), (0, 0, 1), (0, 1, 0)))

        return self

        pass

    def front(self):

        self._run(self._view((0, 0, 0), (1, 0, 0), (0, 0, 1)))

        return self

    def side(self):

        self._run(self._view((0, 0, 0), (0, 1, 0), (0, 0, 1)))

        return self

    async def _clear(self, shapes):

        if len(shapes) == 0:
            self.ren.RemoveAllViewProps()

            self.actors.clear()
            self.shapes.clear()

            self.state.actors = []
            self.active = None

        for s in shapes:
            # handle shapes
            if instance_of(s, ShapeLike):
                uuid = self.shapes[s]
                for a in self.actors.pop(uuid):
                    self.ren.RemoveActor(a)

                del self.shapes[s]

            # handle other actors
            else:
                for uuid, acts in self.actors.items():
                    if s in acts:
                        for el in self.actors.pop(uuid):
                            self.ren.RemoveActor(el)

                        break

            # remove the id==k row from actors
            for ix, el in enumerate(self.state.actors):
                if el["id"] == uuid:
                    break

            self.state.actors.pop(ix)

        self._update_state("actors")
        self.view.update()

    def clear(self, *shapes: Shape | vtkProp3D):
        """
        Clear specified objects. If no arguments are passed, clears all objects.
        """

        # reset last, bc we don't want to keep track of what was removed
        self.last = None
        future = self._run(self._clear(shapes))
        future.result()

        return self

    async def _pop(self):

        if self.active is None:
            self.active = self.actors[-1]["id"]

        if self.active in self.actors:
            for act in self.actors[self.active]:
                self.ren.RemoveActor(act)

            self.actors.pop(self.active)

            # update corresponding state
            for i, el in enumerate(self.state.actors):
                if el["id"] == self.active:
                    self.state.actors.pop(i)
                    self._update_state("actors")
                    break

            self.active = None

        else:
            return

        self.view.update()

    def pop(self):
        """
        Clear the selected showable.
        """

        self._run(self._pop())

        return self

    def onVisibility(self, event):

        actors = self.actors[event["id"]]

        for act in actors:
            act.SetVisibility(event["visible"])

        self.view.update()

    def onSelection(self, event):

        self.state.selected = event
        self.active = event[0]
