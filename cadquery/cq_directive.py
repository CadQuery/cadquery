"""
A special directive for including a cq object.

"""

import traceback

from pathlib import Path
from uuid import uuid1 as uuid
from textwrap import indent
from urllib import request

from cadquery import exporters, Assembly, Compound, Color
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

template_vtk = """

.. raw:: html

    <div class="cq-vtk"
     style="text-align:{txt_align}s;float:left;border: 1px solid #ddd; width:{width}; height:{height}"">
       <script>
       {code}
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
                    shape = result.env["result"]

                if isinstance(shape, Assembly):
                    assy = shape
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
    app.add_directive("cq_vtk", cq_directive_vtk)

    # download and add vtk.js
    build_path = Path(app.outdir)
    out_path = build_path / "_static"
    out_path.mkdir(parents=True, exist_ok=True)

    request.urlretrieve("https://unpkg.com/vtk.js", out_path / "vtk.js")

    app.add_js_file("vtk.js")
