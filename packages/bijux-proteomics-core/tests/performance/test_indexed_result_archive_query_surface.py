# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path
import time

import bijux_proteomics.review as review
from bijux_proteomics.review.evidence_graph.evidence_graph import (
    ProteomicsEvidenceEdgeKind,
)
import bijux_proteomics.workflow as workflow


def _write_large_evidence_graph_artifacts(
    path: Path, *, entity_count: int
) -> tuple[Path, Path]:
    path.mkdir(parents=True, exist_ok=True)
    nodes_path = path / "evidence_graph_nodes.tsv"
    edges_path = path / "evidence_graph_edges.tsv"
    node_rows = [
        "node_id\tentity_type\tentity_ref\tlabel\tclaim_state\ttrust_class\tcontradiction_ids\tcontext_refs"
    ]
    edge_rows = [
        "source_node_id\ttarget_node_id\trelation\tsource_row_ref\tconfidence\tevidence_type\treason\tsupport_count"
    ]
    for index in range(entity_count):
        sample_id = f"S{index}"
        run_id = f"R{index}"
        spectrum_id = f"scan={index}"
        precursor_id = f"PEP{index}/2"
        psm_id = f"psm:{index}"
        peptide_id = f"PEP{index}"
        modified_peptide_id = f"PEP{index}[Phospho@S3]"
        protein_id = f"P{index:05d}"
        ptm_site_id = f"{protein_id}:S3:Phospho"
        pathway_id = f"R-HSA-{index:05d}"
        qc_id = f"qc:{run_id}:fail"

        node_rows.extend(
            (
                f"sample:{sample_id}\tsample\t{sample_id}\tsample {sample_id}\tobserved\tunreviewed\t\t",
                f"run:{run_id}\trun\t{run_id}\trun {run_id}\tobserved\tunreviewed\t\tsample:{sample_id}",
                f"spectrum:{spectrum_id}\tspectrum\t{spectrum_id}\t{spectrum_id}\tobserved\tunreviewed\t\trun:{run_id}",
                f"precursor:{precursor_id}\tprecursor\t{precursor_id}\t{precursor_id}\tobserved\tunreviewed\t\t",
                f"psm:{psm_id}\tpsm\t{psm_id}\t{psm_id}\tobserved\tunreviewed\t\t",
                f"peptide:{peptide_id}\tpeptide\t{peptide_id}\t{peptide_id}\tobserved\tunreviewed\t\t",
                (
                    f"modified_peptide:{modified_peptide_id}\tmodified_peptide\t{modified_peptide_id}\t"
                    f"{modified_peptide_id}\tobserved\tunreviewed\t\t"
                ),
                f"protein:{protein_id}\tprotein\t{protein_id}\t{protein_id}\tobserved\tunreviewed\t\t",
                f"ptm_site:{ptm_site_id}\tptm_site\t{ptm_site_id}\t{ptm_site_id}\tobserved\tunreviewed\t\t",
                f"pathway:{pathway_id}\tpathway\t{pathway_id}\tpathway {pathway_id}\tobserved\tunreviewed\t\t",
                f"qc_decision:{qc_id}\tqc_decision\t{qc_id}\t{qc_id}\tcaution\tmoderate\t\t",
            )
        )
        edge_rows.extend(
            (
                (
                    f"sample:{sample_id}\trun:{run_id}\t{ProteomicsEvidenceEdgeKind.SAMPLE_CONTAINS_RUN.value}\t"
                    f"design.tsv:{index + 2}\t1.0\tworkflow_context\tsample maps to run\t1"
                ),
                (
                    f"run:{run_id}\tspectrum:{spectrum_id}\t{ProteomicsEvidenceEdgeKind.RUN_ACQUIRED_SPECTRUM.value}\t"
                    f"spectra.mgf:{index + 1}\t1.0\tspectrum_assignment\trun acquired spectrum\t1"
                ),
                (
                    f"spectrum:{spectrum_id}\tprecursor:{precursor_id}\t{ProteomicsEvidenceEdgeKind.SPECTRUM_ASSIGNS_PRECURSOR.value}\t"
                    f"features.tsv:{index + 1}\t0.97\tprecursor_assignment\tspectrum assigns precursor\t1"
                ),
                (
                    f"spectrum:{spectrum_id}\tpsm:{psm_id}\t{ProteomicsEvidenceEdgeKind.SPECTRUM_SUPPORTS_PSM.value}\t"
                    f"psm.tsv:{index + 1}\t0.96\tspectrum_assignment\tspectrum supports psm\t1"
                ),
                (
                    f"precursor:{precursor_id}\tpeptide:{peptide_id}\t{ProteomicsEvidenceEdgeKind.PRECURSOR_SUPPORTS_PEPTIDE.value}\t"
                    f"features.tsv:{index + 1}\t0.95\tprecursor_assignment\tprecursor supports peptide\t1"
                ),
                (
                    f"psm:{psm_id}\tpeptide:{peptide_id}\t{ProteomicsEvidenceEdgeKind.PSM_SUPPORTS_PEPTIDE.value}\t"
                    f"psm.tsv:{index + 1}\t0.94\tspectrum_assignment\tpsm supports peptide\t1"
                ),
                (
                    f"peptide:{peptide_id}\tmodified_peptide:{modified_peptide_id}\t{ProteomicsEvidenceEdgeKind.PEPTIDE_HAS_MODIFIED_FORM.value}\t"
                    f"ptm.tsv:{index + 1}\t0.93\tptm_localization\tpeptide has modified form\t1"
                ),
                (
                    f"modified_peptide:{modified_peptide_id}\tptm_site:{ptm_site_id}\t{ProteomicsEvidenceEdgeKind.MODIFIED_PEPTIDE_LOCALIZES_PTM_SITE.value}\t"
                    f"ptm.tsv:{index + 1}\t0.92\tptm_localization\tmodified peptide localizes ptm site\t1"
                ),
                (
                    f"peptide:{peptide_id}\tprotein:{protein_id}\t{ProteomicsEvidenceEdgeKind.PEPTIDE_MAPS_TO_PROTEIN.value}\t"
                    f"digest.tsv:{index + 1}\t1.0\tsequence_mapping\tpeptide maps to protein\t1"
                ),
                (
                    f"peptide:{peptide_id}\tprotein:{protein_id}\t{ProteomicsEvidenceEdgeKind.PEPTIDE_QUANTIFIES_PROTEIN.value}\t"
                    f"protein_matrix.tsv:{index + 1}\t0.91\tquantification\tpeptide quantifies protein\t1"
                ),
                (
                    f"ptm_site:{ptm_site_id}\tprotein:{protein_id}\t{ProteomicsEvidenceEdgeKind.PTM_SITE_BELONGS_TO_PROTEIN.value}\t"
                    f"site_mapping.tsv:{index + 1}\t1.0\tannotation\tptm site belongs to protein\t1"
                ),
                (
                    f"protein:{protein_id}\tpathway:{pathway_id}\t{ProteomicsEvidenceEdgeKind.PROTEIN_MEMBER_OF_PATHWAY.value}\t"
                    f"pathway.tsv:{index + 1}\t0.88\tannotation\tprotein belongs to pathway\t1"
                ),
                (
                    f"run:{run_id}\tqc_decision:{qc_id}\t{ProteomicsEvidenceEdgeKind.RUN_GOVERNED_BY_QC_DECISION.value}\t"
                    f"qc.tsv:{index + 1}\t1.0\tqc\trun governed by qc decision\t1"
                ),
            )
        )
    nodes_path.write_text("\n".join(node_rows) + "\n", encoding="utf-8")
    edges_path.write_text("\n".join(edge_rows) + "\n", encoding="utf-8")
    return nodes_path, edges_path


def _write_large_result_artifacts(
    path: Path,
    *,
    protein_count: int,
    sample_count: int,
) -> tuple[Path, Path, Path]:
    path.mkdir(parents=True, exist_ok=True)
    biological_dir = path / "biological_report"
    ptm_dir = path / "ptm_report"
    biological_dir.mkdir()
    ptm_dir.mkdir()
    protein_rows = [
        (
            "card_id\tgraph_claim_node_id\tgraph_subject_node_id\tgraph_support_node_ids\t"
            "graph_source_row_refs\tprotein_group_id\trepresentative_protein_ref\tprotein_refs\t"
            "gene_symbol\tpeptides\tpeptide_count\tunique_peptide_count\tshared_peptide_count\t"
            "observed_sample_count\tmissing_sample_count\tcondition_a\tcondition_b\t"
            "log2_fold_change\tadjusted_p_value\tsignificant\tevidence_tier\twarning_codes"
        )
    ]
    graph_rows = ["node_id\tentity_type\tentity_ref\tcontext_refs"]
    ptm_rows = [
        (
            "card_id\tsite_key\tprotein_ref\tcondition_a\tcondition_b\tadjusted_p_value\t"
            "log2_fold_change\tcorrected_log2_fold_change\tlocalization_tier\t"
            "observed_sample_count\tprotein_correction_status\tmechanism_reason_codes\t"
            "warning_codes\tclaim_ids\tsource_row_refs\tderived_no_source_reason"
        )
    ]
    rejected_claim_rows = [
        (
            "claim_id\tclaim_kind\tstatus\tsubject_id\tsubject_label\tclaim_text\tcondition_a\t"
            "condition_b\tasserted_direction\tadjusted_p_value\teffect_size\trobustness_score\t"
            "imputation_dependent\tevidence_tier\tconfidence_tier\tpathway_confidence_status\t"
            "pathway_delta\tregulator_evidence_type\tregulator_signal_surface\tregulator_score\t"
            "reason_codes\tsource_ids\tsource_row_refs\tderived_no_source_reason\tvalidation_note"
        )
    ]
    for index in range(protein_count):
        protein_ref = f"P{index:05d}"
        gene_symbol = f"GENE{index:05d}"
        card_id = f"protein-card-{protein_ref}"
        graph_rows.append(f"subject:{protein_ref}\tprotein\t{protein_ref}\t")
        graph_rows.append(
            f"claim:{protein_ref}\tclaim\t{card_id}\tsubject:{protein_ref}"
        )
        graph_rows.append(
            f"support:{protein_ref}\tpeptide\tPEP{index}\tsubject:{protein_ref}"
        )
        protein_rows.append(
            f"{card_id}\tclaim:{protein_ref}\tsubject:{protein_ref}\tsupport:{protein_ref}\t"
            f"protein-row:{protein_ref}\tpg-{protein_ref}\t{protein_ref}\t{protein_ref}\t{gene_symbol}\t"
            f"PEP{index};PEP{index}B\t2\t1\t1\t6\t0\tcontrol\ttreated\t1.2\t0.01\ttrue\thigh\t"
        )
        ptm_rows.append(
            f"ptm-card-{protein_ref}\t{protein_ref}:S3:Phospho\t{protein_ref}\tcontrol\ttreated\t0.02\t"
            f"0.8\t0.5\thigh\t5\tsubtracted_unmodified_protein\tcontext_supported\tshared_peptide_liability\t"
            f"ptm-claim-{protein_ref}\tptm.tsv:{index + 1}\t"
        )
        rejected_claim_rows.append(
            f"rejected-claim-{protein_ref}\tprotein_abundance_change\trejected\t{protein_ref}\t{gene_symbol}\t"
            f"{gene_symbol} was rejected\tcontrol\ttreated\tdown\t0.2\t0.5\t0.6\tfalse\tmoderate\tmoderate\t\t\t\t\t\t"
            f"shared_peptide_liability\t{card_id}\tprotein-row:{protein_ref}\t\tclaim rejected after review"
        )
    for index in range(sample_count):
        sample_id = f"S{index:04d}"
        run_id = f"run-{index:04d}"
        graph_rows.append(f"sample:{sample_id}\tsample\t{sample_id}\t")
        graph_rows.append(f"run:{run_id}\trun\t{run_id}\tsample:{sample_id}")

    (biological_dir / "biological_protein_cards.tsv").write_text(
        "\n".join(protein_rows) + "\n",
        encoding="utf-8",
    )
    (biological_dir / "biological_evidence_graph_nodes.tsv").write_text(
        "\n".join(graph_rows) + "\n",
        encoding="utf-8",
    )
    (biological_dir / "biological_rejected_claims.tsv").write_text(
        "\n".join(rejected_claim_rows) + "\n",
        encoding="utf-8",
    )
    (ptm_dir / "ptm_evidence_cards.tsv").write_text(
        "\n".join(ptm_rows) + "\n",
        encoding="utf-8",
    )
    qc_path = path / "run_qc.tsv"
    qc_rows = [
        (
            "scope\tentity_id\tqc_status\tstatus_reason_codes\tmetric_key\tmetric_label\tobserved_value\t"
            "unit\tseverity\tdisposition\tenforced_violation\tmessage"
        )
    ]
    for index in range(sample_count):
        qc_rows.append(
            f"run\trun-{index:04d}\tfail\tidentification_rate_low\tidentification_rate\t"
            f"Identification rate\t0.05\tfraction\tfailed\tblock\ttrue\tfailed qc for run-{index:04d}"
        )
    qc_path.write_text("\n".join(qc_rows) + "\n", encoding="utf-8")
    return biological_dir, ptm_dir, qc_path


def _write_large_standard_card_tsv(path: Path, *, card_count: int) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    card_path = path / "standard_cards.tsv"
    rows = [
        "card_id\tcard_kind\tsubject_kind\tsubject_id\tsubject_label\tclaim\tevidence_for\tevidence_against\tconfidence\twarning_codes\tsource_ids"
    ]
    for index in range(card_count):
        rows.append(
            f"card:{index}\tprotein\tprotein\tP{index:05d}\tP{index:05d}\tclaim {index}\t"
            f"support {index}\topposition {index}\thigh\twarning_{index % 7}\tsource:{index};source:{index + 1}"
        )
    card_path.write_text("\n".join(rows) + "\n", encoding="utf-8")
    return card_path


def test_indexed_large_result_archive_queries_stay_below_latency_threshold(
    tmp_path: Path,
) -> None:
    nodes_path, edges_path = _write_large_evidence_graph_artifacts(
        tmp_path / "evidence_graph",
        entity_count=1200,
    )
    lazy_graph = review.load_lazy_proteomics_evidence_graph(nodes_path, edges_path)

    graph_start = time.perf_counter()
    for offset in (0, 300, 600, 900, 1199):
        review.query_protein_evidence_summary(lazy_graph, protein_id=f"P{offset:05d}")
        review.query_peptide_support_chain(lazy_graph, peptide_id=f"PEP{offset}")
        review.query_ptm_site_evidence(
            lazy_graph,
            ptm_site_id=f"P{offset:05d}:S3:Phospho",
        )
        review.query_pathway_support_proteins(
            lazy_graph,
            pathway_id=f"R-HSA-{offset:05d}",
        )
        review.query_sample_qc_reasons(lazy_graph, sample_id=f"S{offset}")
    graph_elapsed = time.perf_counter() - graph_start

    biological_dir, ptm_dir, qc_path = _write_large_result_artifacts(
        tmp_path / "result_archives",
        protein_count=1800,
        sample_count=600,
    )
    requests = (
        tuple(
            review.ResultQueryRequest(
                query_id=f"protein-significance-{offset}",
                query_kind=review.ResultQueryKind.PROTEIN_SIGNIFICANCE,
                subject_id=f"P{offset:05d}",
            )
            for offset in range(0, 300, 3)
        )
        + tuple(
            review.ResultQueryRequest(
                query_id=f"protein-peptides-{offset}",
                query_kind=review.ResultQueryKind.PROTEIN_PEPTIDE_SUPPORT,
                subject_id=f"P{offset:05d}",
            )
            for offset in range(0, 300, 3)
        )
        + tuple(
            review.ResultQueryRequest(
                query_id=f"sample-qc-{offset}",
                query_kind=review.ResultQueryKind.SAMPLE_QC_FAILURE,
                subject_id=f"S{offset:04d}",
            )
            for offset in range(0, 180, 3)
        )
        + tuple(
            review.ResultQueryRequest(
                query_id=f"ptm-downgrade-{offset}",
                query_kind=review.ResultQueryKind.PTM_SITE_DOWNGRADE,
                subject_id=f"P{offset:05d}:S3:Phospho",
            )
            for offset in range(0, 180, 3)
        )
    )

    result_query_start = time.perf_counter()
    result_query_report = review.build_result_query_report_from_artifacts(
        requests,
        biological_report_dir=biological_dir,
        ptm_report_dir=ptm_dir,
        run_qc_assessment_tsv_paths=(qc_path,),
    )
    result_query_elapsed = time.perf_counter() - result_query_start

    explanation_requests = tuple(
        review.ResultExplanationRequest(
            explanation_id=f"rejected-{offset}",
            explanation_kind=review.ResultExplanationKind.REJECTED_EVIDENCE_DECISION,
            subject_id=f"rejected-claim-P{offset:05d}",
        )
        for offset in range(0, 200, 2)
    )
    explanation_start = time.perf_counter()
    explanation_report = review.build_result_explanation_report_from_artifacts(
        explanation_requests,
        biological_report_dir=biological_dir,
        ptm_report_dir=ptm_dir,
    )
    explanation_elapsed = time.perf_counter() - explanation_start

    card_path = _write_large_standard_card_tsv(
        tmp_path / "standard_cards", card_count=2500
    )
    card_index = review.load_standard_card_index(card_path)
    card_lookup_start = time.perf_counter()
    for offset in range(0, 1500, 3):
        assert (
            review.find_standard_card_by_card_id(card_index, f"card:{offset}")
            is not None
        )
        assert review.find_standard_cards_by_subject_id(card_index, f"P{offset:05d}")
        assert review.find_standard_cards_by_source_id(card_index, f"source:{offset}")
    card_lookup_elapsed = time.perf_counter() - card_lookup_start

    manifest = workflow.WorkflowArtifactLayoutManifest(
        producer_function="test_indexed_result_archive_queries_stay_below_latency_threshold",
        artifacts=tuple(
            workflow.WorkflowArtifactLayoutEntry(
                artifact_id=f"artifact:reports:tsv_table:reports:artifact_{index}.tsv",
                legacy_relative_path=f"artifact_{index}.tsv",
                relative_path=f"reports/artifact_{index}.tsv",
                canonical_relative_path=f"reports/artifact_{index}.tsv",
                folder=workflow.WorkflowArtifactFolder.REPORTS,
                artifact_kind=workflow.WorkflowArtifactKind.TSV_TABLE,
                artifact_schema="tsv[value]",
                artifact_schema_version="2026-05-26",
                output_table_schema=None,
                output_table_schema_sidecar_relative_path=None,
                row_count=1,
                checksum_sha256="a" * 64,
                producer_function="test_indexed_result_archive_queries_stay_below_latency_threshold",
            )
            for index in range(2500)
        ),
    )
    artifact_index = workflow.exports.index_workflow_artifact_manifest(manifest=manifest)
    artifact_lookup_start = time.perf_counter()
    for offset in range(0, 2000, 2):
        assert (
            workflow.exports.find_workflow_artifact_by_id(
                artifact_index,
                f"artifact:reports:tsv_table:reports:artifact_{offset}.tsv",
            )
            is not None
        )
        assert (
            workflow.exports.find_workflow_artifact_by_legacy_path(
                artifact_index,
                f"artifact_{offset}.tsv",
            )
            is not None
        )
    artifact_lookup_elapsed = time.perf_counter() - artifact_lookup_start

    assert result_query_report.summary.answered_query_count == len(requests)
    assert explanation_report.summary.answered_explanation_count == len(
        explanation_requests
    )
    assert graph_elapsed < 0.75
    assert result_query_elapsed < 1.5
    assert explanation_elapsed < 1.25
    assert card_lookup_elapsed < 0.25
    assert artifact_lookup_elapsed < 0.2
