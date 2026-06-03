# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""PTM site-level quantification surfaces over feature intensity evidence."""

from __future__ import annotations

import csv
from enum import StrEnum
from io import StringIO

from pydantic import ConfigDict, Field

from bijux_proteomics.identification import TargetDecoyLabel
from bijux_proteomics.io.stable_outputs import sort_rows_by_fields, sort_strings
from bijux_proteomics.ptm.sites.ambiguity_handling import (
    PtmSiteGroupQuantificationReport,
    build_ptm_ambiguity_review_report,
    build_ptm_site_group_quantification_report,
)
from bijux_proteomics.ptm.contracts import PtmSiteEntry
from bijux_proteomics.ptm.localization.localization_scoring import (
    PtmLocalizationConfidenceTier,
)
from bijux_proteomics.quantification.contracts import (
    MissingValueKind,
    MissingValueSummaryEntry,
    MissingValueSummaryPolicy,
    MissingValueSummaryReport,
    Ms1FeatureRecord,
    QuantEntityLevel,
)
from bijux_proteomics_foundation import JsonModel


class PtmSiteQuantAmbiguityPolicy(StrEnum):
    """Policy for PTM sites whose localization remains ambiguous."""

    PRESERVE = "preserve"
    EXCLUDE = "exclude"


class PtmSiteQuantValue(JsonModel):
    """One sample-specific PTM site quantification cell."""

    model_config = ConfigDict(extra="forbid")

    sample_id: str = Field(..., min_length=1)
    abundance: float | None = Field(default=None, ge=0.0)
    missing_value_kind: MissingValueKind
    contributing_feature_count: int = Field(..., ge=0)


class PtmSiteQuantRow(JsonModel):
    """One PTM site row across all quantified samples."""

    model_config = ConfigDict(extra="forbid")

    site_key: str = Field(..., min_length=1)
    protein_ref: str = Field(..., min_length=1)
    residue: str = Field(..., min_length=1, max_length=1)
    position: int = Field(..., ge=1)
    modification_name: str = Field(..., min_length=1)
    target_decoy_label: TargetDecoyLabel
    localization_tier: PtmLocalizationConfidenceTier
    ambiguous: bool = False
    shared_peptide: bool = False
    candidate_positions: tuple[int, ...] = Field(default_factory=tuple)
    localized_peptides: tuple[str, ...] = Field(default_factory=tuple)
    values: tuple[PtmSiteQuantValue, ...] = Field(default_factory=tuple)


class PtmSiteQuantSummary(JsonModel):
    """Compact summary over one PTM site quantification review."""

    model_config = ConfigDict(extra="forbid")

    site_row_count: int = Field(..., ge=0)
    sample_count: int = Field(..., ge=0)
    ambiguous_row_count: int = Field(..., ge=0)
    ambiguous_group_row_count: int = Field(..., ge=0)
    excluded_ambiguous_row_count: int = Field(..., ge=0)
    observed_cell_count: int = Field(..., ge=0)
    zero_cell_count: int = Field(..., ge=0)
    missing_cell_count: int = Field(..., ge=0)
    filtered_cell_count: int = Field(..., ge=0)


class PtmExcludedAmbiguousSiteRow(JsonModel):
    """One unresolved site-level claim excluded from the exact-site matrix."""

    model_config = ConfigDict(extra="forbid")

    site_key: str = Field(..., min_length=1)
    group_key: str = Field(..., min_length=1)
    protein_ref: str = Field(..., min_length=1)
    residue: str = Field(..., min_length=1, max_length=1)
    position: int = Field(..., ge=1)
    modification_name: str = Field(..., min_length=1)
    candidate_positions: tuple[int, ...] = Field(default_factory=tuple)
    localized_peptides: tuple[str, ...] = Field(default_factory=tuple)
    sample_ids: tuple[str, ...] = Field(default_factory=tuple)
    reason: str = Field(..., min_length=1)


class PtmSiteQuantificationReport(JsonModel):
    """Owned PTM site-by-sample quantification report."""

    model_config = ConfigDict(extra="forbid")

    ambiguity_policy: PtmSiteQuantAmbiguityPolicy
    sample_ids: tuple[str, ...] = Field(default_factory=tuple)
    rows: tuple[PtmSiteQuantRow, ...] = Field(default_factory=tuple)
    ambiguous_group_quantification: PtmSiteGroupQuantificationReport | None = None
    excluded_ambiguous_rows: tuple[PtmExcludedAmbiguousSiteRow, ...] = Field(
        default_factory=tuple
    )
    excluded_ambiguous_site_keys: tuple[str, ...] = Field(default_factory=tuple)
    missing_summary: MissingValueSummaryReport
    summary: PtmSiteQuantSummary
    note: str = Field(..., min_length=1)


def build_ptm_site_quantification_report(
    site_entries: tuple[PtmSiteEntry, ...],
    *,
    feature_records: tuple[Ms1FeatureRecord, ...],
    ambiguity_policy: PtmSiteQuantAmbiguityPolicy = PtmSiteQuantAmbiguityPolicy.PRESERVE,
) -> PtmSiteQuantificationReport:
    """Build a PTM site-by-sample intensity matrix from localized peptide features."""

    ambiguity_review = build_ptm_ambiguity_review_report(site_entries)
    exact_site_keys = {entry.site_key for entry in ambiguity_review.localized_sites}
    ambiguous_site_keys = {
        site_key
        for group in ambiguity_review.unlocalized_groups
        for site_key in group.site_keys
    }
    exact_site_entries = tuple(
        sorted(
            (
                entry
                for entry in site_entries
                if entry.site_key in exact_site_keys
            ),
            key=lambda row: row.site_key,
        )
    )

    sample_ids = tuple(
        sorted(
            {
                record.sample_id
                for record in feature_records
            }
            | {
                sample_id
                for entry in exact_site_entries
                for sample_id in entry.sample_ids
            }
        )
    )

    feature_lookup: dict[tuple[str, str], list[Ms1FeatureRecord]] = {}
    for record in feature_records:
        for protein_ref in record.protein_refs:
            feature_lookup.setdefault((record.sample_id, protein_ref), []).append(record)

    rows: list[PtmSiteQuantRow] = []
    missing_entries: list[MissingValueSummaryEntry] = []
    excluded_ambiguous_rows: list[PtmExcludedAmbiguousSiteRow] = []
    observed_cell_count = 0
    zero_cell_count = 0
    missing_cell_count = 0
    filtered_cell_count = 0

    grouped_rows: dict[tuple[str, str], PtmSiteQuantValue] = {}
    for entry in exact_site_entries:
        localized_peptides = set(entry.localized_peptides)
        values: list[PtmSiteQuantValue] = []
        for sample_id in sample_ids:
            matching_records = [
                record
                for record in feature_lookup.get((sample_id, entry.protein_ref), ())
                if record.canonical_peptide in localized_peptides
            ]
            missing_kind = _aggregate_missing_kind(
                tuple(record.missing_value_kind for record in matching_records)
                or (MissingValueKind.NOT_OBSERVED,)
            )
            observed_values = tuple(
                record.intensity
                for record in matching_records
                if record.intensity is not None
                and record.missing_value_kind
                in (MissingValueKind.OBSERVED, MissingValueKind.ZERO)
            )
            abundance = (
                float(sum(observed_values)) if observed_values else None
            )
            if missing_kind is MissingValueKind.OBSERVED:
                observed_cell_count += 1
            elif missing_kind is MissingValueKind.ZERO:
                zero_cell_count += 1
            elif missing_kind is MissingValueKind.FILTERED:
                filtered_cell_count += 1
            else:
                missing_cell_count += 1
            value = PtmSiteQuantValue(
                sample_id=sample_id,
                abundance=abundance,
                missing_value_kind=missing_kind,
                contributing_feature_count=len(matching_records),
            )
            grouped_rows[(entry.site_key, sample_id)] = value
            values.append(value)
        rows.append(
            PtmSiteQuantRow(
                site_key=entry.site_key,
                protein_ref=entry.protein_ref,
                residue=entry.residue,
                position=entry.position,
                modification_name=entry.modification_name,
                target_decoy_label=entry.target_decoy_label,
                localization_tier=_infer_site_localization_tier(entry),
                ambiguous=entry.ambiguous,
                shared_peptide=entry.shared_peptide,
                candidate_positions=entry.candidate_positions,
                localized_peptides=entry.localized_peptides,
                values=tuple(values),
            )
        )

    site_entry_by_key = {entry.site_key: entry for entry in site_entries}
    for group in ambiguity_review.unlocalized_groups:
        for site_key in group.site_keys:
            entry = site_entry_by_key[site_key]
            excluded_ambiguous_rows.append(
                PtmExcludedAmbiguousSiteRow(
                    site_key=entry.site_key,
                    group_key=group.group_key,
                    protein_ref=entry.protein_ref,
                    residue=entry.residue,
                    position=entry.position,
                    modification_name=entry.modification_name,
                    candidate_positions=entry.candidate_positions,
                    localized_peptides=entry.localized_peptides,
                    sample_ids=entry.sample_ids,
                    reason=(
                        "unresolved localization is excluded from the exact-site matrix and must travel through the ambiguity-group matrix instead"
                    ),
                )
            )

    for sample_id in sample_ids:
        observed = 0
        zero = 0
        not_observed = 0
        filtered = 0
        for row in rows:
            value = grouped_rows[(row.site_key, sample_id)]
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

    ambiguous_group_quantification = None
    if ambiguity_policy is PtmSiteQuantAmbiguityPolicy.PRESERVE:
        ambiguous_group_quantification = build_ptm_site_group_quantification_report(
            site_entries,
            feature_records=feature_records,
        )

    excluded_site_rows = (
        tuple(sort_rows_by_fields(tuple(excluded_ambiguous_rows), "site_key"))
        if ambiguity_policy is PtmSiteQuantAmbiguityPolicy.EXCLUDE
        else ()
    )

    return PtmSiteQuantificationReport(
        ambiguity_policy=ambiguity_policy,
        sample_ids=sample_ids,
        rows=tuple(rows),
        ambiguous_group_quantification=ambiguous_group_quantification,
        excluded_ambiguous_rows=excluded_site_rows,
        excluded_ambiguous_site_keys=tuple(row.site_key for row in excluded_site_rows),
        missing_summary=MissingValueSummaryReport(
            entity_level=QuantEntityLevel.PEPTIDE,
            policy=MissingValueSummaryPolicy(),
            entries=tuple(missing_entries),
            included_entity_ids=tuple(row.site_key for row in rows),
            excluded_entity_ids=(),
        ),
        summary=PtmSiteQuantSummary(
            site_row_count=len(rows),
            sample_count=len(sample_ids),
            ambiguous_row_count=len(ambiguous_site_keys),
            ambiguous_group_row_count=(
                0
                if ambiguous_group_quantification is None
                else len(ambiguous_group_quantification.rows)
            ),
            excluded_ambiguous_row_count=len(excluded_site_rows),
            observed_cell_count=observed_cell_count,
            zero_cell_count=zero_cell_count,
            missing_cell_count=missing_cell_count,
            filtered_cell_count=filtered_cell_count,
        ),
        note=(
            "ptm site quantification builds one exact-site matrix from resolved site "
            "claims, preserves unresolved localization in one ambiguity-group matrix "
            "when requested, and records excluded ambiguous site rows under an "
            "explicit ambiguity policy"
        ),
    )


def render_ptm_site_quant_summary_tsv(report: PtmSiteQuantificationReport) -> str:
    """Render compact PTM site quantification summary as TSV."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        [
            "ambiguity_policy",
            "site_row_count",
            "sample_count",
            "ambiguous_row_count",
            "ambiguous_group_row_count",
            "excluded_ambiguous_row_count",
            "observed_cell_count",
            "zero_cell_count",
            "missing_cell_count",
            "filtered_cell_count",
        ]
    )
    writer.writerow(
        [
            report.ambiguity_policy.value,
            report.summary.site_row_count,
            report.summary.sample_count,
            report.summary.ambiguous_row_count,
            report.summary.ambiguous_group_row_count,
            report.summary.excluded_ambiguous_row_count,
            report.summary.observed_cell_count,
            report.summary.zero_cell_count,
            report.summary.missing_cell_count,
            report.summary.filtered_cell_count,
        ]
    )
    return buffer.getvalue()


def render_ptm_site_quant_matrix_tsv(report: PtmSiteQuantificationReport) -> str:
    """Render the PTM site-by-sample matrix as one wide TSV."""

    sample_ids = tuple(sorted(report.sample_ids))
    header = [
        "site_key",
        "protein_ref",
        "residue",
        "position",
        "modification_name",
        "target_decoy_label",
        "localization_tier",
        "ambiguous",
        "shared_peptide",
        "candidate_positions",
        "localized_peptides",
    ]
    header.extend(sample_ids)
    rows = ["\t".join(header)]
    for row in sort_rows_by_fields(report.rows, "site_key"):
        lookup = {value.sample_id: value for value in row.values}
        matrix_values = []
        for sample_id in sample_ids:
            value = lookup[sample_id]
            matrix_values.append("" if value.abundance is None else f"{value.abundance:g}")
        rows.append(
            "\t".join(
                (
                    row.site_key,
                    row.protein_ref,
                    row.residue,
                    str(row.position),
                    row.modification_name,
                    row.target_decoy_label.value,
                    row.localization_tier.value,
                    str(row.ambiguous).lower(),
                    str(row.shared_peptide).lower(),
                    ";".join(str(position) for position in sorted(row.candidate_positions)),
                    ";".join(sort_strings(row.localized_peptides)),
                    *matrix_values,
                )
            )
        )
    return "\n".join(rows) + "\n"


def render_ptm_site_quant_missingness_tsv(report: PtmSiteQuantificationReport) -> str:
    """Render one per-sample missingness ledger for the PTM site matrix."""

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


def render_ptm_site_quant_excluded_tsv(report: PtmSiteQuantificationReport) -> str:
    """Render the excluded ambiguous PTM site rows as TSV."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        [
            "site_key",
            "group_key",
            "protein_ref",
            "residue",
            "position",
            "modification_name",
            "candidate_positions",
            "localized_peptides",
            "sample_ids",
            "reason",
        ]
    )
    for row in sort_rows_by_fields(report.excluded_ambiguous_rows, "site_key"):
        writer.writerow(
            [
                row.site_key,
                row.group_key,
                row.protein_ref,
                row.residue,
                row.position,
                row.modification_name,
                ";".join(str(position) for position in sorted(row.candidate_positions)),
                ";".join(sort_strings(row.localized_peptides)),
                ";".join(sort_strings(row.sample_ids)),
                row.reason,
            ]
        )
    return buffer.getvalue()


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


def _infer_site_localization_tier(
    entry: PtmSiteEntry,
) -> PtmLocalizationConfidenceTier:
    if entry.ambiguous:
        return PtmLocalizationConfidenceTier.AMBIGUOUS
    if entry.localization_score >= 0.75:
        return PtmLocalizationConfidenceTier.SUPPORTED
    return PtmLocalizationConfidenceTier.REFUSED
