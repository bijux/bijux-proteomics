from __future__ import annotations

import csv
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
LEDGER_PATH = (
    REPO_ROOT
    / "docs"
    / "09-bijux-proteomics-runtime"
    / "migration-ledger"
    / "agentic-proteins-module-ledger.csv"
)


def _owner_map() -> dict[str, str]:
    with LEDGER_PATH.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    return {str(row["module_path"]): str(row["owner_package"]) for row in rows}


def _row_map() -> dict[str, dict[str, str]]:
    with LEDGER_PATH.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    return {str(row["module_path"]): row for row in rows}


def test_domain_owner_matrix_is_enforced() -> None:
    owners = _owner_map()
    rows = _row_map()
    assert owners["biology/pathway.py"] == "bijux-proteomics-core"
    assert owners["domain/sequence/summary.py"] == "bijux-proteomics-core"
    assert owners["domain/structure/structure.py"] == "bijux-proteomics-core"
    assert owners["domain/confidence/segments.py"] == "bijux-proteomics-knowledge"
    assert owners["domain/metrics/compute.py"] == "bijux-proteomics-intelligence"
    assert owners["design_loop/loop.py"] == "bijux-proteomics-intelligence"
    assert owners["report/__init__.py"] == "bijux-proteomics-intelligence"
    assert owners["report/compute.py"] == "bijux-proteomics-intelligence"
    assert rows["report/__init__.py"]["bucket"] == "domain_ownership"
    assert rows["report/compute.py"]["bucket"] == "domain_ownership"


def test_runtime_support_owner_matrix_is_enforced() -> None:
    owners = _owner_map()
    assert owners["memory/schemas.py"] == "bijux-proteomics-runtime"
    assert owners["registry/agents.py"] == "bijux-proteomics-runtime"
    assert owners["tools/heuristic.py"] == "bijux-proteomics-runtime"


def test_runtime_execution_promotions_are_enforced() -> None:
    rows = _row_map()
    assert rows["memory/__init__.py"]["owner_package"] == "bijux-proteomics-runtime"
    assert rows["memory/__init__.py"]["bucket"] == "runtime_execution_ownership"
    assert rows["memory/schemas.py"]["owner_package"] == "bijux-proteomics-runtime"
    assert rows["memory/schemas.py"]["bucket"] == "runtime_execution_ownership"
    assert rows["memory/store.py"]["owner_package"] == "bijux-proteomics-runtime"
    assert rows["memory/store.py"]["bucket"] == "runtime_execution_ownership"
    assert rows["execution/__init__.py"]["owner_package"] == (
        "bijux-proteomics-runtime"
    )
    assert rows["execution/__init__.py"]["bucket"] == "runtime_execution_ownership"
    assert rows["execution/evaluation/__init__.py"]["owner_package"] == (
        "bijux-proteomics-runtime"
    )
    assert rows["execution/evaluation/__init__.py"]["bucket"] == (
        "runtime_execution_ownership"
    )
    assert rows["execution/evaluation/evaluation.py"]["owner_package"] == (
        "bijux-proteomics-runtime"
    )
    assert rows["execution/evaluation/evaluation.py"]["bucket"] == (
        "runtime_execution_ownership"
    )
    assert rows["execution/schemas.py"]["owner_package"] == (
        "bijux-proteomics-runtime"
    )
    assert rows["execution/schemas.py"]["bucket"] == "runtime_execution_ownership"
    assert rows["execution/validation.py"]["owner_package"] == (
        "bijux-proteomics-runtime"
    )
    assert rows["execution/validation.py"]["bucket"] == (
        "runtime_execution_ownership"
    )
    assert rows["registry/__init__.py"]["owner_package"] == (
        "bijux-proteomics-runtime"
    )
    assert rows["registry/__init__.py"]["bucket"] == "runtime_execution_ownership"
    assert rows["registry/agents.py"]["owner_package"] == (
        "bijux-proteomics-runtime"
    )
    assert rows["registry/agents.py"]["bucket"] == "runtime_execution_ownership"
    assert rows["registry/tools.py"]["owner_package"] == (
        "bijux-proteomics-runtime"
    )
    assert rows["registry/tools.py"]["bucket"] == "runtime_execution_ownership"
    assert rows["validation/__init__.py"]["owner_package"] == (
        "bijux-proteomics-runtime"
    )
    assert rows["validation/__init__.py"]["bucket"] == (
        "runtime_execution_ownership"
    )
    assert rows["validation/state.py"]["owner_package"] == (
        "bijux-proteomics-runtime"
    )
    assert rows["validation/state.py"]["bucket"] == "runtime_execution_ownership"
    assert rows["execution/evaluation/observations.py"]["owner_package"] == (
        "bijux-proteomics-runtime"
    )
    assert rows["execution/evaluation/observations.py"]["bucket"] == (
        "runtime_execution_ownership"
    )
    assert rows["execution/evaluation/schemas.py"]["owner_package"] == (
        "bijux-proteomics-runtime"
    )
    assert rows["execution/evaluation/schemas.py"]["bucket"] == (
        "runtime_execution_ownership"
    )
    assert rows["validation/agents.py"]["owner_package"] == (
        "bijux-proteomics-runtime"
    )
    assert rows["validation/agents.py"]["bucket"] == "runtime_execution_ownership"
    assert rows["validation/tools.py"]["owner_package"] == (
        "bijux-proteomics-runtime"
    )
    assert rows["validation/tools.py"]["bucket"] == "runtime_execution_ownership"
