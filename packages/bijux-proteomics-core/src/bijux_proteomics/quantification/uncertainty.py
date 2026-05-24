# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Protein abundance uncertainty intervals over peptide-bias rollup models."""

from __future__ import annotations

import csv
from enum import StrEnum
from io import StringIO
import math

from pydantic import ConfigDict, Field

from bijux_proteomics.quantification.model_rollup import PeptideBiasRollupReport
from bijux_proteomics_foundation import JsonModel


class ProteinUncertaintySource(StrEnum):
    """Primary driver for one protein abundance uncertainty interval."""

    SINGLE_PEPTIDE_SUPPORT = "single_peptide_support"
    RESIDUAL_DISPERSION = "residual_dispersion"
    MULTI_PEPTIDE_SUPPORT = "multi_peptide_support"


class ProteinAbundanceUncertaintyEntry(JsonModel):
    """One protein abundance interval for one sample."""

    model_config = ConfigDict(extra="forbid")

    protein_id: str = Field(..., min_length=1)
    sample_id: str = Field(..., min_length=1)
    abundance: float = Field(..., ge=0.0)
    lower_ci: float = Field(..., ge=0.0)
    upper_ci: float = Field(..., ge=0.0)
    uncertainty_source: ProteinUncertaintySource
    supporting_peptide_count: int = Field(..., ge=1)


class ProteinAbundanceUncertaintyReport(JsonModel):
    """Protein abundance intervals derived from peptide-bias rollup evidence."""

    model_config = ConfigDict(extra="forbid")

    entries: tuple[ProteinAbundanceUncertaintyEntry, ...] = Field(default_factory=tuple)
    note: str = Field(..., min_length=1)


def estimate_protein_uncertainty(
    model_rollup_result: PeptideBiasRollupReport,
    *,
    minimum_half_width_log2: float = 0.1,
) -> ProteinAbundanceUncertaintyReport:
    """Estimate protein abundance intervals from rollup support and residual structure."""

    if minimum_half_width_log2 <= 0.0:
        raise ValueError("minimum_half_width_log2 must be positive")

    residuals_by_protein: dict[str, list[float]] = {}
    for entry in model_rollup_result.residuals:
        residuals_by_protein.setdefault(entry.protein_id, []).append(entry.residual_log2)

    peptide_counts_by_protein = {
        protein_id: len(
            {
                entry.peptide_id
                for entry in model_rollup_result.peptide_bias
                if entry.protein_id == protein_id
            }
        )
        for protein_id in {
            entry.protein_id for entry in model_rollup_result.protein_abundance
        }
    }

    entries: list[ProteinAbundanceUncertaintyEntry] = []
    for abundance_entry in model_rollup_result.protein_abundance:
        protein_id = abundance_entry.protein_id
        residual_sd = _residual_sd_log2(residuals_by_protein.get(protein_id, ()))
        distinct_peptide_count = peptide_counts_by_protein.get(protein_id, 0)
        half_width_log2, source = _half_width_and_source(
            supporting_peptide_count=abundance_entry.supporting_peptide_count,
            distinct_peptide_count=distinct_peptide_count,
            residual_sd_log2=residual_sd,
            minimum_half_width_log2=minimum_half_width_log2,
        )
        lower_ci = abundance_entry.abundance / (2.0**half_width_log2)
        upper_ci = abundance_entry.abundance * (2.0**half_width_log2)
        entries.append(
            ProteinAbundanceUncertaintyEntry(
                protein_id=protein_id,
                sample_id=abundance_entry.sample_id,
                abundance=abundance_entry.abundance,
                lower_ci=round(lower_ci, 6),
                upper_ci=round(upper_ci, 6),
                uncertainty_source=source,
                supporting_peptide_count=abundance_entry.supporting_peptide_count,
            )
        )

    return ProteinAbundanceUncertaintyReport(
        entries=tuple(
            sorted(entries, key=lambda entry: (entry.protein_id, entry.sample_id))
        ),
        note=(
            "protein abundance intervals combine rollup residual dispersion with "
            "per-sample peptide support and an explicit single-peptide identifiability "
            "penalty so under-supported protein estimates remain visibly uncertain"
        ),
    )


def render_protein_uncertainty_tsv(
    report: ProteinAbundanceUncertaintyReport,
) -> str:
    """Render protein abundance uncertainty entries as TSV."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "protein_id",
            "sample_id",
            "abundance",
            "lower_ci",
            "upper_ci",
            "uncertainty_source",
            "supporting_peptide_count",
        )
    )
    for entry in report.entries:
        writer.writerow(
            (
                entry.protein_id,
                entry.sample_id,
                f"{entry.abundance:.6f}",
                f"{entry.lower_ci:.6f}",
                f"{entry.upper_ci:.6f}",
                entry.uncertainty_source.value,
                str(entry.supporting_peptide_count),
            )
        )
    return buffer.getvalue()


def _residual_sd_log2(residuals: list[float] | tuple[float, ...]) -> float:
    if not residuals:
        return 0.0
    squared = sum(value * value for value in residuals)
    return math.sqrt(squared / len(residuals))


def _half_width_and_source(
    *,
    supporting_peptide_count: int,
    distinct_peptide_count: int,
    residual_sd_log2: float,
    minimum_half_width_log2: float,
) -> tuple[float, ProteinUncertaintySource]:
    support_term = 0.45 / math.sqrt(float(supporting_peptide_count))
    residual_term = residual_sd_log2 * 1.96
    single_peptide_penalty = 0.55 if distinct_peptide_count <= 1 else 0.0
    half_width = minimum_half_width_log2 + support_term + residual_term + single_peptide_penalty

    if distinct_peptide_count <= 1 or supporting_peptide_count <= 1:
        source = ProteinUncertaintySource.SINGLE_PEPTIDE_SUPPORT
    elif residual_sd_log2 >= 0.08:
        source = ProteinUncertaintySource.RESIDUAL_DISPERSION
    else:
        source = ProteinUncertaintySource.MULTI_PEPTIDE_SUPPORT
    return half_width, source


__all__ = [
    "ProteinAbundanceUncertaintyEntry",
    "ProteinAbundanceUncertaintyReport",
    "ProteinUncertaintySource",
    "estimate_protein_uncertainty",
    "render_protein_uncertainty_tsv",
]
