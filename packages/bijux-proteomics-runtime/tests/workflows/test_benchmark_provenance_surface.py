from __future__ import annotations

from pathlib import Path

from bijux_proteomics_runtime.workflows import (
    build_benchmark_execution_cost_report,
    build_benchmark_run_provenance_report,
    run_benchmark_dda_import_path,
    run_benchmark_dia_import_path,
)


def test_benchmark_run_provenance_report_records_input_and_artifact_digests(
    tmp_path: Path,
) -> None:
    manifest = run_benchmark_dia_import_path(tmp_path)
    report = build_benchmark_run_provenance_report(
        tmp_path,
        package_id="dia-diann-pipeline-corpus",
        manifest=manifest,
    )

    assert report.external_engine_name == "dia-nn"
    assert report.external_engine_version == "2.1.0"
    assert len(report.input_digests) == 3
    assert any(
        digest.label == "runtime-import-trace" for digest in report.artifact_digests
    )


def test_benchmark_execution_cost_report_records_runtime_cost_and_sizes(
    tmp_path: Path,
) -> None:
    manifest = run_benchmark_dda_import_path(tmp_path)
    report = build_benchmark_execution_cost_report(
        tmp_path,
        package_id="dda-maxquant-pipeline-corpus",
        manifest=manifest,
    )

    assert report.wall_time_ms > 0.0
    assert report.total_artifact_bytes > 0
    assert report.largest_artifacts
    assert "run_total_ms" in report.critical_bottlenecks
