"""Compatibility forwarding for `bijux_proteomics_runtime.providers.capabilities`."""

from bijux_proteomics_runtime.providers.capabilities import *  # noqa: F401,F403
from bijux_proteomics_runtime.providers.factory import (  # noqa: F401
    PROVIDER_CAPABILITIES,
    cuda_available,
    provider_requirements,
)
