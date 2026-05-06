from __future__ import annotations

import argparse
import ast
from dataclasses import dataclass
from io import StringIO
from pathlib import Path
import re
import tokenize

from bijux_proteomics_dev.governance.support.workspace_inventory import (
    package_root,
    source_modules,
    workspace_package_names,
)
from bijux_proteomics_dev.governance.runtime.topology import REPO_ROOT

__all__ = [
    "SOURCE_DELIVERY_HISTORY_PATH",
    "SourceDeliveryHistoryEntry",
    "SourceDeliveryHistoryGuard",
    "SourceDeliveryHistoryReport",
    "build_source_delivery_history_report",
    "run",
    "validate_source_delivery_history",
]


SOURCE_DELIVERY_HISTORY_PATH = (
    REPO_ROOT / "configs" / "package-governance" / "source-delivery-history.toml"
)
DELIVERY_HISTORY_PATTERNS = (
    re.compile(r"\bfor iteration \d+\b", re.IGNORECASE),
    re.compile(r"\biteration-\d+\b", re.IGNORECASE),
    re.compile(r"\bphase \d+\b", re.IGNORECASE),
    re.compile(r"\bstep \d+\b", re.IGNORECASE),
    re.compile(r"\bv\d+-final\b", re.IGNORECASE),
)


@dataclass(frozen=True)
class SourceDeliveryHistoryEntry:
    """One source comment or docstring that still narrates delivery sequence."""

    distribution_name: str
    path: str
    line_number: int
    kind: str
    matched_text: str


@dataclass(frozen=True)
class SourceDeliveryHistoryGuard:
    """Release-blocking ceiling over delivery-history narration."""

    max_total_violation_count: int


@dataclass(frozen=True)
class SourceDeliveryHistoryReport:
    """Checked report over source comments and docstrings."""

    entries: tuple[SourceDeliveryHistoryEntry, ...]
    guard: SourceDeliveryHistoryGuard


def _matches_delivery_history(text: str) -> str | None:
    for pattern in DELIVERY_HISTORY_PATTERNS:
        match = pattern.search(text)
        if match is not None:
            return match.group(0)
    return None


def _docstring_entries(
    package_name: str, path: Path
) -> list[SourceDeliveryHistoryEntry]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    entries: list[SourceDeliveryHistoryEntry] = []
    nodes: list[tuple[ast.AST, str]] = [(tree, "module")]
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            nodes.append((node, "class_docstring"))
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            nodes.append((node, "function_docstring"))
    for node, kind in nodes:
        docstring = ast.get_docstring(node, clean=False)
        if not docstring:
            continue
        matched_text = _matches_delivery_history(docstring)
        if matched_text is None:
            continue
        line_number = getattr(node, "lineno", 1)
        entries.append(
            SourceDeliveryHistoryEntry(
                distribution_name=package_name,
                path=path.relative_to(REPO_ROOT).as_posix(),
                line_number=line_number,
                kind=kind,
                matched_text=matched_text,
            )
        )
    return entries


def _comment_entries(package_name: str, path: Path) -> list[SourceDeliveryHistoryEntry]:
    entries: list[SourceDeliveryHistoryEntry] = []
    source = path.read_text(encoding="utf-8")
    for token in tokenize.generate_tokens(StringIO(source).readline):
        if token.type != tokenize.COMMENT:
            continue
        matched_text = _matches_delivery_history(token.string)
        if matched_text is None:
            continue
        entries.append(
            SourceDeliveryHistoryEntry(
                distribution_name=package_name,
                path=path.relative_to(REPO_ROOT).as_posix(),
                line_number=token.start[0],
                kind="comment",
                matched_text=matched_text,
            )
        )
    return entries


def build_source_delivery_history_report() -> SourceDeliveryHistoryReport:
    """Build the checked source delivery-history report."""

    entries: list[SourceDeliveryHistoryEntry] = []
    for package_name in workspace_package_names():
        if package_root(package_name).name == "bijux-proteomics-dev":
            continue
        for path in source_modules(package_name):
            entries.extend(_docstring_entries(package_name, path))
            entries.extend(_comment_entries(package_name, path))
    entries.sort(key=lambda entry: (entry.path, entry.line_number, entry.kind))
    return SourceDeliveryHistoryReport(
        entries=tuple(entries),
        guard=SourceDeliveryHistoryGuard(max_total_violation_count=len(entries)),
    )


def validate_source_delivery_history(
    report: SourceDeliveryHistoryReport | None = None,
) -> tuple[str, ...]:
    """Fail release when delivery-history narration returns to source comments or docstrings."""

    report = report or build_source_delivery_history_report()
    if len(report.entries) <= report.guard.max_total_violation_count:
        return ()
    return (
        "source comments or docstrings resumed narrating delivery sequence instead of durable intent",
    )


def _toml_text(report: SourceDeliveryHistoryReport) -> str:
    lines = [
        "# Generated source delivery-history report.",
        "# Regenerate with: ./.venv/bin/python -m bijux_proteomics_dev.docs.governance.source_delivery_history",
        "",
        "[guard]",
        f"max_total_violation_count = {report.guard.max_total_violation_count}",
        "",
    ]
    for entry in report.entries:
        lines.extend(
            [
                "[[entry]]",
                f'distribution_name = "{entry.distribution_name}"',
                f'path = "{entry.path}"',
                f"line_number = {entry.line_number}",
                f'kind = "{entry.kind}"',
                f'matched_text = "{entry.matched_text}"',
                "",
            ]
        )
    return "\n".join(lines)


def _is_up_to_date(report: SourceDeliveryHistoryReport) -> bool:
    if not SOURCE_DELIVERY_HISTORY_PATH.exists():
        return False
    return SOURCE_DELIVERY_HISTORY_PATH.read_text(encoding="utf-8") == _toml_text(
        report
    )


def run(check: bool = False) -> int:
    report = build_source_delivery_history_report()
    failures = validate_source_delivery_history(report)
    if failures:
        for failure in failures:
            print(failure)
        return 1
    if check:
        if _is_up_to_date(report):
            print("source delivery-history report is up to date")
            return 0
        print("source delivery-history report is stale; regenerate it")
        return 1
    SOURCE_DELIVERY_HISTORY_PATH.write_text(_toml_text(report), encoding="utf-8")
    print("generated source delivery-history report")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate or validate the source delivery-history report."
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Fail if the source delivery-history report is not up to date.",
    )
    args = parser.parse_args()
    raise SystemExit(run(check=args.check))
