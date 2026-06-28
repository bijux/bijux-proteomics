# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Compatibility registry for CLI-facing support submodules."""

from __future__ import annotations

from types import ModuleType
from typing import Any

import bijux_proteomics.interfaces.support as support_registry

__all__ = support_registry.__all__


def __getattr__(name: str) -> ModuleType | Any:
    return getattr(support_registry, name)


def __dir__() -> list[str]:
    return sorted(set(globals()) | set(__all__))
