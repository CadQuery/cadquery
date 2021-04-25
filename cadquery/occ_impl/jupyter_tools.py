from IPython.display import Javascript
from .exporters.vtk import toString

TEMPLATE = """// Initial setup

const renderWindow = vtk.Rendering.Core.vtkRenderWindow.newInstance();
const renderer = vtk.Rendering.Core.vtkRenderer.newInstance({{ background: [1, 1, 1 ] }});
renderWindow.addRenderer(renderer);

// load the inline data
var reader = vtk.IO.XML.vtkXMLPolyDataReader.newInstance();
const textEncoder = new TextEncoder();
reader.parseAsArrayBuffer(textEncoder.encode({data}));

// VTK pipeline setup
const mapper = vtk.Rendering.Core.vtkMapper.newInstance();
mapper.setInputConnection(reader.getOutputPort());

const actor = vtk.Rendering.Core.vtkActor.newInstance();
actor.setMapper(mapper);
actor.getProperty().setColor([1,0.8,0])

renderer.addActor(actor);
renderer.resetCamera();

// Use OpenGl

const openglRenderWindow = vtk.Rendering.OpenGL.vtkRenderWindow.newInstance();
renderWindow.addView(openglRenderWindow);

// Add output to the "element"

const container = element.get(0);
openglRenderWindow.setContainer(container);
openglRenderWindow.setSize({w}, {h});

// Interaction setup

const interactor = vtk.Rendering.Core.vtkRenderWindowInteractor.newInstance();
interactor.setView(openglRenderWindow);
interactor.initialize();
interactor.bindEvents(container);
interactor.setInteractorStyle(vtk.Interaction.Style.vtkInteractorStyleTrackballCamera.newInstance());
"""


def display(shape):

    data = toString(shape)
    code = TEMPLATE.format(data=repr(data), w=1000, h=500)

    return Javascript(code, lib="https://unpkg.com/vtk.js")
