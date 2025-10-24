"""CUDA compatibility helpers for guarding against unsupported GPU architectures."""
from __future__ import annotations

import re
from typing import Iterable, Optional

import torch

from modules import errors
from modules.shared_cmd_options import cmd_opts


def _parse_architecture_tag(tag: str) -> Optional[int]:
    """Return the encoded compute capability (major*10 + minor) for a compiled arch tag."""
    match = re.search(r"(\d+)", tag)
    if not match:
        return None

    value = int(match.group(1))
    if value < 10:
        return None

    major = value // 10
    minor = value % 10
    return major * 10 + minor


def _normalise_arch_list(arch_list: Iterable[str]) -> list[int]:
    capabilities = []
    for tag in arch_list:
        capability = _parse_architecture_tag(tag)
        if capability is not None:
            capabilities.append(capability)
    return capabilities


def _get_max_compiled_capability() -> Optional[int]:
    if not torch.cuda.is_available():
        return None

    get_arch_list = getattr(torch.cuda, "get_arch_list", None)
    if get_arch_list is None:
        return None

    try:
        compiled_arches = _normalise_arch_list(get_arch_list())
    except Exception:
        return None

    if not compiled_arches:
        return None

    return max(compiled_arches)


def _format_capability(capability: int | tuple[int, int]) -> str:
    if isinstance(capability, tuple):
        major, minor = capability
    else:
        major, minor = divmod(capability, 10)
    return f"sm_{major}{minor}"


def ensure_future_gpu_compatibility(device_index: int | None = None) -> None:
    """Disable CUDA execution when the installed torch build lacks kernels for the GPU."""
    if not torch.cuda.is_available():
        return

    try:
        index = torch.cuda.current_device() if device_index is None else device_index
        capability = torch.cuda.get_device_capability(index)
        name = torch.cuda.get_device_name(index)
    except Exception:
        # If capability probing fails we leave CUDA enabled and allow the
        # existing error reporting to handle the situation.
        return

    compiled_max = _get_max_compiled_capability()
    if compiled_max is None:
        return

    device_encoded = capability[0] * 10 + capability[1]
    if device_encoded <= compiled_max:
        return

    cmd_opts.use_cpu = list(dict.fromkeys([*cmd_opts.use_cpu, "all"]))

    explanation = (
        """
Your GPU reports compute capability {device_cc} (model: {device_name}),
which is newer than the highest architecture ({compiled_cc}) that the bundled
PyTorch build ({torch_version}) was compiled for.

For stability we will continue in CPU mode until you install a torch wheel
that advertises support for this architecture. The official PyTorch installation
guide is available at https://pytorch.org/get-started/locally/.
        """
    ).strip().format(
        device_cc=_format_capability(capability),
        device_name=name,
        compiled_cc=_format_capability(compiled_max),
        torch_version=torch.__version__,
    )

    errors.print_error_explanation(explanation)


__all__ = ["ensure_future_gpu_compatibility"]
