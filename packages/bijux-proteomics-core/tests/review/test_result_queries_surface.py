# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.io.formats import parse_experimental_design_table
from bijux_proteomics.ptm import (
    PtmEvidenceCardPolicy,
    PtmPhosphositeSelectionPolicy,
    PtmProteinCorrectionMode,
    PtmRegulatorEnrichmentPolicy,
    build_ptm_report_bundle,
    export_ptm_report_bundle,
    parse_ptm_localization_tsv,
    parse_ptm_ortholog_site_tsv,
    parse_ptm_site_annotation_tsv,
)
from bijux_proteomics.quantification import parse_ms1_feature_table
from bijux_proteomics.review import (
    ResultQueryKind,
    ResultQueryStatus,
    ResultQueryRequest,
    build_result_query_report_from_artifacts,
    render_result_query_answer_tsv,
    render_result_query_evidence_tsv,
)
from bijux_proteomics.sequences import FastaParseMode, parse_fasta_document
from bijux_proteomics.workflow import (
    build_biological_result_report_bundle,
    export_biological_result_report_bundle,
)


def _workflow_fixture(name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures" / "workflow" / name


def _ptm_fixture(name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures" / "ptm" / name


def _protein_sequences() -> dict[str, str]:
    fasta = (
        Path(__file__).resolve().parent.parent / "fixtures" / "fasta" / "ptm_sites.fasta"
    )
    report = parse_fasta_document(fasta.read_text(), mode=FastaParseMode.STRICT)
    return {
        record.canonical_accession: record.residues
        for record in report.accepted_records
    }


def _ptm_design_entries():
    return tuple(
        entry.model_copy(update={"batch": None})
        for entry in parse_experimental_design_table(
            _ptm_fixture("ptm.design.tsv")
        ).accepted_entries
    )


def _write_qc_failure_tsv(path: Path) -> None:
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


def test_result_query_engine_answers_protein_qc_and_ptm_questions_with_row_and_graph_links(
    tmp_path: Path,
) -> None:
    design_entries = tuple(
        parse_experimental_design_table(
            _workflow_fixture("biological_report.design.tsv")
        ).accepted_entries
    )
    biological_report = build_biological_result_report_bundle(
        _workflow_fixture("biological_report_features.tsv"),
        design_entries,
        proteins_fasta_path=_workflow_fixture("biological_report_reference.fasta"),
        condition_a="control",
        condition_b="treatment",
    )
    biological_dir = tmp_path / "biological_report"
    export_biological_result_report_bundle(biological_report, biological_dir)

    ptm_evidence = parse_ptm_localization_tsv(_ptm_fixture("localization_results.tsv"))
    ptm_features = parse_ms1_feature_table(_ptm_fixture("ptm_features.tsv"))
    ptm_annotations = parse_ptm_site_annotation_tsv(_ptm_fixture("ptm_site_annotations.tsv"))
    ortholog_sites = parse_ptm_ortholog_site_tsv(_ptm_fixture("ptm_ortholog_sites.tsv"))
    ptm_report = build_ptm_report_bundle(
        ptm_evidence.accepted_records,
        protein_sequences=_protein_sequences(),
        feature_records=ptm_features.accepted_records,
        design_entries=_ptm_design_entries(),
        protein_correction_mode=PtmProteinCorrectionMode.SUBTRACT_UNMODIFIED_PROTEIN,
        batch_field="",
        motif_selection_policy=PtmPhosphositeSelectionPolicy(
            max_adjusted_p_value=1.0,
            min_absolute_log2_fold_change=0.0,
        ),
        annotation_records=ptm_annotations.accepted_records,
        annotation_target_species="Homo sapiens",
        regulator_enrichment_policy=PtmRegulatorEnrichmentPolicy(
            max_adjusted_p_value=1.0,
            min_absolute_log2_fold_change=0.0,
        ),
        ortholog_site_records=ortholog_sites.accepted_records,
        ortholog_source_species="Homo sapiens",
        ortholog_target_species="Mus musculus",
        evidence_card_policy=PtmEvidenceCardPolicy(max_adjusted_p_value=1.0),
    )
    assert ptm_report.evidence_cards is not None
    ptm_dir = tmp_path / "ptm_report"
    export_ptm_report_bundle(ptm_report, ptm_dir)

    qc_path = tmp_path / "run_qc.tsv"
    _write_qc_failure_tsv(qc_path)

    significant_protein = next(
        card for card in biological_report.protein_cards.cards if card.significant
    )
    downgraded_site = next(
        card
        for card in ptm_report.evidence_cards.cards
        if card.warnings or card.protein_correction.status != "not_requested"
    )
    report = build_result_query_report_from_artifacts(
        (
            ResultQueryRequest(
                query_id="protein-significance",
                query_kind=ResultQueryKind.PROTEIN_SIGNIFICANCE,
                subject_id=significant_protein.representative_protein_ref,
            ),
            ResultQueryRequest(
                query_id="protein-peptides",
                query_kind=ResultQueryKind.PROTEIN_PEPTIDE_SUPPORT,
                subject_id=significant_protein.representative_protein_ref,
            ),
            ResultQueryRequest(
                query_id="sample-qc",
                query_kind=ResultQueryKind.SAMPLE_QC_FAILURE,
                subject_id="T2",
            ),
            ResultQueryRequest(
                query_id="ptm-downgrade",
                query_kind=ResultQueryKind.PTM_SITE_DOWNGRADE,
                subject_id=downgraded_site.site_key,
            ),
        ),
        biological_report_dir=biological_dir,
        ptm_report_dir=ptm_dir,
        run_qc_assessment_tsv_paths=(qc_path,),
    )

    assert report.summary.query_count == 4
    assert report.summary.answered_query_count == 3
    assert report.summary.unsupported_query_count == 1

    answers_by_id = {answer.query_id: answer for answer in report.answers}
    assert answers_by_id["protein-significance"].status is ResultQueryStatus.ANSWERED
    assert answers_by_id["protein-peptides"].status is ResultQueryStatus.ANSWERED
    assert answers_by_id["sample-qc"].status is ResultQueryStatus.ANSWERED
    assert significant_protein.card_id in answers_by_id["protein-significance"].result_row_ids
    assert significant_protein.graph_claim_node_id in answers_by_id["protein-significance"].graph_node_ids
    assert "significant" in answers_by_id["protein-significance"].answer_text
    assert "peptides" in answers_by_id["protein-peptides"].answer_text
    assert "t2.mzml" in answers_by_id["sample-qc"].result_row_ids
    assert any(node_id.startswith("sample:") for node_id in answers_by_id["sample-qc"].graph_node_ids)
    assert answers_by_id["ptm-downgrade"].status is ResultQueryStatus.UNSUPPORTED
    assert "graph node anchor" in answers_by_id["ptm-downgrade"].answer_text
    assert answers_by_id["ptm-downgrade"].result_row_ids == ()
    assert answers_by_id["ptm-downgrade"].graph_node_ids == ()
    assert "row_id" in render_result_query_evidence_tsv(report)
    assert "answer_text" in render_result_query_answer_tsv(report)


def test_result_query_engine_answers_ptm_downgrade_with_parent_graph_anchor(
    tmp_path: Path,
) -> None:
    biological_dir = tmp_path / "biological_report"
    biological_dir.mkdir()
    (biological_dir / "biological_protein_cards.tsv").write_text(
        "\n".join(
            (
                "card_id\tgraph_claim_node_id\tgraph_subject_node_id\tgraph_subject_node_kind\tgraph_support_node_ids\tgraph_source_row_refs\tprotein_group_id\trepresentative_protein_ref\tprotein_refs\tidentity_level\tidentity_reason\tgene_symbol\tpeptides\tpeptide_count\tunique_peptide_count\tshared_peptide_count\tcoverage_fraction\tmedian_intensity\tmissing_fraction\tcondition_a\tcondition_b\tcondition_a_mean_intensity\tcondition_b_mean_intensity\tlog2_fold_change\tadjusted_p_value\tsignificant\tevidence_tier\twarning_codes",
                "protein-card-p11111\tclaim:P11111\tsubject:P11111\tprotein\tsupport:P11111\tprotein-row:P11111\tpg-P11111\tP11111\tP11111\tprotein_group\tunique peptide evidence\tAKT1\tPEPTIDEK\t1\t1\t0\t0.25\t1000\t0\tcontrol\ttreated\t100\t400\t2\t0.01\ttrue\thigh\t",
            )
        )
        + "\n",
        encoding="utf-8",
    )
    (biological_dir / "biological_evidence_graph_nodes.tsv").write_text(
        "\n".join(
            (
                "node_id\tentity_type\tentity_ref\tcontext_refs",
                "subject:P11111\tprotein\tP11111\t",
                "claim:P11111\tclaim\tprotein-card-p11111\tsubject:P11111",
                "support:P11111\tpeptide\tPEPTIDEK\tsubject:P11111",
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
                "card_id\tsite_key\tprotein_ref\tadjusted_p_value\tlog2_fold_change\tcorrected_log2_fold_change\tprotein_correction_status\tmechanism_reason_codes\twarning_codes\tclaim_ids\tsource_row_refs\tderived_no_source_reason",
                "ptm-card-p11111\tP11111:S5:Phospho\tP11111\t0.02\t1.5\t0.8\tsubtracted_unmodified_protein\tcontext_supported\tshared_peptide_liability\tptm-claim:P11111-S5\tptm_localization.tsv:4\t",
            )
        )
        + "\n",
        encoding="utf-8",
    )

    report = build_result_query_report_from_artifacts(
        (
            ResultQueryRequest(
                query_id="ptm-downgrade",
                query_kind=ResultQueryKind.PTM_SITE_DOWNGRADE,
                subject_id="P11111:S5:Phospho",
            ),
        ),
        biological_report_dir=biological_dir,
        ptm_report_dir=ptm_dir,
    )

    assert report.summary.answered_query_count == 1
    answer = report.answers[0]
    assert answer.status is ResultQueryStatus.ANSWERED
    assert answer.result_row_ids == ("ptm-card-p11111", "ptm-claim:P11111-S5")
    assert "subject:P11111" in answer.graph_node_ids
    assert "claim:P11111" in answer.graph_node_ids
    assert answer.evidence_links[0].graph_node_ids == answer.graph_node_ids
