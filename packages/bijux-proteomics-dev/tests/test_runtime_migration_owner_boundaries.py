from __future__ import annotations

import csv
from pathlib import Path

REPO_ROOT = next(
    parent
    for parent in Path(__file__).resolve().parents
    if (parent / "packages").is_dir() and (parent / "configs").is_dir()
)
LEDGER_PATH = (
    REPO_ROOT
    / "docs"
    / "09-bijux-proteomics-runtime"
    / "migration-ledger"
    / "agentic-proteins-module-ledger.csv"
)


def _row_map() -> dict[str, dict[str, str]]:
    with LEDGER_PATH.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    return {str(row["module_path"]): row for row in rows}


def test_shadow_families_stay_out_of_the_bridge_tree() -> None:
    rows = _row_map()

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
    rows = _row_map()

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
    rows = _row_map()

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
