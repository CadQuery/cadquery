import sphinx.ext.autodoc

# see sphinx/ext/autodoc/_dynamic/_signatures.py
from ._dynamic._signatures import _format_signatures
from .process_docstring_multimethod import process_docstring_multimethod

from .autosummary_multimethod import MultimethodAutosummary

sphinx.ext.autodoc._dynamic._loader._format_signatures = _format_signatures


def setup(app):

    app.setup_extension("sphinx.ext.autodoc")
    app.connect("autodoc-process-docstring", process_docstring_multimethod)

    app.setup_extension("sphinx.ext.autosummary")
    app.add_directive("autosummary", MultimethodAutosummary, override=True)

    return {"parallel_read_safe": True, "parallel_write_safe": True}
