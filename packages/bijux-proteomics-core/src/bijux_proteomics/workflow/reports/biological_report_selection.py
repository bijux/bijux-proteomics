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
)
from bijux_proteomics.workflow.reports.biological_report_contrast_selection import (
    _select_heatmap_entity_ids as _select_report_heatmap_entity_ids,
)
from bijux_proteomics.workflow.reports.biological_report_contrast_selection import (
    _select_significant_entity_ids as _select_report_significant_entity_ids,
)
from bijux_proteomics.workflow.reports.biological_report_filtering_policies import (
    _build_biological_background_filtering_policy as _build_report_background_filtering_policy,
)
from bijux_proteomics.workflow.reports.biological_report_filtering_policies import (
    _build_biological_foreground_filtering_policy as _build_report_foreground_filtering_policy,
)
from bijux_proteomics.workflow.reports.biological_report_reference_entries import (
    _build_background_reference_entries as _build_report_background_reference_entries,
)
from bijux_proteomics.workflow.reports.biological_report_reference_entries import (
    _build_differential_reference_entries as _build_report_differential_reference_entries,
)
from bijux_proteomics.workflow.reports.biological_report_reference_entries import (
    _build_foreground_reference_entries as _build_report_foreground_reference_entries,
)
from bijux_proteomics.workflow.reports.biological_report_reference_entries import (
    _build_protein_reference_entries as _build_report_protein_reference_entries,
)
from bijux_proteomics.workflow.reports.biological_report_reference_entries import (
    _build_protein_reference_entries_from_biological_set as _build_report_biological_set_reference_entries,
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
    return _build_report_differential_reference_entries(
        report,
        protein_refs_by_entity=protein_refs_by_entity,
    )


def _build_background_reference_entries(
    normalized_table: LabelFreeQuantTable,
) -> tuple[ProteinReferenceEntry, ...]:
    return _build_report_background_reference_entries(normalized_table)


def _build_foreground_reference_entries(
    report: DifferentialAbundanceReport,
    *,
    protein_refs_by_entity: dict[str, tuple[str, ...]] | None = None,
    policy: BiologicalResultSelectionPolicy,
) -> tuple[ProteinReferenceEntry, ...]:
    return _build_report_foreground_reference_entries(
        report,
        protein_refs_by_entity=protein_refs_by_entity,
        policy=policy,
    )


def _build_biological_foreground_filtering_policy(
    selection_policy: BiologicalResultSelectionPolicy,
) -> BiologicalSetFilteringPolicy:
    return _build_report_foreground_filtering_policy(selection_policy)


def _build_biological_background_filtering_policy() -> BiologicalSetFilteringPolicy:
    return _build_report_background_filtering_policy()


def _build_protein_reference_entries_from_biological_set(
    entries: tuple[BiologicalSetEntry, ...],
) -> tuple[ProteinReferenceEntry, ...]:
    return _build_report_biological_set_reference_entries(entries)


def _build_protein_reference_entries(
    entity_rows: Iterable[tuple[str, dict[str, tuple[str, ...]]]],
) -> tuple[ProteinReferenceEntry, ...]:
    return _build_report_protein_reference_entries(entity_rows)
