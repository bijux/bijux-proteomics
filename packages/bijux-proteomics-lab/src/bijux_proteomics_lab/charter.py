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
        required_modules=("planning.py", "design.py", "protocols.py"),
        release_blocker="Lab cannot ship if assay work remains a packet shell without concrete planning behavior.",
    ),
    LabCharterEntry(
        capability=LabCharterCapability.QUEUEING,
        owned_surface="Queue-aware execution planning that respects capacity, backlog, and review-gate pressure.",
        required_modules=("planning.py", "readiness.py", "repositories.py"),
        release_blocker="Lab cannot ship if queue and capacity handling disappear into downstream ad hoc logic.",
    ),
    LabCharterEntry(
        capability=LabCharterCapability.PROGRESSION,
        owned_surface="Operational progression and review transitions grounded in lab-ready state rather than recommendation-only ranking.",
        required_modules=("lifecycle.py", "planning.py", "readiness.py"),
        release_blocker="Lab cannot ship if progression decisions ignore operational readiness or unresolved execution blockers.",
    ),
    LabCharterEntry(
        capability=LabCharterCapability.HANDOFF_PACKETS,
        owned_surface="Reviewable handoff packets that preserve protocol controls, caveats, and artifact integrity.",
        required_modules=("protocols.py", "artifacts.py", "planning.py", "handoffs.py"),
        release_blocker="Lab cannot ship if handoff packets lose protocol controls, caveats, or artifact integrity.",
    ),
    LabCharterEntry(
        capability=LabCharterCapability.OBSERVED_OUTCOME_RECONCILIATION,
        owned_surface="Observed-outcome interpretation that feeds back into reruns, evidence promotion, and future cycles.",
        required_modules=("outcomes.py", "repositories.py", "readiness.py", "risk.py"),
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
        module_path="artifacts.py",
        classification=LabModuleClassification.OPERATIONAL_VALUE,
        anchor_capabilities=(LabCharterCapability.HANDOFF_PACKETS,),
        reason="Artifact envelopes and contracts keep lab handoffs reviewable and integrity-checked.",
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
        module_path="design.py",
        classification=LabModuleClassification.OPERATIONAL_VALUE,
        anchor_capabilities=(
            LabCharterCapability.ASSAY_PLANNING,
            LabCharterCapability.HANDOFF_PACKETS,
        ),
        reason="Experiment-design validation and layout planning are executable lab-operations behavior.",
    ),
    LabModuleAuditEntry(
        module_path="handoffs.py",
        classification=LabModuleClassification.OPERATIONAL_VALUE,
        anchor_capabilities=(LabCharterCapability.HANDOFF_PACKETS,),
        reason="Targeted transition review and handoff-specific decision surfaces keep lab exports grounded in operational responsibility.",
    ),
    LabModuleAuditEntry(
        module_path="lifecycle.py",
        classification=LabModuleClassification.OPERATIONAL_VALUE,
        anchor_capabilities=(LabCharterCapability.PROGRESSION,),
        reason="Lifecycle transitions govern operational progression and review state in the lab layer.",
    ),
    LabModuleAuditEntry(
        module_path="outcomes.py",
        classification=LabModuleClassification.OPERATIONAL_VALUE,
        anchor_capabilities=(LabCharterCapability.OBSERVED_OUTCOME_RECONCILIATION,),
        reason="Outcome interpretation and rerun behavior are core lab feedback-loop ownership.",
    ),
    LabModuleAuditEntry(
        module_path="planning.py",
        classification=LabModuleClassification.OPERATIONAL_VALUE,
        anchor_capabilities=(
            LabCharterCapability.ASSAY_PLANNING,
            LabCharterCapability.QUEUEING,
            LabCharterCapability.PROGRESSION,
        ),
        reason="Planning owns batching, scheduling, and assay-level operational tradeoffs.",
    ),
    LabModuleAuditEntry(
        module_path="protocols.py",
        classification=LabModuleClassification.OPERATIONAL_VALUE,
        anchor_capabilities=(
            LabCharterCapability.ASSAY_PLANNING,
            LabCharterCapability.HANDOFF_PACKETS,
        ),
        reason="Protocol attachments keep controls, versions, and caveats attached to lab handoffs.",
    ),
    LabModuleAuditEntry(
        module_path="readiness.py",
        classification=LabModuleClassification.OPERATIONAL_VALUE,
        anchor_capabilities=(
            LabCharterCapability.QUEUEING,
            LabCharterCapability.PROGRESSION,
        ),
        reason="Operational readiness turns cost, staffing, backlog, and reagent pressure into explicit execution state.",
    ),
    LabModuleAuditEntry(
        module_path="risk.py",
        classification=LabModuleClassification.OPERATIONAL_VALUE,
        anchor_capabilities=(
            LabCharterCapability.HANDOFF_PACKETS,
            LabCharterCapability.OBSERVED_OUTCOME_RECONCILIATION,
        ),
        reason="Assay-risk models stop weak uniqueness, localization, reproducibility, and failure-prone follow-up from hardening into operational certainty.",
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
        module_path="workflow_readiness.py",
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
