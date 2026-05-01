# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Advanced PTM workflow surfaces for review-grade interpretation."""

from __future__ import annotations

from enum import StrEnum

from pydantic import ConfigDict, Field

from bijux_proteomics.ptm import (
    PtmEvidenceRecord,
    PtmOccupancyUncertainty,
    PtmProteinSiteMapping,
    PtmSiteEntry,
    estimate_ptm_site_occupancy,
)
from bijux_proteomics.quantification import Ms1FeatureRecord
from bijux_proteomics_foundation import JsonModel


class PtmSiteLocalizationEvidenceNode(JsonModel):
    """PTM site-localization evidence linked across spectra, peptides, and proteins."""

    model_config = ConfigDict(extra="forbid")

    site_key: str = Field(..., min_length=1)
    protein_ref: str = Field(..., min_length=1)
    residue: str = Field(..., min_length=1, max_length=1)
    protein_position: int = Field(..., ge=1)
    modification_name: str = Field(..., min_length=1)
    psm_spectrum_ids: tuple[str, ...] = Field(default_factory=tuple)
    localized_peptides: tuple[str, ...] = Field(default_factory=tuple)
    peptide_site_indices: tuple[int, ...] = Field(default_factory=tuple)
    candidate_protein_positions: tuple[int, ...] = Field(default_factory=tuple)
    localization_scores: tuple[float, ...] = Field(default_factory=tuple)
    localization_probability: float = Field(..., ge=0.0, le=1.0)
    ambiguous: bool
    fragment_ions: tuple[str, ...] = Field(default_factory=tuple)


class PtmSiteLocalizationEvidenceGraph(JsonModel):
    """Site-level PTM evidence graph for review and handoff."""

    model_config = ConfigDict(extra="forbid")

    nodes: tuple[PtmSiteLocalizationEvidenceNode, ...] = Field(default_factory=tuple)
    source_spectrum_count: int = Field(..., ge=0)
    source_record_count: int = Field(..., ge=0)


class PtmSiteFdrBoundaryDisposition(StrEnum):
    """Disposition for PTM site-level FDR boundary checks."""

    SUPPORTED = "supported"
    REFUSED = "refused"


class PtmSiteFdrBoundaryIssue(JsonModel):
    """One issue explaining why PTM site-level confidence is refused."""

    model_config = ConfigDict(extra="forbid")

    code: str = Field(..., min_length=1)
    message: str = Field(..., min_length=1)


class PtmSiteFdrBoundaryReport(JsonModel):
    """Boundary check result for PTM site-level FDR usage."""

    model_config = ConfigDict(extra="forbid")

    requested_confidence_family: str = Field(..., min_length=1)
    preserve_site_level: bool
    disposition: PtmSiteFdrBoundaryDisposition
    reason: str = Field(..., min_length=1)
    supporting_site_count: int = Field(..., ge=0)
    issues: tuple[PtmSiteFdrBoundaryIssue, ...] = Field(default_factory=tuple)


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
    uncertainty: PtmOccupancyUncertainty
    counterpart_status: PtmOccupancyCounterpartStatus
    caveat: str = Field(..., min_length=1)


class PtmOccupancyCounterpartEvidenceReport(JsonModel):
    """PTM occupancy report preserving counterpart evidence and caveats."""

    model_config = ConfigDict(extra="forbid")

    entries: tuple[PtmOccupancyCounterpartEvidenceEntry, ...] = Field(
        default_factory=tuple
    )
    missing_counterpart_count: int = Field(..., ge=0)
    ambiguous_site_count: int = Field(..., ge=0)


def _to_probability(score: float) -> float:
    """Map non-negative localization score to a bounded probability-like signal."""
    if score <= 0.0:
        return 0.0
    if score <= 1.0:
        return round(score, 4)
    return round(score / (score + 1.0), 4)


def build_ptm_site_localization_evidence_graph(
    records: tuple[PtmEvidenceRecord, ...],
    mappings: tuple[PtmProteinSiteMapping, ...],
    *,
    fragment_ion_support_by_spectrum: dict[str, tuple[str, ...]] | None = None,
) -> PtmSiteLocalizationEvidenceGraph:
    """Build a PTM site-localization evidence graph from records and mappings."""
    record_by_spectrum = {record.spectrum_id: record for record in records}
    grouped: dict[str, list[PtmProteinSiteMapping]] = {}
    for mapping in mappings:
        site_key = (
            f"{mapping.protein_ref}:{mapping.residue}"
            f"{mapping.protein_position}:{mapping.modification_name}"
        )
        grouped.setdefault(site_key, []).append(mapping)

    nodes: list[PtmSiteLocalizationEvidenceNode] = []
    for site_key, bucket in sorted(grouped.items()):
        scores = tuple(sorted((mapping.localization_score for mapping in bucket), reverse=True))
        max_score = scores[0] if scores else 0.0
        spectrum_ids = tuple(sorted({mapping.spectrum_id for mapping in bucket}))
        fragment_ions: set[str] = set()
        if fragment_ion_support_by_spectrum:
            for spectrum_id in spectrum_ids:
                fragment_ions.update(
                    fragment_ion_support_by_spectrum.get(spectrum_id, ())
                )
        peptide_site_indices = tuple(
            sorted({mapping.peptide_site_index for mapping in bucket})
        )
        candidate_positions = tuple(
            sorted(
                {
                    position
                    for mapping in bucket
                    for position in mapping.candidate_protein_positions
                }
            )
        )
        nodes.append(
            PtmSiteLocalizationEvidenceNode(
                site_key=site_key,
                protein_ref=bucket[0].protein_ref,
                residue=bucket[0].residue,
                protein_position=bucket[0].protein_position,
                modification_name=bucket[0].modification_name,
                psm_spectrum_ids=spectrum_ids,
                localized_peptides=tuple(
                    sorted({mapping.localized_peptide for mapping in bucket})
                ),
                peptide_site_indices=peptide_site_indices,
                candidate_protein_positions=candidate_positions,
                localization_scores=scores,
                localization_probability=_to_probability(max_score),
                ambiguous=any(mapping.ambiguous for mapping in bucket),
                fragment_ions=tuple(sorted(fragment_ions)),
            )
        )
    return PtmSiteLocalizationEvidenceGraph(
        nodes=tuple(nodes),
        source_spectrum_count=len(record_by_spectrum),
        source_record_count=len(records),
    )


def evaluate_ptm_site_fdr_boundary(
    site_entries: tuple[PtmSiteEntry, ...],
    *,
    requested_confidence_family: str,
    has_site_level_decoys: bool,
) -> PtmSiteFdrBoundaryReport:
    """Support or refuse PTM site-level FDR without collapsing confidence families."""
    issues: list[PtmSiteFdrBoundaryIssue] = []
    normalized_family = requested_confidence_family.strip().lower()
    if normalized_family != "ptm_site":
        issues.append(
            PtmSiteFdrBoundaryIssue(
                code="non_site_confidence_family",
                message=(
                    "PTM site-level FDR is refused because the requested confidence "
                    "family is not PTM-site specific."
                ),
            )
        )
    if not has_site_level_decoys:
        issues.append(
            PtmSiteFdrBoundaryIssue(
                code="missing_site_level_decoy_support",
                message=(
                    "PTM site-level FDR is refused because site-level decoy or "
                    "entrapment evidence is missing."
                ),
            )
        )
    if not site_entries:
        issues.append(
            PtmSiteFdrBoundaryIssue(
                code="missing_site_evidence",
                message="PTM site-level FDR is refused because no PTM site evidence exists.",
            )
        )
    if issues:
        return PtmSiteFdrBoundaryReport(
            requested_confidence_family=requested_confidence_family,
            preserve_site_level=False,
            disposition=PtmSiteFdrBoundaryDisposition.REFUSED,
            reason=(
                "site-level FDR was refused to avoid collapsing PTM-site confidence "
                "into peptide/protein confidence families"
            ),
            supporting_site_count=len(site_entries),
            issues=tuple(issues),
        )
    return PtmSiteFdrBoundaryReport(
        requested_confidence_family=requested_confidence_family,
        preserve_site_level=True,
        disposition=PtmSiteFdrBoundaryDisposition.SUPPORTED,
        reason=(
            "site-level FDR is supported with PTM-site confidence family and "
            "site-level decoy support"
        ),
        supporting_site_count=len(site_entries),
    )


def build_ptm_occupancy_counterpart_report(
    site_entries: tuple[PtmSiteEntry, ...],
    *,
    feature_records: tuple[Ms1FeatureRecord, ...],
) -> PtmOccupancyCounterpartEvidenceReport:
    """Build occupancy report with counterpart completeness and explicit caveats."""
    occupancy_entries = estimate_ptm_site_occupancy(
        site_entries,
        feature_records=feature_records,
    )
    entries: list[PtmOccupancyCounterpartEvidenceEntry] = []
    for occupancy in occupancy_entries:
        if occupancy.uncertainty is PtmOccupancyUncertainty.AMBIGUOUS_SITE:
            status = PtmOccupancyCounterpartStatus.AMBIGUOUS_SITE
            caveat = "site mapping ambiguity limits interpretation of occupancy estimates"
        elif occupancy.uncertainty is PtmOccupancyUncertainty.MISSING_COUNTERPART:
            status = PtmOccupancyCounterpartStatus.MISSING_COUNTERPART
            caveat = (
                "modified/unmodified counterpart evidence is incomplete, so occupancy "
                "should be interpreted cautiously"
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
                uncertainty=occupancy.uncertainty,
                counterpart_status=status,
                caveat=caveat,
            )
        )
    return PtmOccupancyCounterpartEvidenceReport(
        entries=tuple(entries),
        missing_counterpart_count=sum(
            1
            for entry in entries
            if entry.counterpart_status
            is PtmOccupancyCounterpartStatus.MISSING_COUNTERPART
        ),
        ambiguous_site_count=sum(
            1
            for entry in entries
            if entry.counterpart_status is PtmOccupancyCounterpartStatus.AMBIGUOUS_SITE
        ),
    )
