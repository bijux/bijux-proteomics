"""Compatibility forwarding module for canonical runtime ownership."""

from bijux_proteomics_runtime.providers.factory import (
    PROVIDER_CAPABILITIES,
    cuda_available,
    provider_requirements,
)
from bijux_proteomics_runtime.providers.capabilities import (
    KNOWN_PROVIDERS,
    validate_runtime_capabilities,
)


__all__ = [
    "KNOWN_PROVIDERS",
    "PROVIDER_CAPABILITIES",
    "cuda_available",
    "provider_requirements",
    "validate_runtime_capabilities",
]
