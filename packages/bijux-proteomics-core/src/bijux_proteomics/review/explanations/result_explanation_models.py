# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Public result-explanation enums and report models."""

from __future__ import annotations

from enum import StrEnum

from pydantic import ConfigDict, Field

from bijux_proteomics_foundation import JsonModel


class ResultExplanationKind(StrEnum):
    """Stable explanation families over governed result artifacts."""

    PROTEIN_RESULT = "protein_result"
    PTM_SITE_RESULT = "ptm_site_result"
    PATHWAY_RESULT = "pathway_result"
    SAMPLE_QC_DECISION = "sample_qc_decision"
    REJECTED_EVIDENCE_DECISION = "rejected_evidence_decision"


class ResultExplanationStatus(StrEnum):
    """Stable answer states for one deterministic explanation request."""

    ANSWERED = "answered"
    NOT_FOUND = "not_found"
    UNSUPPORTED = "unsupported"


class ResultExplanationEvidenceRole(StrEnum):
    """Whether one structured explanation point supports or opposes the decision."""

    SUPPORTING = "supporting"
    OPPOSING = "opposing"


class ResultExplanationRequest(JsonModel):
    """One deterministic result-explanation request."""

    model_config = ConfigDict(extra="forbid")

    explanation_id: str = Field(..., min_length=1)
    explanation_kind: ResultExplanationKind
    subject_id: str | None = None


class ResultExplanationPoint(JsonModel):
    """One structured evidence point inside a deterministic explanation."""

    model_config = ConfigDict(extra="forbid")

    explanation_id: str = Field(..., min_length=1)
    role: ResultExplanationEvidenceRole
    result_surface: str = Field(..., min_length=1)
    row_id: str = Field(..., min_length=1)
    graph_node_ids: tuple[str, ...] = Field(default_factory=tuple)
    source_row_refs: tuple[str, ...] = Field(default_factory=tuple)
    summary: str = Field(..., min_length=1)


class ResultExplanation(JsonModel):
    """One deterministic structured explanation over exported result artifacts."""

    model_config = ConfigDict(extra="forbid")

    explanation_id: str = Field(..., min_length=1)
    explanation_kind: ResultExplanationKind
    status: ResultExplanationStatus
    subject_id: str | None = None
    subject_label: str | None = None
    claim: str = Field(..., min_length=1)
    evidence: tuple[ResultExplanationPoint, ...] = Field(default_factory=tuple)
    opposing_evidence: tuple[ResultExplanationPoint, ...] = Field(default_factory=tuple)
    decision: str = Field(..., min_length=1)
    confidence: str = Field(..., min_length=1)
    result_row_ids: tuple[str, ...] = Field(default_factory=tuple)
    graph_node_ids: tuple[str, ...] = Field(default_factory=tuple)
    note: str = Field(..., min_length=1)


class ResultExplanationSummary(JsonModel):
    """Summary over one deterministic explanation pass."""

    model_config = ConfigDict(extra="forbid")

    explanation_count: int = Field(..., ge=0)
    answered_explanation_count: int = Field(..., ge=0)
    not_found_explanation_count: int = Field(..., ge=0)
    unsupported_explanation_count: int = Field(..., ge=0)


class ResultExplanationReport(JsonModel):
    """Deterministic structured explanation report over result artifacts."""

    model_config = ConfigDict(extra="forbid")

    explanations: tuple[ResultExplanation, ...] = Field(default_factory=tuple)
    summary: ResultExplanationSummary
    note: str = Field(..., min_length=1)


__all__ = [
    "ResultExplanation",
    "ResultExplanationEvidenceRole",
    "ResultExplanationKind",
    "ResultExplanationPoint",
    "ResultExplanationReport",
    "ResultExplanationRequest",
    "ResultExplanationStatus",
    "ResultExplanationSummary",
]
