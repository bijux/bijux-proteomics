from __future__ import annotations

import argparse
import ast
from dataclasses import dataclass
from pathlib import Path
import re

from bijux_proteomics.governance.charter import (
    DEFAULT_CORE_MODULE_AUDIT,
    CoreModuleClassification,
)
from bijux_proteomics_dev.governance.foundation.root_consumers import (
    REPO_ROOT,
    downstream_packages,
)

__all__ = [
    "CORE_COMPATIBILITY_EXPORTS_PATH",
    "CoreCompatibilityExportEntry",
    "CoreCompatibilityExportGuard",
    "CoreCompatibilityExportReport",
    "build_core_compatibility_export_report",
    "run",
    "validate_core_compatibility_exports",
]


@dataclass(frozen=True)
class CoreCompatibilityExportEntry:
    """One remaining core compatibility export and its live consumers."""

    module_path: str
    target_module_name: str
    target_module_path: str
    source_consumer_distributions: tuple[str, ...]
    source_consumer_modules: tuple[str, ...]
    test_consumer_modules: tuple[str, ...]


@dataclass(frozen=True)
class CoreCompatibilityExportGuard:
    """Release-blocking budget over remaining compatibility exports."""

    max_compatibility_exports: int
    require_root_level_only: bool


@dataclass(frozen=True)
class CoreCompatibilityExportReport:
    """One checked wrapper burn-down report for core."""

    entries: tuple[CoreCompatibilityExportEntry, ...]
    guard: CoreCompatibilityExportGuard


CORE_SRC_ROOT = (
    REPO_ROOT / "packages" / "bijux-proteomics-core" / "src" / "bijux_proteomics"
)
COMPATIBILITY_IMPORT_RE = re.compile(
    r"^from\s+(bijux_proteomics(?:\.[a-z0-9_]+)+)\s+import\s+\*(?:\s+#.*)?$",
    flags=re.MULTILINE,
)
CORE_COMPATIBILITY_EXPORTS_PATH = (
    REPO_ROOT / "configs" / "package-governance" / "core-compatibility-exports.toml"
)


def _resolve_module_path(module_name: str) -> str:
    relative = module_name.removeprefix("bijux_proteomics.").replace(".", "/")
    candidate = CORE_SRC_ROOT / f"{relative}.py"
    if candidate.exists():
        return f"{relative}.py"
    package_init = CORE_SRC_ROOT / relative / "__init__.py"
    if package_init.exists():
        return f"{relative}/__init__.py"
    raise ValueError(f"unable to resolve compatibility target for {module_name}")


def _compatibility_exports() -> tuple[tuple[str, str, str], ...]:
    exports: list[tuple[str, str, str]] = []
    for entry in DEFAULT_CORE_MODULE_AUDIT:
        if entry.classification is not CoreModuleClassification.COMPATIBILITY_EXPORT:
            continue
        content = (CORE_SRC_ROOT / entry.module_path).read_text(encoding="utf-8")
        match = COMPATIBILITY_IMPORT_RE.search(content)
        assert match is not None, entry.module_path
        target_module_name = match.group(1)
        exports.append(
            (
                entry.module_path,
                target_module_name,
                _resolve_module_path(target_module_name),
            )
        )
    return tuple(exports)


def _module_import_name(module_path: str) -> str:
    suffix = module_path.removesuffix(".py").replace("/", ".")
    return f"bijux_proteomics.{suffix}"


def _source_root(distribution_name: str, import_root: str) -> Path:
    return REPO_ROOT / "packages" / distribution_name / "src" / import_root


def _test_root(distribution_name: str) -> Path:
    return REPO_ROOT / "packages" / distribution_name / "tests"


def _imports_module(path: Path, module_name: str) -> bool:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name == module_name:
                    return True
        if isinstance(node, ast.ImportFrom) and node.module == module_name:
            return True
    return False


def build_core_compatibility_export_report() -> CoreCompatibilityExportReport:
    """Build the checked burn-down report for remaining core wrappers."""

    entries: list[CoreCompatibilityExportEntry] = []
    for module_path, target_module_name, target_module_path in _compatibility_exports():
        import_name = _module_import_name(module_path)
        source_distributions: set[str] = set()
        source_modules: set[str] = set()
        test_modules: set[str] = set()

        for package in downstream_packages():
            src_root = _source_root(package.distribution_name, package.import_root)
            if src_root.exists():
                for path in src_root.rglob("*.py"):
                    if _imports_module(path, import_name):
                        source_distributions.add(package.distribution_name)
                        source_modules.add(path.relative_to(REPO_ROOT).as_posix())
            test_root = _test_root(package.distribution_name)
            if test_root.exists():
                for path in test_root.rglob("*.py"):
                    if _imports_module(path, import_name):
                        test_modules.add(path.relative_to(REPO_ROOT).as_posix())

        entries.append(
            CoreCompatibilityExportEntry(
                module_path=module_path,
                target_module_name=target_module_name,
                target_module_path=target_module_path,
                source_consumer_distributions=tuple(sorted(source_distributions)),
                source_consumer_modules=tuple(sorted(source_modules)),
                test_consumer_modules=tuple(sorted(test_modules)),
            )
        )

    return CoreCompatibilityExportReport(
        entries=tuple(entries),
        guard=CoreCompatibilityExportGuard(
            max_compatibility_exports=len(entries),
            require_root_level_only=True,
        ),
    )


def validate_core_compatibility_exports() -> tuple[str, ...]:
    """Fail when the wrapper count grows or wrappers spread beyond the root."""

    report = build_core_compatibility_export_report()
    failures: list[str] = []
    if len(report.entries) > report.guard.max_compatibility_exports:
        failures.append(
            "core compatibility export count grew beyond the guarded budget"
        )
    if report.guard.require_root_level_only and any(
        "/" in entry.module_path for entry in report.entries
    ):
        failures.append(
            "core compatibility exports escaped the root-level wrapper budget"
        )
    return tuple(failures)


def _toml_text(report: CoreCompatibilityExportReport) -> str:
    lines = [
        "# Generated core compatibility export burn-down report.",
        "# Regenerate with: ./.venv/bin/python -m bijux_proteomics_dev.governance.core.compatibility_exports",
        "",
        "[guard]",
        f"max_compatibility_exports = {report.guard.max_compatibility_exports}",
        f"require_root_level_only = {str(report.guard.require_root_level_only).lower()}",
        "",
    ]
    for entry in report.entries:
        source_distributions = ", ".join(
            f'"{value}"' for value in entry.source_consumer_distributions
        )
        source_modules = ", ".join(
            f'"{value}"' for value in entry.source_consumer_modules
        )
        test_modules = ", ".join(f'"{value}"' for value in entry.test_consumer_modules)
        lines.extend(
            [
                "[[wrapper]]",
                f'module_path = "{entry.module_path}"',
                f'target_module_name = "{entry.target_module_name}"',
                f'target_module_path = "{entry.target_module_path}"',
                f"source_consumer_count = {len(entry.source_consumer_modules)}",
                f"source_consumer_distributions = [{source_distributions}]",
                f"source_consumer_modules = [{source_modules}]",
                f"test_consumer_count = {len(entry.test_consumer_modules)}",
                f"test_consumer_modules = [{test_modules}]",
                "",
            ]
        )
    return "\n".join(lines)


def _is_up_to_date(report: CoreCompatibilityExportReport) -> bool:
    if not CORE_COMPATIBILITY_EXPORTS_PATH.exists():
        return False
    return CORE_COMPATIBILITY_EXPORTS_PATH.read_text(encoding="utf-8") == _toml_text(
        report
    )


def run(check: bool = False) -> int:
    report = build_core_compatibility_export_report()
    failures = validate_core_compatibility_exports()
    if failures:
        for failure in failures:
            print(failure)
        return 1
    if check:
        if _is_up_to_date(report):
            print(
                f"core compatibility export report is up to date for {len(report.entries)} wrappers"
            )
            return 0
        print("core compatibility export report is stale; regenerate it")
        return 1
    CORE_COMPATIBILITY_EXPORTS_PATH.write_text(_toml_text(report), encoding="utf-8")
    print(
        f"generated core compatibility export report for {len(report.entries)} wrappers"
    )
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate or validate the core compatibility export report."
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Fail if the compatibility export report is not up to date.",
    )
    args = parser.parse_args()
    raise SystemExit(run(check=args.check))
