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
            "design/experiments.py",
            "design/protocols.py",
        ),
        release_blocker="Lab cannot ship if assay work remains a packet shell without concrete planning behavior.",
    ),
    LabCharterEntry(
        capability=LabCharterCapability.QUEUEING,
        owned_surface="Queue-aware execution planning that respects capacity, backlog, and review-gate pressure.",
        required_modules=(
            "planning/assays.py",
            "readiness/operations.py",
            "repositories.py",
        ),
        release_blocker="Lab cannot ship if queue and capacity handling disappear into downstream ad hoc logic.",
    ),
    LabCharterEntry(
        capability=LabCharterCapability.PROGRESSION,
        owned_surface="Operational progression and review transitions grounded in lab-ready state rather than recommendation-only ranking.",
        required_modules=(
            "lifecycle/progression.py",
            "planning/assays.py",
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
            "handoffs/transitions.py",
            "handoffs/explanations.py",
            "handoffs/exports.py",
            "handoffs/ptm.py",
            "handoffs/risk.py",
            "benchmarks/targeted.py",
        ),
        release_blocker="Lab cannot ship if handoff packets lose protocol controls, caveats, or artifact integrity.",
    ),
    LabCharterEntry(
        capability=LabCharterCapability.OBSERVED_OUTCOME_RECONCILIATION,
        owned_surface="Observed-outcome interpretation that feeds back into reruns, evidence promotion, and future cycles.",
        required_modules=(
            "outcomes/observations.py",
            "repositories.py",
            "readiness/operations.py",
            "handoffs/risk.py",
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
        module_path="artifacts.py",
        classification=LabModuleClassification.THIN_ABSTRACTION,
        reason="The flat artifacts import path is kept only as a compatibility facade over handoff-owned artifact contracts.",
    ),
    LabModuleAuditEntry(
        module_path="benchmarks/__init__.py",
        classification=LabModuleClassification.THIN_ABSTRACTION,
        reason="The benchmarks band re-exports benchmark rehearsal owners under the durable benchmarks namespace.",
    ),
    LabModuleAuditEntry(
        module_path="benchmarks/targeted.py",
        classification=LabModuleClassification.OPERATIONAL_VALUE,
        anchor_capabilities=(
            LabCharterCapability.HANDOFF_PACKETS,
            LabCharterCapability.OBSERVED_OUTCOME_RECONCILIATION,
        ),
        reason="Targeted benchmark reports prove that discovery evidence can become reviewable operator handoff outputs without hiding support limits.",
    ),
    LabModuleAuditEntry(
        module_path="charter.py",
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
        reason="Artifact envelopes and contracts keep lab handoffs reviewable and integrity-checked.",
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
        module_path="handoffs/packets.py",
        classification=LabModuleClassification.THIN_ABSTRACTION,
        reason="The historical handoff packet import path now remains only as a compatibility facade over narrower handoff owners.",
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
        anchor_capabilities=(
            LabCharterCapability.ASSAY_PLANNING,
            LabCharterCapability.QUEUEING,
            LabCharterCapability.PROGRESSION,
        ),
        reason="Planning owns batching, scheduling, and assay-level operational tradeoffs.",
    ),
    LabModuleAuditEntry(
        module_path="ptm_follow_up.py",
        classification=LabModuleClassification.THIN_ABSTRACTION,
        reason="The flat PTM follow-up import path is kept only as a compatibility facade over the handoff-owned PTM packet builder.",
    ),
    LabModuleAuditEntry(
        module_path="protocols.py",
        classification=LabModuleClassification.THIN_ABSTRACTION,
        reason="The flat protocols import path is kept only as a compatibility facade over design-owned protocol helpers.",
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
        module_path="risk.py",
        classification=LabModuleClassification.THIN_ABSTRACTION,
        reason="The flat risk import path is kept only as a compatibility facade over handoff-owned assay-risk scoring.",
    ),
    LabModuleAuditEntry(
        module_path="reconciliation/__init__.py",
        classification=LabModuleClassification.THIN_ABSTRACTION,
        reason="The reconciliation band re-exports follow-up owners under the durable reconciliation namespace.",
    ),
    LabModuleAuditEntry(
        module_path="reconciliation/follow_up.py",
        classification=LabModuleClassification.OPERATIONAL_VALUE,
        anchor_capabilities=(LabCharterCapability.OBSERVED_OUTCOME_RECONCILIATION,),
        reason="Planned-versus-observed reconciliation converts assay outcomes into honest downstream feedback instead of implicit optimism.",
    ),
    LabModuleAuditEntry(
        module_path="repositories.py",
        classification=LabModuleClassification.OPERATIONAL_VALUE,
        anchor_capabilities=(
            LabCharterCapability.QUEUEING,
            LabCharterCapability.OBSERVED_OUTCOME_RECONCILIATION,
        ),
        reason="Feedback and review-queue records are the typed persistence boundary for lab operations.",
    ),
    LabModuleAuditEntry(
        module_path="targeted_benchmarking.py",
        classification=LabModuleClassification.THIN_ABSTRACTION,
        reason="The flat targeted-benchmarking import path is kept only as a compatibility facade over the benchmark rehearsal owner module.",
    ),
    LabModuleAuditEntry(
        module_path="workflow_readiness.py",
        classification=LabModuleClassification.THIN_ABSTRACTION,
        reason="The flat workflow-readiness import path is kept only as a compatibility facade over readiness-owned workflow checks.",
    ),
    LabModuleAuditEntry(
        module_path="readiness/workflow.py",
        classification=LabModuleClassification.OPERATIONAL_VALUE,
        anchor_capabilities=(
            LabCharterCapability.QUEUEING,
            LabCharterCapability.PROGRESSION,
        ),
        reason="Workflow readiness summaries keep missing assays, review gates, and execution blockers visible before scheduling.",
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
