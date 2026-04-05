# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

import hashlib
from pathlib import Path

from agentic_proteins.runtime import RunManager
from agentic_proteins.runtime.context import RunLifecycleState
from agentic_proteins.runtime.control.state_machine import RunStateMachine
from agentic_proteins.runtime.infra import RunConfig


def _artifact_hashes(run_dir: Path) -> dict[str, str]:
    artifacts_dir = run_dir / "artifacts"
    hashes: dict[str, str] = {}
    for path in sorted(artifacts_dir.glob("*.json")):
        hashes[path.name] = hashlib.sha256(path.read_bytes()).hexdigest()
    return hashes


def test_invariant_determinism(tmp_path: Path) -> None:
    sequence = "ACDEFGHIK"
    config = RunConfig(seed=7)
    first = RunManager(tmp_path / "run_a", config).run(sequence)
    second = RunManager(tmp_path / "run_b", config).run(sequence)
    assert (
        first["plan_fingerprint"] == second["plan_fingerprint"]
    ), "Determinism invariant violated: plan fingerprint drifted."
    assert (
        first["tool_status"] == second["tool_status"]
    ), "Determinism invariant violated: tool status drifted."
    assert (
        first["report"] == second["report"]
    ), "Determinism invariant violated: report drifted."


def test_invariant_state_transitions() -> None:
    machine = RunStateMachine()
    assert (
        machine.state == RunLifecycleState.PLANNED
    ), "State transition invariant violated: initial state drifted."
    assert (
        machine.transition("execute") == RunLifecycleState.EXECUTING
    ), "State transition invariant violated: execute transition drifted."
    assert (
        machine.transition("evaluate") == RunLifecycleState.EVALUATED
    ), "State transition invariant violated: evaluate transition drifted."
    assert (
        machine.transition("invalid") == RunLifecycleState.EVALUATED
    ), "State transition invariant violated: invalid transition should not advance."


def test_invariant_artifact_immutability(tmp_path: Path) -> None:
    sequence = "ACDEFGHIK"
    run_id = "run-invariant"
    base_dir = tmp_path
    original_root = base_dir / "artifacts" / "original"
    reproduced_root = base_dir / "artifacts" / "reproduced"
    RunManager(base_dir, RunConfig(seed=3, artifacts_dir=str(original_root))).run(
        sequence, run_id=run_id
    )
    RunManager(base_dir, RunConfig(seed=3, artifacts_dir=str(reproduced_root))).run(
        sequence, run_id=run_id
    )
    original_hashes = _artifact_hashes(original_root / run_id)
    reproduced_hashes = _artifact_hashes(reproduced_root / run_id)
    assert (
        original_hashes == reproduced_hashes
    ), "Artifact immutability invariant violated: hashes drifted."


def test_invariant_provider_isolation(tmp_path: Path) -> None:
    sequence = "ACDEFGHIK"
    result = RunManager(tmp_path, RunConfig(seed=1)).run(sequence)
    tool_versions = result["version_info"]["tool_versions"]
    assert (
        set(tool_versions) == {"heuristic_proxy"}
    ), "Provider isolation invariant violated: unexpected provider executed."


def test_invariant_failure_containment(tmp_path: Path) -> None:
    result = RunManager(tmp_path, RunConfig()).run("")
    run_id = result["run_id"]
    artifacts_dir = tmp_path / "artifacts" / run_id / "artifacts"
    assert artifacts_dir.exists(), "Failure containment invariant violated: artifacts missing."
    assert (
        list(artifacts_dir.glob("*.json")) == []
    ), "Failure containment invariant violated: artifacts written after failure."
