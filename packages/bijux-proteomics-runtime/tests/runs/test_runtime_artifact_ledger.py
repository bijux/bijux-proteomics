from __future__ import annotations

import json
from pathlib import Path

from bijux_proteomics_runtime.runs import create_run_context
from bijux_proteomics_runtime.runs.artifacts import write_artifact
from bijux_proteomics_runtime.runs.ledger import (
    RuntimeArtifactLedger,
    load_artifact_ledger,
    refresh_runtime_artifact_ledger,
)
from bijux_proteomics_runtime.support.workspace import write_json_atomic


def test_runtime_artifact_ledger_records_top_level_outputs_and_items(
    tmp_path: Path,
) -> None:
    context, _ = create_run_context(tmp_path, run_id="ledger-run-1")
    write_json_atomic(context.workspace.run_summary_path, {"run_id": context.run_id})
    write_json_atomic(context.workspace.run_output_path, {"run_id": context.run_id})
    write_artifact(
        context.workspace,
        "review_packet",
        {"packet_id": "review-1"},
        description="review packet",
    )

    ledger = refresh_runtime_artifact_ledger(
        context.workspace,
        run_id=context.run_id,
        artifact_policy=context.artifact_policy,
        producer="test",
    )

    assert isinstance(ledger, RuntimeArtifactLedger)
    kinds = {entry.artifact_kind for entry in ledger.entries}
    assert "runtime-config" in kinds
    assert "runtime-status" in kinds
    assert "runtime-output" in kinds
    assert "runtime-artifact-item" in kinds


def test_runtime_artifact_ledger_entries_keep_hash_path_producer_and_retention(
    tmp_path: Path,
) -> None:
    context, _ = create_run_context(tmp_path, run_id="ledger-run-2")
    payload = {"state": "ready", "score": 0.9}
    write_json_atomic(context.workspace.state_path, payload)

    ledger = refresh_runtime_artifact_ledger(
        context.workspace,
        run_id=context.run_id,
        artifact_policy=context.artifact_policy,
        producer="test",
    )
    entry = next(
        item for item in ledger.entries if item.artifact_kind == "runtime-state"
    )

    assert entry.path.endswith("state.json")
    assert entry.producer == "test"
    assert entry.retention_class.value == "transient"
    assert entry.content_sha256
    assert entry.size_bytes == len(
        json.dumps(payload, indent=2, sort_keys=True).encode("utf-8")
    )


def test_runtime_artifact_ledger_can_reload_from_disk(tmp_path: Path) -> None:
    context, _ = create_run_context(tmp_path, run_id="ledger-run-3")
    write_json_atomic(context.workspace.report_path, {"report": "ok"})
    refresh_runtime_artifact_ledger(
        context.workspace,
        run_id=context.run_id,
        artifact_policy=context.artifact_policy,
        producer="test",
    )

    reloaded = load_artifact_ledger(context.workspace, context.run_id)

    assert reloaded.run_id == context.run_id
    assert any(item.artifact_kind == "runtime-report" for item in reloaded.entries)
