"""Compatibility forwarding module for canonical runtime ownership."""

from bijux_proteomics_runtime.runs.run_config import RunConfig
from bijux_proteomics_runtime.providers import capabilities
from bijux_proteomics_runtime.providers.capabilities import (
    KNOWN_PROVIDERS,
    validate_runtime_capabilities,
)

__all__ = [
    "KNOWN_PROVIDERS",
    "RunConfig",
    "capabilities",
    "validate_runtime_capabilities",
]
