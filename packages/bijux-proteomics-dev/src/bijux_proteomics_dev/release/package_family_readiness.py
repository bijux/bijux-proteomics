from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import tomllib
from typing import Any

from bijux_proteomics_dev.quality.package_graph import load_workspace_packages

__all__ = [
    "PackageFamilyReadinessEntry",
    "PackageFamilyReadinessIssue",
    "build_package_family_readiness_reports",
    "package_family_readiness_manifest_path",
    "validate_package_family_readiness",
]


@dataclass(frozen=True)
class PackageFamilyReadinessEntry:
    """One release-readiness family declaration across multiple packages."""

    family_id: str
    package_names: tuple[str, ...]
    evidence_paths: tuple[str, ...]
    rationale: str


@dataclass(frozen=True)
class PackageFamilyReadinessIssue:
    """One issue in the package-family readiness declaration."""

    code: str
    detail: str


@dataclass(frozen=True)
class PackageFamilyReadinessReport:
    """Readiness evidence summary for one package family."""

    family_id: str
    package_count: int
    evidence_count: int
    ready: bool
    missing_paths: tuple[str, ...]


def package_family_readiness_manifest_path(repo_root: Path) -> Path:
    """Return the package-family readiness manifest path."""
    return repo_root / "configs" / "package-governance" / "release-families.toml"


def _load_toml(path: Path) -> dict[str, Any]:
    with path.open("rb") as handle:
        return tomllib.load(handle)


def _load_package_family_entries(
    repo_root: Path,
) -> tuple[PackageFamilyReadinessEntry, ...]:
    raw = _load_toml(package_family_readiness_manifest_path(repo_root))
    return tuple(
        PackageFamilyReadinessEntry(
            family_id=str(item["family_id"]),
            package_names=tuple(str(value) for value in item["package_names"]),
            evidence_paths=tuple(str(value) for value in item["evidence_paths"]),
            rationale=str(item["rationale"]),
        )
        for item in raw["family"]
    )


def build_package_family_readiness_reports(
    repo_root: Path,
) -> tuple[PackageFamilyReadinessReport, ...]:
    """Build readiness evidence summaries across declared package families."""
    reports = []
    for entry in _load_package_family_entries(repo_root):
        missing_paths = tuple(
            path for path in entry.evidence_paths if not (repo_root / path).exists()
        )
        reports.append(
            PackageFamilyReadinessReport(
                family_id=entry.family_id,
                package_count=len(entry.package_names),
                evidence_count=len(entry.evidence_paths),
                ready=not missing_paths,
                missing_paths=missing_paths,
            )
        )
    return tuple(reports)


def validate_package_family_readiness(
    repo_root: Path,
) -> tuple[PackageFamilyReadinessIssue, ...]:
    """Validate release-readiness evidence coverage across package families."""
    entries = _load_package_family_entries(repo_root)
    workspace_packages = {
        package.package_name for package in load_workspace_packages(repo_root)
    }
    issues: list[PackageFamilyReadinessIssue] = []
    seen_families: set[str] = set()
    covered_packages: set[str] = set()

    for entry in entries:
        if entry.family_id in seen_families:
            issues.append(
                PackageFamilyReadinessIssue(
                    code="duplicate-family-id",
                    detail=f"duplicate release family entry for {entry.family_id}",
                )
            )
        seen_families.add(entry.family_id)
        for package_name in entry.package_names:
            if package_name not in workspace_packages:
                issues.append(
                    PackageFamilyReadinessIssue(
                        code="unknown-package",
                        detail=f"release family {entry.family_id} references unknown package {package_name}",
                    )
                )
            covered_packages.add(package_name)
        for path in entry.evidence_paths:
            if not (repo_root / path).exists():
                issues.append(
                    PackageFamilyReadinessIssue(
                        code="missing-evidence-path",
                        detail=f"release family {entry.family_id} is missing readiness evidence path {path}",
                    )
                )
            if path.endswith(("/index.md", ".md")):
                continue
            if not path.endswith((".yaml", ".toml", ".py")):
                issues.append(
                    PackageFamilyReadinessIssue(
                        code="unsupported-evidence-path",
                        detail=f"release family {entry.family_id} uses unsupported evidence path {path}",
                    )
                )

    missing_packages = tuple(sorted(workspace_packages - covered_packages))
    if missing_packages:
        issues.append(
            PackageFamilyReadinessIssue(
                code="missing-package-coverage",
                detail=(
                    "workspace packages missing release family coverage: "
                    f"{list(missing_packages)}"
                ),
            )
        )
    return tuple(sorted(issues, key=lambda issue: (issue.code, issue.detail)))
