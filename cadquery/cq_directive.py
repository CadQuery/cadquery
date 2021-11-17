"""
A special directive for including a cq object.

"""

import traceback

from pathlib import Path
from uuid import uuid1 as uuid
from textwrap import indent

from cadquery import exporters, Assembly, Compound, Color, Sketch
from cadquery import cqgi
from cadquery.occ_impl.jupyter_tools import (
    toJSON,
    dumps,
    TEMPLATE_RENDER,
    DEFAULT_COLOR,
)
from docutils.parsers.rst import directives, Directive

template = """

.. raw:: html

    <div class="cq" style="text-align:%(txt_align)s;float:left;">
        %(out_svg)s
    </div>
    <div style="clear:both;">
    </div>

"""
template_content_indent = "      "

rendering_code = """
const RENDERERS = {};
var ID =  0;

const renderWindow = vtk.Rendering.Core.vtkRenderWindow.newInstance();
const openglRenderWindow = vtk.Rendering.OpenGL.vtkRenderWindow.newInstance();
renderWindow.addView(openglRenderWindow);

const rootContainer = document.createElement('div');
rootContainer.style.position = 'fixed';
//rootContainer.style.zIndex = -1;
rootContainer.style.left = 0;
rootContainer.style.top = 0;
rootContainer.style.pointerEvents = 'none';
rootContainer.style.width = '100%';
rootContainer.style.height = '100%';

openglRenderWindow.setContainer(rootContainer);

const interact_style = vtk.Interaction.Style.vtkInteractorStyleManipulator.newInstance();

const manips = {
    rot: vtk.Interaction.Manipulators.vtkMouseCameraTrackballRotateManipulator.newInstance(),
    pan: vtk.Interaction.Manipulators.vtkMouseCameraTrackballPanManipulator.newInstance(),
    zoom1: vtk.Interaction.Manipulators.vtkMouseCameraTrackballZoomManipulator.newInstance(),
    zoom2: vtk.Interaction.Manipulators.vtkMouseCameraTrackballZoomManipulator.newInstance(),
    roll: vtk.Interaction.Manipulators.vtkMouseCameraTrackballRollManipulator.newInstance(),
};

manips.zoom1.setControl(true);
manips.zoom2.setButton(3);
manips.roll.setShift(true);
manips.pan.setButton(2);

for (var k in manips){{
    interact_style.addMouseManipulator(manips[k]);
}};

const interactor = vtk.Rendering.Core.vtkRenderWindowInteractor.newInstance();
interactor.setView(openglRenderWindow);
interactor.initialize();
interactor.setInteractorStyle(interact_style);

document.addEventListener('DOMContentLoaded', function () {
    document.body.appendChild(rootContainer);
});

function updateViewPort(element, renderer) {
  const { innerHeight, innerWidth } = window;
  const { x, y, width, height } = element.getBoundingClientRect();
  const viewport = [
    x / innerWidth,
    1 - (y + height) / innerHeight,
    (x + width) / innerWidth,
    1 - y / innerHeight,
  ];
  renderer.setViewport(...viewport);
}

function recomputeViewports() {
  const rendererElems = document.querySelectorAll('.renderer');
  for (let i = 0; i < rendererElems.length; i++) {
    const elem = rendererElems[i];
    const { id } = elem;
    const renderer = RENDERERS[id];
    updateViewPort(elem, renderer);
  }
  renderWindow.render();
}

function resize() {
  rootContainer.style.width = `${window.innerWidth}px`;
  openglRenderWindow.setSize(window.innerWidth, window.innerHeight);
  recomputeViewports();
}

window.addEventListener('resize', resize);
document.addEventListener('scroll', recomputeViewports);


function enterCurrentRenderer(e) {
  interactor.bindEvents(document.body);
  interact_style.setEnabled(true);
  interactor.setCurrentRenderer(RENDERERS[e.target.id]);
}

function exitCurrentRenderer(e) {
  interactor.setCurrentRenderer(null);
  interact_style.setEnabled(false);
  interactor.unbindEvents();
}


function applyStyle(element) {
  element.classList.add('renderer');
  element.style.width = '100%';
  element.style.height = '100%';
  element.style.display = 'inline-block';
  element.style.boxSizing = 'border';
  return element;
}

window.addEventListener('load', resize);

function render(data, parent_element, ratio){

    // Initial setup
    const renderer = vtk.Rendering.Core.vtkRenderer.newInstance({ background: [1, 1, 1 ] });

    // iterate over all children children
    for (var el of data){
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
        mapper.setResolveCoincidentTopologyToPolygonOffset();
        mapper.setResolveCoincidentTopologyPolygonOffsetParameters(0.5,100);

        const actor = vtk.Rendering.Core.vtkActor.newInstance();
        actor.setMapper(mapper);

        // set color and position
        actor.getProperty().setColor(rgba.slice(0,3));
        actor.getProperty().setOpacity(rgba[3]);

        actor.rotateZ(rot[2]*180/Math.PI);
        actor.rotateY(rot[1]*180/Math.PI);
        actor.rotateX(rot[0]*180/Math.PI);

        actor.setPosition(trans);

        renderer.addActor(actor);

    };

    //add the container
    const container = applyStyle(document.createElement("div"));
    parent_element.appendChild(container);
    container.addEventListener('mouseenter', enterCurrentRenderer);
    container.addEventListener('mouseleave', exitCurrentRenderer);
    container.id = ID;

    renderWindow.addRenderer(renderer);
    updateViewPort(container, renderer);
    renderer.getActiveCamera().set({ position: [1, -1, 1], viewUp: [0, 0, 1] });
    renderer.resetCamera();

    RENDERERS[ID] = renderer;
    ID++;
};
"""


template_vtk = """

.. raw:: html

    <div class="cq-vtk"
     style="text-align:{txt_align}s;float:left;border: 1px solid #ddd; width:{width}; height:{height}"">
       <script>
       var parent_element = {element};
       var data = {data};
       render(data, parent_element);
       </script>
    </div>
    <div style="clear:both;">
    </div>

"""


class cq_directive(Directive):

    has_content = True
    required_arguments = 0
    optional_arguments = 2
    option_spec = {
        "height": directives.length_or_unitless,
        "width": directives.length_or_percentage_or_unitless,
        "align": directives.unchanged,
    }

    def run(self):

        options = self.options
        content = self.content
        state_machine = self.state_machine

        # only consider inline snippets
        plot_code = "\n".join(content)

        # Since we don't have a filename, use a hash based on the content
        # the script must define a variable called 'out', which is expected to
        # be a CQ object
        out_svg = "Your Script Did not assign call build_output() function!"

        try:
            result = cqgi.parse(plot_code).build()

            if result.success:
                out_svg = exporters.getSVG(
                    exporters.toCompound(result.first_result.shape)
                )
            else:
                raise result.exception

        except Exception:
            traceback.print_exc()
            out_svg = traceback.format_exc()

        # now out
        # Now start generating the lines of output
        lines = []

        # get rid of new lines
        out_svg = out_svg.replace("\n", "")

        txt_align = "left"
        if "align" in options:
            txt_align = options["align"]

        lines.extend((template % locals()).split("\n"))

        lines.extend(["::", ""])
        lines.extend(["    %s" % row.rstrip() for row in plot_code.split("\n")])
        lines.append("")

        if len(lines):
            state_machine.insert_input(lines, state_machine.input_lines.source(0))

        return []


class cq_directive_vtk(Directive):

    has_content = True
    required_arguments = 0
    optional_arguments = 2
    option_spec = {
        "height": directives.length_or_unitless,
        "width": directives.length_or_percentage_or_unitless,
        "align": directives.unchanged,
        "select": directives.unchanged,
    }

    def run(self):

        options = self.options
        content = self.content
        state_machine = self.state_machine
        env = self.state.document.settings.env
        build_path = Path(env.app.builder.outdir)
        out_path = build_path / "_static"

        # only consider inline snippets
        plot_code = "\n".join(content)

        # collect the result
        try:
            result = cqgi.parse(plot_code).build()

            if result.success:
                if result.first_result:
                    shape = result.first_result.shape
                else:
                    shape = result.env[options.get("select", "result")]

                if isinstance(shape, Assembly):
                    assy = shape
                elif isinstance(shape, Sketch):
                    assy = Assembly(shape._faces, color=Color(*DEFAULT_COLOR))
                else:
                    assy = Assembly(shape, color=Color(*DEFAULT_COLOR))
            else:
                raise result.exception

        except Exception:
            traceback.print_exc()
            assy = Assembly(Compound.makeText("CQGI error", 10, 5))

        # save vtkjs to static
        fname = Path(str(uuid()))
        exporters.assembly.exportVTKJS(assy, out_path / fname)
        fname = str(fname) + ".zip"

        # add the output
        lines = []

        data = dumps(toJSON(assy))

        lines.extend(
            template_vtk.format(
                code=indent(TEMPLATE_RENDER.format(), "    "),
                data=data,
                ratio="null",
                element="document.currentScript.parentNode",
                txt_align=options.get("align", "left"),
                width=options.get("width", "100%"),
                height=options.get("height", "500px"),
            ).splitlines()
        )

        lines.extend(["::", ""])
        lines.extend(["    %s" % row.rstrip() for row in plot_code.split("\n")])
        lines.append("")

        if len(lines):
            state_machine.insert_input(lines, state_machine.input_lines.source(0))

        return []


def setup(app):
    setup.app = app
    setup.config = app.config
    setup.confdir = app.confdir

    app.add_directive("cq_plot", cq_directive)
    app.add_directive("cadquery", cq_directive_vtk)

    # add vtk.js
    app.add_js_file("vtk.js")
    app.add_js_file(None, body=rendering_code)
