# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Owned protein-intensity matrix surfaces over peptide-intensity evidence."""

from __future__ import annotations

from enum import StrEnum

from pydantic import ConfigDict, Field

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
from bijux_proteomics.quantification.peptide_intensity_matrix import (
    PeptideIntensityMatrixReport,
    PeptideMatrixGroupingMode,
    PeptideMatrixSourceKind,
    build_peptide_intensity_matrix_from_features,
    build_peptide_intensity_matrix_from_psms,
)
from bijux_proteomics_foundation import JsonModel


class ProteinMatrixTargetKind(StrEnum):
    """Supported protein-level rollup targets."""

    PROTEIN = "protein"
    PROTEIN_GROUP = "protein_group"


class ProteinIntensityMatrixValue(JsonModel):
    """One sample-specific protein-matrix cell."""

    model_config = ConfigDict(extra="forbid")

    sample_id: str = Field(..., min_length=1)
    abundance: float | None = Field(default=None, ge=0.0)
    missing_value_kind: MissingValueKind
    contributing_peptide_count: int = Field(..., ge=0)


class ProteinIntensityMatrixRow(JsonModel):
    """One protein or protein-group row across all samples."""

    model_config = ConfigDict(extra="forbid")

    entity_id: str = Field(..., min_length=1)
    target_kind: ProteinMatrixTargetKind
    protein_refs: tuple[str, ...] = Field(default_factory=tuple)
    peptide_count: int = Field(..., ge=0)
    unique_peptide_count: int = Field(..., ge=0)
    shared_peptide_count: int = Field(..., ge=0)
    contributing_peptides: tuple[str, ...] = Field(default_factory=tuple)
    values: tuple[ProteinIntensityMatrixValue, ...] = Field(default_factory=tuple)


class ProteinIntensityMatrixSummary(JsonModel):
    """Compact summary over one protein-intensity matrix review."""

    model_config = ConfigDict(extra="forbid")

    peptide_row_count: int = Field(..., ge=0)
    protein_row_count: int = Field(..., ge=0)
    sample_count: int = Field(..., ge=0)
    unique_only: bool = False
    observed_cell_count: int = Field(..., ge=0)
    zero_cell_count: int = Field(..., ge=0)
    missing_cell_count: int = Field(..., ge=0)
    filtered_cell_count: int = Field(..., ge=0)


class ProteinIntensityMatrixReport(JsonModel):
    """Owned protein-by-sample intensity matrix with explicit peptide rollup policy."""

    model_config = ConfigDict(extra="forbid")

    source_kind: PeptideMatrixSourceKind
    grouping_mode: PeptideMatrixGroupingMode
    target_kind: ProteinMatrixTargetKind
    separate_charge_states: bool = False
    aggregation_method: QuantRollupMethod
    unique_only: bool = False
    sample_ids: tuple[str, ...] = Field(default_factory=tuple)
    rows: tuple[ProteinIntensityMatrixRow, ...] = Field(default_factory=tuple)
    missing_summary: MissingValueSummaryReport
    summary: ProteinIntensityMatrixSummary
    note: str = Field(..., min_length=1)


def build_protein_intensity_matrix_from_peptides(
    peptide_matrix: PeptideIntensityMatrixReport,
    *,
    target_kind: ProteinMatrixTargetKind = ProteinMatrixTargetKind.PROTEIN,
    aggregation_method: QuantRollupMethod = QuantRollupMethod.SUM,
    unique_only: bool = False,
    top_n: int = 3,
) -> ProteinIntensityMatrixReport:
    """Roll one peptide-intensity matrix up to protein or protein-group targets."""
    if top_n < 1:
        raise ValueError("top_n must be at least 1")

    target_peptides: dict[str, list[tuple[ProteinIntensityMatrixValue, str, bool]]] = {}
    target_refs: dict[str, tuple[str, ...]] = {}

    for peptide_row in peptide_matrix.rows:
        is_unique = len(peptide_row.protein_refs) == 1
        if unique_only and not is_unique:
            continue
        if not peptide_row.protein_refs:
            continue
        target_ids: tuple[str, ...]
        if target_kind is ProteinMatrixTargetKind.PROTEIN:
            target_ids = peptide_row.protein_refs
        else:
            target_ids = (";".join(peptide_row.protein_refs),)
        for target_id in target_ids:
            target_refs.setdefault(
                target_id,
                peptide_row.protein_refs
                if target_kind is ProteinMatrixTargetKind.PROTEIN_GROUP
                else (target_id,),
            )
            target_peptides.setdefault(target_id, [])
            for value in peptide_row.values:
                target_peptides[target_id].append(
                    (
                        ProteinIntensityMatrixValue(
                            sample_id=value.sample_id,
                            abundance=value.abundance,
                            missing_value_kind=value.missing_value_kind,
                            contributing_peptide_count=1,
                        ),
                        peptide_row.entity_id,
                        is_unique,
                    )
                )

    rows: list[ProteinIntensityMatrixRow] = []
    missing_entries: list[MissingValueSummaryEntry] = []
    observed_cell_count = 0
    zero_cell_count = 0
    missing_cell_count = 0
    filtered_cell_count = 0
    ordered_target_ids = tuple(sorted(target_peptides))

    grouped_lookup: dict[tuple[str, str], list[tuple[ProteinIntensityMatrixValue, str, bool]]] = {}
    for target_id, entries in target_peptides.items():
        for value, peptide_id, is_unique in entries:
            grouped_lookup.setdefault((target_id, value.sample_id), []).append(
                (value, peptide_id, is_unique)
            )

    for sample_id in peptide_matrix.sample_ids:
        observed = 0
        zero = 0
        not_observed = 0
        filtered = 0
        for target_id in ordered_target_ids:
            missing_kind = _aggregate_missing_kind(
                tuple(
                    entry.missing_value_kind
                    for entry, _, _ in grouped_lookup.get((target_id, sample_id), ())
                )
                or (MissingValueKind.NOT_OBSERVED,)
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

    for target_id in ordered_target_ids:
        target_rows = grouped_lookup
        protein_refs = target_refs[target_id]
        peptide_ids = sorted(
            {
                peptide_id
                for _, peptide_id, _ in target_peptides[target_id]
            }
        )
        unique_peptide_ids = sorted(
            {
                peptide_id
                for _, peptide_id, is_unique in target_peptides[target_id]
                if is_unique
            }
        )
        shared_peptide_ids = sorted(
            {
                peptide_id
                for _, peptide_id, is_unique in target_peptides[target_id]
                if not is_unique
            }
        )
        values: list[ProteinIntensityMatrixValue] = []
        for sample_id in peptide_matrix.sample_ids:
            entries = target_rows.get((target_id, sample_id), ())
            missing_kind = _aggregate_missing_kind(
                tuple(entry.missing_value_kind for entry, _, _ in entries)
                or (MissingValueKind.NOT_OBSERVED,)
            )
            observed_values = tuple(
                entry.abundance
                for entry, _, _ in entries
                if entry.abundance is not None
                and entry.missing_value_kind
                in (MissingValueKind.OBSERVED, MissingValueKind.ZERO)
            )
            abundance: float | None = None
            if observed_values:
                abundance = _aggregate_abundance(
                    tuple(float(value) for value in observed_values),
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
                ProteinIntensityMatrixValue(
                    sample_id=sample_id,
                    abundance=abundance,
                    missing_value_kind=missing_kind,
                    contributing_peptide_count=len(
                        {
                            peptide_id
                            for _, peptide_id, _ in entries
                        }
                    ),
                )
            )
        rows.append(
            ProteinIntensityMatrixRow(
                entity_id=target_id,
                target_kind=target_kind,
                protein_refs=protein_refs,
                peptide_count=len(peptide_ids),
                unique_peptide_count=len(unique_peptide_ids),
                shared_peptide_count=len(shared_peptide_ids),
                contributing_peptides=tuple(peptide_ids),
                values=tuple(values),
            )
        )

    note = (
        "protein matrix rolls peptide intensities up through one explicit policy "
        "while preserving peptide counts, unique-versus-shared burden, and per-sample missingness"
    )
    return ProteinIntensityMatrixReport(
        source_kind=peptide_matrix.source_kind,
        grouping_mode=peptide_matrix.grouping_mode,
        target_kind=target_kind,
        separate_charge_states=peptide_matrix.separate_charge_states,
        aggregation_method=aggregation_method,
        unique_only=unique_only,
        sample_ids=peptide_matrix.sample_ids,
        rows=tuple(rows),
        missing_summary=MissingValueSummaryReport(
            entity_level=QuantEntityLevel.PROTEIN,
            policy=MissingValueSummaryPolicy(),
            entries=tuple(missing_entries),
            included_entity_ids=ordered_target_ids,
            excluded_entity_ids=(),
        ),
        summary=ProteinIntensityMatrixSummary(
            peptide_row_count=len(peptide_matrix.rows),
            protein_row_count=len(rows),
            sample_count=len(peptide_matrix.sample_ids),
            unique_only=unique_only,
            observed_cell_count=observed_cell_count,
            zero_cell_count=zero_cell_count,
            missing_cell_count=missing_cell_count,
            filtered_cell_count=filtered_cell_count,
        ),
        note=note,
    )


def build_protein_intensity_matrix_from_features(
    records: tuple[Ms1FeatureRecord, ...],
    *,
    grouping_mode: PeptideMatrixGroupingMode = PeptideMatrixGroupingMode.MODIFIED_PEPTIDE,
    separate_charge_states: bool = False,
    target_kind: ProteinMatrixTargetKind = ProteinMatrixTargetKind.PROTEIN,
    aggregation_method: QuantRollupMethod = QuantRollupMethod.SUM,
    unique_only: bool = False,
    top_n: int = 3,
) -> ProteinIntensityMatrixReport:
    """Build one protein-intensity matrix from precursor or feature-table records."""
    peptide_matrix = build_peptide_intensity_matrix_from_features(
        records,
        grouping_mode=grouping_mode,
        separate_charge_states=separate_charge_states,
        aggregation_method=aggregation_method,
        top_n=top_n,
    )
    return build_protein_intensity_matrix_from_peptides(
        peptide_matrix,
        target_kind=target_kind,
        aggregation_method=aggregation_method,
        unique_only=unique_only,
        top_n=top_n,
    )


def build_protein_intensity_matrix_from_psms(
    records: tuple[PsmRecord, ...],
    *,
    grouping_mode: PeptideMatrixGroupingMode = PeptideMatrixGroupingMode.MODIFIED_PEPTIDE,
    separate_charge_states: bool = False,
    target_kind: ProteinMatrixTargetKind = ProteinMatrixTargetKind.PROTEIN,
    aggregation_method: QuantRollupMethod = QuantRollupMethod.SUM,
    unique_only: bool = False,
    top_n: int = 3,
) -> ProteinIntensityMatrixReport:
    """Build one protein-intensity matrix from intensity-bearing canonical PSM rows."""
    peptide_matrix = build_peptide_intensity_matrix_from_psms(
        records,
        grouping_mode=grouping_mode,
        separate_charge_states=separate_charge_states,
        aggregation_method=aggregation_method,
        top_n=top_n,
    )
    return build_protein_intensity_matrix_from_peptides(
        peptide_matrix,
        target_kind=target_kind,
        aggregation_method=aggregation_method,
        unique_only=unique_only,
        top_n=top_n,
    )


def render_protein_intensity_matrix_summary_tsv(
    report: ProteinIntensityMatrixReport,
) -> str:
    """Render one compact protein-matrix summary as TSV."""
    header = (
        "source_kind",
        "grouping_mode",
        "target_kind",
        "separate_charge_states",
        "aggregation_method",
        "unique_only",
        "peptide_row_count",
        "protein_row_count",
        "sample_count",
        "observed_cell_count",
        "zero_cell_count",
        "missing_cell_count",
        "filtered_cell_count",
        "note",
    )
    row = (
        report.source_kind.value,
        report.grouping_mode.value,
        report.target_kind.value,
        str(report.separate_charge_states).lower(),
        report.aggregation_method.value,
        str(report.unique_only).lower(),
        str(report.summary.peptide_row_count),
        str(report.summary.protein_row_count),
        str(report.summary.sample_count),
        str(report.summary.observed_cell_count),
        str(report.summary.zero_cell_count),
        str(report.summary.missing_cell_count),
        str(report.summary.filtered_cell_count),
        report.note,
    )
    return "\t".join(header) + "\n" + "\t".join(row) + "\n"


def render_protein_intensity_matrix_tsv(report: ProteinIntensityMatrixReport) -> str:
    """Render the protein-by-sample intensity matrix as one wide TSV."""
    header = [
        "entity_id",
        "target_kind",
        "protein_refs",
        "peptide_count",
        "unique_peptide_count",
        "shared_peptide_count",
        "contributing_peptides",
    ]
    header.extend(report.sample_ids)
    rows = ["\t".join(header)]
    for row in report.rows:
        lookup = {value.sample_id: value for value in row.values}
        matrix_values = []
        for sample_id in report.sample_ids:
            value = lookup[sample_id]
            matrix_values.append("" if value.abundance is None else f"{value.abundance:g}")
        rows.append(
            "\t".join(
                (
                    row.entity_id,
                    row.target_kind.value,
                    ";".join(row.protein_refs),
                    str(row.peptide_count),
                    str(row.unique_peptide_count),
                    str(row.shared_peptide_count),
                    ";".join(row.contributing_peptides),
                    *matrix_values,
                )
            )
        )
    return "\n".join(rows) + "\n"


def render_protein_intensity_missingness_tsv(
    report: ProteinIntensityMatrixReport,
) -> str:
    """Render one per-sample missingness ledger for a protein matrix."""
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


def _aggregate_missing_kind(kinds: tuple[MissingValueKind, ...]) -> MissingValueKind:
    if any(kind in (MissingValueKind.OBSERVED, MissingValueKind.ZERO) for kind in kinds):
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
