# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Validation-focused ranking over protein and PTM biomarker candidates."""

from __future__ import annotations

import csv
from enum import StrEnum
from io import StringIO

from pydantic import ConfigDict, Field

from bijux_proteomics.io.stable_outputs import sort_strings
from bijux_proteomics.review.belief.contracts import (
    ReviewTrustScoreInput,
    TrustScoreDecomposition,
    decompose_trust_score,
)
from bijux_proteomics_foundation import JsonModel

_DEFAULT_BIOMARKER_WEIGHTS = {
    "effect_size": 0.22,
    "robustness": 0.22,
    "detectability": 0.15,
    "specificity": 0.15,
    "annotation": 0.10,
    "assay_feasibility": 0.10,
    "sample_qc": 0.06,
}


class BiomarkerCandidateKind(StrEnum):
    """Stable validation-target candidate kinds."""

    PROTEIN = "protein"
    PTM_SITE = "ptm_site"


class BiomarkerCandidateRankReasonCode(StrEnum):
    """Stable reasons behind biomarker-candidate promotion or downgrading."""

    STRONG_EFFECT_SIZE = "strong_effect_size"
    ROBUST_DIFFERENTIAL_SIGNAL = "robust_differential_signal"
    HIGH_DETECTABILITY = "high_detectability"
    SPECIFIC_TARGET_SUPPORT = "specific_target_support"
    FUNCTIONAL_ANNOTATION_SUPPORT = "functional_annotation_support"
    ASSAY_READY = "assay_ready"
    CLEAN_SAMPLE_QC = "clean_sample_qc"
    WEAK_EFFECT_SIZE = "weak_effect_size"
    WEAK_ROBUSTNESS = "weak_robustness"
    LOW_DETECTABILITY = "low_detectability"
    LOW_SPECIFICITY = "low_specificity"
    LOW_ASSAY_FEASIBILITY = "low_assay_feasibility"
    WEAK_SAMPLE_QC = "weak_sample_qc"
    ANNOTATION_OUTPACES_EVIDENCE = "annotation_outpaces_evidence"


class BiomarkerCandidateRankingInput(JsonModel):
    """One prepared protein or PTM-site candidate for validation ranking."""

    model_config = ConfigDict(extra="forbid")

    candidate_id: str = Field(..., min_length=1)
    candidate_kind: BiomarkerCandidateKind
    display_label: str = Field(..., min_length=1)
    target_protein_ref: str = Field(..., min_length=1)
    site_key: str | None = None
    effect_size: float | None = None
    adjusted_p_value: float | None = Field(default=None, ge=0.0, le=1.0)
    support_count: int = Field(default=0, ge=0)
    effect_score: float = Field(..., ge=0.0, le=1.0)
    robustness_score: float = Field(..., ge=0.0, le=1.0)
    detectability_score: float = Field(..., ge=0.0, le=1.0)
    specificity_score: float = Field(..., ge=0.0, le=1.0)
    annotation_score: float = Field(..., ge=0.0, le=1.0)
    assay_feasibility_score: float = Field(..., ge=0.0, le=1.0)
    sample_qc_score: float = Field(..., ge=0.0, le=1.0)
    annotation_labels: tuple[str, ...] = Field(default_factory=tuple)
    source_ids: tuple[str, ...] = Field(default_factory=tuple)
    uncertainty: float = Field(default=0.0, ge=0.0, le=1.0)
    note: str = Field(..., min_length=1)


class BiomarkerCandidateRankingEntry(JsonModel):
    """One ranked biomarker candidate with decomposed validation evidence."""

    model_config = ConfigDict(extra="forbid")

    candidate_id: str = Field(..., min_length=1)
    candidate_kind: BiomarkerCandidateKind
    display_label: str = Field(..., min_length=1)
    target_protein_ref: str = Field(..., min_length=1)
    site_key: str | None = None
    priority_rank: int = Field(..., ge=1)
    effect_size: float | None = None
    adjusted_p_value: float | None = Field(default=None, ge=0.0, le=1.0)
    support_count: int = Field(..., ge=0)
    decomposition: TrustScoreDecomposition
    rank_reason_codes: tuple[BiomarkerCandidateRankReasonCode, ...] = Field(
        default_factory=tuple
    )
    annotation_labels: tuple[str, ...] = Field(default_factory=tuple)
    source_ids: tuple[str, ...] = Field(default_factory=tuple)
    ranking_note: str = Field(..., min_length=1)


class BiomarkerCandidateRankingSummary(JsonModel):
    """Stable summary over one biomarker-candidate ranking pass."""

    model_config = ConfigDict(extra="forbid")

    candidate_count: int = Field(..., ge=0)
    protein_candidate_count: int = Field(..., ge=0)
    ptm_site_candidate_count: int = Field(..., ge=0)
    penalized_candidate_count: int = Field(..., ge=0)
    assay_ready_candidate_count: int = Field(..., ge=0)


class BiomarkerCandidateRankingReport(JsonModel):
    """Ordered biomarker-candidate ranking for validation follow-up."""

    model_config = ConfigDict(extra="forbid")

    entries: tuple[BiomarkerCandidateRankingEntry, ...] = Field(default_factory=tuple)
    summary: BiomarkerCandidateRankingSummary
    note: str = Field(..., min_length=1)


def build_biomarker_candidate_ranking_report(
    candidates: tuple[BiomarkerCandidateRankingInput, ...],
    *,
    weights: dict[str, float] | None = None,
) -> BiomarkerCandidateRankingReport:
    """Rank validation candidates beyond differential significance alone."""

    active_weights = dict(_DEFAULT_BIOMARKER_WEIGHTS)
    if weights is not None:
        active_weights.update(weights)

    ranked_rows: list[
        tuple[BiomarkerCandidateRankingInput, TrustScoreDecomposition]
    ] = []
    for candidate in candidates:
        penalties = _build_penalties(candidate)
        decomposition = decompose_trust_score(
            ReviewTrustScoreInput(
                candidate_id=candidate.candidate_id,
                evidence_inputs={
                    "effect_size": candidate.effect_score,
                    "robustness": candidate.robustness_score,
                    "detectability": candidate.detectability_score,
                    "specificity": candidate.specificity_score,
                    "annotation": candidate.annotation_score,
                    "assay_feasibility": candidate.assay_feasibility_score,
                    "sample_qc": candidate.sample_qc_score,
                },
                weights=active_weights,
                penalties=penalties,
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

    entries: list[BiomarkerCandidateRankingEntry] = []
    for rank, (candidate, decomposition) in enumerate(ranked_rows, start=1):
        rank_reasons = _build_rank_reasons(candidate)
        entries.append(
            BiomarkerCandidateRankingEntry(
                candidate_id=candidate.candidate_id,
                candidate_kind=candidate.candidate_kind,
                display_label=candidate.display_label,
                target_protein_ref=candidate.target_protein_ref,
                site_key=candidate.site_key,
                priority_rank=rank,
                effect_size=candidate.effect_size,
                adjusted_p_value=candidate.adjusted_p_value,
                support_count=candidate.support_count,
                decomposition=decomposition,
                rank_reason_codes=rank_reasons,
                annotation_labels=tuple(sort_strings(candidate.annotation_labels)),
                source_ids=tuple(sort_strings(candidate.source_ids)),
                ranking_note=_build_ranking_note(
                    candidate, decomposition, rank_reasons
                ),
            )
        )

    return BiomarkerCandidateRankingReport(
        entries=tuple(entries),
        summary=BiomarkerCandidateRankingSummary(
            candidate_count=len(entries),
            protein_candidate_count=sum(
                1
                for entry in entries
                if entry.candidate_kind is BiomarkerCandidateKind.PROTEIN
            ),
            ptm_site_candidate_count=sum(
                1
                for entry in entries
                if entry.candidate_kind is BiomarkerCandidateKind.PTM_SITE
            ),
            penalized_candidate_count=sum(
                1 for entry in entries if entry.decomposition.penalty_total > 0.0
            ),
            assay_ready_candidate_count=sum(
                1
                for entry in entries
                if BiomarkerCandidateRankReasonCode.ASSAY_READY
                in entry.rank_reason_codes
            ),
        ),
        note=(
            "biomarker candidate ranking combines effect size, robustness, "
            "detectability, specificity, functional annotation, assay feasibility, "
            "and sample QC so weak but biologically famous candidates do not rise "
            "above validation-ready evidence by reputation alone"
        ),
    )


def render_biomarker_candidate_ranking_summary_tsv(
    report: BiomarkerCandidateRankingReport,
) -> str:
    """Render biomarker-candidate ranking summary as a stable TSV ledger."""

    handle = StringIO()
    writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
    writer.writerow(("field", "value"))
    writer.writerow(("candidate_count", report.summary.candidate_count))
    writer.writerow(("protein_candidate_count", report.summary.protein_candidate_count))
    writer.writerow(
        ("ptm_site_candidate_count", report.summary.ptm_site_candidate_count)
    )
    writer.writerow(
        ("penalized_candidate_count", report.summary.penalized_candidate_count)
    )
    writer.writerow(
        ("assay_ready_candidate_count", report.summary.assay_ready_candidate_count)
    )
    writer.writerow(("note", report.note))
    return handle.getvalue()


def render_biomarker_candidate_ranking_tsv(
    report: BiomarkerCandidateRankingReport,
) -> str:
    """Render biomarker-candidate ranking as a flat TSV ledger."""

    handle = StringIO()
    writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "candidate_id",
            "candidate_kind",
            "display_label",
            "target_protein_ref",
            "site_key",
            "priority_rank",
            "final_score",
            "weighted_evidence_total",
            "penalty_total",
            "uncertainty",
            "effect_size",
            "adjusted_p_value",
            "support_count",
            "effect_score",
            "robustness_score",
            "detectability_score",
            "specificity_score",
            "annotation_score",
            "assay_feasibility_score",
            "sample_qc_score",
            "annotation_labels",
            "rank_reason_codes",
            "source_ids",
            "ranking_note",
        )
    )
    for entry in report.entries:
        components = {
            component.name: component.raw_value
            for component in entry.decomposition.components
        }
        writer.writerow(
            (
                entry.candidate_id,
                entry.candidate_kind.value,
                entry.display_label,
                entry.target_protein_ref,
                "" if entry.site_key is None else entry.site_key,
                entry.priority_rank,
                f"{entry.decomposition.final_score:.6f}",
                f"{entry.decomposition.weighted_evidence_total:.6f}",
                f"{entry.decomposition.penalty_total:.6f}",
                f"{entry.decomposition.uncertainty:.6f}",
                "" if entry.effect_size is None else f"{entry.effect_size:.6g}",
                ""
                if entry.adjusted_p_value is None
                else f"{entry.adjusted_p_value:.6g}",
                entry.support_count,
                f"{components.get('effect_size', 0.0):.6f}",
                f"{components.get('robustness', 0.0):.6f}",
                f"{components.get('detectability', 0.0):.6f}",
                f"{components.get('specificity', 0.0):.6f}",
                f"{components.get('annotation', 0.0):.6f}",
                f"{components.get('assay_feasibility', 0.0):.6f}",
                f"{components.get('sample_qc', 0.0):.6f}",
                ";".join(entry.annotation_labels),
                ";".join(reason.value for reason in entry.rank_reason_codes),
                ";".join(entry.source_ids),
                entry.ranking_note,
            )
        )
    return handle.getvalue()


def _build_penalties(
    candidate: BiomarkerCandidateRankingInput,
) -> dict[str, float]:
    penalties: dict[str, float] = {}
    if candidate.effect_score < 0.25:
        penalties["weak_effect_size"] = 0.10
    if candidate.robustness_score < 0.35:
        penalties["weak_robustness"] = 0.22
    if candidate.detectability_score < 0.35:
        penalties["low_detectability"] = 0.10
    if candidate.specificity_score < 0.35:
        penalties["low_specificity"] = 0.14
    if candidate.assay_feasibility_score < 0.35:
        penalties["low_assay_feasibility"] = 0.18
    if candidate.sample_qc_score < 0.50:
        penalties["weak_sample_qc"] = 0.08
    evidence_floor = (
        candidate.effect_score
        + candidate.robustness_score
        + candidate.assay_feasibility_score
    ) / 3.0
    if candidate.annotation_score >= 0.80 and evidence_floor < 0.40:
        penalties["annotation_outpaces_evidence"] = 0.20
    return penalties


def _build_rank_reasons(
    candidate: BiomarkerCandidateRankingInput,
) -> tuple[BiomarkerCandidateRankReasonCode, ...]:
    reasons: list[BiomarkerCandidateRankReasonCode] = []
    if candidate.effect_score >= 0.70:
        reasons.append(BiomarkerCandidateRankReasonCode.STRONG_EFFECT_SIZE)
    if candidate.robustness_score >= 0.70:
        reasons.append(BiomarkerCandidateRankReasonCode.ROBUST_DIFFERENTIAL_SIGNAL)
    if candidate.detectability_score >= 0.70:
        reasons.append(BiomarkerCandidateRankReasonCode.HIGH_DETECTABILITY)
    if candidate.specificity_score >= 0.70:
        reasons.append(BiomarkerCandidateRankReasonCode.SPECIFIC_TARGET_SUPPORT)
    if candidate.annotation_score >= 0.60:
        reasons.append(BiomarkerCandidateRankReasonCode.FUNCTIONAL_ANNOTATION_SUPPORT)
    if candidate.assay_feasibility_score >= 0.70:
        reasons.append(BiomarkerCandidateRankReasonCode.ASSAY_READY)
    if candidate.sample_qc_score >= 0.70:
        reasons.append(BiomarkerCandidateRankReasonCode.CLEAN_SAMPLE_QC)
    if candidate.effect_score < 0.25:
        reasons.append(BiomarkerCandidateRankReasonCode.WEAK_EFFECT_SIZE)
    if candidate.robustness_score < 0.35:
        reasons.append(BiomarkerCandidateRankReasonCode.WEAK_ROBUSTNESS)
    if candidate.detectability_score < 0.35:
        reasons.append(BiomarkerCandidateRankReasonCode.LOW_DETECTABILITY)
    if candidate.specificity_score < 0.35:
        reasons.append(BiomarkerCandidateRankReasonCode.LOW_SPECIFICITY)
    if candidate.assay_feasibility_score < 0.35:
        reasons.append(BiomarkerCandidateRankReasonCode.LOW_ASSAY_FEASIBILITY)
    if candidate.sample_qc_score < 0.50:
        reasons.append(BiomarkerCandidateRankReasonCode.WEAK_SAMPLE_QC)
    evidence_floor = (
        candidate.effect_score
        + candidate.robustness_score
        + candidate.assay_feasibility_score
    ) / 3.0
    if candidate.annotation_score >= 0.80 and evidence_floor < 0.40:
        reasons.append(BiomarkerCandidateRankReasonCode.ANNOTATION_OUTPACES_EVIDENCE)
    return tuple(dict.fromkeys(reasons))


def _build_ranking_note(
    candidate: BiomarkerCandidateRankingInput,
    decomposition: TrustScoreDecomposition,
    reason_codes: tuple[BiomarkerCandidateRankReasonCode, ...],
) -> str:
    positive_codes = [
        code.value
        for code in reason_codes
        if code
        in {
            BiomarkerCandidateRankReasonCode.STRONG_EFFECT_SIZE,
            BiomarkerCandidateRankReasonCode.ROBUST_DIFFERENTIAL_SIGNAL,
            BiomarkerCandidateRankReasonCode.HIGH_DETECTABILITY,
            BiomarkerCandidateRankReasonCode.SPECIFIC_TARGET_SUPPORT,
            BiomarkerCandidateRankReasonCode.FUNCTIONAL_ANNOTATION_SUPPORT,
            BiomarkerCandidateRankReasonCode.ASSAY_READY,
            BiomarkerCandidateRankReasonCode.CLEAN_SAMPLE_QC,
        }
    ]
    negative_codes = [
        code.value
        for code in reason_codes
        if code
        not in {
            BiomarkerCandidateRankReasonCode.STRONG_EFFECT_SIZE,
            BiomarkerCandidateRankReasonCode.ROBUST_DIFFERENTIAL_SIGNAL,
            BiomarkerCandidateRankReasonCode.HIGH_DETECTABILITY,
            BiomarkerCandidateRankReasonCode.SPECIFIC_TARGET_SUPPORT,
            BiomarkerCandidateRankReasonCode.FUNCTIONAL_ANNOTATION_SUPPORT,
            BiomarkerCandidateRankReasonCode.ASSAY_READY,
            BiomarkerCandidateRankReasonCode.CLEAN_SAMPLE_QC,
        }
    ]
    positives = (
        "strengths: " + ", ".join(positive_codes[:3])
        if positive_codes
        else "strengths: none dominant"
    )
    penalties = (
        "penalties: " + ", ".join(negative_codes[:3])
        if negative_codes
        else "penalties: none material"
    )
    return (
        f"{positives}; {penalties}; final validation score "
        f"{decomposition.final_score:.3f}. {candidate.note}"
    )


__all__ = [
    "BiomarkerCandidateKind",
    "BiomarkerCandidateRankReasonCode",
    "BiomarkerCandidateRankingEntry",
    "BiomarkerCandidateRankingInput",
    "BiomarkerCandidateRankingReport",
    "BiomarkerCandidateRankingSummary",
    "build_biomarker_candidate_ranking_report",
    "render_biomarker_candidate_ranking_summary_tsv",
    "render_biomarker_candidate_ranking_tsv",
]
