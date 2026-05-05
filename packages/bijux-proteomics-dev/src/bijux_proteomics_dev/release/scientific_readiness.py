from __future__ import annotations

from dataclasses import dataclass
import importlib
from pathlib import Path
import tomllib
from typing import Any

from bijux_proteomics_knowledge.references.benchmarks import KnowledgeWorkflowFamily
from bijux_proteomics_knowledge.references.workflow_queries import (
    get_benchmark_manifest,
)
from bijux_proteomics_dev.quality.package_graph import load_workspace_packages
from bijux_proteomics_dev.release.ssot_readiness import validate_ssot_readiness

__all__ = [
    "ScientificReleaseDossierEntry",
    "ScientificReleaseIssue",
    "ScientificReleaseWorkflowEntry",
    "build_scientific_release_dossier",
    "scientific_release_manifest_path",
    "validate_scientific_release_dossier",
]


@dataclass(frozen=True)
class ScientificReleaseWorkflowEntry:
    """One workflow-specific release-readiness declaration."""

    workflow_family: KnowledgeWorkflowFamily
    owner_package: str
    benchmark_id: str
    builder_module: str
    builder_symbol: str
    source_path: str
    test_path: str
    docs_path: str
    scientific_limit_summary: str


@dataclass(frozen=True)
class ScientificReleaseDossierEntry:
    """Reviewer-facing index entry for one benchmark-backed workflow family."""

    workflow_family: KnowledgeWorkflowFamily
    owner_package: str
    benchmark_id: str
    dataset_locator: str
    builder_locator: str
    source_path: str
    test_path: str
    docs_path: str
    scientific_limit_summary: str
    ready: bool


@dataclass(frozen=True)
class ScientificReleaseIssue:
    """One release-readiness issue for the scientific workflow dossier."""

    code: str
    detail: str


def scientific_release_manifest_path(repo_root: Path) -> Path:
    """Return the checked-in scientific release dossier manifest path."""

    return (
        repo_root
        / "configs"
        / "package-governance"
        / "scientific-release-workflows.toml"
    )


def _load_toml(path: Path) -> dict[str, Any]:
    with path.open("rb") as handle:
        return tomllib.load(handle)


def _load_entries(repo_root: Path) -> tuple[ScientificReleaseWorkflowEntry, ...]:
    raw = _load_toml(scientific_release_manifest_path(repo_root))
    return tuple(
        ScientificReleaseWorkflowEntry(
            workflow_family=KnowledgeWorkflowFamily(str(item["workflow_family"])),
            owner_package=str(item["owner_package"]),
            benchmark_id=str(item["benchmark_id"]),
            builder_module=str(item["builder_module"]),
            builder_symbol=str(item["builder_symbol"]),
            source_path=str(item["source_path"]),
            test_path=str(item["test_path"]),
            docs_path=str(item["docs_path"]),
            scientific_limit_summary=str(item["scientific_limit_summary"]),
        )
        for item in raw["workflow"]
    )


def _builder_exists(entry: ScientificReleaseWorkflowEntry) -> bool:
    module = importlib.import_module(entry.builder_module)
    symbol = getattr(module, entry.builder_symbol, None)
    return callable(symbol)


def _summary_is_vague(summary: str) -> bool:
    lowered = summary.lower()
    banned_phrases = (
        "todo",
        "tbd",
        "placeholder",
        "full parity",
        "complete suite",
        "production-ready",
        "hand-wavy",
        "toy",
    )
    return any(phrase in lowered for phrase in banned_phrases)


def build_scientific_release_dossier(
    repo_root: Path,
) -> tuple[ScientificReleaseDossierEntry, ...]:
    """Build a reviewer-facing dossier over benchmark-backed workflow coverage."""

    ssot_ready = not validate_ssot_readiness(repo_root)
    entries = []
    for entry in _load_entries(repo_root):
        manifest = get_benchmark_manifest(entry.benchmark_id)
        dataset_locator = manifest.dataset_locator if manifest is not None else ""
        paths_exist = all(
            (repo_root / path).exists()
            for path in (entry.source_path, entry.test_path, entry.docs_path)
        )
        ready = (
            manifest is not None
            and paths_exist
            and _builder_exists(entry)
            and not _summary_is_vague(entry.scientific_limit_summary)
            and ssot_ready
        )
        entries.append(
            ScientificReleaseDossierEntry(
                workflow_family=entry.workflow_family,
                owner_package=entry.owner_package,
                benchmark_id=entry.benchmark_id,
                dataset_locator=dataset_locator,
                builder_locator=f"{entry.builder_module}.{entry.builder_symbol}",
                source_path=entry.source_path,
                test_path=entry.test_path,
                docs_path=entry.docs_path,
                scientific_limit_summary=entry.scientific_limit_summary,
                ready=ready,
            )
        )
    return tuple(sorted(entries, key=lambda item: item.workflow_family.value))


def validate_scientific_release_dossier(
    repo_root: Path,
) -> tuple[ScientificReleaseIssue, ...]:
    """Validate the scientific release dossier against live code and manifests."""

    entries = _load_entries(repo_root)
    workspace_packages = {
        package.package_name for package in load_workspace_packages(repo_root)
    }
    issues: list[ScientificReleaseIssue] = []
    seen_families: set[KnowledgeWorkflowFamily] = set()
    for entry in entries:
        if entry.workflow_family in seen_families:
            issues.append(
                ScientificReleaseIssue(
                    code="duplicate-workflow-family",
                    detail=f"duplicate scientific release entry for {entry.workflow_family.value}",
                )
            )
        seen_families.add(entry.workflow_family)
        if entry.owner_package not in workspace_packages:
            issues.append(
                ScientificReleaseIssue(
                    code="unknown-owner-package",
                    detail=f"scientific release entry references unknown package {entry.owner_package}",
                )
            )
        manifest = get_benchmark_manifest(entry.benchmark_id)
        if manifest is None:
            issues.append(
                ScientificReleaseIssue(
                    code="unknown-benchmark-id",
                    detail=f"scientific release entry references unknown benchmark {entry.benchmark_id}",
                )
            )
        elif manifest.workflow_family is not entry.workflow_family:
            issues.append(
                ScientificReleaseIssue(
                    code="workflow-benchmark-mismatch",
                    detail=(
                        f"workflow {entry.workflow_family.value} references benchmark "
                        f"{entry.benchmark_id} with family {manifest.workflow_family.value}"
                    ),
                )
            )
        for path_label, relative_path in (
            ("source", entry.source_path),
            ("test", entry.test_path),
            ("docs", entry.docs_path),
        ):
            if not (repo_root / relative_path).exists():
                issues.append(
                    ScientificReleaseIssue(
                        code=f"missing-{path_label}-path",
                        detail=f"scientific release entry is missing {path_label} path {relative_path}",
                    )
                )
        if not _builder_exists(entry):
            issues.append(
                ScientificReleaseIssue(
                    code="missing-builder",
                    detail=(
                        "scientific release entry references missing builder "
                        f"{entry.builder_module}.{entry.builder_symbol}"
                    ),
                )
            )
        if not entry.scientific_limit_summary.strip():
            issues.append(
                ScientificReleaseIssue(
                    code="blank-limit-summary",
                    detail=f"scientific release entry for {entry.workflow_family.value} has a blank limit summary",
                )
            )
        if _summary_is_vague(entry.scientific_limit_summary):
            issues.append(
                ScientificReleaseIssue(
                    code="vague-limit-summary",
                    detail=(
                        f"scientific release entry for {entry.workflow_family.value} uses vague release language"
                    ),
                )
            )
    missing_families = sorted(
        family.value
        for family in KnowledgeWorkflowFamily
        if family not in seen_families
    )
    if missing_families:
        issues.append(
            ScientificReleaseIssue(
                code="missing-workflow-family",
                detail=f"scientific release dossier is missing workflow families: {missing_families}",
            )
        )
    for issue in validate_ssot_readiness(repo_root):
        issues.append(
            ScientificReleaseIssue(
                code="ssot-readiness-blocked",
                detail=(
                    "scientific release dossier is blocked until SSOT readiness is clean: "
                    f"{issue.code}: {issue.detail}"
                ),
            )
        )
    return tuple(sorted(issues, key=lambda issue: (issue.code, issue.detail)))
