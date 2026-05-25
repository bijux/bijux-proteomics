# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

import ast
from pathlib import Path


CLI_ROOT = Path(__file__).resolve().parents[2] / "src" / "bijux_proteomics" / "interfaces" / "cli"
COMMANDS_ROOT = CLI_ROOT / "commands"


def test_cli_python_files_stay_under_eight_hundred_lines() -> None:
    violations: list[str] = []
    for path in sorted(CLI_ROOT.rglob("*.py")):
        line_count = sum(1 for _ in path.open(encoding="utf-8"))
        if line_count > 800:
            violations.append(
                f"{path.relative_to(CLI_ROOT)} has {line_count} lines"
            )
    assert not violations, "\n".join(violations)


def test_click_command_wrappers_stay_thin() -> None:
    violations: list[str] = []
    for path in sorted(COMMANDS_ROOT.glob("*.py")):
        if path.name == "__init__.py":
            continue
        module = ast.parse(path.read_text(encoding="utf-8"))
        run_functions = {
            node.name
            for node in module.body
            if isinstance(node, ast.FunctionDef) and node.name.startswith("run_")
        }
        for node in module.body:
            if (
                not isinstance(node, ast.FunctionDef)
                or not node.name.endswith("_command")
                or node.name.startswith("run_")
            ):
                continue
            if f"run_{node.name}" not in run_functions:
                violations.append(
                    f"{path.name}:{node.name} is missing its run_{node.name} helper"
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
                and call.func.id == f"run_{node.name}"
            ):
                violations.append(
                    f"{path.name}:{node.name} does not return run_{node.name}(...)"
                )
    assert not violations, "\n".join(violations)
