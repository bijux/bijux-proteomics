# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.review import (
    BiomarkerCandidateKind,
    BiomarkerCandidateRankingInput,
    BiomarkerCandidateRankReasonCode,
    build_biomarker_candidate_ranking_report,
    render_biomarker_candidate_ranking_tsv,
)


def test_biomarker_candidate_ranking_prioritizes_validation_ready_signal_over_famous_annotation() -> (
    None
):
    report = build_biomarker_candidate_ranking_report(
        (
            BiomarkerCandidateRankingInput(
                candidate_id="protein:P00001",
                candidate_kind=BiomarkerCandidateKind.PROTEIN,
                display_label="FAMOUS1",
                target_protein_ref="P00001",
                effect_size=0.25,
                adjusted_p_value=0.18,
                support_count=1,
                effect_score=0.10,
                robustness_score=0.18,
                detectability_score=0.22,
                specificity_score=0.30,
                annotation_score=1.0,
                assay_feasibility_score=0.20,
                sample_qc_score=0.92,
                annotation_labels=("hallmark_pathway", "drug_target", "disease_term"),
                source_ids=("card:protein_group_1",),
                note="widely annotated but weak and impractical discovery signal",
            ),
            BiomarkerCandidateRankingInput(
                candidate_id="protein:P00002",
                candidate_kind=BiomarkerCandidateKind.PROTEIN,
                display_label="ROBUST2",
                target_protein_ref="P00002",
                effect_size=1.45,
                adjusted_p_value=0.002,
                support_count=4,
                effect_score=0.85,
                robustness_score=0.88,
                detectability_score=0.81,
                specificity_score=0.84,
                annotation_score=0.40,
                assay_feasibility_score=0.83,
                sample_qc_score=0.92,
                annotation_labels=("context_term",),
                source_ids=("card:protein_group_2", "assay:P00002"),
                note="strong effect and clean validation surface",
            ),
        )
    )

    assert report.summary.candidate_count == 2
    assert report.entries[0].display_label == "ROBUST2"
    assert report.entries[0].priority_rank == 1
    assert report.entries[1].display_label == "FAMOUS1"
    assert (
        BiomarkerCandidateRankReasonCode.ANNOTATION_OUTPACES_EVIDENCE
        in report.entries[1].rank_reason_codes
    )
    assert (
        BiomarkerCandidateRankReasonCode.ASSAY_READY
        in report.entries[0].rank_reason_codes
    )


def test_biomarker_candidate_ranking_renderer_preserves_reason_codes_for_protein_and_site_candidates() -> (
    None
):
    report = build_biomarker_candidate_ranking_report(
        (
            BiomarkerCandidateRankingInput(
                candidate_id="protein:P00003",
                candidate_kind=BiomarkerCandidateKind.PROTEIN,
                display_label="KIN3",
                target_protein_ref="P00003",
                effect_size=1.2,
                adjusted_p_value=0.01,
                support_count=3,
                effect_score=0.72,
                robustness_score=0.77,
                detectability_score=0.70,
                specificity_score=0.80,
                annotation_score=0.55,
                assay_feasibility_score=0.76,
                sample_qc_score=0.83,
                annotation_labels=("pathway:MAPK",),
                source_ids=("card:protein_group_3",),
                note="protein candidate",
            ),
            BiomarkerCandidateRankingInput(
                candidate_id="site:P00003:S42:phospho",
                candidate_kind=BiomarkerCandidateKind.PTM_SITE,
                display_label="P00003 S42 phospho",
                target_protein_ref="P00003",
                site_key="P00003:S42:phospho",
                effect_size=0.95,
                adjusted_p_value=0.03,
                support_count=5,
                effect_score=0.62,
                robustness_score=0.54,
                detectability_score=0.68,
                specificity_score=0.82,
                annotation_score=0.72,
                assay_feasibility_score=0.58,
                sample_qc_score=0.83,
                annotation_labels=("regulator:MAPK1", "region:activation_loop"),
                source_ids=("site_card:P00003:S42:phospho",),
                note="site candidate",
            ),
        )
    )

    rendered = render_biomarker_candidate_ranking_tsv(report)

    assert report.summary.protein_candidate_count == 1
    assert report.summary.ptm_site_candidate_count == 1
    assert "rank_reason_codes" in rendered
    assert "candidate_kind" in rendered
    assert "assay_ready" in rendered
