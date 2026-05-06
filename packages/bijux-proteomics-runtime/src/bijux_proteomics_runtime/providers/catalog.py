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
    ProviderCapabilities,
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


def provider_metadata() -> dict[str, ProviderMetadata]:
    """Return provider metadata for every currently discoverable provider."""

    metadata: dict[str, ProviderMetadata] = {
        HeuristicStructureProvider.name: HeuristicStructureProvider.metadata,
    }
    try:
        from bijux_proteomics_runtime.providers.local import (
            LocalESMFoldProvider,
            LocalRoseTTAFoldProvider,
        )

        metadata[LocalESMFoldProvider.name] = LocalESMFoldProvider.metadata
        metadata[LocalRoseTTAFoldProvider.name] = LocalRoseTTAFoldProvider.metadata
    except ImportError:
        return metadata
    try:
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
    except ImportError:
        return metadata
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


__all__ = ["PROVIDER_CAPABILITIES", "provider_metadata", "provider_requirements"]
