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
)

FULL_SCREEN = "position:absolute; left:0; top:0; width:100vw; height:100vh;"


class Figure:

    server: Server
    win: vtkRenderWindow
    ren: vtkRenderer
    shapes: dict[Shape, tuple[vtkActor, ...]]
    actors: list[vtkActor]

    def __init__(self, port: int):

        # vtk boilerplate
        renderer = vtkRenderer()
        win = vtkRenderWindow()
        win.AddRenderer(renderer)
        win.OffScreenRenderingOn()

        inter = vtkRenderWindowInteractor()
        inter.SetRenderWindow(win)
        inter.GetInteractorStyle().SetCurrentStyleToTrackballCamera()

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
                vtk_widgets.VtkRemoteView(
                    win, interactive_ratio=1, interactive_quality=100
                )

        server.state.flush()
        server.start(thread=True, exec_mode="task", port=port, open_browser=True)

        self.server = server

    def show(self, s: Shape | vtkActor, *args, **kwargs):

        if isinstance(s, Shape):
            actors = style(s, *args, **kwargs)
            self.shapes[s] = actors

            for a in actors:
                self.ren.AddActor(a)
        else:
            self.actors.append(s)
            self.ren.AddActor(s)

        self.ren.ResetCamera()

    def hide(self, s: Shape | vtkActor):

        if isinstance(s, Shape):
            actors = self.shapes[s]

            for a in actors:
                self.ren.RemoveActor(a)

            del self.shapes[s]

        else:
            self.actors.remove(s)
            self.ren.RemoveActor(s)

        self.ren.ResetCamera()
