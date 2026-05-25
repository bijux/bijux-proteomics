"""Handoff-owned runtime surfaces for portable collaborator archives."""

from __future__ import annotations

from bijux_proteomics_runtime.handoff.archive import (
    CollaboratorHandoffArchive,
    CollaboratorHandoffArchiveSummary,
    build_handoff_archive,
    load_handoff_archive,
)
from bijux_proteomics_runtime.support.primitives.stability import sealed

__all__ = [
    "CollaboratorHandoffArchive",
    "CollaboratorHandoffArchiveSummary",
    "build_handoff_archive",
    "load_handoff_archive",
]

sealed()
