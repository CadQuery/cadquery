import re
from typing import Any

from sphinx.util import inspect
from sphinx.util.inspect import evaluate_signature, safe_getattr, stringify_signature
from sphinx.ext.autodoc import MethodDocumenter


def process_docstring_remove_sigs(app, what, name, obj, options, lines):
    """Remove extra signatures."""
    if what == "method" and isinstance(obj, dict) and len(obj) > 0:
        dispatchmeth = list(obj.values())[0]
        if inspect.isfunction(dispatchmeth) and hasattr(dispatchmeth, "__name__"):
            fun_name = dispatchmeth.__name__
            i = 0
            pat = re.compile(fr"{dispatchmeth.__name__}\(self.*")
            for line in lines:
                if pat.match(line):
                    break
                i += 1
            del lines[i:]


class MultimethodDocumenter(MethodDocumenter):
    def __init__(self, *args) -> None:
        super().__init__(*args)

    def format_signature(self, **kwargs: Any) -> str:
        if self.config.autodoc_typehints_format == "short":
            kwargs.setdefault("unqualified_typehints", True)

        sigs = []
        if (
            self.analyzer
            and ".".join(self.objpath) in self.analyzer.overloads
            and self.config.autodoc_typehints != "none"
        ):
            # Use signatures for overloaded functions instead of the implementation function.
            overloaded = True
        else:
            overloaded = False
            sig = super().format_signature(**kwargs)
            sigs.append(sig)

        meth = self.parent.__dict__.get(self.objpath[-1])
        if inspect.is_singledispatch_function(self.object):
            # append signature of singledispatch'ed functions
            for typ, func in self.object.registry.items():
                if typ is object:
                    pass  # default implementation. skipped.
                else:
                    dispatchfunc = self.annotate_to_first_argument(func, typ)
                    if dispatchfunc:
                        documenter = FunctionDocumenter(self.directive, "")
                        documenter.object = dispatchfunc
                        documenter.objpath = [None]
                        sigs.append(documenter.format_signature())
        elif isinstance(meth, dict):
            # append signature of multimethod functions
            sigs = []
            for dispatchmeth in meth.values():
                if inspect.isfunction(dispatchmeth):
                    documenter = MethodDocumenter(self.directive, "")
                    documenter.parent = self.parent
                    documenter.object = dispatchmeth
                    documenter.objpath = [None]
                    sigs.append(documenter.format_signature())
        if overloaded:
            actual = inspect.signature(
                self.object, type_aliases=self.config.autodoc_type_aliases
            )
            __globals__ = safe_getattr(self.object, "__globals__", {})
            for overload in self.analyzer.overloads.get(".".join(self.objpath)):
                overload = self.merge_default_value(actual, overload)
                overload = evaluate_signature(
                    overload, __globals__, self.config.autodoc_type_aliases
                )

                sig = stringify_signature(overload, **kwargs)
                sigs.append(sig)

        return "\n".join(sigs)


def setup(app):

    app.connect("autodoc-process-docstring", process_docstring_remove_sigs)
    app.add_autodocumenter(MultimethodDocumenter, override=True)

    return {"parallel_read_safe": True}
