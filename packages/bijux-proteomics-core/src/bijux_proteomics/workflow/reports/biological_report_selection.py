# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Compatibility wrappers for split biological report selection ownership."""

from __future__ import annotations

from collections.abc import Iterable

from bijux_proteomics.interpretation import (
    BiologicalSetEntry,
    BiologicalSetFilteringPolicy,
    ProteinReferenceEntry,
)
from bijux_proteomics.io.formats import ExperimentalDesignEntry
from bijux_proteomics.quantification.contracts import (
    DifferentialAbundanceReport,
    LabelFreeQuantTable,
)
from bijux_proteomics.study import ExperimentDesign
from bijux_proteomics.workflow.reports.biological_report_contrast_selection import (
    _resolve_contrast as _resolve_report_contrast,
    _select_heatmap_entity_ids as _select_report_heatmap_entity_ids,
    _select_significant_entity_ids as _select_report_significant_entity_ids,
)
from bijux_proteomics.workflow.reports.biological_report_selection_policy import (
    BiologicalResultSelectionPolicy,
)


def _resolve_contrast(
    design_entries: ExperimentDesign | tuple[ExperimentalDesignEntry, ...],
    *,
    condition_a: str | None,
    condition_b: str | None,
) -> tuple[str, str]:
    return _resolve_report_contrast(
        design_entries,
        condition_a=condition_a,
        condition_b=condition_b,
    )


def _select_significant_entity_ids(
    report: DifferentialAbundanceReport,
    *,
    policy: BiologicalResultSelectionPolicy,
) -> tuple[str, ...]:
    return _select_report_significant_entity_ids(report, policy=policy)


def _select_heatmap_entity_ids(
    report: DifferentialAbundanceReport,
    *,
    policy: BiologicalResultSelectionPolicy,
) -> tuple[str, ...]:
    return _select_report_heatmap_entity_ids(report, policy=policy)


def _build_differential_reference_entries(
    report: DifferentialAbundanceReport,
    *,
    protein_refs_by_entity: dict[str, tuple[str, ...]] | None = None,
) -> tuple[ProteinReferenceEntry, ...]:
    return _build_protein_reference_entries(
        (entry.entity_id, protein_refs_by_entity or {}) for entry in report.entries
    )


def _build_background_reference_entries(
    normalized_table: LabelFreeQuantTable,
) -> tuple[ProteinReferenceEntry, ...]:
    return _build_protein_reference_entries(
        (entity_id, normalized_table.entity_protein_refs)
        for entity_id in normalized_table.entity_ids
    )


def _build_foreground_reference_entries(
    report: DifferentialAbundanceReport,
    *,
    protein_refs_by_entity: dict[str, tuple[str, ...]] | None = None,
    policy: BiologicalResultSelectionPolicy,
) -> tuple[ProteinReferenceEntry, ...]:
    significant_entity_ids = _select_significant_entity_ids(report, policy=policy)
    return _build_protein_reference_entries(
        (entity_id, protein_refs_by_entity or {})
        for entity_id in significant_entity_ids
    )


def _build_biological_foreground_filtering_policy(
    selection_policy: BiologicalResultSelectionPolicy,
) -> BiologicalSetFilteringPolicy:
    return BiologicalSetFilteringPolicy(
        policy_name="biological_result_selection",
        max_adjusted_p_value=selection_policy.max_adjusted_p_value,
        min_absolute_log2_fold_change=selection_policy.min_absolute_log2_fold_change,
        measured_entities_only=True,
        deduplicate_protein_refs=True,
        note=(
            "foreground keeps statistically selected proteins from the governed "
            "contrast using the biological result selection thresholds"
        ),
    )


def _build_biological_background_filtering_policy() -> BiologicalSetFilteringPolicy:
    return BiologicalSetFilteringPolicy(
        policy_name="measured_protein_quantification_universe",
        measured_entities_only=True,
        deduplicate_protein_refs=True,
        note=(
            "background keeps every measured protein in the normalized quantification "
            "table instead of silently broadening to the annotation universe"
        ),
    )


def _build_protein_reference_entries_from_biological_set(
    entries: tuple[BiologicalSetEntry, ...],
) -> tuple[ProteinReferenceEntry, ...]:
    return tuple(
        ProteinReferenceEntry(
            row_number=index,
            source_row_id=entry.source_row_id,
            input_protein_ref=entry.protein_ref,
            protein_ref=entry.protein_ref,
        )
        for index, entry in enumerate(entries, start=2)
    )


def _build_protein_reference_entries(
    entity_rows: Iterable[tuple[str, dict[str, tuple[str, ...]]]],
) -> tuple[ProteinReferenceEntry, ...]:
    entries: list[ProteinReferenceEntry] = []
    row_number = 2
    for entity_id, protein_refs_by_entity in entity_rows:
        protein_refs = protein_refs_by_entity.get(entity_id, ()) or (entity_id,)
        for protein_ref in protein_refs:
            entries.append(
                ProteinReferenceEntry(
                    row_number=row_number,
                    source_row_id=entity_id,
                    input_protein_ref=protein_ref,
                    protein_ref=protein_ref,
                )
            )
            row_number += 1
    return tuple(entries)
