# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Typed identifiers shared across Bijux Proteomics packages."""

from __future__ import annotations

from enum import StrEnum
from typing import Annotated

from pydantic import StringConstraints

Identifier = StringConstraints(
    strip_whitespace=True,
    min_length=1,
    max_length=128,
    pattern=r"^[a-z0-9][a-z0-9._:-]*$",
)

ProgramId = Annotated[str, Identifier]
TargetId = Annotated[str, Identifier]
CandidateId = Annotated[str, Identifier]
ProteinId = Annotated[str, Identifier]
PeptideId = Annotated[str, Identifier]
SpectrumId = Annotated[str, Identifier]
ModificationId = Annotated[str, Identifier]
ExperimentId = Annotated[str, Identifier]
RunId = Annotated[str, Identifier]
AssayId = Annotated[str, Identifier]
EvidenceId = Annotated[str, Identifier]
ClaimId = Annotated[str, Identifier]
ReviewId = Annotated[str, Identifier]
ReviewPacketId = Annotated[str, Identifier]
PromotionId = Annotated[str, Identifier]
BatchId = Annotated[str, Identifier]
GateId = Annotated[str, Identifier]
CycleId = Annotated[str, Identifier]
StudyId = Annotated[str, Identifier]
PtmId = Annotated[str, Identifier]
LabActionId = Annotated[str, Identifier]


class IdentifierKind(StrEnum):
    """Known identifier kinds with stable prefix contracts."""

    PROGRAM = "prog"
    TARGET = "target"
    CANDIDATE = "candidate"
    PROTEIN = "protein"
    PEPTIDE = "peptide"
    SPECTRUM = "spectrum"
    MODIFICATION = "mod"
    EXPERIMENT = "experiment"
    RUN = "run"
    EVIDENCE = "evid"
    CLAIM = "claim"
    REVIEW = "review"
    REVIEW_PACKET = "reviewpkt"
    PROMOTION = "promotion"
    ASSAY = "assay"
    BATCH = "batch"
    GATE = "gate"
    CYCLE = "cycle"
    STUDY = "study"
    PTM = "ptm"
    LAB_ACTION = "labact"


def classify_identifier(identifier: str) -> IdentifierKind | None:
    """Return the identifier kind from prefix, if recognized."""
    prefix = identifier.split("-", maxsplit=1)[0].strip().lower()
    for kind in IdentifierKind:
        if kind.value == prefix:
            return kind
    return None


def ensure_identifier_kind(identifier: str, kind: IdentifierKind) -> None:
    """Raise when an identifier does not match the expected kind prefix."""
    actual = classify_identifier(identifier)
    if actual is not kind:
        raise ValueError(f"identifier '{identifier}' should use '{kind.value}-' prefix")


def build_identifier(kind: IdentifierKind, suffix: str) -> str:
    """Build a canonical identifier from kind and suffix."""
    cleaned = suffix.strip().lower().replace(" ", "-")
    if not cleaned:
        raise ValueError("identifier suffix must be non-empty")
    return f"{kind.value}-{cleaned}"


__all__ = [
    "AssayId",
    "BatchId",
    "CandidateId",
    "ClaimId",
    "CycleId",
    "EvidenceId",
    "ExperimentId",
    "GateId",
    "IdentifierKind",
    "LabActionId",
    "ModificationId",
    "PeptideId",
    "ProgramId",
    "PromotionId",
    "ProteinId",
    "PtmId",
    "ReviewId",
    "ReviewPacketId",
    "RunId",
    "SpectrumId",
    "StudyId",
    "TargetId",
    "build_identifier",
    "classify_identifier",
    "ensure_identifier_kind",
]
