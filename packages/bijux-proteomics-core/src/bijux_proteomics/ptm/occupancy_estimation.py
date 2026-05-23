# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""PTM occupancy estimation surfaces over localized site and feature evidence."""

from __future__ import annotations

import csv
from enum import StrEnum
from io import StringIO

from pydantic import ConfigDict, Field

from bijux_proteomics.chemistry import parse_modified_peptide
from bijux_proteomics.ptm.contracts import (
    PtmOccupancyConfidenceTier,
    PtmOccupancyEntry,
    PtmOccupancyUncertainty,
    PtmSiteEntry,
)
from bijux_proteomics.quantification.contracts import Ms1FeatureRecord
from bijux_proteomics_foundation import JsonModel


class PtmOccupancyCounterpartStatus(StrEnum):
    """Counterpart-evidence status for one occupancy estimate."""

    COMPLETE = "complete"
    MISSING_COUNTERPART = "missing_counterpart"
    AMBIGUOUS_SITE = "ambiguous_site"


class PtmOccupancyCounterpartEvidenceEntry(JsonModel):
    """One occupancy row with counterpart evidence and caveat semantics."""

    model_config = ConfigDict(extra="forbid")

    site_key: str = Field(..., min_length=1)
    sample_id: str = Field(..., min_length=1)
    modified_intensity: float = Field(..., ge=0.0)
    unmodified_intensity: float = Field(..., ge=0.0)
    occupancy_fraction: float | None = Field(default=None, ge=0.0, le=1.0)
    confidence_tier: PtmOccupancyConfidenceTier
    uncertainty: PtmOccupancyUncertainty
    counterpart_status: PtmOccupancyCounterpartStatus
    modified_peptides: tuple[str, ...] = Field(default_factory=tuple)
    unmodified_peptides: tuple[str, ...] = Field(default_factory=tuple)
    modified_feature_count: int = Field(default=0, ge=0)
    unmodified_feature_count: int = Field(default=0, ge=0)
    caveat: str = Field(..., min_length=1)


class PtmOccupancyCounterpartEvidenceReport(JsonModel):
    """PTM occupancy report preserving counterpart evidence and caveats."""

    model_config = ConfigDict(extra="forbid")

    entries: tuple[PtmOccupancyCounterpartEvidenceEntry, ...] = Field(
        default_factory=tuple
    )
    high_confidence_count: int = Field(..., ge=0)
    missing_counterpart_count: int = Field(..., ge=0)
    missing_unmodified_evidence_count: int = Field(..., ge=0)
    missing_modified_evidence_count: int = Field(..., ge=0)
    ambiguous_site_count: int = Field(..., ge=0)


class PtmSiteOccupancySummary(JsonModel):
    """Compact summary over one PTM occupancy estimation pass."""

    model_config = ConfigDict(extra="forbid")

    entry_count: int = Field(..., ge=0)
    complete_count: int = Field(..., ge=0)
    high_confidence_count: int = Field(..., ge=0)
    missing_counterpart_count: int = Field(..., ge=0)
    missing_unmodified_evidence_count: int = Field(..., ge=0)
    missing_modified_evidence_count: int = Field(..., ge=0)
    ambiguous_site_count: int = Field(..., ge=0)


class PtmSiteOccupancyReport(JsonModel):
    """Owned PTM site occupancy report with explicit counterpart coverage."""

    model_config = ConfigDict(extra="forbid")

    entries: tuple[PtmOccupancyEntry, ...] = Field(default_factory=tuple)
    summary: PtmSiteOccupancySummary
    note: str = Field(..., min_length=1)


def build_ptm_site_occupancy_report(
    site_entries: tuple[PtmSiteEntry, ...],
    *,
    feature_records: tuple[Ms1FeatureRecord, ...],
) -> PtmSiteOccupancyReport:
    """Estimate sample-level PTM occupancy from modified and unmodified peptide evidence."""

    feature_by_sample: dict[str, list[Ms1FeatureRecord]] = {}
    for record in feature_records:
        feature_by_sample.setdefault(record.sample_id, []).append(record)

    occupancy_entries: list[PtmOccupancyEntry] = []
    for entry in site_entries:
        if not entry.sample_ids:
            continue
        localized_peptides = set(entry.localized_peptides)
        stripped_sequences = {
            parse_modified_peptide(peptide).sequence for peptide in entry.localized_peptides
        }
        for sample_id in entry.sample_ids:
            sample_records = feature_by_sample.get(sample_id, [])
            modified_records = [
                record
                for record in sample_records
                if entry.protein_ref in record.protein_refs
                and record.intensity is not None
                and record.canonical_peptide in localized_peptides
            ]
            unmodified_records = [
                record
                for record in sample_records
                if entry.protein_ref in record.protein_refs
                and record.intensity is not None
                and record.canonical_peptide in stripped_sequences
                and record.canonical_peptide not in localized_peptides
            ]
            numerator = float(sum(record.intensity or 0.0 for record in modified_records))
            denominator_unmodified = float(
                sum(record.intensity or 0.0 for record in unmodified_records)
            )
            total = numerator + denominator_unmodified
            if entry.ambiguous:
                confidence_tier = PtmOccupancyConfidenceTier.AMBIGUOUS_SITE
                uncertainty = PtmOccupancyUncertainty.AMBIGUOUS_SITE
                note = (
                    "occupancy remains ambiguous because the PTM site mapping is not unique"
                )
            elif denominator_unmodified == 0.0:
                confidence_tier = (
                    PtmOccupancyConfidenceTier.MISSING_UNMODIFIED_EVIDENCE
                )
                uncertainty = PtmOccupancyUncertainty.MISSING_COUNTERPART
                note = (
                    "unmodified counterpart evidence is missing, so occupancy cannot be treated as high-confidence"
                )
            elif numerator == 0.0:
                confidence_tier = PtmOccupancyConfidenceTier.MISSING_MODIFIED_EVIDENCE
                uncertainty = PtmOccupancyUncertainty.MISSING_COUNTERPART
                note = (
                    "modified counterpart evidence is missing, so occupancy should be treated as a lower-confidence proxy"
                )
            else:
                confidence_tier = PtmOccupancyConfidenceTier.HIGH_CONFIDENCE
                uncertainty = PtmOccupancyUncertainty.NONE
                note = "modified and unmodified counterparts are both observed for this site"
            occupancy_entries.append(
                PtmOccupancyEntry(
                    site_key=entry.site_key,
                    sample_id=sample_id,
                    modified_intensity=numerator,
                    unmodified_intensity=denominator_unmodified,
                    occupancy_fraction=(numerator / total) if total > 0 else None,
                    confidence_tier=confidence_tier,
                    uncertainty=uncertainty,
                    note=note,
                    modified_peptides=tuple(
                        sorted({record.canonical_peptide for record in modified_records})
                    ),
                    unmodified_peptides=tuple(
                        sorted({record.canonical_peptide for record in unmodified_records})
                    ),
                    modified_feature_count=len(modified_records),
                    unmodified_feature_count=len(unmodified_records),
                )
            )

    entries = tuple(
        sorted(occupancy_entries, key=lambda entry: (entry.site_key, entry.sample_id))
    )
    return PtmSiteOccupancyReport(
        entries=entries,
        summary=PtmSiteOccupancySummary(
            entry_count=len(entries),
            complete_count=sum(
                1
                for entry in entries
                if entry.uncertainty is PtmOccupancyUncertainty.NONE
            ),
            high_confidence_count=sum(
                1
                for entry in entries
                if entry.confidence_tier is PtmOccupancyConfidenceTier.HIGH_CONFIDENCE
            ),
            missing_counterpart_count=sum(
                1
                for entry in entries
                if entry.uncertainty is PtmOccupancyUncertainty.MISSING_COUNTERPART
            ),
            missing_unmodified_evidence_count=sum(
                1
                for entry in entries
                if entry.confidence_tier
                is PtmOccupancyConfidenceTier.MISSING_UNMODIFIED_EVIDENCE
            ),
            missing_modified_evidence_count=sum(
                1
                for entry in entries
                if entry.confidence_tier
                is PtmOccupancyConfidenceTier.MISSING_MODIFIED_EVIDENCE
            ),
            ambiguous_site_count=sum(
                1
                for entry in entries
                if entry.uncertainty is PtmOccupancyUncertainty.AMBIGUOUS_SITE
            ),
        ),
        note=(
            "ptm occupancy estimation links localized modified peptide signal to "
            "its unmodified counterpart evidence with explicit coverage and uncertainty"
        ),
    )


def build_ptm_occupancy_counterpart_report(
    site_entries: tuple[PtmSiteEntry, ...],
    *,
    feature_records: tuple[Ms1FeatureRecord, ...],
) -> PtmOccupancyCounterpartEvidenceReport:
    """Build occupancy report with counterpart completeness and explicit caveats."""

    occupancy_report = build_ptm_site_occupancy_report(
        site_entries,
        feature_records=feature_records,
    )
    entries: list[PtmOccupancyCounterpartEvidenceEntry] = []
    for occupancy in occupancy_report.entries:
        if occupancy.confidence_tier is PtmOccupancyConfidenceTier.AMBIGUOUS_SITE:
            status = PtmOccupancyCounterpartStatus.AMBIGUOUS_SITE
            caveat = "site mapping ambiguity limits interpretation of occupancy estimates"
        elif (
            occupancy.confidence_tier
            is PtmOccupancyConfidenceTier.MISSING_UNMODIFIED_EVIDENCE
        ):
            status = PtmOccupancyCounterpartStatus.MISSING_COUNTERPART
            caveat = (
                "unmodified counterpart evidence is missing, so occupancy cannot be treated as high-confidence"
            )
        elif (
            occupancy.confidence_tier
            is PtmOccupancyConfidenceTier.MISSING_MODIFIED_EVIDENCE
        ):
            status = PtmOccupancyCounterpartStatus.MISSING_COUNTERPART
            caveat = (
                "modified counterpart evidence is missing, so occupancy should be interpreted cautiously"
            )
        else:
            status = PtmOccupancyCounterpartStatus.COMPLETE
            caveat = "modified and unmodified counterpart evidence is both present"
        entries.append(
            PtmOccupancyCounterpartEvidenceEntry(
                site_key=occupancy.site_key,
                sample_id=occupancy.sample_id,
                modified_intensity=occupancy.modified_intensity,
                unmodified_intensity=occupancy.unmodified_intensity,
                occupancy_fraction=occupancy.occupancy_fraction,
                confidence_tier=occupancy.confidence_tier,
                uncertainty=occupancy.uncertainty,
                counterpart_status=status,
                modified_peptides=occupancy.modified_peptides,
                unmodified_peptides=occupancy.unmodified_peptides,
                modified_feature_count=occupancy.modified_feature_count,
                unmodified_feature_count=occupancy.unmodified_feature_count,
                caveat=caveat,
            )
        )
    return PtmOccupancyCounterpartEvidenceReport(
        entries=tuple(entries),
        high_confidence_count=sum(
            1
            for entry in entries
            if entry.confidence_tier is PtmOccupancyConfidenceTier.HIGH_CONFIDENCE
        ),
        missing_counterpart_count=sum(
            1
            for entry in entries
            if entry.counterpart_status is PtmOccupancyCounterpartStatus.MISSING_COUNTERPART
        ),
        missing_unmodified_evidence_count=sum(
            1
            for entry in entries
            if entry.confidence_tier
            is PtmOccupancyConfidenceTier.MISSING_UNMODIFIED_EVIDENCE
        ),
        missing_modified_evidence_count=sum(
            1
            for entry in entries
            if entry.confidence_tier
            is PtmOccupancyConfidenceTier.MISSING_MODIFIED_EVIDENCE
        ),
        ambiguous_site_count=sum(
            1
            for entry in entries
            if entry.counterpart_status is PtmOccupancyCounterpartStatus.AMBIGUOUS_SITE
        ),
    )


def render_ptm_site_occupancy_summary_tsv(report: PtmSiteOccupancyReport) -> str:
    """Render compact PTM occupancy summary as TSV."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        [
            "entry_count",
            "complete_count",
            "high_confidence_count",
            "missing_counterpart_count",
            "missing_unmodified_evidence_count",
            "missing_modified_evidence_count",
            "ambiguous_site_count",
        ]
    )
    writer.writerow(
        [
            report.summary.entry_count,
            report.summary.complete_count,
            report.summary.high_confidence_count,
            report.summary.missing_counterpart_count,
            report.summary.missing_unmodified_evidence_count,
            report.summary.missing_modified_evidence_count,
            report.summary.ambiguous_site_count,
        ]
    )
    return buffer.getvalue()


def render_ptm_site_occupancy_entry_tsv(report: PtmSiteOccupancyReport) -> str:
    """Render PTM occupancy entries as TSV."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        [
            "site_key",
            "sample_id",
            "modified_intensity",
            "unmodified_intensity",
            "occupancy_fraction",
            "confidence_tier",
            "uncertainty",
            "modified_peptides",
            "unmodified_peptides",
            "modified_feature_count",
            "unmodified_feature_count",
            "note",
        ]
    )
    for entry in report.entries:
        writer.writerow(
            [
                entry.site_key,
                entry.sample_id,
                entry.modified_intensity,
                entry.unmodified_intensity,
                "" if entry.occupancy_fraction is None else entry.occupancy_fraction,
                entry.confidence_tier.value,
                entry.uncertainty.value,
                ";".join(entry.modified_peptides),
                ";".join(entry.unmodified_peptides),
                entry.modified_feature_count,
                entry.unmodified_feature_count,
                entry.note,
            ]
        )
    return buffer.getvalue()


def render_ptm_occupancy_counterpart_tsv(
    report: PtmOccupancyCounterpartEvidenceReport,
) -> str:
    """Render PTM occupancy counterpart evidence as TSV."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        [
            "site_key",
            "sample_id",
            "modified_intensity",
            "unmodified_intensity",
            "occupancy_fraction",
            "confidence_tier",
            "uncertainty",
            "counterpart_status",
            "modified_peptides",
            "unmodified_peptides",
            "modified_feature_count",
            "unmodified_feature_count",
            "caveat",
        ]
    )
    for entry in report.entries:
        writer.writerow(
            [
                entry.site_key,
                entry.sample_id,
                entry.modified_intensity,
                entry.unmodified_intensity,
                "" if entry.occupancy_fraction is None else entry.occupancy_fraction,
                entry.confidence_tier.value,
                entry.uncertainty.value,
                entry.counterpart_status.value,
                ";".join(entry.modified_peptides),
                ";".join(entry.unmodified_peptides),
                entry.modified_feature_count,
                entry.unmodified_feature_count,
                entry.caveat,
            ]
        )
    return buffer.getvalue()
