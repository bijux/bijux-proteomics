# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

import pytest

from bijux_proteomics_foundation.testing.source_tree_limits import (
    SourceFileLineCountException,
    build_source_tree_line_count_report,
)

pytestmark = pytest.mark.governance

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
    if relative_path.startswith("interfaces/support/"):
        return "interface support owners still combine output, biomarker, sequence, and targeted helper families that need narrower modules."
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


def _exception(
    relative_path: str, allowed_line_count: int
) -> SourceFileLineCountException:
    return SourceFileLineCountException(
        relative_path=relative_path,
        allowed_line_count=allowed_line_count,
        temporary_reason=_temporary_reason(relative_path),
    )


CORE_LINE_COUNT_EXCEPTIONS = (
    _exception("_scientific_tables.py", 1110),
    _exception("benchmarks/flagship_acceptance.py", 1158),
    _exception("benchmarks/flagship_asset_roots.py", 1093),
    _exception("benchmarks/flagship_challenge_corpora.py", 1167),
    _exception("benchmarks/flagship_public_packages.py", 1542),
    _exception("benchmarks/workflow_generalization.py", 2183),
    _exception("chemistry/contracts/modified_peptides.py", 1065),
    _exception("dia/protein_matrix.py", 1138),
    _exception("identification/adapters/fragpipe_import.py", 1037),
    _exception("identification/fdr/confidence.py", 1140),
    _exception("identification/protein/protein_inference_benchmarks.py", 1007),
    _exception("interfaces/support/biomarker_candidate_support.py", 1612),
    _exception("interfaces/support/output_protocol.py", 1247),
    _exception("interfaces/support/sequence_support.py", 1456),
    _exception("interfaces/support/targeted_panel_support.py", 1706),
    _exception("interfaces/support/targeted_selection_io.py", 1619),
    _exception("interfaces/support/validation_evidence_support.py", 1542),
    _exception("io/formats/proteomics_formats.py", 1105),
    _exception("io/raw/raw_signal_evidence_cards.py", 1128),
    _exception("io/spectra/spectrum_contracts.py", 2095),
    _exception("ptm/cards/evidence_cards.py", 1403),
    _exception("ptm/contracts.py", 1061),
    _exception("ptm/quant/differential_analysis.py", 1090),
    _exception("quantification/matrix/peptide_intensity_matrix.py", 1044),
    _exception("quantification/provenance/review.py", 1288),
    _exception("review/belief/belief_audit.py", 1007),
    _exception("review/claims/result_queries.py", 1075),
    _exception("review/explanations/result_explanations.py", 1341),
    _exception("sequences/core.py", 1340),
    _exception("sequences/digestion.py", 1198),
    _exception("targeted/assay_interference.py", 1090),
    _exception("targeted/assay_qc.py", 1297),
    _exception("targeted/biomarker_stability.py", 1111),
    _exception("targeted/validation_planning.py", 1006),
    _exception("workflow/cards/protein_evidence_cards.py", 1454),
    _exception("workflow/cross_study_effect_comparison.py", 1187),
    _exception("workflow/cross_study_meta_analysis.py", 1013),
    _exception("workflow/cross_study_pathway_comparison.py", 1173),
    _exception("workflow/cross_study_protein_harmonization.py", 1145),
    _exception("workflow/demo/surprising_demo.py", 1013),
    _exception("workflow/exports/interactive_result_bundle.py", 1396),
    _exception("workflow/exports/interactive_result_comparison.py", 1002),
    _exception("workflow/pipelines/advanced_tmt.py", 1035),
    _exception("workflow/pipelines/dia_dda_comparison.py", 1245),
    _exception("workflow/pipelines/orchestrator.py", 1089),
    _exception("workflow/pipelines/public_benchmark_runner.py", 1151),
    _exception("workflow/study_result.py", 1451),
)


def test_core_source_tree_respects_line_count_ceiling() -> None:
    report = build_source_tree_line_count_report(
        CORE_SRC_ROOT,
        ceiling=LINE_COUNT_CEILING,
        exceptions=CORE_LINE_COUNT_EXCEPTIONS,
        exclude_marked_generated=True,
    )

    assert report.stale_exceptions == ()
    assert report.unexpected_over_ceiling == ()
    assert tuple(item.relative_path for item in report.approved_over_ceiling) == tuple(
        item.relative_path for item in CORE_LINE_COUNT_EXCEPTIONS
    )
