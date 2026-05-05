# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Replay contracts and local run bundles for runtime execution."""

from __future__ import annotations

from typing import Any

from pydantic import ConfigDict, Field

from bijux_proteomics_foundation import JsonModel, hash_payload
from bijux_proteomics_runtime.runtime.context import RunContextContract
from bijux_proteomics_runtime.runtime.control.integrity import (
    require_reusable_artifact_bundle,
)
from bijux_proteomics_runtime.runtime.control.ledger import RuntimeArtifactLedger
from bijux_proteomics_runtime.runtime.workspace import RunWorkspace, write_json_atomic


class ReplayContract(JsonModel):
    """Typed replay contract built from real runtime dependency fingerprints."""

    model_config = ConfigDict(extra="forbid")

    run_id: str = Field(..., min_length=1)
    workflow_id: str = Field(..., min_length=1)
    input_fingerprint: str = Field(..., min_length=1)
    parameter_fingerprint: str = Field(..., min_length=1)
    tool_fingerprint: str = Field(..., min_length=1)
    code_expectation_fingerprint: str = Field(..., min_length=1)
    artifact_policy_fingerprint: str = Field(..., min_length=1)


class ReplayEligibility(JsonModel):
    """Replay decision with explicit invalidation reasons."""

    model_config = ConfigDict(extra="forbid")

    eligible: bool
    invalidation_reasons: tuple[str, ...] = Field(default_factory=tuple)
    notes: tuple[str, ...] = Field(default_factory=tuple)


class LocalRunBundle(JsonModel):
    """Offline-auditable local run bundle."""

    model_config = ConfigDict(extra="forbid")

    run_context: RunContextContract
    replay_contract: ReplayContract
    artifact_ledger: RuntimeArtifactLedger
    run_summary: dict[str, Any] = Field(default_factory=dict)
    failure_report: dict[str, Any] | None = Field(default=None)


def build_replay_contract(
    run_context: RunContextContract,
    *,
    app_version: str,
    git_commit: str,
    tool_versions: dict[str, str],
) -> ReplayContract:
    """Build a replay contract from real run fingerprints."""
    parameter_fingerprint = hash_payload(
        {
            "config_fingerprint": run_context.config_fingerprint,
            "provider_name": run_context.provider_name,
            "workflow_family": run_context.workflow.workflow_family,
        }
    )
    tool_fingerprint = hash_payload(
        {
            "provider_name": run_context.provider_name,
            "tool_versions": tool_versions,
        }
    )
    code_expectation_fingerprint = hash_payload(
        {
            "app_version": app_version,
            "git_commit": git_commit,
            "workflow_family": run_context.workflow.workflow_family,
        }
    )
    artifact_policy_fingerprint = hash_payload(run_context.artifact_policy.to_dict())
    return ReplayContract(
        run_id=run_context.run_id,
        workflow_id=run_context.workflow.workflow_id,
        input_fingerprint=run_context.dataset.dataset_fingerprint,
        parameter_fingerprint=parameter_fingerprint,
        tool_fingerprint=tool_fingerprint,
        code_expectation_fingerprint=code_expectation_fingerprint,
        artifact_policy_fingerprint=artifact_policy_fingerprint,
    )


def evaluate_replay_eligibility(
    expected: ReplayContract,
    current: ReplayContract,
) -> ReplayEligibility:
    """Evaluate replay safety with explicit cache invalidation reasons."""
    reasons: list[str] = []
    notes: list[str] = []
    if expected.input_fingerprint != current.input_fingerprint:
        reasons.append("input_changed")
    if expected.parameter_fingerprint != current.parameter_fingerprint:
        reasons.append("parameters_changed")
    if expected.tool_fingerprint != current.tool_fingerprint:
        reasons.append("tools_changed")
    if expected.code_expectation_fingerprint != current.code_expectation_fingerprint:
        reasons.append("code_expectations_changed")
    if expected.artifact_policy_fingerprint != current.artifact_policy_fingerprint:
        reasons.append("artifact_policy_changed")
    if not reasons:
        notes.append("runtime dependency fingerprints still match")
    return ReplayEligibility(
        eligible=not reasons,
        invalidation_reasons=tuple(reasons),
        notes=tuple(notes),
    )


def build_local_run_bundle(
    *,
    run_context: RunContextContract,
    replay_contract: ReplayContract,
    artifact_ledger: RuntimeArtifactLedger,
    run_summary: dict[str, Any],
    failure_report: dict[str, Any] | None = None,
) -> LocalRunBundle:
    """Build one offline-auditable local run bundle."""
    return LocalRunBundle(
        run_context=run_context,
        replay_contract=replay_contract,
        artifact_ledger=artifact_ledger,
        run_summary=run_summary,
        failure_report=failure_report,
    )


def write_replay_contract(workspace: RunWorkspace, contract: ReplayContract) -> None:
    """Write the replay contract to disk."""
    write_json_atomic(workspace.replay_contract_path, contract.to_dict())


def write_local_run_bundle(workspace: RunWorkspace, bundle: LocalRunBundle) -> None:
    """Write the local run bundle to disk."""
    write_json_atomic(workspace.local_run_bundle_path, bundle.to_dict())


def load_local_run_bundle(workspace: RunWorkspace) -> LocalRunBundle:
    """Load the local run bundle from disk."""
    require_reusable_artifact_bundle(
        workspace,
        run_id=workspace.run_id,
        max_artifact_bytes=1_000_000,
        required_artifact_kinds=("runtime-local-run-bundle", "runtime-replay-contract"),
    )
    return LocalRunBundle.load_json(workspace.local_run_bundle_path)


__all__ = [
    "LocalRunBundle",
    "ReplayContract",
    "ReplayEligibility",
    "build_local_run_bundle",
    "build_replay_contract",
    "evaluate_replay_eligibility",
    "load_local_run_bundle",
    "write_local_run_bundle",
    "write_replay_contract",
]
