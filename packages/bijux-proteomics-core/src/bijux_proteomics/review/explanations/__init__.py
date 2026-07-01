# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Canonical scientific explanation and narrative surfaces."""

from __future__ import annotations

from importlib import import_module
from typing import Any

from bijux_proteomics.review.explanations.failure_explanations import (
    FailureExplanation,
    FailureExplanationCategory,
    FailureExplanationReport,
    FailureExplanationRequest,
    FailureExplanationStatus,
    FailureExplanationSummary,
    build_failure_explanation_report,
    format_failure_explanation_for_cli,
    render_failure_explanation_summary_tsv,
    render_failure_explanation_tsv,
)
from bijux_proteomics.review.explanations.result_explanations import (
    ResultExplanation,
    ResultExplanationEvidenceRole,
    ResultExplanationKind,
    ResultExplanationPoint,
    ResultExplanationReport,
    ResultExplanationRequest,
    ResultExplanationStatus,
    ResultExplanationSummary,
    build_result_explanation_report_from_artifacts,
    render_result_explanation_evidence_tsv,
    render_result_explanation_summary_tsv,
    render_result_explanation_tsv,
)
from bijux_proteomics.review.explanations.scientific_conflicts import (
    ScientificConflictFinding,
    ScientificConflictFindingCode,
    ScientificConflictReport,
    ScientificUntrustworthyChecklist,
    ScientificWorkflowFamily,
    UntrustworthyChecklistEntry,
    build_scientific_untrustworthy_checklists,
    evaluate_domain_conflicts,
)
from bijux_proteomics.review.explanations.scientific_story import (
    ScientificConsistencyIssue,
    ScientificConsistencyIssueCode,
    ScientificConsistencyReport,
    WorkflowScientificSnapshot,
    build_workflow_scientific_snapshot,
    evaluate_workflow_scientific_consistency,
)
from bijux_proteomics.review.explanations.volcano_plots import (
    VolcanoReviewPoint,
    VolcanoReviewPolicy,
    VolcanoReviewReport,
    VolcanoReviewSourceKind,
    apply_volcano_review_policy,
    build_dia_volcano_review,
    build_label_based_volcano_review,
    build_ptm_volcano_review,
    build_quantification_volcano_review,
    export_volcano_review_html,
    export_volcano_review_json,
    export_volcano_review_svg,
    render_volcano_review_html,
    render_volcano_review_json,
    render_volcano_review_svg,
    render_volcano_review_tsv,
)

_LAZY_EXPLANATION_EXPORTS = {
    "ScientificFailureAtlasEntry": (
        "bijux_proteomics.review.explanations.scientific_failure_atlas"
    ),
    "ScientificFailureAtlasReport": (
        "bijux_proteomics.review.explanations.scientific_failure_atlas"
    ),
    "ScientificFailureSeverity": (
        "bijux_proteomics.review.explanations.scientific_failure_atlas"
    ),
    "build_scientific_failure_atlas_report": (
        "bijux_proteomics.review.explanations.scientific_failure_atlas"
    ),
}


def __getattr__(name: str) -> Any:
    module_path = _LAZY_EXPLANATION_EXPORTS.get(name)
    if module_path is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    module = import_module(module_path)
    value = getattr(module, name)
    globals()[name] = value
    return value


__all__ = [
    "FailureExplanation",
    "FailureExplanationCategory",
    "FailureExplanationReport",
    "FailureExplanationRequest",
    "FailureExplanationStatus",
    "FailureExplanationSummary",
    "ResultExplanation",
    "ResultExplanationEvidenceRole",
    "ResultExplanationKind",
    "ResultExplanationPoint",
    "ResultExplanationReport",
    "ResultExplanationRequest",
    "ResultExplanationStatus",
    "ResultExplanationSummary",
    "ScientificConflictFinding",
    "ScientificConflictFindingCode",
    "ScientificConflictReport",
    "ScientificConsistencyIssue",
    "ScientificConsistencyIssueCode",
    "ScientificConsistencyReport",
    "ScientificFailureAtlasEntry",
    "ScientificFailureAtlasReport",
    "ScientificFailureSeverity",
    "ScientificUntrustworthyChecklist",
    "ScientificWorkflowFamily",
    "UntrustworthyChecklistEntry",
    "VolcanoReviewPoint",
    "VolcanoReviewPolicy",
    "VolcanoReviewReport",
    "VolcanoReviewSourceKind",
    "WorkflowScientificSnapshot",
    "apply_volcano_review_policy",
    "build_dia_volcano_review",
    "build_failure_explanation_report",
    "build_label_based_volcano_review",
    "build_ptm_volcano_review",
    "build_quantification_volcano_review",
    "build_result_explanation_report_from_artifacts",
    "build_scientific_failure_atlas_report",
    "build_scientific_untrustworthy_checklists",
    "build_workflow_scientific_snapshot",
    "evaluate_domain_conflicts",
    "evaluate_workflow_scientific_consistency",
    "export_volcano_review_html",
    "export_volcano_review_json",
    "export_volcano_review_svg",
    "format_failure_explanation_for_cli",
    "render_failure_explanation_summary_tsv",
    "render_failure_explanation_tsv",
    "render_result_explanation_evidence_tsv",
    "render_result_explanation_summary_tsv",
    "render_result_explanation_tsv",
    "render_volcano_review_html",
    "render_volcano_review_json",
    "render_volcano_review_svg",
    "render_volcano_review_tsv",
]
