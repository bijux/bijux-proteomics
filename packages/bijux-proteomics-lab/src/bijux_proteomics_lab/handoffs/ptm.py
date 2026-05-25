# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""PTM-specific assay follow-up packets owned by the lab package."""

from __future__ import annotations

from enum import StrEnum
from typing import TYPE_CHECKING

from pydantic import ConfigDict, Field

from bijux_proteomics_foundation import JsonModel

if TYPE_CHECKING:
    from bijux_proteomics.ptm import PtmSiteEntry
    from bijux_proteomics.ptm.review import (
        PtmCooccurrenceCautionReport,
        PtmOccupancyCounterpartEvidenceReport,
    )


class PtmLabAssayRisk(StrEnum):
    """Assay risk class for PTM lab validation planning."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class PtmLabValidationTargetEntry(JsonModel):
    """One PTM target entry for lab validation planning."""

    model_config = ConfigDict(extra="forbid")

    site_key: str = Field(..., min_length=1)
    target_peptides: tuple[str, ...] = Field(default_factory=tuple)
    ambiguous_site: bool
    assay_risk: PtmLabAssayRisk
    recommended_controls: tuple[str, ...] = Field(default_factory=tuple)
    evidence_needs: tuple[str, ...] = Field(default_factory=tuple)


class PtmLabValidationPacket(JsonModel):
    """PTM-to-lab validation packet with risks and evidence requirements."""

    model_config = ConfigDict(extra="forbid")

    entries: tuple[PtmLabValidationTargetEntry, ...] = Field(default_factory=tuple)
    unresolved_risk_count: int = Field(..., ge=0)


def build_ptm_lab_validation_packet(
    site_entries: tuple[PtmSiteEntry, ...],
    *,
    occupancy_report: PtmOccupancyCounterpartEvidenceReport | None = None,
    cooccurrence_report: PtmCooccurrenceCautionReport | None = None,
) -> PtmLabValidationPacket:
    """Build PTM-to-lab validation packet with risk and evidence guidance."""
    from bijux_proteomics.ptm import (
        PtmOccupancyCounterpartEvidenceEntry,
        PtmOccupancyCounterpartStatus,
    )

    occupancy_by_site: dict[str, list[PtmOccupancyCounterpartEvidenceEntry]] = {}
    if occupancy_report is not None:
        for row in occupancy_report.entries:
            occupancy_by_site.setdefault(row.site_key, []).append(row)

    coloc_site_keys: set[str] = set()
    if cooccurrence_report is not None:
        for pair in cooccurrence_report.entries:
            if pair.true_colocalization_evidence:
                coloc_site_keys.add(pair.left_site_key)
                coloc_site_keys.add(pair.right_site_key)

    entries: list[PtmLabValidationTargetEntry] = []
    for site in site_entries:
        occupancy_rows = occupancy_by_site.get(site.site_key, [])
        has_missing_counterpart = any(
            row.counterpart_status is PtmOccupancyCounterpartStatus.MISSING_COUNTERPART
            for row in occupancy_rows
        )
        has_ambiguous_counterpart = any(
            row.counterpart_status is PtmOccupancyCounterpartStatus.AMBIGUOUS_SITE
            for row in occupancy_rows
        )
        if site.ambiguous or has_ambiguous_counterpart:
            risk = PtmLabAssayRisk.HIGH
        elif has_missing_counterpart:
            risk = PtmLabAssayRisk.MEDIUM
        else:
            risk = PtmLabAssayRisk.LOW
        controls = [
            "isotype_or_matrix_control",
            "site-matched_unmodified_peptide_control",
        ]
        if site.site_key in coloc_site_keys:
            controls.append("co-localization_disruption_control")
        evidence_needs = [
            "site-localizing_fragment_ions",
            "orthogonal_site_assay_confirmation",
        ]
        if has_missing_counterpart:
            evidence_needs.append("complete_modified_unmodified_counterpart_quant")
        entries.append(
            PtmLabValidationTargetEntry(
                site_key=site.site_key,
                target_peptides=site.localized_peptides,
                ambiguous_site=site.ambiguous,
                assay_risk=risk,
                recommended_controls=tuple(controls),
                evidence_needs=tuple(evidence_needs),
            )
        )
    return PtmLabValidationPacket(
        entries=tuple(entries),
        unresolved_risk_count=sum(
            1
            for entry in entries
            if entry.assay_risk in {PtmLabAssayRisk.MEDIUM, PtmLabAssayRisk.HIGH}
        ),
    )
