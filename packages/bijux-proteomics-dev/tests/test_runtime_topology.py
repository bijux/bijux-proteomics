from __future__ import annotations

from bijux_proteomics_dev.api.runtime_topology import (
    RUNTIME_TOPOLOGY_PATH,
    build_runtime_topology_budget,
    run,
)


def test_runtime_topology_budget_is_up_to_date() -> None:
    assert run(check=True) == 0


def test_runtime_topology_budget_locks_current_first_level_runtime_shape() -> None:
    budget = build_runtime_topology_budget()
    subtree_names = [entry.name for entry in budget.subtrees]
    module_counts = {entry.name: entry.module_count for entry in budget.subtrees}

    assert RUNTIME_TOPOLOGY_PATH.exists()
    assert budget.actual_first_level_subtrees <= budget.max_first_level_subtrees
    assert subtree_names == [
        "agents",
        "api",
        "core",
        "execution",
        "interfaces",
        "memory",
        "providers",
        "runs",
        "runtime",
        "sandbox",
        "state",
        "tools",
        "workflows",
    ]
    assert module_counts["runs"] > module_counts["runtime"]
    assert module_counts["workflows"] > module_counts["sandbox"]
