from __future__ import annotations

import csv
from pathlib import Path

REPO_ROOT = next(parent for parent in Path(__file__).resolve().parents if (parent / "packages").is_dir() and (parent / "configs").is_dir())
MODULE_ROOT = REPO_ROOT / "packages" / "agentic-proteins" / "src" / "agentic_proteins"
LEDGER_PATH = (
    REPO_ROOT
    / "docs"
    / "09-bijux-proteomics-runtime"
    / "migration-ledger"
    / "agentic-proteins-module-ledger.csv"
)
ALLOWED_BUCKETS = {
    "runtime_execution_ownership",
    "runtime_support_internal_review",
    "domain_ownership",
}


def _module_paths() -> set[str]:
    return {
        path.relative_to(MODULE_ROOT).as_posix()
        for path in MODULE_ROOT.rglob("*.py")
        if "__pycache__" not in path.parts
    }


def _ledger_rows() -> list[dict[str, str]]:
    with LEDGER_PATH.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def test_runtime_migration_ledger_covers_every_agentic_module() -> None:
    module_paths = _module_paths()
    ledger_paths = {row["module_path"] for row in _ledger_rows()}

    missing = sorted(module_paths - ledger_paths)
    extra = sorted(ledger_paths - module_paths)

    assert not missing, "ledger missing modules:\n" + "\n".join(missing)
    assert not extra, "ledger references unknown modules:\n" + "\n".join(extra)


def test_runtime_migration_ledger_has_no_duplicate_module_rows() -> None:
    rows = _ledger_rows()
    seen: set[str] = set()
    duplicates: list[str] = []
    for row in rows:
        path = row["module_path"]
        if path in seen:
            duplicates.append(path)
        seen.add(path)

    assert not duplicates, "duplicate module rows in ledger:\n" + "\n".join(duplicates)


def test_runtime_migration_ledger_rows_have_owner_bucket_and_reason() -> None:
    failures: list[str] = []
    for row in _ledger_rows():
        path = row["module_path"]
        bucket = row["bucket"].strip()
        owner = row["owner_package"].strip()
        reason = row["reason"].strip()

        if bucket not in ALLOWED_BUCKETS:
            failures.append(f"{path}: invalid bucket '{bucket}'")
        if not owner:
            failures.append(f"{path}: missing owner_package")
        if not reason:
            failures.append(f"{path}: missing reason")

    assert not failures, "ledger row contract failures:\n" + "\n".join(failures)
