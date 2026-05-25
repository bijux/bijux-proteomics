# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Machine-readable charter for the operational lab package boundary."""

from __future__ import annotations

from enum import StrEnum

from pydantic import ConfigDict, Field

from bijux_proteomics_foundation import JsonModel


class LabCharterCapability(StrEnum):
    """Operational capabilities that justify the lab package boundary."""

    ASSAY_PLANNING = "assay_planning"
    QUEUEING = "queueing"
    PROGRESSION = "progression"
    HANDOFF_PACKETS = "handoff_packets"
    OBSERVED_OUTCOME_RECONCILIATION = "observed_outcome_reconciliation"


class LabModuleClassification(StrEnum):
    """Allowed audit outcomes for lab source modules."""

    OPERATIONAL_VALUE = "operational_value"
    THIN_ABSTRACTION = "thin_abstraction"
    DUPLICATE_SCHEMA = "duplicate_schema"
    WRONG_PACKAGE_LOGIC = "wrong_package_logic"


class LabCharterEntry(JsonModel):
    """One durable capability owned by the lab package."""

    model_config = ConfigDict(extra="forbid")

    capability: LabCharterCapability
    owned_surface: str = Field(..., min_length=1)
    required_modules: tuple[str, ...] = Field(..., min_length=1)
    release_blocker: str = Field(..., min_length=1)


class LabModuleAuditEntry(JsonModel):
    """Audit record for one lab source module."""

    model_config = ConfigDict(extra="forbid")

    module_path: str = Field(..., min_length=1)
    classification: LabModuleClassification
    anchor_capabilities: tuple[LabCharterCapability, ...] = Field(default_factory=tuple)
    reason: str = Field(..., min_length=1)


DEFAULT_LAB_CHARTER: tuple[LabCharterEntry, ...] = (
    LabCharterEntry(
        capability=LabCharterCapability.ASSAY_PLANNING,
        owned_surface="Executable assay planning that turns scientific requirements into concrete batchable work.",
        required_modules=(
            "planning/assays.py",
            "planning/priorities.py",
            "design/experiments.py",
            "design/protocols.py",
        ),
        release_blocker="Lab cannot ship if assay work remains a packet shell without concrete planning behavior.",
    ),
    LabCharterEntry(
        capability=LabCharterCapability.QUEUEING,
        owned_surface="Queue-aware execution planning that respects capacity, backlog, and review-gate pressure.",
        required_modules=(
            "planning/scheduling.py",
            "planning/priorities.py",
            "readiness/operations.py",
            "planning/queue.py",
        ),
        release_blocker="Lab cannot ship if queue and capacity handling disappear into downstream ad hoc logic.",
    ),
    LabCharterEntry(
        capability=LabCharterCapability.PROGRESSION,
        owned_surface="Operational progression and review transitions grounded in lab-ready state rather than recommendation-only ranking.",
        required_modules=(
            "lifecycle/progression.py",
            "planning/next_cycle.py",
            "planning/priorities.py",
            "readiness/operations.py",
        ),
        release_blocker="Lab cannot ship if progression decisions ignore operational readiness or unresolved execution blockers.",
    ),
    LabCharterEntry(
        capability=LabCharterCapability.HANDOFF_PACKETS,
        owned_surface="Reviewable handoff packets that preserve protocol controls, caveats, and artifact integrity.",
        required_modules=(
            "design/protocols.py",
            "handoffs/artifacts.py",
            "planning/assays.py",
            "planning/priorities.py",
            "handoffs/transitions.py",
            "handoffs/explanations.py",
            "handoffs/exports.py",
            "handoffs/ptm.py",
            "handoffs/risk.py",
            "benchmarks/claims.py",
            "benchmarks/follow_up.py",
            "benchmarks/learning.py",
            "benchmarks/rehearsals.py",
        ),
        release_blocker="Lab cannot ship if handoff packets lose protocol controls, caveats, or artifact integrity.",
    ),
    LabCharterEntry(
        capability=LabCharterCapability.OBSERVED_OUTCOME_RECONCILIATION,
        owned_surface="Observed-outcome interpretation that feeds back into reruns, evidence promotion, and future cycles.",
        required_modules=(
            "outcomes/observations.py",
            "outcomes/feedback.py",
            "readiness/operations.py",
            "handoffs/risk.py",
            "reconciliation/flagship_follow_up.py",
            "reconciliation/follow_up.py",
        ),
        release_blocker="Lab cannot ship if observed outcomes cannot reconcile back into operational follow-up and feedback loops.",
    ),
)


DEFAULT_LAB_MODULE_AUDIT: tuple[LabModuleAuditEntry, ...] = (
    LabModuleAuditEntry(
        module_path="__init__.py",
        classification=LabModuleClassification.THIN_ABSTRACTION,
        reason="The package root is an export surface and intentionally aggregates stable operational entrypoints.",
    ),
    LabModuleAuditEntry(
        module_path="public_api.py",
        classification=LabModuleClassification.OPERATIONAL_VALUE,
        anchor_capabilities=(
            LabCharterCapability.ASSAY_PLANNING,
            LabCharterCapability.QUEUEING,
            LabCharterCapability.PROGRESSION,
            LabCharterCapability.HANDOFF_PACKETS,
            LabCharterCapability.OBSERVED_OUTCOME_RECONCILIATION,
        ),
        reason="The machine-readable root API contract keeps the supported lab-operational import surface explicit and release-auditable.",
    ),
    LabModuleAuditEntry(
        module_path="design/__init__.py",
        classification=LabModuleClassification.THIN_ABSTRACTION,
        reason="The design band re-exports the experiment-design owner surface under the durable design namespace.",
    ),
    LabModuleAuditEntry(
        module_path="design/experiments.py",
        classification=LabModuleClassification.OPERATIONAL_VALUE,
        anchor_capabilities=(
            LabCharterCapability.ASSAY_PLANNING,
            LabCharterCapability.HANDOFF_PACKETS,
        ),
        reason="Experiment-design validation and layout planning are executable lab-operations behavior.",
    ),
    LabModuleAuditEntry(
        module_path="design/protocols.py",
        classification=LabModuleClassification.OPERATIONAL_VALUE,
        anchor_capabilities=(
            LabCharterCapability.ASSAY_PLANNING,
            LabCharterCapability.HANDOFF_PACKETS,
        ),
        reason="Protocol attachments keep controls, versions, and caveats attached to lab handoffs.",
    ),
    LabModuleAuditEntry(
        module_path="benchmarks/__init__.py",
        classification=LabModuleClassification.THIN_ABSTRACTION,
        reason="The benchmarks band re-exports benchmark rehearsal owners under the durable benchmarks namespace.",
    ),
    LabModuleAuditEntry(
        module_path="benchmarks/claims.py",
        classification=LabModuleClassification.OPERATIONAL_VALUE,
        anchor_capabilities=(
            LabCharterCapability.HANDOFF_PACKETS,
            LabCharterCapability.OBSERVED_OUTCOME_RECONCILIATION,
        ),
        reason="Targeted benchmark claims keep benchmark support posture tied to exact discovery, handoff, cache, and observed-feedback evidence.",
    ),
    LabModuleAuditEntry(
        module_path="benchmarks/follow_up.py",
        classification=LabModuleClassification.OPERATIONAL_VALUE,
        anchor_capabilities=(
            LabCharterCapability.ASSAY_PLANNING,
            LabCharterCapability.HANDOFF_PACKETS,
        ),
        reason="Flagship benchmark follow-up packets turn review posture into concrete lab-facing controls, boundary conditions, and burden tradeoffs.",
    ),
    LabModuleAuditEntry(
        module_path="benchmarks/learning.py",
        classification=LabModuleClassification.OPERATIONAL_VALUE,
        anchor_capabilities=(
            LabCharterCapability.HANDOFF_PACKETS,
            LabCharterCapability.OBSERVED_OUTCOME_RECONCILIATION,
        ),
        reason="Benchmark learning artifacts keep requested-versus-observed follow-up loops visible instead of flattening them into generic success stories.",
    ),
    LabModuleAuditEntry(
        module_path="benchmarks/rehearsals.py",
        classification=LabModuleClassification.OPERATIONAL_VALUE,
        anchor_capabilities=(
            LabCharterCapability.HANDOFF_PACKETS,
            LabCharterCapability.OBSERVED_OUTCOME_RECONCILIATION,
        ),
        reason="Targeted benchmark rehearsals keep operator, failure, and external-review delivery separate from claim construction.",
    ),
    LabModuleAuditEntry(
        module_path="benchmarks/outcome_dossiers.py",
        classification=LabModuleClassification.OPERATIONAL_VALUE,
        anchor_capabilities=(
            LabCharterCapability.HANDOFF_PACKETS,
            LabCharterCapability.OBSERVED_OUTCOME_RECONCILIATION,
        ),
        reason="Outcome dossiers keep observed benchmark follow-up consequences reviewable as durable lab-facing evidence instead of one-line summaries.",
    ),
    LabModuleAuditEntry(
        module_path="governance/__init__.py",
        classification=LabModuleClassification.THIN_ABSTRACTION,
        reason="The governance band exposes package-boundary metadata without adding operational behavior.",
    ),
    LabModuleAuditEntry(
        module_path="governance/charter.py",
        classification=LabModuleClassification.OPERATIONAL_VALUE,
        anchor_capabilities=(
            LabCharterCapability.QUEUEING,
            LabCharterCapability.HANDOFF_PACKETS,
        ),
        reason="The machine-readable charter keeps the lab package boundary explicit and reviewable.",
    ),
    LabModuleAuditEntry(
        module_path="handoffs/__init__.py",
        classification=LabModuleClassification.THIN_ABSTRACTION,
        reason="The handoffs band re-exports packet, risk, artifact, and PTM owners under one durable namespace.",
    ),
    LabModuleAuditEntry(
        module_path="handoffs/artifacts.py",
        classification=LabModuleClassification.OPERATIONAL_VALUE,
        anchor_capabilities=(LabCharterCapability.HANDOFF_PACKETS,),
        reason="Artifact compatibility and contract policy keep lab handoffs reviewable and integrity-checked.",
    ),
    LabModuleAuditEntry(
        module_path="handoffs/ptm.py",
        classification=LabModuleClassification.OPERATIONAL_VALUE,
        anchor_capabilities=(LabCharterCapability.HANDOFF_PACKETS,),
        reason="PTM-specific validation packets keep phospho follow-up risks and controls inside the lab owner package.",
    ),
    LabModuleAuditEntry(
        module_path="handoffs/transitions.py",
        classification=LabModuleClassification.OPERATIONAL_VALUE,
        anchor_capabilities=(LabCharterCapability.HANDOFF_PACKETS,),
        reason="Targeted transition review is a durable owner surface separate from later explanations and exports.",
    ),
    LabModuleAuditEntry(
        module_path="handoffs/explanations.py",
        classification=LabModuleClassification.OPERATIONAL_VALUE,
        anchor_capabilities=(LabCharterCapability.HANDOFF_PACKETS,),
        reason="Handoff explanations and refusals keep blocked operational consequences explicit instead of hiding them in export helpers.",
    ),
    LabModuleAuditEntry(
        module_path="handoffs/exports.py",
        classification=LabModuleClassification.OPERATIONAL_VALUE,
        anchor_capabilities=(LabCharterCapability.HANDOFF_PACKETS,),
        reason="LIMS export bundles and assay-plan comparisons belong to delivery ownership rather than transition review ownership.",
    ),
    LabModuleAuditEntry(
        module_path="handoffs/risk.py",
        classification=LabModuleClassification.OPERATIONAL_VALUE,
        anchor_capabilities=(
            LabCharterCapability.HANDOFF_PACKETS,
            LabCharterCapability.OBSERVED_OUTCOME_RECONCILIATION,
        ),
        reason="Assay-risk models stop weak uniqueness, localization, reproducibility, and failure-prone follow-up from hardening into operational certainty.",
    ),
    LabModuleAuditEntry(
        module_path="handoffs/serialization.py",
        classification=LabModuleClassification.OPERATIONAL_VALUE,
        anchor_capabilities=(LabCharterCapability.HANDOFF_PACKETS,),
        reason="Canonical artifact envelopes and payload diffs belong to handoff serialization ownership instead of artifact policy ownership.",
    ),
    LabModuleAuditEntry(
        module_path="lifecycle/__init__.py",
        classification=LabModuleClassification.THIN_ABSTRACTION,
        reason="The lifecycle band re-exports operational progression under the durable lifecycle namespace.",
    ),
    LabModuleAuditEntry(
        module_path="lifecycle/progression.py",
        classification=LabModuleClassification.OPERATIONAL_VALUE,
        anchor_capabilities=(LabCharterCapability.PROGRESSION,),
        reason="Lifecycle transitions govern operational progression and review state in the lab layer.",
    ),
    LabModuleAuditEntry(
        module_path="outcomes/__init__.py",
        classification=LabModuleClassification.THIN_ABSTRACTION,
        reason="The outcomes band re-exports observed execution logic under the durable outcomes namespace.",
    ),
    LabModuleAuditEntry(
        module_path="outcomes/observations.py",
        classification=LabModuleClassification.OPERATIONAL_VALUE,
        anchor_capabilities=(LabCharterCapability.OBSERVED_OUTCOME_RECONCILIATION,),
        reason="Outcome interpretation and rerun behavior are core lab feedback-loop ownership.",
    ),
    LabModuleAuditEntry(
        module_path="planning/__init__.py",
        classification=LabModuleClassification.THIN_ABSTRACTION,
        reason="The planning band re-exports executable assay planning under the durable planning namespace.",
    ),
    LabModuleAuditEntry(
        module_path="planning/assays.py",
        classification=LabModuleClassification.OPERATIONAL_VALUE,
        anchor_capabilities=(LabCharterCapability.ASSAY_PLANNING,),
        reason="Planning assay construction owns batch formation, decision briefs, dependency integrity, and executable request assembly.",
    ),
    LabModuleAuditEntry(
        module_path="planning/next_cycle.py",
        classification=LabModuleClassification.OPERATIONAL_VALUE,
        anchor_capabilities=(LabCharterCapability.PROGRESSION,),
        reason="Next-cycle planning owns contradiction resolution, orthogonal confirmation, and recommendation of the next responsible lab cycle.",
    ),
    LabModuleAuditEntry(
        module_path="planning/priorities.py",
        classification=LabModuleClassification.OPERATIONAL_VALUE,
        anchor_capabilities=(
            LabCharterCapability.ASSAY_PLANNING,
            LabCharterCapability.QUEUEING,
            LabCharterCapability.PROGRESSION,
        ),
        reason="Priority scoring owns information-gain ranking, practicality screening, and cycle-brief assembly under live operational pressure.",
    ),
    LabModuleAuditEntry(
        module_path="planning/queue.py",
        classification=LabModuleClassification.OPERATIONAL_VALUE,
        anchor_capabilities=(LabCharterCapability.QUEUEING,),
        reason="Queue contracts and queue-pressure summaries belong to planning because they decide when lab work is batchable or stale.",
    ),
    LabModuleAuditEntry(
        module_path="planning/scheduling.py",
        classification=LabModuleClassification.OPERATIONAL_VALUE,
        anchor_capabilities=(LabCharterCapability.QUEUEING,),
        reason="Scheduling owns capacity fitting, scenario comparison, and material-feasibility ordering instead of leaving them buried in assay construction.",
    ),
    LabModuleAuditEntry(
        module_path="readiness/__init__.py",
        classification=LabModuleClassification.THIN_ABSTRACTION,
        reason="The readiness band re-exports operational readiness under the durable readiness namespace.",
    ),
    LabModuleAuditEntry(
        module_path="readiness/operations.py",
        classification=LabModuleClassification.OPERATIONAL_VALUE,
        anchor_capabilities=(
            LabCharterCapability.QUEUEING,
            LabCharterCapability.PROGRESSION,
        ),
        reason="Operational readiness turns cost, staffing, backlog, and reagent pressure into explicit execution state.",
    ),
    LabModuleAuditEntry(
        module_path="reconciliation/__init__.py",
        classification=LabModuleClassification.THIN_ABSTRACTION,
        reason="The reconciliation band re-exports follow-up owners under the durable reconciliation namespace.",
    ),
    LabModuleAuditEntry(
        module_path="reconciliation/flagship_follow_up.py",
        classification=LabModuleClassification.OPERATIONAL_VALUE,
        anchor_capabilities=(LabCharterCapability.OBSERVED_OUTCOME_RECONCILIATION,),
        reason="Canonical follow-up packets keep cross-package outcome consequences explicit instead of letting them dissolve into generic summaries.",
    ),
    LabModuleAuditEntry(
        module_path="reconciliation/follow_up.py",
        classification=LabModuleClassification.OPERATIONAL_VALUE,
        anchor_capabilities=(LabCharterCapability.OBSERVED_OUTCOME_RECONCILIATION,),
        reason="Planned-versus-observed reconciliation converts assay outcomes into honest downstream feedback instead of implicit optimism.",
    ),
    LabModuleAuditEntry(
        module_path="outcomes/feedback.py",
        classification=LabModuleClassification.OPERATIONAL_VALUE,
        anchor_capabilities=(LabCharterCapability.OBSERVED_OUTCOME_RECONCILIATION,),
        reason="Feedback records and feedback analytics belong to outcomes because they convert observed work back into auditable downstream posture.",
    ),
    LabModuleAuditEntry(
        module_path="readiness/stages.py",
        classification=LabModuleClassification.OPERATIONAL_VALUE,
        anchor_capabilities=(
            LabCharterCapability.QUEUEING,
            LabCharterCapability.PROGRESSION,
        ),
        reason="Stage-readiness summaries keep missing assays, review gates, and execution blockers visible before scheduling.",
    ),
)


__all__ = [
    "DEFAULT_LAB_CHARTER",
    "DEFAULT_LAB_MODULE_AUDIT",
    "LabCharterCapability",
    "LabCharterEntry",
    "LabModuleAuditEntry",
    "LabModuleClassification",
]
