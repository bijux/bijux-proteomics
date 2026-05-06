from __future__ import annotations

import argparse
import ast
from dataclasses import dataclass
from pathlib import Path

from bijux_proteomics_dev.api.runtime.topology import REPO_ROOT

__all__ = [
    "BANNED_ROOTS",
    "LAB_ROOT_IMPORTS_PATH",
    "LabRootImportEntry",
    "LabRootImportGuard",
    "LabRootImportMetrics",
    "LabRootImportReport",
    "build_lab_root_import_report",
    "run",
    "validate_lab_root_imports",
]


@dataclass(frozen=True)
class LabRootImportEntry:
    """One package-root import found inside lab owner modules."""

    module_path: str
    root_name: str
    import_kind: str
    line_number: int


@dataclass(frozen=True)
class LabRootImportMetrics:
    """Current package-root import state for lab owner modules."""

    scanned_module_count: int
    banned_root_count: int
    violation_count: int
    violations: tuple[LabRootImportEntry, ...]


@dataclass(frozen=True)
class LabRootImportGuard:
    """Release-blocking guardrails for lab package-root imports."""

    baseline_violation_count: int


@dataclass(frozen=True)
class LabRootImportReport:
    """Checked package-root import report for lab owner modules."""

    metrics: LabRootImportMetrics
    guard: LabRootImportGuard


BANNED_ROOTS = (
    "bijux_proteomics",
    "bijux_proteomics_knowledge",
    "bijux_proteomics_intelligence",
    "bijux_proteomics_runtime",
    "bijux_proteomics_lab",
)
LAB_SRC_ROOT = (
    REPO_ROOT / "packages" / "bijux-proteomics-lab" / "src" / "bijux_proteomics_lab"
)
LAB_ROOT_IMPORTS_PATH = (
    REPO_ROOT / "configs" / "package-governance" / "lab-root-imports.toml"
)


def _violations_for(path: Path) -> tuple[LabRootImportEntry, ...]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    relative = path.relative_to(LAB_SRC_ROOT).as_posix()
    violations: list[LabRootImportEntry] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name in BANNED_ROOTS:
                    violations.append(
                        LabRootImportEntry(
                            module_path=relative,
                            root_name=alias.name,
                            import_kind="import",
                            line_number=node.lineno,
                        )
                    )
        if isinstance(node, ast.ImportFrom) and node.module in BANNED_ROOTS:
            violations.append(
                LabRootImportEntry(
                    module_path=relative,
                    root_name=node.module,
                    import_kind="from",
                    line_number=node.lineno,
                )
            )
    return tuple(sorted(violations, key=lambda entry: entry.line_number))


def build_lab_root_import_report() -> LabRootImportReport:
    """Build the checked report of package-root imports inside lab owners."""

    source_modules = tuple(
        path for path in sorted(LAB_SRC_ROOT.rglob("*.py")) if "__pycache__" not in path.parts
    )
    violations = tuple(
        violation for path in source_modules for violation in _violations_for(path)
    )
    metrics = LabRootImportMetrics(
        scanned_module_count=len(source_modules),
        banned_root_count=len(BANNED_ROOTS),
        violation_count=len(violations),
        violations=violations,
    )
    return LabRootImportReport(
        metrics=metrics,
        guard=LabRootImportGuard(baseline_violation_count=metrics.violation_count),
    )


def validate_lab_root_imports() -> tuple[str, ...]:
    """Fail when lab owner modules depend on package roots."""

    report = build_lab_root_import_report()
    if report.metrics.violation_count == 0:
        return ()
    return tuple(
        f"{entry.module_path}:{entry.line_number} imports package root {entry.root_name}"
        for entry in report.metrics.violations
    )


def _toml_text(report: LabRootImportReport) -> str:
    metrics = report.metrics
    guard = report.guard
    lines = [
        "# Generated lab package-root import report.",
        "# Regenerate with: ./.venv/bin/python -m bijux_proteomics_dev.api.lab.root_imports",
        "",
        "[metrics]",
        f"scanned_module_count = {metrics.scanned_module_count}",
        f"banned_root_count = {metrics.banned_root_count}",
        f"violation_count = {metrics.violation_count}",
        "",
        "[guard]",
        f"baseline_violation_count = {guard.baseline_violation_count}",
        "",
    ]
    for root_name in BANNED_ROOTS:
        lines.extend([f'[[banned_root]]\nname = "{root_name}"', ""])
    for violation in metrics.violations:
        lines.extend(
            [
                "[[violation]]",
                f'module_path = "{violation.module_path}"',
                f'root_name = "{violation.root_name}"',
                f'import_kind = "{violation.import_kind}"',
                f"line_number = {violation.line_number}",
                "",
            ]
        )
    return "\n".join(lines)


def _is_up_to_date(report: LabRootImportReport) -> bool:
    if not LAB_ROOT_IMPORTS_PATH.exists():
        return False
    return LAB_ROOT_IMPORTS_PATH.read_text(encoding="utf-8") == _toml_text(report)


def run(check: bool = False) -> int:
    report = build_lab_root_import_report()
    failures = validate_lab_root_imports()
    if failures:
        for failure in failures:
            print(failure)
        return 1
    if check:
        if _is_up_to_date(report):
            print("lab package-root import report is up to date")
            return 0
        print("lab package-root import report is stale; regenerate it")
        return 1
    LAB_ROOT_IMPORTS_PATH.write_text(_toml_text(report), encoding="utf-8")
    print("generated lab package-root import report")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate or validate the lab package-root import report."
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Fail if the lab package-root import report is not up to date.",
    )
    args = parser.parse_args()
    raise SystemExit(run(check=args.check))
