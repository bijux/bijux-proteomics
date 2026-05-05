# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Owner paths for shared identifier contracts."""

from __future__ import annotations

from importlib import import_module

__all__ = [
    "AssayId",
    "BatchId",
    "CandidateId",
    "ClaimId",
    "CycleId",
    "EvidenceId",
    "GateId",
    "IdentifierKind",
    "LabActionId",
    "PtmId",
    "ProgramId",
    "PromotionId",
    "ReviewId",
    "ReviewPacketId",
    "StudyId",
    "TargetId",
    "build_identifier",
    "classify_identifier",
    "ensure_identifier_kind",
]

_OWNER_MODULE = "bijux_proteomics_foundation.identity.identifiers"


def __getattr__(name: str) -> object:
    """Resolve identity owner exports lazily to keep imports acyclic."""
    if name not in __all__:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    module = import_module(_OWNER_MODULE)
    return getattr(module, name)
