from IPython.display import SVG

from .exporters.svg import getSVG


def display(shape):

    return SVG(getSVG(shape))
