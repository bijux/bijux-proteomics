# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.benchmarks.dia_targeted_pressure import (
    build_dia_pressure_corpus_report,
    build_targeted_pressure_corpus_report,
)
from bijux_proteomics.dia.benchmarks import (
    TargetedCalibrationStandardObservation,
    TargetedHandoffHonestyObservation,
    TargetedHeavyLightPairObservation,
    TargetedOutcomeReconciliationObservation,
    build_dia_workflow_scientific_support_report,
    build_targeted_raw_to_reviewed_bundle_report,
    build_targeted_workflow_benchmark_report,
)


def test_dia_pressure_corpus_report_keeps_library_conditioning_visible() -> None:
    support_report = build_dia_workflow_scientific_support_report(
        imported_precursor_count=92,
        expected_precursor_count=100,
        sample_resolved_precursor_count=88,
        expected_sample_resolved_precursor_count=100,
        transition_supported_precursor_count=73,
        expected_transition_precursor_count=100,
        protein_group_count=61,
        expected_protein_group_count=100,
        sample_resolved_protein_count=58,
        expected_sample_resolved_protein_count=100,
        ion_mobility_observed_count=54,
        ion_mobility_expected_count=100,
        library_matched_peptide_count=81,
        expected_library_peptide_count=100,
        absent_expected_peptide_count=19,
    )

    report = build_dia_pressure_corpus_report(
        benchmark_surface_id="reviewable_import_surface:dia_library_conditioned_bundle",
        supporting_identity_paths=(
            "packages/bijux-proteomics-core/tests/fixtures/search_adapter_corpora/diann/diann_report.tsv",
            "packages/bijux-proteomics-core/tests/fixtures/formats/ion_mobility.mzml",
        ),
        support_report=support_report,
    )

    assert report.library_conditioned_partial is True
    assert report.biological_interpretation_blocked is True
    assert any(
        path.endswith("diann_report.tsv") for path in report.supporting_identity_paths
    )
    assert "missing expected peptides" in report.note


def test_targeted_pressure_corpus_report_keeps_handoff_blockers_visible() -> None:
    workflow_benchmark = build_targeted_workflow_benchmark_report(
        calibration_observations=(
            TargetedCalibrationStandardObservation(
                standard_id="std-a",
                sample_id="run-1",
                expected_ratio=1.0,
                observed_ratio=0.97,
                within_tolerance=True,
            ),
            TargetedCalibrationStandardObservation(
                standard_id="std-b",
                sample_id="run-1",
                expected_ratio=1.0,
                observed_ratio=1.34,
                within_tolerance=False,
            ),
        ),
        heavy_light_pairs=(
            TargetedHeavyLightPairObservation(
                pair_id="pair-a",
                light_candidate_id="pep-a-light",
                heavy_candidate_id="pep-a-heavy",
                pair_complete=True,
                heavy_light_ratio=1.02,
                interference_fraction=0.08,
            ),
            TargetedHeavyLightPairObservation(
                pair_id="pair-b",
                light_candidate_id="pep-b-light",
                heavy_candidate_id="pep-b-heavy",
                pair_complete=False,
                interference_fraction=0.22,
            ),
        ),
    )
    raw_to_reviewed_bundle = build_targeted_raw_to_reviewed_bundle_report(
        chromatogram_failed_metric_rows=0,
        benchmark_report=workflow_benchmark,
        handoff_observations=(
            TargetedHandoffHonestyObservation(
                handoff_id="handoff-a",
                claimed_transition_ready=True,
                calibration_failures_visible=True,
                interference_failures_visible=True,
                control_gaps_visible=True,
            ),
            TargetedHandoffHonestyObservation(
                handoff_id="handoff-b",
                claimed_transition_ready=True,
                calibration_failures_visible=False,
                interference_failures_visible=True,
                control_gaps_visible=True,
            ),
        ),
        outcome_observations=(
            TargetedOutcomeReconciliationObservation(
                handoff_id="handoff-a",
                observed_transition_failure=False,
                reconciliation_recorded=False,
                corrective_action_visible=False,
            ),
            TargetedOutcomeReconciliationObservation(
                handoff_id="handoff-b",
                observed_transition_failure=True,
                reconciliation_recorded=False,
                corrective_action_visible=False,
            ),
        ),
    )

    report = build_targeted_pressure_corpus_report(
        benchmark_surface_id="reviewable_import_surface:targeted_transition_bundle",
        supporting_identity_paths=(
            "packages/bijux-proteomics-core/tests/fixtures/formats/targeted_benchmark_qc.tsv",
            "packages/bijux-proteomics-core/tests/fixtures/production_run/spectra.mgf",
        ),
        workflow_benchmark=workflow_benchmark,
        raw_to_reviewed_bundle=raw_to_reviewed_bundle,
    )

    assert report.transition_handoff_blocked is True
    assert report.workflow_benchmark.calibration_failed_count == 1
    assert report.raw_to_reviewed_bundle.inflated_handoff_count == 1
    assert any(
        path.endswith("targeted_benchmark_qc.tsv")
        for path in report.supporting_identity_paths
    )
