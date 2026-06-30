from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

from bijux_proteomics_dev.release.governance.workflow_public_scrutiny import (
    WorkflowPublicScrutinyIssue,
    validate_workflow_public_scrutiny,
)

REPO_ROOT = next(
    parent
    for parent in Path(__file__).resolve().parents
    if (parent / "packages").is_dir() and (parent / "configs").is_dir()
)


def test_workflow_public_scrutiny_real_repo_keeps_black_box_language_gap_visible() -> (
    None
):
    issues = validate_workflow_public_scrutiny(REPO_ROOT)

    assert any(
        issue.code == "black-box-language-outruns-rerun-evidence" for issue in issues
    )


def test_workflow_public_scrutiny_blocks_unready_external_review_kit(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "bijux_proteomics_dev.release.governance.workflow_public_scrutiny.validate_public_artifact_governance",
        lambda: (),
    )
    monkeypatch.setattr(
        "bijux_proteomics_dev.release.governance.workflow_public_scrutiny.build_workflow_external_review_kit_family",
        lambda: SimpleNamespace(
            kits=(
                SimpleNamespace(
                    workflow_family=SimpleNamespace(value="dia"),
                    standalone_verifier_report=SimpleNamespace(verified=False),
                    ready_for_outsider_review=False,
                ),
            )
        ),
    )
    monkeypatch.setattr(
        "bijux_proteomics_dev.release.governance.workflow_public_scrutiny._earned_outsider_auditable_workflow_families",
        lambda: frozenset({"dia"}),
    )

    issues = validate_workflow_public_scrutiny(REPO_ROOT)

    assert (
        WorkflowPublicScrutinyIssue(
            code="external-review-kit-not-standalone-verifiable",
            detail="dia external review kit does not survive standalone verification",
        )
        in issues
    )
    assert (
        WorkflowPublicScrutinyIssue(
            code="external-review-kit-not-ready",
            detail="dia external review kit is not ready for outsider review",
        )
        in issues
    )


def test_workflow_public_scrutiny_ignores_unready_review_grade_family(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "bijux_proteomics_dev.release.governance.workflow_public_scrutiny.validate_public_artifact_governance",
        lambda: (),
    )
    monkeypatch.setattr(
        "bijux_proteomics_dev.release.governance.workflow_public_scrutiny.build_workflow_external_review_kit_family",
        lambda: SimpleNamespace(
            kits=(
                SimpleNamespace(
                    workflow_family=SimpleNamespace(value="lfq"),
                    standalone_verifier_report=SimpleNamespace(verified=False),
                    ready_for_outsider_review=False,
                ),
            )
        ),
    )
    monkeypatch.setattr(
        "bijux_proteomics_dev.release.governance.workflow_public_scrutiny._earned_outsider_auditable_workflow_families",
        lambda: frozenset({"dda", "dia", "ptm", "targeted"}),
    )

    issues = validate_workflow_public_scrutiny(REPO_ROOT)

    assert not any(
        issue.code.startswith("external-review-kit-")
        for issue in issues
    )


def test_workflow_public_scrutiny_blocks_banned_release_language(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "bijux_proteomics_dev.release.governance.workflow_public_scrutiny._read_target_doc",
        lambda repo_root, relative_path: "This surface is scientifically credible.",
    )

    issues = validate_workflow_public_scrutiny(REPO_ROOT)

    assert any(issue.code == "banned-strong-release-language" for issue in issues)


def test_workflow_public_scrutiny_blocks_artifact_role_drift(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "bijux_proteomics_dev.release.governance.workflow_public_scrutiny.validate_public_artifact_governance",
        lambda: (
            SimpleNamespace(
                code="public-artifact-count-growth",
                detail="public artifact count grew beyond the governed budget",
            ),
        ),
    )

    issues = validate_workflow_public_scrutiny(REPO_ROOT)

    assert (
        WorkflowPublicScrutinyIssue(
            code="public-artifact-count-growth",
            detail="public artifact count grew beyond the governed budget",
        )
        in issues
    )
