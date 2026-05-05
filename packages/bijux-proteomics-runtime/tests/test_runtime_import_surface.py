from __future__ import annotations

from pathlib import Path

from bijux_proteomics_runtime.runtime import RunManager
from bijux_proteomics_runtime.runtime.control import (
    ImportRunBundle,
    RuntimeImportTrace,
    load_import_run_bundle,
    load_import_trace,
)


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
