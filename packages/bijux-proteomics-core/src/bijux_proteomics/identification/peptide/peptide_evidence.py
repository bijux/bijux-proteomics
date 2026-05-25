# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Owned peptide evidence classification over observed peptide support."""

from __future__ import annotations

import csv
from enum import StrEnum
import hashlib
import io
import json

from pydantic import ConfigDict, Field

from bijux_proteomics.identification.contracts import (
    PsmRecord,
    TargetDecoyContaminantClass,
    TargetDecoyLabel,
)
from bijux_proteomics.identification.peptide.cross_run_reproducibility import (
    CrossRunReproducibilityClass,
    RunDetectionContext,
    build_peptide_cross_run_reproducibility_report,
)
from bijux_proteomics.identification.peptide_target_decoy_fdr import (
    build_peptide_target_decoy_fdr_report,
)
from bijux_proteomics_foundation import JsonModel


class PeptideEvidenceClass(StrEnum):
    """Primary evidence class over one observed peptide."""

    STRONG = "strong"
    MODERATE = "moderate"
    WEAK = "weak"
    SHARED = "shared"
    AMBIGUOUS = "ambiguous"
    CONTAMINANT = "contaminant"
    DECOY = "decoy"


class PeptideEvidenceTag(StrEnum):
    """Orthogonal evidence tags over one observed peptide."""

    UNIQUE = "unique"
    SHARED = "shared"
    MODIFIED = "modified"
    REPRODUCIBLE = "reproducible"
    CONDITION_SPECIFIC = "condition_specific"
    SINGLE_RUN_ONLY = "single_run_only"
    EXPLORATORY = "exploratory"
    CONTAMINANT = "contaminant"
    DECOY = "decoy"
    AMBIGUOUS = "ambiguous"


class PeptideEvidenceEntry(JsonModel):
    """One owned peptide evidence row."""

    model_config = ConfigDict(extra="forbid")

    peptide: str = Field(..., min_length=1)
    canonical_peptide: str = Field(..., min_length=1)
    primary_class: PeptideEvidenceClass
    tags: tuple[PeptideEvidenceTag, ...] = Field(default_factory=tuple)
    peptide_q_value: float = Field(..., ge=0.0)
    accepted: bool
    psm_count: int = Field(..., ge=1)
    spectrum_count: int = Field(..., ge=1)
    run_count: int = Field(..., ge=0)
    detection_frequency: float = Field(..., ge=0.0, le=1.0)
    replicate_consistency: float = Field(..., ge=0.0, le=1.0)
    condition_specificity: float = Field(..., ge=0.0, le=1.0)
    detected_condition_count: int = Field(..., ge=0)
    reproducibility_class: CrossRunReproducibilityClass
    exploratory_override: bool = False
    best_score: float
    charge_states: tuple[int, ...] = Field(default_factory=tuple)
    run_ids: tuple[str, ...] = Field(default_factory=tuple)
    protein_refs: tuple[str, ...] = Field(default_factory=tuple)
    target_decoy_label: TargetDecoyLabel
    target_decoy_contaminant_class: TargetDecoyContaminantClass
    contaminant_flag: bool = False
    explanation: str = Field(..., min_length=1)


class PeptideEvidenceSummary(JsonModel):
    """Compact summary across peptide evidence classes."""

    model_config = ConfigDict(extra="forbid")

    total_peptides: int = Field(..., ge=0)
    accepted_peptides: int = Field(..., ge=0)
    rejected_peptides: int = Field(..., ge=0)
    strong_count: int = Field(..., ge=0)
    moderate_count: int = Field(..., ge=0)
    weak_count: int = Field(..., ge=0)
    shared_count: int = Field(..., ge=0)
    ambiguous_count: int = Field(..., ge=0)
    unique_count: int = Field(..., ge=0)
    modified_count: int = Field(..., ge=0)
    reproducible_count: int = Field(..., ge=0)
    condition_specific_count: int = Field(..., ge=0)
    single_run_only_count: int = Field(..., ge=0)
    exploratory_count: int = Field(..., ge=0)
    contaminant_count: int = Field(..., ge=0)
    decoy_count: int = Field(..., ge=0)


class PeptideEvidenceReport(JsonModel):
    """Owned peptide evidence classification packet."""

    model_config = ConfigDict(extra="forbid")

    threshold: float | None = Field(default=None, ge=0.0)
    score_orientation: str = Field(..., pattern="^(higher_better|lower_better)$")
    strong_q_value: float = Field(..., ge=0.0)
    reproducible_spectrum_count: int = Field(..., ge=2)
    reproducibility_hash: str = Field(..., min_length=64, max_length=64)
    summary: PeptideEvidenceSummary
    entries: tuple[PeptideEvidenceEntry, ...] = Field(default_factory=tuple)


def build_peptide_evidence_report(
    records: tuple[PsmRecord, ...],
    *,
    threshold: float | None = 0.05,
    score_orientation: str = "higher_better",
    strong_q_value: float = 0.01,
    reproducible_spectrum_count: int = 2,
    run_contexts: tuple[RunDetectionContext, ...] = (),
    exploratory_canonical_peptides: tuple[str, ...] = (),
) -> PeptideEvidenceReport:
    """Build one owned peptide evidence classification report."""
    if strong_q_value < 0.0:
        raise ValueError("strong_q_value must be non-negative")
    if reproducible_spectrum_count < 2:
        raise ValueError("reproducible_spectrum_count must be at least 2")

    grouped_records: dict[str, list[PsmRecord]] = {}
    for record in records:
        grouped_records.setdefault(record.canonical_peptide, []).append(record)

    entries: list[PeptideEvidenceEntry] = []
    peptide_fdr = build_peptide_target_decoy_fdr_report(
        records,
        threshold=threshold,
        score_orientation=score_orientation,
        evidence_policy="best_score",
    )
    reproducibility_report = build_peptide_cross_run_reproducibility_report(
        records,
        run_contexts=run_contexts,
        exploratory_canonical_peptides=exploratory_canonical_peptides,
    )
    reproducibility_by_peptide = {
        entry.entity_id: entry for entry in reproducibility_report.entries
    }
    for ranked_entry in peptide_fdr.entries:
        rollup = ranked_entry.evidence
        supporting_records = tuple(grouped_records[rollup.canonical_peptide])
        reproducibility = reproducibility_by_peptide[rollup.canonical_peptide]
        run_ids = reproducibility.run_ids
        target_decoy_contaminant_class = _combine_target_decoy_contaminant_class(
            tuple(
                record.target_decoy_contaminant_class for record in supporting_records
            )
        )
        contaminant_flag = (
            target_decoy_contaminant_class
            is TargetDecoyContaminantClass.CONTAMINANT
        ) or any(record.contaminant_flag for record in supporting_records)
        shared = len(rollup.protein_refs) > 1
        modified = "[" in rollup.canonical_peptide
        reproducible = (
            (
                reproducibility.reproducibility_class
                in {
                    CrossRunReproducibilityClass.REPRODUCIBLE,
                    CrossRunReproducibilityClass.CONDITION_SPECIFIC,
                    CrossRunReproducibilityClass.EXPLORATORY,
                }
            )
            if reproducibility.run_ids
            else rollup.spectrum_count >= reproducible_spectrum_count
        )
        primary_class, explanation = _classify_primary_class(
            target_decoy_label=rollup.target_decoy_label,
            target_decoy_contaminant_class=target_decoy_contaminant_class,
            contaminant_flag=contaminant_flag,
            has_protein_refs=bool(rollup.protein_refs),
            shared=shared,
            accepted=ranked_entry.accepted,
            q_value=ranked_entry.q_value,
            strong_q_value=strong_q_value,
            reproducibility_class=reproducibility.reproducibility_class,
            reproducible=reproducible,
        )
        explanation = f"{explanation}; {reproducibility.explanation}"
        entries.append(
            PeptideEvidenceEntry(
                peptide=rollup.peptide,
                canonical_peptide=rollup.canonical_peptide,
                primary_class=primary_class,
                tags=_build_tags(
                    shared=shared,
                    modified=modified,
                    reproducible=reproducible,
                    reproducibility_class=reproducibility.reproducibility_class,
                    contaminant_flag=contaminant_flag,
                    target_decoy_label=rollup.target_decoy_label,
                    target_decoy_contaminant_class=target_decoy_contaminant_class,
                ),
                peptide_q_value=ranked_entry.q_value,
                accepted=ranked_entry.accepted,
                psm_count=rollup.psm_count,
                spectrum_count=rollup.spectrum_count,
                run_count=reproducibility.detected_run_count,
                detection_frequency=reproducibility.detection_frequency,
                replicate_consistency=reproducibility.replicate_consistency,
                condition_specificity=reproducibility.condition_specificity,
                detected_condition_count=reproducibility.detected_condition_count,
                reproducibility_class=reproducibility.reproducibility_class,
                exploratory_override=reproducibility.exploratory_override,
                best_score=rollup.best_score,
                charge_states=rollup.charge_states,
                run_ids=run_ids,
                protein_refs=rollup.protein_refs,
                target_decoy_label=rollup.target_decoy_label,
                target_decoy_contaminant_class=target_decoy_contaminant_class,
                contaminant_flag=contaminant_flag,
                explanation=explanation,
            )
        )

    payload = {
        "threshold": threshold,
        "score_orientation": score_orientation,
        "strong_q_value": strong_q_value,
        "reproducible_spectrum_count": reproducible_spectrum_count,
        "run_contexts": [context.to_dict() for context in run_contexts],
        "exploratory_canonical_peptides": list(exploratory_canonical_peptides),
        "entries": [entry.to_dict() for entry in entries],
    }
    summary = PeptideEvidenceSummary(
        total_peptides=len(entries),
        accepted_peptides=sum(1 for entry in entries if entry.accepted),
        rejected_peptides=sum(1 for entry in entries if not entry.accepted),
        strong_count=sum(
            1 for entry in entries if entry.primary_class is PeptideEvidenceClass.STRONG
        ),
        moderate_count=sum(
            1
            for entry in entries
            if entry.primary_class is PeptideEvidenceClass.MODERATE
        ),
        weak_count=sum(
            1 for entry in entries if entry.primary_class is PeptideEvidenceClass.WEAK
        ),
        shared_count=sum(
            1 for entry in entries if entry.primary_class is PeptideEvidenceClass.SHARED
        ),
        ambiguous_count=sum(
            1
            for entry in entries
            if entry.primary_class is PeptideEvidenceClass.AMBIGUOUS
        ),
        unique_count=sum(1 for entry in entries if PeptideEvidenceTag.UNIQUE in entry.tags),
        modified_count=sum(
            1 for entry in entries if PeptideEvidenceTag.MODIFIED in entry.tags
        ),
        reproducible_count=sum(
            1 for entry in entries if PeptideEvidenceTag.REPRODUCIBLE in entry.tags
        ),
        condition_specific_count=sum(
            1
            for entry in entries
            if entry.reproducibility_class
            is CrossRunReproducibilityClass.CONDITION_SPECIFIC
        ),
        single_run_only_count=sum(
            1
            for entry in entries
            if entry.reproducibility_class
            is CrossRunReproducibilityClass.SINGLE_RUN_ONLY
        ),
        exploratory_count=sum(
            1
            for entry in entries
            if entry.reproducibility_class is CrossRunReproducibilityClass.EXPLORATORY
        ),
        contaminant_count=sum(
            1
            for entry in entries
            if entry.primary_class is PeptideEvidenceClass.CONTAMINANT
        ),
        decoy_count=sum(
            1 for entry in entries if entry.primary_class is PeptideEvidenceClass.DECOY
        ),
    )
    return PeptideEvidenceReport(
        threshold=threshold,
        score_orientation=score_orientation,
        strong_q_value=strong_q_value,
        reproducible_spectrum_count=reproducible_spectrum_count,
        reproducibility_hash=hashlib.sha256(
            json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest(),
        summary=summary,
        entries=tuple(entries),
    )


def render_peptide_evidence_summary_tsv(report: PeptideEvidenceReport) -> str:
    """Render the peptide evidence summary ledger as TSV."""
    buffer = io.StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(("metric", "value"))
    for metric, value in (
        ("threshold", "" if report.threshold is None else report.threshold),
        ("score_orientation", report.score_orientation),
        ("strong_q_value", report.strong_q_value),
        ("reproducible_spectrum_count", report.reproducible_spectrum_count),
        ("reproducibility_hash", report.reproducibility_hash),
        ("total_peptides", report.summary.total_peptides),
        ("accepted_peptides", report.summary.accepted_peptides),
        ("rejected_peptides", report.summary.rejected_peptides),
        ("strong_count", report.summary.strong_count),
        ("moderate_count", report.summary.moderate_count),
        ("weak_count", report.summary.weak_count),
        ("shared_count", report.summary.shared_count),
        ("ambiguous_count", report.summary.ambiguous_count),
        ("unique_count", report.summary.unique_count),
        ("modified_count", report.summary.modified_count),
        ("reproducible_count", report.summary.reproducible_count),
        ("condition_specific_count", report.summary.condition_specific_count),
        ("single_run_only_count", report.summary.single_run_only_count),
        ("exploratory_count", report.summary.exploratory_count),
        ("contaminant_count", report.summary.contaminant_count),
        ("decoy_count", report.summary.decoy_count),
    ):
        writer.writerow((metric, value))
    return buffer.getvalue()


def render_peptide_evidence_entries_tsv(report: PeptideEvidenceReport) -> str:
    """Render peptide evidence rows as TSV."""
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
            "run_count",
            "detection_frequency",
            "replicate_consistency",
            "condition_specificity",
            "detected_condition_count",
            "reproducibility_class",
            "exploratory_override",
            "best_score",
            "charge_states",
            "run_ids",
            "protein_refs",
            "target_decoy_label",
            "target_decoy_contaminant_class",
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
                entry.run_count,
                entry.detection_frequency,
                entry.replicate_consistency,
                entry.condition_specificity,
                entry.detected_condition_count,
                entry.reproducibility_class.value,
                str(entry.exploratory_override).lower(),
                entry.best_score,
                ";".join(str(charge) for charge in entry.charge_states),
                ";".join(entry.run_ids),
                ";".join(entry.protein_refs),
                entry.target_decoy_label.value,
                entry.target_decoy_contaminant_class.value,
                str(entry.contaminant_flag).lower(),
                entry.explanation,
            )
        )
    return buffer.getvalue()


def _build_tags(
    *,
    shared: bool,
    modified: bool,
    reproducible: bool,
    reproducibility_class: CrossRunReproducibilityClass,
    contaminant_flag: bool,
    target_decoy_label: TargetDecoyLabel,
    target_decoy_contaminant_class: TargetDecoyContaminantClass,
) -> tuple[PeptideEvidenceTag, ...]:
    tags: list[PeptideEvidenceTag] = [
        PeptideEvidenceTag.SHARED if shared else PeptideEvidenceTag.UNIQUE
    ]
    if modified:
        tags.append(PeptideEvidenceTag.MODIFIED)
    if reproducible:
        tags.append(PeptideEvidenceTag.REPRODUCIBLE)
    if reproducibility_class is CrossRunReproducibilityClass.CONDITION_SPECIFIC:
        tags.append(PeptideEvidenceTag.CONDITION_SPECIFIC)
    if reproducibility_class is CrossRunReproducibilityClass.SINGLE_RUN_ONLY:
        tags.append(PeptideEvidenceTag.SINGLE_RUN_ONLY)
    if reproducibility_class is CrossRunReproducibilityClass.EXPLORATORY:
        tags.append(PeptideEvidenceTag.EXPLORATORY)
    if contaminant_flag:
        tags.append(PeptideEvidenceTag.CONTAMINANT)
    if target_decoy_label is TargetDecoyLabel.DECOY:
        tags.append(PeptideEvidenceTag.DECOY)
    if target_decoy_contaminant_class is TargetDecoyContaminantClass.MIXED:
        tags.append(PeptideEvidenceTag.AMBIGUOUS)
    return tuple(tags)


def _combine_target_decoy_contaminant_class(
    classes: tuple[TargetDecoyContaminantClass, ...],
) -> TargetDecoyContaminantClass:
    active = tuple(
        evidence_class
        for evidence_class in classes
        if evidence_class is not TargetDecoyContaminantClass.UNKNOWN
    )
    if not active:
        return TargetDecoyContaminantClass.UNKNOWN
    if all(
        evidence_class is TargetDecoyContaminantClass.DECOY
        for evidence_class in active
    ):
        return TargetDecoyContaminantClass.DECOY
    if all(
        evidence_class is TargetDecoyContaminantClass.CONTAMINANT
        for evidence_class in active
    ):
        return TargetDecoyContaminantClass.CONTAMINANT
    if all(
        evidence_class is TargetDecoyContaminantClass.TARGET
        for evidence_class in active
    ):
        return TargetDecoyContaminantClass.TARGET
    return TargetDecoyContaminantClass.MIXED


def _classify_primary_class(
    *,
    target_decoy_label: TargetDecoyLabel,
    target_decoy_contaminant_class: TargetDecoyContaminantClass,
    contaminant_flag: bool,
    has_protein_refs: bool,
    shared: bool,
    accepted: bool,
    q_value: float,
    strong_q_value: float,
    reproducibility_class: CrossRunReproducibilityClass,
    reproducible: bool,
) -> tuple[PeptideEvidenceClass, str]:
    if target_decoy_contaminant_class is TargetDecoyContaminantClass.DECOY or (
        target_decoy_label is TargetDecoyLabel.DECOY and not contaminant_flag
    ):
        return (
            PeptideEvidenceClass.DECOY,
            "peptide evidence is carried only by decoy proteins",
        )
    if target_decoy_contaminant_class is TargetDecoyContaminantClass.CONTAMINANT or (
        contaminant_flag
        and target_decoy_contaminant_class is not TargetDecoyContaminantClass.TARGET
    ):
        return (
            PeptideEvidenceClass.CONTAMINANT,
            "peptide evidence includes only contaminant protein support",
        )
    if (
        target_decoy_contaminant_class is TargetDecoyContaminantClass.MIXED
        or target_decoy_label is TargetDecoyLabel.MIXED
        or not has_protein_refs
    ):
        return (
            PeptideEvidenceClass.AMBIGUOUS,
            "protein mapping remains mixed or incomplete across target, decoy, or contaminant support",
        )
    if not accepted:
        reasons = ["peptide-level FDR does not accept the peptide"]
        if shared:
            reasons.append("protein mapping remains shared")
        return (PeptideEvidenceClass.WEAK, "; ".join(reasons))
    if shared:
        if (
            reproducible
            and q_value <= strong_q_value
        ):
            return (
                PeptideEvidenceClass.SHARED,
                "shared peptide is accepted with stable support but cannot support protein-specific evidence on its own",
            )
        return (
            PeptideEvidenceClass.WEAK,
            "shared peptide is accepted but lacks the q-value or reproducible support required for stronger non-unique evidence",
        )
    if (
        q_value <= strong_q_value
        and reproducible
    ):
        return (
            PeptideEvidenceClass.STRONG,
            f"unique peptide passes peptide-level FDR, meets the strong-evidence q-value threshold at {strong_q_value:.4f}, and is reproducibly observed",
        )
    return (
        PeptideEvidenceClass.MODERATE,
        "unique peptide passes peptide-level FDR but lacks either reproducible support or the strong-evidence q-value threshold",
    )


__all__ = [
    "PeptideEvidenceClass",
    "PeptideEvidenceEntry",
    "PeptideEvidenceReport",
    "PeptideEvidenceSummary",
    "PeptideEvidenceTag",
    "build_peptide_evidence_report",
    "render_peptide_evidence_entries_tsv",
    "render_peptide_evidence_summary_tsv",
]
