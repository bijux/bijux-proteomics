from __future__ import annotations

import argparse
import importlib
from dataclasses import dataclass
from pathlib import Path
import re

from bijux_proteomics_dev.api.support.workspace_inventory import (
    package_docs,
    workspace_package_names,
)
from bijux_proteomics_dev.api.runtime.topology import REPO_ROOT

__all__ = [
    "DOCS_TOPOLOGY_REFERENCES_PATH",
    "DocsTopologyReferenceEntry",
    "DocsTopologyReferenceGuard",
    "DocsTopologyReferenceReport",
    "build_docs_topology_reference_report",
    "run",
    "validate_docs_topology_references",
]


DOCS_TOPOLOGY_REFERENCES_PATH = (
    REPO_ROOT / "configs" / "package-governance" / "docs-topology-references.toml"
)
STALE_DOC_REFERENCES = (
    "bijux_proteomics_runtime.api.product_routes",
    "bijux_proteomics_knowledge.references.decision_rules",
    "src/bijux_proteomics_lab/targeted_benchmarking.py",
)
DOC_IMPORT_PATTERN = re.compile(
    r"^\s*(?:from|import)\s+(?P<module>(?:bijux_proteomics|bijux_proteomics_[a-z_]+|agentic_proteins)(?:\.[a-zA-Z0-9_]+)*)",
    re.MULTILINE,
)


@dataclass(frozen=True)
class DocsTopologyReferenceEntry:
    """One stale or non-importable topology reference found in docs."""

    path: str
    kind: str
    reference: str


@dataclass(frozen=True)
class DocsTopologyReferenceGuard:
    """Release-blocking ceiling over stale topology references in docs."""

    max_total_violation_count: int


@dataclass(frozen=True)
class DocsTopologyReferenceReport:
    """Checked docs topology reference report."""

    entries: tuple[DocsTopologyReferenceEntry, ...]
    guard: DocsTopologyReferenceGuard


def _repo_docs() -> tuple[Path, ...]:
    return tuple(sorted((REPO_ROOT / "docs").rglob("*.md")))


def _all_docs() -> tuple[Path, ...]:
    package_paths: list[Path] = []
    for package_name in workspace_package_names():
        package_paths.extend(package_docs(package_name))
    return tuple(sorted((*package_paths, *_repo_docs())))


def build_docs_topology_reference_report() -> DocsTopologyReferenceReport:
    """Build the checked docs topology reference report."""

    entries: list[DocsTopologyReferenceEntry] = []
    for path in _all_docs():
        text = path.read_text(encoding="utf-8")
        relative_path = path.relative_to(REPO_ROOT).as_posix()
        for stale_reference in STALE_DOC_REFERENCES:
            if stale_reference in text:
                entries.append(
                    DocsTopologyReferenceEntry(
                        path=relative_path,
                        kind="stale_reference",
                        reference=stale_reference,
                    )
                )
        for match in DOC_IMPORT_PATTERN.finditer(text):
            module_name = match.group("module")
            try:
                importlib.import_module(module_name)
            except Exception:
                entries.append(
                    DocsTopologyReferenceEntry(
                        path=relative_path,
                        kind="missing_import",
                        reference=module_name,
                    )
                )
    entries.sort(key=lambda entry: (entry.path, entry.kind, entry.reference))
    return DocsTopologyReferenceReport(
        entries=tuple(entries),
        guard=DocsTopologyReferenceGuard(max_total_violation_count=len(entries)),
    )


def validate_docs_topology_references(
    report: DocsTopologyReferenceReport | None = None,
) -> tuple[str, ...]:
    """Fail release when docs teach stale or non-importable topology."""

    report = report or build_docs_topology_reference_report()
    if len(report.entries) <= report.guard.max_total_violation_count:
        return ()
    return ("docs teach stale or non-importable package topology",)


def _toml_text(report: DocsTopologyReferenceReport) -> str:
    lines = [
        "# Generated docs topology reference report.",
        "# Regenerate with: ./.venv/bin/python -m bijux_proteomics_dev.docs.governance.topology_references",
        "",
        "[guard]",
        f"max_total_violation_count = {report.guard.max_total_violation_count}",
        "",
    ]
    for entry in report.entries:
        lines.extend(
            [
                "[[entry]]",
                f'path = "{entry.path}"',
                f'kind = "{entry.kind}"',
                f'reference = "{entry.reference}"',
                "",
            ]
        )
    return "\n".join(lines)


def _is_up_to_date(report: DocsTopologyReferenceReport) -> bool:
    if not DOCS_TOPOLOGY_REFERENCES_PATH.exists():
        return False
    return DOCS_TOPOLOGY_REFERENCES_PATH.read_text(encoding="utf-8") == _toml_text(
        report
    )


def run(check: bool = False) -> int:
    report = build_docs_topology_reference_report()
    failures = validate_docs_topology_references(report)
    if failures:
        for failure in failures:
            print(failure)
        return 1
    if check:
        if _is_up_to_date(report):
            print("docs topology reference report is up to date")
            return 0
        print("docs topology reference report is stale; regenerate it")
        return 1
    DOCS_TOPOLOGY_REFERENCES_PATH.write_text(_toml_text(report), encoding="utf-8")
    print("generated docs topology reference report")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate or validate the docs topology reference report."
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Fail if the docs topology reference report is not up to date.",
    )
    args = parser.parse_args()
    raise SystemExit(run(check=args.check))
