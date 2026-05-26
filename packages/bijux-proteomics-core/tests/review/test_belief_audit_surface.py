# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.review.belief_audit import (
    BeliefAuditSubjectKind,
    build_belief_audit_report_from_artifacts,
    render_belief_audit_html,
    render_belief_audit_tsv,
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
    (path / "biological_regulator_inference.tsv").write_text(
        "\n".join(
            (
                "regulator\tevidence_type\tsignal_surface\tsource_name\tsource_accession\ttarget_count\tmatched_target_count\tcoverage_fraction\tsupporting_protein_refs\tsupporting_site_keys\tsupporting_pathway_ids\tdirection\tscore\tmean_log2_fold_change\tmean_activity_score_delta\tnote",
                "CDK1\tpathway_targets\tprotein_change\tReactome\tR-HSA-1640170\t4\t2\t0.5\tP11111\tP11111:S5:Phospho\tPWY-001\tactivated\t1.3\t1.2\t0.8\tregulator inference remains partial because not all pathway targets were observed",
            )
        )
        + "\n",
        encoding="utf-8",
    )
    (path / "biological_regulator_inference_unresolved.tsv").write_text(
        "\n".join(
            (
                "regulator\tevidence_type\ttarget_field\ttarget_value\tsource_name\tsource_accession\treason",
                "CDK1\tpathway_targets\tprotein_ref\tMCM2\tReactome\tR-HSA-1640170\tprotein was not observed in the study matrix",
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


def _write_validation_artifacts(card_path: Path, warning_path: Path) -> None:
    card_path.write_text(
        "\n".join(
            (
                "candidate_id\tcandidate_kind\tdisplay_label\ttarget_protein_ref\tsite_key\tdiscovery_priority_rank\tdiscovery_final_score\tdiscovery_weighted_evidence_total\tdiscovery_penalty_total\tdiscovery_uncertainty\tdiscovery_effect_size\tdiscovery_adjusted_p_value\tdiscovery_support_count\tbiological_role_labels\tbiological_source_ids\tdiscovery_rank_reason_codes\tassay_entry_count\tomitted_reason\ttargeted_validation_verdict\ttargeted_validation_log2_effect\tconfirmed_assay_count\tcontradicted_assay_count\tinconclusive_assay_count\ttargeted_validation_reason_codes\tstability_score\tstability_downgraded\tstability_reason_codes\tredundancy_cluster_id\trepresentative_candidate_id\tredundancy_representative\tredundancy_dropped\tredundancy_reason_codes\tfinal_status\twarning_codes\tnote",
                "candidate-1\tprotein\tAKT1 candidate\tP11111\t\t1\t0.91\t1.3\t0.1\t0.05\t1.8\t0.01\t3\tkinase_panel\tsupported_claim_1\tstrong_rank\t2\t\tconfirmed\t1.1\t2\t0\t0\torthogonal_support\t0.9\tfalse\t\tcluster-1\tcandidate-1\ttrue\tfalse\t\tconfirmed\tshared_peptide_liability\tconfirmed by targeted assays with one retained warning",
            )
        )
        + "\n",
        encoding="utf-8",
    )
    warning_path.write_text(
        "\n".join(
            (
                "candidate_id\twarning_code\tnote",
                "candidate-1\tshared_peptide_liability\tshared peptide evidence can still confound the candidate if orthogonal support drops",
            )
        )
        + "\n",
        encoding="utf-8",
    )


def test_belief_audit_engine_makes_major_conclusions_challengeable(
    tmp_path: Path,
) -> None:
    biological_dir = tmp_path / "biological_report"
    ptm_dir = tmp_path / "ptm_report"
    qc_path = tmp_path / "run_qc.tsv"
    validation_card_path = tmp_path / "validation_evidence_cards.tsv"
    validation_warning_path = tmp_path / "validation_evidence_card_warnings.tsv"
    _write_biological_artifacts(biological_dir)
    _write_ptm_artifacts(ptm_dir)
    _write_qc_artifact(qc_path)
    _write_validation_artifacts(validation_card_path, validation_warning_path)

    report = build_belief_audit_report_from_artifacts(
        biological_report_dir=biological_dir,
        ptm_report_dir=ptm_dir,
        validation_evidence_card_tsv=validation_card_path,
        validation_evidence_warning_tsv=validation_warning_path,
        run_qc_assessment_tsv_paths=(qc_path,),
    )

    assert report.summary.entry_count == 6
    assert report.summary.protein_entry_count == 1
    assert report.summary.ptm_site_entry_count == 1
    assert report.summary.pathway_entry_count == 1
    assert report.summary.regulator_entry_count == 1
    assert report.summary.biomarker_entry_count == 1
    assert report.summary.qc_decision_entry_count == 1

    entries = {
        entry.subject_kind: entry
        for entry in report.entries
    }
    assert entries[BeliefAuditSubjectKind.PROTEIN].what_would_falsify.startswith(
        "A rerun that removes statistical support"
    )
    assert "warning code low_sequence_coverage" in entries[
        BeliefAuditSubjectKind.PROTEIN
    ].what_weakens
    assert entries[BeliefAuditSubjectKind.PTM_SITE].decision == (
        "site was downgraded on the PTM evidence card"
    )
    assert entries[BeliefAuditSubjectKind.PATHWAY].graph_node_ids == ("pathway:PWY-001",)
    assert entries[BeliefAuditSubjectKind.REGULATOR].result_surfaces == (
        "biological_regulator_inference",
        "biological_regulator_inference_unresolved",
    )
    assert "unresolved target MCM2" in entries[
        BeliefAuditSubjectKind.REGULATOR
    ].what_weakens
    assert "shared_peptide_liability" in entries[
        BeliefAuditSubjectKind.BIOMARKER
    ].what_weakens
    assert entries[BeliefAuditSubjectKind.QC_DECISION].decision.startswith(
        "sample failed run-level QC"
    )

    audit_tsv = render_belief_audit_tsv(report)
    html = render_belief_audit_html(report)
    assert "what_would_falsify" in audit_tsv
    assert "<h1>Belief Audit</h1>" in html
    assert "<h2>Biomarkers</h2>" in html
