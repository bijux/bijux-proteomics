# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Machine-readable charter for the runtime execution product boundary."""

from __future__ import annotations

from enum import StrEnum
from pathlib import Path

from pydantic import ConfigDict, Field

from bijux_proteomics_foundation import JsonModel


class RuntimeCharterCapability(StrEnum):
    """Execution capabilities that justify the runtime package boundary."""

    CANONICAL_ENTRYPOINTS = "canonical_entrypoints"
    PROVIDER_BINDING = "provider_binding"
    WORKFLOW_EXECUTION = "workflow_execution"
    REPLAY_AND_RECOVERY = "replay_and_recovery"
    REVIEWABLE_OUTPUTS = "reviewable_outputs"


class RuntimeModuleClassification(StrEnum):
    """Allowed audit outcomes for runtime source modules."""

    EXECUTION_VALUE = "execution_value"
    THIN_ABSTRACTION = "thin_abstraction"
    GENERIC_INFRASTRUCTURE = "generic_infrastructure"
    WRONG_PACKAGE_LOGIC = "wrong_package_logic"
    DEAD_WEIGHT = "dead_weight"


class RuntimeProductCharter(JsonModel):
    """Durable execution-product charter for runtime ownership."""

    model_config = ConfigDict(extra="forbid")

    package_name: str = Field(..., min_length=1)
    value_statement: str = Field(..., min_length=1)
    capabilities: tuple[RuntimeCharterCapability, ...] = Field(default_factory=tuple)
    required_inputs: tuple[str, ...] = Field(default_factory=tuple)
    excluded_ownership: tuple[str, ...] = Field(default_factory=tuple)


class RuntimeCharterEntry(JsonModel):
    """One durable capability owned by the runtime package."""

    model_config = ConfigDict(extra="forbid")

    capability: RuntimeCharterCapability
    owned_surface: str = Field(..., min_length=1)
    required_modules: tuple[str, ...] = Field(..., min_length=1)
    release_blocker: str = Field(..., min_length=1)


class RuntimeModuleAuditEntry(JsonModel):
    """Audit record for one runtime source module."""

    model_config = ConfigDict(extra="forbid")

    module_path: str = Field(..., min_length=1)
    classification: RuntimeModuleClassification
    anchor_capabilities: tuple[RuntimeCharterCapability, ...] = Field(
        default_factory=tuple
    )
    reason: str = Field(..., min_length=1)


DEFAULT_RUNTIME_CHARTER = RuntimeProductCharter(
    package_name="bijux-proteomics-runtime",
    value_statement=(
        "execute proteomics workflows through canonical operator entrypoints, "
        "provider binding, replay-safe artifacts, and reviewable run outputs "
        "without taking over scientific models, curation, analytical judgment, "
        "or laboratory operations"
    ),
    capabilities=(
        RuntimeCharterCapability.CANONICAL_ENTRYPOINTS,
        RuntimeCharterCapability.PROVIDER_BINDING,
        RuntimeCharterCapability.WORKFLOW_EXECUTION,
        RuntimeCharterCapability.REPLAY_AND_RECOVERY,
        RuntimeCharterCapability.REVIEWABLE_OUTPUTS,
    ),
    required_inputs=(
        "core-owned scientific contracts and execution requests",
        "knowledge-owned evidence and benchmark references",
        "intelligence-owned recommendation and decision briefs",
        "lab-owned operational readiness and assay handoff surfaces",
    ),
    excluded_ownership=(
        "scientific normalization and domain schema ownership",
        "reference curation and ontology maintenance",
        "analytical prioritization and recommendation judgment",
        "laboratory queueing, protocol control, and observed-outcome authority",
    ),
)


DEFAULT_RUNTIME_CHARTER_ENTRIES: tuple[RuntimeCharterEntry, ...] = (
    RuntimeCharterEntry(
        capability=RuntimeCharterCapability.CANONICAL_ENTRYPOINTS,
        owned_surface="Canonical CLI and HTTP entrypoints that start, inspect, compare, import, and resume runtime-controlled execution.",
        required_modules=(
            "api/cli.py",
            "api/app.py",
            "api/v1/endpoints/run.py",
            "runs/operations.py",
        ),
        release_blocker="Runtime cannot ship if operators must bypass canonical CLI or HTTP surfaces to trigger supported execution paths.",
    ),
    RuntimeCharterEntry(
        capability=RuntimeCharterCapability.PROVIDER_BINDING,
        owned_surface="Provider selection, dependency gates, execution-mode checks, and capability metadata for runtime-owned execution backends.",
        required_modules=(
            "providers/catalog.py",
            "providers/selection.py",
            "providers/contracts.py",
            "providers/capabilities.py",
        ),
        release_blocker="Runtime cannot ship if provider dependency and capability rules fragment across compat or downstream packages.",
    ),
    RuntimeCharterEntry(
        capability=RuntimeCharterCapability.WORKFLOW_EXECUTION,
        owned_surface="Execution coordination that turns runtime requests into tool, provider, and agent work over proteomics workflows.",
        required_modules=(
            "parallel/execution.py",
            "streaming/execution.py",
            "runs/manager.py",
            "execution/agents/coordination/coordinator.py",
            "execution/engine/executor.py",
        ),
        release_blocker="Runtime cannot ship if workflow execution collapses into wrapper-only glue without runtime-owned coordination logic.",
    ),
    RuntimeCharterEntry(
        capability=RuntimeCharterCapability.REPLAY_AND_RECOVERY,
        owned_surface="Replay-safe bundles, checkpoints, cache claims, rerun planning, cleanup, and recovery behavior that preserve trustworthy run reuse.",
        required_modules=(
            "resume/execution.py",
            "runs/replay.py",
            "runs/reruns.py",
            "runs/integrity.py",
            "runs/recovery.py",
            "support/workspace.py",
        ),
        release_blocker="Runtime cannot ship if reruns, replay, or recovery depend on ad hoc operator behavior instead of typed runtime control.",
    ),
    RuntimeCharterEntry(
        capability=RuntimeCharterCapability.REVIEWABLE_OUTPUTS,
        owned_surface="Typed run contracts, decision briefs, artifact inventories, histories, and failure reports that downstream packages can consume without private file coupling.",
        required_modules=(
            "artifacts/steps.py",
            "api/catalog.py",
            "runs/contracts.py",
            "runs/launch_bundles.py",
            "runs/failure_reports.py",
            "workflows/paths.py",
        ),
        release_blocker="Runtime cannot ship if operators or downstream packages lose stable reviewable run outputs and fall back to private workspace parsing.",
    ),
)


def _runtime_source_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _execution_value_entry(
    module_path: str,
    capabilities: tuple[RuntimeCharterCapability, ...],
    reason: str,
) -> RuntimeModuleAuditEntry:
    return RuntimeModuleAuditEntry(
        module_path=module_path,
        classification=RuntimeModuleClassification.EXECUTION_VALUE,
        anchor_capabilities=capabilities,
        reason=reason,
    )


def _classify_runtime_module(module_path: str) -> RuntimeModuleAuditEntry:
    if module_path == "__init__.py":
        return RuntimeModuleAuditEntry(
            module_path=module_path,
            classification=RuntimeModuleClassification.THIN_ABSTRACTION,
            reason="The package root is an export surface over canonical runtime entrypoints.",
        )

    if module_path.endswith("/__init__.py"):
        return RuntimeModuleAuditEntry(
            module_path=module_path,
            classification=RuntimeModuleClassification.THIN_ABSTRACTION,
            reason="Namespace package initializers only aggregate stable runtime-owned sub-surfaces.",
        )

    if module_path.startswith("api/") or module_path == "support/identity.py":
        return _execution_value_entry(
            module_path,
            (
                RuntimeCharterCapability.CANONICAL_ENTRYPOINTS,
                RuntimeCharterCapability.REVIEWABLE_OUTPUTS,
            ),
            "Operator-facing entrypoints and envelopes belong in runtime because they define the supported execution and review surface.",
        )

    if module_path.startswith("artifacts/"):
        return _execution_value_entry(
            module_path,
            (
                RuntimeCharterCapability.REPLAY_AND_RECOVERY,
                RuntimeCharterCapability.REVIEWABLE_OUTPUTS,
            ),
            "Typed workflow-step artifact contracts keep replay-safe checksums and reviewable step outputs under one explicit runtime owner.",
        )

    if module_path.startswith("parallel/"):
        return _execution_value_entry(
            module_path,
            (
                RuntimeCharterCapability.WORKFLOW_EXECUTION,
                RuntimeCharterCapability.REVIEWABLE_OUTPUTS,
            ),
            "Deterministic parallel execution belongs in runtime because it schedules workflow-safe concurrent work while preserving reviewable byte-stable outputs.",
        )

    if module_path.startswith("streaming/"):
        return _execution_value_entry(
            module_path,
            (
                RuntimeCharterCapability.WORKFLOW_EXECUTION,
                RuntimeCharterCapability.REVIEWABLE_OUTPUTS,
            ),
            "Large-input streaming import belongs in runtime because it governs bounded-memory execution over accepted import records without changing eager subset outcomes.",
        )

    if module_path.startswith("resume/"):
        return _execution_value_entry(
            module_path,
            (
                RuntimeCharterCapability.REPLAY_AND_RECOVERY,
                RuntimeCharterCapability.REVIEWABLE_OUTPUTS,
            ),
            "Artifact-valid workflow resume planning belongs in runtime because it decides which completed steps stay trustworthy under changed inputs and config.",
        )

    if module_path.startswith("providers/"):
        return _execution_value_entry(
            module_path,
            (RuntimeCharterCapability.PROVIDER_BINDING,),
            "Provider cataloging, construction, dependency checks, and capability metadata are canonical runtime ownership.",
        )

    if module_path == "runs/operations.py":
        return _execution_value_entry(
            module_path,
            (
                RuntimeCharterCapability.CANONICAL_ENTRYPOINTS,
                RuntimeCharterCapability.WORKFLOW_EXECUTION,
            ),
            "Run operations keep CLI and API entrypoints pinned to one canonical execution owner.",
        )

    if module_path == "runs/manager.py":
        return _execution_value_entry(
            module_path,
            (RuntimeCharterCapability.WORKFLOW_EXECUTION,),
            "The run manager owns canonical execution coordination over providers, agents, and runtime artifacts.",
        )

    if module_path.startswith("runs/"):
        return _execution_value_entry(
            module_path,
            (
                RuntimeCharterCapability.REPLAY_AND_RECOVERY,
                RuntimeCharterCapability.REVIEWABLE_OUTPUTS,
            ),
            "Run-owned contracts keep execution context, replay metadata, and reviewable outputs under one stable owner family.",
        )

    if module_path.startswith("workflows/"):
        return _execution_value_entry(
            module_path,
            (
                RuntimeCharterCapability.WORKFLOW_EXECUTION,
                RuntimeCharterCapability.REVIEWABLE_OUTPUTS,
            ),
            "Workflow-owned planning, reproducibility, and run reports stay grouped under one navigable runtime family.",
        )

    if module_path == "governance/charter.py":
        return _execution_value_entry(
            module_path,
            (
                RuntimeCharterCapability.CANONICAL_ENTRYPOINTS,
                RuntimeCharterCapability.REVIEWABLE_OUTPUTS,
            ),
            "The machine-readable charter keeps runtime ownership explicit, auditable, and release-blocking.",
        )

    if module_path == "governance/compatibility_bridges.py":
        return _execution_value_entry(
            module_path,
            (
                RuntimeCharterCapability.CANONICAL_ENTRYPOINTS,
                RuntimeCharterCapability.REVIEWABLE_OUTPUTS,
            ),
            "The compatibility-bridge contract keeps legacy runtime entrypoints, import routing, and retirement budgets explicit under one release-blocking owner surface.",
        )

    if module_path.startswith(("execution/agents/", "execution/")):
        return _execution_value_entry(
            module_path,
            (RuntimeCharterCapability.WORKFLOW_EXECUTION,),
            "Agent, execution-graph, and tool coordination code gives runtime real execution substance instead of wrapper-only transport.",
        )

    if module_path.startswith("state/"):
        return _execution_value_entry(
            module_path,
            (
                RuntimeCharterCapability.REPLAY_AND_RECOVERY,
                RuntimeCharterCapability.REVIEWABLE_OUTPUTS,
            ),
            "Typed memory and state artifacts preserve replay-safe execution history and reviewable downstream consumption.",
        )

    if module_path in {
        "support/artifact_formats.py",
        "support/workspace.py",
    }:
        return _execution_value_entry(
            module_path,
            (
                RuntimeCharterCapability.REPLAY_AND_RECOVERY,
                RuntimeCharterCapability.REVIEWABLE_OUTPUTS,
            ),
            "Typed run context, workspace, and contract code keep runtime execution reproducible, inspectable, and exportable.",
        )

    if module_path.startswith("support/primitives/"):
        return _execution_value_entry(
            module_path,
            (
                RuntimeCharterCapability.WORKFLOW_EXECUTION,
                RuntimeCharterCapability.REVIEWABLE_OUTPUTS,
            ),
            "Runtime execution primitives define stable semantics, status surfaces, and review-facing invariants for the package.",
        )

    raise ValueError(f"unclassified runtime module path: {module_path}")


def _build_runtime_module_audit() -> tuple[RuntimeModuleAuditEntry, ...]:
    source_root = _runtime_source_root()
    module_paths = sorted(
        path.relative_to(source_root).as_posix() for path in source_root.rglob("*.py")
    )
    return tuple(_classify_runtime_module(module_path) for module_path in module_paths)


DEFAULT_RUNTIME_MODULE_AUDIT = _build_runtime_module_audit()


def list_runtime_capabilities() -> tuple[RuntimeCharterCapability, ...]:
    """Return the exact execution capabilities runtime is allowed to own."""
    return DEFAULT_RUNTIME_CHARTER.capabilities


def list_runtime_charter_entries() -> tuple[RuntimeCharterEntry, ...]:
    """Return the exact capability charter entries runtime must satisfy."""
    return DEFAULT_RUNTIME_CHARTER_ENTRIES


__all__ = [
    "DEFAULT_RUNTIME_CHARTER",
    "DEFAULT_RUNTIME_CHARTER_ENTRIES",
    "DEFAULT_RUNTIME_MODULE_AUDIT",
    "RuntimeCharterCapability",
    "RuntimeCharterEntry",
    "RuntimeModuleAuditEntry",
    "RuntimeModuleClassification",
    "RuntimeProductCharter",
    "list_runtime_capabilities",
    "list_runtime_charter_entries",
]
