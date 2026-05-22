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


class DiaDdaComparisonSummary(JsonModel):
    """Compact summary over DIA-vs-DDA evidence overlap."""

    model_config = ConfigDict(extra="forbid")

    dia_protein_count: int = Field(..., ge=0)
    dda_protein_count: int = Field(..., ge=0)
    shared_protein_count: int = Field(..., ge=0)
    dia_only_protein_count: int = Field(..., ge=0)
    dda_only_protein_count: int = Field(..., ge=0)


class DiaDdaComparisonReport(JsonModel):
    """Owned cross-workflow comparison over DIA and DDA evidence."""

    model_config = ConfigDict(extra="forbid")

    dia_source_name: str = Field(default="DIA-NN", min_length=1)
    dda_source_name: str = Field(default="DDA PSM", min_length=1)
    protein_overlap: tuple[DiaDdaProteinOverlapEntry, ...] = Field(default_factory=tuple)
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
    return DiaDdaComparisonReport(
        protein_overlap=tuple(protein_overlap),
        summary=DiaDdaComparisonSummary(
            dia_protein_count=len(dia_proteins),
            dda_protein_count=len(dda_proteins),
            shared_protein_count=shared_count,
            dia_only_protein_count=dia_only_count,
            dda_only_protein_count=dda_only_count,
        ),
        note=(
            "dia-vs-dda comparison keeps accession-level workflow overlap explicit before peptide and intensity complementarity claims are made"
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
