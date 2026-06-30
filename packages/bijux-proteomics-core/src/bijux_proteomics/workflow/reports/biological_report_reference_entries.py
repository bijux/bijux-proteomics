# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Owned protein reference-entry builders for biological report workflows."""

from __future__ import annotations

from collections.abc import Iterable

from bijux_proteomics.interpretation import BiologicalSetEntry, ProteinReferenceEntry
from bijux_proteomics.quantification.contracts import (
    DifferentialAbundanceReport,
    LabelFreeQuantTable,
)
from bijux_proteomics.workflow.reports.biological_report_contrast_selection import (
    _select_significant_entity_ids,
)
from bijux_proteomics.workflow.reports.biological_report_selection_policy import (
    BiologicalResultSelectionPolicy,
)


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
