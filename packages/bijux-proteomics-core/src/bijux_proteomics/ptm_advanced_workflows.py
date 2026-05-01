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
    build_ptm_motif_windows,
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


class PtmMotifEnrichmentTermEntry(JsonModel):
    """One residue-level term in PTM motif enrichment reporting."""

    model_config = ConfigDict(extra="forbid")

    residue: str = Field(..., min_length=1, max_length=1)
    foreground_site_count: int = Field(..., ge=0)
    background_site_count: int = Field(..., ge=0)
    enrichment_ratio: float | None = Field(default=None, ge=0.0)


class PtmMotifEnrichmentBackgroundProvenanceReport(JsonModel):
    """Motif enrichment report with explicit background and test provenance."""

    model_config = ConfigDict(extra="forbid")

    modification_name: str = Field(..., min_length=1)
    background_universe: str = Field(..., min_length=1)
    applied_filters: tuple[str, ...] = Field(default_factory=tuple)
    statistical_test: str = Field(..., min_length=1)
    multiple_testing_correction: str = Field(..., min_length=1)
    foreground_site_count: int = Field(..., ge=0)
    background_site_count: int = Field(..., ge=0)
    terms: tuple[PtmMotifEnrichmentTermEntry, ...] = Field(default_factory=tuple)
    caveats: tuple[str, ...] = Field(default_factory=tuple)


class PtmPhosphoReviewFixtureReport(JsonModel):
    """Phospho-focused review fixture summary with quant and ambiguity context."""

    model_config = ConfigDict(extra="forbid")

    phospho_site_keys: tuple[str, ...] = Field(default_factory=tuple)
    ambiguous_site_keys: tuple[str, ...] = Field(default_factory=tuple)
    occupancy_sample_count: int = Field(..., ge=0)
    motif_window_count: int = Field(..., ge=0)
    quantified_sample_ids: tuple[str, ...] = Field(default_factory=tuple)
    caveats: tuple[str, ...] = Field(default_factory=tuple)


class PtmAcetylReviewFixtureReport(JsonModel):
    """Acetyl-focused review fixture summary for terminal/residue placement context."""

    model_config = ConfigDict(extra="forbid")

    acetyl_site_keys: tuple[str, ...] = Field(default_factory=tuple)
    protein_terminal_site_keys: tuple[str, ...] = Field(default_factory=tuple)
    residue_site_keys: tuple[str, ...] = Field(default_factory=tuple)
    motif_window_count: int = Field(..., ge=0)
    quantified_sample_ids: tuple[str, ...] = Field(default_factory=tuple)
    caveats: tuple[str, ...] = Field(default_factory=tuple)


class UbiquitinRemnantSiteWorkflowEntry(JsonModel):
    """One ubiquitin-remnant site entry with assumptions and caveats."""

    model_config = ConfigDict(extra="forbid")

    site_key: str = Field(..., min_length=1)
    protein_ref: str = Field(..., min_length=1)
    residue: str = Field(..., min_length=1, max_length=1)
    position: int = Field(..., ge=1)
    modification_name: str = Field(..., min_length=1)
    lysine_consistent: bool
    ambiguous: bool
    quantified_sample_ids: tuple[str, ...] = Field(default_factory=tuple)
    caveats: tuple[str, ...] = Field(default_factory=tuple)


class UbiquitinRemnantWorkflowReport(JsonModel):
    """Workflow report for ubiquitin-remnant PTM evidence interpretation."""

    model_config = ConfigDict(extra="forbid")

    entries: tuple[UbiquitinRemnantSiteWorkflowEntry, ...] = Field(default_factory=tuple)
    ambiguous_entry_count: int = Field(..., ge=0)
    non_lysine_entry_count: int = Field(..., ge=0)


class GlycopeptideBoundaryDisposition(StrEnum):
    """Support boundary disposition for glycopeptide workflows."""

    SUPPORTED = "supported"
    REFUSED = "refused"


class GlycopeptideSupportBoundaryReport(JsonModel):
    """Support or refusal boundary for glycopeptide-specific PTM workflows."""

    model_config = ConfigDict(extra="forbid")

    requested_workflow: str = Field(..., min_length=1)
    disposition: GlycopeptideBoundaryDisposition
    reason: str = Field(..., min_length=1)
    required_evidence_fields: tuple[str, ...] = Field(default_factory=tuple)
    missing_evidence_fields: tuple[str, ...] = Field(default_factory=tuple)
    notes: tuple[str, ...] = Field(default_factory=tuple)


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


def build_ptm_motif_enrichment_background_provenance_report(
    site_entries: tuple[PtmSiteEntry, ...],
    *,
    protein_sequences: dict[str, str],
    modification_name: str,
    background_universe: str,
    applied_filters: tuple[str, ...],
    statistical_test: str = "fisher_exact",
    multiple_testing_correction: str = "benjamini_hochberg",
) -> PtmMotifEnrichmentBackgroundProvenanceReport:
    """Build PTM motif enrichment report with background provenance metadata."""
    relevant = tuple(
        entry for entry in site_entries if entry.modification_name == modification_name
    )
    residues = tuple(sorted({entry.residue for entry in relevant})) or ("S", "T", "Y")
    residue_background_counts = {
        residue: sum(sequence.count(residue) for sequence in protein_sequences.values())
        for residue in residues
    }
    term_entries: list[PtmMotifEnrichmentTermEntry] = []
    background_total = sum(residue_background_counts.values())
    foreground_total = len(relevant)
    for residue in residues:
        foreground_count = sum(1 for entry in relevant if entry.residue == residue)
        background_count = residue_background_counts[residue]
        ratio = (
            (foreground_count / foreground_total) / (background_count / max(background_total, 1))
            if foreground_total > 0 and background_count > 0
            else None
        )
        term_entries.append(
            PtmMotifEnrichmentTermEntry(
                residue=residue,
                foreground_site_count=foreground_count,
                background_site_count=background_count,
                enrichment_ratio=round(ratio, 6) if ratio is not None else None,
            )
        )
    caveats: list[str] = []
    if any(entry.ambiguous for entry in relevant):
        caveats.append("foreground contains ambiguous site assignments")
    if not relevant:
        caveats.append("foreground is empty for requested PTM class")
    return PtmMotifEnrichmentBackgroundProvenanceReport(
        modification_name=modification_name,
        background_universe=background_universe,
        applied_filters=applied_filters,
        statistical_test=statistical_test,
        multiple_testing_correction=multiple_testing_correction,
        foreground_site_count=foreground_total,
        background_site_count=background_total,
        terms=tuple(term_entries),
        caveats=tuple(caveats),
    )


def build_phospho_specific_review_fixture_report(
    site_entries: tuple[PtmSiteEntry, ...],
    *,
    feature_records: tuple[Ms1FeatureRecord, ...],
    protein_sequences: dict[str, str],
) -> PtmPhosphoReviewFixtureReport:
    """Build a phospho-specific review fixture report for localization and quant context."""
    phospho_entries = tuple(
        entry for entry in site_entries if entry.modification_name == "Phospho"
    )
    occupancy_report = build_ptm_occupancy_counterpart_report(
        phospho_entries,
        feature_records=feature_records,
    )
    motif_windows = build_ptm_motif_windows(
        phospho_entries,
        protein_sequences=protein_sequences,
        flank_size=7,
    )
    caveats: list[str] = []
    if any(entry.ambiguous for entry in phospho_entries):
        caveats.append("phospho fixture includes ambiguous localization examples")
    if occupancy_report.missing_counterpart_count > 0:
        caveats.append("phospho fixture includes missing counterpart occupancy examples")
    return PtmPhosphoReviewFixtureReport(
        phospho_site_keys=tuple(sorted(entry.site_key for entry in phospho_entries)),
        ambiguous_site_keys=tuple(
            sorted(entry.site_key for entry in phospho_entries if entry.ambiguous)
        ),
        occupancy_sample_count=len(occupancy_report.entries),
        motif_window_count=len(motif_windows),
        quantified_sample_ids=tuple(
            sorted({entry.sample_id for entry in occupancy_report.entries})
        ),
        caveats=tuple(caveats),
    )


def build_acetyl_specific_review_fixture_report(
    site_entries: tuple[PtmSiteEntry, ...],
    *,
    feature_records: tuple[Ms1FeatureRecord, ...],
    protein_sequences: dict[str, str],
) -> PtmAcetylReviewFixtureReport:
    """Build an acetyl-focused review fixture report with placement semantics."""
    acetyl_entries = tuple(
        entry for entry in site_entries if entry.modification_name == "Acetyl"
    )
    occupancy_report = build_ptm_occupancy_counterpart_report(
        acetyl_entries,
        feature_records=feature_records,
    )
    motif_windows = build_ptm_motif_windows(
        acetyl_entries,
        protein_sequences=protein_sequences,
        flank_size=7,
    )
    protein_terminal_keys = tuple(
        sorted(entry.site_key for entry in acetyl_entries if entry.position == 1)
    )
    residue_keys = tuple(
        sorted(entry.site_key for entry in acetyl_entries if entry.position != 1)
    )
    caveats: list[str] = []
    if protein_terminal_keys:
        caveats.append("contains protein-terminal acetylation placements")
    if residue_keys:
        caveats.append("contains residue-level acetylation placements")
    if occupancy_report.missing_counterpart_count > 0:
        caveats.append("contains missing counterpart occupancy caveats")
    return PtmAcetylReviewFixtureReport(
        acetyl_site_keys=tuple(sorted(entry.site_key for entry in acetyl_entries)),
        protein_terminal_site_keys=protein_terminal_keys,
        residue_site_keys=residue_keys,
        motif_window_count=len(motif_windows),
        quantified_sample_ids=tuple(
            sorted({entry.sample_id for entry in occupancy_report.entries})
        ),
        caveats=tuple(caveats),
    )


def build_ubiquitin_remnant_workflow_report(
    site_entries: tuple[PtmSiteEntry, ...],
    *,
    feature_records: tuple[Ms1FeatureRecord, ...],
) -> UbiquitinRemnantWorkflowReport:
    """Build workflow report for K-GG style ubiquitin-remnant evidence."""
    supported_mod_names = {"GlyGly", "K-GG", "DiGly", "UbiquitinRemnant"}
    remnant_entries = tuple(
        entry
        for entry in site_entries
        if entry.modification_name in supported_mod_names
    )
    rows: list[UbiquitinRemnantSiteWorkflowEntry] = []
    for entry in remnant_entries:
        quantified_samples = tuple(
            sorted(
                {
                    record.sample_id
                    for record in feature_records
                    if entry.protein_ref in record.protein_refs and record.intensity is not None
                }
            )
        )
        caveats: list[str] = []
        lysine_consistent = entry.residue == "K"
        if not lysine_consistent:
            caveats.append("site residue is not lysine for a ubiquitin-remnant assumption")
        if entry.ambiguous:
            caveats.append("site localization remains ambiguous")
        if not quantified_samples:
            caveats.append("no quant-linked samples found for this site")
        rows.append(
            UbiquitinRemnantSiteWorkflowEntry(
                site_key=entry.site_key,
                protein_ref=entry.protein_ref,
                residue=entry.residue,
                position=entry.position,
                modification_name=entry.modification_name,
                lysine_consistent=lysine_consistent,
                ambiguous=entry.ambiguous,
                quantified_sample_ids=quantified_samples,
                caveats=tuple(caveats),
            )
        )
    return UbiquitinRemnantWorkflowReport(
        entries=tuple(rows),
        ambiguous_entry_count=sum(1 for row in rows if row.ambiguous),
        non_lysine_entry_count=sum(1 for row in rows if not row.lysine_consistent),
    )


def evaluate_glycopeptide_support_boundary(
    *,
    requested_workflow: str,
    has_glycan_composition: bool,
    has_glycosite_localization: bool,
    has_oxonium_ion_support: bool,
    treats_as_ordinary_modification: bool,
) -> GlycopeptideSupportBoundaryReport:
    """Support or refuse glycopeptide workflows without flattening glyco semantics."""
    required = (
        "glycan_composition",
        "glycosite_localization",
        "oxonium_ion_support",
    )
    available = {
        "glycan_composition": has_glycan_composition,
        "glycosite_localization": has_glycosite_localization,
        "oxonium_ion_support": has_oxonium_ion_support,
    }
    missing = tuple(name for name in required if not available[name])
    notes: list[str] = []
    if treats_as_ordinary_modification:
        notes.append(
            "workflow treats glycopeptides as ordinary residue modifications, which is refused"
        )
    if missing or treats_as_ordinary_modification:
        return GlycopeptideSupportBoundaryReport(
            requested_workflow=requested_workflow,
            disposition=GlycopeptideBoundaryDisposition.REFUSED,
            reason=(
                "glycopeptide workflow is refused because glyco-specific evidence and "
                "semantics are incomplete"
            ),
            required_evidence_fields=required,
            missing_evidence_fields=missing,
            notes=tuple(notes),
        )
    return GlycopeptideSupportBoundaryReport(
        requested_workflow=requested_workflow,
        disposition=GlycopeptideBoundaryDisposition.SUPPORTED,
        reason=(
            "glycopeptide workflow is supported with glycan composition, site localization, "
            "and oxonium-ion evidence"
        ),
        required_evidence_fields=required,
    )
