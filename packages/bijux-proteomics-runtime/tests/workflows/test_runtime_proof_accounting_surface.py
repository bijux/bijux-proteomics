# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics_runtime.workflows import (
    RuntimeProofClass,
    build_runtime_execution_shortcut_audit,
    build_runtime_flagship_proof_gate,
    build_runtime_proof_map,
    build_runtime_proof_promotion_checklist,
    validate_runtime_execution_shortcut_audit,
)


def test_runtime_execution_shortcut_audit_lists_only_explicit_simulation_exceptions() -> None:
    audit = build_runtime_execution_shortcut_audit()

    helper_ids = {entry.helper_id for entry in audit.entries}
    assert helper_ids == {
        "packages/bijux-proteomics-runtime/tests/api/test_runtime_cli_surface.py::_fake_import_result",
        "packages/bijux-proteomics-runtime/tests/api/test_runtime_cli_surface.py::_fake_run_sequence",
        "packages/bijux-proteomics-runtime/tests/execution/test_runtime_container_and_scheduler_end_to_end.py::_fake_run_flow_from_fixture",
        "packages/bijux-proteomics-runtime/tests/execution/test_runtime_container_and_scheduler_end_to_end.py::_fake_run_flow",
        "packages/bijux-proteomics-runtime/tests/performance/test_runtime_execution_control_benchmark_surface.py::_fake_success",
    }
    assert all(entry.proof_class is RuntimeProofClass.SIMULATION_ONLY for entry in audit.entries)
    assert all(entry.justified_exception for entry in audit.entries)
    assert all(not entry.counts_toward_flagship_proof for entry in audit.entries)


def test_runtime_execution_shortcut_audit_blocks_unapproved_fake_helpers() -> None:
    assert validate_runtime_execution_shortcut_audit() == ()


def test_runtime_proof_map_distinguishes_raw_import_replay_and_simulation_claims() -> None:
    proof_map = build_runtime_proof_map()
    claims = {claim.claim_id: claim for claim in proof_map.claims}

    assert claims["sequence_to_digest:review-surface"].proof_class is RuntimeProofClass.RAW_EXECUTION
    assert claims["dda_import:review-surface"].proof_class is RuntimeProofClass.IMPORT_BACKED_EXECUTION
    assert claims["dia_import:failure-replay"].proof_class is RuntimeProofClass.REPLAY_BACKED_EXECUTION
    assert claims["simulated-external-engine-contract:simulation-contract"].proof_class is RuntimeProofClass.SIMULATION_ONLY
    assert all(
        claim.proof_class is not RuntimeProofClass.SIMULATION_ONLY
        for claim in proof_map.claims
        if claim.counts_toward_flagship_authority
    )


def test_runtime_flagship_proof_gate_keeps_simulation_out_of_release_authority() -> None:
    gate = build_runtime_flagship_proof_gate()

    assert gate.blocked_workflow_families == ()
    assert gate.issues == ()


def test_runtime_proof_promotion_checklist_ties_missing_work_to_concrete_paths() -> None:
    checklist = build_runtime_proof_promotion_checklist()
    items = {item.workflow_family: item for item in checklist.items}

    assert tuple(items) == ("dda_import", "dia_import", "targeted_review")
    assert items["dda_import"].current_proof_class is RuntimeProofClass.IMPORT_BACKED_EXECUTION
    assert items["dda_import"].required_path.endswith("workflows/benchmark_runs.py")
    assert items["dia_import"].satisfied is False
    assert items["targeted_review"].required_path.endswith(
        "targeted_transition_review_package/package_manifest.json"
    )
