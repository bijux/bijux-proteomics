# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Inference-disagreement decision briefs built from core identification semantics."""

from __future__ import annotations

from enum import StrEnum
from typing import TYPE_CHECKING

from pydantic import ConfigDict, Field

from bijux_proteomics_foundation import JsonModel

if TYPE_CHECKING:
    from bijux_proteomics.identification import PsmRecord


class InferenceDisagreementSeverity(StrEnum):
    """Severity level for inference decision brief entries."""

    INFO = "info"
    WARNING = "warning"
    BLOCKING = "blocking"


class InferenceDisagreementReviewEntry(JsonModel):
    """One disagreement entry prepared for scientific review."""

    model_config = ConfigDict(extra="forbid")

    subject_id: str = Field(..., min_length=1)
    kind: str = Field(..., min_length=1)
    severity: InferenceDisagreementSeverity
    note: str = Field(..., min_length=1)


class InferenceDisagreementReviewPacket(JsonModel):
    """Review packet over inference disagreements and strategy divergence."""

    model_config = ConfigDict(extra="forbid")

    entry_count: int = Field(..., ge=0)
    blocking_count: int = Field(..., ge=0)
    warning_count: int = Field(..., ge=0)
    strategy_overlap_alert_count: int = Field(..., ge=0)
    entries: tuple[InferenceDisagreementReviewEntry, ...] = Field(default_factory=tuple)
    recommendation: str = Field(..., min_length=1)


def build_inference_disagreement_review_packet(
    records: tuple[PsmRecord, ...],
) -> InferenceDisagreementReviewPacket:
    """Package inference disagreements for scientific review workflows."""
    from bijux_proteomics.identification import build_inference_disagreement_report
    from bijux_proteomics.identification.confidence import (
        compare_protein_inference_strategies,
    )

    disagreement_report = build_inference_disagreement_report(records)
    strategy_report = compare_protein_inference_strategies(records)

    entries: list[InferenceDisagreementReviewEntry] = []
    for entry in disagreement_report.entries:
        severity = (
            InferenceDisagreementSeverity.BLOCKING
            if entry.kind.value == "protein_set"
            else InferenceDisagreementSeverity.WARNING
        )
        entries.append(
            InferenceDisagreementReviewEntry(
                subject_id=entry.subject_id,
                kind=entry.kind.value,
                severity=severity,
                note=entry.note,
            )
        )
    strategy_overlap_alert_count = sum(
        comparison.jaccard_similarity < 0.5
        for comparison in strategy_report.comparisons
    )
    if not entries and strategy_overlap_alert_count == 0:
        recommendation = "inference strategies are consistent; proceed with standard review gate checks"
    elif any(
        entry.severity is InferenceDisagreementSeverity.BLOCKING for entry in entries
    ):
        recommendation = "blocking inference disagreements were detected; require strategy adjudication before release"
    else:
        recommendation = "review warnings were detected; include disagreement rationale in the evidence handoff"
    return InferenceDisagreementReviewPacket(
        entry_count=len(entries),
        blocking_count=sum(
            entry.severity is InferenceDisagreementSeverity.BLOCKING
            for entry in entries
        ),
        warning_count=sum(
            entry.severity is InferenceDisagreementSeverity.WARNING for entry in entries
        ),
        strategy_overlap_alert_count=strategy_overlap_alert_count,
        entries=tuple(entries),
        recommendation=recommendation,
    )
