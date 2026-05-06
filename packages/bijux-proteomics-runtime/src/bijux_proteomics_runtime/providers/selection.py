# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Provider factory and capability checks."""

from __future__ import annotations

from importlib import util

from bijux_proteomics_runtime.providers.builtin.heuristic import (
    HeuristicStructureProvider,
)
from bijux_proteomics_runtime.providers.contracts import BaseProvider
from bijux_proteomics_runtime.providers.errors import PredictionError

__all__ = [
    "_require_module",
    "cuda_available",
    "create_provider",
]


def create_provider(name: str) -> BaseProvider:
    """Create a provider instance by name."""
    if name == HeuristicStructureProvider.name:
        return HeuristicStructureProvider()
    if name == "local_esmfold":
        _require_module("torch", "pip install bijux-proteomics-runtime[local-esmfold]")
        _require_module(
            "transformers", "pip install bijux-proteomics-runtime[local-esmfold]"
        )
        from bijux_proteomics_runtime.providers.local.esmfold import (
            LocalESMFoldProvider,
        )

        return LocalESMFoldProvider()
    if name == "local_rosettafold":
        _require_module(
            "torch", "pip install bijux-proteomics-runtime[local-rosettafold]"
        )
        from bijux_proteomics_runtime.providers.local.rosettafold import (
            LocalRoseTTAFoldProvider,
        )

        return LocalRoseTTAFoldProvider()
    if name.startswith("api_openprotein"):
        _require_module("openprotein", "pip install bijux-proteomics-runtime[api]")
        from bijux_proteomics_runtime.providers.remote.openprotein import (
            APIOpenProteinProvider,
        )

        model = name.removeprefix("api_openprotein_") or "esmfold"
        return APIOpenProteinProvider(model=model)
    if name == "api_colabfold":
        _require_module("colabfold", "pip install bijux-proteomics-runtime[api]")
        from bijux_proteomics_runtime.providers.remote.colabfold import (
            APIColabFoldProvider,
        )

        return APIColabFoldProvider()
    raise PredictionError(f"Unknown provider: {name}", code="UNKNOWN_PROVIDER")


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
