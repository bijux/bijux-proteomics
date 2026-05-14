from __future__ import annotations

from .compatibility_ledger_support import (
    compatibility_ledger_row_map,
)


def test_shadow_families_stay_out_of_the_bridge_tree() -> None:
    rows = compatibility_ledger_row_map()

    assert "__init__.py" in rows
    assert rows["__init__.py"]["owner_package"] == "agentic-proteins-compat"
    assert rows["__init__.py"]["bucket"] == "runtime_support_internal_review"

    removed_families = (
        "api/",
        "biology/",
        "core/",
        "design_loop/",
        "domain/",
        "memory/",
        "registry/",
        "report/",
        "runtime/",
        "sandbox/",
        "validation/",
    )
    for module_path in rows:
        assert not module_path.startswith(removed_families)


def test_surviving_bridge_families_resolve_to_runtime_owners() -> None:
    rows = compatibility_ledger_row_map()

    expected_runtime_modules = (
        "agents/__init__.py",
        "agents/coordination/__init__.py",
        "agents/coordination/coordinator.py",
        "execution/__init__.py",
        "execution/manager.py",
        "interfaces/http/app.py",
        "interfaces/structure_reports.py",
        "orchestration/__init__.py",
        "orchestration/manager.py",
        "orchestration/runtime/executor.py",
        "providers/experimental/__init__.py",
        "providers/remote/__init__.py",
        "providers/remote/openprotein.py",
        "state/context.py",
        "tools/__init__.py",
        "tools/heuristic.py",
    )

    for module_path in expected_runtime_modules:
        assert rows[module_path]["owner_package"] == "bijux-proteomics-runtime"
        assert rows[module_path]["bucket"] == "runtime_execution_ownership"


def test_bridge_tree_only_uses_durable_surviving_families() -> None:
    rows = compatibility_ledger_row_map()

    surviving_families = {
        "__init__.py",
        "agents",
        "execution",
        "interfaces",
        "orchestration",
        "providers",
        "state",
        "tools",
    }
    observed_families = {
        module_path.split("/", 1)[0]
        for module_path in rows
        if module_path != "__init__.py"
    }

    assert observed_families == surviving_families - {"__init__.py"}
