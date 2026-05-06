# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from agentic_proteins.providers import (
    KNOWN_PROVIDERS,
    PROVIDER_CAPABILITIES,
    create_provider,
    provider_requirements,
    validate_runtime_capabilities,
)
from agentic_proteins.providers.selection import _require_module
from bijux_proteomics_runtime.providers.capabilities import (
    KNOWN_PROVIDERS as runtime_known_providers,
    validate_runtime_capabilities as runtime_validate_runtime_capabilities,
)
from bijux_proteomics_runtime.providers.catalog import (
    PROVIDER_CAPABILITIES as runtime_provider_capabilities,
    provider_requirements as runtime_provider_requirements,
)
from bijux_proteomics_runtime.providers.selection import (
    _require_module as runtime_require_module,
    create_provider as runtime_create_provider,
)


def test_provider_surface_forwards_to_runtime_symbols() -> None:
    assert KNOWN_PROVIDERS is runtime_known_providers
    assert PROVIDER_CAPABILITIES is runtime_provider_capabilities
    assert provider_requirements is runtime_provider_requirements
    assert validate_runtime_capabilities is runtime_validate_runtime_capabilities
    assert create_provider is runtime_create_provider
    assert _require_module is runtime_require_module
