# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi
"""Enrichment and activity assembly for biological report bundles."""

from __future__ import annotations

from typing import TYPE_CHECKING, NamedTuple

from bijux_proteomics.workflow.reports.biological_report_complex_enrichment_assembly import (
    _build_biological_complex_enrichment_reports,
)
from bijux_proteomics.workflow.reports.biological_report_foreground_background_assembly import (
    _build_biological_enrichment_input_sets,
)
from bijux_proteomics.workflow.reports.biological_report_go_enrichment_assembly import (
    _build_biological_go_enrichment_report,
)
from bijux_proteomics.workflow.reports.biological_report_pathway_enrichment_assembly import (
    _build_biological_pathway_enrichment_reports,
)

if TYPE_CHECKING:
    from bijux_proteomics.interpretation.complex_activity.models import (
        ComplexActivityReport,
    )
    from bijux_proteomics.interpretation.complex_enrichment import (
        ComplexEnrichmentReport,
        ComplexMembershipRecord,
    )
    from bijux_proteomics.interpretation.foreground_background_model import (
        BiologicalForegroundBackgroundModel,
    )
    from bijux_proteomics.interpretation.go_enrichment import (
        GoAnnotationRecord,
        GoEnrichmentReport,
    )
    from bijux_proteomics.interpretation.pathway_activity.models import (
        PathwayActivityReport,
    )
    from bijux_proteomics.interpretation.pathway_enrichment import (
        PathwayEnrichmentReport,
        PathwayMembershipRecord,
    )
    from bijux_proteomics.interpretation.protein_annotation_mapping import (
        ProteinAnnotationRecord,
    )
    from bijux_proteomics.io.formats import ExperimentalDesignEntry
    from bijux_proteomics.quantification.contracts import LabelFreeQuantTable
    from bijux_proteomics.quantification.contracts.differential import (
        DifferentialAbundanceReport,
    )
    from bijux_proteomics.sequences.core import NormalizedProteinRecord
    from bijux_proteomics.workflow.reports.biological_report_selection_policy import (
        BiologicalResultSelectionPolicy,
    )


class BiologicalEnrichmentAssemblyReports(NamedTuple):
    """Owned enrichment and activity outputs for report assembly."""

    foreground_background_model: BiologicalForegroundBackgroundModel
    go_enrichment_report: GoEnrichmentReport | None
    pathway_activity_report: PathwayActivityReport | None
    pathway_enrichment_report: PathwayEnrichmentReport | None
    complex_activity_report: ComplexActivityReport | None
    complex_enrichment_report: ComplexEnrichmentReport | None


def _build_biological_enrichment_reports(
    *,
    normalized_table: LabelFreeQuantTable,
    differential_report: DifferentialAbundanceReport,
    design_entries: tuple[ExperimentalDesignEntry, ...],
    fasta_records: tuple[NormalizedProteinRecord, ...],
    custom_annotations: tuple[ProteinAnnotationRecord, ...],
    go_annotation_records: tuple[GoAnnotationRecord, ...],
    pathway_records: tuple[PathwayMembershipRecord, ...],
    complex_records: tuple[ComplexMembershipRecord, ...],
    active_selection_policy: BiologicalResultSelectionPolicy,
) -> BiologicalEnrichmentAssemblyReports:
    """Build enrichment and activity reports from parsed reference records."""

    enrichment_input_requested = any(
        (go_annotation_records, pathway_records, complex_records)
    )
    enrichment_input_sets = _build_biological_enrichment_input_sets(
        normalized_table=normalized_table,
        differential_report=differential_report,
        active_selection_policy=active_selection_policy,
        enrichment_input_requested=enrichment_input_requested,
    )
    go_enrichment_report = _build_biological_go_enrichment_report(
        enrichment_foreground_entries=enrichment_input_sets.enrichment_foreground_entries,
        enrichment_background_entries=enrichment_input_sets.enrichment_background_entries,
        go_annotation_records=go_annotation_records,
        active_selection_policy=active_selection_policy,
    )
    pathway_reports = _build_biological_pathway_enrichment_reports(
        normalized_table=normalized_table,
        design_entries=design_entries,
        fasta_records=fasta_records,
        custom_annotations=custom_annotations,
        pathway_records=pathway_records,
        enrichment_foreground_entries=enrichment_input_sets.enrichment_foreground_entries,
        enrichment_background_entries=enrichment_input_sets.enrichment_background_entries,
        active_selection_policy=active_selection_policy,
    )
    complex_reports = _build_biological_complex_enrichment_reports(
        normalized_table=normalized_table,
        design_entries=design_entries,
        fasta_records=fasta_records,
        custom_annotations=custom_annotations,
        complex_records=complex_records,
        enrichment_foreground_entries=enrichment_input_sets.enrichment_foreground_entries,
        enrichment_background_entries=enrichment_input_sets.enrichment_background_entries,
        active_selection_policy=active_selection_policy,
    )

    return BiologicalEnrichmentAssemblyReports(
        foreground_background_model=enrichment_input_sets.foreground_background_model,
        go_enrichment_report=go_enrichment_report,
        pathway_activity_report=pathway_reports.pathway_activity_report,
        pathway_enrichment_report=pathway_reports.pathway_enrichment_report,
        complex_activity_report=complex_reports.complex_activity_report,
        complex_enrichment_report=complex_reports.complex_enrichment_report,
    )
