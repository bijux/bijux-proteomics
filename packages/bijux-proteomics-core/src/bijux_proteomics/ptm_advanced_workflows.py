# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Advanced PTM workflow surfaces for review-grade interpretation."""

from __future__ import annotations

from pydantic import ConfigDict, Field

from bijux_proteomics.ptm import PtmEvidenceRecord, PtmProteinSiteMapping
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
