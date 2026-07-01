# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Pathway activity scoring over protein matrices with explicit member coverage."""

from __future__ import annotations

from bijux_proteomics.domain.confidence import (
    ConfidenceTier as PathwayActivityConfidenceStatus,
)

from .analysis import (
    build_pathway_activity_report,
)
from .models import (
    PathwayActivityPolicy,
    PathwayActivityReport,
    PathwayActivitySummary,
    PathwayConditionComparisonEntry,
    PathwayConditionScoreEntry,
    PathwayMemberContributionEntry,
    PathwaySampleScoreEntry,
    UnresolvedPathwayActivityMemberEntry,
)
from .rendering import (
    render_pathway_activity_condition_comparison_tsv,
    render_pathway_activity_condition_score_tsv,
    render_pathway_activity_matrix_tsv,
    render_pathway_activity_sample_score_tsv,
    render_pathway_activity_summary_tsv,
    render_pathway_activity_unresolved_member_tsv,
    render_pathway_member_contribution_tsv,
)

__all__ = [
    "PathwayActivityConfidenceStatus",
    "PathwayActivityPolicy",
    "PathwayActivityReport",
    "PathwayActivitySummary",
    "PathwayConditionComparisonEntry",
    "PathwayConditionScoreEntry",
    "PathwayMemberContributionEntry",
    "PathwaySampleScoreEntry",
    "UnresolvedPathwayActivityMemberEntry",
    "build_pathway_activity_report",
    "render_pathway_activity_condition_comparison_tsv",
    "render_pathway_activity_condition_score_tsv",
    "render_pathway_activity_matrix_tsv",
    "render_pathway_activity_sample_score_tsv",
    "render_pathway_activity_summary_tsv",
    "render_pathway_activity_unresolved_member_tsv",
    "render_pathway_member_contribution_tsv",
]
