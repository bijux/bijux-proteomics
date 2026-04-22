from __future__ import annotations

from pathlib import Path
import csv


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


def test_domain_owner_matrix_is_enforced() -> None:
    owners = _owner_map()
    assert owners["biology/pathway.py"] == "bijux-proteomics-core"
    assert owners["domain/sequence/summary.py"] == "bijux-proteomics-core"
    assert owners["domain/structure/structure.py"] == "bijux-proteomics-core"
    assert owners["domain/confidence/segments.py"] == "bijux-proteomics-knowledge"
    assert owners["domain/metrics/compute.py"] == "bijux-proteomics-intelligence"
    assert owners["design_loop/loop.py"] == "bijux-proteomics-intelligence"


def test_runtime_support_owner_matrix_is_enforced() -> None:
    owners = _owner_map()
    assert owners["memory/schemas.py"] == "bijux-proteomics-runtime"
    assert owners["registry/agents.py"] == "bijux-proteomics-runtime"
    assert owners["tools/heuristic.py"] == "bijux-proteomics-runtime"
