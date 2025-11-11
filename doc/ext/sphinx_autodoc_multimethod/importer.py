"""Importer utilities for autodoc

See sphinx.ext.autodoc.importer.py

Modify _format_signatures for multimethod customization.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING
from sphinx.errors import PycodeError
from sphinx.pycode import ModuleAnalyzer
from sphinx.util import inspect, logging
from sphinx.util.inspect import (
    _stringify_signature_to_parts,
    evaluate_signature,
    safe_getattr,
)
from inspect import Parameter

if TYPE_CHECKING:
    from collections.abc import Callable, Mapping, Sequence
    from importlib.machinery import ModuleSpec
    from typing import Any, Protocol, TypeAlias

    from sphinx.config import Config
    from sphinx.events import EventManager
    from sphinx.ext.autodoc._directive_options import _AutoDocumenterOptions

    _FormattedSignature: TypeAlias = tuple[str, str]

    class _AttrGetter(Protocol):
        def __call__(self, obj: Any, name: str, default: Any = ..., /) -> Any:
            ...


from sphinx.ext.autodoc.importer import (
    _extract_signatures_from_docstring,
    _extract_signature_from_object,
    _annotate_to_first_argument,
    _merge_default_value,
)

logger = logging.getLogger(__name__)

# create list of identified multimethod names
MM_NAMES = []


def append_signature_multiple_dispatch(self, methods: ValuesView[Any]):

    sigs = []
    for dispatchmeth in methods:
        documenter = MethodDocumenter(self.directive, "")
        documenter.parent = self.parent
        documenter.object = dispatchmeth
        documenter.objpath = [None]
        sigs.append(documenter.format_signature())

    return sigs


def _format_multimethod_signatures(
    config: Config,
    events: EventManager,
    get_attr: _AttrGetter,
    parent: Any,
    props: _ItemProperties,
):
    signatures = []

    parts = [props.module_name]
    parts.extend(props.parts)
    name = ".".join(parts)
    MM_NAMES.append(name)
    for _, f in props._obj.items():
        props._obj = f
        sig = _extract_signature_from_object(
            config=config, events=events, get_attr=get_attr, parent=parent, props=props,
        )
        signatures.append(sig[0])
    return signatures


def _format_signatures(
    *,
    config: Config,
    events: EventManager,
    get_attr: _AttrGetter,
    parent: Any,
    options: _AutoDocumenterOptions,
    props: _ItemProperties,
    args: str | None = None,
    retann: str | None = "",
    **kwargs: Any,
) -> list[_FormattedSignature]:
    """Format the signature (arguments and return annotation) of the object.

    Let the user process it via the ``autodoc-process-signature`` event.
    """
    if props.obj_type in {"class", "exception"}:
        from sphinx.ext.autodoc._property_types import _ClassDefProperties

        assert isinstance(props, _ClassDefProperties)
        if props.doc_as_attr:
            return []
        if config.autodoc_class_signature == "separated":
            # do not show signatures
            return []

    if config.autodoc_typehints_format == "short":
        kwargs.setdefault("unqualified_typehints", True)
    if config.python_display_short_literal_types:
        kwargs.setdefault("short_literals", True)

    if args is None:
        signatures: list[_FormattedSignature] = []
    else:
        signatures = [(args, retann or "")]

    if (
        not signatures
        and config.autodoc_docstring_signature
        and props.obj_type not in {"module", "data", "type"}
    ):
        # only act if a signature is not explicitly given already,
        # and if the feature is enabled
        signatures[:] = _extract_signatures_from_docstring(
            config=config,
            get_attr=get_attr,
            options=options,
            parent=parent,
            props=props,
        )

    if not signatures:
        # try to introspect the signature
        try:
            signatures[:] = _extract_signature_from_object(
                config=config,
                events=events,
                get_attr=get_attr,
                parent=parent,
                props=props,
                **kwargs,
            )
        except Exception as exc:
            msg = __("error while formatting arguments for %s: %s")
            logger.warning(msg, props.full_name, exc, type="autodoc")

    if props.obj_type in {"attribute", "property"}:
        # Only keep the return annotation
        signatures = [("", retann) for _args, retann in signatures]

    if result := events.emit_firstresult(
        "autodoc-process-signature",
        props.obj_type,
        props.full_name,
        props._obj,
        options,
        signatures[0][0] if signatures else None,  # args
        signatures[0][1] if signatures else "",  # retann
    ):
        if len(result) == 2 and isinstance(result[0], str):
            args, retann = result
            signatures[0] = (args, retann if isinstance(retann, str) else "")

    if props.obj_type in {"module", "data", "type"}:
        signatures[1:] = ()  # discard all signatures save the first

    if real_modname := props._obj___module__ or props.module_name:
        try:
            analyzer = ModuleAnalyzer.for_module(real_modname)
            # parse right now, to get PycodeErrors on parsing (results will
            # be cached anyway)
            analyzer.analyze()
        except PycodeError as exc:
            logger.debug("[autodoc] module analyzer failed: %s", exc)
            # no source file -- e.g. for builtin and C modules
            analyzer = None
    else:
        analyzer = None

    if props.obj_type in {"function", "decorator"}:
        overloaded = (
            analyzer is not None
            and props.dotted_parts in analyzer.overloads
            and config.autodoc_typehints != "none"
        )
        is_singledispatch = inspect.is_singledispatch_function(props._obj)

        if overloaded:
            # Use signatures for overloaded functions and methods instead of
            # their implementations.
            signatures.clear()
        # -- multimethod customization
        elif isinstance(props._obj, dict):
            return _format_multimethod_signatures(
                config, events, get_attr, parent, props
            )
        # -- end multimethod customization
        elif not is_singledispatch:
            return signatures

        if is_singledispatch:
            from sphinx.ext.autodoc._property_types import _FunctionDefProperties

            # append signature of singledispatch'ed functions
            for typ, func in props._obj.registry.items():
                if typ is object:
                    continue  # default implementation. skipped.
                dispatch_func = _annotate_to_first_argument(
                    func, typ, config=config, props=props
                )
                if not dispatch_func:
                    continue
                dispatch_props = _FunctionDefProperties(
                    obj_type="function",
                    module_name="",
                    parts=("",),
                    docstring_lines=(),
                    signatures=(),
                    _obj=dispatch_func,
                    _obj___module__=None,
                    _obj___qualname__=None,
                    _obj___name__=None,
                    properties=frozenset(),
                )
                signatures += _format_signatures(
                    config=config,
                    events=events,
                    get_attr=get_attr,
                    parent=None,
                    options=options,
                    props=dispatch_props,
                )
        if overloaded and analyzer is not None:
            actual = inspect.signature(
                props._obj, type_aliases=config.autodoc_type_aliases
            )
            obj_globals = safe_getattr(props._obj, "__globals__", {})
            overloads = analyzer.overloads[props.dotted_parts]
            for overload in overloads:
                overload = _merge_default_value(actual, overload)
                overload = evaluate_signature(
                    overload, obj_globals, config.autodoc_type_aliases
                )
                signatures.append(_stringify_signature_to_parts(overload, **kwargs))

        return signatures

    if props.obj_type in {"class", "exception"}:
        from sphinx.ext.autodoc._property_types import _ClassDefProperties

        assert isinstance(props, _ClassDefProperties)
        method_name = props._signature_method_name
        if method_name == "__call__":
            signature_cls = type(props._obj)
        else:
            signature_cls = props._obj
        overloads = []
        overloaded = False
        if method_name:
            for cls in signature_cls.__mro__:
                try:
                    analyzer = ModuleAnalyzer.for_module(cls.__module__)
                    analyzer.analyze()
                except PycodeError:
                    pass
                else:
                    qualname = f"{cls.__qualname__}.{method_name}"
                    if qualname in analyzer.overloads:
                        overloads = analyzer.overloads[qualname]
                        overloaded = True
                        break
                    if qualname in analyzer.tagorder:
                        # the constructor is defined in the class, but not overridden.
                        break
        if overloaded and config.autodoc_typehints != "none":
            # Use signatures for overloaded methods instead of the implementation method.
            signatures.clear()
            method = safe_getattr(signature_cls, method_name, None)
            method_globals = safe_getattr(method, "__globals__", {})
            for overload in overloads:
                overload = evaluate_signature(
                    overload, method_globals, config.autodoc_type_aliases
                )

                parameters = list(overload.parameters.values())
                overload = overload.replace(
                    parameters=parameters[1:], return_annotation=Parameter.empty
                )
                signatures.append(_stringify_signature_to_parts(overload, **kwargs))
            return signatures

        return signatures

    if props.obj_type == "method":
        overloaded = (
            analyzer is not None
            and props.dotted_parts in analyzer.overloads
            and config.autodoc_typehints != "none"
        )
        meth = parent.__dict__.get(props.name)
        is_singledispatch = inspect.is_singledispatch_method(meth)

        if overloaded:
            # Use signatures for overloaded functions and methods instead of
            # their implementations.
            signatures.clear()
        # -- multimethod customization
        elif isinstance(props._obj, dict):
            return _format_multimethod_signatures(
                config, events, get_attr, parent, props
            )
        # -- end multimethod customization
        elif not is_singledispatch:
            return signatures

        if is_singledispatch:
            from sphinx.ext.autodoc._property_types import _FunctionDefProperties

            # append signature of singledispatch'ed methods
            for typ, func in meth.dispatcher.registry.items():
                if typ is object:
                    continue  # default implementation. skipped.
                if inspect.isclassmethod(func):
                    func = func.__func__
                dispatch_meth = _annotate_to_first_argument(
                    func, typ, config=config, props=props
                )
                if not dispatch_meth:
                    continue
                dispatch_props = _FunctionDefProperties(
                    obj_type="method",
                    module_name="",
                    parts=("",),
                    docstring_lines=(),
                    signatures=(),
                    _obj=dispatch_meth,
                    _obj___module__=None,
                    _obj___qualname__=None,
                    _obj___name__=None,
                    properties=frozenset(),
                )
                signatures += _format_signatures(
                    config=config,
                    events=events,
                    get_attr=get_attr,
                    parent=parent,
                    options=options,
                    props=dispatch_props,
                )
        if overloaded and analyzer is not None:
            from sphinx.ext.autodoc._property_types import _FunctionDefProperties

            assert isinstance(props, _FunctionDefProperties)
            actual = inspect.signature(
                props._obj,
                bound_method=not props.is_staticmethod,
                type_aliases=config.autodoc_type_aliases,
            )

            obj_globals = safe_getattr(props._obj, "__globals__", {})
            overloads = analyzer.overloads[props.dotted_parts]
            for overload in overloads:
                overload = _merge_default_value(actual, overload)
                overload = evaluate_signature(
                    overload, obj_globals, config.autodoc_type_aliases
                )

                if not props.is_staticmethod:
                    # hide the first argument (e.g. 'self')
                    parameters = list(overload.parameters.values())
                    overload = overload.replace(parameters=parameters[1:])
                signatures.append(_stringify_signature_to_parts(overload, **kwargs))

        return signatures

    return signatures
