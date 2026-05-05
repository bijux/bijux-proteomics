from __future__ import annotations

from pathlib import Path

from bijux_proteomics_dev.quality.benchmark_artifacts import (
    VersionedBenchmarkSnapshot,
    compare_benchmark_snapshots,
    load_benchmark_artifact_definitions,
    validate_benchmark_artifact_definitions,
)

REPO_ROOT = Path(__file__).resolve().parents[3]


def test_benchmark_artifact_manifest_covers_each_workspace_package() -> None:
    definitions = load_benchmark_artifact_definitions(REPO_ROOT)

    assert len(definitions) == 9
    assert {definition.package_name for definition in definitions} == {
        "agentic-proteins",
        "bijux-proteomics-dev",
        "bijux-proteomics-foundation",
        "bijux-proteomics-core",
        "bijux-proteomics-runtime",
        "bijux-proteomics-intelligence",
        "bijux-proteomics-knowledge",
        "bijux-proteomics-lab",
    }
    foundation_ids = {
        definition.benchmark_id
        for definition in definitions
        if definition.package_name == "bijux-proteomics-foundation"
    }
    assert foundation_ids == {
        "foundation-canonicalization-throughput",
        "foundation-hashing-throughput",
    }


def test_benchmark_artifact_manifest_is_valid_for_current_repo() -> None:
    assert validate_benchmark_artifact_definitions(REPO_ROOT) == ()


def test_compare_benchmark_snapshots_returns_cross_version_delta() -> None:
    previous = VersionedBenchmarkSnapshot(
        benchmark_id="core-digestion-throughput",
        package_name="bijux-proteomics-core",
        package_version="0.3.5",
        metric_name="proteins_per_second",
        unit="proteins_per_second",
        value=125.0,
        provenance_sha256="a" * 64,
    )
    current = VersionedBenchmarkSnapshot(
        benchmark_id="core-digestion-throughput",
        package_name="bijux-proteomics-core",
        package_version="0.3.6",
        metric_name="proteins_per_second",
        unit="proteins_per_second",
        value=150.0,
        provenance_sha256="b" * 64,
    )

    comparison = compare_benchmark_snapshots(previous, current)

    assert comparison.delta == 25.0
    assert comparison.ratio == 1.2
