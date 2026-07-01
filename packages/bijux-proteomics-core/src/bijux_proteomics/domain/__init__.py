# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Governed public facade for core domain owners."""

from __future__ import annotations

from importlib import import_module
from typing import Any

from bijux_proteomics.domain.public_api import (
    build_domain_export_owner_map,
    list_domain_export_names,
)

_DOMAIN_EXPORT_OWNER_MAP = build_domain_export_owner_map()
_DOMAIN_PUBLIC_EXPORTS = list_domain_export_names()

__all__ = list(_DOMAIN_PUBLIC_EXPORTS)


def __getattr__(name: str) -> Any:
    """Load one governed domain export lazily from its owner module."""

    owner_module = _DOMAIN_EXPORT_OWNER_MAP.get(name)
    if owner_module is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    module = import_module(owner_module)
    value = getattr(module, name)
    globals()[name] = value
    return value


def __dir__() -> list[str]:
    """Return a stable directory view for the domain facade."""

    return sorted(set(globals()) | set(_DOMAIN_PUBLIC_EXPORTS))
