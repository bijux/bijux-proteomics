# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Numerical solving owners for protein LFQ sample profiles."""

from __future__ import annotations

from collections import defaultdict
import math

import numpy as np

from bijux_proteomics.quantification.contracts.input_models import MissingValueKind
from bijux_proteomics.quantification.matrix.peptide_intensity_matrix import (
    PeptideIntensityMatrixRow,
)
from bijux_proteomics.quantification.rollup.protein_lfq.models import (
    ProteinLfqPairwiseRatio,
)


def build_pairwise_ratio_rows(
    peptide_rows: list[tuple[PeptideIntensityMatrixRow, bool]],
    *,
    sample_ids: tuple[str, ...],
    minimum_shared_peptides: int,
) -> list[ProteinLfqPairwiseRatio]:
    """Build sample-pair ratio constraints from peptide evidence."""
    return build_pairwise_ratio_rows_vectorized(
        peptide_rows,
        sample_ids=sample_ids,
        minimum_shared_peptides=minimum_shared_peptides,
    )


def build_pairwise_ratio_rows_pure(
    peptide_rows: list[tuple[PeptideIntensityMatrixRow, bool]],
    *,
    sample_ids: tuple[str, ...],
    minimum_shared_peptides: int,
) -> list[ProteinLfqPairwiseRatio]:
    """Reference implementation for pairwise ratio construction."""
    ratios_by_pair: dict[tuple[str, str], list[tuple[float, str]]] = defaultdict(list)
    for row, _ in peptide_rows:
        sample_abundances = {
            value.sample_id: float(value.abundance)
            for value in row.values
            if value.abundance is not None
            and value.abundance > 0.0
            and value.missing_value_kind is MissingValueKind.OBSERVED
        }
        for index, sample_a in enumerate(sample_ids):
            abundance_a = sample_abundances.get(sample_a)
            if abundance_a is None:
                continue
            for sample_b in sample_ids[index + 1 :]:
                abundance_b = sample_abundances.get(sample_b)
                if abundance_b is None:
                    continue
                ratios_by_pair[(sample_a, sample_b)].append(
                    (math.log2(abundance_b) - math.log2(abundance_a), row.entity_id)
                )

    pairwise_ratios: list[ProteinLfqPairwiseRatio] = []
    for sample_a, sample_b in sorted(ratios_by_pair):
        entries = ratios_by_pair[(sample_a, sample_b)]
        if len(entries) < minimum_shared_peptides:
            continue
        median_log2_ratio = median(tuple(value for value, _ in entries))
        pairwise_ratios.append(
            ProteinLfqPairwiseRatio(
                sample_a=sample_a,
                sample_b=sample_b,
                shared_peptide_count=len(entries),
                median_log2_ratio=median_log2_ratio,
                median_ratio=float(2.0**median_log2_ratio),
                contributing_peptides=tuple(
                    sorted({peptide_id for _, peptide_id in entries})
                ),
            )
        )
    return pairwise_ratios


def build_pairwise_ratio_rows_vectorized(
    peptide_rows: list[tuple[PeptideIntensityMatrixRow, bool]],
    *,
    sample_ids: tuple[str, ...],
    minimum_shared_peptides: int,
) -> list[ProteinLfqPairwiseRatio]:
    """Vectorized pairwise ratio construction over shared peptide observations."""
    peptide_ids, log2_matrix, observed_mask = build_peptide_log2_observation_matrix(
        peptide_rows,
        sample_ids=sample_ids,
    )
    pairwise_ratios: list[ProteinLfqPairwiseRatio] = []
    for sample_a_index, sample_a in enumerate(sample_ids):
        for sample_b_index in range(sample_a_index + 1, len(sample_ids)):
            sample_b = sample_ids[sample_b_index]
            shared_mask = (
                observed_mask[:, sample_a_index] & observed_mask[:, sample_b_index]
            )
            shared_count = int(np.sum(shared_mask))
            if shared_count < minimum_shared_peptides:
                continue
            shared_ratios = (
                log2_matrix[shared_mask, sample_b_index]
                - log2_matrix[shared_mask, sample_a_index]
            )
            median_log2_ratio = float(np.median(shared_ratios))
            contributing_peptides = tuple(
                sorted(
                    peptide_id
                    for peptide_id, include in zip(
                        peptide_ids, shared_mask, strict=True
                    )
                    if include
                )
            )
            pairwise_ratios.append(
                ProteinLfqPairwiseRatio(
                    sample_a=sample_a,
                    sample_b=sample_b,
                    shared_peptide_count=shared_count,
                    median_log2_ratio=median_log2_ratio,
                    median_ratio=float(2.0**median_log2_ratio),
                    contributing_peptides=contributing_peptides,
                )
            )
    return pairwise_ratios


def observed_log2_intensities_by_sample(
    peptide_rows: list[tuple[PeptideIntensityMatrixRow, bool]],
    *,
    sample_ids: tuple[str, ...],
) -> dict[str, tuple[float, ...]]:
    """Collect observed peptide log2 abundances grouped by sample."""
    return observed_log2_intensities_by_sample_vectorized(
        peptide_rows,
        sample_ids=sample_ids,
    )


def observed_log2_intensities_by_sample_pure(
    peptide_rows: list[tuple[PeptideIntensityMatrixRow, bool]],
    *,
    sample_ids: tuple[str, ...],
) -> dict[str, tuple[float, ...]]:
    """Reference implementation for per-sample observed log2 abundances."""
    observed: dict[str, list[float]] = {sample_id: [] for sample_id in sample_ids}
    for row, _ in peptide_rows:
        for value in row.values:
            if (
                value.abundance is not None
                and value.abundance > 0.0
                and value.missing_value_kind is MissingValueKind.OBSERVED
            ):
                observed[value.sample_id].append(math.log2(float(value.abundance)))
    return {
        sample_id: tuple(values) for sample_id, values in observed.items() if values
    }


def observed_log2_intensities_by_sample_vectorized(
    peptide_rows: list[tuple[PeptideIntensityMatrixRow, bool]],
    *,
    sample_ids: tuple[str, ...],
) -> dict[str, tuple[float, ...]]:
    """Vectorized implementation for per-sample observed log2 abundances."""
    _peptide_ids, log2_matrix, observed_mask = build_peptide_log2_observation_matrix(
        peptide_rows,
        sample_ids=sample_ids,
    )
    return {
        sample_id: tuple(
            log2_matrix[observed_mask[:, sample_index], sample_index].tolist()
        )
        for sample_index, sample_id in enumerate(sample_ids)
        if np.any(observed_mask[:, sample_index])
    }


def build_peptide_log2_observation_matrix(
    peptide_rows: list[tuple[PeptideIntensityMatrixRow, bool]],
    *,
    sample_ids: tuple[str, ...],
) -> tuple[tuple[str, ...], np.ndarray, np.ndarray]:
    """Project peptide rows onto a dense observed log2 matrix."""
    sample_index = {sample_id: index for index, sample_id in enumerate(sample_ids)}
    peptide_ids: list[str] = []
    log2_matrix = np.full((len(peptide_rows), len(sample_ids)), np.nan, dtype=float)
    observed_mask = np.zeros((len(peptide_rows), len(sample_ids)), dtype=bool)
    for row_index, (row, _) in enumerate(peptide_rows):
        peptide_ids.append(row.entity_id)
        for value in row.values:
            column_index = sample_index[value.sample_id]
            if (
                value.abundance is not None
                and value.abundance > 0.0
                and value.missing_value_kind is MissingValueKind.OBSERVED
            ):
                observed_mask[row_index, column_index] = True
                log2_matrix[row_index, column_index] = math.log2(float(value.abundance))
    return tuple(peptide_ids), log2_matrix, observed_mask


def connected_components(
    *,
    sample_ids: tuple[str, ...],
    pairwise_ratios: list[ProteinLfqPairwiseRatio],
    observed_logs: dict[str, tuple[float, ...]],
) -> tuple[tuple[str, ...], ...]:
    """Discover connected sample components implied by pairwise ratios."""
    adjacency: dict[str, set[str]] = {sample_id: set() for sample_id in sample_ids}
    for ratio in pairwise_ratios:
        adjacency[ratio.sample_a].add(ratio.sample_b)
        adjacency[ratio.sample_b].add(ratio.sample_a)

    observed_samples = tuple(
        sample_id for sample_id in sample_ids if sample_id in observed_logs
    )
    components: list[tuple[str, ...]] = []
    seen: set[str] = set()
    for sample_id in observed_samples:
        if sample_id in seen:
            continue
        stack = [sample_id]
        component: list[str] = []
        while stack:
            current = stack.pop()
            if current in seen:
                continue
            seen.add(current)
            component.append(current)
            stack.extend(sorted(adjacency[current] - seen))
        components.append(tuple(sorted(component)))
    return tuple(components)


def solve_component_profiles(
    *,
    components: tuple[tuple[str, ...], ...],
    pairwise_ratios: list[ProteinLfqPairwiseRatio],
    observed_logs: dict[str, tuple[float, ...]],
) -> tuple[dict[str, float], dict[str, int]]:
    """Solve centered component profiles and anchor them to observed medians."""
    pairwise_by_samples = {
        (ratio.sample_a, ratio.sample_b): ratio for ratio in pairwise_ratios
    }
    solved_logs: dict[str, float] = {}
    component_ids: dict[str, int] = {}
    for component_index, component in enumerate(components, start=1):
        for sample_id in component:
            component_ids[sample_id] = component_index
        if len(component) == 1:
            sample_id = component[0]
            solved_logs[sample_id] = median(observed_logs[sample_id])
            continue

        index_by_sample = {
            sample_id: index for index, sample_id in enumerate(component)
        }
        equations: list[list[float]] = []
        targets: list[float] = []
        for sample_a_index, sample_a in enumerate(component):
            for sample_b in component[sample_a_index + 1 :]:
                ratio = pairwise_by_samples.get((sample_a, sample_b))
                if ratio is None:
                    continue
                equation = [0.0] * len(component)
                equation[index_by_sample[sample_a]] = -1.0
                equation[index_by_sample[sample_b]] = 1.0
                equations.append(equation)
                targets.append(ratio.median_log2_ratio)

        anchor = [1.0] * len(component)
        equations.append(anchor)
        targets.append(0.0)

        matrix = np.array(equations, dtype=float)
        target_vector = np.array(targets, dtype=float)
        centered_solution, *_ = np.linalg.lstsq(matrix, target_vector, rcond=None)
        offsets = [
            median(observed_logs[sample_id])
            - float(centered_solution[index_by_sample[sample_id]])
            for sample_id in component
        ]
        offset = median(tuple(offsets))
        for sample_id in component:
            solved_logs[sample_id] = float(
                centered_solution[index_by_sample[sample_id]] + offset
            )
    return solved_logs, component_ids


def median(values: tuple[float, ...]) -> float:
    """Return the median value for one finite tuple."""
    ordered = sorted(values)
    midpoint = len(ordered) // 2
    if len(ordered) % 2 == 1:
        return float(ordered[midpoint])
    return float((ordered[midpoint - 1] + ordered[midpoint]) / 2.0)


__all__ = [
    "build_pairwise_ratio_rows",
    "build_pairwise_ratio_rows_pure",
    "build_pairwise_ratio_rows_vectorized",
    "connected_components",
    "median",
    "observed_log2_intensities_by_sample",
    "observed_log2_intensities_by_sample_pure",
    "observed_log2_intensities_by_sample_vectorized",
    "solve_component_profiles",
]
