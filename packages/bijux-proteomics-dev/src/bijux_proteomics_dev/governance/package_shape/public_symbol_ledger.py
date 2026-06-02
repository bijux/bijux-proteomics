from __future__ import annotations

import argparse
import ast
from dataclasses import dataclass
from functools import cache
import importlib
import inspect
from pathlib import Path

from bijux_proteomics_dev.governance.runtime.topology import REPO_ROOT
from bijux_proteomics_dev.governance.support.workspace_inventory import (
    import_root,
    src_root,
    tests_root,
    workspace_import_path,
    workspace_package_names,
)

__all__ = [
    "PUBLIC_SYMBOL_LEDGER_PATH",
    "PublicSymbolLedgerEntry",
    "PublicSymbolLedgerGuard",
    "PublicSymbolLedgerReport",
    "build_public_symbol_ledger_report",
    "run",
    "validate_public_symbol_ledger",
]


PUBLIC_SYMBOL_LEDGER_PATH = (
    REPO_ROOT / "configs" / "package-governance" / "public-symbol-ledger.toml"
)


@dataclass(frozen=True)
class PublicSymbolLedgerEntry:
    """One exported root symbol mapped to its real owner module and owner tests."""

    distribution_name: str
    import_root: str
    symbol_name: str
    symbol_kind: str
    owner_distribution_name: str
    owner_module_name: str
    owner_module_path: str
    owner_test_paths: tuple[str, ...]


@dataclass(frozen=True)
class PublicSymbolLedgerGuard:
    """Release-blocking baseline for named public symbols with owner proof."""

    min_public_symbol_count: int
    min_symbols_with_owner_tests: int


@dataclass(frozen=True)
class PublicSymbolLedgerReport:
    """Checked public symbol ledger across workspace package roots."""

    entries: tuple[PublicSymbolLedgerEntry, ...]
    guard: PublicSymbolLedgerGuard


def _relative_repo_path(path: Path) -> str:
    return path.relative_to(REPO_ROOT).as_posix()


def _symbol_kind(value: object) -> str:
    if inspect.ismodule(value):
        return "module"
    if inspect.isclass(value):
        return "class"
    if inspect.isfunction(value) or inspect.ismethod(value) or inspect.isbuiltin(value):
        return "callable"
    return "data"


def _module_export_sources(
    root_module_name: str,
    module_path: Path,
    *,
    visited: frozenset[str] = frozenset(),
) -> dict[str, str]:
    if root_module_name in visited:
        return {}
    tree = ast.parse(module_path.read_text(encoding="utf-8"), filename=str(module_path))
    mapping: dict[str, str] = {}
    runtime_package_name: str | None = None
    def _record_statements(statements: list[ast.stmt]) -> None:
        nonlocal runtime_package_name
        for node in statements:
            if isinstance(node, ast.If):
                _record_statements(node.body)
                _record_statements(node.orelse)
                continue
            if isinstance(node, ast.Try):
                _record_statements(node.body)
                for handler in node.handlers:
                    _record_statements(handler.body)
                _record_statements(node.orelse)
                _record_statements(node.finalbody)
                continue
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if (
                        isinstance(target, ast.Name)
                        and target.id == "_RUNTIME_PACKAGE"
                        and isinstance(node.value, ast.Constant)
                        and isinstance(node.value.value, str)
                    ):
                        runtime_package_name = node.value.value
            if isinstance(node, ast.ImportFrom):
                if node.level == 0:
                    if node.module is None:
                        continue
                    source_module_name = node.module
                else:
                    relative_parts = []
                    if node.module:
                        relative_parts.extend(node.module.split("."))
                    source_module_name = ".".join((root_module_name, *relative_parts))
                for alias in node.names:
                    mapping[alias.asname or alias.name] = source_module_name
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    mapping[alias.asname or alias.name] = alias.name
            elif isinstance(node, ast.Assign) and isinstance(node.value, ast.Dict):
                for key, value in zip(node.value.keys, node.value.values, strict=False):
                    if (
                        not isinstance(key, ast.Constant)
                        or not isinstance(key.value, str)
                    ):
                        continue
                    if isinstance(value, ast.Constant) and isinstance(value.value, str):
                        mapping[key.value] = value.value
                    elif (
                        isinstance(value, ast.Tuple)
                        and value.elts
                        and isinstance(value.elts[0], ast.Constant)
                        and isinstance(value.elts[0].value, str)
                    ):
                        mapping[key.value] = value.elts[0].value

    _record_statements(tree.body)
    if runtime_package_name and runtime_package_name != root_module_name:
        runtime_package = importlib.import_module(runtime_package_name)
        runtime_module_file = getattr(runtime_package, "__file__", None)
        if runtime_module_file:
            runtime_module_path = Path(runtime_module_file).resolve()
            mapping.update(
                _module_export_sources(
                    runtime_package_name,
                    runtime_module_path,
                    visited=visited | {root_module_name},
                )
            )
    return mapping


@cache
def _root_export_sources(package_name: str) -> dict[str, str]:
    root_name = import_root(package_name)
    return _module_export_sources(root_name, src_root(package_name) / "__init__.py")


def _owner_module_name(
    import_root_name: str, symbol_name: str, symbol: object, source_map: dict[str, str]
) -> str:
    if symbol_name in source_map:
        return source_map[symbol_name]
    if inspect.ismodule(symbol):
        return symbol.__name__
    return str(getattr(symbol, "__module__", import_root_name))


def _owner_distribution_name(owner_module_name: str, fallback_package_name: str) -> str:
    for package_name in workspace_package_names():
        root_name = import_root(package_name)
        if owner_module_name == root_name or owner_module_name.startswith(
            f"{root_name}."
        ):
            return package_name
    return fallback_package_name


def _owner_module_path(package_name: str, owner_module_name: str) -> str:
    try:
        module = importlib.import_module(owner_module_name)
    except Exception:  # noqa: BLE001
        return ""
    module_file = getattr(module, "__file__", None)
    if not module_file:
        return ""
    path = Path(module_file).resolve()
    if REPO_ROOT not in path.parents and path != REPO_ROOT:
        return ""
    relative = _relative_repo_path(path)
    if not relative.startswith("packages/"):
        return ""
    return relative


def _candidate_owner_test_paths(
    owner_package_name: str,
    symbol_name: str,
    owner_module_name: str,
    owner_module_path: str,
) -> tuple[str, ...]:
    root = tests_root(owner_package_name)
    if not root.exists():
        return ()
    owner_family = ""
    if owner_module_path:
        relative = (REPO_ROOT / owner_module_path).relative_to(
            src_root(owner_package_name).parent
        )
        parts = relative.parts[1:]
        if parts:
            owner_family = parts[0]

    preferred: list[str] = []
    module_owned: list[str] = []
    family_owned: list[str] = []
    fallback: list[str] = []
    for path in sorted(root.rglob("*.py")):
        text = path.read_text(encoding="utf-8")
        relative_path = _relative_repo_path(path)
        tree = ast.parse(text, filename=str(path))
        if owner_family and owner_family in path.parts:
            family_owned.append(relative_path)
        owner_module_imported = False
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module == owner_module_name:
                owner_module_imported = True
                break
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name == owner_module_name:
                        owner_module_imported = True
                        break
            if owner_module_imported:
                break
        if owner_module_imported:
            module_owned.append(relative_path)
        if symbol_name not in text:
            continue
        fallback.append(relative_path)
        if owner_family and owner_family in path.parts:
            preferred.append(relative_path)
    return tuple(preferred or fallback or module_owned or family_owned)


@cache
def build_public_symbol_ledger_report() -> PublicSymbolLedgerReport:
    """Build the public symbol ledger for every exported root symbol."""

    entries: list[PublicSymbolLedgerEntry] = []
    symbols_with_owner_tests = 0
    with workspace_import_path():
        for package_name in workspace_package_names():
            root_name = import_root(package_name)
            module = importlib.import_module(root_name)
            source_map = _root_export_sources(package_name)
            for symbol_name in getattr(module, "__all__", ()):
                value = getattr(module, symbol_name)
                owner_module_name = _owner_module_name(
                    root_name, symbol_name, value, source_map
                )
                owner_distribution_name = _owner_distribution_name(
                    owner_module_name, package_name
                )
                owner_module_path = _owner_module_path(
                    owner_distribution_name,
                    owner_module_name,
                )
                owner_test_paths = _candidate_owner_test_paths(
                    owner_package_name=owner_distribution_name,
                    symbol_name=symbol_name,
                    owner_module_name=owner_module_name,
                    owner_module_path=owner_module_path,
                )
                if owner_test_paths:
                    symbols_with_owner_tests += 1
                entries.append(
                    PublicSymbolLedgerEntry(
                        distribution_name=package_name,
                        import_root=root_name,
                        symbol_name=symbol_name,
                        symbol_kind=_symbol_kind(value),
                        owner_distribution_name=owner_distribution_name,
                        owner_module_name=owner_module_name,
                        owner_module_path=owner_module_path,
                        owner_test_paths=owner_test_paths,
                    )
                )
    entries = sorted(
        entries,
        key=lambda entry: (
            entry.distribution_name,
            entry.symbol_name,
            entry.owner_module_name,
        ),
    )
    return PublicSymbolLedgerReport(
        entries=tuple(entries),
        guard=PublicSymbolLedgerGuard(
            min_public_symbol_count=len(entries),
            min_symbols_with_owner_tests=symbols_with_owner_tests,
        ),
    )


def validate_public_symbol_ledger(
    report: PublicSymbolLedgerReport | None = None,
) -> tuple[str, ...]:
    """Fail release when exported symbols lose named owner modules or owner tests."""

    report = report or build_public_symbol_ledger_report()
    failures: list[str] = []
    symbol_count = len(report.entries)
    symbols_with_owner_tests = sum(
        bool(entry.owner_test_paths) for entry in report.entries
    )
    if symbol_count < report.guard.min_public_symbol_count:
        failures.append("public symbol count dropped below the governed baseline")
    if symbols_with_owner_tests < report.guard.min_symbols_with_owner_tests:
        failures.append(
            "public symbols with owner tests dropped below the governed baseline"
        )
    for entry in report.entries:
        if not entry.owner_module_name:
            failures.append(
                f"{entry.distribution_name}.{entry.symbol_name} is missing a named owner module"
            )
        if not entry.owner_module_path:
            failures.append(
                f"{entry.distribution_name}.{entry.symbol_name} does not resolve to a repo owner module"
            )
        if not entry.owner_test_paths:
            failures.append(
                f"{entry.distribution_name}.{entry.symbol_name} is missing an owner test path"
            )
    return tuple(failures)


def _render_tuple(values: tuple[str, ...]) -> str:
    return ", ".join(f'"{value}"' for value in values)


def _toml_text(report: PublicSymbolLedgerReport) -> str:
    lines = [
        "# Generated public symbol ledger.",
        "# Regenerate with: ./.venv/bin/python -m bijux_proteomics_dev.governance.package_shape.public_symbol_ledger",
        "",
        "[guard]",
        f"min_public_symbol_count = {report.guard.min_public_symbol_count}",
        f"min_symbols_with_owner_tests = {report.guard.min_symbols_with_owner_tests}",
        "",
    ]
    for entry in report.entries:
        lines.extend(
            [
                "[[symbol]]",
                f'distribution_name = "{entry.distribution_name}"',
                f'import_root = "{entry.import_root}"',
                f'name = "{entry.symbol_name}"',
                f'symbol_kind = "{entry.symbol_kind}"',
                f'owner_distribution_name = "{entry.owner_distribution_name}"',
                f'owner_module_name = "{entry.owner_module_name}"',
                f'owner_module_path = "{entry.owner_module_path}"',
                f"owner_test_paths = [{_render_tuple(entry.owner_test_paths)}]",
                "",
            ]
        )
    return "\n".join(lines)


def _is_up_to_date(report: PublicSymbolLedgerReport) -> bool:
    if not PUBLIC_SYMBOL_LEDGER_PATH.exists():
        return False
    return PUBLIC_SYMBOL_LEDGER_PATH.read_text(encoding="utf-8") == _toml_text(report)


def run(check: bool = False) -> int:
    report = build_public_symbol_ledger_report()
    failures = validate_public_symbol_ledger(report)
    if failures:
        for failure in failures:
            print(failure)
        return 1
    if check:
        if _is_up_to_date(report):
            print("public symbol ledger is up to date")
            return 0
        print("public symbol ledger is stale; regenerate it")
        return 1
    PUBLIC_SYMBOL_LEDGER_PATH.write_text(_toml_text(report), encoding="utf-8")
    print("generated public symbol ledger")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate or validate the public symbol ledger."
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Fail if the public symbol ledger is not up to date.",
    )
    args = parser.parse_args()
    raise SystemExit(run(check=args.check))
