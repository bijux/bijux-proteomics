# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Complex enrichment and activity assembly for biological report bundles."""

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

if TYPE_CHECKING:
    from bijux_proteomics.interpretation.complex_activity.models import (
        ComplexActivityReport,
    )
    from bijux_proteomics.interpretation.complex_enrichment import (
        ComplexEnrichmentReport,
        ComplexMembershipRecord,
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


class BiologicalComplexEnrichmentReports(NamedTuple):
    """Complex-scoped enrichment assembly outputs."""

    complex_activity_report: ComplexActivityReport | None
    complex_enrichment_report: ComplexEnrichmentReport | None


def _build_biological_complex_enrichment_reports(
    *,
    normalized_table: LabelFreeQuantTable,
    design_entries: tuple[ExperimentalDesignEntry, ...],
    fasta_records: tuple[NormalizedProteinRecord, ...],
    custom_annotations: tuple[ProteinAnnotationRecord, ...],
    complex_records: tuple[ComplexMembershipRecord, ...],
    enrichment_foreground_entries: tuple[ProteinReferenceEntry, ...],
    enrichment_background_entries: tuple[ProteinReferenceEntry, ...],
    active_selection_policy: BiologicalResultSelectionPolicy,
) -> BiologicalComplexEnrichmentReports:
    if not complex_records:
        return BiologicalComplexEnrichmentReports(
            complex_activity_report=None,
            complex_enrichment_report=None,
        )

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
    return BiologicalComplexEnrichmentReports(
        complex_activity_report=complex_activity_report,
        complex_enrichment_report=complex_enrichment_report,
    )
