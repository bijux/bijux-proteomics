from __future__ import annotations

from pathlib import Path

from bijux_proteomics_runtime.workflows import (
    build_benchmark_portability_check,
    run_benchmark_dia_import_path,
)


def test_benchmark_portability_check_keeps_semantics_across_two_environments(
    tmp_path: Path,
) -> None:
    primary_manifest = run_benchmark_dia_import_path(tmp_path / "primary")
    secondary_manifest = run_benchmark_dia_import_path(tmp_path / "secondary")
    portability = build_benchmark_portability_check(
        tmp_path / "primary",
        package_id="dia-diann-pipeline-corpus",
        primary_manifest=primary_manifest,
        secondary_base_dir=tmp_path / "secondary",
        secondary_manifest=secondary_manifest,
    )

    assert portability.semantic_signature_match is True
    assert "run_id" in portability.environment_specific_differences
