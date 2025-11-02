import re
from types import ModuleType
from typing import Any, List, Tuple, ValuesView

import sphinx.ext.autodoc
from sphinx.ext.autosummary import Autosummary
from sphinx.ext.autosummary import (
    get_import_prefixes_from_env,
    ImportExceptionGroup,
    mangle_signature,
    extract_summary,
)
from sphinx.locale import __
from sphinx.ext.autodoc._directive_options import _AutoDocumenterOptions
from sphinx.ext.autodoc.directive import _AutodocAttrGetter
from sphinx.ext.autosummary import _get_documenter
from sphinx.ext.autodoc.importer import _load_object_by_name
from sphinx.ext.autodoc._docstrings import _prepare_docstrings, _process_docstrings
from sphinx.pycode import ModuleAnalyzer, PycodeError
from sphinx.util import logging

from .importer import _format_signatures

sphinx.ext.autodoc.importer._format_signatures = _format_signatures

logger = logging.getLogger(__name__)
patindent = re.compile(r"(\W*)")


def process_docstring_multimethod(app, what, name, obj, options, lines):
    """multimethod docstring customization

    Remove extraneous signatures and combine docstrings if docstring also defined
    in registered method.
    """

    # get list of multimethod names identified during signature formatting
    from .importer import MM_NAMES

    if name not in MM_NAMES:
        return

    lines_replace = []
    patsig = re.compile(rf"\W*[{'|'.join(name)}]+\(.*\).*")

    indent = -1
    prevline = " \t"
    for line in lines:
        if indent < 0:
            # fix indent when multiple docstrings defined
            if m := patindent.match(line):
                indent = len(m.group(1))
            else:
                indent = 0

        if patsig.match(line) and prevline == "":
            lines_replace.append("")
        else:
            lines_replace.append(line[indent:])
        prevline = line

    del lines[:]
    lines.extend(lines_replace)


class MultimethodAutosummary(Autosummary):
    """Customize autosummary multimethod signature.

    Display signature as "(...)" to indicate multiple argument dispatching. 
    """

    def get_items(self, names: list[str]) -> list[tuple[str, str | None, str, str]]:
        """Try to import the given names, and return a list of
        ``[(name, signature, summary_string, real_name), ...]``.

        signature is already formatted and is None if :nosignatures: option was given.
        """
        prefixes = get_import_prefixes_from_env(self.env)

        items: list[tuple[str, str | None, str, str]] = []

        signatures_option = self.options.get("signatures")
        if signatures_option is None:
            signatures_option = "none" if "nosignatures" in self.options else "long"
        if signatures_option not in {"none", "short", "long"}:
            msg = (
                "Invalid value for autosummary :signatures: option: "
                f"{signatures_option!r}. Valid values are 'none', 'short', 'long'"
            )
            raise ValueError(msg)

        env = self.env
        config = env.config
        current_document = env.current_document
        events = env.events
        get_attr = _AutodocAttrGetter(env._registry.autodoc_attrgetters)
        opts = _AutoDocumenterOptions()

        max_item_chars = 50

        for name in names:
            display_name = name
            if name.startswith("~"):
                name = name[1:]
                display_name = name.split(".")[-1]

            try:
                real_name, obj, parent, modname = self.import_by_name(
                    name, prefixes=prefixes
                )
            except ImportExceptionGroup as exc:
                errors = list({f"* {type(e).__name__}: {e}" for e in exc.exceptions})
                logger.warning(
                    __("autosummary: failed to import %s.\nPossible hints:\n%s"),
                    name,
                    "\n".join(errors),
                    location=self.get_location(),
                )
                continue

            obj_type = _get_documenter(obj, parent)
            if isinstance(obj, ModuleType):
                full_name = real_name
            else:
                # give explicitly separated module name, so that members
                # of inner classes can be documented
                full_name = f"{modname}::{real_name[len(modname) + 1 :]}"
            # NB. using full_name here is important, since Documenters
            #     handle module prefixes slightly differently
            props = _load_object_by_name(
                name=full_name,
                objtype=obj_type,
                mock_imports=config.autodoc_mock_imports,
                type_aliases=config.autodoc_type_aliases,
                current_document=current_document,
                config=config,
                env=env,
                events=events,
                get_attr=get_attr,
                options=opts,
            )
            if props is None:
                logger.warning(
                    __("failed to import object %s"),
                    real_name,
                    location=self.get_location(),
                )
                items.append((display_name, "", "", real_name))
                continue

            # try to also get a source code analyzer for attribute docs
            real_module = props._obj___module__ or props.module_name
            try:
                analyzer = ModuleAnalyzer.for_module(real_module)
                # parse right now, to get PycodeErrors on parsing (results will
                # be cached anyway)
                analyzer.analyze()
            except PycodeError as err:
                logger.debug("[autodoc] module analyzer failed: %s", err)
                # no source file -- e.g. for builtin and C modules
                analyzer = None

            # -- Grab the signature

            if signatures_option == "none":
                sig = None
            elif not props.signatures:
                sig = ""
            elif signatures_option == "short":
                sig = "()" if props.signatures == ("()",) else "(…)"
            else:  # signatures_option == 'long'
                max_chars = max(10, max_item_chars - len(display_name))
                # -- multimethod customization
                if (obj_type == "method" or obj_type == "function") and isinstance(
                    props._obj, dict
                ):
                    sig = "(...)"
                else:
                    sig = mangle_signature(
                        "\n".join(props.signatures), max_chars=max_chars
                    )
                # -- end multimethod customization

            # -- Grab the summary

            # get content from docstrings or attribute documentation
            attr_docs = {} if analyzer is None else analyzer.attr_docs
            docstrings = _prepare_docstrings(props=props, attr_docs=attr_docs)
            docstring_lines = _process_docstrings(
                docstrings, events=events, props=props, options=opts,
            )
            summary = extract_summary(list(docstring_lines), self.state.document)

            items.append((display_name, sig, summary, real_name))

        return items


def setup(app):

    app.setup_extension("sphinx.ext.autodoc")
    app.connect("autodoc-process-docstring", process_docstring_multimethod)
    app.add_directive("autosummary", MultimethodAutosummary, override=True)

    return {"parallel_read_safe": True, "parallel_write_safe": True}
