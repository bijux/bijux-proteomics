# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Scientific benchmark surfaces for DIA-targeted and transition workflows."""

from __future__ import annotations

from collections.abc import Iterable
from enum import StrEnum
from typing import TYPE_CHECKING

from pydantic import ConfigDict, Field

from bijux_proteomics_foundation import JsonModel

if TYPE_CHECKING:
    from bijux_proteomics.dia.library_coverage import DiaLibraryCoverageReport


class WorkflowScientificSupportTier(StrEnum):
    """Scientifically meaningful support tier for one workflow surface."""

    SUPPORTED = "supported"
    PARTIAL = "partial"
    REFUSED = "refused"


class DiaWorkflowSupportTierEntry(JsonModel):
    """One DIA support surface with explicit tier and threshold accounting."""

    model_config = ConfigDict(extra="forbid")

    surface: str = Field(..., min_length=1)
    support_tier: WorkflowScientificSupportTier
    observed_fraction: float = Field(..., ge=0.0, le=1.0)
    supported_threshold: float = Field(..., ge=0.0, le=1.0)
    partial_threshold: float = Field(..., ge=0.0, le=1.0)
    detail: str = Field(..., min_length=1)


class DiaWorkflowScientificSupportReport(JsonModel):
    """Tiered DIA workflow support report over import, transitions, protein, and interpretation."""

    model_config = ConfigDict(extra="forbid")

    entries: tuple[DiaWorkflowSupportTierEntry, ...] = Field(default_factory=tuple)
    ion_mobility_observed_fraction: float = Field(..., ge=0.0, le=1.0)
    library_coverage_fraction: float = Field(..., ge=0.0, le=1.0)
    sample_library_coverage_fraction: float = Field(..., ge=0.0, le=1.0)
    condition_library_coverage_fraction: float = Field(..., ge=0.0, le=1.0)
    absent_expected_peptide_fraction: float = Field(..., ge=0.0, le=1.0)
    partial_support_definition: str = Field(..., min_length=1)
    ready_for_biological_interpretation: bool


class TargetedCalibrationStandardObservation(JsonModel):
    """Observed calibration-standard behavior for one targeted benchmark sample."""

    model_config = ConfigDict(extra="forbid")

    standard_id: str = Field(..., min_length=1)
    sample_id: str = Field(..., min_length=1)
    expected_ratio: float = Field(..., gt=0.0)
    observed_ratio: float = Field(..., gt=0.0)
    within_tolerance: bool


class TargetedHeavyLightPairObservation(JsonModel):
    """Observed heavy/light pairing and interference behavior."""

    model_config = ConfigDict(extra="forbid")

    pair_id: str = Field(..., min_length=1)
    light_candidate_id: str = Field(..., min_length=1)
    heavy_candidate_id: str = Field(..., min_length=1)
    pair_complete: bool
    heavy_light_ratio: float | None = Field(default=None, gt=0.0)
    interference_fraction: float = Field(..., ge=0.0, le=1.0)


class TargetedWorkflowBenchmarkReport(JsonModel):
    """Targeted workflow benchmark over calibration, pairing, and interference."""

    model_config = ConfigDict(extra="forbid")

    calibration_supported_count: int = Field(..., ge=0)
    calibration_failed_count: int = Field(..., ge=0)
    complete_heavy_light_pair_count: int = Field(..., ge=0)
    missing_heavy_light_pair_count: int = Field(..., ge=0)
    interference_flag_count: int = Field(..., ge=0)
    support_tier: WorkflowScientificSupportTier
    partial_support_definition: str = Field(..., min_length=1)
    ready_for_transition_handoff: bool
    note: str = Field(..., min_length=1)


class TargetedHandoffHonestyObservation(JsonModel):
    """One targeted handoff packet checked against what the benchmark actually proved."""

    model_config = ConfigDict(extra="forbid")

    handoff_id: str = Field(..., min_length=1)
    claimed_transition_ready: bool
    calibration_failures_visible: bool
    interference_failures_visible: bool
    control_gaps_visible: bool


class TargetedOutcomeReconciliationObservation(JsonModel):
    """One observed targeted outcome compared with the claimed handoff posture."""

    model_config = ConfigDict(extra="forbid")

    handoff_id: str = Field(..., min_length=1)
    observed_transition_failure: bool
    reconciliation_recorded: bool
    corrective_action_visible: bool


class TargetedRawToReviewedBundleReport(JsonModel):
    """One raw-to-reviewed targeted bundle linking QC, handoff honesty, and outcomes."""

    model_config = ConfigDict(extra="forbid")

    chromatogram_surface_reviewable: bool
    honest_handoff_count: int = Field(..., ge=0)
    inflated_handoff_count: int = Field(..., ge=0)
    reconciled_outcome_count: int = Field(..., ge=0)
    unreconciled_outcome_count: int = Field(..., ge=0)
    ready_for_reviewed_handoff: bool
    note: str = Field(..., min_length=1)


def _fraction(numerator: int, denominator: int) -> float:
    if denominator <= 0:
        return 0.0
    return min(1.0, max(0.0, numerator / denominator))


def _tier_from_fraction(
    *,
    fraction: float,
    supported_threshold: float,
    partial_threshold: float,
) -> WorkflowScientificSupportTier:
    if fraction >= supported_threshold:
        return WorkflowScientificSupportTier.SUPPORTED
    if fraction >= partial_threshold:
        return WorkflowScientificSupportTier.PARTIAL
    return WorkflowScientificSupportTier.REFUSED


def build_dia_workflow_scientific_support_report(
    *,
    imported_precursor_count: int,
    expected_precursor_count: int,
    sample_resolved_precursor_count: int,
    expected_sample_resolved_precursor_count: int,
    transition_supported_precursor_count: int,
    expected_transition_precursor_count: int,
    protein_group_count: int,
    expected_protein_group_count: int,
    sample_resolved_protein_count: int,
    expected_sample_resolved_protein_count: int,
    ion_mobility_observed_count: int,
    ion_mobility_expected_count: int,
    library_matched_peptide_count: int,
    expected_library_peptide_count: int,
    absent_expected_peptide_count: int,
    sample_library_coverage_fraction: float | None = None,
    condition_library_coverage_fraction: float | None = None,
) -> DiaWorkflowScientificSupportReport:
    """Score DIA support tiers with explicit realism pressure and partial-support rules."""

    import_fraction = _fraction(imported_precursor_count, expected_precursor_count)
    precursor_matrix_fraction = _fraction(
        sample_resolved_precursor_count,
        expected_sample_resolved_precursor_count,
    )
    transition_fraction = _fraction(
        transition_supported_precursor_count,
        expected_transition_precursor_count,
    )
    protein_fraction = _fraction(protein_group_count, expected_protein_group_count)
    protein_matrix_fraction = _fraction(
        sample_resolved_protein_count,
        expected_sample_resolved_protein_count,
    )
    ion_mobility_fraction = _fraction(
        ion_mobility_observed_count,
        ion_mobility_expected_count,
    )
    library_coverage_fraction = _fraction(
        library_matched_peptide_count,
        expected_library_peptide_count,
    )
    sample_library_fraction = _optional_fraction(sample_library_coverage_fraction)
    condition_library_fraction = _optional_fraction(condition_library_coverage_fraction)
    absent_expected_fraction = _fraction(
        absent_expected_peptide_count,
        expected_library_peptide_count,
    )

    library_tier = _tier_from_fraction(
        fraction=min(import_fraction, library_coverage_fraction),
        supported_threshold=0.9,
        partial_threshold=0.7,
    )
    transition_tier = _tier_from_fraction(
        fraction=transition_fraction,
        supported_threshold=0.85,
        partial_threshold=0.6,
    )
    precursor_matrix_tier = _tier_from_fraction(
        fraction=min(import_fraction, precursor_matrix_fraction),
        supported_threshold=0.9,
        partial_threshold=0.7,
    )
    protein_tier = _tier_from_fraction(
        fraction=min(
            protein_fraction,
            protein_matrix_fraction,
            library_coverage_fraction,
        ),
        supported_threshold=0.8,
        partial_threshold=0.5,
    )
    interpretation_signal = min(
        library_coverage_fraction,
        sample_library_fraction,
        condition_library_fraction,
        ion_mobility_fraction if ion_mobility_expected_count > 0 else 1.0,
        1.0 - absent_expected_fraction,
    )
    interpretation_tier = _tier_from_fraction(
        fraction=interpretation_signal,
        supported_threshold=0.8,
        partial_threshold=0.55,
    )
    if (
        library_tier is WorkflowScientificSupportTier.REFUSED
        or transition_tier is WorkflowScientificSupportTier.REFUSED
        or protein_tier is WorkflowScientificSupportTier.REFUSED
    ):
        interpretation_tier = WorkflowScientificSupportTier.REFUSED

    entries = (
        DiaWorkflowSupportTierEntry(
            surface="library_conditioned_import",
            support_tier=library_tier,
            observed_fraction=min(import_fraction, library_coverage_fraction),
            supported_threshold=0.9,
            partial_threshold=0.7,
            detail=(
                "import support is bounded by both precursor import success and peptide coverage against the expected library scope"
            ),
        ),
        DiaWorkflowSupportTierEntry(
            surface="precursor_matrix_evidence",
            support_tier=precursor_matrix_tier,
            observed_fraction=min(import_fraction, precursor_matrix_fraction),
            supported_threshold=0.9,
            partial_threshold=0.7,
            detail=(
                "precursor-level analysis is only strong when imported evidence remains sample-resolved enough to support precursor-by-sample matrices rather than one-off run rows"
            ),
        ),
        DiaWorkflowSupportTierEntry(
            surface="transition_semantics",
            support_tier=transition_tier,
            observed_fraction=transition_fraction,
            supported_threshold=0.85,
            partial_threshold=0.6,
            detail=(
                "transition semantics stay reviewable only when most expected precursors retain explicit fragment-linked support"
            ),
        ),
        DiaWorkflowSupportTierEntry(
            surface="protein_level_evidence",
            support_tier=protein_tier,
            observed_fraction=min(
                protein_fraction,
                protein_matrix_fraction,
                library_coverage_fraction,
            ),
            supported_threshold=0.8,
            partial_threshold=0.5,
            detail=(
                "protein-level evidence is downgraded whenever protein-by-sample matrix coverage or library coverage collapses even if imported precursors still look healthy"
            ),
        ),
        DiaWorkflowSupportTierEntry(
            surface="biological_interpretation",
            support_tier=interpretation_tier,
            observed_fraction=interpretation_signal,
            supported_threshold=0.8,
            partial_threshold=0.55,
            detail=(
                "biological interpretation is only strong when aggregate library coverage, sample and condition library visibility, peptide presence, and ion-mobility evidence all stay above bounded thresholds"
            ),
        ),
    )
    return DiaWorkflowScientificSupportReport(
        entries=entries,
        ion_mobility_observed_fraction=ion_mobility_fraction,
        library_coverage_fraction=library_coverage_fraction,
        sample_library_coverage_fraction=sample_library_fraction,
        condition_library_coverage_fraction=condition_library_fraction,
        absent_expected_peptide_fraction=absent_expected_fraction,
        partial_support_definition=(
            "partial DIA support means imported evidence remains reviewable, but one or more realism pressures "
            "such as incomplete library coverage, uneven sample or condition library visibility, weak transition retention, weak protein-matrix coverage, missing ion-mobility evidence, or absent expected peptides "
            "still block strong biological interpretation"
        ),
        ready_for_biological_interpretation=(
            interpretation_tier is WorkflowScientificSupportTier.SUPPORTED
        ),
    )


def build_dia_workflow_scientific_support_from_library_coverage(
    *,
    imported_precursor_count: int,
    expected_precursor_count: int,
    sample_resolved_precursor_count: int,
    expected_sample_resolved_precursor_count: int,
    transition_supported_precursor_count: int,
    expected_transition_precursor_count: int,
    protein_group_count: int,
    expected_protein_group_count: int,
    sample_resolved_protein_count: int,
    expected_sample_resolved_protein_count: int,
    ion_mobility_observed_count: int,
    ion_mobility_expected_count: int,
    library_coverage_report: DiaLibraryCoverageReport,
) -> DiaWorkflowScientificSupportReport:
    """Build DIA support tiers directly from one spectral-library coverage report."""

    return build_dia_workflow_scientific_support_report(
        imported_precursor_count=imported_precursor_count,
        expected_precursor_count=expected_precursor_count,
        sample_resolved_precursor_count=sample_resolved_precursor_count,
        expected_sample_resolved_precursor_count=expected_sample_resolved_precursor_count,
        transition_supported_precursor_count=transition_supported_precursor_count,
        expected_transition_precursor_count=expected_transition_precursor_count,
        protein_group_count=protein_group_count,
        expected_protein_group_count=expected_protein_group_count,
        sample_resolved_protein_count=sample_resolved_protein_count,
        expected_sample_resolved_protein_count=expected_sample_resolved_protein_count,
        ion_mobility_observed_count=ion_mobility_observed_count,
        ion_mobility_expected_count=ion_mobility_expected_count,
        library_matched_peptide_count=library_coverage_report.summary.detected_peptide_count,
        expected_library_peptide_count=library_coverage_report.summary.library_peptide_count,
        absent_expected_peptide_count=(
            library_coverage_report.summary.library_peptide_count
            - library_coverage_report.summary.detected_peptide_count
        ),
        sample_library_coverage_fraction=_mean(
            entry.peptide_coverage_fraction
            for entry in library_coverage_report.sample_entries
        ),
        condition_library_coverage_fraction=_mean(
            entry.peptide_coverage_fraction
            for entry in library_coverage_report.condition_entries
        ),
    )


def build_targeted_workflow_benchmark_report(
    *,
    calibration_observations: tuple[TargetedCalibrationStandardObservation, ...],
    heavy_light_pairs: tuple[TargetedHeavyLightPairObservation, ...],
    max_interference_fraction: float = 0.15,
) -> TargetedWorkflowBenchmarkReport:
    """Benchmark targeted support against calibration, pairing, and interference pressure."""

    calibration_supported = sum(
        1 for observation in calibration_observations if observation.within_tolerance
    )
    calibration_failed = len(calibration_observations) - calibration_supported
    complete_pairs = sum(1 for pair in heavy_light_pairs if pair.pair_complete)
    missing_pairs = len(heavy_light_pairs) - complete_pairs
    interference_flag_count = sum(
        1
        for pair in heavy_light_pairs
        if pair.interference_fraction > max_interference_fraction
    )
    ready = (
        calibration_failed == 0
        and missing_pairs == 0
        and interference_flag_count == 0
        and bool(calibration_observations)
        and bool(heavy_light_pairs)
    )
    support_tier = (
        WorkflowScientificSupportTier.SUPPORTED
        if ready
        else WorkflowScientificSupportTier.PARTIAL
        if bool(calibration_observations) and bool(heavy_light_pairs)
        else WorkflowScientificSupportTier.REFUSED
    )
    return TargetedWorkflowBenchmarkReport(
        calibration_supported_count=calibration_supported,
        calibration_failed_count=calibration_failed,
        complete_heavy_light_pair_count=complete_pairs,
        missing_heavy_light_pair_count=missing_pairs,
        interference_flag_count=interference_flag_count,
        support_tier=support_tier,
        partial_support_definition=(
            "partial targeted support means the workflow keeps chromatogram, calibration, or heavy/light evidence reviewable, "
            "but missing pairs, failed standards, or interference still block confident transition handoff"
        ),
        ready_for_transition_handoff=ready,
        note=(
            "targeted workflow clears calibration, heavy/light pairing, and interference pressure"
            if ready
            else "targeted workflow remains limited by calibration failure, incomplete pairing, or transition interference"
        ),
    )


def _optional_fraction(value: float | None) -> float:
    if value is None:
        return 1.0
    return min(1.0, max(0.0, value))


def _mean(values: Iterable[float]) -> float:
    sequence = tuple(float(value) for value in values)
    if not sequence:
        return 1.0
    return min(1.0, max(0.0, sum(sequence) / len(sequence)))


def build_targeted_raw_to_reviewed_bundle_report(
    *,
    chromatogram_failed_metric_rows: int,
    benchmark_report: TargetedWorkflowBenchmarkReport,
    handoff_observations: tuple[TargetedHandoffHonestyObservation, ...],
    outcome_observations: tuple[TargetedOutcomeReconciliationObservation, ...],
) -> TargetedRawToReviewedBundleReport:
    """Link targeted QC, handoff honesty, and observed outcome reconciliation."""

    chromatogram_surface_reviewable = chromatogram_failed_metric_rows == 0
    honest_handoff_count = 0
    inflated_handoff_count = 0
    for observation in handoff_observations:
        inflated = observation.claimed_transition_ready and (
            not observation.calibration_failures_visible
            or not observation.interference_failures_visible
            or not observation.control_gaps_visible
        )
        if inflated:
            inflated_handoff_count += 1
        else:
            honest_handoff_count += 1

    reconciled_outcome_count = 0
    unreconciled_outcome_count = 0
    for outcome_observation in outcome_observations:
        if (
            outcome_observation.observed_transition_failure
            and outcome_observation.reconciliation_recorded
            and outcome_observation.corrective_action_visible
        ) or not outcome_observation.observed_transition_failure:
            reconciled_outcome_count += 1
        else:
            unreconciled_outcome_count += 1

    ready = (
        chromatogram_surface_reviewable
        and benchmark_report.ready_for_transition_handoff
        and inflated_handoff_count == 0
        and unreconciled_outcome_count == 0
        and bool(handoff_observations)
        and bool(outcome_observations)
    )
    return TargetedRawToReviewedBundleReport(
        chromatogram_surface_reviewable=chromatogram_surface_reviewable,
        honest_handoff_count=honest_handoff_count,
        inflated_handoff_count=inflated_handoff_count,
        reconciled_outcome_count=reconciled_outcome_count,
        unreconciled_outcome_count=unreconciled_outcome_count,
        ready_for_reviewed_handoff=ready,
        note=(
            "targeted bundle keeps chromatogram QC, handoff honesty, and observed outcome reconciliation aligned before follow-up claims are promoted"
            if ready
            else "targeted bundle still contains QC, handoff, or reconciliation gaps that would let review-grade evidence masquerade as execution-ready follow-up"
        ),
    )
