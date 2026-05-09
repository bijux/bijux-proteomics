from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from bijux_proteomics.benchmarks.workflow_generalization import (
    build_workflow_generalization_reports,
    count_public_packages_for_family,
)
from bijux_proteomics_intelligence.reviews.workflow_authority import (
    WorkflowAuthorityKind,
    build_workflow_authority_matrix,
)
from bijux_proteomics_knowledge.references.workflows.benchmarks import (
    KnowledgeWorkflowFamily,
)

__all__ = [
    "WorkflowAuthorityDocIssue",
    "validate_workflow_authority_docs",
]


@dataclass(frozen=True)
class WorkflowAuthorityDocIssue:
    """One docs-versus-authority mismatch in flagship release surfaces."""

    code: str
    detail: str


def validate_workflow_authority_docs(
    repo_root: Path,
) -> tuple[WorkflowAuthorityDocIssue, ...]:
    """Fail when release-facing docs overstate workflow authority."""

    matrix = build_workflow_authority_matrix()
    generalization_reports = {
        report.workflow_family: report
        for report in build_workflow_generalization_reports()
    }
    foundation_root = repo_root / "docs" / "01-bijux-proteomics" / "foundation"
    readme_text = (repo_root / "README.md").read_text(encoding="utf-8")
    release_text = (foundation_root / "flagship-release-candidate.md").read_text(
        encoding="utf-8"
    )
    matrix_text = (foundation_root / "workflow-claim-limits.md").read_text(
        encoding="utf-8"
    )

    outsider = tuple(
        row.workflow_family for row in matrix.rows if _cell_earned(row, WorkflowAuthorityKind.OUTSIDER_AUDITABLE)
    )
    internal_support = tuple(
        row.workflow_family
        for row in matrix.rows
        if row.public_release_language == "internal_support_only"
    )
    outsider_line = (
        "Outsider-auditable workflow families today: "
        + _format_family_sentence(outsider)
        + "."
    )
    internal_line = (
        "Internal-support-only workflow families today: "
        + _format_family_sentence(internal_support)
        + "."
    )

    issues: list[WorkflowAuthorityDocIssue] = []
    for label, text in (
        ("README.md", readme_text),
        ("docs/01-bijux-proteomics/foundation/flagship-release-candidate.md", release_text),
        ("docs/01-bijux-proteomics/foundation/workflow-claim-limits.md", matrix_text),
    ):
        if outsider_line not in text:
            issues.append(
                WorkflowAuthorityDocIssue(
                    code="missing-outsider-authority-line",
                    detail=f"{label} does not match the outsider-auditable workflow family set from the workflow authority matrix",
                )
            )
        if internal_line not in text:
            issues.append(
                WorkflowAuthorityDocIssue(
                    code="missing-internal-support-line",
                    detail=f"{label} does not match the internal-support workflow family set from the workflow authority matrix",
                )
            )

    for workflow_family in outsider:
        trust_doc = foundation_root / f"why-trust-{workflow_family.value}.md"
        if not trust_doc.is_file():
            issues.append(
                WorkflowAuthorityDocIssue(
                    code="missing-trust-page",
                    detail=f"{workflow_family.value} is outsider-auditable in the matrix but its trust page is missing",
                )
            )
            continue
        trust_text = trust_doc.read_text(encoding="utf-8")
        if count_public_packages_for_family(workflow_family.value) < 2:
            issues.append(
                WorkflowAuthorityDocIssue(
                    code="outsider-family-lacks-second-public-package",
                    detail=f"{workflow_family.value} still has family-level trust language but fewer than two tracked public packages",
                )
            )
        report = generalization_reports.get(workflow_family.value)
        if report is None:
            issues.append(
                WorkflowAuthorityDocIssue(
                    code="outsider-family-lacks-generalization-report",
                    detail=f"{workflow_family.value} still has family-level trust language but no published cross-package generalization report",
                )
            )
        elif report.artifact_path not in trust_text:
            issues.append(
                WorkflowAuthorityDocIssue(
                    code="trust-page-missing-generalization-link",
                    detail=f"{workflow_family.value} trust page does not link to its published cross-package generalization report",
                )
            )
    for workflow_family in internal_support:
        trust_doc = foundation_root / f"why-trust-{workflow_family.value}.md"
        if trust_doc.exists():
            issues.append(
                WorkflowAuthorityDocIssue(
                    code="internal-support-family-has-trust-page",
                    detail=f"{workflow_family.value} is internal-support only in the matrix but still has a trust page",
                )
            )
        boundary_doc = (
            foundation_root
            / f"why-{workflow_family.value}-stops-at-internal-support.md"
        )
        if not boundary_doc.is_file():
            issues.append(
                WorkflowAuthorityDocIssue(
                    code="missing-internal-support-limit-page",
                    detail=f"{workflow_family.value} is internal-support only in the matrix but its internal-support limit page is missing",
                )
            )
            continue
        report = generalization_reports.get(workflow_family.value)
        if report is not None:
            boundary_text = boundary_doc.read_text(encoding="utf-8")
            if report.artifact_path not in boundary_text:
                issues.append(
                    WorkflowAuthorityDocIssue(
                        code="internal-support-limit-page-missing-generalization-link",
                        detail=f"{workflow_family.value} internal-support limit page does not link to its published cross-package generalization report",
                    )
                )
    return tuple(issues)


def _cell_earned(row, authority_kind: WorkflowAuthorityKind) -> bool:
    return next(cell for cell in row.cells if cell.authority_kind == authority_kind).earned


def _format_family_sentence(
    workflow_families: tuple[KnowledgeWorkflowFamily, ...],
) -> str:
    return ", ".join(f"`{workflow_family.value}`" for workflow_family in workflow_families)
