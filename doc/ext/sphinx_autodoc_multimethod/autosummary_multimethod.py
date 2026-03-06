from types import ModuleType, FunctionType

from sphinx.ext.autosummary import (
    Autosummary,
    ImportExceptionGroup,
    get_import_prefixes_from_env,
    mangle_signature,
    extract_summary,
)

from sphinx.ext.autodoc._directive_options import _AutoDocumenterOptions
from sphinx.ext.autodoc._shared import _AutodocAttrGetter, _AutodocConfig
from sphinx.ext.autosummary import _get_documenter
from sphinx.ext.autodoc._dynamic._loader import _load_object_by_name


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

        document_settings = self.state.document.settings
        env = self.env
        config = _AutodocConfig.from_config(env.config)
        current_document = env.current_document
        events = env.events
        get_attr = _AutodocAttrGetter(env._registry.autodoc_attrgetters)
        opts = _AutoDocumenterOptions()
        ref_context = env.ref_context
        reread_always = env.reread_always

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
                current_document=current_document,
                config=config,
                events=events,
                get_attr=get_attr,
                options=opts,
                ref_context=ref_context,
                reread_always=reread_always,
            )
            if props is None:
                logger.warning(
                    __("failed to import object %s"),
                    real_name,
                    location=self.get_location(),
                )
                items.append((display_name, "", "", real_name))
                continue

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
                # also singledispatch, overload, ...
                if isinstance(props._obj, FunctionType) and len(props.signatures) > 1:
                    sig = "(...)"
                else:
                    sig = mangle_signature(
                        "\n".join(props.signatures), max_chars=max_chars
                    )
                # -- end multimethod customization

            # -- Grab the summary

            # get content from docstrings or attribute documentation
            summary = extract_summary(props.docstring_lines, document_settings)

            items.append((display_name, sig, summary, real_name))

        return items
