# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Provider package exports."""

from __future__ import annotations

from bijux_proteomics_runtime.providers.assurance import (
    build_execution_reality_matrix,
    build_provider_capability_matrix,
    cpu_safe_conformance_providers,
    provider_validation_lanes,
)
from bijux_proteomics_runtime.providers.builtin.heuristic import (
    HeuristicStructureProvider,
)
from bijux_proteomics_runtime.providers.catalog import provider_metadata
from bijux_proteomics_runtime.providers.contracts import (
    BaseProvider,
    PredictionResult,
    ProviderCapabilities,
    ProviderExecutionContract,
    ProviderMetadata,
    _time_left,
)
from bijux_proteomics_runtime.providers.errors import PredictionError
from bijux_proteomics_runtime.support.primitives.stability import experimental

experimental()

__all__ = [
    "BaseProvider",
    "build_execution_reality_matrix",
    "build_provider_capability_matrix",
    "cpu_safe_conformance_providers",
    "HeuristicStructureProvider",
    "PredictionError",
    "PredictionResult",
    "ProviderCapabilities",
    "ProviderExecutionContract",
    "ProviderMetadata",
    "provider_validation_lanes",
    "_time_left",
    "provider_metadata",
]
