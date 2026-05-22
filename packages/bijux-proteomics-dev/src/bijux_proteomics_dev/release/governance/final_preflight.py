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
from bijux_proteomics_dev.release.governance.benchmark_flagship_status import (
    run as run_benchmark_flagship_status,
)
from bijux_proteomics_dev.release.governance.benchmark_flagship_status import (
    validate_benchmark_flagship_promotion,
)
from bijux_proteomics_dev.release.governance.benchmark_rerun_governance import (
    run as run_benchmark_rerun_governance,
)
from bijux_proteomics_dev.release.governance.benchmark_rerun_governance import (
    validate_black_box_benchmark_language,
)
from bijux_proteomics_dev.release.governance.hostile_review_pages import (
    run as run_hostile_review_pages,
)
from bijux_proteomics_dev.release.governance.package_family_readiness import (
    validate_package_family_readiness,
)
from bijux_proteomics_dev.release.governance.public_artifact_governance import (
    run as run_public_artifact_governance,
)
from bijux_proteomics_dev.release.governance.public_language import (
    run as run_public_language,
)
from bijux_proteomics_dev.release.governance.readme_truth import (
    validate_readme_truth,
)
from bijux_proteomics_dev.release.governance.release_narrowing_protocol import (
    run as run_release_narrowing_protocol,
)
from bijux_proteomics_dev.release.governance.runtime_black_box_docs import (
    run as run_runtime_black_box_docs,
)
from bijux_proteomics_dev.release.governance.scientific_readiness import (
    validate_scientific_release_dossier,
)
from bijux_proteomics_dev.release.governance.test_collection_gate import (
    build_test_collection_gate_report,
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
from bijux_proteomics_dev.release.governance.workflow_consequence_docs import (
    run as run_workflow_consequence_docs,
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
    validate_flagship_workflow_manifest,
)

__all__ = [
    "FINAL_PREFLIGHT_STAGE_IDS",
    "FinalPreflightIssue",
    "FinalPreflightReport",
    "FinalPreflightStage",
    "REPO_ROOT",
    "build_final_preflight_report",
    "run",
]


FINAL_PREFLIGHT_STAGE_IDS = (
    "docs-clarity",
    "package-boundaries",
    "test-collection",
    "benchmark-assets",
    "runtime-reproducibility",
    "consequence-coherence",
    "artifact-hygiene",
)


@dataclass(frozen=True)
class FinalPreflightIssue:
    """One normalized issue in the hostile-review preflight."""

    code: str
    detail: str


@dataclass(frozen=True)
class FinalPreflightStage:
    """One deterministic stage inside the final hostile-review preflight."""

    stage_id: str
    label: str
    issues: tuple[FinalPreflightIssue, ...]


@dataclass(frozen=True)
class FinalPreflightReport:
    """Ordered hostile-review report across the minimum release gates."""

    stages: tuple[FinalPreflightStage, ...]


def _normalize_issues(
    raw_issues: tuple[object, ...] | list[object],
    *,
    default_code: str,
) -> tuple[FinalPreflightIssue, ...]:
    issues: list[FinalPreflightIssue] = []
    for raw_issue in raw_issues:
        if isinstance(raw_issue, str):
            issues.append(FinalPreflightIssue(code=default_code, detail=raw_issue))
            continue
        code = getattr(raw_issue, "code", default_code)
        detail = getattr(raw_issue, "detail", str(raw_issue))
        issues.append(FinalPreflightIssue(code=str(code), detail=str(detail)))
    return tuple(issues)


def _freshness_issue(
    module_label: str, check_result: int
) -> tuple[FinalPreflightIssue, ...]:
    if check_result == 0:
        return ()
    return (
        FinalPreflightIssue(
            code="stale-generated-doc-surface",
            detail=f"{module_label} is stale; regenerate it before release preflight",
        ),
    )


def _docs_stage(repo_root: Path) -> FinalPreflightStage:
    issues = [
        *_normalize_issues(
            validate_readme_truth(repo_root), default_code="readme-truth"
        ),
        *_normalize_issues(
            validate_workflow_authority_docs(repo_root),
            default_code="workflow-authority-docs",
        ),
        *_normalize_issues(
            validate_workflow_public_scrutiny(repo_root),
            default_code="workflow-public-scrutiny",
        ),
        *_freshness_issue(
            "bijux_proteomics_dev.release.governance.hostile_review_pages",
            run_hostile_review_pages(check=True),
        ),
        *_freshness_issue(
            "bijux_proteomics_dev.release.governance.release_narrowing_protocol",
            run_release_narrowing_protocol(check=True),
        ),
        *_freshness_issue(
            "bijux_proteomics_dev.release.governance.public_language",
            run_public_language(check=True),
        ),
        *_freshness_issue(
            "bijux_proteomics_dev.release.governance.public_artifact_governance",
            run_public_artifact_governance(check=True),
        ),
    ]
    return FinalPreflightStage(
        stage_id="docs-clarity",
        label="docs clarity",
        issues=tuple(issues),
    )


def _package_boundaries_stage(repo_root: Path) -> FinalPreflightStage:
    issues = [
        *_normalize_issues(
            validate_package_dependency_policy(),
            default_code="package-dependency-policy",
        ),
        *_normalize_issues(
            validate_package_boundary_coherence(repo_root),
            default_code="package-boundary-coherence",
        ),
        *_normalize_issues(
            validate_package_family_readiness(repo_root),
            default_code="package-family-readiness",
        ),
    ]
    return FinalPreflightStage(
        stage_id="package-boundaries",
        label="package boundaries",
        issues=tuple(issues),
    )


def _test_collection_stage(repo_root: Path) -> FinalPreflightStage:
    report = build_test_collection_gate_report(repo_root=repo_root)
    issues = tuple(
        FinalPreflightIssue(
            code=f"{check.check_kind}-check-failed",
            detail=(
                f"{check.package_name} {check.check_kind} check failed for "
                f"{check.target}: {check.detail}"
            ),
        )
        for check in report.failed_checks
    )
    return FinalPreflightStage(
        stage_id="test-collection",
        label="test collection",
        issues=issues,
    )


def _benchmark_assets_stage(repo_root: Path) -> FinalPreflightStage:
    issues = [
        *_normalize_issues(
            validate_scientific_release_dossier(repo_root),
            default_code="scientific-release",
        ),
        *_normalize_issues(
            validate_workflow_claim_grounding(repo_root),
            default_code="workflow-claim-grounding",
        ),
        *_normalize_issues(
            validate_benchmark_flagship_promotion(),
            default_code="benchmark-flagship-promotion",
        ),
        *_freshness_issue(
            "bijux_proteomics_dev.release.governance.benchmark_flagship_status",
            run_benchmark_flagship_status(check=True),
        ),
    ]
    return FinalPreflightStage(
        stage_id="benchmark-assets",
        label="benchmark assets",
        issues=tuple(issues),
    )


def _runtime_reproducibility_stage(repo_root: Path) -> FinalPreflightStage:
    issues = [
        *_normalize_issues(
            validate_flagship_workflow_manifest(repo_root=repo_root),
            default_code="flagship-workflow",
        ),
        *_normalize_issues(
            build_runtime_black_box_rerun_gate().issues,
            default_code="runtime-black-box-rerun-gate",
        ),
        *_normalize_issues(
            validate_black_box_benchmark_language(),
            default_code="black-box-benchmark-language",
        ),
        *_freshness_issue(
            "bijux_proteomics_dev.release.governance.runtime_black_box_docs",
            run_runtime_black_box_docs(check=True),
        ),
        *_freshness_issue(
            "bijux_proteomics_dev.release.governance.benchmark_rerun_governance",
            run_benchmark_rerun_governance(check=True),
        ),
    ]
    return FinalPreflightStage(
        stage_id="runtime-reproducibility",
        label="runtime reproducibility",
        issues=tuple(issues),
    )


def _consequence_coherence_stage(repo_root: Path) -> FinalPreflightStage:
    issues = [
        *_normalize_issues(
            validate_workflow_intelligence_confidence(repo_root),
            default_code="workflow-intelligence-confidence",
        ),
        *_normalize_issues(
            validate_workflow_lab_consequence(),
            default_code="workflow-lab-consequence",
        ),
        *_normalize_issues(
            validate_workflow_consequence_coherence(repo_root),
            default_code="workflow-consequence-coherence",
        ),
        *_freshness_issue(
            "bijux_proteomics_dev.release.governance.workflow_consequence_docs",
            run_workflow_consequence_docs(check=True),
        ),
    ]
    return FinalPreflightStage(
        stage_id="consequence-coherence",
        label="consequence coherence",
        issues=tuple(issues),
    )


def _artifact_hygiene_stage(repo_root: Path) -> FinalPreflightStage:
    issues = [
        *_normalize_issues(
            validate_package_root_hygiene(repo_root),
            default_code="artifact-hygiene",
        ),
        *_normalize_issues(
            validate_repository_drift_audit(repo_root),
            default_code="artifact-drift",
        ),
    ]
    return FinalPreflightStage(
        stage_id="artifact-hygiene",
        label="artifact hygiene",
        issues=tuple(issues),
    )


def build_final_preflight_report(repo_root: Path = REPO_ROOT) -> FinalPreflightReport:
    """Build the exact-order hostile-review preflight report."""

    stages = (
        _docs_stage(repo_root),
        _package_boundaries_stage(repo_root),
        _test_collection_stage(repo_root),
        _benchmark_assets_stage(repo_root),
        _runtime_reproducibility_stage(repo_root),
        _consequence_coherence_stage(repo_root),
        _artifact_hygiene_stage(repo_root),
    )
    return FinalPreflightReport(stages=stages)


def run(repo_root: Path = REPO_ROOT) -> int:
    report = build_final_preflight_report(repo_root)
    any_failures = False
    for stage in report.stages:
        if stage.issues:
            any_failures = True
            print(f"[fail] {stage.stage_id}: {stage.label}")
            for issue in stage.issues:
                print(f"  - {issue.code}: {issue.detail}")
            continue
        print(f"[pass] {stage.stage_id}: {stage.label}")
    return 1 if any_failures else 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Run the final hostile-review preflight in exact stage order."
    )
    parser.parse_args()
    raise SystemExit(run())
