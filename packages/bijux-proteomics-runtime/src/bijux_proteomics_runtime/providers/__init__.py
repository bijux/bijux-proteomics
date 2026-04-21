# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Provider package exports."""

from __future__ import annotations

from agentic_proteins.core.stability import experimental
from bijux_proteomics_runtime.providers.base import (
    BaseProvider,
    PredictionResult,
    ProviderCapabilities,
    ProviderMetadata,
    _time_left,
)
from bijux_proteomics_runtime.providers.errors import PredictionError
from bijux_proteomics_runtime.providers.heuristic import HeuristicStructureProvider

experimental()

__all__ = [
    "BaseProvider",
    "HeuristicStructureProvider",
    "PredictionError",
    "PredictionResult",
    "ProviderCapabilities",
    "ProviderMetadata",
    "_time_left",
    "provider_metadata",
]


def provider_metadata() -> dict[str, ProviderMetadata]:
    """provider_metadata."""
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
        from bijux_proteomics_runtime.providers.experimental import (
            APIColabFoldProvider,
            APIOpenProteinProvider,
        )

        metadata[APIColabFoldProvider.name] = APIColabFoldProvider.metadata
        metadata["api_openprotein_esmfold"] = ProviderMetadata(
            name="api_openprotein_esmfold", experimental=True
        )
        metadata["api_openprotein_alphafold"] = ProviderMetadata(
            name="api_openprotein_alphafold", experimental=True
        )
    except ImportError:
        return metadata
    return metadata
