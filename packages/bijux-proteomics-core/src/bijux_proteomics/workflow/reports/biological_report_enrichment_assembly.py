# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi
"""Enrichment and activity assembly for biological report bundles."""

from __future__ import annotations

from typing import TYPE_CHECKING, NamedTuple

from bijux_proteomics.interpretation.complex_activity import (
    build_complex_activity_report,
)
from bijux_proteomics.interpretation.complex_enrichment import (
    ComplexEnrichmentCorrectionPolicy,
    apply_complex_enrichment_multiple_testing,
    build_complex_enrichment_report,
)
from bijux_proteomics.interpretation.foreground_background_model import (
    BiologicalSetSourceKind,
    build_biological_foreground_background_model,
    require_valid_biological_foreground_background_model,
)
from bijux_proteomics.interpretation.go_enrichment import (
    GoEnrichmentCorrectionPolicy,
    apply_go_enrichment_multiple_testing,
    build_go_enrichment_report,
)
from bijux_proteomics.interpretation.pathway_activity import (
    build_pathway_activity_report,
)
from bijux_proteomics.interpretation.pathway_enrichment import (
    PathwayEnrichmentCorrectionPolicy,
    apply_pathway_enrichment_multiple_testing,
    build_pathway_enrichment_report,
)
from bijux_proteomics.workflow.reports.biological_report_filtering_policies import (
    _build_biological_background_filtering_policy,
    _build_biological_foreground_filtering_policy,
)
from bijux_proteomics.workflow.reports.biological_report_reference_entries import (
    _build_background_reference_entries,
    _build_foreground_reference_entries,
    _build_protein_reference_entries_from_biological_set,
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
    from bijux_proteomics.workflow.reports.biological_report_models import (
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

    foreground_background_model = build_biological_foreground_background_model(
        _build_foreground_reference_entries(
            differential_report,
            protein_refs_by_entity=normalized_table.entity_protein_refs,
            policy=active_selection_policy,
        ),
        _build_background_reference_entries(normalized_table),
        foreground_source_kind=BiologicalSetSourceKind.DIFFERENTIAL_SIGNIFICANT_RESULTS,
        background_source_kind=BiologicalSetSourceKind.MEASURED_QUANT_MATRIX,
        foreground_policy=_build_biological_foreground_filtering_policy(
            active_selection_policy
        ),
        background_policy=_build_biological_background_filtering_policy(),
    )
    enrichment_input_requested = any(
        (go_annotation_records, pathway_records, complex_records)
    )
    validated_foreground_background_model = (
        require_valid_biological_foreground_background_model(
            foreground_background_model
        )
        if enrichment_input_requested
        else foreground_background_model
    )
    enrichment_foreground_entries = (
        _build_protein_reference_entries_from_biological_set(
            validated_foreground_background_model.foreground_entries
        )
    )
    enrichment_background_entries = (
        _build_protein_reference_entries_from_biological_set(
            validated_foreground_background_model.background_entries
        )
    )

    go_enrichment_report = None
    if go_annotation_records:
        go_enrichment_report = apply_go_enrichment_multiple_testing(
            build_go_enrichment_report(
                enrichment_foreground_entries,
                enrichment_background_entries,
                go_annotation_records,
            ),
            policy=GoEnrichmentCorrectionPolicy(
                max_adjusted_p_value=active_selection_policy.max_adjusted_p_value,
                min_enrichment_ratio=1.0,
            ),
        )

    pathway_activity_report = None
    pathway_enrichment_report = None
    if pathway_records:
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

    complex_activity_report = None
    complex_enrichment_report = None
    if complex_records:
        complex_activity_report = build_complex_activity_report(
            normalized_table,
            complex_records,
            design_entries=design_entries,
            fasta_records=fasta_records,
            custom_annotations=custom_annotations,
        )
        complex_enrichment_report = apply_complex_enrichment_multiple_testing(
            build_complex_enrichment_report(
                enrichment_foreground_entries,
                enrichment_background_entries,
                complex_records,
                fasta_records=fasta_records,
                custom_annotations=custom_annotations,
            ),
            policy=ComplexEnrichmentCorrectionPolicy(
                max_adjusted_p_value=active_selection_policy.max_adjusted_p_value,
                min_enrichment_ratio=1.0,
            ),
        )

    return BiologicalEnrichmentAssemblyReports(
        foreground_background_model=foreground_background_model,
        go_enrichment_report=go_enrichment_report,
        pathway_activity_report=pathway_activity_report,
        pathway_enrichment_report=pathway_enrichment_report,
        complex_activity_report=complex_activity_report,
        complex_enrichment_report=complex_enrichment_report,
    )
