# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Scientific comparison surfaces for advanced DIA-NN runtime outputs."""

from __future__ import annotations

from bijux_proteomics.dia.precursor_matrix import (
    DiaPrecursorExclusionEntry,
    DiaPrecursorExclusionReason,
)
from bijux_proteomics.review.claims.biological_claim_validation import (
    BiologicalClaimValidationEntry,
)
from bijux_proteomics.workflow.pipelines.advanced_diann import (
    AdvancedDiannProteinDecisionEntry,
    AdvancedDiannWorkflowReport,
)
from bijux_proteomics_runtime.workflows.advanced_diann import (
    AdvancedDiannRuntimeRunReport,
    AdvancedDiannRuntimeStatus,
)
from bijux_proteomics_runtime.workflows.advanced_diann_comparison_models import (
    AdvancedDiannClaimChangeEntry,
    AdvancedDiannClaimComparisonState,
    AdvancedDiannParameterChangeEntry,
    AdvancedDiannProteinChangeEntry,
    AdvancedDiannProteinComparisonState,
    AdvancedDiannRejectedRowChangeEntry,
    AdvancedDiannRejectedRowComparisonState,
    AdvancedDiannRuntimeComparisonReport,
)


def compare_advanced_diann_runtime_outputs(
    left: AdvancedDiannRuntimeRunReport,
    right: AdvancedDiannRuntimeRunReport,
) -> AdvancedDiannRuntimeComparisonReport:
    """Compare two completed advanced DIA-NN runtime runs scientifically."""

    left_report = _completed_advanced_report(left)
    right_report = _completed_advanced_report(right)

    parameter_changes = _parameter_changes(left_report, right_report)
    changed_proteins = _protein_changes(left_report, right_report)
    changed_claims = _claim_changes(left_report, right_report)
    changed_rejected_rows = _rejected_row_changes(left_report, right_report)

    equivalent = not any(
        (
            parameter_changes,
            changed_proteins,
            changed_claims,
            changed_rejected_rows,
        )
    )
    return AdvancedDiannRuntimeComparisonReport(
        left_workflow_id=left.workflow_id,
        right_workflow_id=right.workflow_id,
        equivalent=equivalent,
        parameter_changes=parameter_changes,
        changed_proteins=changed_proteins,
        changed_claims=changed_claims,
        changed_rejected_rows=changed_rejected_rows,
        note=(
            "advanced dia-nn runtime comparison explains scientific drift through "
            "parameter changes, protein decision changes, claim changes, and "
            "q-value-filtered precursor row changes"
        ),
    )


def _completed_advanced_report(
    run_report: AdvancedDiannRuntimeRunReport,
) -> AdvancedDiannWorkflowReport:
    if run_report.status is not AdvancedDiannRuntimeStatus.COMPLETED:
        raise ValueError("advanced dia-nn comparison requires completed runtime runs")
    if run_report.advanced_report is None:
        raise ValueError(
            "advanced dia-nn comparison requires a completed runtime run with an advanced report"
        )
    return run_report.advanced_report


def _parameter_changes(
    left: AdvancedDiannWorkflowReport,
    right: AdvancedDiannWorkflowReport,
) -> tuple[AdvancedDiannParameterChangeEntry, ...]:
    left_policy = left.diann_workflow.precursor_matrix_report.policy
    right_policy = right.diann_workflow.precursor_matrix_report.policy
    comparisons = (
        (
            "max_q_value",
            left_policy.max_q_value,
            right_policy.max_q_value,
            "precursor q-value filtering threshold changed",
        ),
        (
            "include_decoys",
            left_policy.include_decoys,
            right_policy.include_decoys,
            "decoy retention policy changed",
        ),
        (
            "q_value_filter_timing",
            left_policy.q_value_filter_timing.value,
            right_policy.q_value_filter_timing.value,
            "q-value filtering timing changed",
        ),
    )
    return tuple(
        AdvancedDiannParameterChangeEntry(
            parameter_name=parameter_name,
            left_value=left_value,
            right_value=right_value,
            note=note,
        )
        for parameter_name, left_value, right_value, note in comparisons
        if left_value != right_value
    )


def _protein_changes(
    left: AdvancedDiannWorkflowReport,
    right: AdvancedDiannWorkflowReport,
) -> tuple[AdvancedDiannProteinChangeEntry, ...]:
    left_entries = _protein_entries_by_group(left)
    right_entries = _protein_entries_by_group(right)
    changes: list[AdvancedDiannProteinChangeEntry] = []
    for protein_group_id in sorted(set(left_entries) | set(right_entries)):
        left_entry = left_entries.get(protein_group_id)
        right_entry = right_entries.get(protein_group_id)
        left_state = _protein_state(left_entry)
        right_state = _protein_state(right_entry)
        if left_state is right_state:
            continue
        representative = (
            None
            if left_entry is None and right_entry is None
            else (
                left_entry.representative_protein_ref
                if left_entry is not None
                else right_entry.representative_protein_ref
            )
        )
        changes.append(
            AdvancedDiannProteinChangeEntry(
                protein_group_id=protein_group_id,
                representative_protein_ref=representative,
                left_state=left_state,
                right_state=right_state,
                note=("protein-level advanced dia-nn decision changed between runs"),
            )
        )
    return tuple(changes)


def _claim_changes(
    left: AdvancedDiannWorkflowReport,
    right: AdvancedDiannWorkflowReport,
) -> tuple[AdvancedDiannClaimChangeEntry, ...]:
    left_entries = _claim_entries_by_id(left)
    right_entries = _claim_entries_by_id(right)
    changes: list[AdvancedDiannClaimChangeEntry] = []
    for claim_id in sorted(set(left_entries) | set(right_entries)):
        left_entry = left_entries.get(claim_id)
        right_entry = right_entries.get(claim_id)
        left_state = _claim_state(left_entry)
        right_state = _claim_state(right_entry)
        if left_state is right_state:
            continue
        entry = left_entry if left_entry is not None else right_entry
        if entry is None:
            raise RuntimeError(
                "advanced dia-nn claim comparison expected at least one changed claim entry"
            )
        changes.append(
            AdvancedDiannClaimChangeEntry(
                claim_id=claim_id,
                subject_id=entry.subject_id,
                claim_text=entry.claim_text,
                left_state=left_state,
                right_state=right_state,
                note="biological claim outcome changed between advanced dia-nn runs",
            )
        )
    return tuple(changes)


def _rejected_row_changes(
    left: AdvancedDiannWorkflowReport,
    right: AdvancedDiannWorkflowReport,
) -> tuple[AdvancedDiannRejectedRowChangeEntry, ...]:
    left_entries = _q_value_excluded_rows_by_precursor(left)
    right_entries = _q_value_excluded_rows_by_precursor(right)
    changes: list[AdvancedDiannRejectedRowChangeEntry] = []
    for precursor_id in sorted(set(left_entries) | set(right_entries)):
        left_entry = left_entries.get(precursor_id)
        right_entry = right_entries.get(precursor_id)
        left_state = _rejected_row_state(left_entry)
        right_state = _rejected_row_state(right_entry)
        if left_state is right_state:
            continue
        entry = left_entry if left_entry is not None else right_entry
        if entry is None:
            raise RuntimeError(
                "advanced dia-nn rejected-row comparison expected at least one changed precursor entry"
            )
        changes.append(
            AdvancedDiannRejectedRowChangeEntry(
                precursor_id=precursor_id,
                protein_group_id=entry.protein_group_id,
                sample_id=entry.sample_id,
                run_name=entry.run_name,
                left_state=left_state,
                right_state=right_state,
                left_q_value=None if left_entry is None else left_entry.q_value,
                right_q_value=None if right_entry is None else right_entry.q_value,
                note=(
                    "q-value-filtered precursor row changed retained-versus-rejected "
                    "state between advanced dia-nn runs"
                ),
            )
        )
    return tuple(changes)


def _protein_entries_by_group(
    report: AdvancedDiannWorkflowReport,
) -> dict[str, AdvancedDiannProteinDecisionEntry]:
    return {
        entry.protein_group_id: entry
        for entry in (
            *report.accepted_protein_decisions,
            *report.downgraded_protein_decisions,
        )
    }


def _claim_entries_by_id(
    report: AdvancedDiannWorkflowReport,
) -> dict[str, BiologicalClaimValidationEntry]:
    claim_validation = report.diann_workflow.biological_report.claim_validation_report
    if claim_validation is None:
        return {}
    return {
        entry.claim_id: entry
        for entry in (
            *claim_validation.supported_claims,
            *claim_validation.rejected_claims,
        )
    }


def _q_value_excluded_rows_by_precursor(
    report: AdvancedDiannWorkflowReport,
) -> dict[str, DiaPrecursorExclusionEntry]:
    return {
        entry.source_precursor_id: entry
        for entry in report.diann_workflow.precursor_matrix_report.excluded_entries
        if entry.reason is DiaPrecursorExclusionReason.Q_VALUE_THRESHOLD
    }


def _protein_state(
    entry: AdvancedDiannProteinDecisionEntry | None,
) -> AdvancedDiannProteinComparisonState:
    if entry is None:
        return AdvancedDiannProteinComparisonState.ABSENT
    if entry.downgrade_reasons:
        return AdvancedDiannProteinComparisonState.DOWNGRADED
    return AdvancedDiannProteinComparisonState.ACCEPTED


def _claim_state(
    entry: BiologicalClaimValidationEntry | None,
) -> AdvancedDiannClaimComparisonState:
    if entry is None:
        return AdvancedDiannClaimComparisonState.ABSENT
    if entry.status.value == "supported":
        return AdvancedDiannClaimComparisonState.SUPPORTED
    return AdvancedDiannClaimComparisonState.REJECTED


def _rejected_row_state(
    entry: DiaPrecursorExclusionEntry | None,
) -> AdvancedDiannRejectedRowComparisonState:
    if entry is None:
        return AdvancedDiannRejectedRowComparisonState.RETAINED
    return AdvancedDiannRejectedRowComparisonState.REJECTED


__all__ = [
    "AdvancedDiannRuntimeComparisonReport",
    "compare_advanced_diann_runtime_outputs",
]
