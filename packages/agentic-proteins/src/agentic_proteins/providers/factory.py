"""Compatibility forwarding module for canonical runtime provider ownership."""

from importlib import util
import os
import shutil

from bijux_proteomics_runtime.providers.catalog import (
    PROVIDER_CAPABILITIES,
    provider_requirements,
)
from bijux_proteomics_runtime.providers.selection import (
    _require_module,
    create_provider,
    cuda_available,
)

__all__ = [
    "PROVIDER_CAPABILITIES",
    "_require_module",
    "create_provider",
    "cuda_available",
    "os",
    "provider_requirements",
    "shutil",
    "util",
]
