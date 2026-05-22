# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""PTM occupancy estimation surfaces over localized site and feature evidence."""

from __future__ import annotations

from pydantic import ConfigDict, Field

from bijux_proteomics.chemistry import parse_modified_peptide
from bijux_proteomics.ptm.contracts import (
    PtmOccupancyEntry,
    PtmOccupancyUncertainty,
    PtmSiteEntry,
)
from bijux_proteomics.quantification.contracts import Ms1FeatureRecord
from bijux_proteomics_foundation import JsonModel


class PtmSiteOccupancySummary(JsonModel):
    """Compact summary over one PTM occupancy estimation pass."""

    model_config = ConfigDict(extra="forbid")

    entry_count: int = Field(..., ge=0)
    complete_count: int = Field(..., ge=0)
    missing_counterpart_count: int = Field(..., ge=0)
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
                uncertainty = PtmOccupancyUncertainty.AMBIGUOUS_SITE
                note = (
                    "occupancy remains ambiguous because the PTM site mapping is not unique"
                )
            elif numerator == 0.0 or denominator_unmodified == 0.0:
                uncertainty = PtmOccupancyUncertainty.MISSING_COUNTERPART
                note = (
                    "occupancy is missing one counterpart intensity and should be treated cautiously"
                )
            else:
                uncertainty = PtmOccupancyUncertainty.NONE
                note = "modified and unmodified counterparts are both observed for this site"
            occupancy_entries.append(
                PtmOccupancyEntry(
                    site_key=entry.site_key,
                    sample_id=sample_id,
                    modified_intensity=numerator,
                    unmodified_intensity=denominator_unmodified,
                    occupancy_fraction=(numerator / total) if total > 0 else None,
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
            missing_counterpart_count=sum(
                1
                for entry in entries
                if entry.uncertainty is PtmOccupancyUncertainty.MISSING_COUNTERPART
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
