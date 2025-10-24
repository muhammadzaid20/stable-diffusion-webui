"""Compatibility helpers for ``pkg_resources``.

Setuptools 70 removed the vendored ``packaging`` module from ``pkg_resources``.
Several third-party libraries – notably OpenAI's ``clip`` package that ships
with the WebUI – still import ``pkg_resources.packaging`` directly.  On modern
environments this results in an ``AttributeError`` during import which prevents
the application from starting.  We shim the attribute back in so that legacy
callers continue to work without having to pin ``setuptools`` to an older
release.
"""

from __future__ import annotations


def ensure_packaging_attribute() -> None:
    """Expose ``packaging`` through :mod:`pkg_resources` when missing.

    The helper is intentionally forgiving – if ``pkg_resources`` or
    ``packaging`` cannot be imported we simply return and let the original
    ImportError surface, matching the behaviour that older environments had.
    """

    try:
        import pkg_resources
    except ModuleNotFoundError:
        return

    if getattr(pkg_resources, "packaging", None) is not None:
        return

    try:
        import packaging
    except ModuleNotFoundError:
        return

    pkg_resources.packaging = packaging  # type: ignore[attr-defined]

