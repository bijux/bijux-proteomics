# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.study.laboratory_plans import (
    TargetedPlatformAssumptionInput,
    TargetedPlatformSupportState,
    TargetedWorkflowMethod,
    build_targeted_platform_support_matrix,
)


def test_build_targeted_platform_support_matrix_separates_supported_partial_and_refused() -> (
    None
):
    report = build_targeted_platform_support_matrix(
        (
            TargetedPlatformAssumptionInput(
                platform_id="orbitrap-prm",
                method=TargetedWorkflowMethod.PRM,
                has_transition_list=True,
                has_retention_windows=True,
                has_collision_energy_profile=True,
                has_instrument_method_template=True,
                has_heavy_reference=True,
                has_calibration_standards=True,
                has_vendor_tuning_profile=True,
            ),
            TargetedPlatformAssumptionInput(
                platform_id="qqq-srm",
                method=TargetedWorkflowMethod.SRM,
                has_transition_list=True,
                has_retention_windows=True,
                has_collision_energy_profile=True,
                has_instrument_method_template=False,
                has_heavy_reference=True,
                has_calibration_standards=False,
                has_vendor_tuning_profile=False,
            ),
            TargetedPlatformAssumptionInput(
                platform_id="iontrap-prm",
                method=TargetedWorkflowMethod.PRM,
                has_transition_list=False,
                has_retention_windows=True,
                has_collision_energy_profile=False,
                has_instrument_method_template=True,
                has_heavy_reference=False,
                has_calibration_standards=False,
                has_vendor_tuning_profile=False,
            ),
        )
    )

    states = {entry.platform_id: entry.support_state for entry in report.entries}

    assert states["orbitrap-prm"] is TargetedPlatformSupportState.SUPPORTED
    assert states["qqq-srm"] is TargetedPlatformSupportState.PARTIAL
    assert states["iontrap-prm"] is TargetedPlatformSupportState.REFUSED
    qqq_entry = next(entry for entry in report.entries if entry.platform_id == "qqq-srm")
    assert "partial targeted support means" in qqq_entry.partial_support_definition
    assert "calibration_standards" in qqq_entry.missing_assumptions
    refused_entry = next(
        entry for entry in report.entries if entry.platform_id == "iontrap-prm"
    )
    assert "transition_list" in refused_entry.missing_assumptions
    assert report.supported_count == 1
    assert report.partial_count == 1
    assert report.refused_count == 1
