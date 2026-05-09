from __future__ import annotations

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
