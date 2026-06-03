from __future__ import annotations

import re
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from bijux_proteomics_dev.quality.graphs.package_graph import load_workspace_packages

__all__ = [
    "ArtifactSchemaIssue",
    "HighValueArtifactSchema",
    "artifact_schema_manifest_path",
    "load_high_value_artifact_schemas",
    "validate_high_value_artifact_schemas",
]


_SEMVER_PATTERN = re.compile(r"^\d+\.\d+\.\d+$")


@dataclass(frozen=True)
class HighValueArtifactSchema:
    """One curated, versioned artifact schema for long-lived review outputs."""

    document_kind: str
    package_name: str
    schema_version: str
    contract_path: str
    rationale: str


@dataclass(frozen=True)
class ArtifactSchemaIssue:
    """One issue in the curated artifact schema registry."""

    code: str
    detail: str


def artifact_schema_manifest_path(repo_root: Path) -> Path:
    """Return the curated high-value artifact schema manifest path."""
    return (
        repo_root
        / "configs"
        / "package-governance"
        / "high-value-artifact-schemas.toml"
    )


def _load_toml(path: Path) -> dict[str, Any]:
    with path.open("rb") as handle:
        return tomllib.load(handle)


def load_high_value_artifact_schemas(
    repo_root: Path,
) -> tuple[HighValueArtifactSchema, ...]:
    """Load curated high-value artifact schemas from the governance manifest."""
    raw = _load_toml(artifact_schema_manifest_path(repo_root))
    entries = [
        HighValueArtifactSchema(
            document_kind=str(item["document_kind"]),
            package_name=str(item["package_name"]),
            schema_version=str(item["schema_version"]),
            contract_path=str(item["contract_path"]),
            rationale=str(item["rationale"]),
        )
        for item in raw["artifact_schema"]
    ]
    return tuple(entries)


def _document_kind_is_declared(repo_root: Path, entry: HighValueArtifactSchema) -> bool:
    package_dir = repo_root / "packages" / entry.package_name
    search_roots = [package_dir / "src"]
    if entry.contract_path.startswith("apis/"):
        search_roots.append(repo_root / "apis")
    patterns = (
        f'document_kind="{entry.document_kind}"',
        f'_build_document_schema("{entry.document_kind}")',
        f"document_kind='{entry.document_kind}'",
        f"_build_document_schema('{entry.document_kind}')",
    )
    for root in search_roots:
        if not root.exists():
            continue
        for path in root.rglob("*.py"):
            text = path.read_text(encoding="utf-8")
            if any(pattern in text for pattern in patterns):
                return True
    return False


def validate_high_value_artifact_schemas(
    repo_root: Path,
) -> tuple[ArtifactSchemaIssue, ...]:
    """Validate the curated registry of long-lived artifact schemas."""
    entries = load_high_value_artifact_schemas(repo_root)
    workspace_packages = {
        package.package_name for package in load_workspace_packages(repo_root)
    }
    issues: list[ArtifactSchemaIssue] = []
    seen_document_kinds: set[str] = set()

    for entry in entries:
        if entry.document_kind in seen_document_kinds:
            issues.append(
                ArtifactSchemaIssue(
                    code="duplicate-document-kind",
                    detail=f"duplicate artifact schema entry for {entry.document_kind}",
                )
            )
        seen_document_kinds.add(entry.document_kind)
        if entry.package_name not in workspace_packages:
            issues.append(
                ArtifactSchemaIssue(
                    code="unknown-package",
                    detail=f"artifact schema registry references unknown package {entry.package_name}",
                )
            )
        if not _SEMVER_PATTERN.match(entry.schema_version):
            issues.append(
                ArtifactSchemaIssue(
                    code="invalid-schema-version",
                    detail=f"{entry.document_kind} uses non-semver schema version {entry.schema_version}",
                )
            )
        if not (repo_root / entry.contract_path).exists():
            issues.append(
                ArtifactSchemaIssue(
                    code="missing-contract-path",
                    detail=f"artifact schema contract path does not exist: {entry.contract_path}",
                )
            )
        if not _document_kind_is_declared(repo_root, entry):
            issues.append(
                ArtifactSchemaIssue(
                    code="undeclared-document-kind",
                    detail=(
                        f"{entry.document_kind} is not declared under "
                        f"{entry.package_name}/src"
                    ),
                )
            )

    return tuple(sorted(issues, key=lambda issue: (issue.code, issue.detail)))
