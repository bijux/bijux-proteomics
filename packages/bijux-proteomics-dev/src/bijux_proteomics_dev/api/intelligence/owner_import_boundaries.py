from __future__ import annotations

import argparse
import ast
from dataclasses import dataclass
from pathlib import Path

from bijux_proteomics_dev.api.runtime.topology import REPO_ROOT

__all__ = [
    "BANNED_MODULES",
    "INTELLIGENCE_OWNER_IMPORT_BOUNDARIES_PATH",
    "INTELLIGENCE_SRC_ROOT",
    "IntelligenceOwnerImportBoundaryEntry",
    "IntelligenceOwnerImportBoundaryGuard",
    "IntelligenceOwnerImportBoundaryMetrics",
    "IntelligenceOwnerImportBoundaryReport",
    "build_intelligence_owner_import_boundary_report",
    "run",
    "validate_intelligence_owner_import_boundaries",
]


@dataclass(frozen=True)
class IntelligenceOwnerImportBoundaryEntry:
    """One intelligence owner import that targets a banned package bucket."""

    module_path: str
    imported_module: str
    import_kind: str
    line_number: int


@dataclass(frozen=True)
class IntelligenceOwnerImportBoundaryMetrics:
    """Current import-boundary state for intelligence owner modules."""

    scanned_module_count: int
    banned_module_count: int
    violation_count: int
    violations: tuple[IntelligenceOwnerImportBoundaryEntry, ...]


@dataclass(frozen=True)
class IntelligenceOwnerImportBoundaryGuard:
    """Release-blocking guardrails for intelligence owner import boundaries."""

    baseline_violation_count: int


@dataclass(frozen=True)
class IntelligenceOwnerImportBoundaryReport:
    """Checked report of banned owner-bucket imports inside intelligence."""

    metrics: IntelligenceOwnerImportBoundaryMetrics
    guard: IntelligenceOwnerImportBoundaryGuard


BANNED_MODULES = (
    "bijux_proteomics",
    "bijux_proteomics.domain.sequence",
    "bijux_proteomics.domain.structure",
    "bijux_proteomics_knowledge",
    "bijux_proteomics_knowledge.references",
)
INTELLIGENCE_SRC_ROOT = (
    REPO_ROOT
    / "packages"
    / "bijux-proteomics-intelligence"
    / "src"
    / "bijux_proteomics_intelligence"
)
INTELLIGENCE_OWNER_IMPORT_BOUNDARIES_PATH = (
    REPO_ROOT
    / "configs"
    / "package-governance"
    / "intelligence-owner-import-boundaries.toml"
)


def _violations_for(path: Path) -> tuple[IntelligenceOwnerImportBoundaryEntry, ...]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    relative = path.relative_to(INTELLIGENCE_SRC_ROOT).as_posix()
    violations: list[IntelligenceOwnerImportBoundaryEntry] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name in BANNED_MODULES:
                    violations.append(
                        IntelligenceOwnerImportBoundaryEntry(
                            module_path=relative,
                            imported_module=alias.name,
                            import_kind="import",
                            line_number=node.lineno,
                        )
                    )
        if isinstance(node, ast.ImportFrom) and node.module in BANNED_MODULES:
            violations.append(
                IntelligenceOwnerImportBoundaryEntry(
                    module_path=relative,
                    imported_module=node.module,
                    import_kind="from",
                    line_number=node.lineno,
                )
            )
    return tuple(sorted(violations, key=lambda entry: entry.line_number))


def build_intelligence_owner_import_boundary_report() -> (
    IntelligenceOwnerImportBoundaryReport
):
    """Build the checked intelligence owner import-boundary report."""

    source_modules = tuple(
        path
        for path in sorted(INTELLIGENCE_SRC_ROOT.rglob("*.py"))
        if "__pycache__" not in path.parts
    )
    violations = tuple(
        violation
        for path in source_modules
        for violation in _violations_for(path)
    )
    metrics = IntelligenceOwnerImportBoundaryMetrics(
        scanned_module_count=len(source_modules),
        banned_module_count=len(BANNED_MODULES),
        violation_count=len(violations),
        violations=violations,
    )
    return IntelligenceOwnerImportBoundaryReport(
        metrics=metrics,
        guard=IntelligenceOwnerImportBoundaryGuard(
            baseline_violation_count=metrics.violation_count
        ),
    )


def validate_intelligence_owner_import_boundaries() -> tuple[str, ...]:
    """Fail when intelligence owner modules depend on banned package buckets."""

    report = build_intelligence_owner_import_boundary_report()
    if report.metrics.violation_count == 0:
        return ()
    return tuple(
        (
            f"{entry.module_path}:{entry.line_number} imports "
            f"banned owner bucket {entry.imported_module}"
        )
        for entry in report.metrics.violations
    )


def _toml_text(report: IntelligenceOwnerImportBoundaryReport) -> str:
    metrics = report.metrics
    guard = report.guard
    lines = [
        "# Generated intelligence owner import-boundary report.",
        "# Regenerate with: ./.venv/bin/python -m bijux_proteomics_dev.api.intelligence.owner_import_boundaries",
        "",
        "[metrics]",
        f"scanned_module_count = {metrics.scanned_module_count}",
        f"banned_module_count = {metrics.banned_module_count}",
        f"violation_count = {metrics.violation_count}",
        "",
        "[guard]",
        f"baseline_violation_count = {guard.baseline_violation_count}",
        "",
    ]
    for module_name in BANNED_MODULES:
        lines.extend([f'[[banned_module]]\nname = "{module_name}"', ""])
    for violation in metrics.violations:
        lines.extend(
            [
                "[[violation]]",
                f'module_path = "{violation.module_path}"',
                f'imported_module = "{violation.imported_module}"',
                f'import_kind = "{violation.import_kind}"',
                f"line_number = {violation.line_number}",
                "",
            ]
        )
    return "\n".join(lines)


def _is_up_to_date(report: IntelligenceOwnerImportBoundaryReport) -> bool:
    if not INTELLIGENCE_OWNER_IMPORT_BOUNDARIES_PATH.exists():
        return False
    return INTELLIGENCE_OWNER_IMPORT_BOUNDARIES_PATH.read_text(
        encoding="utf-8"
    ) == _toml_text(report)


def run(check: bool = False) -> int:
    report = build_intelligence_owner_import_boundary_report()
    failures = validate_intelligence_owner_import_boundaries()
    if failures:
        for failure in failures:
            print(failure)
        return 1
    if check:
        if _is_up_to_date(report):
            print("intelligence owner import-boundary report is up to date")
            return 0
        print("intelligence owner import-boundary report is stale; regenerate it")
        return 1
    INTELLIGENCE_OWNER_IMPORT_BOUNDARIES_PATH.write_text(
        _toml_text(report), encoding="utf-8"
    )
    print("generated intelligence owner import-boundary report")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description=(
            "Generate or validate the intelligence owner import-boundary report."
        )
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help=(
            "Fail if the intelligence owner import-boundary report is not up to date."
        ),
    )
    args = parser.parse_args()
    raise SystemExit(run(check=args.check))
