# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Benchmark surfaces for MaxQuant import and quantification fidelity."""

from __future__ import annotations

import csv
from enum import StrEnum
from io import StringIO
from pathlib import Path

from pydantic import ConfigDict, Field

from bijux_proteomics.identification.maxquant_import import (
    MaxquantImportReport,
    MaxquantLfqIntensityEntry,
    MaxquantProteinGroupReviewEntry,
    build_maxquant_import_report,
)
from bijux_proteomics.quantification import LabelFreeQuantTable
from bijux_proteomics.workflow.maxquant_biological_workflow import (
    MaxquantProteinGroupAcceptancePolicy,
    MaxquantProteinGroupAcceptanceReason,
    build_label_free_quant_table_from_maxquant_protein_groups,
)
from bijux_proteomics_foundation import JsonModel


class MaxquantBenchmarkProteinDisposition(StrEnum):
    """Stable benchmark disposition for one MaxQuant protein-group row."""

    ACCEPTED = "accepted"
    FILTERED = "filtered"


class MaxquantBenchmarkSourceProteinGroup(JsonModel):
    """One source-native MaxQuant protein-group row parsed for benchmarking."""

    model_config = ConfigDict(extra="forbid")

    entity_id: str = Field(..., min_length=1)
    protein_ids: tuple[str, ...] = Field(default_factory=tuple)
    majority_protein_ids: tuple[str, ...] = Field(default_factory=tuple)
    reverse_flag: bool = False
    contaminant_flag: bool = False
    only_identified_by_site: bool = False
    observed_lfq_experiment_count: int = Field(..., ge=0)
    lfq_intensities: tuple[MaxquantLfqIntensityEntry, ...] = Field(default_factory=tuple)


class MaxquantBenchmarkProteinIdentityComparison(JsonModel):
    """Accepted protein-group identity comparison between source and Bijux import."""

    model_config = ConfigDict(extra="forbid")

    source_entity_ids: tuple[str, ...] = Field(default_factory=tuple)
    imported_entity_ids: tuple[str, ...] = Field(default_factory=tuple)
    missing_in_import: tuple[str, ...] = Field(default_factory=tuple)
    extra_in_import: tuple[str, ...] = Field(default_factory=tuple)
    matched: bool
    note: str = Field(..., min_length=1)


class MaxquantBenchmarkFilteringComparisonEntry(JsonModel):
    """One explicit filtering comparison between source and imported protein groups."""

    model_config = ConfigDict(extra="forbid")

    entity_id: str = Field(..., min_length=1)
    source_disposition: MaxquantBenchmarkProteinDisposition
    imported_disposition: MaxquantBenchmarkProteinDisposition
    source_reasons: tuple[MaxquantProteinGroupAcceptanceReason, ...] = Field(
        default_factory=tuple
    )
    imported_reasons: tuple[MaxquantProteinGroupAcceptanceReason, ...] = Field(
        default_factory=tuple
    )
    matched: bool


class MaxquantBenchmarkLfqComparisonEntry(JsonModel):
    """One LFQ intensity preservation row between source and Bijux quant bridge."""

    model_config = ConfigDict(extra="forbid")

    entity_id: str = Field(..., min_length=1)
    sample_id: str = Field(..., min_length=1)
    source_intensity: float | None = Field(default=None, ge=0.0)
    imported_intensity: float | None = Field(default=None, ge=0.0)
    absolute_difference: float = Field(..., ge=0.0)
    exact_match: bool


class MaxquantBenchmarkSummary(JsonModel):
    """Compact summary over one MaxQuant fidelity benchmark."""

    model_config = ConfigDict(extra="forbid")

    source_protein_group_count: int = Field(..., ge=0)
    imported_protein_group_count: int = Field(..., ge=0)
    source_accepted_protein_group_count: int = Field(..., ge=0)
    imported_accepted_protein_group_count: int = Field(..., ge=0)
    source_filtered_protein_group_count: int = Field(..., ge=0)
    imported_filtered_protein_group_count: int = Field(..., ge=0)
    missing_in_import_count: int = Field(..., ge=0)
    extra_in_import_count: int = Field(..., ge=0)
    source_lfq_value_count: int = Field(..., ge=0)
    imported_lfq_value_count: int = Field(..., ge=0)
    exact_lfq_value_match_count: int = Field(..., ge=0)
    max_lfq_absolute_difference: float = Field(..., ge=0.0)
    protein_identity_matched: bool
    filtering_matched: bool
    lfq_values_matched: bool


class MaxquantBenchmarkReport(JsonModel):
    """Owned benchmark report over one MaxQuant bundle."""

    model_config = ConfigDict(extra="forbid")

    import_report: MaxquantImportReport
    acceptance_policy: MaxquantProteinGroupAcceptancePolicy
    lfq_table: LabelFreeQuantTable
    protein_identity_comparison: MaxquantBenchmarkProteinIdentityComparison
    filtering_comparisons: tuple[MaxquantBenchmarkFilteringComparisonEntry, ...] = (
        Field(default_factory=tuple)
    )
    lfq_comparisons: tuple[MaxquantBenchmarkLfqComparisonEntry, ...] = Field(
        default_factory=tuple
    )
    summary: MaxquantBenchmarkSummary
    note: str = Field(..., min_length=1)


def build_maxquant_benchmark_report(
    evidence_txt_path: Path,
    *,
    peptides_txt_path: Path,
    protein_groups_txt_path: Path,
    config_path: Path | None = None,
    acceptance_policy: MaxquantProteinGroupAcceptancePolicy | None = None,
) -> MaxquantBenchmarkReport:
    """Compare governed Bijux MaxQuant import behavior against source protein groups."""

    import_report = build_maxquant_import_report(
        evidence_txt_path,
        peptides_txt_path=peptides_txt_path,
        protein_groups_txt_path=protein_groups_txt_path,
        config_path=config_path,
    )
    active_policy = acceptance_policy or MaxquantProteinGroupAcceptancePolicy()
    source_rows = _parse_source_protein_groups(protein_groups_txt_path)
    source_accepted, source_filtered = _evaluate_source_protein_groups(
        source_rows,
        policy=active_policy,
    )
    imported_accepted, imported_filtered = _evaluate_imported_protein_groups(
        import_report.protein_group_rows,
        policy=active_policy,
    )
    lfq_table = build_label_free_quant_table_from_maxquant_protein_groups(
        imported_accepted,
        peptide_rows=import_report.peptide_rows,
    )
    protein_identity_comparison = _build_protein_identity_comparison(
        source_rows=source_accepted,
        imported_rows=imported_accepted,
    )
    filtering_comparisons = _build_filtering_comparisons(
        source_rows=source_rows,
        imported_rows=import_report.protein_group_rows,
        policy=active_policy,
    )
    lfq_comparisons = _build_lfq_comparisons(
        source_rows=source_accepted,
        lfq_table=lfq_table,
    )
    return MaxquantBenchmarkReport(
        import_report=import_report,
        acceptance_policy=active_policy,
        lfq_table=lfq_table,
        protein_identity_comparison=protein_identity_comparison,
        filtering_comparisons=filtering_comparisons,
        lfq_comparisons=lfq_comparisons,
        summary=MaxquantBenchmarkSummary(
            source_protein_group_count=len(source_rows),
            imported_protein_group_count=import_report.summary.protein_group_row_count,
            source_accepted_protein_group_count=len(source_accepted),
            imported_accepted_protein_group_count=len(imported_accepted),
            source_filtered_protein_group_count=len(source_filtered),
            imported_filtered_protein_group_count=len(imported_filtered),
            missing_in_import_count=len(protein_identity_comparison.missing_in_import),
            extra_in_import_count=len(protein_identity_comparison.extra_in_import),
            source_lfq_value_count=len(source_accepted) * len(lfq_table.sample_ids),
            imported_lfq_value_count=len(lfq_comparisons),
            exact_lfq_value_match_count=sum(
                1 for entry in lfq_comparisons if entry.exact_match
            ),
            max_lfq_absolute_difference=max(
                (entry.absolute_difference for entry in lfq_comparisons),
                default=0.0,
            ),
            protein_identity_matched=protein_identity_comparison.matched,
            filtering_matched=all(
                entry.matched for entry in filtering_comparisons
            ),
            lfq_values_matched=all(entry.exact_match for entry in lfq_comparisons),
        ),
        note=(
            "MaxQuant benchmark compares source protein-group acceptance, LFQ intensity preservation, and filtering behavior against the governed Bijux import and quantification bridge"
        ),
    )


def render_maxquant_benchmark_summary_tsv(report: MaxquantBenchmarkReport) -> str:
    """Render a compact MaxQuant benchmark summary as TSV."""

    handle = StringIO()
    writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
    writer.writerow(("field", "value"))
    for field_name, value in (
        ("source_protein_group_count", report.summary.source_protein_group_count),
        ("imported_protein_group_count", report.summary.imported_protein_group_count),
        (
            "source_accepted_protein_group_count",
            report.summary.source_accepted_protein_group_count,
        ),
        (
            "imported_accepted_protein_group_count",
            report.summary.imported_accepted_protein_group_count,
        ),
        (
            "source_filtered_protein_group_count",
            report.summary.source_filtered_protein_group_count,
        ),
        (
            "imported_filtered_protein_group_count",
            report.summary.imported_filtered_protein_group_count,
        ),
        ("missing_in_import_count", report.summary.missing_in_import_count),
        ("extra_in_import_count", report.summary.extra_in_import_count),
        ("source_lfq_value_count", report.summary.source_lfq_value_count),
        ("imported_lfq_value_count", report.summary.imported_lfq_value_count),
        (
            "exact_lfq_value_match_count",
            report.summary.exact_lfq_value_match_count,
        ),
        (
            "max_lfq_absolute_difference",
            f"{report.summary.max_lfq_absolute_difference:g}",
        ),
        (
            "protein_identity_matched",
            str(report.summary.protein_identity_matched).lower(),
        ),
        ("filtering_matched", str(report.summary.filtering_matched).lower()),
        ("lfq_values_matched", str(report.summary.lfq_values_matched).lower()),
        ("note", report.note),
    ):
        writer.writerow((field_name, value))
    return handle.getvalue()


def render_maxquant_protein_identity_comparison_tsv(
    report: MaxquantBenchmarkReport,
) -> str:
    """Render accepted protein identity comparison for one MaxQuant benchmark."""

    comparison = report.protein_identity_comparison
    handle = StringIO()
    writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "source_entity_ids",
            "imported_entity_ids",
            "missing_in_import",
            "extra_in_import",
            "matched",
            "note",
        )
    )
    writer.writerow(
        (
            ";".join(comparison.source_entity_ids),
            ";".join(comparison.imported_entity_ids),
            ";".join(comparison.missing_in_import),
            ";".join(comparison.extra_in_import),
            str(comparison.matched).lower(),
            comparison.note,
        )
    )
    return handle.getvalue()


def render_maxquant_filtering_comparison_tsv(report: MaxquantBenchmarkReport) -> str:
    """Render one MaxQuant filtering comparison ledger as TSV."""

    handle = StringIO()
    writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "entity_id",
            "source_disposition",
            "imported_disposition",
            "source_reasons",
            "imported_reasons",
            "matched",
        )
    )
    for entry in report.filtering_comparisons:
        writer.writerow(
            (
                entry.entity_id,
                entry.source_disposition.value,
                entry.imported_disposition.value,
                ";".join(reason.value for reason in entry.source_reasons),
                ";".join(reason.value for reason in entry.imported_reasons),
                str(entry.matched).lower(),
            )
        )
    return handle.getvalue()


def render_maxquant_lfq_comparison_tsv(report: MaxquantBenchmarkReport) -> str:
    """Render one MaxQuant LFQ intensity comparison ledger as TSV."""

    handle = StringIO()
    writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "entity_id",
            "sample_id",
            "source_intensity",
            "imported_intensity",
            "absolute_difference",
            "exact_match",
        )
    )
    for entry in report.lfq_comparisons:
        writer.writerow(
            (
                entry.entity_id,
                entry.sample_id,
                "" if entry.source_intensity is None else f"{entry.source_intensity:g}",
                (
                    ""
                    if entry.imported_intensity is None
                    else f"{entry.imported_intensity:g}"
                ),
                f"{entry.absolute_difference:g}",
                str(entry.exact_match).lower(),
            )
        )
    return handle.getvalue()


def _parse_source_protein_groups(
    protein_groups_txt_path: Path,
) -> tuple[MaxquantBenchmarkSourceProteinGroup, ...]:
    with protein_groups_txt_path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        if reader.fieldnames is None:
            raise ValueError(
                "maxquant benchmark protein-groups input must include a header row"
            )
        rows: list[MaxquantBenchmarkSourceProteinGroup] = []
        for row in reader:
            normalized = {key: (value or "").strip() for key, value in row.items()}
            lfq_intensities = tuple(
                MaxquantLfqIntensityEntry(
                    experiment_name=column.removeprefix("LFQ intensity ").strip(),
                    intensity=_parse_float(normalized[column]),
                )
                for column in reader.fieldnames
                if column.startswith("LFQ intensity ")
            )
            protein_ids = _split_tokens(normalized.get("Protein IDs", ""))
            majority_protein_ids = _split_tokens(
                normalized.get("Majority protein IDs", "")
            )
            rows.append(
                MaxquantBenchmarkSourceProteinGroup(
                    entity_id=_protein_group_entity_id(
                        majority_protein_ids=majority_protein_ids,
                        protein_ids=protein_ids,
                    ),
                    protein_ids=protein_ids,
                    majority_protein_ids=majority_protein_ids,
                    reverse_flag=_parse_flag(normalized.get("Reverse", "")),
                    contaminant_flag=_parse_flag(
                        normalized.get("Potential contaminant", "")
                    ),
                    only_identified_by_site=_parse_flag(
                        normalized.get("Only identified by site", "")
                    ),
                    observed_lfq_experiment_count=sum(
                        1 for entry in lfq_intensities if entry.intensity > 0.0
                    ),
                    lfq_intensities=lfq_intensities,
                )
            )
    return tuple(rows)


def _evaluate_source_protein_groups(
    rows: tuple[MaxquantBenchmarkSourceProteinGroup, ...],
    *,
    policy: MaxquantProteinGroupAcceptancePolicy,
) -> tuple[
    tuple[MaxquantBenchmarkSourceProteinGroup, ...],
    tuple[MaxquantBenchmarkSourceProteinGroup, ...],
]:
    accepted: list[MaxquantBenchmarkSourceProteinGroup] = []
    filtered: list[MaxquantBenchmarkSourceProteinGroup] = []
    for row in rows:
        reasons = _source_filter_reasons(row, policy=policy)
        if reasons:
            filtered.append(row)
            continue
        accepted.append(row)
    return tuple(accepted), tuple(filtered)


def _evaluate_imported_protein_groups(
    rows: tuple[MaxquantProteinGroupReviewEntry, ...],
    *,
    policy: MaxquantProteinGroupAcceptancePolicy,
) -> tuple[
    tuple[MaxquantProteinGroupReviewEntry, ...],
    tuple[MaxquantProteinGroupReviewEntry, ...],
]:
    accepted: list[MaxquantProteinGroupReviewEntry] = []
    filtered: list[MaxquantProteinGroupReviewEntry] = []
    for row in rows:
        reasons = _imported_filter_reasons(row, policy=policy)
        if reasons:
            filtered.append(row)
            continue
        accepted.append(row)
    return tuple(accepted), tuple(filtered)


def _build_protein_identity_comparison(
    *,
    source_rows: tuple[MaxquantBenchmarkSourceProteinGroup, ...],
    imported_rows: tuple[MaxquantProteinGroupReviewEntry, ...],
) -> MaxquantBenchmarkProteinIdentityComparison:
    source_entity_ids = tuple(sorted(row.entity_id for row in source_rows))
    imported_entity_ids = tuple(
        sorted(_protein_group_entity_id_from_import(row) for row in imported_rows)
    )
    source_set = set(source_entity_ids)
    imported_set = set(imported_entity_ids)
    missing_in_import = tuple(sorted(source_set - imported_set))
    extra_in_import = tuple(sorted(imported_set - source_set))
    return MaxquantBenchmarkProteinIdentityComparison(
        source_entity_ids=source_entity_ids,
        imported_entity_ids=imported_entity_ids,
        missing_in_import=missing_in_import,
        extra_in_import=extra_in_import,
        matched=not missing_in_import and not extra_in_import,
        note=(
            "accepted MaxQuant protein-group identities should match exactly between the source proteinGroups table and the governed Bijux import surface"
        ),
    )


def _build_filtering_comparisons(
    *,
    source_rows: tuple[MaxquantBenchmarkSourceProteinGroup, ...],
    imported_rows: tuple[MaxquantProteinGroupReviewEntry, ...],
    policy: MaxquantProteinGroupAcceptancePolicy,
) -> tuple[MaxquantBenchmarkFilteringComparisonEntry, ...]:
    imported_by_entity = {
        _protein_group_entity_id_from_import(row): row for row in imported_rows
    }
    comparisons: list[MaxquantBenchmarkFilteringComparisonEntry] = []
    for source_row in sorted(source_rows, key=lambda row: row.entity_id):
        imported_row = imported_by_entity.get(source_row.entity_id)
        if imported_row is None:
            comparisons.append(
                MaxquantBenchmarkFilteringComparisonEntry(
                    entity_id=source_row.entity_id,
                    source_disposition=_disposition_from_reasons(
                        _source_filter_reasons(source_row, policy=policy)
                    ),
                    imported_disposition=MaxquantBenchmarkProteinDisposition.FILTERED,
                    source_reasons=_source_filter_reasons(source_row, policy=policy),
                    imported_reasons=(),
                    matched=False,
                )
            )
            continue
        source_reasons = _source_filter_reasons(source_row, policy=policy)
        imported_reasons = _imported_filter_reasons(imported_row, policy=policy)
        comparisons.append(
            MaxquantBenchmarkFilteringComparisonEntry(
                entity_id=source_row.entity_id,
                source_disposition=_disposition_from_reasons(source_reasons),
                imported_disposition=_disposition_from_reasons(imported_reasons),
                source_reasons=source_reasons,
                imported_reasons=imported_reasons,
                matched=source_reasons == imported_reasons,
            )
        )
    return tuple(comparisons)


def _build_lfq_comparisons(
    *,
    source_rows: tuple[MaxquantBenchmarkSourceProteinGroup, ...],
    lfq_table: LabelFreeQuantTable,
) -> tuple[MaxquantBenchmarkLfqComparisonEntry, ...]:
    source_by_entity_sample = {
        (row.entity_id, intensity.experiment_name): (
            intensity.intensity if intensity.intensity > 0.0 else None
        )
        for row in source_rows
        for intensity in row.lfq_intensities
    }
    comparisons: list[MaxquantBenchmarkLfqComparisonEntry] = []
    for value in sorted(
        lfq_table.values,
        key=lambda entry: (entry.entity_id, entry.sample_id),
    ):
        source_intensity = source_by_entity_sample[(value.entity_id, value.sample_id)]
        imported_intensity = value.abundance
        absolute_difference = abs((source_intensity or 0.0) - (imported_intensity or 0.0))
        comparisons.append(
            MaxquantBenchmarkLfqComparisonEntry(
                entity_id=value.entity_id,
                sample_id=value.sample_id,
                source_intensity=source_intensity,
                imported_intensity=imported_intensity,
                absolute_difference=absolute_difference,
                exact_match=source_intensity == imported_intensity,
            )
        )
    return tuple(comparisons)


def _source_filter_reasons(
    row: MaxquantBenchmarkSourceProteinGroup,
    *,
    policy: MaxquantProteinGroupAcceptancePolicy,
) -> tuple[MaxquantProteinGroupAcceptanceReason, ...]:
    reasons: list[MaxquantProteinGroupAcceptanceReason] = []
    if policy.exclude_contaminants and row.contaminant_flag:
        reasons.append(MaxquantProteinGroupAcceptanceReason.CONTAMINANT)
    if policy.exclude_reverse and row.reverse_flag:
        reasons.append(MaxquantProteinGroupAcceptanceReason.REVERSE)
    if policy.exclude_only_identified_by_site and row.only_identified_by_site:
        reasons.append(MaxquantProteinGroupAcceptanceReason.ONLY_IDENTIFIED_BY_SITE)
    if policy.require_protein_refs and not row.protein_ids:
        reasons.append(MaxquantProteinGroupAcceptanceReason.MISSING_PROTEIN_REFS)
    if policy.require_lfq_signal and row.observed_lfq_experiment_count == 0:
        reasons.append(MaxquantProteinGroupAcceptanceReason.MISSING_LFQ_SIGNAL)
    return tuple(reasons)


def _imported_filter_reasons(
    row: MaxquantProteinGroupReviewEntry,
    *,
    policy: MaxquantProteinGroupAcceptancePolicy,
) -> tuple[MaxquantProteinGroupAcceptanceReason, ...]:
    reasons: list[MaxquantProteinGroupAcceptanceReason] = []
    if policy.exclude_contaminants and row.contaminant_flag:
        reasons.append(MaxquantProteinGroupAcceptanceReason.CONTAMINANT)
    if policy.exclude_reverse and row.reverse_flag:
        reasons.append(MaxquantProteinGroupAcceptanceReason.REVERSE)
    if policy.exclude_only_identified_by_site and row.only_identified_by_site:
        reasons.append(MaxquantProteinGroupAcceptanceReason.ONLY_IDENTIFIED_BY_SITE)
    if policy.require_protein_refs and not row.protein_ids:
        reasons.append(MaxquantProteinGroupAcceptanceReason.MISSING_PROTEIN_REFS)
    if policy.require_lfq_signal and not any(
        entry.intensity > 0.0 for entry in row.lfq_intensities
    ):
        reasons.append(MaxquantProteinGroupAcceptanceReason.MISSING_LFQ_SIGNAL)
    return tuple(reasons)


def _disposition_from_reasons(
    reasons: tuple[MaxquantProteinGroupAcceptanceReason, ...],
) -> MaxquantBenchmarkProteinDisposition:
    if reasons:
        return MaxquantBenchmarkProteinDisposition.FILTERED
    return MaxquantBenchmarkProteinDisposition.ACCEPTED


def _protein_group_entity_id(
    *, majority_protein_ids: tuple[str, ...], protein_ids: tuple[str, ...]
) -> str:
    protein_ref_tokens = majority_protein_ids or protein_ids
    if protein_ref_tokens:
        return ";".join(protein_ref_tokens)
    return "unassigned_protein_group"


def _protein_group_entity_id_from_import(row: MaxquantProteinGroupReviewEntry) -> str:
    return _protein_group_entity_id(
        majority_protein_ids=row.majority_protein_ids,
        protein_ids=row.protein_ids,
    )


def _split_tokens(value: str) -> tuple[str, ...]:
    return tuple(token.strip() for token in value.split(";") if token.strip())


def _parse_float(value: str) -> float:
    return float(value) if value else 0.0


def _parse_flag(value: str) -> bool:
    return value.strip().lower() in {"+", "1", "true", "yes"}
