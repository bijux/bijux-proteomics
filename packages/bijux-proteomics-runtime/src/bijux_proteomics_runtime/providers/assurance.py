# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Machine-readable provider assurance surfaces for runtime validation."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from bijux_proteomics_runtime.providers.capabilities import KNOWN_PROVIDERS
from bijux_proteomics_runtime.providers.catalog import (
    PROVIDER_CAPABILITIES,
    PROVIDER_EXECUTION_CONTRACTS,
    provider_metadata,
    provider_requirements,
)


class ProviderRealityTier(StrEnum):
    """How directly one provider lane is proven in this repository."""

    CPU_SAFE_CONFORMANCE = "cpu_safe_conformance"
    REAL_LOCAL_VALIDATION = "real_local_validation"
    REAL_REMOTE_VALIDATION = "real_remote_validation"


@dataclass(frozen=True)
class ProviderValidationLane:
    """One governed validation lane for a provider surface."""

    lane_id: str
    provider_name: str
    reality_tier: ProviderRealityTier
    execution_mode: str
    repo_relative_fixture_paths: tuple[str, ...]
    expected_artifact_paths: tuple[str, ...]
    validating_test_paths: tuple[str, ...]
    command_hint: str
    notes: tuple[str, ...] = ()


@dataclass(frozen=True)
class ProviderCapabilityMatrixRow:
    """Runtime-facing provider capability and assurance summary."""

    provider_name: str
    experimental: bool
    supports_cpu: bool
    supports_gpu: bool
    cpu_fallback_allowed: bool
    cooperative_cancellation: bool
    expected_error_codes: tuple[str, ...]
    required_raw_keys: tuple[str, ...]
    validation_lane_ids: tuple[str, ...]
    unmet_requirements: tuple[str, ...]


@dataclass(frozen=True)
class ProviderExecutionRealityRow:
    """Explicit reality posture for one provider execution story."""

    provider_name: str
    reality_tiers: tuple[ProviderRealityTier, ...]
    simulation_only: bool
    notes: tuple[str, ...]


def provider_validation_lanes() -> tuple[ProviderValidationLane, ...]:
    """Return the governed provider validation lanes."""

    lanes = (
        ProviderValidationLane(
            lane_id="heuristic_cpu_conformance",
            provider_name="heuristic_proxy",
            reality_tier=ProviderRealityTier.CPU_SAFE_CONFORMANCE,
            execution_mode="cpu",
            repo_relative_fixture_paths=(
                "packages/bijux-proteomics-runtime/tests/fixtures/providers/cpu_safe_conformance_sequence.fasta",
            ),
            expected_artifact_paths=("predicted.pdb",),
            validating_test_paths=(
                "packages/bijux-proteomics-runtime/tests/providers/test_provider_assurance_matrix.py",
            ),
            command_hint="provider assurance lane is exercised by focused runtime provider tests",
            notes=(
                "CPU-safe conformance lane exists so hardware scarcity does not erase core provider proof.",
            ),
        ),
        ProviderValidationLane(
            lane_id="esmfold_cpu_conformance",
            provider_name="local_esmfold",
            reality_tier=ProviderRealityTier.CPU_SAFE_CONFORMANCE,
            execution_mode="cpu",
            repo_relative_fixture_paths=(
                "packages/bijux-proteomics-runtime/tests/fixtures/providers/cpu_safe_conformance_sequence.fasta",
            ),
            expected_artifact_paths=("predicted.pdb", "report.json"),
            validating_test_paths=(
                "packages/agentic-proteins/tests/providers/local_models/test_local_model_contracts.py",
            ),
            command_hint="agentic-proteins local model contracts verify CPU fallback with real fixtures when dependencies are present",
            notes=(
                "This lane remains dependency-gated, but the CPU path is governed explicitly.",
            ),
        ),
        ProviderValidationLane(
            lane_id="esmfold_real_local",
            provider_name="local_esmfold",
            reality_tier=ProviderRealityTier.REAL_LOCAL_VALIDATION,
            execution_mode="cpu",
            repo_relative_fixture_paths=(
                "packages/bijux-proteomics-runtime/tests/fixtures/providers/real_local_validation_sequence.fasta",
            ),
            expected_artifact_paths=("predicted.pdb", "report.json"),
            validating_test_paths=(
                "packages/agentic-proteins/tests/providers/local_models/test_local_model_contracts.py",
            ),
            command_hint="agentic-proteins real local provider contracts run artifact-backed validation when local weights are installed",
        ),
        ProviderValidationLane(
            lane_id="rosettafold_real_local",
            provider_name="local_rosettafold",
            reality_tier=ProviderRealityTier.REAL_LOCAL_VALIDATION,
            execution_mode="gpu",
            repo_relative_fixture_paths=(
                "packages/bijux-proteomics-runtime/tests/fixtures/providers/real_local_validation_sequence.fasta",
            ),
            expected_artifact_paths=("predicted.pdb", "report.json"),
            validating_test_paths=(
                "packages/agentic-proteins/tests/providers/local_models/test_local_model_contracts.py",
            ),
            command_hint="agentic-proteins local model contracts run GPU-backed validation when RosettaFold weights are installed",
        ),
        ProviderValidationLane(
            lane_id="colabfold_real_remote",
            provider_name="api_colabfold",
            reality_tier=ProviderRealityTier.REAL_REMOTE_VALIDATION,
            execution_mode="remote",
            repo_relative_fixture_paths=(
                "packages/bijux-proteomics-runtime/tests/fixtures/providers/remote_validation_request.json",
            ),
            expected_artifact_paths=("predicted.pdb",),
            validating_test_paths=(
                "packages/agentic-proteins/tests/providers/test_remote_providers.py",
            ),
            command_hint="agentic-proteins remote provider contracts execute this lane when API dependencies and credentials are available",
        ),
        ProviderValidationLane(
            lane_id="openprotein_esmfold_real_remote",
            provider_name="api_openprotein_esmfold",
            reality_tier=ProviderRealityTier.REAL_REMOTE_VALIDATION,
            execution_mode="remote",
            repo_relative_fixture_paths=(
                "packages/bijux-proteomics-runtime/tests/fixtures/providers/remote_validation_request.json",
            ),
            expected_artifact_paths=("predicted.pdb",),
            validating_test_paths=(
                "packages/agentic-proteins/tests/providers/test_remote_providers.py",
            ),
            command_hint="agentic-proteins remote provider contracts execute this lane when OpenProtein credentials are configured",
        ),
        ProviderValidationLane(
            lane_id="openprotein_alphafold_real_remote",
            provider_name="api_openprotein_alphafold",
            reality_tier=ProviderRealityTier.REAL_REMOTE_VALIDATION,
            execution_mode="remote",
            repo_relative_fixture_paths=(
                "packages/bijux-proteomics-runtime/tests/fixtures/providers/remote_validation_request.json",
            ),
            expected_artifact_paths=("predicted.pdb",),
            validating_test_paths=(
                "packages/agentic-proteins/tests/providers/test_remote_providers.py",
            ),
            command_hint="agentic-proteins remote provider contracts execute this lane when OpenProtein credentials are configured",
        ),
    )
    return tuple(sorted(lanes, key=lambda lane: lane.lane_id))


def build_provider_capability_matrix() -> tuple[ProviderCapabilityMatrixRow, ...]:
    """Return the capability matrix used for CI-visible provider posture."""

    metadata_by_name = provider_metadata()
    lanes_by_provider: dict[str, list[str]] = {}
    for lane in provider_validation_lanes():
        lanes_by_provider.setdefault(lane.provider_name, []).append(lane.lane_id)

    rows: list[ProviderCapabilityMatrixRow] = []
    for provider_name in sorted(KNOWN_PROVIDERS):
        capabilities = PROVIDER_CAPABILITIES[provider_name]
        contract = PROVIDER_EXECUTION_CONTRACTS[provider_name]
        metadata = metadata_by_name.get(provider_name)
        rows.append(
            ProviderCapabilityMatrixRow(
                provider_name=provider_name,
                experimental=False if metadata is None else metadata.experimental,
                supports_cpu=capabilities.supports_cpu,
                supports_gpu=capabilities.supports_gpu,
                cpu_fallback_allowed=capabilities.cpu_fallback_allowed,
                cooperative_cancellation=contract.cooperative_cancellation,
                expected_error_codes=contract.failure_guarantees.expected_error_codes,
                required_raw_keys=contract.artifact_guarantees.required_raw_keys,
                validation_lane_ids=tuple(sorted(lanes_by_provider.get(provider_name, []))),
                unmet_requirements=tuple(provider_requirements(provider_name)),
            )
        )
    return tuple(rows)


def build_execution_reality_matrix() -> tuple[ProviderExecutionRealityRow, ...]:
    """Return a matrix that separates real execution from governed stand-ins."""

    lanes_by_provider: dict[str, list[ProviderRealityTier]] = {}
    for lane in provider_validation_lanes():
        lanes_by_provider.setdefault(lane.provider_name, []).append(lane.reality_tier)

    rows: list[ProviderExecutionRealityRow] = []
    for provider_name in sorted(KNOWN_PROVIDERS):
        tiers = tuple(
            sorted(set(lanes_by_provider.get(provider_name, [])), key=lambda item: item.value)
        )
        rows.append(
            ProviderExecutionRealityRow(
                provider_name=provider_name,
                reality_tiers=tiers,
                simulation_only=not tiers,
                notes=(
                    ("no governed real or CPU-safe validation lane is attached",)
                    if not tiers
                    else ("provider execution posture is backed by explicit validation lanes",)
                ),
            )
        )
    return tuple(rows)


def cpu_safe_conformance_providers() -> tuple[str, ...]:
    """Return providers with at least one CPU-safe conformance lane."""

    return tuple(
        sorted(
            {
                lane.provider_name
                for lane in provider_validation_lanes()
                if lane.reality_tier is ProviderRealityTier.CPU_SAFE_CONFORMANCE
            }
        )
    )


__all__ = [
    "ProviderCapabilityMatrixRow",
    "ProviderExecutionRealityRow",
    "ProviderRealityTier",
    "ProviderValidationLane",
    "build_execution_reality_matrix",
    "build_provider_capability_matrix",
    "cpu_safe_conformance_providers",
    "provider_validation_lanes",
]
