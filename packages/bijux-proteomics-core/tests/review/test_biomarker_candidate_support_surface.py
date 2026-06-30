# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

import bijux_proteomics.interfaces.support.biomarker_candidate_support as biomarker_candidate_support
from bijux_proteomics.interfaces.support.biomarker_candidate_support.biological_candidates import (
    _build_biomarker_candidates_from_biological_report_dir,
)
from bijux_proteomics.interfaces.support.biomarker_candidate_support.ptm_candidates import (
    _build_biomarker_candidates_from_ptm_report_dir,
)
from bijux_proteomics.review import BiomarkerCandidateKind


def test_biomarker_candidate_support_facade_exports_primary_loaders() -> None:
    assert biomarker_candidate_support.__all__ == (
        "_build_biomarker_candidates_from_biological_report_dir",
        "_build_biomarker_candidates_from_ptm_report_dir",
        "_load_biomarker_candidate_inputs",
    )


def test_biological_report_candidate_loader_matches_out_of_order_differential_rows(
    tmp_path: Path,
) -> None:
    report_dir = tmp_path / "biological_report"
    report_dir.mkdir()
    (report_dir / "biological_report_summary.tsv").write_text(
        "\n".join(
            (
                "field\tvalue",
                "experiment_confidence_score\t0.85",
            )
        )
        + "\n",
        encoding="utf-8",
    )
    (report_dir / "biological_protein_cards.tsv").write_text(
        "\n".join(
            (
                "card_id\tprotein_group_id\trepresentative_protein_ref\tgene_symbol\tidentity_level\tunique_peptide_count\tshared_peptide_count\tevidence_tier\tpathway_ids\tcontext_ids\tfunctional_regions\tproteogenomic_support_class\tptm_sites\twarning_codes",
                "card-1\tpg-1\tP11111\tKIN1\tprotein_group\t2\t1\thigh\tpathway:kinase\tcontext:nucleus\tregion:loop\tobserved\tP11111:S5:Phospho\t",
                "card-2\tpg-2\tP22222\tKIN2\tprotein_group\t1\t0\tmoderate\tpathway:repair\t\t\t\t\twarning:shared",
            )
        )
        + "\n",
        encoding="utf-8",
    )
    (report_dir / "biological_differential.tsv").write_text(
        "\n".join(
            (
                "entity_id\tlog2_fold_change\tadjusted_p_value\trobustness_score",
                "pg-2\t0.7\t0.04\t0.5",
                "pg-1\t1.8\t0.002\t0.9",
            )
        )
        + "\n",
        encoding="utf-8",
    )

    candidates, sample_qc_score = (
        _build_biomarker_candidates_from_biological_report_dir(
            report_dir,
            selected_peptide_support={
                "P11111": {
                    "detectability_score": 0.9,
                    "uniqueness_score": 0.8,
                    "suitability_score": 0.7,
                },
                "P22222": {
                    "detectability_score": 0.4,
                    "uniqueness_score": 0.5,
                    "suitability_score": 0.3,
                },
            },
            assay_interference_support={
                "P11111": {"assay_score": 0.8},
                "P22222": {"assay_score": 0.2},
            },
        )
    )

    assert sample_qc_score == 0.85
    assert tuple(candidate.candidate_id for candidate in candidates) == (
        "protein:pg-1",
        "protein:pg-2",
    )
    assert all(
        candidate.candidate_kind is BiomarkerCandidateKind.PROTEIN
        for candidate in candidates
    )
    assert candidates[0].effect_size == 1.8
    assert candidates[0].annotation_labels == (
        "pathway:kinase",
        "context:nucleus",
        "region:loop",
        "P11111:S5:Phospho",
        "proteogenomic:observed",
    )


def test_ptm_report_candidate_loader_matches_out_of_order_differential_rows(
    tmp_path: Path,
) -> None:
    report_dir = tmp_path / "ptm_report"
    report_dir.mkdir()
    (report_dir / "ptm_evidence_cards.tsv").write_text(
        "\n".join(
            (
                "card_id\tsite_key\tprotein_ref\tresidue\tposition\tmodification_name\tidentity_level\tlocalization_tier\tmechanism_class\tpeptide_spectrum_count\tobserved_sample_count\tcentered_windows\tortholog_conservation_status\tfunctional_regions\tregulators\twarning_codes",
                "ptm-card-1\tP11111:S5:Phospho\tP11111\tS\t5\tPhospho\tsite\tclass_i\tactivation\t4\t3\twindow:RRXS\tconserved\tregion:loop\tregulator:MAPK1\t",
                "ptm-card-2\tP22222:T9:Phospho\tP22222\tT\t9\tPhospho\tsite\tclass_ii\tinhibitory\t2\t2\twindow:TP\tvariable\t\t\twarning:shared",
            )
        )
        + "\n",
        encoding="utf-8",
    )
    (report_dir / "ptm_differential.tsv").write_text(
        "\n".join(
            (
                "site_key\tlow_localization\tambiguous\tshared_peptide\tlog2_fold_change\tadjusted_p_value\timputation_dependent_hit\tprotein_correction_status",
                "P22222:T9:Phospho\ttrue\tfalse\ttrue\t0.6\t0.03\ttrue\tnot_requested",
                "P11111:S5:Phospho\tfalse\tfalse\tfalse\t1.2\t0.002\tfalse\tsubtracted_unmodified_protein",
            )
        )
        + "\n",
        encoding="utf-8",
    )

    candidates = _build_biomarker_candidates_from_ptm_report_dir(
        report_dir,
        sample_qc_score=0.9,
    )

    assert tuple(candidate.site_key for candidate in candidates) == (
        "P11111:S5:Phospho",
        "P22222:T9:Phospho",
    )
    assert all(
        candidate.candidate_kind is BiomarkerCandidateKind.PTM_SITE
        for candidate in candidates
    )
    assert candidates[0].effect_size == 1.2
    assert "ortholog:conserved" in candidates[0].annotation_labels
    assert "mechanism:activation" in candidates[0].annotation_labels
