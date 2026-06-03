# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.review import (
    EvidenceAwareRankingCandidate,
    EvidenceAwareRankingEntityKind,
    build_evidence_aware_ranking_report,
    render_evidence_aware_ranking_tsv,
)


def test_evidence_aware_ranking_prioritizes_supported_result_over_low_support_artifact() -> (
    None
):
    report = build_evidence_aware_ranking_report(
        (
            EvidenceAwareRankingCandidate(
                candidate_id="protein:P11111",
                entity_kind=EvidenceAwareRankingEntityKind.PROTEIN,
                display_label="P11111",
                effect_size=1.4,
                adjusted_p_value=0.004,
                abundance_value=12.0,
                support_count=4,
                annotation_label="kinase",
                effect_score=0.7,
                significance_score=0.4,
                abundance_score=0.9,
                support_score=1.0,
                qc_score=0.85,
                annotation_score=0.8,
                reproducibility_score=0.9,
                confidence_score=0.9,
                note="robust multi-peptide protein result",
            ),
            EvidenceAwareRankingCandidate(
                candidate_id="protein:P99999",
                entity_kind=EvidenceAwareRankingEntityKind.PROTEIN,
                display_label="P99999",
                effect_size=1.8,
                adjusted_p_value=0.0002,
                abundance_value=4.0,
                support_count=1,
                effect_score=0.9,
                significance_score=0.62,
                abundance_score=0.1,
                support_score=0.25,
                qc_score=0.35,
                annotation_score=0.0,
                reproducibility_score=0.3,
                confidence_score=0.2,
                penalties={
                    "single_peptide_artifact": 0.18,
                    "low_abundance_signal": 0.12,
                },
                uncertainty=0.1,
                note="apparently significant but weak single-peptide result",
            ),
        )
    )

    assert report.summary.entry_count == 2
    assert report.entries[0].candidate_id == "protein:P11111"
    assert report.entries[0].priority_rank == 1
    assert (
        report.entries[0].decomposition.final_score
        > report.entries[1].decomposition.final_score
    )
    assert report.entries[1].penalty_codes == (
        "low_abundance_signal",
        "single_peptide_artifact",
    )


def test_evidence_aware_ranking_renderer_preserves_priority_and_component_columns() -> (
    None
):
    report = build_evidence_aware_ranking_report(
        (
            EvidenceAwareRankingCandidate(
                candidate_id="pathway:R-HSA-123",
                entity_kind=EvidenceAwareRankingEntityKind.PATHWAY,
                display_label="Signal relay",
                effect_size=1.1,
                adjusted_p_value=0.02,
                abundance_value=10.0,
                support_count=3,
                annotation_label="Reactome",
                effect_score=0.55,
                significance_score=0.28,
                abundance_score=0.7,
                support_score=0.75,
                qc_score=0.8,
                annotation_score=1.0,
                reproducibility_score=0.7,
                confidence_score=0.6,
                note="pathway-level support from multiple proteins",
            ),
        )
    )

    rendered = render_evidence_aware_ranking_tsv(report)

    assert rendered.splitlines()[0].startswith(
        "candidate_id\tentity_kind\tdisplay_label\tpriority_rank\tfinal_score"
    )
    assert "support_score" in rendered
    assert "Signal relay" in rendered
