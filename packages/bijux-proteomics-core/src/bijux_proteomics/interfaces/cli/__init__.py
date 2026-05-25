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


def _is_lazy_cli_import(exc: ImportError) -> bool:
    missing_name = getattr(exc, "name", None)
    error_text = str(exc)
    if missing_name in {"click", "pydantic"}:
        return True
    if missing_name is not None and missing_name.startswith("bijux_proteomics_"):
        return True
    return any(
        dependency_name in error_text
        for dependency_name in ("click", "pydantic", "bijux_proteomics_")
    )


try:
    from bijux_proteomics.interfaces.cli.app import cli as cli
except ImportError as exc:
    if not _is_lazy_cli_import(exc):
        raise
    cli = _LazyCliProxy()

__all__ = ["cli"]
