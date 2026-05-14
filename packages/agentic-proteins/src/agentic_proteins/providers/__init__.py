"""Compatibility provider entrypoints."""

from bijux_proteomics_runtime.providers.assurance import (
    build_execution_reality_matrix,
    build_provider_capability_matrix,
    cpu_safe_conformance_providers,
    provider_validation_lanes,
)
from bijux_proteomics_runtime.providers.builtin.heuristic import (
    HeuristicStructureProvider,
)
from bijux_proteomics_runtime.providers.capabilities import (
    KNOWN_PROVIDERS,
    validate_runtime_capabilities,
)
from bijux_proteomics_runtime.providers.catalog import (
    PROVIDER_CAPABILITIES,
    PROVIDER_EXECUTION_CONTRACTS,
    provider_metadata,
    provider_requirements,
)
from bijux_proteomics_runtime.providers.contracts import (
    BaseProvider,
    PredictionResult,
    ProviderCapabilities,
    ProviderExecutionContract,
    ProviderMetadata,
    _time_left,
    provider_contract_supports_error_code,
    validate_prediction_result,
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
    "PROVIDER_EXECUTION_CONTRACTS",
    "HeuristicStructureProvider",
    "PredictionError",
    "PredictionResult",
    "ProviderCapabilities",
    "ProviderExecutionContract",
    "ProviderMetadata",
    "build_execution_reality_matrix",
    "build_provider_capability_matrix",
    "cpu_safe_conformance_providers",
    "_require_module",
    "_time_left",
    "create_provider",
    "cuda_available",
    "provider_contract_supports_error_code",
    "provider_requirements",
    "provider_validation_lanes",
    "provider_metadata",
    "validate_prediction_result",
    "validate_runtime_capabilities",
]
