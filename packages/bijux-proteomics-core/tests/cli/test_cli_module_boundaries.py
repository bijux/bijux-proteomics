# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

import ast
import importlib
from pathlib import Path

CLI_ROOT = (
    Path(__file__).resolve().parents[2]
    / "src"
    / "bijux_proteomics"
    / "interfaces"
    / "cli"
)
COMMANDS_ROOT = CLI_ROOT / "commands"
PYTHON_API_ROOT = (
    Path(__file__).resolve().parents[2]
    / "src"
    / "bijux_proteomics"
    / "interfaces"
    / "python_api"
)


def test_cli_python_files_stay_under_eight_hundred_lines() -> None:
    violations: list[str] = []
    for path in sorted(CLI_ROOT.rglob("*.py")):
        line_count = sum(1 for _ in path.open(encoding="utf-8"))
        if line_count > 800:
            violations.append(f"{path.relative_to(CLI_ROOT)} has {line_count} lines")
    assert not violations, "\n".join(violations)


def test_click_command_wrappers_stay_thin() -> None:
    violations: list[str] = []
    for path in sorted(COMMANDS_ROOT.glob("*.py")):
        if path.name in {"__init__.py", "groups.py"}:
            continue
        module = ast.parse(path.read_text(encoding="utf-8"))
        local_run_functions = {
            node.name
            for node in module.body
            if isinstance(node, ast.FunctionDef) and node.name.startswith("run_")
        }
        if local_run_functions:
            violations.append(
                f"{path.name} still defines local runner functions: {sorted(local_run_functions)}"
            )
        imported_run_functions: set[str] = set()
        for node in module.body:
            if not isinstance(node, ast.ImportFrom):
                continue
            if node.module != f"bijux_proteomics.interfaces.python_api.{path.stem}":
                continue
            imported_run_functions.update(
                alias.asname or alias.name
                for alias in node.names
                if alias.name.startswith("run_")
            )
        expected_api_module = PYTHON_API_ROOT / path.name
        if not expected_api_module.exists():
            violations.append(f"{path.name} is missing {expected_api_module.name}")
            continue
        api_module = importlib.import_module(
            f"bijux_proteomics.interfaces.python_api.{path.stem}"
        )
        for node in module.body:
            if not isinstance(node, ast.FunctionDef) or node.name.startswith("run_"):
                continue
            if node.name.endswith("_command") or node.name in {
                "program_template",
                "summarize_program",
            }:
                runner_name = f"run_{node.name}"
            else:
                continue
            if runner_name not in imported_run_functions:
                violations.append(
                    f"{path.name}:{node.name} is missing imported {runner_name}"
                )
                continue
            if not hasattr(api_module, runner_name):
                violations.append(
                    f"{path.name}:{node.name} is missing {runner_name} on the python api module"
                )
                continue
            body = list(node.body)
            if not body:
                violations.append(f"{path.name}:{node.name} has an empty body")
                continue
            if (
                isinstance(body[0], ast.Expr)
                and isinstance(body[0].value, ast.Constant)
                and isinstance(body[0].value.value, str)
            ):
                body = body[1:]
            if len(body) != 1 or not isinstance(body[0], ast.Return):
                violations.append(
                    f"{path.name}:{node.name} does more than delegate to its runner"
                )
                continue
            call = body[0].value
            if not (
                isinstance(call, ast.Call)
                and isinstance(call.func, ast.Name)
                and call.func.id == runner_name
            ):
                violations.append(
                    f"{path.name}:{node.name} does not return {runner_name}(...)"
                )
    assert not violations, "\n".join(violations)
