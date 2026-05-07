from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

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
    foundation_root = repo_root / "docs" / "01-bijux-proteomics" / "foundation"
    readme_text = (repo_root / "README.md").read_text(encoding="utf-8")
    release_text = (foundation_root / "flagship-release-candidate.md").read_text(
        encoding="utf-8"
    )
    matrix_text = (foundation_root / "workflow-authority-matrix.md").read_text(
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
        ("docs/01-bijux-proteomics/foundation/workflow-authority-matrix.md", matrix_text),
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
    for workflow_family in internal_support:
        trust_doc = foundation_root / f"why-trust-{workflow_family.value}.md"
        if trust_doc.exists():
            issues.append(
                WorkflowAuthorityDocIssue(
                    code="internal-support-family-has-trust-page",
                    detail=f"{workflow_family.value} is internal-support only in the matrix but still has a trust page",
                )
            )
        boundary_doc = foundation_root / f"{workflow_family.value}-authority-boundary.md"
        if not boundary_doc.is_file():
            issues.append(
                WorkflowAuthorityDocIssue(
                    code="missing-authority-boundary-page",
                    detail=f"{workflow_family.value} is internal-support only in the matrix but its authority boundary page is missing",
                )
            )
    return tuple(issues)


def _cell_earned(row, authority_kind: WorkflowAuthorityKind) -> bool:
    return next(cell for cell in row.cells if cell.authority_kind == authority_kind).earned


def _format_family_sentence(
    workflow_families: tuple[KnowledgeWorkflowFamily, ...],
) -> str:
    return ", ".join(f"`{workflow_family.value}`" for workflow_family in workflow_families)
