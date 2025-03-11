import asyncio

from typing import Any, cast

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
    shapes: dict[Shape, vtkProp3D]
    actors: list[vtkProp3D]
    loop: Any

    def __init__(self, port: int):

        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

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
        server = get_server(123)
        server.client_type = "vue3"

        # layout
        with DivLayout(server):
            client.Style("body { margin: 0; }")

            with html.Div(style=FULL_SCREEN):
                self.view = vtk_widgets.VtkRemoteView(
                    win, interactive_ratio=1, interactive_quality=100
                )

        server.state.flush()
        server.start(thread=True, exec_mode="task", port=port, open_browser=True)

        self.server = server

    def show(self, s: Shape | vtkActor | list[vtkProp3D], *args, **kwargs):

        if isinstance(s, Shape):
            actor = style(s, *args, **kwargs)[0]
            self.shapes[s] = actor
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

    def clear(self, s: Shape | vtkActor):

        if isinstance(s, Shape):
            actor = self.shapes[s]
            self.ren.RemoveActor(actor)

            del self.shapes[s]

        else:
            self.actors.remove(s)
            self.ren.RemoveActor(s)

        self.ren.ResetCamera()
        self.view.update()
