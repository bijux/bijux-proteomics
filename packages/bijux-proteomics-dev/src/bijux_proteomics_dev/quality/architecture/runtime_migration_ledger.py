from __future__ import annotations

from dataclasses import dataclass
from fnmatch import fnmatch
from pathlib import Path
import csv
from typing import Any

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover
    import tomli as tomllib

def _repo_root() -> Path:
    current = Path(__file__).resolve()
    for parent in current.parents:
        if (parent / "pyproject.toml").exists() and (parent / "packages").exists():
            return parent
    raise RuntimeError("Unable to resolve repository root for runtime migration ledger")


REPO_ROOT = _repo_root()
MODULE_ROOT = REPO_ROOT / "packages" / "agentic-proteins" / "src" / "agentic_proteins"
RULES_PATH = REPO_ROOT / "configs" / "runtime-boundaries" / "migration-ledger" / "rules.toml"
LEDGER_CSV_PATH = (
    REPO_ROOT
    / "docs"
    / "09-bijux-proteomics-runtime"
    / "migration-ledger"
    / "agentic-proteins-module-ledger.csv"
)
LEDGER_SUMMARY_PATH = (
    REPO_ROOT
    / "docs"
    / "09-bijux-proteomics-runtime"
    / "migration-ledger"
    / "agentic-proteins-module-ledger-summary.md"
)


@dataclass(frozen=True)
class Rule:
    pattern: str
    bucket: str
    owner_package: str
    reason: str


@dataclass(frozen=True)
class LedgerRow:
    module_path: str
    bucket: str
    owner_package: str
    reason: str


def _load_rules() -> list[Rule]:
    with RULES_PATH.open("rb") as handle:
        raw = tomllib.load(handle)
    rules: list[Rule] = []
    for entry in raw["rule"]:
        rules.append(
            Rule(
                pattern=str(entry["pattern"]),
                bucket=str(entry["bucket"]),
                owner_package=str(entry["owner_package"]),
                reason=str(entry["reason"]),
            )
        )
    return rules


def _module_paths() -> list[str]:
    modules: list[str] = []
    for path in sorted(MODULE_ROOT.rglob("*.py")):
        if "__pycache__" in path.parts:
            continue
        modules.append(path.relative_to(MODULE_ROOT).as_posix())
    return modules


def _match_rule(module_path: str, rules: list[Rule]) -> Rule:
    for rule in rules:
        if fnmatch(module_path, rule.pattern):
            return rule
    raise ValueError(f"No migration ledger rule matched module: {module_path}")


def build_ledger() -> list[LedgerRow]:
    rules = _load_rules()
    rows: list[LedgerRow] = []
    for module_path in _module_paths():
        rule = _match_rule(module_path, rules)
        rows.append(
            LedgerRow(
                module_path=module_path,
                bucket=rule.bucket,
                owner_package=rule.owner_package,
                reason=rule.reason,
            )
        )
    return rows


def write_ledger(rows: list[LedgerRow]) -> None:
    LEDGER_CSV_PATH.parent.mkdir(parents=True, exist_ok=True)
    with LEDGER_CSV_PATH.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["module_path", "bucket", "owner_package", "reason"])
        for row in rows:
            writer.writerow([row.module_path, row.bucket, row.owner_package, row.reason])


def _bucket_counts(rows: list[LedgerRow]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        counts[row.bucket] = counts.get(row.bucket, 0) + 1
    return counts


def write_summary(rows: list[LedgerRow]) -> None:
    counts = _bucket_counts(rows)
    lines = [
        "# agentic-proteins Module Migration Ledger Summary",
        "",
        f"- total modules: {len(rows)}",
    ]
    for bucket in sorted(counts):
        lines.append(f"- {bucket}: {counts[bucket]}")
    lines.append("")
    lines.append("## Owner package distribution")
    lines.append("")

    owners: dict[str, int] = {}
    for row in rows:
        owners[row.owner_package] = owners.get(row.owner_package, 0) + 1
    for owner in sorted(owners):
        lines.append(f"- {owner}: {owners[owner]}")

    LEDGER_SUMMARY_PATH.parent.mkdir(parents=True, exist_ok=True)
    LEDGER_SUMMARY_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run() -> int:
    rows = build_ledger()
    write_ledger(rows)
    write_summary(rows)
    print(f"generated migration ledger for {len(rows)} modules")
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
