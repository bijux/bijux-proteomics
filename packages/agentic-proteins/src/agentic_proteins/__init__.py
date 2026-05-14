# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Compatibility alias root for canonical runtime entrypoints."""

from __future__ import annotations

from importlib import metadata

from bijux_proteomics_runtime import AppConfig, RunManager, cli, create_app

__all__ = ["AppConfig", "RunManager", "cli", "create_app"]

try:
    __version__ = metadata.version("agentic-proteins")
except metadata.PackageNotFoundError:
    __version__ = "0.3.6"
