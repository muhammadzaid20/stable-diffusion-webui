import gradio as gr

from modules import patches, scripts, ui_tempdir
from modules.gradio_compat import resolve_io_component_base


__all__ = [
    "add_classes_to_gradio_component",
]


def add_classes_to_gradio_component(comp):
    """Attach css-friendly class names to Gradio components."""

    comp.elem_classes = [f"gradio-{comp.get_block_name()}", *(comp.elem_classes or [])]

    if getattr(comp, "multiselect", False):
        comp.elem_classes.append("multiselect")


def IOComponent_init(self, *args, **kwargs):
    tooltip = kwargs.pop("tooltip", None)
    if tooltip is not None:
        self.webui_tooltip = tooltip

    if scripts.scripts_current is not None:
        scripts.scripts_current.before_component(self, **kwargs)

    scripts.script_callbacks.before_component_callback(self, **kwargs)

    res = original_IOComponent_init(self, *args, **kwargs)

    add_classes_to_gradio_component(self)

    scripts.script_callbacks.after_component_callback(self, **kwargs)

    if scripts.scripts_current is not None:
        scripts.scripts_current.after_component(self, **kwargs)

    return res


def Block_get_config(self):
    config = original_Block_get_config(self)

    webui_tooltip = getattr(self, "webui_tooltip", None)
    if webui_tooltip:
        config["webui_tooltip"] = webui_tooltip

    config.pop("example_inputs", None)

    return config


def BlockContext_init(self, *args, **kwargs):
    if scripts.scripts_current is not None:
        scripts.scripts_current.before_component(self, **kwargs)

    scripts.script_callbacks.before_component_callback(self, **kwargs)

    res = original_BlockContext_init(self, *args, **kwargs)

    add_classes_to_gradio_component(self)

    scripts.script_callbacks.after_component_callback(self, **kwargs)

    if scripts.scripts_current is not None:
        scripts.scripts_current.after_component(self, **kwargs)

    return res


def Blocks_get_config_file(self, *args, **kwargs):
    config = original_Blocks_get_config_file(self, *args, **kwargs)

    for comp_config in config["components"]:
        if "example_inputs" in comp_config:
            comp_config["example_inputs"] = {"serialized": []}

    return config


IOComponentBase = resolve_io_component_base()

original_IOComponent_init = patches.patch(
    __name__, obj=IOComponentBase, field="__init__", replacement=IOComponent_init
)
original_Block_get_config = patches.patch(
    __name__, obj=gr.blocks.Block, field="get_config", replacement=Block_get_config
)
original_BlockContext_init = patches.patch(
    __name__, obj=gr.blocks.BlockContext, field="__init__", replacement=BlockContext_init
)
original_Blocks_get_config_file = patches.patch(
    __name__,
    obj=gr.blocks.Blocks,
    field="get_config_file",
    replacement=Blocks_get_config_file,
)

ui_tempdir.install_ui_tempdir_override()
