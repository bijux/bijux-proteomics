# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

import ast
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
SOURCE_ROOT = REPO_ROOT / "src" / "bijux_proteomics"
ARTIFACT_LAYOUT_OWNER = SOURCE_ROOT / "workflow" / "exports" / "artifact_layout.py"
MANAGED_WORKFLOW_EXPORT_OWNERS = (
    "ptm/cards/reporting.py",
    "workflow/pipelines/advanced_diann.py",
    "workflow/pipelines/advanced_fragpipe.py",
    "workflow/pipelines/advanced_maxquant.py",
    "workflow/pipelines/advanced_ptm.py",
    "workflow/pipelines/advanced_targeted.py",
    "workflow/pipelines/advanced_tmt.py",
    "workflow/pipelines/dda_biological_workflow.py",
    "workflow/pipelines/diann_biological_workflow.py",
    "workflow/pipelines/label_based_reporting.py",
    "workflow/pipelines/maxquant_biological_workflow.py",
    "workflow/pipelines/ptm_site_workflow.py",
    "workflow/pipelines/tmt_experiment_workflow.py",
    "workflow/reports/biological_report_rendering.py",
    "workflow/targeted_review_workflow.py",
)


def _calls_function(tree: ast.AST, function_name: str) -> bool:
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if isinstance(node.func, ast.Name) and node.func.id == function_name:
            return True
    return False


def test_artifact_layout_owner_self_validates_written_workflow_outputs() -> None:
    tree = ast.parse(ARTIFACT_LAYOUT_OWNER.read_text(encoding="utf-8"))

    assert _calls_function(
        tree, "validate_workflow_artifact_manifest"
    ), "workflow artifact layout owner must validate managed outputs after writing"


def test_managed_workflow_export_owners_use_validated_artifact_layout() -> None:
    offenders: list[str] = []

    for relative_path in MANAGED_WORKFLOW_EXPORT_OWNERS:
        tree = ast.parse((SOURCE_ROOT / relative_path).read_text(encoding="utf-8"))
        if not _calls_function(tree, "synchronize_workflow_artifact_layout"):
            offenders.append(relative_path)

    assert not offenders, (
        "workflow export owners must route directory outputs through "
        "synchronize_workflow_artifact_layout: " + ", ".join(offenders)
    )
