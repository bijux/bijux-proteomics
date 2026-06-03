from __future__ import annotations

import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from bijux_proteomics_dev.quality.benchmarks.benchmark_ownership import (
    load_benchmark_owners,
)
from bijux_proteomics_dev.quality.graphs.package_graph import load_workspace_packages

__all__ = [
    "BenchmarkArtifactComparison",
    "BenchmarkArtifactDefinition",
    "BenchmarkArtifactIssue",
    "VersionedBenchmarkSnapshot",
    "benchmark_artifact_manifest_path",
    "compare_benchmark_snapshots",
    "load_benchmark_artifact_definitions",
    "validate_benchmark_artifact_definitions",
]


@dataclass(frozen=True)
class BenchmarkArtifactDefinition:
    """One benchmark artifact that stays comparable across package versions."""

    benchmark_id: str
    package_name: str
    metric_name: str
    unit: str
    owner_focus_path: str


@dataclass(frozen=True)
class BenchmarkArtifactIssue:
    """One issue in the versioned benchmark artifact registry."""

    code: str
    detail: str


@dataclass(frozen=True)
class VersionedBenchmarkSnapshot:
    """One versioned benchmark snapshot for cross-version comparison."""

    benchmark_id: str
    package_name: str
    package_version: str
    metric_name: str
    unit: str
    value: float
    provenance_sha256: str


@dataclass(frozen=True)
class BenchmarkArtifactComparison:
    """Cross-version comparison over one declared benchmark artifact."""

    benchmark_id: str
    package_name: str
    previous_version: str
    current_version: str
    metric_name: str
    unit: str
    delta: float
    ratio: float
    comparable: bool


def benchmark_artifact_manifest_path(repo_root: Path) -> Path:
    """Return the benchmark artifact manifest path."""
    return repo_root / "configs" / "package-governance" / "benchmark-artifacts.toml"


def _load_toml(path: Path) -> dict[str, Any]:
    with path.open("rb") as handle:
        return tomllib.load(handle)


def load_benchmark_artifact_definitions(
    repo_root: Path,
) -> tuple[BenchmarkArtifactDefinition, ...]:
    """Load the versioned benchmark artifact registry."""
    raw = _load_toml(benchmark_artifact_manifest_path(repo_root))
    return tuple(
        BenchmarkArtifactDefinition(
            benchmark_id=str(item["benchmark_id"]),
            package_name=str(item["package_name"]),
            metric_name=str(item["metric_name"]),
            unit=str(item["unit"]),
            owner_focus_path=str(item["owner_focus_path"]),
        )
        for item in raw["benchmark_artifact"]
    )


def validate_benchmark_artifact_definitions(
    repo_root: Path,
) -> tuple[BenchmarkArtifactIssue, ...]:
    """Validate declared benchmark artifacts against current workspace ownership."""
    definitions = load_benchmark_artifact_definitions(repo_root)
    workspace_packages = {
        package.package_name for package in load_workspace_packages(repo_root)
    }
    owner_focus_paths = {
        (entry.package_name, entry.focus_path)
        for entry in load_benchmark_owners(repo_root)
    }
    issues: list[BenchmarkArtifactIssue] = []
    seen_ids: set[str] = set()

    for definition in definitions:
        if definition.benchmark_id in seen_ids:
            issues.append(
                BenchmarkArtifactIssue(
                    code="duplicate-benchmark-id",
                    detail=f"duplicate benchmark artifact id {definition.benchmark_id}",
                )
            )
        seen_ids.add(definition.benchmark_id)
        if definition.package_name not in workspace_packages:
            issues.append(
                BenchmarkArtifactIssue(
                    code="unknown-package",
                    detail=f"benchmark artifact registry references unknown package {definition.package_name}",
                )
            )
        if (
            definition.package_name,
            definition.owner_focus_path,
        ) not in owner_focus_paths:
            issues.append(
                BenchmarkArtifactIssue(
                    code="owner-focus-mismatch",
                    detail=(
                        f"benchmark artifact {definition.benchmark_id} does not match a benchmark owner "
                        f"focus path for {definition.package_name}"
                    ),
                )
            )
        if not (repo_root / definition.owner_focus_path).exists():
            issues.append(
                BenchmarkArtifactIssue(
                    code="missing-focus-path",
                    detail=f"benchmark artifact focus path does not exist: {definition.owner_focus_path}",
                )
            )
    return tuple(sorted(issues, key=lambda issue: (issue.code, issue.detail)))


def compare_benchmark_snapshots(
    previous: VersionedBenchmarkSnapshot,
    current: VersionedBenchmarkSnapshot,
) -> BenchmarkArtifactComparison:
    """Compare two versioned benchmark snapshots for the same declared artifact."""
    comparable = (
        previous.benchmark_id == current.benchmark_id
        and previous.package_name == current.package_name
        and previous.metric_name == current.metric_name
        and previous.unit == current.unit
    )
    if not comparable:
        raise ValueError("benchmark snapshots must share id, package, metric, and unit")
    if previous.provenance_sha256 == current.provenance_sha256:
        ratio = 1.0
    elif previous.value == 0:
        ratio = float("inf")
    else:
        ratio = round(current.value / previous.value, 6)
    return BenchmarkArtifactComparison(
        benchmark_id=previous.benchmark_id,
        package_name=previous.package_name,
        previous_version=previous.package_version,
        current_version=current.package_version,
        metric_name=previous.metric_name,
        unit=previous.unit,
        delta=round(current.value - previous.value, 6),
        ratio=ratio,
        comparable=True,
    )
