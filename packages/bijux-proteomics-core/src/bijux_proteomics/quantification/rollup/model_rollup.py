# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Peptide-bias-aware protein rollup over peptide-intensity matrices."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from io import StringIO
import math

import numpy as np
from pydantic import ConfigDict, Field

from bijux_proteomics.domain.records import QuantMatrix as CanonicalQuantMatrix
from bijux_proteomics.quantification.matrix.peptide_intensity_matrix import (
    PeptideIntensityMatrixReport,
)
from bijux_proteomics_foundation import JsonModel


class PeptideToProteinEntry(JsonModel):
    """One explicit peptide-to-protein assignment for additive rollup fitting."""

    model_config = ConfigDict(extra="forbid")

    peptide_id: str = Field(..., min_length=1)
    protein_id: str = Field(..., min_length=1)


class ProteinAbundanceEntry(JsonModel):
    """One fitted protein abundance for one sample."""

    model_config = ConfigDict(extra="forbid")

    protein_id: str = Field(..., min_length=1)
    sample_id: str = Field(..., min_length=1)
    abundance: float = Field(..., ge=0.0)
    log2_abundance: float
    supporting_peptide_count: int = Field(..., ge=1)


class PeptideBiasEntry(JsonModel):
    """One learned constant peptide bias within one protein rollup model."""

    model_config = ConfigDict(extra="forbid")

    protein_id: str = Field(..., min_length=1)
    peptide_id: str = Field(..., min_length=1)
    peptide_sequence: str = Field(..., min_length=1)
    peptide_bias_log2: float
    observed_sample_count: int = Field(..., ge=0)


class RollupResidualEntry(JsonModel):
    """One observed peptide intensity and its additive-model residual."""

    model_config = ConfigDict(extra="forbid")

    protein_id: str = Field(..., min_length=1)
    peptide_id: str = Field(..., min_length=1)
    sample_id: str = Field(..., min_length=1)
    observed_log2_intensity: float
    fitted_log2_intensity: float
    residual_log2: float


class PeptideBiasRollupReport(JsonModel):
    """Fitted peptide-bias rollup outputs over one peptide-intensity matrix."""

    model_config = ConfigDict(extra="forbid")

    protein_abundance: tuple[ProteinAbundanceEntry, ...] = Field(default_factory=tuple)
    peptide_bias: tuple[PeptideBiasEntry, ...] = Field(default_factory=tuple)
    residuals: tuple[RollupResidualEntry, ...] = Field(default_factory=tuple)
    note: str = Field(..., min_length=1)


@dataclass(frozen=True)
class _ObservedPeptideValue:
    peptide_id: str
    peptide_sequence: str
    sample_id: str
    log2_intensity: float


def fit_peptide_bias_model(
    peptide_matrix: PeptideIntensityMatrixReport | CanonicalQuantMatrix,
    peptide_to_protein: tuple[PeptideToProteinEntry, ...],
) -> PeptideBiasRollupReport:
    """Fit an additive protein-plus-peptide-bias model in log2 intensity space."""

    if isinstance(peptide_matrix, CanonicalQuantMatrix):
        peptide_matrix = PeptideIntensityMatrixReport.from_quant_matrix(peptide_matrix)
    if not peptide_to_protein:
        raise ValueError("peptide_to_protein must not be empty")

    peptide_map = _validate_peptide_mapping(peptide_to_protein)
    observed_values = _observed_values(peptide_matrix)
    missing_mappings = sorted(
        peptide_id for peptide_id in observed_values if peptide_id not in peptide_map
    )
    if missing_mappings:
        raise ValueError(
            "peptide_to_protein is missing observed peptide assignments for: "
            + ", ".join(missing_mappings)
        )

    protein_observations: dict[str, list[_ObservedPeptideValue]] = {}
    for peptide_id, peptide_entries in observed_values.items():
        protein_id = peptide_map[peptide_id]
        protein_observations.setdefault(protein_id, []).extend(peptide_entries)

    abundance_rows: list[ProteinAbundanceEntry] = []
    bias_rows: list[PeptideBiasEntry] = []
    residual_rows: list[RollupResidualEntry] = []

    peptide_sequence_by_id = {
        row.entity_id: row.peptide_sequence for row in peptide_matrix.rows
    }

    for protein_id in sorted(protein_observations):
        component_entries = _fit_protein_components(
            protein_id=protein_id,
            observations=tuple(protein_observations[protein_id]),
            peptide_sequence_by_id=peptide_sequence_by_id,
        )
        abundance_rows.extend(component_entries[0])
        bias_rows.extend(component_entries[1])
        residual_rows.extend(component_entries[2])

    return PeptideBiasRollupReport(
        protein_abundance=tuple(
            sorted(
                abundance_rows,
                key=lambda entry: (entry.protein_id, entry.sample_id),
            )
        ),
        peptide_bias=tuple(
            sorted(
                bias_rows,
                key=lambda entry: (entry.protein_id, entry.peptide_id),
            )
        ),
        residuals=tuple(
            sorted(
                residual_rows,
                key=lambda entry: (entry.protein_id, entry.peptide_id, entry.sample_id),
            )
        ),
        note=(
            "protein rollup fits log2 peptide intensities as protein abundance plus "
            "constant peptide bias so peptide-specific offsets do not masquerade as "
            "biological sample effects"
        ),
    )


def render_protein_abundance_tsv(report: PeptideBiasRollupReport) -> str:
    """Render fitted protein abundances as TSV."""

    return _render_rows(
        (
            "protein_id",
            "sample_id",
            "abundance",
            "log2_abundance",
            "supporting_peptide_count",
        ),
        (
            (
                entry.protein_id,
                entry.sample_id,
                f"{entry.abundance:.6f}",
                f"{entry.log2_abundance:.6f}",
                str(entry.supporting_peptide_count),
            )
            for entry in report.protein_abundance
        ),
    )


def render_peptide_bias_tsv(report: PeptideBiasRollupReport) -> str:
    """Render fitted peptide bias terms as TSV."""

    return _render_rows(
        (
            "protein_id",
            "peptide_id",
            "peptide_sequence",
            "peptide_bias_log2",
            "observed_sample_count",
        ),
        (
            (
                entry.protein_id,
                entry.peptide_id,
                entry.peptide_sequence,
                f"{entry.peptide_bias_log2:.6f}",
                str(entry.observed_sample_count),
            )
            for entry in report.peptide_bias
        ),
    )


def render_rollup_residuals_tsv(report: PeptideBiasRollupReport) -> str:
    """Render additive-model residual rows as TSV."""

    return _render_rows(
        (
            "protein_id",
            "peptide_id",
            "sample_id",
            "observed_log2_intensity",
            "fitted_log2_intensity",
            "residual_log2",
        ),
        (
            (
                entry.protein_id,
                entry.peptide_id,
                entry.sample_id,
                f"{entry.observed_log2_intensity:.6f}",
                f"{entry.fitted_log2_intensity:.6f}",
                f"{entry.residual_log2:.6f}",
            )
            for entry in report.residuals
        ),
    )


def _validate_peptide_mapping(
    peptide_to_protein: tuple[PeptideToProteinEntry, ...],
) -> dict[str, str]:
    mapping: dict[str, str] = {}
    conflicting: dict[str, set[str]] = {}
    for entry in peptide_to_protein:
        if entry.peptide_id in mapping and mapping[entry.peptide_id] != entry.protein_id:
            conflicting.setdefault(entry.peptide_id, {mapping[entry.peptide_id]}).add(
                entry.protein_id
            )
            continue
        mapping[entry.peptide_id] = entry.protein_id
    if conflicting:
        raise ValueError(
            "peptide_to_protein must assign each peptide to exactly one protein and "
            "found conflicts for: "
            + ", ".join(
                f"{peptide_id} ({', '.join(sorted(proteins))})"
                for peptide_id, proteins in sorted(conflicting.items())
            )
        )
    return mapping


def _observed_values(
    peptide_matrix: PeptideIntensityMatrixReport,
) -> dict[str, tuple[_ObservedPeptideValue, ...]]:
    observed: dict[str, list[_ObservedPeptideValue]] = {}
    for row in peptide_matrix.rows:
        for value in row.values:
            if value.abundance is None or value.abundance <= 0.0:
                continue
            observed.setdefault(row.entity_id, []).append(
                _ObservedPeptideValue(
                    peptide_id=row.entity_id,
                    peptide_sequence=row.peptide_sequence,
                    sample_id=value.sample_id,
                    log2_intensity=math.log2(value.abundance),
                )
            )
    return {peptide_id: tuple(entries) for peptide_id, entries in observed.items()}


def _fit_protein_components(
    *,
    protein_id: str,
    observations: tuple[_ObservedPeptideValue, ...],
    peptide_sequence_by_id: dict[str, str],
) -> tuple[list[ProteinAbundanceEntry], list[PeptideBiasEntry], list[RollupResidualEntry]]:
    by_peptide: dict[str, list[_ObservedPeptideValue]] = {}
    by_sample: dict[str, list[_ObservedPeptideValue]] = {}
    for observation in observations:
        by_peptide.setdefault(observation.peptide_id, []).append(observation)
        by_sample.setdefault(observation.sample_id, []).append(observation)

    components = _connected_components(
        peptide_ids=tuple(sorted(by_peptide)),
        sample_ids=tuple(sorted(by_sample)),
        observations=observations,
    )

    abundance_rows: list[ProteinAbundanceEntry] = []
    bias_rows: list[PeptideBiasEntry] = []
    residual_rows: list[RollupResidualEntry] = []

    for peptide_ids, sample_ids in components:
        component_observations = tuple(
            observation
            for observation in observations
            if observation.peptide_id in peptide_ids and observation.sample_id in sample_ids
        )
        sample_effects, peptide_biases = _fit_component_model(
            component_observations,
            peptide_ids=peptide_ids,
            sample_ids=sample_ids,
        )

        support_by_sample = {
            sample_id: len(
                {observation.peptide_id for observation in component_observations if observation.sample_id == sample_id}
            )
            for sample_id in sample_ids
        }
        for sample_id in sample_ids:
            log2_abundance = sample_effects[sample_id]
            abundance_rows.append(
                ProteinAbundanceEntry(
                    protein_id=protein_id,
                    sample_id=sample_id,
                    abundance=round(2.0**log2_abundance, 6),
                    log2_abundance=round(log2_abundance, 6),
                    supporting_peptide_count=support_by_sample[sample_id],
                )
            )
        for peptide_id in peptide_ids:
            bias_rows.append(
                PeptideBiasEntry(
                    protein_id=protein_id,
                    peptide_id=peptide_id,
                    peptide_sequence=peptide_sequence_by_id.get(peptide_id, peptide_id),
                    peptide_bias_log2=round(peptide_biases[peptide_id], 6),
                    observed_sample_count=len(
                        {
                            observation.sample_id
                            for observation in component_observations
                            if observation.peptide_id == peptide_id
                        }
                    ),
                )
            )
        for observation in component_observations:
            fitted = sample_effects[observation.sample_id] + peptide_biases[observation.peptide_id]
            residual_rows.append(
                RollupResidualEntry(
                    protein_id=protein_id,
                    peptide_id=observation.peptide_id,
                    sample_id=observation.sample_id,
                    observed_log2_intensity=round(observation.log2_intensity, 6),
                    fitted_log2_intensity=round(fitted, 6),
                    residual_log2=round(observation.log2_intensity - fitted, 6),
                )
            )

    return abundance_rows, bias_rows, residual_rows


def _connected_components(
    *,
    peptide_ids: tuple[str, ...],
    sample_ids: tuple[str, ...],
    observations: tuple[_ObservedPeptideValue, ...],
) -> tuple[tuple[tuple[str, ...], tuple[str, ...]], ...]:
    peptide_to_samples: dict[str, set[str]] = {peptide_id: set() for peptide_id in peptide_ids}
    sample_to_peptides: dict[str, set[str]] = {sample_id: set() for sample_id in sample_ids}
    for observation in observations:
        peptide_to_samples[observation.peptide_id].add(observation.sample_id)
        sample_to_peptides[observation.sample_id].add(observation.peptide_id)

    visited_peptides: set[str] = set()
    visited_samples: set[str] = set()
    components: list[tuple[tuple[str, ...], tuple[str, ...]]] = []

    for peptide_id in peptide_ids:
        if peptide_id in visited_peptides:
            continue
        pending_peptides = [peptide_id]
        component_peptides: set[str] = set()
        component_samples: set[str] = set()
        while pending_peptides:
            current_peptide = pending_peptides.pop()
            if current_peptide in visited_peptides:
                continue
            visited_peptides.add(current_peptide)
            component_peptides.add(current_peptide)
            for sample_id in peptide_to_samples[current_peptide]:
                if sample_id in component_samples:
                    continue
                component_samples.add(sample_id)
                if sample_id in visited_samples:
                    continue
                visited_samples.add(sample_id)
                for linked_peptide in sample_to_peptides[sample_id]:
                    if linked_peptide not in visited_peptides:
                        pending_peptides.append(linked_peptide)
        components.append(
            (tuple(sorted(component_peptides)), tuple(sorted(component_samples)))
        )
    return tuple(components)


def _fit_component_model(
    observations: tuple[_ObservedPeptideValue, ...],
    *,
    peptide_ids: tuple[str, ...],
    sample_ids: tuple[str, ...],
) -> tuple[dict[str, float], dict[str, float]]:
    if len(peptide_ids) == 1:
        peptide_id = peptide_ids[0]
        sample_effects = {
            sample_id: median_value
            for sample_id, median_value in _per_sample_medians(observations).items()
        }
        return sample_effects, {peptide_id: 0.0}

    sample_index = {sample_id: index for index, sample_id in enumerate(sample_ids)}
    bias_index = {
        peptide_id: len(sample_ids) + index
        for index, peptide_id in enumerate(peptide_ids[1:])
    }
    design = np.zeros((len(observations), len(sample_ids) + len(peptide_ids) - 1))
    target = np.zeros(len(observations))
    for row_index, observation in enumerate(observations):
        design[row_index, sample_index[observation.sample_id]] = 1.0
        if observation.peptide_id in bias_index:
            design[row_index, bias_index[observation.peptide_id]] = 1.0
        target[row_index] = observation.log2_intensity

    coefficients, _, _, _ = np.linalg.lstsq(design, target, rcond=None)
    sample_effects = {
        sample_id: float(coefficients[index]) for sample_id, index in sample_index.items()
    }
    peptide_biases = {peptide_ids[0]: 0.0}
    for peptide_id in peptide_ids[1:]:
        peptide_biases[peptide_id] = float(coefficients[bias_index[peptide_id]])

    mean_bias = sum(peptide_biases.values()) / len(peptide_biases)
    peptide_biases = {
        peptide_id: bias - mean_bias for peptide_id, bias in peptide_biases.items()
    }
    sample_effects = {
        sample_id: effect + mean_bias for sample_id, effect in sample_effects.items()
    }
    return sample_effects, peptide_biases


def _per_sample_medians(
    observations: tuple[_ObservedPeptideValue, ...],
) -> dict[str, float]:
    by_sample: dict[str, list[float]] = {}
    for observation in observations:
        by_sample.setdefault(observation.sample_id, []).append(observation.log2_intensity)
    return {
        sample_id: float(np.median(values))
        for sample_id, values in sorted(by_sample.items())
    }


def _render_rows(header: tuple[str, ...], rows: tuple[tuple[str, ...], ...] | object) -> str:
    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(header)
    for row in rows:
        writer.writerow(row)
    return buffer.getvalue()


__all__ = [
    "PeptideBiasEntry",
    "PeptideBiasRollupReport",
    "PeptideToProteinEntry",
    "ProteinAbundanceEntry",
    "RollupResidualEntry",
    "fit_peptide_bias_model",
    "render_peptide_bias_tsv",
    "render_protein_abundance_tsv",
    "render_rollup_residuals_tsv",
]
