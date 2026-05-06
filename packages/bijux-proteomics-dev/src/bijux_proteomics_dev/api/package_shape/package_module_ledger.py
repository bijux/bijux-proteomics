from __future__ import annotations

import argparse
import ast
from dataclasses import dataclass
from pathlib import Path

from bijux_proteomics_dev.api.support.workspace_inventory import (
    import_root,
    is_wrapper_module,
    source_modules,
    src_root,
    tests_root,
    workspace_import_roots_used,
    workspace_package_names,
)
from bijux_proteomics_dev.api.runtime.topology import REPO_ROOT

__all__ = [
    "PACKAGE_MODULE_LEDGER_PATH",
    "PackageModuleLedgerEntry",
    "PackageModuleLedgerGuard",
    "PackageModuleLedgerReport",
    "build_package_module_ledger_report",
    "run",
    "validate_package_module_ledger",
]


PACKAGE_MODULE_LEDGER_PATH = (
    REPO_ROOT / "configs" / "package-governance" / "package-module-ledger.toml"
)


@dataclass(frozen=True)
class PackageModuleLedgerEntry:
    """One classified source or test module in the workspace."""

    distribution_name: str
    module_path: str
    module_import_path: str
    module_kind: str
    public_definition_count: int
    workspace_import_root_count: int


@dataclass(frozen=True)
class PackageModuleLedgerGuard:
    """Release-blocking baseline over classified module shapes."""

    min_owner_logic_module_count: int
    max_compatibility_surface_count: int
    max_import_glue_module_count: int
    max_dead_weight_module_count: int


@dataclass(frozen=True)
class PackageModuleLedgerReport:
    """Checked classified module ledger across repository packages."""

    entries: tuple[PackageModuleLedgerEntry, ...]
    guard: PackageModuleLedgerGuard


def _relative_module_path(path: Path) -> str:
    return path.relative_to(REPO_ROOT).as_posix()


def _source_module_import_path(package_name: str, path: Path) -> str:
    relative = path.relative_to(src_root(package_name)).with_suffix("")
    parts = list(relative.parts)
    if parts and parts[-1] == "__init__":
        parts = parts[:-1]
    return ".".join((import_root(package_name), *parts))


def _test_module_import_path(package_name: str, path: Path) -> str:
    relative = path.relative_to(tests_root(package_name)).with_suffix("")
    return ".".join(("tests", package_name.replace("-", "_"), *relative.parts))


def _test_python_modules(package_name: str) -> tuple[Path, ...]:
    root = tests_root(package_name)
    if not root.exists():
        return ()
    return tuple(sorted(path for path in root.rglob("*.py") if path.is_file()))


def _parse(path: Path) -> ast.Module:
    return ast.parse(path.read_text(encoding="utf-8"), filename=str(path))


def _public_definition_count(path: Path) -> int:
    tree = _parse(path)
    return sum(
        isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
        and not node.name.startswith("_")
        for node in tree.body
    )


def _has_runtime_logic(path: Path) -> bool:
    tree = _parse(path)
    return any(
        isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
        for node in tree.body
    )


def _is_import_glue_module(path: Path) -> bool:
    tree = _parse(path)
    if _has_runtime_logic(path):
        return False
    allowed_nodes = (
        ast.Assign,
        ast.Expr,
        ast.Import,
        ast.ImportFrom,
        ast.Pass,
        ast.AnnAssign,
    )
    return all(isinstance(node, allowed_nodes) for node in tree.body)


def _classify_source_module(package_name: str, path: Path) -> str:
    relative = path.relative_to(src_root(package_name))
    if relative == Path("__init__.py"):
        return "root_export_surface"
    if path.name == "__init__.py" and _is_import_glue_module(path):
        return "import_glue"
    if path.parent == src_root(package_name) and is_wrapper_module(path):
        return "compatibility_surface"
    if _is_import_glue_module(path):
        return "import_glue"
    if _public_definition_count(path) == 0 and not workspace_import_roots_used(path):
        return "dead_weight"
    return "owner_logic"


def build_package_module_ledger_report() -> PackageModuleLedgerReport:
    """Build the machine-readable module ledger across source and tests."""

    entries: list[PackageModuleLedgerEntry] = []
    owner_logic_module_count = 0
    compatibility_surface_count = 0
    import_glue_module_count = 0
    dead_weight_module_count = 0

    for package_name in workspace_package_names():
        for path in source_modules(package_name):
            module_kind = _classify_source_module(package_name, path)
            if module_kind == "owner_logic":
                owner_logic_module_count += 1
            elif module_kind == "compatibility_surface":
                compatibility_surface_count += 1
            elif module_kind == "import_glue":
                import_glue_module_count += 1
            elif module_kind == "dead_weight":
                dead_weight_module_count += 1
            entries.append(
                PackageModuleLedgerEntry(
                    distribution_name=package_name,
                    module_path=_relative_module_path(path),
                    module_import_path=_source_module_import_path(package_name, path),
                    module_kind=module_kind,
                    public_definition_count=_public_definition_count(path),
                    workspace_import_root_count=len(workspace_import_roots_used(path)),
                )
            )
        for path in _test_python_modules(package_name):
            entries.append(
                PackageModuleLedgerEntry(
                    distribution_name=package_name,
                    module_path=_relative_module_path(path),
                    module_import_path=_test_module_import_path(package_name, path),
                    module_kind="test_only_helper",
                    public_definition_count=_public_definition_count(path),
                    workspace_import_root_count=len(workspace_import_roots_used(path)),
                )
            )

    return PackageModuleLedgerReport(
        entries=tuple(
            sorted(entries, key=lambda entry: (entry.distribution_name, entry.module_path))
        ),
        guard=PackageModuleLedgerGuard(
            min_owner_logic_module_count=owner_logic_module_count,
            max_compatibility_surface_count=compatibility_surface_count,
            max_import_glue_module_count=import_glue_module_count,
            max_dead_weight_module_count=dead_weight_module_count,
        ),
    )


def validate_package_module_ledger(
    report: PackageModuleLedgerReport | None = None,
) -> tuple[str, ...]:
    """Fail release when owner logic shrinks or low-substance module kinds grow."""

    report = report or build_package_module_ledger_report()
    owner_logic_module_count = sum(
        entry.module_kind == "owner_logic" for entry in report.entries
    )
    compatibility_surface_count = sum(
        entry.module_kind == "compatibility_surface" for entry in report.entries
    )
    import_glue_module_count = sum(
        entry.module_kind == "import_glue" for entry in report.entries
    )
    dead_weight_module_count = sum(
        entry.module_kind == "dead_weight" for entry in report.entries
    )
    failures: list[str] = []
    if owner_logic_module_count < report.guard.min_owner_logic_module_count:
        failures.append("owner logic module count dropped below the governed baseline")
    if compatibility_surface_count > report.guard.max_compatibility_surface_count:
        failures.append("compatibility surface count grew beyond the governed baseline")
    if import_glue_module_count > report.guard.max_import_glue_module_count:
        failures.append("import-glue module count grew beyond the governed baseline")
    if dead_weight_module_count > report.guard.max_dead_weight_module_count:
        failures.append("dead-weight module count grew beyond the governed baseline")
    return tuple(failures)


def _toml_text(report: PackageModuleLedgerReport) -> str:
    lines = [
        "# Generated package module ledger.",
        "# Regenerate with: ./.venv/bin/python -m bijux_proteomics_dev.api.package_shape.package_module_ledger",
        "",
        "[guard]",
        f"min_owner_logic_module_count = {report.guard.min_owner_logic_module_count}",
        f"max_compatibility_surface_count = {report.guard.max_compatibility_surface_count}",
        f"max_import_glue_module_count = {report.guard.max_import_glue_module_count}",
        f"max_dead_weight_module_count = {report.guard.max_dead_weight_module_count}",
        "",
    ]
    for entry in report.entries:
        lines.extend(
            [
                "[[module]]",
                f'distribution_name = "{entry.distribution_name}"',
                f'module_path = "{entry.module_path}"',
                f'module_import_path = "{entry.module_import_path}"',
                f'module_kind = "{entry.module_kind}"',
                f"public_definition_count = {entry.public_definition_count}",
                f"workspace_import_root_count = {entry.workspace_import_root_count}",
                "",
            ]
        )
    return "\n".join(lines)


def _is_up_to_date(report: PackageModuleLedgerReport) -> bool:
    if not PACKAGE_MODULE_LEDGER_PATH.exists():
        return False
    return PACKAGE_MODULE_LEDGER_PATH.read_text(encoding="utf-8") == _toml_text(report)


def run(check: bool = False) -> int:
    report = build_package_module_ledger_report()
    failures = validate_package_module_ledger(report)
    if failures:
        for failure in failures:
            print(failure)
        return 1
    if check:
        if _is_up_to_date(report):
            print("package module ledger is up to date")
            return 0
        print("package module ledger is stale; regenerate it")
        return 1
    PACKAGE_MODULE_LEDGER_PATH.write_text(_toml_text(report), encoding="utf-8")
    print("generated package module ledger")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate or validate the package module ledger."
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Fail if the package module ledger is not up to date.",
    )
    args = parser.parse_args()
    raise SystemExit(run(check=args.check))
