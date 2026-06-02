# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Public identification pressure corpora tied to flagship benchmark packages."""

from __future__ import annotations

from pydantic import ConfigDict, Field

from bijux_proteomics.identification.calibration_benchmarks import (
    AdapterCalibrationBenchmarkSuiteReport,
)
from bijux_proteomics.identification.contaminant_audit import (
    ContaminantAwareProteinInferenceAudit,
)
from bijux_proteomics.identification.protein_inference_benchmarks import (
    IdentificationWorkflowClaimReview,
    ProteinInferenceBenchmarkScenarioKind,
    ProteinInferenceBenchmarkSuiteReport,
)
from bijux_proteomics.identification.search_adapters import SearchAdapterKind
from bijux_proteomics_foundation import JsonModel


class CalibrationPressureCorpusReport(JsonModel):
    """Flagship calibration corpus over real imported search-adapter result families."""

    model_config = ConfigDict(extra="forbid")

    corpus_id: str = Field(..., min_length=1)
    benchmark_package_id: str = Field(..., min_length=1)
    imported_result_identity_paths: tuple[str, ...] = Field(default_factory=tuple)
    adapter_kinds: tuple[SearchAdapterKind, ...] = Field(default_factory=tuple)
    adapter_family_count: int = Field(..., ge=0)
    nonmonotonic_adapter_count: int = Field(..., ge=0)
    threshold_drift_watchpoint_count: int = Field(..., ge=0)
    entrapment_watchpoint_count: int = Field(..., ge=0)
    benchmark_suite: AdapterCalibrationBenchmarkSuiteReport
    requires_follow_up: bool
    note: str = Field(..., min_length=1)


class ProteinInferencePressureCorpusReport(JsonModel):
    """Flagship protein-inference pressure corpus with contaminant and trust posture."""

    model_config = ConfigDict(extra="forbid")

    corpus_id: str = Field(..., min_length=1)
    benchmark_package_id: str = Field(..., min_length=1)
    supporting_identity_paths: tuple[str, ...] = Field(default_factory=tuple)
    shared_peptide_pressure_scenario_count: int = Field(..., ge=0)
    isoform_pressure_scenario_count: int = Field(..., ge=0)
    false_negative_pressure_scenario_count: int = Field(..., ge=0)
    unresolved_contaminant_promotion: bool
    benchmark_suite: ProteinInferenceBenchmarkSuiteReport
    claim_review: IdentificationWorkflowClaimReview
    contaminant_audit: ContaminantAwareProteinInferenceAudit
    ready_for_broad_identification_claim: bool
    note: str = Field(..., min_length=1)


def build_calibration_pressure_corpus_report(
    *,
    benchmark_package_id: str,
    imported_result_identity_paths: tuple[str, ...],
    benchmark_suite: AdapterCalibrationBenchmarkSuiteReport,
    top_fraction_interval_watchpoint: float = 0.05,
) -> CalibrationPressureCorpusReport:
    """Build the flagship calibration corpus from real adapter-family evidence."""

    adapter_kinds = tuple(entry.adapter_kind for entry in benchmark_suite.entries)
    nonmonotonic_count = sum(
        not entry.q_value_monotonic for entry in benchmark_suite.entries
    )
    threshold_drift_count = sum(
        entry.calibration.top_fraction_decoy_interval_width
        > top_fraction_interval_watchpoint
        for entry in benchmark_suite.entries
    )
    entrapment_watchpoint_count = sum(
        entry.entrapment.accepted_entrapment_count > 0
        for entry in benchmark_suite.entries
    )
    requires_follow_up = bool(
        nonmonotonic_count or threshold_drift_count or entrapment_watchpoint_count
    )
    return CalibrationPressureCorpusReport(
        corpus_id="flagship_identification_pressure:calibration",
        benchmark_package_id=benchmark_package_id,
        imported_result_identity_paths=tuple(sorted(imported_result_identity_paths)),
        adapter_kinds=adapter_kinds,
        adapter_family_count=len(adapter_kinds),
        nonmonotonic_adapter_count=nonmonotonic_count,
        threshold_drift_watchpoint_count=threshold_drift_count,
        entrapment_watchpoint_count=entrapment_watchpoint_count,
        benchmark_suite=benchmark_suite,
        requires_follow_up=requires_follow_up,
        note=(
            "The flagship calibration corpus turns public imported search-adapter results into one named pressure surface for q-value ordering, interval drift, and entrapment behavior."
        ),
    )


def build_protein_inference_pressure_corpus_report(
    *,
    benchmark_package_id: str,
    supporting_identity_paths: tuple[str, ...],
    benchmark_suite: ProteinInferenceBenchmarkSuiteReport,
    claim_review: IdentificationWorkflowClaimReview,
    contaminant_audit: ContaminantAwareProteinInferenceAudit,
) -> ProteinInferencePressureCorpusReport:
    """Build the flagship protein-inference pressure corpus."""

    shared_peptide_pressure_scenario_count = sum(
        scenario_kind is ProteinInferenceBenchmarkScenarioKind.SHARED_PEPTIDE_HEAVY
        for scenario_kind in benchmark_suite.scenario_kinds
    )
    isoform_pressure_scenario_count = sum(
        scenario_kind is ProteinInferenceBenchmarkScenarioKind.ISOFORM_HEAVY
        for scenario_kind in benchmark_suite.scenario_kinds
    )
    false_negative_pressure_scenario_count = sum(
        any(
            assessment.false_negative_count > 0
            for assessment in report.method_assessments
        )
        for report in benchmark_suite.reports
    )
    ready = (
        claim_review.accepted and not contaminant_audit.unresolved_contaminant_promotion
    )
    return ProteinInferencePressureCorpusReport(
        corpus_id="flagship_identification_pressure:protein_inference",
        benchmark_package_id=benchmark_package_id,
        supporting_identity_paths=tuple(sorted(supporting_identity_paths)),
        shared_peptide_pressure_scenario_count=shared_peptide_pressure_scenario_count,
        isoform_pressure_scenario_count=isoform_pressure_scenario_count,
        false_negative_pressure_scenario_count=false_negative_pressure_scenario_count,
        unresolved_contaminant_promotion=contaminant_audit.unresolved_contaminant_promotion,
        benchmark_suite=benchmark_suite,
        claim_review=claim_review,
        contaminant_audit=contaminant_audit,
        ready_for_broad_identification_claim=ready,
        note=(
            "The flagship protein-inference corpus keeps shared-peptide, isoform, false-negative, and contaminant pressure visible before any broad identification claim is promoted."
        ),
    )


__all__ = [
    "CalibrationPressureCorpusReport",
    "ProteinInferencePressureCorpusReport",
    "build_calibration_pressure_corpus_report",
    "build_protein_inference_pressure_corpus_report",
]
