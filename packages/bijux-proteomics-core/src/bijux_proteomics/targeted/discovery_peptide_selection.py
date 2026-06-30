# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Discovery-backed peptide selection for targeted follow-up assays."""

from __future__ import annotations

import csv
from enum import StrEnum
from io import StringIO

from pydantic import ConfigDict, Field

from bijux_proteomics.chemistry.modified_peptide_parser import (
    ModifiedPeptideNotationDialect,
    parse_modified_peptide_notation,
)
from bijux_proteomics.identification.peptide_evidence import (
    PeptideEvidenceClass,
    PeptideEvidenceEntry,
)
from bijux_proteomics.sequences.fasta import NormalizedProteinRecord
from bijux_proteomics.sequences.peptide_chemical_liability import (
    PeptideChemicalLiabilityTier,
    build_peptide_chemical_liability_report,
)
from bijux_proteomics.sequences.peptide_detectability import (
    PeptideDetectabilityTier,
    build_peptide_detectability_report,
)
from bijux_proteomics.sequences.peptide_uniqueness_index import (
    PeptideUniquenessClass,
    build_peptide_uniqueness_index,
)
from bijux_proteomics.sequences.digestion import (
    PeptideDigestionMode,
    ProteaseRule,
    digest_protein_records,
    get_protease_rule,
)
from bijux_proteomics.sequences.peptide_uniqueness_index import (
    PeptideUniquenessIndexEntry,
    PeptideUniquenessIndexReport,
)
from bijux_proteomics_foundation import JsonModel

_MIN_DETECTABILITY_SCORE = 0.55
_MIN_SUITABILITY_SCORE = 0.5
_SUPPORTED_OBSERVED_CLASSES = frozenset(
    {
        PeptideEvidenceClass.STRONG,
        PeptideEvidenceClass.MODERATE,
        PeptideEvidenceClass.WEAK,
    }
)
_UNIQUE_SELECTION_CLASSES = frozenset({PeptideUniquenessClass.UNIQUE})


class DiscoveryTargetProteinEntry(JsonModel):
    """One target protein selected from discovery outputs for targeted follow-up."""

    model_config = ConfigDict(extra="forbid")

    protein_group_id: str = Field(..., min_length=1)
    representative_protein_ref: str = Field(..., min_length=1)
    protein_refs: tuple[str, ...] = Field(default_factory=tuple)
    gene_symbol: str | None = None
    discovery_peptides: tuple[str, ...] = Field(default_factory=tuple)


class TargetedPeptideCandidateSource(StrEnum):
    """Source of evidence behind a targeted peptide recommendation."""

    OBSERVED_DISCOVERY = "observed_discovery"
    THEORETICAL_DIGEST = "theoretical_digest"


class TargetedPeptideSelectionRejectionCode(StrEnum):
    """Stable refusal reasons for peptide-target candidates."""

    DISCOVERY_EVIDENCE_REJECTED = "discovery_evidence_rejected"
    DISCOVERY_EVIDENCE_NOT_TARGET_SPECIFIC = "discovery_evidence_not_target_specific"
    NON_UNIQUE = "non_unique"
    LOW_DETECTABILITY = "low_detectability"
    CHEMICALLY_UNSUITABLE = "chemically_unsuitable"
    DUPLICATE_SEQUENCE = "duplicate_sequence"
    PROTEIN_SEQUENCE_MISSING = "protein_sequence_missing"


class DiscoveryTargetedPeptideSelectionEntry(JsonModel):
    """One ranked peptide recommendation for targeted assay follow-up."""

    model_config = ConfigDict(extra="forbid")

    target_protein_ref: str = Field(..., min_length=1)
    target_protein_group_id: str = Field(..., min_length=1)
    gene_symbol: str | None = None
    peptide_sequence: str = Field(..., min_length=1)
    canonical_peptide: str = Field(..., min_length=1)
    candidate_source: TargetedPeptideCandidateSource
    rank: int = Field(..., ge=1)
    observed_in_discovery: bool
    observed_psm_count: int | None = Field(default=None, ge=0)
    run_count: int | None = Field(default=None, ge=0)
    detection_frequency: float | None = Field(default=None, ge=0.0, le=1.0)
    replicate_consistency: float | None = Field(default=None, ge=0.0, le=1.0)
    primary_evidence_class: PeptideEvidenceClass | None = None
    uniqueness_class: PeptideUniquenessClass
    uniqueness_score: float = Field(..., ge=0.0, le=1.0)
    detectability_score: float = Field(..., ge=0.0, le=1.0)
    detectability_tier: PeptideDetectabilityTier
    suitability_score: float = Field(..., ge=0.0, le=1.0)
    liability_tier: PeptideChemicalLiabilityTier
    liability_codes: tuple[str, ...] = Field(default_factory=tuple)
    selection_score: float = Field(..., ge=0.0, le=1.0)
    selection_reasons: tuple[str, ...] = Field(default_factory=tuple)


class DiscoveryTargetedPeptideRejectionEntry(JsonModel):
    """One peptide candidate kept visible with explicit rejection reasons."""

    model_config = ConfigDict(extra="forbid")

    target_protein_ref: str = Field(..., min_length=1)
    target_protein_group_id: str = Field(..., min_length=1)
    gene_symbol: str | None = None
    peptide_sequence: str = Field(..., min_length=1)
    canonical_peptide: str = Field(..., min_length=1)
    candidate_source: TargetedPeptideCandidateSource
    observed_in_discovery: bool
    observed_psm_count: int | None = Field(default=None, ge=0)
    primary_evidence_class: PeptideEvidenceClass | None = None
    uniqueness_class: PeptideUniquenessClass | None = None
    detectability_score: float | None = Field(default=None, ge=0.0, le=1.0)
    suitability_score: float | None = Field(default=None, ge=0.0, le=1.0)
    rejection_codes: tuple[TargetedPeptideSelectionRejectionCode, ...] = Field(
        default_factory=tuple
    )
    explanation: str = Field(..., min_length=1)


class DiscoveryTargetedPeptideSelectionSummary(JsonModel):
    """Compact accounting over one discovery-to-targeted peptide selection pass."""

    model_config = ConfigDict(extra="forbid")

    target_protein_count: int = Field(..., ge=0)
    target_with_selected_peptides: int = Field(..., ge=0)
    selected_entry_count: int = Field(..., ge=0)
    observed_selected_entry_count: int = Field(..., ge=0)
    theoretical_selected_entry_count: int = Field(..., ge=0)
    rejected_candidate_count: int = Field(..., ge=0)


class DiscoveryTargetedPeptideSelectionReport(JsonModel):
    """Discovery-backed peptide selection report for targeted assay design."""

    model_config = ConfigDict(extra="forbid")

    protease: str = Field(..., min_length=1)
    missed_cleavages: int = Field(..., ge=0)
    top_peptides_per_target: int = Field(..., ge=1)
    summary: DiscoveryTargetedPeptideSelectionSummary
    selected_entries: tuple[DiscoveryTargetedPeptideSelectionEntry, ...] = Field(
        default_factory=tuple
    )
    rejected_candidates: tuple[DiscoveryTargetedPeptideRejectionEntry, ...] = Field(
        default_factory=tuple
    )
    note: str = Field(..., min_length=1)


def build_discovery_targeted_peptide_selection_report(
    targets: tuple[DiscoveryTargetProteinEntry, ...],
    peptide_evidence_entries: tuple[PeptideEvidenceEntry, ...],
    protein_records: tuple[NormalizedProteinRecord, ...],
    *,
    uniqueness_index: PeptideUniquenessIndexReport | None = None,
    protease: ProteaseRule | str = "trypsin",
    missed_cleavages: int = 0,
    top_peptides_per_target: int = 3,
) -> DiscoveryTargetedPeptideSelectionReport:
    """Rank targeted peptides from discovery evidence with explicit fallback logic."""

    if top_peptides_per_target < 1:
        raise ValueError("top_peptides_per_target must be at least 1")
    if missed_cleavages < 0:
        raise ValueError("missed_cleavages must be non-negative")

    protease_rule = (
        get_protease_rule(protease) if isinstance(protease, str) else protease
    )
    uniqueness_report = (
        uniqueness_index
        if uniqueness_index is not None
        else build_peptide_uniqueness_index(
            protein_records,
            protease=protease_rule,
            missed_cleavages=missed_cleavages,
            digestion_mode=PeptideDigestionMode.FULL,
        )
    )
    uniqueness_by_sequence = {
        entry.peptide_sequence: entry for entry in uniqueness_report.entries
    }
    proteins_by_ref = _index_protein_records(protein_records)
    evidence_entries = tuple(
        sorted(
            peptide_evidence_entries,
            key=lambda entry: (
                entry.canonical_peptide,
                -entry.psm_count,
                entry.primary_class.value,
            ),
        )
    )

    selected_entries: list[DiscoveryTargetedPeptideSelectionEntry] = []
    rejected_candidates: list[DiscoveryTargetedPeptideRejectionEntry] = []
    selected_target_refs: set[str] = set()

    for target in sorted(
        targets,
        key=lambda entry: (entry.representative_protein_ref, entry.protein_group_id),
    ):
        observed_candidates, observed_rejections = _score_observed_candidates(
            target=target,
            peptide_evidence_entries=evidence_entries,
            uniqueness_by_sequence=uniqueness_by_sequence,
            protease=protease_rule,
        )
        rejected_candidates.extend(observed_rejections)
        chosen_sequences: set[str] = set()

        ranked_candidates = sorted(
            observed_candidates,
            key=lambda entry: (-entry.selection_score, entry.canonical_peptide),
        )
        for candidate in ranked_candidates:
            if len(chosen_sequences) >= top_peptides_per_target:
                break
            if candidate.peptide_sequence in chosen_sequences:
                rejected_candidates.append(
                    DiscoveryTargetedPeptideRejectionEntry(
                        target_protein_ref=target.representative_protein_ref,
                        target_protein_group_id=target.protein_group_id,
                        gene_symbol=target.gene_symbol,
                        peptide_sequence=candidate.peptide_sequence,
                        canonical_peptide=candidate.canonical_peptide,
                        candidate_source=candidate.candidate_source,
                        observed_in_discovery=candidate.observed_in_discovery,
                        observed_psm_count=candidate.observed_psm_count,
                        primary_evidence_class=candidate.primary_evidence_class,
                        uniqueness_class=candidate.uniqueness_class,
                        detectability_score=candidate.detectability_score,
                        suitability_score=candidate.suitability_score,
                        rejection_codes=(
                            TargetedPeptideSelectionRejectionCode.DUPLICATE_SEQUENCE,
                        ),
                        explanation=(
                            "sequence is already selected for this target and is kept out "
                            "of the final panel to preserve peptide diversity"
                        ),
                    )
                )
                continue
            selected_entries.append(
                candidate.model_copy(update={"rank": len(chosen_sequences) + 1})
            )
            chosen_sequences.add(candidate.peptide_sequence)

        protein_record = proteins_by_ref.get(target.representative_protein_ref)
        if protein_record is None:
            rejected_candidates.append(
                DiscoveryTargetedPeptideRejectionEntry(
                    target_protein_ref=target.representative_protein_ref,
                    target_protein_group_id=target.protein_group_id,
                    gene_symbol=target.gene_symbol,
                    peptide_sequence=target.representative_protein_ref,
                    canonical_peptide=target.representative_protein_ref,
                    candidate_source=TargetedPeptideCandidateSource.THEORETICAL_DIGEST,
                    observed_in_discovery=False,
                    rejection_codes=(
                        TargetedPeptideSelectionRejectionCode.PROTEIN_SEQUENCE_MISSING,
                    ),
                    explanation=(
                        "target protein is not present in the governed FASTA, so "
                        "theoretical fallback peptide generation cannot proceed"
                    ),
                )
            )
        elif len(chosen_sequences) < top_peptides_per_target:
            fallback_candidates, fallback_rejections = _score_theoretical_candidates(
                target=target,
                protein_record=protein_record,
                uniqueness_by_sequence=uniqueness_by_sequence,
                protease=protease_rule,
                missed_cleavages=missed_cleavages,
                excluded_sequences=chosen_sequences
                | {entry.peptide_sequence for entry in observed_rejections},
            )
            rejected_candidates.extend(fallback_rejections)
            for candidate in sorted(
                fallback_candidates,
                key=lambda entry: (-entry.selection_score, entry.canonical_peptide),
            ):
                if len(chosen_sequences) >= top_peptides_per_target:
                    break
                if candidate.peptide_sequence in chosen_sequences:
                    continue
                selected_entries.append(
                    candidate.model_copy(update={"rank": len(chosen_sequences) + 1})
                )
                chosen_sequences.add(candidate.peptide_sequence)

        if chosen_sequences:
            selected_target_refs.add(target.representative_protein_ref)

    sorted_selected = tuple(
        sorted(
            selected_entries,
            key=lambda entry: (
                entry.target_protein_ref,
                entry.rank,
                entry.canonical_peptide,
            ),
        )
    )
    sorted_rejected = tuple(
        sorted(
            rejected_candidates,
            key=lambda entry: (
                entry.target_protein_ref,
                entry.candidate_source.value,
                entry.canonical_peptide,
            ),
        )
    )
    return DiscoveryTargetedPeptideSelectionReport(
        protease=protease_rule.name,
        missed_cleavages=missed_cleavages,
        top_peptides_per_target=top_peptides_per_target,
        summary=DiscoveryTargetedPeptideSelectionSummary(
            target_protein_count=len(targets),
            target_with_selected_peptides=len(selected_target_refs),
            selected_entry_count=len(sorted_selected),
            observed_selected_entry_count=sum(
                1
                for entry in sorted_selected
                if entry.candidate_source
                is TargetedPeptideCandidateSource.OBSERVED_DISCOVERY
            ),
            theoretical_selected_entry_count=sum(
                1
                for entry in sorted_selected
                if entry.candidate_source
                is TargetedPeptideCandidateSource.THEORETICAL_DIGEST
            ),
            rejected_candidate_count=len(sorted_rejected),
        ),
        selected_entries=sorted_selected,
        rejected_candidates=sorted_rejected,
        note=(
            "targeted peptide selection prefers observed discovery peptides that are "
            "unique, detectable, and chemically suitable, then falls back to "
            "governed theoretical digest candidates only when discovery evidence "
            "does not provide enough acceptable peptides for the target"
        ),
    )


def render_discovery_targeted_peptide_selection_summary_tsv(
    report: DiscoveryTargetedPeptideSelectionReport,
) -> str:
    """Render compact targeted-peptide selection summary accounting as TSV."""

    handle = StringIO()
    writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
    writer.writerow(("field", "value"))
    writer.writerow(("protease", report.protease))
    writer.writerow(("missed_cleavages", report.missed_cleavages))
    writer.writerow(("top_peptides_per_target", report.top_peptides_per_target))
    writer.writerow(("target_protein_count", report.summary.target_protein_count))
    writer.writerow(
        ("target_with_selected_peptides", report.summary.target_with_selected_peptides)
    )
    writer.writerow(("selected_entry_count", report.summary.selected_entry_count))
    writer.writerow(
        ("observed_selected_entry_count", report.summary.observed_selected_entry_count)
    )
    writer.writerow(
        (
            "theoretical_selected_entry_count",
            report.summary.theoretical_selected_entry_count,
        )
    )
    writer.writerow(
        ("rejected_candidate_count", report.summary.rejected_candidate_count)
    )
    writer.writerow(("note", report.note))
    return handle.getvalue()


def render_discovery_targeted_peptide_selection_selected_tsv(
    report: DiscoveryTargetedPeptideSelectionReport,
) -> str:
    """Render ranked targeted peptide recommendations as TSV."""

    handle = StringIO()
    writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "target_protein_ref",
            "target_protein_group_id",
            "gene_symbol",
            "rank",
            "candidate_source",
            "peptide_sequence",
            "canonical_peptide",
            "observed_in_discovery",
            "observed_psm_count",
            "run_count",
            "detection_frequency",
            "replicate_consistency",
            "primary_evidence_class",
            "uniqueness_class",
            "uniqueness_score",
            "detectability_score",
            "detectability_tier",
            "suitability_score",
            "liability_tier",
            "liability_codes",
            "selection_score",
            "selection_reasons",
        )
    )
    for entry in report.selected_entries:
        writer.writerow(
            (
                entry.target_protein_ref,
                entry.target_protein_group_id,
                "" if entry.gene_symbol is None else entry.gene_symbol,
                entry.rank,
                entry.candidate_source.value,
                entry.peptide_sequence,
                entry.canonical_peptide,
                str(entry.observed_in_discovery).lower(),
                "" if entry.observed_psm_count is None else entry.observed_psm_count,
                "" if entry.run_count is None else entry.run_count,
                ""
                if entry.detection_frequency is None
                else f"{entry.detection_frequency:.6f}",
                ""
                if entry.replicate_consistency is None
                else f"{entry.replicate_consistency:.6f}",
                ""
                if entry.primary_evidence_class is None
                else entry.primary_evidence_class.value,
                entry.uniqueness_class.value,
                f"{entry.uniqueness_score:.6f}",
                f"{entry.detectability_score:.6f}",
                entry.detectability_tier.value,
                f"{entry.suitability_score:.6f}",
                entry.liability_tier.value,
                ";".join(entry.liability_codes),
                f"{entry.selection_score:.6f}",
                ";".join(entry.selection_reasons),
            )
        )
    return handle.getvalue()


def render_discovery_targeted_peptide_selection_rejected_tsv(
    report: DiscoveryTargetedPeptideSelectionReport,
) -> str:
    """Render rejected targeted peptide candidates as TSV."""

    handle = StringIO()
    writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "target_protein_ref",
            "target_protein_group_id",
            "gene_symbol",
            "candidate_source",
            "peptide_sequence",
            "canonical_peptide",
            "observed_in_discovery",
            "observed_psm_count",
            "primary_evidence_class",
            "uniqueness_class",
            "detectability_score",
            "suitability_score",
            "rejection_codes",
            "explanation",
        )
    )
    for entry in report.rejected_candidates:
        writer.writerow(
            (
                entry.target_protein_ref,
                entry.target_protein_group_id,
                "" if entry.gene_symbol is None else entry.gene_symbol,
                entry.candidate_source.value,
                entry.peptide_sequence,
                entry.canonical_peptide,
                str(entry.observed_in_discovery).lower(),
                "" if entry.observed_psm_count is None else entry.observed_psm_count,
                ""
                if entry.primary_evidence_class is None
                else entry.primary_evidence_class.value,
                "" if entry.uniqueness_class is None else entry.uniqueness_class.value,
                ""
                if entry.detectability_score is None
                else f"{entry.detectability_score:.6f}",
                ""
                if entry.suitability_score is None
                else f"{entry.suitability_score:.6f}",
                ";".join(code.value for code in entry.rejection_codes),
                entry.explanation,
            )
        )
    return handle.getvalue()


def _score_observed_candidates(
    *,
    target: DiscoveryTargetProteinEntry,
    peptide_evidence_entries: tuple[PeptideEvidenceEntry, ...],
    uniqueness_by_sequence: dict[str, PeptideUniquenessIndexEntry],
    protease: ProteaseRule,
) -> tuple[
    tuple[DiscoveryTargetedPeptideSelectionEntry, ...],
    tuple[DiscoveryTargetedPeptideRejectionEntry, ...],
]:
    selected: list[DiscoveryTargetedPeptideSelectionEntry] = []
    rejected: list[DiscoveryTargetedPeptideRejectionEntry] = []
    target_protein_refs = {target.representative_protein_ref, *target.protein_refs}
    target_peptides = set(target.discovery_peptides)

    for evidence in peptide_evidence_entries:
        peptide_sequence, modification_assignments = _normalize_evidence_peptide(
            evidence.canonical_peptide
        )
        if target_peptides and peptide_sequence not in target_peptides:
            continue
        if target_protein_refs.isdisjoint(evidence.protein_refs):
            continue

        uniqueness_entry = uniqueness_by_sequence.get(peptide_sequence)
        if uniqueness_entry is None:
            rejected.append(
                DiscoveryTargetedPeptideRejectionEntry(
                    target_protein_ref=target.representative_protein_ref,
                    target_protein_group_id=target.protein_group_id,
                    gene_symbol=target.gene_symbol,
                    peptide_sequence=peptide_sequence,
                    canonical_peptide=evidence.canonical_peptide,
                    candidate_source=TargetedPeptideCandidateSource.OBSERVED_DISCOVERY,
                    observed_in_discovery=True,
                    observed_psm_count=evidence.psm_count,
                    primary_evidence_class=evidence.primary_class,
                    rejection_codes=(
                        TargetedPeptideSelectionRejectionCode.DISCOVERY_EVIDENCE_NOT_TARGET_SPECIFIC,
                    ),
                    explanation=(
                        "observed peptide is absent from the governed uniqueness index, "
                        "so target-specific follow-up cannot be defended"
                    ),
                )
            )
            continue

        detectability = build_peptide_detectability_report(
            peptide_sequence,
            modification_assignments=modification_assignments,
            observed_psm_count=evidence.psm_count,
            protease=protease,
            uniqueness_class=uniqueness_entry.uniqueness_class,
        )
        liability = build_peptide_chemical_liability_report(
            peptide_sequence,
            modification_assignments=modification_assignments,
            observed_psm_count=evidence.psm_count,
            protease=protease,
        )

        rejection_codes: list[TargetedPeptideSelectionRejectionCode] = []
        if (
            evidence.primary_class not in _SUPPORTED_OBSERVED_CLASSES
            or not evidence.accepted
        ):
            rejection_codes.append(
                TargetedPeptideSelectionRejectionCode.DISCOVERY_EVIDENCE_REJECTED
            )
        if uniqueness_entry.uniqueness_class not in _UNIQUE_SELECTION_CLASSES:
            rejection_codes.append(TargetedPeptideSelectionRejectionCode.NON_UNIQUE)
        if detectability.detectability_score < _MIN_DETECTABILITY_SCORE:
            rejection_codes.append(
                TargetedPeptideSelectionRejectionCode.LOW_DETECTABILITY
            )
        if liability.suitability_score < _MIN_SUITABILITY_SCORE:
            rejection_codes.append(
                TargetedPeptideSelectionRejectionCode.CHEMICALLY_UNSUITABLE
            )

        if rejection_codes:
            rejected.append(
                DiscoveryTargetedPeptideRejectionEntry(
                    target_protein_ref=target.representative_protein_ref,
                    target_protein_group_id=target.protein_group_id,
                    gene_symbol=target.gene_symbol,
                    peptide_sequence=peptide_sequence,
                    canonical_peptide=evidence.canonical_peptide,
                    candidate_source=TargetedPeptideCandidateSource.OBSERVED_DISCOVERY,
                    observed_in_discovery=True,
                    observed_psm_count=evidence.psm_count,
                    primary_evidence_class=evidence.primary_class,
                    uniqueness_class=uniqueness_entry.uniqueness_class,
                    detectability_score=detectability.detectability_score,
                    suitability_score=liability.suitability_score,
                    rejection_codes=tuple(rejection_codes),
                    explanation=_rejection_explanation(rejection_codes),
                )
            )
            continue

        selected.append(
            DiscoveryTargetedPeptideSelectionEntry(
                target_protein_ref=target.representative_protein_ref,
                target_protein_group_id=target.protein_group_id,
                gene_symbol=target.gene_symbol,
                peptide_sequence=peptide_sequence,
                canonical_peptide=evidence.canonical_peptide,
                candidate_source=TargetedPeptideCandidateSource.OBSERVED_DISCOVERY,
                rank=1,
                observed_in_discovery=True,
                observed_psm_count=evidence.psm_count,
                run_count=evidence.run_count,
                detection_frequency=evidence.detection_frequency,
                replicate_consistency=evidence.replicate_consistency,
                primary_evidence_class=evidence.primary_class,
                uniqueness_class=uniqueness_entry.uniqueness_class,
                uniqueness_score=detectability.uniqueness_score,
                detectability_score=detectability.detectability_score,
                detectability_tier=detectability.detectability_tier,
                suitability_score=liability.suitability_score,
                liability_tier=liability.liability_tier,
                liability_codes=tuple(code.value for code in liability.liability_codes),
                selection_score=_selection_score(
                    uniqueness_score=detectability.uniqueness_score,
                    detectability_score=detectability.detectability_score,
                    suitability_score=liability.suitability_score,
                    evidence_score=_observed_evidence_score(evidence),
                    discovery_bonus=1.0,
                ),
                selection_reasons=(
                    "observed_in_discovery",
                    "unique_to_target_database",
                    "detectable_by_sequence_properties",
                    "chemically_suitable_for_targeted_follow_up",
                ),
            )
        )

    return tuple(selected), tuple(rejected)


def _score_theoretical_candidates(
    *,
    target: DiscoveryTargetProteinEntry,
    protein_record: NormalizedProteinRecord,
    uniqueness_by_sequence: dict[str, PeptideUniquenessIndexEntry],
    protease: ProteaseRule,
    missed_cleavages: int,
    excluded_sequences: set[str],
) -> tuple[
    tuple[DiscoveryTargetedPeptideSelectionEntry, ...],
    tuple[DiscoveryTargetedPeptideRejectionEntry, ...],
]:
    selected: list[DiscoveryTargetedPeptideSelectionEntry] = []
    rejected: list[DiscoveryTargetedPeptideRejectionEntry] = []
    digest_entries = digest_protein_records(
        (protein_record,),
        protease=protease,
        missed_cleavages=missed_cleavages,
        mode=PeptideDigestionMode.FULL,
    )
    seen_sequences: set[str] = set()
    for peptide in sorted(
        digest_entries, key=lambda entry: (entry.start, entry.sequence)
    ):
        if peptide.sequence in seen_sequences:
            continue
        seen_sequences.add(peptide.sequence)
        if peptide.sequence in excluded_sequences:
            continue
        uniqueness_entry = uniqueness_by_sequence.get(peptide.sequence)
        if uniqueness_entry is None:
            continue
        detectability = build_peptide_detectability_report(
            peptide.sequence,
            protease=protease,
            uniqueness_class=uniqueness_entry.uniqueness_class,
            observed_psm_count=0,
        )
        liability = build_peptide_chemical_liability_report(
            peptide.sequence,
            protease=protease,
            observed_psm_count=0,
        )
        rejection_codes: list[TargetedPeptideSelectionRejectionCode] = []
        if uniqueness_entry.uniqueness_class not in _UNIQUE_SELECTION_CLASSES:
            rejection_codes.append(TargetedPeptideSelectionRejectionCode.NON_UNIQUE)
        if detectability.detectability_score < _MIN_DETECTABILITY_SCORE:
            rejection_codes.append(
                TargetedPeptideSelectionRejectionCode.LOW_DETECTABILITY
            )
        if liability.suitability_score < _MIN_SUITABILITY_SCORE:
            rejection_codes.append(
                TargetedPeptideSelectionRejectionCode.CHEMICALLY_UNSUITABLE
            )
        if rejection_codes:
            rejected.append(
                DiscoveryTargetedPeptideRejectionEntry(
                    target_protein_ref=target.representative_protein_ref,
                    target_protein_group_id=target.protein_group_id,
                    gene_symbol=target.gene_symbol,
                    peptide_sequence=peptide.sequence,
                    canonical_peptide=peptide.sequence,
                    candidate_source=TargetedPeptideCandidateSource.THEORETICAL_DIGEST,
                    observed_in_discovery=False,
                    uniqueness_class=uniqueness_entry.uniqueness_class,
                    detectability_score=detectability.detectability_score,
                    suitability_score=liability.suitability_score,
                    rejection_codes=tuple(rejection_codes),
                    explanation=_rejection_explanation(rejection_codes),
                )
            )
            continue
        selected.append(
            DiscoveryTargetedPeptideSelectionEntry(
                target_protein_ref=target.representative_protein_ref,
                target_protein_group_id=target.protein_group_id,
                gene_symbol=target.gene_symbol,
                peptide_sequence=peptide.sequence,
                canonical_peptide=peptide.sequence,
                candidate_source=TargetedPeptideCandidateSource.THEORETICAL_DIGEST,
                rank=1,
                observed_in_discovery=False,
                uniqueness_class=uniqueness_entry.uniqueness_class,
                uniqueness_score=detectability.uniqueness_score,
                detectability_score=detectability.detectability_score,
                detectability_tier=detectability.detectability_tier,
                suitability_score=liability.suitability_score,
                liability_tier=liability.liability_tier,
                liability_codes=tuple(code.value for code in liability.liability_codes),
                selection_score=_selection_score(
                    uniqueness_score=detectability.uniqueness_score,
                    detectability_score=detectability.detectability_score,
                    suitability_score=liability.suitability_score,
                    evidence_score=0.0,
                    discovery_bonus=0.0,
                ),
                selection_reasons=(
                    "theoretical_digest_fallback",
                    "unique_to_target_database",
                    "detectable_by_sequence_properties",
                    "chemically_suitable_for_targeted_follow_up",
                ),
            )
        )

    return tuple(selected), tuple(rejected)


def _index_protein_records(
    protein_records: tuple[NormalizedProteinRecord, ...],
) -> dict[str, NormalizedProteinRecord]:
    indexed: dict[str, NormalizedProteinRecord] = {}
    for record in protein_records:
        indexed.setdefault(record.canonical_accession, record)
        indexed.setdefault(record.source_identifier, record)
    return indexed


def _normalize_evidence_peptide(
    canonical_peptide: str,
) -> tuple[str, tuple[str, ...]]:
    if "[" not in canonical_peptide and "-" not in canonical_peptide:
        return canonical_peptide, ()
    parsed = parse_modified_peptide_notation(
        canonical_peptide,
        dialect=ModifiedPeptideNotationDialect.BIJUX,
    )
    assignments = tuple(
        f"{mod.name}[{mod.residue}]"
        for mod in parsed.modifications
        if mod.residue is not None
    )
    return parsed.sequence, assignments


def _observed_evidence_score(entry: PeptideEvidenceEntry) -> float:
    class_score = {
        PeptideEvidenceClass.STRONG: 1.0,
        PeptideEvidenceClass.MODERATE: 0.8,
        PeptideEvidenceClass.WEAK: 0.6,
        PeptideEvidenceClass.SHARED: 0.25,
        PeptideEvidenceClass.AMBIGUOUS: 0.1,
        PeptideEvidenceClass.CONTAMINANT: 0.0,
        PeptideEvidenceClass.DECOY: 0.0,
    }[entry.primary_class]
    return min(
        1.0,
        (class_score * 0.4)
        + (entry.replicate_consistency * 0.3)
        + (entry.detection_frequency * 0.2)
        + (min(entry.psm_count / 5.0, 1.0) * 0.1),
    )


def _selection_score(
    *,
    uniqueness_score: float,
    detectability_score: float,
    suitability_score: float,
    evidence_score: float,
    discovery_bonus: float,
) -> float:
    return round(
        min(
            1.0,
            (uniqueness_score * 0.25)
            + (detectability_score * 0.25)
            + (suitability_score * 0.25)
            + (evidence_score * 0.2)
            + (discovery_bonus * 0.05),
        ),
        6,
    )


def _rejection_explanation(
    rejection_codes: list[TargetedPeptideSelectionRejectionCode],
) -> str:
    explanations = {
        TargetedPeptideSelectionRejectionCode.DISCOVERY_EVIDENCE_REJECTED: (
            "discovery evidence is not accepted strongly enough for targeted follow-up"
        ),
        TargetedPeptideSelectionRejectionCode.DISCOVERY_EVIDENCE_NOT_TARGET_SPECIFIC: (
            "discovery evidence cannot be connected back to a governed target-specific "
            "peptide mapping"
        ),
        TargetedPeptideSelectionRejectionCode.NON_UNIQUE: (
            "candidate peptide is not unique to the target protein within the governed FASTA"
        ),
        TargetedPeptideSelectionRejectionCode.LOW_DETECTABILITY: (
            "candidate peptide does not meet the detectability floor for targeted follow-up"
        ),
        TargetedPeptideSelectionRejectionCode.CHEMICALLY_UNSUITABLE: (
            "candidate peptide carries chemical liabilities that make it a poor targeted assay choice"
        ),
        TargetedPeptideSelectionRejectionCode.DUPLICATE_SEQUENCE: (
            "candidate sequence duplicates a stronger peptide already selected for the same target"
        ),
        TargetedPeptideSelectionRejectionCode.PROTEIN_SEQUENCE_MISSING: (
            "governed FASTA does not contain the target protein sequence"
        ),
    }
    return "; ".join(explanations[code] for code in rejection_codes)


__all__ = [
    "DiscoveryTargetProteinEntry",
    "DiscoveryTargetedPeptideRejectionEntry",
    "DiscoveryTargetedPeptideSelectionEntry",
    "DiscoveryTargetedPeptideSelectionReport",
    "DiscoveryTargetedPeptideSelectionSummary",
    "TargetedPeptideCandidateSource",
    "TargetedPeptideSelectionRejectionCode",
    "build_discovery_targeted_peptide_selection_report",
    "render_discovery_targeted_peptide_selection_rejected_tsv",
    "render_discovery_targeted_peptide_selection_selected_tsv",
    "render_discovery_targeted_peptide_selection_summary_tsv",
]
