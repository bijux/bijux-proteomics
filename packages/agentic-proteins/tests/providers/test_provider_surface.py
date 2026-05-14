# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from agentic_proteins.providers import (
    KNOWN_PROVIDERS,
    PROVIDER_CAPABILITIES,
    PROVIDER_EXECUTION_CONTRACTS,
    build_execution_reality_matrix,
    build_provider_capability_matrix,
    cpu_safe_conformance_providers,
    create_provider,
    provider_contract_supports_error_code,
    provider_requirements,
    provider_validation_lanes,
    validate_prediction_result,
    validate_runtime_capabilities,
)
from agentic_proteins.providers.selection import _require_module
from bijux_proteomics_runtime.providers.assurance import (
    build_execution_reality_matrix as runtime_build_execution_reality_matrix,
)
from bijux_proteomics_runtime.providers.assurance import (
    build_provider_capability_matrix as runtime_build_provider_capability_matrix,
)
from bijux_proteomics_runtime.providers.assurance import (
    cpu_safe_conformance_providers as runtime_cpu_safe_conformance_providers,
)
from bijux_proteomics_runtime.providers.assurance import (
    provider_validation_lanes as runtime_provider_validation_lanes,
)
from bijux_proteomics_runtime.providers.capabilities import (
    KNOWN_PROVIDERS as runtime_known_providers,
)
from bijux_proteomics_runtime.providers.capabilities import (
    validate_runtime_capabilities as runtime_validate_runtime_capabilities,
)
from bijux_proteomics_runtime.providers.catalog import (
    PROVIDER_CAPABILITIES as runtime_provider_capabilities,
)
from bijux_proteomics_runtime.providers.catalog import (
    PROVIDER_EXECUTION_CONTRACTS as runtime_provider_execution_contracts,
)
from bijux_proteomics_runtime.providers.catalog import (
    provider_requirements as runtime_provider_requirements,
)
from bijux_proteomics_runtime.providers.contracts import (
    provider_contract_supports_error_code as runtime_provider_contract_supports_error_code,
)
from bijux_proteomics_runtime.providers.contracts import (
    validate_prediction_result as runtime_validate_prediction_result,
)
from bijux_proteomics_runtime.providers.selection import (
    _require_module as runtime_require_module,
)
from bijux_proteomics_runtime.providers.selection import (
    create_provider as runtime_create_provider,
)


def test_provider_surface_forwards_to_runtime_symbols() -> None:
    assert KNOWN_PROVIDERS is runtime_known_providers
    assert PROVIDER_CAPABILITIES is runtime_provider_capabilities
    assert PROVIDER_EXECUTION_CONTRACTS is runtime_provider_execution_contracts
    assert provider_requirements is runtime_provider_requirements
    assert validate_runtime_capabilities is runtime_validate_runtime_capabilities
    assert create_provider is runtime_create_provider
    assert _require_module is runtime_require_module
    assert validate_prediction_result is runtime_validate_prediction_result
    assert (
        provider_contract_supports_error_code
        is runtime_provider_contract_supports_error_code
    )
    assert build_provider_capability_matrix is runtime_build_provider_capability_matrix
    assert build_execution_reality_matrix is runtime_build_execution_reality_matrix
    assert provider_validation_lanes is runtime_provider_validation_lanes
    assert cpu_safe_conformance_providers is runtime_cpu_safe_conformance_providers
