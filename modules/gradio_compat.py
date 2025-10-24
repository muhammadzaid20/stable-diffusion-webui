import importlib

import gradio as gr


_COMPONENT_ATTRS = ("IOComponent", "Component")
_DEPRECATION_MODULES = (
    ("deprecation", "GradioDeprecationWarning"),
    ("utils.deprecation", "GradioDeprecationWarning"),
    ("helpers.deprecation", "GradioDeprecationWarning"),
)


def resolve_io_component_base():
    """Locate the canonical Gradio component base class across versions."""

    components_module = getattr(gr, "components", None)
    if components_module is not None:
        for attr in _COMPONENT_ATTRS:
            candidate = getattr(components_module, attr, None)
            if candidate is not None:
                return candidate

    base_spec = importlib.util.find_spec("gradio.components.base")
    if base_spec is not None:
        components_base = importlib.import_module("gradio.components.base")
        for attr in _COMPONENT_ATTRS[1:]:
            candidate = getattr(components_base, attr, None)
            if candidate is not None:
                return candidate

    raise AttributeError("Could not locate a Gradio component base class to patch")


def resolve_deprecation_warning():
    """Return Gradio's deprecation warning class when available."""

    namespace = getattr(gr, "deprecation", None)
    if namespace is not None:
        warning_cls = getattr(namespace, "GradioDeprecationWarning", None)
        if warning_cls is not None:
            return warning_cls

    for module_suffix, attr in _DEPRECATION_MODULES:
        module_name = f"gradio.{module_suffix}"
        try:
            module = importlib.import_module(module_name)
        except ModuleNotFoundError:
            continue
        except AttributeError:
            # Some namespace packages in Gradio 5.x do not expose __path__ and
            # raise AttributeError during import discovery. Treat these as
            # missing modules and continue searching fallbacks.
            continue

        warning_cls = getattr(module, attr, None)
        if warning_cls is not None:
            return warning_cls

    return None


def with_webui_tooltip(component, tooltip):
    """Attach Stable Diffusion WebUI tooltip metadata to a Gradio component."""

    if tooltip is not None:
        setattr(component, "webui_tooltip", tooltip)

    return component


__all__ = [
    "resolve_io_component_base",
    "resolve_deprecation_warning",
    "with_webui_tooltip",
]
