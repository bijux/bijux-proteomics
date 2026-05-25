# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Owned comparison surfaces over DIA and DDA evidence packets."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from enum import StrEnum
from io import StringIO
from pathlib import Path

from pydantic import ConfigDict, Field

from bijux_proteomics.identification import (
    PsmRecord,
    SearchResultColumnMapping,
    TargetDecoyLabel,
    is_biological_foreground_class,
    parse_psm_tsv,
)
from bijux_proteomics.identification.diann_import import (
    DiaNnBundleImportReport,
    build_diann_import_report,
)
from bijux_proteomics.quantification.contracts import (
    DifferentialAbundanceReport,
    QuantEntityLevel,
)
from bijux_proteomics.quantification.peptide_intensity_matrix import (
    PeptideMatrixGroupingMode,
    build_peptide_intensity_matrix_from_psms,
)
from bijux_proteomics.quantification.protein_intensity_matrix import (
    ProteinIntensityMatrixReport,
    ProteinMatrixTargetKind,
    build_protein_intensity_matrix_from_peptides,
)
from bijux_proteomics_foundation import JsonModel


class WorkflowOverlapClass(StrEnum):
    """Stable overlap classes across DIA and DDA evidence."""

    SHARED = "shared"
    DIA_ONLY = "dia_only"
    DDA_ONLY = "dda_only"
    CONFLICTING = "conflicting"


class DiaDdaProteinOverlapEntry(JsonModel):
    """One accession-level overlap row across DIA and DDA workflows."""

    model_config = ConfigDict(extra="forbid")

    protein_ref: str = Field(..., min_length=1)
    overlap_class: WorkflowOverlapClass
    dia_sample_count: int = Field(..., ge=0)
    dda_sample_count: int = Field(..., ge=0)
    dia_total_intensity: float = Field(..., ge=0.0)
    dda_total_intensity: float = Field(..., ge=0.0)


class DiaDdaPeptideOverlapEntry(JsonModel):
    """One peptide-level overlap row across DIA and DDA workflows."""

    model_config = ConfigDict(extra="forbid")

    peptide_sequence: str = Field(..., min_length=1)
    overlap_class: WorkflowOverlapClass
    dia_sample_count: int = Field(..., ge=0)
    dda_sample_count: int = Field(..., ge=0)
    dia_total_intensity: float = Field(..., ge=0.0)
    dda_total_intensity: float = Field(..., ge=0.0)
    dia_protein_refs: tuple[str, ...] = Field(default_factory=tuple)
    dda_protein_refs: tuple[str, ...] = Field(default_factory=tuple)


class ComparisonEntityLevel(StrEnum):
    """Stable entity levels for cross-workflow review surfaces."""

    PROTEIN = "protein"
    PEPTIDE = "peptide"


class WorkflowSourceKind(StrEnum):
    """Stable workflow source kinds for exclusive-evidence reporting."""

    DIA = "dia"
    DDA = "dda"


class DiaDdaExclusiveEvidenceEntry(JsonModel):
    """One explicit workflow-exclusive protein or peptide evidence row."""

    model_config = ConfigDict(extra="forbid")

    source_kind: WorkflowSourceKind
    entity_level: ComparisonEntityLevel
    entity_id: str = Field(..., min_length=1)
    sample_count: int = Field(..., ge=0)
    total_intensity: float = Field(..., ge=0.0)
    protein_refs: tuple[str, ...] = Field(default_factory=tuple)


class DiaDdaSharedIntensityCorrelationEntry(JsonModel):
    """One shared-entity correlation row across DIA and DDA sample intensities."""

    model_config = ConfigDict(extra="forbid")

    entity_level: ComparisonEntityLevel
    entity_id: str = Field(..., min_length=1)
    shared_sample_count: int = Field(..., ge=0)
    dia_mean_intensity: float = Field(..., ge=0.0)
    dda_mean_intensity: float = Field(..., ge=0.0)
    pearson_correlation: float | None = Field(default=None, ge=-1.0, le=1.0)


class DiaDdaConflictingEvidenceEntry(JsonModel):
    """One explicit disagreement row that cannot be flattened into shared evidence."""

    model_config = ConfigDict(extra="forbid")

    entity_level: ComparisonEntityLevel
    entity_id: str = Field(..., min_length=1)
    overlap_class: WorkflowOverlapClass = WorkflowOverlapClass.CONFLICTING
    reason_code: str = Field(..., min_length=1)
    detail: str = Field(..., min_length=1)
    dia_sample_count: int = Field(..., ge=0)
    dda_sample_count: int = Field(..., ge=0)
    dia_total_intensity: float = Field(..., ge=0.0)
    dda_total_intensity: float = Field(..., ge=0.0)
    dia_protein_refs: tuple[str, ...] = Field(default_factory=tuple)
    dda_protein_refs: tuple[str, ...] = Field(default_factory=tuple)


class DiaDdaDifferentialComparisonEntry(JsonModel):
    """One cross-workflow differential-result comparison row."""

    model_config = ConfigDict(extra="forbid")

    entity_level: QuantEntityLevel
    entity_id: str = Field(..., min_length=1)
    condition_a: str = Field(..., min_length=1)
    condition_b: str = Field(..., min_length=1)
    contrast_name: str = Field(..., min_length=1)
    comparison_class: WorkflowOverlapClass
    dia_log2_fold_change: float | None = None
    dda_log2_fold_change: float | None = None
    dia_adjusted_p_value: float | None = Field(default=None, ge=0.0, le=1.0)
    dda_adjusted_p_value: float | None = Field(default=None, ge=0.0, le=1.0)
    dia_significant: bool
    dda_significant: bool
    direction_agreement: str | None = None
    reason_code: str | None = None


class DiaDdaComparisonSummary(JsonModel):
    """Compact summary over DIA-vs-DDA evidence overlap."""

    model_config = ConfigDict(extra="forbid")

    dia_protein_count: int = Field(..., ge=0)
    dda_protein_count: int = Field(..., ge=0)
    shared_protein_count: int = Field(..., ge=0)
    dia_only_protein_count: int = Field(..., ge=0)
    dda_only_protein_count: int = Field(..., ge=0)
    dia_peptide_count: int = Field(..., ge=0)
    dda_peptide_count: int = Field(..., ge=0)
    shared_peptide_count: int = Field(..., ge=0)
    dia_only_peptide_count: int = Field(..., ge=0)
    dda_only_peptide_count: int = Field(..., ge=0)
    conflicting_peptide_count: int = Field(default=0, ge=0)
    exclusive_evidence_entry_count: int = Field(..., ge=0)
    conflicting_evidence_entry_count: int = Field(default=0, ge=0)
    shared_intensity_correlation_entry_count: int = Field(..., ge=0)
    protein_correlation_entry_count: int = Field(..., ge=0)
    peptide_correlation_entry_count: int = Field(..., ge=0)
    differential_comparison_entry_count: int = Field(default=0, ge=0)
    shared_differential_count: int = Field(default=0, ge=0)
    dia_only_differential_count: int = Field(default=0, ge=0)
    dda_only_differential_count: int = Field(default=0, ge=0)
    conflicting_differential_count: int = Field(default=0, ge=0)


class DiaDdaComparisonReport(JsonModel):
    """Owned cross-workflow comparison over DIA and DDA evidence."""

    model_config = ConfigDict(extra="forbid")

    dia_source_name: str = Field(default="DIA-NN", min_length=1)
    dda_source_name: str = Field(default="DDA PSM", min_length=1)
    protein_overlap: tuple[DiaDdaProteinOverlapEntry, ...] = Field(default_factory=tuple)
    peptide_overlap: tuple[DiaDdaPeptideOverlapEntry, ...] = Field(default_factory=tuple)
    exclusive_evidence: tuple[DiaDdaExclusiveEvidenceEntry, ...] = Field(default_factory=tuple)
    conflicting_evidence: tuple[DiaDdaConflictingEvidenceEntry, ...] = Field(
        default_factory=tuple
    )
    shared_intensity_correlation: tuple[DiaDdaSharedIntensityCorrelationEntry, ...] = Field(
        default_factory=tuple
    )
    differential_comparison: tuple[DiaDdaDifferentialComparisonEntry, ...] = Field(
        default_factory=tuple
    )
    summary: DiaDdaComparisonSummary
    note: str = Field(..., min_length=1)


def build_dia_dda_comparison_report(
    dia_report: DiaNnBundleImportReport,
    dda_records: tuple[PsmRecord, ...],
    *,
    max_q_value: float = 0.05,
    dia_differential_report: DifferentialAbundanceReport | None = None,
    dda_differential_report: DifferentialAbundanceReport | None = None,
    differential_significance_threshold: float = 0.05,
) -> DiaDdaComparisonReport:
    """Compare accession-level DIA and DDA evidence under one q-value threshold."""

    dia_proteins = _dia_protein_abundance(dia_report, max_q_value=max_q_value)
    dda_proteins = _dda_protein_abundance(dda_records, max_q_value=max_q_value)
    dia_peptides = _dia_peptide_abundance(dia_report, max_q_value=max_q_value)
    dda_peptides = _dda_peptide_abundance(dda_records, max_q_value=max_q_value)
    protein_ids = tuple(sorted(set(dia_proteins) | set(dda_proteins)))
    protein_overlap: list[DiaDdaProteinOverlapEntry] = []
    shared_count = 0
    dia_only_count = 0
    dda_only_count = 0
    for protein_ref in protein_ids:
        dia_values = dia_proteins.get(protein_ref, {})
        dda_values = dda_proteins.get(protein_ref, {})
        if dia_values and dda_values:
            overlap_class = WorkflowOverlapClass.SHARED
            shared_count += 1
        elif dia_values:
            overlap_class = WorkflowOverlapClass.DIA_ONLY
            dia_only_count += 1
        else:
            overlap_class = WorkflowOverlapClass.DDA_ONLY
            dda_only_count += 1
        protein_overlap.append(
            DiaDdaProteinOverlapEntry(
                protein_ref=protein_ref,
                overlap_class=overlap_class,
                dia_sample_count=len(dia_values),
                dda_sample_count=len(dda_values),
                dia_total_intensity=sum(dia_values.values()),
                dda_total_intensity=sum(dda_values.values()),
            )
        )
    peptide_ids = tuple(sorted(set(dia_peptides) | set(dda_peptides)))
    peptide_overlap: list[DiaDdaPeptideOverlapEntry] = []
    shared_peptide_count = 0
    dia_only_peptide_count = 0
    dda_only_peptide_count = 0
    conflicting_peptide_count = 0
    for peptide_sequence in peptide_ids:
        dia_entry = dia_peptides.get(peptide_sequence)
        dda_entry = dda_peptides.get(peptide_sequence)
        dia_values = {} if dia_entry is None else dia_entry["values"]
        dda_values = {} if dda_entry is None else dda_entry["values"]
        if dia_values and dda_values:
            dia_protein_refs = () if dia_entry is None else dia_entry["protein_refs"]
            dda_protein_refs = () if dda_entry is None else dda_entry["protein_refs"]
            if dia_protein_refs != dda_protein_refs:
                overlap_class = WorkflowOverlapClass.CONFLICTING
                conflicting_peptide_count += 1
            else:
                overlap_class = WorkflowOverlapClass.SHARED
                shared_peptide_count += 1
        elif dia_values:
            overlap_class = WorkflowOverlapClass.DIA_ONLY
            dia_only_peptide_count += 1
        else:
            overlap_class = WorkflowOverlapClass.DDA_ONLY
            dda_only_peptide_count += 1
        peptide_overlap.append(
            DiaDdaPeptideOverlapEntry(
                peptide_sequence=peptide_sequence,
                overlap_class=overlap_class,
                dia_sample_count=len(dia_values),
                dda_sample_count=len(dda_values),
                dia_total_intensity=sum(dia_values.values()),
                dda_total_intensity=sum(dda_values.values()),
                dia_protein_refs=() if dia_entry is None else dia_entry["protein_refs"],
                dda_protein_refs=() if dda_entry is None else dda_entry["protein_refs"],
            )
        )
    exclusive_evidence = tuple(
        sorted(
            (
                *[
                    DiaDdaExclusiveEvidenceEntry(
                        source_kind=WorkflowSourceKind.DIA,
                        entity_level=ComparisonEntityLevel.PROTEIN,
                        entity_id=entry.protein_ref,
                        sample_count=entry.dia_sample_count,
                        total_intensity=entry.dia_total_intensity,
                        protein_refs=(entry.protein_ref,),
                    )
                    for entry in protein_overlap
                    if entry.overlap_class is WorkflowOverlapClass.DIA_ONLY
                ],
                *[
                    DiaDdaExclusiveEvidenceEntry(
                        source_kind=WorkflowSourceKind.DDA,
                        entity_level=ComparisonEntityLevel.PROTEIN,
                        entity_id=entry.protein_ref,
                        sample_count=entry.dda_sample_count,
                        total_intensity=entry.dda_total_intensity,
                        protein_refs=(entry.protein_ref,),
                    )
                    for entry in protein_overlap
                    if entry.overlap_class is WorkflowOverlapClass.DDA_ONLY
                ],
                *[
                    DiaDdaExclusiveEvidenceEntry(
                        source_kind=WorkflowSourceKind.DIA,
                        entity_level=ComparisonEntityLevel.PEPTIDE,
                        entity_id=entry.peptide_sequence,
                        sample_count=entry.dia_sample_count,
                        total_intensity=entry.dia_total_intensity,
                        protein_refs=entry.dia_protein_refs,
                    )
                    for entry in peptide_overlap
                    if entry.overlap_class is WorkflowOverlapClass.DIA_ONLY
                ],
                *[
                    DiaDdaExclusiveEvidenceEntry(
                        source_kind=WorkflowSourceKind.DDA,
                        entity_level=ComparisonEntityLevel.PEPTIDE,
                        entity_id=entry.peptide_sequence,
                        sample_count=entry.dda_sample_count,
                        total_intensity=entry.dda_total_intensity,
                        protein_refs=entry.dda_protein_refs,
                    )
                    for entry in peptide_overlap
                    if entry.overlap_class is WorkflowOverlapClass.DDA_ONLY
                ],
            ),
            key=lambda entry: (
                entry.entity_level.value,
                entry.source_kind.value,
                entry.entity_id,
            ),
        )
    )
    conflicting_evidence = tuple(
        DiaDdaConflictingEvidenceEntry(
            entity_level=ComparisonEntityLevel.PEPTIDE,
            entity_id=entry.peptide_sequence,
            reason_code="protein_assignment_mismatch",
            detail=(
                f"peptide {entry.peptide_sequence} maps to "
                f"{';'.join(entry.dia_protein_refs) or 'no proteins'} in DIA and "
                f"{';'.join(entry.dda_protein_refs) or 'no proteins'} in DDA"
            ),
            dia_sample_count=entry.dia_sample_count,
            dda_sample_count=entry.dda_sample_count,
            dia_total_intensity=entry.dia_total_intensity,
            dda_total_intensity=entry.dda_total_intensity,
            dia_protein_refs=entry.dia_protein_refs,
            dda_protein_refs=entry.dda_protein_refs,
        )
        for entry in peptide_overlap
        if entry.overlap_class is WorkflowOverlapClass.CONFLICTING
    )
    shared_intensity_correlation = tuple(
        sorted(
            (
                *[
                    _build_correlation_entry(
                        entity_level=ComparisonEntityLevel.PROTEIN,
                        entity_id=protein_ref,
                        dia_values=dia_proteins[protein_ref],
                        dda_values=dda_proteins[protein_ref],
                    )
                    for protein_ref in sorted(set(dia_proteins) & set(dda_proteins))
                ],
                *[
                    _build_correlation_entry(
                        entity_level=ComparisonEntityLevel.PEPTIDE,
                        entity_id=peptide_sequence,
                        dia_values=dia_peptides[peptide_sequence]["values"],
                        dda_values=dda_peptides[peptide_sequence]["values"],
                    )
                    for peptide_sequence in sorted(set(dia_peptides) & set(dda_peptides))
                ],
            ),
            key=lambda entry: (entry.entity_level.value, entry.entity_id),
        )
    )
    differential_comparison = _build_differential_comparison(
        dia_differential_report=dia_differential_report,
        dda_differential_report=dda_differential_report,
        significance_threshold=differential_significance_threshold,
    )
    return DiaDdaComparisonReport(
        protein_overlap=tuple(protein_overlap),
        peptide_overlap=tuple(peptide_overlap),
        exclusive_evidence=exclusive_evidence,
        conflicting_evidence=conflicting_evidence,
        shared_intensity_correlation=shared_intensity_correlation,
        differential_comparison=differential_comparison,
        summary=DiaDdaComparisonSummary(
            dia_protein_count=len(dia_proteins),
            dda_protein_count=len(dda_proteins),
            shared_protein_count=shared_count,
            dia_only_protein_count=dia_only_count,
            dda_only_protein_count=dda_only_count,
            dia_peptide_count=len(dia_peptides),
            dda_peptide_count=len(dda_peptides),
            shared_peptide_count=shared_peptide_count,
            dia_only_peptide_count=dia_only_peptide_count,
            dda_only_peptide_count=dda_only_peptide_count,
            conflicting_peptide_count=conflicting_peptide_count,
            exclusive_evidence_entry_count=len(exclusive_evidence),
            conflicting_evidence_entry_count=len(conflicting_evidence),
            shared_intensity_correlation_entry_count=len(shared_intensity_correlation),
            protein_correlation_entry_count=sum(
                entry.entity_level is ComparisonEntityLevel.PROTEIN
                for entry in shared_intensity_correlation
            ),
            peptide_correlation_entry_count=sum(
                entry.entity_level is ComparisonEntityLevel.PEPTIDE
                for entry in shared_intensity_correlation
            ),
            differential_comparison_entry_count=len(differential_comparison),
            shared_differential_count=sum(
                entry.comparison_class is WorkflowOverlapClass.SHARED
                for entry in differential_comparison
            ),
            dia_only_differential_count=sum(
                entry.comparison_class is WorkflowOverlapClass.DIA_ONLY
                for entry in differential_comparison
            ),
            dda_only_differential_count=sum(
                entry.comparison_class is WorkflowOverlapClass.DDA_ONLY
                for entry in differential_comparison
            ),
            conflicting_differential_count=sum(
                entry.comparison_class is WorkflowOverlapClass.CONFLICTING
                for entry in differential_comparison
            ),
        ),
        note=(
            "dia-vs-dda comparison keeps shared, exclusive, conflicting, intensity-correlation, and differential-result disagreement surfaces visible before workflow complementarity claims are made"
        ),
    )


def build_diann_vs_dda_psm_comparison_report(
    diann_report_path: Path,
    dda_psm_path: Path,
    *,
    max_q_value: float = 0.05,
    dia_differential_tsv_path: Path | None = None,
    dda_differential_tsv_path: Path | None = None,
    differential_significance_threshold: float = 0.05,
) -> DiaDdaComparisonReport:
    """Build DIA-vs-DDA comparison directly from one DIA-NN report and one DDA PSM TSV."""

    dia_report = build_diann_import_report(diann_report_path)
    dda_parse_report = parse_psm_tsv(dda_psm_path, mapping=_comparison_psm_mapping())
    comparison_report = build_dia_dda_comparison_report(
        dia_report,
        dda_parse_report.accepted_records,
        max_q_value=max_q_value,
    )
    dia_differential = _load_differential_snapshots_from_tsv(dia_differential_tsv_path)
    dda_differential = _load_differential_snapshots_from_tsv(dda_differential_tsv_path)
    if not dia_differential and not dda_differential:
        return comparison_report
    if not dia_differential or not dda_differential:
        raise ValueError(
            "dia-vs-dda differential comparison requires both DIA and DDA differential TSV inputs"
        )
    return _with_differential_comparison(
        comparison_report,
        differential_comparison=_build_differential_comparison_from_snapshots(
            dia_snapshots=dia_differential,
            dda_snapshots=dda_differential,
            significance_threshold=differential_significance_threshold,
        ),
    )


def _comparison_psm_mapping() -> SearchResultColumnMapping:
    return SearchResultColumnMapping(
        run_id="run_id",
        spectrum_id="spectrum_id",
        peptide="peptide",
        modified_peptide="modified_peptide",
        charge="charge",
        score="score",
        intensity="intensity",
        q_value="q_value",
        protein_refs="proteins",
    )


def _dia_protein_abundance(
    report: DiaNnBundleImportReport,
    *,
    max_q_value: float,
) -> dict[str, dict[str, float]]:
    abundance_by_protein: dict[str, dict[str, float]] = {}
    for row in report.protein_group_rows:
        if row.target_decoy_label is not TargetDecoyLabel.TARGET or row.q_value > max_q_value:
            continue
        quantity = row.protein_group_quantity
        if quantity is None:
            continue
        for protein_ref in row.protein_refs:
            abundance_by_protein.setdefault(protein_ref, {})
            abundance_by_protein[protein_ref][row.sample_name] = (
                abundance_by_protein[protein_ref].get(row.sample_name, 0.0) + quantity
            )
    return abundance_by_protein


def _dda_protein_abundance(
    records: tuple[PsmRecord, ...],
    *,
    max_q_value: float,
) -> dict[str, dict[str, float]]:
    filtered_records = tuple(
        record
        for record in records
        if record.run_id is not None
        and record.intensity is not None
        and is_biological_foreground_class(record.target_decoy_contaminant_class)
        and record.q_value is not None
        and record.q_value <= max_q_value
    )
    peptide_matrix = build_peptide_intensity_matrix_from_psms(
        filtered_records,
        grouping_mode=PeptideMatrixGroupingMode.PEPTIDE_SEQUENCE,
    )
    protein_matrix = build_protein_intensity_matrix_from_peptides(
        peptide_matrix,
        target_kind=ProteinMatrixTargetKind.PROTEIN,
    )
    return _protein_matrix_abundance(protein_matrix)


def _dia_peptide_abundance(
    report: DiaNnBundleImportReport,
    *,
    max_q_value: float,
) -> dict[str, dict[str, object]]:
    abundance_by_peptide: dict[str, dict[str, object]] = {}
    for row in report.precursor_rows:
        if row.target_decoy_label is not TargetDecoyLabel.TARGET or row.q_value > max_q_value:
            continue
        quantity = row.precursor_quantity
        if quantity is None:
            continue
        peptide_bucket = abundance_by_peptide.setdefault(
            row.peptide_sequence,
            {"values": {}, "protein_refs": set()},
        )
        values = peptide_bucket["values"]
        assert isinstance(values, dict)
        values[row.sample_name] = values.get(row.sample_name, 0.0) + quantity
        protein_refs = peptide_bucket["protein_refs"]
        assert isinstance(protein_refs, set)
        protein_refs.update(row.protein_refs)
    return {
        peptide_sequence: {
            "values": bucket["values"],
            "protein_refs": tuple(sorted(bucket["protein_refs"])),
        }
        for peptide_sequence, bucket in abundance_by_peptide.items()
    }


def _dda_peptide_abundance(
    records: tuple[PsmRecord, ...],
    *,
    max_q_value: float,
) -> dict[str, dict[str, object]]:
    filtered_records = tuple(
        record
        for record in records
        if record.run_id is not None
        and record.intensity is not None
        and is_biological_foreground_class(record.target_decoy_contaminant_class)
        and record.q_value is not None
        and record.q_value <= max_q_value
    )
    peptide_matrix = build_peptide_intensity_matrix_from_psms(
        filtered_records,
        grouping_mode=PeptideMatrixGroupingMode.PEPTIDE_SEQUENCE,
    )
    abundance_by_peptide: dict[str, dict[str, object]] = {}
    for row in peptide_matrix.rows:
        sample_values: dict[str, float] = {}
        for value in row.values:
            if value.abundance is not None:
                sample_values[value.sample_id] = value.abundance
        if sample_values:
            abundance_by_peptide[row.entity_id] = {
                "values": sample_values,
                "protein_refs": row.protein_refs,
            }
    return abundance_by_peptide


def _protein_matrix_abundance(
    report: ProteinIntensityMatrixReport,
) -> dict[str, dict[str, float]]:
    abundance_by_protein: dict[str, dict[str, float]] = {}
    for row in report.rows:
        sample_values: dict[str, float] = {}
        for value in row.values:
            if value.abundance is not None:
                sample_values[value.sample_id] = value.abundance
        if sample_values:
            abundance_by_protein[row.entity_id] = sample_values
    return abundance_by_protein


def _build_correlation_entry(
    *,
    entity_level: ComparisonEntityLevel,
    entity_id: str,
    dia_values: dict[str, float],
    dda_values: dict[str, float],
) -> DiaDdaSharedIntensityCorrelationEntry:
    shared_sample_ids = tuple(sorted(set(dia_values) & set(dda_values)))
    dia_series = [dia_values[sample_id] for sample_id in shared_sample_ids]
    dda_series = [dda_values[sample_id] for sample_id in shared_sample_ids]
    return DiaDdaSharedIntensityCorrelationEntry(
        entity_level=entity_level,
        entity_id=entity_id,
        shared_sample_count=len(shared_sample_ids),
        dia_mean_intensity=(sum(dia_series) / len(dia_series) if dia_series else 0.0),
        dda_mean_intensity=(sum(dda_series) / len(dda_series) if dda_series else 0.0),
        pearson_correlation=_pearson_correlation(dia_series, dda_series),
    )


def _pearson_correlation(
    left: list[float],
    right: list[float],
) -> float | None:
    if len(left) != len(right) or len(left) < 2:
        return None
    left_mean = sum(left) / len(left)
    right_mean = sum(right) / len(right)
    left_centered = [value - left_mean for value in left]
    right_centered = [value - right_mean for value in right]
    numerator = sum(
        left_value * right_value
        for left_value, right_value in zip(left_centered, right_centered, strict=True)
    )
    left_scale = sum(value * value for value in left_centered) ** 0.5
    right_scale = sum(value * value for value in right_centered) ** 0.5
    if left_scale == 0.0 or right_scale == 0.0:
        return None
    raw_correlation = numerator / (left_scale * right_scale)
    return max(-1.0, min(1.0, raw_correlation))


@dataclass(frozen=True)
class _DifferentialSnapshot:
    entity_level: QuantEntityLevel
    entity_id: str
    condition_a: str
    condition_b: str
    contrast_name: str
    log2_fold_change: float
    adjusted_p_value: float | None
    p_value: float


def _build_differential_comparison(
    *,
    dia_differential_report: DifferentialAbundanceReport | None,
    dda_differential_report: DifferentialAbundanceReport | None,
    significance_threshold: float,
) -> tuple[DiaDdaDifferentialComparisonEntry, ...]:
    if dia_differential_report is None and dda_differential_report is None:
        return ()
    if dia_differential_report is None or dda_differential_report is None:
        raise ValueError(
            "dia-vs-dda differential comparison requires both DIA and DDA differential reports"
        )
    return _build_differential_comparison_from_snapshots(
        dia_snapshots=_differential_snapshots_from_report(dia_differential_report),
        dda_snapshots=_differential_snapshots_from_report(dda_differential_report),
        significance_threshold=significance_threshold,
    )


def _build_differential_comparison_from_snapshots(
    *,
    dia_snapshots: tuple[_DifferentialSnapshot, ...],
    dda_snapshots: tuple[_DifferentialSnapshot, ...],
    significance_threshold: float,
) -> tuple[DiaDdaDifferentialComparisonEntry, ...]:
    if not dia_snapshots and not dda_snapshots:
        return ()
    entity_levels = {entry.entity_level for entry in dia_snapshots} | {
        entry.entity_level for entry in dda_snapshots
    }
    if len(entity_levels) != 1:
        raise ValueError(
            "dia-vs-dda differential comparison requires one shared entity level"
        )
    dia_by_key = { _differential_key(entry): entry for entry in dia_snapshots }
    dda_by_key = { _differential_key(entry): entry for entry in dda_snapshots }
    rows: list[DiaDdaDifferentialComparisonEntry] = []
    for key in sorted(set(dia_by_key) | set(dda_by_key)):
        dia_entry = dia_by_key.get(key)
        dda_entry = dda_by_key.get(key)
        entity_level, entity_id, condition_a, condition_b, contrast_name = key
        dia_significant = _is_significant_differential_snapshot(
            dia_entry,
            significance_threshold=significance_threshold,
        )
        dda_significant = _is_significant_differential_snapshot(
            dda_entry,
            significance_threshold=significance_threshold,
        )
        reason_code: str | None = None
        direction_agreement: str | None = None
        if dia_entry is None:
            comparison_class = WorkflowOverlapClass.DDA_ONLY
            reason_code = "missing_dia_result"
        elif dda_entry is None:
            comparison_class = WorkflowOverlapClass.DIA_ONLY
            reason_code = "missing_dda_result"
        else:
            direction_agreement = _direction_agreement(dia_entry, dda_entry)
            if dia_significant and dda_significant and direction_agreement == "opposite":
                comparison_class = WorkflowOverlapClass.CONFLICTING
                reason_code = "differential_direction_mismatch"
            elif dia_significant and not dda_significant:
                comparison_class = WorkflowOverlapClass.DIA_ONLY
                reason_code = "significant_only_in_dia"
            elif dda_significant and not dia_significant:
                comparison_class = WorkflowOverlapClass.DDA_ONLY
                reason_code = "significant_only_in_dda"
            else:
                comparison_class = WorkflowOverlapClass.SHARED
                if direction_agreement == "opposite":
                    reason_code = "non_significant_direction_difference"
        rows.append(
            DiaDdaDifferentialComparisonEntry(
                entity_level=entity_level,
                entity_id=entity_id,
                condition_a=condition_a,
                condition_b=condition_b,
                contrast_name=contrast_name,
                comparison_class=comparison_class,
                dia_log2_fold_change=(
                    None if dia_entry is None else dia_entry.log2_fold_change
                ),
                dda_log2_fold_change=(
                    None if dda_entry is None else dda_entry.log2_fold_change
                ),
                dia_adjusted_p_value=(
                    None if dia_entry is None else _display_p_value(dia_entry)
                ),
                dda_adjusted_p_value=(
                    None if dda_entry is None else _display_p_value(dda_entry)
                ),
                dia_significant=dia_significant,
                dda_significant=dda_significant,
                direction_agreement=direction_agreement,
                reason_code=reason_code,
            )
        )
    return tuple(rows)


def _differential_key(
    entry: _DifferentialSnapshot,
) -> tuple[QuantEntityLevel, str, str, str, str]:
    return (
        entry.entity_level,
        entry.entity_id,
        entry.condition_a,
        entry.condition_b,
        entry.contrast_name,
    )


def _differential_snapshots_from_report(
    report: DifferentialAbundanceReport,
) -> tuple[_DifferentialSnapshot, ...]:
    contrast_name = _comparison_contrast_name(
        report.condition_a,
        report.condition_b,
        report.contrast_name,
    )
    return tuple(
        _DifferentialSnapshot(
            entity_level=report.entity_level,
            entity_id=entry.entity_id,
            condition_a=entry.condition_a,
            condition_b=entry.condition_b,
            contrast_name=contrast_name,
            log2_fold_change=entry.log2_fold_change,
            adjusted_p_value=entry.adjusted_p_value,
            p_value=entry.p_value,
        )
        for entry in report.entries
    )


def _load_differential_snapshots_from_tsv(
    path: Path | None,
) -> tuple[_DifferentialSnapshot, ...]:
    if path is None:
        return ()
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        if reader.fieldnames is None:
            raise ValueError(f"differential TSV {path} is missing a header row")
        required_columns = {
            "entity_id",
            "condition_a",
            "condition_b",
            "contrast_name",
            "log2_fold_change",
            "p_value",
            "adjusted_p_value",
        }
        missing_columns = sorted(required_columns - set(reader.fieldnames))
        if missing_columns:
            raise ValueError(
                f"differential TSV {path} is missing required columns: "
                + ", ".join(missing_columns)
            )
        rows: list[_DifferentialSnapshot] = []
        for row in reader:
            if row["entity_id"].strip() == "":
                continue
            rows.append(
                _DifferentialSnapshot(
                    entity_level=QuantEntityLevel.PROTEIN,
                    entity_id=row["entity_id"].strip(),
                    condition_a=row["condition_a"].strip(),
                    condition_b=row["condition_b"].strip(),
                    contrast_name=_comparison_contrast_name(
                        row["condition_a"].strip(),
                        row["condition_b"].strip(),
                        row["contrast_name"].strip(),
                    ),
                    log2_fold_change=float(row["log2_fold_change"]),
                    adjusted_p_value=_parse_optional_float(row["adjusted_p_value"]),
                    p_value=float(row["p_value"]),
                )
            )
    return tuple(rows)


def _parse_optional_float(value: str) -> float | None:
    stripped = value.strip()
    return None if stripped == "" else float(stripped)


def _comparison_contrast_name(
    condition_a: str,
    condition_b: str,
    contrast_name: str | None,
) -> str:
    candidate = "" if contrast_name is None else contrast_name.strip()
    return candidate or f"{condition_a}_vs_{condition_b}"


def _display_p_value(entry: _DifferentialSnapshot) -> float:
    return entry.p_value if entry.adjusted_p_value is None else entry.adjusted_p_value


def _is_significant_differential_snapshot(
    entry: _DifferentialSnapshot | None,
    *,
    significance_threshold: float,
) -> bool:
    if entry is None:
        return False
    return _display_p_value(entry) <= significance_threshold


def _direction_agreement(
    dia_entry: _DifferentialSnapshot,
    dda_entry: _DifferentialSnapshot,
) -> str:
    dia_direction = _effect_direction(dia_entry.log2_fold_change)
    dda_direction = _effect_direction(dda_entry.log2_fold_change)
    if dia_direction == dda_direction:
        return "same"
    return "opposite"


def _effect_direction(log2_fold_change: float) -> str:
    if log2_fold_change >= 0.0:
        return "up_or_flat"
    return "down"


def _with_differential_comparison(
    report: DiaDdaComparisonReport,
    *,
    differential_comparison: tuple[DiaDdaDifferentialComparisonEntry, ...],
) -> DiaDdaComparisonReport:
    return report.model_copy(
        update={
            "differential_comparison": differential_comparison,
            "summary": report.summary.model_copy(
                update={
                    "differential_comparison_entry_count": len(differential_comparison),
                    "shared_differential_count": sum(
                        entry.comparison_class is WorkflowOverlapClass.SHARED
                        for entry in differential_comparison
                    ),
                    "dia_only_differential_count": sum(
                        entry.comparison_class is WorkflowOverlapClass.DIA_ONLY
                        for entry in differential_comparison
                    ),
                    "dda_only_differential_count": sum(
                        entry.comparison_class is WorkflowOverlapClass.DDA_ONLY
                        for entry in differential_comparison
                    ),
                    "conflicting_differential_count": sum(
                        entry.comparison_class is WorkflowOverlapClass.CONFLICTING
                        for entry in differential_comparison
                    ),
                }
            ),
        }
    )


def render_dia_dda_comparison_summary_tsv(report: DiaDdaComparisonReport) -> str:
    """Render the compact DIA-vs-DDA comparison summary as TSV."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        [
            "dia_source_name",
            "dda_source_name",
            "dia_protein_count",
            "dda_protein_count",
            "shared_protein_count",
            "dia_only_protein_count",
            "dda_only_protein_count",
            "dia_peptide_count",
            "dda_peptide_count",
            "shared_peptide_count",
            "dia_only_peptide_count",
            "dda_only_peptide_count",
            "conflicting_peptide_count",
            "exclusive_evidence_entry_count",
            "conflicting_evidence_entry_count",
            "shared_intensity_correlation_entry_count",
            "protein_correlation_entry_count",
            "peptide_correlation_entry_count",
            "differential_comparison_entry_count",
            "shared_differential_count",
            "dia_only_differential_count",
            "dda_only_differential_count",
            "conflicting_differential_count",
            "note",
        ]
    )
    writer.writerow(
        [
            report.dia_source_name,
            report.dda_source_name,
            report.summary.dia_protein_count,
            report.summary.dda_protein_count,
            report.summary.shared_protein_count,
            report.summary.dia_only_protein_count,
            report.summary.dda_only_protein_count,
            report.summary.dia_peptide_count,
            report.summary.dda_peptide_count,
            report.summary.shared_peptide_count,
            report.summary.dia_only_peptide_count,
            report.summary.dda_only_peptide_count,
            report.summary.conflicting_peptide_count,
            report.summary.exclusive_evidence_entry_count,
            report.summary.conflicting_evidence_entry_count,
            report.summary.shared_intensity_correlation_entry_count,
            report.summary.protein_correlation_entry_count,
            report.summary.peptide_correlation_entry_count,
            report.summary.differential_comparison_entry_count,
            report.summary.shared_differential_count,
            report.summary.dia_only_differential_count,
            report.summary.dda_only_differential_count,
            report.summary.conflicting_differential_count,
            report.note,
        ]
    )
    return buffer.getvalue()


def render_dia_dda_protein_overlap_tsv(report: DiaDdaComparisonReport) -> str:
    """Render protein-level overlap across DIA and DDA workflows as TSV."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        [
            "protein_ref",
            "overlap_class",
            "dia_sample_count",
            "dda_sample_count",
            "dia_total_intensity",
            "dda_total_intensity",
        ]
    )
    for entry in report.protein_overlap:
        writer.writerow(
            [
                entry.protein_ref,
                entry.overlap_class.value,
                entry.dia_sample_count,
                entry.dda_sample_count,
                f"{entry.dia_total_intensity:g}",
                f"{entry.dda_total_intensity:g}",
            ]
        )
    return buffer.getvalue()


def render_dia_dda_peptide_overlap_tsv(report: DiaDdaComparisonReport) -> str:
    """Render peptide-level overlap across DIA and DDA workflows as TSV."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        [
            "peptide_sequence",
            "overlap_class",
            "dia_sample_count",
            "dda_sample_count",
            "dia_total_intensity",
            "dda_total_intensity",
            "dia_protein_refs",
            "dda_protein_refs",
        ]
    )
    for entry in report.peptide_overlap:
        writer.writerow(
            [
                entry.peptide_sequence,
                entry.overlap_class.value,
                entry.dia_sample_count,
                entry.dda_sample_count,
                f"{entry.dia_total_intensity:g}",
                f"{entry.dda_total_intensity:g}",
                ";".join(entry.dia_protein_refs),
                ";".join(entry.dda_protein_refs),
            ]
        )
    return buffer.getvalue()


def render_dia_dda_shared_intensity_correlation_tsv(
    report: DiaDdaComparisonReport,
) -> str:
    """Render shared-entity DIA-vs-DDA intensity correlation as TSV."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        [
            "entity_level",
            "entity_id",
            "shared_sample_count",
            "dia_mean_intensity",
            "dda_mean_intensity",
            "pearson_correlation",
        ]
    )
    for entry in report.shared_intensity_correlation:
        writer.writerow(
            [
                entry.entity_level.value,
                entry.entity_id,
                entry.shared_sample_count,
                f"{entry.dia_mean_intensity:g}",
                f"{entry.dda_mean_intensity:g}",
                (
                    ""
                    if entry.pearson_correlation is None
                    else f"{entry.pearson_correlation:g}"
                ),
            ]
        )
    return buffer.getvalue()


def render_dia_dda_exclusive_evidence_tsv(report: DiaDdaComparisonReport) -> str:
    """Render workflow-exclusive DIA and DDA evidence as TSV."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        [
            "source_kind",
            "entity_level",
            "entity_id",
            "sample_count",
            "total_intensity",
            "protein_refs",
        ]
    )
    for entry in report.exclusive_evidence:
        writer.writerow(
            [
                entry.source_kind.value,
                entry.entity_level.value,
                entry.entity_id,
                entry.sample_count,
                f"{entry.total_intensity:g}",
                ";".join(entry.protein_refs),
            ]
        )
    return buffer.getvalue()


def render_dia_dda_conflicting_evidence_tsv(report: DiaDdaComparisonReport) -> str:
    """Render workflow disagreements that cannot be collapsed into shared evidence."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        [
            "entity_level",
            "entity_id",
            "overlap_class",
            "reason_code",
            "detail",
            "dia_sample_count",
            "dda_sample_count",
            "dia_total_intensity",
            "dda_total_intensity",
            "dia_protein_refs",
            "dda_protein_refs",
        ]
    )
    for entry in report.conflicting_evidence:
        writer.writerow(
            [
                entry.entity_level.value,
                entry.entity_id,
                entry.overlap_class.value,
                entry.reason_code,
                entry.detail,
                entry.dia_sample_count,
                entry.dda_sample_count,
                f"{entry.dia_total_intensity:g}",
                f"{entry.dda_total_intensity:g}",
                ";".join(entry.dia_protein_refs),
                ";".join(entry.dda_protein_refs),
            ]
        )
    return buffer.getvalue()


def render_dia_dda_differential_comparison_tsv(report: DiaDdaComparisonReport) -> str:
    """Render one stable DIA-vs-DDA differential comparison table."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        [
            "entity_level",
            "entity_id",
            "condition_a",
            "condition_b",
            "contrast_name",
            "comparison_class",
            "dia_log2_fold_change",
            "dda_log2_fold_change",
            "dia_adjusted_p_value",
            "dda_adjusted_p_value",
            "dia_significant",
            "dda_significant",
            "direction_agreement",
            "reason_code",
        ]
    )
    for entry in report.differential_comparison:
        writer.writerow(
            [
                entry.entity_level.value,
                entry.entity_id,
                entry.condition_a,
                entry.condition_b,
                entry.contrast_name,
                entry.comparison_class.value,
                "" if entry.dia_log2_fold_change is None else f"{entry.dia_log2_fold_change:g}",
                "" if entry.dda_log2_fold_change is None else f"{entry.dda_log2_fold_change:g}",
                "" if entry.dia_adjusted_p_value is None else f"{entry.dia_adjusted_p_value:g}",
                "" if entry.dda_adjusted_p_value is None else f"{entry.dda_adjusted_p_value:g}",
                str(entry.dia_significant).lower(),
                str(entry.dda_significant).lower(),
                entry.direction_agreement or "",
                entry.reason_code or "",
            ]
        )
    return buffer.getvalue()
