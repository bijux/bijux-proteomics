from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from bijux_proteomics.benchmarks.flagship_acceptance import (
    build_flagship_acceptance_dashboard,
)
from bijux_proteomics_dev.governance.package_shape.package_readme_maturity import (
    PACKAGE_README_MATURITY_PATH,
    build_package_readme_maturity_report,
)
from bijux_proteomics_dev.governance.package_shape.package_reopened_completion_claims import (
    PACKAGE_REOPENED_COMPLETION_CLAIMS_PATH,
    build_package_reopened_completion_claim_report,
)
from bijux_proteomics_dev.governance.package_shape.package_scorecard import (
    PACKAGE_SCORECARD_PATH,
    build_package_scorecard_report,
)
from bijux_proteomics_dev.quality.artifacts.package_root_hygiene import (
    validate_package_root_hygiene,
)
from bijux_proteomics_dev.quality.artifacts.repository_drift_audit import (
    validate_repository_drift_audit,
)
from bijux_proteomics_dev.release.governance.generated_governance_freshness import (
    validate_generated_governance_freshness,
)
from bijux_proteomics_dev.release.governance.package_family_readiness import (
    build_package_family_readiness_reports,
)
from bijux_proteomics_dev.release.governance.public_artifact_governance import (
    validate_public_artifact_governance,
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
from bijux_proteomics_intelligence.candidates.ranking_benchmarks import (
    build_flagship_ranking_policy,
    build_legacy_ranking_policy,
    compare_ranking_policies_against_benchmark_corpus,
)
from bijux_proteomics_intelligence.reviews.public_scrutiny import (
    build_public_artifact_index,
    build_public_artifact_role_matrix,
)
from bijux_proteomics_runtime.workflows.black_box_reproducibility import (
    build_runtime_black_box_rerun_gate,
)
from bijux_proteomics_runtime.workflows.flagship_workflow_manifest import (
    FLAGSHIP_WORKFLOW_MANIFEST_PATH,
    validate_flagship_workflow_manifest,
)

__all__ = [
    "RepositoryTruthIssue",
    "RepositoryTruthReport",
    "build_repository_truth_report",
    "validate_repository_truth_report",
]


@dataclass(frozen=True)
class RepositoryTruthIssue:
    """One blocker on reference-grade or elite truth claims."""

    code: str
    detail: str


@dataclass(frozen=True)
class RepositoryTruthReport:
    """Repository-level truth posture for stronger scientific maturity claims."""

    flagship_workflow_undeniable: bool
    reference_grade_claim_allowed: bool
    elite_claim_allowed: bool
    architecturally_ready_package_count: int
    reopened_completion_claim_package_names: tuple[str, ...]
    completion_claim_package_names: tuple[str, ...]
    evidence_paths: tuple[str, ...]
    blockers: tuple[RepositoryTruthIssue, ...]


def build_repository_truth_report(repo_root: Path) -> RepositoryTruthReport:
    """Build the repository-level truth posture for stronger maturity claims."""

    scorecard = build_package_scorecard_report()
    reopened = build_package_reopened_completion_claim_report()
    maturity = build_package_readme_maturity_report()
    family_reports = build_package_family_readiness_reports(repo_root)
    workflow_manifest_issues = validate_flagship_workflow_manifest(repo_root=repo_root)
    scientific_dossier_issues = validate_scientific_release_dossier(repo_root)
    workflow_authority_doc_issues = validate_workflow_authority_docs(repo_root)
    workflow_claim_grounding_issues = validate_workflow_claim_grounding(repo_root)
    workflow_intelligence_issues = validate_workflow_intelligence_confidence(repo_root)
    workflow_lab_consequence_issues = validate_workflow_lab_consequence()
    workflow_consequence_issues = validate_workflow_consequence_coherence(
        repo_root=repo_root
    )
    workflow_public_scrutiny_issues = validate_workflow_public_scrutiny(repo_root)
    freshness_issues = validate_generated_governance_freshness()
    package_hygiene_issues = validate_package_root_hygiene(repo_root)
    drift_audit_issues = validate_repository_drift_audit(repo_root)
    runtime_rerun_gate = build_runtime_black_box_rerun_gate()
    acceptance_dashboard = build_flagship_acceptance_dashboard()
    public_artifact_governance_issues = validate_public_artifact_governance()
    ranking_improvement = compare_ranking_policies_against_benchmark_corpus(
        build_legacy_ranking_policy(),
        build_flagship_ranking_policy(),
    )
    public_artifact_index = build_public_artifact_index()
    public_artifact_role_matrix = build_public_artifact_role_matrix()

    architecturally_ready_package_count = sum(
        entry.architectural_ready for entry in scorecard.entries
    )
    reopened_packages = tuple(
        entry.distribution_name
        for entry in reopened.entries
        if entry.reopened_completion_claim
    )
    completion_claim_packages = tuple(
        entry.distribution_name
        for entry in maturity.entries
        if entry.completion_claims_while_not_ready
    )
    flagship_workflow_undeniable = (
        not workflow_manifest_issues and ranking_improvement.decision_improved
    )

    blockers: list[RepositoryTruthIssue] = []
    for manifest_issue in workflow_manifest_issues:
        blockers.append(
            RepositoryTruthIssue(
                code=f"flagship-workflow-{manifest_issue.code}",
                detail=manifest_issue.detail,
            )
        )
    for scientific_issue in scientific_dossier_issues:
        blockers.append(
            RepositoryTruthIssue(
                code=f"scientific-release-{scientific_issue.code}",
                detail=scientific_issue.detail,
            )
        )
    for authority_issue in workflow_authority_doc_issues:
        blockers.append(
            RepositoryTruthIssue(
                code=f"workflow-authority-docs-{authority_issue.code}",
                detail=authority_issue.detail,
            )
        )
    for claim_grounding_issue in workflow_claim_grounding_issues:
        blockers.append(
            RepositoryTruthIssue(
                code=f"workflow-claim-grounding-{claim_grounding_issue.code}",
                detail=claim_grounding_issue.detail,
            )
        )
    for intelligence_issue in workflow_intelligence_issues:
        blockers.append(
            RepositoryTruthIssue(
                code=f"workflow-intelligence-{intelligence_issue.code}",
                detail=intelligence_issue.detail,
            )
        )
    for lab_consequence_issue in workflow_lab_consequence_issues:
        blockers.append(
            RepositoryTruthIssue(
                code=f"workflow-lab-consequence-{lab_consequence_issue.code}",
                detail=lab_consequence_issue.detail,
            )
        )
    for consequence_issue in workflow_consequence_issues:
        blockers.append(
            RepositoryTruthIssue(
                code=f"workflow-consequence-coherence-{consequence_issue.code}",
                detail=consequence_issue.detail,
            )
        )
    for public_scrutiny_issue in workflow_public_scrutiny_issues:
        blockers.append(
            RepositoryTruthIssue(
                code=f"workflow-public-scrutiny-{public_scrutiny_issue.code}",
                detail=public_scrutiny_issue.detail,
            )
        )
    for artifact_governance_issue in public_artifact_governance_issues:
        blockers.append(
            RepositoryTruthIssue(
                code=f"public-artifact-governance-{artifact_governance_issue.code}",
                detail=artifact_governance_issue.detail,
            )
        )
    for freshness_issue in freshness_issues:
        blockers.append(
            RepositoryTruthIssue(
                code=f"governance-freshness-{freshness_issue.code}",
                detail=freshness_issue.detail,
            )
        )
    for hygiene_issue in package_hygiene_issues:
        blockers.append(
            RepositoryTruthIssue(
                code=f"artifact-hygiene-{hygiene_issue.code}",
                detail=hygiene_issue.detail,
            )
        )
    for drift_issue in drift_audit_issues:
        blockers.append(
            RepositoryTruthIssue(
                code=f"artifact-drift-{drift_issue.code}",
                detail=drift_issue.detail,
            )
        )
    for rerun_gate_issue in runtime_rerun_gate.issues:
        blockers.append(
            RepositoryTruthIssue(
                code=f"runtime-rerun-gate-{rerun_gate_issue.code}",
                detail=rerun_gate_issue.detail,
            )
        )
    for row in acceptance_dashboard.rows:
        if row.claim_ahead_of_evidence:
            blockers.append(
                RepositoryTruthIssue(
                    code=f"workflow-acceptance-{row.workflow_family.value}-claim-ahead-of-evidence",
                    detail=(
                        f"{row.workflow_family.value} still claims {row.public_release_language.value} "
                        f"but only earns {row.earned_release_language.value} under the flagship acceptance sheet"
                    ),
                )
            )
    if reopened_packages:
        blockers.append(
            RepositoryTruthIssue(
                code="reopened-completion-claims-block-reference-grade",
                detail=(
                    "reference-grade posture remains blocked by reopened completion claims in "
                    + ", ".join(reopened_packages)
                ),
            )
        )
    if completion_claim_packages:
        blockers.append(
            RepositoryTruthIssue(
                code="completion-claims-while-not-ready",
                detail=(
                    "packages still claim completion while architectural-ready is false: "
                    + ", ".join(completion_claim_packages)
                ),
            )
        )
    if architecturally_ready_package_count < len(scorecard.entries):
        blockers.append(
            RepositoryTruthIssue(
                code="architectural-ready-floor-not-met",
                detail=(
                    f"only {architecturally_ready_package_count}/{len(scorecard.entries)} packages are architectural-ready"
                ),
            )
        )
    if any(not report.ready for report in family_reports):
        blocked_families = tuple(
            report.family_id for report in family_reports if not report.ready
        )
        blockers.append(
            RepositoryTruthIssue(
                code="release-family-readiness-blocked",
                detail="release families still blocked: " + ", ".join(blocked_families),
            )
        )
    if not ranking_improvement.decision_improved:
        blockers.append(
            RepositoryTruthIssue(
                code="ranking-benchmark-proof-missing",
                detail=(
                    "flagship ranking policy does not yet outperform the legacy baseline "
                    f"on corpus {ranking_improvement.corpus_id}"
                ),
            )
        )

    reference_grade_claim_allowed = flagship_workflow_undeniable and not blockers
    elite_claim_allowed = (
        reference_grade_claim_allowed
        and architecturally_ready_package_count == len(scorecard.entries)
    )
    return RepositoryTruthReport(
        flagship_workflow_undeniable=flagship_workflow_undeniable,
        reference_grade_claim_allowed=reference_grade_claim_allowed,
        elite_claim_allowed=elite_claim_allowed,
        architecturally_ready_package_count=architecturally_ready_package_count,
        reopened_completion_claim_package_names=reopened_packages,
        completion_claim_package_names=completion_claim_packages,
        evidence_paths=(
            FLAGSHIP_WORKFLOW_MANIFEST_PATH.relative_to(repo_root).as_posix(),
            PACKAGE_SCORECARD_PATH.relative_to(repo_root).as_posix(),
            PACKAGE_REOPENED_COMPLETION_CLAIMS_PATH.relative_to(repo_root).as_posix(),
            PACKAGE_README_MATURITY_PATH.relative_to(repo_root).as_posix(),
            scientific_release_manifest_path(repo_root)
            .relative_to(repo_root)
            .as_posix(),
            "artifacts/intelligence/ranking-benchmarks/reviewable-ranking-corpus.json",
            "artifacts/intelligence/ranking-benchmarks/flagship-reviewable-ranking.json",
            "artifacts/runtime/proof-accounting/runtime_proof_map.json",
            acceptance_dashboard.artifact_path,
            public_artifact_index.artifact_path,
            public_artifact_role_matrix.doc_path,
            "docs/01-bijux-proteomics/foundation/workflow-consequence-maps.md",
            "docs/01-bijux-proteomics/foundation/what-changed-the-recommendation.md",
            "docs/07-bijux-proteomics-lab/foundation/outcome-learning-loops.md",
            "docs/07-bijux-proteomics-lab/foundation/workflow-refusal-handbook.md",
        ),
        blockers=tuple(blockers),
    )


def validate_repository_truth_report(
    repo_root: Path,
) -> tuple[RepositoryTruthIssue, ...]:
    """Validate repository truth posture for stronger release language."""

    report = build_repository_truth_report(repo_root)
    issues: list[RepositoryTruthIssue] = []
    if report.reference_grade_claim_allowed and not report.flagship_workflow_undeniable:
        issues.append(
            RepositoryTruthIssue(
                code="reference-grade-without-undeniable-workflow",
                detail=(
                    "reference-grade posture must not be allowed before one workflow is undeniable"
                ),
            )
        )
    if report.elite_claim_allowed and not report.reference_grade_claim_allowed:
        issues.append(
            RepositoryTruthIssue(
                code="elite-without-reference-grade",
                detail="elite posture must remain stricter than reference-grade posture",
            )
        )
    return tuple(issues)
