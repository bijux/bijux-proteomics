from __future__ import annotations

import csv
from pathlib import Path

REPO_ROOT = next(
    parent
    for parent in Path(__file__).resolve().parents
    if (parent / "packages").is_dir() and (parent / "configs").is_dir()
)
MODULE_ROOT = REPO_ROOT / "packages" / "agentic-proteins" / "src" / "agentic_proteins"
LEDGER_PATH = (
    REPO_ROOT
    / "docs"
    / "09-bijux-proteomics-runtime"
    / "migration-ledger"
    / "agentic-proteins-module-ledger.csv"
)


def compatibility_ledger_rows() -> list[dict[str, str]]:
    with LEDGER_PATH.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def compatibility_ledger_row_map() -> dict[str, dict[str, str]]:
    return {str(row["module_path"]): row for row in compatibility_ledger_rows()}


def compatibility_module_paths() -> set[str]:
    return {
        path.relative_to(MODULE_ROOT).as_posix()
        for path in MODULE_ROOT.rglob("*.py")
        if "__pycache__" not in path.parts
    }
