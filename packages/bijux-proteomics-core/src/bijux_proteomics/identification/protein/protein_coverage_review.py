# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Compatibility review surface over the owned protein coverage engine."""

from __future__ import annotations

from bijux_proteomics.identification.contracts import PsmRecord
from bijux_proteomics.identification.protein.protein_coverage import (
    ProteinCoveragePeptideCoordinateEntry,
    ProteinCoverageProteinEntry,
    ProteinCoverageRegionEntry,
    ProteinCoverageReport,
    ProteinCoverageSummary,
    ProteinCoverageUncoveredRegionEntry,
    build_protein_coverage_report,
    render_protein_coverage_entries_tsv,
    render_protein_coverage_peptide_coordinates_tsv,
    render_protein_coverage_regions_tsv,
    render_protein_coverage_summary_tsv,
    render_protein_coverage_uncovered_regions_tsv,
)

ProteinCoverageReviewSummary = ProteinCoverageSummary
ProteinCoverageReviewEntry = ProteinCoverageProteinEntry
ProteinCoverageReviewReport = ProteinCoverageReport


def build_protein_coverage_review_report(
    records: tuple[PsmRecord, ...],
    *,
    protein_sequences: dict[str, str],
    threshold: float | None = None,
    score_orientation: str = "higher_better",
) -> ProteinCoverageReviewReport:
    """Build the reviewer-facing protein coverage packet from the owner surface."""
    return build_protein_coverage_report(
        records,
        protein_sequences=protein_sequences,
        threshold=threshold,
        score_orientation=score_orientation,
    )


__all__ = [
    "ProteinCoveragePeptideCoordinateEntry",
    "ProteinCoverageProteinEntry",
    "ProteinCoverageRegionEntry",
    "ProteinCoverageReviewEntry",
    "ProteinCoverageReviewReport",
    "ProteinCoverageReviewSummary",
    "ProteinCoverageSummary",
    "ProteinCoverageUncoveredRegionEntry",
    "build_protein_coverage_review_report",
    "render_protein_coverage_entries_tsv",
    "render_protein_coverage_peptide_coordinates_tsv",
    "render_protein_coverage_regions_tsv",
    "render_protein_coverage_summary_tsv",
    "render_protein_coverage_uncovered_regions_tsv",
]
