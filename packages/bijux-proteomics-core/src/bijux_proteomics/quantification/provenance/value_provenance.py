# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Owned review surface for per-cell quantitative provenance."""

from __future__ import annotations

import csv
from io import StringIO
from pathlib import Path

from pydantic import ConfigDict, Field

from bijux_proteomics._output_tables import write_output_table_tsv
from bijux_proteomics.quantification.contracts import (
    ImputationMethod,
    LabelFreeQuantTable,
    MissingValueKind,
    QuantEntityLevel,
    QuantMeasureKind,
    QuantRollupMethod,
    QuantValueOrigin,
)
from bijux_proteomics_foundation import JsonModel


class QuantValueProvenanceReportRow(JsonModel):
    """One reviewable matrix cell with explicit contributor lineage."""

    model_config = ConfigDict(extra="forbid")

    entity_id: str = Field(..., min_length=1)
    sample_id: str = Field(..., min_length=1)
    entity_level: QuantEntityLevel
    measure_kind: QuantMeasureKind
    aggregation_method: QuantRollupMethod
    abundance: float | None = Field(default=None, ge=0.0)
    missing_value_kind: MissingValueKind
    value_origin: QuantValueOrigin
    source_feature_count: int = Field(..., ge=0)
    source_feature_ids: tuple[str, ...] = Field(default_factory=tuple)
    source_peptides: tuple[str, ...] = Field(default_factory=tuple)
    source_precursor_ids: tuple[str, ...] = Field(default_factory=tuple)
    excluded_contributor_ids: tuple[str, ...] = Field(default_factory=tuple)
    exclusion_reason_codes: tuple[str, ...] = Field(default_factory=tuple)
    protein_refs: tuple[str, ...] = Field(default_factory=tuple)
    member_peptides: tuple[str, ...] = Field(default_factory=tuple)
    imputation_method: ImputationMethod = ImputationMethod.NONE


class QuantValueProvenanceReportSummary(JsonModel):
    """Compact counts over a quant value provenance report."""

    model_config = ConfigDict(extra="forbid")

    row_count: int = Field(..., ge=0)
    observed_row_count: int = Field(..., ge=0)
    missing_row_count: int = Field(..., ge=0)
    imputed_row_count: int = Field(..., ge=0)
    row_with_exclusions_count: int = Field(..., ge=0)


class QuantValueProvenanceReport(JsonModel):
    """Stable report over all cell-level quantitative provenance in one table."""

    model_config = ConfigDict(extra="forbid")

    entity_level: QuantEntityLevel
    measure_kind: QuantMeasureKind
    aggregation_method: QuantRollupMethod
    normalization_method: str = Field(..., min_length=1)
    imputation_method: ImputationMethod
    rows: tuple[QuantValueProvenanceReportRow, ...] = Field(default_factory=tuple)
    summary: QuantValueProvenanceReportSummary
    note: str = Field(..., min_length=1)


def build_quant_value_provenance_report(
    table: LabelFreeQuantTable,
) -> QuantValueProvenanceReport:
    """Build a per-cell report that explains each quantitative value back to raw support."""

    rows = tuple(
        sorted(
            (
                QuantValueProvenanceReportRow(
                    entity_id=value.entity_id,
                    sample_id=value.sample_id,
                    entity_level=table.entity_level,
                    measure_kind=table.measure_kind,
                    aggregation_method=table.aggregation_method,
                    abundance=value.abundance,
                    missing_value_kind=value.missing_value_kind,
                    value_origin=(
                        QuantValueOrigin.MISSING
                        if value.value_provenance is None
                        else value.value_provenance.value_origin
                    ),
                    source_feature_count=value.source_feature_count,
                    source_feature_ids=(
                        ()
                        if value.value_provenance is None
                        else value.value_provenance.source_feature_ids
                    ),
                    source_peptides=(
                        ()
                        if value.value_provenance is None
                        else value.value_provenance.source_peptides
                    ),
                    source_precursor_ids=(
                        ()
                        if value.value_provenance is None
                        else value.value_provenance.source_precursor_ids
                    ),
                    excluded_contributor_ids=(
                        ()
                        if value.value_provenance is None
                        else tuple(
                            excluded.contributor.contributor_id
                            for excluded in value.value_provenance.excluded_contributors
                        )
                    ),
                    exclusion_reason_codes=(
                        ()
                        if value.value_provenance is None
                        else tuple(
                            excluded.reason_code
                            for excluded in value.value_provenance.excluded_contributors
                        )
                    ),
                    protein_refs=table.entity_protein_refs.get(value.entity_id, ()),
                    member_peptides=table.entity_member_peptides.get(
                        value.entity_id, ()
                    ),
                    imputation_method=(
                        ImputationMethod.NONE
                        if value.imputation_provenance is None
                        else value.imputation_provenance.method
                    ),
                )
                for value in table.values
            ),
            key=lambda row: (row.entity_id, row.sample_id),
        )
    )
    summary = QuantValueProvenanceReportSummary(
        row_count=len(rows),
        observed_row_count=sum(
            1 for row in rows if row.value_origin is QuantValueOrigin.OBSERVED
        ),
        missing_row_count=sum(
            1 for row in rows if row.value_origin is QuantValueOrigin.MISSING
        ),
        imputed_row_count=sum(
            1 for row in rows if row.value_origin is QuantValueOrigin.IMPUTED
        ),
        row_with_exclusions_count=sum(
            1 for row in rows if row.excluded_contributor_ids
        ),
    )
    return QuantValueProvenanceReport(
        entity_level=table.entity_level,
        measure_kind=table.measure_kind,
        aggregation_method=table.aggregation_method,
        normalization_method=table.normalization_method.value,
        imputation_method=table.imputation_method,
        rows=rows,
        summary=summary,
        note=(
            "each quantitative matrix cell preserves selected contributors, excluded contributors, aggregation policy, and observed-versus-imputed origin so one abundance value can be traced back to raw evidence"
        ),
    )


def render_quant_value_provenance_tsv(
    report: QuantValueProvenanceReport,
) -> str:
    """Render one stable TSV over per-cell quantitative provenance."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        [
            "entity_id",
            "sample_id",
            "entity_level",
            "measure_kind",
            "aggregation_method",
            "abundance",
            "missing_value_kind",
            "value_origin",
            "source_feature_count",
            "source_feature_ids",
            "source_peptides",
            "source_precursor_ids",
            "excluded_contributor_ids",
            "exclusion_reason_codes",
            "protein_refs",
            "member_peptides",
            "imputation_method",
        ]
    )
    for row in report.rows:
        writer.writerow(
            [
                row.entity_id,
                row.sample_id,
                row.entity_level.value,
                row.measure_kind.value,
                row.aggregation_method.value,
                "" if row.abundance is None else row.abundance,
                row.missing_value_kind.value,
                row.value_origin.value,
                row.source_feature_count,
                ";".join(row.source_feature_ids),
                ";".join(row.source_peptides),
                ";".join(row.source_precursor_ids),
                ";".join(row.excluded_contributor_ids),
                ";".join(row.exclusion_reason_codes),
                ";".join(row.protein_refs),
                ";".join(row.member_peptides),
                row.imputation_method.value,
            ]
        )
    return buffer.getvalue()


def export_quant_value_provenance_tsv(
    report: QuantValueProvenanceReport,
    path: Path,
) -> None:
    """Write one stable TSV over per-cell quantitative provenance."""

    write_output_table_tsv(path, render_quant_value_provenance_tsv(report))


__all__ = [
    "QuantValueProvenanceReport",
    "QuantValueProvenanceReportRow",
    "QuantValueProvenanceReportSummary",
    "build_quant_value_provenance_report",
    "export_quant_value_provenance_tsv",
    "render_quant_value_provenance_tsv",
]
