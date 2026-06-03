# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Provider catalog metadata and runtime requirement lookups."""

from __future__ import annotations

from importlib import util
import os
import shutil

from bijux_proteomics_runtime.providers.builtin.heuristic import (
    HeuristicStructureProvider,
)
from bijux_proteomics_runtime.providers.contracts import (
    ProviderArtifactGuarantees,
    ProviderCapabilities,
    ProviderExecutionContract,
    ProviderFailureGuarantees,
    ProviderMetadata,
)

PROVIDER_CAPABILITIES = {
    "heuristic_proxy": ProviderCapabilities(
        supports_gpu=False, supports_cpu=True, cpu_fallback_allowed=True
    ),
    "local_esmfold": ProviderCapabilities(
        supports_gpu=True,
        supports_cpu=True,
        cpu_fallback_allowed=True,
        notes="CPU fallback is slow and memory intensive.",
    ),
    "local_rosettafold": ProviderCapabilities(
        supports_gpu=True,
        supports_cpu=False,
        cpu_fallback_allowed=False,
        notes="GPU required; CPU execution not supported.",
    ),
    "api_colabfold": ProviderCapabilities(
        supports_gpu=False, supports_cpu=True, cpu_fallback_allowed=True
    ),
    "api_openprotein_esmfold": ProviderCapabilities(
        supports_gpu=False, supports_cpu=True, cpu_fallback_allowed=True
    ),
    "api_openprotein_alphafold": ProviderCapabilities(
        supports_gpu=False, supports_cpu=True, cpu_fallback_allowed=True
    ),
}

PROVIDER_EXECUTION_CONTRACTS = {
    "heuristic_proxy": ProviderExecutionContract(
        cooperative_cancellation=False,
        artifact_guarantees=ProviderArtifactGuarantees(
            pdb_text_required=True,
            raw_payload_required=True,
            required_raw_keys=("mean_plddt",),
        ),
        failure_guarantees=ProviderFailureGuarantees(
            expected_error_codes=("BAD_INPUT",),
            malformed_input_code="BAD_INPUT",
        ),
        notes="CPU-safe heuristic provider used for deterministic contract proof.",
    ),
    "local_esmfold": ProviderExecutionContract(
        cooperative_cancellation=False,
        artifact_guarantees=ProviderArtifactGuarantees(
            pdb_text_required=True,
            raw_payload_required=True,
            required_raw_keys=("mean_plddt",),
        ),
        failure_guarantees=ProviderFailureGuarantees(
            expected_error_codes=(
                "BAD_INPUT",
                "TIMEOUT",
                "MODEL_LOAD_ERROR",
                "NO_OUTPUT",
                "INVALID_OUTPUT_SHAPE",
            ),
            partial_output_code="NO_OUTPUT",
            malformed_input_code="BAD_INPUT",
            corrupted_artifact_code="INVALID_OUTPUT_SHAPE",
        ),
        notes="Real local validation exists, plus CPU fallback contract proof.",
    ),
    "local_rosettafold": ProviderExecutionContract(
        cooperative_cancellation=False,
        artifact_guarantees=ProviderArtifactGuarantees(
            pdb_text_required=True,
            raw_payload_required=True,
            required_raw_keys=("mean_plddt",),
        ),
        failure_guarantees=ProviderFailureGuarantees(
            expected_error_codes=(
                "BAD_INPUT",
                "TIMEOUT",
                "NO_OUTPUT",
                "INVALID_OUTPUT_SHAPE",
                "MODEL_LOAD_ERROR",
            ),
            partial_output_code="NO_OUTPUT",
            malformed_input_code="BAD_INPUT",
            corrupted_artifact_code="INVALID_OUTPUT_SHAPE",
        ),
        notes="GPU-only local validation with explicit malformed-output and timeout paths.",
    ),
    "api_colabfold": ProviderExecutionContract(
        cooperative_cancellation=True,
        artifact_guarantees=ProviderArtifactGuarantees(
            pdb_text_required=True,
            raw_payload_required=True,
            required_raw_keys=("job_id",),
        ),
        failure_guarantees=ProviderFailureGuarantees(
            expected_error_codes=(
                "TIMEOUT",
                "AUTH_ERROR",
                "INPUT_TOO_LARGE",
                "REMOTE_ERROR",
                "NO_OUTPUT",
                "INVALID_OUTPUT_SHAPE",
            ),
            cancellation_code="TIMEOUT",
            partial_output_code="NO_OUTPUT",
            corrupted_artifact_code="INVALID_OUTPUT_SHAPE",
        ),
        notes="Remote validation lane is real but dependency- and network-gated.",
    ),
    "api_openprotein_esmfold": ProviderExecutionContract(
        cooperative_cancellation=True,
        artifact_guarantees=ProviderArtifactGuarantees(
            pdb_text_required=True,
            raw_payload_required=True,
            required_raw_keys=("job",),
        ),
        failure_guarantees=ProviderFailureGuarantees(
            expected_error_codes=("TIMEOUT", "AUTH_ERROR", "REMOTE_ERROR", "NO_OUTPUT"),
            cancellation_code="TIMEOUT",
            partial_output_code="NO_OUTPUT",
        ),
        notes="Remote OpenProtein validation is real but environment-gated.",
    ),
    "api_openprotein_alphafold": ProviderExecutionContract(
        cooperative_cancellation=True,
        artifact_guarantees=ProviderArtifactGuarantees(
            pdb_text_required=True,
            raw_payload_required=True,
            required_raw_keys=("job",),
        ),
        failure_guarantees=ProviderFailureGuarantees(
            expected_error_codes=("TIMEOUT", "AUTH_ERROR", "REMOTE_ERROR", "NO_OUTPUT"),
            cancellation_code="TIMEOUT",
            partial_output_code="NO_OUTPUT",
        ),
        notes="Remote OpenProtein validation is real but environment-gated.",
    ),
}


def provider_metadata() -> dict[str, ProviderMetadata]:
    """Return provider metadata for every currently discoverable provider."""

    metadata: dict[str, ProviderMetadata] = {
        HeuristicStructureProvider.name: HeuristicStructureProvider.metadata,
    }
    from bijux_proteomics_runtime.providers import local as local_providers

    local_esmfold = getattr(local_providers, "LocalESMFoldProvider", None)
    if local_esmfold is not None:
        metadata[local_esmfold.name] = local_esmfold.metadata
    local_rosettafold = getattr(local_providers, "LocalRoseTTAFoldProvider", None)
    if local_rosettafold is not None:
        metadata[local_rosettafold.name] = local_rosettafold.metadata
    from bijux_proteomics_runtime.providers.remote import APIColabFoldProvider

    metadata[APIColabFoldProvider.name] = APIColabFoldProvider.metadata
    metadata["api_openprotein_esmfold"] = ProviderMetadata(
        name="api_openprotein_esmfold",
        experimental=True,
    )
    metadata["api_openprotein_alphafold"] = ProviderMetadata(
        name="api_openprotein_alphafold",
        experimental=True,
    )
    return metadata


def provider_requirements(name: str) -> list[str]:
    """Return unmet dependency, environment, and weight requirements."""

    errors: list[str] = []
    if name == HeuristicStructureProvider.name:
        return errors
    if name in {"local_esmfold", "local_rosettafold"}:
        if util.find_spec("torch") is None:
            errors.append("missing_dependency:torch")
        if name == "local_esmfold" and util.find_spec("transformers") is None:
            errors.append("missing_dependency:transformers")
        if name == "local_rosettafold":
            weights_path = "models/rosettafold/RFAA_paper_weights.pt"
            if not os.path.exists(weights_path):
                errors.append(
                    "missing_weights:"
                    f"{weights_path}:sha256=unknown:hint=download weights and place at this path"
                )
    if name.startswith("api_openprotein"):
        if not os.getenv("OPENPROTEIN_USER"):
            errors.append("missing_env:OPENPROTEIN_USER")
        if not os.getenv("OPENPROTEIN_PASSWORD"):
            errors.append("missing_env:OPENPROTEIN_PASSWORD")
        if util.find_spec("openprotein") is None:
            errors.append("missing_dependency:openprotein-python")
    if name == "api_colabfold" and util.find_spec("colabfold") is None:
        errors.append("missing_dependency:colabfold")
    if name == "local_rosettafold" and shutil.which("docker") is None:
        errors.append("missing_dependency:docker")
    return errors


__all__ = [
    "PROVIDER_CAPABILITIES",
    "PROVIDER_EXECUTION_CONTRACTS",
    "provider_metadata",
    "provider_requirements",
]
