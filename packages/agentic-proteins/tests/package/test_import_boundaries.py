# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

import ast
from pathlib import Path

from agentic_proteins_testsupport.paths import package_tests_root, repo_root

LAYER_ORDER = {
    "cli": 7,
    "interfaces": 7,
    "httpapi": 7,
    "orchestration": 5,
    "execution": 5,
    "agents": 4,
    "planning": 3,
    "tools": 2,
    "providers": 2,
    "core": 1,
    "domain": 1,
    "memory": 1,
    "state": 1,
    "utils": 1,
}

ALLOWED_TOP_LEVEL_ENTRIES = {
    "__init__.py",
    "agents",
    "orchestration",
    "execution",
    "interfaces",
    "providers",
    "py.typed",
    "state",
    "tools",
}

REMOVED_COMPAT_FAMILIES = {
    "api",
    "biology",
    "core",
    "design_loop",
    "domain",
    "memory",
    "registry",
    "report",
    "runtime",
    "validation",
}


def _module_layer(path: Path) -> int | None:
    parts = path.parts
    if "agentic_proteins" not in parts:
        return None
    idx = parts.index("agentic_proteins")
    if idx + 1 >= len(parts):
        return None
    part = parts[idx + 1]
    if part.endswith(".py"):
        part = part[:-3]
    return LAYER_ORDER.get(part)


def test_import_boundaries() -> None:
    root = repo_root() / "packages" / "agentic-proteins" / "src" / "agentic_proteins"
    for path in root.rglob("*.py"):
        layer = _module_layer(path)
        if layer is None:
            continue
        tree = ast.parse(path.read_text(), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                names = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom) and node.module:
                names = [node.module]
            else:
                continue
            for name in names:
                if not name.startswith("agentic_proteins."):
                    continue
                target_pkg = name.split(".")[1]
                target_layer = LAYER_ORDER.get(target_pkg)
                if target_layer is None:
                    continue
                if target_layer > layer:
                    raise AssertionError(
                        f"Forbidden import {name} in {path} (layer {layer} -> {target_layer})"
                    )


def test_package_root_uses_one_bridge_vocabulary() -> None:
    root = repo_root() / "packages" / "agentic-proteins" / "src" / "agentic_proteins"
    actual_entries = {
        path.name for path in root.iterdir() if path.name != "__pycache__"
    }

    assert actual_entries <= ALLOWED_TOP_LEVEL_ENTRIES
    assert not (actual_entries & REMOVED_COMPAT_FAMILIES)


def test_removed_compat_families_stay_deleted() -> None:
    root = repo_root() / "packages" / "agentic-proteins" / "src" / "agentic_proteins"
    for family in REMOVED_COMPAT_FAMILIES:
        assert not (root / family).exists(), family


def test_package_root_mirrors_runtime_root_exports() -> None:
    import agentic_proteins
    import bijux_proteomics_runtime

    assert agentic_proteins.__all__ == list(bijux_proteomics_runtime.__all__)
    for name in bijux_proteomics_runtime.__all__:
        assert getattr(agentic_proteins, name) is getattr(
            bijux_proteomics_runtime, name
        )
    assert agentic_proteins.__version__


def test_high_level_tests_use_public_entrypoints() -> None:
    root = package_tests_root()
    allowed_prefixes = (
        "agentic_proteins.interfaces",
        "agentic_proteins.orchestration",
        "agentic_proteins.execution",
        "agentic_proteins.state",
        "agentic_proteins.tools",
        "agentic_proteins.providers",
        "agentic_proteins.agents",
    )
    for path in (root / "e2e").rglob("test_*.py"):
        tree = ast.parse(path.read_text(), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                names = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom) and node.module:
                names = [node.module]
            else:
                continue
            for name in names:
                if not name.startswith("agentic_proteins."):
                    continue
                if not name.startswith(allowed_prefixes):
                    raise AssertionError(
                        f"Test imports must use public entrypoints: {name} in {path}"
                    )
