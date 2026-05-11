from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

from bijux_proteomics_dev.release.governance.repository_truth import (
    RepositoryTruthIssue,
    build_repository_truth_report,
    validate_repository_truth_report,
)
from bijux_proteomics_dev.governance.package_shape.package_reopened_completion_claims import (
    build_package_reopened_completion_claim_report,
)

REPO_ROOT = next(
    parent
    for parent in Path(__file__).resolve().parents
    if (parent / "packages").is_dir() and (parent / "configs").is_dir()
)


def test_repository_truth_report_blocks_reference_grade_and_elite_claims_honestly() -> (
    None
):
    report = build_repository_truth_report(REPO_ROOT)
    reopened_packages = tuple(
        entry.distribution_name
        for entry in build_package_reopened_completion_claim_report().entries
        if entry.reopened_completion_claim
    )

    assert report.flagship_workflow_undeniable is True
    assert report.reference_grade_claim_allowed is False
    assert report.elite_claim_allowed is False
    assert report.reopened_completion_claim_package_names == reopened_packages
    assert report.completion_claim_package_names == ()
    assert report.evidence_paths
    assert "docs/decision-support/workflow-consequence-maps.md" in report.evidence_paths
    assert "docs/lab-consequence/workflow-refusal-handbook.md" in report.evidence_paths
    assert any(
        issue.code == "architectural-ready-floor-not-met" for issue in report.blockers
    )
    assert any(
        issue.code == "governance-freshness-stale-generated-governance-report"
        for issue in report.blockers
    )


def test_repository_truth_report_has_no_internal_consistency_failures() -> None:
    assert validate_repository_truth_report(REPO_ROOT) == ()


def test_repository_truth_report_blocks_fake_backed_runtime_authority(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "bijux_proteomics_dev.release.governance.repository_truth.build_package_scorecard_report",
        lambda: SimpleNamespace(entries=(SimpleNamespace(architectural_ready=True),)),
    )
    monkeypatch.setattr(
        "bijux_proteomics_dev.release.governance.repository_truth.build_package_reopened_completion_claim_report",
        lambda: SimpleNamespace(entries=()),
    )
    monkeypatch.setattr(
        "bijux_proteomics_dev.release.governance.repository_truth.build_package_readme_maturity_report",
        lambda: SimpleNamespace(entries=()),
    )
    monkeypatch.setattr(
        "bijux_proteomics_dev.release.governance.repository_truth.build_package_family_readiness_reports",
        lambda repo_root: (SimpleNamespace(family_id="flagship", ready=True),),
    )
    monkeypatch.setattr(
        "bijux_proteomics_dev.release.governance.repository_truth.validate_flagship_workflow_manifest",
        lambda repo_root=None: (),
    )
    monkeypatch.setattr(
        "bijux_proteomics_dev.release.governance.repository_truth.validate_scientific_release_dossier",
        lambda repo_root: (),
    )
    monkeypatch.setattr(
        "bijux_proteomics_dev.release.governance.repository_truth.validate_workflow_claim_grounding",
        lambda repo_root: (),
    )
    monkeypatch.setattr(
        "bijux_proteomics_dev.release.governance.repository_truth.validate_generated_governance_freshness",
        lambda: (),
    )
    monkeypatch.setattr(
        "bijux_proteomics_dev.release.governance.repository_truth.compare_ranking_policies_against_benchmark_corpus",
        lambda legacy, flagship: SimpleNamespace(
            decision_improved=True,
            corpus_id="mock-corpus",
        ),
    )
    monkeypatch.setattr(
        "bijux_proteomics_dev.release.governance.repository_truth.build_runtime_black_box_rerun_gate",
        lambda: SimpleNamespace(
            issues=(
                SimpleNamespace(
                    workflow_family="dda_import",
                    code="fake-helper-still-present-in-flagship-path",
                    detail="dda import still depends on a fake helper",
                ),
            )
        ),
    )

    report = build_repository_truth_report(REPO_ROOT)

    assert (
        RepositoryTruthIssue(
            code="runtime-rerun-gate-fake-helper-still-present-in-flagship-path",
            detail="dda import still depends on a fake helper",
        )
        in report.blockers
    )


def test_repository_truth_report_blocks_workflow_authority_doc_drift(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "bijux_proteomics_dev.release.governance.repository_truth.build_package_scorecard_report",
        lambda: SimpleNamespace(entries=(SimpleNamespace(architectural_ready=True),)),
    )
    monkeypatch.setattr(
        "bijux_proteomics_dev.release.governance.repository_truth.build_package_reopened_completion_claim_report",
        lambda: SimpleNamespace(entries=()),
    )
    monkeypatch.setattr(
        "bijux_proteomics_dev.release.governance.repository_truth.build_package_readme_maturity_report",
        lambda: SimpleNamespace(entries=()),
    )
    monkeypatch.setattr(
        "bijux_proteomics_dev.release.governance.repository_truth.build_package_family_readiness_reports",
        lambda repo_root: (SimpleNamespace(family_id="flagship", ready=True),),
    )
    monkeypatch.setattr(
        "bijux_proteomics_dev.release.governance.repository_truth.validate_flagship_workflow_manifest",
        lambda repo_root=None: (),
    )
    monkeypatch.setattr(
        "bijux_proteomics_dev.release.governance.repository_truth.validate_scientific_release_dossier",
        lambda repo_root: (),
    )
    monkeypatch.setattr(
        "bijux_proteomics_dev.release.governance.repository_truth.validate_workflow_authority_docs",
        lambda repo_root: (
            SimpleNamespace(
                code="internal-support-family-has-trust-page",
                detail="multiplex is internal-support only in the matrix but still has a trust page",
            ),
        ),
    )
    monkeypatch.setattr(
        "bijux_proteomics_dev.release.governance.repository_truth.validate_workflow_claim_grounding",
        lambda repo_root: (),
    )
    monkeypatch.setattr(
        "bijux_proteomics_dev.release.governance.repository_truth.validate_generated_governance_freshness",
        lambda: (),
    )
    monkeypatch.setattr(
        "bijux_proteomics_dev.release.governance.repository_truth.compare_ranking_policies_against_benchmark_corpus",
        lambda legacy, flagship: SimpleNamespace(
            decision_improved=True,
            corpus_id="mock-corpus",
        ),
    )
    monkeypatch.setattr(
        "bijux_proteomics_dev.release.governance.repository_truth.build_runtime_black_box_rerun_gate",
        lambda: SimpleNamespace(issues=()),
    )

    report = build_repository_truth_report(REPO_ROOT)

    assert (
        RepositoryTruthIssue(
            code="workflow-authority-docs-internal-support-family-has-trust-page",
            detail="multiplex is internal-support only in the matrix but still has a trust page",
        )
        in report.blockers
    )


def test_repository_truth_report_blocks_acceptance_claim_drift(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "bijux_proteomics_dev.release.governance.repository_truth.build_package_scorecard_report",
        lambda: SimpleNamespace(entries=(SimpleNamespace(architectural_ready=True),)),
    )
    monkeypatch.setattr(
        "bijux_proteomics_dev.release.governance.repository_truth.build_package_reopened_completion_claim_report",
        lambda: SimpleNamespace(entries=()),
    )
    monkeypatch.setattr(
        "bijux_proteomics_dev.release.governance.repository_truth.build_package_readme_maturity_report",
        lambda: SimpleNamespace(entries=()),
    )
    monkeypatch.setattr(
        "bijux_proteomics_dev.release.governance.repository_truth.build_package_family_readiness_reports",
        lambda repo_root: (SimpleNamespace(family_id="flagship", ready=True),),
    )
    monkeypatch.setattr(
        "bijux_proteomics_dev.release.governance.repository_truth.validate_flagship_workflow_manifest",
        lambda repo_root=None: (),
    )
    monkeypatch.setattr(
        "bijux_proteomics_dev.release.governance.repository_truth.validate_scientific_release_dossier",
        lambda repo_root: (),
    )
    monkeypatch.setattr(
        "bijux_proteomics_dev.release.governance.repository_truth.validate_workflow_authority_docs",
        lambda repo_root: (),
    )
    monkeypatch.setattr(
        "bijux_proteomics_dev.release.governance.repository_truth.validate_workflow_claim_grounding",
        lambda repo_root: (),
    )
    monkeypatch.setattr(
        "bijux_proteomics_dev.release.governance.repository_truth.validate_generated_governance_freshness",
        lambda: (),
    )
    monkeypatch.setattr(
        "bijux_proteomics_dev.release.governance.repository_truth.compare_ranking_policies_against_benchmark_corpus",
        lambda legacy, flagship: SimpleNamespace(
            decision_improved=True,
            corpus_id="mock-corpus",
        ),
    )
    monkeypatch.setattr(
        "bijux_proteomics_dev.release.governance.repository_truth.build_runtime_black_box_rerun_gate",
        lambda: SimpleNamespace(issues=()),
    )
    monkeypatch.setattr(
        "bijux_proteomics_dev.release.governance.repository_truth.build_flagship_acceptance_dashboard",
        lambda: SimpleNamespace(
            artifact_path="packages/bijux-proteomics-core/benchmark-assets/flagship-acceptance/acceptance_dashboard.json",
            rows=(
                SimpleNamespace(
                    workflow_family=SimpleNamespace(value="dia"),
                    public_release_language=SimpleNamespace(
                        value="outsider_auditable_bounded"
                    ),
                    earned_release_language=SimpleNamespace(
                        value="review_grade_bounded"
                    ),
                    claim_ahead_of_evidence=True,
                ),
            ),
        ),
    )

    report = build_repository_truth_report(REPO_ROOT)

    assert (
        RepositoryTruthIssue(
            code="workflow-acceptance-dia-claim-ahead-of-evidence",
            detail=(
                "dia still claims outsider_auditable_bounded but only earns review_grade_bounded under the flagship acceptance sheet"
            ),
        )
        in report.blockers
    )


def test_repository_truth_report_blocks_decision_grade_intelligence_without_audits(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "bijux_proteomics_dev.release.governance.repository_truth.build_package_scorecard_report",
        lambda: SimpleNamespace(entries=(SimpleNamespace(architectural_ready=True),)),
    )
    monkeypatch.setattr(
        "bijux_proteomics_dev.release.governance.repository_truth.build_package_reopened_completion_claim_report",
        lambda: SimpleNamespace(entries=()),
    )
    monkeypatch.setattr(
        "bijux_proteomics_dev.release.governance.repository_truth.build_package_readme_maturity_report",
        lambda: SimpleNamespace(entries=()),
    )
    monkeypatch.setattr(
        "bijux_proteomics_dev.release.governance.repository_truth.build_package_family_readiness_reports",
        lambda repo_root: (SimpleNamespace(family_id="flagship", ready=True),),
    )
    monkeypatch.setattr(
        "bijux_proteomics_dev.release.governance.repository_truth.validate_flagship_workflow_manifest",
        lambda repo_root=None: (),
    )
    monkeypatch.setattr(
        "bijux_proteomics_dev.release.governance.repository_truth.validate_scientific_release_dossier",
        lambda repo_root: (),
    )
    monkeypatch.setattr(
        "bijux_proteomics_dev.release.governance.repository_truth.validate_workflow_authority_docs",
        lambda repo_root: (),
    )
    monkeypatch.setattr(
        "bijux_proteomics_dev.release.governance.repository_truth.validate_workflow_claim_grounding",
        lambda repo_root: (),
    )
    monkeypatch.setattr(
        "bijux_proteomics_dev.release.governance.repository_truth.validate_workflow_intelligence_confidence",
        lambda repo_root: (
            SimpleNamespace(
                code="decision-grade-intelligence-without-overconfidence-audit",
                detail=(
                    "dda uses decision-grade intelligence language without a published "
                    "overconfidence audit row"
                ),
            ),
        ),
    )
    monkeypatch.setattr(
        "bijux_proteomics_dev.release.governance.repository_truth.validate_generated_governance_freshness",
        lambda: (),
    )
    monkeypatch.setattr(
        "bijux_proteomics_dev.release.governance.repository_truth.compare_ranking_policies_against_benchmark_corpus",
        lambda legacy, flagship: SimpleNamespace(
            decision_improved=True,
            corpus_id="mock-corpus",
        ),
    )
    monkeypatch.setattr(
        "bijux_proteomics_dev.release.governance.repository_truth.build_runtime_black_box_rerun_gate",
        lambda: SimpleNamespace(issues=()),
    )
    monkeypatch.setattr(
        "bijux_proteomics_dev.release.governance.repository_truth.build_flagship_acceptance_dashboard",
        lambda: SimpleNamespace(
            artifact_path="packages/bijux-proteomics-core/benchmark-assets/flagship-acceptance/acceptance_dashboard.json",
            rows=(),
        ),
    )

    report = build_repository_truth_report(REPO_ROOT)

    assert (
        RepositoryTruthIssue(
            code="workflow-intelligence-decision-grade-intelligence-without-overconfidence-audit",
            detail=(
                "dda uses decision-grade intelligence language without a published "
                "overconfidence audit row"
            ),
        )
        in report.blockers
    )


def test_repository_truth_report_blocks_lab_consequence_without_outcome_evidence(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "bijux_proteomics_dev.release.governance.repository_truth.build_package_scorecard_report",
        lambda: SimpleNamespace(entries=(SimpleNamespace(architectural_ready=True),)),
    )
    monkeypatch.setattr(
        "bijux_proteomics_dev.release.governance.repository_truth.build_package_reopened_completion_claim_report",
        lambda: SimpleNamespace(entries=()),
    )
    monkeypatch.setattr(
        "bijux_proteomics_dev.release.governance.repository_truth.build_package_readme_maturity_report",
        lambda: SimpleNamespace(entries=()),
    )
    monkeypatch.setattr(
        "bijux_proteomics_dev.release.governance.repository_truth.build_package_family_readiness_reports",
        lambda repo_root: (SimpleNamespace(family_id="flagship", ready=True),),
    )
    monkeypatch.setattr(
        "bijux_proteomics_dev.release.governance.repository_truth.validate_flagship_workflow_manifest",
        lambda repo_root=None: (),
    )
    monkeypatch.setattr(
        "bijux_proteomics_dev.release.governance.repository_truth.validate_scientific_release_dossier",
        lambda repo_root: (),
    )
    monkeypatch.setattr(
        "bijux_proteomics_dev.release.governance.repository_truth.validate_workflow_authority_docs",
        lambda repo_root: (),
    )
    monkeypatch.setattr(
        "bijux_proteomics_dev.release.governance.repository_truth.validate_workflow_claim_grounding",
        lambda repo_root: (),
    )
    monkeypatch.setattr(
        "bijux_proteomics_dev.release.governance.repository_truth.validate_workflow_intelligence_confidence",
        lambda repo_root: (),
    )
    monkeypatch.setattr(
        "bijux_proteomics_dev.release.governance.repository_truth.validate_workflow_lab_consequence",
        lambda: (
            SimpleNamespace(
                code="lab-consequential-without-outcome-dossier",
                detail=(
                    "dda is called lab-consequential without a shipped requested-versus-observed outcome dossier"
                ),
            ),
        ),
    )
    monkeypatch.setattr(
        "bijux_proteomics_dev.release.governance.repository_truth.validate_generated_governance_freshness",
        lambda: (),
    )
    monkeypatch.setattr(
        "bijux_proteomics_dev.release.governance.repository_truth.compare_ranking_policies_against_benchmark_corpus",
        lambda legacy, flagship: SimpleNamespace(
            decision_improved=True,
            corpus_id="mock-corpus",
        ),
    )
    monkeypatch.setattr(
        "bijux_proteomics_dev.release.governance.repository_truth.build_runtime_black_box_rerun_gate",
        lambda: SimpleNamespace(issues=()),
    )
    monkeypatch.setattr(
        "bijux_proteomics_dev.release.governance.repository_truth.build_flagship_acceptance_dashboard",
        lambda: SimpleNamespace(
            artifact_path="packages/bijux-proteomics-core/benchmark-assets/flagship-acceptance/acceptance_dashboard.json",
            rows=(),
        ),
    )

    report = build_repository_truth_report(REPO_ROOT)

    assert (
        RepositoryTruthIssue(
            code="workflow-lab-consequence-lab-consequential-without-outcome-dossier",
            detail=(
                "dda is called lab-consequential without a shipped requested-versus-observed outcome dossier"
            ),
        )
        in report.blockers
    )


def test_repository_truth_report_blocks_consequence_chain_drift(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "bijux_proteomics_dev.release.governance.repository_truth.build_package_scorecard_report",
        lambda: SimpleNamespace(entries=(SimpleNamespace(architectural_ready=True),)),
    )
    monkeypatch.setattr(
        "bijux_proteomics_dev.release.governance.repository_truth.build_package_reopened_completion_claim_report",
        lambda: SimpleNamespace(entries=()),
    )
    monkeypatch.setattr(
        "bijux_proteomics_dev.release.governance.repository_truth.build_package_readme_maturity_report",
        lambda: SimpleNamespace(entries=()),
    )
    monkeypatch.setattr(
        "bijux_proteomics_dev.release.governance.repository_truth.build_package_family_readiness_reports",
        lambda repo_root: (SimpleNamespace(family_id="flagship", ready=True),),
    )
    monkeypatch.setattr(
        "bijux_proteomics_dev.release.governance.repository_truth.validate_flagship_workflow_manifest",
        lambda repo_root=None: (),
    )
    monkeypatch.setattr(
        "bijux_proteomics_dev.release.governance.repository_truth.validate_scientific_release_dossier",
        lambda repo_root: (),
    )
    monkeypatch.setattr(
        "bijux_proteomics_dev.release.governance.repository_truth.validate_workflow_authority_docs",
        lambda repo_root: (),
    )
    monkeypatch.setattr(
        "bijux_proteomics_dev.release.governance.repository_truth.validate_workflow_claim_grounding",
        lambda repo_root: (),
    )
    monkeypatch.setattr(
        "bijux_proteomics_dev.release.governance.repository_truth.validate_workflow_intelligence_confidence",
        lambda repo_root: (),
    )
    monkeypatch.setattr(
        "bijux_proteomics_dev.release.governance.repository_truth.validate_workflow_lab_consequence",
        lambda: (),
    )
    monkeypatch.setattr(
        "bijux_proteomics_dev.release.governance.repository_truth.validate_workflow_consequence_coherence",
        lambda repo_root: (
            SimpleNamespace(
                code="family-posture-mismatch",
                detail=(
                    "lfq allows recommend_with_downgrade in intelligence but the shared consequence map still pins do_not_recommend"
                ),
            ),
        ),
    )
    monkeypatch.setattr(
        "bijux_proteomics_dev.release.governance.repository_truth.validate_workflow_public_scrutiny",
        lambda repo_root: (),
    )
    monkeypatch.setattr(
        "bijux_proteomics_dev.release.governance.repository_truth.validate_generated_governance_freshness",
        lambda: (),
    )
    monkeypatch.setattr(
        "bijux_proteomics_dev.release.governance.repository_truth.compare_ranking_policies_against_benchmark_corpus",
        lambda legacy, flagship: SimpleNamespace(
            decision_improved=True,
            corpus_id="mock-corpus",
        ),
    )
    monkeypatch.setattr(
        "bijux_proteomics_dev.release.governance.repository_truth.build_runtime_black_box_rerun_gate",
        lambda: SimpleNamespace(issues=()),
    )
    monkeypatch.setattr(
        "bijux_proteomics_dev.release.governance.repository_truth.build_flagship_acceptance_dashboard",
        lambda: SimpleNamespace(artifact_path="acceptance_dashboard.json", rows=()),
    )
    monkeypatch.setattr(
        "bijux_proteomics_dev.release.governance.repository_truth.build_public_artifact_index",
        lambda: SimpleNamespace(
            artifact_path="artifact_index.json",
            entries=tuple(
                SimpleNamespace(entry_id=f"entry-{index}") for index in range(17)
            ),
        ),
    )
    monkeypatch.setattr(
        "bijux_proteomics_dev.release.governance.repository_truth.build_public_artifact_role_matrix",
        lambda: SimpleNamespace(doc_path="public-artifact-role-matrix.md", rows=(1,)),
    )
    monkeypatch.setattr(
        "bijux_proteomics_dev.release.governance.repository_truth.validate_public_artifact_governance",
        lambda: (),
    )

    report = build_repository_truth_report(REPO_ROOT)

    assert (
        RepositoryTruthIssue(
            code="workflow-consequence-coherence-family-posture-mismatch",
            detail=(
                "lfq allows recommend_with_downgrade in intelligence but the shared consequence map still pins do_not_recommend"
            ),
        )
        in report.blockers
    )


def test_repository_truth_report_blocks_public_scrutiny_drift(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "bijux_proteomics_dev.release.governance.repository_truth.build_package_scorecard_report",
        lambda: SimpleNamespace(entries=(SimpleNamespace(architectural_ready=True),)),
    )
    monkeypatch.setattr(
        "bijux_proteomics_dev.release.governance.repository_truth.build_package_reopened_completion_claim_report",
        lambda: SimpleNamespace(entries=()),
    )
    monkeypatch.setattr(
        "bijux_proteomics_dev.release.governance.repository_truth.build_package_readme_maturity_report",
        lambda: SimpleNamespace(entries=()),
    )
    monkeypatch.setattr(
        "bijux_proteomics_dev.release.governance.repository_truth.build_package_family_readiness_reports",
        lambda repo_root: (SimpleNamespace(family_id="flagship", ready=True),),
    )
    monkeypatch.setattr(
        "bijux_proteomics_dev.release.governance.repository_truth.validate_flagship_workflow_manifest",
        lambda repo_root=None: (),
    )
    monkeypatch.setattr(
        "bijux_proteomics_dev.release.governance.repository_truth.validate_scientific_release_dossier",
        lambda repo_root: (),
    )
    monkeypatch.setattr(
        "bijux_proteomics_dev.release.governance.repository_truth.validate_workflow_authority_docs",
        lambda repo_root: (),
    )
    monkeypatch.setattr(
        "bijux_proteomics_dev.release.governance.repository_truth.validate_workflow_claim_grounding",
        lambda repo_root: (),
    )
    monkeypatch.setattr(
        "bijux_proteomics_dev.release.governance.repository_truth.validate_workflow_intelligence_confidence",
        lambda repo_root: (),
    )
    monkeypatch.setattr(
        "bijux_proteomics_dev.release.governance.repository_truth.validate_workflow_lab_consequence",
        lambda: (),
    )
    monkeypatch.setattr(
        "bijux_proteomics_dev.release.governance.repository_truth.validate_workflow_public_scrutiny",
        lambda repo_root: (
            SimpleNamespace(
                code="external-review-kit-not-ready",
                detail="dia external review kit is not ready for outsider review",
            ),
        ),
    )
    monkeypatch.setattr(
        "bijux_proteomics_dev.release.governance.repository_truth.validate_generated_governance_freshness",
        lambda: (),
    )
    monkeypatch.setattr(
        "bijux_proteomics_dev.release.governance.repository_truth.compare_ranking_policies_against_benchmark_corpus",
        lambda legacy, flagship: SimpleNamespace(
            decision_improved=True,
            corpus_id="mock-corpus",
        ),
    )
    monkeypatch.setattr(
        "bijux_proteomics_dev.release.governance.repository_truth.build_runtime_black_box_rerun_gate",
        lambda: SimpleNamespace(issues=()),
    )
    monkeypatch.setattr(
        "bijux_proteomics_dev.release.governance.repository_truth.build_flagship_acceptance_dashboard",
        lambda: SimpleNamespace(artifact_path="acceptance_dashboard.json", rows=()),
    )
    monkeypatch.setattr(
        "bijux_proteomics_dev.release.governance.repository_truth.build_public_artifact_index",
        lambda: SimpleNamespace(
            artifact_path="artifact_index.json",
            entries=tuple(
                SimpleNamespace(entry_id=f"entry-{index}") for index in range(17)
            ),
        ),
    )
    monkeypatch.setattr(
        "bijux_proteomics_dev.release.governance.repository_truth.build_public_artifact_role_matrix",
        lambda: SimpleNamespace(doc_path="public-artifact-role-matrix.md", rows=(1,)),
    )
    monkeypatch.setattr(
        "bijux_proteomics_dev.release.governance.repository_truth.validate_public_artifact_governance",
        lambda: (),
    )

    report = build_repository_truth_report(REPO_ROOT)

    assert (
        RepositoryTruthIssue(
            code="workflow-public-scrutiny-external-review-kit-not-ready",
            detail="dia external review kit is not ready for outsider review",
        )
        in report.blockers
    )


def test_repository_truth_report_blocks_public_artifact_governance_drift(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "bijux_proteomics_dev.release.governance.repository_truth.build_package_scorecard_report",
        lambda: SimpleNamespace(entries=(SimpleNamespace(architectural_ready=True),)),
    )
    monkeypatch.setattr(
        "bijux_proteomics_dev.release.governance.repository_truth.build_package_reopened_completion_claim_report",
        lambda: SimpleNamespace(entries=()),
    )
    monkeypatch.setattr(
        "bijux_proteomics_dev.release.governance.repository_truth.build_package_readme_maturity_report",
        lambda: SimpleNamespace(entries=()),
    )
    monkeypatch.setattr(
        "bijux_proteomics_dev.release.governance.repository_truth.build_package_family_readiness_reports",
        lambda repo_root: (SimpleNamespace(family_id="flagship", ready=True),),
    )
    monkeypatch.setattr(
        "bijux_proteomics_dev.release.governance.repository_truth.validate_flagship_workflow_manifest",
        lambda repo_root=None: (),
    )
    monkeypatch.setattr(
        "bijux_proteomics_dev.release.governance.repository_truth.validate_scientific_release_dossier",
        lambda repo_root: (),
    )
    monkeypatch.setattr(
        "bijux_proteomics_dev.release.governance.repository_truth.validate_workflow_authority_docs",
        lambda repo_root: (),
    )
    monkeypatch.setattr(
        "bijux_proteomics_dev.release.governance.repository_truth.validate_workflow_claim_grounding",
        lambda repo_root: (),
    )
    monkeypatch.setattr(
        "bijux_proteomics_dev.release.governance.repository_truth.validate_workflow_intelligence_confidence",
        lambda repo_root: (),
    )
    monkeypatch.setattr(
        "bijux_proteomics_dev.release.governance.repository_truth.validate_workflow_lab_consequence",
        lambda: (),
    )
    monkeypatch.setattr(
        "bijux_proteomics_dev.release.governance.repository_truth.validate_workflow_public_scrutiny",
        lambda repo_root: (),
    )
    monkeypatch.setattr(
        "bijux_proteomics_dev.release.governance.repository_truth.validate_generated_governance_freshness",
        lambda: (),
    )
    monkeypatch.setattr(
        "bijux_proteomics_dev.release.governance.repository_truth.compare_ranking_policies_against_benchmark_corpus",
        lambda legacy, flagship: SimpleNamespace(
            decision_improved=True,
            corpus_id="mock-corpus",
        ),
    )
    monkeypatch.setattr(
        "bijux_proteomics_dev.release.governance.repository_truth.build_runtime_black_box_rerun_gate",
        lambda: SimpleNamespace(issues=()),
    )
    monkeypatch.setattr(
        "bijux_proteomics_dev.release.governance.repository_truth.build_flagship_acceptance_dashboard",
        lambda: SimpleNamespace(artifact_path="acceptance_dashboard.json", rows=()),
    )
    monkeypatch.setattr(
        "bijux_proteomics_dev.release.governance.repository_truth.build_public_artifact_index",
        lambda: SimpleNamespace(
            artifact_path="artifact_index.json",
            entries=(),
        ),
    )
    monkeypatch.setattr(
        "bijux_proteomics_dev.release.governance.repository_truth.build_public_artifact_role_matrix",
        lambda: SimpleNamespace(doc_path="public-artifact-role-matrix.md", rows=()),
    )
    monkeypatch.setattr(
        "bijux_proteomics_dev.release.governance.repository_truth.validate_public_artifact_governance",
        lambda: (
            SimpleNamespace(
                code="public-artifact-count-growth",
                detail="public artifact count grew beyond the governed budget",
            ),
        ),
    )

    report = build_repository_truth_report(REPO_ROOT)

    assert (
        RepositoryTruthIssue(
            code="public-artifact-governance-public-artifact-count-growth",
            detail="public artifact count grew beyond the governed budget",
        )
        in report.blockers
    )
