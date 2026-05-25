# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Owned peptide-intensity matrix surfaces over feature and PSM evidence."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from pydantic import ConfigDict, Field, model_validator

from bijux_proteomics.chemistry import parse_modified_peptide
from bijux_proteomics.domain.records import (
    MissingValueState,
    QuantEntityKind,
    QuantMatrix as CanonicalQuantMatrix,
    QuantMeasureKind,
    SampleMetadata as CanonicalSampleMetadata,
)
from bijux_proteomics.identification import PsmRecord
from bijux_proteomics.io.stable_outputs import sort_rows_by_fields, sort_strings
from bijux_proteomics.quantification.contracts import (
    MissingValueKind,
    MissingValueSummaryEntry,
    MissingValueSummaryPolicy,
    MissingValueSummaryReport,
    Ms1FeatureRecord,
    PrecursorIntensityRecord,
    QuantEntityLevel,
    QuantRollupMethod,
)
from bijux_proteomics.quantification.matrix.core_matrix import (
    build_numeric_quant_matrix,
)
from bijux_proteomics_foundation import JsonModel


class PeptideMatrixSourceKind(StrEnum):
    """Supported source-record families for peptide-matrix construction."""

    FEATURE = "feature"
    PSM = "psm"
    PRECURSOR = "precursor"


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


class PeptideIntensityAggregationEntry(JsonModel):
    """Explicit duplicate-rollup ledger for one peptide-by-sample matrix cell."""

    model_config = ConfigDict(extra="forbid")

    entity_id: str = Field(..., min_length=1)
    sample_id: str = Field(..., min_length=1)
    peptide_sequence: str = Field(..., min_length=1)
    modified_peptides: tuple[str, ...] = Field(default_factory=tuple)
    charge_states: tuple[int, ...] = Field(default_factory=tuple)
    protein_refs: tuple[str, ...] = Field(default_factory=tuple)
    aggregation_method: QuantRollupMethod
    source_record_ids: tuple[str, ...] = Field(default_factory=tuple)
    source_record_count: int = Field(..., ge=0)
    quantified_record_count: int = Field(..., ge=0)
    observed_source_record_count: int = Field(..., ge=0)
    zero_source_record_count: int = Field(..., ge=0)
    not_observed_source_record_count: int = Field(..., ge=0)
    filtered_source_record_count: int = Field(..., ge=0)
    source_abundances: tuple[float, ...] = Field(default_factory=tuple)
    aggregated_abundance: float | None = Field(default=None, ge=0.0)
    missing_value_kind: MissingValueKind


class PeptideIntensityMatrixReport(JsonModel):
    """Owned peptide-by-sample matrix with explicit grouping and missingness."""

    model_config = ConfigDict(extra="forbid")

    source_kind: PeptideMatrixSourceKind
    grouping_mode: PeptideMatrixGroupingMode
    separate_charge_states: bool = False
    aggregation_method: QuantRollupMethod
    sample_ids: tuple[str, ...] = Field(default_factory=tuple)
    rows: tuple[PeptideIntensityMatrixRow, ...] = Field(default_factory=tuple)
    aggregation_entries: tuple[PeptideIntensityAggregationEntry, ...] = Field(
        default_factory=tuple
    )
    quant_matrix: CanonicalQuantMatrix | None = None
    missing_summary: MissingValueSummaryReport
    summary: PeptideIntensityMatrixSummary
    note: str = Field(..., min_length=1)

    @model_validator(mode="after")
    def _bind_quant_matrix(self) -> PeptideIntensityMatrixReport:
        if self.quant_matrix is None:
            self.quant_matrix = self._build_quant_matrix()
        return self

    def to_quant_matrix(
        self,
        *,
        matrix_id: str = "peptide_intensity_matrix",
        sample_metadata: tuple[CanonicalSampleMetadata, ...] = (),
    ) -> CanonicalQuantMatrix:
        """Convert this reviewer-facing peptide matrix into the canonical matrix."""

        if (
            self.quant_matrix is not None
            and self.quant_matrix.matrix_id == matrix_id
            and (
                not sample_metadata
                or self.quant_matrix.sample_metadata == sample_metadata
            )
        ):
            return self.quant_matrix
        return self._build_quant_matrix(
            matrix_id=matrix_id,
            sample_metadata=sample_metadata,
        )

    def _build_quant_matrix(
        self,
        *,
        matrix_id: str = "peptide_intensity_matrix",
        sample_metadata: tuple[CanonicalSampleMetadata, ...] = (),
    ) -> CanonicalQuantMatrix:
        return build_numeric_quant_matrix(
            matrix_id=matrix_id,
            entity_kind=QuantEntityKind.PEPTIDE,
            measure_kind=QuantMeasureKind.INTENSITY,
            entity_ids=tuple(row.entity_id for row in self.rows),
            sample_ids=self.sample_ids,
            value_lookup={
                (row.entity_id, value.sample_id): value.abundance
                for row in self.rows
                for value in row.values
            },
            missing_state_lookup={
                (row.entity_id, value.sample_id): MissingValueState(
                    value.missing_value_kind.value
                )
                for row in self.rows
                for value in row.values
            },
            support_count_lookup={
                (row.entity_id, value.sample_id): value.source_record_count
                for row in self.rows
                for value in row.values
            },
            row_metadata_lookup={
                row.entity_id: {
                    "peptide_sequence": row.peptide_sequence,
                    "modified_peptides": ";".join(row.modified_peptides),
                    "charge_states": ";".join(
                        str(charge) for charge in row.charge_states
                    ),
                    "protein_refs": ";".join(row.protein_refs),
                }
                for row in self.rows
            },
            sample_metadata=sample_metadata,
            transformation_history=(
                f"source_kind:{self.source_kind.value}",
                f"grouping_mode:{self.grouping_mode.value}",
                f"aggregation_method:{self.aggregation_method.value}",
                f"separate_charge_states:{str(self.separate_charge_states).lower()}",
            ),
            metadata={
                "note": self.note,
                "source_kind": self.source_kind.value,
                "grouping_mode": self.grouping_mode.value,
                "aggregation_method": self.aggregation_method.value,
                "separate_charge_states": str(self.separate_charge_states).lower(),
            },
        )

    @classmethod
    def from_quant_matrix(cls, matrix: CanonicalQuantMatrix) -> PeptideIntensityMatrixReport:
        """Rebuild one peptide matrix report from a canonical peptide matrix."""

        row_metadata_lookup = {
            entity_id: matrix.row_metadata[index]
            for index, entity_id in enumerate(matrix.entity_ids)
        }
        rows: list[PeptideIntensityMatrixRow] = []
        for row_index, entity_id in enumerate(matrix.entity_ids):
            metadata = row_metadata_lookup.get(entity_id, {})
            rows.append(
                PeptideIntensityMatrixRow(
                    entity_id=entity_id,
                    peptide_sequence=metadata.get("peptide_sequence", entity_id),
                    modified_peptides=tuple(
                        token
                        for token in metadata.get("modified_peptides", "").split(";")
                        if token
                    ),
                    charge_states=tuple(
                        int(token)
                        for token in metadata.get("charge_states", "").split(";")
                        if token
                    ),
                    protein_refs=tuple(
                        token
                        for token in metadata.get("protein_refs", "").split(";")
                        if token
                    ),
                    values=tuple(
                        PeptideIntensityMatrixValue(
                            sample_id=sample_id,
                            abundance=matrix.values[row_index][column_index],
                            missing_value_kind=MissingValueKind(
                                matrix.missing_value_states[row_index][column_index].value
                            ),
                            source_record_count=(
                                0
                                if not matrix.support_counts
                                else matrix.support_counts[row_index][column_index]
                            ),
                        )
                        for column_index, sample_id in enumerate(matrix.sample_ids)
                    ),
                )
            )
        aggregation_entries: list[PeptideIntensityAggregationEntry] = []
        for row in rows:
            for value in row.values:
                aggregation_entries.append(
                    PeptideIntensityAggregationEntry(
                        entity_id=row.entity_id,
                        sample_id=value.sample_id,
                        peptide_sequence=row.peptide_sequence,
                        modified_peptides=row.modified_peptides,
                        charge_states=row.charge_states,
                        protein_refs=row.protein_refs,
                        aggregation_method=QuantRollupMethod(
                            matrix.metadata.get(
                                "aggregation_method",
                                QuantRollupMethod.SUM.value,
                            )
                        ),
                        source_record_count=value.source_record_count,
                        quantified_record_count=(
                            value.source_record_count
                            if value.missing_value_kind
                            in (
                                MissingValueKind.OBSERVED,
                                MissingValueKind.ZERO,
                            )
                            else 0
                        ),
                        observed_source_record_count=(
                            value.source_record_count
                            if value.missing_value_kind is MissingValueKind.OBSERVED
                            else 0
                        ),
                        zero_source_record_count=(
                            value.source_record_count
                            if value.missing_value_kind is MissingValueKind.ZERO
                            else 0
                        ),
                        not_observed_source_record_count=(
                            value.source_record_count
                            if value.missing_value_kind is MissingValueKind.NOT_OBSERVED
                            else 0
                        ),
                        filtered_source_record_count=(
                            value.source_record_count
                            if value.missing_value_kind is MissingValueKind.FILTERED
                            else 0
                        ),
                        aggregated_abundance=value.abundance,
                        missing_value_kind=value.missing_value_kind,
                    )
                )
        observed_cell_count = sum(
            1
            for row in rows
            for value in row.values
            if value.missing_value_kind is MissingValueKind.OBSERVED
        )
        zero_cell_count = sum(
            1
            for row in rows
            for value in row.values
            if value.missing_value_kind is MissingValueKind.ZERO
        )
        missing_cell_count = sum(
            1
            for row in rows
            for value in row.values
            if value.missing_value_kind is MissingValueKind.NOT_OBSERVED
        )
        filtered_cell_count = sum(
            1
            for row in rows
            for value in row.values
            if value.missing_value_kind is MissingValueKind.FILTERED
        )
        return cls(
            source_kind=PeptideMatrixSourceKind(
                matrix.metadata.get("source_kind", PeptideMatrixSourceKind.FEATURE.value)
            ),
            grouping_mode=PeptideMatrixGroupingMode(
                matrix.metadata.get(
                    "grouping_mode",
                    PeptideMatrixGroupingMode.MODIFIED_PEPTIDE.value,
                )
            ),
            separate_charge_states=matrix.metadata.get("separate_charge_states", "false")
            == "true",
            aggregation_method=QuantRollupMethod(
                matrix.metadata.get("aggregation_method", QuantRollupMethod.SUM.value)
            ),
            sample_ids=matrix.sample_ids,
            rows=tuple(rows),
            aggregation_entries=tuple(aggregation_entries),
            quant_matrix=matrix,
            missing_summary=MissingValueSummaryReport(
                entity_level=QuantEntityLevel.PEPTIDE,
                policy=MissingValueSummaryPolicy(),
                entries=tuple(
                    MissingValueSummaryEntry(
                        sample_id=sample_id,
                        observed_count=sum(
                            1
                            for row in rows
                            for value in row.values
                            if value.sample_id == sample_id
                            and value.missing_value_kind is MissingValueKind.OBSERVED
                        ),
                        zero_count=sum(
                            1
                            for row in rows
                            for value in row.values
                            if value.sample_id == sample_id
                            and value.missing_value_kind is MissingValueKind.ZERO
                        ),
                        not_observed_count=sum(
                            1
                            for row in rows
                            for value in row.values
                            if value.sample_id == sample_id
                            and value.missing_value_kind
                            is MissingValueKind.NOT_OBSERVED
                        ),
                        filtered_count=sum(
                            1
                            for row in rows
                            for value in row.values
                            if value.sample_id == sample_id
                            and value.missing_value_kind is MissingValueKind.FILTERED
                        ),
                    )
                    for sample_id in matrix.sample_ids
                ),
                included_entity_ids=matrix.entity_ids,
                excluded_entity_ids=(),
            ),
            summary=PeptideIntensityMatrixSummary(
                accepted_source_record_count=sum(
                    value.source_record_count for row in rows for value in row.values
                ),
                skipped_source_record_count=0,
                sample_count=len(matrix.sample_ids),
                peptide_row_count=len(rows),
                observed_cell_count=observed_cell_count,
                zero_cell_count=zero_cell_count,
                missing_cell_count=missing_cell_count,
                filtered_cell_count=filtered_cell_count,
            ),
            note=matrix.metadata.get("note", "canonical peptide matrix"),
        )


@dataclass(frozen=True)
class _PeptideObservation:
    source_record_id: str
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


def build_peptide_intensity_matrix_from_precursors(
    records: tuple[PrecursorIntensityRecord, ...],
    *,
    grouping_mode: PeptideMatrixGroupingMode = (
        PeptideMatrixGroupingMode.MODIFIED_PEPTIDE
    ),
    separate_charge_states: bool = False,
    aggregation_method: QuantRollupMethod = QuantRollupMethod.SUM,
    top_n: int = 3,
) -> PeptideIntensityMatrixReport:
    """Build one peptide-intensity matrix from precursor-quantity records."""

    observations = tuple(_precursor_observation(record) for record in records)
    return _build_peptide_intensity_matrix_report(
        observations,
        source_kind=PeptideMatrixSourceKind.PRECURSOR,
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
    ordered_sample_ids = sort_strings(report.sample_ids)
    ordered_rows = sort_rows_by_fields(report.rows, "entity_id")
    header = [
        "entity_id",
        "peptide_sequence",
        "modified_peptides",
        "charge_states",
        "protein_refs",
    ]
    header.extend(ordered_sample_ids)
    rows = ["\t".join(header)]
    for row in ordered_rows:
        value_lookup = {value.sample_id: value for value in row.values}
        matrix_values = []
        for sample_id in ordered_sample_ids:
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
                    ";".join(sort_strings(row.modified_peptides)),
                    ";".join(str(charge) for charge in row.charge_states),
                    ";".join(sort_strings(row.protein_refs)),
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
    for entry in sort_rows_by_fields(report.missing_summary.entries, "sample_id"):
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


def render_peptide_intensity_missingness_mask_tsv(
    report: PeptideIntensityMatrixReport,
) -> str:
    """Render one peptide-by-sample missingness mask as a wide TSV."""

    ordered_sample_ids = sort_strings(report.sample_ids)
    ordered_rows = sort_rows_by_fields(report.rows, "entity_id")
    header = [
        "entity_id",
        "peptide_sequence",
        "modified_peptides",
        "charge_states",
        "protein_refs",
    ]
    header.extend(ordered_sample_ids)
    rows = ["\t".join(header)]
    for row in ordered_rows:
        value_lookup = {value.sample_id: value for value in row.values}
        mask_values = [
            value_lookup[sample_id].missing_value_kind.value
            for sample_id in ordered_sample_ids
        ]
        rows.append(
            "\t".join(
                (
                    row.entity_id,
                    row.peptide_sequence,
                    ";".join(sort_strings(row.modified_peptides)),
                    ";".join(str(charge) for charge in row.charge_states),
                    ";".join(sort_strings(row.protein_refs)),
                    *mask_values,
                )
            )
        )
    return "\n".join(rows) + "\n"


def render_peptide_intensity_aggregation_tsv(
    report: PeptideIntensityMatrixReport,
) -> str:
    """Render the explicit duplicate-rollup ledger for one peptide matrix."""

    header = (
        "entity_id",
        "sample_id",
        "peptide_sequence",
        "modified_peptides",
        "charge_states",
        "protein_refs",
        "aggregation_method",
        "source_record_ids",
        "source_record_count",
        "quantified_record_count",
        "observed_source_record_count",
        "zero_source_record_count",
        "not_observed_source_record_count",
        "filtered_source_record_count",
        "source_abundances",
        "aggregated_abundance",
        "missing_value_kind",
    )
    rows = ["\t".join(header)]
    for entry in sort_rows_by_fields(report.aggregation_entries, "entity_id", "sample_id"):
        rows.append(
            "\t".join(
                (
                    entry.entity_id,
                    entry.sample_id,
                    entry.peptide_sequence,
                    ";".join(sort_strings(entry.modified_peptides)),
                    ";".join(str(charge) for charge in entry.charge_states),
                    ";".join(sort_strings(entry.protein_refs)),
                    entry.aggregation_method.value,
                    ";".join(sort_strings(entry.source_record_ids)),
                    str(entry.source_record_count),
                    str(entry.quantified_record_count),
                    str(entry.observed_source_record_count),
                    str(entry.zero_source_record_count),
                    str(entry.not_observed_source_record_count),
                    str(entry.filtered_source_record_count),
                    ";".join(f"{value:g}" for value in entry.source_abundances),
                    "" if entry.aggregated_abundance is None else f"{entry.aggregated_abundance:g}",
                    entry.missing_value_kind.value,
                )
            )
        )
    return "\n".join(rows) + "\n"


def _feature_observation(record: Ms1FeatureRecord) -> _PeptideObservation:
    parsed = parse_modified_peptide(record.canonical_peptide)
    return _PeptideObservation(
        source_record_id=record.feature_id,
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
        source_record_id=record.spectrum_id,
        sample_id=record.run_id,
        peptide_sequence=peptide_sequence,
        modified_peptide=modified_peptide,
        charge_state=record.charge,
        intensity=record.intensity,
        missing_value_kind=missing_value_kind,
        protein_refs=record.protein_refs,
    )


def _precursor_observation(record: PrecursorIntensityRecord) -> _PeptideObservation:
    parsed = parse_modified_peptide(record.canonical_peptide)
    return _PeptideObservation(
        source_record_id=record.precursor_id,
        sample_id=record.sample_id,
        peptide_sequence=record.peptide_sequence or parsed.sequence,
        modified_peptide=record.modified_peptide or parsed.canonical_notation,
        charge_state=record.charge,
        intensity=record.intensity,
        missing_value_kind=record.missing_value_kind,
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
    grouped_quantified_counts: dict[tuple[str, str], int] = {}
    grouped_record_ids: dict[tuple[str, str], list[str]] = {}
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
        grouped_record_ids.setdefault(key, []).append(observation.source_record_id)
        grouped_counts[key] = grouped_counts.get(key, 0) + 1
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
            grouped_quantified_counts[key] = grouped_quantified_counts.get(key, 0) + 1

    ordered_entity_ids = tuple(sorted(row_sequences))
    rows: list[PeptideIntensityMatrixRow] = []
    aggregation_entries: list[PeptideIntensityAggregationEntry] = []
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
            aggregation_entries.append(
                PeptideIntensityAggregationEntry(
                    entity_id=entity_id,
                    sample_id=sample_id,
                    peptide_sequence=row_sequences[entity_id],
                    modified_peptides=tuple(
                        sorted(row_modified_peptides.get(entity_id, ()))
                    ),
                    charge_states=tuple(sorted(row_charge_states.get(entity_id, ()))),
                    protein_refs=tuple(sorted(row_protein_refs.get(entity_id, ()))),
                    aggregation_method=aggregation_method,
                    source_record_ids=tuple(sorted(grouped_record_ids.get(key, ()))),
                    source_record_count=len(grouped_record_ids.get(key, ())),
                    quantified_record_count=grouped_quantified_counts.get(key, 0),
                    observed_source_record_count=sum(
                        1
                        for kind in grouped_kinds.get(key, ())
                        if kind is MissingValueKind.OBSERVED
                    ),
                    zero_source_record_count=sum(
                        1
                        for kind in grouped_kinds.get(key, ())
                        if kind is MissingValueKind.ZERO
                    ),
                    not_observed_source_record_count=sum(
                        1
                        for kind in grouped_kinds.get(key, ())
                        if kind is MissingValueKind.NOT_OBSERVED
                    ),
                    filtered_source_record_count=sum(
                        1
                        for kind in grouped_kinds.get(key, ())
                        if kind is MissingValueKind.FILTERED
                    ),
                    source_abundances=tuple(observed_values),
                    aggregated_abundance=abundance,
                    missing_value_kind=missing_kind,
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
        aggregation_entries=tuple(aggregation_entries),
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
