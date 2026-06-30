# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi
"""Biological context and interpretation assembly for biological reports."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, NamedTuple

from bijux_proteomics.interpretation.biological_context_mapping import (
    BiologicalContextKind,
    build_biological_context_mapping_report,
    parse_biological_context_table,
)
from bijux_proteomics.interpretation.compartment_biology import (
    CompartmentBiologyPolicy,
    build_compartment_biology_report,
)
from bijux_proteomics.interpretation.disease_phenotype_interpretation import (
    DiseasePhenotypeInterpretationPolicy,
    build_disease_phenotype_interpretation_report,
)
from bijux_proteomics.interpretation.drug_target_interpretation import (
    DrugTargetInterpretationPolicy,
    build_drug_target_interpretation_report,
)
from bijux_proteomics.interpretation.tissue_cell_type_context import (
    build_tissue_cell_type_context_report,
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
    from bijux_proteomics.workflow.reports.biological_report_models import (
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

    if context_annotation_tsv_path is None:
        return BiologicalContextAssemblyReports(
            context_import_report=None,
            context_mapping_report=None,
            tissue_cell_type_context_report=None,
            drug_target_report=None,
            disease_phenotype_report=None,
            compartment_biology_report=None,
        )

    context_import_report = parse_biological_context_table(context_annotation_tsv_path)
    context_records = context_import_report.accepted_records
    context_mapping_report = build_biological_context_mapping_report(
        differential_reference_entries,
        context_records,
    )

    tissue_cell_type_context_report = None
    if any(
        record.context_kind
        in {
            BiologicalContextKind.TISSUE_MARKER,
            BiologicalContextKind.CELL_TYPE_MARKER,
        }
        for record in context_records
    ):
        tissue_cell_type_context_report = build_tissue_cell_type_context_report(
            normalized_table,
            experiment_design,
            context_records,
        )

    drug_target_report = None
    if any(
        record.context_kind is BiologicalContextKind.DRUG_TARGET
        for record in context_records
    ):
        drug_target_report = build_drug_target_interpretation_report(
            normalized_table,
            differential_report,
            context_records,
            pathway_records=pathway_records,
            annotation_report=annotation_report,
            policy=DrugTargetInterpretationPolicy(
                max_adjusted_p_value=active_selection_policy.max_adjusted_p_value,
                min_absolute_log2_fold_change=(
                    active_selection_policy.min_absolute_log2_fold_change
                ),
            ),
        )

    disease_phenotype_report = None
    if any(
        record.context_kind
        in {
            BiologicalContextKind.DISEASE_TERM,
            BiologicalContextKind.PHENOTYPE_TERM,
        }
        for record in context_records
    ):
        disease_phenotype_report = build_disease_phenotype_interpretation_report(
            normalized_table,
            differential_report,
            context_records,
            policy=DiseasePhenotypeInterpretationPolicy(
                max_adjusted_p_value=active_selection_policy.max_adjusted_p_value,
                min_absolute_log2_fold_change=(
                    active_selection_policy.min_absolute_log2_fold_change
                ),
                min_enrichment_ratio=1.0,
            ),
        )

    compartment_biology_report = None
    if any(
        record.context_kind is BiologicalContextKind.SUBCELLULAR_COMPARTMENT
        for record in context_records
    ):
        compartment_biology_report = build_compartment_biology_report(
            normalized_table,
            differential_report,
            context_records,
            design_entries=design_entries,
            policy=CompartmentBiologyPolicy(
                max_adjusted_p_value=active_selection_policy.max_adjusted_p_value,
                min_absolute_log2_fold_change=(
                    active_selection_policy.min_absolute_log2_fold_change
                ),
            ),
        )

    return BiologicalContextAssemblyReports(
        context_import_report=context_import_report,
        context_mapping_report=context_mapping_report,
        tissue_cell_type_context_report=tissue_cell_type_context_report,
        drug_target_report=drug_target_report,
        disease_phenotype_report=disease_phenotype_report,
        compartment_biology_report=compartment_biology_report,
    )
