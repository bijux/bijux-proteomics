# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Evidence bundles for scientific review."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from enum import StrEnum
from typing import cast

from pydantic import ConfigDict, Field

from bijux_proteomics_foundation import (
    DocumentSchema,
    EvidenceId,
    JsonModel,
    TargetId,
)


class EvidenceKind(StrEnum):
    """Evidence families tracked by the platform."""

    SEQUENCE_HOMOLOGY = "sequence_homology"
    CONSERVATION = "conservation"
    LITERATURE = "literature"
    STRUCTURE = "structure"
    BINDING = "binding"
    ENZYMATIC = "enzymatic"
    ASSAY = "assay"
    CELLULAR = "cellular"
    PHENOTYPE = "phenotype"
    PATHWAY = "pathway"
    SAFETY = "safety"
    DEVELOPABILITY = "developability"
    MANUFACTURABILITY = "manufacturability"
    DIFFERENTIAL_PROTEOMICS = "differential_proteomics"
    PHOSPHOPROTEOMICS = "phosphoproteomics"
    INTERACTOMICS = "interactomics"
    TARGET_ENGAGEMENT = "target_engagement"


class EvidenceStrength(StrEnum):
    """How strongly an evidence record supports a claim."""

    EXPLORATORY = "exploratory"
    SUPPORTING = "supporting"
    DECISIVE = "decisive"


class EvidenceSourceType(StrEnum):
    """Source categories used for trust weighting."""

    LITERATURE = "literature"
    STRUCTURE_MODEL = "structure_model"
    LAB_ASSAY = "lab_assay"
    CURATED_NOTE = "curated_note"
    EXTERNAL_DATABASE = "external_database"


class EvidenceOrigin(StrEnum):
    """Origin of an evidence record."""

    OBSERVED = "observed"
    INFERRED = "inferred"
    IMPORTED = "imported"
    SYNTHETIC = "synthetic"


class EvidenceExtractionMethod(StrEnum):
    """How the evidence record was produced."""

    MANUAL_CURATION = "manual_curation"
    AUTOMATED_IMPORT = "automated_import"
    MODEL_INFERENCE = "model_inference"
    LAB_CAPTURE = "lab_capture"


class QuantitativeSupport(JsonModel):
    """Quantitative support for an evidence claim."""

    model_config = ConfigDict(extra="forbid")

    effect_size: float | None = Field(default=None, description="Observed effect size.")
    confidence_interval_low: float | None = Field(
        default=None,
        description="Lower bound of the confidence interval.",
    )
    confidence_interval_high: float | None = Field(
        default=None,
        description="Upper bound of the confidence interval.",
    )
    confidence_interval_level: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Confidence level associated with the interval estimate.",
    )
    variance: float | None = Field(
        default=None, ge=0.0, description="Observed variance."
    )
    coefficient_of_variation: float | None = Field(
        default=None,
        ge=0.0,
        description="Coefficient of variation for replicate measurements.",
    )
    p_value: float | None = Field(
        default=None, ge=0.0, le=1.0, description="Nominal p-value."
    )
    q_value: float | None = Field(
        default=None, ge=0.0, le=1.0, description="Multiple-test adjusted q-value."
    )
    replicate_count: int | None = Field(
        default=None, ge=1, description="Replicate count behind the observation."
    )
    peptide_count: int | None = Field(
        default=None, ge=1, description="Number of quantified peptides."
    )
    protein_coverage: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Protein sequence coverage fraction.",
    )
    site_localization_probability: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="PTM site localization probability when relevant.",
    )
    censored_by_detection_limit: bool = Field(
        default=False,
        description="Whether the estimate is censored by detection limits.",
    )
    detection_limit_value: float | None = Field(
        default=None,
        ge=0.0,
        description="Lower or upper detection limit associated with censoring.",
    )
    censoring_direction: str | None = Field(
        default=None,
        description="Direction of censoring such as left-censored or right-censored.",
    )
    absolute_scale: bool = Field(
        default=False,
        description="Whether the quantitative estimate is on an absolute scale.",
    )
    scale_type: str | None = Field(
        default=None,
        description="Scale semantics such as fold-change, log2-ratio, or concentration.",
    )
    unit: str | None = Field(
        default=None, description="Measurement unit for quantitative effects."
    )


class ProteomicsArtifactFlags(JsonModel):
    """Common proteomics artifact flags that affect interpretation confidence."""

    model_config = ConfigDict(extra="forbid")

    missing_not_at_random: bool = Field(
        default=False, description="Potential MNAR missingness."
    )
    ion_interference: bool = Field(
        default=False, description="Potential ion interference or suppression."
    )
    peptide_to_protein_ambiguity: bool = Field(
        default=False,
        description="Peptides may map ambiguously across proteins.",
    )
    ptm_site_localization_uncertain: bool = Field(
        default=False,
        description="PTM localization is uncertain.",
    )


class EvidenceRecord(JsonModel):
    """Single evidence statement."""

    model_config = ConfigDict(extra="forbid")

    evidence_id: EvidenceId = Field(..., description="Stable evidence identifier.")
    kind: EvidenceKind = Field(..., description="Evidence family.")
    title: str = Field(..., min_length=1, description="Short title.")
    source: str = Field(..., min_length=1, description="Source location or system.")
    source_type: EvidenceSourceType = Field(
        default=EvidenceSourceType.CURATED_NOTE,
        description="Source category for trust policies.",
    )
    source_uri: str | None = Field(
        default=None,
        description="Stable URI or locator for the source.",
    )
    origin: EvidenceOrigin = Field(
        default=EvidenceOrigin.OBSERVED,
        description="Whether the evidence was observed, inferred, imported, or synthetic.",
    )
    extraction_method: EvidenceExtractionMethod = Field(
        default=EvidenceExtractionMethod.MANUAL_CURATION,
        description="How the evidence record was produced.",
    )
    assay_modality: str | None = Field(
        default=None,
        description="Assay modality such as biochemical, cellular, or proteomics.",
    )
    biological_system: str | None = Field(
        default=None,
        description="Biological system where the observation was generated.",
    )
    species: str | None = Field(
        default=None, description="Species context for the evidence."
    )
    sample_type: str | None = Field(
        default=None,
        description="Sample or matrix type used for the observation.",
    )
    endpoint: str | None = Field(
        default=None,
        description="Primary endpoint measured by this evidence record.",
    )
    dose: str | None = Field(
        default=None, description="Dose level or concentration used in the experiment."
    )
    timepoint: str | None = Field(
        default=None, description="Measurement timepoint for the observed signal."
    )
    perturbation: str | None = Field(
        default=None, description="Perturbation applied to the system."
    )
    control_design: str | None = Field(
        default=None,
        description="Control arm design for the experiment.",
    )
    replicate_design: str | None = Field(
        default=None,
        description="Replicate design such as technical triplicate or biological duplicate.",
    )
    normalization_method: str | None = Field(
        default=None,
        description="Normalization method used for quantitative processing.",
    )
    sample_preparation: str | None = Field(
        default=None,
        description="Sample preparation method before measurement.",
    )
    tissue_context: str | None = Field(
        default=None,
        description="Tissue context used for the evidence generation.",
    )
    cell_line_context: str | None = Field(
        default=None,
        description="Cell line context when experiments are cell based.",
    )
    quantitative_support: QuantitativeSupport | None = Field(
        default=None,
        description="Optional quantitative support payload for the claim.",
    )
    artifact_flags: ProteomicsArtifactFlags | None = Field(
        default=None,
        description="Optional proteomics artifact flags affecting interpretation.",
    )
    curator: str | None = Field(
        default=None,
        description="Human or system responsible for producing the record.",
    )
    claim: str = Field(..., min_length=1, description="Human-readable claim.")
    related_targets: list[str] = Field(
        default_factory=list,
        description="Related target identifiers.",
    )
    decision_tags: list[str] = Field(
        default_factory=list,
        description="Decision dimensions informed by the record.",
    )
    derived_from: list[str] = Field(
        default_factory=list,
        description="Upstream evidence identifiers or source records.",
    )
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Confidence in the record.",
    )
    strength: EvidenceStrength = Field(..., description="Support level.")
    observed_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="When the evidence was produced or observed.",
    )
    expires_at: datetime | None = Field(
        default=None,
        description="Optional point after which the evidence should be treated as stale.",
    )


class EvidenceBundle(JsonModel):
    """Set of evidence attached to a program or target."""

    model_config = ConfigDict(extra="forbid")

    bundle_id: EvidenceId = Field(..., description="Stable bundle identifier.")
    target_id: TargetId = Field(..., description="Target identifier.")
    document_schema: DocumentSchema = Field(
        default_factory=lambda: DocumentSchema(created_by="bijux-proteomics-knowledge"),
        description="Schema and provenance metadata.",
    )
    records: list[EvidenceRecord] = Field(
        default_factory=list,
        description="Evidence records in the bundle.",
    )


class EvidenceCoverage(JsonModel):
    """Coverage and strength of the current evidence bundle."""

    model_config = ConfigDict(extra="forbid")

    bundle_id: EvidenceId = Field(..., description="Stable bundle identifier.")
    target_id: TargetId = Field(..., description="Target identifier.")
    by_kind: dict[str, int] = Field(
        default_factory=dict,
        description="Count of records grouped by evidence kind.",
    )
    missing_kinds: list[str] = Field(
        default_factory=list,
        description="Required kinds that are still missing.",
    )
    decisive_records: int = Field(
        default=0,
        ge=0,
        description="Number of decisive records in the bundle.",
    )
    mean_confidence: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Average confidence across records.",
    )


class DecisionReadiness(JsonModel):
    """Whether the current evidence is strong enough for a program decision."""

    model_config = ConfigDict(extra="forbid")

    target_id: TargetId = Field(..., description="Target identifier.")
    ready: bool = Field(..., description="Whether the bundle is decision-ready.")
    blockers: list[str] = Field(
        default_factory=list,
        description="Specific reasons a decision should not proceed yet.",
    )
    recommendations: list[str] = Field(
        default_factory=list,
        description="Concrete actions to improve readiness.",
    )
    coverage: EvidenceCoverage = Field(
        ...,
        description="Coverage report used for the readiness call.",
    )


class EvidenceConflict(JsonModel):
    """Two records that appear to disagree about the same decision area."""

    model_config = ConfigDict(extra="forbid")

    conflict_type: str = Field(
        default="generic",
        min_length=1,
        description="Stable conflict taxonomy for policy and analytics.",
    )
    severity: str = Field(
        default="medium",
        min_length=1,
        description="Severity tier used to prioritize resolution.",
    )
    left_evidence_id: str = Field(
        ..., min_length=1, description="First evidence identifier."
    )
    right_evidence_id: str = Field(
        ..., min_length=1, description="Second evidence identifier."
    )
    reason: str = Field(
        ..., min_length=1, description="Why the pair is considered conflicting."
    )


class BundleTrustReport(JsonModel):
    """Trust summary for an evidence bundle."""

    model_config = ConfigDict(extra="forbid")

    bundle_id: str = Field(..., min_length=1, description="Stable bundle identifier.")
    target_id: str = Field(..., min_length=1, description="Target identifier.")
    trust_score: float = Field(..., ge=0.0, le=1.0, description="Overall trust score.")
    stale_records: list[str] = Field(
        default_factory=list,
        description="Evidence identifiers that should be refreshed.",
    )
    conflicts: list[EvidenceConflict] = Field(
        default_factory=list,
        description="Detected evidence conflicts.",
    )
    duplicate_groups: list[list[str]] = Field(
        default_factory=list,
        description="Potential duplicate evidence identifiers.",
    )


class TrustPolicy(JsonModel):
    """Explicit policy for evidence trust scoring."""

    model_config = ConfigDict(extra="forbid")

    policy_id: str = Field(
        ..., min_length=1, description="Stable trust policy identifier."
    )
    source_type_weights: dict[EvidenceSourceType, float] = Field(
        default_factory=lambda: {
            EvidenceSourceType.LAB_ASSAY: 1.0,
            EvidenceSourceType.LITERATURE: 0.9,
            EvidenceSourceType.EXTERNAL_DATABASE: 0.8,
            EvidenceSourceType.STRUCTURE_MODEL: 0.75,
            EvidenceSourceType.CURATED_NOTE: 0.65,
        },
        description="Weight applied to each evidence source category.",
    )
    strength_weights: dict[EvidenceStrength, float] = Field(
        default_factory=lambda: {
            EvidenceStrength.EXPLORATORY: 0.5,
            EvidenceStrength.SUPPORTING: 0.8,
            EvidenceStrength.DECISIVE: 1.0,
        },
        description="Weight applied to each evidence strength level.",
    )
    stale_penalty: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Penalty multiplier applied to stale evidence.",
    )
    stale_record_penalty: float = Field(
        default=0.05,
        ge=0.0,
        le=1.0,
        description="Penalty applied per stale record at the bundle level.",
    )
    conflict_penalty: float = Field(
        default=0.1,
        ge=0.0,
        le=1.0,
        description="Penalty applied per detected conflict.",
    )
    duplicate_penalty: float = Field(
        default=0.03,
        ge=0.0,
        le=1.0,
        description="Penalty applied per duplicate group.",
    )
    max_age_days_by_source: dict[EvidenceSourceType, int] = Field(
        default_factory=lambda: {
            EvidenceSourceType.LAB_ASSAY: 180,
            EvidenceSourceType.LITERATURE: 365,
            EvidenceSourceType.EXTERNAL_DATABASE: 120,
            EvidenceSourceType.STRUCTURE_MODEL: 240,
            EvidenceSourceType.CURATED_NOTE: 90,
        },
        description="Maximum preferred age in days by source type before evidence is considered stale.",
    )


class ConflictPolicy(JsonModel):
    """Explicit policy for evidence conflict detection."""

    model_config = ConfigDict(extra="forbid")

    policy_id: str = Field(
        ..., min_length=1, description="Stable conflict policy identifier."
    )
    require_shared_decision_tag: bool = Field(
        default=True,
        description="Whether conflicts require overlapping decision tags.",
    )
    detect_assay_readout_conflicts: bool = Field(
        default=True,
        description="Whether same-source assay records with divergent claims should conflict.",
    )
    detect_quantitative_direction_conflicts: bool = Field(
        default=True,
        description="Whether opposite quantitative effect directions should conflict.",
    )
    magnitude_divergence_threshold: float = Field(
        default=1.5,
        ge=0.0,
        description="Minimum absolute effect-size difference to flag magnitude disagreement.",
    )


class EvidenceRefreshPriority(StrEnum):
    """Priority for refreshing stale or aging evidence."""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class EvidenceRefreshNeed(JsonModel):
    """Actionable refresh recommendation for one evidence record."""

    model_config = ConfigDict(extra="forbid")

    evidence_id: str = Field(..., min_length=1, description="Evidence identifier.")
    priority: EvidenceRefreshPriority = Field(
        ...,
        description="Recommended refresh priority.",
    )
    reason: str = Field(..., min_length=1, description="Why refresh is recommended.")
    suggested_action: str = Field(
        ...,
        min_length=1,
        description="Concrete action to improve freshness.",
    )


class BundleFreshnessReport(JsonModel):
    """Freshness posture for an evidence bundle."""

    model_config = ConfigDict(extra="forbid")

    bundle_id: str = Field(..., min_length=1, description="Stable bundle identifier.")
    target_id: str = Field(..., min_length=1, description="Target identifier.")
    stale_records: list[str] = Field(
        default_factory=list,
        description="Records already past their validity window.",
    )
    aging_records: list[str] = Field(
        default_factory=list,
        description="Records nearing expiry and worth refreshing soon.",
    )
    refresh_needs: list[EvidenceRefreshNeed] = Field(
        default_factory=list,
        description="Prioritized refresh actions for the bundle.",
    )


class EvidenceQualityDecomposition(JsonModel):
    """Decomposed quality dimensions for an evidence record."""

    model_config = ConfigDict(extra="forbid")

    assay_validity: float = Field(
        ..., ge=0.0, le=1.0, description="Assay validity signal."
    )
    reproducibility: float = Field(
        ..., ge=0.0, le=1.0, description="Reproducibility signal."
    )
    orthogonality: float = Field(
        ..., ge=0.0, le=1.0, description="Orthogonal support signal."
    )
    biological_relevance: float = Field(
        ..., ge=0.0, le=1.0, description="Biological relevance signal."
    )
    statistical_support: float = Field(
        ..., ge=0.0, le=1.0, description="Statistical support signal."
    )
    context_match: float = Field(
        ..., ge=0.0, le=1.0, description="Context match signal."
    )
    context_relevance: float = Field(
        ..., ge=0.0, le=1.0, description="Biological context relevance."
    )
    source_credibility: float = Field(
        ..., ge=0.0, le=1.0, description="Source credibility signal."
    )
    recency: float = Field(..., ge=0.0, le=1.0, description="Recency signal.")
    derived_confidence: float = Field(
        ..., ge=0.0, le=1.0, description="Confidence derived from dimensions."
    )


class ContextCompatibilityReport(JsonModel):
    """Compatibility of one evidence record with target biological context."""

    model_config = ConfigDict(extra="forbid")

    evidence_id: str = Field(..., min_length=1, description="Evidence identifier.")
    score: float = Field(
        ..., ge=0.0, le=1.0, description="Context compatibility score."
    )
    notes: list[str] = Field(
        default_factory=list, description="Context compatibility notes."
    )


class EvidenceTriangulationReport(JsonModel):
    """Convergence summary across orthogonal evidence modalities."""

    model_config = ConfigDict(extra="forbid")

    target_id: str = Field(..., min_length=1, description="Target identifier.")
    decision_tag: str = Field(
        ..., min_length=1, description="Decision tag under analysis."
    )
    modality_counts: dict[str, int] = Field(
        default_factory=dict, description="Count by modality."
    )
    modality_diversity: int = Field(
        ..., ge=0, description="Number of distinct modalities."
    )
    decisive_share: float = Field(
        ..., ge=0.0, le=1.0, description="Fraction of records with decisive strength."
    )
    missing_required_modalities: list[str] = Field(
        default_factory=list,
        description="Required modalities that are absent for this decision tag.",
    )
    convergence_score: float = Field(
        ..., ge=0.0, le=1.0, description="Triangulation convergence score."
    )


class ArtifactRiskReport(JsonModel):
    """Interpretability risk report based on proteomics artifact flags."""

    model_config = ConfigDict(extra="forbid")

    evidence_id: str = Field(..., min_length=1, description="Evidence identifier.")
    risk_score: float = Field(
        ..., ge=0.0, le=1.0, description="Artifact-derived risk score."
    )
    notes: list[str] = Field(
        default_factory=list, description="Artifact interpretation notes."
    )


class QuantitativeSupportReport(JsonModel):
    """Interpretability report for one quantitative support payload."""

    model_config = ConfigDict(extra="forbid")

    support_score: float = Field(
        ..., ge=0.0, le=1.0, description="Quantitative support quality score."
    )
    notes: list[str] = Field(
        default_factory=list, description="Interpretation notes for score drivers."
    )


class EvidenceContextCompletenessReport(JsonModel):
    """Completeness report for contextual scientific fields on one evidence record."""

    model_config = ConfigDict(extra="forbid")

    evidence_id: str = Field(..., min_length=1, description="Evidence identifier.")
    completeness_score: float = Field(
        ..., ge=0.0, le=1.0, description="Context completeness score."
    )
    missing_fields: list[str] = Field(
        default_factory=list, description="Context fields that are missing."
    )


class ScientificContextCompletenessReport(JsonModel):
    """Completeness report for extended scientific context fields."""

    model_config = ConfigDict(extra="forbid")

    evidence_id: str = Field(..., min_length=1, description="Evidence identifier.")
    completeness_score: float = Field(
        ..., ge=0.0, le=1.0, description="Scientific context completeness score."
    )
    missing_fields: list[str] = Field(
        default_factory=list, description="Scientific context fields that are missing."
    )


class KnowledgeQualityAudit(JsonModel):
    """Cross-cutting quality audit for one evidence bundle and decision tag."""

    model_config = ConfigDict(extra="forbid")

    bundle_id: str = Field(..., min_length=1, description="Bundle identifier.")
    target_id: str = Field(..., min_length=1, description="Target identifier.")
    decision_tag: str = Field(
        ..., min_length=1, description="Decision tag under audit."
    )
    trust_score: float = Field(..., ge=0.0, le=1.0, description="Bundle trust score.")
    triangulation_score: float = Field(
        ..., ge=0.0, le=1.0, description="Decision-tag triangulation score."
    )
    low_context_records: list[str] = Field(
        default_factory=list, description="Records with poor scientific context."
    )
    weak_quantitative_records: list[str] = Field(
        default_factory=list, description="Records with weak quantitative support."
    )
    conflict_count: int = Field(
        default=0, ge=0, description="Number of conflicts in the bundle."
    )
    recommendations: list[str] = Field(
        default_factory=list, description="Actionable quality recommendations."
    )


class QuantitativeCoverageReport(JsonModel):
    """Coverage report for quantitative evidence support within a bundle."""

    model_config = ConfigDict(extra="forbid")

    bundle_id: str = Field(..., min_length=1, description="Bundle identifier.")
    total_records: int = Field(..., ge=0, description="Total records evaluated.")
    quantitative_records: int = Field(
        ..., ge=0, description="Records carrying quantitative support."
    )
    coverage_ratio: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Fraction of records with quantitative support.",
    )


class EvidenceRelevanceScore(JsonModel):
    """Relevance score for one evidence record in a decision context."""

    model_config = ConfigDict(extra="forbid")

    evidence_id: str = Field(..., min_length=1, description="Evidence identifier.")
    relevance_score: float = Field(
        ..., ge=0.0, le=1.0, description="Overall relevance score."
    )
    drivers: list[str] = Field(
        default_factory=list, description="Primary relevance drivers."
    )


class ModalityCoverageReport(JsonModel):
    """Coverage report for required evidence modalities under one decision tag."""

    model_config = ConfigDict(extra="forbid")

    decision_tag: str = Field(
        ..., min_length=1, description="Decision tag under analysis."
    )
    observed_modalities: dict[str, int] = Field(
        default_factory=dict, description="Observed count by modality."
    )
    missing_modalities: list[str] = Field(
        default_factory=list, description="Required modalities not yet observed."
    )
    coverage_score: float = Field(
        ..., ge=0.0, le=1.0, description="Fraction of required modalities observed."
    )


class EvidenceProvenanceReport(JsonModel):
    """Lineage summary for an evidence record within a bundle."""

    model_config = ConfigDict(extra="forbid")

    evidence_id: str = Field(..., min_length=1, description="Evidence identifier.")
    ancestor_ids: list[str] = Field(
        default_factory=list, description="Transitive upstream evidence identifiers."
    )
    lineage_depth: int = Field(
        default=0, ge=0, description="Maximum lineage depth from upstream ancestry."
    )
    has_missing_ancestors: bool = Field(
        default=False,
        description="Whether lineage references missing upstream evidence IDs.",
    )


class ContextScoringProfile(JsonModel):
    """Configurable penalties for biological context mismatch scoring."""

    model_config = ConfigDict(extra="forbid")

    profile_id: str = Field(
        ..., min_length=1, description="Stable context scoring profile identifier."
    )
    species_mismatch_penalty: float = Field(
        default=0.25, ge=0.0, le=1.0, description="Penalty for species mismatch."
    )
    system_mismatch_penalty: float = Field(
        default=0.25,
        ge=0.0,
        le=1.0,
        description="Penalty for biological system mismatch.",
    )
    sample_type_mismatch_penalty: float = Field(
        default=0.2, ge=0.0, le=1.0, description="Penalty for sample-type mismatch."
    )


class EvidenceCollectionAction(JsonModel):
    """Concrete action to improve decision evidence quality."""

    model_config = ConfigDict(extra="forbid")

    priority: str = Field(
        ..., min_length=1, description="Priority tier for the collection action."
    )
    action: str = Field(..., min_length=1, description="Action text for scientists.")
    rationale: str = Field(..., min_length=1, description="Why this action is needed.")


class QuantitativeValidationIssue(JsonModel):
    """Validation issue detected in quantitative evidence support."""

    model_config = ConfigDict(extra="forbid")

    code: str = Field(..., min_length=1, description="Stable issue code.")
    message: str = Field(..., min_length=1, description="Human-readable issue message.")


class BundleIntegrityIssue(JsonModel):
    """Integrity issue detected across evidence bundle records."""

    model_config = ConfigDict(extra="forbid")

    code: str = Field(..., min_length=1, description="Stable issue code.")
    message: str = Field(..., min_length=1, description="Human-readable issue message.")


class DecisionTagNormalizationReport(JsonModel):
    """Summary of decision-tag normalization changes in a bundle."""

    model_config = ConfigDict(extra="forbid")

    changed_records: int = Field(
        default=0, ge=0, description="Number of records whose tags changed."
    )
    normalized_tag_set: list[str] = Field(
        default_factory=list, description="Unique normalized tag values."
    )


def summarize_bundle(bundle: EvidenceBundle) -> dict[str, object]:
    """Build a compact evidence summary."""
    by_kind = {kind.value: 0 for kind in EvidenceKind}
    decisive = 0
    for record in bundle.records:
        by_kind[record.kind.value] += 1
        if record.strength is EvidenceStrength.DECISIVE:
            decisive += 1
    return {
        "bundle_id": bundle.bundle_id,
        "target_id": bundle.target_id,
        "schema_version": bundle.document_schema.schema_version,
        "record_count": len(bundle.records),
        "decisive_records": decisive,
        "by_kind": by_kind,
    }


def decompose_evidence_quality(
    record: EvidenceRecord,
    *,
    now: datetime | None = None,
) -> EvidenceQualityDecomposition:
    """Decompose quality and derive confidence from explicit dimensions."""
    now = now or datetime.now(UTC)
    source_credibility = weight_source_type(
        record.source_type, policy=default_trust_policy()
    )
    assay_validity = min(1.0, 0.4 + (0.6 if record.kind is EvidenceKind.ASSAY else 0.3))
    replicate_count = (
        record.quantitative_support.replicate_count
        if record.quantitative_support is not None
        and record.quantitative_support.replicate_count is not None
        else 1
    )
    reproducibility = min(1.0, 0.3 + (replicate_count / 5.0))
    orthogonality = min(1.0, 0.4 + (0.2 * len(set(record.decision_tags))))
    biological_relevance = (
        1.0 if record.kind in {EvidenceKind.CELLULAR, EvidenceKind.PHENOTYPE} else 0.75
    )
    quantitative_report = evaluate_quantitative_support(record.quantitative_support)
    statistical_support = quantitative_report.support_score
    context_match = 0.95 if record.species and record.biological_system else 0.7
    context_relevance = 0.9 if record.biological_system else 0.6
    age_days = max((now - record.observed_at).total_seconds() / 86400.0, 0.0)
    recency = 1.0 if age_days <= 30 else max(0.4, 1.0 - (age_days / 365.0))
    weighted_sum = (
        assay_validity * 0.2
        + reproducibility * 0.15
        + orthogonality * 0.1
        + biological_relevance * 0.15
        + statistical_support * 0.1
        + context_match * 0.1
        + context_relevance * 0.1
        + source_credibility * 0.2
        + recency * 0.1
    )
    derived_confidence = round(min(1.0, weighted_sum / 1.2), 4)
    return EvidenceQualityDecomposition(
        assay_validity=round(assay_validity, 4),
        reproducibility=round(reproducibility, 4),
        orthogonality=round(orthogonality, 4),
        biological_relevance=round(biological_relevance, 4),
        statistical_support=round(statistical_support, 4),
        context_match=round(context_match, 4),
        context_relevance=round(context_relevance, 4),
        source_credibility=round(source_credibility, 4),
        recency=round(recency, 4),
        derived_confidence=derived_confidence,
    )


def assess_context_compatibility(
    record: EvidenceRecord,
    *,
    expected_species: str | None = None,
    expected_system: str | None = None,
    expected_sample_type: str | None = None,
    profile: ContextScoringProfile | None = None,
) -> ContextCompatibilityReport:
    """Assess how well evidence context matches expected program biology."""
    profile = profile or ContextScoringProfile(profile_id="default-context-profile")
    notes: list[str] = []
    score = 1.0
    if expected_species is not None and (
        (record.species or "").lower() != expected_species.lower()
    ):
        score -= profile.species_mismatch_penalty
        notes.append("species context does not match expected program species")
    if expected_system is not None and (
        (record.biological_system or "").lower() != expected_system.lower()
    ):
        score -= profile.system_mismatch_penalty
        notes.append("biological system context does not match expected system")
    if expected_sample_type is not None and (
        (record.sample_type or "").lower() != expected_sample_type.lower()
    ):
        score -= profile.sample_type_mismatch_penalty
        notes.append("sample type context does not match expected sample type")
    if not notes:
        notes.append("evidence context matches expected biology")
    return ContextCompatibilityReport(
        evidence_id=record.evidence_id,
        score=max(0.0, round(score, 4)),
        notes=notes,
    )


def triangulate_evidence(
    bundle: EvidenceBundle,
    *,
    decision_tag: str,
    required_modalities: list[str] | None = None,
) -> EvidenceTriangulationReport:
    """Score multi-modality convergence for a decision tag."""
    modality_counts: dict[str, int] = {}
    matching_records: list[EvidenceRecord] = []
    for record in bundle.records:
        if decision_tag not in record.decision_tags:
            continue
        matching_records.append(record)
        modality = record.kind.value
        modality_counts[modality] = modality_counts.get(modality, 0) + 1
    diversity = len(modality_counts)
    decisive_count = sum(
        1 for record in matching_records if record.strength is EvidenceStrength.DECISIVE
    )
    total_count = len(matching_records)
    decisive_share = round((decisive_count / total_count), 4) if total_count else 0.0
    required_modalities = required_modalities or []
    missing_required_modalities = [
        modality for modality in required_modalities if modality not in modality_counts
    ]
    modality_score = min(1.0, diversity / 4.0)
    decisive_score = decisive_share
    completeness_score = (
        1.0
        if not required_modalities
        else max(
            0.0,
            1.0 - (len(missing_required_modalities) / len(required_modalities)),
        )
    )
    convergence = round(
        (modality_score * 0.5) + (decisive_score * 0.3) + (completeness_score * 0.2), 4
    )
    return EvidenceTriangulationReport(
        target_id=bundle.target_id,
        decision_tag=decision_tag,
        modality_counts=modality_counts,
        modality_diversity=diversity,
        decisive_share=decisive_share,
        missing_required_modalities=missing_required_modalities,
        convergence_score=convergence,
    )


def assess_artifact_risk(record: EvidenceRecord) -> ArtifactRiskReport:
    """Score interpretation risk from proteomics artifact flags."""
    flags = record.artifact_flags
    if flags is None:
        return ArtifactRiskReport(
            evidence_id=record.evidence_id,
            risk_score=0.0,
            notes=["no artifact flags reported"],
        )
    risk = 0.0
    notes: list[str] = []
    if flags.missing_not_at_random:
        risk += 0.25
        notes.append("MNAR missingness may bias quantitative interpretation")
    if flags.ion_interference:
        risk += 0.25
        notes.append("ion interference may distort abundance estimates")
    if flags.peptide_to_protein_ambiguity:
        risk += 0.2
        notes.append(
            "peptide-to-protein ambiguity may weaken protein-level conclusions"
        )
    if flags.ptm_site_localization_uncertain:
        risk += 0.2
        notes.append("PTM localization uncertainty may weaken site-specific claims")
    if not notes:
        notes.append("artifact flags indicate low interpretation risk")
    return ArtifactRiskReport(
        evidence_id=record.evidence_id,
        risk_score=min(1.0, round(risk, 4)),
        notes=notes,
    )


def evaluate_quantitative_support(
    support: QuantitativeSupport | None,
) -> QuantitativeSupportReport:
    """Score quantitative support quality for downstream trust decisions."""
    if support is None:
        return QuantitativeSupportReport(
            support_score=0.0,
            notes=["no quantitative support provided"],
        )
    score = 0.25
    notes: list[str] = []
    if support.replicate_count is not None and support.replicate_count >= 3:
        score += 0.2
        notes.append("replicate count supports reproducibility")
    if support.coefficient_of_variation is not None:
        if support.coefficient_of_variation <= 0.3:
            score += 0.15
            notes.append("coefficient of variation is within an acceptable range")
        else:
            notes.append("coefficient of variation is high")
    if support.p_value is not None and support.p_value <= 0.05:
        score += 0.1
        notes.append("p-value supports statistical separation")
    if support.q_value is not None and support.q_value <= 0.1:
        score += 0.1
        notes.append("q-value remains acceptable after correction")
    if support.protein_coverage is not None:
        if support.protein_coverage >= 0.3:
            score += 0.1
            notes.append("protein coverage supports interpretation")
        else:
            notes.append("protein coverage is limited")
    if support.peptide_count is not None:
        if support.peptide_count >= 3:
            score += 0.05
            notes.append("peptide count is sufficient for stable quantification")
        else:
            notes.append("peptide count is low")
    if support.site_localization_probability is not None:
        if support.site_localization_probability >= 0.75:
            score += 0.05
            notes.append("site localization probability is strong")
        else:
            notes.append("site localization probability is weak")
    if (
        support.confidence_interval_low is not None
        and support.confidence_interval_high is not None
        and support.confidence_interval_low <= support.confidence_interval_high
    ):
        score += 0.05
        notes.append("confidence interval bounds are available")
    if (
        support.confidence_interval_level is not None
        and support.confidence_interval_level >= 0.9
    ):
        score += 0.03
        notes.append("confidence interval level is scientifically standard")
    if support.scale_type:
        score += 0.03
        notes.append("scale semantics are explicitly reported")
    if support.censored_by_detection_limit:
        score -= 0.1
        notes.append("quantitative estimate is censored by detection limit")
        if support.detection_limit_value is not None:
            notes.append("detection limit value is reported for censoring context")
        if support.censoring_direction:
            notes.append("censoring direction is explicitly reported")
    if support.absolute_scale:
        score += 0.05
        notes.append("measurement is on absolute scale")
    if not notes:
        notes.append("quantitative support contains minimal scoring features")
    return QuantitativeSupportReport(
        support_score=max(0.0, min(round(score, 4), 1.0)),
        notes=notes,
    )


def assess_context_completeness(
    record: EvidenceRecord,
) -> EvidenceContextCompletenessReport:
    """Assess whether key biological and assay context fields are populated."""
    required_fields = {
        "assay_modality": record.assay_modality,
        "biological_system": record.biological_system,
        "species": record.species,
        "sample_type": record.sample_type,
        "endpoint": record.endpoint,
    }
    missing_fields = [
        field_name
        for field_name, field_value in required_fields.items()
        if field_value is None or not str(field_value).strip()
    ]
    filled = len(required_fields) - len(missing_fields)
    score = round(filled / len(required_fields), 4)
    return EvidenceContextCompletenessReport(
        evidence_id=record.evidence_id,
        completeness_score=score,
        missing_fields=missing_fields,
    )


def assess_scientific_context_completeness(
    record: EvidenceRecord,
) -> ScientificContextCompletenessReport:
    """Assess completeness of extended scientific context for assay-grounded evidence."""
    context_fields = {
        "assay_modality": record.assay_modality,
        "biological_system": record.biological_system,
        "species": record.species,
        "sample_type": record.sample_type,
        "endpoint": record.endpoint,
        "dose": record.dose,
        "timepoint": record.timepoint,
        "perturbation": record.perturbation,
        "control_design": record.control_design,
        "replicate_design": record.replicate_design,
        "normalization_method": record.normalization_method,
        "sample_preparation": record.sample_preparation,
        "tissue_context": record.tissue_context,
        "cell_line_context": record.cell_line_context,
    }
    missing_fields = [
        field_name
        for field_name, field_value in context_fields.items()
        if field_value is None or not str(field_value).strip()
    ]
    filled = len(context_fields) - len(missing_fields)
    score = round(filled / len(context_fields), 4)
    return ScientificContextCompletenessReport(
        evidence_id=record.evidence_id,
        completeness_score=score,
        missing_fields=missing_fields,
    )


def audit_knowledge_quality(
    bundle: EvidenceBundle,
    *,
    decision_tag: str,
    required_modalities: list[str] | None = None,
) -> KnowledgeQualityAudit:
    """Build an integrated quality audit from trust, context, quantitative, and triangulation signals."""
    trust = compute_bundle_trust(bundle)
    triangulation = triangulate_evidence(
        bundle,
        decision_tag=decision_tag,
        required_modalities=required_modalities or [],
    )
    low_context_records: list[str] = []
    weak_quantitative_records: list[str] = []
    for record in bundle.records:
        context = assess_scientific_context_completeness(record)
        if context.completeness_score < 0.6:
            low_context_records.append(record.evidence_id)
        quantitative = evaluate_quantitative_support(record.quantitative_support)
        if record.quantitative_support is not None and quantitative.support_score < 0.5:
            weak_quantitative_records.append(record.evidence_id)

    recommendations: list[str] = []
    if triangulation.missing_required_modalities:
        recommendations.append(
            "collect missing modalities: "
            + ", ".join(triangulation.missing_required_modalities)
        )
    if low_context_records:
        recommendations.append("complete assay context fields for low-context records")
    if weak_quantitative_records:
        recommendations.append(
            "improve quantitative design for weak quantitative records"
        )
    if trust.conflicts:
        recommendations.append(
            "resolve outstanding evidence conflicts before decision signoff"
        )
    if not recommendations:
        recommendations.append("knowledge quality is strong for current decision scope")

    return KnowledgeQualityAudit(
        bundle_id=bundle.bundle_id,
        target_id=bundle.target_id,
        decision_tag=decision_tag,
        trust_score=trust.trust_score,
        triangulation_score=triangulation.convergence_score,
        low_context_records=low_context_records,
        weak_quantitative_records=weak_quantitative_records,
        conflict_count=len(trust.conflicts),
        recommendations=recommendations,
    )


def summarize_quantitative_coverage(
    bundle: EvidenceBundle,
) -> QuantitativeCoverageReport:
    """Summarize quantitative support coverage in an evidence bundle."""
    total = len(bundle.records)
    quantitative = sum(
        1 for record in bundle.records if record.quantitative_support is not None
    )
    coverage_ratio = round((quantitative / total), 4) if total else 0.0
    return QuantitativeCoverageReport(
        bundle_id=bundle.bundle_id,
        total_records=total,
        quantitative_records=quantitative,
        coverage_ratio=coverage_ratio,
    )


def rank_evidence_for_decision(
    bundle: EvidenceBundle,
    *,
    decision_tag: str,
    expected_species: str | None = None,
    expected_system: str | None = None,
    expected_sample_type: str | None = None,
) -> list[EvidenceRelevanceScore]:
    """Rank evidence by decision-tag alignment, context match, and scientific quality."""
    ranked: list[EvidenceRelevanceScore] = []
    for record in bundle.records:
        if decision_tag not in record.decision_tags:
            continue
        context = assess_context_compatibility(
            record,
            expected_species=expected_species,
            expected_system=expected_system,
            expected_sample_type=expected_sample_type,
        )
        quality = decompose_evidence_quality(record)
        quantitative = evaluate_quantitative_support(record.quantitative_support)
        score = round(
            (
                record.confidence * 0.35
                + context.score * 0.25
                + quality.derived_confidence * 0.25
                + quantitative.support_score * 0.15
            ),
            4,
        )
        drivers: list[str] = []
        if context.score >= 0.9:
            drivers.append("strong context match")
        if quality.statistical_support >= 0.7:
            drivers.append("strong statistical support")
        if record.strength is EvidenceStrength.DECISIVE:
            drivers.append("decisive evidence strength")
        if not drivers:
            drivers.append("baseline confidence and quality support ranking")
        ranked.append(
            EvidenceRelevanceScore(
                evidence_id=record.evidence_id,
                relevance_score=score,
                drivers=drivers,
            )
        )
    return sorted(ranked, key=lambda item: item.relevance_score, reverse=True)


def evaluate_modality_coverage(
    bundle: EvidenceBundle,
    *,
    decision_tag: str,
    required_modalities: list[str],
) -> ModalityCoverageReport:
    """Evaluate modality coverage for a decision dimension."""
    observed: dict[str, int] = {}
    for record in bundle.records:
        if decision_tag not in record.decision_tags:
            continue
        modality = record.kind.value
        observed[modality] = observed.get(modality, 0) + 1
    missing = [modality for modality in required_modalities if modality not in observed]
    coverage_score = (
        round((len(required_modalities) - len(missing)) / len(required_modalities), 4)
        if required_modalities
        else 1.0
    )
    return ModalityCoverageReport(
        decision_tag=decision_tag,
        observed_modalities=observed,
        missing_modalities=missing,
        coverage_score=max(0.0, min(coverage_score, 1.0)),
    )


def summarize_evidence_provenance(
    bundle: EvidenceBundle,
    *,
    evidence_id: str,
) -> EvidenceProvenanceReport:
    """Summarize transitive evidence ancestry from derived_from links."""
    by_id = {record.evidence_id: record for record in bundle.records}
    if evidence_id not in by_id:
        return EvidenceProvenanceReport(
            evidence_id=evidence_id,
            ancestor_ids=[],
            lineage_depth=0,
            has_missing_ancestors=True,
        )
    ancestors: set[str] = set()
    missing = False

    def walk(current_id: str, depth: int) -> int:
        nonlocal missing
        record = by_id.get(current_id)
        if record is None:
            missing = True
            return depth
        max_depth = depth
        for upstream_id in record.derived_from:
            if upstream_id not in by_id:
                missing = True
            if upstream_id in ancestors:
                continue
            ancestors.add(upstream_id)
            max_depth = max(max_depth, walk(upstream_id, depth + 1))
        return max_depth

    depth = walk(evidence_id, 0)
    return EvidenceProvenanceReport(
        evidence_id=evidence_id,
        ancestor_ids=sorted(ancestors),
        lineage_depth=depth,
        has_missing_ancestors=missing,
    )


def plan_evidence_collection(
    bundle: EvidenceBundle,
    *,
    decision_tag: str,
    required_modalities: list[str],
) -> list[EvidenceCollectionAction]:
    """Plan concrete evidence-collection actions for a decision tag."""
    coverage = evaluate_modality_coverage(
        bundle,
        decision_tag=decision_tag,
        required_modalities=required_modalities,
    )
    actions: list[EvidenceCollectionAction] = [
        EvidenceCollectionAction(
            priority="high",
            action=f"collect {missing_modality} evidence for '{decision_tag}'",
            rationale="required modality is missing for decision triangulation",
        )
        for missing_modality in coverage.missing_modalities
    ]
    for record in bundle.records:
        if decision_tag not in record.decision_tags:
            continue
        context = assess_scientific_context_completeness(record)
        if context.completeness_score < 0.6:
            actions.append(
                EvidenceCollectionAction(
                    priority="medium",
                    action=f"complete assay context fields for {record.evidence_id}",
                    rationale="context completeness is too low for robust interpretation",
                )
            )
        quantitative = evaluate_quantitative_support(record.quantitative_support)
        if record.quantitative_support is not None and quantitative.support_score < 0.5:
            actions.append(
                EvidenceCollectionAction(
                    priority="medium",
                    action=f"repeat {record.evidence_id} with improved quantitative design",
                    rationale="quantitative support quality is below acceptable threshold",
                )
            )
    if not actions:
        actions.append(
            EvidenceCollectionAction(
                priority="low",
                action=f"maintain current evidence refresh cadence for '{decision_tag}'",
                rationale="coverage and evidence quality are sufficient for current decision scope",
            )
        )
    return actions


def validate_quantitative_support_payload(
    support: QuantitativeSupport | None,
) -> list[QuantitativeValidationIssue]:
    """Validate quantitative support payload coherence."""
    if support is None:
        return []
    issues: list[QuantitativeValidationIssue] = []
    if (
        support.confidence_interval_low is not None
        and support.confidence_interval_high is not None
        and support.confidence_interval_low > support.confidence_interval_high
    ):
        issues.append(
            QuantitativeValidationIssue(
                code="interval-bounds-inverted",
                message="confidence_interval_low should be <= confidence_interval_high",
            )
        )
    if support.censored_by_detection_limit and support.detection_limit_value is None:
        issues.append(
            QuantitativeValidationIssue(
                code="censoring-limit-missing",
                message="censored observations should include detection_limit_value",
            )
        )
    if (
        support.p_value is not None
        and support.q_value is not None
        and support.q_value < support.p_value
    ):
        issues.append(
            QuantitativeValidationIssue(
                code="q-value-less-than-p-value",
                message="q_value should generally be >= p_value for corrected statistics",
            )
        )
    if support.absolute_scale and not support.unit:
        issues.append(
            QuantitativeValidationIssue(
                code="absolute-scale-unit-missing",
                message="absolute_scale measurements should include an explicit unit",
            )
        )
    return issues


def validate_bundle_integrity(bundle: EvidenceBundle) -> list[BundleIntegrityIssue]:
    """Validate basic bundle integrity invariants used by reasoning workflows."""
    issues: list[BundleIntegrityIssue] = []
    ids = [record.evidence_id for record in bundle.records]
    if len(ids) != len(set(ids)):
        issues.append(
            BundleIntegrityIssue(
                code="duplicate-evidence-ids",
                message="bundle contains duplicate evidence_id values",
            )
        )
    known_ids = set(ids)
    issues.extend(
        BundleIntegrityIssue(
            code="decision-tags-missing",
            message=f"{record.evidence_id} should include at least one decision tag",
        )
        for record in bundle.records
        if not record.decision_tags
    )
    issues.extend(
        BundleIntegrityIssue(
            code="derived-from-missing",
            message=f"{record.evidence_id} references missing upstream evidence '{upstream_id}'",
        )
        for record in bundle.records
        for upstream_id in record.derived_from
        if upstream_id not in known_ids
    )
    return issues


def normalize_bundle_decision_tags(
    bundle: EvidenceBundle,
) -> tuple[EvidenceBundle, DecisionTagNormalizationReport]:
    """Normalize decision tags to lowercase kebab style and deduplicate per record."""
    changed = 0
    normalized_records: list[EvidenceRecord] = []
    normalized_tag_set: set[str] = set()
    for record in bundle.records:
        normalized_tags = sorted(
            {
                tag.strip().lower().replace(" ", "-")
                for tag in record.decision_tags
                if tag and tag.strip()
            }
        )
        normalized_tag_set.update(normalized_tags)
        if normalized_tags != record.decision_tags:
            changed += 1
            normalized_records.append(
                record.model_copy(update={"decision_tags": normalized_tags})
            )
        else:
            normalized_records.append(record)
    normalized_bundle = bundle.model_copy(update={"records": normalized_records})
    report = DecisionTagNormalizationReport(
        changed_records=changed,
        normalized_tag_set=sorted(normalized_tag_set),
    )
    return normalized_bundle, report


def evidence_gaps(bundle: EvidenceBundle, required_kinds: list[str]) -> list[str]:
    """Return required evidence kinds that are still missing."""
    present = {record.kind.value for record in bundle.records}
    return [kind for kind in required_kinds if kind not in present]


def coverage_report(
    bundle: EvidenceBundle,
    required_kinds: list[str],
) -> EvidenceCoverage:
    """Summarize required coverage for a decision."""
    summary = summarize_bundle(bundle)
    record_count = len(bundle.records)
    mean_confidence = (
        sum(record.confidence for record in bundle.records) / record_count
        if record_count
        else 0.0
    )
    return EvidenceCoverage(
        bundle_id=bundle.bundle_id,
        target_id=bundle.target_id,
        by_kind=cast(dict[str, int], summary["by_kind"]),
        missing_kinds=evidence_gaps(bundle, required_kinds),
        decisive_records=cast(int, summary["decisive_records"]),
        mean_confidence=round(mean_confidence, 4),
    )


def assess_decision_readiness(
    bundle: EvidenceBundle,
    required_kinds: list[str],
    *,
    minimum_mean_confidence: float = 0.7,
    minimum_decisive_records: int = 1,
) -> DecisionReadiness:
    """Assess whether a bundle is strong enough for a gated decision."""
    coverage = coverage_report(bundle, required_kinds)
    blockers: list[str] = []
    recommendations: list[str] = []

    if coverage.missing_kinds:
        blockers.append(
            "missing required evidence kinds: " + ", ".join(coverage.missing_kinds)
        )
        recommendations.append(
            "collect " + ", ".join(coverage.missing_kinds) + " evidence before signoff"
        )
    if coverage.decisive_records < minimum_decisive_records:
        blockers.append("not enough decisive evidence for an irreversible decision")
        recommendations.append("add decisive assay or structural evidence")
    if coverage.mean_confidence < minimum_mean_confidence:
        blockers.append(
            f"mean confidence {coverage.mean_confidence:.2f} is below "
            f"{minimum_mean_confidence:.2f}"
        )
        recommendations.append(
            "replace exploratory evidence with stronger corroboration"
        )

    return DecisionReadiness(
        target_id=bundle.target_id,
        ready=not blockers,
        blockers=blockers,
        recommendations=recommendations,
        coverage=coverage,
    )


def default_trust_policy() -> TrustPolicy:
    """Return the default trust policy used by the package."""
    return TrustPolicy(policy_id="default-trust-policy")


def weight_source_type(
    source_type: EvidenceSourceType,
    *,
    policy: TrustPolicy | None = None,
) -> float:
    """Return a trust weight for the source category."""
    policy = policy or default_trust_policy()
    return policy.source_type_weights[source_type]


def score_evidence_record(
    record: EvidenceRecord,
    *,
    now: datetime | None = None,
    policy: TrustPolicy | None = None,
) -> float:
    """Compute a trust score for a single evidence record."""
    now = now or datetime.now(UTC)
    policy = policy or default_trust_policy()
    strength_weight = policy.strength_weights[record.strength]
    stale_penalty = (
        policy.stale_penalty
        if record.expires_at is not None and record.expires_at < now
        else 1.0
    )
    return round(
        record.confidence
        * weight_source_type(record.source_type, policy=policy)
        * strength_weight
        * stale_penalty,
        4,
    )


def stale_records(
    bundle: EvidenceBundle,
    *,
    now: datetime | None = None,
    policy: TrustPolicy | None = None,
) -> list[EvidenceRecord]:
    """Return records whose explicit expiry has passed."""
    now = now or datetime.now(UTC)
    policy = policy or default_trust_policy()
    stale: list[EvidenceRecord] = []
    for record in bundle.records:
        if record.expires_at is not None and record.expires_at < now:
            stale.append(record)
            continue
        max_age_days = policy.max_age_days_by_source.get(record.source_type)
        if max_age_days is None:
            continue
        age_days = max((now - record.observed_at).total_seconds() / 86400.0, 0.0)
        if age_days > max_age_days:
            stale.append(record)
    return stale


def aging_records(
    bundle: EvidenceBundle,
    *,
    now: datetime | None = None,
    horizon_days: int = 30,
    policy: TrustPolicy | None = None,
) -> list[EvidenceRecord]:
    """Return records that will expire soon enough to justify refresh planning."""
    now = now or datetime.now(UTC)
    policy = policy or default_trust_policy()
    horizon = now + timedelta(days=horizon_days)
    aging: list[EvidenceRecord] = []
    for record in bundle.records:
        if record.expires_at is not None and now <= record.expires_at <= horizon:
            aging.append(record)
            continue
        if record.expires_at is not None:
            continue
        max_age_days = policy.max_age_days_by_source.get(record.source_type)
        if max_age_days is None:
            continue
        age_days = max((now - record.observed_at).total_seconds() / 86400.0, 0.0)
        days_to_stale = max_age_days - age_days
        if 0 <= days_to_stale <= horizon_days:
            aging.append(record)
    return aging


def plan_evidence_refresh(
    bundle: EvidenceBundle,
    *,
    now: datetime | None = None,
    horizon_days: int = 30,
    policy: TrustPolicy | None = None,
) -> BundleFreshnessReport:
    """Build a prioritized refresh plan for stale and aging evidence."""
    now = now or datetime.now(UTC)
    policy = policy or default_trust_policy()
    stale = stale_records(bundle, now=now, policy=policy)
    aging = aging_records(bundle, now=now, horizon_days=horizon_days, policy=policy)
    refresh_needs: list[EvidenceRefreshNeed] = [
        EvidenceRefreshNeed(
            evidence_id=record.evidence_id,
            priority=EvidenceRefreshPriority.HIGH,
            reason="the evidence record is already past its validity window",
            suggested_action=_refresh_action_for_record(record),
        )
        for record in stale
    ]
    stale_ids = {record.evidence_id for record in stale}
    for record in aging:
        if record.evidence_id in stale_ids:
            continue
        priority = (
            EvidenceRefreshPriority.HIGH
            if record.strength is EvidenceStrength.DECISIVE
            else EvidenceRefreshPriority.MEDIUM
        )
        refresh_needs.append(
            EvidenceRefreshNeed(
                evidence_id=record.evidence_id,
                priority=priority,
                reason="the evidence record will expire soon and should be refreshed proactively",
                suggested_action=_refresh_action_for_record(record),
            )
        )
    return BundleFreshnessReport(
        bundle_id=bundle.bundle_id,
        target_id=bundle.target_id,
        stale_records=[record.evidence_id for record in stale],
        aging_records=[
            record.evidence_id
            for record in aging
            if record.evidence_id not in stale_ids
        ],
        refresh_needs=refresh_needs,
    )


def _refresh_action_for_record(record: EvidenceRecord) -> str:
    """Return a concrete refresh recommendation for a record."""
    if record.source_type is EvidenceSourceType.LAB_ASSAY:
        return "repeat or reconfirm the assay readout in the lab system"
    if record.source_type is EvidenceSourceType.LITERATURE:
        return "search for newer literature and re-evaluate the claim"
    if record.source_type is EvidenceSourceType.STRUCTURE_MODEL:
        return "rerun or revalidate the structure model with the latest inputs"
    if record.source_type is EvidenceSourceType.EXTERNAL_DATABASE:
        return "re-ingest the linked external database record"
    return "refresh the curated note with a current reviewer assessment"


def deduplicate_records(bundle: EvidenceBundle) -> list[list[str]]:
    """Group records that look like duplicates."""
    grouped: dict[tuple[str, str, str], list[str]] = {}
    for record in bundle.records:
        key = (
            record.kind.value,
            record.claim.strip().lower(),
            record.source.strip().lower(),
        )
        grouped.setdefault(key, []).append(record.evidence_id)
    return [ids for ids in grouped.values() if len(ids) > 1]


def default_conflict_policy() -> ConflictPolicy:
    """Return the default conflict policy used by the package."""
    return ConflictPolicy(policy_id="default-conflict-policy")


def flag_conflicting_evidence(
    bundle: EvidenceBundle,
    *,
    policy: ConflictPolicy | None = None,
) -> list[EvidenceConflict]:
    """Identify conflicting evidence with opposite decision tags on the same target."""
    policy = policy or default_conflict_policy()
    conflicts: list[EvidenceConflict] = []
    for index, left in enumerate(bundle.records):
        left_tags = set(left.decision_tags)
        for right in bundle.records[index + 1 :]:
            same_kind = left.kind is right.kind
            if policy.require_shared_decision_tag and not left_tags.intersection(
                right.decision_tags
            ):
                continue
            if (
                policy.detect_quantitative_direction_conflicts
                and same_kind
                and left.endpoint
                and right.endpoint
                and left.endpoint.strip().lower() == right.endpoint.strip().lower()
                and _has_opposite_effect_direction(left, right)
            ):
                conflicts.append(
                    EvidenceConflict(
                        conflict_type="quantitative_direction_conflict",
                        severity="high",
                        left_evidence_id=left.evidence_id,
                        right_evidence_id=right.evidence_id,
                        reason="records show opposite quantitative effect direction on a shared endpoint",
                    )
                )
                continue
            if (
                same_kind
                and left.endpoint
                and right.endpoint
                and left.endpoint.strip().lower() == right.endpoint.strip().lower()
                and _has_magnitude_conflict(
                    left, right, threshold=policy.magnitude_divergence_threshold
                )
            ):
                conflicts.append(
                    EvidenceConflict(
                        conflict_type="quantitative_magnitude_conflict",
                        severity="medium",
                        left_evidence_id=left.evidence_id,
                        right_evidence_id=right.evidence_id,
                        reason="records show a large effect-size magnitude disagreement on a shared endpoint",
                    )
                )
                continue
            if (
                policy.detect_assay_readout_conflicts
                and left.kind is EvidenceKind.ASSAY
                and right.kind is EvidenceKind.ASSAY
                and left.source_uri is not None
                and left.source_uri == right.source_uri
            ):
                conflicts.append(
                    EvidenceConflict(
                        conflict_type="assay_readout_disagreement",
                        severity="high",
                        left_evidence_id=left.evidence_id,
                        right_evidence_id=right.evidence_id,
                        reason="same assay source but inconsistent assay interpretation",
                    )
                )
                continue
            if _looks_polarity_conflict(left.claim, right.claim):
                conflicts.append(
                    EvidenceConflict(
                        conflict_type="opposite_claim_polarity",
                        severity="high",
                        left_evidence_id=left.evidence_id,
                        right_evidence_id=right.evidence_id,
                        reason="evidence claims suggest opposite progression polarity",
                    )
                )
                continue
            if (
                left.species is not None
                and right.species is not None
                and left.species.strip().lower() != right.species.strip().lower()
            ):
                conflicts.append(
                    EvidenceConflict(
                        conflict_type="species_context_mismatch",
                        severity="medium",
                        left_evidence_id=left.evidence_id,
                        right_evidence_id=right.evidence_id,
                        reason="records inform the same decision tag under different species contexts",
                    )
                )
                continue
            if (
                left.biological_system is not None
                and right.biological_system is not None
                and left.biological_system.strip().lower()
                != right.biological_system.strip().lower()
            ):
                conflicts.append(
                    EvidenceConflict(
                        conflict_type="biological_system_mismatch",
                        severity="medium",
                        left_evidence_id=left.evidence_id,
                        right_evidence_id=right.evidence_id,
                        reason="records inform the same decision tag under different biological systems",
                    )
                )
                continue
            if {left.strength, right.strength} == {
                EvidenceStrength.DECISIVE,
                EvidenceStrength.EXPLORATORY,
            }:
                conflicts.append(
                    EvidenceConflict(
                        conflict_type="claim_strength_mismatch",
                        severity="medium",
                        left_evidence_id=left.evidence_id,
                        right_evidence_id=right.evidence_id,
                        reason="same decision tag but materially different claim strength",
                    )
                )
    return conflicts


def _looks_polarity_conflict(left_claim: str, right_claim: str) -> bool:
    left_text = left_claim.strip().lower()
    right_text = right_claim.strip().lower()
    positive_tokens = {"meets", "supports", "retains", "passes", "improves"}
    negative_tokens = {"misses", "fails", "contraindicates", "worsens", "reduces"}
    left_positive = any(token in left_text for token in positive_tokens)
    right_positive = any(token in right_text for token in positive_tokens)
    left_negative = any(token in left_text for token in negative_tokens)
    right_negative = any(token in right_text for token in negative_tokens)
    return (left_positive and right_negative) or (left_negative and right_positive)


def _has_opposite_effect_direction(left: EvidenceRecord, right: EvidenceRecord) -> bool:
    left_effect = (
        left.quantitative_support.effect_size if left.quantitative_support else None
    )
    right_effect = (
        right.quantitative_support.effect_size if right.quantitative_support else None
    )
    if left_effect is None or right_effect is None:
        return False
    return (left_effect > 0 and right_effect < 0) or (
        left_effect < 0 and right_effect > 0
    )


def _has_magnitude_conflict(
    left: EvidenceRecord, right: EvidenceRecord, *, threshold: float
) -> bool:
    left_effect = (
        left.quantitative_support.effect_size if left.quantitative_support else None
    )
    right_effect = (
        right.quantitative_support.effect_size if right.quantitative_support else None
    )
    if left_effect is None or right_effect is None:
        return False
    return abs(left_effect - right_effect) >= threshold


def compute_bundle_trust(
    bundle: EvidenceBundle,
    *,
    now: datetime | None = None,
    policy: TrustPolicy | None = None,
    conflict_policy: ConflictPolicy | None = None,
) -> BundleTrustReport:
    """Compute overall trust after staleness, conflicts, and deduplication."""
    now = now or datetime.now(UTC)
    policy = policy or default_trust_policy()
    record_scores = [
        score_evidence_record(record, now=now, policy=policy)
        for record in bundle.records
    ]
    base_score = sum(record_scores) / len(record_scores) if record_scores else 0.0
    stale = stale_records(bundle, now=now)
    conflicts = flag_conflicting_evidence(bundle, policy=conflict_policy)
    duplicate_groups = deduplicate_records(bundle)
    penalty = (
        policy.stale_record_penalty * len(stale)
        + policy.conflict_penalty * len(conflicts)
        + policy.duplicate_penalty * len(duplicate_groups)
    )
    return BundleTrustReport(
        bundle_id=bundle.bundle_id,
        target_id=bundle.target_id,
        trust_score=max(0.0, round(base_score - penalty, 4)),
        stale_records=[record.evidence_id for record in stale],
        conflicts=conflicts,
        duplicate_groups=duplicate_groups,
    )
