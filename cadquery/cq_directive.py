"""
A special directive for including a cq object.

"""

import sys, os, shutil, imp, warnings, cStringIO, re,traceback

from cadquery import *
import StringIO
from docutils.parsers.rst import directives


template = """

.. raw:: html

    <div class="cq" style="text-align:%(txtAlign)s;float:left;">
        %(outSVG)s
    </div>
    <div style="clear:both;">
    </div>

"""
template_content_indent = '      '


def cq_directive(name, arguments, options, content, lineno,
                   content_offset, block_text, state, state_machine):

    #only consider inline snippets
    plot_code = '\n'.join(content)

    # Since we don't have a filename, use a hash based on the content
    #the script must define a variable called 'out', which is expected to
    #be a CQ object
    outSVG = "Your Script Did not assign the 'result' variable!"


    try:
        _s = StringIO.StringIO()
        exec(plot_code)
        
        exporters.exportShape(result,"SVG",_s)
        outSVG = _s.getvalue()
    except:
        traceback.print_exc()
        outSVG = traceback.format_exc()

    #now out
    # Now start generating the lines of output
    lines = []

    #get rid of new lines
    outSVG = outSVG.replace('\n','')

    txtAlign = "left"
    if options.has_key("align"):
        txtAlign = options['align']

    lines.extend((template % locals()).split('\n'))

    lines.extend(['::', ''])
    lines.extend(['    %s' % row.rstrip()
                  for row in plot_code.split('\n')])
    lines.append('')

    if len(lines):
        state_machine.insert_input(
            lines, state_machine.input_lines.source(0))

    return []

def setup(app):
    setup.app = app
    setup.config = app.config
    setup.confdir = app.confdir

    options = {'height': directives.length_or_unitless,
               'width': directives.length_or_percentage_or_unitless,
               'align': directives.unchanged
    }

    app.add_directive('cq_plot', cq_directive, True, (0, 2, 0), **options)


