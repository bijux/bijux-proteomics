from __future__ import annotations

from pathlib import Path

from bijux_proteomics_runtime.workflows import (
    build_benchmark_artifact_browser,
    run_benchmark_dda_import_path,
)


def test_benchmark_artifact_browser_summarizes_import_lane_outputs(
    tmp_path: Path,
) -> None:
    manifest = run_benchmark_dda_import_path(tmp_path)
    browser = build_benchmark_artifact_browser(
        tmp_path,
        package_id="dda-maxquant-pipeline-corpus",
        manifest=manifest,
    )

    assert browser.imported_results[0].summary == (
        "imported tabular comparator payload with 3 rows"
    )
    assert any(
        entry.artifact_kind == "runtime-review-packet"
        for entry in browser.handoff_outputs
    )
    assert any(
        choice.startswith("config_fingerprint=") for choice in browser.parameter_choices
    )
