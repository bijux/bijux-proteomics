"""Compatibility provider entrypoints."""

from bijux_proteomics_runtime.providers.contracts import (
    BaseProvider,
    PredictionResult,
    ProviderCapabilities,
    ProviderMetadata,
    _time_left,
)
from bijux_proteomics_runtime.providers.catalog import (
    PROVIDER_CAPABILITIES,
    provider_metadata,
    provider_requirements,
)
from bijux_proteomics_runtime.providers.capabilities import (
    KNOWN_PROVIDERS,
    validate_runtime_capabilities,
)
from bijux_proteomics_runtime.providers.builtin.heuristic import (
    HeuristicStructureProvider,
)
from bijux_proteomics_runtime.providers.errors import PredictionError
from bijux_proteomics_runtime.providers.selection import (
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
