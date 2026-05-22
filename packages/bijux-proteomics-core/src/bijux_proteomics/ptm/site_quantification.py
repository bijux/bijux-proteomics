# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""PTM site-level quantification surfaces over feature intensity evidence."""

from __future__ import annotations

from pydantic import ConfigDict, Field

from bijux_proteomics.identification import TargetDecoyLabel
from bijux_proteomics.ptm.contracts import PtmSiteEntry
from bijux_proteomics.quantification.contracts import (
    MissingValueKind,
    MissingValueSummaryEntry,
    MissingValueSummaryPolicy,
    MissingValueSummaryReport,
    Ms1FeatureRecord,
    QuantEntityLevel,
)
from bijux_proteomics_foundation import JsonModel


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
    observed_cell_count: int = Field(..., ge=0)
    zero_cell_count: int = Field(..., ge=0)
    missing_cell_count: int = Field(..., ge=0)
    filtered_cell_count: int = Field(..., ge=0)


class PtmSiteQuantificationReport(JsonModel):
    """Owned PTM site-by-sample quantification report."""

    model_config = ConfigDict(extra="forbid")

    sample_ids: tuple[str, ...] = Field(default_factory=tuple)
    rows: tuple[PtmSiteQuantRow, ...] = Field(default_factory=tuple)
    missing_summary: MissingValueSummaryReport
    summary: PtmSiteQuantSummary
    note: str = Field(..., min_length=1)


def build_ptm_site_quantification_report(
    site_entries: tuple[PtmSiteEntry, ...],
    *,
    feature_records: tuple[Ms1FeatureRecord, ...],
) -> PtmSiteQuantificationReport:
    """Build a PTM site-by-sample intensity matrix from localized peptide features."""

    sample_ids = tuple(
        sorted(
            {
                record.sample_id
                for record in feature_records
            }
            | {
                sample_id
                for entry in site_entries
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
    observed_cell_count = 0
    zero_cell_count = 0
    missing_cell_count = 0
    filtered_cell_count = 0

    grouped_rows: dict[tuple[str, str], PtmSiteQuantValue] = {}
    for entry in sorted(site_entries, key=lambda row: row.site_key):
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
                ambiguous=entry.ambiguous,
                shared_peptide=entry.shared_peptide,
                candidate_positions=entry.candidate_positions,
                localized_peptides=entry.localized_peptides,
                values=tuple(values),
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

    return PtmSiteQuantificationReport(
        sample_ids=sample_ids,
        rows=tuple(rows),
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
            ambiguous_row_count=sum(1 for row in rows if row.ambiguous),
            observed_cell_count=observed_cell_count,
            zero_cell_count=zero_cell_count,
            missing_cell_count=missing_cell_count,
            filtered_cell_count=filtered_cell_count,
        ),
        note=(
            "ptm site quantification aggregates localized peptide feature intensities "
            "onto protein-mapped PTM sites while preserving per-sample missingness"
        ),
    )


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
