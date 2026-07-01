# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Schema models for PTM evidence-card surfaces."""

from __future__ import annotations

from enum import StrEnum

from pydantic import ConfigDict, Field, model_validator

from bijux_proteomics.domain.source_row_lineage import SourceRowLineage
from bijux_proteomics.identification import TargetDecoyLabel
from bijux_proteomics.ptm.crosstalk import (
    PtmCrosstalkEvidenceSource,
    PtmCrosstalkRelationship,
)
from bijux_proteomics.ptm.differential_analysis import PtmProteinCorrectionMode
from bijux_proteomics.ptm.localization_scoring import (
    PtmLocalizationConfidenceTier,
    PtmLocalizationProbabilitySource,
)
from bijux_proteomics.ptm.mechanism_classification import (
    PtmMechanismClass,
    PtmMechanismReasonCode,
)
from bijux_proteomics.ptm.ortholog_site_conservation import (
    PtmOrthologConservationStatus,
)
from bijux_proteomics.ptm.regulator_enrichment import PtmRegulatorKind
from bijux_proteomics.quantification.contracts.input_models import MissingValueKind
from bijux_proteomics.sequences.protein_identity_resolution import ProteinIdentityLevel
from bijux_proteomics.sequences.protein_region_context_models import (
    ProteinFunctionalRegionEvidence,
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


__all__ = [
    "PtmEvidenceCard",
    "PtmEvidenceCardClaim",
    "PtmEvidenceCardClaimKind",
    "PtmEvidenceCardCrosstalkPartner",
    "PtmEvidenceCardDifferentialResult",
    "PtmEvidenceCardLocalization",
    "PtmEvidenceCardLocalizationObservation",
    "PtmEvidenceCardMechanismClassification",
    "PtmEvidenceCardMotifEvidence",
    "PtmEvidenceCardPeptideObservation",
    "PtmEvidenceCardPolicy",
    "PtmEvidenceCardProteinCorrection",
    "PtmEvidenceCardQuantification",
    "PtmEvidenceCardRegulatorEvidence",
    "PtmEvidenceCardReport",
    "PtmEvidenceCardSampleValue",
    "PtmEvidenceCardSummary",
    "PtmEvidenceCardWarning",
    "PtmEvidenceCardWarningCode",
    "PtmEvidenceCardOrthologConservation",
]
