# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""External credibility and ecosystem-fit surfaces for iteration 20."""

from __future__ import annotations

from pydantic import ConfigDict, Field

from bijux_proteomics_foundation import JsonModel


class TrialIssueEntry(JsonModel):
    """One precise issue filed by a trial user."""

    model_config = ConfigDict(extra="forbid")

    issue_id: str = Field(..., min_length=1)
    summary: str = Field(..., min_length=1)
    evidence_pointer: str = Field(..., min_length=1)
    severity: str = Field(..., min_length=1)


class ExternalDdaTrialInput(JsonModel):
    """Input payload for external strong-user DDA trial reporting."""

    model_config = ConfigDict(extra="forbid")

    trial_id: str = Field(..., min_length=1)
    external_user_id: str = Field(..., min_length=1)
    dataset_id: str = Field(..., min_length=1)
    executed_steps: tuple[str, ...] = Field(default_factory=tuple)
    issues: tuple[TrialIssueEntry, ...] = Field(default_factory=tuple)


class ExternalDdaTrialReport(JsonModel):
    """Report for external strong-user DDA trial execution and issue quality."""

    model_config = ConfigDict(extra="forbid")

    trial_id: str = Field(..., min_length=1)
    external_user_id: str = Field(..., min_length=1)
    dataset_id: str = Field(..., min_length=1)
    executed_steps: tuple[str, ...] = Field(default_factory=tuple)
    issues: tuple[TrialIssueEntry, ...] = Field(default_factory=tuple)
    precise_issue_count: int = Field(..., ge=0)
    trial_completed: bool


def build_external_strong_user_dda_trial_report(
    payload: ExternalDdaTrialInput,
) -> ExternalDdaTrialReport:
    """Build DDA external trial report and require explicit issue evidence pointers."""

    precise_issues = tuple(
        issue for issue in payload.issues if issue.evidence_pointer.strip()
    )
    required_steps = {"dda-import", "qc", "evidence", "review"}
    completed = required_steps.issubset(set(payload.executed_steps))
    return ExternalDdaTrialReport(
        trial_id=payload.trial_id,
        external_user_id=payload.external_user_id,
        dataset_id=payload.dataset_id,
        executed_steps=tuple(payload.executed_steps),
        issues=tuple(payload.issues),
        precise_issue_count=len(precise_issues),
        trial_completed=completed,
    )


class ExternalDiaTrialInput(JsonModel):
    """Input payload for external strong-user DIA trial reporting."""

    model_config = ConfigDict(extra="forbid")

    trial_id: str = Field(..., min_length=1)
    external_user_id: str = Field(..., min_length=1)
    dataset_id: str = Field(..., min_length=1)
    executed_steps: tuple[str, ...] = Field(default_factory=tuple)
    issues: tuple[TrialIssueEntry, ...] = Field(default_factory=tuple)


class ExternalDiaTrialReport(JsonModel):
    """Report for external strong-user DIA trial execution and issue quality."""

    model_config = ConfigDict(extra="forbid")

    trial_id: str = Field(..., min_length=1)
    external_user_id: str = Field(..., min_length=1)
    dataset_id: str = Field(..., min_length=1)
    executed_steps: tuple[str, ...] = Field(default_factory=tuple)
    issues: tuple[TrialIssueEntry, ...] = Field(default_factory=tuple)
    precise_issue_count: int = Field(..., ge=0)
    trial_completed: bool


def build_external_strong_user_dia_trial_report(
    payload: ExternalDiaTrialInput,
) -> ExternalDiaTrialReport:
    """Build DIA external trial report and require explicit issue evidence pointers."""

    precise_issues = tuple(
        issue for issue in payload.issues if issue.evidence_pointer.strip()
    )
    required_steps = {"dia-import", "quant", "qc", "evidence"}
    completed = required_steps.issubset(set(payload.executed_steps))
    return ExternalDiaTrialReport(
        trial_id=payload.trial_id,
        external_user_id=payload.external_user_id,
        dataset_id=payload.dataset_id,
        executed_steps=tuple(payload.executed_steps),
        issues=tuple(payload.issues),
        precise_issue_count=len(precise_issues),
        trial_completed=completed,
    )


class ExternalQuantTrialInput(JsonModel):
    """Input payload for external strong-user quant trial reporting."""

    model_config = ConfigDict(extra="forbid")

    trial_id: str = Field(..., min_length=1)
    external_user_id: str = Field(..., min_length=1)
    mini_study_id: str = Field(..., min_length=1)
    executed_steps: tuple[str, ...] = Field(default_factory=tuple)
    issues: tuple[TrialIssueEntry, ...] = Field(default_factory=tuple)


class ExternalQuantTrialReport(JsonModel):
    """Report for external strong-user quant trial execution and issue quality."""

    model_config = ConfigDict(extra="forbid")

    trial_id: str = Field(..., min_length=1)
    external_user_id: str = Field(..., min_length=1)
    mini_study_id: str = Field(..., min_length=1)
    executed_steps: tuple[str, ...] = Field(default_factory=tuple)
    issues: tuple[TrialIssueEntry, ...] = Field(default_factory=tuple)
    precise_issue_count: int = Field(..., ge=0)
    trial_completed: bool


def build_external_strong_user_quant_trial_report(
    payload: ExternalQuantTrialInput,
) -> ExternalQuantTrialReport:
    """Build quant external trial report for normalization/DA/review coverage."""

    precise_issues = tuple(
        issue for issue in payload.issues if issue.evidence_pointer.strip()
    )
    required_steps = {"normalization", "differential-abundance", "review"}
    completed = required_steps.issubset(set(payload.executed_steps))
    return ExternalQuantTrialReport(
        trial_id=payload.trial_id,
        external_user_id=payload.external_user_id,
        mini_study_id=payload.mini_study_id,
        executed_steps=tuple(payload.executed_steps),
        issues=tuple(payload.issues),
        precise_issue_count=len(precise_issues),
        trial_completed=completed,
    )


class ExternalPtmTrialInput(JsonModel):
    """Input payload for external strong-user PTM trial reporting."""

    model_config = ConfigDict(extra="forbid")

    trial_id: str = Field(..., min_length=1)
    external_user_id: str = Field(..., min_length=1)
    ptm_study_id: str = Field(..., min_length=1)
    executed_steps: tuple[str, ...] = Field(default_factory=tuple)
    issues: tuple[TrialIssueEntry, ...] = Field(default_factory=tuple)


class ExternalPtmTrialReport(JsonModel):
    """Report for external strong-user PTM trial execution and issue quality."""

    model_config = ConfigDict(extra="forbid")

    trial_id: str = Field(..., min_length=1)
    external_user_id: str = Field(..., min_length=1)
    ptm_study_id: str = Field(..., min_length=1)
    executed_steps: tuple[str, ...] = Field(default_factory=tuple)
    issues: tuple[TrialIssueEntry, ...] = Field(default_factory=tuple)
    precise_issue_count: int = Field(..., ge=0)
    trial_completed: bool


def build_external_strong_user_ptm_trial_report(
    payload: ExternalPtmTrialInput,
) -> ExternalPtmTrialReport:
    """Build PTM external trial report for ambiguity inspection and lab handoff."""

    precise_issues = tuple(
        issue for issue in payload.issues if issue.evidence_pointer.strip()
    )
    required_steps = {"ptm-ambiguity-review", "lab-handoff"}
    completed = required_steps.issubset(set(payload.executed_steps))
    return ExternalPtmTrialReport(
        trial_id=payload.trial_id,
        external_user_id=payload.external_user_id,
        ptm_study_id=payload.ptm_study_id,
        executed_steps=tuple(payload.executed_steps),
        issues=tuple(payload.issues),
        precise_issue_count=len(precise_issues),
        trial_completed=completed,
    )


class ExternalLabTrialInput(JsonModel):
    """Input payload for external strong-user lab trial reporting."""

    model_config = ConfigDict(extra="forbid")

    trial_id: str = Field(..., min_length=1)
    external_user_id: str = Field(..., min_length=1)
    lab_program_id: str = Field(..., min_length=1)
    executed_steps: tuple[str, ...] = Field(default_factory=tuple)
    issues: tuple[TrialIssueEntry, ...] = Field(default_factory=tuple)


class ExternalLabTrialReport(JsonModel):
    """Report for external strong-user lab trial execution and issue quality."""

    model_config = ConfigDict(extra="forbid")

    trial_id: str = Field(..., min_length=1)
    external_user_id: str = Field(..., min_length=1)
    lab_program_id: str = Field(..., min_length=1)
    executed_steps: tuple[str, ...] = Field(default_factory=tuple)
    issues: tuple[TrialIssueEntry, ...] = Field(default_factory=tuple)
    precise_issue_count: int = Field(..., ge=0)
    trial_completed: bool


def build_external_strong_user_lab_trial_report(
    payload: ExternalLabTrialInput,
) -> ExternalLabTrialReport:
    """Build lab external trial report for plans, risks, and handoff exports."""

    precise_issues = tuple(
        issue for issue in payload.issues if issue.evidence_pointer.strip()
    )
    required_steps = {"assay-plan", "risk-review", "handoff-export"}
    completed = required_steps.issubset(set(payload.executed_steps))
    return ExternalLabTrialReport(
        trial_id=payload.trial_id,
        external_user_id=payload.external_user_id,
        lab_program_id=payload.lab_program_id,
        executed_steps=tuple(payload.executed_steps),
        issues=tuple(payload.issues),
        precise_issue_count=len(precise_issues),
        trial_completed=completed,
    )


class EcosystemComparisonEntry(JsonModel):
    """One ecosystem comparison row against a mature proteomics toolchain."""

    model_config = ConfigDict(extra="forbid")

    ecosystem_name: str = Field(..., min_length=1)
    scope_match_score: float = Field(..., ge=0.0, le=1.0)
    evidence_traceability_score: float = Field(..., ge=0.0, le=1.0)
    known_gap_summary: str = Field(..., min_length=1)


class MatureEcosystemComparisonReport(JsonModel):
    """Honest scope/evidence comparison report against mature ecosystems."""

    model_config = ConfigDict(extra="forbid")

    entries: tuple[EcosystemComparisonEntry, ...] = Field(default_factory=tuple)
    average_scope_match_score: float = Field(..., ge=0.0, le=1.0)
    average_evidence_traceability_score: float = Field(..., ge=0.0, le=1.0)


def build_mature_ecosystem_comparison_report(
    entries: tuple[EcosystemComparisonEntry, ...],
) -> MatureEcosystemComparisonReport:
    """Compare scope and evidence posture with transparent gap accounting."""

    ordered = tuple(sorted(entries, key=lambda entry: entry.ecosystem_name.lower()))
    if not ordered:
        return MatureEcosystemComparisonReport(
            entries=(),
            average_scope_match_score=0.0,
            average_evidence_traceability_score=0.0,
        )
    scope_avg = sum(item.scope_match_score for item in ordered) / len(ordered)
    evidence_avg = sum(item.evidence_traceability_score for item in ordered) / len(ordered)
    return MatureEcosystemComparisonReport(
        entries=ordered,
        average_scope_match_score=scope_avg,
        average_evidence_traceability_score=evidence_avg,
    )


class BijuxCoreIntegrationContractInput(JsonModel):
    """Input describing compatibility between proteomics outputs and Bijux core contracts."""

    model_config = ConfigDict(extra="forbid")

    contract_id: str = Field(..., min_length=1)
    dag_nodes_emitted: tuple[str, ...] = Field(default_factory=tuple)
    edge_types_emitted: tuple[str, ...] = Field(default_factory=tuple)
    evidence_payload_refs: tuple[str, ...] = Field(default_factory=tuple)
    incompatible_surfaces: tuple[str, ...] = Field(default_factory=tuple)


class BijuxCoreIntegrationContractReport(JsonModel):
    """Compatibility report for emitting Bijux core DAG and evidence contracts."""

    model_config = ConfigDict(extra="forbid")

    contract_id: str = Field(..., min_length=1)
    dag_nodes_emitted: tuple[str, ...] = Field(default_factory=tuple)
    edge_types_emitted: tuple[str, ...] = Field(default_factory=tuple)
    evidence_payload_refs: tuple[str, ...] = Field(default_factory=tuple)
    incompatible_surfaces: tuple[str, ...] = Field(default_factory=tuple)
    compatible: bool


def build_bijux_core_integration_contract_report(
    payload: BijuxCoreIntegrationContractInput,
) -> BijuxCoreIntegrationContractReport:
    """Build compatibility report for Bijux core DAG/evidence integration."""

    return BijuxCoreIntegrationContractReport(
        contract_id=payload.contract_id,
        dag_nodes_emitted=tuple(sorted(set(payload.dag_nodes_emitted))),
        edge_types_emitted=tuple(sorted(set(payload.edge_types_emitted))),
        evidence_payload_refs=tuple(sorted(set(payload.evidence_payload_refs))),
        incompatible_surfaces=tuple(sorted(set(payload.incompatible_surfaces))),
        compatible=not payload.incompatible_surfaces,
    )


class AgenticProteinsMigrationItem(JsonModel):
    """One migration mapping from legacy agentic-proteins surface to canonical package usage."""

    model_config = ConfigDict(extra="forbid")

    legacy_surface: str = Field(..., min_length=1)
    canonical_surface: str = Field(..., min_length=1)
    compatibility_mode: str = Field(..., min_length=1)


class AgenticProteinsMigrationReport(JsonModel):
    """Migration report for maintaining legacy users while promoting canonical usage."""

    model_config = ConfigDict(extra="forbid")

    migration_id: str = Field(..., min_length=1)
    mappings: tuple[AgenticProteinsMigrationItem, ...] = Field(default_factory=tuple)
    blocking_gaps: tuple[str, ...] = Field(default_factory=tuple)
    migration_ready: bool


def build_agentic_proteins_migration_report(
    migration_id: str,
    mappings: tuple[AgenticProteinsMigrationItem, ...],
    *,
    blocking_gaps: tuple[str, ...] = (),
) -> AgenticProteinsMigrationReport:
    """Build migration report for legacy-to-canonical proteomics usage transition."""

    ordered_mappings = tuple(
        sorted(mappings, key=lambda mapping: mapping.legacy_surface.lower())
    )
    return AgenticProteinsMigrationReport(
        migration_id=migration_id,
        mappings=ordered_mappings,
        blocking_gaps=tuple(sorted(set(blocking_gaps))),
        migration_ready=bool(ordered_mappings) and not blocking_gaps,
    )


class FlagshipDemoInput(JsonModel):
    """Input describing one full flagship proteomics demonstration run."""

    model_config = ConfigDict(extra="forbid")

    demo_id: str = Field(..., min_length=1)
    input_artifacts: tuple[str, ...] = Field(default_factory=tuple)
    completed_stages: tuple[str, ...] = Field(default_factory=tuple)
    evidence_graph_ref: str = Field(..., min_length=1)
    review_packet_ref: str = Field(..., min_length=1)
    lab_handoff_ref: str = Field(..., min_length=1)


class FlagshipDemoReport(JsonModel):
    """Report for one complete inputs-to-lab-handoff flagship workflow demo."""

    model_config = ConfigDict(extra="forbid")

    demo_id: str = Field(..., min_length=1)
    input_artifacts: tuple[str, ...] = Field(default_factory=tuple)
    completed_stages: tuple[str, ...] = Field(default_factory=tuple)
    evidence_graph_ref: str = Field(..., min_length=1)
    review_packet_ref: str = Field(..., min_length=1)
    lab_handoff_ref: str = Field(..., min_length=1)
    complete_demo: bool


def build_final_flagship_proteomics_demo_report(
    payload: FlagshipDemoInput,
) -> FlagshipDemoReport:
    """Build complete flagship demo report from inputs to lab handoff."""

    required_stages = {"input-ingest", "evidence-graph", "review-packet", "lab-handoff"}
    complete = required_stages.issubset(set(payload.completed_stages))
    return FlagshipDemoReport(
        demo_id=payload.demo_id,
        input_artifacts=tuple(sorted(set(payload.input_artifacts))),
        completed_stages=tuple(payload.completed_stages),
        evidence_graph_ref=payload.evidence_graph_ref,
        review_packet_ref=payload.review_packet_ref,
        lab_handoff_ref=payload.lab_handoff_ref,
        complete_demo=complete,
    )


class UsageSimplificationCandidate(JsonModel):
    """One product surface candidate for keep/demote/remove decision."""

    model_config = ConfigDict(extra="forbid")

    surface_id: str = Field(..., min_length=1)
    recent_usage_count: int = Field(..., ge=0)
    user_value_summary: str = Field(..., min_length=1)
    decision: str = Field(..., min_length=1)


class ProductSimplificationByUsageReport(JsonModel):
    """Simplification report from observed usage and explicit value statements."""

    model_config = ConfigDict(extra="forbid")

    candidates: tuple[UsageSimplificationCandidate, ...] = Field(default_factory=tuple)
    remove_count: int = Field(..., ge=0)
    demote_count: int = Field(..., ge=0)
    keep_count: int = Field(..., ge=0)


def build_product_simplification_by_real_usage_report(
    candidates: tuple[UsageSimplificationCandidate, ...],
) -> ProductSimplificationByUsageReport:
    """Build simplification report that removes or demotes low-value unused surfaces."""

    ordered = tuple(sorted(candidates, key=lambda item: item.surface_id.lower()))
    remove_count = sum(1 for item in ordered if item.decision == "remove")
    demote_count = sum(1 for item in ordered if item.decision == "demote")
    keep_count = sum(1 for item in ordered if item.decision == "keep")
    return ProductSimplificationByUsageReport(
        candidates=ordered,
        remove_count=remove_count,
        demote_count=demote_count,
        keep_count=keep_count,
    )
