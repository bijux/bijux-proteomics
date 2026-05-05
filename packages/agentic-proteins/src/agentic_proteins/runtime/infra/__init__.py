"""Compatibility forwarding module for canonical runtime ownership."""

from bijux_proteomics_runtime.runtime.context.run_config import RunConfig
from bijux_proteomics_runtime.runtime.control import (
    provider_capabilities as capabilities,
)
from bijux_proteomics_runtime.runtime.control.provider_capabilities import (
    KNOWN_PROVIDERS,
    validate_runtime_capabilities,
)

__all__ = [
    "KNOWN_PROVIDERS",
    "RunConfig",
    "capabilities",
    "validate_runtime_capabilities",
]
