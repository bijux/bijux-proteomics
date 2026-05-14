# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Owned peptide-intensity matrix surfaces over feature and PSM evidence."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from pydantic import ConfigDict, Field

from bijux_proteomics.chemistry import parse_modified_peptide
from bijux_proteomics.identification import PsmRecord
from bijux_proteomics.quantification.contracts import (
    MissingValueKind,
    MissingValueSummaryEntry,
    MissingValueSummaryPolicy,
    MissingValueSummaryReport,
    Ms1FeatureRecord,
    QuantEntityLevel,
    QuantRollupMethod,
)
from bijux_proteomics_foundation import JsonModel


class PeptideMatrixSourceKind(StrEnum):
    """Supported source-record families for peptide-matrix construction."""

    FEATURE = "feature"
    PSM = "psm"


class PeptideMatrixGroupingMode(StrEnum):
    """Stable peptide grouping policies for intensity-matrix review."""

    PEPTIDE_SEQUENCE = "peptide_sequence"
    MODIFIED_PEPTIDE = "modified_peptide"


class PeptideIntensityMatrixValue(JsonModel):
    """One sample-specific peptide-matrix cell."""

    model_config = ConfigDict(extra="forbid")

    sample_id: str = Field(..., min_length=1)
    abundance: float | None = Field(default=None, ge=0.0)
    missing_value_kind: MissingValueKind
    source_record_count: int = Field(..., ge=0)


class PeptideIntensityMatrixRow(JsonModel):
    """One peptide row across all samples in a reviewer-facing matrix."""

    model_config = ConfigDict(extra="forbid")

    entity_id: str = Field(..., min_length=1)
    peptide_sequence: str = Field(..., min_length=1)
    modified_peptides: tuple[str, ...] = Field(default_factory=tuple)
    charge_states: tuple[int, ...] = Field(default_factory=tuple)
    protein_refs: tuple[str, ...] = Field(default_factory=tuple)
    values: tuple[PeptideIntensityMatrixValue, ...] = Field(default_factory=tuple)


class PeptideIntensityMatrixSummary(JsonModel):
    """Compact summary over one peptide-intensity matrix review."""

    model_config = ConfigDict(extra="forbid")

    accepted_source_record_count: int = Field(..., ge=0)
    skipped_source_record_count: int = Field(..., ge=0)
    sample_count: int = Field(..., ge=0)
    peptide_row_count: int = Field(..., ge=0)
    observed_cell_count: int = Field(..., ge=0)
    zero_cell_count: int = Field(..., ge=0)
    missing_cell_count: int = Field(..., ge=0)
    filtered_cell_count: int = Field(..., ge=0)


class PeptideIntensityMatrixReport(JsonModel):
    """Owned peptide-by-sample matrix with explicit grouping and missingness."""

    model_config = ConfigDict(extra="forbid")

    source_kind: PeptideMatrixSourceKind
    grouping_mode: PeptideMatrixGroupingMode
    separate_charge_states: bool = False
    aggregation_method: QuantRollupMethod
    sample_ids: tuple[str, ...] = Field(default_factory=tuple)
    rows: tuple[PeptideIntensityMatrixRow, ...] = Field(default_factory=tuple)
    missing_summary: MissingValueSummaryReport
    summary: PeptideIntensityMatrixSummary
    note: str = Field(..., min_length=1)


@dataclass(frozen=True)
class _PeptideObservation:
    sample_id: str
    peptide_sequence: str
    modified_peptide: str
    charge_state: int | None
    intensity: float | None
    missing_value_kind: MissingValueKind
    protein_refs: tuple[str, ...]


def build_peptide_intensity_matrix_from_features(
    records: tuple[Ms1FeatureRecord, ...],
    *,
    grouping_mode: PeptideMatrixGroupingMode = (
        PeptideMatrixGroupingMode.MODIFIED_PEPTIDE
    ),
    separate_charge_states: bool = False,
    aggregation_method: QuantRollupMethod = QuantRollupMethod.SUM,
    top_n: int = 3,
) -> PeptideIntensityMatrixReport:
    """Build one peptide-intensity matrix from precursor or feature-table records."""
    observations = tuple(_feature_observation(record) for record in records)
    return _build_peptide_intensity_matrix_report(
        observations,
        source_kind=PeptideMatrixSourceKind.FEATURE,
        grouping_mode=grouping_mode,
        separate_charge_states=separate_charge_states,
        aggregation_method=aggregation_method,
        top_n=top_n,
        accepted_source_record_count=len(records),
        skipped_source_record_count=0,
        sample_ids=tuple(record.sample_id for record in records),
    )


def build_peptide_intensity_matrix_from_psms(
    records: tuple[PsmRecord, ...],
    *,
    grouping_mode: PeptideMatrixGroupingMode = (
        PeptideMatrixGroupingMode.MODIFIED_PEPTIDE
    ),
    separate_charge_states: bool = False,
    aggregation_method: QuantRollupMethod = QuantRollupMethod.SUM,
    top_n: int = 3,
) -> PeptideIntensityMatrixReport:
    """Build one peptide-intensity matrix from intensity-bearing canonical PSM rows."""
    observations: list[_PeptideObservation] = []
    sample_ids: list[str] = []
    skipped = 0
    for record in records:
        if record.run_id is not None:
            sample_ids.append(record.run_id)
        observation = _psm_observation(record)
        if observation is None:
            skipped += 1
            continue
        observations.append(observation)
    return _build_peptide_intensity_matrix_report(
        tuple(observations),
        source_kind=PeptideMatrixSourceKind.PSM,
        grouping_mode=grouping_mode,
        separate_charge_states=separate_charge_states,
        aggregation_method=aggregation_method,
        top_n=top_n,
        accepted_source_record_count=len(observations),
        skipped_source_record_count=skipped,
        sample_ids=tuple(sample_ids),
    )


def render_peptide_intensity_matrix_summary_tsv(
    report: PeptideIntensityMatrixReport,
) -> str:
    """Render one compact peptide-matrix summary as TSV."""
    header = (
        "source_kind",
        "grouping_mode",
        "separate_charge_states",
        "aggregation_method",
        "accepted_source_record_count",
        "skipped_source_record_count",
        "sample_count",
        "peptide_row_count",
        "observed_cell_count",
        "zero_cell_count",
        "missing_cell_count",
        "filtered_cell_count",
        "note",
    )
    row = (
        report.source_kind.value,
        report.grouping_mode.value,
        str(report.separate_charge_states).lower(),
        report.aggregation_method.value,
        str(report.summary.accepted_source_record_count),
        str(report.summary.skipped_source_record_count),
        str(report.summary.sample_count),
        str(report.summary.peptide_row_count),
        str(report.summary.observed_cell_count),
        str(report.summary.zero_cell_count),
        str(report.summary.missing_cell_count),
        str(report.summary.filtered_cell_count),
        report.note,
    )
    return "\t".join(header) + "\n" + "\t".join(row) + "\n"


def render_peptide_intensity_matrix_tsv(report: PeptideIntensityMatrixReport) -> str:
    """Render the peptide-by-sample intensity matrix as one wide TSV."""
    header = [
        "entity_id",
        "peptide_sequence",
        "modified_peptides",
        "charge_states",
        "protein_refs",
    ]
    header.extend(report.sample_ids)
    rows = ["\t".join(header)]
    for row in report.rows:
        value_lookup = {value.sample_id: value for value in row.values}
        matrix_values = []
        for sample_id in report.sample_ids:
            value = value_lookup[sample_id]
            if value.abundance is None:
                matrix_values.append("")
            else:
                matrix_values.append(f"{value.abundance:g}")
        rows.append(
            "\t".join(
                (
                    row.entity_id,
                    row.peptide_sequence,
                    ";".join(row.modified_peptides),
                    ";".join(str(charge) for charge in row.charge_states),
                    ";".join(row.protein_refs),
                    *matrix_values,
                )
            )
        )
    return "\n".join(rows) + "\n"


def render_peptide_intensity_missingness_tsv(
    report: PeptideIntensityMatrixReport,
) -> str:
    """Render one per-sample missingness ledger for a peptide matrix."""
    header = (
        "sample_id",
        "observed_count",
        "zero_count",
        "not_observed_count",
        "filtered_count",
    )
    rows = ["\t".join(header)]
    for entry in report.missing_summary.entries:
        rows.append(
            "\t".join(
                (
                    entry.sample_id,
                    str(entry.observed_count),
                    str(entry.zero_count),
                    str(entry.not_observed_count),
                    str(entry.filtered_count),
                )
            )
        )
    return "\n".join(rows) + "\n"


def _feature_observation(record: Ms1FeatureRecord) -> _PeptideObservation:
    parsed = parse_modified_peptide(record.canonical_peptide)
    return _PeptideObservation(
        sample_id=record.sample_id,
        peptide_sequence=parsed.sequence,
        modified_peptide=parsed.canonical_notation,
        charge_state=record.charge,
        intensity=record.intensity,
        missing_value_kind=record.missing_value_kind,
        protein_refs=record.protein_refs,
    )


def _psm_observation(record: PsmRecord) -> _PeptideObservation | None:
    if record.run_id is None or record.intensity is None:
        return None
    peptide_sequence = record.peptide_sequence
    if peptide_sequence is None:
        peptide_sequence = parse_modified_peptide(record.canonical_peptide).sequence
    modified_peptide = record.modified_peptide or record.canonical_peptide
    missing_value_kind = (
        MissingValueKind.ZERO if record.intensity == 0.0 else MissingValueKind.OBSERVED
    )
    return _PeptideObservation(
        sample_id=record.run_id,
        peptide_sequence=peptide_sequence,
        modified_peptide=modified_peptide,
        charge_state=record.charge,
        intensity=record.intensity,
        missing_value_kind=missing_value_kind,
        protein_refs=record.protein_refs,
    )


def _build_peptide_intensity_matrix_report(
    observations: tuple[_PeptideObservation, ...],
    *,
    source_kind: PeptideMatrixSourceKind,
    grouping_mode: PeptideMatrixGroupingMode,
    separate_charge_states: bool,
    aggregation_method: QuantRollupMethod,
    top_n: int,
    accepted_source_record_count: int,
    skipped_source_record_count: int,
    sample_ids: tuple[str, ...],
) -> PeptideIntensityMatrixReport:
    if top_n < 1:
        raise ValueError("top_n must be at least 1")

    ordered_sample_ids = tuple(
        sorted({sample_id for sample_id in sample_ids if sample_id})
    )
    grouped_values: dict[tuple[str, str], list[float]] = {}
    grouped_kinds: dict[tuple[str, str], list[MissingValueKind]] = {}
    grouped_counts: dict[tuple[str, str], int] = {}
    row_sequences: dict[str, str] = {}
    row_modified_peptides: dict[str, set[str]] = {}
    row_charge_states: dict[str, set[int]] = {}
    row_protein_refs: dict[str, set[str]] = {}

    for observation in observations:
        entity_id = _entity_id_for_observation(
            observation,
            grouping_mode=grouping_mode,
            separate_charge_states=separate_charge_states,
        )
        key = (entity_id, observation.sample_id)
        grouped_kinds.setdefault(key, []).append(observation.missing_value_kind)
        row_sequences.setdefault(entity_id, observation.peptide_sequence)
        row_modified_peptides.setdefault(entity_id, set()).add(
            observation.modified_peptide
        )
        row_protein_refs.setdefault(entity_id, set()).update(observation.protein_refs)
        if observation.charge_state is not None:
            row_charge_states.setdefault(entity_id, set()).add(observation.charge_state)
        if observation.missing_value_kind in (
            MissingValueKind.OBSERVED,
            MissingValueKind.ZERO,
        ):
            grouped_values.setdefault(key, []).append(
                float(observation.intensity or 0.0)
            )
            grouped_counts[key] = grouped_counts.get(key, 0) + 1

    ordered_entity_ids = tuple(sorted(row_sequences))
    rows: list[PeptideIntensityMatrixRow] = []
    missing_entries: list[MissingValueSummaryEntry] = []
    observed_cell_count = 0
    zero_cell_count = 0
    missing_cell_count = 0
    filtered_cell_count = 0

    for sample_id in ordered_sample_ids:
        observed = 0
        zero = 0
        not_observed = 0
        filtered = 0
        for entity_id in ordered_entity_ids:
            missing_kind = _aggregate_missing_kind(
                tuple(
                    grouped_kinds.get(
                        (entity_id, sample_id),
                        (MissingValueKind.NOT_OBSERVED,),
                    )
                )
            )
            if missing_kind is MissingValueKind.OBSERVED:
                observed += 1
            elif missing_kind is MissingValueKind.ZERO:
                zero += 1
            elif missing_kind is MissingValueKind.FILTERED:
                filtered += 1
            else:
                not_observed += 1
        missing_entries.append(
            MissingValueSummaryEntry(
                sample_id=sample_id,
                observed_count=observed,
                zero_count=zero,
                not_observed_count=not_observed,
                filtered_count=filtered,
            )
        )

    for entity_id in ordered_entity_ids:
        values: list[PeptideIntensityMatrixValue] = []
        for sample_id in ordered_sample_ids:
            key = (entity_id, sample_id)
            missing_kind = _aggregate_missing_kind(
                tuple(
                    grouped_kinds.get(
                        key,
                        (MissingValueKind.NOT_OBSERVED,),
                    )
                )
            )
            observed_values = tuple(grouped_values.get(key, ()))
            abundance: float | None = None
            if observed_values:
                abundance = _aggregate_abundance(
                    observed_values,
                    aggregation_method=aggregation_method,
                    top_n=top_n,
                )
                if abundance == 0.0 and missing_kind is not MissingValueKind.OBSERVED:
                    missing_kind = MissingValueKind.ZERO
            if missing_kind is MissingValueKind.OBSERVED:
                observed_cell_count += 1
            elif missing_kind is MissingValueKind.ZERO:
                zero_cell_count += 1
            elif missing_kind is MissingValueKind.FILTERED:
                filtered_cell_count += 1
            else:
                missing_cell_count += 1
            values.append(
                PeptideIntensityMatrixValue(
                    sample_id=sample_id,
                    abundance=abundance,
                    missing_value_kind=missing_kind,
                    source_record_count=grouped_counts.get(key, 0),
                )
            )
        rows.append(
            PeptideIntensityMatrixRow(
                entity_id=entity_id,
                peptide_sequence=row_sequences[entity_id],
                modified_peptides=tuple(
                    sorted(row_modified_peptides.get(entity_id, ()))
                ),
                charge_states=tuple(sorted(row_charge_states.get(entity_id, ()))),
                protein_refs=tuple(sorted(row_protein_refs.get(entity_id, ()))),
                values=tuple(values),
            )
        )

    note = (
        "peptide matrix preserves modified-peptide grouping, optional charge separation, "
        "aggregated source evidence, and explicit missingness per sample"
    )
    return PeptideIntensityMatrixReport(
        source_kind=source_kind,
        grouping_mode=grouping_mode,
        separate_charge_states=separate_charge_states,
        aggregation_method=aggregation_method,
        sample_ids=ordered_sample_ids,
        rows=tuple(rows),
        missing_summary=MissingValueSummaryReport(
            entity_level=QuantEntityLevel.PEPTIDE,
            policy=MissingValueSummaryPolicy(),
            entries=tuple(missing_entries),
            included_entity_ids=ordered_entity_ids,
            excluded_entity_ids=(),
        ),
        summary=PeptideIntensityMatrixSummary(
            accepted_source_record_count=accepted_source_record_count,
            skipped_source_record_count=skipped_source_record_count,
            sample_count=len(ordered_sample_ids),
            peptide_row_count=len(rows),
            observed_cell_count=observed_cell_count,
            zero_cell_count=zero_cell_count,
            missing_cell_count=missing_cell_count,
            filtered_cell_count=filtered_cell_count,
        ),
        note=note,
    )


def _entity_id_for_observation(
    observation: _PeptideObservation,
    *,
    grouping_mode: PeptideMatrixGroupingMode,
    separate_charge_states: bool,
) -> str:
    if grouping_mode is PeptideMatrixGroupingMode.PEPTIDE_SEQUENCE:
        base = observation.peptide_sequence
    else:
        base = observation.modified_peptide
    if not separate_charge_states or observation.charge_state is None:
        return base
    return f"{base}/z{observation.charge_state}"


def _aggregate_missing_kind(kinds: tuple[MissingValueKind, ...]) -> MissingValueKind:
    if any(
        kind in (MissingValueKind.OBSERVED, MissingValueKind.ZERO) for kind in kinds
    ):
        if any(kind is MissingValueKind.ZERO for kind in kinds) and not any(
            kind is MissingValueKind.OBSERVED for kind in kinds
        ):
            return MissingValueKind.ZERO
        return MissingValueKind.OBSERVED
    if any(kind is MissingValueKind.FILTERED for kind in kinds):
        return MissingValueKind.FILTERED
    return MissingValueKind.NOT_OBSERVED


def _aggregate_abundance(
    values: tuple[float, ...],
    *,
    aggregation_method: QuantRollupMethod,
    top_n: int,
) -> float:
    if aggregation_method is QuantRollupMethod.SUM:
        return float(sum(values))
    if aggregation_method is QuantRollupMethod.MEDIAN:
        ordered = sorted(values)
        midpoint = len(ordered) // 2
        if len(ordered) % 2 == 1:
            return float(ordered[midpoint])
        return float((ordered[midpoint - 1] + ordered[midpoint]) / 2.0)
    ordered = sorted(values, reverse=True)
    return float(sum(ordered[:top_n]))
