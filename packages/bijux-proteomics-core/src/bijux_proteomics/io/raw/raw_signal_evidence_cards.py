# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Structured raw-signal evidence cards over spectrum and chromatographic support."""

from __future__ import annotations

import csv
from enum import StrEnum
from html import escape
from io import StringIO
from pathlib import Path

from pydantic import ConfigDict, Field, model_validator

from bijux_proteomics.domain.semantic_ids import build_raw_signal_card_id
from bijux_proteomics.domain.source_row_lineage import SourceRowLineage
from bijux_proteomics.identification import (
    SearchResultColumnMapping,
    parse_psm_tsv,
)
from bijux_proteomics.io.chromatography.chromatographic_evidence import (
    ChromatographicEvidenceScoreReport,
    ChromatographicTargetEvidenceEntry,
    score_chromatographic_evidence,
)
from bijux_proteomics.io.chromatography.chromatographic_peak_picking import (
    ChromatographicPeak,
    ChromatographicPeakPickingReport,
)
from bijux_proteomics.io.chromatography.dia_fragment_coelution import (
    DiaFragmentCoelutionFragmentEntry,
    DiaFragmentCoelutionReport,
    DiaFragmentCoelutionRunEntry,
)
from bijux_proteomics.io.chromatography.retention_time_alignment import (
    RetentionTimeAlignmentFailedAnchor,
    RetentionTimeAlignmentReport,
    RetentionTimeAlignmentResidual,
    RetentionTimeAlignmentRunModel,
    align_chromatographic_peak_retention_times,
)
from bijux_proteomics.io.raw.chromatographic_peak_picking import (
    extract_mzml_chromatographic_peaks,
)
from bijux_proteomics.io.raw.dia_fragment_coelution import (
    extract_mzml_dia_fragment_trace_coelution,
)
from bijux_proteomics.io.raw.mzml_reader import parse_mzml
from bijux_proteomics.io.raw.precursor_isotope_fit import (
    PrecursorIsotopeFitEntry,
    PrecursorIsotopeFitReport,
    extract_mzml_precursor_isotope_fit,
)
from bijux_proteomics.io.spectra.chimeric_spectrum import (
    ChimericSpectrumCompetingEvidenceEntry,
    ChimericSpectrumEntry,
    ChimericSpectrumReport,
    score_chimeric_spectra_from_psms,
)
from bijux_proteomics.io.tables.xic_target_table import (
    XicTargetParseReport,
    parse_xic_target_table,
)
from bijux_proteomics_foundation import JsonModel


class RawSignalEvidenceCardWarningCode(StrEnum):
    """Stable warning codes preserved on one raw-signal evidence card."""

    CHIMERIC_SPECTRUM = "chimeric_spectrum"
    CHROMATOGRAPHIC_PEAK_CONCERN = "chromatographic_peak_concern"
    RETENTION_TIME_ALIGNMENT_OUTSIDE_TOLERANCE = (
        "retention_time_alignment_outside_tolerance"
    )
    RETENTION_TIME_ALIGNMENT_MISSING_ANCHOR = "retention_time_alignment_missing_anchor"
    PRECURSOR_ISOTOPE_MISMATCH = "precursor_isotope_mismatch"
    WEAK_FRAGMENT_SUPPORT = "weak_fragment_support"


class RawSignalEvidenceCardWarning(JsonModel):
    """One explicit warning attached to one raw-signal evidence card."""

    model_config = ConfigDict(extra="forbid")

    code: RawSignalEvidenceCardWarningCode
    message: str = Field(..., min_length=1)


class RawSignalChromatographicPeakObservation(JsonModel):
    """One run-level chromatographic peak preserved on one raw-signal card."""

    model_config = ConfigDict(extra="forbid")

    run_id: str = Field(..., min_length=1)
    source_path: str = Field(..., min_length=1)
    peak: ChromatographicPeak


class RawSignalEvidenceCard(JsonModel):
    """One structured raw-signal evidence card for one peptide or precursor."""

    model_config = ConfigDict(extra="forbid")

    card_id: str = Field(..., min_length=1)
    precursor_id: str = Field(..., min_length=1)
    peptide_ref: str = Field(..., min_length=1)
    display_name: str | None = None
    precursor_mz: float | None = Field(default=None, gt=0.0)
    chromatographic_target_ids: tuple[str, ...] = Field(default_factory=tuple)
    chromatographic_targets: tuple[ChromatographicTargetEvidenceEntry, ...] = Field(
        default_factory=tuple
    )
    chromatographic_peaks: tuple[RawSignalChromatographicPeakObservation, ...] = Field(
        default_factory=tuple
    )
    retention_time_models: tuple[RetentionTimeAlignmentRunModel, ...] = Field(
        default_factory=tuple
    )
    retention_time_residuals: tuple[RetentionTimeAlignmentResidual, ...] = Field(
        default_factory=tuple
    )
    retention_time_failed_anchors: tuple[RetentionTimeAlignmentFailedAnchor, ...] = (
        Field(default_factory=tuple)
    )
    spectrum_evidence: tuple[ChimericSpectrumEntry, ...] = Field(default_factory=tuple)
    competing_spectrum_evidence: tuple[ChimericSpectrumCompetingEvidenceEntry, ...] = (
        Field(default_factory=tuple)
    )
    fragment_run_entries: tuple[DiaFragmentCoelutionRunEntry, ...] = Field(
        default_factory=tuple
    )
    fragment_entries: tuple[DiaFragmentCoelutionFragmentEntry, ...] = Field(
        default_factory=tuple
    )
    precursor_isotope_fit_entries: tuple[PrecursorIsotopeFitEntry, ...] = Field(
        default_factory=tuple
    )
    warnings: tuple[RawSignalEvidenceCardWarning, ...] = Field(default_factory=tuple)
    source_row_refs: tuple[str, ...] = Field(default_factory=tuple)
    derived_no_source_reason: str | None = None

    @model_validator(mode="after")
    def _validate_source_row_lineage(self) -> RawSignalEvidenceCard:
        SourceRowLineage(
            source_row_refs=self.source_row_refs,
            derived_no_source_reason=self.derived_no_source_reason,
        )
        return self


class RawSignalEvidenceCardSummary(JsonModel):
    """Compact summary over one raw-signal evidence-card pass."""

    model_config = ConfigDict(extra="forbid")

    card_count: int = Field(..., ge=0)
    warning_card_count: int = Field(..., ge=0)
    spectrum_evidence_card_count: int = Field(..., ge=0)
    fragment_support_card_count: int = Field(..., ge=0)
    retention_time_flagged_card_count: int = Field(..., ge=0)
    isotope_fit_card_count: int = Field(..., ge=0)


class RawSignalEvidenceCardReport(JsonModel):
    """Stable raw-signal evidence-card report over selected peptides or precursors."""

    model_config = ConfigDict(extra="forbid")

    cards: tuple[RawSignalEvidenceCard, ...] = Field(default_factory=tuple)
    summary: RawSignalEvidenceCardSummary
    note: str = Field(..., min_length=1)


def build_raw_signal_evidence_card_report(
    *,
    peak_reports: tuple[ChromatographicPeakPickingReport, ...],
    chromatographic_evidence_report: ChromatographicEvidenceScoreReport,
    alignment_report: RetentionTimeAlignmentReport | None = None,
    spectrum_report: ChimericSpectrumReport | None = None,
    fragment_coelution_report: DiaFragmentCoelutionReport | None = None,
    precursor_isotope_fit_report: PrecursorIsotopeFitReport | None = None,
    selected_precursor_ids: tuple[str, ...] = (),
    selected_peptide_refs: tuple[str, ...] = (),
) -> RawSignalEvidenceCardReport:
    """Build one raw-signal evidence card per selected precursor or peptide."""

    if not peak_reports:
        raise ValueError("raw-signal evidence cards require at least one peak report")

    selected_precursor_set = {
        value.strip() for value in selected_precursor_ids if value.strip()
    }
    selected_peptide_set = {
        value.strip() for value in selected_peptide_refs if value.strip()
    }

    precursor_specs = _collect_precursor_specs(
        peak_reports,
        fragment_coelution_report=fragment_coelution_report,
    )
    cards: list[RawSignalEvidenceCard] = []
    chromatographic_targets_by_target_id = {
        entry.target_id: entry
        for entry in chromatographic_evidence_report.target_entries
    }
    peaks_by_target_id = _peaks_by_target_id(peak_reports)

    spectrum_entries_by_id = (
        {}
        if spectrum_report is None
        else {entry.spectrum_id: entry for entry in spectrum_report.spectra}
    )
    competing_entries_by_spectrum_id = _competing_entries_by_spectrum_id(
        spectrum_report
    )

    for precursor_id, spec in sorted(
        precursor_specs.items(),
        key=lambda item: (item[1].peptide_ref, item[0]),
    ):
        if selected_precursor_set and precursor_id not in selected_precursor_set:
            if not (selected_peptide_set and spec.peptide_ref in selected_peptide_set):
                continue
        elif (
            selected_peptide_set
            and spec.peptide_ref not in selected_peptide_set
            and precursor_id not in selected_precursor_set
        ):
            continue

        chromatographic_targets = tuple(
            sorted(
                (
                    chromatographic_targets_by_target_id[target_id]
                    for target_id in spec.chromatographic_target_ids
                    if target_id in chromatographic_targets_by_target_id
                ),
                key=lambda item: item.target_id,
            )
        )
        chromatographic_peaks = tuple(
            sorted(
                (
                    observation
                    for target_id in spec.chromatographic_target_ids
                    for observation in peaks_by_target_id.get(target_id, ())
                ),
                key=lambda item: (
                    item.run_id,
                    item.peak.apex_time_seconds,
                    item.peak.peak_id,
                ),
            )
        )
        retention_time_residuals = _retention_time_residuals_for_targets(
            alignment_report,
            spec.chromatographic_target_ids,
        )
        retention_time_failed_anchors = _failed_anchors_for_targets(
            alignment_report,
            spec.chromatographic_target_ids,
        )
        retention_time_models = _retention_time_models_for_card(
            alignment_report,
            chromatographic_peaks,
        )
        spectrum_ids = _spectrum_ids_for_peptide(
            spec.peptide_ref,
            spectrum_report,
            competing_entries_by_spectrum_id,
        )
        spectrum_evidence = tuple(
            sorted(
                (
                    spectrum_entries_by_id[spectrum_id]
                    for spectrum_id in spectrum_ids
                    if spectrum_id in spectrum_entries_by_id
                ),
                key=lambda item: (
                    item.flagged_chimeric is False,
                    -item.chimeric_score,
                    item.spectrum_id,
                ),
            )
        )
        competing_spectrum_evidence = tuple(
            sorted(
                (
                    entry
                    for spectrum_id in spectrum_ids
                    for entry in competing_entries_by_spectrum_id.get(spectrum_id, ())
                ),
                key=lambda item: (
                    item.spectrum_id,
                    -item.competition_score,
                    item.competing_peptide,
                ),
            )
        )
        fragment_run_entries = _fragment_run_entries_for_precursor(
            fragment_coelution_report,
            precursor_id,
        )
        fragment_entries = _fragment_entries_for_precursor(
            fragment_coelution_report,
            precursor_id,
        )
        precursor_isotope_fit_entries = _precursor_isotope_fit_entries_for_precursor(
            precursor_isotope_fit_report,
            precursor_id,
        )
        warnings = _build_card_warnings(
            spec.peptide_ref,
            chromatographic_targets=chromatographic_targets,
            retention_time_residuals=retention_time_residuals,
            retention_time_failed_anchors=retention_time_failed_anchors,
            spectrum_evidence=spectrum_evidence,
            fragment_run_entries=fragment_run_entries,
            fragment_entries=fragment_entries,
            precursor_isotope_fit_entries=precursor_isotope_fit_entries,
        )
        cards.append(
            RawSignalEvidenceCard(
                card_id=build_raw_signal_card_id(precursor_id),
                precursor_id=precursor_id,
                peptide_ref=spec.peptide_ref,
                display_name=spec.display_name,
                precursor_mz=spec.precursor_mz,
                chromatographic_target_ids=tuple(
                    sorted(spec.chromatographic_target_ids)
                ),
                chromatographic_targets=chromatographic_targets,
                chromatographic_peaks=chromatographic_peaks,
                retention_time_models=retention_time_models,
                retention_time_residuals=retention_time_residuals,
                retention_time_failed_anchors=retention_time_failed_anchors,
                spectrum_evidence=spectrum_evidence,
                competing_spectrum_evidence=competing_spectrum_evidence,
                fragment_run_entries=fragment_run_entries,
                fragment_entries=fragment_entries,
                precursor_isotope_fit_entries=precursor_isotope_fit_entries,
                warnings=warnings,
                derived_no_source_reason=(
                    "raw-signal evidence cards summarize mzML trace windows, spectra, and peak models rather than row-numbered tabular inputs"
                ),
            )
        )

    return RawSignalEvidenceCardReport(
        cards=tuple(cards),
        summary=RawSignalEvidenceCardSummary(
            card_count=len(cards),
            warning_card_count=sum(1 for card in cards if card.warnings),
            spectrum_evidence_card_count=sum(
                1 for card in cards if card.spectrum_evidence
            ),
            fragment_support_card_count=sum(
                1 for card in cards if card.fragment_run_entries
            ),
            retention_time_flagged_card_count=sum(
                1
                for card in cards
                if card.retention_time_residuals or card.retention_time_failed_anchors
            ),
            isotope_fit_card_count=sum(
                1 for card in cards if card.precursor_isotope_fit_entries
            ),
        ),
        note=(
            "raw-signal evidence cards preserve spectrum evidence, chromatographic peaks, "
            "retention-time alignment, fragment support, precursor isotope fit, and "
            "explicit warnings together so one peptide or precursor can be reviewed "
            "without opening multiple raw signal ledgers"
        ),
    )


def extract_mzml_raw_signal_evidence_cards(
    chromatogram_mzml_paths: tuple[Path, ...],
    xic_target_table: Path,
    *,
    fragment_target_table: Path | None = None,
    spectrum_mzml_path: Path | None = None,
    psm_path: Path | None = None,
    tolerance_da: float | None = None,
    tolerance_ppm: float | None = None,
    aligned_rt_tolerance_seconds: float = 5.0,
    min_anchor_count: int = 2,
    apex_tolerance_seconds: float = 5.0,
    min_correlation: float = 0.8,
    min_passing_fragment_count: int = 2,
    fragment_ms_level: int = 2,
    default_isolation_window_half_width_da: float = 1.0,
    chimeric_score_threshold: float = 0.45,
    selected_precursor_ids: tuple[str, ...] = (),
    selected_peptide_refs: tuple[str, ...] = (),
) -> RawSignalEvidenceCardReport:
    """Extract raw-signal evidence-card inputs from mzML and normalized targets."""

    if not chromatogram_mzml_paths:
        raise ValueError(
            "raw-signal evidence cards require at least one chromatogram mzML"
        )
    if (spectrum_mzml_path is None) ^ (psm_path is None):
        raise ValueError(
            "spectrum_mzml_path and psm_path must be provided together for spectrum evidence"
        )

    target_report = parse_xic_target_table(xic_target_table)
    peak_reports = tuple(
        extract_mzml_chromatographic_peaks(
            mzml_path,
            target_report,
            tolerance_da=tolerance_da,
            tolerance_ppm=tolerance_ppm,
        )
        for mzml_path in chromatogram_mzml_paths
    )
    alignment_report = (
        None
        if len(peak_reports) == 1
        else align_chromatographic_peak_retention_times(
            peak_reports,
            aligned_rt_tolerance_seconds=aligned_rt_tolerance_seconds,
            min_anchor_count=min_anchor_count,
        )
    )
    chromatographic_evidence_report = score_chromatographic_evidence(
        peak_reports if alignment_report is None else alignment_report.peak_reports,
        alignment_report=alignment_report,
    )
    fragment_coelution_report = (
        None
        if fragment_target_table is None
        else extract_mzml_dia_fragment_trace_coelution(
            chromatogram_mzml_paths,
            fragment_target_table,
            tolerance_da=tolerance_da,
            tolerance_ppm=tolerance_ppm,
            ms_level=fragment_ms_level,
            apex_tolerance_seconds=apex_tolerance_seconds,
            min_correlation=min_correlation,
            min_passing_fragment_count=min_passing_fragment_count,
        )
    )
    precursor_isotope_fit_report = (
        None
        if not _targets_support_precursor_isotope_fit(target_report)
        else extract_mzml_precursor_isotope_fit(
            chromatogram_mzml_paths,
            target_report,
            extraction_tolerance_da=tolerance_da,
            extraction_tolerance_ppm=tolerance_ppm,
            fit_tolerance_da=tolerance_da,
            fit_tolerance_ppm=tolerance_ppm,
        )
    )
    spectrum_report = None
    if spectrum_mzml_path is not None and psm_path is not None:
        spectra = parse_mzml(spectrum_mzml_path).accepted_spectra
        psms = parse_psm_tsv(psm_path, mapping=_default_psm_mapping()).accepted_records
        spectrum_report = score_chimeric_spectra_from_psms(
            spectra,
            psms,
            tolerance_da=tolerance_da,
            tolerance_ppm=tolerance_ppm,
            default_isolation_window_half_width_da=(
                default_isolation_window_half_width_da
            ),
            chimeric_score_threshold=chimeric_score_threshold,
        )
    return build_raw_signal_evidence_card_report(
        peak_reports=peak_reports,
        chromatographic_evidence_report=chromatographic_evidence_report,
        alignment_report=alignment_report,
        spectrum_report=spectrum_report,
        fragment_coelution_report=fragment_coelution_report,
        precursor_isotope_fit_report=precursor_isotope_fit_report,
        selected_precursor_ids=selected_precursor_ids,
        selected_peptide_refs=selected_peptide_refs,
    )


def render_raw_signal_evidence_card_summary_tsv(
    report: RawSignalEvidenceCardReport,
) -> str:
    """Render a compact raw-signal evidence-card summary TSV."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "card_count",
            "warning_card_count",
            "spectrum_evidence_card_count",
            "fragment_support_card_count",
            "retention_time_flagged_card_count",
            "isotope_fit_card_count",
        )
    )
    writer.writerow(
        (
            report.summary.card_count,
            report.summary.warning_card_count,
            report.summary.spectrum_evidence_card_count,
            report.summary.fragment_support_card_count,
            report.summary.retention_time_flagged_card_count,
            report.summary.isotope_fit_card_count,
        )
    )
    return buffer.getvalue()


def render_raw_signal_evidence_card_tsv(report: RawSignalEvidenceCardReport) -> str:
    """Render one flat raw-signal evidence-card ledger."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "card_id",
            "precursor_id",
            "peptide_ref",
            "display_name",
            "precursor_mz",
            "chromatographic_target_ids",
            "chromatographic_peak_count",
            "rt_residual_count",
            "rt_failed_anchor_count",
            "spectrum_evidence_count",
            "flagged_chimeric_spectrum_count",
            "fragment_run_count",
            "failed_fragment_count",
            "warning_codes",
            "isotope_fit_run_count",
            "flagged_isotope_fit_count",
            "source_row_refs",
            "derived_no_source_reason",
        )
    )
    for card in report.cards:
        writer.writerow(
            (
                card.card_id,
                card.precursor_id,
                card.peptide_ref,
                card.display_name or "",
                "" if card.precursor_mz is None else f"{card.precursor_mz:.6f}",
                "|".join(card.chromatographic_target_ids),
                len(card.chromatographic_peaks),
                len(card.retention_time_residuals),
                len(card.retention_time_failed_anchors),
                len(card.spectrum_evidence),
                sum(1 for entry in card.spectrum_evidence if entry.flagged_chimeric),
                len(card.fragment_run_entries),
                len(
                    {
                        entry.fragment_id
                        for entry in card.fragment_entries
                        if entry.failure_reason is not None
                    }
                ),
                "|".join(warning.code.value for warning in card.warnings),
                len(card.precursor_isotope_fit_entries),
                sum(
                    1
                    for entry in card.precursor_isotope_fit_entries
                    if entry.concern_codes or entry.isotope_fit_score < 0.75
                ),
                "|".join(card.source_row_refs),
                ""
                if card.derived_no_source_reason is None
                else card.derived_no_source_reason,
            )
        )
    return buffer.getvalue()


def render_raw_signal_evidence_cards_html(report: RawSignalEvidenceCardReport) -> str:
    """Render one compact HTML review over raw-signal evidence cards."""

    lines = [
        "<!DOCTYPE html>",
        '<html lang="en">',
        "<head>",
        '<meta charset="utf-8">',
        "<title>Raw Signal Evidence Cards</title>",
        "<style>",
        "body { font-family: ui-monospace, SFMono-Regular, Menlo, monospace; margin: 24px; }",
        "table { border-collapse: collapse; margin: 12px 0 24px; width: 100%; }",
        "th, td { border: 1px solid #c7c7c7; padding: 6px 8px; text-align: left; vertical-align: top; }",
        "th { background: #f3f3f3; }",
        "section { margin-bottom: 32px; }",
        ".warning { color: #8a2d19; }",
        "</style>",
        "</head>",
        "<body>",
        "<h1>Raw Signal Evidence Cards</h1>",
        f"<p>{escape(report.note)}</p>",
    ]
    for card in report.cards:
        lines.extend(
            [
                "<section>",
                (f"<h2>{escape(card.peptide_ref)} ({escape(card.precursor_id)})</h2>"),
                (
                    f"<p>Card id: {escape(card.card_id)}<br>"
                    f"Display name: {escape(card.display_name or '')}<br>"
                    f"Target ids: {escape('|'.join(card.chromatographic_target_ids))}</p>"
                ),
            ]
        )
        if card.warnings:
            lines.append("<ul>")
            for warning in card.warnings:
                lines.append(
                    '<li class="warning">'
                    f"{escape(warning.code.value)}: {escape(warning.message)}"
                    "</li>"
                )
            lines.append("</ul>")
        lines.extend(_html_table_for_chromatographic_targets(card))
        lines.extend(_html_table_for_peaks(card))
        lines.extend(_html_table_for_retention_time(card))
        lines.extend(_html_table_for_spectra(card))
        lines.extend(_html_table_for_fragment_runs(card))
        lines.extend(_html_table_for_precursor_isotope_fit(card))
        lines.append("</section>")
    lines.extend(["</body>", "</html>"])
    return "\n".join(lines) + "\n"


class _PrecursorSpec(JsonModel):
    """Internal grouped precursor specification for card assembly."""

    model_config = ConfigDict(extra="forbid")

    precursor_id: str
    peptide_ref: str
    display_name: str | None = None
    precursor_mz: float | None = None
    chromatographic_target_ids: tuple[str, ...] = Field(default_factory=tuple)


def _collect_precursor_specs(
    peak_reports: tuple[ChromatographicPeakPickingReport, ...],
    *,
    fragment_coelution_report: DiaFragmentCoelutionReport | None,
) -> dict[str, _PrecursorSpec]:
    specs: dict[str, _PrecursorSpec] = {}
    for target in peak_reports[0].trace_report.accepted_targets:
        precursor_id = target.metadata.get("precursor_id") or target.target_id
        peptide_ref = (
            target.metadata.get("peptide_ref")
            or target.display_name
            or target.target_id
        )
        current = specs.get(precursor_id)
        target_ids = (
            target.target_id,
            *(() if current is None else current.chromatographic_target_ids),
        )
        specs[precursor_id] = _PrecursorSpec(
            precursor_id=precursor_id,
            peptide_ref=peptide_ref,
            display_name=target.display_name,
            precursor_mz=target.precursor_mz,
            chromatographic_target_ids=tuple(sorted(set(target_ids))),
        )
    if fragment_coelution_report is not None:
        for entry in fragment_coelution_report.run_entries:
            current = specs.get(entry.precursor_id)
            if current is None:
                specs[entry.precursor_id] = _PrecursorSpec(
                    precursor_id=entry.precursor_id,
                    peptide_ref=entry.peptide_ref,
                    chromatographic_target_ids=(),
                )
    return specs


def _peaks_by_target_id(
    peak_reports: tuple[ChromatographicPeakPickingReport, ...],
) -> dict[str, tuple[RawSignalChromatographicPeakObservation, ...]]:
    grouped: dict[str, list[RawSignalChromatographicPeakObservation]] = {}
    for report in peak_reports:
        run_id = _run_id_from_peak_report(report)
        source_path = report.trace_report.source_path
        for peak in report.peaks:
            grouped.setdefault(peak.target_id, []).append(
                RawSignalChromatographicPeakObservation(
                    run_id=run_id,
                    source_path=source_path,
                    peak=peak,
                )
            )
    return {
        target_id: tuple(
            sorted(
                observations,
                key=lambda item: (
                    item.run_id,
                    item.peak.apex_time_seconds,
                    item.peak.peak_id,
                ),
            )
        )
        for target_id, observations in grouped.items()
    }


def _retention_time_residuals_for_targets(
    alignment_report: RetentionTimeAlignmentReport | None,
    target_ids: tuple[str, ...],
) -> tuple[RetentionTimeAlignmentResidual, ...]:
    if alignment_report is None:
        return ()
    target_id_set = set(target_ids)
    return tuple(
        residual
        for residual in sorted(
            alignment_report.residuals,
            key=lambda item: (item.run_id, item.target_id),
        )
        if residual.target_id in target_id_set
    )


def _failed_anchors_for_targets(
    alignment_report: RetentionTimeAlignmentReport | None,
    target_ids: tuple[str, ...],
) -> tuple[RetentionTimeAlignmentFailedAnchor, ...]:
    if alignment_report is None:
        return ()
    target_id_set = set(target_ids)
    return tuple(
        entry
        for entry in sorted(
            alignment_report.failed_anchors,
            key=lambda item: (item.run_id, item.target_id),
        )
        if entry.target_id in target_id_set
    )


def _retention_time_models_for_card(
    alignment_report: RetentionTimeAlignmentReport | None,
    chromatographic_peaks: tuple[RawSignalChromatographicPeakObservation, ...],
) -> tuple[RetentionTimeAlignmentRunModel, ...]:
    if alignment_report is None:
        return ()
    run_ids = {observation.run_id for observation in chromatographic_peaks}
    run_ids.add(alignment_report.reference_run_id)
    return tuple(
        model for model in alignment_report.run_models if model.run_id in run_ids
    )


def _competing_entries_by_spectrum_id(
    spectrum_report: ChimericSpectrumReport | None,
) -> dict[str, tuple[ChimericSpectrumCompetingEvidenceEntry, ...]]:
    if spectrum_report is None:
        return {}
    grouped: dict[str, list[ChimericSpectrumCompetingEvidenceEntry]] = {}
    for entry in spectrum_report.competing_evidence:
        grouped.setdefault(entry.spectrum_id, []).append(entry)
    return {
        spectrum_id: tuple(
            sorted(
                entries,
                key=lambda item: (-item.competition_score, item.competing_peptide),
            )
        )
        for spectrum_id, entries in grouped.items()
    }


def _spectrum_ids_for_peptide(
    peptide_ref: str,
    spectrum_report: ChimericSpectrumReport | None,
    competing_entries_by_spectrum_id: dict[
        str, tuple[ChimericSpectrumCompetingEvidenceEntry, ...]
    ],
) -> tuple[str, ...]:
    if spectrum_report is None:
        return ()
    spectrum_ids = {
        entry.spectrum_id
        for entry in spectrum_report.spectra
        if entry.primary_peptide == peptide_ref
    }
    spectrum_ids.update(
        spectrum_id
        for spectrum_id, entries in competing_entries_by_spectrum_id.items()
        if any(entry.competing_peptide == peptide_ref for entry in entries)
    )
    return tuple(sorted(spectrum_ids))


def _fragment_run_entries_for_precursor(
    fragment_coelution_report: DiaFragmentCoelutionReport | None,
    precursor_id: str,
) -> tuple[DiaFragmentCoelutionRunEntry, ...]:
    if fragment_coelution_report is None:
        return ()
    return tuple(
        entry
        for entry in sorted(
            fragment_coelution_report.run_entries,
            key=lambda item: (item.run_id, item.precursor_id),
        )
        if entry.precursor_id == precursor_id
    )


def _fragment_entries_for_precursor(
    fragment_coelution_report: DiaFragmentCoelutionReport | None,
    precursor_id: str,
) -> tuple[DiaFragmentCoelutionFragmentEntry, ...]:
    if fragment_coelution_report is None:
        return ()
    return tuple(
        entry
        for entry in sorted(
            fragment_coelution_report.fragment_entries,
            key=lambda item: (item.run_id, item.fragment_id),
        )
        if entry.precursor_id == precursor_id
    )


def _precursor_isotope_fit_entries_for_precursor(
    precursor_isotope_fit_report: PrecursorIsotopeFitReport | None,
    precursor_id: str,
) -> tuple[PrecursorIsotopeFitEntry, ...]:
    if precursor_isotope_fit_report is None:
        return ()
    return tuple(
        entry
        for entry in sorted(
            precursor_isotope_fit_report.entries,
            key=lambda item: (item.run_id, item.target_id),
        )
        if entry.precursor_id == precursor_id
    )


def _build_card_warnings(
    peptide_ref: str,
    *,
    chromatographic_targets: tuple[ChromatographicTargetEvidenceEntry, ...],
    retention_time_residuals: tuple[RetentionTimeAlignmentResidual, ...],
    retention_time_failed_anchors: tuple[RetentionTimeAlignmentFailedAnchor, ...],
    spectrum_evidence: tuple[ChimericSpectrumEntry, ...],
    fragment_run_entries: tuple[DiaFragmentCoelutionRunEntry, ...],
    fragment_entries: tuple[DiaFragmentCoelutionFragmentEntry, ...],
    precursor_isotope_fit_entries: tuple[PrecursorIsotopeFitEntry, ...],
) -> tuple[RawSignalEvidenceCardWarning, ...]:
    warnings: list[RawSignalEvidenceCardWarning] = []
    if any(entry.flagged_chimeric for entry in spectrum_evidence):
        warnings.append(
            RawSignalEvidenceCardWarning(
                code=RawSignalEvidenceCardWarningCode.CHIMERIC_SPECTRUM,
                message=(
                    f"{peptide_ref} includes at least one spectrum with competing "
                    "fragment evidence inside the isolation window"
                ),
            )
        )
    if any(entry.concern_codes for entry in chromatographic_targets):
        warnings.append(
            RawSignalEvidenceCardWarning(
                code=RawSignalEvidenceCardWarningCode.CHROMATOGRAPHIC_PEAK_CONCERN,
                message=(
                    f"{peptide_ref} has chromatographic peak concerns such as "
                    "multiple peaks, overlap, missingness, or weak signal"
                ),
            )
        )
    if any(entry.outside_aligned_tolerance for entry in retention_time_residuals):
        warnings.append(
            RawSignalEvidenceCardWarning(
                code=RawSignalEvidenceCardWarningCode.RETENTION_TIME_ALIGNMENT_OUTSIDE_TOLERANCE,
                message=(
                    f"{peptide_ref} has at least one run with an aligned retention-time "
                    "residual outside the configured tolerance"
                ),
            )
        )
    if retention_time_failed_anchors:
        warnings.append(
            RawSignalEvidenceCardWarning(
                code=RawSignalEvidenceCardWarningCode.RETENTION_TIME_ALIGNMENT_MISSING_ANCHOR,
                message=(
                    f"{peptide_ref} has at least one run where the chromatographic "
                    "anchor could not be aligned"
                ),
            )
        )
    if any(
        entry.concern_codes or entry.isotope_fit_score < 0.75
        for entry in precursor_isotope_fit_entries
    ):
        warnings.append(
            RawSignalEvidenceCardWarning(
                code=RawSignalEvidenceCardWarningCode.PRECURSOR_ISOTOPE_MISMATCH,
                message=(
                    f"{peptide_ref} has precursor isotope evidence with shifted "
                    "monoisotopic mass, missing isotope peaks, or inconsistent "
                    "charge spacing in at least one run"
                ),
            )
        )
    if any(
        "insufficient_passing_fragments" in entry.concern_codes
        for entry in fragment_run_entries
    ) or any(entry.failure_reason is not None for entry in fragment_entries):
        warnings.append(
            RawSignalEvidenceCardWarning(
                code=RawSignalEvidenceCardWarningCode.WEAK_FRAGMENT_SUPPORT,
                message=(
                    f"{peptide_ref} has fragment-trace evidence with missing, shifted, "
                    "or low-correlation fragments"
                ),
            )
        )
    return tuple(warnings)


def _run_id_from_peak_report(report: ChromatographicPeakPickingReport) -> str:
    return Path(report.trace_report.source_path).stem


def _targets_support_precursor_isotope_fit(
    target_report: XicTargetParseReport,
) -> bool:
    if not target_report.accepted_entries:
        return False
    return all(
        target.expected_charge is not None and bool(target.metadata.get("peptide_ref"))
        for target in target_report.accepted_entries
    )


def _default_psm_mapping() -> SearchResultColumnMapping:
    return SearchResultColumnMapping(
        spectrum_id="spectrum_id",
        peptide="peptide",
        charge="charge",
        score="score",
        q_value="q_value",
        protein_refs="proteins",
    )


def _html_table_for_chromatographic_targets(card: RawSignalEvidenceCard) -> list[str]:
    if not card.chromatographic_targets:
        return []
    lines = [
        "<h3>Chromatographic Targets</h3>",
        "<table>",
        "<tr><th>target_id</th><th>score</th><th>rt_score</th><th>missing_run_ids</th><th>concerns</th></tr>",
    ]
    for entry in card.chromatographic_targets:
        lines.append(
            "<tr>"
            f"<td>{escape(entry.target_id)}</td>"
            f"<td>{entry.chromatographic_evidence_score:.4f}</td>"
            f"<td>{entry.rt_agreement_score:.4f}</td>"
            f"<td>{escape('|'.join(entry.missing_run_ids))}</td>"
            f"<td>{escape('|'.join(entry.concern_codes))}</td>"
            "</tr>"
        )
    lines.extend(["</table>"])
    return lines


def _html_table_for_peaks(card: RawSignalEvidenceCard) -> list[str]:
    if not card.chromatographic_peaks:
        return []
    lines = [
        "<h3>Chromatographic Peaks</h3>",
        "<table>",
        "<tr><th>run_id</th><th>peak_id</th><th>target_id</th><th>apex_time_seconds</th><th>area</th><th>overlap</th><th>shoulder</th></tr>",
    ]
    for observation in card.chromatographic_peaks:
        peak = observation.peak
        lines.append(
            "<tr>"
            f"<td>{escape(observation.run_id)}</td>"
            f"<td>{escape(peak.peak_id)}</td>"
            f"<td>{escape(peak.target_id)}</td>"
            f"<td>{peak.apex_time_seconds:.4f}</td>"
            f"<td>{peak.area:.4f}</td>"
            f"<td>{str(peak.overlap_flag).lower()}</td>"
            f"<td>{str(peak.shoulder_flag).lower()}</td>"
            "</tr>"
        )
    lines.extend(["</table>"])
    return lines


def _html_table_for_retention_time(card: RawSignalEvidenceCard) -> list[str]:
    if not card.retention_time_models and not card.retention_time_residuals:
        return []
    lines = ["<h3>Retention-Time Alignment</h3>"]
    if card.retention_time_models:
        lines.extend(
            [
                "<table>",
                "<tr><th>run_id</th><th>status</th><th>shift_seconds</th><th>median_absolute_residual_seconds</th></tr>",
            ]
        )
        for model in card.retention_time_models:
            lines.append(
                "<tr>"
                f"<td>{escape(model.run_id)}</td>"
                f"<td>{escape(model.status.value)}</td>"
                f"<td>{'' if model.shift_seconds is None else f'{model.shift_seconds:.4f}'}</td>"
                f"<td>{'' if model.median_absolute_residual_seconds is None else f'{model.median_absolute_residual_seconds:.4f}'}</td>"
                "</tr>"
            )
        lines.append("</table>")
    if card.retention_time_residuals:
        lines.extend(
            [
                "<table>",
                "<tr><th>run_id</th><th>target_id</th><th>aligned_apex_time_seconds</th><th>residual_seconds</th><th>outside_tolerance</th></tr>",
            ]
        )
        for residual in card.retention_time_residuals:
            lines.append(
                "<tr>"
                f"<td>{escape(residual.run_id)}</td>"
                f"<td>{escape(residual.target_id)}</td>"
                f"<td>{residual.aligned_apex_time_seconds:.4f}</td>"
                f"<td>{residual.residual_seconds:.4f}</td>"
                f"<td>{str(residual.outside_aligned_tolerance).lower()}</td>"
                "</tr>"
            )
        lines.append("</table>")
    return lines


def _html_table_for_spectra(card: RawSignalEvidenceCard) -> list[str]:
    if not card.spectrum_evidence:
        return []
    lines = [
        "<h3>Spectrum Evidence</h3>",
        "<table>",
        "<tr><th>spectrum_id</th><th>primary_peptide</th><th>chimeric_score</th><th>flagged_chimeric</th><th>strongest_competing_peptide</th><th>strongest_competing_score</th></tr>",
    ]
    for entry in card.spectrum_evidence:
        lines.append(
            "<tr>"
            f"<td>{escape(entry.spectrum_id)}</td>"
            f"<td>{escape(entry.primary_peptide)}</td>"
            f"<td>{entry.chimeric_score:.4f}</td>"
            f"<td>{str(entry.flagged_chimeric).lower()}</td>"
            f"<td>{escape(entry.strongest_competing_peptide or '')}</td>"
            f"<td>{entry.strongest_competing_score:.4f}</td>"
            "</tr>"
        )
    lines.append("</table>")
    return lines


def _html_table_for_fragment_runs(card: RawSignalEvidenceCard) -> list[str]:
    if not card.fragment_run_entries:
        return []
    lines = [
        "<h3>Fragment Support</h3>",
        "<table>",
        "<tr><th>run_id</th><th>coelution_score</th><th>passing_fragment_count</th><th>failed_fragment_ids</th><th>concerns</th></tr>",
    ]
    for entry in card.fragment_run_entries:
        lines.append(
            "<tr>"
            f"<td>{escape(entry.run_id)}</td>"
            f"<td>{entry.coelution_score:.4f}</td>"
            f"<td>{entry.passing_fragment_count}</td>"
            f"<td>{escape('|'.join(entry.failed_fragment_ids))}</td>"
            f"<td>{escape('|'.join(entry.concern_codes))}</td>"
            "</tr>"
        )
    lines.append("</table>")
    return lines


def _html_table_for_precursor_isotope_fit(card: RawSignalEvidenceCard) -> list[str]:
    if not card.precursor_isotope_fit_entries:
        return []
    lines = [
        "<h3>Precursor Isotope Fit</h3>",
        "<table>",
        "<tr><th>run_id</th><th>apex_spectrum_id</th><th>mass_error_ppm</th><th>pattern_score</th><th>charge_score</th><th>fit_score</th><th>missing_isotopes</th><th>concerns</th></tr>",
    ]
    for entry in card.precursor_isotope_fit_entries:
        lines.append(
            "<tr>"
            f"<td>{escape(entry.run_id)}</td>"
            f"<td>{escape(entry.apex_spectrum_id or '')}</td>"
            f"<td>{'' if entry.monoisotopic_mass_error_ppm is None else f'{entry.monoisotopic_mass_error_ppm:.4f}'}</td>"
            f"<td>{entry.isotope_pattern_score:.4f}</td>"
            f"<td>{entry.charge_consistency_score:.4f}</td>"
            f"<td>{entry.isotope_fit_score:.4f}</td>"
            f"<td>{escape('|'.join(str(index) for index in entry.missing_isotope_indices))}</td>"
            f"<td>{escape('|'.join(entry.concern_codes))}</td>"
            "</tr>"
        )
    lines.append("</table>")
    return lines


__all__ = [
    "RawSignalChromatographicPeakObservation",
    "RawSignalEvidenceCard",
    "RawSignalEvidenceCardReport",
    "RawSignalEvidenceCardSummary",
    "RawSignalEvidenceCardWarning",
    "RawSignalEvidenceCardWarningCode",
    "build_raw_signal_evidence_card_report",
    "extract_mzml_raw_signal_evidence_cards",
    "render_raw_signal_evidence_card_summary_tsv",
    "render_raw_signal_evidence_card_tsv",
    "render_raw_signal_evidence_cards_html",
]
