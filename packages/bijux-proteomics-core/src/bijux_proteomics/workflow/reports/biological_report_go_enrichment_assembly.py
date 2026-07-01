# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""GO enrichment assembly for biological report bundles."""

from __future__ import annotations

from typing import TYPE_CHECKING

from bijux_proteomics.interpretation.go_enrichment import (
    GoEnrichmentCorrectionPolicy,
    apply_go_enrichment_multiple_testing,
    build_go_enrichment_report,
)

if TYPE_CHECKING:
    from bijux_proteomics.interpretation.go_enrichment import (
        GoAnnotationRecord,
        GoEnrichmentReport,
    )
    from bijux_proteomics.interpretation.protein_annotation_mapping import (
        ProteinReferenceEntry,
    )
    from bijux_proteomics.workflow.reports.biological_report_selection_policy import (
        BiologicalResultSelectionPolicy,
    )


def _build_biological_go_enrichment_report(
    *,
    enrichment_foreground_entries: tuple[ProteinReferenceEntry, ...],
    enrichment_background_entries: tuple[ProteinReferenceEntry, ...],
    go_annotation_records: tuple[GoAnnotationRecord, ...],
    active_selection_policy: BiologicalResultSelectionPolicy,
) -> GoEnrichmentReport | None:
    if not go_annotation_records:
        return None

    return apply_go_enrichment_multiple_testing(
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
