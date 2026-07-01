# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Neutral-loss aware PTM fragment scoring."""

from __future__ import annotations

import csv
from io import StringIO

from pydantic import ConfigDict, Field

from bijux_proteomics.chemistry.fragments import (
    FragmentIon,
    FragmentIonSeries,
    calculate_fragment_ions,
)
from bijux_proteomics.chemistry.modifications import (
    ModificationPosition,
    ModificationRegistryDocument,
    ParsedModifiedPeptide,
    get_modification,
    parse_modified_peptide,
)
from bijux_proteomics.io.spectra import SpectrumPeak
from bijux_proteomics_foundation import JsonModel


class PtmFragmentScoreRow(JsonModel):
    """One observed PTM fragment match with localization-aware annotation."""

    model_config = ConfigDict(extra="forbid")

    ion_id: str = Field(..., min_length=1)
    ion_type: str = Field(..., min_length=1)
    neutral_loss: str | None = None
    theoretical_mz: float = Field(..., gt=0.0)
    observed_mz: float = Field(..., gt=0.0)
    ppm_error: float
    intensity: float = Field(..., ge=0.0)
    site_determining: bool


def score_ptm_fragments(
    modified_peptide: str | ParsedModifiedPeptide,
    observed_peaks: tuple[SpectrumPeak, ...],
    tolerance: float,
    *,
    charges: tuple[int, ...] = (1,),
    series: tuple[FragmentIonSeries, ...] = (
        FragmentIonSeries.B,
        FragmentIonSeries.Y,
    ),
    registry: ModificationRegistryDocument | None = None,
) -> tuple[PtmFragmentScoreRow, ...]:
    """Score observed peaks against PTM-aware theoretical fragments."""

    if tolerance <= 0.0:
        raise ValueError("tolerance must be greater than zero")
    parsed = _ensure_parsed_peptide(modified_peptide, registry=registry)
    theoretical_ions = calculate_fragment_ions(
        parsed,
        charges=charges,
        series=series,
        include_neutral_losses=True,
        registry=registry,
    )
    matched_rows: list[PtmFragmentScoreRow] = []
    for ion in theoretical_ions:
        match = _best_matching_peak(
            observed_peaks=observed_peaks,
            theoretical_mz=ion.mz_monoisotopic,
            tolerance=tolerance,
        )
        if match is None:
            continue
        observed_mz, intensity = match
        ppm_error = (
            (observed_mz - ion.mz_monoisotopic) / ion.mz_monoisotopic
        ) * 1_000_000.0
        matched_rows.append(
            PtmFragmentScoreRow(
                ion_id=_ion_id(ion),
                ion_type=ion.series.value,
                neutral_loss=ion.neutral_loss,
                theoretical_mz=ion.mz_monoisotopic,
                observed_mz=observed_mz,
                ppm_error=ppm_error,
                intensity=intensity,
                site_determining=_is_site_determining_ion(
                    ion,
                    peptide=parsed,
                    registry=registry,
                ),
            )
        )
    return tuple(
        sorted(
            matched_rows,
            key=lambda row: (
                row.ion_type,
                row.theoretical_mz,
                row.neutral_loss or "",
                row.ion_id,
            ),
        )
    )


def render_ptm_fragment_scores_tsv(rows: tuple[PtmFragmentScoreRow, ...]) -> str:
    """Render PTM fragment scores as a stable TSV ledger."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "ion_id",
            "ion_type",
            "neutral_loss",
            "theoretical_mz",
            "observed_mz",
            "ppm_error",
            "intensity",
            "site_determining",
        )
    )
    for row in rows:
        writer.writerow(
            (
                row.ion_id,
                row.ion_type,
                row.neutral_loss,
                row.theoretical_mz,
                row.observed_mz,
                row.ppm_error,
                row.intensity,
                str(row.site_determining).lower(),
            )
        )
    return buffer.getvalue()


def _ensure_parsed_peptide(
    peptide: str | ParsedModifiedPeptide,
    *,
    registry: ModificationRegistryDocument | None,
) -> ParsedModifiedPeptide:
    if isinstance(peptide, ParsedModifiedPeptide):
        return peptide
    return parse_modified_peptide(peptide, registry=registry)


def _best_matching_peak(
    *,
    observed_peaks: tuple[SpectrumPeak, ...],
    theoretical_mz: float,
    tolerance: float,
) -> tuple[float, float] | None:
    best_peak: SpectrumPeak | None = None
    best_error: float | None = None
    for peak in observed_peaks:
        error = peak.mz - theoretical_mz
        if abs(error) > tolerance:
            continue
        if (
            best_peak is None
            or best_error is None
            or abs(error) < abs(best_error)
            or (abs(error) == abs(best_error) and peak.intensity > best_peak.intensity)
        ):
            best_peak = peak
            best_error = error
    if best_peak is None:
        return None
    return best_peak.mz, best_peak.intensity


def _ion_id(ion: FragmentIon) -> str:
    neutral_loss_suffix = "" if ion.neutral_loss is None else f"-{ion.neutral_loss}"
    return f"{ion.series.value}{ion.ordinal}+{ion.charge}{neutral_loss_suffix}"


def _is_site_determining_ion(
    ion: FragmentIon,
    *,
    peptide: ParsedModifiedPeptide,
    registry: ModificationRegistryDocument | None,
) -> bool:
    if ion.neutral_loss is not None:
        return False
    for modification in peptide.modifications:
        site_index = modification.site_index
        if modification.site is not ModificationPosition.ANYWHERE or site_index is None:
            continue
        if site_index < ion.span_start or site_index > ion.span_end:
            continue
        definition = get_modification(modification.name, registry=registry)
        eligible_positions = tuple(
            index
            for index, residue in enumerate(peptide.sequence, start=1)
            if residue in definition.residues
        )
        if len(eligible_positions) <= 1:
            continue
        covered_positions = tuple(
            position
            for position in eligible_positions
            if ion.span_start <= position <= ion.span_end
        )
        if covered_positions == (site_index,):
            return True
    return False
