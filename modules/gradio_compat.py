import importlib

import gradio as gr


_COMPONENT_ATTRS = ("IOComponent", "Component")


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
