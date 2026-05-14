# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from agentic_proteins.tools.catalog import ToolCatalog, ToolRegistry
from agentic_proteins.tools.contracts import validate_tools_for_agents
from bijux_proteomics_runtime.execution.tools.catalog import (
    ToolCatalog as RuntimeToolCatalog,
)
from bijux_proteomics_runtime.execution.tools.contracts import (
    validate_tools_for_agents as runtime_validate_tools_for_agents,
)


def test_tool_catalog_surface_forwards_to_runtime_symbols() -> None:
    assert ToolCatalog is RuntimeToolCatalog
    assert ToolRegistry is RuntimeToolCatalog
    assert validate_tools_for_agents is runtime_validate_tools_for_agents
