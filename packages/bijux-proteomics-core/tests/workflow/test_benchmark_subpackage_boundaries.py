# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

import ast
import importlib
from pathlib import Path

_BENCHMARK_ROOT = (
    Path(__file__).resolve().parents[2]
    / "src"
    / "bijux_proteomics"
    / "workflow"
    / "benchmarks"
)
_BENCHMARK_ROOT_WRAPPERS = {
    "diann_benchmarks.py": (
        "bijux_proteomics.workflow.benchmarks.fidelity.diann_benchmarks"
    ),
    "maxquant_benchmarks.py": (
        "bijux_proteomics.workflow.benchmarks.fidelity.maxquant_benchmarks"
    ),
    "public_benchmark_descriptors.py": (
        "bijux_proteomics.workflow.benchmarks.datasets.public_benchmark_descriptors"
    ),
    "public_benchmark_subset.py": (
        "bijux_proteomics.workflow.benchmarks.datasets.public_benchmark_subset"
    ),
    "synthetic_quant_truth.py": (
        "bijux_proteomics.workflow.benchmarks.synthetic.synthetic_quant_truth"
    ),
}


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


def test_benchmark_root_wrappers_stay_thin_nested_facades() -> None:
    for filename, expected_target in _BENCHMARK_ROOT_WRAPPERS.items():
        nodes = _significant_nodes(_BENCHMARK_ROOT / filename)
        assert nodes, f"{filename} should contain a compatibility re-export"
        assert all(isinstance(node, ast.ImportFrom) for node in nodes), (
            f"{filename} should stay a thin compatibility facade"
        )
        assert any(
            node.module == expected_target
            for node in nodes
            if isinstance(node, ast.ImportFrom)
        ), f"{filename} should re-export its canonical benchmark owner"


def test_benchmark_subpackages_export_representative_owner_surfaces() -> None:
    datasets = importlib.import_module("bijux_proteomics.workflow.benchmarks.datasets")
    fidelity = importlib.import_module("bijux_proteomics.workflow.benchmarks.fidelity")
    synthetic = importlib.import_module("bijux_proteomics.workflow.benchmarks.synthetic")

    assert hasattr(datasets, "PublicBenchmarkDescriptor")
    assert hasattr(datasets, "load_public_benchmark_descriptor")
    assert hasattr(datasets, "build_public_benchmark_subset")
    assert hasattr(fidelity, "build_diann_benchmark_report")
    assert hasattr(fidelity, "render_diann_benchmark_summary_tsv")
    assert hasattr(fidelity, "build_maxquant_benchmark_report")
    assert hasattr(fidelity, "render_maxquant_benchmark_summary_tsv")
    assert hasattr(synthetic, "generate_quant_truth_dataset")
    assert hasattr(synthetic, "render_synthetic_quant_truth_tsv")
