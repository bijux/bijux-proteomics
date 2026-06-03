from __future__ import annotations

from pathlib import Path

import pytest

from bijux_proteomics_dev.release.governance.workflow_authority_docs import (
    validate_workflow_authority_docs,
)

REPO_ROOT = next(
    parent
    for parent in Path(__file__).resolve().parents
    if (parent / "packages").is_dir() and (parent / "configs").is_dir()
)


def test_docs_workflow_authority_surface_match_matrix() -> None:
    assert validate_workflow_authority_docs(REPO_ROOT) == ()


def test_docs_workflow_authority_surface_require_second_public_package_for_family_trust(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "bijux_proteomics_dev.release.governance.workflow_authority_docs.count_public_packages_for_family",
        lambda workflow_family: 1 if workflow_family == "dda" else 2,
    )

    issues = validate_workflow_authority_docs(REPO_ROOT)

    assert any(
        issue.code == "outsider-family-lacks-second-public-package"
        and "dda" in issue.detail
        for issue in issues
    )


def test_docs_workflow_authority_surface_require_generalization_report_for_family_trust(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original_validate = validate_workflow_authority_docs
    from bijux_proteomics.benchmarks.workflow_generalization import (
        build_workflow_generalization_reports,
    )

    monkeypatch.setattr(
        "bijux_proteomics_dev.release.governance.workflow_authority_docs.build_workflow_generalization_reports",
        lambda: tuple(
            report
            for report in build_workflow_generalization_reports()
            if report.workflow_family != "dda"
        ),
    )

    issues = original_validate(REPO_ROOT)

    assert any(
        issue.code == "outsider-family-lacks-generalization-report"
        and "dda" in issue.detail
        for issue in issues
    )
