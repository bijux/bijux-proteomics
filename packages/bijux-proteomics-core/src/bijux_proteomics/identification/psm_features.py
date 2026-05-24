# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Real spectrum-derived feature extraction for canonical peptide-spectrum matches."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from io import StringIO
from math import log
from typing import Any

from pydantic import ConfigDict, Field

from bijux_proteomics.chemistry import calculate_fragment_ions, calculate_peptide_mz
from bijux_proteomics.identification.contracts import (
    PsmRecord,
    TargetDecoyLabel,
    parse_target_decoy_label,
)
from bijux_proteomics.io.spectra import SpectrumModel
from bijux_proteomics.io.spectrum_peak_matching import match_spectrum_peaks_to_fragments
from bijux_proteomics.sequences.digestion import count_missed_cleavages
from bijux_proteomics_foundation import JsonModel


class PsmFeatureRow(JsonModel):
    """One real rescoring feature row extracted from a canonical PSM and spectrum."""

    model_config = ConfigDict(extra="forbid")

    psm_id: str = Field(..., min_length=1)
    spectrum_id: str = Field(..., min_length=1)
    score_native: float
    q_value_native: float | None = Field(default=None, ge=0.0)
    charge: int = Field(..., ge=1)
    peptide_length: int = Field(..., ge=0)
    missed_cleavages: int = Field(..., ge=0)
    precursor_ppm_error: float
    matched_ion_count: int = Field(..., ge=0)
    explained_intensity: float = Field(..., ge=0.0, le=1.0)
    spectrum_entropy: float = Field(..., ge=0.0, le=1.0)
    top_peak_unmatched_fraction: float = Field(..., ge=0.0, le=1.0)
    target_decoy_label: TargetDecoyLabel


@dataclass(frozen=True)
class _PeptideMappingEntry:
    peptide_keys: tuple[str, ...]
    protein_refs: tuple[str, ...]


def extract_psm_features(
    psms: tuple[PsmRecord, ...],
    spectra: tuple[SpectrumModel, ...] | dict[str, SpectrumModel],
    peptides: dict[str, tuple[str, ...] | list[str] | str] | tuple[object, ...],
    fasta_index: dict[str, str],
    *,
    fragment_tolerance_da: float = 0.02,
    protease: str = "trypsin",
) -> tuple[PsmFeatureRow, ...]:
    """Extract spectrum-derived rescoring features for canonical PSM records.

    `explained_intensity` is emitted as the explained intensity fraction from the
    fragment-matching report because the rescoring surface needs a normalized signal
    feature rather than an engine-native absolute intensity scale.
    """

    if fragment_tolerance_da <= 0.0:
        raise ValueError("fragment_tolerance_da must be greater than zero")
    spectrum_index = _normalize_spectra(spectra)
    peptide_mapping = _normalize_peptide_mapping(peptides)
    normalized_fasta_index = {
        protein_ref.strip(): sequence.strip().upper()
        for protein_ref, sequence in fasta_index.items()
        if protein_ref.strip() and sequence.strip()
    }
    rows = [
        _extract_psm_feature_row(
            psm=psm,
            spectrum_index=spectrum_index,
            peptide_mapping=peptide_mapping,
            fasta_index=normalized_fasta_index,
            fragment_tolerance_da=fragment_tolerance_da,
            protease=protease,
        )
        for psm in psms
    ]
    return tuple(rows)


def render_psm_feature_tsv(rows: tuple[PsmFeatureRow, ...]) -> str:
    """Render extracted PSM feature rows as TSV."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "psm_id",
            "spectrum_id",
            "score_native",
            "q_value_native",
            "charge",
            "peptide_length",
            "missed_cleavages",
            "precursor_ppm_error",
            "matched_ion_count",
            "explained_intensity",
            "spectrum_entropy",
            "top_peak_unmatched_fraction",
            "target_decoy_label",
        )
    )
    for row in rows:
        writer.writerow(
            (
                row.psm_id,
                row.spectrum_id,
                row.score_native,
                "" if row.q_value_native is None else row.q_value_native,
                row.charge,
                row.peptide_length,
                row.missed_cleavages,
                row.precursor_ppm_error,
                row.matched_ion_count,
                row.explained_intensity,
                row.spectrum_entropy,
                row.top_peak_unmatched_fraction,
                row.target_decoy_label.value,
            )
        )
    return buffer.getvalue()


def _extract_psm_feature_row(
    *,
    psm: PsmRecord,
    spectrum_index: dict[str, SpectrumModel],
    peptide_mapping: tuple[_PeptideMappingEntry, ...],
    fasta_index: dict[str, str],
    fragment_tolerance_da: float,
    protease: str,
) -> PsmFeatureRow:
    spectrum = _find_spectrum(psm, spectrum_index)
    peptide_sequence = psm.peptide_sequence or psm.peptide or psm.canonical_peptide
    resolved_protein_refs = _resolve_protein_refs(
        psm=psm,
        peptide_mapping=peptide_mapping,
        fasta_index=fasta_index,
    )
    target_decoy_label = (
        psm.target_decoy_label
        if psm.target_decoy_label is not TargetDecoyLabel.UNKNOWN
        else parse_target_decoy_label(protein_refs=resolved_protein_refs)
    )
    theoretical_fragments = calculate_fragment_ions(
        psm.canonical_peptide,
        charges=tuple(range(1, min(psm.charge, 2) + 1)),
    )
    match_report = match_spectrum_peaks_to_fragments(
        spectrum,
        peptide=psm.canonical_peptide,
        theoretical_fragments=theoretical_fragments,
        tolerance_da=fragment_tolerance_da,
        tolerance_ppm=None,
    )
    expected_precursor_mz = calculate_peptide_mz(psm.canonical_peptide, charge=psm.charge)
    precursor_ppm_error = _ppm_error(
        observed_mz=spectrum.precursor_mz,
        expected_mz=expected_precursor_mz,
    )
    return PsmFeatureRow(
        psm_id=_psm_id(psm),
        spectrum_id=psm.spectrum_id,
        score_native=psm.score,
        q_value_native=psm.q_value,
        charge=psm.charge,
        peptide_length=len(peptide_sequence),
        missed_cleavages=count_missed_cleavages(peptide_sequence, protease),
        precursor_ppm_error=precursor_ppm_error,
        matched_ion_count=len(match_report.matches),
        explained_intensity=match_report.explained_intensity_fraction,
        spectrum_entropy=_calculate_normalized_spectral_entropy(spectrum),
        top_peak_unmatched_fraction=_top_peak_unmatched_fraction(
            spectrum=spectrum,
            match_report=match_report,
        ),
        target_decoy_label=target_decoy_label,
    )


def _normalize_spectra(
    spectra: tuple[SpectrumModel, ...] | dict[str, SpectrumModel],
) -> dict[str, SpectrumModel]:
    if isinstance(spectra, dict):
        return {
            spectrum_id: spectrum
            for spectrum_id, spectrum in spectra.items()
        }
    index: dict[str, SpectrumModel] = {}
    for spectrum in spectra:
        index[spectrum.spectrum_id] = spectrum
        if spectrum.native_id:
            index.setdefault(spectrum.native_id, spectrum)
        if spectrum.title:
            index.setdefault(spectrum.title, spectrum)
    return index


def _normalize_peptide_mapping(
    peptides: dict[str, tuple[str, ...] | list[str] | str] | tuple[object, ...],
) -> tuple[_PeptideMappingEntry, ...]:
    if isinstance(peptides, dict):
        return tuple(
            _PeptideMappingEntry(
                peptide_keys=(str(key).strip().upper(),),
                protein_refs=_normalize_protein_refs(raw_value),
            )
            for key, raw_value in peptides.items()
            if str(key).strip()
        )
    entries = []
    for entry in peptides:
        canonical = _string_field(entry, "canonical_peptide")
        peptide = _string_field(entry, "peptide")
        peptide_sequence = _string_field(entry, "peptide_sequence")
        mapped_protein_refs = _normalize_protein_refs(
            _field(entry, "protein_refs") or _field(entry, "mapped_protein_refs") or ()
        )
        if not mapped_protein_refs:
            continue
        peptide_keys = tuple(
            dict.fromkeys(
                key.upper()
                for key in (canonical, peptide, peptide_sequence)
                if key is not None and key.strip()
            )
        )
        if not peptide_keys:
            continue
        entries.append(
            _PeptideMappingEntry(
                peptide_keys=peptide_keys,
                protein_refs=mapped_protein_refs,
            )
        )
    return tuple(entries)


def _field(entry: object, name: str) -> Any:
    if isinstance(entry, dict):
        return entry.get(name)
    return getattr(entry, name, None)


def _string_field(entry: object, name: str) -> str | None:
    value = _field(entry, name)
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _normalize_protein_refs(raw_value: Any) -> tuple[str, ...]:
    if raw_value in (None, ""):
        return ()
    if isinstance(raw_value, str):
        values = raw_value.split(";")
    else:
        values = tuple(str(value) for value in raw_value)
    return tuple(dict.fromkeys(value.strip() for value in values if value.strip()))


def _resolve_protein_refs(
    *,
    psm: PsmRecord,
    peptide_mapping: tuple[_PeptideMappingEntry, ...],
    fasta_index: dict[str, str],
) -> tuple[str, ...]:
    if psm.protein_refs:
        refs = psm.protein_refs
    else:
        keys = {
            psm.canonical_peptide.upper(),
            (psm.peptide or "").upper(),
            (psm.peptide_sequence or "").upper(),
        }
        refs = ()
        for entry in peptide_mapping:
            if keys.intersection(entry.peptide_keys):
                refs = tuple(dict.fromkeys((*refs, *entry.protein_refs)))
    if not refs:
        return ()
    peptide_sequence = (psm.peptide_sequence or psm.peptide or "").upper()
    if not peptide_sequence:
        return refs
    validated_refs = tuple(
        protein_ref
        for protein_ref in refs
        if protein_ref in fasta_index and peptide_sequence in fasta_index[protein_ref]
    )
    return validated_refs or refs


def _find_spectrum(
    psm: PsmRecord,
    spectrum_index: dict[str, SpectrumModel],
) -> SpectrumModel:
    spectrum = spectrum_index.get(psm.spectrum_id)
    if spectrum is not None:
        return spectrum
    raise ValueError(f"no spectrum matched PSM spectrum_id {psm.spectrum_id!r}")


def _psm_id(psm: PsmRecord) -> str:
    if psm.provenance is not None:
        for key in ("psm_id", "psmid", "hit_id", "spectrum_match_id"):
            value = psm.provenance.original_identifiers.get(key)
            if value:
                return value
        source_file = psm.provenance.source_file
        source_row_numbers = psm.provenance.source_row_number
        if source_file or source_row_numbers:
            parts = [psm.spectrum_id, psm.canonical_peptide, f"z{psm.charge}"]
            if source_file:
                parts.append(source_file)
            if source_row_numbers:
                parts.append(source_row_numbers)
            return "|".join(parts)
    return f"{psm.spectrum_id}|{psm.canonical_peptide}|z{psm.charge}"


def _ppm_error(*, observed_mz: float, expected_mz: float) -> float:
    return ((observed_mz - expected_mz) / expected_mz) * 1_000_000.0


def _calculate_normalized_spectral_entropy(spectrum: SpectrumModel) -> float:
    if not spectrum.peaks:
        return 0.0
    total_intensity = sum(peak.intensity for peak in spectrum.peaks)
    if total_intensity <= 0.0:
        return 0.0
    entropy = 0.0
    for peak in spectrum.peaks:
        if peak.intensity <= 0.0:
            continue
        proportion = peak.intensity / total_intensity
        entropy -= proportion * log(proportion)
    maximum_entropy = log(len(spectrum.peaks))
    if maximum_entropy <= 0.0:
        return 0.0
    return entropy / maximum_entropy


def _top_peak_unmatched_fraction(
    *,
    spectrum: SpectrumModel,
    match_report,
    top_n: int = 10,
) -> float:
    if top_n <= 0 or not spectrum.peaks:
        return 0.0
    matched_peak_keys = {
        (match.observed_mz, match.observed_intensity) for match in match_report.matches
    }
    top_peaks = tuple(
        sorted(
            spectrum.peaks,
            key=lambda peak: (peak.intensity, -peak.mz),
            reverse=True,
        )[:top_n]
    )
    total_top_intensity = sum(peak.intensity for peak in top_peaks)
    if total_top_intensity <= 0.0:
        return 0.0
    unmatched_intensity = sum(
        peak.intensity
        for peak in top_peaks
        if (peak.mz, peak.intensity) not in matched_peak_keys
    )
    return unmatched_intensity / total_top_intensity


__all__ = (
    "PsmFeatureRow",
    "extract_psm_features",
    "render_psm_feature_tsv",
)
