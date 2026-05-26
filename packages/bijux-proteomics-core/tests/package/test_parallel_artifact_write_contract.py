# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

import ast
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
SOURCE_ROOT = REPO_ROOT / "src" / "bijux_proteomics"
ATOMIC_FILE_OWNER = SOURCE_ROOT / "_atomic_files.py"
OUTPUT_TABLE_OWNER = SOURCE_ROOT / "_output_tables.py"
OUTPUT_PROTOCOL_OWNER = SOURCE_ROOT / "interfaces" / "support" / "output_protocol.py"
ARTIFACT_LAYOUT_OWNER = SOURCE_ROOT / "workflow" / "exports" / "artifact_layout.py"
MANAGED_WORKFLOW_WRITE_OWNERS = (
    "workflow/demo/scale_demo.py",
    "workflow/demo/surprising_demo.py",
    "workflow/pipelines/advanced_diann.py",
    "workflow/pipelines/advanced_fragpipe.py",
    "workflow/pipelines/advanced_maxquant.py",
    "workflow/pipelines/advanced_ptm.py",
    "workflow/pipelines/advanced_targeted.py",
    "workflow/pipelines/advanced_tmt.py",
    "workflow/pipelines/dda_biological_workflow.py",
    "workflow/pipelines/diann_biological_workflow.py",
    "workflow/pipelines/flagship_run.py",
    "workflow/pipelines/integrated_scientific_report.py",
    "workflow/pipelines/maxquant_biological_workflow.py",
    "workflow/pipelines/orchestrator.py",
    "workflow/pipelines/ptm_site_workflow.py",
    "workflow/pipelines/tmt_experiment_workflow.py",
    "workflow/pipelines/trust_bundle.py",
    "workflow/reports/biological_report_rendering.py",
)


def _calls_name(tree: ast.AST, function_name: str) -> bool:
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if isinstance(node.func, ast.Name) and node.func.id == function_name:
            return True
    return False


def _calls_attribute(tree: ast.AST, attribute_name: str) -> bool:
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if isinstance(node.func, ast.Attribute) and node.func.attr == attribute_name:
            return True
    return False


def test_atomic_file_owner_uses_hidden_temporary_paths_and_atomic_replace() -> None:
    source_text = ATOMIC_FILE_OWNER.read_text(encoding="utf-8")

    assert ".bijux-write-" in source_text
    assert "os.replace" in source_text
    assert "unlink(missing_ok=True)" in source_text


def test_shared_artifact_write_owners_route_through_atomic_helpers() -> None:
    output_table_tree = ast.parse(OUTPUT_TABLE_OWNER.read_text(encoding="utf-8"))
    output_protocol_tree = ast.parse(OUTPUT_PROTOCOL_OWNER.read_text(encoding="utf-8"))
    artifact_layout_tree = ast.parse(ARTIFACT_LAYOUT_OWNER.read_text(encoding="utf-8"))

    assert _calls_name(output_table_tree, "atomic_write_text")
    assert _calls_name(output_protocol_tree, "atomic_write_text")
    assert _calls_name(artifact_layout_tree, "atomic_write_text")
    assert _calls_name(artifact_layout_tree, "atomic_copy_file")


def test_managed_workflow_write_owners_avoid_direct_write_text_and_copyfile_calls() -> None:
    offenders: list[str] = []

    for relative_path in MANAGED_WORKFLOW_WRITE_OWNERS:
        tree = ast.parse((SOURCE_ROOT / relative_path).read_text(encoding="utf-8"))
        if _calls_attribute(tree, "write_text") or _calls_attribute(tree, "copyfile"):
            offenders.append(relative_path)

    assert not offenders, (
        "managed workflow write owners must avoid direct write_text/copyfile calls: "
        + ", ".join(offenders)
    )
