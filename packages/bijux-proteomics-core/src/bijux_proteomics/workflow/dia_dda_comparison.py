# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Owned comparison surfaces over DIA and DDA evidence packets."""

from __future__ import annotations

from enum import StrEnum
from pathlib import Path

from pydantic import ConfigDict, Field

from bijux_proteomics.identification import (
    PsmRecord,
    SearchResultColumnMapping,
    TargetDecoyLabel,
    parse_psm_tsv,
)
from bijux_proteomics.identification.diann_import import (
    DiaNnBundleImportReport,
    build_diann_import_report,
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
    exclusive_evidence_entry_count: int = Field(..., ge=0)


class DiaDdaComparisonReport(JsonModel):
    """Owned cross-workflow comparison over DIA and DDA evidence."""

    model_config = ConfigDict(extra="forbid")

    dia_source_name: str = Field(default="DIA-NN", min_length=1)
    dda_source_name: str = Field(default="DDA PSM", min_length=1)
    protein_overlap: tuple[DiaDdaProteinOverlapEntry, ...] = Field(default_factory=tuple)
    peptide_overlap: tuple[DiaDdaPeptideOverlapEntry, ...] = Field(default_factory=tuple)
    exclusive_evidence: tuple[DiaDdaExclusiveEvidenceEntry, ...] = Field(default_factory=tuple)
    summary: DiaDdaComparisonSummary
    note: str = Field(..., min_length=1)


def build_dia_dda_comparison_report(
    dia_report: DiaNnBundleImportReport,
    dda_records: tuple[PsmRecord, ...],
    *,
    max_q_value: float = 0.05,
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
    for peptide_sequence in peptide_ids:
        dia_entry = dia_peptides.get(peptide_sequence)
        dda_entry = dda_peptides.get(peptide_sequence)
        dia_values = {} if dia_entry is None else dia_entry["values"]
        dda_values = {} if dda_entry is None else dda_entry["values"]
        if dia_values and dda_values:
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
    return DiaDdaComparisonReport(
        protein_overlap=tuple(protein_overlap),
        peptide_overlap=tuple(peptide_overlap),
        exclusive_evidence=exclusive_evidence,
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
            exclusive_evidence_entry_count=len(exclusive_evidence),
        ),
        note=(
            "dia-vs-dda comparison keeps protein overlap, peptide overlap, and explicit workflow-exclusive evidence visible before intensity complementarity claims are made"
        ),
    )


def build_diann_vs_dda_psm_comparison_report(
    diann_report_path: Path,
    dda_psm_path: Path,
    *,
    max_q_value: float = 0.05,
) -> DiaDdaComparisonReport:
    """Build DIA-vs-DDA comparison directly from one DIA-NN report and one DDA PSM TSV."""

    dia_report = build_diann_import_report(diann_report_path)
    dda_parse_report = parse_psm_tsv(dda_psm_path, mapping=_comparison_psm_mapping())
    return build_dia_dda_comparison_report(
        dia_report,
        dda_parse_report.accepted_records,
        max_q_value=max_q_value,
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
        and record.target_decoy_label is TargetDecoyLabel.TARGET
        and not record.contaminant_flag
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
        and record.target_decoy_label is TargetDecoyLabel.TARGET
        and not record.contaminant_flag
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
