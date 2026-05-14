from __future__ import annotations

from dataclasses import dataclass

from bijux_proteomics_intelligence.reviews.workflow_authority import (
    WorkflowAuthorityKind,
    build_workflow_authority_matrix,
)
from bijux_proteomics_lab.benchmarks.outcome_dossiers import (
    build_flagship_assay_worth_ledger,
    build_flagship_follow_up_outcome_dossier_family,
)

__all__ = [
    "WorkflowLabConsequenceIssue",
    "validate_workflow_lab_consequence",
]


@dataclass(frozen=True)
class WorkflowLabConsequenceIssue:
    """One unsupported use of lab-consequential workflow language."""

    code: str
    detail: str


def validate_workflow_lab_consequence() -> tuple[WorkflowLabConsequenceIssue, ...]:
    """Require outcome-bearing evidence before lab-consequential language is earned."""

    matrix = build_workflow_authority_matrix()
    dossiers = {
        dossier.workflow_family: dossier
        for dossier in build_flagship_follow_up_outcome_dossier_family().dossiers
    }
    worth_entries = {
        entry.workflow_family: entry
        for entry in build_flagship_assay_worth_ledger().entries
    }

    issues: list[WorkflowLabConsequenceIssue] = []
    for row in matrix.rows:
        lab_cell = next(
            cell
            for cell in row.cells
            if cell.authority_kind is WorkflowAuthorityKind.LAB_CONSEQUENTIAL
        )
        if not lab_cell.earned:
            continue

        dossier = dossiers.get(row.workflow_family)
        if dossier is None:
            issues.append(
                WorkflowLabConsequenceIssue(
                    code="lab-consequential-without-outcome-dossier",
                    detail=(
                        f"{row.workflow_family.value} is called lab-consequential without a shipped requested-versus-observed outcome dossier"
                    ),
                )
            )
        elif dossier.artifact_path not in lab_cell.artifact_paths:
            issues.append(
                WorkflowLabConsequenceIssue(
                    code="lab-consequential-without-dossier-traceability",
                    detail=(
                        f"{row.workflow_family.value} is called lab-consequential without pointing the authority cell at its shipped outcome dossier"
                    ),
                )
            )

        worth_entry = worth_entries.get(row.workflow_family)
        worth_ledger_path = build_flagship_assay_worth_ledger().artifact_path
        if worth_entry is None:
            issues.append(
                WorkflowLabConsequenceIssue(
                    code="lab-consequential-without-worth-ledger",
                    detail=(
                        f"{row.workflow_family.value} is called lab-consequential without a shipped assay-worth-it ledger row"
                    ),
                )
            )
        elif worth_ledger_path not in lab_cell.artifact_paths:
            issues.append(
                WorkflowLabConsequenceIssue(
                    code="lab-consequential-without-ledger-traceability",
                    detail=(
                        f"{row.workflow_family.value} is called lab-consequential without pointing the authority cell at the assay-worth-it ledger"
                    ),
                )
            )
    return tuple(issues)
