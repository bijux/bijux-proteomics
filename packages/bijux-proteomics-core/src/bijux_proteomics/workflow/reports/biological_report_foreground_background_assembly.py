# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Foreground/background preparation for biological enrichment assembly."""

from __future__ import annotations

from typing import TYPE_CHECKING, NamedTuple

from bijux_proteomics.interpretation.foreground_background_model import (
    BiologicalSetSourceKind,
    build_biological_foreground_background_model,
    require_valid_biological_foreground_background_model,
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
    from bijux_proteomics.interpretation.foreground_background_model import (
        BiologicalForegroundBackgroundModel,
    )
    from bijux_proteomics.interpretation.protein_annotation_mapping import (
        ProteinReferenceEntry,
    )
    from bijux_proteomics.quantification.contracts import LabelFreeQuantTable
    from bijux_proteomics.quantification.contracts.differential import (
        DifferentialAbundanceReport,
    )
    from bijux_proteomics.workflow.reports.biological_report_selection_policy import (
        BiologicalResultSelectionPolicy,
    )


class BiologicalEnrichmentInputSets(NamedTuple):
    """Foreground/background inputs owned by enrichment assembly."""

    foreground_background_model: BiologicalForegroundBackgroundModel
    enrichment_foreground_entries: tuple[ProteinReferenceEntry, ...]
    enrichment_background_entries: tuple[ProteinReferenceEntry, ...]


def _build_biological_enrichment_input_sets(
    *,
    normalized_table: LabelFreeQuantTable,
    differential_report: DifferentialAbundanceReport,
    active_selection_policy: BiologicalResultSelectionPolicy,
    enrichment_input_requested: bool,
) -> BiologicalEnrichmentInputSets:
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
    validated_foreground_background_model = (
        require_valid_biological_foreground_background_model(
            foreground_background_model
        )
        if enrichment_input_requested
        else foreground_background_model
    )
    return BiologicalEnrichmentInputSets(
        foreground_background_model=foreground_background_model,
        enrichment_foreground_entries=(
            _build_protein_reference_entries_from_biological_set(
                validated_foreground_background_model.foreground_entries
            )
        ),
        enrichment_background_entries=(
            _build_protein_reference_entries_from_biological_set(
                validated_foreground_background_model.background_entries
            )
        ),
    )
