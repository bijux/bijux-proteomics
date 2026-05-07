# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics_runtime.workflows.assurance import (
    WorkflowAssuranceTier,
    build_canonical_operator_path,
    build_workflow_assurance_matrix,
    major_workflow_families,
    simulation_contract_lane_ids,
    workflow_assurance_lanes,
)


def _repo_root() -> Path:
    return next(
        parent
        for parent in Path(__file__).resolve().parents
        if (parent / "packages").is_dir() and (parent / "configs").is_dir()
    )


def test_workflow_assurance_lanes_keep_fixtures_and_tests_visible() -> None:
    repo_root = _repo_root()
    lanes = workflow_assurance_lanes()

    assert lanes
    for lane in lanes:
        for fixture_path in lane.repo_relative_fixture_paths:
            assert (repo_root / fixture_path).exists(), fixture_path
        for test_path in lane.validating_test_paths:
            assert (repo_root / test_path).exists(), test_path
        assert lane.expected_surfaces


def test_major_workflow_families_have_non_simulation_assurance() -> None:
    rows = {row.workflow_family: row for row in build_workflow_assurance_matrix()}

    for workflow_family in major_workflow_families():
        row = rows[workflow_family]
        assert row.blocker_notes == ()
        assert row.real_lane_ids or row.external_compatibility_pack_ids


def test_canonical_operator_path_is_runtime_owned_and_artifact_backed() -> None:
    path = build_canonical_operator_path()

    assert path.workflow_family == "sequence_to_digest"
    assert path.entrypoint.endswith("run_reviewable_sequence_path")
    assert path.required_artifact_kinds == (
        "runtime-status",
        "runtime-report",
        "runtime-replay-contract",
        "runtime-integrity-report",
    )
    assert path.validating_test_paths == (
        "packages/bijux-proteomics-runtime/tests/workflows/test_runtime_operator_path_surface.py",
    )


def test_simulation_contract_lane_ids_are_explicit_and_separate() -> None:
    lanes_by_id = {lane.lane_id: lane for lane in workflow_assurance_lanes()}
    simulation_lane_ids = simulation_contract_lane_ids()

    assert simulation_lane_ids == ("simulated-external-engine-contract",)
    assert all(
        lanes_by_id[lane_id].assurance_tier is WorkflowAssuranceTier.SIMULATION_CONTRACT
        for lane_id in simulation_lane_ids
    )
