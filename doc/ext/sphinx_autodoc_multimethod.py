from types import ModuleType
from typing import Any, List, Tuple, ValuesView
from multimethod import multimethod
import re

from sphinx.ext.autosummary import Autosummary
from sphinx.ext.autosummary import (
    get_import_prefixes_from_env,
    ImportExceptionGroup,
    mangle_signature,
    extract_summary,
)
from docutils.statemachine import StringList
from sphinx.pycode import ModuleAnalyzer, PycodeError

from sphinx.ext.autodoc import MethodDocumenter as SphinxMethodDocumenter

from sphinx.util import inspect, logging
from sphinx.util.inspect import evaluate_signature, safe_getattr, stringify_signature
from sphinx.util.typing import get_type_hints

logger = logging.getLogger(__name__)


def get_first(obj):
    """Use to return first element (first param type annotation or first registered multimethod)."""
    return next(iter(obj))


patindent = re.compile(r"(\W*)")


def process_docstring_multimethod(app, what, name, obj, options, lines):
    """multimethod docstring customization

    Remove extraneous signatures and combine docstrings if docstring also defined
    in registered methods.  Requires sphinx-build -E if rebuilding docs.
    """

    methods = []

    if what == "method" and isinstance(obj, multimethod):
        # instance or static method

        # handle functools.singledispatch style register (multiple names)
        if obj.pending:
            methods = set(m.__name__ for m in obj.pending)
        else:
            methods = set(m.__name__ for m in obj.values())

    elif what == "method" and inspect.isclassmethod(obj) and hasattr(obj, "pending"):

        if obj.pending:
            methods = set(m.__name__ for m in obj.pending)
        else:
            methods = set(m.__name__ for m in obj.__func__.values())

    if methods:
        lines_replace = []
        patsig = re.compile(rf"\W*[{'|'.join(methods)}]+\(.*\).*")

        indent = -1
        for line in lines:
            if indent < 0:
                # fix indent when multiple docstrings defined
                if m := patindent.match(line):
                    indent = len(m.group(1))
                else:
                    indent = 0

            if patsig.match(line):
                lines_replace.append("")
            else:
                lines_replace.append(line[indent:])

        del lines[:]
        lines.extend(lines_replace)


class MultimethodAutosummary(Autosummary):
    """Customize autosummary multimethod signature."""

    def get_items(self, names: List[str]) -> List[Tuple[str, str, str, str]]:
        """Try to import the given names, and return a list of
        ``[(name, signature, summary_string, real_name), ...]``.
        """
        prefixes = get_import_prefixes_from_env(self.env)

        items: List[Tuple[str, str, str, str]] = []

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
                errors = list(
                    set("* %s: %s" % (type(e).__name__, e) for e in exc.exceptions)
                )
                logger.warning(
                    __("autosummary: failed to import %s.\nPossible hints:\n%s"),
                    name,
                    "\n".join(errors),
                    location=self.get_location(),
                )
                continue

            self.bridge.result = StringList()  # initialize for each documenter
            full_name = real_name
            if not isinstance(obj, ModuleType):
                # give explicitly separated module name, so that members
                # of inner classes can be documented
                full_name = modname + "::" + full_name[len(modname) + 1 :]
            # NB. using full_name here is important, since Documenters
            #     handle module prefixes slightly differently
            documenter = self.create_documenter(self.env.app, obj, parent, full_name)
            if not documenter.parse_name():
                logger.warning(
                    __("failed to parse name %s"),
                    real_name,
                    location=self.get_location(),
                )
                items.append((display_name, "", "", real_name))
                continue
            if not documenter.import_object():
                logger.warning(
                    __("failed to import object %s"),
                    real_name,
                    location=self.get_location(),
                )
                items.append((display_name, "", "", real_name))
                continue

            # try to also get a source code analyzer for attribute docs
            try:
                documenter.analyzer = ModuleAnalyzer.for_module(
                    documenter.get_real_modname()
                )
                # parse right now, to get PycodeErrors on parsing (results will
                # be cached anyway)
                documenter.analyzer.find_attr_docs()
            except PycodeError as err:
                logger.debug("[autodoc] module analyzer failed: %s", err)
                # no source file -- e.g. for builtin and C modules
                documenter.analyzer = None

            # -- Grab the signature

            try:
                sig = documenter.format_signature(show_annotation=False)
                # -- multimethod customization
                if isinstance(obj, multimethod):
                    sig = "(...)"
                # -- end customization
            except TypeError:
                # the documenter does not support ``show_annotation`` option
                sig = documenter.format_signature()

            if not sig:
                sig = ""
            else:
                max_chars = max(10, max_item_chars - len(display_name))
                sig = mangle_signature(sig, max_chars=max_chars)

            # -- Grab the summary

            documenter.add_content(None)
            summary = extract_summary(self.bridge.result.data[:], self.state.document)

            items.append((display_name, sig, summary, real_name))

        return items


class MethodDocumenter(SphinxMethodDocumenter):
    """Customize to append multimethod signatures."""

    def append_signature_multiple_dispatch(self, methods: ValuesView[Any]):

        sigs = []
        for dispatchmeth in methods:
            documenter = MethodDocumenter(self.directive, "")
            documenter.parent = self.parent
            documenter.object = dispatchmeth
            documenter.objpath = [None]
            sigs.append(documenter.format_signature())

        return sigs

    def format_signature(self, **kwargs: Any) -> str:
        if self.config.autodoc_typehints_format == "short":
            kwargs.setdefault("unqualified_typehints", True)

        sigs = []
        if (
            self.analyzer
            and ".".join(self.objpath) in self.analyzer.overloads
            and self.config.autodoc_typehints != "none"
        ):
            # Use signatures for overloaded methods instead of the implementation method.
            overloaded = True
        else:
            overloaded = False
            sig = super(SphinxMethodDocumenter, self).format_signature(**kwargs)
            sigs.append(sig)

        meth = self.parent.__dict__.get(self.objpath[-1])
        if inspect.is_singledispatch_method(meth):
            # append signature of singledispatch'ed functions
            for typ, func in meth.dispatcher.registry.items():
                if typ is object:
                    pass  # default implementation. skipped.
                else:
                    dispatchmeth = self.annotate_to_first_argument(func, typ)
                    if dispatchmeth:
                        documenter = MethodDocumenter(self.directive, "")
                        documenter.parent = self.parent
                        documenter.object = dispatchmeth
                        documenter.objpath = [None]
                        sigs.append(documenter.format_signature())
        # -- multimethod customization
        elif isinstance(meth, multimethod):
            if meth.pending:
                methods = meth.pending
            else:
                methods = set(meth.values())
            sigs = self.append_signature_multiple_dispatch(methods)
        elif inspect.isclassmethod(self.object) and hasattr(self.object, "pending"):
            if self.object.pending:
                methods = self.object.pending
            else:
                methods = set(self.object.__func__.values())
            sigs = self.append_signature_multiple_dispatch(methods)
        elif inspect.isstaticmethod(meth) and isinstance(self.object, multimethod):
            sigs = []
            methods = self.object.values()
            for dispatchmeth in methods:
                actual = inspect.signature(
                    dispatchmeth,
                    bound_method=False,
                    type_aliases=self.config.autodoc_type_aliases,
                )
                sig = stringify_signature(actual, **kwargs)
                sigs.append(sig)
        # -- end customization
        if overloaded:
            if inspect.isstaticmethod(
                self.object, cls=self.parent, name=self.object_name
            ):
                actual = inspect.signature(
                    self.object,
                    bound_method=False,
                    type_aliases=self.config.autodoc_type_aliases,
                )
            else:
                actual = inspect.signature(
                    self.object,
                    bound_method=True,
                    type_aliases=self.config.autodoc_type_aliases,
                )

            __globals__ = safe_getattr(self.object, "__globals__", {})
            for overload in self.analyzer.overloads.get(".".join(self.objpath)):
                overload = self.merge_default_value(actual, overload)
                overload = evaluate_signature(
                    overload, __globals__, self.config.autodoc_type_aliases
                )

                if not inspect.isstaticmethod(
                    self.object, cls=self.parent, name=self.object_name
                ):
                    parameters = list(overload.parameters.values())
                    overload = overload.replace(parameters=parameters[1:])
                sig = stringify_signature(overload, **kwargs)
                sigs.append(sig)

        return "\n".join(sigs)


def setup(app):

    app.connect("autodoc-process-docstring", process_docstring_multimethod)
    app.add_directive("autosummary", MultimethodAutosummary, override=True)
    app.add_autodocumenter(MethodDocumenter, override=True)

    return {"parallel_read_safe": True, "parallel_write_safe": True}
