"""Compatibility remote-provider entrypoints."""

from __future__ import annotations

from bijux_proteomics_runtime.providers.remote import EXPERIMENTAL
from bijux_proteomics_runtime.providers.remote.colabfold import APIColabFoldProvider
from bijux_proteomics_runtime.providers.remote.openprotein import (
    APIOpenProteinProvider,
)

__all__ = ["APIOpenProteinProvider", "APIColabFoldProvider", "EXPERIMENTAL"]
