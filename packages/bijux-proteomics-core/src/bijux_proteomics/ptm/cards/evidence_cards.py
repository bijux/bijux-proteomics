# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Owned PTM evidence-card surfaces over significant site results."""

from __future__ import annotations

from bijux_proteomics._output_tables import write_output_table_tsv

import csv
import re
from enum import StrEnum
from io import StringIO
from pathlib import Path

from pydantic import ConfigDict, Field, model_validator

from bijux_proteomics.domain import SourceRowLineage
from bijux_proteomics.domain.card_schema import (
    StandardCardEntry,
    StandardCardKind,
    StandardCardSubjectKind,
    render_standard_card_row,
)
from bijux_proteomics.domain.confidence import ConfidenceTier
from bijux_proteomics.domain.semantic_ids import (
    build_ptm_card_id,
    build_ptm_claim_id,
    build_site_id,
)
from bijux_proteomics.identification import TargetDecoyLabel
from bijux_proteomics.io.stable_outputs import sort_rows_by_fields, sort_strings
from bijux_proteomics.ptm.contracts import PtmEvidenceRecord, PtmSiteEntry
from bijux_proteomics.ptm.crosstalk import (
    PtmCrosstalkEvidenceSource,
    PtmCrosstalkRelationship,
    build_ptm_crosstalk_report,
)
from bijux_proteomics.ptm.differential_analysis import (
    PtmDifferentialAnalysisReport,
    PtmProteinCorrectionMode,
    PtmProteinCorrectionStatus,
    PtmSiteDifferentialEntry,
    PtmSiteDifferentialReport,
)
from bijux_proteomics.ptm.localization_scoring import (
    PtmLocalizationConfidenceTier,
    PtmLocalizationProbabilitySource,
    PtmLocalizationScoringEntry,
    PtmLocalizationScoringReport,
)
from bijux_proteomics.ptm.mechanism_classification import (
    PtmMechanismClass,
    PtmMechanismClassificationReport,
    PtmMechanismReasonCode,
)
from bijux_proteomics.ptm.motif_analysis import PtmPhosphositeMotifEnrichmentReport
from bijux_proteomics.ptm.ortholog_site_conservation import (
    PtmOrthologConservationReport,
    PtmOrthologConservationStatus,
)
from bijux_proteomics.ptm.regulator_enrichment import (
    PtmRegulatorEnrichmentEntry,
    PtmRegulatorEnrichmentReport,
    PtmRegulatorKind,
)
from bijux_proteomics.ptm.site_annotation_import import PtmSiteAnnotationMappingReport
from bijux_proteomics.ptm.site_quantification import (
    PtmSiteQuantRow,
    PtmSiteQuantificationReport,
)
from bijux_proteomics.quantification.contracts import MissingValueKind
from bijux_proteomics.sequences import (
    NormalizedProteinRecord,
    ProteinFunctionalRegionEvidence,
    ProteinIdentityLevel,
    ProteinIdentityReference,
    ProteinIdentityResolutionEntry,
    ProteinRegionContextRecord,
    ProteinSiteRegionReference,
    build_protein_identity_resolution_report,
    build_protein_site_region_context_report,
)
from bijux_proteomics_foundation import JsonModel


class PtmEvidenceCardPolicy(JsonModel):
    """Selection policy for PTM evidence-card generation."""

    model_config = ConfigDict(extra="forbid")

    max_adjusted_p_value: float = Field(default=0.1, ge=0.0, le=1.0)


class PtmEvidenceCardWarningCode(StrEnum):
    """Explicit warning codes preserved on one PTM evidence card."""

    LOW_LOCALIZATION = "low_localization"
    AMBIGUOUS_SITE = "ambiguous_site"
    SHARED_PEPTIDE = "shared_peptide"
    DECOY_SITE = "decoy_site"
    MISSING_PROTEIN_BASELINE = "missing_protein_baseline"
    CORRECTED_LOW_LOCALIZATION = "corrected_low_localization"


class PtmEvidenceCardWarning(JsonModel):
    """One warning attached to a PTM evidence card."""

    model_config = ConfigDict(extra="forbid")

    code: PtmEvidenceCardWarningCode
    message: str = Field(..., min_length=1)


class PtmEvidenceCardPeptideObservation(JsonModel):
    """One peptide-spectrum observation preserved on a PTM evidence card."""

    model_config = ConfigDict(extra="forbid")

    spectrum_id: str = Field(..., min_length=1)
    sample_id: str | None = None
    localized_peptide: str = Field(..., min_length=1)
    canonical_peptide: str = Field(..., min_length=1)
    charge: int = Field(..., ge=1)
    score: float
    q_value: float | None = Field(default=None, ge=0.0)
    protein_refs: tuple[str, ...] = Field(default_factory=tuple)


class PtmEvidenceCardLocalizationObservation(JsonModel):
    """One localized-modification review entry preserved on a PTM evidence card."""

    model_config = ConfigDict(extra="forbid")

    spectrum_id: str = Field(..., min_length=1)
    sample_id: str | None = None
    localized_peptide: str = Field(..., min_length=1)
    peptide_site_index: int = Field(..., ge=1)
    candidate_site_indices: tuple[int, ...] = Field(default_factory=tuple)
    ambiguity_group: str = Field(..., min_length=1)
    localization_probability: float = Field(..., ge=0.0, le=1.0)
    probability_source: PtmLocalizationProbabilitySource
    localization_tier: PtmLocalizationConfidenceTier
    supported_site_determining_ions: tuple[str, ...] = Field(default_factory=tuple)


class PtmEvidenceCardLocalization(JsonModel):
    """Localization evidence summary for one PTM evidence card."""

    model_config = ConfigDict(extra="forbid")

    localization_tier: PtmLocalizationConfidenceTier
    low_localization: bool = False
    ambiguous: bool = False
    shared_peptide: bool = False
    localized_peptides: tuple[str, ...] = Field(default_factory=tuple)
    observations: tuple[PtmEvidenceCardLocalizationObservation, ...] = Field(
        default_factory=tuple
    )
    best_localization_probability: float | None = Field(default=None, ge=0.0, le=1.0)
    supported_site_determining_ion_count: int = Field(default=0, ge=0)


class PtmEvidenceCardSampleValue(JsonModel):
    """One sample-level PTM site quantification cell on a PTM evidence card."""

    model_config = ConfigDict(extra="forbid")

    sample_id: str = Field(..., min_length=1)
    abundance: float | None = Field(default=None, ge=0.0)
    missing_value_kind: MissingValueKind
    contributing_feature_count: int = Field(..., ge=0)


class PtmEvidenceCardQuantification(JsonModel):
    """Quantification evidence preserved on one PTM evidence card."""

    model_config = ConfigDict(extra="forbid")

    sample_values: tuple[PtmEvidenceCardSampleValue, ...] = Field(default_factory=tuple)
    observed_sample_count: int = Field(..., ge=0)
    zero_sample_count: int = Field(..., ge=0)
    missing_sample_count: int = Field(..., ge=0)
    filtered_sample_count: int = Field(..., ge=0)


class PtmEvidenceCardDifferentialResult(JsonModel):
    """Differential result preserved on one PTM evidence card."""

    model_config = ConfigDict(extra="forbid")

    condition_a: str = Field(..., min_length=1)
    condition_b: str = Field(..., min_length=1)
    observations_a: int = Field(..., ge=0)
    observations_b: int = Field(..., ge=0)
    complete_pair_count: int = Field(..., ge=0)
    mean_log2_abundance_a: float
    mean_log2_abundance_b: float
    log2_fold_change: float
    p_value: float = Field(..., ge=0.0, le=1.0)
    adjusted_p_value: float | None = Field(default=None, ge=0.0, le=1.0)
    standard_error: float | None = Field(default=None, ge=0.0)
    confidence_interval_low: float | None = None
    confidence_interval_high: float | None = None
    effect_size_cohens_d: float | None = None
    imputation_dependent_hit: bool = False
    uncertainty_note: str | None = None


class PtmEvidenceCardProteinCorrection(JsonModel):
    """Protein-correction evidence preserved on one PTM evidence card."""

    model_config = ConfigDict(extra="forbid")

    mode: PtmProteinCorrectionMode
    status: str = Field(..., min_length=1)
    protein_log2_fold_change: float | None = None
    protein_adjusted_p_value: float | None = Field(default=None, ge=0.0, le=1.0)
    corrected_log2_fold_change: float | None = None


class PtmEvidenceCardMotifEvidence(JsonModel):
    """Motif evidence preserved on one PTM evidence card."""

    model_config = ConfigDict(extra="forbid")

    centered_windows: tuple[str, ...] = Field(default_factory=tuple)
    enriched_terms: tuple[str, ...] = Field(default_factory=tuple)


class PtmEvidenceCardRegulatorEvidence(JsonModel):
    """Regulator evidence preserved on one PTM evidence card."""

    model_config = ConfigDict(extra="forbid")

    regulator: str = Field(..., min_length=1)
    regulator_kind: PtmRegulatorKind
    direction: str = Field(..., min_length=1)
    adjusted_p_value: float | None = Field(default=None, ge=0.0, le=1.0)
    p_value: float = Field(..., ge=0.0, le=1.0)
    enrichment_ratio: float | None = Field(default=None, ge=0.0)
    annotation_coverage_fraction: float = Field(..., ge=0.0, le=1.0)


class PtmEvidenceCardCrosstalkPartner(JsonModel):
    """One PTM-site partner linked through owned crosstalk evidence."""

    model_config = ConfigDict(extra="forbid")

    partner_site_key: str = Field(..., min_length=1)
    partner_protein_ref: str = Field(..., min_length=1)
    partner_modification_name: str = Field(..., min_length=1)
    partner_position: int = Field(..., ge=1)
    partner_log2_fold_change: float
    relationship: PtmCrosstalkRelationship
    evidence_sources: tuple[PtmCrosstalkEvidenceSource, ...] = Field(
        default_factory=tuple
    )
    shared_peptides: tuple[str, ...] = Field(default_factory=tuple)
    shared_pathways: tuple[str, ...] = Field(default_factory=tuple)
    residue_distance: int | None = Field(default=None, ge=0)
    evidence_note: str = Field(..., min_length=1)


class PtmEvidenceCardOrthologConservation(JsonModel):
    """Ortholog-site conservation context preserved on one PTM evidence card."""

    model_config = ConfigDict(extra="forbid")

    status: PtmOrthologConservationStatus
    source_species: str = Field(..., min_length=1)
    target_species: str = Field(..., min_length=1)
    ortholog_target_site_keys: tuple[str, ...] = Field(default_factory=tuple)
    ortholog_target_protein_refs: tuple[str, ...] = Field(default_factory=tuple)
    ortholog_target_positions: tuple[int, ...] = Field(default_factory=tuple)
    evidence_labels: tuple[str, ...] = Field(default_factory=tuple)
    source_names: tuple[str, ...] = Field(default_factory=tuple)
    source_accessions: tuple[str, ...] = Field(default_factory=tuple)
    note: str = Field(..., min_length=1)


class PtmEvidenceCardMechanismClassification(JsonModel):
    """Mechanism classification preserved on one PTM evidence card."""

    model_config = ConfigDict(extra="forbid")

    mechanism_class: PtmMechanismClass
    reason_codes: tuple[PtmMechanismReasonCode, ...] = Field(default_factory=tuple)
    raw_log2_fold_change: float
    corrected_log2_fold_change: float | None = None
    protein_log2_fold_change: float | None = None
    protein_adjusted_p_value: float | None = Field(default=None, ge=0.0, le=1.0)
    note: str = Field(..., min_length=1)


class PtmEvidenceCard(JsonModel):
    """One structured PTM evidence card for one significant site."""

    model_config = ConfigDict(extra="forbid")

    card_id: str = Field(..., min_length=1)
    site_key: str = Field(..., min_length=1)
    protein_ref: str = Field(..., min_length=1)
    residue: str = Field(..., min_length=1, max_length=1)
    position: int = Field(..., ge=1)
    modification_name: str = Field(..., min_length=1)
    target_decoy_label: TargetDecoyLabel
    identity_level: ProteinIdentityLevel
    identity_reason: str = Field(..., min_length=1)
    peptide_evidence: tuple[PtmEvidenceCardPeptideObservation, ...] = Field(
        default_factory=tuple
    )
    localization: PtmEvidenceCardLocalization
    quantification: PtmEvidenceCardQuantification | None = None
    differential_result: PtmEvidenceCardDifferentialResult
    motif_evidence: PtmEvidenceCardMotifEvidence
    regulator_evidence: tuple[PtmEvidenceCardRegulatorEvidence, ...] = Field(
        default_factory=tuple
    )
    crosstalk_partners: tuple[PtmEvidenceCardCrosstalkPartner, ...] = Field(
        default_factory=tuple
    )
    mechanism_classification: PtmEvidenceCardMechanismClassification | None = None
    ortholog_conservation: PtmEvidenceCardOrthologConservation | None = None
    functional_regions: tuple[ProteinFunctionalRegionEvidence, ...] = Field(
        default_factory=tuple
    )
    protein_correction: PtmEvidenceCardProteinCorrection
    warnings: tuple[PtmEvidenceCardWarning, ...] = Field(default_factory=tuple)
    claim_ids: tuple[str, ...] = Field(default_factory=tuple)
    source_row_refs: tuple[str, ...] = Field(default_factory=tuple)
    derived_no_source_reason: str | None = None

    @model_validator(mode="after")
    def _validate_source_row_lineage(self) -> PtmEvidenceCard:
        SourceRowLineage(
            source_row_refs=self.source_row_refs,
            derived_no_source_reason=self.derived_no_source_reason,
        )
        return self


class PtmEvidenceCardClaimKind(StrEnum):
    """Narrative claim kinds preserved over PTM evidence cards."""

    DIFFERENTIAL_SITE = "differential_site"


class PtmEvidenceCardClaim(JsonModel):
    """One narrative PTM claim linked back to a PTM evidence card."""

    model_config = ConfigDict(extra="forbid")

    claim_id: str = Field(..., min_length=1)
    card_id: str = Field(..., min_length=1)
    site_key: str = Field(..., min_length=1)
    claim_kind: PtmEvidenceCardClaimKind
    text: str = Field(..., min_length=1)
    source_row_refs: tuple[str, ...] = Field(default_factory=tuple)
    derived_no_source_reason: str | None = None

    @model_validator(mode="after")
    def _validate_source_row_lineage(self) -> PtmEvidenceCardClaim:
        SourceRowLineage(
            source_row_refs=self.source_row_refs,
            derived_no_source_reason=self.derived_no_source_reason,
        )
        return self


class PtmEvidenceCardSummary(JsonModel):
    """Stable summary over one PTM evidence-card pass."""

    model_config = ConfigDict(extra="forbid")

    significant_site_count: int = Field(..., ge=0)
    card_count: int = Field(..., ge=0)
    narrative_claim_count: int = Field(..., ge=0)
    regulator_supported_card_count: int = Field(..., ge=0)
    motif_annotated_card_count: int = Field(..., ge=0)
    crosstalk_supported_card_count: int = Field(..., ge=0)
    mechanism_classified_card_count: int = Field(..., ge=0)
    ortholog_context_card_count: int = Field(..., ge=0)
    functional_context_card_count: int = Field(..., ge=0)
    warning_card_count: int = Field(..., ge=0)


class PtmEvidenceCardReport(JsonModel):
    """Stable PTM evidence-card report over significant site results."""

    model_config = ConfigDict(extra="forbid")

    condition_a: str = Field(..., min_length=1)
    condition_b: str = Field(..., min_length=1)
    policy: PtmEvidenceCardPolicy
    cards: tuple[PtmEvidenceCard, ...] = Field(default_factory=tuple)
    narrative_claims: tuple[PtmEvidenceCardClaim, ...] = Field(default_factory=tuple)
    summary: PtmEvidenceCardSummary
    note: str = Field(..., min_length=1)


def build_ptm_evidence_card_report(
    records: tuple[PtmEvidenceRecord, ...],
    site_entries: tuple[PtmSiteEntry, ...],
    localization_scoring: PtmLocalizationScoringReport,
    differential_analysis: PtmDifferentialAnalysisReport,
    *,
    site_quantification: PtmSiteQuantificationReport | None = None,
    motif_enrichment: PtmPhosphositeMotifEnrichmentReport | None = None,
    regulator_enrichment: PtmRegulatorEnrichmentReport | None = None,
    annotation_mapping_report: PtmSiteAnnotationMappingReport | None = None,
    mechanism_classification_report: PtmMechanismClassificationReport | None = None,
    ortholog_conservation_report: PtmOrthologConservationReport | None = None,
    protein_records: tuple[NormalizedProteinRecord, ...] | None = None,
    protein_sequences: dict[str, str] | None = None,
    protein_region_context_records: tuple[ProteinRegionContextRecord, ...] | None = None,
    policy: PtmEvidenceCardPolicy | None = None,
) -> PtmEvidenceCardReport:
    """Build one PTM evidence-card report over significant differential sites."""

    active_policy = policy or PtmEvidenceCardPolicy()
    site_entry_by_key = {entry.site_key: entry for entry in site_entries}
    quant_row_by_key = (
        {row.site_key: row for row in site_quantification.rows}
        if site_quantification is not None
        else {}
    )
    differential_entries = tuple(
        entry
        for entry in differential_analysis.differential_report.entries
        if entry.adjusted_p_value is not None
        and entry.adjusted_p_value <= active_policy.max_adjusted_p_value
    )
    regulator_entries_by_site: dict[str, list[PtmRegulatorEnrichmentEntry]] = {}
    if regulator_enrichment is not None:
        for entry in regulator_enrichment.entries:
            for site_key in entry.supporting_sites:
                regulator_entries_by_site.setdefault(site_key, []).append(entry)
    functional_context_by_site: dict[str, tuple[ProteinFunctionalRegionEvidence, ...]] = {}
    if protein_region_context_records:
        functional_context_report = build_protein_site_region_context_report(
            tuple(
                ProteinSiteRegionReference(
                    site_key=site_entry.site_key,
                    protein_ref=site_entry.protein_ref,
                    position=site_entry.position,
                )
                for site_entry in site_entries
            ),
            protein_region_context_records,
        )
        functional_context_by_site = {
            entry.site_key: entry.functional_regions
            for entry in functional_context_report.entries
        }
    identity_entries_by_site = _build_identity_entries_by_site(
        records,
        site_entries=site_entries,
        protein_records=protein_records,
        protein_sequences=protein_sequences,
    )
    crosstalk_partners_by_site = _build_crosstalk_partners_by_site(
        site_entries,
        differential_analysis.differential_report,
        annotation_mapping_report=annotation_mapping_report,
    )
    mechanism_classification_by_site = _build_mechanism_classification_by_site(
        mechanism_classification_report
    )
    ortholog_conservation_by_site = _build_ortholog_conservation_by_site(
        ortholog_conservation_report
    )

    cards: list[PtmEvidenceCard] = []
    narrative_claims: list[PtmEvidenceCardClaim] = []
    for differential_entry in sort_rows_by_fields(
        differential_entries,
        "protein_ref",
        "position",
        "modification_name",
        "site_key",
    ):
        site_entry = site_entry_by_key[differential_entry.site_key]
        source_row_lineage = _build_source_row_lineage_for_site(records, site_entry)
        peptide_evidence = _build_peptide_evidence(records, site_entry)
        identity_entry = identity_entries_by_site.get(differential_entry.site_key)
        localization = _build_localization_evidence(
            localization_scoring.entries,
            differential_entry=differential_entry,
            site_entry=site_entry,
        )
        quantification = _build_quantification_evidence(
            quant_row_by_key.get(differential_entry.site_key)
        )
        motif_evidence = _build_motif_evidence(
            motif_enrichment,
            site_key=differential_entry.site_key,
        )
        regulators = tuple(
            PtmEvidenceCardRegulatorEvidence(
                regulator=entry.regulator,
                regulator_kind=entry.regulator_kind,
                direction=entry.direction.value,
                adjusted_p_value=entry.adjusted_p_value,
                p_value=entry.p_value,
                enrichment_ratio=entry.enrichment_ratio,
                annotation_coverage_fraction=entry.annotation_coverage_fraction,
            )
            for entry in sort_rows_by_fields(
                tuple(regulator_entries_by_site.get(differential_entry.site_key, ())),
                "adjusted_p_value",
                "p_value",
                "direction",
                "regulator_kind",
                "regulator",
            )
        )
        warnings = _build_card_warnings(
            differential_entry=differential_entry,
            site_entry=site_entry,
        )
        site_id = build_site_id(
            differential_entry.protein_ref,
            differential_entry.residue,
            differential_entry.position,
            differential_entry.modification_name,
        )
        card_id = _build_card_id(differential_entry, site_id=site_id)
        claim_id = _build_claim_id(differential_entry, site_id=site_id)
        cards.append(
            PtmEvidenceCard(
                card_id=card_id,
                site_key=differential_entry.site_key,
                protein_ref=differential_entry.protein_ref,
                residue=differential_entry.residue,
                position=differential_entry.position,
                modification_name=differential_entry.modification_name,
                target_decoy_label=site_entry.target_decoy_label,
                identity_level=(
                    ProteinIdentityLevel.AMBIGUOUS
                    if identity_entry is None
                    else identity_entry.identity_level
                ),
                identity_reason=(
                    "no protein identity support was available for this PTM site"
                    if identity_entry is None
                    else identity_entry.identity_reason
                ),
                peptide_evidence=peptide_evidence,
                localization=localization,
                quantification=quantification,
                differential_result=PtmEvidenceCardDifferentialResult(
                    condition_a=differential_entry.condition_a,
                    condition_b=differential_entry.condition_b,
                    observations_a=differential_entry.observations_a,
                    observations_b=differential_entry.observations_b,
                    complete_pair_count=differential_entry.complete_pair_count,
                    mean_log2_abundance_a=differential_entry.mean_log2_abundance_a,
                    mean_log2_abundance_b=differential_entry.mean_log2_abundance_b,
                    log2_fold_change=differential_entry.log2_fold_change,
                    p_value=differential_entry.p_value,
                    adjusted_p_value=differential_entry.adjusted_p_value,
                    standard_error=differential_entry.standard_error,
                    confidence_interval_low=differential_entry.confidence_interval_low,
                    confidence_interval_high=differential_entry.confidence_interval_high,
                    effect_size_cohens_d=differential_entry.effect_size_cohens_d,
                    imputation_dependent_hit=differential_entry.imputation_dependent_hit,
                    uncertainty_note=differential_entry.uncertainty_note,
                ),
                motif_evidence=motif_evidence,
                regulator_evidence=regulators,
                crosstalk_partners=crosstalk_partners_by_site.get(
                    differential_entry.site_key,
                    (),
                ),
                mechanism_classification=mechanism_classification_by_site.get(
                    differential_entry.site_key
                ),
                ortholog_conservation=ortholog_conservation_by_site.get(
                    differential_entry.site_key
                ),
                functional_regions=functional_context_by_site.get(
                    differential_entry.site_key,
                    (),
                ),
                protein_correction=PtmEvidenceCardProteinCorrection(
                    mode=differential_analysis.protein_correction_mode,
                    status=differential_entry.protein_correction_status,
                    protein_log2_fold_change=differential_entry.protein_log2_fold_change,
                    protein_adjusted_p_value=differential_entry.protein_adjusted_p_value,
                    corrected_log2_fold_change=differential_entry.corrected_log2_fold_change,
                ),
                warnings=warnings,
                claim_ids=(claim_id,),
                source_row_refs=source_row_lineage.source_row_refs,
                derived_no_source_reason=source_row_lineage.derived_no_source_reason,
            )
        )
        narrative_claims.append(
            PtmEvidenceCardClaim(
                claim_id=claim_id,
                card_id=card_id,
                site_key=differential_entry.site_key,
                claim_kind=PtmEvidenceCardClaimKind.DIFFERENTIAL_SITE,
                text=_build_claim_text(
                    differential_entry,
                    motif_evidence=motif_evidence,
                    regulators=regulators,
                ),
                source_row_refs=source_row_lineage.source_row_refs,
                derived_no_source_reason=source_row_lineage.derived_no_source_reason,
            )
        )

    stable_cards = tuple(
        sorted(
            cards,
            key=lambda entry: (
                entry.protein_ref,
                entry.position,
                entry.modification_name,
                entry.card_id,
            ),
        )
    )
    stable_claims = tuple(
        sorted(
            narrative_claims,
            key=lambda entry: (
                entry.site_key,
                entry.claim_id,
            ),
        )
    )
    return PtmEvidenceCardReport(
        condition_a=differential_analysis.differential_report.condition_a,
        condition_b=differential_analysis.differential_report.condition_b,
        policy=active_policy,
        cards=stable_cards,
        narrative_claims=stable_claims,
        summary=PtmEvidenceCardSummary(
            significant_site_count=len(differential_entries),
            card_count=len(stable_cards),
            narrative_claim_count=len(stable_claims),
            regulator_supported_card_count=sum(
                1 for entry in stable_cards if entry.regulator_evidence
            ),
            motif_annotated_card_count=sum(
                1 for entry in stable_cards if entry.motif_evidence.centered_windows
            ),
            crosstalk_supported_card_count=sum(
                1 for entry in stable_cards if entry.crosstalk_partners
            ),
            mechanism_classified_card_count=sum(
                1 for entry in stable_cards if entry.mechanism_classification is not None
            ),
            ortholog_context_card_count=sum(
                1 for entry in stable_cards if entry.ortholog_conservation is not None
            ),
            functional_context_card_count=sum(
                1 for entry in stable_cards if entry.functional_regions
            ),
            warning_card_count=sum(1 for entry in stable_cards if entry.warnings),
        ),
        note=(
            "ptm evidence cards preserve one structured object per significant site, "
            "carry peptide, localization, quantification, differential, mechanism "
            "classification, motif, crosstalk, ortholog-site conservation, "
            "functional-region, regulator, and protein-correction evidence together, "
            "and link every narrative claim back to a stable card id"
        ),
    )


def render_ptm_evidence_card_summary_tsv(report: PtmEvidenceCardReport) -> str:
    """Render a compact PTM evidence-card summary as TSV."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "condition_a",
            "condition_b",
            "significant_site_count",
            "card_count",
            "narrative_claim_count",
            "regulator_supported_card_count",
            "motif_annotated_card_count",
            "crosstalk_supported_card_count",
            "mechanism_classified_card_count",
            "ortholog_context_card_count",
            "functional_context_card_count",
            "warning_card_count",
        )
    )
    writer.writerow(
        (
            report.condition_a,
            report.condition_b,
            report.summary.significant_site_count,
            report.summary.card_count,
            report.summary.narrative_claim_count,
            report.summary.regulator_supported_card_count,
            report.summary.motif_annotated_card_count,
            report.summary.crosstalk_supported_card_count,
            report.summary.mechanism_classified_card_count,
            report.summary.ortholog_context_card_count,
            report.summary.functional_context_card_count,
            report.summary.warning_card_count,
        )
    )
    return buffer.getvalue()


def render_ptm_evidence_card_tsv(report: PtmEvidenceCardReport) -> str:
    """Render PTM evidence cards as a flat TSV ledger."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "card_id",
            "card_kind",
            "subject_kind",
            "subject_id",
            "subject_label",
            "claim",
            "evidence_for",
            "evidence_against",
            "confidence",
            "warning_codes",
            "source_ids",
            "site_key",
            "protein_ref",
            "residue",
            "position",
            "modification_name",
            "target_decoy_label",
            "identity_level",
            "identity_reason",
            "condition_a",
            "condition_b",
            "adjusted_p_value",
            "log2_fold_change",
            "corrected_log2_fold_change",
            "localization_tier",
            "protein_correction_status",
            "mechanism_class",
            "mechanism_reason_codes",
            "peptide_spectrum_count",
            "observed_sample_count",
            "centered_windows",
            "ortholog_conservation_status",
            "ortholog_conservation_species_pair",
            "ortholog_target_site_keys",
            "ortholog_target_protein_refs",
            "functional_regions",
            "regulators",
            "crosstalk_partner_site_keys",
            "crosstalk_relationships",
            "crosstalk_evidence_sources",
            "crosstalk_shared_pathways",
            "claim_ids",
            "source_row_refs",
            "derived_no_source_reason",
        )
    )
    for entry in report.cards:
        standard_card = _build_standard_card_entry(entry)
        writer.writerow(
            (
                *render_standard_card_row(standard_card),
                entry.site_key,
                entry.protein_ref,
                entry.residue,
                entry.position,
                entry.modification_name,
                entry.target_decoy_label.value,
                entry.identity_level.value,
                entry.identity_reason,
                entry.differential_result.condition_a,
                entry.differential_result.condition_b,
                "" if entry.differential_result.adjusted_p_value is None else entry.differential_result.adjusted_p_value,
                entry.differential_result.log2_fold_change,
                (
                    ""
                    if entry.protein_correction.corrected_log2_fold_change is None
                    else entry.protein_correction.corrected_log2_fold_change
                ),
                entry.localization.localization_tier.value,
                entry.protein_correction.status,
                (
                    ""
                    if entry.mechanism_classification is None
                    else entry.mechanism_classification.mechanism_class.value
                ),
                (
                    ""
                    if entry.mechanism_classification is None
                    else ";".join(
                        reason.value
                        for reason in entry.mechanism_classification.reason_codes
                    )
                ),
                len(entry.peptide_evidence),
                0 if entry.quantification is None else entry.quantification.observed_sample_count,
                ";".join(entry.motif_evidence.centered_windows),
                (
                    ""
                    if entry.ortholog_conservation is None
                    else entry.ortholog_conservation.status.value
                ),
                (
                    ""
                    if entry.ortholog_conservation is None
                    else (
                        f"{entry.ortholog_conservation.source_species}->"
                        f"{entry.ortholog_conservation.target_species}"
                    )
                ),
                (
                    ""
                    if entry.ortholog_conservation is None
                    else ";".join(entry.ortholog_conservation.ortholog_target_site_keys)
                ),
                (
                    ""
                    if entry.ortholog_conservation is None
                    else ";".join(
                        entry.ortholog_conservation.ortholog_target_protein_refs
                    )
                ),
                ";".join(
                    f"{region.region_kind.value}:{region.label}@{region.start}-{region.end}"
                    for region in entry.functional_regions
                ),
                ";".join(
                    f"{regulator.regulator}:{regulator.direction}"
                    for regulator in entry.regulator_evidence
                ),
                ";".join(
                    partner.partner_site_key for partner in entry.crosstalk_partners
                ),
                ";".join(
                    partner.relationship.value for partner in entry.crosstalk_partners
                ),
                ";".join(
                    ",".join(source.value for source in partner.evidence_sources)
                    for partner in entry.crosstalk_partners
                ),
                ";".join(
                    ",".join(partner.shared_pathways)
                    for partner in entry.crosstalk_partners
                    if partner.shared_pathways
                ),
                ";".join(entry.claim_ids),
                ";".join(entry.source_row_refs),
                ""
                if entry.derived_no_source_reason is None
                else entry.derived_no_source_reason,
            )
        )
    return buffer.getvalue()


def _build_standard_card_entry(entry: PtmEvidenceCard) -> StandardCardEntry:
    return StandardCardEntry(
        card_id=entry.card_id,
        card_kind=StandardCardKind.PTM,
        subject_kind=StandardCardSubjectKind.PTM_SITE,
        subject_id=entry.site_key,
        subject_label=(
            f"{entry.protein_ref} {entry.residue}{entry.position} {entry.modification_name}"
        ),
        claim=(
            f"PTM site {entry.site_key} has log2 fold change "
            f"{entry.differential_result.log2_fold_change:g} between "
            f"{entry.differential_result.condition_a} and {entry.differential_result.condition_b}."
        ),
        evidence_for=(
            f"localization tier is {entry.localization.localization_tier.value}; "
            f"{len(entry.peptide_evidence)} peptide-spectrum matches support this site."
        ),
        evidence_against=(
            "no explicit weakening evidence was preserved on this PTM card."
            if not entry.warnings
            else "warnings remained attached: "
            + ", ".join(warning.code.value for warning in entry.warnings)
            + "."
        ),
        confidence=_standard_card_confidence(entry.localization.localization_tier),
        warning_codes=tuple(warning.code.value for warning in entry.warnings),
        source_ids=tuple(dict.fromkeys((*entry.source_row_refs, *entry.claim_ids))),
    )


def _standard_card_confidence(localization_tier: PtmLocalizationConfidenceTier):
    if localization_tier is PtmLocalizationConfidenceTier.HIGH_CONFIDENCE:
        return ConfidenceTier.HIGH
    if localization_tier is PtmLocalizationConfidenceTier.SUPPORTED:
        return ConfidenceTier.MODERATE
    return ConfidenceTier.LOW


def render_ptm_evidence_claim_tsv(report: PtmEvidenceCardReport) -> str:
    """Render PTM evidence-card narrative claims as TSV."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "claim_id",
            "card_id",
            "site_key",
            "claim_kind",
            "text",
            "source_row_refs",
            "derived_no_source_reason",
        )
    )
    for entry in report.narrative_claims:
        writer.writerow(
            (
                entry.claim_id,
                entry.card_id,
                entry.site_key,
                entry.claim_kind.value,
                entry.text,
                ";".join(entry.source_row_refs),
                ""
                if entry.derived_no_source_reason is None
                else entry.derived_no_source_reason,
            )
        )
    return buffer.getvalue()


def export_ptm_evidence_card_summary_tsv(
    report: PtmEvidenceCardReport,
    path: Path,
) -> None:
    """Write PTM evidence-card summary to a stable TSV artifact."""

    write_output_table_tsv(path, render_ptm_evidence_card_summary_tsv(report))


def export_ptm_evidence_card_tsv(
    report: PtmEvidenceCardReport,
    path: Path,
) -> None:
    """Write PTM evidence cards to a stable TSV artifact."""

    write_output_table_tsv(path, render_ptm_evidence_card_tsv(report))


def export_ptm_evidence_claim_tsv(
    report: PtmEvidenceCardReport,
    path: Path,
) -> None:
    """Write PTM evidence-card narrative claims to a stable TSV artifact."""

    write_output_table_tsv(path, render_ptm_evidence_claim_tsv(report))


def _build_peptide_evidence(
    records: tuple[PtmEvidenceRecord, ...],
    site_entry: PtmSiteEntry,
) -> tuple[PtmEvidenceCardPeptideObservation, ...]:
    observations = tuple(
        PtmEvidenceCardPeptideObservation(
            spectrum_id=record.spectrum_id,
            sample_id=record.sample_id,
            localized_peptide=record.localized_peptide,
            canonical_peptide=record.canonical_peptide,
            charge=record.charge,
            score=record.score,
            q_value=record.q_value,
            protein_refs=record.protein_refs,
        )
        for record in _matching_records_for_site(records, site_entry)
    )
    return tuple(
        sort_rows_by_fields(
            observations,
            "spectrum_id",
            "sample_id",
            "localized_peptide",
        )
    )


def _build_source_row_lineage_for_site(
    records: tuple[PtmEvidenceRecord, ...],
    site_entry: PtmSiteEntry,
) -> SourceRowLineage:
    matching_records = _matching_records_for_site(records, site_entry)
    if matching_records:
        return SourceRowLineage.from_imported_provenances(
            tuple(record.provenance for record in matching_records)
        )
    return SourceRowLineage.from_imported_provenances(
        (site_entry.provenance,),
        derived_no_source_reason=(
            "ptm evidence cards summarize governed site-level differential evidence but exact source-row pairs were not retained after site aggregation"
        ),
    )


def _matching_records_for_site(
    records: tuple[PtmEvidenceRecord, ...],
    site_entry: PtmSiteEntry,
) -> tuple[PtmEvidenceRecord, ...]:
    return tuple(
        record
        for record in records
        if site_entry.protein_ref in record.protein_refs
        and record.localized_peptide in site_entry.localized_peptides
        and site_entry.modification_name in record.modification_names
    )


def _build_localization_evidence(
    localization_entries: tuple[PtmLocalizationScoringEntry, ...],
    *,
    differential_entry: PtmSiteDifferentialEntry,
    site_entry: PtmSiteEntry,
) -> PtmEvidenceCardLocalization:
    observations = tuple(
        PtmEvidenceCardLocalizationObservation(
            spectrum_id=entry.spectrum_id,
            sample_id=entry.sample_id,
            localized_peptide=entry.localized_peptide,
            peptide_site_index=entry.peptide_site_index,
            candidate_site_indices=entry.candidate_site_indices,
            ambiguity_group=entry.ambiguity_group,
            localization_probability=entry.localization_probability,
            probability_source=entry.probability_source,
            localization_tier=entry.localization_tier,
            supported_site_determining_ions=entry.supported_site_determining_ions,
        )
        for entry in localization_entries
        if entry.localized_peptide in site_entry.localized_peptides
        and entry.modification_name == differential_entry.modification_name
    )
    stable_observations = tuple(
        sort_rows_by_fields(
            observations,
            "spectrum_id",
            "peptide_site_index",
            "localized_peptide",
        )
    )
    probabilities = tuple(
        sorted(
            {
                observation.localization_probability
                for observation in stable_observations
            }
        )
    )
    return PtmEvidenceCardLocalization(
        localization_tier=differential_entry.localization_tier,
        low_localization=differential_entry.low_localization,
        ambiguous=differential_entry.ambiguous,
        shared_peptide=differential_entry.shared_peptide,
        localized_peptides=site_entry.localized_peptides,
        observations=stable_observations,
        best_localization_probability=(
            None if not probabilities else probabilities[-1]
        ),
        supported_site_determining_ion_count=sum(
            len(observation.supported_site_determining_ions)
            for observation in stable_observations
        ),
    )


def _build_identity_entries_by_site(
    records: tuple[PtmEvidenceRecord, ...],
    *,
    site_entries: tuple[PtmSiteEntry, ...],
    protein_records: tuple[NormalizedProteinRecord, ...] | None,
    protein_sequences: dict[str, str] | None,
) -> dict[str, ProteinIdentityResolutionEntry]:
    if not protein_records and not protein_sequences:
        return {}
    references: list[ProteinIdentityReference] = []
    for site_entry in site_entries:
        peptide_evidence = _build_peptide_evidence(records, site_entry)
        references.append(
            ProteinIdentityReference(
                evidence_key=site_entry.site_key,
                target_protein_ref=site_entry.protein_ref,
                candidate_protein_refs=tuple(
                    dict.fromkeys(
                        (
                            site_entry.protein_ref,
                            *(
                                protein_ref
                                for observation in peptide_evidence
                                for protein_ref in observation.protein_refs
                            ),
                        )
                    )
                ),
                peptide_sequences=tuple(
                    dict.fromkeys(
                        observation.canonical_peptide
                        for observation in peptide_evidence
                    )
                ),
            )
        )
    report = build_protein_identity_resolution_report(
        tuple(references),
        protein_records=() if protein_records is None else protein_records,
        protein_sequences=protein_sequences,
    )
    return {
        entry.evidence_key: entry
        for entry in report.entries
    }


def _build_crosstalk_partners_by_site(
    site_entries: tuple[PtmSiteEntry, ...],
    differential_report: PtmSiteDifferentialReport,
    *,
    annotation_mapping_report: PtmSiteAnnotationMappingReport | None = None,
) -> dict[str, tuple[PtmEvidenceCardCrosstalkPartner, ...]]:
    crosstalk_report = build_ptm_crosstalk_report(
        site_entries,
        differential_report,
        annotation_mapping_report=annotation_mapping_report,
    )
    partners_by_site: dict[str, list[PtmEvidenceCardCrosstalkPartner]] = {}
    for entry in crosstalk_report.entries:
        partners_by_site.setdefault(entry.left_site_key, []).append(
            PtmEvidenceCardCrosstalkPartner(
                partner_site_key=entry.right_site_key,
                partner_protein_ref=entry.right_protein_ref,
                partner_modification_name=entry.right_modification_name,
                partner_position=entry.right_position,
                partner_log2_fold_change=entry.right_log2_fold_change,
                relationship=entry.relationship,
                evidence_sources=entry.evidence_sources,
                shared_peptides=entry.shared_peptides,
                shared_pathways=entry.shared_pathways,
                residue_distance=entry.residue_distance,
                evidence_note=entry.evidence_note,
            )
        )
        partners_by_site.setdefault(entry.right_site_key, []).append(
            PtmEvidenceCardCrosstalkPartner(
                partner_site_key=entry.left_site_key,
                partner_protein_ref=entry.left_protein_ref,
                partner_modification_name=entry.left_modification_name,
                partner_position=entry.left_position,
                partner_log2_fold_change=entry.left_log2_fold_change,
                relationship=entry.relationship,
                evidence_sources=entry.evidence_sources,
                shared_peptides=entry.shared_peptides,
                shared_pathways=entry.shared_pathways,
                residue_distance=entry.residue_distance,
                evidence_note=entry.evidence_note,
            )
        )
    return {
        site_key: tuple(
            sorted(partners, key=lambda partner: partner.partner_site_key)
        )
        for site_key, partners in partners_by_site.items()
    }


def _build_mechanism_classification_by_site(
    mechanism_classification_report: PtmMechanismClassificationReport | None,
) -> dict[str, PtmEvidenceCardMechanismClassification]:
    if mechanism_classification_report is None:
        return {}
    return {
        entry.site_key: PtmEvidenceCardMechanismClassification(
            mechanism_class=entry.mechanism_class,
            reason_codes=entry.reason_codes,
            raw_log2_fold_change=entry.raw_log2_fold_change,
            corrected_log2_fold_change=entry.corrected_log2_fold_change,
            protein_log2_fold_change=entry.protein_log2_fold_change,
            protein_adjusted_p_value=entry.protein_adjusted_p_value,
            note=entry.note,
        )
        for entry in mechanism_classification_report.entries
    }


def _build_ortholog_conservation_by_site(
    ortholog_conservation_report: PtmOrthologConservationReport | None,
) -> dict[str, PtmEvidenceCardOrthologConservation]:
    if ortholog_conservation_report is None:
        return {}
    return {
        entry.site_key: PtmEvidenceCardOrthologConservation(
            status=entry.status,
            source_species=entry.source_species,
            target_species=entry.target_species,
            ortholog_target_site_keys=entry.ortholog_target_site_keys,
            ortholog_target_protein_refs=entry.ortholog_target_protein_refs,
            ortholog_target_positions=entry.ortholog_target_positions,
            evidence_labels=entry.evidence_labels,
            source_names=entry.source_names,
            source_accessions=entry.source_accessions,
            note=entry.note,
        )
        for entry in ortholog_conservation_report.entries
    }


def _build_quantification_evidence(
    quant_row: PtmSiteQuantRow | None,
) -> PtmEvidenceCardQuantification | None:
    if quant_row is None:
        return None
    sample_values = tuple(
        PtmEvidenceCardSampleValue(
            sample_id=value.sample_id,
            abundance=value.abundance,
            missing_value_kind=value.missing_value_kind,
            contributing_feature_count=value.contributing_feature_count,
        )
        for value in quant_row.values
    )
    return PtmEvidenceCardQuantification(
        sample_values=sample_values,
        observed_sample_count=sum(
            1
            for value in sample_values
            if value.missing_value_kind is MissingValueKind.OBSERVED
        ),
        zero_sample_count=sum(
            1
            for value in sample_values
            if value.missing_value_kind is MissingValueKind.ZERO
        ),
        missing_sample_count=sum(
            1
            for value in sample_values
            if value.missing_value_kind is MissingValueKind.NOT_OBSERVED
        ),
        filtered_sample_count=sum(
            1
            for value in sample_values
            if value.missing_value_kind is MissingValueKind.FILTERED
        ),
    )


def _build_motif_evidence(
    motif_enrichment: PtmPhosphositeMotifEnrichmentReport | None,
    *,
    site_key: str,
) -> PtmEvidenceCardMotifEvidence:
    if motif_enrichment is None:
        return PtmEvidenceCardMotifEvidence()
    matching_windows = tuple(
        sort_strings(
            tuple(
                window.centered_window
                for window in motif_enrichment.regulated_windows
                if window.site_key == site_key
            )
        )
    )
    enriched_terms = (
        tuple(
            f"{entry.position_offset:+d}:{entry.residue}"
            for entry in motif_enrichment.enriched_terms
        )
        if matching_windows
        else ()
    )
    return PtmEvidenceCardMotifEvidence(
        centered_windows=matching_windows,
        enriched_terms=enriched_terms,
    )


def _build_card_warnings(
    *,
    differential_entry: PtmSiteDifferentialEntry,
    site_entry: PtmSiteEntry,
) -> tuple[PtmEvidenceCardWarning, ...]:
    warnings: list[PtmEvidenceCardWarning] = []
    if differential_entry.low_localization:
        warnings.append(
            PtmEvidenceCardWarning(
                code=PtmEvidenceCardWarningCode.LOW_LOCALIZATION,
                message="site differential remains low-localization and requires explicit review",
            )
        )
    if differential_entry.ambiguous:
        warnings.append(
            PtmEvidenceCardWarning(
                code=PtmEvidenceCardWarningCode.AMBIGUOUS_SITE,
                message="site evidence remains ambiguous across candidate positions",
            )
        )
    if differential_entry.shared_peptide:
        warnings.append(
            PtmEvidenceCardWarning(
                code=PtmEvidenceCardWarningCode.SHARED_PEPTIDE,
                message="site evidence is carried by a peptide shared across proteins",
            )
        )
    if site_entry.target_decoy_label is TargetDecoyLabel.DECOY:
        warnings.append(
            PtmEvidenceCardWarning(
                code=PtmEvidenceCardWarningCode.DECOY_SITE,
                message="site evidence originates from decoy-labeled PTM support",
            )
        )
    if (
        differential_entry.protein_correction_status
        == PtmProteinCorrectionStatus.MISSING_PROTEIN_BASELINE.value
    ):
        warnings.append(
            PtmEvidenceCardWarning(
                code=PtmEvidenceCardWarningCode.MISSING_PROTEIN_BASELINE,
                message="protein-abundance correction could not be applied because matched protein evidence was missing",
            )
        )
    if (
        differential_entry.protein_correction_status
        == PtmProteinCorrectionStatus.CORRECTED_LOW_LOCALIZATION.value
    ):
        warnings.append(
            PtmEvidenceCardWarning(
                code=PtmEvidenceCardWarningCode.CORRECTED_LOW_LOCALIZATION,
                message="protein-abundance correction is present but remains review-only because localization is weak",
            )
        )
    return tuple(warnings)


def _build_card_id(
    differential_entry: PtmSiteDifferentialEntry,
    *,
    site_id: str,
) -> str:
    return build_ptm_card_id(
        site_id,
        differential_entry.condition_a,
        differential_entry.condition_b,
    )


def _build_claim_id(
    differential_entry: PtmSiteDifferentialEntry,
    *,
    site_id: str,
) -> str:
    return build_ptm_claim_id(
        site_id,
        differential_entry.condition_a,
        differential_entry.condition_b,
    )


def _build_claim_text(
    differential_entry: PtmSiteDifferentialEntry,
    *,
    motif_evidence: PtmEvidenceCardMotifEvidence,
    regulators: tuple[PtmEvidenceCardRegulatorEvidence, ...],
) -> str:
    condition_phrase = (
        f"{differential_entry.condition_b} versus {differential_entry.condition_a}"
    )
    fragments = [
        (
            f"{differential_entry.site_key} changed in {condition_phrase} "
            f"with log2 fold change {differential_entry.log2_fold_change:.3g} "
            f"and adjusted p-value {differential_entry.adjusted_p_value:.3g}"
        )
    ]
    if motif_evidence.centered_windows:
        fragments.append(
            f"motif window {motif_evidence.centered_windows[0]} supports sequence context"
        )
    if regulators:
        fragments.append(
            "linked regulators include "
            + ", ".join(
                f"{entry.regulator} ({entry.direction})" for entry in regulators[:3]
            )
        )
    return "; ".join(fragments)


def _slugify(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
