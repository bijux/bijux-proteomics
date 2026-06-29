# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

import ast
from pathlib import Path

import pytest

CORE_SRC_ROOT = Path("packages/bijux-proteomics-core/src/bijux_proteomics")
ALLOWED_RUNTIME_IMPORTS = {
    "interfaces/execution/runtime_adapter.py": {
        "bijux_proteomics_runtime.runs",
    },
    "interfaces/runtime_plans.py": {
        "bijux_proteomics_runtime.workflows",
    },
}
ALLOWED_CROSS_PACKAGE_IMPORTS = {
    "benchmarks/flagship_acceptance.py": {
        "bijux_proteomics_intelligence.reviews.benchmarks",
        "bijux_proteomics_knowledge.references.workflows.benchmarks",
        "bijux_proteomics_knowledge.references.workflows.comparator_failures",
        "bijux_proteomics_knowledge.references.workflows.scientific_thresholds",
    },
    "ptm/cards/review.py": {
        "bijux_proteomics_lab.handoffs.ptm",
    },
    "workflow/demo/surprising_demo.py": {
        "bijux_proteomics_intelligence.belief_audit",
        "bijux_proteomics_intelligence.contradictions",
        "bijux_proteomics_intelligence.falsifiers",
        "bijux_proteomics_intelligence.refusal",
        "bijux_proteomics_intelligence.reviews",
        "bijux_proteomics_knowledge.memory.integrity.graph",
        "bijux_proteomics_knowledge.memory.models.claims",
    },
    "workflow/demo/surprising_demo_claims.py": {
        "bijux_proteomics_knowledge.memory.models.claims",
        "bijux_proteomics_knowledge.memory.models.evidence",
    },
    "workflow/pipelines/integrated_scientific_report.py": {
        "bijux_proteomics_intelligence.reviews",
        "bijux_proteomics_knowledge.memory.models.claims",
    },
    "workflow/reports/biological_report_assembly.py": {
        "bijux_proteomics_lab.handoffs.qc_feedback",
    },
    "workflow/reports/biological_result_graph.py": {
        "bijux_proteomics_lab.handoffs.qc_feedback",
    },
    "interpretation/pathway_activity/analysis.py": {
        "bijux_proteomics_knowledge.pathways.members",
    },
}
REMOVED_COMPATIBILITY_IMPORTS = {
    "bijux_proteomics.advanced_format_ingestion",
    "bijux_proteomics.execution_backend",
    "bijux_proteomics.execution_contracts",
    "bijux_proteomics.runner",
    "bijux_proteomics.runtime_adapter",
    "bijux_proteomics.schema",
    "bijux_proteomics.serialization",
    "bijux_proteomics.workflow_runtime",
}


def _imported_modules(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            modules.add(node.module)
    return modules


@pytest.mark.slow
def test_core_scientific_modules_do_not_import_runtime_intelligence_knowledge_or_lab() -> (
    None
):
    unexpected: dict[str, list[str]] = {}

    for path in CORE_SRC_ROOT.rglob("*.py"):
        module_path = path.relative_to(CORE_SRC_ROOT).as_posix()
        imported = _imported_modules(path)
        disallowed = sorted(
            module
            for module in imported
            if module.startswith(
                (
                    "bijux_proteomics_intelligence",
                    "bijux_proteomics_knowledge",
                    "bijux_proteomics_lab",
                )
            )
        )
        allowed_cross_package = ALLOWED_CROSS_PACKAGE_IMPORTS.get(module_path, set())
        if set(disallowed) != allowed_cross_package:
            unexpected[module_path] = disallowed

        runtime_imports = sorted(
            module
            for module in imported
            if module.startswith("bijux_proteomics_runtime")
        )
        if not runtime_imports:
            continue
        allowed = ALLOWED_RUNTIME_IMPORTS.get(module_path, set())
        if set(runtime_imports) != allowed:
            unexpected[module_path] = runtime_imports

    assert unexpected == {}


@pytest.mark.slow
def test_core_source_does_not_reintroduce_removed_wrapper_imports() -> None:
    stale_imports: dict[str, list[str]] = {}

    for path in CORE_SRC_ROOT.rglob("*.py"):
        module_path = path.relative_to(CORE_SRC_ROOT).as_posix()
        imported = _imported_modules(path)
        stale = sorted(imported & REMOVED_COMPATIBILITY_IMPORTS)
        if stale:
            stale_imports[module_path] = stale

    assert stale_imports == {}
