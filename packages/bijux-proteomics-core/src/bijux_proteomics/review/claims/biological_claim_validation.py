# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Validation over final biological claims before narrative handoff."""

from __future__ import annotations

import csv
from enum import StrEnum
from io import StringIO

from pydantic import ConfigDict, Field, model_validator

from bijux_proteomics.domain.confidence import coerce_confidence_tier
from bijux_proteomics.domain.source_row_lineage import SourceRowLineage
from bijux_proteomics.io.stable_outputs import sort_strings
from bijux_proteomics.review.evidence_graph.evidence_graph_confidence import (
    EvidenceGraphConfidenceTier,
)
from bijux_proteomics.review.evidence_graph.evidence_graph_downgrades import (
    FinalClaimEvidenceTier,
)
from bijux_proteomics_foundation import JsonModel


class BiologicalClaimKind(StrEnum):
    """Stable biological claim classes validated before final narrative use."""

    PROTEIN_ABUNDANCE_CHANGE = "protein_abundance_change"
    PATHWAY_ACTIVITY_CHANGE = "pathway_activity_change"
    REGULATOR_ACTIVITY = "regulator_activity"


class BiologicalClaimDirection(StrEnum):
    """Stable direction labels preserved on biological claim candidates."""

    UP = "up"
    DOWN = "down"
    MIXED = "mixed"
    UNRESOLVED = "unresolved"


class BiologicalClaimStatus(StrEnum):
    """Stable validation outcome for one biological claim."""

    SUPPORTED = "supported"
    REJECTED = "rejected"


class BiologicalClaimValidationReason(StrEnum):
    """Durable reason codes explaining accepted or rejected biological claims."""

    ROBUST_QUANTIFICATION = "robust_quantification"
    PATHWAY_DIRECTIONAL_ACTIVITY = "pathway_directional_activity"
    SUBSTRATE_DIRECTIONAL_SUPPORT = "substrate_directional_support"
    REGULATOR_DIRECTIONAL_SUPPORT = "regulator_directional_support"
    NOT_SIGNIFICANT = "not_significant"
    LOW_ROBUSTNESS = "low_robustness"
    IMPUTATION_DEPENDENT = "imputation_dependent"
    WEAK_EVIDENCE_TIER = "weak_evidence_tier"
    LOW_CONFIDENCE_TIER = "low_confidence_tier"
    MISSING_DIRECTIONAL_DELTA = "missing_directional_delta"
    LOW_PATHWAY_CONFIDENCE = "low_pathway_confidence"
    LOW_REGULATOR_SCORE = "low_regulator_score"
    UNSUPPORTED_REGULATOR_DIRECTION = "unsupported_regulator_direction"
    KINASE_REQUIRES_SITE_SURFACE = "kinase_requires_site_surface"


class BiologicalClaimCandidate(JsonModel):
    """One structured biological claim prepared for evidence validation."""

    model_config = ConfigDict(extra="forbid")

    claim_id: str = Field(..., min_length=1)
    claim_kind: BiologicalClaimKind
    subject_id: str = Field(..., min_length=1)
    subject_label: str = Field(..., min_length=1)
    claim_text: str = Field(..., min_length=1)
    condition_a: str = Field(..., min_length=1)
    condition_b: str = Field(..., min_length=1)
    asserted_direction: BiologicalClaimDirection
    significant: bool = False
    adjusted_p_value: float | None = Field(default=None, ge=0.0, le=1.0)
    effect_size: float | None = None
    robustness_score: float | None = Field(default=None, ge=0.0, le=1.0)
    imputation_dependent: bool = False
    evidence_tier: FinalClaimEvidenceTier | None = None
    confidence_tier: EvidenceGraphConfidenceTier | None = None
    pathway_confidence_status: str | None = None
    pathway_delta: float | None = None
    regulator_evidence_type: str | None = None
    regulator_signal_surface: str | None = None
    regulator_score: float | None = Field(default=None, ge=0.0, le=1.0)
    source_ids: tuple[str, ...] = Field(default_factory=tuple)
    source_row_refs: tuple[str, ...] = Field(default_factory=tuple)
    derived_no_source_reason: str | None = None
    note: str = Field(..., min_length=1)

    @model_validator(mode="after")
    def _validate_source_row_lineage(self) -> BiologicalClaimCandidate:
        SourceRowLineage(
            source_row_refs=self.source_row_refs,
            derived_no_source_reason=self.derived_no_source_reason,
        )
        return self


class BiologicalClaimValidationPolicy(JsonModel):
    """Threshold policy used to validate final biological claims."""

    model_config = ConfigDict(extra="forbid")

    max_adjusted_p_value: float = Field(default=0.1, ge=0.0, le=1.0)
    min_robustness_score: float = Field(default=0.55, ge=0.0, le=1.0)
    min_pathway_activity_delta: float = Field(default=0.2, ge=0.0)
    min_regulator_score: float = Field(default=0.55, ge=0.0, le=1.0)


class BiologicalClaimValidationEntry(JsonModel):
    """One validated or rejected biological claim with explicit reasons."""

    model_config = ConfigDict(extra="forbid")

    claim_id: str = Field(..., min_length=1)
    claim_kind: BiologicalClaimKind
    status: BiologicalClaimStatus
    subject_id: str = Field(..., min_length=1)
    subject_label: str = Field(..., min_length=1)
    claim_text: str = Field(..., min_length=1)
    condition_a: str = Field(..., min_length=1)
    condition_b: str = Field(..., min_length=1)
    asserted_direction: BiologicalClaimDirection
    adjusted_p_value: float | None = Field(default=None, ge=0.0, le=1.0)
    effect_size: float | None = None
    robustness_score: float | None = Field(default=None, ge=0.0, le=1.0)
    imputation_dependent: bool = False
    evidence_tier: FinalClaimEvidenceTier | None = None
    confidence_tier: EvidenceGraphConfidenceTier | None = None
    pathway_confidence_status: str | None = None
    pathway_delta: float | None = None
    regulator_evidence_type: str | None = None
    regulator_signal_surface: str | None = None
    regulator_score: float | None = Field(default=None, ge=0.0, le=1.0)
    reason_codes: tuple[BiologicalClaimValidationReason, ...] = Field(
        default_factory=tuple
    )
    source_ids: tuple[str, ...] = Field(default_factory=tuple)
    source_row_refs: tuple[str, ...] = Field(default_factory=tuple)
    derived_no_source_reason: str | None = None
    validation_note: str = Field(..., min_length=1)

    @model_validator(mode="after")
    def _validate_source_row_lineage(self) -> BiologicalClaimValidationEntry:
        SourceRowLineage(
            source_row_refs=self.source_row_refs,
            derived_no_source_reason=self.derived_no_source_reason,
        )
        return self


class BiologicalClaimValidationSummary(JsonModel):
    """Stable summary over one biological claim validation pass."""

    model_config = ConfigDict(extra="forbid")

    candidate_count: int = Field(..., ge=0)
    supported_claim_count: int = Field(..., ge=0)
    rejected_claim_count: int = Field(..., ge=0)
    protein_claim_count: int = Field(..., ge=0)
    pathway_claim_count: int = Field(..., ge=0)
    regulator_claim_count: int = Field(..., ge=0)


class BiologicalClaimValidationReport(JsonModel):
    """Owned claim-validation report used to gate final biological narrative output."""

    model_config = ConfigDict(extra="forbid")

    supported_claims: tuple[BiologicalClaimValidationEntry, ...] = Field(
        default_factory=tuple
    )
    rejected_claims: tuple[BiologicalClaimValidationEntry, ...] = Field(
        default_factory=tuple
    )
    summary: BiologicalClaimValidationSummary
    note: str = Field(..., min_length=1)


def build_biological_claim_validation_report(
    candidates: tuple[BiologicalClaimCandidate, ...],
    *,
    policy: BiologicalClaimValidationPolicy | None = None,
) -> BiologicalClaimValidationReport:
    """Validate biological claims before they appear in a final narrative surface."""

    active_policy = policy or BiologicalClaimValidationPolicy()
    supported_claims: list[BiologicalClaimValidationEntry] = []
    rejected_claims: list[BiologicalClaimValidationEntry] = []

    for candidate in candidates:
        reasons = _validate_candidate(candidate, policy=active_policy)
        status = (
            BiologicalClaimStatus.SUPPORTED
            if _is_supported_reason_set(reasons)
            else BiologicalClaimStatus.REJECTED
        )
        entry = BiologicalClaimValidationEntry(
            claim_id=candidate.claim_id,
            claim_kind=candidate.claim_kind,
            status=status,
            subject_id=candidate.subject_id,
            subject_label=candidate.subject_label,
            claim_text=candidate.claim_text,
            condition_a=candidate.condition_a,
            condition_b=candidate.condition_b,
            asserted_direction=candidate.asserted_direction,
            adjusted_p_value=candidate.adjusted_p_value,
            effect_size=candidate.effect_size,
            robustness_score=candidate.robustness_score,
            imputation_dependent=candidate.imputation_dependent,
            evidence_tier=candidate.evidence_tier,
            confidence_tier=candidate.confidence_tier,
            pathway_confidence_status=candidate.pathway_confidence_status,
            pathway_delta=candidate.pathway_delta,
            regulator_evidence_type=candidate.regulator_evidence_type,
            regulator_signal_surface=candidate.regulator_signal_surface,
            regulator_score=candidate.regulator_score,
            reason_codes=tuple(sorted(reasons, key=lambda value: value.value)),
            source_ids=tuple(sort_strings(candidate.source_ids)),
            source_row_refs=candidate.source_row_refs,
            derived_no_source_reason=candidate.derived_no_source_reason,
            validation_note=_build_validation_note(candidate, status, reasons),
        )
        if status is BiologicalClaimStatus.SUPPORTED:
            supported_claims.append(entry)
        else:
            rejected_claims.append(entry)

    supported_claims.sort(key=lambda entry: (entry.claim_kind.value, entry.subject_id))
    rejected_claims.sort(key=lambda entry: (entry.claim_kind.value, entry.subject_id))
    return BiologicalClaimValidationReport(
        supported_claims=tuple(supported_claims),
        rejected_claims=tuple(rejected_claims),
        summary=BiologicalClaimValidationSummary(
            candidate_count=len(candidates),
            supported_claim_count=len(supported_claims),
            rejected_claim_count=len(rejected_claims),
            protein_claim_count=sum(
                1
                for candidate in candidates
                if candidate.claim_kind is BiologicalClaimKind.PROTEIN_ABUNDANCE_CHANGE
            ),
            pathway_claim_count=sum(
                1
                for candidate in candidates
                if candidate.claim_kind is BiologicalClaimKind.PATHWAY_ACTIVITY_CHANGE
            ),
            regulator_claim_count=sum(
                1
                for candidate in candidates
                if candidate.claim_kind is BiologicalClaimKind.REGULATOR_ACTIVITY
            ),
        ),
        note=(
            "biological claim validation rejects pathway, regulator, and protein "
            "statements that lack directional or quantitative support before they can "
            "appear in final biological narrative surfaces"
        ),
    )


def render_biological_claim_validation_summary_tsv(
    report: BiologicalClaimValidationReport,
) -> str:
    """Render biological claim validation summary as TSV."""

    handle = StringIO()
    writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
    writer.writerow(("field", "value"))
    writer.writerow(("candidate_count", report.summary.candidate_count))
    writer.writerow(("supported_claim_count", report.summary.supported_claim_count))
    writer.writerow(("rejected_claim_count", report.summary.rejected_claim_count))
    writer.writerow(("protein_claim_count", report.summary.protein_claim_count))
    writer.writerow(("pathway_claim_count", report.summary.pathway_claim_count))
    writer.writerow(("regulator_claim_count", report.summary.regulator_claim_count))
    writer.writerow(("note", report.note))
    return handle.getvalue()


def render_supported_biological_claim_tsv(
    report: BiologicalClaimValidationReport,
) -> str:
    """Render supported biological claims as TSV."""

    return _render_claim_rows(report.supported_claims)


def render_rejected_biological_claim_tsv(
    report: BiologicalClaimValidationReport,
) -> str:
    """Render rejected biological claims as TSV."""

    return _render_claim_rows(report.rejected_claims)


def _validate_candidate(
    candidate: BiologicalClaimCandidate,
    *,
    policy: BiologicalClaimValidationPolicy,
) -> set[BiologicalClaimValidationReason]:
    if candidate.claim_kind is BiologicalClaimKind.PROTEIN_ABUNDANCE_CHANGE:
        return _validate_protein_claim(candidate, policy=policy)
    if candidate.claim_kind is BiologicalClaimKind.PATHWAY_ACTIVITY_CHANGE:
        return _validate_pathway_claim(candidate, policy=policy)
    if candidate.claim_kind is BiologicalClaimKind.REGULATOR_ACTIVITY:
        return _validate_regulator_claim(candidate, policy=policy)
    raise ValueError(f"unsupported biological claim kind: {candidate.claim_kind.value}")


def _validate_protein_claim(
    candidate: BiologicalClaimCandidate,
    *,
    policy: BiologicalClaimValidationPolicy,
) -> set[BiologicalClaimValidationReason]:
    reasons: set[BiologicalClaimValidationReason] = set()
    if not candidate.significant:
        reasons.add(BiologicalClaimValidationReason.NOT_SIGNIFICANT)
    if (
        candidate.adjusted_p_value is not None
        and candidate.adjusted_p_value > policy.max_adjusted_p_value
    ):
        reasons.add(BiologicalClaimValidationReason.NOT_SIGNIFICANT)
    if (
        candidate.robustness_score is None
        or candidate.robustness_score < policy.min_robustness_score
    ):
        reasons.add(BiologicalClaimValidationReason.LOW_ROBUSTNESS)
    if candidate.imputation_dependent:
        reasons.add(BiologicalClaimValidationReason.IMPUTATION_DEPENDENT)
    if candidate.evidence_tier not in {
        FinalClaimEvidenceTier.HIGH_CONFIDENCE,
        FinalClaimEvidenceTier.MODERATE,
    }:
        reasons.add(BiologicalClaimValidationReason.WEAK_EVIDENCE_TIER)
    if candidate.confidence_tier not in {
        EvidenceGraphConfidenceTier.HIGH,
        EvidenceGraphConfidenceTier.MODERATE,
    }:
        reasons.add(BiologicalClaimValidationReason.LOW_CONFIDENCE_TIER)
    if not reasons:
        reasons.add(BiologicalClaimValidationReason.ROBUST_QUANTIFICATION)
    return reasons


def _validate_pathway_claim(
    candidate: BiologicalClaimCandidate,
    *,
    policy: BiologicalClaimValidationPolicy,
) -> set[BiologicalClaimValidationReason]:
    reasons: set[BiologicalClaimValidationReason] = set()
    if (
        candidate.pathway_delta is None
        or abs(candidate.pathway_delta) < policy.min_pathway_activity_delta
    ):
        reasons.add(BiologicalClaimValidationReason.MISSING_DIRECTIONAL_DELTA)
    if (
        coerce_confidence_tier(candidate.pathway_confidence_status)
        is not EvidenceGraphConfidenceTier.HIGH
    ):
        reasons.add(BiologicalClaimValidationReason.LOW_PATHWAY_CONFIDENCE)
    if not reasons:
        reasons.add(BiologicalClaimValidationReason.PATHWAY_DIRECTIONAL_ACTIVITY)
    return reasons


def _validate_regulator_claim(
    candidate: BiologicalClaimCandidate,
    *,
    policy: BiologicalClaimValidationPolicy,
) -> set[BiologicalClaimValidationReason]:
    reasons: set[BiologicalClaimValidationReason] = set()
    if (
        candidate.regulator_score is None
        or candidate.regulator_score < policy.min_regulator_score
    ):
        reasons.add(BiologicalClaimValidationReason.LOW_REGULATOR_SCORE)
    if candidate.asserted_direction not in {
        BiologicalClaimDirection.UP,
        BiologicalClaimDirection.DOWN,
    }:
        reasons.add(BiologicalClaimValidationReason.UNSUPPORTED_REGULATOR_DIRECTION)
    if candidate.regulator_evidence_type == "kinase_substrate":
        if candidate.regulator_signal_surface != "site_regulation":
            reasons.add(BiologicalClaimValidationReason.KINASE_REQUIRES_SITE_SURFACE)
        if not reasons:
            reasons.add(BiologicalClaimValidationReason.SUBSTRATE_DIRECTIONAL_SUPPORT)
        return reasons
    if candidate.regulator_signal_surface not in {
        "protein_abundance",
        "pathway_activity",
        "site_regulation",
    }:
        reasons.add(BiologicalClaimValidationReason.UNSUPPORTED_REGULATOR_DIRECTION)
    if not reasons:
        reasons.add(BiologicalClaimValidationReason.REGULATOR_DIRECTIONAL_SUPPORT)
    return reasons


def _is_supported_reason_set(
    reasons: set[BiologicalClaimValidationReason],
) -> bool:
    return reasons in (
        {BiologicalClaimValidationReason.ROBUST_QUANTIFICATION},
        {BiologicalClaimValidationReason.PATHWAY_DIRECTIONAL_ACTIVITY},
        {BiologicalClaimValidationReason.SUBSTRATE_DIRECTIONAL_SUPPORT},
        {BiologicalClaimValidationReason.REGULATOR_DIRECTIONAL_SUPPORT},
    )


def _build_validation_note(
    candidate: BiologicalClaimCandidate,
    status: BiologicalClaimStatus,
    reasons: set[BiologicalClaimValidationReason],
) -> str:
    if status is BiologicalClaimStatus.SUPPORTED:
        if candidate.claim_kind is BiologicalClaimKind.PROTEIN_ABUNDANCE_CHANGE:
            return "supported because the protein change clears significance, robustness, and evidence thresholds"
        if candidate.claim_kind is BiologicalClaimKind.PATHWAY_ACTIVITY_CHANGE:
            return "supported because the pathway claim preserves directional activity delta with high-confidence comparison support"
        return "supported because the regulator claim preserves directional downstream evidence on the required evidence surface"
    return "rejected from final narrative because the claim failed one or more required evidence checks"


def _render_claim_rows(
    entries: tuple[BiologicalClaimValidationEntry, ...],
) -> str:
    handle = StringIO()
    writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "claim_id",
            "claim_kind",
            "status",
            "subject_id",
            "subject_label",
            "claim_text",
            "condition_a",
            "condition_b",
            "asserted_direction",
            "adjusted_p_value",
            "effect_size",
            "robustness_score",
            "imputation_dependent",
            "evidence_tier",
            "confidence_tier",
            "pathway_confidence_status",
            "pathway_delta",
            "regulator_evidence_type",
            "regulator_signal_surface",
            "regulator_score",
            "reason_codes",
            "source_ids",
            "source_row_refs",
            "derived_no_source_reason",
            "validation_note",
        )
    )
    for entry in entries:
        writer.writerow(
            (
                entry.claim_id,
                entry.claim_kind.value,
                entry.status.value,
                entry.subject_id,
                entry.subject_label,
                entry.claim_text,
                entry.condition_a,
                entry.condition_b,
                entry.asserted_direction.value,
                "" if entry.adjusted_p_value is None else entry.adjusted_p_value,
                "" if entry.effect_size is None else entry.effect_size,
                "" if entry.robustness_score is None else entry.robustness_score,
                str(entry.imputation_dependent).lower(),
                "" if entry.evidence_tier is None else entry.evidence_tier.value,
                "" if entry.confidence_tier is None else entry.confidence_tier.value,
                ""
                if entry.pathway_confidence_status is None
                else entry.pathway_confidence_status,
                "" if entry.pathway_delta is None else entry.pathway_delta,
                ""
                if entry.regulator_evidence_type is None
                else entry.regulator_evidence_type,
                ""
                if entry.regulator_signal_surface is None
                else entry.regulator_signal_surface,
                "" if entry.regulator_score is None else entry.regulator_score,
                ";".join(reason.value for reason in entry.reason_codes),
                ";".join(entry.source_ids),
                ";".join(entry.source_row_refs),
                ""
                if entry.derived_no_source_reason is None
                else entry.derived_no_source_reason,
                entry.validation_note,
            )
        )
    return handle.getvalue()


__all__ = [
    "BiologicalClaimCandidate",
    "BiologicalClaimDirection",
    "BiologicalClaimKind",
    "BiologicalClaimStatus",
    "BiologicalClaimValidationEntry",
    "BiologicalClaimValidationPolicy",
    "BiologicalClaimValidationReason",
    "BiologicalClaimValidationReport",
    "BiologicalClaimValidationSummary",
    "build_biological_claim_validation_report",
    "render_biological_claim_validation_summary_tsv",
    "render_rejected_biological_claim_tsv",
    "render_supported_biological_claim_tsv",
]
