from __future__ import annotations

import bijux_proteomics_dev.release.governance.final_preflight as final_preflight_module
from bijux_proteomics_dev.release.governance.final_preflight import (
    FINAL_PREFLIGHT_STAGE_IDS,
    FinalPreflightIssue,
    FinalPreflightReport,
    FinalPreflightStage,
    build_final_preflight_report,
    run,
)


def test_final_preflight_keeps_exact_stage_order() -> None:
    report = build_final_preflight_report()

    assert FINAL_PREFLIGHT_STAGE_IDS == (
        "docs-clarity",
        "package-boundaries",
        "benchmark-assets",
        "runtime-reproducibility",
        "consequence-coherence",
        "artifact-hygiene",
    )
    assert tuple(stage.stage_id for stage in report.stages) == FINAL_PREFLIGHT_STAGE_IDS


def test_final_preflight_returns_failure_when_any_stage_has_issues(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        "bijux_proteomics_dev.release.governance.final_preflight.build_final_preflight_report",
        lambda repo_root: FinalPreflightReport(
            stages=(
                FinalPreflightStage(
                    stage_id="docs-clarity",
                    label="docs clarity",
                    issues=(FinalPreflightIssue(code="readme-truth", detail="blocked"),),
                ),
            )
        ),
    )

    assert run() == 1


def test_final_preflight_returns_success_when_all_stages_pass(monkeypatch) -> None:
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


def test_docs_stage_blocks_stale_public_artifact_docs(monkeypatch) -> None:
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

    assert FinalPreflightIssue(
        code="stale-generated-doc-surface",
        detail=(
            "bijux_proteomics_dev.release.governance.public_artifact_governance "
            "is stale; regenerate it before release preflight"
        ),
    ) in stage.issues
