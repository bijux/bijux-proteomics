"""Compatibility forwarding module for canonical runtime execution ownership."""

from bijux_proteomics_runtime.execution.evaluation import (
    observations as _runtime_observations,
)
from bijux_proteomics_runtime.execution.evaluation.observations import *  # noqa: F401,F403

__all__ = _runtime_observations.__all__
