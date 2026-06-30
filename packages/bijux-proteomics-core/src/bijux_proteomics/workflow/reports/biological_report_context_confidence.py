# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Context-derived confidence rules for biological report sections."""

from __future__ import annotations

from bijux_proteomics.interpretation import (
    DiseasePhenotypeInterpretationReport,
    DrugTargetInterpretationReport,
    TissueCellTypeContextReport,
)
from bijux_proteomics.interpretation.compartment_biology import (
    CompartmentBiologyReport,
)
from bijux_proteomics.workflow.reports.biological_report_molecular_context_confidence import (
    _build_disease_phenotype_entry,
    _build_drug_target_entry,
)
from bijux_proteomics.workflow.reports.biological_report_section_metadata import (
    BiologicalReportSectionConfidenceEntry,
)
from bijux_proteomics.workflow.reports.biological_report_compartment_confidence import (
    _build_compartment_entry,
)
from bijux_proteomics.workflow.reports.biological_report_sample_context_confidence import (
    _build_cohort_entry,
    _build_tissue_context_entry,
)
from bijux_proteomics.workflow.studies.cohort_stratification import (
    CohortStratificationReport,
)


def _build_context_section_confidence_entries(
    *,
    drug_target_report: DrugTargetInterpretationReport | None,
    disease_phenotype_report: DiseasePhenotypeInterpretationReport | None,
    cohort_stratification_report: CohortStratificationReport | None,
    tissue_cell_type_context_report: TissueCellTypeContextReport | None,
    compartment_biology_report: CompartmentBiologyReport | None,
) -> tuple[BiologicalReportSectionConfidenceEntry, ...]:
    """Build confidence entries for contextual report sections."""

    return (
        _build_drug_target_entry(drug_target_report),
        _build_disease_phenotype_entry(disease_phenotype_report),
        _build_cohort_entry(cohort_stratification_report),
        _build_tissue_context_entry(tissue_cell_type_context_report),
        _build_compartment_entry(compartment_biology_report),
    )
