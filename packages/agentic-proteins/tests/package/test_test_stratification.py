# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

import ast
from pathlib import Path

from agentic_proteins_testsupport.paths import package_tests_root, repo_root


def _iter_test_files(root: Path) -> list[Path]:
    if not root.exists():
        return []
    return [path for path in root.rglob("test_*.py") if path.is_file()]


def test_owner_tests_do_not_import_legacy_execution_aliases() -> None:
    root = package_tests_root()
    for path in _iter_test_files(root):
        if "package" in path.parts or "execution" in path.parts:
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
                if name.startswith("agentic_proteins.execution"):
                    raise AssertionError(
                        f"Owner tests may not import legacy execution aliases: {path}"
                    )


def test_e2e_tests_use_local_executor_only() -> None:
    root = package_tests_root() / "e2e"
    for path in _iter_test_files(root):
        content = path.read_text()
        if "agentic_proteins.orchestration.runtime.executor import" in content:
            for line in content.splitlines():
                if (
                    "agentic_proteins.orchestration.runtime.executor import" in line
                    and (
                        "LocalExecutor" not in line
                        or "Executor" in line.replace("LocalExecutor", "")
                    )
                ):
                    raise AssertionError(
                        f"E2E tests must import LocalExecutor only: {path}"
                    )
        if (
            "agentic_proteins.orchestration.runtime.executor.Executor" in content
            or "agentic_proteins.execution.runtime.executor.Executor" in content
        ):
            raise AssertionError(f"E2E tests must not use Executor directly: {path}")


def test_no_markdown_in_src_tree() -> None:
    root = repo_root()
    src_dirs = [
        root / "packages" / "agentic-proteins" / "src",
        root / "packages" / "bijux-proteomics-core" / "src",
        root / "packages" / "bijux-proteomics-lab" / "src",
        root / "packages" / "bijux-proteomics-knowledge" / "src",
    ]
    md_files = [
        path
        for src_dir in src_dirs
        if src_dir.exists()
        for path in src_dir.rglob("*.md")
    ]
    if md_files:
        raise AssertionError(f"Markdown files must live in docs/: {md_files[:3]}")
