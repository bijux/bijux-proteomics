from __future__ import annotations

from pathlib import Path

from bijux_proteomics_runtime.support.workspace import RunWorkspace
from bijux_proteomics_runtime.workflows import (
    build_benchmark_run_specs,
    build_benchmark_runtime_truth_surface,
    run_benchmark_dda_import_path,
    run_benchmark_dia_import_path,
    run_benchmark_sequence_path,
)


def test_benchmark_run_specs_keep_real_runtime_packages_visible() -> None:
    specs = {spec.package_id: spec for spec in build_benchmark_run_specs()}

    assert tuple(specs) == (
        "sequence-first-useful-corpus",
        "dda-maxquant-pipeline-corpus",
        "dia-diann-pipeline-corpus",
    )
    assert specs["sequence-first-useful-corpus"].run_mode.value == "raw_executable"
    assert specs["dda-maxquant-pipeline-corpus"].engine_name == "maxquant"
    assert any(
        path.endswith("public_benchmark_packages/dda_reviewable_run/package_manifest.json")
        for path in specs["dda-maxquant-pipeline-corpus"].public_package_paths
    )
    assert specs["dia-diann-pipeline-corpus"].engine_version == "2.1.0"
    assert any(
        path.endswith("public_benchmark_packages/dia_library_review_package/package_manifest.json")
        for path in specs["dia-diann-pipeline-corpus"].public_package_paths
    )


def test_run_benchmark_sequence_path_executes_real_runtime_path(tmp_path: Path) -> None:
    manifest = run_benchmark_sequence_path(tmp_path)

    assert manifest.command == "run"
    assert manifest.import_only is False
    assert manifest.workflow_family == "sequence_to_digest"
    assert Path(manifest.summary_path).exists()
    assert Path(manifest.integrity_report_path).exists()


def test_run_benchmark_import_paths_ingest_real_comparator_tables(
    tmp_path: Path,
) -> None:
    dda_manifest = run_benchmark_dda_import_path(tmp_path / "dda")
    dia_manifest = run_benchmark_dia_import_path(tmp_path / "dia")

    dda_workspace = RunWorkspace.for_run(tmp_path / "dda", dda_manifest.run_id)
    dia_workspace = RunWorkspace.for_run(tmp_path / "dia", dia_manifest.run_id)
    dda_payload = (
        dda_workspace.artifact_items_dir / "imported_evidence.json"
    ).read_text(encoding="utf-8")
    dia_payload = (
        dia_workspace.artifact_items_dir / "imported_evidence.json"
    ).read_text(encoding="utf-8")

    assert '"row_count": 3' in dda_payload
    assert '"scan_number"' in dda_payload
    assert '"row_count": 3' in dia_payload
    assert '"precursor_id"' in dia_payload


def test_benchmark_runtime_truth_surface_stays_honest_about_blocked_families() -> None:
    rows = {row.workflow_family: row for row in build_benchmark_runtime_truth_surface()}

    assert rows["sequence_to_digest"].run_mode.value == "raw_executable"
    assert rows["dda_import"].externally_cross_checked is True
    assert rows["dia_import"].artifact_browser_ready is True
    assert rows["quant_review"].run_mode.value == "blocked"
    assert rows["ptm_review"].run_mode.value == "blocked"
