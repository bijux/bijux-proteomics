from __future__ import annotations

import ast
from dataclasses import dataclass
from pathlib import Path

from bijux_proteomics_dev.governance.runtime.topology import REPO_ROOT
from bijux_proteomics_dev.governance.support.workspace_inventory import (
    package_test_modules,
    workspace_package_names,
)

__all__ = [
    "HiddenSkipUsage",
    "build_hidden_skip_usages",
    "validate_test_skip_policy",
]

_RAW_SKIP_APIS = frozenset({"skip", "importorskip"})


@dataclass(frozen=True)
class HiddenSkipUsage:
    """One raw skip API call that bypasses the shared skip policy helper."""

    path: Path
    line_number: int
    api_name: str


def build_hidden_skip_usages(
    repo_root: Path = REPO_ROOT,
) -> tuple[HiddenSkipUsage, ...]:
    usages: list[HiddenSkipUsage] = []
    for package_name in workspace_package_names():
        for path in package_test_modules(package_name):
            if repo_root not in path.parents:
                continue
            usages.extend(_raw_skip_usages_in_test_module(path))
    return tuple(sorted(usages, key=lambda usage: (str(usage.path), usage.line_number)))


def validate_test_skip_policy(repo_root: Path = REPO_ROOT) -> tuple[str, ...]:
    return tuple(
        (
            f"{usage.path.relative_to(repo_root).as_posix()}:{usage.line_number} "
            f"uses raw pytest.{usage.api_name}; route skips through "
            "bijux_proteomics_foundation.testing.skip_policy"
        )
        for usage in build_hidden_skip_usages(repo_root)
    )


def _raw_skip_usages_in_test_module(path: Path) -> tuple[HiddenSkipUsage, ...]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    pytest_aliases = _pytest_module_aliases(tree)
    pytest_function_aliases = _pytest_function_aliases(tree)
    usages: list[HiddenSkipUsage] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        api_name = _raw_skip_api_name(
            node.func, pytest_aliases, pytest_function_aliases
        )
        if api_name is None:
            continue
        usages.append(
            HiddenSkipUsage(
                path=path,
                line_number=node.lineno,
                api_name=api_name,
            )
        )
    return tuple(usages)


def _pytest_module_aliases(tree: ast.AST) -> set[str]:
    aliases = {"pytest"}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name == "pytest":
                    aliases.add(alias.asname or alias.name)
    return aliases


def _pytest_function_aliases(tree: ast.AST) -> dict[str, str]:
    aliases: dict[str, str] = {}
    for node in ast.walk(tree):
        if not isinstance(node, ast.ImportFrom) or node.module != "pytest":
            continue
        for alias in node.names:
            if alias.name in _RAW_SKIP_APIS:
                aliases[alias.asname or alias.name] = alias.name
    return aliases


def _raw_skip_api_name(
    function: ast.expr,
    pytest_aliases: set[str],
    pytest_function_aliases: dict[str, str],
) -> str | None:
    if (
        isinstance(function, ast.Attribute)
        and isinstance(function.value, ast.Name)
        and function.value.id in pytest_aliases
        and function.attr in _RAW_SKIP_APIS
    ):
        return function.attr
    if isinstance(function, ast.Name):
        return pytest_function_aliases.get(function.id)
    return None
