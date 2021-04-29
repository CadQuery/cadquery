from typing import Dict, Any, List
from json import dumps

from IPython.display import Javascript


from .exporters.vtk import toString
from .shapes import Shape
from ..assembly import Assembly
from .assembly import toJSON

TEMPLATE = """
var data = {data}

function render(data){{
    
    // Initial setup
    const renderWindow = vtk.Rendering.Core.vtkRenderWindow.newInstance();
    const renderer = vtk.Rendering.Core.vtkRenderer.newInstance({{ background: [1, 1, 1 ] }});
    renderWindow.addRenderer(renderer);
        
    // iterate over all children children
    data.forEach(
        function(el){{
            var trans = el.position;
            var rot = el.orientation;
            var rgba = el.color;
            var shape = el.shape;
            
            // load the inline data
            var reader = vtk.IO.XML.vtkXMLPolyDataReader.newInstance();
            const textEncoder = new TextEncoder();
            reader.parseAsArrayBuffer(textEncoder.encode(shape));

            // setup actor,mapper and add
            const mapper = vtk.Rendering.Core.vtkMapper.newInstance();
            mapper.setInputConnection(reader.getOutputPort());

            const actor = vtk.Rendering.Core.vtkActor.newInstance();
            actor.setMapper(mapper);

            // set color and position
            console.log(rgba);
            actor.getProperty().setColor(rgba.slice(0,3));
            actor.getProperty().setOpacity(rgba[3]);
            
            actor.rotateZ(rot[2]*180/3.1416);
            actor.rotateY(rot[1]*180/3.1416);
            actor.rotateX(rot[0]*180/3.1416);
            
            actor.setPosition(trans);
            

            renderer.addActor(actor);
            
            console.log(actor);
        }}
    );
    
    renderer.resetCamera();
    
    const openglRenderWindow = vtk.Rendering.OpenGL.vtkRenderWindow.newInstance();
    renderWindow.addView(openglRenderWindow);

    // Add output to the "element"

    const container = element.get(0);//createElement('div');
    console.log(container);
    container.style.height = '500px';
    container.style.width = '700px';
    container.style.margin = 'auto';
    openglRenderWindow.setContainer(container);
    openglRenderWindow.setSize({w}, {h});
    
    // Interaction setup

    const interactor = vtk.Rendering.Core.vtkRenderWindowInteractor.newInstance();
    interactor.setView(openglRenderWindow);
    interactor.initialize();
    interactor.bindEvents(container);
    interactor.setInteractorStyle(vtk.Interaction.Style.vtkInteractorStyleTrackballCamera.newInstance());

    // Orientation marker

    const axes = vtk.Rendering.Core.vtkAnnotatedCubeActor.newInstance();
    axes.setXPlusFaceProperty({{text: '+X'}});
    axes.setXMinusFaceProperty({{text: '-X'}});
    axes.setYPlusFaceProperty({{text: '+Y'}});
    axes.setYMinusFaceProperty({{text: '-Y'}});
    axes.setZPlusFaceProperty({{text: '+Z'}});
    axes.setZMinusFaceProperty({{text: '-Z'}});

    const orientationWidget = vtk.Interaction.Widgets.vtkOrientationMarkerWidget.newInstance({{
        actor: axes,
        interactor: interactor }});
    orientationWidget.setEnabled(true);
    orientationWidget.setViewportCorner(vtk.Interaction.Widgets.vtkOrientationMarkerWidget.Corners.BOTTOM_LEFT);
    orientationWidget.setViewportSize(0.2);
    
    // Disable keyboard events

    interactor.handleKeyPress = (event) => {{}};

}};

render(data);
"""


def display(shape):

    payload: List[Dict[str, Any]] = []

    if isinstance(shape, Shape):
        payload.append(
            dict(
                shape=toString(shape),
                color=[1, 0.8, 0, 1],
                position=[0, 0, 0],
                orientation=[0, 0, 0],
            )
        )
    elif isinstance(shape, Assembly):
        payload = toJSON(shape)
    else:
        raise ValueError(f"Type {type(shape)} is not supported")

    code = TEMPLATE.format(data=dumps(payload), w=1000, h=500)

    return Javascript(code, lib="https://unpkg.com/vtk.js")
