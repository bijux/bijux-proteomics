"""Compatibility provider-capability entrypoints."""

from bijux_proteomics_runtime.providers.capabilities import (
    KNOWN_PROVIDERS,
    validate_runtime_capabilities,
)
from bijux_proteomics_runtime.providers.catalog import (
    PROVIDER_CAPABILITIES,
    provider_requirements,
)

__all__ = [
    "KNOWN_PROVIDERS",
    "PROVIDER_CAPABILITIES",
    "provider_requirements",
    "validate_runtime_capabilities",
]
