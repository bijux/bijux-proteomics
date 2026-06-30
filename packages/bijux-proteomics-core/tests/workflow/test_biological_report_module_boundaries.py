# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

import ast
from pathlib import Path

WORKFLOW_ROOT = (
    Path(__file__).resolve().parents[2] / "src" / "bijux_proteomics" / "workflow"
)
REPORTS_ROOT = WORKFLOW_ROOT / "reports"
BIOLOGICAL_REPORT_MODULES = tuple(sorted(REPORTS_ROOT.glob("biological_report*.py")))
BIOLOGICAL_REPORT_LINE_LIMIT = 1000
MODULE_SURFACES: dict[str, tuple[str, ...]] = {
    "biological_report_models.py": (
        "BiologicalReportSectionConfidenceEntry",
        "BiologicalReportSectionConfidenceLabel",
        "BiologicalReportSectionKey",
        "BiologicalResultReportBundle",
        "BiologicalResultReportExportManifest",
        "BiologicalResultReportSummary",
        "BiologicalResultSelectionPolicy",
    ),
    "biological_report_section_confidence.py": (
        "_build_biological_report_section_confidence_entries",
        "_count_section_confidence_labels",
    ),
    "biological_report_selection.py": (
        "_build_background_reference_entries",
        "_build_biological_foreground_filtering_policy",
        "_resolve_contrast",
        "_select_heatmap_entity_ids",
        "_select_significant_entity_ids",
    ),
    "biological_report_claims.py": (
        "_build_biological_claim_validation_report",
        "_build_biological_evidence_aware_ranking_report",
        "_build_biological_hypothesis_report",
    ),
    "biological_report_ranking.py": (
        "_build_biological_pathway_ranking_candidates",
        "_build_biological_protein_ranking_candidates",
    ),
    "biological_report_assembly.py": (
        "build_biological_result_report_bundle",
        "build_biological_result_report_bundle_from_quant_table",
    ),
    "biological_report_html_support.py": (
        "_format_optional_float",
        "_render_biological_report_section_confidence_table_html",
        "_render_section_heading_html",
    ),
    "biological_report_html.py": ("_render_biological_result_report_html",),
    "biological_report_rendering.py": (
        "export_biological_result_report_bundle",
        "render_biological_report_section_confidence_tsv",
        "render_biological_result_report_summary_tsv",
    ),
}


def test_biological_report_modules_stay_under_one_thousand_lines() -> None:
    violations: list[str] = []
    for path in BIOLOGICAL_REPORT_MODULES:
        line_count = sum(1 for _ in path.open(encoding="utf-8"))
        if line_count > BIOLOGICAL_REPORT_LINE_LIMIT:
            violations.append(
                f"{path.relative_to(WORKFLOW_ROOT)} has {line_count} lines"
            )
    assert not violations, "\n".join(violations)


def test_biological_report_submodules_expose_owned_surfaces() -> None:
    missing_symbols: list[str] = []
    for filename, symbols in MODULE_SURFACES.items():
        module = ast.parse((REPORTS_ROOT / filename).read_text(encoding="utf-8"))
        defined_symbols = {
            node.name
            for node in module.body
            if isinstance(node, (ast.FunctionDef, ast.ClassDef))
        }
        defined_symbols.update(
            target.id
            for node in module.body
            if isinstance(node, ast.Assign)
            for target in node.targets
            if isinstance(target, ast.Name)
        )
        for symbol in symbols:
            if symbol not in defined_symbols:
                missing_symbols.append(f"{filename} missing {symbol}")
    assert not missing_symbols, "\n".join(missing_symbols)


def test_biological_reporting_facade_delegates_to_split_owners() -> None:
    module = ast.parse(
        (REPORTS_ROOT / "biological_reporting.py").read_text(encoding="utf-8")
    )
    import_map = {
        node.module: {alias.name for alias in node.names}
        for node in module.body
        if isinstance(node, ast.ImportFrom) and node.module is not None
    }
    exported_names: set[str] = set()
    for node in module.body:
        if not isinstance(node, ast.Assign):
            continue
        if not any(
            isinstance(target, ast.Name) and target.id == "__all__"
            for target in node.targets
        ):
            continue
        if isinstance(node.value, ast.List | ast.Tuple):
            exported_names.update(
                element.value
                for element in node.value.elts
                if isinstance(element, ast.Constant) and isinstance(element.value, str)
            )

    assert import_map[
        "bijux_proteomics.workflow.reports.biological_report_assembly"
    ] >= {
        "build_biological_result_report_bundle",
        "build_biological_result_report_bundle_from_quant_table",
    }
    assert import_map["bijux_proteomics.workflow.reports.biological_report_models"] >= {
        "BiologicalReportSectionConfidenceEntry",
        "BiologicalReportSectionConfidenceLabel",
        "BiologicalReportSectionKey",
        "BiologicalResultReportArtifactPaths",
        "BiologicalResultReportBundle",
        "BiologicalResultReportExportManifest",
        "BiologicalResultReportSummary",
        "BiologicalResultSelectionPolicy",
    }
    assert import_map[
        "bijux_proteomics.workflow.reports.biological_report_rendering"
    ] >= {
        "export_biological_result_report_bundle",
        "render_biological_report_section_confidence_tsv",
        "render_biological_result_report_summary_tsv",
    }
    assert import_map[
        "bijux_proteomics.review.explanations.volcano_plots"
    ] >= {"VolcanoReviewPolicy"}
    assert exported_names >= {
        "BiologicalReportSectionConfidenceEntry",
        "BiologicalReportSectionConfidenceLabel",
        "BiologicalReportSectionKey",
        "BiologicalResultReportArtifactPaths",
        "BiologicalResultReportBundle",
        "BiologicalResultReportExportManifest",
        "BiologicalResultReportSummary",
        "BiologicalResultSelectionPolicy",
        "VolcanoReviewPolicy",
        "build_biological_result_report_bundle",
        "build_biological_result_report_bundle_from_quant_table",
        "export_biological_result_report_bundle",
        "render_biological_report_section_confidence_tsv",
        "render_biological_result_report_summary_tsv",
    }
