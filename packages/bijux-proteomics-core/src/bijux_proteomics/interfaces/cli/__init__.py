# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""CLI surface for Bijux Proteomics Core."""

from __future__ import annotations

from importlib import import_module
from typing import Any


class _LazyCliProxy:
    """Delegate CLI access to the heavy app module only when used."""

    def _load(self) -> Any:
        module = import_module("bijux_proteomics.interfaces.cli.app")
        return module.cli

    def __call__(self, *args: object, **kwargs: object) -> Any:
        return self._load()(*args, **kwargs)

    def __getattr__(self, name: str) -> Any:
        return getattr(self._load(), name)

    def __repr__(self) -> str:
        return "<lazy bijux_proteomics cli proxy>"


try:
    from bijux_proteomics.interfaces.cli.app import cli as cli
except ImportError as exc:
    missing_name = getattr(exc, "name", None)
    error_text = str(exc)
    dependency_missing = missing_name in {"click", "pydantic"} or (
        "click" in error_text or "pydantic" in error_text
    )
    if not dependency_missing:
        raise
    cli = _LazyCliProxy()

__all__ = ["cli"]
