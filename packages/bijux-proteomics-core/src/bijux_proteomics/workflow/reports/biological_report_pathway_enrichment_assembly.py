# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Pathway enrichment and activity assembly for biological report bundles."""

from __future__ import annotations

from typing import TYPE_CHECKING, NamedTuple

from bijux_proteomics.interpretation.pathway_activity import (
    build_pathway_activity_report,
)
from bijux_proteomics.interpretation.pathway_enrichment import (
    PathwayEnrichmentCorrectionPolicy,
    apply_pathway_enrichment_multiple_testing,
    build_pathway_enrichment_report,
)

if TYPE_CHECKING:
    from bijux_proteomics.interpretation.pathway_activity.models import (
        PathwayActivityReport,
    )
    from bijux_proteomics.interpretation.pathway_enrichment import (
        PathwayEnrichmentReport,
        PathwayMembershipRecord,
    )
    from bijux_proteomics.interpretation.protein_annotation_mapping import (
        ProteinAnnotationRecord,
        ProteinReferenceEntry,
    )
    from bijux_proteomics.io.formats import ExperimentalDesignEntry
    from bijux_proteomics.quantification.contracts import LabelFreeQuantTable
    from bijux_proteomics.sequences.core import NormalizedProteinRecord
    from bijux_proteomics.workflow.reports.biological_report_selection_policy import (
        BiologicalResultSelectionPolicy,
    )


class BiologicalPathwayEnrichmentReports(NamedTuple):
    """Pathway-scoped enrichment assembly outputs."""

    pathway_activity_report: PathwayActivityReport | None
    pathway_enrichment_report: PathwayEnrichmentReport | None


def _build_biological_pathway_enrichment_reports(
    *,
    normalized_table: LabelFreeQuantTable,
    design_entries: tuple[ExperimentalDesignEntry, ...],
    fasta_records: tuple[NormalizedProteinRecord, ...],
    custom_annotations: tuple[ProteinAnnotationRecord, ...],
    pathway_records: tuple[PathwayMembershipRecord, ...],
    enrichment_foreground_entries: tuple[ProteinReferenceEntry, ...],
    enrichment_background_entries: tuple[ProteinReferenceEntry, ...],
    active_selection_policy: BiologicalResultSelectionPolicy,
) -> BiologicalPathwayEnrichmentReports:
    if not pathway_records:
        return BiologicalPathwayEnrichmentReports(
            pathway_activity_report=None,
            pathway_enrichment_report=None,
        )

    pathway_activity_report = build_pathway_activity_report(
        normalized_table,
        pathway_records,
        design_entries=design_entries,
        fasta_records=fasta_records,
        custom_annotations=custom_annotations,
    )
    pathway_enrichment_report = apply_pathway_enrichment_multiple_testing(
        build_pathway_enrichment_report(
            enrichment_foreground_entries,
            enrichment_background_entries,
            pathway_records,
            fasta_records=fasta_records,
            custom_annotations=custom_annotations,
        ),
        policy=PathwayEnrichmentCorrectionPolicy(
            max_adjusted_p_value=active_selection_policy.max_adjusted_p_value,
            min_enrichment_ratio=1.0,
        ),
    )
    return BiologicalPathwayEnrichmentReports(
        pathway_activity_report=pathway_activity_report,
        pathway_enrichment_report=pathway_enrichment_report,
    )
