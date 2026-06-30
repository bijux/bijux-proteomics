# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Molecular-context assembly for biological report bundles."""

from __future__ import annotations

from typing import TYPE_CHECKING, NamedTuple

from bijux_proteomics.interpretation.biological_context_mapping import (
    BiologicalContextKind,
)
from bijux_proteomics.interpretation.disease_phenotype_interpretation import (
    DiseasePhenotypeInterpretationPolicy,
    build_disease_phenotype_interpretation_report,
)
from bijux_proteomics.interpretation.drug_target_interpretation import (
    DrugTargetInterpretationPolicy,
    build_drug_target_interpretation_report,
)

if TYPE_CHECKING:
    from bijux_proteomics.interpretation.biological_context_mapping import (
        BiologicalContextRecord,
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
    )
    from bijux_proteomics.quantification.contracts import LabelFreeQuantTable
    from bijux_proteomics.quantification.contracts.differential import (
        DifferentialAbundanceReport,
    )
    from bijux_proteomics.workflow.reports.biological_report_models import (
        BiologicalResultSelectionPolicy,
    )


class BiologicalMolecularContextReports(NamedTuple):
    """Molecular-context outputs owned by biological context assembly."""

    drug_target_report: DrugTargetInterpretationReport | None
    disease_phenotype_report: DiseasePhenotypeInterpretationReport | None


def _build_biological_molecular_context_reports(
    *,
    normalized_table: LabelFreeQuantTable,
    differential_report: DifferentialAbundanceReport,
    context_records: tuple[BiologicalContextRecord, ...],
    pathway_records: tuple[PathwayMembershipRecord, ...],
    annotation_report: ProteinAnnotationMappingReport,
    active_selection_policy: BiologicalResultSelectionPolicy,
) -> BiologicalMolecularContextReports:
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

    return BiologicalMolecularContextReports(
        drug_target_report=drug_target_report,
        disease_phenotype_report=disease_phenotype_report,
    )
