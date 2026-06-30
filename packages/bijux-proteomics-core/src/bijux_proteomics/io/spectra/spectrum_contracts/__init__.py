# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Spectrum, MGF, and fragment-annotation contracts."""

from __future__ import annotations

import csv
import io
import json
from pathlib import Path

from bijux_proteomics.chemistry.fragments import (
    FragmentIon,
    calculate_fragment_ions,
)
from bijux_proteomics.chemistry.modifications import (
    ParsedModifiedPeptide,
    canonicalize_modified_peptide,
)
from bijux_proteomics.io.spectra.spectrum_peak_matching import (
    build_spectrum_peak_match_report,
)
from bijux_proteomics_foundation import DocumentSchema
from bijux_proteomics.io.spectra.spectrum_contracts.collection import (
    build_spectrum_collection_summary,
    build_spectrum_lookup_index,
    build_spectrum_provenance_manifest,
    build_spectrum_summary_table_report,
    iter_mgf_spectra,
    lookup_spectra,
    normalize_spectrum_scan_key,
    parse_mgf,
    render_mgf,
    render_spectrum_distribution_tsv,
    render_spectrum_similarity_tsv,
    render_spectrum_summary_tsv,
)
from bijux_proteomics.io.spectra.spectrum_contracts.models import (
    AnnotatedSpectrumBundle,
    MgfParseReport,
    PeakNormalizationPolicy,
    PrecursorIsotopeOffsetAdvisory,
    PrecursorIsotopeOffsetCandidate,
    PrecursorMassError,
    PrecursorMassErrorDistributionRow,
    PrecursorMassErrorObservation,
    PrecursorMassErrorQuery,
    PrecursorMassErrorReport,
    RejectedSpectrumBlock,
    SpectralSimilarityMethod,
    SpectralSimilarityScore,
    SpectrumAnnotation,
    SpectrumAnnotationAmbiguityKind,
    SpectrumAnnotationAmbiguityWarning,
    SpectrumAnnotationMatch,
    SpectrumAnnotationParameters,
    SpectrumAnnotationToleranceUnit,
    SpectrumAnnotationUnmatchedPeak,
    SpectrumCollectionSummary,
    SpectrumDistributionRow,
    SpectrumFilterReport,
    SpectrumLibrarySimilarityMatch,
    SpectrumLibrarySimilarityReport,
    SpectrumLookupIndex,
    SpectrumMetrics,
    SpectrumModel,
    SpectrumPeak,
    SpectrumPlotPayload,
    SpectrumPlotPeak,
    SpectrumProvenanceManifest,
    SpectrumSimilarityClassification,
    SpectrumSimilarityComparisonReport,
    SpectrumSimilarityMatchingMode,
    SpectrumSimilarityMode,
    SpectrumSimilarityParameters,
    SpectrumSummaryTableReport,
    SpectrumValidationIssue,
)
from bijux_proteomics.io.spectra.spectrum_contracts.processing import (
    build_precursor_mass_error_report,
    build_spectrum_metrics,
    calculate_precursor_mass_error,
    detect_precursor_isotope_offset_advisory,
    filter_spectrum_peaks,
    normalize_spectrum_peaks,
    render_precursor_mass_error_distribution_tsv,
    render_precursor_mass_error_observations_tsv,
    render_precursor_mass_error_summary_tsv,
)


def calculate_spectral_similarity(
    reference_spectrum: SpectrumModel,
    query_spectrum: SpectrumModel,
    *,
    tolerance_da: float | None = None,
    bin_width_da: float | None = None,
    method: SpectralSimilarityMethod = SpectralSimilarityMethod.COSINE,
    mode: SpectrumSimilarityMode = SpectrumSimilarityMode.RAW,
    top_n: int | None = None,
) -> SpectralSimilarityScore:
    """Calculate a basic matched-peak spectral similarity score."""
    matching_mode, resolved_tolerance_da, resolved_bin_width_da = (
        _resolve_similarity_matching_strategy(
            tolerance_da=tolerance_da,
            bin_width_da=bin_width_da,
        )
    )
    reference_spectrum = _prepare_similarity_spectrum(
        reference_spectrum,
        mode=mode,
        top_n=top_n,
    )
    query_spectrum = _prepare_similarity_spectrum(
        query_spectrum,
        mode=mode,
        top_n=top_n,
    )

    if matching_mode is SpectrumSimilarityMatchingMode.BINNED:
        matched_reference, matched_query, reference_total, query_total = (
            _match_binned_similarity_vectors(
                reference_spectrum,
                query_spectrum,
                bin_width_da=resolved_bin_width_da or 1.0,
            )
        )
    else:
        matched_reference, matched_query, reference_total, query_total = (
            _match_tolerance_similarity_vectors(
                reference_spectrum,
                query_spectrum,
                tolerance_da=resolved_tolerance_da or 0.02,
            )
        )

    dot_product = sum(
        reference * query
        for reference, query in zip(matched_reference, matched_query, strict=True)
    )
    if method is SpectralSimilarityMethod.DOT_PRODUCT:
        score = dot_product
    else:
        reference_norm = sum(value * value for value in reference_total) ** 0.5
        query_norm = sum(value * value for value in query_total) ** 0.5
        score = (
            0.0
            if reference_norm == 0.0 or query_norm == 0.0
            else dot_product / (reference_norm * query_norm)
        )
    matched_reference_intensity = sum(matched_reference)
    matched_query_intensity = sum(matched_query)
    total_reference_intensity = sum(reference_total)
    total_query_intensity = sum(query_total)
    return SpectralSimilarityScore(
        method=method,
        mode=mode,
        matching_mode=matching_mode,
        tolerance_da=resolved_tolerance_da,
        bin_width_da=resolved_bin_width_da,
        score=score,
        matched_peak_count=len(matched_reference),
        reference_peak_count=len(reference_spectrum.peaks),
        query_peak_count=len(query_spectrum.peaks),
        reference_explained_intensity_fraction=(
            0.0
            if total_reference_intensity == 0.0
            else matched_reference_intensity / total_reference_intensity
        ),
        query_explained_intensity_fraction=(
            0.0
            if total_query_intensity == 0.0
            else matched_query_intensity / total_query_intensity
        ),
    )


def build_spectrum_similarity_comparison_report(
    reference_spectrum: SpectrumModel,
    query_spectrum: SpectrumModel,
    *,
    tolerance_da: float | None = None,
    bin_width_da: float | None = None,
    method: SpectralSimilarityMethod = SpectralSimilarityMethod.COSINE,
    mode: SpectrumSimilarityMode = SpectrumSimilarityMode.RAW,
    top_n: int | None = None,
) -> SpectrumSimilarityComparisonReport:
    """Build a reviewer-facing comparison between two spectra."""
    score = calculate_spectral_similarity(
        reference_spectrum,
        query_spectrum,
        tolerance_da=tolerance_da,
        bin_width_da=bin_width_da,
        method=method,
        mode=mode,
        top_n=top_n,
    )
    parameters = SpectrumSimilarityParameters(
        method=score.method,
        mode=score.mode,
        matching_mode=score.matching_mode,
        tolerance_da=score.tolerance_da,
        bin_width_da=score.bin_width_da,
        top_n=top_n,
    )
    classification = _classify_spectral_similarity(score)
    report = SpectrumSimilarityComparisonReport(
        document_schema=DocumentSchema(
            created_by="bijux-proteomics-core",
            document_kind="spectrum_similarity_comparison",
            package_name="bijux-proteomics-core",
            status="generated",
        ),
        parameters=parameters,
        reference_spectrum_id=reference_spectrum.spectrum_id,
        query_spectrum_id=query_spectrum.spectrum_id,
        classification=classification,
        score=score.score,
        matched_peak_count=score.matched_peak_count,
        reference_peak_count=score.reference_peak_count,
        query_peak_count=score.query_peak_count,
        reference_explained_intensity_fraction=(
            score.reference_explained_intensity_fraction
        ),
        query_explained_intensity_fraction=score.query_explained_intensity_fraction,
        interpretation=_describe_spectral_similarity(classification, score),
    )
    payload = report.to_dict()
    return report.model_copy(
        update={
            "document_schema": report.document_schema.with_content_hash(payload),
        }
    )


def build_spectrum_library_similarity_report(
    query_spectrum: SpectrumModel,
    reference_spectra: tuple[SpectrumModel, ...],
    *,
    tolerance_da: float | None = None,
    bin_width_da: float | None = None,
    method: SpectralSimilarityMethod = SpectralSimilarityMethod.COSINE,
    mode: SpectrumSimilarityMode = SpectrumSimilarityMode.RAW,
    top_n: int | None = None,
    max_matches: int | None = None,
) -> SpectrumLibrarySimilarityReport:
    """Rank one query spectrum against a reference collection."""
    scores = [
        (
            reference,
            calculate_spectral_similarity(
                reference,
                query_spectrum,
                tolerance_da=tolerance_da,
                bin_width_da=bin_width_da,
                method=method,
                mode=mode,
                top_n=top_n,
            ),
        )
        for reference in reference_spectra
    ]
    ranked = sorted(
        scores,
        key=lambda item: (
            -item[1].score,
            -item[1].matched_peak_count,
            item[0].spectrum_id,
        ),
    )
    if max_matches is not None:
        ranked = ranked[:max_matches]

    matches: list[SpectrumLibrarySimilarityMatch] = []
    duplicate_like_count = 0
    similar_count = 0
    for rank, (reference, score) in enumerate(ranked, start=1):
        classification = _classify_spectral_similarity(score)
        if classification is SpectrumSimilarityClassification.DUPLICATE_LIKE:
            duplicate_like_count += 1
        if classification in {
            SpectrumSimilarityClassification.DUPLICATE_LIKE,
            SpectrumSimilarityClassification.SIMILAR,
        }:
            similar_count += 1
        matches.append(
            SpectrumLibrarySimilarityMatch(
                rank=rank,
                reference_spectrum_id=reference.spectrum_id,
                classification=classification,
                score=score.score,
                matched_peak_count=score.matched_peak_count,
                reference_peak_count=score.reference_peak_count,
                query_peak_count=score.query_peak_count,
                reference_explained_intensity_fraction=(
                    score.reference_explained_intensity_fraction
                ),
                query_explained_intensity_fraction=(
                    score.query_explained_intensity_fraction
                ),
            )
        )

    parameters = SpectrumSimilarityParameters(
        method=method,
        mode=mode,
        matching_mode=(
            ranked[0][1].matching_mode
            if ranked
            else SpectrumSimilarityMatchingMode.TOLERANCE
        ),
        tolerance_da=ranked[0][1].tolerance_da if ranked else tolerance_da,
        bin_width_da=ranked[0][1].bin_width_da if ranked else bin_width_da,
        top_n=top_n,
    )
    report = SpectrumLibrarySimilarityReport(
        document_schema=DocumentSchema(
            created_by="bijux-proteomics-core",
            document_kind="spectrum_library_similarity_report",
            package_name="bijux-proteomics-core",
            status="generated",
        ),
        parameters=parameters,
        query_spectrum_id=query_spectrum.spectrum_id,
        candidate_count=len(reference_spectra),
        duplicate_like_match_count=duplicate_like_count,
        similar_match_count=similar_count,
        matches=tuple(matches),
    )
    payload = report.to_dict()
    return report.model_copy(
        update={
            "document_schema": report.document_schema.with_content_hash(payload),
        }
    )


def _prepare_similarity_spectrum(
    spectrum: SpectrumModel,
    *,
    mode: SpectrumSimilarityMode,
    top_n: int | None,
) -> SpectrumModel:
    if mode is SpectrumSimilarityMode.RAW:
        return normalize_spectrum_peaks(
            spectrum,
            policy=PeakNormalizationPolicy(
                merge_tolerance_da=0.0,
                drop_zero_intensity=False,
                scale_to_base_peak=False,
            ),
        )
    if mode is SpectrumSimilarityMode.NORMALIZED:
        return normalize_spectrum_peaks(
            spectrum,
            policy=PeakNormalizationPolicy(
                merge_tolerance_da=0.0,
                drop_zero_intensity=False,
                scale_to_base_peak=True,
            ),
        )
    if mode is SpectrumSimilarityMode.TOP_N:
        normalized = normalize_spectrum_peaks(
            spectrum,
            policy=PeakNormalizationPolicy(
                merge_tolerance_da=0.0,
                drop_zero_intensity=False,
                scale_to_base_peak=True,
            ),
        )
        return filter_spectrum_peaks(
            normalized,
            top_n=top_n if top_n is not None else 50,
        ).spectrum
    normalized = normalize_spectrum_peaks(
        spectrum,
        policy=PeakNormalizationPolicy(
            merge_tolerance_da=0.0,
            drop_zero_intensity=False,
            scale_to_base_peak=True,
        ),
    )
    return normalized.model_copy(
        update={
            "peaks": tuple(
                SpectrumPeak(mz=peak.mz, intensity=peak.intensity**0.5)
                for peak in normalized.peaks
            )
        }
    )


def _resolve_similarity_matching_strategy(
    *,
    tolerance_da: float | None,
    bin_width_da: float | None,
) -> tuple[SpectrumSimilarityMatchingMode, float | None, float | None]:
    if tolerance_da is not None and bin_width_da is not None:
        raise ValueError("choose either tolerance_da or bin_width_da, not both")
    if bin_width_da is not None:
        if bin_width_da <= 0:
            raise ValueError("bin_width_da must be greater than zero")
        return SpectrumSimilarityMatchingMode.BINNED, None, bin_width_da
    if tolerance_da is None:
        tolerance_da = 0.02
    if tolerance_da <= 0:
        raise ValueError("tolerance_da must be greater than zero")
    return SpectrumSimilarityMatchingMode.TOLERANCE, tolerance_da, None


def _match_tolerance_similarity_vectors(
    reference_spectrum: SpectrumModel,
    query_spectrum: SpectrumModel,
    *,
    tolerance_da: float,
) -> tuple[list[float], list[float], list[float], list[float]]:
    matched_reference: list[float] = []
    matched_query: list[float] = []
    used_reference_indices: set[int] = set()
    for query_peak in sorted(query_spectrum.peaks, key=lambda peak: peak.mz):
        best_index: int | None = None
        best_error: float | None = None
        for index, reference_peak in enumerate(reference_spectrum.peaks):
            if index in used_reference_indices:
                continue
            error = query_peak.mz - reference_peak.mz
            if abs(error) > tolerance_da:
                continue
            if best_index is None or best_error is None or abs(error) < abs(best_error):
                best_index = index
                best_error = error
        if best_index is None:
            continue
        used_reference_indices.add(best_index)
        matched_reference.append(reference_spectrum.peaks[best_index].intensity)
        matched_query.append(query_peak.intensity)
    return (
        matched_reference,
        matched_query,
        [peak.intensity for peak in reference_spectrum.peaks],
        [peak.intensity for peak in query_spectrum.peaks],
    )


def _match_binned_similarity_vectors(
    reference_spectrum: SpectrumModel,
    query_spectrum: SpectrumModel,
    *,
    bin_width_da: float,
) -> tuple[list[float], list[float], list[float], list[float]]:
    reference_bins = _bin_similarity_peaks(
        reference_spectrum, bin_width_da=bin_width_da
    )
    query_bins = _bin_similarity_peaks(query_spectrum, bin_width_da=bin_width_da)
    shared_bins = tuple(sorted(set(reference_bins) & set(query_bins)))
    matched_reference = [reference_bins[index] for index in shared_bins]
    matched_query = [query_bins[index] for index in shared_bins]
    return (
        matched_reference,
        matched_query,
        list(reference_bins.values()),
        list(query_bins.values()),
    )


def _bin_similarity_peaks(
    spectrum: SpectrumModel,
    *,
    bin_width_da: float,
) -> dict[int, float]:
    bins: dict[int, float] = {}
    for peak in spectrum.peaks:
        index = int(round(peak.mz / bin_width_da))
        bins[index] = bins.get(index, 0.0) + peak.intensity
    return dict(sorted(bins.items()))


def _classify_spectral_similarity(
    score: SpectralSimilarityScore,
) -> SpectrumSimilarityClassification:
    if score.reference_peak_count == 0 or score.query_peak_count == 0:
        return SpectrumSimilarityClassification.INSUFFICIENT_SIGNAL
    if score.matched_peak_count == 0:
        return SpectrumSimilarityClassification.DISTINCT
    if (
        score.score >= 0.98
        and min(
            score.reference_explained_intensity_fraction,
            score.query_explained_intensity_fraction,
        )
        >= 0.9
    ):
        return SpectrumSimilarityClassification.DUPLICATE_LIKE
    if score.score >= 0.7 and score.matched_peak_count >= 2:
        return SpectrumSimilarityClassification.SIMILAR
    return SpectrumSimilarityClassification.DISTINCT


def _describe_spectral_similarity(
    classification: SpectrumSimilarityClassification,
    score: SpectralSimilarityScore,
) -> str:
    if classification is SpectrumSimilarityClassification.INSUFFICIENT_SIGNAL:
        return "One or both spectra have no usable peaks after preprocessing."
    if classification is SpectrumSimilarityClassification.DUPLICATE_LIKE:
        return (
            "The spectra are duplicate-like under the selected preprocessing and "
            "matching policy."
        )
    if classification is SpectrumSimilarityClassification.SIMILAR:
        return (
            "The spectra share substantial fragment evidence and are suitable for "
            "similar-spectrum or library-style review."
        )
    if score.matched_peak_count == 0:
        return "No shared peaks were matched under the selected comparison policy."
    return "The spectra share limited evidence and should be treated as distinct."


def _canonical_peptide_text(peptide: str | ParsedModifiedPeptide) -> str:
    if isinstance(peptide, ParsedModifiedPeptide):
        return canonicalize_modified_peptide(peptide)
    return canonicalize_modified_peptide(peptide)


def _fragment_label(fragment: FragmentIon) -> str:
    return f"{fragment.series.value}{fragment.ordinal}+{fragment.charge}"


def _resolve_annotation_tolerance(
    *,
    tolerance_da: float | None,
    tolerance_ppm: float | None,
) -> tuple[SpectrumAnnotationToleranceUnit, float | None, float | None]:
    if tolerance_da is not None and tolerance_ppm is not None:
        raise ValueError("choose either tolerance_da or tolerance_ppm, not both")
    if tolerance_ppm is not None:
        if tolerance_ppm <= 0:
            raise ValueError("tolerance_ppm must be greater than zero")
        return SpectrumAnnotationToleranceUnit.PPM, None, tolerance_ppm
    if tolerance_da is None or tolerance_da <= 0:
        raise ValueError("tolerance_da must be greater than zero")
    return SpectrumAnnotationToleranceUnit.DA, tolerance_da, None


def _matches_fragment_tolerance(
    *,
    observed_mz: float,
    fragment_mz: float,
    tolerance_unit: SpectrumAnnotationToleranceUnit,
    tolerance_da: float | None,
    tolerance_ppm: float | None,
) -> bool:
    error_da = observed_mz - fragment_mz
    if tolerance_unit is SpectrumAnnotationToleranceUnit.PPM:
        if tolerance_ppm is None:
            raise ValueError("tolerance_ppm must be resolved for ppm annotation")
        return abs((error_da / fragment_mz) * 1_000_000.0) <= tolerance_ppm
    if tolerance_da is None:
        raise ValueError("tolerance_da must be resolved for dalton annotation")
    return abs(error_da) <= tolerance_da


def annotate_spectrum_fragments(
    spectrum: SpectrumModel,
    *,
    peptide: str | ParsedModifiedPeptide,
    tolerance_da: float | None = 0.5,
    tolerance_ppm: float | None = None,
    include_neutral_losses: bool = True,
) -> SpectrumAnnotation:
    """Match theoretical fragments against observed peaks within one tolerance."""
    canonical = _canonical_peptide_text(peptide)
    peak_match_report = build_spectrum_peak_match_report(
        spectrum,
        peptide=peptide,
        tolerance_da=tolerance_da,
        tolerance_ppm=tolerance_ppm,
        include_neutral_losses=include_neutral_losses,
    )
    schema = DocumentSchema(
        created_by="bijux-proteomics-core",
        document_kind="spectrum_annotation",
        package_name="bijux-proteomics-core",
        status="generated",
    )
    annotation = SpectrumAnnotation(
        document_schema=schema,
        spectrum_id=spectrum.spectrum_id,
        peptide=canonical,
        precursor_mz=spectrum.precursor_mz,
        precursor_charge=spectrum.precursor_charge,
        tolerance_unit=SpectrumAnnotationToleranceUnit(
            peak_match_report.tolerance_mode.value
        ),
        tolerance_da=peak_match_report.tolerance_da,
        tolerance_ppm=peak_match_report.tolerance_ppm,
        matches=tuple(
            SpectrumAnnotationMatch(
                fragment=match.fragment,
                fragment_label=match.fragment_label,
                observed_mz=match.observed_mz,
                observed_intensity=match.observed_intensity,
                mass_error_da=match.mass_error_da,
                mass_error_ppm=match.mass_error_ppm,
            )
            for match in peak_match_report.matches
        ),
        unmatched_peaks=tuple(
            SpectrumAnnotationUnmatchedPeak(
                mz=peak.mz,
                intensity=peak.intensity,
            )
            for peak in peak_match_report.unmatched_peaks
        ),
        ambiguity_warnings=tuple(
            SpectrumAnnotationAmbiguityWarning(
                kind=SpectrumAnnotationAmbiguityKind(warning.kind.value),
                fragment_labels=warning.fragment_labels,
                peak_mzs=warning.peak_mzs,
                tolerance_unit=SpectrumAnnotationToleranceUnit(
                    warning.tolerance_mode.value
                ),
                tolerance_da=warning.tolerance_da,
                tolerance_ppm=warning.tolerance_ppm,
                note=warning.note,
            )
            for warning in peak_match_report.ambiguity_warnings
        ),
        matched_peak_count=peak_match_report.matched_peak_count,
        explained_intensity=peak_match_report.explained_intensity,
        total_observed_intensity=peak_match_report.total_observed_intensity,
        explained_intensity_fraction=peak_match_report.explained_intensity_fraction,
        unmatched_peak_count=peak_match_report.unmatched_peak_count,
    )
    payload = annotation.to_dict()
    return annotation.model_copy(
        update={
            "document_schema": annotation.document_schema.with_content_hash(payload)
        }
    )


def export_spectrum_annotation_tsv(annotation: SpectrumAnnotation, path: Path) -> None:
    """Write a stable TSV table for one spectrum annotation."""
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, delimiter="\t")
        writer.writerow(
            [
                "spectrum_id",
                "peptide",
                "tolerance_mode",
                "series",
                "ordinal",
                "fragment_charge",
                "span_start",
                "span_end",
                "fragment_sequence",
                "fragment_mz",
                "neutral_loss",
                "observed_mz",
                "observed_intensity",
                "mass_error_da",
                "mass_error_ppm",
                "label",
            ]
        )
        for match in annotation.matches:
            writer.writerow(
                [
                    annotation.spectrum_id,
                    annotation.peptide,
                    annotation.tolerance_unit.value,
                    match.fragment.series.value,
                    match.fragment.ordinal,
                    match.fragment.charge,
                    match.fragment.span_start,
                    match.fragment.span_end,
                    match.fragment.sequence,
                    match.fragment.mz_monoisotopic,
                    (
                        None
                        if match.fragment.neutral_loss is None
                        else match.fragment.neutral_loss
                    ),
                    match.observed_mz,
                    match.observed_intensity,
                    match.mass_error_da,
                    match.mass_error_ppm,
                    match.fragment_label,
                ]
            )


def build_spectrum_plot_payload(
    spectrum: SpectrumModel,
    *,
    annotation: SpectrumAnnotation | None = None,
) -> SpectrumPlotPayload:
    """Build a stable JSON payload consumable by docs or a UI plot layer."""
    labels_by_peak: dict[tuple[float, float], list[str]] = {}
    if annotation is not None:
        for match in annotation.matches:
            labels_by_peak.setdefault(
                (match.observed_mz, match.observed_intensity), []
            ).append(match.fragment_label)
    peaks = tuple(
        SpectrumPlotPeak(
            mz=peak.mz,
            intensity=peak.intensity,
            labels=tuple(sorted(labels_by_peak.get((peak.mz, peak.intensity), ()))),
        )
        for peak in spectrum.peaks
    )
    schema = DocumentSchema(
        created_by="bijux-proteomics-core",
        document_kind="spectrum_plot_payload",
        package_name="bijux-proteomics-core",
        status="generated",
    )
    payload = SpectrumPlotPayload(
        document_schema=schema,
        spectrum_id=spectrum.spectrum_id,
        precursor_mz=spectrum.precursor_mz,
        precursor_charge=spectrum.precursor_charge,
        peaks=peaks,
    )
    return payload.model_copy(
        update={
            "document_schema": payload.document_schema.with_content_hash(
                payload.to_dict()
            )
        }
    )


def build_annotated_spectrum_bundle(
    spectrum: SpectrumModel,
    *,
    peptide: str | ParsedModifiedPeptide,
    tolerance_da: float | None = 0.5,
    tolerance_ppm: float | None = None,
    include_neutral_losses: bool = True,
) -> AnnotatedSpectrumBundle:
    """Build one self-contained annotation bundle with raw and theoretical evidence."""
    canonical = _canonical_peptide_text(peptide)
    theoretical_fragments = calculate_fragment_ions(
        peptide,
        include_neutral_losses=include_neutral_losses,
    )
    annotation = annotate_spectrum_fragments(
        spectrum,
        peptide=peptide,
        tolerance_da=tolerance_da,
        tolerance_ppm=tolerance_ppm,
        include_neutral_losses=include_neutral_losses,
    )
    tolerance_unit, resolved_tolerance_da, resolved_tolerance_ppm = (
        _resolve_annotation_tolerance(
            tolerance_da=tolerance_da,
            tolerance_ppm=tolerance_ppm,
        )
    )
    schema = DocumentSchema(
        created_by="bijux-proteomics-core",
        document_kind="annotated_spectrum_bundle",
        package_name="bijux-proteomics-core",
        status="generated",
    )
    bundle = AnnotatedSpectrumBundle(
        document_schema=schema,
        spectrum=spectrum,
        annotation=annotation,
        theoretical_fragments=theoretical_fragments,
        parameters=SpectrumAnnotationParameters(
            peptide=canonical,
            tolerance_unit=tolerance_unit,
            tolerance_da=resolved_tolerance_da,
            tolerance_ppm=resolved_tolerance_ppm,
            include_neutral_losses=include_neutral_losses,
        ),
    )
    return bundle.model_copy(
        update={
            "document_schema": bundle.document_schema.with_content_hash(
                bundle.to_dict()
            )
        }
    )


def write_annotated_spectrum_bundle(
    bundle: AnnotatedSpectrumBundle,
    path: Path,
) -> None:
    """Write one annotated spectrum bundle as stable JSON."""
    path.write_text(
        json.dumps(bundle.to_dict(), sort_keys=True, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )


def export_annotated_spectrum_bundle(
    bundle: AnnotatedSpectrumBundle,
    path: Path,
) -> None:
    """Compatibility wrapper for the legacy annotated spectrum bundle export name."""

    write_annotated_spectrum_bundle(bundle, path)
