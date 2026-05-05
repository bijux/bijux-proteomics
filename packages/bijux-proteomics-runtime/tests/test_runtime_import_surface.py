from __future__ import annotations

import json
from pathlib import Path

from bijux_proteomics_runtime.runs import RunManager
from bijux_proteomics_runtime.runs.import_lineage import ImportRunBundle
from bijux_proteomics_runtime.runs.import_lineage import RuntimeImportTrace
from bijux_proteomics_runtime.runs.import_lineage import load_import_run_bundle
from bijux_proteomics_runtime.runs.import_lineage import load_import_trace

from .runtime_fixture_data import load_fixture


def test_runtime_import_result_persists_trace_and_reviewable_outputs(
    tmp_path: Path,
) -> None:
    source_path = tmp_path / "external" / "dia-report.json"
    source_path.parent.mkdir(parents=True, exist_ok=True)
    source_path.write_text('{"report":"ok"}', encoding="utf-8")

    manager = RunManager(tmp_path)
    result = manager.import_result(
        sequence="MPEPTIDE",
        source_path=source_path,
        imported_payload={"peptides": ["PEPTIDE"], "engine_score": 0.91},
        engine_name="spectronaut",
        engine_version="19.0",
        run_id="runtime-import-1",
    )

    workspace_root = tmp_path / "artifacts" / "runtime-import-1"
    import_trace = RuntimeImportTrace.load_json(workspace_root / "import_trace.json")
    import_bundle = ImportRunBundle.load_json(workspace_root / "import_run_bundle.json")

    assert result["status"] == "success"
    assert import_trace.external_engine_name == "spectronaut"
    assert (
        import_trace.imported_artifacts[0].artifact_kind == "runtime-imported-evidence"
    )
    assert {artifact.artifact_kind for artifact in import_trace.derived_artifacts} >= {
        "runtime-evidence-bundle",
        "runtime-review-packet",
        "runtime-run-context",
    }
    assert import_bundle.import_trace.external_engine_version == "19.0"


def test_runtime_import_control_exports_loaders(tmp_path: Path) -> None:
    source_path = tmp_path / "external" / "dda-import.json"
    source_path.parent.mkdir(parents=True, exist_ok=True)
    source_path.write_text('{"report":"ok"}', encoding="utf-8")
    manager = RunManager(tmp_path)
    manager.import_result(
        sequence="MPEPTIDE",
        source_path=source_path,
        imported_payload={"proteins": ["P12345"]},
        engine_name="maxquant",
        engine_version="2.1.0",
        run_id="runtime-import-2",
    )

    from bijux_proteomics_runtime.runtime.workspace import RunWorkspace

    workspace = RunWorkspace.for_run(tmp_path, "runtime-import-2")
    assert isinstance(load_import_trace(workspace), RuntimeImportTrace)
    assert isinstance(load_import_run_bundle(workspace), ImportRunBundle)


def test_runtime_import_fixture_keeps_degraded_provenance_explicit(
    tmp_path: Path,
) -> None:
    fixture = load_fixture("execution", "degraded_provenance_import_review.json")
    source_path = tmp_path / "external" / str(fixture["source_filename"])
    source_path.parent.mkdir(parents=True, exist_ok=True)
    source_path.write_text(
        json.dumps(fixture["source_payload"], indent=2, sort_keys=True),
        encoding="utf-8",
    )

    manager = RunManager(tmp_path)
    result = manager.import_result(
        sequence=str(fixture["sequence"]),
        source_path=source_path,
        imported_payload=dict(fixture["source_payload"]),
        engine_name=str(fixture["engine_name"]),
        engine_version=str(fixture["engine_version"]),
        run_id="runtime-import-degraded-provenance-1",
    )

    workspace_root = tmp_path / "artifacts" / "runtime-import-degraded-provenance-1"
    imported_payload = json.loads(
        (workspace_root / "artifacts" / "imported_evidence.json").read_text(
            encoding="utf-8"
        )
    )
    import_trace = RuntimeImportTrace.load_json(workspace_root / "import_trace.json")

    assert result["status"] == "success"
    assert imported_payload["payload"]["provenance_status"] == fixture["expected_provenance_status"]
    assert imported_payload["payload"]["provenance_gaps"] == fixture["expected_provenance_gaps"]
    assert import_trace.imported_artifacts[0].artifact_kind == "runtime-imported-evidence"
    assert {artifact.artifact_kind for artifact in import_trace.derived_artifacts} >= {
        "runtime-evidence-bundle",
        "runtime-review-packet",
    }
