# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Quantitative evidence helpers for protein-evidence card assembly."""

from __future__ import annotations

from collections import defaultdict

from bijux_proteomics.identification import PsmRecord, TargetDecoyLabel
from bijux_proteomics.identification.protein_coverage import (
    build_protein_coverage_report,
)
from bijux_proteomics.interpretation import ProteinAnnotationStatus
from bijux_proteomics.quantification.contracts import (
    DifferentialAbundanceEntry,
    LabelFreeQuantTable,
    MissingValueKind,
    QuantValue,
)
from bijux_proteomics.workflow.cards.protein_evidence.models import (
    ProteinEvidenceCardAnnotation,
    ProteinEvidenceCardCoverage,
    ProteinEvidenceCardDifferentialResult,
    ProteinEvidenceCardQuantification,
    ProteinEvidenceCardSampleValue,
    ProteinEvidenceCardSelectionPolicy,
    ProteinEvidenceCardWarning,
    ProteinEvidenceCardWarningCode,
)


def group_values_by_entity(
    values: tuple[QuantValue, ...],
) -> dict[str, tuple[QuantValue, ...]]:
    grouped: dict[str, list[QuantValue]] = defaultdict(list)
    for value in values:
        grouped[value.entity_id].append(value)
    return {
        entity_id: tuple(sorted(entries, key=lambda entry: entry.sample_id))
        for entity_id, entries in grouped.items()
    }


def build_quantification_payload(
    values: tuple[QuantValue, ...],
    *,
    sample_conditions: dict[str, str | None],
) -> ProteinEvidenceCardQuantification:
    sample_values = tuple(
        ProteinEvidenceCardSampleValue(
            sample_id=value.sample_id,
            condition=sample_conditions.get(value.sample_id),
            abundance=value.abundance,
            missing_value_kind=value.missing_value_kind,
            source_feature_count=value.source_feature_count,
        )
        for value in values
    )
    return ProteinEvidenceCardQuantification(
        sample_values=sample_values,
        observed_sample_count=sum(
            1
            for value in sample_values
            if value.missing_value_kind is MissingValueKind.OBSERVED
        ),
        zero_sample_count=sum(
            1
            for value in sample_values
            if value.missing_value_kind is MissingValueKind.ZERO
        ),
        missing_sample_count=sum(
            1
            for value in sample_values
            if value.missing_value_kind is MissingValueKind.NOT_OBSERVED
        ),
        filtered_sample_count=sum(
            1
            for value in sample_values
            if value.missing_value_kind is MissingValueKind.FILTERED
        ),
    )


def build_differential_payload(
    entry: DifferentialAbundanceEntry,
) -> ProteinEvidenceCardDifferentialResult:
    return ProteinEvidenceCardDifferentialResult(
        condition_a=entry.condition_a,
        condition_b=entry.condition_b,
        observations_a=entry.observations_a,
        observations_b=entry.observations_b,
        complete_pair_count=entry.complete_pair_count,
        mean_log2_abundance_a=entry.mean_log2_abundance_a,
        mean_log2_abundance_b=entry.mean_log2_abundance_b,
        log2_fold_change=entry.log2_fold_change,
        p_value=entry.p_value,
        adjusted_p_value=entry.adjusted_p_value,
        standard_error=entry.standard_error,
        confidence_interval_low=entry.confidence_interval_low,
        confidence_interval_high=entry.confidence_interval_high,
        effect_size_cohens_d=entry.effect_size_cohens_d,
        uncertainty_note=entry.uncertainty_note,
    )


def build_coverage_by_protein(
    quant_table: LabelFreeQuantTable,
    *,
    protein_sequences: dict[str, str],
) -> dict[str, ProteinEvidenceCardCoverage]:
    synthetic_records: list[PsmRecord] = []
    for entity_id, peptides in quant_table.entity_member_peptides.items():
        protein_refs = quant_table.entity_protein_refs.get(entity_id, ()) or (
            entity_id,
        )
        for peptide_index, peptide in enumerate(sorted(set(peptides)), start=1):
            synthetic_records.append(
                PsmRecord(
                    spectrum_id=f"{entity_id}:coverage:{peptide_index}",
                    peptide=peptide,
                    peptide_sequence=peptide,
                    canonical_peptide=peptide,
                    charge=2,
                    score=1.0,
                    q_value=0.0,
                    protein_refs=protein_refs,
                    target_decoy_label=target_decoy_label_for_refs(protein_refs),
                    contaminant_flag=all(
                        ref.upper().startswith("CON__") for ref in protein_refs
                    ),
                )
            )
    report = build_protein_coverage_report(
        tuple(synthetic_records),
        protein_sequences=protein_sequences,
    )
    return {
        entry.protein_ref: ProteinEvidenceCardCoverage(
            coverage_protein_ref=entry.protein_ref,
            residue_count=entry.residue_count,
            covered_residue_count=entry.covered_residue_count,
            coverage_fraction=entry.coverage_fraction,
            covered_peptides=entry.covered_peptides,
        )
        for entry in report.entries
    }


def target_decoy_label_for_refs(protein_refs: tuple[str, ...]) -> TargetDecoyLabel:
    normalized_refs = tuple(ref.upper() for ref in protein_refs)
    if normalized_refs and all(
        ref.startswith(("REV__", "DECOY__", "DECOY:")) for ref in normalized_refs
    ):
        return TargetDecoyLabel.DECOY
    return TargetDecoyLabel.TARGET


def entry_is_significant(
    entry: DifferentialAbundanceEntry,
    *,
    policy: ProteinEvidenceCardSelectionPolicy,
) -> bool:
    return (
        entry.adjusted_p_value is not None
        and entry.adjusted_p_value <= policy.max_adjusted_p_value
        and abs(entry.log2_fold_change) >= policy.min_absolute_log2_fold_change
    )


def build_warnings(
    *,
    annotation: ProteinEvidenceCardAnnotation,
    coverage: ProteinEvidenceCardCoverage,
    differential_entry: DifferentialAbundanceEntry,
    significant: bool,
    unique_peptide_count: int,
    peptide_count: int,
) -> tuple[ProteinEvidenceCardWarning, ...]:
    warnings: list[ProteinEvidenceCardWarning] = []
    if not significant:
        warnings.append(
            ProteinEvidenceCardWarning(
                code=ProteinEvidenceCardWarningCode.NOT_SIGNIFICANT,
                message="final protein result did not satisfy the configured biological selection policy",
            )
        )
    if annotation.annotation_status is ProteinAnnotationStatus.UNMAPPED:
        warnings.append(
            ProteinEvidenceCardWarning(
                code=ProteinEvidenceCardWarningCode.ANNOTATION_UNMAPPED,
                message="representative protein could not be annotated from the provided FASTA or custom annotation inputs",
            )
        )
    if peptide_count > 0 and unique_peptide_count == 0:
        warnings.append(
            ProteinEvidenceCardWarning(
                code=ProteinEvidenceCardWarningCode.SHARED_PEPTIDE_ONLY,
                message="protein result is supported only by peptides shared across multiple protein targets",
            )
        )
    elif unique_peptide_count < 2:
        warnings.append(
            ProteinEvidenceCardWarning(
                code=ProteinEvidenceCardWarningCode.LOW_UNIQUE_PEPTIDE_SUPPORT,
                message="protein result has fewer than two unique member peptides",
            )
        )
    if coverage.residue_count == 0 or coverage.coverage_fraction < 0.1:
        warnings.append(
            ProteinEvidenceCardWarning(
                code=ProteinEvidenceCardWarningCode.LOW_SEQUENCE_COVERAGE,
                message="sequence-backed protein coverage remained below 10 percent",
            )
        )
    if (
        differential_entry.not_observed_values_a > 0
        or differential_entry.not_observed_values_b > 0
        or differential_entry.filtered_values_a > 0
        or differential_entry.filtered_values_b > 0
    ):
        warnings.append(
            ProteinEvidenceCardWarning(
                code=ProteinEvidenceCardWarningCode.CONDITION_MISSINGNESS,
                message="differential comparison includes missing or filtered values in at least one condition",
            )
        )
    return tuple(warnings)


__all__ = [
    "build_coverage_by_protein",
    "build_differential_payload",
    "build_quantification_payload",
    "build_warnings",
    "entry_is_significant",
    "group_values_by_entity",
    "target_decoy_label_for_refs",
]
