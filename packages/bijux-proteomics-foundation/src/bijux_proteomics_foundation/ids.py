# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Compatibility wrapper for shared identifier contracts."""

from __future__ import annotations

from bijux_proteomics_foundation.identity.identifiers import (
    AssayId,
    BatchId,
    CandidateId,
    ClaimId,
    CycleId,
    EvidenceId,
    ExperimentId,
    GateId,
    IdentifierKind,
    LabActionId,
    ModificationId,
    PeptideId,
    ProgramId,
    PromotionId,
    ProteinId,
    PtmId,
    ReviewId,
    ReviewPacketId,
    RunId,
    SpectrumId,
    StudyId,
    TargetId,
    build_identifier,
    classify_identifier,
    ensure_identifier_kind,
)

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
