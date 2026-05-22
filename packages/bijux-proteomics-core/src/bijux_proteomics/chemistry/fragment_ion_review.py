# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Reviewer-facing fragment-ion generation surfaces."""

from __future__ import annotations

import csv
import io

from pydantic import ConfigDict, Field

from bijux_proteomics.chemistry.contracts import (
    FragmentIon,
    FragmentIonSeries,
    ModificationRegistryDocument,
    ParsedModifiedPeptide,
    build_modified_peptide,
    calculate_fragment_ions,
    canonicalize_modified_peptide,
    parse_modified_peptide,
)
from bijux_proteomics_foundation import JsonModel


class FragmentIonReviewReport(JsonModel):
    """One reviewer-facing fragment-ion generation report."""

    model_config = ConfigDict(extra="forbid")

    canonical_notation: str = Field(..., min_length=1)
    residue_sequence: str = Field(..., min_length=1)
    charges: tuple[int, ...] = Field(default_factory=tuple)
    series: tuple[FragmentIonSeries, ...] = Field(default_factory=tuple)
    include_neutral_losses: bool = False
    fragment_ion_count: int = Field(..., ge=0)
    counts_by_series: dict[str, int] = Field(default_factory=dict)
    counts_by_charge: dict[str, int] = Field(default_factory=dict)
    neutral_loss_count: int = Field(..., ge=0)
    ions: tuple[FragmentIon, ...] = Field(default_factory=tuple)


def build_fragment_ion_review_report(
    peptide: str | ParsedModifiedPeptide,
    *,
    charges: tuple[int, ...] = (1, 2, 3),
    series: tuple[FragmentIonSeries, ...] = (
        FragmentIonSeries.A,
        FragmentIonSeries.B,
        FragmentIonSeries.Y,
    ),
    include_neutral_losses: bool = False,
    registry: ModificationRegistryDocument | None = None,
) -> FragmentIonReviewReport:
    """Build one fragment-ion review report for a peptide."""
    parsed = _ensure_review_peptide(peptide, registry=registry)
    ions = calculate_fragment_ions(
        parsed,
        charges=charges,
        series=series,
        include_neutral_losses=include_neutral_losses,
        registry=registry,
    )
    counts_by_series: dict[str, int] = {}
    counts_by_charge: dict[str, int] = {}
    neutral_loss_count = 0

    for ion in ions:
        counts_by_series[ion.series.value] = (
            counts_by_series.get(ion.series.value, 0) + 1
        )
        charge_key = str(ion.charge)
        counts_by_charge[charge_key] = counts_by_charge.get(charge_key, 0) + 1
        if ion.neutral_loss is not None:
            neutral_loss_count += 1

    return FragmentIonReviewReport(
        canonical_notation=canonicalize_modified_peptide(parsed, registry=registry),
        residue_sequence=parsed.sequence,
        charges=tuple(sorted(dict.fromkeys(charges))),
        series=tuple(series),
        include_neutral_losses=include_neutral_losses,
        fragment_ion_count=len(ions),
        counts_by_series=dict(sorted(counts_by_series.items())),
        counts_by_charge=dict(
            sorted(counts_by_charge.items(), key=lambda item: int(item[0]))
        ),
        neutral_loss_count=neutral_loss_count,
        ions=ions,
    )


def render_fragment_ion_report_tsv(report: FragmentIonReviewReport) -> str:
    """Render fragment-ion rows as a stable TSV table."""
    buffer = io.StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "series",
            "ordinal",
            "charge",
            "span_start",
            "span_end",
            "sequence",
            "neutral_loss",
            "neutral_mass_monoisotopic",
            "neutral_mass_average",
            "mz_monoisotopic",
            "mz_average",
        )
    )
    for ion in report.ions:
        writer.writerow(
            (
                ion.series.value,
                ion.ordinal,
                ion.charge,
                ion.span_start,
                ion.span_end,
                ion.sequence,
                ion.neutral_loss,
                ion.neutral_mass_monoisotopic,
                ion.neutral_mass_average,
                ion.mz_monoisotopic,
                ion.mz_average,
            )
        )
    return buffer.getvalue()


def _ensure_review_peptide(
    peptide: str | ParsedModifiedPeptide,
    *,
    registry: ModificationRegistryDocument | None,
) -> ParsedModifiedPeptide:
    if isinstance(peptide, ParsedModifiedPeptide):
        return peptide
    if "[" in peptide or peptide.startswith("["):
        return parse_modified_peptide(peptide, registry=registry)
    return build_modified_peptide(peptide, registry=registry)
