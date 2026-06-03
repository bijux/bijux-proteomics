# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Cross-family scientific story checks over digestion, identification, quant, PTM, and review."""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import ConfigDict, Field, field_validator

from bijux_proteomics.domain.reason_codes import (
    ReasonCodeCategory,
    require_registered_reason_codes,
)
from bijux_proteomics_foundation import JsonModel


class ScientificConsistencyIssueCode(StrEnum):
    """Machine-readable impossible or degraded cross-family states."""

    EMPTY_DIGESTION_SPACE = "empty_digestion_space"
    DIGESTION_ISSUES_PRESENT = "digestion_issues_present"
    QUANT_SUPPORT_OUTSIDE_IDENTIFICATION = "quant_support_outside_identification"
    PTM_SUPPORT_OUTSIDE_IDENTIFICATION = "ptm_support_outside_identification"
    DECISION_GRADE_WITH_QC_BLOCKERS = "decision_grade_with_qc_blockers"
    DECISION_GRADE_WITH_QUANT_BLOCKERS = "decision_grade_with_quant_blockers"
    DECISION_GRADE_WITH_HIGH_MISSINGNESS = "decision_grade_with_high_missingness"
    DECISION_GRADE_WITH_AMBIGUOUS_PTM = "decision_grade_with_ambiguous_ptm"
    REVIEW_PROJECTION_WITHOUT_CANDIDATES = "review_projection_without_candidates"


class WorkflowScientificSnapshot(JsonModel):
    """Minimal, reviewable scientific state across the core workflow families."""

    model_config = ConfigDict(extra="forbid")

    workflow_id: str = Field(..., min_length=1)
    digested_peptide_count: int = Field(..., ge=0)
    digestion_issue_codes: tuple[str, ...] = Field(default_factory=tuple)
    identified_protein_ids: tuple[str, ...] = Field(default_factory=tuple)
    shared_peptide_group_count: int = Field(..., ge=0)
    quant_support_protein_ids: tuple[str, ...] = Field(default_factory=tuple)
    quant_missingness_fraction: float = Field(..., ge=0.0, le=1.0)
    quant_readiness_state: str = Field(..., min_length=1)
    quant_blocking_reasons: tuple[str, ...] = Field(default_factory=tuple)
    ptm_protein_ids: tuple[str, ...] = Field(default_factory=tuple)
    ambiguous_ptm_site_count: int = Field(..., ge=0)
    qc_blocking_issue_codes: tuple[str, ...] = Field(default_factory=tuple)
    review_candidate_ids: tuple[str, ...] = Field(default_factory=tuple)
    target_decoy_collision_count: int = Field(..., ge=0)
    external_engine_disagreement_count: int = Field(..., ge=0)
    decision_grade_requested: bool = False

    @field_validator("quant_blocking_reasons")
    @classmethod
    def _validate_quant_blocking_reasons(
        cls, value: tuple[str, ...]
    ) -> tuple[str, ...]:
        return require_registered_reason_codes(
            value,
            ReasonCodeCategory.WORKFLOW_BLOCK,
        )

    @field_validator("qc_blocking_issue_codes")
    @classmethod
    def _validate_qc_blocking_issue_codes(
        cls, value: tuple[str, ...]
    ) -> tuple[str, ...]:
        return require_registered_reason_codes(
            value,
            ReasonCodeCategory.QC_REASON,
            ReasonCodeCategory.WORKFLOW_BLOCK,
        )


class ScientificConsistencyIssue(JsonModel):
    """One cross-family consistency issue with reviewer-facing meaning."""

    model_config = ConfigDict(extra="forbid")

    code: ScientificConsistencyIssueCode
    rationale: str = Field(..., min_length=1)
    blocking: bool


class ScientificConsistencyReport(JsonModel):
    """Scientific story validation over the flagship workflow families."""

    model_config = ConfigDict(extra="forbid")

    workflow_id: str = Field(..., min_length=1)
    composed_story: bool
    issues: tuple[ScientificConsistencyIssue, ...] = Field(default_factory=tuple)
    note: str = Field(..., min_length=1)


def build_workflow_scientific_snapshot(
    workflow_id: str,
    identification_bundle: Any,
    quant_review_bundle: Any,
    ptm_lab_validation_packet: Any,
    *,
    quant_support_protein_ids: tuple[str, ...],
    digested_peptide_count: int,
    digestion_issue_codes: tuple[str, ...] = (),
    qc_blocking_issue_codes: tuple[str, ...] = (),
    review_candidate_ids: tuple[str, ...] = (),
    target_decoy_collision_count: int = 0,
    external_engine_disagreement_count: int = 0,
    decision_grade_requested: bool = False,
) -> WorkflowScientificSnapshot:
    """Distill the core workflow families into one reviewable scientific snapshot."""

    protein_groups = identification_bundle.protein_summary.protein_groups
    identified_protein_ids = tuple(
        sorted(group.protein_ref for group in protein_groups)
    )
    shared_peptide_group_count = sum(
        1 for group in protein_groups if group.shared_peptide_count > 0
    )
    missingness_entries = quant_review_bundle.missingness_profile.entries
    missingness_with_gaps = sum(
        1 for entry in missingness_entries if len(entry.missing_samples) > 0
    )
    if missingness_entries:
        quant_missingness_fraction = missingness_with_gaps / len(missingness_entries)
    else:
        quant_missingness_fraction = 0.0
    ptm_protein_ids = tuple(
        sorted(
            {
                entry.site_key.split(":", 1)[0]
                for entry in ptm_lab_validation_packet.entries
            }
        )
    )
    ambiguous_ptm_site_count = sum(
        1 for entry in ptm_lab_validation_packet.entries if entry.ambiguous_site
    )

    return WorkflowScientificSnapshot(
        workflow_id=workflow_id,
        digested_peptide_count=digested_peptide_count,
        digestion_issue_codes=tuple(digestion_issue_codes),
        identified_protein_ids=identified_protein_ids,
        shared_peptide_group_count=shared_peptide_group_count,
        quant_support_protein_ids=tuple(sorted(set(quant_support_protein_ids))),
        quant_missingness_fraction=quant_missingness_fraction,
        quant_readiness_state=quant_review_bundle.decision_readiness.readiness_state.value,
        quant_blocking_reasons=tuple(
            quant_review_bundle.decision_readiness.blocking_reasons
        ),
        ptm_protein_ids=ptm_protein_ids,
        ambiguous_ptm_site_count=ambiguous_ptm_site_count,
        qc_blocking_issue_codes=tuple(qc_blocking_issue_codes),
        review_candidate_ids=tuple(sorted(set(review_candidate_ids))),
        target_decoy_collision_count=target_decoy_collision_count,
        external_engine_disagreement_count=external_engine_disagreement_count,
        decision_grade_requested=decision_grade_requested,
    )


def evaluate_workflow_scientific_consistency(
    snapshot: WorkflowScientificSnapshot,
) -> ScientificConsistencyReport:
    """Check whether the core scientific families still compose into one story."""

    issues: list[ScientificConsistencyIssue] = []
    identified = set(snapshot.identified_protein_ids)

    if snapshot.digested_peptide_count == 0:
        issues.append(
            ScientificConsistencyIssue(
                code=ScientificConsistencyIssueCode.EMPTY_DIGESTION_SPACE,
                rationale="digestion produced no peptides, so downstream evidence has no sequence-space support",
                blocking=True,
            )
        )
    if snapshot.digestion_issue_codes:
        issues.append(
            ScientificConsistencyIssue(
                code=ScientificConsistencyIssueCode.DIGESTION_ISSUES_PRESENT,
                rationale="digestion emitted explicit issue codes that must stay visible downstream",
                blocking=True,
            )
        )

    quant_without_identification = sorted(
        set(snapshot.quant_support_protein_ids) - identified
    )
    if quant_without_identification:
        issues.append(
            ScientificConsistencyIssue(
                code=ScientificConsistencyIssueCode.QUANT_SUPPORT_OUTSIDE_IDENTIFICATION,
                rationale=(
                    "quantification promotes proteins outside the accepted identification support set: "
                    + ", ".join(quant_without_identification)
                ),
                blocking=True,
            )
        )

    ptm_without_identification = sorted(set(snapshot.ptm_protein_ids) - identified)
    if ptm_without_identification:
        issues.append(
            ScientificConsistencyIssue(
                code=ScientificConsistencyIssueCode.PTM_SUPPORT_OUTSIDE_IDENTIFICATION,
                rationale=(
                    "PTM review promotes proteins outside the accepted identification support set: "
                    + ", ".join(ptm_without_identification)
                ),
                blocking=True,
            )
        )

    if snapshot.decision_grade_requested and snapshot.qc_blocking_issue_codes:
        issues.append(
            ScientificConsistencyIssue(
                code=ScientificConsistencyIssueCode.DECISION_GRADE_WITH_QC_BLOCKERS,
                rationale="decision-grade promotion is incompatible with unresolved QC blockers",
                blocking=True,
            )
        )
    if snapshot.decision_grade_requested and snapshot.quant_blocking_reasons:
        issues.append(
            ScientificConsistencyIssue(
                code=ScientificConsistencyIssueCode.DECISION_GRADE_WITH_QUANT_BLOCKERS,
                rationale="decision-grade promotion is incompatible with quant blocking reasons",
                blocking=True,
            )
        )
    if snapshot.decision_grade_requested and snapshot.quant_missingness_fraction > 0.5:
        issues.append(
            ScientificConsistencyIssue(
                code=ScientificConsistencyIssueCode.DECISION_GRADE_WITH_HIGH_MISSINGNESS,
                rationale="decision-grade promotion is incompatible with majority-missing quantitative support",
                blocking=True,
            )
        )
    if snapshot.decision_grade_requested and snapshot.ambiguous_ptm_site_count > 0:
        issues.append(
            ScientificConsistencyIssue(
                code=ScientificConsistencyIssueCode.DECISION_GRADE_WITH_AMBIGUOUS_PTM,
                rationale="decision-grade promotion is incompatible with unresolved PTM site ambiguity",
                blocking=True,
            )
        )
    if snapshot.decision_grade_requested and not snapshot.review_candidate_ids:
        issues.append(
            ScientificConsistencyIssue(
                code=ScientificConsistencyIssueCode.REVIEW_PROJECTION_WITHOUT_CANDIDATES,
                rationale="decision-grade promotion requires at least one explicit downstream candidate projection",
                blocking=True,
            )
        )

    return ScientificConsistencyReport(
        workflow_id=snapshot.workflow_id,
        composed_story=not any(issue.blocking for issue in issues),
        issues=tuple(issues),
        note=(
            "The scientific story is composed only when digestion, identification, quantification, PTM, and review projection do not contradict each other."
        ),
    )
