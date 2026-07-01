# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Row assembly owners for protein LFQ reports."""

from __future__ import annotations

from collections import defaultdict

from bijux_proteomics.quantification.contracts.input_models import MissingValueKind
from bijux_proteomics.quantification.matrix.peptide_intensity_matrix import (
    PeptideIntensityMatrixRow,
)
from bijux_proteomics.quantification.matrix.protein_intensity_matrix import (
    ProteinMatrixTargetKind,
)
from bijux_proteomics.quantification.rollup.protein_lfq.models import (
    ProteinLfqDisconnectedComponentEntry,
    ProteinLfqRow,
    ProteinLfqValue,
)
from bijux_proteomics.quantification.rollup.protein_lfq.solving import (
    build_pairwise_ratio_rows,
    connected_components,
    observed_log2_intensities_by_sample,
    solve_component_profiles,
)


def build_target_lfq_row(
    target_id: str,
    peptide_rows: list[tuple[PeptideIntensityMatrixRow, bool]],
    *,
    sample_ids: tuple[str, ...],
    protein_refs: tuple[str, ...],
    target_kind: ProteinMatrixTargetKind,
    minimum_shared_peptides: int,
) -> ProteinLfqRow:
    """Assemble one protein LFQ row from its peptide evidence."""
    pairwise_ratios = build_pairwise_ratio_rows(
        peptide_rows,
        sample_ids=sample_ids,
        minimum_shared_peptides=minimum_shared_peptides,
    )
    observed_logs = observed_log2_intensities_by_sample(
        peptide_rows, sample_ids=sample_ids
    )
    components = connected_components(
        sample_ids=sample_ids,
        pairwise_ratios=pairwise_ratios,
        observed_logs=observed_logs,
    )
    solved_logs, component_ids = solve_component_profiles(
        components=components,
        pairwise_ratios=pairwise_ratios,
        observed_logs=observed_logs,
    )

    peptide_ids = sorted({row.entity_id for row, _ in peptide_rows})
    unique_peptide_ids = sorted(
        {row.entity_id for row, is_unique in peptide_rows if is_unique}
    )
    shared_peptide_ids = sorted(
        {row.entity_id for row, is_unique in peptide_rows if not is_unique}
    )
    values: list[ProteinLfqValue] = []
    for sample_id in sample_ids:
        sample_kinds = tuple(
            next(
                value for value in row.values if value.sample_id == sample_id
            ).missing_value_kind
            for row, _ in peptide_rows
        )
        log2_abundance = solved_logs.get(sample_id)
        abundance = None if log2_abundance is None else float(2.0**log2_abundance)
        if abundance is None:
            missing_kind = aggregate_missing_kind(sample_kinds)
        else:
            missing_kind = MissingValueKind.OBSERVED
        contributing_peptide_count = sum(
            1
            for row, _ in peptide_rows
            if any(
                value.sample_id == sample_id
                and value.abundance is not None
                and value.abundance > 0.0
                and value.missing_value_kind is MissingValueKind.OBSERVED
                for value in row.values
            )
        )
        values.append(
            ProteinLfqValue(
                sample_id=sample_id,
                abundance=abundance,
                log2_abundance=log2_abundance,
                missing_value_kind=missing_kind,
                contributing_peptide_count=contributing_peptide_count,
                component_id=component_ids.get(sample_id),
            )
        )

    fully_connected = len(components) <= 1 and len(sample_ids) > 0
    return ProteinLfqRow(
        entity_id=target_id,
        target_kind=target_kind,
        protein_refs=protein_refs,
        peptide_count=len(peptide_ids),
        unique_peptide_count=len(unique_peptide_ids),
        shared_peptide_count=len(shared_peptide_ids),
        pairwise_ratio_count=len(pairwise_ratios),
        connected_component_count=len(components),
        fully_connected=fully_connected,
        contributing_peptides=tuple(peptide_ids),
        pairwise_ratios=tuple(pairwise_ratios),
        values=tuple(values),
    )


def build_disconnected_component_entries(
    row: ProteinLfqRow,
    *,
    peptide_rows: list[tuple[PeptideIntensityMatrixRow, bool]],
) -> tuple[ProteinLfqDisconnectedComponentEntry, ...]:
    """Describe disconnected LFQ components that cannot share one scale."""
    component_samples: dict[int, list[str]] = defaultdict(list)
    for value in row.values:
        if value.component_id is None:
            continue
        component_samples[value.component_id].append(value.sample_id)
    if len(component_samples) <= 1:
        return ()

    entries: list[ProteinLfqDisconnectedComponentEntry] = []
    for component_id in sorted(component_samples):
        sample_ids = tuple(sorted(component_samples[component_id]))
        sample_id_set = set(sample_ids)
        disconnected_from_sample_ids = tuple(
            sorted(
                {
                    sample_id
                    for other_component_id, other_sample_ids in component_samples.items()
                    if other_component_id != component_id
                    for sample_id in other_sample_ids
                }
            )
        )
        pairwise_ratio_count = sum(
            1
            for ratio in row.pairwise_ratios
            if ratio.sample_a in sample_id_set and ratio.sample_b in sample_id_set
        )
        contributing_peptides = tuple(
            sorted(
                {
                    peptide_row.entity_id
                    for peptide_row, _ in peptide_rows
                    if any(
                        value.sample_id in sample_id_set
                        and value.abundance is not None
                        and value.abundance > 0.0
                        and value.missing_value_kind is MissingValueKind.OBSERVED
                        for value in peptide_row.values
                    )
                }
            )
        )
        entries.append(
            ProteinLfqDisconnectedComponentEntry(
                entity_id=row.entity_id,
                target_kind=row.target_kind,
                protein_refs=row.protein_refs,
                component_id=component_id,
                sample_ids=sample_ids,
                disconnected_from_sample_ids=disconnected_from_sample_ids,
                sample_count=len(sample_ids),
                pairwise_ratio_count=pairwise_ratio_count,
                contributing_peptides=contributing_peptides,
            )
        )
    return tuple(entries)


def aggregate_missing_kind(kinds: tuple[MissingValueKind, ...]) -> MissingValueKind:
    """Collapse peptide-level missing kinds into the protein-row result kind."""
    if any(
        kind in (MissingValueKind.OBSERVED, MissingValueKind.ZERO) for kind in kinds
    ):
        if any(kind is MissingValueKind.ZERO for kind in kinds) and not any(
            kind is MissingValueKind.OBSERVED for kind in kinds
        ):
            return MissingValueKind.ZERO
        return MissingValueKind.OBSERVED
    if any(kind is MissingValueKind.EXCLUDED for kind in kinds):
        return MissingValueKind.EXCLUDED
    if any(kind is MissingValueKind.CENSORED for kind in kinds):
        return MissingValueKind.CENSORED
    if any(kind is MissingValueKind.FILTERED for kind in kinds):
        return MissingValueKind.FILTERED
    if all(kind is MissingValueKind.NOT_APPLICABLE for kind in kinds):
        return MissingValueKind.NOT_APPLICABLE
    return MissingValueKind.NOT_OBSERVED


__all__ = [
    "aggregate_missing_kind",
    "build_disconnected_component_entries",
    "build_target_lfq_row",
]
