# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""PTM ambiguity review and site-group quantification surfaces."""

from __future__ import annotations

import csv
from enum import StrEnum
from io import StringIO
from typing import TYPE_CHECKING

from pydantic import ConfigDict, Field

from bijux_proteomics.io.stable_outputs import sort_rows_by_fields, sort_strings
from bijux_proteomics.ptm.localization.localization_scoring import (
    PtmLocalizationConfidenceTier,
    PtmLocalizationScoringReport,
)
from bijux_proteomics.ptm.sites.site_groups import (
    PtmSiteGroupEvidenceEntry,
    build_ptm_site_group_evidence,
)
from bijux_proteomics.quantification.contracts.input_models import (
    MissingValueKind,
    Ms1FeatureRecord,
    QuantEntityLevel,
)
from bijux_proteomics.quantification.contracts.missingness import (
    MissingValueSummaryEntry,
    MissingValueSummaryPolicy,
    MissingValueSummaryReport,
)
from bijux_proteomics_foundation import JsonModel

if TYPE_CHECKING:
    from bijux_proteomics.ptm.contracts import PtmSiteEntry


class PtmAmbiguityConfidenceTier(StrEnum):
    """Localization-confidence tier for ambiguity-aware PTM reporting."""

    DECISIVE = "decisive"
    SUPPORTED = "supported"
    AMBIGUOUS = "ambiguous"


class PtmLocalizedSiteReviewEntry(JsonModel):
    """One localized PTM site kept as a site-level claim."""

    model_config = ConfigDict(extra="forbid")

    site_key: str = Field(..., min_length=1)
    protein_ref: str = Field(..., min_length=1)
    residue: str = Field(..., min_length=1, max_length=1)
    position: int = Field(..., ge=1)
    modification_name: str = Field(..., min_length=1)
    localized_peptides: tuple[str, ...] = Field(default_factory=tuple)
    sample_ids: tuple[str, ...] = Field(default_factory=tuple)
    localization_score: float = Field(..., ge=0.0)
    localization_probability: float | None = Field(default=None, ge=0.0, le=1.0)
    confidence_tier: PtmAmbiguityConfidenceTier
    note: str = Field(..., min_length=1)


class PtmUnlocalizedSiteGroupReviewEntry(JsonModel):
    """One unresolved PTM site group that should not be overclaimed as one exact site."""

    model_config = ConfigDict(extra="forbid")

    group_key: str = Field(..., min_length=1)
    protein_ref: str = Field(..., min_length=1)
    modification_name: str = Field(..., min_length=1)
    candidate_positions: tuple[int, ...] = Field(default_factory=tuple)
    possible_residues: tuple[str, ...] = Field(default_factory=tuple)
    site_keys: tuple[str, ...] = Field(default_factory=tuple)
    localized_peptides: tuple[str, ...] = Field(default_factory=tuple)
    sample_ids: tuple[str, ...] = Field(default_factory=tuple)
    localization_score: float = Field(..., ge=0.0)
    localization_probability: float | None = Field(default=None, ge=0.0, le=1.0)
    confidence_tier: PtmAmbiguityConfidenceTier
    note: str = Field(..., min_length=1)


class PtmAmbiguityReviewSummary(JsonModel):
    """Compact summary over ambiguity-aware PTM reporting."""

    model_config = ConfigDict(extra="forbid")

    localized_site_count: int = Field(..., ge=0)
    unlocalized_group_count: int = Field(..., ge=0)
    possible_residue_count: int = Field(..., ge=0)
    decisive_localized_site_count: int = Field(..., ge=0)
    ambiguous_group_count: int = Field(..., ge=0)


class PtmAmbiguityReviewReport(JsonModel):
    """Owned PTM ambiguity review over localized sites and unresolved site groups."""

    model_config = ConfigDict(extra="forbid")

    localized_sites: tuple[PtmLocalizedSiteReviewEntry, ...] = Field(
        default_factory=tuple
    )
    unlocalized_groups: tuple[PtmUnlocalizedSiteGroupReviewEntry, ...] = Field(
        default_factory=tuple
    )
    summary: PtmAmbiguityReviewSummary
    note: str = Field(..., min_length=1)


class PtmSiteGroupQuantValue(JsonModel):
    """One sample-specific PTM ambiguity-group quantification cell."""

    model_config = ConfigDict(extra="forbid")

    sample_id: str = Field(..., min_length=1)
    abundance: float | None = Field(default=None, ge=0.0)
    missing_value_kind: MissingValueKind
    contributing_feature_count: int = Field(..., ge=0)


class PtmSiteGroupQuantRow(JsonModel):
    """One unresolved PTM ambiguity group across all quantified samples."""

    model_config = ConfigDict(extra="forbid")

    group_key: str = Field(..., min_length=1)
    protein_ref: str = Field(..., min_length=1)
    modification_name: str = Field(..., min_length=1)
    candidate_positions: tuple[int, ...] = Field(default_factory=tuple)
    possible_residues: tuple[str, ...] = Field(default_factory=tuple)
    site_keys: tuple[str, ...] = Field(default_factory=tuple)
    localized_peptides: tuple[str, ...] = Field(default_factory=tuple)
    localization_score: float = Field(..., ge=0.0)
    localization_probability: float | None = Field(default=None, ge=0.0, le=1.0)
    confidence_tier: PtmAmbiguityConfidenceTier
    values: tuple[PtmSiteGroupQuantValue, ...] = Field(default_factory=tuple)


class PtmSiteGroupQuantSummary(JsonModel):
    """Compact summary over ambiguity-group quantification."""

    model_config = ConfigDict(extra="forbid")

    group_row_count: int = Field(..., ge=0)
    sample_count: int = Field(..., ge=0)
    observed_cell_count: int = Field(..., ge=0)
    zero_cell_count: int = Field(..., ge=0)
    missing_cell_count: int = Field(..., ge=0)
    filtered_cell_count: int = Field(..., ge=0)


class PtmSiteGroupQuantificationReport(JsonModel):
    """Owned PTM quantification report over unresolved site groups."""

    model_config = ConfigDict(extra="forbid")

    sample_ids: tuple[str, ...] = Field(default_factory=tuple)
    rows: tuple[PtmSiteGroupQuantRow, ...] = Field(default_factory=tuple)
    missing_summary: MissingValueSummaryReport
    summary: PtmSiteGroupQuantSummary
    note: str = Field(..., min_length=1)


def build_ptm_ambiguity_review_report(
    site_entries: tuple[PtmSiteEntry, ...],
    *,
    localization_scoring_report: PtmLocalizationScoringReport | None = None,
    protein_sequences: dict[str, str] | None = None,
) -> PtmAmbiguityReviewReport:
    """Separate localized PTM sites from unresolved site groups with confidence context."""

    probability_lookup, tier_lookup = _build_localization_lookup(
        localization_scoring_report
    )
    site_by_key = {entry.site_key: entry for entry in site_entries}

    localized_sites = tuple(
        PtmLocalizedSiteReviewEntry(
            site_key=entry.site_key,
            protein_ref=entry.protein_ref,
            residue=entry.residue,
            position=entry.position,
            modification_name=entry.modification_name,
            localized_peptides=entry.localized_peptides,
            sample_ids=entry.sample_ids,
            localization_score=entry.localization_score,
            localization_probability=_site_probability(entry, probability_lookup),
            confidence_tier=_confidence_tier(
                ambiguous=False,
                localization_score=entry.localization_score,
                localization_probability=_site_probability(entry, probability_lookup),
                localization_tier=_site_tier(entry, tier_lookup),
            ),
            note="site localization resolves to one protein position",
        )
        for entry in site_entries
        if not entry.ambiguous
    )

    unlocalized_groups: list[PtmUnlocalizedSiteGroupReviewEntry] = []
    for group in build_ptm_site_group_evidence(site_entries):
        if not group.unresolved:
            continue
        bucket = [site_by_key[site_key] for site_key in group.site_keys]
        localization_score = max(entry.localization_score for entry in bucket)
        localization_probability = _group_probability(bucket, probability_lookup)
        possible_residues = _possible_residues(
            group,
            bucket=bucket,
            protein_sequences=protein_sequences,
        )
        localized_peptides = tuple(
            sorted(
                {peptide for entry in bucket for peptide in entry.localized_peptides}
            )
        )
        unlocalized_groups.append(
            PtmUnlocalizedSiteGroupReviewEntry(
                group_key=group.group_key,
                protein_ref=group.protein_ref,
                modification_name=group.modification_name,
                candidate_positions=group.candidate_positions,
                possible_residues=possible_residues,
                site_keys=group.site_keys,
                localized_peptides=localized_peptides,
                sample_ids=group.sample_ids,
                localization_score=localization_score,
                localization_probability=localization_probability,
                confidence_tier=_confidence_tier(
                    ambiguous=True,
                    localization_score=localization_score,
                    localization_probability=localization_probability,
                    localization_tier=_group_tier(bucket, tier_lookup),
                ),
                note=(
                    "site evidence remains unresolved and should travel as one ambiguity group rather than one exact site"
                ),
            )
        )

    localized_site_entries = tuple(
        sorted(localized_sites, key=lambda entry: entry.site_key)
    )
    unlocalized_group_entries = tuple(
        sorted(unlocalized_groups, key=lambda entry: entry.group_key)
    )
    return PtmAmbiguityReviewReport(
        localized_sites=localized_site_entries,
        unlocalized_groups=unlocalized_group_entries,
        summary=PtmAmbiguityReviewSummary(
            localized_site_count=len(localized_site_entries),
            unlocalized_group_count=len(unlocalized_group_entries),
            possible_residue_count=sum(
                len(entry.possible_residues) for entry in unlocalized_group_entries
            ),
            decisive_localized_site_count=sum(
                1
                for entry in localized_site_entries
                if entry.confidence_tier is PtmAmbiguityConfidenceTier.DECISIVE
            ),
            ambiguous_group_count=sum(
                1
                for entry in unlocalized_group_entries
                if entry.confidence_tier is PtmAmbiguityConfidenceTier.AMBIGUOUS
            ),
        ),
        note=(
            "ptm ambiguity review separates localized site claims from unresolved site groups, preserves possible residues, and carries forward localization confidence"
        ),
    )


def build_ptm_site_group_quantification_report(
    site_entries: tuple[PtmSiteEntry, ...],
    *,
    feature_records: tuple[Ms1FeatureRecord, ...],
    localization_scoring_report: PtmLocalizationScoringReport | None = None,
    protein_sequences: dict[str, str] | None = None,
) -> PtmSiteGroupQuantificationReport:
    """Quantify unresolved PTM site groups without overclaiming one exact site."""

    review = build_ptm_ambiguity_review_report(
        site_entries,
        localization_scoring_report=localization_scoring_report,
        protein_sequences=protein_sequences,
    )
    sample_ids = tuple(
        sorted(
            {record.sample_id for record in feature_records}
            | {
                sample_id
                for entry in review.unlocalized_groups
                for sample_id in entry.sample_ids
            }
        )
    )
    feature_lookup: dict[tuple[str, str], list[Ms1FeatureRecord]] = {}
    for record in feature_records:
        for protein_ref in record.protein_refs:
            feature_lookup.setdefault((record.sample_id, protein_ref), []).append(
                record
            )

    rows: list[PtmSiteGroupQuantRow] = []
    missing_entries: list[MissingValueSummaryEntry] = []
    grouped_values: dict[tuple[str, str], PtmSiteGroupQuantValue] = {}
    observed_cell_count = 0
    zero_cell_count = 0
    missing_cell_count = 0
    filtered_cell_count = 0
    for entry in review.unlocalized_groups:
        peptides = set(entry.localized_peptides)
        values: list[PtmSiteGroupQuantValue] = []
        for sample_id in sample_ids:
            matching_records = [
                record
                for record in feature_lookup.get((sample_id, entry.protein_ref), ())
                if record.canonical_peptide in peptides
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
            abundance = float(sum(observed_values)) if observed_values else None
            if missing_kind is MissingValueKind.OBSERVED:
                observed_cell_count += 1
            elif missing_kind is MissingValueKind.ZERO:
                zero_cell_count += 1
            elif missing_kind is MissingValueKind.FILTERED:
                filtered_cell_count += 1
            else:
                missing_cell_count += 1
            value = PtmSiteGroupQuantValue(
                sample_id=sample_id,
                abundance=abundance,
                missing_value_kind=missing_kind,
                contributing_feature_count=len(matching_records),
            )
            grouped_values[(entry.group_key, sample_id)] = value
            values.append(value)
        rows.append(
            PtmSiteGroupQuantRow(
                group_key=entry.group_key,
                protein_ref=entry.protein_ref,
                modification_name=entry.modification_name,
                candidate_positions=entry.candidate_positions,
                possible_residues=entry.possible_residues,
                site_keys=entry.site_keys,
                localized_peptides=entry.localized_peptides,
                localization_score=entry.localization_score,
                localization_probability=entry.localization_probability,
                confidence_tier=entry.confidence_tier,
                values=tuple(values),
            )
        )

    for sample_id in sample_ids:
        observed = 0
        zero = 0
        not_observed = 0
        filtered = 0
        for row in rows:
            value = grouped_values[(row.group_key, sample_id)]
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

    return PtmSiteGroupQuantificationReport(
        sample_ids=sample_ids,
        rows=tuple(rows),
        missing_summary=MissingValueSummaryReport(
            entity_level=QuantEntityLevel.PEPTIDE,
            policy=MissingValueSummaryPolicy(),
            entries=tuple(missing_entries),
            included_entity_ids=tuple(row.group_key for row in rows),
            excluded_entity_ids=(),
        ),
        summary=PtmSiteGroupQuantSummary(
            group_row_count=len(rows),
            sample_count=len(sample_ids),
            observed_cell_count=observed_cell_count,
            zero_cell_count=zero_cell_count,
            missing_cell_count=missing_cell_count,
            filtered_cell_count=filtered_cell_count,
        ),
        note=(
            "ptm site-group quantification preserves unresolved localization as one ambiguity group and quantifies unique localized-peptide feature signal without duplicating candidate-site rows"
        ),
    )


def render_ptm_ambiguity_review_summary_tsv(report: PtmAmbiguityReviewReport) -> str:
    """Render compact PTM ambiguity review summary as TSV."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        [
            "localized_site_count",
            "unlocalized_group_count",
            "possible_residue_count",
            "decisive_localized_site_count",
            "ambiguous_group_count",
        ]
    )
    writer.writerow(
        [
            report.summary.localized_site_count,
            report.summary.unlocalized_group_count,
            report.summary.possible_residue_count,
            report.summary.decisive_localized_site_count,
            report.summary.ambiguous_group_count,
        ]
    )
    return buffer.getvalue()


def render_ptm_localized_site_review_tsv(report: PtmAmbiguityReviewReport) -> str:
    """Render localized PTM site claims as TSV."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        [
            "site_key",
            "protein_ref",
            "residue",
            "position",
            "modification_name",
            "localized_peptides",
            "sample_ids",
            "localization_score",
            "localization_probability",
            "confidence_tier",
            "note",
        ]
    )
    for entry in sort_rows_by_fields(report.localized_sites, "site_key"):
        writer.writerow(
            [
                entry.site_key,
                entry.protein_ref,
                entry.residue,
                entry.position,
                entry.modification_name,
                ";".join(sort_strings(entry.localized_peptides)),
                ";".join(sort_strings(entry.sample_ids)),
                entry.localization_score,
                ""
                if entry.localization_probability is None
                else entry.localization_probability,
                entry.confidence_tier.value,
                entry.note,
            ]
        )
    return buffer.getvalue()


def render_ptm_unlocalized_group_review_tsv(report: PtmAmbiguityReviewReport) -> str:
    """Render unresolved PTM ambiguity groups as TSV."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        [
            "group_key",
            "protein_ref",
            "modification_name",
            "candidate_positions",
            "possible_residues",
            "site_keys",
            "localized_peptides",
            "sample_ids",
            "localization_score",
            "localization_probability",
            "confidence_tier",
            "note",
        ]
    )
    for entry in sort_rows_by_fields(report.unlocalized_groups, "group_key"):
        writer.writerow(
            [
                entry.group_key,
                entry.protein_ref,
                entry.modification_name,
                ";".join(
                    str(position) for position in sorted(entry.candidate_positions)
                ),
                ";".join(sort_strings(entry.possible_residues)),
                ";".join(sort_strings(entry.site_keys)),
                ";".join(sort_strings(entry.localized_peptides)),
                ";".join(sort_strings(entry.sample_ids)),
                entry.localization_score,
                ""
                if entry.localization_probability is None
                else entry.localization_probability,
                entry.confidence_tier.value,
                entry.note,
            ]
        )
    return buffer.getvalue()


def render_ptm_site_group_quant_summary_tsv(
    report: PtmSiteGroupQuantificationReport,
) -> str:
    """Render compact ambiguity-group quantification summary as TSV."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        [
            "group_row_count",
            "sample_count",
            "observed_cell_count",
            "zero_cell_count",
            "missing_cell_count",
            "filtered_cell_count",
        ]
    )
    writer.writerow(
        [
            report.summary.group_row_count,
            report.summary.sample_count,
            report.summary.observed_cell_count,
            report.summary.zero_cell_count,
            report.summary.missing_cell_count,
            report.summary.filtered_cell_count,
        ]
    )
    return buffer.getvalue()


def render_ptm_site_group_quant_matrix_tsv(
    report: PtmSiteGroupQuantificationReport,
) -> str:
    """Render ambiguity-group abundance matrix as TSV."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        [
            "group_key",
            "protein_ref",
            "modification_name",
            "candidate_positions",
            "possible_residues",
            "confidence_tier",
            *sorted(report.sample_ids),
        ]
    )
    sample_ids = tuple(sorted(report.sample_ids))
    for row in sort_rows_by_fields(report.rows, "group_key"):
        value_lookup = {value.sample_id: value for value in row.values}
        writer.writerow(
            [
                row.group_key,
                row.protein_ref,
                row.modification_name,
                ";".join(str(position) for position in sorted(row.candidate_positions)),
                ";".join(sort_strings(row.possible_residues)),
                row.confidence_tier.value,
                *[
                    ""
                    if value_lookup[sample_id].abundance is None
                    else value_lookup[sample_id].abundance
                    for sample_id in sample_ids
                ],
            ]
        )
    return buffer.getvalue()


def render_ptm_site_group_quant_missingness_tsv(
    report: PtmSiteGroupQuantificationReport,
) -> str:
    """Render ambiguity-group missingness by sample as TSV."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        [
            "sample_id",
            "observed_count",
            "zero_count",
            "not_observed_count",
            "filtered_count",
        ]
    )
    for entry in sort_rows_by_fields(report.missing_summary.entries, "sample_id"):
        writer.writerow(
            [
                entry.sample_id,
                entry.observed_count,
                entry.zero_count,
                entry.not_observed_count,
                entry.filtered_count,
            ]
        )
    return buffer.getvalue()


def _build_localization_lookup(
    report: PtmLocalizationScoringReport | None,
) -> tuple[
    dict[tuple[str, str], float],
    dict[tuple[str, str], PtmLocalizationConfidenceTier],
]:
    if report is None:
        return {}, {}
    grouped: dict[tuple[str, str], list[float]] = {}
    tier_grouped: dict[tuple[str, str], list[PtmLocalizationConfidenceTier]] = {}
    for entry in report.entries:
        grouped.setdefault(
            (entry.localized_peptide, entry.modification_name),
            [],
        ).append(entry.localization_probability)
        tier_grouped.setdefault(
            (entry.localized_peptide, entry.modification_name),
            [],
        ).append(entry.localization_tier)
    return (
        {key: round(sum(values) / len(values), 4) for key, values in grouped.items()},
        {
            key: max(values, key=_localization_tier_rank)
            for key, values in tier_grouped.items()
        },
    )


def _site_probability(
    entry: PtmSiteEntry,
    probability_lookup: dict[tuple[str, str], float],
) -> float | None:
    probabilities = [
        probability_lookup[(peptide, entry.modification_name)]
        for peptide in entry.localized_peptides
        if (peptide, entry.modification_name) in probability_lookup
    ]
    if not probabilities:
        return None
    return round(sum(probabilities) / len(probabilities), 4)


def _group_probability(
    entries: list[PtmSiteEntry],
    probability_lookup: dict[tuple[str, str], float],
) -> float | None:
    probabilities = [
        probability
        for entry in entries
        for peptide in entry.localized_peptides
        if (probability := probability_lookup.get((peptide, entry.modification_name)))
        is not None
    ]
    if not probabilities:
        return None
    return round(sum(probabilities) / len(probabilities), 4)


def _site_tier(
    entry: PtmSiteEntry,
    tier_lookup: dict[tuple[str, str], PtmLocalizationConfidenceTier],
) -> PtmLocalizationConfidenceTier | None:
    tiers = [
        tier_lookup[(peptide, entry.modification_name)]
        for peptide in entry.localized_peptides
        if (peptide, entry.modification_name) in tier_lookup
    ]
    if not tiers:
        return None
    return max(tiers, key=_localization_tier_rank)


def _group_tier(
    entries: list[PtmSiteEntry],
    tier_lookup: dict[tuple[str, str], PtmLocalizationConfidenceTier],
) -> PtmLocalizationConfidenceTier | None:
    tiers = [
        tier
        for entry in entries
        for peptide in entry.localized_peptides
        if (tier := tier_lookup.get((peptide, entry.modification_name))) is not None
    ]
    if not tiers:
        return None
    return max(tiers, key=_localization_tier_rank)


def _confidence_tier(
    *,
    ambiguous: bool,
    localization_score: float,
    localization_probability: float | None,
    localization_tier: PtmLocalizationConfidenceTier | None,
) -> PtmAmbiguityConfidenceTier:
    if localization_tier is PtmLocalizationConfidenceTier.HIGH_CONFIDENCE:
        return PtmAmbiguityConfidenceTier.DECISIVE
    if localization_tier is PtmLocalizationConfidenceTier.AMBIGUOUS:
        return PtmAmbiguityConfidenceTier.AMBIGUOUS
    if localization_tier is PtmLocalizationConfidenceTier.SUPPORTED:
        return PtmAmbiguityConfidenceTier.SUPPORTED
    if not ambiguous and (
        localization_probability is not None
        and localization_probability >= 0.95
        or localization_score >= 0.95
    ):
        return PtmAmbiguityConfidenceTier.DECISIVE
    if ambiguous:
        return (
            PtmAmbiguityConfidenceTier.SUPPORTED
            if localization_probability is not None and localization_probability >= 0.75
            else PtmAmbiguityConfidenceTier.AMBIGUOUS
        )
    return PtmAmbiguityConfidenceTier.SUPPORTED


def _localization_tier_rank(tier: PtmLocalizationConfidenceTier) -> int:
    if tier is PtmLocalizationConfidenceTier.HIGH_CONFIDENCE:
        return 3
    if tier is PtmLocalizationConfidenceTier.SUPPORTED:
        return 2
    if tier is PtmLocalizationConfidenceTier.AMBIGUOUS:
        return 1
    return 0


def _possible_residues(
    group: PtmSiteGroupEvidenceEntry,
    *,
    bucket: list[PtmSiteEntry],
    protein_sequences: dict[str, str] | None,
) -> tuple[str, ...]:
    if protein_sequences is None:
        return tuple(sorted({entry.residue for entry in bucket}))
    sequence = protein_sequences.get(group.protein_ref)
    if sequence is None:
        return tuple(sorted({entry.residue for entry in bucket}))
    residues: list[str] = []
    for position in group.candidate_positions:
        if 1 <= position <= len(sequence):
            residues.append(sequence[position - 1])
    if not residues:
        return tuple(sorted({entry.residue for entry in bucket}))
    return tuple(sorted(set(residues)))


def _aggregate_missing_kind(
    kinds: tuple[MissingValueKind, ...],
) -> MissingValueKind:
    if MissingValueKind.OBSERVED in kinds:
        return MissingValueKind.OBSERVED
    if MissingValueKind.ZERO in kinds:
        return MissingValueKind.ZERO
    if MissingValueKind.FILTERED in kinds:
        return MissingValueKind.FILTERED
    return MissingValueKind.NOT_OBSERVED
