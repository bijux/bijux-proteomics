# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Evidence-aware ranking over proteins, PTM sites, and pathway findings."""

from __future__ import annotations

import csv
from enum import StrEnum
from io import StringIO
import math
from pathlib import Path

from pydantic import ConfigDict, Field

from bijux_proteomics.io.stable_outputs import sort_strings
from bijux_proteomics.review.belief.contracts import (
    ReviewTrustScoreInput,
    TrustScoreDecomposition,
    decompose_trust_score,
)
from bijux_proteomics_foundation import JsonModel


_DEFAULT_EVIDENCE_WEIGHTS = {
    "effect_size": 0.18,
    "significance": 0.2,
    "abundance": 0.1,
    "support": 0.18,
    "qc": 0.1,
    "annotation": 0.08,
    "reproducibility": 0.08,
    "confidence": 0.08,
}


class EvidenceAwareRankingEntityKind(StrEnum):
    """Stable entity kinds ranked by evidence-aware review priority."""

    PROTEIN = "protein"
    PTM_SITE = "ptm_site"
    PATHWAY = "pathway"


class EvidenceAwareRankingCandidate(JsonModel):
    """One candidate finding prepared for evidence-aware ranking."""

    model_config = ConfigDict(extra="forbid")

    candidate_id: str = Field(..., min_length=1)
    entity_kind: EvidenceAwareRankingEntityKind
    display_label: str = Field(..., min_length=1)
    effect_size: float | None = None
    adjusted_p_value: float | None = Field(default=None, ge=0.0, le=1.0)
    abundance_value: float | None = None
    support_count: int = Field(default=0, ge=0)
    annotation_label: str | None = None
    effect_score: float = Field(..., ge=0.0, le=1.0)
    significance_score: float = Field(..., ge=0.0, le=1.0)
    abundance_score: float = Field(default=0.0, ge=0.0, le=1.0)
    support_score: float = Field(default=0.0, ge=0.0, le=1.0)
    qc_score: float = Field(default=0.0, ge=0.0, le=1.0)
    annotation_score: float = Field(default=0.0, ge=0.0, le=1.0)
    reproducibility_score: float = Field(default=0.0, ge=0.0, le=1.0)
    confidence_score: float = Field(default=0.0, ge=0.0, le=1.0)
    penalties: dict[str, float] = Field(default_factory=dict)
    uncertainty: float = Field(default=0.0, ge=0.0, le=1.0)
    source_ids: tuple[str, ...] = Field(default_factory=tuple)
    note: str = Field(..., min_length=1)


class EvidenceAwareRankingEntry(JsonModel):
    """One ranked finding with decomposed evidence and penalty context."""

    model_config = ConfigDict(extra="forbid")

    candidate_id: str = Field(..., min_length=1)
    entity_kind: EvidenceAwareRankingEntityKind
    display_label: str = Field(..., min_length=1)
    priority_rank: int = Field(..., ge=1)
    effect_size: float | None = None
    adjusted_p_value: float | None = Field(default=None, ge=0.0, le=1.0)
    abundance_value: float | None = None
    support_count: int = Field(..., ge=0)
    annotation_label: str | None = None
    decomposition: TrustScoreDecomposition
    penalty_codes: tuple[str, ...] = Field(default_factory=tuple)
    source_ids: tuple[str, ...] = Field(default_factory=tuple)
    ranking_note: str = Field(..., min_length=1)


class EvidenceAwareRankingSummary(JsonModel):
    """Stable summary over one evidence-aware ranking pass."""

    model_config = ConfigDict(extra="forbid")

    entry_count: int = Field(..., ge=0)
    protein_entry_count: int = Field(..., ge=0)
    ptm_site_entry_count: int = Field(..., ge=0)
    pathway_entry_count: int = Field(..., ge=0)
    penalized_entry_count: int = Field(..., ge=0)


class EvidenceAwareRankingReport(JsonModel):
    """Ordered evidence-aware ranking across owned biological finding kinds."""

    model_config = ConfigDict(extra="forbid")

    entries: tuple[EvidenceAwareRankingEntry, ...] = Field(default_factory=tuple)
    summary: EvidenceAwareRankingSummary
    note: str = Field(..., min_length=1)


def build_evidence_aware_ranking_report(
    candidates: tuple[EvidenceAwareRankingCandidate, ...],
    *,
    weights: dict[str, float] | None = None,
) -> EvidenceAwareRankingReport:
    """Rank findings by evidence strength and biological interpretability."""

    active_weights = dict(_DEFAULT_EVIDENCE_WEIGHTS)
    if weights is not None:
        active_weights.update(weights)

    ranked_rows: list[tuple[EvidenceAwareRankingCandidate, TrustScoreDecomposition]] = []
    for candidate in candidates:
        decomposition = decompose_trust_score(
            ReviewTrustScoreInput(
                candidate_id=candidate.candidate_id,
                evidence_inputs={
                    "effect_size": candidate.effect_score,
                    "significance": candidate.significance_score,
                    "abundance": candidate.abundance_score,
                    "support": candidate.support_score,
                    "qc": candidate.qc_score,
                    "annotation": candidate.annotation_score,
                    "reproducibility": candidate.reproducibility_score,
                    "confidence": candidate.confidence_score,
                },
                weights=active_weights,
                penalties=candidate.penalties,
                uncertainty=candidate.uncertainty,
            )
        )
        ranked_rows.append((candidate, decomposition))

    ranked_rows.sort(
        key=lambda item: (
            -item[1].final_score,
            -item[1].weighted_evidence_total,
            item[0].candidate_id,
        )
    )

    entries = []
    for rank, (candidate, decomposition) in enumerate(ranked_rows, start=1):
        entries.append(
            EvidenceAwareRankingEntry(
                candidate_id=candidate.candidate_id,
                entity_kind=candidate.entity_kind,
                display_label=candidate.display_label,
                priority_rank=rank,
                effect_size=candidate.effect_size,
                adjusted_p_value=candidate.adjusted_p_value,
                abundance_value=candidate.abundance_value,
                support_count=candidate.support_count,
                annotation_label=candidate.annotation_label,
                decomposition=decomposition,
                penalty_codes=tuple(sorted(candidate.penalties)),
                source_ids=tuple(sort_strings(candidate.source_ids)),
                ranking_note=_build_ranking_note(candidate, decomposition),
            )
        )

    return EvidenceAwareRankingReport(
        entries=tuple(entries),
        summary=EvidenceAwareRankingSummary(
            entry_count=len(entries),
            protein_entry_count=sum(
                1
                for entry in entries
                if entry.entity_kind is EvidenceAwareRankingEntityKind.PROTEIN
            ),
            ptm_site_entry_count=sum(
                1
                for entry in entries
                if entry.entity_kind is EvidenceAwareRankingEntityKind.PTM_SITE
            ),
            pathway_entry_count=sum(
                1
                for entry in entries
                if entry.entity_kind is EvidenceAwareRankingEntityKind.PATHWAY
            ),
            penalized_entry_count=sum(1 for entry in entries if entry.penalty_codes),
        ),
        note=(
            "evidence-aware ranking decomposes finding priority across effect size, "
            "significance, abundance, support, QC, annotation, reproducibility, and "
            "confidence so weak low-support artifacts do not outrank more durable biology "
            "by default"
        ),
    )


def render_evidence_aware_ranking_tsv(report: EvidenceAwareRankingReport) -> str:
    """Render evidence-aware ranking as a flat TSV ledger."""

    handle = StringIO()
    writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "candidate_id",
            "entity_kind",
            "display_label",
            "priority_rank",
            "final_score",
            "weighted_evidence_total",
            "penalty_total",
            "uncertainty",
            "effect_size",
            "adjusted_p_value",
            "abundance_value",
            "support_count",
            "annotation_label",
            "effect_score",
            "significance_score",
            "abundance_score",
            "support_score",
            "qc_score",
            "annotation_score",
            "reproducibility_score",
            "confidence_score",
            "penalty_codes",
            "source_ids",
            "ranking_note",
        )
    )
    for entry in report.entries:
        components = {component.name: component.raw_value for component in entry.decomposition.components}
        writer.writerow(
            (
                entry.candidate_id,
                entry.entity_kind.value,
                entry.display_label,
                entry.priority_rank,
                entry.decomposition.final_score,
                entry.decomposition.weighted_evidence_total,
                entry.decomposition.penalty_total,
                entry.decomposition.uncertainty,
                "" if entry.effect_size is None else entry.effect_size,
                "" if entry.adjusted_p_value is None else entry.adjusted_p_value,
                "" if entry.abundance_value is None else entry.abundance_value,
                entry.support_count,
                "" if entry.annotation_label is None else entry.annotation_label,
                components.get("effect_size", 0.0),
                components.get("significance", 0.0),
                components.get("abundance", 0.0),
                components.get("support", 0.0),
                components.get("qc", 0.0),
                components.get("annotation", 0.0),
                components.get("reproducibility", 0.0),
                components.get("confidence", 0.0),
                ";".join(entry.penalty_codes),
                ";".join(sort_strings(entry.source_ids)),
                entry.ranking_note,
            )
        )
    return handle.getvalue()


def export_evidence_aware_ranking_tsv(
    report: EvidenceAwareRankingReport,
    path: Path,
) -> None:
    """Write one evidence-aware ranking report to a stable TSV artifact."""

    path.write_text(render_evidence_aware_ranking_tsv(report), encoding="utf-8")


def normalize_linear_range(values: dict[str, float | None]) -> dict[str, float]:
    """Scale comparable values into the [0, 1] range while preserving order."""

    present_values = [value for value in values.values() if value is not None]
    if not present_values:
        return {key: 0.0 for key in values}
    minimum = min(present_values)
    maximum = max(present_values)
    if maximum == minimum:
        return {
            key: 0.0 if value is None else 1.0
            for key, value in values.items()
        }
    scale = maximum - minimum
    return {
        key: (
            0.0
            if value is None
            else min(1.0, max(0.0, (value - minimum) / scale))
        )
        for key, value in values.items()
    }


def score_effect_size(absolute_effect_size: float | None, *, saturation: float = 2.0) -> float:
    """Convert an absolute effect size into a bounded evidence score."""

    if absolute_effect_size is None or saturation <= 0.0:
        return 0.0
    return min(1.0, max(0.0, absolute_effect_size / saturation))


def score_adjusted_p_value(adjusted_p_value: float | None) -> float:
    """Convert an adjusted p-value into a bounded evidence score."""

    if adjusted_p_value is None or adjusted_p_value <= 0.0:
        return 0.0 if adjusted_p_value is None else 1.0
    return min(1.0, max(0.0, -1.0 * math.log10(adjusted_p_value) / 6.0))


def score_support_count(support_count: int, *, saturation: int = 4) -> float:
    """Convert a contributor count into a bounded support score."""

    if saturation <= 0:
        raise ValueError("support-count saturation must be positive")
    return min(1.0, max(0.0, support_count / saturation))


def _build_ranking_note(
    candidate: EvidenceAwareRankingCandidate,
    decomposition: TrustScoreDecomposition,
) -> str:
    positive_components = [
        component.name
        for component in sorted(
            decomposition.components,
            key=lambda component: (-component.contribution, component.name),
        )
        if component.raw_value > 0.0
    ][:3]
    if candidate.penalties:
        return (
            "ranked from "
            + ", ".join(positive_components or ("no positive components",))
            + " with penalties "
            + ", ".join(sorted(candidate.penalties))
        )
    return "ranked from " + ", ".join(
        positive_components or ("no positive components",)
    )


__all__ = [
    "EvidenceAwareRankingCandidate",
    "EvidenceAwareRankingEntityKind",
    "EvidenceAwareRankingEntry",
    "EvidenceAwareRankingReport",
    "EvidenceAwareRankingSummary",
    "build_evidence_aware_ranking_report",
    "export_evidence_aware_ranking_tsv",
    "normalize_linear_range",
    "render_evidence_aware_ranking_tsv",
    "score_adjusted_p_value",
    "score_effect_size",
    "score_support_count",
]
