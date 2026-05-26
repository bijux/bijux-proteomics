# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.review import (
    AnalysisRecommendationKind,
    build_analysis_recommendation_report_from_artifacts,
    render_analysis_recommendation_tsv,
)


def test_analysis_recommendation_engine_ties_each_action_to_detected_condition(
    tmp_path: Path,
) -> None:
    biological_dir = tmp_path / "biological_report"
    biological_dir.mkdir()
    (biological_dir / "biological_protein_cards.tsv").write_text(
        "\n".join(
            (
                "card_id\tgraph_claim_node_id\tgraph_subject_node_id\tgraph_support_node_ids\tgraph_source_row_refs\tprotein_group_id\trepresentative_protein_ref\tprotein_refs\tgene_symbol\tpeptides\tpeptide_count\tunique_peptide_count\tshared_peptide_count\tobserved_sample_count\tmissing_sample_count\tcondition_a\tcondition_b\tlog2_fold_change\tadjusted_p_value\tsignificant\tevidence_tier\twarning_codes",
                "protein-card-p11111\tclaim:P11111\tprotein:P11111\tpeptide:PEPA\tdifferential:P11111\tpg-P11111\tP11111\tP11111\tAKT1\tPEPA\t1\t1\t0\t4\t0\tcontrol\ttreated\t1.4\t0.02\ttrue\thigh_support\t",
            )
        )
        + "\n",
        encoding="utf-8",
    )
    (biological_dir / "biological_evidence_graph_nodes.tsv").write_text(
        "\n".join(
            (
                "node_id\tentity_type\tentity_ref\tcontext_refs",
                "protein:P11111\tprotein\tP11111\t",
                "sample:T2\tsample\tT2\trun:t2.mzml",
                "run:t2.mzml\trun\tt2.mzml\tsample:T2",
            )
        )
        + "\n",
        encoding="utf-8",
    )

    ptm_dir = tmp_path / "ptm_report"
    ptm_dir.mkdir()
    (ptm_dir / "ptm_evidence_cards.tsv").write_text(
        "\n".join(
            (
                "card_id\tsite_key\tprotein_ref\tcondition_a\tcondition_b\tadjusted_p_value\tlog2_fold_change\tcorrected_log2_fold_change\tlocalization_tier\tobserved_sample_count\tprotein_correction_status\tmechanism_reason_codes\twarning_codes\tclaim_ids\tsource_row_refs\tderived_no_source_reason",
                "ptm-card-1\tP11111:S5:Phospho\tP11111\tcontrol\ttreated\t0.03\t1.5\t\tmedium_confidence\t4\tnot_requested\tcontext_supported\t\tptm-claim-1\tptm_localization.tsv:4\t",
            )
        )
        + "\n",
        encoding="utf-8",
    )

    qc_path = tmp_path / "run_qc.tsv"
    qc_path.write_text(
        "\n".join(
            (
                "scope\tentity_id\tqc_status\tstatus_reason_codes\tmetric_key\tmetric_label\tobserved_value\tunit\tseverity\tdisposition\tenforced_violation\tmessage",
                "run\tt2.mzml\tfail\televated_contaminant_fraction;identification_rate_low\tcontaminant_psm_fraction\tContaminant PSM fraction\t0.12\tfraction\tfailed\tblock\ttrue\tcontaminant evidence burden exceeds the expected background range",
            )
        )
        + "\n",
        encoding="utf-8",
    )

    batch_path = tmp_path / "batch_effect_summary.tsv"
    batch_path.write_text(
        "\n".join(
            (
                "batch_field\tdisposition\tglobal_median_log2_abundance\tbatch_count\tflagged_batch_count\tbatch_variance_proxy\tbatch_associated_component_count\tfully_confounded_with_condition\tbatch_correction_blocked\tbatch_warning\tnote",
                "batch\tblocked\t10.1\t2\t2\t0.8\t2\ttrue\ttrue\tbatch is fully confounded with condition; batch correction is blocked\tbatch estimation detected full confounding between batch and condition and therefore blocks batch correction",
            )
        )
        + "\n",
        encoding="utf-8",
    )

    report = build_analysis_recommendation_report_from_artifacts(
        biological_report_dir=biological_dir,
        ptm_report_dir=ptm_dir,
        run_qc_assessment_tsv_paths=(qc_path,),
        batch_effect_summary_tsv_path=batch_path,
    )

    assert report.summary.recommendation_count == 4
    assert set(report.summary.detected_data_types) == {
        "protein_biological",
        "ptm_site",
        "run_qc",
        "batch_effect",
    }
    by_kind = {entry.recommendation_kind: entry for entry in report.recommendations}
    assert by_kind[AnalysisRecommendationKind.RUN_PTM_CORRECTION].detected_condition_code == (
        "ptm_protein_correction_not_requested"
    )
    assert by_kind[AnalysisRecommendationKind.INSPECT_CONTAMINATION].detected_condition_code == (
        "elevated_contamination"
    )
    assert by_kind[AnalysisRecommendationKind.EXCLUDE_FAILED_RUN].detected_condition_code == (
        "failed_run_qc"
    )
    assert by_kind[AnalysisRecommendationKind.AVOID_BATCH_CORRECTION].detected_condition_code == (
        "batch_condition_confounding"
    )
    assert "detected_condition_code" in render_analysis_recommendation_tsv(report)
