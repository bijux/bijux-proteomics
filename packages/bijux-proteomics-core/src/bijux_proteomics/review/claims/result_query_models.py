# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Public result-query enums and report models."""

from __future__ import annotations

from enum import StrEnum

from pydantic import ConfigDict, Field

from bijux_proteomics_foundation import JsonModel


class ResultQueryKind(StrEnum):
    """Stable deterministic question families over governed result artifacts."""

    PROTEIN_SIGNIFICANCE = "protein_significance"
    PROTEIN_PEPTIDE_SUPPORT = "protein_peptide_support"
    SAMPLE_QC_FAILURE = "sample_qc_failure"
    PTM_SITE_DOWNGRADE = "ptm_site_downgrade"


class ResultQueryStatus(StrEnum):
    """Stable answer states for one deterministic result query."""

    ANSWERED = "answered"
    NOT_FOUND = "not_found"
    UNSUPPORTED = "unsupported"


class ResultQueryRequest(JsonModel):
    """One deterministic result query request."""

    model_config = ConfigDict(extra="forbid")

    query_id: str = Field(..., min_length=1)
    query_kind: ResultQueryKind
    subject_id: str | None = None


class ResultQueryEvidenceLink(JsonModel):
    """One explicit evidence citation attached to a deterministic answer."""

    model_config = ConfigDict(extra="forbid")

    query_id: str = Field(..., min_length=1)
    result_surface: str = Field(..., min_length=1)
    row_id: str = Field(..., min_length=1)
    graph_node_ids: tuple[str, ...] = Field(default_factory=tuple)
    source_row_refs: tuple[str, ...] = Field(default_factory=tuple)
    note: str = Field(..., min_length=1)


class ResultQueryAnswer(JsonModel):
    """One deterministic answer over exported proteomics results."""

    model_config = ConfigDict(extra="forbid")

    query_id: str = Field(..., min_length=1)
    query_kind: ResultQueryKind
    status: ResultQueryStatus
    subject_id: str | None = None
    subject_label: str | None = None
    answer_text: str = Field(..., min_length=1)
    result_row_ids: tuple[str, ...] = Field(default_factory=tuple)
    graph_node_ids: tuple[str, ...] = Field(default_factory=tuple)
    evidence_links: tuple[ResultQueryEvidenceLink, ...] = Field(default_factory=tuple)
    note: str = Field(..., min_length=1)


class ResultQuerySummary(JsonModel):
    """Summary over one deterministic result-query pass."""

    model_config = ConfigDict(extra="forbid")

    query_count: int = Field(..., ge=0)
    answered_query_count: int = Field(..., ge=0)
    not_found_query_count: int = Field(..., ge=0)
    unsupported_query_count: int = Field(..., ge=0)


class ResultQueryReport(JsonModel):
    """Deterministic question-answer report over result artifacts."""

    model_config = ConfigDict(extra="forbid")

    answers: tuple[ResultQueryAnswer, ...] = Field(default_factory=tuple)
    summary: ResultQuerySummary
    note: str = Field(..., min_length=1)


__all__ = [
    "ResultQueryAnswer",
    "ResultQueryEvidenceLink",
    "ResultQueryKind",
    "ResultQueryReport",
    "ResultQueryRequest",
    "ResultQueryStatus",
    "ResultQuerySummary",
]
