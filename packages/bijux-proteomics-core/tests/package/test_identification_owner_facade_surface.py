# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.identification import fdr, peptide, protein, psm
from bijux_proteomics.identification.public_api import (
    FDR_FACADE_BUDGET,
    PEPTIDE_FACADE_BUDGET,
    PROTEIN_FACADE_BUDGET,
    PSM_FACADE_BUDGET,
    flatten_facade_exports,
    list_identification_fdr_api_modules,
    list_identification_peptide_api_modules,
    list_identification_protein_api_modules,
    list_identification_psm_api_modules,
)

REPO_ROOT = Path(__file__).resolve().parents[4]


def _non_empty_line_count(relative_path: str) -> int:
    content = (REPO_ROOT / relative_path).read_text(encoding="utf-8").splitlines()
    return sum(1 for line in content if line.strip())


def test_psm_facade_exports_match_governed_public_api() -> None:
    expected = flatten_facade_exports(list_identification_psm_api_modules())

    assert tuple(psm.__all__) == expected
    assert hasattr(psm, "extract_psm_features")
    assert hasattr(psm, "fit_target_decoy_logistic_model")
    assert _non_empty_line_count(
        "packages/bijux-proteomics-core/src/bijux_proteomics/identification/psm/__init__.py"
    ) <= PSM_FACADE_BUDGET.max_init_lines


def test_peptide_facade_exports_match_governed_public_api() -> None:
    expected = flatten_facade_exports(list_identification_peptide_api_modules())

    assert tuple(peptide.__all__) == expected
    assert hasattr(peptide, "build_peptide_evidence_report")
    assert hasattr(peptide, "build_peptide_cross_run_reproducibility_report")
    assert _non_empty_line_count(
        "packages/bijux-proteomics-core/src/bijux_proteomics/identification/peptide/__init__.py"
    ) <= PEPTIDE_FACADE_BUDGET.max_init_lines


def test_protein_facade_exports_match_governed_public_api() -> None:
    expected = flatten_facade_exports(list_identification_protein_api_modules())

    assert tuple(protein.__all__) == expected
    assert hasattr(protein, "ParsimonyReviewReport")
    assert hasattr(protein, "build_protein_grouping_report")
    assert hasattr(protein, "build_protein_parsimony_report")
    assert _non_empty_line_count(
        "packages/bijux-proteomics-core/src/bijux_proteomics/identification/protein/__init__.py"
    ) <= PROTEIN_FACADE_BUDGET.max_init_lines


def test_fdr_facade_exports_match_governed_public_api() -> None:
    expected = flatten_facade_exports(list_identification_fdr_api_modules())

    assert tuple(fdr.__all__) == expected
    assert hasattr(fdr, "build_psm_target_decoy_fdr_report")
    assert hasattr(fdr, "build_confidence_threshold_sensitivity_bundle")
    assert _non_empty_line_count(
        "packages/bijux-proteomics-core/src/bijux_proteomics/identification/fdr/__init__.py"
    ) <= FDR_FACADE_BUDGET.max_init_lines
