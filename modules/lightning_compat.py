"""Compatibility helpers for importing Lightning/PyTorch Lightning.

This module centralizes all import fallbacks between the legacy
``pytorch_lightning`` package and the modern ``lightning`` namespace.
It also aliases the discovered module into ``sys.modules`` so code and
third-party extensions that still import ``pytorch_lightning`` continue
working even if only ``lightning`` is installed.
"""
from __future__ import annotations

import importlib
import sys
from types import ModuleType
from typing import Iterable, Optional

__all__ = [
    "get_lightning_module",
    "import_lightning_module",
    "import_lightning_submodule",
    "get_rank_zero_only",
    "ensure_rank_zero_aliases",
]

_PL_CACHE: Optional[ModuleType] = None


def _alias_module(module: ModuleType, alias: str) -> None:
    """Register *module* under *alias* if it is not already imported."""
    if alias not in sys.modules:
        sys.modules[alias] = module


def get_lightning_module() -> ModuleType:
    """Return the imported Lightning module, caching the result."""
    global _PL_CACHE
    if _PL_CACHE is not None:
        return _PL_CACHE

    # Try the modern ``lightning.pytorch`` package first.
    try:
        module = importlib.import_module("lightning.pytorch")
        _alias_module(module, "pytorch_lightning")
    except ModuleNotFoundError:
        module = importlib.import_module("pytorch_lightning")
        _alias_module(module, "lightning.pytorch")

    _PL_CACHE = module
    return module


# Backwards compatibility name for callers that previously imported this helper
import_lightning_module = get_lightning_module


def import_lightning_submodule(paths: Iterable[str]) -> ModuleType:
    """Import the first available module from *paths*."""
    last_error: Optional[Exception] = None
    for path in paths:
        try:
            return importlib.import_module(path)
        except ModuleNotFoundError as exc:
            last_error = exc
            continue
    if last_error is not None:
        raise last_error
    raise ModuleNotFoundError("No Lightning submodule found for paths: " + ", ".join(paths))


def get_rank_zero_only():
    """Return the rank_zero_only decorator regardless of the installed flavor."""
    try:
        module = import_lightning_submodule(
            (
                "pytorch_lightning.utilities.distributed",
                "lightning.pytorch.utilities.rank_zero",
            )
        )
    except ModuleNotFoundError:
        # Fallback that behaves like the decorator, simply returning the function.
        def identity(fn):
            return fn

        return identity

    return getattr(module, "rank_zero_only")


def ensure_rank_zero_aliases() -> None:
    """Alias the rank_zero utilities into both legacy module paths."""
    pl_module = get_lightning_module()
    utilities = getattr(pl_module, "utilities", None)
    rank_zero = getattr(utilities, "rank_zero", None) if utilities else None
    if rank_zero is None:
        return

    _alias_module(rank_zero, "pytorch_lightning.utilities.distributed")
    _alias_module(rank_zero, "lightning.pytorch.utilities.distributed")
