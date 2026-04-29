# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""LC-MS run quality-control and batch-diagnostic contracts."""

from __future__ import annotations

from collections import Counter, defaultdict
from enum import StrEnum
from pathlib import Path
from statistics import median

from pydantic import ConfigDict, Field

from bijux_proteomics.chemistry import calculate_peptide_mz
from bijux_proteomics.digestion import get_protease_rule, ProteaseCleavageMode, ProteaseRule
from bijux_proteomics.formats import ExperimentalDesignEntry
from bijux_proteomics.identification import PsmRecord
from bijux_proteomics.spectra import calculate_precursor_mass_error, SpectrumModel
from bijux_proteomics_foundation import DocumentSchema, JsonModel


class QcDigestionSpecificity(StrEnum):
    """Stable digestion-specificity classes for identified peptides."""

    ENZYMATIC = "enzymatic"
    SEMI_SPECIFIC = "semi_specific"
    NON_SPECIFIC = "non_specific"


class QcChargeStateEntry(JsonModel):
    """One charge-state count and fraction."""

    model_config = ConfigDict(extra="forbid")

    charge_label: str = Field(..., min_length=1)
    count: int = Field(..., ge=0)
    fraction: float = Field(..., ge=0.0, le=1.0)


class QcMassErrorSummary(JsonModel):
    """Stable summary over precursor mass-error evidence."""

    model_config = ConfigDict(extra="forbid")

    matched_psm_count: int = Field(..., ge=0)
    mean_ppm: float | None = None
    median_ppm: float | None = None
    median_abs_ppm: float | None = Field(default=None, ge=0.0)
    p95_abs_ppm: float | None = Field(default=None, ge=0.0)
    max_abs_ppm: float | None = Field(default=None, ge=0.0)


class QcRetentionTimeSummary(JsonModel):
    """Stable retention-time coverage summary for one run."""

    model_config = ConfigDict(extra="forbid")

    spectra_with_retention_time: int = Field(..., ge=0)
    identified_with_retention_time: int = Field(..., ge=0)
    min_retention_time_seconds: float | None = Field(default=None, ge=0.0)
    max_retention_time_seconds: float | None = Field(default=None, ge=0.0)
    span_seconds: float | None = Field(default=None, ge=0.0)
    identified_min_retention_time_seconds: float | None = Field(default=None, ge=0.0)
    identified_max_retention_time_seconds: float | None = Field(default=None, ge=0.0)
    identified_span_seconds: float | None = Field(default=None, ge=0.0)
    identified_median_retention_time_seconds: float | None = Field(default=None, ge=0.0)


class QcContaminantSummary(JsonModel):
    """Stable contaminant burden summary for one run."""

    model_config = ConfigDict(extra="forbid")

    contaminant_psm_count: int = Field(..., ge=0)
    contaminant_psm_fraction: float = Field(..., ge=0.0, le=1.0)
    contaminant_protein_counts: dict[str, int] = Field(default_factory=dict)


class QcDigestionSpecificityEntry(JsonModel):
    """One digestion-specificity bucket for identified peptides."""

    model_config = ConfigDict(extra="forbid")

    specificity: QcDigestionSpecificity
    count: int = Field(..., ge=0)
    fraction: float = Field(..., ge=0.0, le=1.0)


class QcContaminantPolicy(JsonModel):
    """Stable policy for contaminant classification from protein references."""

    model_config = ConfigDict(extra="forbid")

    prefixes: tuple[str, ...] = ("CON__",)
    substrings: tuple[str, ...] = ("KERATIN", "CONTAMINANT", "CRAP")


class LcmsRunQcReport(JsonModel):
    """Run-level LC-MS QC summary built from spectra and identifications."""

    model_config = ConfigDict(extra="forbid")

    document_schema: DocumentSchema
    run_id: str = Field(..., min_length=1)
    sample_id: str | None = None
    condition: str | None = None
    replicate: int | None = Field(default=None, ge=1)
    fraction: int | None = Field(default=None, ge=1)
    batch: str | None = None
    instrument: str | None = None
    spectrum_count: int = Field(..., ge=0)
    identified_spectrum_count: int = Field(..., ge=0)
    psm_count: int = Field(..., ge=0)
    identification_rate: float = Field(..., ge=0.0, le=1.0)
    spectrum_charge_distribution: tuple[QcChargeStateEntry, ...] = Field(default_factory=tuple)
    identified_charge_distribution: tuple[QcChargeStateEntry, ...] = Field(default_factory=tuple)
    mass_error: QcMassErrorSummary
    retention_time: QcRetentionTimeSummary
    missed_cleavage_count: int = Field(..., ge=0)
    missed_cleavage_rate: float = Field(..., ge=0.0, le=1.0)
    contaminant_summary: QcContaminantSummary
    digestion_specificity: tuple[QcDigestionSpecificityEntry, ...] = Field(default_factory=tuple)


class InstrumentBatchQcRunEntry(JsonModel):
    """One run scored against its batch peers."""

    model_config = ConfigDict(extra="forbid")

    run_id: str = Field(..., min_length=1)
    sample_id: str | None = None
    batch: str | None = None
    instrument: str | None = None
    spectrum_count: int = Field(..., ge=0)
    identification_rate: float = Field(..., ge=0.0, le=1.0)
    median_abs_mass_error_ppm: float | None = Field(default=None, ge=0.0)
    identified_retention_time_span_seconds: float | None = Field(default=None, ge=0.0)
    retention_time_shift_seconds: float | None = None
    outlier_reasons: tuple[str, ...] = Field(default_factory=tuple)


class InstrumentBatchQcReport(JsonModel):
    """Batch-level QC summary over multiple LC-MS runs."""

    model_config = ConfigDict(extra="forbid")

    document_schema: DocumentSchema
    batch_id: str | None = None
    instrument: str | None = None
    run_count: int = Field(..., ge=0)
    median_spectrum_count: float = Field(..., ge=0.0)
    median_identification_rate: float = Field(..., ge=0.0, le=1.0)
    median_abs_mass_error_ppm: float | None = Field(default=None, ge=0.0)
    median_identified_retention_time_seconds: float | None = Field(default=None, ge=0.0)
    outlier_run_ids: tuple[str, ...] = Field(default_factory=tuple)
    runs: tuple[InstrumentBatchQcRunEntry, ...] = Field(default_factory=tuple)


def _build_document_schema(document_kind: str) -> DocumentSchema:
    return DocumentSchema(
        created_by="bijux-proteomics-core",
        document_kind=document_kind,
        package_name="bijux-proteomics-core",
        status="generated",
    )


def _resolve_run_id(run_id: str | None, design_entry: ExperimentalDesignEntry | None) -> str:
    if run_id:
        return run_id
    if design_entry and design_entry.spectra_file:
        return Path(design_entry.spectra_file).stem
    if design_entry and design_entry.sample_id:
        return f"{design_entry.sample_id}-run"
    return "run"


def _quantile(sorted_values: list[float], fraction: float) -> float:
    if not sorted_values:
        raise ValueError("cannot calculate a quantile for an empty sequence")
    if len(sorted_values) == 1:
        return sorted_values[0]
    position = (len(sorted_values) - 1) * fraction
    lower_index = int(position)
    upper_index = min(lower_index + 1, len(sorted_values) - 1)
    interpolation = position - lower_index
    return sorted_values[lower_index] + (
        (sorted_values[upper_index] - sorted_values[lower_index]) * interpolation
    )


def _fraction(count: int, total: int) -> float:
    return 0.0 if total == 0 else count / total


def _build_charge_distribution(counts: Counter[str], total: int) -> tuple[QcChargeStateEntry, ...]:
    return tuple(
        QcChargeStateEntry(charge_label=label, count=count, fraction=_fraction(count, total))
        for label, count in sorted(counts.items(), key=lambda item: item[0])
    )


def _is_contaminant_reference(reference: str, policy: QcContaminantPolicy) -> bool:
    normalized = reference.strip().upper()
    return normalized.startswith(tuple(prefix.upper() for prefix in policy.prefixes)) or any(
        token.upper() in normalized for token in policy.substrings
    )


def _count_missed_cleavages(sequence: str, rule: ProteaseRule) -> int:
    if len(sequence) < 2:
        return 0
    count = 0
    if rule.cleavage_mode is ProteaseCleavageMode.C_TERMINAL:
        for index in range(len(sequence) - 1):
            residue = sequence[index]
            next_residue = sequence[index + 1]
            if residue in rule.cleavage_residues and next_residue not in rule.blocked_by_next:
                count += 1
        return count
    for index in range(1, len(sequence)):
        residue = sequence[index]
        previous_residue = sequence[index - 1]
        if residue in rule.cleavage_residues and previous_residue not in rule.blocked_by_previous:
            count += 1
    return count


def _boundary_valid(
    protein_sequence: str,
    *,
    peptide_start: int,
    peptide_end: int,
    rule: ProteaseRule,
) -> tuple[bool, bool]:
    sequence_length = len(protein_sequence)
    if rule.cleavage_mode is ProteaseCleavageMode.C_TERMINAL:
        if peptide_start == 1:
            left_valid = True
        else:
            left_residue = protein_sequence[peptide_start - 2]
            first_peptide_residue = protein_sequence[peptide_start - 1]
            left_valid = left_residue in rule.cleavage_residues and first_peptide_residue not in rule.blocked_by_next
        if peptide_end == sequence_length:
            right_valid = True
        else:
            last_peptide_residue = protein_sequence[peptide_end - 1]
            right_neighbor = protein_sequence[peptide_end]
            right_valid = last_peptide_residue in rule.cleavage_residues and right_neighbor not in rule.blocked_by_next
        return left_valid, right_valid

    if peptide_start == 1:
        left_valid = True
    else:
        left_neighbor = protein_sequence[peptide_start - 2]
        first_peptide_residue = protein_sequence[peptide_start - 1]
        left_valid = first_peptide_residue in rule.cleavage_residues and left_neighbor not in rule.blocked_by_previous
    if peptide_end == sequence_length:
        right_valid = True
    else:
        last_peptide_residue = protein_sequence[peptide_end - 1]
        right_neighbor = protein_sequence[peptide_end]
        right_valid = right_neighbor in rule.cleavage_residues and last_peptide_residue not in rule.blocked_by_previous
    return left_valid, right_valid


def _classify_specificity(
    peptide_sequence: str,
    protein_refs: tuple[str, ...],
    protein_sequences: dict[str, str],
    rule: ProteaseRule,
) -> QcDigestionSpecificity:
    best = QcDigestionSpecificity.NON_SPECIFIC
    for protein_ref in protein_refs:
        protein_sequence = protein_sequences.get(protein_ref)
        if not protein_sequence:
            continue
        offset = protein_sequence.find(peptide_sequence)
        while offset != -1:
            start = offset + 1
            end = offset + len(peptide_sequence)
            left_valid, right_valid = _boundary_valid(
                protein_sequence,
                peptide_start=start,
                peptide_end=end,
                rule=rule,
            )
            if left_valid and right_valid:
                return QcDigestionSpecificity.ENZYMATIC
            if left_valid or right_valid:
                best = QcDigestionSpecificity.SEMI_SPECIFIC
            offset = protein_sequence.find(peptide_sequence, offset + 1)
    return best


def build_lcms_run_qc_report(
    spectra: tuple[SpectrumModel, ...],
    psm_records: tuple[PsmRecord, ...],
    *,
    design_entry: ExperimentalDesignEntry | None = None,
    protein_sequences: dict[str, str] | None = None,
    protease: ProteaseRule | str = "trypsin",
    run_id: str | None = None,
    contaminant_policy: QcContaminantPolicy | None = None,
) -> LcmsRunQcReport:
    """Build a typed QC report for one LC-MS run."""
    active_rule = get_protease_rule(protease) if isinstance(protease, str) else protease
    active_contaminant_policy = contaminant_policy or QcContaminantPolicy()
    spectra_by_id = {spectrum.spectrum_id: spectrum for spectrum in spectra}
    identified_spectrum_ids = {record.spectrum_id for record in psm_records}

    spectrum_charge_counts: Counter[str] = Counter()
    for spectrum in spectra:
        label = "unknown" if spectrum.precursor_charge is None else str(spectrum.precursor_charge)
        spectrum_charge_counts[label] += 1

    identified_charge_counts: Counter[str] = Counter(str(record.charge) for record in psm_records)

    mass_errors_ppm: list[float] = []
    for record in psm_records:
        spectrum = spectra_by_id.get(record.spectrum_id)
        if spectrum is None:
            continue
        theoretical_mz = calculate_peptide_mz(record.peptide, charge=record.charge)
        mass_error = calculate_precursor_mass_error(
            observed_mz=spectrum.precursor_mz,
            theoretical_mz=theoretical_mz,
        )
        mass_errors_ppm.append(mass_error.delta_ppm)

    sorted_abs_mass_errors = sorted(abs(value) for value in mass_errors_ppm)
    mass_error_summary = QcMassErrorSummary(
        matched_psm_count=len(mass_errors_ppm),
        mean_ppm=None if not mass_errors_ppm else sum(mass_errors_ppm) / len(mass_errors_ppm),
        median_ppm=None if not mass_errors_ppm else median(mass_errors_ppm),
        median_abs_ppm=None if not sorted_abs_mass_errors else median(sorted_abs_mass_errors),
        p95_abs_ppm=None if not sorted_abs_mass_errors else _quantile(sorted_abs_mass_errors, 0.95),
        max_abs_ppm=None if not sorted_abs_mass_errors else max(sorted_abs_mass_errors),
    )

    retention_times = sorted(
        spectrum.retention_time_seconds
        for spectrum in spectra
        if spectrum.retention_time_seconds is not None
    )
    identified_retention_times = sorted(
        spectra_by_id[record.spectrum_id].retention_time_seconds
        for record in psm_records
        if record.spectrum_id in spectra_by_id and spectra_by_id[record.spectrum_id].retention_time_seconds is not None
    )
    retention_summary = QcRetentionTimeSummary(
        spectra_with_retention_time=len(retention_times),
        identified_with_retention_time=len(identified_retention_times),
        min_retention_time_seconds=None if not retention_times else retention_times[0],
        max_retention_time_seconds=None if not retention_times else retention_times[-1],
        span_seconds=None if len(retention_times) < 2 else retention_times[-1] - retention_times[0],
        identified_min_retention_time_seconds=None if not identified_retention_times else identified_retention_times[0],
        identified_max_retention_time_seconds=None if not identified_retention_times else identified_retention_times[-1],
        identified_span_seconds=None if len(identified_retention_times) < 2 else identified_retention_times[-1] - identified_retention_times[0],
        identified_median_retention_time_seconds=None if not identified_retention_times else median(identified_retention_times),
    )

    missed_cleavage_count = sum(_count_missed_cleavages(record.canonical_peptide, active_rule) for record in psm_records)

    contaminant_proteins: Counter[str] = Counter()
    contaminant_psm_count = 0
    for record in psm_records:
        contaminated_refs = [
            reference
            for reference in record.protein_refs
            if _is_contaminant_reference(reference, active_contaminant_policy)
        ]
        if not contaminated_refs:
            continue
        contaminant_psm_count += 1
        for reference in contaminated_refs:
            contaminant_proteins[reference] += 1
    contaminant_summary = QcContaminantSummary(
        contaminant_psm_count=contaminant_psm_count,
        contaminant_psm_fraction=_fraction(contaminant_psm_count, len(psm_records)),
        contaminant_protein_counts=dict(sorted(contaminant_proteins.items())),
    )

    specificity_counts: Counter[QcDigestionSpecificity] = Counter()
    sequence_lookup = protein_sequences or {}
    for record in psm_records:
        specificity = _classify_specificity(
            record.canonical_peptide,
            record.protein_refs,
            sequence_lookup,
            active_rule,
        )
        specificity_counts[specificity] += 1
    digestion_specificity = tuple(
        QcDigestionSpecificityEntry(
            specificity=specificity,
            count=specificity_counts.get(specificity, 0),
            fraction=_fraction(specificity_counts.get(specificity, 0), len(psm_records)),
        )
        for specificity in (
            QcDigestionSpecificity.ENZYMATIC,
            QcDigestionSpecificity.SEMI_SPECIFIC,
            QcDigestionSpecificity.NON_SPECIFIC,
        )
    )

    resolved_run_id = _resolve_run_id(run_id, design_entry)
    return LcmsRunQcReport(
        document_schema=_build_document_schema("lcms_run_qc_report"),
        run_id=resolved_run_id,
        sample_id=design_entry.sample_id if design_entry else None,
        condition=design_entry.condition if design_entry else None,
        replicate=design_entry.replicate if design_entry else None,
        fraction=design_entry.fraction if design_entry else None,
        batch=design_entry.batch if design_entry else None,
        instrument=design_entry.instrument if design_entry else None,
        spectrum_count=len(spectra),
        identified_spectrum_count=len(identified_spectrum_ids & set(spectra_by_id)),
        psm_count=len(psm_records),
        identification_rate=_fraction(len(identified_spectrum_ids & set(spectra_by_id)), len(spectra)),
        spectrum_charge_distribution=_build_charge_distribution(spectrum_charge_counts, len(spectra)),
        identified_charge_distribution=_build_charge_distribution(identified_charge_counts, len(psm_records)),
        mass_error=mass_error_summary,
        retention_time=retention_summary,
        missed_cleavage_count=missed_cleavage_count,
        missed_cleavage_rate=_fraction(missed_cleavage_count, len(psm_records)),
        contaminant_summary=contaminant_summary,
        digestion_specificity=digestion_specificity,
    )


def build_instrument_batch_qc_report(
    run_reports: tuple[LcmsRunQcReport, ...],
    *,
    batch_id: str | None = None,
    instrument: str | None = None,
    identification_rate_floor_ratio: float = 0.85,
    spectrum_count_floor_ratio: float = 0.8,
    median_abs_mass_error_multiplier: float = 2.0,
) -> InstrumentBatchQcReport:
    """Build a typed batch-level QC summary and outlier flags."""
    if not run_reports:
        raise ValueError("batch QC requires at least one run report")

    resolved_batch_id = batch_id
    if resolved_batch_id is None:
        batch_ids = {report.batch for report in run_reports if report.batch}
        resolved_batch_id = next(iter(batch_ids)) if len(batch_ids) == 1 else None
    resolved_instrument = instrument
    if resolved_instrument is None:
        instruments = {report.instrument for report in run_reports if report.instrument}
        resolved_instrument = next(iter(instruments)) if len(instruments) == 1 else None

    spectrum_count_values = [report.spectrum_count for report in run_reports]
    identification_rate_values = [report.identification_rate for report in run_reports]
    median_spectrum_count = float(median(spectrum_count_values))
    median_identification_rate = float(median(identification_rate_values))

    median_abs_mass_error_values = [
        report.mass_error.median_abs_ppm
        for report in run_reports
        if report.mass_error.median_abs_ppm is not None
    ]
    median_abs_mass_error_ppm = (
        None if not median_abs_mass_error_values else float(median(median_abs_mass_error_values))
    )
    identified_median_rt_values = [
        report.retention_time.identified_median_retention_time_seconds
        for report in run_reports
        if report.retention_time.identified_median_retention_time_seconds is not None
    ]
    median_identified_retention_time_seconds = (
        None if not identified_median_rt_values else float(median(identified_median_rt_values))
    )

    run_entries: list[InstrumentBatchQcRunEntry] = []
    outlier_run_ids: list[str] = []
    for report in sorted(run_reports, key=lambda item: item.run_id):
        reasons: list[str] = []
        if median_spectrum_count > 0 and report.spectrum_count < (median_spectrum_count * spectrum_count_floor_ratio):
            reasons.append("low_spectrum_count")
        if median_identification_rate > 0 and report.identification_rate < (median_identification_rate * identification_rate_floor_ratio):
            reasons.append("low_identification_rate")
        if (
            median_abs_mass_error_ppm is not None
            and report.mass_error.median_abs_ppm is not None
            and report.mass_error.median_abs_ppm > max(5.0, median_abs_mass_error_ppm * median_abs_mass_error_multiplier)
        ):
            reasons.append("high_mass_error")
        retention_time_shift_seconds = None
        if (
            median_identified_retention_time_seconds is not None
            and report.retention_time.identified_median_retention_time_seconds is not None
        ):
            retention_time_shift_seconds = (
                report.retention_time.identified_median_retention_time_seconds
                - median_identified_retention_time_seconds
            )
        if reasons:
            outlier_run_ids.append(report.run_id)
        run_entries.append(
            InstrumentBatchQcRunEntry(
                run_id=report.run_id,
                sample_id=report.sample_id,
                batch=report.batch,
                instrument=report.instrument,
                spectrum_count=report.spectrum_count,
                identification_rate=report.identification_rate,
                median_abs_mass_error_ppm=report.mass_error.median_abs_ppm,
                identified_retention_time_span_seconds=report.retention_time.identified_span_seconds,
                retention_time_shift_seconds=retention_time_shift_seconds,
                outlier_reasons=tuple(reasons),
            )
        )

    return InstrumentBatchQcReport(
        document_schema=_build_document_schema("instrument_batch_qc_report"),
        batch_id=resolved_batch_id,
        instrument=resolved_instrument,
        run_count=len(run_reports),
        median_spectrum_count=median_spectrum_count,
        median_identification_rate=median_identification_rate,
        median_abs_mass_error_ppm=median_abs_mass_error_ppm,
        median_identified_retention_time_seconds=median_identified_retention_time_seconds,
        outlier_run_ids=tuple(sorted(outlier_run_ids)),
        runs=tuple(run_entries),
    )
