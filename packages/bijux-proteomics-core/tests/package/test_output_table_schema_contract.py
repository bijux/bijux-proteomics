# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

import ast
from pathlib import Path

import pytest

SOURCE_ROOT = Path(__file__).resolve().parents[2] / "src" / "bijux_proteomics"

MODULE_LOCAL_TSV_WRITE_HELPERS = {
    "workflow/exports/targeted_review_workflow.py": {"_write_text"},
}


def _call_target_name(node: ast.AST) -> str | None:
    if isinstance(node, ast.Call):
        if isinstance(node.func, ast.Name):
            return node.func.id
        if isinstance(node.func, ast.Attribute):
            return node.func.attr
    return None


@pytest.mark.slow
def test_direct_tsv_writes_do_not_bypass_output_table_validation() -> None:
    offenders: list[str] = []
    for path in SOURCE_ROOT.rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            if not (
                isinstance(node.func, ast.Attribute) and node.func.attr == "write_text"
            ):
                continue
            if not node.args:
                continue
            rendered = node.args[0]
            target_name = _call_target_name(rendered)
            if target_name is None:
                continue
            if target_name.startswith("render_") and target_name.endswith("_tsv"):
                offenders.append(
                    f"{path.relative_to(SOURCE_ROOT)}:{node.lineno}:{target_name}"
                )
    assert offenders == []


@pytest.mark.slow
def test_tsv_exporters_route_rendered_tables_through_output_table_helper() -> None:
    offenders: list[str] = []
    for path in SOURCE_ROOT.rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if not isinstance(node, ast.FunctionDef):
                continue
            if not node.name.startswith(("export_", "write_")):
                continue
            rendered_tsv_calls = {
                _call_target_name(child)
                for child in ast.walk(node)
                if isinstance(child, ast.Call)
            }
            rendered_tsv_calls.discard(None)
            if not any(
                name is not None
                and name.startswith("render_")
                and name.endswith("_tsv")
                for name in rendered_tsv_calls
            ):
                continue
            allowed_helpers = {
                "write_output_table_tsv",
                "_write_text_output",
                *MODULE_LOCAL_TSV_WRITE_HELPERS.get(
                    path.relative_to(SOURCE_ROOT).as_posix(),
                    set(),
                ),
            }
            if allowed_helpers.intersection(rendered_tsv_calls):
                continue
            offenders.append(
                f"{path.relative_to(SOURCE_ROOT)}:{node.lineno}:{node.name}"
            )
    assert offenders == []
