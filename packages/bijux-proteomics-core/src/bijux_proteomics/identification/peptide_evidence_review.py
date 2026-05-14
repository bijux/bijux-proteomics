# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Reviewer-facing peptide evidence classification."""

from __future__ import annotations

import csv
from enum import StrEnum
import io

from pydantic import ConfigDict, Field

from bijux_proteomics.identification.contracts import (
    FdrEvidenceLevel,
    PsmRecord,
    TargetDecoyLabel,
    calculate_level_specific_fdr,
    rollup_peptide_evidence,
)
from bijux_proteomics_foundation import JsonModel


class PeptideEvidencePrimaryClass(StrEnum):
    """Primary evidence class over one observed peptide."""

    STRONG = "strong"
    WEAK = "weak"
    CONTAMINANT = "contaminant"
    DECOY = "decoy"


class PeptideEvidenceTag(StrEnum):
    """Orthogonal evidence tags over one observed peptide."""

    UNIQUE = "unique"
    SHARED = "shared"
    MODIFIED = "modified"
    CONTAMINANT = "contaminant"
    DECOY = "decoy"


class PeptideEvidenceReviewEntry(JsonModel):
    """One peptide evidence review row."""

    model_config = ConfigDict(extra="forbid")

    peptide: str = Field(..., min_length=1)
    canonical_peptide: str = Field(..., min_length=1)
    primary_class: PeptideEvidencePrimaryClass
    tags: tuple[PeptideEvidenceTag, ...] = Field(default_factory=tuple)
    peptide_q_value: float = Field(..., ge=0.0)
    accepted: bool
    psm_count: int = Field(..., ge=1)
    spectrum_count: int = Field(..., ge=1)
    best_score: float
    charge_states: tuple[int, ...] = Field(default_factory=tuple)
    protein_refs: tuple[str, ...] = Field(default_factory=tuple)
    target_decoy_label: TargetDecoyLabel
    contaminant_flag: bool = False
    explanation: str = Field(..., min_length=1)


class PeptideEvidenceReviewSummary(JsonModel):
    """Compact summary across peptide evidence classes."""

    model_config = ConfigDict(extra="forbid")

    total_peptides: int = Field(..., ge=0)
    accepted_peptides: int = Field(..., ge=0)
    rejected_peptides: int = Field(..., ge=0)
    strong_count: int = Field(..., ge=0)
    weak_count: int = Field(..., ge=0)
    unique_count: int = Field(..., ge=0)
    shared_count: int = Field(..., ge=0)
    modified_count: int = Field(..., ge=0)
    contaminant_count: int = Field(..., ge=0)
    decoy_count: int = Field(..., ge=0)


class PeptideEvidenceReviewReport(JsonModel):
    """One review packet over observed peptide evidence."""

    model_config = ConfigDict(extra="forbid")

    threshold: float | None = Field(default=None, ge=0.0)
    score_orientation: str = Field(..., pattern="^(higher_better|lower_better)$")
    strong_q_value: float = Field(..., ge=0.0)
    summary: PeptideEvidenceReviewSummary
    entries: tuple[PeptideEvidenceReviewEntry, ...] = Field(default_factory=tuple)


def build_peptide_evidence_review_report(
    records: tuple[PsmRecord, ...],
    *,
    threshold: float | None = 0.05,
    score_orientation: str = "higher_better",
    strong_q_value: float = 0.01,
) -> PeptideEvidenceReviewReport:
    """Build one direct peptide evidence classification report."""
    if strong_q_value < 0.0:
        raise ValueError("strong_q_value must be non-negative")

    peptide_rollups = rollup_peptide_evidence(records)
    peptide_fdr_entries = {
        entry.entity_id: entry
        for entry in calculate_level_specific_fdr(
            records,
            threshold=threshold,
            score_orientation=score_orientation,
        ).peptide_entries
        if entry.evidence_level is FdrEvidenceLevel.PEPTIDE
    }

    entries: list[PeptideEvidenceReviewEntry] = []
    for rollup in peptide_rollups:
        evidence = peptide_fdr_entries[rollup.canonical_peptide]
        contaminant_flag = any(
            protein_ref.startswith("CON__") for protein_ref in rollup.protein_refs
        )
        shared = len(rollup.protein_refs) > 1
        modified = "[" in rollup.canonical_peptide
        primary_class, explanation = _classify_primary_class(
            target_decoy_label=rollup.target_decoy_label,
            contaminant_flag=contaminant_flag,
            shared=shared,
            accepted=evidence.accepted,
            q_value=evidence.q_value,
            strong_q_value=strong_q_value,
        )
        tags: list[PeptideEvidenceTag] = [
            PeptideEvidenceTag.SHARED if shared else PeptideEvidenceTag.UNIQUE
        ]
        if modified:
            tags.append(PeptideEvidenceTag.MODIFIED)
        if contaminant_flag:
            tags.append(PeptideEvidenceTag.CONTAMINANT)
        if rollup.target_decoy_label is TargetDecoyLabel.DECOY:
            tags.append(PeptideEvidenceTag.DECOY)
        entries.append(
            PeptideEvidenceReviewEntry(
                peptide=rollup.peptide,
                canonical_peptide=rollup.canonical_peptide,
                primary_class=primary_class,
                tags=tuple(tags),
                peptide_q_value=evidence.q_value,
                accepted=evidence.accepted,
                psm_count=rollup.psm_count,
                spectrum_count=rollup.spectrum_count,
                best_score=rollup.best_score,
                charge_states=rollup.charge_states,
                protein_refs=rollup.protein_refs,
                target_decoy_label=rollup.target_decoy_label,
                contaminant_flag=contaminant_flag,
                explanation=explanation,
            )
        )

    return PeptideEvidenceReviewReport(
        threshold=threshold,
        score_orientation=score_orientation,
        strong_q_value=strong_q_value,
        summary=PeptideEvidenceReviewSummary(
            total_peptides=len(entries),
            accepted_peptides=sum(1 for entry in entries if entry.accepted),
            rejected_peptides=sum(1 for entry in entries if not entry.accepted),
            strong_count=sum(
                1
                for entry in entries
                if entry.primary_class is PeptideEvidencePrimaryClass.STRONG
            ),
            weak_count=sum(
                1
                for entry in entries
                if entry.primary_class is PeptideEvidencePrimaryClass.WEAK
            ),
            unique_count=sum(
                1 for entry in entries if PeptideEvidenceTag.UNIQUE in entry.tags
            ),
            shared_count=sum(
                1 for entry in entries if PeptideEvidenceTag.SHARED in entry.tags
            ),
            modified_count=sum(
                1 for entry in entries if PeptideEvidenceTag.MODIFIED in entry.tags
            ),
            contaminant_count=sum(
                1
                for entry in entries
                if entry.primary_class is PeptideEvidencePrimaryClass.CONTAMINANT
            ),
            decoy_count=sum(
                1
                for entry in entries
                if entry.primary_class is PeptideEvidencePrimaryClass.DECOY
            ),
        ),
        entries=tuple(entries),
    )


def render_peptide_evidence_summary_tsv(report: PeptideEvidenceReviewReport) -> str:
    """Render the peptide evidence summary ledger as TSV."""
    buffer = io.StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(("metric", "value"))
    for metric, value in (
        ("threshold", "" if report.threshold is None else report.threshold),
        ("score_orientation", report.score_orientation),
        ("strong_q_value", report.strong_q_value),
        ("total_peptides", report.summary.total_peptides),
        ("accepted_peptides", report.summary.accepted_peptides),
        ("rejected_peptides", report.summary.rejected_peptides),
        ("strong_count", report.summary.strong_count),
        ("weak_count", report.summary.weak_count),
        ("unique_count", report.summary.unique_count),
        ("shared_count", report.summary.shared_count),
        ("modified_count", report.summary.modified_count),
        ("contaminant_count", report.summary.contaminant_count),
        ("decoy_count", report.summary.decoy_count),
    ):
        writer.writerow((metric, value))
    return buffer.getvalue()


def render_peptide_evidence_entries_tsv(report: PeptideEvidenceReviewReport) -> str:
    """Render peptide evidence review rows as TSV."""
    buffer = io.StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "peptide",
            "canonical_peptide",
            "primary_class",
            "tags",
            "peptide_q_value",
            "accepted",
            "psm_count",
            "spectrum_count",
            "best_score",
            "charge_states",
            "protein_refs",
            "target_decoy_label",
            "contaminant_flag",
            "explanation",
        )
    )
    for entry in report.entries:
        writer.writerow(
            (
                entry.peptide,
                entry.canonical_peptide,
                entry.primary_class.value,
                ";".join(tag.value for tag in entry.tags),
                entry.peptide_q_value,
                str(entry.accepted).lower(),
                entry.psm_count,
                entry.spectrum_count,
                entry.best_score,
                ";".join(str(charge) for charge in entry.charge_states),
                ";".join(entry.protein_refs),
                entry.target_decoy_label.value,
                str(entry.contaminant_flag).lower(),
                entry.explanation,
            )
        )
    return buffer.getvalue()


def _classify_primary_class(
    *,
    target_decoy_label: TargetDecoyLabel,
    contaminant_flag: bool,
    shared: bool,
    accepted: bool,
    q_value: float,
    strong_q_value: float,
) -> tuple[PeptideEvidencePrimaryClass, str]:
    if target_decoy_label is TargetDecoyLabel.DECOY:
        return (
            PeptideEvidencePrimaryClass.DECOY,
            "peptide evidence is carried only by decoy proteins",
        )
    if contaminant_flag:
        return (
            PeptideEvidencePrimaryClass.CONTAMINANT,
            "peptide evidence includes contaminant protein support",
        )
    if accepted and q_value <= strong_q_value and not shared:
        return (
            PeptideEvidencePrimaryClass.STRONG,
            f"unique peptide passes peptide-level FDR and the strong-evidence q-value threshold at {strong_q_value:.4f}",
        )

    reasons: list[str] = []
    if shared:
        reasons.append("peptide is shared across multiple observed proteins")
    if not accepted:
        reasons.append("peptide-level FDR does not accept the peptide")
    elif q_value > strong_q_value:
        reasons.append(
            f"peptide-level q-value {q_value:.4f} misses the strong-evidence threshold"
        )
    if target_decoy_label is TargetDecoyLabel.MIXED:
        reasons.append("target and decoy support remain mixed")
    elif target_decoy_label is TargetDecoyLabel.UNKNOWN:
        reasons.append("target-decoy support is unknown")
    explanation = (
        "; ".join(reasons)
        if reasons
        else "peptide evidence remains reviewer-facing but not strong"
    )
    return (PeptideEvidencePrimaryClass.WEAK, explanation)
