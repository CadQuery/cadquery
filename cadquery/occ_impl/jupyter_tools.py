from IPython.display import SVG

from .exporters import toString, ExportTypes


def display(shape):

    return SVG(toString(shape, ExportTypes.SVG))
