from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path

from bijux_proteomics_dev.api.runtime_topology import REPO_ROOT
from bijux_proteomics_runtime.governance.charter import (
    DEFAULT_RUNTIME_MODULE_AUDIT,
    RuntimeModuleClassification,
)

__all__ = [
    "RUNTIME_THIN_MODULES_PATH",
    "RuntimeThinModuleEntry",
    "RuntimeThinModuleGuard",
    "RuntimeThinModuleMetrics",
    "RuntimeThinModuleReport",
    "build_runtime_thin_module_report",
    "run",
    "validate_runtime_thin_modules",
]


@dataclass(frozen=True)
class RuntimeThinModuleEntry:
    """One thin runtime module tracked by the release guard."""

    module_path: str
    line_count: int
    namespace_initializer: bool


@dataclass(frozen=True)
class RuntimeThinModuleMetrics:
    """Current runtime thin-module inventory and its boundary-doc coverage."""

    thin_module_count: int
    namespace_initializer_count: int
    non_initializer_thin_module_count: int
    documented_boundary_doc_count: int
    thin_modules: tuple[RuntimeThinModuleEntry, ...]


@dataclass(frozen=True)
class RuntimeThinModuleGuard:
    """Release-blocking guardrails for runtime thin modules."""

    baseline_thin_module_count: int
    baseline_namespace_initializer_count: int
    baseline_documented_boundary_doc_count: int


@dataclass(frozen=True)
class RuntimeThinModuleReport:
    """Checked thin-module report for runtime."""

    metrics: RuntimeThinModuleMetrics
    guard: RuntimeThinModuleGuard


RUNTIME_SRC_ROOT = (
    REPO_ROOT
    / "packages"
    / "bijux-proteomics-runtime"
    / "src"
    / "bijux_proteomics_runtime"
)
RUNTIME_DOCS_ROOT = REPO_ROOT / "packages" / "bijux-proteomics-runtime"
RUNTIME_THIN_MODULES_PATH = (
    REPO_ROOT / "configs" / "package-governance" / "runtime-thin-modules.toml"
)
BOUNDARY_DOC_PATHS = (
    "README.md",
    "docs/ARCHITECTURE.md",
    "docs/BOUNDARIES.md",
    "docs/CONTRACTS.md",
    "docs/PUBLIC-SURFACES.md",
    "docs/ROUTE-OWNERSHIP.md",
    "docs/PROVIDER-OWNERSHIP.md",
    "docs/ARTIFACT-LINEAGE.md",
)


def _line_count(relative_path: str) -> int:
    return len(
        (RUNTIME_SRC_ROOT / Path(relative_path))
        .read_text(encoding="utf-8")
        .splitlines()
    )


def build_runtime_thin_module_report() -> RuntimeThinModuleReport:
    """Build the checked thin-module report for runtime."""

    thin_modules = tuple(
        RuntimeThinModuleEntry(
            module_path=entry.module_path,
            line_count=_line_count(entry.module_path),
            namespace_initializer=entry.module_path.endswith("__init__.py"),
        )
        for entry in DEFAULT_RUNTIME_MODULE_AUDIT
        if entry.classification is RuntimeModuleClassification.THIN_ABSTRACTION
    )
    documented_boundary_doc_count = sum(
        1 for path in BOUNDARY_DOC_PATHS if (RUNTIME_DOCS_ROOT / path).exists()
    )
    metrics = RuntimeThinModuleMetrics(
        thin_module_count=len(thin_modules),
        namespace_initializer_count=sum(
            1 for entry in thin_modules if entry.namespace_initializer
        ),
        non_initializer_thin_module_count=sum(
            1 for entry in thin_modules if not entry.namespace_initializer
        ),
        documented_boundary_doc_count=documented_boundary_doc_count,
        thin_modules=thin_modules,
    )
    return RuntimeThinModuleReport(
        metrics=metrics,
        guard=RuntimeThinModuleGuard(
            baseline_thin_module_count=metrics.thin_module_count,
            baseline_namespace_initializer_count=metrics.namespace_initializer_count,
            baseline_documented_boundary_doc_count=(
                metrics.documented_boundary_doc_count
            ),
        ),
    )


def validate_runtime_thin_modules() -> tuple[str, ...]:
    """Fail when new thin runtime modules appear without boundary clarity."""

    report = build_runtime_thin_module_report()
    metrics = report.metrics
    guard = report.guard
    failures: list[str] = []

    if metrics.non_initializer_thin_module_count > 0:
        failures.append(
            "runtime thin-module inventory now includes non-initializer files"
        )
    if metrics.thin_module_count > guard.baseline_thin_module_count:
        if (
            metrics.documented_boundary_doc_count
            <= guard.baseline_documented_boundary_doc_count
        ):
            failures.append(
                "new thin runtime modules appeared without stronger boundary clarity"
            )
    return tuple(failures)


def _toml_text(report: RuntimeThinModuleReport) -> str:
    metrics = report.metrics
    guard = report.guard
    lines = [
        "# Generated runtime thin-module report.",
        "# Regenerate with: ./.venv/bin/python -m bijux_proteomics_dev.api.runtime_thin_modules",
        "",
        "[metrics]",
        f"thin_module_count = {metrics.thin_module_count}",
        f"namespace_initializer_count = {metrics.namespace_initializer_count}",
        (
            "non_initializer_thin_module_count = "
            f"{metrics.non_initializer_thin_module_count}"
        ),
        f"documented_boundary_doc_count = {metrics.documented_boundary_doc_count}",
        "",
        "[guard]",
        f"baseline_thin_module_count = {guard.baseline_thin_module_count}",
        (
            "baseline_namespace_initializer_count = "
            f"{guard.baseline_namespace_initializer_count}"
        ),
        (
            "baseline_documented_boundary_doc_count = "
            f"{guard.baseline_documented_boundary_doc_count}"
        ),
        "",
    ]
    for entry in metrics.thin_modules:
        lines.extend(
            [
                "[[thin_module]]",
                f'module_path = "{entry.module_path}"',
                f"line_count = {entry.line_count}",
                f"namespace_initializer = {str(entry.namespace_initializer).lower()}",
                "",
            ]
        )
    return "\n".join(lines)


def _is_up_to_date(report: RuntimeThinModuleReport) -> bool:
    if not RUNTIME_THIN_MODULES_PATH.exists():
        return False
    return RUNTIME_THIN_MODULES_PATH.read_text(encoding="utf-8") == _toml_text(report)


def run(check: bool = False) -> int:
    report = build_runtime_thin_module_report()
    failures = validate_runtime_thin_modules()
    if failures:
        for failure in failures:
            print(failure)
        return 1
    if check:
        if _is_up_to_date(report):
            print("runtime thin-module report is up to date")
            return 0
        print("runtime thin-module report is stale; regenerate it")
        return 1
    RUNTIME_THIN_MODULES_PATH.write_text(_toml_text(report), encoding="utf-8")
    print("generated runtime thin-module report")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate or validate the runtime thin-module report."
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Fail if the runtime thin-module report is not up to date.",
    )
    args = parser.parse_args()
    raise SystemExit(run(check=args.check))
