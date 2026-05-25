# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

import ast
from pathlib import Path

from bijux_proteomics.ptm import cards, localization, parsing, quant, regulation, sites


_WRAPPER_MODULES = (
    "ptm/abundance_correction.py",
    "ptm/acetylation.py",
    "ptm/ambiguity_handling.py",
    "ptm/benchmarks.py",
    "ptm/context_annotation.py",
    "ptm/crosstalk.py",
    "ptm/differential_analysis.py",
    "ptm/evidence_cards.py",
    "ptm/fragment_scoring.py",
    "ptm/hotspots.py",
    "ptm/kinase_inference.py",
    "ptm/localization_risk.py",
    "ptm/localization_scoring.py",
    "ptm/mechanism_classification.py",
    "ptm/motif_analysis.py",
    "ptm/occupancy_estimation.py",
    "ptm/ortholog_site_conservation.py",
    "ptm/oxidation.py",
    "ptm/peptide_parser.py",
    "ptm/phosphatase_inference.py",
    "ptm/protein_site_mapping.py",
    "ptm/proteoforms.py",
    "ptm/regulator_enrichment.py",
    "ptm/reporting.py",
    "ptm/review.py",
    "ptm/site_annotation_import.py",
    "ptm/site_groups.py",
    "ptm/site_quantification.py",
)


def _core_src_root() -> Path:
    return Path(__file__).resolve().parents[2] / "src" / "bijux_proteomics"


def test_ptm_subpackages_export_representative_owner_surfaces() -> None:
    assert hasattr(parsing, "parse_ptm_peptide")
    assert hasattr(parsing, "parse_ptm_site_annotation_tsv")
    assert hasattr(localization, "score_ptm_fragments")
    assert hasattr(localization, "detect_false_localization")
    assert hasattr(sites, "build_ptm_ambiguity_review_report")
    assert hasattr(sites, "map_ptm_evidence_to_protein_sites")
    assert hasattr(quant, "build_ptm_site_quantification_report")
    assert hasattr(quant, "build_ptm_differential_analysis_report")
    assert hasattr(regulation, "build_ptm_crosstalk_report")
    assert hasattr(regulation, "build_ptm_regulator_enrichment_report")
    assert hasattr(cards, "build_ptm_evidence_card_report")
    assert hasattr(cards, "build_ptm_report_bundle")


def test_ptm_root_wrappers_stay_compatibility_only() -> None:
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


def test_ptm_root_and_subpackage_surfaces_share_owner_functions() -> None:
    from bijux_proteomics import ptm

    assert ptm.parse_ptm_peptide is parsing.parse_ptm_peptide
    assert ptm.score_ptm_fragments is localization.score_ptm_fragments
    assert ptm.build_ptm_ambiguity_review_report is sites.build_ptm_ambiguity_review_report
    assert ptm.build_ptm_site_quantification_report is quant.build_ptm_site_quantification_report
    assert ptm.build_ptm_crosstalk_report is regulation.build_ptm_crosstalk_report
    assert ptm.build_ptm_evidence_card_report is cards.build_ptm_evidence_card_report
