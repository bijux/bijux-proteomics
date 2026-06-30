# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Public belief-audit models."""

from __future__ import annotations

from enum import StrEnum

from pydantic import ConfigDict, Field

from bijux_proteomics_foundation import JsonModel


class BeliefAuditSubjectKind(StrEnum):
    """Stable scientific conclusion families audited by the review surface."""

    PROTEIN = "protein"
    PTM_SITE = "ptm_site"
    PATHWAY = "pathway"
    REGULATOR = "regulator"
    BIOMARKER = "biomarker"
    QC_DECISION = "qc_decision"


class BeliefAuditEntry(JsonModel):
    """One challengeable scientific conclusion with explicit support and falsifiers."""

    model_config = ConfigDict(extra="forbid")

    audit_id: str = Field(..., min_length=1)
    subject_kind: BeliefAuditSubjectKind
    subject_id: str = Field(..., min_length=1)
    subject_label: str = Field(..., min_length=1)
    claim: str = Field(..., min_length=1)
    decision: str = Field(..., min_length=1)
    confidence: str = Field(..., min_length=1)
    why_believed: str = Field(..., min_length=1)
    what_weakens: str = Field(..., min_length=1)
    what_would_falsify: str = Field(..., min_length=1)
    result_surfaces: tuple[str, ...] = Field(default_factory=tuple)
    result_row_ids: tuple[str, ...] = Field(default_factory=tuple)
    graph_node_ids: tuple[str, ...] = Field(default_factory=tuple)
    note: str = Field(..., min_length=1)


class BeliefAuditSummary(JsonModel):
    """Summary over one deterministic belief-audit pass."""

    model_config = ConfigDict(extra="forbid")

    entry_count: int = Field(..., ge=0)
    protein_entry_count: int = Field(..., ge=0)
    ptm_site_entry_count: int = Field(..., ge=0)
    pathway_entry_count: int = Field(..., ge=0)
    regulator_entry_count: int = Field(..., ge=0)
    biomarker_entry_count: int = Field(..., ge=0)
    qc_decision_entry_count: int = Field(..., ge=0)


class BeliefAuditReport(JsonModel):
    """Deterministic belief-audit report over governed conclusion artifacts."""

    model_config = ConfigDict(extra="forbid")

    entries: tuple[BeliefAuditEntry, ...] = Field(default_factory=tuple)
    summary: BeliefAuditSummary
    note: str = Field(..., min_length=1)


__all__ = [
    "BeliefAuditEntry",
    "BeliefAuditReport",
    "BeliefAuditSubjectKind",
    "BeliefAuditSummary",
]
