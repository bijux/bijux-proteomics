# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Provider factory and capability checks."""

from __future__ import annotations

from importlib import util
import os
import shutil

from agentic_proteins.providers.base import BaseProvider, ProviderCapabilities
from agentic_proteins.providers.errors import PredictionError
from agentic_proteins.providers.heuristic import HeuristicStructureProvider

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


def create_provider(name: str) -> BaseProvider:
    """Create a provider instance by name."""
    if name == HeuristicStructureProvider.name:
        return HeuristicStructureProvider()
    if name == "local_esmfold":
        _require_module("torch", "pip install agentic-proteins[local-esmfold]")
        _require_module("transformers", "pip install agentic-proteins[local-esmfold]")
        from agentic_proteins.providers.local.esmfold import LocalESMFoldProvider

        return LocalESMFoldProvider()
    if name == "local_rosettafold":
        _require_module("torch", "pip install agentic-proteins[local-rosettafold]")
        from agentic_proteins.providers.local.rosettafold import (
            LocalRoseTTAFoldProvider,
        )

        return LocalRoseTTAFoldProvider()
    if name.startswith("api_openprotein"):
        _require_module("openprotein", "pip install agentic-proteins[api]")
        from agentic_proteins.providers.experimental.openprotein import (
            APIOpenProteinProvider,
        )

        model = name.removeprefix("api_openprotein_") or "esmfold"
        return APIOpenProteinProvider(model=model)
    if name == "api_colabfold":
        _require_module("colabfold", "pip install agentic-proteins[api]")
        from agentic_proteins.providers.experimental.colabfold import (
            APIColabFoldProvider,
        )

        return APIColabFoldProvider()
    raise PredictionError(f"Unknown provider: {name}", code="UNKNOWN_PROVIDER")


def provider_requirements(name: str) -> list[str]:
    """Return unmet dependency/env/weights requirements for a provider name."""
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


def _require_module(module: str, hint: str) -> None:
    """Raise a clear error when a provider dependency is missing."""
    if util.find_spec(module) is None:
        raise PredictionError(
            f"Missing dependency: {module}. Install with `{hint}`.",
            code="MISSING_DEPENDENCY",
        )


def cuda_available() -> bool:
    """Return True when CUDA is available (best-effort)."""
    try:
        import torch

        return bool(torch.cuda.is_available())
    except Exception:  # noqa: BLE001
        return False
