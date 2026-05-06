"""Compatibility provider-selection entrypoints."""

from bijux_proteomics_runtime.providers.selection import (
    _require_module,
    create_provider,
    cuda_available,
)

__all__ = [
    "_require_module",
    "create_provider",
    "cuda_available",
]
