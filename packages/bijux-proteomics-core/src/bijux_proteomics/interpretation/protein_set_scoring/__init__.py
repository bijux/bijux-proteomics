# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Protein-set scoring surfaces for sample-level biological program review."""

from __future__ import annotations

from bijux_proteomics.domain import ConfidenceTier
from bijux_proteomics.interpretation.protein_set_scoring.analysis import (
    build_protein_set_scoring_report,
    render_protein_set_condition_comparison_tsv,
    render_protein_set_condition_score_tsv,
    render_protein_set_sample_score_tsv,
    render_protein_set_score_matrix_tsv,
    render_protein_set_scoring_summary_tsv,
    render_protein_set_unresolved_member_tsv,
    render_rejected_protein_set_tsv,
)
from bijux_proteomics.interpretation.protein_set_scoring.definition_import import (
    parse_protein_set_table,
)
from bijux_proteomics.interpretation.protein_set_scoring.models import (
    ProteinSetColumnMapping,
    ProteinSetConditionComparisonEntry,
    ProteinSetConditionScoreEntry,
    ProteinSetImportReport,
    ProteinSetImportSummary,
    ProteinSetRecord,
    ProteinSetSampleScoreEntry,
    ProteinSetScoringPolicy,
    ProteinSetScoringReport,
    ProteinSetScoringSummary,
    RejectedProteinSetRow,
    UnresolvedProteinSetMemberEntry,
)

ProteinSetScoreConfidenceStatus = ConfidenceTier

__all__ = [
    "ProteinSetColumnMapping",
    "ProteinSetConditionComparisonEntry",
    "ProteinSetConditionScoreEntry",
    "ProteinSetScoreConfidenceStatus",
    "ProteinSetImportReport",
    "ProteinSetImportSummary",
    "ProteinSetRecord",
    "ProteinSetSampleScoreEntry",
    "ProteinSetScoringPolicy",
    "ProteinSetScoringReport",
    "ProteinSetScoringSummary",
    "RejectedProteinSetRow",
    "UnresolvedProteinSetMemberEntry",
    "build_protein_set_scoring_report",
    "parse_protein_set_table",
    "render_protein_set_condition_comparison_tsv",
    "render_protein_set_condition_score_tsv",
    "render_protein_set_sample_score_tsv",
    "render_protein_set_score_matrix_tsv",
    "render_protein_set_scoring_summary_tsv",
    "render_protein_set_unresolved_member_tsv",
    "render_rejected_protein_set_tsv",
]
