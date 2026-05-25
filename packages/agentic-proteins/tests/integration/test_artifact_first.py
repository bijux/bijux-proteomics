# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

import json
from pathlib import Path

from agentic_proteins.orchestration.artifacts import load_artifact
from agentic_proteins.orchestration.manager import RunManager
from agentic_proteins.state.workspace import RunWorkspace
from agentic_proteins_testsupport.artifacts import assert_valid_run_artifacts


def test_state_snapshot_roundtrip_from_artifacts(tmp_path: Path) -> None:
    manager = RunManager(tmp_path)
    result = manager.run("ACDE")
    workspace = RunWorkspace.for_run(tmp_path, result["run_id"])

    assert_valid_run_artifacts(workspace.run_dir)
    state_payload = json.loads(workspace.state_path.read_text())
    artifacts = state_payload.get("artifacts", [])
    assert artifacts

    report_artifact = next(item for item in artifacts if item["kind"] == "report")
    report_payload = load_artifact(workspace, report_artifact["artifact_id"])
    stored_report = json.loads(workspace.report_path.read_text())
    assert report_payload == stored_report
