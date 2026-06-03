# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Owned PTM crosstalk surfaces over regulated site evidence."""

from __future__ import annotations

from bijux_proteomics._output_tables import write_output_table_tsv

import csv
from enum import StrEnum
from io import StringIO
from itertools import combinations
from pathlib import Path

from pydantic import ConfigDict, Field

from bijux_proteomics.io.stable_outputs import sort_rows_by_fields
from bijux_proteomics.ptm.contracts import PtmSiteEntry
from bijux_proteomics.ptm.parsing.site_annotation_import import (
    PtmSiteAnnotationMappingReport,
)
from bijux_proteomics.ptm.quant.differential_analysis import PtmSiteDifferentialReport
from bijux_proteomics_foundation import JsonModel


class PtmCrosstalkRelationship(StrEnum):
    """Regulation relationship between two PTM sites."""

    CO_CHANGING = "co_changing"
    OPPOSING = "opposing"


class PtmCrosstalkEvidenceSource(StrEnum):
    """Stable evidence sources supporting one PTM crosstalk pair."""

    SAME_PROTEIN = "same_protein"
    SAME_PEPTIDE = "same_peptide"
    NEARBY_RESIDUES = "nearby_residues"
    SHARED_PATHWAY = "shared_pathway"


class PtmCrosstalkPairEntry(JsonModel):
    """One PTM-site pair connected through owned crosstalk evidence."""

    model_config = ConfigDict(extra="forbid")

    pair_key: str = Field(..., min_length=1)
    relationship: PtmCrosstalkRelationship
    left_site_key: str = Field(..., min_length=1)
    right_site_key: str = Field(..., min_length=1)
    left_protein_ref: str = Field(..., min_length=1)
    right_protein_ref: str = Field(..., min_length=1)
    left_modification_name: str = Field(..., min_length=1)
    right_modification_name: str = Field(..., min_length=1)
    left_position: int = Field(..., ge=1)
    right_position: int = Field(..., ge=1)
    left_log2_fold_change: float
    right_log2_fold_change: float
    left_adjusted_p_value: float | None = Field(default=None, ge=0.0, le=1.0)
    right_adjusted_p_value: float | None = Field(default=None, ge=0.0, le=1.0)
    evidence_sources: tuple[PtmCrosstalkEvidenceSource, ...] = Field(
        default_factory=tuple
    )
    shared_peptides: tuple[str, ...] = Field(default_factory=tuple)
    shared_pathways: tuple[str, ...] = Field(default_factory=tuple)
    residue_distance: int | None = Field(default=None, ge=0)
    evidence_note: str = Field(..., min_length=1)


class PtmProteinCrosstalkMapEntry(JsonModel):
    """Protein-level PTM crosstalk map over one regulated protein surface."""

    model_config = ConfigDict(extra="forbid")

    protein_ref: str = Field(..., min_length=1)
    site_keys: tuple[str, ...] = Field(default_factory=tuple)
    pair_keys: tuple[str, ...] = Field(default_factory=tuple)
    co_changing_pair_count: int = Field(..., ge=0)
    opposing_pair_count: int = Field(..., ge=0)
    pathway_terms: tuple[str, ...] = Field(default_factory=tuple)
    note: str = Field(..., min_length=1)


class PtmCrosstalkSummary(JsonModel):
    """Stable summary over one PTM crosstalk pass."""

    model_config = ConfigDict(extra="forbid")

    differential_site_count: int = Field(..., ge=0)
    pair_count: int = Field(..., ge=0)
    co_changing_pair_count: int = Field(..., ge=0)
    opposing_pair_count: int = Field(..., ge=0)
    same_protein_pair_count: int = Field(..., ge=0)
    same_peptide_pair_count: int = Field(..., ge=0)
    nearby_residue_pair_count: int = Field(..., ge=0)
    shared_pathway_pair_count: int = Field(..., ge=0)
    protein_map_count: int = Field(..., ge=0)


class PtmCrosstalkReport(JsonModel):
    """Owned PTM crosstalk report over regulated site pairs."""

    model_config = ConfigDict(extra="forbid")

    nearby_residue_distance_threshold: int = Field(..., ge=0)
    entries: tuple[PtmCrosstalkPairEntry, ...] = Field(default_factory=tuple)
    protein_maps: tuple[PtmProteinCrosstalkMapEntry, ...] = Field(default_factory=tuple)
    summary: PtmCrosstalkSummary
    note: str = Field(..., min_length=1)


def build_ptm_crosstalk_report(
    site_entries: tuple[PtmSiteEntry, ...],
    differential_report: PtmSiteDifferentialReport,
    *,
    annotation_mapping_report: PtmSiteAnnotationMappingReport | None = None,
    nearby_residue_distance: int = 7,
) -> PtmCrosstalkReport:
    """Connect regulated PTM sites through protein, peptide, distance, and pathway evidence."""

    differential_by_site = {
        entry.site_key: entry for entry in differential_report.entries
    }
    regulated_sites = tuple(
        site_entry
        for site_entry in sort_rows_by_fields(site_entries, "protein_ref", "position", "site_key")
        if site_entry.site_key in differential_by_site
    )
    pathways_by_site = _pathways_by_site(annotation_mapping_report)

    entries: list[PtmCrosstalkPairEntry] = []
    for left_site, right_site in combinations(regulated_sites, 2):
        evidence_sources = _pair_evidence_sources(
            left_site,
            right_site,
            pathways_by_site=pathways_by_site,
            nearby_residue_distance=nearby_residue_distance,
        )
        if not evidence_sources:
            continue
        left_entry = differential_by_site[left_site.site_key]
        right_entry = differential_by_site[right_site.site_key]
        shared_peptides = tuple(
            sorted(
                set(left_site.localized_peptides).intersection(right_site.localized_peptides)
            )
        )
        shared_pathways = tuple(
            sorted(
                pathways_by_site.get(left_site.site_key, set()).intersection(
                    pathways_by_site.get(right_site.site_key, set())
                )
            )
        )
        residue_distance = (
            abs(left_site.position - right_site.position)
            if left_site.protein_ref == right_site.protein_ref
            else None
        )
        entries.append(
            PtmCrosstalkPairEntry(
                pair_key=f"{left_site.site_key}--{right_site.site_key}",
                relationship=_relationship(
                    left_entry.log2_fold_change,
                    right_entry.log2_fold_change,
                ),
                left_site_key=left_site.site_key,
                right_site_key=right_site.site_key,
                left_protein_ref=left_site.protein_ref,
                right_protein_ref=right_site.protein_ref,
                left_modification_name=left_site.modification_name,
                right_modification_name=right_site.modification_name,
                left_position=left_site.position,
                right_position=right_site.position,
                left_log2_fold_change=left_entry.log2_fold_change,
                right_log2_fold_change=right_entry.log2_fold_change,
                left_adjusted_p_value=left_entry.adjusted_p_value,
                right_adjusted_p_value=right_entry.adjusted_p_value,
                evidence_sources=evidence_sources,
                shared_peptides=shared_peptides,
                shared_pathways=shared_pathways,
                residue_distance=residue_distance,
                evidence_note=_evidence_note(
                    left_site,
                    right_site,
                    evidence_sources=evidence_sources,
                    shared_peptides=shared_peptides,
                    shared_pathways=shared_pathways,
                    residue_distance=residue_distance,
                ),
            )
        )

    protein_maps = _build_protein_maps(
        regulated_sites,
        entries=tuple(entries),
        pathways_by_site=pathways_by_site,
    )
    stable_entries = tuple(
        sort_rows_by_fields(
            tuple(entries),
            "left_protein_ref",
            "left_position",
            "right_position",
            "pair_key",
        )
    )
    return PtmCrosstalkReport(
        nearby_residue_distance_threshold=nearby_residue_distance,
        entries=stable_entries,
        protein_maps=protein_maps,
        summary=PtmCrosstalkSummary(
            differential_site_count=len(regulated_sites),
            pair_count=len(stable_entries),
            co_changing_pair_count=sum(
                1
                for entry in stable_entries
                if entry.relationship is PtmCrosstalkRelationship.CO_CHANGING
            ),
            opposing_pair_count=sum(
                1
                for entry in stable_entries
                if entry.relationship is PtmCrosstalkRelationship.OPPOSING
            ),
            same_protein_pair_count=sum(
                1
                for entry in stable_entries
                if PtmCrosstalkEvidenceSource.SAME_PROTEIN in entry.evidence_sources
            ),
            same_peptide_pair_count=sum(
                1
                for entry in stable_entries
                if PtmCrosstalkEvidenceSource.SAME_PEPTIDE in entry.evidence_sources
            ),
            nearby_residue_pair_count=sum(
                1
                for entry in stable_entries
                if PtmCrosstalkEvidenceSource.NEARBY_RESIDUES in entry.evidence_sources
            ),
            shared_pathway_pair_count=sum(
                1
                for entry in stable_entries
                if PtmCrosstalkEvidenceSource.SHARED_PATHWAY in entry.evidence_sources
            ),
            protein_map_count=len(protein_maps),
        ),
        note=(
            "ptm crosstalk preserves exact regulated site pairs, their co-changing or "
            "opposing direction, and the owned evidence connecting them through protein, "
            "peptide, nearby-residue, or shared-pathway context"
        ),
    )


def render_ptm_crosstalk_summary_tsv(report: PtmCrosstalkReport) -> str:
    """Render the compact PTM crosstalk summary as TSV."""

    handle = StringIO()
    writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
    writer.writerow(("field", "value"))
    writer.writerow(("differential_site_count", report.summary.differential_site_count))
    writer.writerow(("pair_count", report.summary.pair_count))
    writer.writerow(("co_changing_pair_count", report.summary.co_changing_pair_count))
    writer.writerow(("opposing_pair_count", report.summary.opposing_pair_count))
    writer.writerow(("same_protein_pair_count", report.summary.same_protein_pair_count))
    writer.writerow(("same_peptide_pair_count", report.summary.same_peptide_pair_count))
    writer.writerow(("nearby_residue_pair_count", report.summary.nearby_residue_pair_count))
    writer.writerow(("shared_pathway_pair_count", report.summary.shared_pathway_pair_count))
    writer.writerow(("protein_map_count", report.summary.protein_map_count))
    writer.writerow(
        ("nearby_residue_distance_threshold", report.nearby_residue_distance_threshold)
    )
    writer.writerow(("note", report.note))
    return handle.getvalue()


def render_ptm_crosstalk_pair_tsv(report: PtmCrosstalkReport) -> str:
    """Render PTM crosstalk pairs as TSV."""

    handle = StringIO()
    writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "pair_key",
            "relationship",
            "left_site_key",
            "right_site_key",
            "left_protein_ref",
            "right_protein_ref",
            "left_modification_name",
            "right_modification_name",
            "left_position",
            "right_position",
            "left_log2_fold_change",
            "right_log2_fold_change",
            "left_adjusted_p_value",
            "right_adjusted_p_value",
            "evidence_sources",
            "shared_peptides",
            "shared_pathways",
            "residue_distance",
            "evidence_note",
        )
    )
    for entry in report.entries:
        writer.writerow(
            (
                entry.pair_key,
                entry.relationship.value,
                entry.left_site_key,
                entry.right_site_key,
                entry.left_protein_ref,
                entry.right_protein_ref,
                entry.left_modification_name,
                entry.right_modification_name,
                entry.left_position,
                entry.right_position,
                entry.left_log2_fold_change,
                entry.right_log2_fold_change,
                "" if entry.left_adjusted_p_value is None else entry.left_adjusted_p_value,
                "" if entry.right_adjusted_p_value is None else entry.right_adjusted_p_value,
                ";".join(source.value for source in entry.evidence_sources),
                ";".join(entry.shared_peptides),
                ";".join(entry.shared_pathways),
                "" if entry.residue_distance is None else entry.residue_distance,
                entry.evidence_note,
            )
        )
    return handle.getvalue()


def render_ptm_crosstalk_protein_map_tsv(report: PtmCrosstalkReport) -> str:
    """Render protein-level PTM crosstalk maps as TSV."""

    handle = StringIO()
    writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "protein_ref",
            "site_keys",
            "pair_keys",
            "co_changing_pair_count",
            "opposing_pair_count",
            "pathway_terms",
            "note",
        )
    )
    for entry in report.protein_maps:
        writer.writerow(
            (
                entry.protein_ref,
                ";".join(entry.site_keys),
                ";".join(entry.pair_keys),
                entry.co_changing_pair_count,
                entry.opposing_pair_count,
                ";".join(entry.pathway_terms),
                entry.note,
            )
        )
    return handle.getvalue()


def export_ptm_crosstalk_summary_tsv(report: PtmCrosstalkReport, path: Path) -> None:
    """Write the PTM crosstalk summary TSV."""

    write_output_table_tsv(path, render_ptm_crosstalk_summary_tsv(report))


def export_ptm_crosstalk_pair_tsv(report: PtmCrosstalkReport, path: Path) -> None:
    """Write the PTM crosstalk pair TSV."""

    write_output_table_tsv(path, render_ptm_crosstalk_pair_tsv(report))


def export_ptm_crosstalk_protein_map_tsv(
    report: PtmCrosstalkReport,
    path: Path,
) -> None:
    """Write the PTM crosstalk protein-map TSV."""

    write_output_table_tsv(path, render_ptm_crosstalk_protein_map_tsv(report))


def _pathways_by_site(
    annotation_mapping_report: PtmSiteAnnotationMappingReport | None,
) -> dict[str, set[str]]:
    if annotation_mapping_report is None:
        return {}
    pathways_by_site: dict[str, set[str]] = {}
    for entry in annotation_mapping_report.matched_annotations:
        if not entry.pathways:
            continue
        pathways_by_site.setdefault(entry.site_key, set()).update(entry.pathways)
    return pathways_by_site


def _pair_evidence_sources(
    left_site: PtmSiteEntry,
    right_site: PtmSiteEntry,
    *,
    pathways_by_site: dict[str, set[str]],
    nearby_residue_distance: int,
) -> tuple[PtmCrosstalkEvidenceSource, ...]:
    evidence_sources: list[PtmCrosstalkEvidenceSource] = []
    if left_site.protein_ref == right_site.protein_ref:
        evidence_sources.append(PtmCrosstalkEvidenceSource.SAME_PROTEIN)
        if abs(left_site.position - right_site.position) <= nearby_residue_distance:
            evidence_sources.append(PtmCrosstalkEvidenceSource.NEARBY_RESIDUES)
    if set(left_site.localized_peptides).intersection(right_site.localized_peptides):
        evidence_sources.append(PtmCrosstalkEvidenceSource.SAME_PEPTIDE)
    if pathways_by_site.get(left_site.site_key, set()).intersection(
        pathways_by_site.get(right_site.site_key, set())
    ):
        evidence_sources.append(PtmCrosstalkEvidenceSource.SHARED_PATHWAY)
    return tuple(evidence_sources)


def _relationship(
    left_log2_fold_change: float,
    right_log2_fold_change: float,
) -> PtmCrosstalkRelationship:
    if left_log2_fold_change * right_log2_fold_change < 0.0:
        return PtmCrosstalkRelationship.OPPOSING
    return PtmCrosstalkRelationship.CO_CHANGING


def _evidence_note(
    left_site: PtmSiteEntry,
    right_site: PtmSiteEntry,
    *,
    evidence_sources: tuple[PtmCrosstalkEvidenceSource, ...],
    shared_peptides: tuple[str, ...],
    shared_pathways: tuple[str, ...],
    residue_distance: int | None,
) -> str:
    clauses: list[str] = []
    if PtmCrosstalkEvidenceSource.SAME_PROTEIN in evidence_sources:
        clauses.append(f"sites share protein {left_site.protein_ref}")
    if PtmCrosstalkEvidenceSource.SAME_PEPTIDE in evidence_sources:
        clauses.append(
            "sites share localized peptide evidence " + ", ".join(shared_peptides)
        )
    if (
        PtmCrosstalkEvidenceSource.NEARBY_RESIDUES in evidence_sources
        and residue_distance is not None
    ):
        clauses.append(f"sites are {residue_distance} residues apart")
    if PtmCrosstalkEvidenceSource.SHARED_PATHWAY in evidence_sources:
        clauses.append("sites share pathways " + ", ".join(shared_pathways))
    return (
        f"{left_site.site_key} and {right_site.site_key} are connected because "
        + "; ".join(clauses)
    )


def _build_protein_maps(
    regulated_sites: tuple[PtmSiteEntry, ...],
    *,
    entries: tuple[PtmCrosstalkPairEntry, ...],
    pathways_by_site: dict[str, set[str]],
) -> tuple[PtmProteinCrosstalkMapEntry, ...]:
    pair_keys_by_protein: dict[str, set[str]] = {}
    cochanging_by_protein: dict[str, int] = {}
    opposing_by_protein: dict[str, int] = {}
    for entry in entries:
        if entry.left_protein_ref != entry.right_protein_ref:
            continue
        protein_ref = entry.left_protein_ref
        pair_keys_by_protein.setdefault(protein_ref, set()).add(entry.pair_key)
        if entry.relationship is PtmCrosstalkRelationship.CO_CHANGING:
            cochanging_by_protein[protein_ref] = (
                cochanging_by_protein.get(protein_ref, 0) + 1
            )
        else:
            opposing_by_protein[protein_ref] = (
                opposing_by_protein.get(protein_ref, 0) + 1
            )

    site_keys_by_protein: dict[str, list[str]] = {}
    pathway_terms_by_protein: dict[str, set[str]] = {}
    for site_entry in regulated_sites:
        site_keys_by_protein.setdefault(site_entry.protein_ref, []).append(site_entry.site_key)
        pathway_terms_by_protein.setdefault(site_entry.protein_ref, set()).update(
            pathways_by_site.get(site_entry.site_key, set())
        )

    return tuple(
        PtmProteinCrosstalkMapEntry(
            protein_ref=protein_ref,
            site_keys=tuple(sorted(site_keys)),
            pair_keys=tuple(sorted(pair_keys_by_protein.get(protein_ref, set()))),
            co_changing_pair_count=cochanging_by_protein.get(protein_ref, 0),
            opposing_pair_count=opposing_by_protein.get(protein_ref, 0),
            pathway_terms=tuple(sorted(pathway_terms_by_protein.get(protein_ref, set()))),
            note=(
                "protein map preserves every regulated PTM site plus connected co-changing "
                "and opposing crosstalk pairs touching this protein"
            ),
        )
        for protein_ref, site_keys in sorted(site_keys_by_protein.items())
    )


__all__ = (
    "PtmCrosstalkEvidenceSource",
    "PtmCrosstalkPairEntry",
    "PtmCrosstalkRelationship",
    "PtmCrosstalkReport",
    "PtmCrosstalkSummary",
    "PtmProteinCrosstalkMapEntry",
    "build_ptm_crosstalk_report",
    "export_ptm_crosstalk_pair_tsv",
    "export_ptm_crosstalk_protein_map_tsv",
    "export_ptm_crosstalk_summary_tsv",
    "render_ptm_crosstalk_pair_tsv",
    "render_ptm_crosstalk_protein_map_tsv",
    "render_ptm_crosstalk_summary_tsv",
)
