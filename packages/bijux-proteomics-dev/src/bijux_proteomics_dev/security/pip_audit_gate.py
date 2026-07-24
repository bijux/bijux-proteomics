"""Gate for pip-audit JSON reports."""

from __future__ import annotations

import json
import os
import sys
from typing import Any

REPORT_PATH = os.getenv("PIPA_JSON", "artifacts/security/pip-audit.json")
IGNORE_IDS = set(filter(None, os.getenv("SECURITY_IGNORE_IDS", "").split()))
IS_STRICT = os.getenv("SECURITY_STRICT", "1") == "1"


def _load_report(path: str) -> list[dict[str, Any]]:
    try:
        with open(path, encoding="utf-8") as file:
            data = json.load(file)
    except (FileNotFoundError, json.JSONDecodeError) as error:
        message = f"ERROR: pip-audit JSON missing/unreadable at '{path}': {error!s}"
        if IS_STRICT:
            print(message)
            sys.exit(2)
        print(f"{message} (non-strict: continuing with empty report)")
        return []

    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        deps = data.get("dependencies", [])
        if isinstance(deps, list):
            return deps
    message = f"ERROR: unexpected report format in '{path}'"
    if IS_STRICT:
        print(message)
        sys.exit(2)
    print(f"{message} (non-strict: continuing with empty report)")
    return []


def _all_ids(vulnerability: dict[str, Any]) -> set[str]:
    ids: set[str] = set()
    primary = vulnerability.get("id")
    if isinstance(primary, str) and primary:
        ids.add(primary)
    aliases = vulnerability.get("aliases") or []
    if isinstance(aliases, list):
        for alias in aliases:
            if isinstance(alias, str) and alias:
                ids.add(alias)
    return ids


def _primary_id(ids: set[str]) -> str:
    return sorted(ids)[0] if ids else "?"


def _fmt_table(rows: list[tuple[str, str, str, str]], header: tuple[str, ...]) -> str:
    widths = [len(column) for column in header]
    for row in rows:
        for index, cell in enumerate(row):
            widths[index] = max(widths[index], len(cell))

    def fmt_row(columns: tuple[str, ...] | tuple[str, str, str, str]) -> str:
        return "  ".join(
            cell.ljust(widths[index]) for index, cell in enumerate(columns)
        )

    separator = "  ".join("-" * width for width in widths)
    return "\n".join([fmt_row(header), separator, *(fmt_row(row) for row in rows)])


def main() -> None:
    if IGNORE_IDS:
        print(f"INFO: ignoring IDs/aliases: {' '.join(sorted(IGNORE_IDS))}")

    dependencies = _load_report(REPORT_PATH)
    if not dependencies:
        print("OK: no dependencies in report (or empty after parsing).")
        sys.exit(0)

    remaining: list[tuple[str, str, str, str]] = []
    ignored_count = 0
    for dependency in dependencies:
        name = str(dependency.get("name", "?"))
        version = str(dependency.get("version", "?"))
        vulnerabilities = dependency.get("vulns") or []
        if not isinstance(vulnerabilities, list):
            continue
        for vulnerability in vulnerabilities:
            ids = _all_ids(vulnerability)
            if ids & IGNORE_IDS:
                ignored_count += 1
                continue
            fixes = vulnerability.get("fix_versions") or []
            if not isinstance(fixes, list):
                fixes = []
            fix_display = ", ".join(fixes) if fixes else "-"
            remaining.append((name, version, _primary_id(ids), fix_display))

    if ignored_count:
        print(
            "INFO:"
            f" {ignored_count} vulnerability instance(s) matched ignore list and were skipped."
        )

    if not remaining:
        print("OK: 0 vulnerabilities remain after ignores.")
        sys.exit(0)

    remaining.sort(key=lambda row: (row[0], row[2], row[1]))
    table = _fmt_table(remaining, ("Package", "Version", "ID", "FixVersions"))
    print(
        f"FAIL: {len(remaining)} vulnerability instance(s) remain after ignores.\n{table}"
    )

    if IS_STRICT:
        print(f"STRICT: failing due to remaining vulnerabilities. See {REPORT_PATH}")
        sys.exit(1)
    print(
        f"NON-STRICT: not failing despite remaining vulnerabilities. See {REPORT_PATH}"
    )
    sys.exit(0)


if __name__ == "__main__":
    main()
