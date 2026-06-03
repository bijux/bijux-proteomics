# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Score chimeric-spectrum evidence from peaks, isolation context, and candidates."""

from __future__ import annotations

from collections import defaultdict
import csv
from dataclasses import dataclass
from io import StringIO

from pydantic import ConfigDict, Field

from bijux_proteomics.chemistry import build_modified_peptide, calculate_peptide_mz
from bijux_proteomics.identification import PsmRecord
from bijux_proteomics.io.spectra import (
    SpectrumAnnotation,
    SpectrumModel,
    annotate_spectrum_fragments,
    calculate_precursor_mass_error,
)
from bijux_proteomics_foundation import JsonModel


class ChimericSpectrumCandidateAnnotation(JsonModel):
    """One candidate peptide annotation for one observed spectrum."""

    model_config = ConfigDict(extra="forbid")

    spectrum_id: str = Field(..., min_length=1)
    canonical_peptide: str = Field(..., min_length=1)
    charge: int = Field(..., ge=1)
    annotation_score: float | None = None
    protein_refs: tuple[str, ...] = Field(default_factory=tuple)


class ChimericSpectrumCompetingEvidenceEntry(JsonModel):
    """One competing candidate peptide that contributes chimeric evidence."""

    model_config = ConfigDict(extra="forbid")

    spectrum_id: str = Field(..., min_length=1)
    competing_peptide: str = Field(..., min_length=1)
    competing_charge: int = Field(..., ge=1)
    protein_refs: tuple[str, ...] = Field(default_factory=tuple)
    annotation_score: float | None = None
    theoretical_precursor_mz: float = Field(..., gt=0.0)
    precursor_delta_da: float
    precursor_delta_ppm: float
    within_isolation_window: bool = False
    explained_intensity_fraction: float = Field(..., ge=0.0, le=1.0)
    unique_explained_intensity_fraction: float = Field(..., ge=0.0, le=1.0)
    matched_peak_count: int = Field(..., ge=0)
    shared_peak_count: int = Field(..., ge=0)
    unique_peak_count: int = Field(..., ge=0)
    competition_score: float = Field(..., ge=0.0, le=1.0)
    concern_codes: tuple[str, ...] = Field(default_factory=tuple)


class ChimericSpectrumEntry(JsonModel):
    """One scored spectrum with primary and competing peptide evidence."""

    model_config = ConfigDict(extra="forbid")

    spectrum_id: str = Field(..., min_length=1)
    precursor_mz: float = Field(..., gt=0.0)
    isolation_window_target_mz: float = Field(..., gt=0.0)
    isolation_window_lower_mz: float = Field(..., gt=0.0)
    isolation_window_upper_mz: float = Field(..., gt=0.0)
    candidate_count: int = Field(..., ge=1)
    primary_peptide: str = Field(..., min_length=1)
    primary_charge: int = Field(..., ge=1)
    primary_annotation_score: float | None = None
    primary_explained_intensity_fraction: float = Field(..., ge=0.0, le=1.0)
    strongest_competing_peptide: str | None = None
    strongest_competing_score: float = Field(..., ge=0.0, le=1.0)
    chimeric_score: float = Field(..., ge=0.0, le=1.0)
    flagged_chimeric: bool = False
    concern_codes: tuple[str, ...] = Field(default_factory=tuple)


class ChimericSpectrumSummary(JsonModel):
    """Compact summary over one chimeric-spectrum scoring pass."""

    model_config = ConfigDict(extra="forbid")

    spectrum_count: int = Field(..., ge=0)
    scored_spectrum_count: int = Field(..., ge=0)
    flagged_chimeric_count: int = Field(..., ge=0)
    competing_evidence_entry_count: int = Field(..., ge=0)
    mean_chimeric_score: float = Field(..., ge=0.0, le=1.0)


class ChimericSpectrumReport(JsonModel):
    """Stable chimeric-spectrum scoring report over scored candidate annotations."""

    model_config = ConfigDict(extra="forbid")

    spectra: tuple[ChimericSpectrumEntry, ...] = Field(default_factory=tuple)
    competing_evidence: tuple[ChimericSpectrumCompetingEvidenceEntry, ...] = Field(
        default_factory=tuple
    )
    summary: ChimericSpectrumSummary
    note: str = Field(..., min_length=1)


@dataclass(frozen=True)
class _ScoredCandidate:
    annotation: ChimericSpectrumCandidateAnnotation
    spectrum_annotation: SpectrumAnnotation
    theoretical_precursor_mz: float
    precursor_delta_da: float
    precursor_delta_ppm: float
    within_isolation_window: bool
    matched_peak_keys: frozenset[tuple[float, float]]


def build_chimeric_candidate_annotations(
    records: tuple[PsmRecord, ...],
) -> tuple[ChimericSpectrumCandidateAnnotation, ...]:
    """Convert candidate PSM records into one stable annotation set per spectrum."""

    best_by_candidate: dict[
        tuple[str, str, int], ChimericSpectrumCandidateAnnotation
    ] = {}
    for record in records:
        key = (record.spectrum_id, record.canonical_peptide, record.charge)
        candidate = ChimericSpectrumCandidateAnnotation(
            spectrum_id=record.spectrum_id,
            canonical_peptide=record.canonical_peptide,
            charge=record.charge,
            annotation_score=record.score,
            protein_refs=record.protein_refs,
        )
        current = best_by_candidate.get(key)
        if current is None or _annotation_sort_key(candidate) > _annotation_sort_key(
            current
        ):
            best_by_candidate[key] = candidate
    return tuple(
        sorted(
            best_by_candidate.values(),
            key=lambda item: (
                item.spectrum_id,
                -_sortable_score(item.annotation_score),
                item.canonical_peptide,
                item.charge,
            ),
        )
    )


def score_chimeric_spectra(
    spectra: tuple[SpectrumModel, ...],
    candidate_annotations: tuple[ChimericSpectrumCandidateAnnotation, ...],
    *,
    tolerance_da: float | None = 0.02,
    tolerance_ppm: float | None = None,
    default_isolation_window_half_width_da: float = 1.0,
    chimeric_score_threshold: float = 0.45,
) -> ChimericSpectrumReport:
    """Score spectra for mixed peptide evidence instead of assigning manual labels."""

    if not spectra:
        raise ValueError("chimeric spectrum scoring requires at least one spectrum")
    if not candidate_annotations:
        raise ValueError(
            "chimeric spectrum scoring requires at least one candidate annotation"
        )
    if default_isolation_window_half_width_da <= 0.0:
        raise ValueError("default_isolation_window_half_width_da must be positive")
    if not 0.0 <= chimeric_score_threshold <= 1.0:
        raise ValueError("chimeric_score_threshold must be between 0 and 1")

    spectra_by_id = {spectrum.spectrum_id: spectrum for spectrum in spectra}
    grouped_candidates: dict[str, list[ChimericSpectrumCandidateAnnotation]] = (
        defaultdict(list)
    )
    for candidate in candidate_annotations:
        if candidate.spectrum_id in spectra_by_id:
            grouped_candidates[candidate.spectrum_id].append(candidate)

    spectrum_entries: list[ChimericSpectrumEntry] = []
    competing_entries: list[ChimericSpectrumCompetingEvidenceEntry] = []

    for spectrum_id in sorted(grouped_candidates):
        spectrum = spectra_by_id[spectrum_id]
        ranked_candidates = _score_candidates(
            spectrum,
            tuple(grouped_candidates[spectrum_id]),
            tolerance_da=tolerance_da,
            tolerance_ppm=tolerance_ppm,
            default_isolation_window_half_width_da=(
                default_isolation_window_half_width_da
            ),
        )
        if not ranked_candidates:
            continue
        primary = ranked_candidates[0]
        strongest_competitor: ChimericSpectrumCompetingEvidenceEntry | None = None
        candidate_competing_entries: list[ChimericSpectrumCompetingEvidenceEntry] = []
        for competitor in ranked_candidates[1:]:
            competing_entry = _build_competing_entry(
                primary,
                competitor,
                default_isolation_window_half_width_da=(
                    default_isolation_window_half_width_da
                ),
            )
            candidate_competing_entries.append(competing_entry)
            if strongest_competitor is None or (
                competing_entry.competition_score,
                competing_entry.explained_intensity_fraction,
                competing_entry.competing_peptide,
            ) > (
                strongest_competitor.competition_score,
                strongest_competitor.explained_intensity_fraction,
                strongest_competitor.competing_peptide,
            ):
                strongest_competitor = competing_entry

        competing_entries.extend(candidate_competing_entries)
        isolation_target_mz, lower_bound_mz, upper_bound_mz = _isolation_window_bounds(
            spectrum, default_isolation_window_half_width_da
        )
        chimeric_score = (
            0.0
            if strongest_competitor is None
            else strongest_competitor.competition_score
        )
        concern_codes = (
            ()
            if strongest_competitor is None
            else tuple(
                sorted(
                    {
                        "competing_peptide_signal",
                        *strongest_competitor.concern_codes,
                    }
                )
            )
        )
        spectrum_entries.append(
            ChimericSpectrumEntry(
                spectrum_id=spectrum.spectrum_id,
                precursor_mz=spectrum.precursor_mz,
                isolation_window_target_mz=round(isolation_target_mz, 6),
                isolation_window_lower_mz=round(lower_bound_mz, 6),
                isolation_window_upper_mz=round(upper_bound_mz, 6),
                candidate_count=len(ranked_candidates),
                primary_peptide=primary.annotation.canonical_peptide,
                primary_charge=primary.annotation.charge,
                primary_annotation_score=primary.annotation.annotation_score,
                primary_explained_intensity_fraction=round(
                    primary.spectrum_annotation.explained_intensity_fraction,
                    4,
                ),
                strongest_competing_peptide=(
                    None
                    if strongest_competitor is None
                    else strongest_competitor.competing_peptide
                ),
                strongest_competing_score=round(chimeric_score, 4),
                chimeric_score=round(chimeric_score, 4),
                flagged_chimeric=chimeric_score >= chimeric_score_threshold,
                concern_codes=concern_codes,
            )
        )

    ordered_spectra = tuple(
        sorted(
            spectrum_entries,
            key=lambda item: (-item.chimeric_score, item.spectrum_id),
        )
    )
    ordered_competing = tuple(
        sorted(
            competing_entries,
            key=lambda item: (
                -item.competition_score,
                item.spectrum_id,
                item.competing_peptide,
            ),
        )
    )
    mean_chimeric_score = (
        round(
            sum(entry.chimeric_score for entry in ordered_spectra)
            / len(ordered_spectra),
            4,
        )
        if ordered_spectra
        else 0.0
    )
    return ChimericSpectrumReport(
        spectra=ordered_spectra,
        competing_evidence=ordered_competing,
        summary=ChimericSpectrumSummary(
            spectrum_count=len(spectra),
            scored_spectrum_count=len(ordered_spectra),
            flagged_chimeric_count=sum(
                1 for entry in ordered_spectra if entry.flagged_chimeric
            ),
            competing_evidence_entry_count=len(ordered_competing),
            mean_chimeric_score=mean_chimeric_score,
        ),
        note=(
            "chimeric spectrum scoring uses matched fragment evidence, precursor isolation context, and governed candidate peptide annotations so clean spectra and mixed spectra separate by observed competing signal rather than manual status"
        ),
    )


def score_chimeric_spectra_from_psms(
    spectra: tuple[SpectrumModel, ...],
    records: tuple[PsmRecord, ...],
    *,
    tolerance_da: float | None = 0.02,
    tolerance_ppm: float | None = None,
    default_isolation_window_half_width_da: float = 1.0,
    chimeric_score_threshold: float = 0.45,
) -> ChimericSpectrumReport:
    """Score spectra for chimeric evidence from canonical PSM candidate annotations."""

    return score_chimeric_spectra(
        spectra,
        build_chimeric_candidate_annotations(records),
        tolerance_da=tolerance_da,
        tolerance_ppm=tolerance_ppm,
        default_isolation_window_half_width_da=default_isolation_window_half_width_da,
        chimeric_score_threshold=chimeric_score_threshold,
    )


def render_chimeric_spectrum_spectra_tsv(report: ChimericSpectrumReport) -> str:
    """Render spectrum-level chimeric scoring rows as stable TSV."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "spectrum_id",
            "precursor_mz",
            "isolation_window_target_mz",
            "isolation_window_lower_mz",
            "isolation_window_upper_mz",
            "candidate_count",
            "primary_peptide",
            "primary_charge",
            "primary_annotation_score",
            "primary_explained_intensity_fraction",
            "strongest_competing_peptide",
            "strongest_competing_score",
            "chimeric_score",
            "flagged_chimeric",
            "concern_codes",
        )
    )
    for entry in report.spectra:
        writer.writerow(
            (
                entry.spectrum_id,
                f"{entry.precursor_mz:.6f}",
                f"{entry.isolation_window_target_mz:.6f}",
                f"{entry.isolation_window_lower_mz:.6f}",
                f"{entry.isolation_window_upper_mz:.6f}",
                entry.candidate_count,
                entry.primary_peptide,
                entry.primary_charge,
                ""
                if entry.primary_annotation_score is None
                else f"{entry.primary_annotation_score:.4f}",
                f"{entry.primary_explained_intensity_fraction:.4f}",
                ""
                if entry.strongest_competing_peptide is None
                else entry.strongest_competing_peptide,
                f"{entry.strongest_competing_score:.4f}",
                f"{entry.chimeric_score:.4f}",
                str(entry.flagged_chimeric).lower(),
                "|".join(entry.concern_codes),
            )
        )
    return buffer.getvalue()


def render_chimeric_spectrum_competing_evidence_tsv(
    report: ChimericSpectrumReport,
) -> str:
    """Render competing peptide evidence rows for chimeric review."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "spectrum_id",
            "competing_peptide",
            "competing_charge",
            "protein_refs",
            "annotation_score",
            "theoretical_precursor_mz",
            "precursor_delta_da",
            "precursor_delta_ppm",
            "within_isolation_window",
            "explained_intensity_fraction",
            "unique_explained_intensity_fraction",
            "matched_peak_count",
            "shared_peak_count",
            "unique_peak_count",
            "competition_score",
            "concern_codes",
        )
    )
    for entry in report.competing_evidence:
        writer.writerow(
            (
                entry.spectrum_id,
                entry.competing_peptide,
                entry.competing_charge,
                ";".join(entry.protein_refs),
                ""
                if entry.annotation_score is None
                else f"{entry.annotation_score:.4f}",
                f"{entry.theoretical_precursor_mz:.6f}",
                f"{entry.precursor_delta_da:.6f}",
                f"{entry.precursor_delta_ppm:.4f}",
                str(entry.within_isolation_window).lower(),
                f"{entry.explained_intensity_fraction:.4f}",
                f"{entry.unique_explained_intensity_fraction:.4f}",
                entry.matched_peak_count,
                entry.shared_peak_count,
                entry.unique_peak_count,
                f"{entry.competition_score:.4f}",
                "|".join(entry.concern_codes),
            )
        )
    return buffer.getvalue()


def _score_candidates(
    spectrum: SpectrumModel,
    candidates: tuple[ChimericSpectrumCandidateAnnotation, ...],
    *,
    tolerance_da: float | None,
    tolerance_ppm: float | None,
    default_isolation_window_half_width_da: float,
) -> tuple[_ScoredCandidate, ...]:
    scored: list[_ScoredCandidate] = []
    isolation_target_mz, lower_bound_mz, upper_bound_mz = _isolation_window_bounds(
        spectrum,
        default_isolation_window_half_width_da,
    )
    for candidate in candidates:
        parsed = build_modified_peptide(candidate.canonical_peptide)
        theoretical_precursor_mz = calculate_peptide_mz(parsed, charge=candidate.charge)
        precursor_error = calculate_precursor_mass_error(
            observed_mz=isolation_target_mz,
            theoretical_mz=theoretical_precursor_mz,
        )
        annotation = annotate_spectrum_fragments(
            spectrum,
            peptide=candidate.canonical_peptide,
            tolerance_da=tolerance_da,
            tolerance_ppm=tolerance_ppm,
            include_neutral_losses=False,
        )
        scored.append(
            _ScoredCandidate(
                annotation=candidate,
                spectrum_annotation=annotation,
                theoretical_precursor_mz=theoretical_precursor_mz,
                precursor_delta_da=precursor_error.delta_da,
                precursor_delta_ppm=precursor_error.delta_ppm,
                within_isolation_window=(
                    lower_bound_mz <= theoretical_precursor_mz <= upper_bound_mz
                ),
                matched_peak_keys=frozenset(
                    (match.observed_mz, match.observed_intensity)
                    for match in annotation.matches
                ),
            )
        )
    return tuple(
        sorted(
            scored,
            key=lambda item: (
                -_sortable_score(item.annotation.annotation_score),
                -item.spectrum_annotation.explained_intensity_fraction,
                -item.spectrum_annotation.matched_peak_count,
                abs(item.precursor_delta_da),
                item.annotation.canonical_peptide,
                item.annotation.charge,
            ),
        )
    )


def _build_competing_entry(
    primary: _ScoredCandidate,
    competitor: _ScoredCandidate,
    *,
    default_isolation_window_half_width_da: float,
) -> ChimericSpectrumCompetingEvidenceEntry:
    shared_peak_keys = primary.matched_peak_keys & competitor.matched_peak_keys
    unique_peak_keys = competitor.matched_peak_keys - primary.matched_peak_keys
    total_observed_intensity = competitor.spectrum_annotation.total_observed_intensity
    unique_explained_intensity = sum(intensity for _mz, intensity in unique_peak_keys)
    unique_explained_intensity_fraction = (
        0.0
        if total_observed_intensity <= 0.0
        else unique_explained_intensity / total_observed_intensity
    )
    precursor_fit_score = _precursor_fit_score(
        precursor_delta_da=competitor.precursor_delta_da,
        within_isolation_window=competitor.within_isolation_window,
        default_isolation_window_half_width_da=default_isolation_window_half_width_da,
    )
    explained_component = min(
        1.0,
        competitor.spectrum_annotation.explained_intensity_fraction / 0.35,
    )
    unique_component = min(1.0, unique_explained_intensity_fraction / 0.15)
    match_component = min(1.0, competitor.spectrum_annotation.matched_peak_count / 4.0)
    competition_score = round(
        (0.35 * explained_component)
        + (0.40 * unique_component)
        + (0.15 * precursor_fit_score)
        + (0.10 * match_component),
        4,
    )
    concern_codes = set()
    if competitor.within_isolation_window:
        concern_codes.add("coisolated_precursor_candidate")
    if unique_explained_intensity_fraction > 0.0:
        concern_codes.add("distinct_fragment_support")
    if competitor.spectrum_annotation.explained_intensity_fraction >= 0.2:
        concern_codes.add("substantial_competing_intensity")
    return ChimericSpectrumCompetingEvidenceEntry(
        spectrum_id=primary.annotation.spectrum_id,
        competing_peptide=competitor.annotation.canonical_peptide,
        competing_charge=competitor.annotation.charge,
        protein_refs=competitor.annotation.protein_refs,
        annotation_score=competitor.annotation.annotation_score,
        theoretical_precursor_mz=round(competitor.theoretical_precursor_mz, 6),
        precursor_delta_da=round(competitor.precursor_delta_da, 6),
        precursor_delta_ppm=round(competitor.precursor_delta_ppm, 4),
        within_isolation_window=competitor.within_isolation_window,
        explained_intensity_fraction=round(
            competitor.spectrum_annotation.explained_intensity_fraction,
            4,
        ),
        unique_explained_intensity_fraction=round(
            unique_explained_intensity_fraction,
            4,
        ),
        matched_peak_count=competitor.spectrum_annotation.matched_peak_count,
        shared_peak_count=len(shared_peak_keys),
        unique_peak_count=len(unique_peak_keys),
        competition_score=competition_score,
        concern_codes=tuple(sorted(concern_codes)),
    )


def _annotation_sort_key(
    candidate: ChimericSpectrumCandidateAnnotation,
) -> tuple[float, str, int]:
    return (
        _sortable_score(candidate.annotation_score),
        candidate.canonical_peptide,
        -candidate.charge,
    )


def _sortable_score(value: float | None) -> float:
    return float("-inf") if value is None else value


def _isolation_window_bounds(
    spectrum: SpectrumModel,
    default_isolation_window_half_width_da: float,
) -> tuple[float, float, float]:
    target_mz = spectrum.isolation_window_target_mz or spectrum.precursor_mz
    lower_offset = (
        default_isolation_window_half_width_da
        if spectrum.isolation_window_lower_offset is None
        else spectrum.isolation_window_lower_offset
    )
    upper_offset = (
        default_isolation_window_half_width_da
        if spectrum.isolation_window_upper_offset is None
        else spectrum.isolation_window_upper_offset
    )
    return (target_mz, target_mz - lower_offset, target_mz + upper_offset)


def _precursor_fit_score(
    *,
    precursor_delta_da: float,
    within_isolation_window: bool,
    default_isolation_window_half_width_da: float,
) -> float:
    if within_isolation_window:
        return 1.0
    overflow = abs(precursor_delta_da) - default_isolation_window_half_width_da
    if overflow >= default_isolation_window_half_width_da:
        return 0.0
    return max(0.0, 1.0 - (overflow / default_isolation_window_half_width_da))


__all__ = [
    "ChimericSpectrumCandidateAnnotation",
    "ChimericSpectrumCompetingEvidenceEntry",
    "ChimericSpectrumEntry",
    "ChimericSpectrumReport",
    "ChimericSpectrumSummary",
    "build_chimeric_candidate_annotations",
    "render_chimeric_spectrum_competing_evidence_tsv",
    "render_chimeric_spectrum_spectra_tsv",
    "score_chimeric_spectra",
    "score_chimeric_spectra_from_psms",
]
