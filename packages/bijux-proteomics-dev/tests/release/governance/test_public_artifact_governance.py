from __future__ import annotations

from types import SimpleNamespace

from bijux_proteomics_dev.release.governance.public_artifact_governance import (
    run,
    validate_public_artifact_governance,
)


def test_public_artifact_governance_docs_are_up_to_date() -> None:
    assert run(check=True) == 0


def test_public_artifact_governance_real_repo_has_no_live_failures() -> None:
    assert validate_public_artifact_governance() == ()


def test_public_artifact_governance_blocks_artifact_growth(monkeypatch) -> None:
    monkeypatch.setattr(
        "bijux_proteomics_dev.release.governance.public_artifact_governance.build_public_artifact_docs",
        lambda: (
            SimpleNamespace(
                artifact_budget=1,
                entries=(
                    SimpleNamespace(
                        entry_id="entry-1",
                        workflow_family=None,
                        owner_package="docs",
                        audience="reviewer",
                        question_answered="q1",
                        decision_role="role-1",
                        coexistence_rationale="r1",
                        stronger_neighbor=None,
                        weaker_neighbor=None,
                    ),
                    SimpleNamespace(
                        entry_id="entry-2",
                        workflow_family=None,
                        owner_package="docs",
                        audience="reviewer",
                        question_answered="q2",
                        decision_role="role-2",
                        coexistence_rationale="r2",
                        stronger_neighbor=None,
                        weaker_neighbor=None,
                    ),
                ),
            ),
            SimpleNamespace(rows=(SimpleNamespace(entry_id="entry-1"), SimpleNamespace(entry_id="entry-2"))),
        ),
    )

    issues = validate_public_artifact_governance()

    assert any(issue.code == "public-artifact-count-growth" for issue in issues)


def test_public_artifact_governance_blocks_role_overlap(monkeypatch) -> None:
    monkeypatch.setattr(
        "bijux_proteomics_dev.release.governance.public_artifact_governance.build_public_artifact_docs",
        lambda: (
            SimpleNamespace(
                artifact_budget=2,
                entries=(
                    SimpleNamespace(
                        entry_id="artifact-1",
                        workflow_family=None,
                        owner_package="docs",
                        audience="reviewer",
                        question_answered="q1",
                        decision_role="same-role",
                        coexistence_rationale="r1",
                        stronger_neighbor=None,
                        weaker_neighbor=None,
                    ),
                    SimpleNamespace(
                        entry_id="artifact-2",
                        workflow_family=None,
                        owner_package="docs",
                        audience="maintainer",
                        question_answered="q2",
                        decision_role="same-role",
                        coexistence_rationale="r2",
                        stronger_neighbor=None,
                        weaker_neighbor=None,
                    ),
                ),
            ),
            SimpleNamespace(
                rows=(
                    SimpleNamespace(entry_id="artifact-1"),
                    SimpleNamespace(entry_id="artifact-2"),
                )
            ),
        ),
    )

    issues = validate_public_artifact_governance()

    assert any(issue.code == "public-artifact-role-overlap" for issue in issues)


def test_public_artifact_governance_blocks_workflow_artifact_without_neighbor(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        "bijux_proteomics_dev.release.governance.public_artifact_governance.build_public_artifact_docs",
        lambda: (
            SimpleNamespace(
                artifact_budget=1,
                entries=(
                    SimpleNamespace(
                        entry_id="artifact-1",
                        workflow_family=SimpleNamespace(value="dda"),
                        owner_package="docs",
                        audience="scientist",
                        question_answered="q1",
                        decision_role="workflow-justification",
                        coexistence_rationale="r1",
                        stronger_neighbor=None,
                        weaker_neighbor=None,
                    ),
                ),
            ),
            SimpleNamespace(rows=(SimpleNamespace(entry_id="artifact-1"),)),
        ),
    )

    issues = validate_public_artifact_governance()

    assert any(issue.code == "workflow-artifact-missing-neighbor" for issue in issues)
