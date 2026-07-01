from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path

from bijux_proteomics_dev.governance.dependencies.package_dependency_policy import (
    validate_package_dependency_policy,
)
from bijux_proteomics_dev.governance.foundation.package_boundary_coherence import (
    validate_package_boundary_coherence,
)
from bijux_proteomics_dev.governance.runtime.topology import REPO_ROOT
from bijux_proteomics_dev.quality.artifacts.package_root_hygiene import (
    validate_package_root_hygiene,
)
from bijux_proteomics_dev.quality.artifacts.repository_drift_audit import (
    validate_repository_drift_audit,
)
from bijux_proteomics_dev.release.governance.benchmark_freshness_review import (
    BENCHMARK_FRESHNESS_REVIEW_PATH,
    validate_benchmark_freshness_review,
)
from bijux_proteomics_dev.release.governance.benchmark_rerun_governance import (
    validate_black_box_benchmark_language,
)
from bijux_proteomics_dev.release.governance.package_family_readiness import (
    package_family_readiness_manifest_path,
    validate_package_family_readiness,
)
from bijux_proteomics_dev.release.governance.scientific_readiness import (
    scientific_release_manifest_path,
    validate_scientific_release_dossier,
)
from bijux_proteomics_dev.release.governance.workflow_authority_docs import (
    validate_workflow_authority_docs,
)
from bijux_proteomics_dev.release.governance.workflow_claim_grounding import (
    validate_workflow_claim_grounding,
)
from bijux_proteomics_dev.release.governance.workflow_consequence_chain import (
    validate_workflow_consequence_coherence,
)
from bijux_proteomics_dev.release.governance.workflow_intelligence_confidence import (
    validate_workflow_intelligence_confidence,
)
from bijux_proteomics_dev.release.governance.workflow_lab_consequence import (
    validate_workflow_lab_consequence,
)
from bijux_proteomics_dev.release.governance.workflow_public_scrutiny import (
    validate_workflow_public_scrutiny,
)
from bijux_proteomics_runtime.workflows.black_box_reproducibility import (
    build_runtime_black_box_rerun_gate,
)
from bijux_proteomics_runtime.workflows.flagship_workflow_manifest import (
    FLAGSHIP_WORKFLOW_MANIFEST_PATH,
    validate_flagship_workflow_manifest,
)

__all__ = [
    "RELEASE_READINESS_MATRIX_PATH",
    "ReleaseReadinessCategory",
    "ReleaseReadinessIssue",
    "ReleaseReadinessMatrix",
    "build_release_readiness_matrix",
    "run",
    "validate_release_readiness_matrix",
]


RELEASE_READINESS_MATRIX_PATH = (
    REPO_ROOT / "configs" / "package-governance" / "release-readiness-matrix.toml"
)


@dataclass(frozen=True)
class ReleaseReadinessCategory:
    """One hostile-review category in the repository readiness matrix."""

    category_id: str
    title: str
    ready: bool
    rationale: str
    evidence_paths: tuple[str, ...]
    blocker_codes: tuple[str, ...]
    blocker_details: tuple[str, ...]


@dataclass(frozen=True)
class ReleaseReadinessMatrix:
    """Repository readiness matrix across hostile-review categories."""

    categories: tuple[ReleaseReadinessCategory, ...]


@dataclass(frozen=True)
class ReleaseReadinessIssue:
    """One internal consistency issue in the checked readiness matrix."""

    code: str
    detail: str


def _issues_to_codes_and_details(
    issues: tuple[object, ...] | list[object],
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    codes: list[str] = []
    details: list[str] = []
    for issue in issues:
        if isinstance(issue, str):
            code = "release-contract-failure"
            detail = issue
        else:
            code = getattr(issue, "code", "")
            detail = getattr(issue, "detail", "")
        codes.append(str(code))
        details.append(str(detail))
    return tuple(codes), tuple(details)


def _category(
    *,
    category_id: str,
    title: str,
    rationale: str,
    evidence_paths: tuple[str, ...],
    issues: tuple[object, ...] | list[object],
) -> ReleaseReadinessCategory:
    blocker_codes, blocker_details = _issues_to_codes_and_details(issues)
    return ReleaseReadinessCategory(
        category_id=category_id,
        title=title,
        ready=not blocker_codes,
        rationale=rationale,
        evidence_paths=evidence_paths,
        blocker_codes=blocker_codes,
        blocker_details=blocker_details,
    )


def build_release_readiness_matrix(
    repo_root: Path = REPO_ROOT,
) -> ReleaseReadinessMatrix:
    """Build the repository hostile-review readiness matrix."""

    flagship_workflow_issues = validate_flagship_workflow_manifest(repo_root=repo_root)
    family_readiness_issues = validate_package_family_readiness(repo_root)
    scientific_release_issues = validate_scientific_release_dossier(repo_root)
    benchmark_freshness_issues = validate_benchmark_freshness_review()
    claim_grounding_issues = validate_workflow_claim_grounding(repo_root)
    authority_doc_issues = validate_workflow_authority_docs(repo_root)
    public_scrutiny_issues = validate_workflow_public_scrutiny(repo_root)
    dependency_policy_issues = validate_package_dependency_policy()
    boundary_coherence_issues = validate_package_boundary_coherence(repo_root)
    package_hygiene_issues = validate_package_root_hygiene(repo_root)
    drift_audit_issues = validate_repository_drift_audit(repo_root)
    intelligence_issues = validate_workflow_intelligence_confidence(repo_root)
    lab_consequence_issues = validate_workflow_lab_consequence()
    consequence_coherence_issues = validate_workflow_consequence_coherence(repo_root)
    runtime_rerun_gate = build_runtime_black_box_rerun_gate()
    black_box_language_issues = validate_black_box_benchmark_language()

    categories = (
        _category(
            category_id="workflow-family-product-evidence",
            title="Workflow-family product evidence",
            rationale=(
                "The root promise must be anchored in one checked workflow "
                "manifest plus declared package-family readiness evidence."
            ),
            evidence_paths=(
                FLAGSHIP_WORKFLOW_MANIFEST_PATH.relative_to(repo_root).as_posix(),
                package_family_readiness_manifest_path(repo_root)
                .relative_to(repo_root)
                .as_posix(),
                "docs/01-bijux-proteomics/foundation/product-architecture.md",
            ),
            issues=(*flagship_workflow_issues, *family_readiness_issues),
        ),
        _category(
            category_id="black-box-rerunability",
            title="Black-box rerunability",
            rationale=(
                "A hostile reviewer should be able to start from the flagship "
                "runtime lane and see whether rerun evidence is strong enough "
                "without maintainers narrating around missing artifacts."
            ),
            evidence_paths=(
                *runtime_rerun_gate.evidence_paths,
                "docs/09-bijux-proteomics-runtime/black-box-benchmark-dashboard.md",
                "docs/09-bijux-proteomics-runtime/benchmark-rerun-kits.md",
                "docs/09-bijux-proteomics-runtime/benchmark-comparability-matrix.md",
                "docs/01-bijux-proteomics/foundation/public-artifact-index.md",
                "docs/01-bijux-proteomics/foundation/flagship-release-candidate.md",
            ),
            issues=(*runtime_rerun_gate.issues, *black_box_language_issues),
        ),
        _category(
            category_id="benchmark-asset-quality",
            title="Benchmark asset quality",
            rationale=(
                "Release claims must stay behind the benchmark asset coverage, "
                "grounding, and scientific release evidence actually checked in."
            ),
            evidence_paths=(
                scientific_release_manifest_path(repo_root)
                .relative_to(repo_root)
                .as_posix(),
                BENCHMARK_FRESHNESS_REVIEW_PATH.relative_to(repo_root).as_posix(),
                "docs/04-bijux-proteomics-core/foundation/flagship-benchmark-assets.md",
                "docs/04-bijux-proteomics-core/foundation/flagship-public-benchmark-catalog.md",
            ),
            issues=(
                *scientific_release_issues,
                *benchmark_freshness_issues,
                *claim_grounding_issues,
            ),
        ),
        _category(
            category_id="docs-clarity",
            title="Docs clarity",
            rationale=(
                "Root and handbook wording must route readers to the right "
                "evidence without stronger trust language than the current docs "
                "surfaces can honestly defend."
            ),
            evidence_paths=(
                "README.md",
                "docs/index.md",
                "docs/01-bijux-proteomics/foundation/product-architecture.md",
                "docs/01-bijux-proteomics/foundation/cross-package-ownership.md",
                "docs/01-bijux-proteomics/foundation/release-readiness-matrix.md",
            ),
            issues=(*authority_doc_issues, *public_scrutiny_issues),
        ),
        _category(
            category_id="package-boundary-stability",
            title="Package-boundary stability",
            rationale=(
                "Import directions, public surfaces, and README routing must "
                "continue to describe the same ownership model."
            ),
            evidence_paths=(
                "configs/package-governance/package-dependency-policy.toml",
                "configs/package-governance/repository-product-shape.toml",
                "docs/01-bijux-proteomics/foundation/cross-package-ownership.md",
            ),
            issues=(*dependency_policy_issues, *boundary_coherence_issues),
        ),
        _category(
            category_id="artifact-hygiene",
            title="Artifact hygiene",
            rationale=(
                "A repository that still leaks caches, package-local artifacts, or "
                "duplicate owner surfaces on disk is not ready for stronger release language."
            ),
            evidence_paths=(
                "configs/package-governance/repository-file-ownership.toml",
                "configs/package-governance/repository-drift-audit.toml",
                "docs/01-bijux-proteomics/operations/artifact-governance.md",
                "packages/bijux-proteomics-dev/src/bijux_proteomics_dev/quality/artifacts/package_root_hygiene.py",
            ),
            issues=(*package_hygiene_issues, *drift_audit_issues),
        ),
        _category(
            category_id="consequence-realism",
            title="Consequence realism",
            rationale=(
                "Recommendation posture must not outrun the downstream lab "
                "consequence and refusal surfaces that inherit that claim."
            ),
            evidence_paths=(
                "docs/05-bijux-proteomics-intelligence/foundation/workflow-recommendation-confidence.md",
                "docs/01-bijux-proteomics/foundation/workflow-consequence-maps.md",
                "docs/01-bijux-proteomics/foundation/what-changed-the-recommendation.md",
                "docs/07-bijux-proteomics-lab/foundation/outcome-learning-loops.md",
                "docs/07-bijux-proteomics-lab/foundation/workflow-refusal-handbook.md",
                "docs/07-bijux-proteomics-lab/index.md",
                "docs/01-bijux-proteomics/foundation/current-capability-limits.md",
            ),
            issues=(
                *intelligence_issues,
                *lab_consequence_issues,
                *consequence_coherence_issues,
            ),
        ),
    )
    return ReleaseReadinessMatrix(categories=categories)


def validate_release_readiness_matrix(
    repo_root: Path = REPO_ROOT,
) -> tuple[ReleaseReadinessIssue, ...]:
    """Validate the checked release-readiness matrix for internal consistency."""

    matrix = build_release_readiness_matrix(repo_root)
    issues: list[ReleaseReadinessIssue] = []
    expected_categories = {
        "workflow-family-product-evidence",
        "black-box-rerunability",
        "benchmark-asset-quality",
        "docs-clarity",
        "package-boundary-stability",
        "artifact-hygiene",
        "consequence-realism",
    }
    seen_categories = {category.category_id for category in matrix.categories}
    if seen_categories != expected_categories:
        issues.append(
            ReleaseReadinessIssue(
                code="category-set-drift",
                detail=(
                    "release readiness matrix categories drifted: "
                    f"{sorted(seen_categories)}"
                ),
            )
        )

    for category in matrix.categories:
        for relative_path in category.evidence_paths:
            if not (repo_root / relative_path).exists():
                issues.append(
                    ReleaseReadinessIssue(
                        code="missing-evidence-path",
                        detail=(
                            f"{category.category_id} is missing evidence path "
                            f"{relative_path}"
                        ),
                    )
                )
        if category.ready and category.blocker_codes:
            issues.append(
                ReleaseReadinessIssue(
                    code="ready-category-has-blockers",
                    detail=f"{category.category_id} is ready but still lists blockers",
                )
            )
        if not category.ready and not category.blocker_codes:
            issues.append(
                ReleaseReadinessIssue(
                    code="blocked-category-missing-blockers",
                    detail=f"{category.category_id} is blocked but has no blocker codes",
                )
            )
        if len(category.blocker_codes) != len(category.blocker_details):
            issues.append(
                ReleaseReadinessIssue(
                    code="blocker-shape-drift",
                    detail=(
                        f"{category.category_id} blocker code/detail counts no longer match"
                    ),
                )
            )
    return tuple(sorted(issues, key=lambda issue: (issue.code, issue.detail)))


def _render_tuple(values: tuple[str, ...]) -> str:
    return ", ".join(f'"{value}"' for value in values)


def _toml_text(matrix: ReleaseReadinessMatrix) -> str:
    lines = [
        "# Generated release readiness matrix.",
        "# Regenerate with: ./.venv/bin/python -m bijux_proteomics_dev.release.governance.release_readiness_matrix",
        "",
    ]
    for category in matrix.categories:
        lines.extend(
            [
                "[[category]]",
                f'category_id = "{category.category_id}"',
                f'title = "{category.title}"',
                f"ready = {'true' if category.ready else 'false'}",
                f'rationale = "{category.rationale}"',
                f"evidence_paths = [{_render_tuple(category.evidence_paths)}]",
                f"blocker_codes = [{_render_tuple(category.blocker_codes)}]",
                f"blocker_details = [{_render_tuple(category.blocker_details)}]",
                "",
            ]
        )
    return "\n".join(lines)


def _is_up_to_date(matrix: ReleaseReadinessMatrix) -> bool:
    if not RELEASE_READINESS_MATRIX_PATH.exists():
        return False
    return RELEASE_READINESS_MATRIX_PATH.read_text(encoding="utf-8") == _toml_text(
        matrix
    )


def run(check: bool = False) -> int:
    matrix = build_release_readiness_matrix()
    issues = validate_release_readiness_matrix()
    if issues:
        for issue in issues:
            print(f"{issue.code}: {issue.detail}")
        return 1
    if check:
        if _is_up_to_date(matrix):
            print("release readiness matrix is up to date")
            return 0
        print("release readiness matrix is stale; regenerate it")
        return 1
    RELEASE_READINESS_MATRIX_PATH.write_text(_toml_text(matrix), encoding="utf-8")
    print("generated release readiness matrix")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate or validate the release readiness matrix."
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Fail if the release readiness matrix is not up to date.",
    )
    args = parser.parse_args()
    raise SystemExit(run(check=args.check))
