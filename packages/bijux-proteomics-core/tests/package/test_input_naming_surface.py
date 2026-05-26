# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

import ast
from pathlib import Path

from bijux_proteomics import domain, sequences


SOURCE_ROOT = Path(__file__).resolve().parents[2] / "src" / "bijux_proteomics"

LEGACY_PARSER_WRAPPERS = {
    "domain/structure/structure.py": {
        "load_structure_from_pdb_text": "parse_structure_from_pdb_text",
    },
    "sequences/contaminant_database.py": {
        "load_builtin_contaminant_records": "build_builtin_contaminant_records",
    },
}

EXPECTED_CANONICAL_LOAD_NAMES = {
    "load_annotation_pack",
    "load_generic_psm_table_mapping",
    "load_lazy_proteomics_evidence_graph",
    "load_matrix_archive",
    "load_modification_pack",
    "load_modification_registry",
    "load_protein_index",
    "load_public_benchmark_descriptor",
    "load_qc_threshold_policy",
    "load_result_archive",
    "load_standard_card_index",
    "load_standard_card_tsv",
    "load_surprising_demo_manifest",
    "load_workflow_artifact_manifest",
}

MUTATING_IO_METHODS = {
    "mkdir",
    "rename",
    "replace",
    "rmdir",
    "save",
    "touch",
    "unlink",
    "write_bytes",
    "write_text",
}


def _parse_module(relative_path: str) -> ast.Module:
    return ast.parse((SOURCE_ROOT / relative_path).read_text(encoding="utf-8"))


def _function_node(module: ast.Module, name: str) -> ast.FunctionDef:
    for node in module.body:
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return node
    raise AssertionError(f"missing function {name!r}")


def _function_payload(node: ast.FunctionDef) -> list[ast.stmt]:
    payload: list[ast.stmt] = []
    for statement in node.body:
        if (
            isinstance(statement, ast.Expr)
            and isinstance(statement.value, ast.Constant)
            and isinstance(statement.value.value, str)
        ):
            continue
        payload.append(statement)
    return payload


def _call_target_name(node: ast.AST | None) -> str | None:
    if isinstance(node, ast.Call):
        if isinstance(node.func, ast.Name):
            return node.func.id
        if isinstance(node.func, ast.Attribute):
            return node.func.attr
    return None


def _assert_wrapper(module_path: str, legacy_name: str, canonical_name: str) -> None:
    node = _function_node(_parse_module(module_path), legacy_name)
    payload = [
        statement
        for statement in _function_payload(node)
        if not (
            isinstance(statement, ast.Expr)
            and isinstance(statement.value, ast.Call)
            and _call_target_name(statement.value) == "warn"
        )
    ]
    assert len(payload) == 1, f"{legacy_name} should stay a one-step wrapper"
    statement = payload[0]
    call = statement.value if isinstance(statement, ast.Return) else None
    assert _call_target_name(call) == canonical_name


def test_parse_functions_do_not_write_or_mutate_external_state() -> None:
    offenders: list[str] = []
    for path in SOURCE_ROOT.rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in tree.body:
            if not isinstance(node, ast.FunctionDef) or not node.name.startswith("parse_"):
                continue
            for child in ast.walk(node):
                if not isinstance(child, ast.Call):
                    continue
                if isinstance(child.func, ast.Attribute) and child.func.attr in MUTATING_IO_METHODS:
                    offenders.append(
                        f"{path.relative_to(SOURCE_ROOT)}:{node.lineno}:{node.name}"
                    )
    assert offenders == []


def test_load_function_names_remain_reserved_for_structured_hydration() -> None:
    legacy_wrapper_names = {
        name
        for wrappers in LEGACY_PARSER_WRAPPERS.values()
        for name in wrappers
    }
    found_canonical_names: set[str] = set()
    for path in SOURCE_ROOT.rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in tree.body:
            if not isinstance(node, ast.FunctionDef) or not node.name.startswith("load_"):
                continue
            if node.name in legacy_wrapper_names:
                continue
            found_canonical_names.add(node.name)
    assert found_canonical_names == EXPECTED_CANONICAL_LOAD_NAMES


def test_legacy_load_wrappers_delegate_to_canonical_parser_or_builder_names() -> None:
    for module_path, wrappers in LEGACY_PARSER_WRAPPERS.items():
        for legacy_name, canonical_name in wrappers.items():
            _assert_wrapper(module_path, legacy_name, canonical_name)


def test_package_surfaces_expose_canonical_parser_and_builder_names() -> None:
    assert hasattr(domain, "parse_structure_from_pdb_text")
    assert hasattr(domain, "load_structure_from_pdb_text")
    assert hasattr(sequences, "build_builtin_contaminant_records")
    assert hasattr(sequences, "load_builtin_contaminant_records")
