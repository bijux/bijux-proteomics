from __future__ import annotations

from .compatibility_ledger_support import (
    compatibility_ledger_rows,
    compatibility_module_paths,
)

ALLOWED_BUCKETS = {
    "runtime_execution_ownership",
    "runtime_support_internal_review",
    "domain_ownership",
}


def test_compatibility_ledger_covers_every_agentic_module() -> None:
    module_paths = compatibility_module_paths()
    ledger_paths = {row["module_path"] for row in compatibility_ledger_rows()}

    missing = sorted(module_paths - ledger_paths)
    extra = sorted(ledger_paths - module_paths)

    assert not missing, "ledger missing modules:\n" + "\n".join(missing)
    assert not extra, "ledger references unknown modules:\n" + "\n".join(extra)


def test_compatibility_ledger_has_no_duplicate_module_rows() -> None:
    rows = compatibility_ledger_rows()
    seen: set[str] = set()
    duplicates: list[str] = []
    for row in rows:
        path = row["module_path"]
        if path in seen:
            duplicates.append(path)
        seen.add(path)

    assert not duplicates, "duplicate module rows in ledger:\n" + "\n".join(duplicates)


def test_compatibility_ledger_rows_have_owner_bucket_and_reason() -> None:
    failures: list[str] = []
    for row in compatibility_ledger_rows():
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
