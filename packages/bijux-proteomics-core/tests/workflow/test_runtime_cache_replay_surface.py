# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics_runtime.runtime.control.workflow_runs import (
    build_proteomics_workflow_cache_replay_report,
)


def test_build_proteomics_workflow_cache_replay_report_classifies_all_outcomes() -> (
    None
):
    report = build_proteomics_workflow_cache_replay_report(
        previous_artifact_hashes={
            "matrix": "aaa",
            "qc": "bbb",
            "lab_packet": "ccc",
            "legacy_surface": "ddd",
        },
        current_artifact_hashes={
            "matrix": "aaa",
            "qc": "ccc",
            "lab_packet": "ccc",
            "new_surface": "eee",
        },
        reused_surfaces=("matrix",),
        refused_surfaces=("legacy_surface",),
    )

    outcomes = {entry.surface: entry.outcome.value for entry in report.entries}
    assert outcomes["matrix"] == "reused"
    assert outcomes["qc"] == "changed"
    assert outcomes["lab_packet"] == "unchanged"
    assert outcomes["new_surface"] == "rerun"
    assert outcomes["legacy_surface"] == "refused"
    assert report.reused_count == 1
    assert report.rerun_count == 1
    assert report.changed_count == 1
    assert report.unchanged_count == 1
    assert report.refused_count == 1
