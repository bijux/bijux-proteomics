# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

import ast
import importlib
from pathlib import Path

_BENCHMARK_ROOT = (
    Path(__file__).resolve().parents[2] / "src" / "bijux_proteomics" / "benchmarks"
)


def _significant_nodes(path: Path) -> list[ast.stmt]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    nodes = list(tree.body)
    if (
        nodes
        and isinstance(nodes[0], ast.Expr)
        and isinstance(nodes[0].value, ast.Constant)
        and isinstance(nodes[0].value.value, str)
    ):
        nodes = nodes[1:]
    return [
        node
        for node in nodes
        if not (isinstance(node, ast.ImportFrom) and node.module == "__future__")
    ]


def test_benchmark_weak_evidence_wrapper_stays_thin() -> None:
    path = _BENCHMARK_ROOT / "weak_evidence.py"
    nodes = _significant_nodes(path)

    assert nodes
    assert all(isinstance(node, ast.ImportFrom) for node in nodes), (
        "benchmarks/weak_evidence.py should stay a thin compatibility facade"
    )
    assert any(
        node.module == "bijux_proteomics.workflow.pipelines.benchmarking.weak_evidence"
        for node in nodes
        if isinstance(node, ast.ImportFrom)
    )


def test_benchmark_modules_import_weak_evidence_pipeline_owner_directly() -> None:
    violations: list[str] = []

    for path in sorted(_BENCHMARK_ROOT.rglob("*.py")):
        if path == _BENCHMARK_ROOT / "weak_evidence.py":
            continue
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if (
                isinstance(node, ast.ImportFrom)
                and node.module == "bijux_proteomics.workflow.weak_evidence"
            ):
                violations.append(
                    f"{path.relative_to(_BENCHMARK_ROOT)} imports bijux_proteomics.workflow.weak_evidence instead of the pipeline owner module"
                )
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name == "bijux_proteomics.workflow.weak_evidence":
                        violations.append(
                            f"{path.relative_to(_BENCHMARK_ROOT)} imports bijux_proteomics.workflow.weak_evidence instead of the pipeline owner module"
                        )

    assert not violations, "\n".join(violations)


def test_benchmark_weak_evidence_exports_delegate_to_pipeline_owner() -> None:
    benchmark_module = importlib.import_module(
        "bijux_proteomics.benchmarks.weak_evidence"
    )
    workflow_module = importlib.import_module(
        "bijux_proteomics.workflow.pipelines.benchmarking.weak_evidence"
    )

    assert (
        benchmark_module.run_weak_evidence_benchmark
        is workflow_module.run_weak_evidence_benchmark
    )
    assert (
        benchmark_module.build_flagship_weak_evidence_benchmark_descriptor
        is workflow_module.build_flagship_weak_evidence_benchmark_descriptor
    )
    assert (
        benchmark_module.render_weak_evidence_benchmark_summary_tsv
        is workflow_module.render_weak_evidence_benchmark_summary_tsv
    )
