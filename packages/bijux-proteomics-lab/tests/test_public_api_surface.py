# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

import bijux_proteomics_lab


def test_design_public_api_contains_expected_exports() -> None:
    assert "ExperimentDesignStructureSummary" in bijux_proteomics_lab.__all__
    assert "EvidenceNeedWetLabAction" in bijux_proteomics_lab.__all__
    assert "LabExecutionRequest" in bijux_proteomics_lab.__all__
    assert "SamplePreparationMetadata" in bijux_proteomics_lab.__all__
    assert "InstrumentMethodMetadata" in bijux_proteomics_lab.__all__
    assert "ReplicationStrategySummary" in bijux_proteomics_lab.__all__
    assert "validate_experiment_design" in bijux_proteomics_lab.__all__
    assert "build_power_analysis_advisory" in bijux_proteomics_lab.__all__
    assert "plan_batch_randomization" in bijux_proteomics_lab.__all__
    assert "build_fractionation_plan" in bijux_proteomics_lab.__all__
    assert "plan_multiplex_labeling" in bijux_proteomics_lab.__all__
    assert "plan_spike_in_qc_samples" in bijux_proteomics_lab.__all__
    assert "assess_carryover_risk" in bijux_proteomics_lab.__all__
    assert "build_lab_protocol_evidence_bundle" in bijux_proteomics_lab.__all__
