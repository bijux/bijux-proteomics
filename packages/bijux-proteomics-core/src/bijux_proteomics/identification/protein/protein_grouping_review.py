# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Compatibility review wrappers over the owned protein grouping engine."""

from __future__ import annotations

from bijux_proteomics.identification.contracts import PsmRecord
from bijux_proteomics.identification.protein import protein_grouping as _owner

ProteinGroupingSummary = _owner.ProteinGroupingSummary
ProteinGroupingReviewEntry = _owner.ProteinGroupingEntry
ProteinGroupingReviewReport = _owner.ProteinGroupingReport
render_protein_grouping_summary_tsv = _owner.render_protein_grouping_summary_tsv
render_protein_grouping_entries_tsv = _owner.render_protein_grouping_entries_tsv


def build_protein_grouping_review_report(
    records: tuple[PsmRecord, ...],
) -> ProteinGroupingReviewReport:
    """Build the reviewer-facing protein grouping report from the owned engine."""
    return _owner.build_protein_grouping_report(records)
