from __future__ import annotations

import argparse
import tomllib
from dataclasses import dataclass
from pathlib import Path

from bijux_proteomics_dev.governance.runtime.topology import REPO_ROOT

__all__ = [
    "REPOSITORY_FILE_OWNERSHIP_PATH",
    "RepositoryFileOwnershipArea",
    "RepositoryFileOwnershipIssue",
    "build_repository_file_ownership_matrix",
    "run",
    "validate_repository_file_ownership_matrix",
]


REPOSITORY_FILE_OWNERSHIP_PATH = (
    REPO_ROOT / "configs" / "package-governance" / "repository-file-ownership.toml"
)


@dataclass(frozen=True)
class RepositoryFileOwnershipArea:
    """One durable repository area and its owning storage rule."""

    area_id: str
    owner_surface: str
    purpose: str
    path_rules: tuple[str, ...]
    anchor_paths: tuple[str, ...]
    prohibited_alternates: tuple[str, ...]
    cleanup_commands: tuple[str, ...]


@dataclass(frozen=True)
class RepositoryFileOwnershipIssue:
    """One repository file-ownership matrix failure."""

    code: str
    detail: str


def build_repository_file_ownership_matrix() -> tuple[RepositoryFileOwnershipArea, ...]:
    """Return the repository storage matrix for durable and generated surfaces."""

    return (
        RepositoryFileOwnershipArea(
            area_id="root-directories",
            owner_surface="repository-root",
            purpose=(
                "Keep repository-wide contracts, docs, workflow entrypoints, and package "
                "boundaries visible at the root instead of scattering them under packages."
            ),
            path_rules=(
                "Use `apis/` for checked OpenAPI contracts and frozen payloads.",
                "Use `configs/` for repository-wide governance, lint, typing, and release manifests.",
                "Use `docs/` for repository-level handbook pages and reader journeys.",
                "Use `makes/` for root and package orchestration entrypoints.",
                "Use `packages/` only for package-owned code, tests, package docs, and package metadata.",
            ),
            anchor_paths=("apis", "configs", "docs", "makes", "packages"),
            prohibited_alternates=(
                "Do not create package-local `apis/`, `configs/`, or `makes/` directories to mirror root governance.",
                "Do not place repository-wide docs under a package root when one root handbook page already owns the concern.",
            ),
            cleanup_commands=("make clean-root-artifacts",),
        ),
        RepositoryFileOwnershipArea(
            area_id="package-docs",
            owner_surface="package-readers",
            purpose=(
                "Keep package-scoped onboarding close to the package that owns the code while "
                "routing repository-wide concerns back to the root handbook."
            ),
            path_rules=(
                "Every package overview starts in `packages/<package>/README.md`.",
                "Package-specific handbook pages belong under `packages/<package>/docs/` when they explain package-owned behavior.",
                "Root docs own cross-package journeys, release gates, and repository-wide policy pages.",
            ),
            anchor_paths=(
                "packages/bijux-proteomics-foundation/README.md",
                "packages/bijux-proteomics-runtime/docs/CONTRACTS.md",
                "packages/bijux-proteomics-dev/docs/index.md",
            ),
            prohibited_alternates=(
                "Do not duplicate root release guidance or repository artifact policy under package docs.",
                "Do not add package-local copies of root reader-path or repository-shape pages.",
            ),
            cleanup_commands=(
                "make quality-docs-consistency",
                "make quality-docs-links",
            ),
        ),
        RepositoryFileOwnershipArea(
            area_id="benchmark-assets",
            owner_surface="bijux-proteomics-core",
            purpose=(
                "Keep benchmark packages, challenge corpora, and flagship benchmark metadata in "
                "one scientific owner package so asset lineage stays inspectable."
            ),
            path_rules=(
                "Checked benchmark assets live under `packages/bijux-proteomics-core/benchmark-assets/`.",
                "Packages other than core may reference benchmark assets but must not create their own benchmark roots.",
            ),
            anchor_paths=(
                "packages/bijux-proteomics-core/benchmark-assets",
                "docs/04-bijux-proteomics-core/foundation/flagship-benchmark-assets.md",
            ),
            prohibited_alternates=(
                "Do not create sibling benchmark roots under runtime, intelligence, knowledge, lab, or foundation packages.",
                "Do not store flagship benchmark manifests under `artifacts/` as if they were governed source.",
            ),
            cleanup_commands=("make quality",),
        ),
        RepositoryFileOwnershipArea(
            area_id="generated-outputs",
            owner_surface="artifacts-root",
            purpose=(
                "Separate transient execution state from governed source so local runs cannot "
                "masquerade as durable repository truth."
            ),
            path_rules=(
                "Default local outputs, caches, reports, and rerun products to `artifacts/`.",
                "Only write outside `artifacts/` when the task explicitly updates a governed destination such as `docs/`, `apis/`, or `configs/`.",
                "Publishable package roots must stay free of transient state such as `.pytest_cache`, `.ruff_cache`, `coverage.xml`, `dist/`, and `site/`.",
            ),
            anchor_paths=(
                "artifacts",
                "docs/01-bijux-proteomics/operations/artifact-governance.md",
            ),
            prohibited_alternates=(
                "Do not leave caches or generated outputs under `packages/*` roots.",
                "Do not route local run state into the workspace root or ad hoc temp folders inside source trees.",
            ),
            cleanup_commands=("make test-clean", "make clean-root-artifacts"),
        ),
        RepositoryFileOwnershipArea(
            area_id="maintainer-automation",
            owner_surface="bijux-proteomics-dev-and-root-makes",
            purpose=(
                "Keep repository-health automation in one package plus root make entrypoints so "
                "maintainers can find quality, release, and sync behavior without package hunting."
            ),
            path_rules=(
                "Python governance and release helpers live under `packages/bijux-proteomics-dev/src/bijux_proteomics_dev/`.",
                "Human-facing automation entrypoints live in `makes/` and the root `Makefile` flow.",
                "Generated governance manifests belong under `configs/package-governance/`.",
            ),
            anchor_paths=(
                "packages/bijux-proteomics-dev/src/bijux_proteomics_dev",
                "makes/root.mk",
                "configs/package-governance",
            ),
            prohibited_alternates=(
                "Do not hide repository-wide quality or release automation under product packages.",
                "Do not invent new one-off maintainer scripts in package roots when root make targets already own the flow.",
            ),
            cleanup_commands=("make quality", "make release-preflight"),
        ),
    )


def validate_repository_file_ownership_matrix(
    repo_root: Path = REPO_ROOT,
) -> tuple[RepositoryFileOwnershipIssue, ...]:
    """Validate the checked repository file-ownership matrix."""

    matrix = build_repository_file_ownership_matrix()
    issues: list[RepositoryFileOwnershipIssue] = []
    expected_area_ids = (
        "root-directories",
        "package-docs",
        "benchmark-assets",
        "generated-outputs",
        "maintainer-automation",
    )
    if tuple(area.area_id for area in matrix) != expected_area_ids:
        issues.append(
            RepositoryFileOwnershipIssue(
                code="area-order-drift",
                detail=(
                    "repository file-ownership area order drifted: "
                    f"{tuple(area.area_id for area in matrix)!r}"
                ),
            )
        )
    for area in matrix:
        if not area.path_rules:
            issues.append(
                RepositoryFileOwnershipIssue(
                    code="missing-path-rules",
                    detail=f"{area.area_id} no longer defines storage rules",
                )
            )
        if not area.cleanup_commands:
            issues.append(
                RepositoryFileOwnershipIssue(
                    code="missing-cleanup-commands",
                    detail=f"{area.area_id} no longer defines cleanup commands",
                )
            )
        for anchor in area.anchor_paths:
            if not (repo_root / anchor).exists():
                issues.append(
                    RepositoryFileOwnershipIssue(
                        code="missing-anchor-path",
                        detail=f"{area.area_id} is missing anchor path {anchor}",
                    )
                )
    return tuple(sorted(issues, key=lambda issue: (issue.code, issue.detail)))


def _render_tuple(values: tuple[str, ...]) -> str:
    return ", ".join(f'"{value}"' for value in values)


def _toml_text(matrix: tuple[RepositoryFileOwnershipArea, ...]) -> str:
    lines = [
        "# Generated repository file-ownership matrix.",
        "# Regenerate with: ./.venv/bin/python -m bijux_proteomics_dev.quality.artifacts.repository_file_ownership",
        "",
    ]
    for area in matrix:
        lines.extend(
            [
                "[[area]]",
                f'area_id = "{area.area_id}"',
                f'owner_surface = "{area.owner_surface}"',
                f'purpose = "{area.purpose}"',
                f"path_rules = [{_render_tuple(area.path_rules)}]",
                f"anchor_paths = [{_render_tuple(area.anchor_paths)}]",
                f"prohibited_alternates = [{_render_tuple(area.prohibited_alternates)}]",
                f"cleanup_commands = [{_render_tuple(area.cleanup_commands)}]",
                "",
            ]
        )
    return "\n".join(lines)


def _load_matrix(path: Path) -> tuple[RepositoryFileOwnershipArea, ...] | None:
    if not path.exists():
        return None
    with path.open("rb") as handle:
        raw = tomllib.load(handle)
    return tuple(
        RepositoryFileOwnershipArea(
            area_id=item["area_id"],
            owner_surface=item["owner_surface"],
            purpose=item["purpose"],
            path_rules=tuple(item["path_rules"]),
            anchor_paths=tuple(item["anchor_paths"]),
            prohibited_alternates=tuple(item["prohibited_alternates"]),
            cleanup_commands=tuple(item["cleanup_commands"]),
        )
        for item in raw.get("area", [])
    )


def run(check: bool = False) -> int:
    matrix = build_repository_file_ownership_matrix()
    issues = validate_repository_file_ownership_matrix()
    if issues:
        for issue in issues:
            print(f"{issue.code}: {issue.detail}")
        return 1
    if check:
        if _load_matrix(REPOSITORY_FILE_OWNERSHIP_PATH) == matrix:
            print("repository file-ownership matrix is up to date")
            return 0
        print("repository file-ownership matrix is stale; regenerate it")
        return 1
    REPOSITORY_FILE_OWNERSHIP_PATH.write_text(
        _toml_text(matrix),
        encoding="utf-8",
    )
    print("generated repository file-ownership matrix")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate or validate the repository file-ownership matrix."
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Fail if the repository file-ownership matrix is not up to date.",
    )
    raise SystemExit(run(check=parser.parse_args().check))
