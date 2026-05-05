"""Compatibility forwarding module for canonical runtime ownership."""

from agentic_proteins.runtime.infra import capabilities
from bijux_proteomics_runtime.runtime.context.run_config import RunConfig
from agentic_proteins.runtime.infra.capabilities import KNOWN_PROVIDERS
from agentic_proteins.runtime.infra.capabilities import validate_runtime_capabilities

__all__ = [
    "KNOWN_PROVIDERS",
    "RunConfig",
    "capabilities",
    "validate_runtime_capabilities",
]
