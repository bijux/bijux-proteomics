from __future__ import annotations

import json
from pathlib import Path

from bijux_proteomics_runtime.api.catalog import build_runtime_status_response
from bijux_proteomics_runtime.runs.import_lineage import (
    load_import_run_bundle,
    load_import_trace,
)
from bijux_proteomics_runtime.runs.integrity import load_artifact_integrity_report
from bijux_proteomics_runtime.runs.ledger import load_artifact_ledger
from bijux_proteomics_runtime.runs.replay import load_local_run_bundle
from bijux_proteomics_runtime.support.workspace import RunWorkspace
from bijux_proteomics_runtime.workflows.paths import (
    run_reviewable_import_path,
    run_reviewable_sequence_path,
)

from ..support.fixture_data import load_fixture


def _first_sequence_from_fixture() -> str:
    fixture_dir = Path(__file__).resolve().parents[1] / "fixtures" / "first_useful_run"
    lines = (fixture_dir / "proteins.fasta").read_text(encoding="utf-8").splitlines()
    return "".join(line.strip() for line in lines if line and not line.startswith(">"))


def test_runtime_local_path_publishes_reviewable_outputs_from_real_corpus(
    tmp_path: Path,
) -> None:
    manifest = run_reviewable_sequence_path(
        tmp_path,
        sequence=_first_sequence_from_fixture(),
        execution_mode="cpu",
    )
    workspace = RunWorkspace.for_run(tmp_path, manifest.run_id)
    bundle = load_local_run_bundle(workspace)
    ledger = load_artifact_ledger(workspace, manifest.run_id)
    integrity = load_artifact_integrity_report(workspace)
    status = build_runtime_status_response(tmp_path, manifest.run_id)

    assert manifest.command == "run"
    assert manifest.import_only is False
    assert set(manifest.artifact_kinds) == {
        "runtime-status",
        "runtime-report",
        "runtime-replay-contract",
        "runtime-integrity-report",
    }
    assert bundle.run_context.workflow.workflow_family == "structure_prediction"
    assert bundle.run_summary["command"] == "run"
    assert status.summary.command == "run"
    assert integrity.verified is True
    assert set(manifest.artifact_kinds).issubset(
        {entry.artifact_kind for entry in ledger.entries}
    )


def test_runtime_import_path_publishes_reviewable_import_lineage_from_fixture(
    tmp_path: Path,
) -> None:
    fixture = load_fixture("execution", "import_review_path.json")
    source_path = tmp_path / "external" / str(fixture["source_filename"])
    source_path.parent.mkdir(parents=True, exist_ok=True)
    source_path.write_text(
        json.dumps(fixture["source_payload"], indent=2, sort_keys=True),
        encoding="utf-8",
    )

    manifest = run_reviewable_import_path(
        tmp_path,
        sequence=str(fixture["sequence"]),
        source_path=source_path,
        engine_name=str(fixture["engine_name"]),
        engine_version=str(fixture["engine_version"]),
    )
    workspace = RunWorkspace.for_run(tmp_path, manifest.run_id)
    import_trace = load_import_trace(workspace)
    import_bundle = load_import_run_bundle(workspace)
    ledger = load_artifact_ledger(workspace, manifest.run_id)
    integrity = load_artifact_integrity_report(workspace)
    status = build_runtime_status_response(tmp_path, manifest.run_id)

    assert manifest.command == "import"
    assert manifest.import_only is True
    assert set(manifest.artifact_kinds) == set(fixture["expected_artifact_kinds"])
    assert import_trace.external_engine_name == fixture["engine_name"]
    assert import_trace.external_engine_version == fixture["engine_version"]
    assert import_bundle.run_context.workflow.import_only is True
    assert import_bundle.import_trace.imported_artifacts[0].artifact_kind == (
        "runtime-imported-evidence"
    )
    assert status.summary.command == "import"
    assert integrity.verified is True
    assert set(manifest.artifact_kinds).issubset(
        {entry.artifact_kind for entry in ledger.entries}
    )
