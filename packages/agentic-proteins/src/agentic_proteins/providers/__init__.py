"""Compatibility provider entrypoints."""

from agentic_proteins.providers.base import (
    BaseProvider,
    PredictionResult,
    ProviderCapabilities,
    ProviderMetadata,
    _time_left,
)
from agentic_proteins.providers.capabilities import (
    KNOWN_PROVIDERS,
    PROVIDER_CAPABILITIES,
    provider_requirements,
    validate_runtime_capabilities,
)
from agentic_proteins.providers.errors import PredictionError
from agentic_proteins.providers.heuristic import HeuristicStructureProvider
from bijux_proteomics_runtime.providers.catalog import provider_metadata
from agentic_proteins.providers.selection import (
    _require_module,
    create_provider,
    cuda_available,
)

__all__ = [
    "BaseProvider",
    "KNOWN_PROVIDERS",
    "PROVIDER_CAPABILITIES",
    "HeuristicStructureProvider",
    "PredictionError",
    "PredictionResult",
    "ProviderCapabilities",
    "ProviderMetadata",
    "_require_module",
    "_time_left",
    "create_provider",
    "cuda_available",
    "provider_requirements",
    "provider_metadata",
    "validate_runtime_capabilities",
]
