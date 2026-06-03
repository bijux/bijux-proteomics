# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""MaxLFQ-like protein quantification over peptide-intensity evidence."""

from __future__ import annotations

from collections import defaultdict
import math

import numpy as np
from pydantic import ConfigDict, Field, model_validator

from bijux_proteomics.domain.records import (
    MissingValueState,
    QuantEntityKind,
    QuantMeasureKind,
)
from bijux_proteomics.domain.records import (
    QuantMatrix as CanonicalQuantMatrix,
)
from bijux_proteomics.domain.records import (
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
    QuantRollupMethod,
)
from bijux_proteomics.quantification.matrix.core_matrix import (
    build_numeric_quant_matrix,
)
from bijux_proteomics.quantification.matrix.peptide_intensity_matrix import (
    PeptideIntensityMatrixReport,
    PeptideIntensityMatrixRow,
    PeptideMatrixGroupingMode,
    PeptideMatrixSourceKind,
    build_peptide_intensity_matrix_from_features,
    build_peptide_intensity_matrix_from_psms,
)
from bijux_proteomics.quantification.matrix.protein_intensity_matrix import (
    ProteinMatrixTargetKind,
)
from bijux_proteomics_foundation import JsonModel


class ProteinLfqValue(JsonModel):
    """One sample-specific MaxLFQ-like protein estimate."""

    model_config = ConfigDict(extra="forbid")

    sample_id: str = Field(..., min_length=1)
    abundance: float | None = Field(default=None, ge=0.0)
    log2_abundance: float | None = None
    missing_value_kind: MissingValueKind
    contributing_peptide_count: int = Field(..., ge=0)
    component_id: int | None = Field(default=None, ge=1)


class ProteinLfqPairwiseRatio(JsonModel):
    """One pairwise peptide-ratio constraint contributing to a protein solution."""

    model_config = ConfigDict(extra="forbid")

    sample_a: str = Field(..., min_length=1)
    sample_b: str = Field(..., min_length=1)
    shared_peptide_count: int = Field(..., ge=1)
    median_log2_ratio: float
    median_ratio: float = Field(..., gt=0.0)
    contributing_peptides: tuple[str, ...] = Field(default_factory=tuple)


class ProteinLfqDisconnectedComponentEntry(JsonModel):
    """One disconnected sample component that cannot be compared across LFQ scales."""

    model_config = ConfigDict(extra="forbid")

    entity_id: str = Field(..., min_length=1)
    target_kind: ProteinMatrixTargetKind
    protein_refs: tuple[str, ...] = Field(default_factory=tuple)
    component_id: int = Field(..., ge=1)
    sample_ids: tuple[str, ...] = Field(default_factory=tuple)
    disconnected_from_sample_ids: tuple[str, ...] = Field(default_factory=tuple)
    sample_count: int = Field(..., ge=1)
    pairwise_ratio_count: int = Field(..., ge=0)
    contributing_peptides: tuple[str, ...] = Field(default_factory=tuple)


class ProteinLfqRow(JsonModel):
    """One protein or exact protein-group LFQ row across all samples."""

    model_config = ConfigDict(extra="forbid")

    entity_id: str = Field(..., min_length=1)
    target_kind: ProteinMatrixTargetKind
    protein_refs: tuple[str, ...] = Field(default_factory=tuple)
    peptide_count: int = Field(..., ge=0)
    unique_peptide_count: int = Field(..., ge=0)
    shared_peptide_count: int = Field(..., ge=0)
    pairwise_ratio_count: int = Field(..., ge=0)
    connected_component_count: int = Field(..., ge=0)
    fully_connected: bool
    contributing_peptides: tuple[str, ...] = Field(default_factory=tuple)
    pairwise_ratios: tuple[ProteinLfqPairwiseRatio, ...] = Field(default_factory=tuple)
    values: tuple[ProteinLfqValue, ...] = Field(default_factory=tuple)


class ProteinLfqSummary(JsonModel):
    """Compact summary over one MaxLFQ-like protein quantification review."""

    model_config = ConfigDict(extra="forbid")

    peptide_row_count: int = Field(..., ge=0)
    protein_row_count: int = Field(..., ge=0)
    sample_count: int = Field(..., ge=0)
    unique_only: bool = False
    minimum_shared_peptides: int = Field(..., ge=1)
    fully_connected_row_count: int = Field(..., ge=0)
    disconnected_row_count: int = Field(..., ge=0)
    disconnected_component_entry_count: int = Field(default=0, ge=0)
    total_pairwise_ratio_count: int = Field(..., ge=0)
    observed_cell_count: int = Field(..., ge=0)
    missing_cell_count: int = Field(..., ge=0)


class ProteinLfqReport(JsonModel):
    """Owned MaxLFQ-like protein quantification matrix with explicit diagnostics."""

    model_config = ConfigDict(extra="forbid")

    source_kind: PeptideMatrixSourceKind
    grouping_mode: PeptideMatrixGroupingMode
    target_kind: ProteinMatrixTargetKind
    separate_charge_states: bool = False
    aggregation_method: QuantRollupMethod
    unique_only: bool = False
    minimum_shared_peptides: int = Field(..., ge=1)
    sample_ids: tuple[str, ...] = Field(default_factory=tuple)
    rows: tuple[ProteinLfqRow, ...] = Field(default_factory=tuple)
    disconnected_components: tuple[ProteinLfqDisconnectedComponentEntry, ...] = Field(
        default_factory=tuple
    )
    quant_matrix: CanonicalQuantMatrix | None = None
    missing_summary: MissingValueSummaryReport
    summary: ProteinLfqSummary
    note: str = Field(..., min_length=1)

    @model_validator(mode="after")
    def _bind_quant_matrix(self) -> ProteinLfqReport:
        if self.quant_matrix is None:
            self.quant_matrix = self._build_quant_matrix()
        return self

    def to_quant_matrix(
        self,
        *,
        matrix_id: str = "protein_lfq_matrix",
        sample_metadata: tuple[CanonicalSampleMetadata, ...] = (),
    ) -> CanonicalQuantMatrix:
        """Convert this MaxLFQ-like report into the canonical quant matrix."""

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
        matrix_id: str = "protein_lfq_matrix",
        sample_metadata: tuple[CanonicalSampleMetadata, ...] = (),
    ) -> CanonicalQuantMatrix:
        entity_kind = (
            QuantEntityKind.PROTEIN
            if self.target_kind is ProteinMatrixTargetKind.PROTEIN
            else QuantEntityKind.PROTEIN_GROUP
        )
        return build_numeric_quant_matrix(
            matrix_id=matrix_id,
            entity_kind=entity_kind,
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
                (row.entity_id, value.sample_id): value.contributing_peptide_count
                for row in self.rows
                for value in row.values
            },
            row_metadata_lookup={
                row.entity_id: {
                    "target_kind": row.target_kind.value,
                    "protein_refs": ";".join(row.protein_refs),
                    "peptide_count": str(row.peptide_count),
                    "unique_peptide_count": str(row.unique_peptide_count),
                    "shared_peptide_count": str(row.shared_peptide_count),
                    "pairwise_ratio_count": str(row.pairwise_ratio_count),
                    "connected_component_count": str(row.connected_component_count),
                    "fully_connected": str(row.fully_connected).lower(),
                    "contributing_peptides": ";".join(row.contributing_peptides),
                }
                for row in self.rows
            },
            sample_metadata=sample_metadata,
            transformation_history=(
                "maxlfq_like",
                f"source_kind:{self.source_kind.value}",
                f"grouping_mode:{self.grouping_mode.value}",
                f"target_kind:{self.target_kind.value}",
                f"unique_only:{str(self.unique_only).lower()}",
                f"minimum_shared_peptides:{self.minimum_shared_peptides}",
            ),
            metadata={
                "note": self.note,
                "source_kind": self.source_kind.value,
                "grouping_mode": self.grouping_mode.value,
                "target_kind": self.target_kind.value,
                "unique_only": str(self.unique_only).lower(),
                "minimum_shared_peptides": str(self.minimum_shared_peptides),
            },
        )


def build_protein_lfq_report_from_peptides(
    peptide_matrix: PeptideIntensityMatrixReport | CanonicalQuantMatrix,
    *,
    target_kind: ProteinMatrixTargetKind = ProteinMatrixTargetKind.PROTEIN,
    unique_only: bool = False,
    minimum_shared_peptides: int = 1,
) -> ProteinLfqReport:
    """Build one MaxLFQ-like protein matrix from a peptide-intensity matrix."""
    if isinstance(peptide_matrix, CanonicalQuantMatrix):
        peptide_matrix = PeptideIntensityMatrixReport.from_quant_matrix(peptide_matrix)
    if minimum_shared_peptides < 1:
        raise ValueError("minimum_shared_peptides must be at least 1")

    grouped_rows: dict[str, list[tuple[PeptideIntensityMatrixRow, bool]]] = defaultdict(
        list
    )
    target_refs: dict[str, tuple[str, ...]] = {}

    for peptide_row in peptide_matrix.rows:
        is_unique = len(peptide_row.protein_refs) == 1
        if unique_only and not is_unique:
            continue
        if not peptide_row.protein_refs:
            continue
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
            grouped_rows[target_id].append((peptide_row, is_unique))

    rows: list[ProteinLfqRow] = []
    missing_entries: list[MissingValueSummaryEntry] = []
    observed_cell_count = 0
    missing_cell_count = 0
    fully_connected_row_count = 0
    disconnected_row_count = 0
    disconnected_component_entries: list[ProteinLfqDisconnectedComponentEntry] = []
    total_pairwise_ratio_count = 0

    ordered_target_ids = tuple(sorted(grouped_rows))
    row_results: dict[str, ProteinLfqRow] = {}
    for target_id in ordered_target_ids:
        row = _build_target_lfq_row(
            target_id,
            grouped_rows[target_id],
            sample_ids=peptide_matrix.sample_ids,
            protein_refs=target_refs[target_id],
            target_kind=target_kind,
            minimum_shared_peptides=minimum_shared_peptides,
        )
        row_results[target_id] = row
        rows.append(row)
        total_pairwise_ratio_count += row.pairwise_ratio_count
        if row.fully_connected:
            fully_connected_row_count += 1
        elif row.connected_component_count > 1:
            disconnected_row_count += 1
            disconnected_component_entries.extend(
                _build_disconnected_component_entries(
                    row,
                    peptide_rows=grouped_rows[target_id],
                )
            )
        for value in row.values:
            if value.abundance is None:
                missing_cell_count += 1
            else:
                observed_cell_count += 1

    for sample_id in peptide_matrix.sample_ids:
        observed = 0
        zero = 0
        not_observed = 0
        filtered = 0
        for target_id in ordered_target_ids:
            value = next(
                candidate
                for candidate in row_results[target_id].values
                if candidate.sample_id == sample_id
            )
            if value.missing_value_kind is MissingValueKind.OBSERVED:
                observed += 1
            elif value.missing_value_kind is MissingValueKind.ZERO:
                zero += 1
            elif value.missing_value_kind is MissingValueKind.FILTERED:
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

    summary = ProteinLfqSummary(
        peptide_row_count=len(peptide_matrix.rows),
        protein_row_count=len(rows),
        sample_count=len(peptide_matrix.sample_ids),
        unique_only=unique_only,
        minimum_shared_peptides=minimum_shared_peptides,
        fully_connected_row_count=fully_connected_row_count,
        disconnected_row_count=disconnected_row_count,
        disconnected_component_entry_count=len(disconnected_component_entries),
        total_pairwise_ratio_count=total_pairwise_ratio_count,
        observed_cell_count=observed_cell_count,
        missing_cell_count=missing_cell_count,
    )
    return ProteinLfqReport(
        source_kind=peptide_matrix.source_kind,
        grouping_mode=peptide_matrix.grouping_mode,
        target_kind=target_kind,
        separate_charge_states=peptide_matrix.separate_charge_states,
        aggregation_method=peptide_matrix.aggregation_method,
        unique_only=unique_only,
        minimum_shared_peptides=minimum_shared_peptides,
        sample_ids=peptide_matrix.sample_ids,
        rows=tuple(rows),
        disconnected_components=tuple(disconnected_component_entries),
        missing_summary=MissingValueSummaryReport(
            entity_level=peptide_matrix.missing_summary.entity_level,
            policy=MissingValueSummaryPolicy(),
            entries=tuple(missing_entries),
            included_entity_ids=tuple(row.entity_id for row in rows),
            excluded_entity_ids=(),
        ),
        summary=summary,
        note=(
            "maxlfq-like protein quantification preserves shared-peptide pairwise log-ratios and solves sample profiles with component-aware least squares"
        ),
    )


def build_protein_lfq_report_from_features(
    records: tuple[Ms1FeatureRecord, ...],
    *,
    grouping_mode: PeptideMatrixGroupingMode = (
        PeptideMatrixGroupingMode.MODIFIED_PEPTIDE
    ),
    target_kind: ProteinMatrixTargetKind = ProteinMatrixTargetKind.PROTEIN,
    separate_charge_states: bool = False,
    aggregation_method: QuantRollupMethod = QuantRollupMethod.SUM,
    unique_only: bool = False,
    minimum_shared_peptides: int = 1,
    top_n: int = 3,
) -> ProteinLfqReport:
    """Build one MaxLFQ-like protein matrix from MS1 feature evidence."""
    peptide_matrix = build_peptide_intensity_matrix_from_features(
        records,
        grouping_mode=grouping_mode,
        separate_charge_states=separate_charge_states,
        aggregation_method=aggregation_method,
        top_n=top_n,
    )
    return build_protein_lfq_report_from_peptides(
        peptide_matrix,
        target_kind=target_kind,
        unique_only=unique_only,
        minimum_shared_peptides=minimum_shared_peptides,
    )


def build_protein_lfq_report_from_psms(
    records: tuple[PsmRecord, ...],
    *,
    grouping_mode: PeptideMatrixGroupingMode = (
        PeptideMatrixGroupingMode.MODIFIED_PEPTIDE
    ),
    target_kind: ProteinMatrixTargetKind = ProteinMatrixTargetKind.PROTEIN,
    separate_charge_states: bool = False,
    aggregation_method: QuantRollupMethod = QuantRollupMethod.SUM,
    unique_only: bool = False,
    minimum_shared_peptides: int = 1,
    top_n: int = 3,
) -> ProteinLfqReport:
    """Build one MaxLFQ-like protein matrix from intensity-bearing canonical PSM rows."""
    peptide_matrix = build_peptide_intensity_matrix_from_psms(
        records,
        grouping_mode=grouping_mode,
        separate_charge_states=separate_charge_states,
        aggregation_method=aggregation_method,
        top_n=top_n,
    )
    return build_protein_lfq_report_from_peptides(
        peptide_matrix,
        target_kind=target_kind,
        unique_only=unique_only,
        minimum_shared_peptides=minimum_shared_peptides,
    )


def render_protein_lfq_summary_tsv(report: ProteinLfqReport) -> str:
    """Render one compact MaxLFQ-like summary as TSV."""
    header = (
        "source_kind",
        "grouping_mode",
        "target_kind",
        "separate_charge_states",
        "aggregation_method",
        "unique_only",
        "minimum_shared_peptides",
        "peptide_row_count",
        "protein_row_count",
        "sample_count",
        "fully_connected_row_count",
        "disconnected_row_count",
        "disconnected_component_entry_count",
        "total_pairwise_ratio_count",
        "observed_cell_count",
        "missing_cell_count",
        "note",
    )
    row = (
        report.source_kind.value,
        report.grouping_mode.value,
        report.target_kind.value,
        str(report.separate_charge_states).lower(),
        report.aggregation_method.value,
        str(report.unique_only).lower(),
        str(report.minimum_shared_peptides),
        str(report.summary.peptide_row_count),
        str(report.summary.protein_row_count),
        str(report.summary.sample_count),
        str(report.summary.fully_connected_row_count),
        str(report.summary.disconnected_row_count),
        str(report.summary.disconnected_component_entry_count),
        str(report.summary.total_pairwise_ratio_count),
        str(report.summary.observed_cell_count),
        str(report.summary.missing_cell_count),
        report.note,
    )
    return "\t".join(header) + "\n" + "\t".join(row) + "\n"


def render_protein_lfq_matrix_tsv(report: ProteinLfqReport) -> str:
    """Render the protein LFQ matrix as one wide TSV."""
    ordered_sample_ids = sort_strings(report.sample_ids)
    ordered_rows = sort_rows_by_fields(report.rows, "entity_id")
    header = [
        "entity_id",
        "target_kind",
        "protein_refs",
        "peptide_count",
        "unique_peptide_count",
        "shared_peptide_count",
        "pairwise_ratio_count",
        "connected_component_count",
        "contributing_peptides",
    ]
    header.extend(ordered_sample_ids)
    rows = ["\t".join(header)]
    for row in ordered_rows:
        value_lookup = {value.sample_id: value for value in row.values}
        matrix_values = []
        for sample_id in ordered_sample_ids:
            value = value_lookup[sample_id]
            matrix_values.append(
                "" if value.abundance is None else f"{value.abundance:g}"
            )
        rows.append(
            "\t".join(
                (
                    row.entity_id,
                    row.target_kind.value,
                    ";".join(sort_strings(row.protein_refs)),
                    str(row.peptide_count),
                    str(row.unique_peptide_count),
                    str(row.shared_peptide_count),
                    str(row.pairwise_ratio_count),
                    str(row.connected_component_count),
                    ";".join(sort_strings(row.contributing_peptides)),
                    *matrix_values,
                )
            )
        )
    return "\n".join(rows) + "\n"


def render_protein_lfq_pairwise_ratios_tsv(report: ProteinLfqReport) -> str:
    """Render one pairwise-ratio ledger for all protein LFQ rows."""
    ordered_rows = sort_rows_by_fields(report.rows, "entity_id")
    header = (
        "entity_id",
        "target_kind",
        "sample_a",
        "sample_b",
        "shared_peptide_count",
        "median_log2_ratio",
        "median_ratio",
        "contributing_peptides",
    )
    rows = ["\t".join(header)]
    for row in ordered_rows:
        for ratio in sort_rows_by_fields(row.pairwise_ratios, "sample_a", "sample_b"):
            rows.append(
                "\t".join(
                    (
                        row.entity_id,
                        row.target_kind.value,
                        ratio.sample_a,
                        ratio.sample_b,
                        str(ratio.shared_peptide_count),
                        f"{ratio.median_log2_ratio:g}",
                        f"{ratio.median_ratio:g}",
                        ";".join(sort_strings(ratio.contributing_peptides)),
                    )
                )
            )
    return "\n".join(rows) + "\n"


def render_protein_lfq_missingness_tsv(report: ProteinLfqReport) -> str:
    """Render one per-sample missingness ledger for a protein LFQ matrix."""
    header = (
        "sample_id",
        "observed_count",
        "zero_count",
        "not_observed_count",
        "filtered_count",
        "imputed_count",
        "censored_count",
        "excluded_count",
        "not_applicable_count",
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
                    str(entry.imputed_count),
                    str(entry.censored_count),
                    str(entry.excluded_count),
                    str(entry.not_applicable_count),
                )
            )
        )
    return "\n".join(rows) + "\n"


def render_protein_lfq_missingness_mask_tsv(report: ProteinLfqReport) -> str:
    """Render one protein-LFQ missingness mask beside the wide LFQ matrix."""

    ordered_sample_ids = sort_strings(report.sample_ids)
    ordered_rows = sort_rows_by_fields(report.rows, "entity_id")
    header = [
        "entity_id",
        "target_kind",
        "protein_refs",
        "peptide_count",
        "unique_peptide_count",
        "shared_peptide_count",
        "pairwise_ratio_count",
        "connected_component_count",
        "contributing_peptides",
    ]
    header.extend(ordered_sample_ids)
    rows = ["\t".join(header)]
    for row in ordered_rows:
        value_lookup = {value.sample_id: value for value in row.values}
        rows.append(
            "\t".join(
                (
                    row.entity_id,
                    row.target_kind.value,
                    ";".join(sort_strings(row.protein_refs)),
                    str(row.peptide_count),
                    str(row.unique_peptide_count),
                    str(row.shared_peptide_count),
                    str(row.pairwise_ratio_count),
                    str(row.connected_component_count),
                    ";".join(sort_strings(row.contributing_peptides)),
                    *[
                        value_lookup[sample_id].missing_value_kind.value
                        for sample_id in ordered_sample_ids
                    ],
                )
            )
        )
    return "\n".join(rows) + "\n"


def render_protein_lfq_disconnected_components_tsv(report: ProteinLfqReport) -> str:
    """Render one ledger of LFQ sample components that remain disconnected."""

    header = (
        "entity_id",
        "target_kind",
        "protein_refs",
        "component_id",
        "sample_ids",
        "disconnected_from_sample_ids",
        "sample_count",
        "pairwise_ratio_count",
        "contributing_peptides",
    )
    rows = ["\t".join(header)]
    for entry in sort_rows_by_fields(
        report.disconnected_components,
        "entity_id",
        "component_id",
    ):
        rows.append(
            "\t".join(
                (
                    entry.entity_id,
                    entry.target_kind.value,
                    ";".join(sort_strings(entry.protein_refs)),
                    str(entry.component_id),
                    ";".join(sort_strings(entry.sample_ids)),
                    ";".join(sort_strings(entry.disconnected_from_sample_ids)),
                    str(entry.sample_count),
                    str(entry.pairwise_ratio_count),
                    ";".join(sort_strings(entry.contributing_peptides)),
                )
            )
        )
    return "\n".join(rows) + "\n"


def _build_target_lfq_row(
    target_id: str,
    peptide_rows: list[tuple[PeptideIntensityMatrixRow, bool]],
    *,
    sample_ids: tuple[str, ...],
    protein_refs: tuple[str, ...],
    target_kind: ProteinMatrixTargetKind,
    minimum_shared_peptides: int,
) -> ProteinLfqRow:
    pairwise_ratios = _build_pairwise_ratio_rows(
        peptide_rows,
        sample_ids=sample_ids,
        minimum_shared_peptides=minimum_shared_peptides,
    )
    observed_logs = _observed_log2_intensities_by_sample(
        peptide_rows, sample_ids=sample_ids
    )
    components = _connected_components(
        sample_ids=sample_ids,
        pairwise_ratios=pairwise_ratios,
        observed_logs=observed_logs,
    )
    solved_logs, component_ids = _solve_component_profiles(
        components=components,
        pairwise_ratios=pairwise_ratios,
        observed_logs=observed_logs,
    )

    peptide_ids = sorted({row.entity_id for row, _ in peptide_rows})
    unique_peptide_ids = sorted(
        {row.entity_id for row, is_unique in peptide_rows if is_unique}
    )
    shared_peptide_ids = sorted(
        {row.entity_id for row, is_unique in peptide_rows if not is_unique}
    )
    values: list[ProteinLfqValue] = []
    for sample_id in sample_ids:
        sample_kinds = tuple(
            next(
                value for value in row.values if value.sample_id == sample_id
            ).missing_value_kind
            for row, _ in peptide_rows
        )
        log2_abundance = solved_logs.get(sample_id)
        abundance = None if log2_abundance is None else float(2.0**log2_abundance)
        if abundance is None:
            missing_kind = _aggregate_missing_kind(sample_kinds)
        else:
            missing_kind = MissingValueKind.OBSERVED
        contributing_peptide_count = sum(
            1
            for row, _ in peptide_rows
            if any(
                value.sample_id == sample_id
                and value.abundance is not None
                and value.abundance > 0.0
                and value.missing_value_kind is MissingValueKind.OBSERVED
                for value in row.values
            )
        )
        values.append(
            ProteinLfqValue(
                sample_id=sample_id,
                abundance=abundance,
                log2_abundance=log2_abundance,
                missing_value_kind=missing_kind,
                contributing_peptide_count=contributing_peptide_count,
                component_id=component_ids.get(sample_id),
            )
        )

    fully_connected = len(components) <= 1 and len(sample_ids) > 0
    return ProteinLfqRow(
        entity_id=target_id,
        target_kind=target_kind,
        protein_refs=protein_refs,
        peptide_count=len(peptide_ids),
        unique_peptide_count=len(unique_peptide_ids),
        shared_peptide_count=len(shared_peptide_ids),
        pairwise_ratio_count=len(pairwise_ratios),
        connected_component_count=len(components),
        fully_connected=fully_connected,
        contributing_peptides=tuple(peptide_ids),
        pairwise_ratios=tuple(pairwise_ratios),
        values=tuple(values),
    )


def _build_disconnected_component_entries(
    row: ProteinLfqRow,
    *,
    peptide_rows: list[tuple[PeptideIntensityMatrixRow, bool]],
) -> tuple[ProteinLfqDisconnectedComponentEntry, ...]:
    component_samples: dict[int, list[str]] = defaultdict(list)
    for value in row.values:
        if value.component_id is None:
            continue
        component_samples[value.component_id].append(value.sample_id)
    if len(component_samples) <= 1:
        return ()

    entries: list[ProteinLfqDisconnectedComponentEntry] = []
    for component_id in sorted(component_samples):
        sample_ids = tuple(sorted(component_samples[component_id]))
        sample_id_set = set(sample_ids)
        disconnected_from_sample_ids = tuple(
            sorted(
                {
                    sample_id
                    for other_component_id, other_sample_ids in component_samples.items()
                    if other_component_id != component_id
                    for sample_id in other_sample_ids
                }
            )
        )
        pairwise_ratio_count = sum(
            1
            for ratio in row.pairwise_ratios
            if ratio.sample_a in sample_id_set and ratio.sample_b in sample_id_set
        )
        contributing_peptides = tuple(
            sorted(
                {
                    peptide_row.entity_id
                    for peptide_row, _ in peptide_rows
                    if any(
                        value.sample_id in sample_id_set
                        and value.abundance is not None
                        and value.abundance > 0.0
                        and value.missing_value_kind is MissingValueKind.OBSERVED
                        for value in peptide_row.values
                    )
                }
            )
        )
        entries.append(
            ProteinLfqDisconnectedComponentEntry(
                entity_id=row.entity_id,
                target_kind=row.target_kind,
                protein_refs=row.protein_refs,
                component_id=component_id,
                sample_ids=sample_ids,
                disconnected_from_sample_ids=disconnected_from_sample_ids,
                sample_count=len(sample_ids),
                pairwise_ratio_count=pairwise_ratio_count,
                contributing_peptides=contributing_peptides,
            )
        )
    return tuple(entries)


def _build_pairwise_ratio_rows(
    peptide_rows: list[tuple[PeptideIntensityMatrixRow, bool]],
    *,
    sample_ids: tuple[str, ...],
    minimum_shared_peptides: int,
) -> list[ProteinLfqPairwiseRatio]:
    return _build_pairwise_ratio_rows_vectorized(
        peptide_rows,
        sample_ids=sample_ids,
        minimum_shared_peptides=minimum_shared_peptides,
    )


def _build_pairwise_ratio_rows_pure(
    peptide_rows: list[tuple[PeptideIntensityMatrixRow, bool]],
    *,
    sample_ids: tuple[str, ...],
    minimum_shared_peptides: int,
) -> list[ProteinLfqPairwiseRatio]:
    ratios_by_pair: dict[tuple[str, str], list[tuple[float, str]]] = defaultdict(list)
    for row, _ in peptide_rows:
        sample_abundances = {
            value.sample_id: float(value.abundance)
            for value in row.values
            if value.abundance is not None
            and value.abundance > 0.0
            and value.missing_value_kind is MissingValueKind.OBSERVED
        }
        for index, sample_a in enumerate(sample_ids):
            abundance_a = sample_abundances.get(sample_a)
            if abundance_a is None:
                continue
            for sample_b in sample_ids[index + 1 :]:
                abundance_b = sample_abundances.get(sample_b)
                if abundance_b is None:
                    continue
                ratios_by_pair[(sample_a, sample_b)].append(
                    (math.log2(abundance_b) - math.log2(abundance_a), row.entity_id)
                )

    pairwise_ratios: list[ProteinLfqPairwiseRatio] = []
    for sample_a, sample_b in sorted(ratios_by_pair):
        entries = ratios_by_pair[(sample_a, sample_b)]
        if len(entries) < minimum_shared_peptides:
            continue
        median_log2_ratio = _median(tuple(value for value, _ in entries))
        pairwise_ratios.append(
            ProteinLfqPairwiseRatio(
                sample_a=sample_a,
                sample_b=sample_b,
                shared_peptide_count=len(entries),
                median_log2_ratio=median_log2_ratio,
                median_ratio=float(2.0**median_log2_ratio),
                contributing_peptides=tuple(
                    sorted({peptide_id for _, peptide_id in entries})
                ),
            )
        )
    return pairwise_ratios


def _build_pairwise_ratio_rows_vectorized(
    peptide_rows: list[tuple[PeptideIntensityMatrixRow, bool]],
    *,
    sample_ids: tuple[str, ...],
    minimum_shared_peptides: int,
) -> list[ProteinLfqPairwiseRatio]:
    peptide_ids, log2_matrix, observed_mask = _build_peptide_log2_observation_matrix(
        peptide_rows,
        sample_ids=sample_ids,
    )
    pairwise_ratios: list[ProteinLfqPairwiseRatio] = []
    for sample_a_index, sample_a in enumerate(sample_ids):
        for sample_b_index in range(sample_a_index + 1, len(sample_ids)):
            sample_b = sample_ids[sample_b_index]
            shared_mask = (
                observed_mask[:, sample_a_index] & observed_mask[:, sample_b_index]
            )
            shared_count = int(np.sum(shared_mask))
            if shared_count < minimum_shared_peptides:
                continue
            shared_ratios = (
                log2_matrix[shared_mask, sample_b_index]
                - log2_matrix[shared_mask, sample_a_index]
            )
            median_log2_ratio = float(np.median(shared_ratios))
            contributing_peptides = tuple(
                sorted(
                    peptide_id
                    for peptide_id, include in zip(
                        peptide_ids, shared_mask, strict=True
                    )
                    if include
                )
            )
            pairwise_ratios.append(
                ProteinLfqPairwiseRatio(
                    sample_a=sample_a,
                    sample_b=sample_b,
                    shared_peptide_count=shared_count,
                    median_log2_ratio=median_log2_ratio,
                    median_ratio=float(2.0**median_log2_ratio),
                    contributing_peptides=contributing_peptides,
                )
            )
    return pairwise_ratios


def _observed_log2_intensities_by_sample(
    peptide_rows: list[tuple[PeptideIntensityMatrixRow, bool]],
    *,
    sample_ids: tuple[str, ...],
) -> dict[str, tuple[float, ...]]:
    return _observed_log2_intensities_by_sample_vectorized(
        peptide_rows,
        sample_ids=sample_ids,
    )


def _observed_log2_intensities_by_sample_pure(
    peptide_rows: list[tuple[PeptideIntensityMatrixRow, bool]],
    *,
    sample_ids: tuple[str, ...],
) -> dict[str, tuple[float, ...]]:
    observed: dict[str, list[float]] = {sample_id: [] for sample_id in sample_ids}
    for row, _ in peptide_rows:
        for value in row.values:
            if (
                value.abundance is not None
                and value.abundance > 0.0
                and value.missing_value_kind is MissingValueKind.OBSERVED
            ):
                observed[value.sample_id].append(math.log2(float(value.abundance)))
    return {
        sample_id: tuple(values) for sample_id, values in observed.items() if values
    }


def _observed_log2_intensities_by_sample_vectorized(
    peptide_rows: list[tuple[PeptideIntensityMatrixRow, bool]],
    *,
    sample_ids: tuple[str, ...],
) -> dict[str, tuple[float, ...]]:
    _peptide_ids, log2_matrix, observed_mask = _build_peptide_log2_observation_matrix(
        peptide_rows,
        sample_ids=sample_ids,
    )
    return {
        sample_id: tuple(
            log2_matrix[observed_mask[:, sample_index], sample_index].tolist()
        )
        for sample_index, sample_id in enumerate(sample_ids)
        if np.any(observed_mask[:, sample_index])
    }


def _build_peptide_log2_observation_matrix(
    peptide_rows: list[tuple[PeptideIntensityMatrixRow, bool]],
    *,
    sample_ids: tuple[str, ...],
) -> tuple[tuple[str, ...], np.ndarray, np.ndarray]:
    sample_index = {sample_id: index for index, sample_id in enumerate(sample_ids)}
    peptide_ids: list[str] = []
    log2_matrix = np.full((len(peptide_rows), len(sample_ids)), np.nan, dtype=float)
    observed_mask = np.zeros((len(peptide_rows), len(sample_ids)), dtype=bool)
    for row_index, (row, _) in enumerate(peptide_rows):
        peptide_ids.append(row.entity_id)
        for value in row.values:
            column_index = sample_index[value.sample_id]
            if (
                value.abundance is not None
                and value.abundance > 0.0
                and value.missing_value_kind is MissingValueKind.OBSERVED
            ):
                observed_mask[row_index, column_index] = True
                log2_matrix[row_index, column_index] = math.log2(float(value.abundance))
    return tuple(peptide_ids), log2_matrix, observed_mask


def _connected_components(
    *,
    sample_ids: tuple[str, ...],
    pairwise_ratios: list[ProteinLfqPairwiseRatio],
    observed_logs: dict[str, tuple[float, ...]],
) -> tuple[tuple[str, ...], ...]:
    adjacency: dict[str, set[str]] = {sample_id: set() for sample_id in sample_ids}
    for ratio in pairwise_ratios:
        adjacency[ratio.sample_a].add(ratio.sample_b)
        adjacency[ratio.sample_b].add(ratio.sample_a)

    observed_samples = tuple(
        sample_id for sample_id in sample_ids if sample_id in observed_logs
    )
    components: list[tuple[str, ...]] = []
    seen: set[str] = set()
    for sample_id in observed_samples:
        if sample_id in seen:
            continue
        stack = [sample_id]
        component: list[str] = []
        while stack:
            current = stack.pop()
            if current in seen:
                continue
            seen.add(current)
            component.append(current)
            stack.extend(sorted(adjacency[current] - seen))
        components.append(tuple(sorted(component)))
    return tuple(components)


def _solve_component_profiles(
    *,
    components: tuple[tuple[str, ...], ...],
    pairwise_ratios: list[ProteinLfqPairwiseRatio],
    observed_logs: dict[str, tuple[float, ...]],
) -> tuple[dict[str, float], dict[str, int]]:
    pairwise_by_samples = {
        (ratio.sample_a, ratio.sample_b): ratio for ratio in pairwise_ratios
    }
    solved_logs: dict[str, float] = {}
    component_ids: dict[str, int] = {}
    for component_index, component in enumerate(components, start=1):
        for sample_id in component:
            component_ids[sample_id] = component_index
        if len(component) == 1:
            sample_id = component[0]
            solved_logs[sample_id] = _median(observed_logs[sample_id])
            continue

        index_by_sample = {
            sample_id: index for index, sample_id in enumerate(component)
        }
        equations: list[list[float]] = []
        targets: list[float] = []
        for sample_a_index, sample_a in enumerate(component):
            for sample_b in component[sample_a_index + 1 :]:
                ratio = pairwise_by_samples.get((sample_a, sample_b))
                if ratio is None:
                    continue
                equation = [0.0] * len(component)
                equation[index_by_sample[sample_a]] = -1.0
                equation[index_by_sample[sample_b]] = 1.0
                equations.append(equation)
                targets.append(ratio.median_log2_ratio)

        anchor = [1.0] * len(component)
        equations.append(anchor)
        targets.append(0.0)

        matrix = np.array(equations, dtype=float)
        target_vector = np.array(targets, dtype=float)
        centered_solution, *_ = np.linalg.lstsq(matrix, target_vector, rcond=None)
        offsets = [
            _median(observed_logs[sample_id])
            - float(centered_solution[index_by_sample[sample_id]])
            for sample_id in component
        ]
        offset = _median(tuple(offsets))
        for sample_id in component:
            solved_logs[sample_id] = float(
                centered_solution[index_by_sample[sample_id]] + offset
            )
    return solved_logs, component_ids


def _aggregate_missing_kind(kinds: tuple[MissingValueKind, ...]) -> MissingValueKind:
    if any(
        kind in (MissingValueKind.OBSERVED, MissingValueKind.ZERO) for kind in kinds
    ):
        if any(kind is MissingValueKind.ZERO for kind in kinds) and not any(
            kind is MissingValueKind.OBSERVED for kind in kinds
        ):
            return MissingValueKind.ZERO
        return MissingValueKind.OBSERVED
    if any(kind is MissingValueKind.EXCLUDED for kind in kinds):
        return MissingValueKind.EXCLUDED
    if any(kind is MissingValueKind.CENSORED for kind in kinds):
        return MissingValueKind.CENSORED
    if any(kind is MissingValueKind.FILTERED for kind in kinds):
        return MissingValueKind.FILTERED
    if all(kind is MissingValueKind.NOT_APPLICABLE for kind in kinds):
        return MissingValueKind.NOT_APPLICABLE
    return MissingValueKind.NOT_OBSERVED


def _median(values: tuple[float, ...]) -> float:
    ordered = sorted(values)
    midpoint = len(ordered) // 2
    if len(ordered) % 2 == 1:
        return float(ordered[midpoint])
    return float((ordered[midpoint - 1] + ordered[midpoint]) / 2.0)
