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
from bijux_proteomics.workflow.reports.biological_report_models import (
    _BIOLOGICAL_REPORT_SECTION_TITLES,
    BiologicalReportSectionConfidenceEntry,
    BiologicalReportSectionConfidenceLabel,
    BiologicalReportSectionKey,
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


def _build_drug_target_entry(
    report: DrugTargetInterpretationReport | None,
) -> BiologicalReportSectionConfidenceEntry:
    if report is None or report.summary.entry_count == 0:
        return _build_section_confidence_entry(
            BiologicalReportSectionKey.DRUG_TARGET_INTERPRETATION,
            BiologicalReportSectionConfidenceLabel.INVALID,
            "no drug-target relationships were supported by explicit target annotations",
        )
    summary = report.summary
    if summary.high_evidence_entry_count > 0 and summary.direct_target_entry_count > 0:
        label = BiologicalReportSectionConfidenceLabel.HIGH
    elif summary.high_evidence_entry_count + summary.moderate_evidence_entry_count > 0:
        label = BiologicalReportSectionConfidenceLabel.MODERATE
    else:
        label = BiologicalReportSectionConfidenceLabel.WEAK
    return _build_section_confidence_entry(
        BiologicalReportSectionKey.DRUG_TARGET_INTERPRETATION,
        label,
        (
            "drug-target confidence derives from explicit target evidence tiers and "
            f"{summary.direct_target_entry_count} direct target entries"
        ),
    )


def _build_disease_phenotype_entry(
    report: DiseasePhenotypeInterpretationReport | None,
) -> BiologicalReportSectionConfidenceEntry:
    if report is None or report.summary.evaluated_term_count == 0:
        return _build_section_confidence_entry(
            BiologicalReportSectionKey.DISEASE_PHENOTYPE_INTERPRETATION,
            BiologicalReportSectionConfidenceLabel.INVALID,
            "no disease or phenotype terms were evaluable from the supplied annotations",
        )
    summary = report.summary
    if (
        summary.high_confidence_term_count > 0
        and summary.unknown_foreground_protein_count == 0
    ):
        label = BiologicalReportSectionConfidenceLabel.HIGH
    elif summary.filter_passing_term_count > 0:
        label = BiologicalReportSectionConfidenceLabel.MODERATE
    else:
        label = BiologicalReportSectionConfidenceLabel.WEAK
    return _build_section_confidence_entry(
        BiologicalReportSectionKey.DISEASE_PHENOTYPE_INTERPRETATION,
        label,
        (
            "disease and phenotype confidence derives from passing-term counts and "
            f"{summary.unknown_foreground_protein_count} unknown foreground proteins"
        ),
    )


def _build_cohort_entry(
    report: CohortStratificationReport | None,
) -> BiologicalReportSectionConfidenceEntry:
    if report is None or report.summary.supported_stratum_count == 0:
        return _build_section_confidence_entry(
            BiologicalReportSectionKey.COHORT_STRATIFICATION,
            BiologicalReportSectionConfidenceLabel.INVALID,
            "no supported subgroup strata passed the cohort stratification feasibility checks",
        )
    summary = report.summary
    if summary.subgroup_effect_count > 0 or summary.interaction_candidate_count > 0:
        label = BiologicalReportSectionConfidenceLabel.EXPLORATORY
    else:
        label = BiologicalReportSectionConfidenceLabel.WEAK
    return _build_section_confidence_entry(
        BiologicalReportSectionKey.COHORT_STRATIFICATION,
        label,
        (
            "cohort stratification confidence derives from supported subgroup strata and "
            f"{summary.interaction_candidate_count} interaction candidate(s)"
        ),
    )


def _build_tissue_context_entry(
    report: TissueCellTypeContextReport | None,
) -> BiologicalReportSectionConfidenceEntry:
    if report is None or report.summary.sample_with_marker_definition_count == 0:
        return _build_section_confidence_entry(
            BiologicalReportSectionKey.TISSUE_CELL_TYPE_CONTEXT,
            BiologicalReportSectionConfidenceLabel.INVALID,
            "no samples carried marker definitions for tissue or cell-type validation",
        )
    summary = report.summary
    if summary.mismatch_warning_count > 0:
        label = BiologicalReportSectionConfidenceLabel.WEAK
    elif summary.insufficient_marker_support_count > 0:
        label = BiologicalReportSectionConfidenceLabel.MODERATE
    else:
        label = BiologicalReportSectionConfidenceLabel.HIGH
    return _build_section_confidence_entry(
        BiologicalReportSectionKey.TISSUE_CELL_TYPE_CONTEXT,
        label,
        (
            "tissue and cell-type context confidence derives from sample marker agreement, "
            f"{summary.mismatch_warning_count} mismatch warning(s), and "
            f"{summary.insufficient_marker_support_count} insufficient-support sample(s)"
        ),
    )


def _build_compartment_entry(
    report: CompartmentBiologyReport | None,
) -> BiologicalReportSectionConfidenceEntry:
    if report is None or report.summary.compartment_count == 0:
        return _build_section_confidence_entry(
            BiologicalReportSectionKey.COMPARTMENT_BIOLOGY,
            BiologicalReportSectionConfidenceLabel.INVALID,
            "no compartments were evaluable from the supplied localization context",
        )
    summary = report.summary
    if (
        summary.condition_comparison_count > 0
        and summary.low_confidence_sample_score_count == 0
        and summary.unresolved_member_count == 0
        and summary.unknown_foreground_protein_count == 0
    ):
        label = BiologicalReportSectionConfidenceLabel.HIGH
    elif summary.condition_comparison_count > 0:
        label = BiologicalReportSectionConfidenceLabel.MODERATE
    else:
        label = BiologicalReportSectionConfidenceLabel.WEAK
    return _build_section_confidence_entry(
        BiologicalReportSectionKey.COMPARTMENT_BIOLOGY,
        label,
        (
            "compartment confidence derives from condition comparisons, unresolved members, "
            "and unknown-localization counts"
        ),
    )


def _build_section_confidence_entry(
    section_key: BiologicalReportSectionKey,
    confidence_label: BiologicalReportSectionConfidenceLabel,
    rationale: str,
) -> BiologicalReportSectionConfidenceEntry:
    return BiologicalReportSectionConfidenceEntry(
        section_key=section_key,
        section_title=_BIOLOGICAL_REPORT_SECTION_TITLES[section_key],
        confidence_label=confidence_label,
        rationale=rationale,
    )
