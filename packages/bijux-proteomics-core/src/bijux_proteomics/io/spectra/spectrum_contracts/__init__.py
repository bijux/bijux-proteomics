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
from bijux_proteomics.io.spectra.spectrum_contracts.similarity import (
    build_spectrum_library_similarity_report,
    build_spectrum_similarity_comparison_report,
    calculate_spectral_similarity,
)


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
