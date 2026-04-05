# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Provider package exports."""

from __future__ import annotations

from agentic_proteins.core.stability import experimental
from agentic_proteins.providers.base import (
    BaseProvider,
    PredictionResult,
    ProviderCapabilities,
    ProviderMetadata,
    _time_left,
)
from agentic_proteins.providers.errors import PredictionError
from agentic_proteins.providers.heuristic import HeuristicStructureProvider

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
        from agentic_proteins.providers.local import (
            LocalESMFoldProvider,
            LocalRoseTTAFoldProvider,
        )

        metadata[LocalESMFoldProvider.name] = LocalESMFoldProvider.metadata
        metadata[LocalRoseTTAFoldProvider.name] = LocalRoseTTAFoldProvider.metadata
    except ImportError:
        return metadata
    try:
        from agentic_proteins.providers.experimental import (
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
