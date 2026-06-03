# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Provider factory and capability checks."""

from __future__ import annotations

from importlib import util

from bijux_proteomics_foundation.outcomes.exceptions import (
    MissingOptionalDependencyError,
)
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


def _module_available(module: str) -> bool:
    try:
        return util.find_spec(module) is not None
    except ModuleNotFoundError:
        return False


def create_provider(name: str) -> BaseProvider:
    """Create a provider instance by name."""
    if name == HeuristicStructureProvider.name:
        return HeuristicStructureProvider()
    if name == "local_esmfold":
        _require_module(
            "torch",
            "pip install bijux-proteomics-runtime[local-esmfold]",
            dependency_name="torch",
            feature_name="provider 'local_esmfold'",
        )
        _require_module(
            "transformers",
            "pip install bijux-proteomics-runtime[local-esmfold]",
            dependency_name="transformers",
            feature_name="provider 'local_esmfold'",
        )
        from bijux_proteomics_runtime.providers.local.esmfold import (
            LocalESMFoldProvider,
        )

        return LocalESMFoldProvider()
    if name == "local_rosettafold":
        _require_module(
            "torch",
            "pip install bijux-proteomics-runtime[local-rosettafold]",
            dependency_name="torch",
            feature_name="provider 'local_rosettafold'",
        )
        from bijux_proteomics_runtime.providers.local.rosettafold import (
            LocalRoseTTAFoldProvider,
        )

        return LocalRoseTTAFoldProvider()
    if name.startswith("api_openprotein"):
        _require_module(
            "openprotein",
            "pip install bijux-proteomics-runtime[api]",
            dependency_name="openprotein-python",
            feature_name=f"provider '{name}'",
        )
        from bijux_proteomics_runtime.providers.remote.openprotein import (
            APIOpenProteinProvider,
        )

        model = name.removeprefix("api_openprotein_") or "esmfold"
        return APIOpenProteinProvider(model=model)
    if name == "api_colabfold":
        _require_module(
            "colabfold",
            "pip install bijux-proteomics-runtime[api]",
            dependency_name="colabfold",
            feature_name="provider 'api_colabfold'",
        )
        from bijux_proteomics_runtime.providers.remote.colabfold import (
            APIColabFoldProvider,
        )

        return APIColabFoldProvider()
    raise PredictionError(f"Unknown provider: {name}", code="UNKNOWN_PROVIDER")


def _require_module(
    module: str,
    hint: str,
    *,
    dependency_name: str,
    feature_name: str,
) -> None:
    """Raise a clear error when a provider dependency is missing."""
    if not _module_available(module):
        error = MissingOptionalDependencyError(
            dependency_name=dependency_name,
            feature_name=feature_name,
            install_hint=hint,
        )
        raise PredictionError(
            str(error),
            code="MISSING_DEPENDENCY",
        ) from error


def cuda_available() -> bool:
    """Return True when CUDA is available (best-effort)."""
    try:
        import torch

        return bool(torch.cuda.is_available())
    except Exception:  # noqa: BLE001
        return False
