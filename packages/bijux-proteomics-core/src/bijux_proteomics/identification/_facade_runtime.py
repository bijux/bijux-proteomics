# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Shared runtime helpers for governed identification facades."""

from __future__ import annotations

from importlib import import_module
from typing import Any


def resolve_facade_export(
    name: str,
    export_owner_map: dict[str, str],
    module_globals: dict[str, Any],
) -> Any:
    """Load and cache one governed facade export from its owner module."""

    owner_module = export_owner_map.get(name)
    if owner_module is None:
        raise AttributeError(
            f"module {module_globals['__name__']!r} has no attribute {name!r}"
        )
    module = import_module(owner_module)
    value = getattr(module, name)
    module_globals[name] = value
    return value


def build_facade_dir(
    module_globals: dict[str, Any],
    public_exports: tuple[str, ...],
) -> list[str]:
    """Return a stable directory view for a governed facade module."""

    return sorted(set(module_globals) | set(public_exports))
