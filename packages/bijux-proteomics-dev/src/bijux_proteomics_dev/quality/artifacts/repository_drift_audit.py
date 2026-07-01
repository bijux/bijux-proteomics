from __future__ import annotations

import argparse
import tomllib
from dataclasses import dataclass
from pathlib import Path

from bijux_proteomics_dev.governance.runtime.topology import REPO_ROOT
from bijux_proteomics_dev.governance.support.workspace_inventory import (
    package_root,
    workspace_package_names,
)

__all__ = [
    "REPOSITORY_DRIFT_AUDIT_PATH",
    "RepositoryDriftAuditEntry",
    "RepositoryDriftAuditIssue",
    "build_repository_drift_audit",
    "run",
    "validate_repository_drift_audit",
]


REPOSITORY_DRIFT_AUDIT_PATH = (
    REPO_ROOT / "configs" / "package-governance" / "repository-drift-audit.toml"
)
_ROOT_GOVERNANCE_DIRS = ("apis", "configs", "makes", ".github")
_ROOT_SINGLETON_DOC_BASENAMES = (
    "artifact-governance.md",
    "cross-package-ownership.md",
    "product-architecture.md",
    "release-readiness-matrix.md",
    "workspace-layout.md",
)


@dataclass(frozen=True)
class RepositoryDriftAuditEntry:
    """One drift class that must stay empty or narrowly owned."""

    audit_id: str
    purpose: str
    offending_paths: tuple[str, ...]


@dataclass(frozen=True)
class RepositoryDriftAuditIssue:
    """One repository drift failure."""

    code: str
    detail: str


def _package_names(repo_root: Path) -> tuple[str, ...]:
    if repo_root == REPO_ROOT:
        return workspace_package_names()
    packages_dir = repo_root / "packages"
    return tuple(sorted(path.name for path in packages_dir.iterdir() if path.is_dir()))


def _package_root(repo_root: Path, package_name: str) -> Path:
    if repo_root == REPO_ROOT:
        return package_root(package_name)
    return repo_root / "packages" / package_name


def build_repository_drift_audit(
    repo_root: Path = REPO_ROOT,
) -> tuple[RepositoryDriftAuditEntry, ...]:
    """Report duplicate repository-wide storage patterns under package roots."""

    governance_mirrors: list[str] = []
    benchmark_root_duplicates: list[str] = []
    singleton_doc_duplicates: list[str] = []
    package_local_artifacts: list[str] = []

    for package_name in _package_names(repo_root):
        root = _package_root(repo_root, package_name)
        for dirname in _ROOT_GOVERNANCE_DIRS:
            candidate = root / dirname
            if candidate.exists():
                governance_mirrors.append(candidate.relative_to(repo_root).as_posix())
        if package_name != "bijux-proteomics-core":
            benchmark_root = root / "benchmark-assets"
            if benchmark_root.exists():
                benchmark_root_duplicates.append(
                    benchmark_root.relative_to(repo_root).as_posix()
                )
        docs_root = root / "docs"
        if docs_root.exists():
            for basename in _ROOT_SINGLETON_DOC_BASENAMES:
                for path in docs_root.rglob(basename):
                    singleton_doc_duplicates.append(
                        path.relative_to(repo_root).as_posix()
                    )
        artifacts_root = root / "artifacts"
        if artifacts_root.exists():
            package_local_artifacts.append(
                artifacts_root.relative_to(repo_root).as_posix()
            )

    return (
        RepositoryDriftAuditEntry(
            audit_id="package-governance-mirrors",
            purpose=(
                "Package roots must not grow their own copies of repository-wide "
                "governance directories."
            ),
            offending_paths=tuple(sorted(governance_mirrors)),
        ),
        RepositoryDriftAuditEntry(
            audit_id="benchmark-root-duplicates",
            purpose=(
                "Benchmark asset roots belong to core so asset lineage keeps one durable owner."
            ),
            offending_paths=tuple(sorted(benchmark_root_duplicates)),
        ),
        RepositoryDriftAuditEntry(
            audit_id="singleton-doc-duplicates",
            purpose=(
                "Repository-wide handbook pages should not be mirrored under package docs."
            ),
            offending_paths=tuple(sorted(singleton_doc_duplicates)),
        ),
        RepositoryDriftAuditEntry(
            audit_id="package-local-artifacts",
            purpose=(
                "Package-local `artifacts/` roots blur publishable source and transient state."
            ),
            offending_paths=tuple(sorted(package_local_artifacts)),
        ),
    )


def validate_repository_drift_audit(
    repo_root: Path = REPO_ROOT,
) -> tuple[RepositoryDriftAuditIssue, ...]:
    """Fail when repository-wide ownership drifts into package-local mirrors."""

    issues: list[RepositoryDriftAuditIssue] = []
    for entry in build_repository_drift_audit(repo_root):
        for path in entry.offending_paths:
            issues.append(
                RepositoryDriftAuditIssue(
                    code=entry.audit_id,
                    detail=f"{path} duplicates a repository-wide owner surface",
                )
            )
    return tuple(sorted(issues, key=lambda issue: (issue.code, issue.detail)))


def _render_tuple(values: tuple[str, ...]) -> str:
    return ", ".join(f'"{value}"' for value in values)


def _toml_text(entries: tuple[RepositoryDriftAuditEntry, ...]) -> str:
    lines = [
        "# Generated repository drift audit.",
        "# Regenerate with: ./.venv/bin/python -m bijux_proteomics_dev.quality.artifacts.repository_drift_audit",
        "",
    ]
    for entry in entries:
        lines.extend(
            [
                "[[entry]]",
                f'audit_id = "{entry.audit_id}"',
                f'purpose = "{entry.purpose}"',
                f"offending_paths = [{_render_tuple(entry.offending_paths)}]",
                "",
            ]
        )
    return "\n".join(lines)


def _load_entries(path: Path) -> tuple[RepositoryDriftAuditEntry, ...] | None:
    if not path.exists():
        return None
    with path.open("rb") as handle:
        raw = tomllib.load(handle)
    return tuple(
        RepositoryDriftAuditEntry(
            audit_id=item["audit_id"],
            purpose=item["purpose"],
            offending_paths=tuple(item["offending_paths"]),
        )
        for item in raw.get("entry", [])
    )


def run(check: bool = False) -> int:
    entries = build_repository_drift_audit()
    issues = validate_repository_drift_audit()
    if issues:
        for issue in issues:
            print(f"{issue.code}: {issue.detail}")
        return 1
    if check:
        if _load_entries(REPOSITORY_DRIFT_AUDIT_PATH) == entries:
            print("repository drift audit is up to date")
            return 0
        print("repository drift audit is stale; regenerate it")
        return 1
    REPOSITORY_DRIFT_AUDIT_PATH.write_text(_toml_text(entries), encoding="utf-8")
    print("generated repository drift audit")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate or validate the repository drift audit."
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Fail if the repository drift audit is not up to date.",
    )
    raise SystemExit(run(check=parser.parse_args().check))
