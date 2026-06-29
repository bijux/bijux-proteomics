# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Protein complex activity scoring over protein matrices with limiting subunits."""

from __future__ import annotations

from bijux_proteomics.domain import ConfidenceTier

from .analysis import (
    ComplexActivityPolicy,
    ComplexActivityReport,
    ComplexActivitySummary,
    ComplexConditionComparisonEntry,
    ComplexConditionScoreEntry,
    ComplexMemberContributionEntry,
    ComplexSampleScoreEntry,
    UnresolvedComplexActivityMemberEntry,
    build_complex_activity_report,
    render_complex_activity_condition_comparison_tsv,
    render_complex_activity_condition_score_tsv,
    render_complex_activity_matrix_tsv,
    render_complex_activity_sample_score_tsv,
    render_complex_activity_summary_tsv,
    render_complex_activity_unresolved_member_tsv,
    render_complex_member_contribution_tsv,
)

ComplexActivityConfidenceStatus = ConfidenceTier

__all__ = [
    "ComplexActivityConfidenceStatus",
    "ComplexActivityPolicy",
    "ComplexActivityReport",
    "ComplexActivitySummary",
    "ComplexConditionComparisonEntry",
    "ComplexConditionScoreEntry",
    "ComplexMemberContributionEntry",
    "ComplexSampleScoreEntry",
    "UnresolvedComplexActivityMemberEntry",
    "build_complex_activity_report",
    "render_complex_activity_condition_comparison_tsv",
    "render_complex_activity_condition_score_tsv",
    "render_complex_activity_matrix_tsv",
    "render_complex_activity_sample_score_tsv",
    "render_complex_activity_summary_tsv",
    "render_complex_activity_unresolved_member_tsv",
    "render_complex_member_contribution_tsv",
]
