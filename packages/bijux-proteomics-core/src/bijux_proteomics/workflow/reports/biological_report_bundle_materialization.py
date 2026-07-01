# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Final bundle materialization for biological report assembly."""

from __future__ import annotations

from bijux_proteomics.workflow.reports.biological_report_bundle_contracts import (
    BiologicalActivityReportBundle,
    BiologicalContextualReportBundle,
    BiologicalEnrichmentReportBundle,
    BiologicalResultReportBundle,
    BiologicalScientificReportBundle,
    BiologicalVisualReportBundle,
)
from bijux_proteomics.workflow.reports.biological_report_section_metadata import (
    BiologicalReportSectionConfidenceEntry,
)
from bijux_proteomics.workflow.reports.biological_report_selection_policy import (
    BiologicalResultSelectionPolicy,
)
from bijux_proteomics.workflow.reports.biological_report_summary_contracts import (
    BiologicalResultReportSummary,
)

_BIOLOGICAL_RESULT_REPORT_BUNDLE_NOTE = (
    "biological reporting assembles governed protein differential analysis, "
    "protein evidence cards, annotation mapping, optional user-supplied "
    "biological context mapping, enrichment, volcano review, heatmap "
    "preparation, and sample exploration into one owned workflow bundle with "
    "experiment-level confidence scoring, tissue and cell-type context review, "
    "claim validation, biological hypotheses, and explicit component reasons"
)


def _materialize_biological_result_report_bundle(
    *,
    scientific: BiologicalScientificReportBundle,
    contextual: BiologicalContextualReportBundle,
    activity: BiologicalActivityReportBundle,
    enrichment: BiologicalEnrichmentReportBundle,
    visual: BiologicalVisualReportBundle,
    selection_policy: BiologicalResultSelectionPolicy,
    section_confidence_entries: tuple[BiologicalReportSectionConfidenceEntry, ...],
    summary: BiologicalResultReportSummary,
) -> BiologicalResultReportBundle:
    return BiologicalResultReportBundle(
        scientific=scientific,
        contextual=contextual,
        activity=activity,
        enrichment=enrichment,
        visual=visual,
        selection_policy=selection_policy,
        section_confidence_entries=section_confidence_entries,
        summary=summary,
        note=_BIOLOGICAL_RESULT_REPORT_BUNDLE_NOTE,
    )


__all__ = [
    "_BIOLOGICAL_RESULT_REPORT_BUNDLE_NOTE",
    "_materialize_biological_result_report_bundle",
]
