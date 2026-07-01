# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""LC-MS run quality-control and batch-diagnostic contracts."""

from __future__ import annotations

from collections import Counter
from statistics import median

from bijux_proteomics.chemistry.mass import calculate_peptide_mz
from bijux_proteomics.identification import PsmRecord
from bijux_proteomics.identification.contaminant_evidence import (
    build_contaminant_evidence_report,
)
from bijux_proteomics.io.formats import ExperimentalDesignEntry
from bijux_proteomics.io.spectra import SpectrumModel, calculate_precursor_mass_error
from bijux_proteomics.lab.qc.assessment import build_run_anomalies
from bijux_proteomics.lab.qc.models import (
    LcmsRunQcReport,
    QcChargeStateEntry,
    QcContaminantPolicy,
    QcContaminantSummary,
    QcDigestionSpecificity,
    QcDigestionSpecificityEntry,
    QcIdentificationSummary,
    QcInstrumentSummary,
    QcMassErrorSummary,
    QcQuantSummary,
    QcRetentionTimeSummary,
)
from bijux_proteomics.lab.qc.support import (
    build_document_schema,
    fraction,
    quantile,
    resolve_run_id,
)
from bijux_proteomics.quantification.contracts import (
    LabelFreeQuantTable,
    MissingValueKind,
)
from bijux_proteomics.sequences.digestion import (
    ProteaseCleavageMode,
    ProteaseRule,
    get_protease_rule,
)
from bijux_proteomics.sequences.digestion import (
    count_missed_cleavages as count_sequence_missed_cleavages,
)


def _build_charge_distribution(
    counts: Counter[str], total: int
) -> tuple[QcChargeStateEntry, ...]:
    return tuple(
        QcChargeStateEntry(
            charge_label=label, count=count, fraction=fraction(count, total)
        )
        for label, count in sorted(counts.items(), key=lambda item: item[0])
    )


def _build_quant_summary(
    table: LabelFreeQuantTable | None,
    *,
    sample_id: str | None,
) -> QcQuantSummary | None:
    if table is None or sample_id is None or sample_id not in table.sample_ids:
        return None
    sample_values = [value for value in table.values if value.sample_id == sample_id]
    if not sample_values:
        return None
    observed_values = [
        float(value.abundance)
        for value in sample_values
        if value.abundance is not None
        and value.missing_value_kind
        in (MissingValueKind.OBSERVED, MissingValueKind.ZERO)
    ]
    zero_count = sum(
        1
        for value in sample_values
        if value.missing_value_kind is MissingValueKind.ZERO
    )
    filtered_count = sum(
        1
        for value in sample_values
        if value.missing_value_kind is MissingValueKind.FILTERED
    )
    not_observed_count = sum(
        1
        for value in sample_values
        if value.missing_value_kind is MissingValueKind.NOT_OBSERVED
    )
    observed_count = sum(
        1
        for value in sample_values
        if value.missing_value_kind
        in (MissingValueKind.OBSERVED, MissingValueKind.ZERO)
    )
    total_count = len(sample_values)
    return QcQuantSummary(
        sample_id=sample_id,
        entity_level=table.entity_level,
        observed_entity_count=observed_count,
        zero_entity_count=zero_count,
        filtered_entity_count=filtered_count,
        not_observed_entity_count=not_observed_count,
        total_entity_count=total_count,
        observed_fraction=fraction(observed_count, total_count),
        missing_fraction=fraction(filtered_count + not_observed_count, total_count),
        median_observed_abundance=None
        if not observed_values
        else median(observed_values),
        normalization_method=table.normalization_method.value,
    )


def _is_contaminant_reference(reference: str, policy: QcContaminantPolicy) -> bool:
    normalized = reference.strip().upper()
    return normalized.startswith(
        tuple(prefix.upper() for prefix in policy.prefixes)
    ) or any(token.upper() in normalized for token in policy.substrings)


def _count_missed_cleavages(sequence: str, rule: ProteaseRule) -> int:
    return count_sequence_missed_cleavages(sequence, rule)


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
            left_valid = (
                left_residue in rule.cleavage_residues
                and first_peptide_residue not in rule.blocked_by_next
            )
        if peptide_end == sequence_length:
            right_valid = True
        else:
            last_peptide_residue = protein_sequence[peptide_end - 1]
            right_neighbor = protein_sequence[peptide_end]
            right_valid = (
                last_peptide_residue in rule.cleavage_residues
                and right_neighbor not in rule.blocked_by_next
            )
        return left_valid, right_valid

    if peptide_start == 1:
        left_valid = True
    else:
        left_neighbor = protein_sequence[peptide_start - 2]
        first_peptide_residue = protein_sequence[peptide_start - 1]
        left_valid = (
            first_peptide_residue in rule.cleavage_residues
            and left_neighbor not in rule.blocked_by_previous
        )
    if peptide_end == sequence_length:
        right_valid = True
    else:
        last_peptide_residue = protein_sequence[peptide_end - 1]
        right_neighbor = protein_sequence[peptide_end]
        right_valid = (
            right_neighbor in rule.cleavage_residues
            and last_peptide_residue not in rule.blocked_by_previous
        )
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
    quant_table: LabelFreeQuantTable | None = None,
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
        label = (
            "unknown"
            if spectrum.precursor_charge is None
            else str(spectrum.precursor_charge)
        )
        spectrum_charge_counts[label] += 1

    identified_charge_counts: Counter[str] = Counter(
        str(record.charge) for record in psm_records
    )

    mass_errors_ppm: list[float] = []
    for record in psm_records:
        candidate_spectrum = spectra_by_id.get(record.spectrum_id)
        if candidate_spectrum is None:
            continue
        spectrum = candidate_spectrum
        theoretical_mz = calculate_peptide_mz(record.peptide, charge=record.charge)
        mass_error = calculate_precursor_mass_error(
            observed_mz=spectrum.precursor_mz,
            theoretical_mz=theoretical_mz,
        )
        mass_errors_ppm.append(mass_error.delta_ppm)

    sorted_abs_mass_errors = sorted(abs(value) for value in mass_errors_ppm)
    mass_error_summary = QcMassErrorSummary(
        matched_psm_count=len(mass_errors_ppm),
        mean_ppm=None
        if not mass_errors_ppm
        else sum(mass_errors_ppm) / len(mass_errors_ppm),
        median_ppm=None if not mass_errors_ppm else median(mass_errors_ppm),
        median_abs_ppm=None
        if not sorted_abs_mass_errors
        else median(sorted_abs_mass_errors),
        p95_abs_ppm=None
        if not sorted_abs_mass_errors
        else quantile(sorted_abs_mass_errors, 0.95),
        max_abs_ppm=None if not sorted_abs_mass_errors else max(sorted_abs_mass_errors),
    )

    retention_times = sorted(
        spectrum.retention_time_seconds
        for spectrum in spectra
        if spectrum.retention_time_seconds is not None
    )
    identified_retention_times: list[float] = sorted(
        retention_time
        for record in psm_records
        for spectrum in [spectra_by_id.get(record.spectrum_id)]
        if spectrum is not None
        for retention_time in [spectrum.retention_time_seconds]
        if retention_time is not None
    )
    retention_summary = QcRetentionTimeSummary(
        spectra_with_retention_time=len(retention_times),
        identified_with_retention_time=len(identified_retention_times),
        min_retention_time_seconds=None if not retention_times else retention_times[0],
        max_retention_time_seconds=None if not retention_times else retention_times[-1],
        span_seconds=None
        if len(retention_times) < 2
        else retention_times[-1] - retention_times[0],
        identified_min_retention_time_seconds=None
        if not identified_retention_times
        else identified_retention_times[0],
        identified_max_retention_time_seconds=None
        if not identified_retention_times
        else identified_retention_times[-1],
        identified_span_seconds=None
        if len(identified_retention_times) < 2
        else identified_retention_times[-1] - identified_retention_times[0],
        identified_median_retention_time_seconds=None
        if not identified_retention_times
        else median(identified_retention_times),
    )

    missed_cleavage_count = sum(
        _count_missed_cleavages(record.canonical_peptide, active_rule)
        for record in psm_records
    )
    resolved_run_id = resolve_run_id(run_id, design_entry)
    sample_id = design_entry.sample_id if design_entry else None
    qc_psm_records = tuple(
        record
        if record.run_id
        else record.model_copy(update={"run_id": resolved_run_id})
        for record in psm_records
    )

    contaminant_report = build_contaminant_evidence_report(
        qc_psm_records,
        contaminant_prefixes=active_contaminant_policy.prefixes,
        sample_id_by_run={} if sample_id is None else {resolved_run_id: sample_id},
    )
    run_burden = next(
        (
            entry
            for entry in contaminant_report.burden_entries
            if entry.run_id == resolved_run_id
        ),
        None,
    )
    contaminant_summary = QcContaminantSummary(
        contaminant_psm_count=0
        if run_burden is None
        else run_burden.contaminant_psm_count,
        contaminant_psm_fraction=0.0
        if run_burden is None
        else run_burden.contaminant_psm_fraction,
        contaminant_peptide_count=0
        if run_burden is None
        else run_burden.contaminant_peptide_count,
        contaminant_protein_count=0
        if run_burden is None
        else run_burden.contaminant_protein_count,
        contaminant_intensity=0.0
        if run_burden is None
        else run_burden.contaminant_intensity,
        total_psm_intensity=0.0 if run_burden is None else run_burden.total_intensity,
        contaminant_intensity_fraction=0.0
        if run_burden is None
        else run_burden.contaminant_intensity_fraction,
        contaminant_protein_counts={
            entry.protein_ref: entry.psm_count
            for entry in contaminant_report.protein_entries
        },
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
            fraction=fraction(specificity_counts.get(specificity, 0), len(psm_records)),
        )
        for specificity in (
            QcDigestionSpecificity.ENZYMATIC,
            QcDigestionSpecificity.SEMI_SPECIFIC,
            QcDigestionSpecificity.NON_SPECIFIC,
        )
    )

    instrument_summary = QcInstrumentSummary(
        instrument=design_entry.instrument if design_entry else None,
        spectrum_count=len(spectra),
        spectra_with_precursor_charge=sum(
            1 for spectrum in spectra if spectrum.precursor_charge is not None
        ),
        spectra_with_retention_time=len(retention_times),
        acquisition_span_seconds=retention_summary.span_seconds,
        dominant_charge_label=(
            max(
                spectrum_charge_counts.items(),
                key=lambda item: (item[1], item[0]),
            )[0]
            if spectrum_charge_counts
            else None
        ),
    )
    identified_spectrum_count = len(identified_spectrum_ids & set(spectra_by_id))
    identification_rate = fraction(identified_spectrum_count, len(spectra))
    identification_summary = QcIdentificationSummary(
        identified_spectrum_count=identified_spectrum_count,
        psm_count=len(psm_records),
        identification_rate=identification_rate,
        matched_mass_error_psm_count=len(mass_errors_ppm),
        median_abs_mass_error_ppm=mass_error_summary.median_abs_ppm,
        contaminant_psm_fraction=contaminant_summary.contaminant_psm_fraction,
        missed_cleavage_rate=fraction(missed_cleavage_count, len(psm_records)),
    )
    quant_summary = _build_quant_summary(quant_table, sample_id=sample_id)
    return LcmsRunQcReport(
        document_schema=build_document_schema("lcms_run_qc_report"),
        run_id=resolved_run_id,
        sample_id=sample_id,
        condition=design_entry.condition if design_entry else None,
        replicate=design_entry.replicate if design_entry else None,
        fraction=design_entry.fraction if design_entry else None,
        batch=design_entry.batch if design_entry else None,
        instrument=design_entry.instrument if design_entry else None,
        design_metadata={}
        if design_entry is None
        else dict(sorted(design_entry.metadata.items())),
        instrument_summary=instrument_summary,
        identification_summary=identification_summary,
        quant_summary=quant_summary,
        run_anomalies=build_run_anomalies(
            identification_rate=identification_rate,
            mass_error_summary=mass_error_summary,
            retention_summary=retention_summary,
            quant_summary=quant_summary,
            contaminant_summary=contaminant_summary,
        ),
        spectrum_count=len(spectra),
        identified_spectrum_count=identified_spectrum_count,
        psm_count=len(psm_records),
        identification_rate=identification_rate,
        spectrum_charge_distribution=_build_charge_distribution(
            spectrum_charge_counts, len(spectra)
        ),
        identified_charge_distribution=_build_charge_distribution(
            identified_charge_counts, len(psm_records)
        ),
        mass_error=mass_error_summary,
        retention_time=retention_summary,
        missed_cleavage_count=missed_cleavage_count,
        missed_cleavage_rate=fraction(missed_cleavage_count, len(psm_records)),
        contaminant_summary=contaminant_summary,
        protein_psm_counts=dict(
            sorted(
                Counter(
                    ref for record in psm_records for ref in record.protein_refs
                ).items()
            )
        ),
        digestion_specificity=digestion_specificity,
    )
