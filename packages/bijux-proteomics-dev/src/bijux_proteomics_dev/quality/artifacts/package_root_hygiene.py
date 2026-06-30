from __future__ import annotations

import argparse
import shutil
from dataclasses import dataclass
from pathlib import Path

from bijux_proteomics_dev.governance.runtime.topology import REPO_ROOT
from bijux_proteomics_dev.governance.support.workspace_inventory import (
    workspace_package_names,
)
from bijux_proteomics_dev.tools.cache_hygiene import (
    find_forbidden_cache_dirs,
    purge_forbidden_cache_dirs,
)

__all__ = [
    "FORBIDDEN_PACKAGE_ROOT_SPILLOVER",
    "PackageRootHygieneIssue",
    "PackageRootHygieneReportEntry",
    "build_package_root_hygiene_report",
    "run",
    "validate_package_root_hygiene",
]


FORBIDDEN_PACKAGE_ROOT_SPILLOVER = (
    "artifacts",
    ".venv",
    ".hypothesis",
    ".benchmarks",
    ".coverage",
    "coverage.xml",
    "htmlcov",
    "build",
    "dist",
    "site",
)


@dataclass(frozen=True)
class PackageRootHygieneReportEntry:
    """One publishable package root and the transient state it still carries."""

    distribution_name: str
    cache_paths: tuple[str, ...]
    spillover_paths: tuple[str, ...]


@dataclass(frozen=True)
class PackageRootHygieneIssue:
    """One package-root hygiene failure."""

    code: str
    detail: str


def _package_names(repo_root: Path) -> tuple[str, ...]:
    if repo_root == REPO_ROOT:
        return workspace_package_names()
    packages_dir = repo_root / "packages"
    return tuple(sorted(path.name for path in packages_dir.iterdir() if path.is_dir()))


def build_package_root_hygiene_report(
    repo_root: Path = REPO_ROOT,
    *,
    purge_transient_caches: bool = False,
) -> tuple[PackageRootHygieneReportEntry, ...]:
    """Inspect publishable package roots for cache spillover and transient state."""

    entries: list[PackageRootHygieneReportEntry] = []
    for package_name in _package_names(repo_root):
        root = repo_root / "packages" / package_name
        if purge_transient_caches:
            purge_forbidden_cache_dirs(root)
            purge_forbidden_package_root_spillover(root)
        cache_paths = tuple(
            path.relative_to(repo_root).as_posix()
            for path in find_forbidden_cache_dirs(root)
        )
        spillover_paths = tuple(
            sorted(
                (root / relative_path).relative_to(repo_root).as_posix()
                for relative_path in FORBIDDEN_PACKAGE_ROOT_SPILLOVER
                if (root / relative_path).exists()
            )
        )
        entries.append(
            PackageRootHygieneReportEntry(
                distribution_name=package_name,
                cache_paths=cache_paths,
                spillover_paths=spillover_paths,
            )
        )
    return tuple(entries)


def purge_forbidden_package_root_spillover(root: Path) -> tuple[Path, ...]:
    """Remove forbidden top-level package-root spillover paths."""

    removed: list[Path] = []
    for relative_path in FORBIDDEN_PACKAGE_ROOT_SPILLOVER:
        candidate = root / relative_path
        if candidate.is_symlink() or candidate.is_file():
            candidate.unlink()
            removed.append(candidate)
            continue
        if candidate.is_dir():
            shutil.rmtree(candidate)
            removed.append(candidate)
    return tuple(removed)


def validate_package_root_hygiene(
    repo_root: Path = REPO_ROOT,
    *,
    purge_transient_caches: bool = True,
) -> tuple[PackageRootHygieneIssue, ...]:
    """Fail when publishable package roots still hold transient execution state."""

    issues: list[PackageRootHygieneIssue] = []
    for entry in build_package_root_hygiene_report(
        repo_root,
        purge_transient_caches=purge_transient_caches,
    ):
        for path in entry.cache_paths:
            issues.append(
                PackageRootHygieneIssue(
                    code="package-cache-spillover",
                    detail=(
                        f"{entry.distribution_name} still contains forbidden cache "
                        f"state at {path}"
                    ),
                )
            )
        for path in entry.spillover_paths:
            issues.append(
                PackageRootHygieneIssue(
                    code="package-root-spillover",
                    detail=(
                        f"{entry.distribution_name} still contains forbidden root "
                        f"output at {path}"
                    ),
                )
            )
    return tuple(sorted(issues, key=lambda issue: (issue.code, issue.detail)))


def run(repo_root: Path = REPO_ROOT) -> int:
    """Print package-root hygiene issues and return a process status."""

    issues = validate_package_root_hygiene(repo_root)
    if not issues:
        print("package root hygiene is clean")
        return 0
    for issue in issues:
        print(f"{issue.code}: {issue.detail}")
    return 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Validate package-root hygiene for publishable packages."
    )
    raise SystemExit(run())
