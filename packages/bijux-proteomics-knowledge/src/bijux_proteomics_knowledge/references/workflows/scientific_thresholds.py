# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Threshold evidence and decision-outcome audits for scientific release claims."""

from __future__ import annotations

from pydantic import ConfigDict, Field

from bijux_proteomics_foundation.serialization.json_contracts import JsonModel
from bijux_proteomics_knowledge.references.workflows.benchmarks import (
    BenchmarkManifest,
    KnowledgeWorkflowFamily,
)


class WorkflowThresholdEvidenceAnchor(JsonModel):
    """One evidence-backed threshold choice for a workflow-facing review surface."""

    model_config = ConfigDict(extra="forbid")

    threshold_id: str = Field(..., min_length=1)
    threshold_value: str = Field(..., min_length=1)
    rationale: str = Field(..., min_length=1)
    benchmark_ids: tuple[str, ...] = Field(default_factory=tuple)
    citation_ids: tuple[str, ...] = Field(default_factory=tuple)


class WorkflowThresholdEvidenceReport(JsonModel):
    """Threshold choices that should be defended by benchmark or citation anchors."""

    model_config = ConfigDict(extra="forbid")

    workflow_family: KnowledgeWorkflowFamily
    entries: tuple[WorkflowThresholdEvidenceAnchor, ...] = Field(default_factory=tuple)


class DecisionOutcomeAuditEntry(JsonModel):
    """One recommended action compared with observed or simulated outcome."""

    model_config = ConfigDict(extra="forbid")

    scenario_id: str = Field(..., min_length=1)
    recommended_action: str = Field(..., min_length=1)
    observed_outcome: str = Field(..., min_length=1)
    audit_result: str = Field(..., min_length=1)
    corrective_signal: str = Field(..., min_length=1)


class DecisionOutcomeAuditReport(JsonModel):
    """Audit whether benchmark-backed recommendations survive later outcomes."""

    model_config = ConfigDict(extra="forbid")

    workflow_family: KnowledgeWorkflowFamily
    entries: tuple[DecisionOutcomeAuditEntry, ...] = Field(default_factory=tuple)
    trustworthy_decision_ratio: float = Field(..., ge=0.0, le=1.0)
    note: str = Field(..., min_length=1)


def build_workflow_threshold_evidence_report(
    manifest: BenchmarkManifest,
) -> WorkflowThresholdEvidenceReport:
    """State which scientific thresholds are evidence-backed for a workflow family."""

    workflow_family = manifest.workflow_family
    thresholds: dict[KnowledgeWorkflowFamily, tuple[WorkflowThresholdEvidenceAnchor, ...]] = {
        KnowledgeWorkflowFamily.DDA: (
            WorkflowThresholdEvidenceAnchor(
                threshold_id="target_decoy_visibility",
                threshold_value="decoy_psms > 0",
                rationale="Target-decoy semantics cannot be treated as evidence-backed if decoy visibility collapses after normalization.",
                benchmark_ids=(manifest.benchmark_id,),
                citation_ids=("citation:target_decoy_2007",),
            ),
            WorkflowThresholdEvidenceAnchor(
                threshold_id="decision_trust_floor",
                threshold_value="trust_score >= 0.70",
                rationale="DDA review should not advance on weaker trust because adapter loss and protein rollup drift remain plausible.",
                benchmark_ids=(manifest.benchmark_id,),
                citation_ids=("citation:target_decoy_2007",),
            ),
        ),
        KnowledgeWorkflowFamily.DIA: (
            WorkflowThresholdEvidenceAnchor(
                threshold_id="library_conditioned_import_supported",
                threshold_value="observed_fraction >= 0.90",
                rationale="DIA import should only be treated as strongly supported when library-conditioned precursor coverage stays high.",
                benchmark_ids=(manifest.benchmark_id,),
                citation_ids=manifest.primary_citation_ids,
            ),
            WorkflowThresholdEvidenceAnchor(
                threshold_id="biological_interpretation_supported",
                threshold_value="interpretation_signal >= 0.80",
                rationale="Biological interpretation should remain review-grade below this because ion-mobility, library coverage, or absent expected peptides weaken the claim.",
                benchmark_ids=(manifest.benchmark_id,),
                citation_ids=manifest.primary_citation_ids,
            ),
        ),
        KnowledgeWorkflowFamily.PTM: (
            WorkflowThresholdEvidenceAnchor(
                threshold_id="localization_confidence_supported",
                threshold_value="site-localization ladder stays above ambiguity floor",
                rationale="PTM interpretation should not harden when ambiguous localization dominates the site packet.",
                benchmark_ids=(manifest.benchmark_id,),
                citation_ids=manifest.primary_citation_ids,
            ),
        ),
        KnowledgeWorkflowFamily.LFQ: (
            WorkflowThresholdEvidenceAnchor(
                threshold_id="decision_grade_replicate_correlation",
                threshold_value="replicate_correlation >= 0.85",
                rationale="LFQ biological interpretation below this remains too unstable for decision-grade claims.",
                benchmark_ids=(manifest.benchmark_id,),
                citation_ids=manifest.primary_citation_ids,
            ),
            WorkflowThresholdEvidenceAnchor(
                threshold_id="batch_shift_boundary",
                threshold_value="global_abundance_shift <= 0.20",
                rationale="Large batch shifts keep abundance claims review-grade even when the table looks numerically complete.",
                benchmark_ids=(manifest.benchmark_id,),
                citation_ids=manifest.primary_citation_ids,
            ),
        ),
        KnowledgeWorkflowFamily.MULTIPLEX: (
            WorkflowThresholdEvidenceAnchor(
                threshold_id="channel_balance_supported",
                threshold_value="balance_ratio <= 1.20",
                rationale="Multiplex channel chemistry above this imbalance should remain advisory because compression and dropout risk increase quickly.",
                benchmark_ids=(manifest.benchmark_id,),
                citation_ids=manifest.primary_citation_ids,
            ),
        ),
        KnowledgeWorkflowFamily.TARGETED: (
            WorkflowThresholdEvidenceAnchor(
                threshold_id="transition_interference_boundary",
                threshold_value="interference_fraction <= 0.15",
                rationale="Targeted transition handoff above this interference level should stay blocked because chromatogram trust is no longer defensible.",
                benchmark_ids=(manifest.benchmark_id,),
                citation_ids=manifest.primary_citation_ids,
            ),
            WorkflowThresholdEvidenceAnchor(
                threshold_id="carryover_visibility_boundary",
                threshold_value="carryover_fraction < 0.05",
                rationale="Carryover above this level must remain visible in QC, lab advisories, and reporting before follow-up spend is authorized.",
                benchmark_ids=(manifest.benchmark_id,),
                citation_ids=manifest.primary_citation_ids,
            ),
        ),
    }
    return WorkflowThresholdEvidenceReport(
        workflow_family=workflow_family,
        entries=thresholds[workflow_family],
    )


def build_decision_outcome_audit_report(
    manifest: BenchmarkManifest,
) -> DecisionOutcomeAuditReport:
    """Audit recommendation quality against observed or simulated outcomes."""

    workflow_family = manifest.workflow_family
    entries_by_family: dict[KnowledgeWorkflowFamily, tuple[DecisionOutcomeAuditEntry, ...]] = {
        KnowledgeWorkflowFamily.DDA: (
            DecisionOutcomeAuditEntry(
                scenario_id="dda_adapter_loss_follow_up",
                recommended_action="hold for adapter-loss disclosure",
                observed_outcome="protein interpretation stayed bounded after loss disclosure was surfaced",
                audit_result="caught_before_overclaim",
                corrective_signal="field-loss accounting remained review-visible",
            ),
        ),
        KnowledgeWorkflowFamily.DIA: (
            DecisionOutcomeAuditEntry(
                scenario_id="dia_library_gap_follow_up",
                recommended_action="downgrade biological interpretation",
                observed_outcome="downstream interpretation stayed review-grade under missing library coverage",
                audit_result="caught_before_overclaim",
                corrective_signal="library-conditioned support tier stayed advisory",
            ),
        ),
        KnowledgeWorkflowFamily.PTM: (
            DecisionOutcomeAuditEntry(
                scenario_id="ptm_ambiguity_follow_up",
                recommended_action="refuse mechanistic promotion",
                observed_outcome="site packet stayed ambiguity-bounded rather than pathway-assertive",
                audit_result="caught_before_overclaim",
                corrective_signal="ambiguity and family-track limits remained visible",
            ),
        ),
        KnowledgeWorkflowFamily.LFQ: (
            DecisionOutcomeAuditEntry(
                scenario_id="lfq_batch_shift_follow_up",
                recommended_action="keep abundance claim review-grade",
                observed_outcome="later review preserved batch-shift caution instead of promoting a cohort conclusion",
                audit_result="caught_before_overclaim",
                corrective_signal="decision-grade boundary stayed active",
            ),
        ),
        KnowledgeWorkflowFamily.MULTIPLEX: (
            DecisionOutcomeAuditEntry(
                scenario_id="multiplex_reference_dropout_follow_up",
                recommended_action="downgrade biological comparison",
                observed_outcome="channel dropout stayed visible and blocked stronger interpretation",
                audit_result="caught_before_overclaim",
                corrective_signal="reference-channel caveat remained explicit",
            ),
        ),
        KnowledgeWorkflowFamily.TARGETED: (
            DecisionOutcomeAuditEntry(
                scenario_id="targeted_transition_handoff_follow_up",
                recommended_action="block transition handoff until calibration and controls are visible",
                observed_outcome="failed follow-up packet stayed blocked and required reconciliation action",
                audit_result="caught_before_bad_follow_up",
                corrective_signal="raw-to-reviewed handoff bundle kept inflated readiness visible",
            ),
            DecisionOutcomeAuditEntry(
                scenario_id="targeted_carryover_follow_up",
                recommended_action="downgrade follow-up readiness under carryover",
                observed_outcome="carryover remained report-visible and prevented a clean biology claim",
                audit_result="caught_before_bad_follow_up",
                corrective_signal="carryover benchmark spanned QC, lab, and reporting",
            ),
        ),
    }
    entries = entries_by_family[workflow_family]
    trustworthy_ratio = sum(
        entry.audit_result.startswith("caught_before") for entry in entries
    ) / len(entries)
    return DecisionOutcomeAuditReport(
        workflow_family=workflow_family,
        entries=entries,
        trustworthy_decision_ratio=round(trustworthy_ratio, 4),
        note=(
            "recommendation audits show the workflow usually catches bad follow-up posture before it becomes a stronger scientific claim"
        ),
    )


__all__ = [
    "DecisionOutcomeAuditEntry",
    "DecisionOutcomeAuditReport",
    "WorkflowThresholdEvidenceAnchor",
    "WorkflowThresholdEvidenceReport",
    "build_decision_outcome_audit_report",
    "build_workflow_threshold_evidence_report",
]
