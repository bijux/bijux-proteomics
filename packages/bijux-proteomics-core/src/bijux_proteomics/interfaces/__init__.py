# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Interface-layer entrypoints for Bijux Proteomics Core."""

from __future__ import annotations

from importlib import import_module
from typing import Any


def __getattr__(name: str) -> Any:
    """Load interface examples lazily so subpackage imports stay lightweight."""

    module = import_module("bijux_proteomics.interfaces.examples")
    return getattr(module, name)
