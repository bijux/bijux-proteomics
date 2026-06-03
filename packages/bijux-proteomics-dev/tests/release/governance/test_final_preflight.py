from __future__ import annotations

from _pytest.monkeypatch import MonkeyPatch

import bijux_proteomics_dev.release.governance.final_preflight as final_preflight_module
from bijux_proteomics_dev.release.governance.final_preflight import (
    FINAL_PREFLIGHT_STAGE_IDS,
    FinalPreflightIssue,
    FinalPreflightReport,
    FinalPreflightStage,
    run,
)
from bijux_proteomics_dev.release.governance.test_collection_gate import (
    CollectionGateCheck,
    CollectionGateReport,
)


def test_final_preflight_returns_failure_when_any_stage_has_issues(
    monkeypatch: MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "bijux_proteomics_dev.release.governance.final_preflight.build_final_preflight_report",
        lambda repo_root: FinalPreflightReport(
            stages=(
                FinalPreflightStage(
                    stage_id="docs-clarity",
                    label="docs clarity",
                    issues=(
                        FinalPreflightIssue(code="readme-truth", detail="blocked"),
                    ),
                ),
            )
        ),
    )

    assert run() == 1


def test_final_preflight_returns_success_when_all_stages_pass(
    monkeypatch: MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "bijux_proteomics_dev.release.governance.final_preflight.build_final_preflight_report",
        lambda repo_root: FinalPreflightReport(
            stages=tuple(
                FinalPreflightStage(stage_id=stage_id, label=stage_id, issues=())
                for stage_id in FINAL_PREFLIGHT_STAGE_IDS
            )
        ),
    )

    assert run() == 0


def test_docs_stage_blocks_stale_public_artifact_docs(
    monkeypatch: MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        final_preflight_module,
        "validate_readme_truth",
        lambda repo_root: (),
    )
    monkeypatch.setattr(
        final_preflight_module,
        "validate_workflow_authority_docs",
        lambda repo_root: (),
    )
    monkeypatch.setattr(
        final_preflight_module,
        "validate_workflow_public_scrutiny",
        lambda repo_root: (),
    )
    monkeypatch.setattr(
        final_preflight_module,
        "run_hostile_review_pages",
        lambda check=True: 0,
    )
    monkeypatch.setattr(
        final_preflight_module,
        "run_release_narrowing_protocol",
        lambda check=True: 0,
    )
    monkeypatch.setattr(
        final_preflight_module,
        "run_public_language",
        lambda check=True: 0,
    )
    monkeypatch.setattr(
        final_preflight_module,
        "run_public_artifact_governance",
        lambda check=True: 1,
    )

    stage = final_preflight_module._docs_stage(final_preflight_module.REPO_ROOT)

    assert (
        FinalPreflightIssue(
            code="stale-generated-doc-surface",
            detail=(
                "bijux_proteomics_dev.release.governance.public_artifact_governance "
                "is stale; regenerate it before release preflight"
            ),
        )
        in stage.issues
    )


def test_consequence_stage_blocks_stale_consequence_docs(
    monkeypatch: MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        final_preflight_module,
        "validate_workflow_intelligence_confidence",
        lambda repo_root: (),
    )
    monkeypatch.setattr(
        final_preflight_module,
        "validate_workflow_lab_consequence",
        lambda: (),
    )
    monkeypatch.setattr(
        final_preflight_module,
        "validate_workflow_consequence_coherence",
        lambda repo_root: (),
    )
    monkeypatch.setattr(
        final_preflight_module,
        "run_workflow_consequence_docs",
        lambda check=True: 1,
    )

    stage = final_preflight_module._consequence_coherence_stage(
        final_preflight_module.REPO_ROOT
    )

    assert (
        FinalPreflightIssue(
            code="stale-generated-doc-surface",
            detail=(
                "bijux_proteomics_dev.release.governance.workflow_consequence_docs "
                "is stale; regenerate it before release preflight"
            ),
        )
        in stage.issues
    )


def test_test_collection_stage_normalizes_failed_gate_checks(
    monkeypatch: MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        final_preflight_module,
        "build_test_collection_gate_report",
        lambda repo_root: CollectionGateReport(
            import_checks=(
                CollectionGateCheck(
                    check_kind="import",
                    package_name="bijux-proteomics-core",
                    target="bijux_proteomics",
                    command=("python", "-c", "import bijux_proteomics"),
                    ok=False,
                    detail="module import failed",
                ),
            ),
            collection_checks=(
                CollectionGateCheck(
                    check_kind="collection",
                    package_name="agentic-proteins",
                    target="packages/agentic-proteins/tests",
                    command=("python", "-m", "pytest"),
                    ok=False,
                    detail="pytest collection failed",
                ),
            ),
        ),
    )

    stage = final_preflight_module._test_collection_stage(
        final_preflight_module.REPO_ROOT
    )

    assert stage.stage_id == "test-collection"
    assert stage.label == "test collection"
    assert stage.issues == (
        FinalPreflightIssue(
            code="import-check-failed",
            detail=(
                "bijux-proteomics-core import check failed for bijux_proteomics: "
                "module import failed"
            ),
        ),
        FinalPreflightIssue(
            code="collection-check-failed",
            detail=(
                "agentic-proteins collection check failed for "
                "packages/agentic-proteins/tests: pytest collection failed"
            ),
        ),
    )
