from __future__ import annotations

import json
from pathlib import Path

from bijux_proteomics_runtime.support.workspace import RunWorkspace
from bijux_proteomics_runtime.workflows.paths import (
    RuntimeReviewableOutputPath,
    build_runtime_smoke_workflows,
    run_reviewable_import_path,
    run_reviewable_sequence_path,
)


def _first_sequence_from_fixture() -> str:
    fixture = Path(__file__).resolve().parents[1] / "fixtures" / "first_useful_run"
    lines = (fixture / "proteins.fasta").read_text(encoding="utf-8").splitlines()
    return "".join(line.strip() for line in lines if line and not line.startswith(">"))


def test_runtime_smoke_workflows_cover_review_and_handoff_paths() -> None:
    workflows = {
        workflow.workflow_key: workflow for workflow in build_runtime_smoke_workflows()
    }

    assert tuple(workflows) == (
        "sequence_to_digest",
        "dda_import",
        "dia_import",
        "quant",
        "ptm",
        "review",
        "lab_handoff",
        "package_smoke",
    )
    assert workflows["sequence_to_digest"].steps[0].operation_name == (
        "run_reviewable_sequence_path"
    )
    assert workflows["dda_import"].steps[0].import_only is True
    assert workflows["lab_handoff"].steps[0].handoff_surface == (
        "lab_operational_follow_up"
    )
    assert workflows["package_smoke"].steps[0].operation_name == (
        "run_runtime_package_smoke_workflow"
    )


def test_runtime_useful_run_path_persists_reviewable_manifest(
    tmp_path: Path,
) -> None:
    manifest = run_reviewable_sequence_path(
        tmp_path,
        sequence=_first_sequence_from_fixture(),
        execution_mode="cpu",
    )
    workspace = RunWorkspace.for_run(tmp_path, manifest.run_id)
    persisted = RuntimeReviewableOutputPath.load_json(
        workspace.artifact_items_dir / "reviewable_run_path.json"
    )

    assert manifest.command == "run"
    assert manifest.import_only is False
    assert Path(manifest.summary_path).exists()
    assert Path(manifest.replay_contract_path).exists()
    assert Path(manifest.integrity_report_path).exists()
    assert persisted.downstream_surface == "intelligence_review"


def test_runtime_useful_import_path_persists_reviewable_manifest(
    tmp_path: Path,
) -> None:
    source_path = tmp_path / "external" / "dia-result.json"
    source_path.parent.mkdir(parents=True, exist_ok=True)
    source_path.write_text(
        json.dumps({"peptides": ["PEPTIDE"], "engine_score": 0.97}),
        encoding="utf-8",
    )

    manifest = run_reviewable_import_path(
        tmp_path,
        sequence="MPEPTIDE",
        source_path=source_path,
        engine_name="spectronaut",
        engine_version="19.0",
    )
    workspace = RunWorkspace.for_run(tmp_path, manifest.run_id)
    persisted = RuntimeReviewableOutputPath.load_json(
        workspace.artifact_items_dir / "reviewable_import_path.json"
    )

    assert manifest.command == "import"
    assert manifest.import_only is True
    assert manifest.import_trace_path is not None
    assert Path(manifest.import_trace_path).exists()
    assert Path(manifest.integrity_report_path).exists()
    assert persisted.artifact_kinds[:2] == (
        "runtime-status",
        "runtime-import-trace",
    )


def test_runtime_useful_import_path_accepts_tsv_result_sets(tmp_path: Path) -> None:
    source_path = tmp_path / "external" / "dda-result.tsv"
    source_path.parent.mkdir(parents=True, exist_ok=True)
    source_path.write_text(
        "scan_number\tsequence_with_mods\tscore_value\n"
        "mq-1\tPEPTIDE\t113.0\n"
        "mq-2\tPEPTIDER\t99.5\n",
        encoding="utf-8",
    )

    manifest = run_reviewable_import_path(
        tmp_path,
        sequence="MPEPTIDE",
        source_path=source_path,
        engine_name="maxquant",
        engine_version="19.0",
    )
    workspace = RunWorkspace.for_run(tmp_path, manifest.run_id)
    imported_payload = (
        workspace.artifact_items_dir / "imported_evidence.json"
    ).read_text(encoding="utf-8")

    assert '"row_count": 2' in imported_payload
    assert '"scan_number"' in imported_payload
