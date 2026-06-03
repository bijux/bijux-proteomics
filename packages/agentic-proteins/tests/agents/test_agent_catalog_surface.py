# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from agentic_proteins.agents.catalog import AgentCatalog, AgentRegistry
from agentic_proteins.agents.contracts import validate_agent_catalog
from bijux_proteomics_runtime.execution.agents.catalog import (
    AgentCatalog as RuntimeAgentCatalog,
)
from bijux_proteomics_runtime.execution.agents.contracts import (
    validate_agent_catalog as runtime_validate_agent_catalog,
)


def test_agent_catalog_surface_forwards_to_runtime_symbols() -> None:
    assert AgentCatalog is RuntimeAgentCatalog
    assert AgentRegistry is RuntimeAgentCatalog
    assert validate_agent_catalog is runtime_validate_agent_catalog
