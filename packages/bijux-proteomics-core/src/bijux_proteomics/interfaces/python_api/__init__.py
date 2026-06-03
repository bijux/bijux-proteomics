# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Programmatic Python entrypoints for CLI-owned scientific operations."""

from __future__ import annotations

from importlib import import_module
from pathlib import Path
import re
from typing import Any, Final

_RUNNER_PATTERN: Final = re.compile(r"^def (run_[a-z0-9_]+)\(", re.MULTILINE)
_PACKAGE_DIR: Final = Path(__file__).resolve().parent


def _build_runner_index() -> dict[str, str]:
    index: dict[str, str] = {}
    for path in sorted(_PACKAGE_DIR.glob("*.py")):
        if path.name == "__init__.py":
            continue
        module_name = path.stem
        for runner_name in _RUNNER_PATTERN.findall(path.read_text(encoding="utf-8")):
            index[runner_name] = module_name
    return index


_RUNNER_INDEX: Final = _build_runner_index()
__all__ = sorted(_RUNNER_INDEX)


def __getattr__(name: str) -> Any:
    module_name = _RUNNER_INDEX.get(name)
    if module_name is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    module = import_module(f"{__name__}.{module_name}")
    value = getattr(module, name)
    globals()[name] = value
    return value


def __dir__() -> list[str]:
    return sorted(set(globals()) | set(__all__))
