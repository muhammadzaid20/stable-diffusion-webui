import importlib
from functools import wraps

import gradio as gr


from modules import patches


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


def _wrap_event_listener_setup(original):
    @wraps(original)
    def setup_with_legacy_js(*args, **kwargs):
        event_trigger = original(*args, **kwargs)

        @wraps(event_trigger)
        def trigger_with_legacy_js(*trigger_args, **trigger_kwargs):
            if "_js" in trigger_kwargs and "js" not in trigger_kwargs:
                trigger_kwargs["js"] = trigger_kwargs.pop("_js")

            return event_trigger(*trigger_args, **trigger_kwargs)

        # Gradio attaches runtime metadata (event name, callbacks, etc.) to the
        # returned trigger. Propagate that state to our wrapper so downstream
        # consumers continue to behave as expected.
        trigger_with_legacy_js.__dict__.update(event_trigger.__dict__)

        return trigger_with_legacy_js

    return setup_with_legacy_js


try:
    from gradio.events import EventListener

    _original_event_listener_setup = EventListener._setup

    patches.patch(
        __name__,
        obj=EventListener,
        field="_setup",
        replacement=_wrap_event_listener_setup(_original_event_listener_setup),
    )
except Exception:
    # If Gradio significantly reshapes its event dispatch internals we fall back to
    # the runtime error generated when `_js` parameters are supplied.
    pass


__all__ = [
    "resolve_io_component_base",
    "resolve_deprecation_warning",
    "with_webui_tooltip",
]
