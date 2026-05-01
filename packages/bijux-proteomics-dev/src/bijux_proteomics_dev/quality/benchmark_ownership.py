from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import tomllib
from typing import Any

from bijux_proteomics_dev.quality.package_graph import load_workspace_packages

__all__ = [
    "BenchmarkOwnerEntry",
    "BenchmarkOwnershipIssue",
    "benchmark_owner_manifest_path",
    "load_benchmark_owners",
    "validate_benchmark_owners",
]


@dataclass(frozen=True)
class BenchmarkOwnerEntry:
    """One package-specific benchmark ownership declaration."""

    package_name: str
    focus_path: str
    declaration_path: str
    rationale: str


@dataclass(frozen=True)
class BenchmarkOwnershipIssue:
    """One benchmark ownership manifest issue."""

    code: str
    detail: str


def benchmark_owner_manifest_path(repo_root: Path) -> Path:
    """Return the benchmark owner manifest path."""
    return repo_root / "configs" / "package-governance" / "benchmark-owners.toml"


def _load_toml(path: Path) -> dict[str, Any]:
    with path.open("rb") as handle:
        return tomllib.load(handle)


def load_benchmark_owners(repo_root: Path) -> tuple[BenchmarkOwnerEntry, ...]:
    """Load package benchmark owner declarations."""
    raw = _load_toml(benchmark_owner_manifest_path(repo_root))
    entries = [
        BenchmarkOwnerEntry(
            package_name=str(item["package_name"]),
            focus_path=str(item["focus_path"]),
            declaration_path=str(item["declaration_path"]),
            rationale=str(item["rationale"]),
        )
        for item in raw["owner"]
    ]
    return tuple(entries)


def validate_benchmark_owners(repo_root: Path) -> tuple[BenchmarkOwnershipIssue, ...]:
    """Validate package-specific benchmark ownership declarations."""
    entries = load_benchmark_owners(repo_root)
    workspace_packages = {
        package.package_name for package in load_workspace_packages(repo_root)
    }
    issues: list[BenchmarkOwnershipIssue] = []
    seen: set[str] = set()
    for entry in entries:
        if entry.package_name in seen:
            issues.append(
                BenchmarkOwnershipIssue(
                    code="duplicate-package-owner",
                    detail=f"duplicate benchmark owner entry for {entry.package_name}",
                )
            )
        seen.add(entry.package_name)
        if entry.package_name not in workspace_packages:
            issues.append(
                BenchmarkOwnershipIssue(
                    code="unknown-package",
                    detail=f"benchmark owner manifest references unknown package {entry.package_name}",
                )
            )
        if not (repo_root / entry.focus_path).exists():
            issues.append(
                BenchmarkOwnershipIssue(
                    code="missing-focus-path",
                    detail=f"benchmark focus path does not exist: {entry.focus_path}",
                )
            )
        if not (repo_root / entry.declaration_path).exists():
            issues.append(
                BenchmarkOwnershipIssue(
                    code="missing-declaration-path",
                    detail=f"benchmark declaration path does not exist: {entry.declaration_path}",
                )
            )
    missing_packages = sorted(workspace_packages - seen)
    if missing_packages:
        issues.append(
            BenchmarkOwnershipIssue(
                code="missing-package-owner",
                detail=f"packages missing benchmark owner entries: {missing_packages}",
            )
        )
    return tuple(sorted(issues, key=lambda issue: (issue.code, issue.detail)))
