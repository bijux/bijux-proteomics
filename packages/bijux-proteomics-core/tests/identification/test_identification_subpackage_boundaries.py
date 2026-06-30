# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

import ast
from pathlib import Path

from bijux_proteomics.identification import (
    adapters,
    fdr,
    peptide,
    protein,
    psm,
    search_adapters,
)

_WRAPPER_MODULES = (
    "identification/calibration_benchmarks.py",
    "identification/calibration_drift.py",
    "identification/comet_import.py",
    "identification/confidence.py",
    "identification/contaminant_audit.py",
    "identification/contaminant_evidence.py",
    "identification/cross_run_reproducibility.py",
    "identification/diann_import.py",
    "identification/error_rate_annotation.py",
    "identification/evidence_level_fdr_review.py",
    "identification/fragpipe_benchmarks.py",
    "identification/fragpipe_import.py",
    "identification/generic_psm_mapper.py",
    "identification/maxquant_import.py",
    "identification/openms_import.py",
    "identification/parsimony_review.py",
    "identification/peptide_evidence.py",
    "identification/peptide_evidence_review.py",
    "identification/peptide_target_decoy_fdr.py",
    "identification/picked_protein_fdr.py",
    "identification/picked_protein_fdr_review.py",
    "identification/protein_ambiguity_review.py",
    "identification/protein_coverage.py",
    "identification/protein_coverage_review.py",
    "identification/protein_coverage_visualization.py",
    "identification/protein_evidence.py",
    "identification/protein_evidence_review.py",
    "identification/protein_grouping.py",
    "identification/protein_grouping_review.py",
    "identification/protein_inference_benchmarks.py",
    "identification/protein_parsimony.py",
    "identification/protein_target_decoy_fdr.py",
    "identification/psm_features.py",
    "identification/psm_inspection.py",
    "identification/psm_rescoring.py",
    "identification/psm_target_decoy_fdr.py",
    "identification/rejected_evidence_table.py",
    "identification/sage_import.py",
    "identification/score_separation_diagnostic.py",
    "identification/search_adapter_loss.py",
    "identification/spectronaut_import.py",
    "identification/target_decoy_benchmarks.py",
    "identification/target_decoy_reference_validation.py",
)


def _core_src_root() -> Path:
    return Path(__file__).resolve().parents[2] / "src" / "bijux_proteomics"


def test_identification_subpackages_export_representative_owner_surfaces() -> None:
    assert hasattr(psm, "extract_psm_features")
    assert hasattr(psm, "render_psm_rescoring_tsv")
    assert hasattr(peptide, "build_peptide_evidence_report")
    assert hasattr(peptide, "build_peptide_cross_run_reproducibility_report")
    assert hasattr(protein, "build_protein_grouping_report")
    assert hasattr(protein, "build_protein_parsimony_report")
    assert hasattr(fdr, "build_psm_target_decoy_fdr_report")
    assert hasattr(fdr, "build_empirical_score_calibration_report")
    assert hasattr(adapters, "build_diann_import_report")
    assert hasattr(adapters, "build_search_adapter_information_loss_report")
    assert hasattr(search_adapters, "build_search_adapter_corpus_conformance_matrix")
    assert hasattr(search_adapters, "search_adapter_registry")


def test_identification_root_wrappers_stay_compatibility_only() -> None:
    root = _core_src_root()
    for relative_path in _WRAPPER_MODULES:
        path = root / relative_path
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        body = tree.body
        assert body, f"{relative_path} should not be empty"
        assert isinstance(body[0], ast.Expr)
        for node in body[1:]:
            assert isinstance(
                node,
                ast.ImportFrom,
            ), f"{relative_path} should stay a thin compatibility facade"


def test_identification_root_and_subpackage_surfaces_share_owner_functions() -> None:
    from bijux_proteomics import identification

    assert identification.extract_psm_features is psm.extract_psm_features
    assert (
        identification.build_peptide_evidence_report
        is peptide.build_peptide_evidence_report
    )
    assert (
        identification.build_protein_grouping_report
        is protein.build_protein_grouping_report
    )
    assert (
        identification.build_psm_target_decoy_fdr_report
        is fdr.build_psm_target_decoy_fdr_report
    )
    assert (
        identification.build_diann_import_report is adapters.build_diann_import_report
    )
