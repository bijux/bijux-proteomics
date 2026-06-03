# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.review import (
    ResultExplanationEvidenceRole,
    ResultExplanationKind,
    ResultExplanationRequest,
    ResultExplanationStatus,
    build_result_explanation_report_from_artifacts,
    render_result_explanation_evidence_tsv,
    render_result_explanation_tsv,
)


def _write_biological_artifacts(path: Path) -> None:
    path.mkdir()
    (path / "biological_protein_cards.tsv").write_text(
        "\n".join(
            (
                "card_id\tgraph_claim_node_id\tgraph_subject_node_id\tgraph_support_node_ids\tgraph_source_row_refs\tprotein_group_id\trepresentative_protein_ref\tprotein_refs\tgene_symbol\tpeptides\tpeptide_count\tunique_peptide_count\tshared_peptide_count\tobserved_sample_count\tmissing_sample_count\tcondition_a\tcondition_b\tlog2_fold_change\tadjusted_p_value\tsignificant\tevidence_tier\twarning_codes",
                "protein-card-p11111\tclaim:P11111\tprotein:P11111\tpeptide:PEPA;peptide:PEPB\tdifferential:P11111;feature:P11111\tpg-P11111\tP11111\tP11111\tAKT1\tPEPA;PEPB\t2\t2\t0\t4\t0\tcontrol\ttreated\t1.8\t0.01\ttrue\thigh_support\tlow_sequence_coverage",
            )
        )
        + "\n",
        encoding="utf-8",
    )
    (path / "biological_evidence_graph_nodes.tsv").write_text(
        "\n".join(
            (
                "node_id\tentity_type\tentity_ref\tcontext_refs",
                "protein:P11111\tprotein\tP11111\t",
                "claim:P11111\tclaim\tprotein-card-p11111\tprotein:P11111",
                "pathway:PWY-001\tpathway\tPWY-001\tprotein:P11111",
                "sample:T2\tsample\tT2\trun:t2.mzml",
                "run:t2.mzml\trun\tt2.mzml\tsample:T2",
            )
        )
        + "\n",
        encoding="utf-8",
    )
    (path / "biological_pathway_activity_condition_comparisons.tsv").write_text(
        "\n".join(
            (
                "pathway_id\tpathway_name\tsource_name\tsource_accession\tcondition_a\tcondition_b\tcondition_a_confidence_status\tcondition_b_confidence_status\tcomparison_confidence_status\tmean_activity_score_a\tmean_activity_score_b\tactivity_score_delta",
                "PWY-001\tCell Cycle\tReactome\tR-HSA-1640170\tcontrol\ttreated\thigh_confidence\thigh_confidence\thigh_confidence\t0.2\t1.4\t1.2",
            )
        )
        + "\n",
        encoding="utf-8",
    )
    (path / "biological_pathway_activity_members.tsv").write_text(
        "\n".join(
            (
                "pathway_id\tpathway_name\tsource_name\tsource_accession\tsample_id\tcondition\tbatch\tmember_kind\tmember_id\tresolved_protein_refs\tobserved_protein_refs\tresolved_protein_count\tobserved_protein_count\tmissing_protein_count\tmember_activity_score\tobserved",
                "PWY-001\tCell Cycle\tReactome\tR-HSA-1640170\tT1\ttreated\t\tprotein\tCDK1\tP11111\tP11111\t1\t1\t0\t1.1\ttrue",
                "PWY-001\tCell Cycle\tReactome\tR-HSA-1640170\tT2\ttreated\t\tprotein\tCCNB1\tP22222\tP22222\t1\t1\t0\t0.9\ttrue",
            )
        )
        + "\n",
        encoding="utf-8",
    )
    (path / "biological_pathway_activity_unresolved.tsv").write_text(
        "\n".join(
            (
                "pathway_id\tpathway_name\tsource_name\tsource_accession\tmember_kind\tmember_id\treason",
                "PWY-001\tCell Cycle\tReactome\tR-HSA-1640170\tprotein\tMCM2\tprotein was not observed in the study matrix",
            )
        )
        + "\n",
        encoding="utf-8",
    )
    (path / "biological_rejected_claims.tsv").write_text(
        "\n".join(
            (
                "claim_id\tclaim_kind\tstatus\tsubject_id\tsubject_label\tclaim_text\tcondition_a\tcondition_b\tasserted_direction\tadjusted_p_value\teffect_size\trobustness_score\timputation_dependent\tevidence_tier\tconfidence_tier\tpathway_confidence_status\tpathway_delta\tregulator_evidence_type\tregulator_signal_surface\tregulator_score\treason_codes\tsource_ids\tsource_row_refs\tderived_no_source_reason\tvalidation_note",
                "claim-pathway-1\tpathway_activity_change\trejected\tPWY-001\tCell Cycle\tCell Cycle is activated in treated samples\tcontrol\ttreated\tupregulated\t0.02\t\t\tfalse\tmoderate\thigh\tlow_confidence\t0.2\t\t\t\tlow_pathway_confidence;missing_directional_delta\tpathway-row-1;protein-card-p11111\t\tpathway activity claims aggregate governed pathway activity comparisons rather than preserving one direct input row\trejected from final narrative because the claim failed one or more required evidence checks",
            )
        )
        + "\n",
        encoding="utf-8",
    )


def _write_ptm_artifacts(path: Path) -> None:
    path.mkdir()
    (path / "ptm_evidence_cards.tsv").write_text(
        "\n".join(
            (
                "card_id\tsite_key\tprotein_ref\tcondition_a\tcondition_b\tadjusted_p_value\tlog2_fold_change\tcorrected_log2_fold_change\tlocalization_tier\tobserved_sample_count\tprotein_correction_status\tmechanism_reason_codes\twarning_codes\tclaim_ids\tsource_row_refs\tderived_no_source_reason",
                "ptm-card-p11111\tP11111:S5:Phospho\tP11111\tcontrol\ttreated\t0.03\t1.5\t0.7\thigh_confidence\t4\tsubtracted_unmodified_protein\tcontext_supported\tshared_peptide_liability\tptm-claim:P11111-S5\tptm_localization.tsv:4\t",
            )
        )
        + "\n",
        encoding="utf-8",
    )


def _write_qc_artifact(path: Path) -> None:
    path.write_text(
        "\n".join(
            (
                "scope\tentity_id\tqc_status\tstatus_reason_codes\tmetric_key\tmetric_label\tobserved_value\tunit\tseverity\tdisposition\tenforced_violation\tmessage",
                "run\tt2.mzml\tfail\tidentification_rate_low\tidentification_rate\tIdentification rate\t0.05\tfraction\tfailed\tblock\ttrue\tidentification rate fell below enforced threshold",
            )
        )
        + "\n",
        encoding="utf-8",
    )


def test_result_explanation_engine_structures_claims_evidence_and_decisions(
    tmp_path: Path,
) -> None:
    biological_dir = tmp_path / "biological_report"
    ptm_dir = tmp_path / "ptm_report"
    qc_path = tmp_path / "run_qc.tsv"
    _write_biological_artifacts(biological_dir)
    _write_ptm_artifacts(ptm_dir)
    _write_qc_artifact(qc_path)

    report = build_result_explanation_report_from_artifacts(
        (
            ResultExplanationRequest(
                explanation_id="protein",
                explanation_kind=ResultExplanationKind.PROTEIN_RESULT,
                subject_id="P11111",
            ),
            ResultExplanationRequest(
                explanation_id="ptm",
                explanation_kind=ResultExplanationKind.PTM_SITE_RESULT,
                subject_id="P11111:S5:Phospho",
            ),
            ResultExplanationRequest(
                explanation_id="pathway",
                explanation_kind=ResultExplanationKind.PATHWAY_RESULT,
                subject_id="PWY-001",
            ),
            ResultExplanationRequest(
                explanation_id="sample-qc",
                explanation_kind=ResultExplanationKind.SAMPLE_QC_DECISION,
                subject_id="T2",
            ),
            ResultExplanationRequest(
                explanation_id="rejected",
                explanation_kind=ResultExplanationKind.REJECTED_EVIDENCE_DECISION,
                subject_id="claim-pathway-1",
            ),
        ),
        biological_report_dir=biological_dir,
        ptm_report_dir=ptm_dir,
        run_qc_assessment_tsv_paths=(qc_path,),
    )

    assert report.summary.explanation_count == 5
    assert report.summary.answered_explanation_count == 5
    assert all(
        explanation.status is ResultExplanationStatus.ANSWERED
        for explanation in report.explanations
    )

    explanations = {
        explanation.explanation_id: explanation for explanation in report.explanations
    }
    assert explanations["protein"].claim.startswith("Protein P11111 changed")
    assert explanations["protein"].confidence == "moderate"
    assert explanations["protein"].evidence
    assert explanations["protein"].opposing_evidence
    assert (
        explanations["protein"].evidence[0].role
        is ResultExplanationEvidenceRole.SUPPORTING
    )

    assert (
        explanations["ptm"].decision == "site was downgraded on the PTM evidence card"
    )
    assert "ptm-claim:P11111-S5" in explanations["ptm"].result_row_ids
    assert explanations["ptm"].opposing_evidence

    assert explanations["pathway"].claim.startswith(
        "Pathway Cell Cycle shows higher activity"
    )
    assert explanations["pathway"].confidence == "high"
    assert any(
        "top observed contributing members" in point.summary
        for point in explanations["pathway"].evidence
    )
    assert any(
        "unresolved member MCM2" in point.summary
        for point in explanations["pathway"].opposing_evidence
    )

    assert explanations["sample-qc"].decision.startswith("sample failed run-level QC")
    assert explanations["sample-qc"].result_row_ids == ("t2.mzml",)
    assert "sample:T2" in explanations["sample-qc"].graph_node_ids

    assert (
        explanations["rejected"].claim == "Cell Cycle is activated in treated samples"
    )
    assert explanations["rejected"].confidence == "high"
    assert any(
        "rejection code low_pathway_confidence" in point.summary
        for point in explanations["rejected"].opposing_evidence
    )

    evidence_tsv = render_result_explanation_evidence_tsv(report)
    explanation_tsv = render_result_explanation_tsv(report)
    assert "evidence_role" in evidence_tsv
    assert "claim" in explanation_tsv
