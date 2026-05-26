# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics_foundation.testing.source_tree_limits import (
    SourceFileLineCountException,
    build_source_tree_line_count_report,
)

CORE_SRC_ROOT = Path("packages/bijux-proteomics-core/src/bijux_proteomics")
LINE_COUNT_CEILING = 1000


def _temporary_reason(relative_path: str) -> str:
    if relative_path == "_scientific_tables.py":
        return "scientific table schema, projection, and rendering helpers still share one owner and need a narrower split."
    if relative_path.startswith("benchmarks/"):
        return "benchmark fixture catalogs, public package builders, and workflow corpora still need narrower owner families."
    if relative_path.startswith("chemistry/"):
        return "chemistry contract owners still combine too many formula, residue, and peptide family surfaces."
    if relative_path.startswith("dia/"):
        return "dia matrix assembly still combines ingestion, normalization, and report helpers in one owner."
    if relative_path.startswith("identification/"):
        return "identification owners still mix import, scoring, and benchmark surfaces that need narrower boundaries."
    if relative_path.startswith("interpretation/"):
        return "interpretation owners still combine multiple biological inference families that need narrower modules."
    if relative_path.startswith("io/"):
        return "io owners still combine multiple dialect, schema, and rendering responsibilities that need narrower modules."
    if relative_path.startswith("lab/"):
        return "lab support inside core still consolidates multiple QC families that should be separated further."
    if relative_path.startswith("ptm/"):
        return "ptm owners still combine card, contract, and quantification families that need narrower modules."
    if relative_path.startswith("quantification/"):
        return "quantification owners still combine matrix, provenance, rollup, and statistical families that need narrower modules."
    if relative_path.startswith("review/"):
        return "review owners still combine query and explanation families that need narrower modules."
    if relative_path.startswith("sequences/"):
        return "sequence owners still combine parsing, digestion, and protein context families that need narrower modules."
    if relative_path.startswith("targeted/"):
        return "targeted owners still combine interference, QC, and stability families that need narrower modules."
    if relative_path.startswith("workflow/"):
        return "workflow owners still combine comparison, export, and reporting families that need narrower modules."
    return "temporary large-file allowance for a core scientific owner that still needs narrower boundaries."


def _exception(relative_path: str, allowed_line_count: int) -> SourceFileLineCountException:
    return SourceFileLineCountException(
        relative_path=relative_path,
        allowed_line_count=allowed_line_count,
        temporary_reason=_temporary_reason(relative_path),
    )


CORE_LINE_COUNT_EXCEPTIONS = (
    _exception("_scientific_tables.py", 1028),
    _exception("benchmarks/flagship_acceptance.py", 1158),
    _exception("benchmarks/flagship_asset_roots.py", 1093),
    _exception("benchmarks/flagship_challenge_corpora.py", 1163),
    _exception("benchmarks/flagship_public_packages.py", 1542),
    _exception("benchmarks/workflow_generalization.py", 2183),
    _exception("chemistry/contracts.py", 2139),
    _exception("dia/protein_matrix.py", 1137),
    _exception("identification/adapters/fragpipe_import.py", 1037),
    _exception("identification/fdr/confidence.py", 1140),
    _exception("identification/protein/protein_inference_benchmarks.py", 1007),
    _exception("interpretation/complex_activity.py", 1020),
    _exception("interpretation/pathway_activity.py", 1016),
    _exception("interpretation/regulator_inference.py", 1409),
    _exception("io/formats/proteomics_formats.py", 1032),
    _exception("io/raw/raw_signal_evidence_cards.py", 1109),
    _exception("io/spectra/spectrum_contracts.py", 2092),
    _exception("lab/qc.py", 2174),
    _exception("ptm/cards/evidence_cards.py", 1398),
    _exception("ptm/contracts.py", 1046),
    _exception("ptm/quant/differential_analysis.py", 1070),
    _exception("quantification/matrix/peptide_intensity_matrix.py", 1026),
    _exception("quantification/missingness/missingness.py", 1113),
    _exception("quantification/provenance/review.py", 1361),
    _exception("quantification/provenance/sample_exploration.py", 1203),
    _exception("quantification/rollup/protein_lfq.py", 1113),
    _exception("quantification/statistics/differential_abundance.py", 1471),
    _exception("quantification/statistics/differential_result_robustness.py", 1092),
    _exception("review/claims/result_queries.py", 1067),
    _exception("review/explanations/result_explanations.py", 1329),
    _exception("sequences/core.py", 1321),
    _exception("sequences/digestion.py", 1184),
    _exception("sequences/protein_region_context.py", 1168),
    _exception("targeted/assay_interference.py", 1078),
    _exception("targeted/assay_qc.py", 1197),
    _exception("targeted/biomarker_stability.py", 1064),
    _exception("workflow/cards/protein_evidence_cards.py", 1412),
    _exception("workflow/cross_study_effect_comparison.py", 1135),
    _exception("workflow/cross_study_pathway_comparison.py", 1111),
    _exception("workflow/cross_study_protein_harmonization.py", 1091),
    _exception("workflow/demo/surprising_demo.py", 1104),
    _exception("workflow/exports/interactive_result_bundle.py", 1313),
    _exception("workflow/pipelines/dia_dda_comparison.py", 1211),
    _exception("workflow/pipelines/label_based_differential_analysis.py", 1275),
    _exception("workflow/pipelines/orchestrator.py", 1070),
    _exception("workflow/pipelines/public_benchmark_runner.py", 1118),
    _exception("workflow/study_result.py", 1098),
)


def test_core_source_tree_respects_line_count_ceiling() -> None:
    report = build_source_tree_line_count_report(
        CORE_SRC_ROOT,
        ceiling=LINE_COUNT_CEILING,
        exceptions=CORE_LINE_COUNT_EXCEPTIONS,
    )

    assert report.stale_exceptions == ()
    assert report.unexpected_over_ceiling == ()
    assert tuple(item.relative_path for item in report.approved_over_ceiling) == tuple(
        item.relative_path for item in CORE_LINE_COUNT_EXCEPTIONS
    )
