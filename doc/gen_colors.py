"""
A script to generate RST (HTML only) for displaying all the colours supported
by OCP. Used in the file assy.rst.
"""

from OCP import Quantity
import cadquery as cq
from typing import Dict
from itertools import chain


OCP_COLOR_LEADER, SEP = "Quantity_NOC", "_"

TEMPLATE = """\
      <div style="background-color:rgba({background_color});padding:10px;border-radius:5px;color:rgba({text_color});">{color_name}</div>\
"""


def color_to_rgba_str(c: cq.Color) -> str:
    """ Convert a Color object to a string for the HTML/CSS template.
    """
    t = c.toTuple()
    vals = [int(v * 255) for v in t[:3]]
    return ",".join([str(v) for v in chain(vals, [t[3]])])


def calc_text_color(c: cq.Color) -> str:
    """ Calculate required overlay text color from background color.
    """
    val = sum(c.toTuple()[:3]) / 3
    if val < 0.5:
        rv = "255,255,255"
    else:
        rv = "0,0,0"

    return rv


def get_colors() -> Dict[str, cq.Color]:
    """ Scan OCP for colors and output to a dict.
    """
    colors = {}
    for name in dir(Quantity):
        splitted = name.rsplit(SEP, 1)
        if splitted[0] == OCP_COLOR_LEADER:
            colors.update({splitted[1].lower(): cq.Color(splitted[1])})

    return colors


def rst():
    """ Produce the text for a Sphinx directive.
    """
    lines = [
        ".. raw:: html",
        "",
        '    <div class="color-grid" style="display:grid;grid-gap:10px;grid-template-columns:repeat(auto-fill, minmax(200px,1fr));">',
    ]
    colors = get_colors()
    for name, c in colors.items():
        lines += [
            TEMPLATE.format(
                background_color=color_to_rgba_str(c),
                text_color=calc_text_color(c),
                color_name=name,
            )
        ]

    lines.append("    </div>")
    return "\n".join(lines)


if __name__ == "__main__":
    print(rst())
