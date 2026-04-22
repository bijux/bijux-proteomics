from __future__ import annotations

from bijux_proteomics_runtime.registry.agents import AgentRegistry


def test_runtime_registry_surface_smoke() -> None:
    AgentRegistry.clear()

    class ExampleAgent:
        name = "example"

    AgentRegistry.register(ExampleAgent)
    assert AgentRegistry.get("example") is ExampleAgent
