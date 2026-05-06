from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
from fnmatch import fnmatch
import io
from pathlib import Path
import tomllib


def _repo_root() -> Path:
    current = Path(__file__).resolve()
    for parent in current.parents:
        if (parent / "pyproject.toml").exists() and (parent / "packages").exists():
            return parent
    raise RuntimeError("Unable to resolve repository root for runtime migration ledger")


REPO_ROOT = _repo_root()
MODULE_ROOT = REPO_ROOT / "packages" / "agentic-proteins" / "src" / "agentic_proteins"
RULES_PATH = (
    REPO_ROOT / "configs" / "runtime-boundaries" / "migration-ledger" / "rules.toml"
)
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
            writer.writerow(
                [row.module_path, row.bucket, row.owner_package, row.reason]
            )


def _bucket_counts(rows: list[LedgerRow]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        counts[row.bucket] = counts.get(row.bucket, 0) + 1
    return counts


def write_summary(rows: list[LedgerRow]) -> None:
    LEDGER_SUMMARY_PATH.parent.mkdir(parents=True, exist_ok=True)
    LEDGER_SUMMARY_PATH.write_text(_summary_text(rows), encoding="utf-8")


def _csv_text(rows: list[LedgerRow]) -> str:
    buffer = io.StringIO(newline="")
    writer = csv.writer(buffer)
    writer.writerow(["module_path", "bucket", "owner_package", "reason"])
    for row in rows:
        writer.writerow([row.module_path, row.bucket, row.owner_package, row.reason])
    return buffer.getvalue()


def _summary_text(rows: list[LedgerRow]) -> str:
    counts = _bucket_counts(rows)
    total = len(rows)
    runtime_count = counts.get("runtime_execution_ownership", 0)
    review_count = counts.get("runtime_support_internal_review", 0)
    domain_count = counts.get("domain_ownership", 0)

    def percentage(count: int) -> int:
        if total == 0:
            return 0
        return round((count / total) * 100)

    review_hotspots: dict[str, int] = {}
    for row in rows:
        if row.bucket != "runtime_support_internal_review":
            continue
        family = row.module_path.split("/", 1)[0]
        review_hotspots[family] = review_hotspots.get(family, 0) + 1

    lines = [
        "---",
        "title: Agentic Module Ledger Summary",
        "audience: maintainer",
        "type: reference",
        "status: canonical",
        "owner: bijux-proteomics-runtime",
        "last_reviewed: 2026-04-26",
        "---",
        "",
        "# agentic-proteins Module Migration Ledger Summary",
        "",
        "This summary gives the current migration posture in one page. The signal is where ownership is already clear and where review debt is still concentrated.",
        "",
        "## Current Counts",
        "",
        f"- total modules: {total}",
    ]
    for bucket in (
        "runtime_execution_ownership",
        "runtime_support_internal_review",
        "domain_ownership",
    ):
        lines.append(f"- `{bucket}`: {counts.get(bucket, 0)}")
    lines.append("")
    lines.append(
        f"About {percentage(runtime_count)} percent of the ledger is already classified as clear runtime execution ownership, "
        f"about {percentage(review_count)} percent still needs internal review, and about {percentage(domain_count)} percent is already marked for lower-layer ownership."
    )
    lines.append("")
    lines.append("## Target Owner Distribution")
    lines.append("")

    owners: dict[str, int] = {}
    for row in rows:
        owners[row.owner_package] = owners.get(row.owner_package, 0) + 1
    for owner, count in sorted(owners.items(), key=lambda item: (-item[1], item[0])):
        lines.append(f"- `{owner}`: {count}")
    lines.append("")
    lines.append("## Review Hotspots")
    lines.append("")
    for family, count in sorted(
        review_hotspots.items(), key=lambda item: (-item[1], item[0])
    )[:3]:
        lines.append(f"- `{family}/**`: {count} review-required modules")
    lines.append("")
    lines.append("## What The Numbers Mean")
    lines.append("")
    lines.append(
        "The main ambiguity is no longer the public runtime surface. The harder work is mixed support code where older modules still blend orchestration, validation, reporting, or agent behavior."
    )
    lines.append("")
    lines.append(
        "That is why the internal-review bucket is larger than the clear domain bucket. The useful next step is to narrow mixed modules until each one can be defended as either canonical runtime behavior or lower-layer ownership."
    )
    return "\n".join(lines) + "\n"


def _is_up_to_date(rows: list[LedgerRow]) -> bool:
    if not LEDGER_CSV_PATH.exists() or not LEDGER_SUMMARY_PATH.exists():
        return False
    expected_csv = _csv_text(rows).replace("\r\n", "\n")
    expected_summary = _summary_text(rows)
    return (
        LEDGER_CSV_PATH.read_text(encoding="utf-8").replace("\r\n", "\n")
        == expected_csv
        and LEDGER_SUMMARY_PATH.read_text(encoding="utf-8") == expected_summary
    )


def run(check: bool = False) -> int:
    rows = build_ledger()
    if check:
        if _is_up_to_date(rows):
            print(f"migration ledger is up to date for {len(rows)} modules")
            return 0
        print("migration ledger is stale; regenerate with compatibility_ledger")
        return 1
    write_ledger(rows)
    write_summary(rows)
    print(f"generated migration ledger for {len(rows)} modules")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate or validate the agentic-proteins migration ledger."
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Fail if generated ledger outputs are not up to date.",
    )
    args = parser.parse_args()
    raise SystemExit(run(check=args.check))
