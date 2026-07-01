# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi
"""Biological context and interpretation assembly for biological reports."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, NamedTuple

from bijux_proteomics.workflow.reports.biological_report_annotation_context_assembly import (
    _build_biological_annotation_context_reports,
)
from bijux_proteomics.workflow.reports.biological_report_compartment_biology_assembly import (
    _build_biological_compartment_biology_report,
)
from bijux_proteomics.workflow.reports.biological_report_molecular_context_assembly import (
    _build_biological_molecular_context_reports,
)
from bijux_proteomics.workflow.reports.biological_report_sample_context_assembly import (
    _build_biological_sample_context_report,
)

if TYPE_CHECKING:
    from bijux_proteomics.interpretation.biological_context_mapping import (
        BiologicalContextImportReport,
        BiologicalContextMappingReport,
    )
    from bijux_proteomics.interpretation.compartment_biology import (
        CompartmentBiologyReport,
    )
    from bijux_proteomics.interpretation.disease_phenotype_interpretation import (
        DiseasePhenotypeInterpretationReport,
    )
    from bijux_proteomics.interpretation.drug_target_interpretation import (
        DrugTargetInterpretationReport,
    )
    from bijux_proteomics.interpretation.pathway_enrichment import (
        PathwayMembershipRecord,
    )
    from bijux_proteomics.interpretation.protein_annotation_mapping import (
        ProteinAnnotationMappingReport,
        ProteinReferenceEntry,
    )
    from bijux_proteomics.interpretation.tissue_cell_type_context import (
        TissueCellTypeContextReport,
    )
    from bijux_proteomics.io.formats import ExperimentalDesignEntry
    from bijux_proteomics.quantification.contracts import LabelFreeQuantTable
    from bijux_proteomics.quantification.contracts.differential import (
        DifferentialAbundanceReport,
    )
    from bijux_proteomics.study import ExperimentDesign
    from bijux_proteomics.workflow.reports.biological_report_selection_policy import (
        BiologicalResultSelectionPolicy,
    )


class BiologicalContextAssemblyReports(NamedTuple):
    """Owned biological context outputs for report assembly."""

    context_import_report: BiologicalContextImportReport | None
    context_mapping_report: BiologicalContextMappingReport | None
    tissue_cell_type_context_report: TissueCellTypeContextReport | None
    drug_target_report: DrugTargetInterpretationReport | None
    disease_phenotype_report: DiseasePhenotypeInterpretationReport | None
    compartment_biology_report: CompartmentBiologyReport | None


def _build_biological_context_reports(
    *,
    normalized_table: LabelFreeQuantTable,
    experiment_design: ExperimentDesign,
    design_entries: tuple[ExperimentalDesignEntry, ...],
    differential_report: DifferentialAbundanceReport,
    differential_reference_entries: tuple[ProteinReferenceEntry, ...],
    annotation_report: ProteinAnnotationMappingReport,
    pathway_records: tuple[PathwayMembershipRecord, ...],
    active_selection_policy: BiologicalResultSelectionPolicy,
    context_annotation_tsv_path: Path | None,
) -> BiologicalContextAssemblyReports:
    """Build optional biological context reports from one imported context table."""

    annotation_context_reports = _build_biological_annotation_context_reports(
        differential_reference_entries=differential_reference_entries,
        context_annotation_tsv_path=context_annotation_tsv_path,
    )
    context_records = (
        ()
        if annotation_context_reports.context_import_report is None
        else annotation_context_reports.context_import_report.accepted_records
    )
    sample_context_report = _build_biological_sample_context_report(
        normalized_table=normalized_table,
        experiment_design=experiment_design,
        context_records=context_records,
    )
    molecular_context_reports = _build_biological_molecular_context_reports(
        normalized_table=normalized_table,
        differential_report=differential_report,
        context_records=context_records,
        pathway_records=pathway_records,
        annotation_report=annotation_report,
        active_selection_policy=active_selection_policy,
    )
    compartment_biology_report = _build_biological_compartment_biology_report(
        normalized_table=normalized_table,
        differential_report=differential_report,
        design_entries=design_entries,
        context_records=context_records,
        active_selection_policy=active_selection_policy,
    )

    return BiologicalContextAssemblyReports(
        context_import_report=annotation_context_reports.context_import_report,
        context_mapping_report=annotation_context_reports.context_mapping_report,
        tissue_cell_type_context_report=sample_context_report,
        drug_target_report=molecular_context_reports.drug_target_report,
        disease_phenotype_report=(molecular_context_reports.disease_phenotype_report),
        compartment_biology_report=compartment_biology_report,
    )
