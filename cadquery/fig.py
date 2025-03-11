from asyncio import (
    new_event_loop,
    set_event_loop,
    run_coroutine_threadsafe,
    AbstractEventLoop,
)
from threading import Thread

from trame.app import get_server, Server
from trame.widgets import html, vtk as vtk_widgets, client
from trame.ui.html import DivLayout

from cadquery import Shape
from cadquery.vis import style

from vtkmodules.vtkRenderingCore import (
    vtkRenderer,
    vtkRenderWindow,
    vtkRenderWindowInteractor,
    vtkActor,
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
    shapes: dict[Shape, list[vtkProp3D]]
    actors: list[vtkProp3D]
    loop: AbstractEventLoop
    thread: Thread

    def __init__(self, port: int):

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
        server = get_server("CQ")
        server.client_type = "vue3"

        # layout
        with DivLayout(server):
            client.Style("body { margin: 0; }")

            with html.Div(style=FULL_SCREEN):
                self.view = vtk_widgets.VtkRemoteView(
                    win, interactive_ratio=1, interactive_quality=100
                )

        server.state.flush()
        coro = server.start(
            thread=True, exec_mode="coroutine", port=port, open_browser=True
        )

        self.server = server
        self.loop = new_event_loop()

        def _run():
            set_event_loop(self.loop)
            self.loop.run_forever()

        self.thread = Thread(target=_run, daemon=True)
        self.thread.start()

        run_coroutine_threadsafe(coro, self.loop)

    def _run(self, coro):

        run_coroutine_threadsafe(coro, self.loop)

    def show(self, s: Shape | vtkActor | list[vtkProp3D], *args, **kwargs):
        async def _show():

            if isinstance(s, Shape):
                # do not show markers by default
                if "markersize" not in kwargs:
                    kwargs["markersize"] = 0

                actors = style(s, *args, **kwargs)
                self.shapes[s] = actors

                for actor in actors:
                    self.ren.AddActor(actor)

            elif isinstance(s, vtkActor):
                self.actors.append(s)
                self.ren.AddActor(s)
            else:
                self.actors.extend(s)

                for el in s:
                    self.ren.AddActor(el)

            self.ren.ResetCamera()
            self.view.update()

        self._run(_show())

    def clear(self, *shapes: Shape | vtkActor):
        async def _clear():

            if len(shapes) == 0:
                for a in self.actors:
                    self.ren.RemoveActor(a)

                for actors in self.shapes.values():
                    for a in actors:
                        self.ren.RemoveActor(a)

            for s in shapes:
                if isinstance(s, Shape):
                    for a in self.shapes[s]:
                        self.ren.RemoveActor(a)

                    del self.shapes[s]
                else:
                    self.actors.remove(s)
                    self.ren.RemoveActor(s)

            self.ren.ResetCamera()
            self.view.update()

        self._run(_clear())
