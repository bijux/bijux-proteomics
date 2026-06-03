# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

import bijux_proteomics_lab
from bijux_proteomics_lab.public_api import list_lab_root_api_entries


def test_lab_public_api_contains_only_curated_entrypoints() -> None:
    assert bijux_proteomics_lab.__all__ == [
        "plan_experiment_batches",
        "build_advisory_assay_plan",
        "build_executable_assay_plan",
    ]


def test_lab_public_api_removes_breadth_signaling_exports() -> None:
    removed = {
        "AssayLifecycleStage",
        "OperationalReadinessReport",
        "TargetedBenchmarkReport",
        "build_lims_export_bundle",
        "recommend_rerun_policy",
    }

    assert removed.isdisjoint(bijux_proteomics_lab.__all__)


def test_lab_public_api_module_matches_root_exports() -> None:
    assert tuple(entry.export_name for entry in list_lab_root_api_entries()) == tuple(
        bijux_proteomics_lab.__all__
    )
