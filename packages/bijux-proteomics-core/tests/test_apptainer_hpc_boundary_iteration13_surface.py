# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.external_exec_iteration13 import (
    HpcContainerBoundaryInput,
    HpcContainerRuntime,
    evaluate_apptainer_hpc_boundary,
)


def test_evaluate_apptainer_hpc_boundary_refuses_when_semantics_are_incomplete() -> (
    None
):
    report = evaluate_apptainer_hpc_boundary(
        HpcContainerBoundaryInput(
            runtime=HpcContainerRuntime.APPTAINER,
            has_sif_image=True,
            has_bind_mount_plan=False,
            has_scheduler_integration=False,
        )
    )

    assert report.supported is False
    assert "bind_mount_plan" in report.reason
