# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

import ast
from pathlib import Path

from bijux_proteomics import domain

SOURCE_ROOT = Path(__file__).resolve().parents[2] / "src" / "bijux_proteomics"

ERROR_OWNER_PATHS = (
    "workflow/benchmarks/public_benchmark_descriptors.py",
    "workflow/result_archive.py",
    "workflow/studies/study_result.py",
    "review/structure_reports/render.py",
    "targeted/result_validation.py",
    "interfaces/support/timecourse_support/timepoint_order.py",
)


def test_owned_scientific_failure_surfaces_do_not_raise_bare_value_error() -> None:
    offenders: list[str] = []
    for relative_path in ERROR_OWNER_PATHS:
        tree = ast.parse((SOURCE_ROOT / relative_path).read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if not isinstance(node, ast.Raise):
                continue
            if node.exc is None:
                continue
            if (
                isinstance(node.exc, ast.Call)
                and isinstance(node.exc.func, ast.Name)
                and node.exc.func.id == "ValueError"
            ):
                offenders.append(f"{relative_path}:{node.lineno}")
    assert offenders == []


def test_domain_package_exports_standardized_error_classes() -> None:
    for name in (
        "SchemaError",
        "DesignError",
        "ScientificEvidenceError",
        "UnsupportedFormatError",
        "InvalidWorkflowError",
    ):
        assert hasattr(domain, name)
