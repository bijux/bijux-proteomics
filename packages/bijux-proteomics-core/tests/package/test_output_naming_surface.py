# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

import ast
from pathlib import Path

import pytest

from bijux_proteomics import benchmarks, sequences, workflow
from bijux_proteomics.identification import confidence as identification_confidence
from bijux_proteomics.identification import contracts as identification_contracts
from bijux_proteomics.quantification import contracts as quantification_contracts

SOURCE_ROOT = Path(__file__).resolve().parents[2] / "src" / "bijux_proteomics"

ALLOWED_RENDER_SUFFIXES = (
    "_tsv",
    "_json",
    "_html",
    "_svg",
    "_mgf",
    "_markdown",
    "_fasta",
)

LEGACY_RENDER_WRAPPERS = {
    "_tabular.py": {"render_tsv_rows": "render_rows_tsv"},
    "domain/card_schema.py": {
        "render_standard_card_row": "build_standard_card_row",
    },
    "lab/planning.py": {
        "render_lab_review_packet": "build_lab_review_packet_rendering",
    },
    "sequences/core.py": {"render_fasta_records": "render_records_fasta"},
}

LEGACY_BUNDLE_WRAPPERS = {
    "sequences/theoretical_digest.py": {
        "export_theoretical_digest_bundle": "write_theoretical_digest_bundle",
    },
    "workflow/reports/biological_report_rendering.py": {
        "export_biological_result_report_bundle": "write_biological_result_report_bundle",
    },
    "workflow/pipelines/dda_biological_workflow.py": {
        "export_dda_biological_workflow_bundle": "write_dda_biological_workflow_bundle",
    },
    "workflow/pipelines/diann_biological_workflow.py": {
        "export_diann_biological_workflow_bundle": "write_diann_biological_workflow_bundle",
    },
    "workflow/pipelines/maxquant_biological_workflow.py": {
        "export_maxquant_biological_workflow_bundle": "write_maxquant_biological_workflow_bundle",
    },
    "workflow/pipelines/label_based_reporting.py": {
        "export_label_based_report_bundle": "write_label_based_report_bundle",
    },
    "workflow/pipelines/ptm_site_workflow.py": {
        "export_ptm_site_workflow_bundle": "write_ptm_site_workflow_bundle",
    },
    "workflow/pipelines/tmt_experiment_workflow.py": {
        "export_tmt_experiment_workflow_bundle": "write_tmt_experiment_workflow_bundle",
    },
    "workflow/pipelines/flagship_run.py": {
        "export_proteomics_run_bundle": "write_proteomics_run_bundle",
    },
    "ptm/cards/reporting.py": {"export_ptm_report_bundle": "write_ptm_report_bundle"},
    "quantification/contracts/protein_rollup.py": {
        "export_label_free_provenance_bundle": "write_label_free_provenance_bundle",
    },
    "quantification/contracts/artifact_bundle.py": {
        "export_quant_artifact_bundle": "write_quant_artifact_bundle",
    },
    "identification/contracts/review.py": {
        "export_review_ready_evidence_bundle": "write_review_ready_evidence_bundle",
    },
    "identification/fdr/confidence.py": {
        "export_psm_peptide_protein_trace_bundle": (
            "write_psm_peptide_protein_trace_bundle"
        ),
    },
    "io/spectra/spectrum_contracts.py": {
        "export_annotated_spectrum_bundle": "write_annotated_spectrum_bundle",
    },
    "benchmarks/public_case_studies.py": {
        "export_public_biological_case_study_report": (
            "write_public_biological_case_study_bundle"
        ),
    },
}


def _parse_module(relative_path: str) -> ast.Module:
    return ast.parse((SOURCE_ROOT / relative_path).read_text(encoding="utf-8"))


def _function_node(module: ast.Module, name: str) -> ast.FunctionDef:
    for node in module.body:
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return node
    raise AssertionError(f"missing function {name!r}")


def _call_target_name(node: ast.AST) -> str | None:
    if isinstance(node, ast.Call):
        if isinstance(node.func, ast.Name):
            return node.func.id
        if isinstance(node.func, ast.Attribute):
            return node.func.attr
    return None


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


def _assert_wrapper(module_path: str, legacy_name: str, canonical_name: str) -> None:
    node = _function_node(_parse_module(module_path), legacy_name)
    payload = _function_payload(node)
    assert len(payload) == 1, f"{legacy_name} should stay a one-statement wrapper"
    statement = payload[0]
    call = None
    if isinstance(statement, (ast.Return, ast.Expr)):
        call = statement.value
    assert _call_target_name(call) == canonical_name


@pytest.mark.slow
def test_renderer_names_use_explicit_format_suffixes_or_wrappers() -> None:
    legacy_wrapper_names = {
        name for wrappers in LEGACY_RENDER_WRAPPERS.values() for name in wrappers
    }
    unexpected: list[str] = []
    for path in SOURCE_ROOT.rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if not isinstance(node, ast.FunctionDef):
                continue
            if not node.name.startswith("render_"):
                continue
            if node.name in legacy_wrapper_names:
                continue
            if node.name.endswith(ALLOWED_RENDER_SUFFIXES):
                continue
            unexpected.append(
                f"{path.relative_to(SOURCE_ROOT)}:{node.lineno}:{node.name}"
            )
    assert unexpected == []


def test_legacy_render_wrappers_delegate_to_canonical_names() -> None:
    for module_path, wrappers in LEGACY_RENDER_WRAPPERS.items():
        for legacy_name, canonical_name in wrappers.items():
            _assert_wrapper(module_path, legacy_name, canonical_name)


@pytest.mark.slow
def test_render_functions_do_not_write_files() -> None:
    offenders: list[str] = []
    for path in SOURCE_ROOT.rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if not isinstance(node, ast.FunctionDef) or not node.name.startswith(
                "render_"
            ):
                continue
            for child in ast.walk(node):
                if not isinstance(child, ast.Call):
                    continue
                if isinstance(child.func, ast.Attribute) and child.func.attr in {
                    "write_text",
                    "write_bytes",
                    "mkdir",
                }:
                    offenders.append(
                        f"{path.relative_to(SOURCE_ROOT)}:{node.lineno}:{node.name}"
                    )
    assert offenders == []


@pytest.mark.slow
def test_bundle_writer_names_use_write_prefix_with_legacy_wrappers() -> None:
    expected_write_names = {
        "write_annotated_spectrum_bundle",
        "write_biological_result_report_bundle",
        "write_dda_biological_workflow_bundle",
        "write_diann_biological_workflow_bundle",
        "write_label_based_report_bundle",
        "write_label_free_provenance_bundle",
        "write_maxquant_biological_workflow_bundle",
        "write_proteomics_run_bundle",
        "write_psm_peptide_protein_trace_bundle",
        "write_ptm_report_bundle",
        "write_ptm_site_workflow_bundle",
        "write_public_biological_case_study_bundle",
        "write_quant_artifact_bundle",
        "write_review_ready_evidence_bundle",
        "write_theoretical_digest_bundle",
        "write_tmt_experiment_workflow_bundle",
    }
    found_write_names: set[str] = set()
    for path in SOURCE_ROOT.rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if (
                isinstance(node, ast.FunctionDef)
                and node.name.startswith("write_")
                and node.name.endswith("_bundle")
            ):
                found_write_names.add(node.name)
    assert found_write_names == expected_write_names

    for module_path, wrappers in LEGACY_BUNDLE_WRAPPERS.items():
        for legacy_name, canonical_name in wrappers.items():
            _assert_wrapper(module_path, legacy_name, canonical_name)


def test_package_surfaces_expose_canonical_bundle_writers() -> None:
    assert hasattr(sequences, "write_theoretical_digest_bundle")
    assert hasattr(workflow, "write_biological_result_report_bundle")
    assert hasattr(workflow, "write_proteomics_run_bundle")
    assert hasattr(workflow, "write_ptm_site_workflow_bundle")
    assert hasattr(workflow, "write_tmt_experiment_workflow_bundle")
    assert hasattr(benchmarks, "write_public_biological_case_study_bundle")
    assert hasattr(identification_contracts, "write_review_ready_evidence_bundle")
    assert hasattr(identification_confidence, "write_psm_peptide_protein_trace_bundle")
    assert hasattr(quantification_contracts, "write_label_free_provenance_bundle")
    assert hasattr(quantification_contracts, "write_quant_artifact_bundle")
