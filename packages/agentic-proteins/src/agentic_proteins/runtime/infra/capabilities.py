"""Compatibility forwarding module for canonical runtime ownership."""

from bijux_proteomics_runtime.providers.catalog import (
    PROVIDER_CAPABILITIES,
    provider_requirements,
)
from bijux_proteomics_runtime.providers.capabilities import (
    KNOWN_PROVIDERS,
    validate_runtime_capabilities,
)
from bijux_proteomics_runtime.providers.selection import cuda_available


__all__ = [
    "KNOWN_PROVIDERS",
    "PROVIDER_CAPABILITIES",
    "cuda_available",
    "provider_requirements",
    "validate_runtime_capabilities",
]
