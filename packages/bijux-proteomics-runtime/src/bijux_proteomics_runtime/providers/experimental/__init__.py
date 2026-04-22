# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Experimental provider implementations."""

from __future__ import annotations

from agentic_proteins.core.stability import experimental
from bijux_proteomics_runtime.providers.experimental.colabfold import APIColabFoldProvider
from bijux_proteomics_runtime.providers.experimental.openprotein import APIOpenProteinProvider

experimental()

EXPERIMENTAL = True

__all__ = ["APIOpenProteinProvider", "APIColabFoldProvider", "EXPERIMENTAL"]
