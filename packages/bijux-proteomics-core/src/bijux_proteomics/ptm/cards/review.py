# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Advanced PTM workflow surfaces for review-grade interpretation."""

from __future__ import annotations

from collections.abc import Mapping
from enum import StrEnum
from typing import TYPE_CHECKING

from pydantic import ConfigDict, Field

from bijux_proteomics.ptm.contracts import (
    PtmEvidenceRecord,
    PtmProteinSiteMapping,
    PtmSiteEntry,
)
from bijux_proteomics.ptm.localization.localization_scoring import (
    PtmLocalizationConfidenceTier,
    PtmLocalizationProbabilitySource,
    build_ptm_localization_scoring_report,
)
from bijux_proteomics.ptm.quant.occupancy_estimation import (
    PtmOccupancyCounterpartEvidenceReport,
    build_ptm_occupancy_counterpart_report,
)
from bijux_proteomics.ptm.regulation.motif_analysis import (
    PtmMotifEnrichmentBackgroundProvenanceReport,  # noqa: F401
    PtmMotifEnrichmentTermEntry,  # noqa: F401
    build_ptm_motif_enrichment_background_provenance_report,  # noqa: F401
    build_ptm_motif_windows,
)
from bijux_proteomics.quantification import Ms1FeatureRecord
from bijux_proteomics_foundation import JsonModel

if TYPE_CHECKING:
    from bijux_proteomics_lab.handoffs.ptm import PtmLabValidationPacket


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
    localization_probability_source: PtmLocalizationProbabilitySource
    localization_tier: PtmLocalizationConfidenceTier
    ambiguous: bool
    fragment_ions: tuple[str, ...] = Field(default_factory=tuple)
    site_determining_ions: tuple[str, ...] = Field(default_factory=tuple)
    supported_site_determining_ions: tuple[str, ...] = Field(default_factory=tuple)


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

    entries: tuple[UbiquitinRemnantSiteWorkflowEntry, ...] = Field(
        default_factory=tuple
    )
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


class PtmCooccurrencePairCautionEntry(JsonModel):
    """One pairwise PTM co-occurrence caution entry."""

    model_config = ConfigDict(extra="forbid")

    left_site_key: str = Field(..., min_length=1)
    right_site_key: str = Field(..., min_length=1)
    same_peptide_evidence: bool
    same_protein_evidence: bool
    same_sample_evidence: bool
    same_run_evidence: bool
    true_colocalization_evidence: bool
    caution: str = Field(..., min_length=1)


class PtmCooccurrenceCautionReport(JsonModel):
    """Co-occurrence caution report separating evidence levels."""

    model_config = ConfigDict(extra="forbid")

    entries: tuple[PtmCooccurrencePairCautionEntry, ...] = Field(default_factory=tuple)
    same_peptide_pair_count: int = Field(..., ge=0)
    same_protein_pair_count: int = Field(..., ge=0)
    same_sample_pair_count: int = Field(..., ge=0)
    same_run_pair_count: int = Field(..., ge=0)
    true_colocalization_pair_count: int = Field(..., ge=0)


def build_ptm_site_localization_evidence_graph(
    records: tuple[PtmEvidenceRecord, ...],
    mappings: tuple[PtmProteinSiteMapping, ...],
    *,
    fragment_ion_support_by_spectrum: dict[str, tuple[str, ...]] | None = None,
) -> PtmSiteLocalizationEvidenceGraph:
    """Build a PTM site-localization evidence graph from records and mappings."""
    record_by_spectrum = {record.spectrum_id: record for record in records}
    scoring_report = build_ptm_localization_scoring_report(
        records,
        fragment_ion_support_by_spectrum=fragment_ion_support_by_spectrum,
    )
    scoring_by_spectrum_and_index = {
        (entry.spectrum_id, entry.peptide_site_index): entry
        for entry in scoring_report.entries
    }
    grouped: dict[str, list[PtmProteinSiteMapping]] = {}
    for mapping in mappings:
        site_key = (
            f"{mapping.protein_ref}:{mapping.residue}"
            f"{mapping.protein_position}:{mapping.modification_name}"
        )
        grouped.setdefault(site_key, []).append(mapping)

    nodes: list[PtmSiteLocalizationEvidenceNode] = []
    for site_key, bucket in sorted(grouped.items()):
        scores = tuple(
            sorted((mapping.localization_score for mapping in bucket), reverse=True)
        )
        spectrum_ids = tuple(sorted({mapping.spectrum_id for mapping in bucket}))
        fragment_ions: set[str] = set()
        site_determining_ions: set[str] = set()
        supported_site_determining_ions: set[str] = set()
        probability_source = PtmLocalizationProbabilitySource.NORMALIZED_SCORE
        localization_tier = PtmLocalizationConfidenceTier.REFUSED
        probability = 0.0
        probability_candidates: list[
            tuple[
                float, PtmLocalizationProbabilitySource, PtmLocalizationConfidenceTier
            ]
        ] = []
        scoring_entries = [
            scoring_by_spectrum_and_index[
                (mapping.spectrum_id, mapping.peptide_site_index)
            ]
            for mapping in bucket
            if (mapping.spectrum_id, mapping.peptide_site_index)
            in scoring_by_spectrum_and_index
        ]
        if fragment_ion_support_by_spectrum:
            for spectrum_id in spectrum_ids:
                fragment_ions.update(
                    fragment_ion_support_by_spectrum.get(spectrum_id, ())
                )
        for scoring_entry in scoring_entries:
            site_determining_ions.update(scoring_entry.site_determining_ions)
            supported_site_determining_ions.update(
                scoring_entry.supported_site_determining_ions
            )
            probability_candidates.append(
                (
                    scoring_entry.localization_probability,
                    scoring_entry.probability_source,
                    scoring_entry.localization_tier,
                )
            )
        if probability_candidates:
            probability, probability_source, localization_tier = max(
                probability_candidates,
                key=lambda candidate: (
                    _localization_tier_rank(candidate[2]),
                    candidate[0],
                    1
                    if candidate[1]
                    is PtmLocalizationProbabilitySource.REPORTED_PROBABILITY
                    else 0,
                ),
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
                localization_probability=probability,
                localization_probability_source=probability_source,
                localization_tier=localization_tier,
                ambiguous=any(mapping.ambiguous for mapping in bucket),
                fragment_ions=tuple(sorted(fragment_ions)),
                site_determining_ions=tuple(sorted(site_determining_ions)),
                supported_site_determining_ions=tuple(
                    sorted(supported_site_determining_ions)
                ),
            )
        )
    return PtmSiteLocalizationEvidenceGraph(
        nodes=tuple(nodes),
        source_spectrum_count=len(record_by_spectrum),
        source_record_count=len(records),
    )


def _localization_tier_rank(tier: PtmLocalizationConfidenceTier) -> int:
    if tier is PtmLocalizationConfidenceTier.HIGH_CONFIDENCE:
        return 3
    if tier is PtmLocalizationConfidenceTier.SUPPORTED:
        return 2
    if tier is PtmLocalizationConfidenceTier.AMBIGUOUS:
        return 1
    return 0


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


def build_phospho_specific_review_fixture_report(
    site_entries: tuple[PtmSiteEntry, ...],
    *,
    feature_records: tuple[Ms1FeatureRecord, ...],
    protein_sequences: Mapping[str, str],
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
        caveats.append(
            "phospho fixture includes missing counterpart occupancy examples"
        )
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
    protein_sequences: Mapping[str, str],
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
                    if entry.protein_ref in record.protein_refs
                    and record.intensity is not None
                }
            )
        )
        caveats: list[str] = []
        lysine_consistent = entry.residue == "K"
        if not lysine_consistent:
            caveats.append(
                "site residue is not lysine for a ubiquitin-remnant assumption"
            )
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


def build_ptm_cooccurrence_caution_report(
    mappings: tuple[PtmProteinSiteMapping, ...],
    *,
    spectrum_run_by_id: dict[str, str] | None = None,
) -> PtmCooccurrenceCautionReport:
    """Build caution report for PTM co-occurrence evidence levels."""
    grouped: dict[str, list[PtmProteinSiteMapping]] = {}
    for mapping in mappings:
        site_key = (
            f"{mapping.protein_ref}:{mapping.residue}"
            f"{mapping.protein_position}:{mapping.modification_name}"
        )
        grouped.setdefault(site_key, []).append(mapping)

    ordered_keys = sorted(grouped)
    entries: list[PtmCooccurrencePairCautionEntry] = []
    for index, left_key in enumerate(ordered_keys):
        for right_key in ordered_keys[index + 1 :]:
            left_bucket = grouped[left_key]
            right_bucket = grouped[right_key]
            left_peptides = {mapping.canonical_peptide for mapping in left_bucket}
            right_peptides = {mapping.canonical_peptide for mapping in right_bucket}
            left_samples = {
                mapping.sample_id for mapping in left_bucket if mapping.sample_id
            }
            right_samples = {
                mapping.sample_id for mapping in right_bucket if mapping.sample_id
            }
            left_spectra = {mapping.spectrum_id for mapping in left_bucket}
            right_spectra = {mapping.spectrum_id for mapping in right_bucket}
            left_runs = (
                {
                    spectrum_run_by_id.get(spectrum_id, spectrum_id)
                    for spectrum_id in left_spectra
                }
                if spectrum_run_by_id
                else set()
            )
            right_runs = (
                {
                    spectrum_run_by_id.get(spectrum_id, spectrum_id)
                    for spectrum_id in right_spectra
                }
                if spectrum_run_by_id
                else set()
            )

            same_peptide = bool(left_peptides & right_peptides)
            same_protein = left_bucket[0].protein_ref == right_bucket[0].protein_ref
            same_sample = bool(left_samples & right_samples)
            same_run = bool(left_runs & right_runs) if spectrum_run_by_id else False
            true_colocalized = bool(left_spectra & right_spectra)

            if true_colocalized:
                caution = "co-localization signal is present within shared spectra and should still be reviewed"
            elif same_run:
                caution = "co-occurrence is observed in the same run but without shared spectral localization"
            elif same_sample:
                caution = "co-occurrence is sample-level and not direct co-localization evidence"
            elif same_protein:
                caution = "co-occurrence is protein-level only and may reflect independent sites"
            elif same_peptide:
                caution = "co-occurrence is peptide-level only and requires localization review"
            else:
                caution = "no co-occurrence coupling evidence detected between sites"

            entries.append(
                PtmCooccurrencePairCautionEntry(
                    left_site_key=left_key,
                    right_site_key=right_key,
                    same_peptide_evidence=same_peptide,
                    same_protein_evidence=same_protein,
                    same_sample_evidence=same_sample,
                    same_run_evidence=same_run,
                    true_colocalization_evidence=true_colocalized,
                    caution=caution,
                )
            )

    return PtmCooccurrenceCautionReport(
        entries=tuple(entries),
        same_peptide_pair_count=sum(
            1 for entry in entries if entry.same_peptide_evidence
        ),
        same_protein_pair_count=sum(
            1 for entry in entries if entry.same_protein_evidence
        ),
        same_sample_pair_count=sum(
            1 for entry in entries if entry.same_sample_evidence
        ),
        same_run_pair_count=sum(1 for entry in entries if entry.same_run_evidence),
        true_colocalization_pair_count=sum(
            1 for entry in entries if entry.true_colocalization_evidence
        ),
    )


def build_ptm_lab_validation_packet(
    site_entries: tuple[PtmSiteEntry, ...],
    *,
    occupancy_report: PtmOccupancyCounterpartEvidenceReport | None = None,
    cooccurrence_report: PtmCooccurrenceCautionReport | None = None,
) -> PtmLabValidationPacket:
    """Route PTM lab-validation packet construction through the lab owner package."""
    from bijux_proteomics_lab.handoffs.ptm import (
        build_ptm_lab_validation_packet as _build,
    )

    return _build(
        site_entries,
        occupancy_report=occupancy_report,
        cooccurrence_report=cooccurrence_report,
    )
