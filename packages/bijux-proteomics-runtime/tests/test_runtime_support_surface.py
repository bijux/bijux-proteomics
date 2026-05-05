from __future__ import annotations

from bijux_proteomics_runtime.agents.catalog import AgentCatalog


def test_runtime_registry_surface_smoke() -> None:
    AgentCatalog.clear()

    class ExampleAgent:
        name = "example"

    AgentCatalog.register(ExampleAgent)
    assert AgentCatalog.get("example") is ExampleAgent
