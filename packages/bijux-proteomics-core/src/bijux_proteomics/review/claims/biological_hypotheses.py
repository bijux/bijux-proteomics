# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Structured biological hypotheses derived from graph-backed evidence support."""

from __future__ import annotations

import csv
from enum import StrEnum
from io import StringIO

from pydantic import ConfigDict, Field

from bijux_proteomics.domain.confidence import ConfidenceTier
from bijux_proteomics.io.stable_outputs import sort_strings
from bijux_proteomics_foundation import JsonModel


class BiologicalHypothesisKind(StrEnum):
    """Stable biological hypothesis classes emitted for report handoff."""

    PROTEIN_MECHANISM = "protein_mechanism"
    PATHWAY_ACTIVITY = "pathway_activity"
    REGULATOR_ACTIVITY = "regulator_activity"


BiologicalHypothesisConfidenceTier = ConfidenceTier


class BiologicalHypothesisRejectionReason(StrEnum):
    """Durable reasons why a candidate cannot become a supported hypothesis row."""

    MISSING_EVIDENCE_NODE_IDS = "missing_evidence_node_ids"
    MISSING_SUPPORTING_EVIDENCE = "missing_supporting_evidence"


class BiologicalHypothesisCandidate(JsonModel):
    """One structured biological hypothesis candidate prepared for owned review."""

    model_config = ConfigDict(extra="forbid")

    hypothesis_id: str = Field(..., min_length=1)
    hypothesis_kind: BiologicalHypothesisKind
    subject_id: str = Field(..., min_length=1)
    subject_label: str = Field(..., min_length=1)
    claim: str = Field(..., min_length=1)
    supporting_protein_refs: tuple[str, ...] = Field(default_factory=tuple)
    supporting_site_keys: tuple[str, ...] = Field(default_factory=tuple)
    supporting_pathway_ids: tuple[str, ...] = Field(default_factory=tuple)
    opposing_evidence: tuple[str, ...] = Field(default_factory=tuple)
    evidence_node_ids: tuple[str, ...] = Field(default_factory=tuple)
    base_confidence_score: float = Field(..., ge=0.0, le=1.0)
    next_experiment_suggestion: str | None = None
    source_ids: tuple[str, ...] = Field(default_factory=tuple)
    note: str = Field(..., min_length=1)


class BiologicalHypothesisEntry(JsonModel):
    """One supported biological hypothesis with graph-backed evidence node IDs."""

    model_config = ConfigDict(extra="forbid")

    hypothesis_id: str = Field(..., min_length=1)
    hypothesis_kind: BiologicalHypothesisKind
    subject_id: str = Field(..., min_length=1)
    subject_label: str = Field(..., min_length=1)
    claim: str = Field(..., min_length=1)
    supporting_protein_refs: tuple[str, ...] = Field(default_factory=tuple)
    supporting_site_keys: tuple[str, ...] = Field(default_factory=tuple)
    supporting_pathway_ids: tuple[str, ...] = Field(default_factory=tuple)
    opposing_evidence: tuple[str, ...] = Field(default_factory=tuple)
    evidence_node_ids: tuple[str, ...] = Field(default_factory=tuple)
    confidence_score: float = Field(..., ge=0.0, le=1.0)
    confidence_tier: BiologicalHypothesisConfidenceTier
    next_experiment_suggestion: str = Field(..., min_length=1)
    source_ids: tuple[str, ...] = Field(default_factory=tuple)
    note: str = Field(..., min_length=1)


class RejectedBiologicalHypothesisCandidate(JsonModel):
    """One hypothesis candidate withheld from output because support is incomplete."""

    model_config = ConfigDict(extra="forbid")

    hypothesis_id: str = Field(..., min_length=1)
    hypothesis_kind: BiologicalHypothesisKind
    subject_id: str = Field(..., min_length=1)
    subject_label: str = Field(..., min_length=1)
    claim: str = Field(..., min_length=1)
    rejection_reason: BiologicalHypothesisRejectionReason
    supporting_protein_refs: tuple[str, ...] = Field(default_factory=tuple)
    supporting_site_keys: tuple[str, ...] = Field(default_factory=tuple)
    supporting_pathway_ids: tuple[str, ...] = Field(default_factory=tuple)
    source_ids: tuple[str, ...] = Field(default_factory=tuple)
    rejection_note: str = Field(..., min_length=1)


class BiologicalHypothesisSummary(JsonModel):
    """Stable summary over one biological-hypothesis generation pass."""

    model_config = ConfigDict(extra="forbid")

    candidate_count: int = Field(..., ge=0)
    hypothesis_count: int = Field(..., ge=0)
    rejected_candidate_count: int = Field(..., ge=0)
    protein_hypothesis_count: int = Field(..., ge=0)
    pathway_hypothesis_count: int = Field(..., ge=0)
    regulator_hypothesis_count: int = Field(..., ge=0)
    high_confidence_hypothesis_count: int = Field(..., ge=0)


class BiologicalHypothesisReport(JsonModel):
    """Owned biological hypothesis report for final scientific handoff."""

    model_config = ConfigDict(extra="forbid")

    hypotheses: tuple[BiologicalHypothesisEntry, ...] = Field(default_factory=tuple)
    rejected_candidates: tuple[RejectedBiologicalHypothesisCandidate, ...] = Field(
        default_factory=tuple
    )
    summary: BiologicalHypothesisSummary
    note: str = Field(..., min_length=1)


def build_biological_hypothesis_report(
    candidates: tuple[BiologicalHypothesisCandidate, ...],
) -> BiologicalHypothesisReport:
    """Generate graph-backed biological hypotheses from structured evidence rows."""

    hypotheses: list[BiologicalHypothesisEntry] = []
    rejected_candidates: list[RejectedBiologicalHypothesisCandidate] = []

    for candidate in candidates:
        supporting_protein_refs = tuple(sort_strings(candidate.supporting_protein_refs))
        supporting_site_keys = tuple(sort_strings(candidate.supporting_site_keys))
        supporting_pathway_ids = tuple(sort_strings(candidate.supporting_pathway_ids))
        evidence_node_ids = tuple(sort_strings(candidate.evidence_node_ids))
        source_ids = tuple(sort_strings(candidate.source_ids))
        opposing_evidence = tuple(sort_strings(candidate.opposing_evidence))

        rejection_reason = _candidate_rejection_reason(
            evidence_node_ids=evidence_node_ids,
            supporting_protein_refs=supporting_protein_refs,
            supporting_site_keys=supporting_site_keys,
        )
        if rejection_reason is not None:
            rejected_candidates.append(
                RejectedBiologicalHypothesisCandidate(
                    hypothesis_id=candidate.hypothesis_id,
                    hypothesis_kind=candidate.hypothesis_kind,
                    subject_id=candidate.subject_id,
                    subject_label=candidate.subject_label,
                    claim=candidate.claim,
                    rejection_reason=rejection_reason,
                    supporting_protein_refs=supporting_protein_refs,
                    supporting_site_keys=supporting_site_keys,
                    supporting_pathway_ids=supporting_pathway_ids,
                    source_ids=source_ids,
                    rejection_note=_build_rejection_note(rejection_reason),
                )
            )
            continue

        confidence_score = _score_hypothesis_candidate(
            base_confidence_score=candidate.base_confidence_score,
            evidence_node_ids=evidence_node_ids,
            supporting_protein_refs=supporting_protein_refs,
            supporting_site_keys=supporting_site_keys,
            opposing_evidence=opposing_evidence,
        )
        hypotheses.append(
            BiologicalHypothesisEntry(
                hypothesis_id=candidate.hypothesis_id,
                hypothesis_kind=candidate.hypothesis_kind,
                subject_id=candidate.subject_id,
                subject_label=candidate.subject_label,
                claim=candidate.claim,
                supporting_protein_refs=supporting_protein_refs,
                supporting_site_keys=supporting_site_keys,
                supporting_pathway_ids=supporting_pathway_ids,
                opposing_evidence=opposing_evidence,
                evidence_node_ids=evidence_node_ids,
                confidence_score=confidence_score,
                confidence_tier=_confidence_tier(confidence_score),
                next_experiment_suggestion=(
                    candidate.next_experiment_suggestion
                    or _default_next_experiment_suggestion(candidate)
                ),
                source_ids=source_ids,
                note=candidate.note,
            )
        )

    hypotheses.sort(
        key=lambda entry: (
            -entry.confidence_score,
            entry.hypothesis_kind.value,
            entry.subject_id,
            entry.hypothesis_id,
        )
    )
    rejected_candidates.sort(
        key=lambda entry: (
            entry.rejection_reason.value,
            entry.hypothesis_kind.value,
            entry.subject_id,
            entry.hypothesis_id,
        )
    )
    return BiologicalHypothesisReport(
        hypotheses=tuple(hypotheses),
        rejected_candidates=tuple(rejected_candidates),
        summary=BiologicalHypothesisSummary(
            candidate_count=len(candidates),
            hypothesis_count=len(hypotheses),
            rejected_candidate_count=len(rejected_candidates),
            protein_hypothesis_count=sum(
                1
                for hypothesis in hypotheses
                if hypothesis.hypothesis_kind
                is BiologicalHypothesisKind.PROTEIN_MECHANISM
            ),
            pathway_hypothesis_count=sum(
                1
                for hypothesis in hypotheses
                if hypothesis.hypothesis_kind
                is BiologicalHypothesisKind.PATHWAY_ACTIVITY
            ),
            regulator_hypothesis_count=sum(
                1
                for hypothesis in hypotheses
                if hypothesis.hypothesis_kind
                is BiologicalHypothesisKind.REGULATOR_ACTIVITY
            ),
            high_confidence_hypothesis_count=sum(
                1
                for hypothesis in hypotheses
                if hypothesis.confidence_tier is BiologicalHypothesisConfidenceTier.HIGH
            ),
        ),
        note=(
            "biological hypothesis generation emits only graph-backed hypotheses that "
            "carry explicit evidence node ids, supporting entities, opposing evidence, "
            "and a concrete next experiment suggestion"
        ),
    )


def render_biological_hypothesis_summary_tsv(report: BiologicalHypothesisReport) -> str:
    """Render the biological hypothesis summary as TSV."""

    handle = StringIO()
    writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
    writer.writerow(("field", "value"))
    writer.writerow(("candidate_count", report.summary.candidate_count))
    writer.writerow(("hypothesis_count", report.summary.hypothesis_count))
    writer.writerow(
        ("rejected_candidate_count", report.summary.rejected_candidate_count)
    )
    writer.writerow(
        ("protein_hypothesis_count", report.summary.protein_hypothesis_count)
    )
    writer.writerow(
        ("pathway_hypothesis_count", report.summary.pathway_hypothesis_count)
    )
    writer.writerow(
        ("regulator_hypothesis_count", report.summary.regulator_hypothesis_count)
    )
    writer.writerow(
        (
            "high_confidence_hypothesis_count",
            report.summary.high_confidence_hypothesis_count,
        )
    )
    writer.writerow(("note", report.note))
    return handle.getvalue()


def render_biological_hypothesis_tsv(report: BiologicalHypothesisReport) -> str:
    """Render supported biological hypotheses as TSV."""

    handle = StringIO()
    writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "hypothesis_id",
            "hypothesis_kind",
            "subject_id",
            "subject_label",
            "claim",
            "supporting_protein_refs",
            "supporting_site_keys",
            "supporting_pathway_ids",
            "opposing_evidence",
            "evidence_node_ids",
            "confidence_score",
            "confidence_tier",
            "next_experiment_suggestion",
            "source_ids",
            "note",
        )
    )
    for entry in report.hypotheses:
        writer.writerow(
            (
                entry.hypothesis_id,
                entry.hypothesis_kind.value,
                entry.subject_id,
                entry.subject_label,
                entry.claim,
                ";".join(entry.supporting_protein_refs),
                ";".join(entry.supporting_site_keys),
                ";".join(entry.supporting_pathway_ids),
                ";".join(entry.opposing_evidence),
                ";".join(entry.evidence_node_ids),
                _format_float(entry.confidence_score),
                entry.confidence_tier.value,
                entry.next_experiment_suggestion,
                ";".join(entry.source_ids),
                entry.note,
            )
        )
    return handle.getvalue()


def render_rejected_biological_hypothesis_candidate_tsv(
    report: BiologicalHypothesisReport,
) -> str:
    """Render rejected biological hypothesis candidates as TSV."""

    handle = StringIO()
    writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "hypothesis_id",
            "hypothesis_kind",
            "subject_id",
            "subject_label",
            "claim",
            "rejection_reason",
            "supporting_protein_refs",
            "supporting_site_keys",
            "supporting_pathway_ids",
            "source_ids",
            "rejection_note",
        )
    )
    for entry in report.rejected_candidates:
        writer.writerow(
            (
                entry.hypothesis_id,
                entry.hypothesis_kind.value,
                entry.subject_id,
                entry.subject_label,
                entry.claim,
                entry.rejection_reason.value,
                ";".join(entry.supporting_protein_refs),
                ";".join(entry.supporting_site_keys),
                ";".join(entry.supporting_pathway_ids),
                ";".join(entry.source_ids),
                entry.rejection_note,
            )
        )
    return handle.getvalue()


def _candidate_rejection_reason(
    *,
    evidence_node_ids: tuple[str, ...],
    supporting_protein_refs: tuple[str, ...],
    supporting_site_keys: tuple[str, ...],
) -> BiologicalHypothesisRejectionReason | None:
    if not evidence_node_ids:
        return BiologicalHypothesisRejectionReason.MISSING_EVIDENCE_NODE_IDS
    if not supporting_protein_refs and not supporting_site_keys:
        return BiologicalHypothesisRejectionReason.MISSING_SUPPORTING_EVIDENCE
    return None


def _score_hypothesis_candidate(
    *,
    base_confidence_score: float,
    evidence_node_ids: tuple[str, ...],
    supporting_protein_refs: tuple[str, ...],
    supporting_site_keys: tuple[str, ...],
    opposing_evidence: tuple[str, ...],
) -> float:
    score = base_confidence_score
    score += min(0.12, 0.03 * len(evidence_node_ids))
    score += min(0.12, 0.03 * len(supporting_protein_refs))
    if supporting_site_keys:
        score += 0.05
    score -= min(0.20, 0.05 * len(opposing_evidence))
    return round(min(1.0, max(0.0, score)), 3)


def _confidence_tier(score: float) -> BiologicalHypothesisConfidenceTier:
    if score >= 0.8:
        return BiologicalHypothesisConfidenceTier.HIGH
    if score >= 0.6:
        return BiologicalHypothesisConfidenceTier.MODERATE
    return BiologicalHypothesisConfidenceTier.LOW


def _default_next_experiment_suggestion(
    candidate: BiologicalHypothesisCandidate,
) -> str:
    if candidate.supporting_site_keys:
        return (
            "confirm the site-specific signal with a targeted phosphopeptide assay "
            "across the same contrast"
        )
    if candidate.hypothesis_kind is BiologicalHypothesisKind.PATHWAY_ACTIVITY:
        return (
            "perturb the pathway and quantify the named supporting proteins in an "
            "orthogonal follow-up experiment"
        )
    if candidate.hypothesis_kind is BiologicalHypothesisKind.REGULATOR_ACTIVITY:
        return (
            "perturb the regulator and measure the supporting proteins or sites in a "
            "targeted follow-up assay"
        )
    if len(candidate.supporting_protein_refs) > 1:
        return (
            "verify the coordinated protein pattern with a targeted multiplex assay "
            "in an independent cohort"
        )
    return (
        "validate the protein change with an orthogonal targeted assay in an "
        "independent cohort"
    )


def _build_rejection_note(reason: BiologicalHypothesisRejectionReason) -> str:
    if reason is BiologicalHypothesisRejectionReason.MISSING_EVIDENCE_NODE_IDS:
        return (
            "candidate withheld because the workflow could not anchor it onto owned "
            "evidence graph node ids"
        )
    return (
        "candidate withheld because it did not retain supporting proteins or sites "
        "after evidence reconciliation"
    )


def _format_float(value: float) -> str:
    return f"{value:.3f}".rstrip("0").rstrip(".")


__all__ = [
    "BiologicalHypothesisCandidate",
    "BiologicalHypothesisConfidenceTier",
    "BiologicalHypothesisEntry",
    "BiologicalHypothesisKind",
    "BiologicalHypothesisRejectionReason",
    "BiologicalHypothesisReport",
    "BiologicalHypothesisSummary",
    "RejectedBiologicalHypothesisCandidate",
    "build_biological_hypothesis_report",
    "render_biological_hypothesis_summary_tsv",
    "render_biological_hypothesis_tsv",
    "render_rejected_biological_hypothesis_candidate_tsv",
]
