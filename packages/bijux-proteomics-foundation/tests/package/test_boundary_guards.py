# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

import ast
import importlib
from pathlib import Path

FOUNDATION_SRC_ROOT = Path(
    "packages/bijux-proteomics-foundation/src/bijux_proteomics_foundation"
)
FOUNDATION_TEST_ROOT = Path("packages/bijux-proteomics-foundation/tests")
FORBIDDEN_ENGINE_TOKENS = {"adapter", "engine"}
FORBIDDEN_ORCHESTRATION_TOKENS = {
    "workflow",
    "orchestration",
    "runner",
    "provider",
    "scheduler",
    "container",
}
FORBIDDEN_SCIENTIFIC_TOKENS = {
    "modification",
    "enzyme",
    "instrument",
    "assay_type",
    "controlledvocabulary",
}
FORBIDDEN_PRESENTATION_TOKENS = {
    "apirouter",
    "apiresponse",
    "cli",
    "console",
    "markdown",
    "formatter",
    "render",
    "response",
    "route",
    "router",
}
PRIVATE_PRESENTATION_COMPATIBILITY_MODULES = {"_package_aliases"}
FORBIDDEN_RUNTIME_TRANSPORT_TOKENS = {
    "artifactformat",
    "schemaformatcompatibilityreport",
    "schemaformatcontract",
}
FORBIDDEN_THIN_MODULE_STEMS = {"evolution", "nullability", "primitives"}
FORBIDDEN_HIGHER_LAYER_IMPORTS = (
    "agentic_proteins",
    "bijux_proteomics.",
    "bijux_proteomics_runtime",
    "bijux_proteomics_intelligence",
    "bijux_proteomics_knowledge",
    "bijux_proteomics_lab",
)


def _python_files(root: Path) -> list[Path]:
    return sorted(path for path in root.rglob("*.py") if path.name != "py.typed")


def _load_tree(path: Path) -> ast.AST:
    return ast.parse(path.read_text(), filename=str(path))


def _defined_names(tree: ast.AST) -> list[str]:
    return [
        node.name.lower()
        for node in ast.walk(tree)
        if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef))
    ]


def _imported_modules(tree: ast.AST) -> list[str]:
    modules: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.extend(alias.name for alias in node.names)
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            modules.append(node.module)
    return modules


def test_foundation_excludes_proteomics_engine_adapter_surfaces() -> None:
    violations: list[str] = []
    for path in _python_files(FOUNDATION_SRC_ROOT):
        tree = _load_tree(path)
        stem = path.stem.lower()
        defined_names = _defined_names(tree)
        if any(token in stem for token in FORBIDDEN_ENGINE_TOKENS):
            violations.append(str(path.relative_to(FOUNDATION_SRC_ROOT)))
            continue
        if any(
            any(token in name for token in FORBIDDEN_ENGINE_TOKENS)
            for name in defined_names
        ):
            violations.append(str(path.relative_to(FOUNDATION_SRC_ROOT)))
    assert violations == []


def test_foundation_excludes_workflow_orchestration_surfaces() -> None:
    violations: list[str] = []
    for path in _python_files(FOUNDATION_SRC_ROOT):
        tree = _load_tree(path)
        stem = path.stem.lower()
        defined_names = _defined_names(tree)
        if any(token in stem for token in FORBIDDEN_ORCHESTRATION_TOKENS):
            violations.append(str(path.relative_to(FOUNDATION_SRC_ROOT)))
            continue
        if any(
            any(token in name for token in FORBIDDEN_ORCHESTRATION_TOKENS)
            for name in defined_names
        ):
            violations.append(str(path.relative_to(FOUNDATION_SRC_ROOT)))
    assert violations == []


def test_foundation_excludes_scientific_vocabulary_surfaces() -> None:
    violations: list[str] = []
    for path in _python_files(FOUNDATION_SRC_ROOT):
        tree = _load_tree(path)
        stem = path.stem.lower()
        defined_names = _defined_names(tree)
        if stem == "vocabulary":
            violations.append(str(path.relative_to(FOUNDATION_SRC_ROOT)))
            continue
        if any(
            any(token in name for token in FORBIDDEN_SCIENTIFIC_TOKENS)
            for name in defined_names
        ):
            violations.append(str(path.relative_to(FOUNDATION_SRC_ROOT)))
    assert violations == []


def test_foundation_excludes_api_and_cli_formatting_surfaces() -> None:
    violations: list[str] = []
    for path in _python_files(FOUNDATION_SRC_ROOT):
        tree = _load_tree(path)
        stem = path.stem.lower()
        if stem in PRIVATE_PRESENTATION_COMPATIBILITY_MODULES:
            continue
        defined_names = _defined_names(tree)
        if stem in {"api", "cli", "render"}:
            violations.append(str(path.relative_to(FOUNDATION_SRC_ROOT)))
            continue
        if any(
            any(token in name for token in FORBIDDEN_PRESENTATION_TOKENS)
            for name in defined_names
        ):
            violations.append(str(path.relative_to(FOUNDATION_SRC_ROOT)))
    assert violations == []


def test_foundation_excludes_runtime_transport_contract_surfaces() -> None:
    violations: list[str] = []
    for path in _python_files(FOUNDATION_SRC_ROOT):
        tree = _load_tree(path)
        stem = path.stem.lower()
        defined_names = _defined_names(tree)
        if stem == "formats":
            violations.append(str(path.relative_to(FOUNDATION_SRC_ROOT)))
            continue
        if any(
            any(token in name for token in FORBIDDEN_RUNTIME_TRANSPORT_TOKENS)
            for name in defined_names
        ):
            violations.append(str(path.relative_to(FOUNDATION_SRC_ROOT)))
    assert violations == []


def test_foundation_excludes_thin_standalone_contract_modules() -> None:
    thin_modules = sorted(
        path.relative_to(FOUNDATION_SRC_ROOT)
        for path in FOUNDATION_SRC_ROOT.glob("*.py")
        if path.stem in FORBIDDEN_THIN_MODULE_STEMS
    )

    assert thin_modules == []


def test_foundation_does_not_import_higher_layer_packages() -> None:
    violations: list[str] = []
    for path in _python_files(FOUNDATION_SRC_ROOT):
        tree = _load_tree(path)
        imported_modules = _imported_modules(tree)
        for module in imported_modules:
            if module.startswith("bijux_proteomics_foundation"):
                continue
            if any(
                module.startswith(prefix) for prefix in FORBIDDEN_HIGHER_LAYER_IMPORTS
            ):
                violations.append(
                    f"{path.relative_to(FOUNDATION_SRC_ROOT)} imports {module}"
                )
    assert violations == []
def test_foundation_root_export_surface_stays_reviewable() -> None:
    module = importlib.import_module("bijux_proteomics_foundation")

    assert len(module.__all__) <= 24
