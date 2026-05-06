# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Compatibility shell for historical agentic runtime entrypoints."""

from __future__ import annotations

from importlib import metadata

__all__ = ["__version__"]


try:
    __version__ = metadata.version("agentic-proteins")
except metadata.PackageNotFoundError:
    __version__ = ""
