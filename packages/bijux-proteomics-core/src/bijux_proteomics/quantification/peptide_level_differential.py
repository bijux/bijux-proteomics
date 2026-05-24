# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Peptide-level differential testing with explicit peptide-disagreement downgrades."""

from __future__ import annotations

import csv
from io import StringIO
import math

import numpy as np
from pydantic import ConfigDict, Field

from bijux_proteomics.domain.records import QuantMatrix as CanonicalQuantMatrix
from bijux_proteomics.io.formats import ExperimentalDesignEntry
from bijux_proteomics.quantification.contracts import (
    _condition_lookup,
    _student_t_two_sided_p_value,
)
from bijux_proteomics.quantification.peptide_intensity_matrix import (
    PeptideIntensityMatrixReport,
)
from bijux_proteomics_foundation import JsonModel


class PeptideLevelDifferentialEntry(JsonModel):
    """One protein-level effect estimated from peptide-level intensities."""

    model_config = ConfigDict(extra="forbid")

    protein_id: str = Field(..., min_length=1)
    log2fc: float
    p_value: float = Field(..., ge=0.0, le=1.0)
    q_value: float = Field(..., ge=0.0, le=1.0)
    peptide_count: int = Field(..., ge=1)
    peptide_disagreement_score: float = Field(..., ge=0.0, le=1.0)


class PeptideLevelDifferentialReport(JsonModel):
    """Protein-level differential report derived from peptide observations."""

    model_config = ConfigDict(extra="forbid")

    condition_a: str = Field(..., min_length=1)
    condition_b: str = Field(..., min_length=1)
    entries: tuple[PeptideLevelDifferentialEntry, ...] = Field(default_factory=tuple)
    note: str = Field(..., min_length=1)


class _ObservedPeptideIntensity(JsonModel):
    """Internal observed peptide intensity on one sample."""

    model_config = ConfigDict(extra="forbid")

    protein_id: str = Field(..., min_length=1)
    peptide_id: str = Field(..., min_length=1)
    sample_id: str = Field(..., min_length=1)
    condition: str = Field(..., min_length=1)
    log2_intensity: float


def test_protein_effect_from_peptides(
    peptide_matrix: PeptideIntensityMatrixReport | CanonicalQuantMatrix,
    design: tuple[ExperimentalDesignEntry, ...],
    *,
    condition_a: str | None = None,
    condition_b: str | None = None,
) -> PeptideLevelDifferentialReport:
    """Estimate protein effects from peptide rows and downgrade conflicted proteins."""

    if isinstance(peptide_matrix, CanonicalQuantMatrix):
        peptide_matrix = PeptideIntensityMatrixReport.from_quant_matrix(peptide_matrix)
    if not design:
        raise ValueError("design must not be empty")

    condition_by_sample = _condition_lookup(design)
    design_conditions = tuple(sorted({value for value in condition_by_sample.values() if value}))
    if condition_a is None or condition_b is None:
        if len(design_conditions) != 2:
            raise ValueError(
                "peptide-level differential requires exactly two conditions or explicit condition names"
            )
        condition_a, condition_b = design_conditions
    assert condition_a is not None
    assert condition_b is not None
    if condition_a == condition_b:
        raise ValueError("condition_a and condition_b must be different")

    observed = _collect_observed_peptide_intensities(
        peptide_matrix=peptide_matrix,
        condition_by_sample=condition_by_sample,
        condition_a=condition_a,
        condition_b=condition_b,
    )
    entries: list[PeptideLevelDifferentialEntry] = []
    for protein_id in sorted(observed):
        protein_rows = observed[protein_id]
        if not protein_rows:
            continue
        entries.append(
            _fit_one_protein(
                protein_id=protein_id,
                observed=tuple(protein_rows),
                condition_a=condition_a,
                condition_b=condition_b,
            )
        )

    adjusted_q_values = _benjamini_hochberg(tuple(entry.p_value for entry in entries))
    corrected_entries = tuple(
        entry.model_copy(update={"q_value": adjusted_q_values[index]})
        for index, entry in enumerate(entries)
    )
    return PeptideLevelDifferentialReport(
        condition_a=condition_a,
        condition_b=condition_b,
        entries=tuple(sorted(corrected_entries, key=lambda entry: entry.protein_id)),
        note=(
            "protein differential effects are fit from log2 peptide intensities with "
            "explicit peptide offsets, then downgraded when peptide-level condition "
            "effects disagree about the underlying protein behavior"
        ),
    )


def render_peptide_level_differential_tsv(
    report: PeptideLevelDifferentialReport,
) -> str:
    """Render peptide-level differential results as TSV."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "protein_id",
            "log2fc",
            "p_value",
            "q_value",
            "peptide_count",
            "peptide_disagreement_score",
        )
    )
    for entry in report.entries:
        writer.writerow(
            (
                entry.protein_id,
                f"{entry.log2fc:.6f}",
                f"{entry.p_value:.6f}",
                f"{entry.q_value:.6f}",
                str(entry.peptide_count),
                f"{entry.peptide_disagreement_score:.6f}",
            )
        )
    return buffer.getvalue()


test_protein_effect_from_peptides.__test__ = False


def _collect_observed_peptide_intensities(
    *,
    peptide_matrix: PeptideIntensityMatrixReport,
    condition_by_sample: dict[str, str],
    condition_a: str,
    condition_b: str,
) -> dict[str, list[_ObservedPeptideIntensity]]:
    observed: dict[str, list[_ObservedPeptideIntensity]] = {}
    for row in peptide_matrix.rows:
        if len(row.protein_refs) != 1:
            continue
        protein_id = row.protein_refs[0]
        for value in row.values:
            abundance = value.abundance
            condition = condition_by_sample.get(value.sample_id)
            if abundance is None or abundance <= 0.0 or condition not in {condition_a, condition_b}:
                continue
            observed.setdefault(protein_id, []).append(
                _ObservedPeptideIntensity(
                    protein_id=protein_id,
                    peptide_id=row.entity_id,
                    sample_id=value.sample_id,
                    condition=condition,
                    log2_intensity=math.log2(abundance),
                )
            )
    return observed


def _fit_one_protein(
    *,
    protein_id: str,
    observed: tuple[_ObservedPeptideIntensity, ...],
    condition_a: str,
    condition_b: str,
) -> PeptideLevelDifferentialEntry:
    peptide_ids = tuple(sorted({entry.peptide_id for entry in observed}))
    if not peptide_ids:
        raise ValueError("observed protein rows must contain at least one peptide")

    peptide_index = {peptide_id: index for index, peptide_id in enumerate(peptide_ids)}
    design_width = 2 + max(len(peptide_ids) - 1, 0)
    design_matrix = np.zeros((len(observed), design_width), dtype=float)
    response = np.zeros(len(observed), dtype=float)
    for row_index, entry in enumerate(observed):
        design_matrix[row_index, 0] = 1.0
        design_matrix[row_index, 1] = 1.0 if entry.condition == condition_b else 0.0
        peptide_position = peptide_index[entry.peptide_id]
        if peptide_position > 0:
            design_matrix[row_index, 1 + peptide_position] = 1.0
        response[row_index] = entry.log2_intensity

    coefficients, _, _, _ = np.linalg.lstsq(design_matrix, response, rcond=None)
    fitted = design_matrix @ coefficients
    residuals = response - fitted
    log2fc = float(coefficients[1])
    raw_p_value = _condition_p_value(
        design_matrix=design_matrix,
        coefficients=coefficients,
        residuals=residuals,
        condition_coefficient_index=1,
    )
    disagreement_score = _peptide_disagreement_score(
        observed=observed,
        protein_log2fc=log2fc,
        condition_a=condition_a,
        condition_b=condition_b,
    )
    downgraded_p_value = min(
        1.0,
        raw_p_value + disagreement_score * (1.0 - raw_p_value),
    )
    return PeptideLevelDifferentialEntry(
        protein_id=protein_id,
        log2fc=round(log2fc, 6),
        p_value=round(downgraded_p_value, 6),
        q_value=1.0,
        peptide_count=len(peptide_ids),
        peptide_disagreement_score=round(disagreement_score, 6),
    )


def _condition_p_value(
    *,
    design_matrix: np.ndarray,
    coefficients: np.ndarray,
    residuals: np.ndarray,
    condition_coefficient_index: int,
) -> float:
    degrees_of_freedom = design_matrix.shape[0] - design_matrix.shape[1]
    if degrees_of_freedom <= 0:
        return 1.0
    xtx = design_matrix.T @ design_matrix
    try:
        xtx_inverse = np.linalg.inv(xtx)
    except np.linalg.LinAlgError:
        return 1.0
    residual_variance = float(np.sum(residuals * residuals) / degrees_of_freedom)
    if residual_variance <= 0.0:
        return 1.0
    standard_error = math.sqrt(
        residual_variance
        * float(xtx_inverse[condition_coefficient_index, condition_coefficient_index])
    )
    if standard_error <= 0.0 or not math.isfinite(standard_error):
        return 1.0
    t_statistic = float(coefficients[condition_coefficient_index] / standard_error)
    return _student_t_two_sided_p_value(abs(t_statistic), float(degrees_of_freedom))


def _peptide_disagreement_score(
    *,
    observed: tuple[_ObservedPeptideIntensity, ...],
    protein_log2fc: float,
    condition_a: str,
    condition_b: str,
) -> float:
    peptide_effects: list[float] = []
    by_peptide: dict[str, dict[str, list[float]]] = {}
    for entry in observed:
        by_peptide.setdefault(entry.peptide_id, {}).setdefault(entry.condition, []).append(
            entry.log2_intensity
        )
    for peptide_id in sorted(by_peptide):
        values_a = by_peptide[peptide_id].get(condition_a, [])
        values_b = by_peptide[peptide_id].get(condition_b, [])
        if not values_a or not values_b:
            continue
        peptide_effects.append(float(np.mean(values_b) - np.mean(values_a)))
    if len(peptide_effects) <= 1:
        return 0.0

    effect_array = np.array(peptide_effects, dtype=float)
    spread = float(np.sqrt(np.mean((effect_array - protein_log2fc) ** 2)))
    positive = np.any(effect_array >= 0.35)
    negative = np.any(effect_array <= -0.35)
    directional_conflict = 1.0 if positive and negative else 0.0
    disagreement = min(1.0, spread / 2.0 + (0.35 * directional_conflict))
    return disagreement


def _benjamini_hochberg(p_values: tuple[float, ...]) -> tuple[float, ...]:
    if not p_values:
        return ()
    adjusted: list[float] = [1.0] * len(p_values)
    running = 1.0
    total = len(p_values)
    ordered = sorted(enumerate(p_values), key=lambda item: item[1])
    for reverse_rank, (index, p_value) in enumerate(reversed(ordered), start=1):
        rank = total - reverse_rank + 1
        candidate = p_value * total / rank
        running = min(running, candidate)
        adjusted[index] = min(max(running, 0.0), 1.0)
    return tuple(adjusted)


__all__ = [
    "PeptideLevelDifferentialEntry",
    "PeptideLevelDifferentialReport",
    "render_peptide_level_differential_tsv",
    "test_protein_effect_from_peptides",
]
