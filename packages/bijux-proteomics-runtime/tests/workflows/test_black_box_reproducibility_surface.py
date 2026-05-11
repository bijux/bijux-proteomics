# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics_runtime.workflows import (
    build_runtime_artifact_stability_reports,
    build_runtime_black_box_rerun_gate,
    build_runtime_black_box_verification_routes,
    build_runtime_environment_contracts,
    build_runtime_execution_mode_comparisons,
    build_runtime_replay_challenges,
    build_runtime_rerun_refusals,
)


def test_black_box_routes_cover_all_flagship_families() -> None:
    routes = {
        route.workflow_family: route
        for route in build_runtime_black_box_verification_routes()
    }

    assert tuple(routes) == ("dda", "dia", "lfq", "multiplex", "ptm", "targeted")
    assert routes["dda"].benchmark_entry_artifact_path.endswith("package_manifest.json")
    assert routes["dda"].benchmark_source_manifest_path.endswith(
        "source_locator_manifest.json"
    )
    assert routes["dda"].runtime_bundle_artifact_path.endswith("dda/run_bundle.json")
    assert routes["dia"].run_mode.value == "raw_executable"


def test_execution_mode_comparisons_keep_import_vs_raw_boundaries_explicit() -> None:
    comparisons = {
        row.workflow_family: row for row in build_runtime_execution_mode_comparisons()
    }

    assert comparisons["dda"].current_run_mode.value == "import_only"
    assert comparisons["dda"].raw_rerun_supported is False
    assert "raw external-engine parity" in comparisons["dda"].blocked_claims
    assert comparisons["dia"].raw_rerun_supported is True
    assert "chromatogram-native DIA authority" in comparisons["dia"].blocked_claims


def test_replay_challenges_environment_contracts_and_refusals_stay_aligned() -> None:
    challenges = {row.workflow_family: row for row in build_runtime_replay_challenges()}
    contracts = {
        row.workflow_family: row for row in build_runtime_environment_contracts()
    }
    refusals = {row.workflow_family: row for row in build_runtime_rerun_refusals()}
    stability = {
        row.workflow_family: row for row in build_runtime_artifact_stability_reports()
    }

    assert (
        "open `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/dda_reviewable_run/package_manifest.json`"
        in challenges["dda"].minimal_steps[0]
    )
    assert "run_id" in stability["dda"].permitted_environment_drift
    assert contracts["dda"].external_dependencies
    assert contracts["targeted"].required_tools[0] == "python 3.11"
    assert refusals["dda"].rerun_ready is False
    assert "raw DDA search parity" in refusals["dda"].blocked_claims
    assert refusals["lfq"].rerun_ready is True


def test_runtime_black_box_rerun_gate_routes_release_blockers_to_public_surfaces() -> (
    None
):
    gate = build_runtime_black_box_rerun_gate()

    assert gate.gate_id == "runtime-black-box-rerun-gate"
    assert "dda" in gate.blocked_workflow_families
    assert "dia" in gate.blocked_workflow_families
    assert "multiplex" in gate.blocked_workflow_families
    assert (
        "docs/09-bijux-proteomics-runtime/runtime-execution-boundary.md"
        in gate.evidence_paths
    )
    assert any(issue.code == "faithful-rerun-refused" for issue in gate.issues)
