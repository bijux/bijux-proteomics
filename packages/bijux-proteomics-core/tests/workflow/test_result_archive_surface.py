# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

import pytest

from bijux_proteomics.domain.errors import ScientificEvidenceError
from bijux_proteomics.io.formats import parse_experimental_design_table
from bijux_proteomics.ptm import (
    PtmEvidenceCardPolicy,
    PtmProteinCorrectionMode,
    PtmRegulatorEnrichmentPolicy,
    build_ptm_report_bundle,
    export_ptm_report_bundle,
    parse_ptm_localization_tsv,
    parse_ptm_site_annotation_tsv,
)
from bijux_proteomics.quantification import parse_ms1_feature_table
from bijux_proteomics.review import (
    query_pathway_support_proteins,
    query_peptide_support_chain,
    query_protein_evidence_summary,
)
from bijux_proteomics.sequences import FastaParseMode, parse_fasta_document
from bijux_proteomics.workflow import (
    ProteomicsStudyConclusionKind,
    ProteomicsStudyKind,
    ProteomicsStudyQcKind,
    build_biological_result_report_bundle,
    build_result_manifest_from_artifacts,
    export_biological_result_report_bundle,
    write_result_archive_lab_action_packets,
)
from bijux_proteomics.workflow.result_archive import load_result_archive


def _workflow_fixture(name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures" / "workflow" / name


def _ptm_fixture(name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures" / "ptm" / name


def _fasta_fixture(name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures" / "fasta" / name


def _protein_sequences() -> dict[str, str]:
    report = parse_fasta_document(
        _fasta_fixture("ptm_sites.fasta").read_text(encoding="utf-8"),
        mode=FastaParseMode.STRICT,
    )
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


def _write_run_qc_tsv(path: Path) -> None:
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


def _write_biological_report_dir(tmp_path: Path) -> Path:
    design_entries = tuple(
        parse_experimental_design_table(
            _workflow_fixture("biological_report.design.tsv")
        ).accepted_entries
    )
    report = build_biological_result_report_bundle(
        _workflow_fixture("biological_report_features.tsv"),
        design_entries,
        proteins_fasta_path=_workflow_fixture("biological_report_reference.fasta"),
        pathway_membership_tsv_path=_workflow_fixture("biological_report_pathways.tsv"),
        complex_membership_tsv_path=_workflow_fixture(
            "biological_report_complexes.tsv"
        ),
        go_annotation_tsv_path=_workflow_fixture("biological_report_go.tsv"),
        condition_a="control",
        condition_b="treatment",
    )
    output_dir = tmp_path / "biological_report"
    manifest = export_biological_result_report_bundle(report, output_dir)
    (output_dir / "biological_report_manifest.json").write_text(
        manifest.to_stable_json() + "\n",
        encoding="utf-8",
    )
    return output_dir


def _write_ptm_report_dir(tmp_path: Path) -> Path:
    ptm_evidence = parse_ptm_localization_tsv(_ptm_fixture("localization_results.tsv"))
    ptm_features = parse_ms1_feature_table(_ptm_fixture("ptm_features.tsv"))
    ptm_annotations = parse_ptm_site_annotation_tsv(
        _ptm_fixture("ptm_site_annotations.tsv")
    )
    report = build_ptm_report_bundle(
        ptm_evidence.accepted_records,
        protein_sequences=_protein_sequences(),
        feature_records=ptm_features.accepted_records,
        design_entries=_ptm_design_entries(),
        protein_correction_mode=PtmProteinCorrectionMode.SUBTRACT_UNMODIFIED_PROTEIN,
        batch_field="",
        condition_a="control",
        condition_b="treated",
        annotation_records=ptm_annotations.accepted_records,
        annotation_target_species="Homo sapiens",
        regulator_enrichment_policy=PtmRegulatorEnrichmentPolicy(
            max_adjusted_p_value=1.0,
            min_absolute_log2_fold_change=0.0,
        ),
        evidence_card_policy=PtmEvidenceCardPolicy(max_adjusted_p_value=1.0),
    )
    output_dir = tmp_path / "ptm_report"
    manifest = export_ptm_report_bundle(report, output_dir)
    (output_dir / "ptm_report_manifest.json").write_text(
        manifest.to_stable_json() + "\n",
        encoding="utf-8",
    )
    return output_dir


def _write_result_manifest_json(
    *,
    archive_dir: Path,
    biological_report_dir: Path | None,
    ptm_report_dir: Path | None,
    run_qc_paths: tuple[Path, ...] = (),
    lab_action_packet_paths: tuple[Path, ...] = (),
) -> Path:
    report = build_result_manifest_from_artifacts(
        biological_report_dir=biological_report_dir,
        ptm_report_dir=ptm_report_dir,
        run_qc_assessment_tsv_paths=run_qc_paths,
        lab_action_packet_tsv_paths=lab_action_packet_paths,
        input_paths=(
            _workflow_fixture("biological_report_features.tsv"),
            _workflow_fixture("biological_report.design.tsv"),
        ),
        commands=(
            "biological-report biological_report_features.tsv biological_report.design.tsv biological_report_reference.fasta",
            "ptm-site-report localization_results.tsv ptm_features.tsv ptm.design.tsv",
        ),
    )
    archive_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = archive_dir / "result_manifest.json"
    manifest_path.write_text(report.to_stable_json() + "\n", encoding="utf-8")
    return manifest_path


def test_result_archive_rehydrates_mixed_queries_without_workflow_rerun(
    tmp_path: Path,
) -> None:
    biological_report_dir = _write_biological_report_dir(tmp_path)
    ptm_report_dir = _write_ptm_report_dir(tmp_path)
    run_qc_path = tmp_path / "run_qc.tsv"
    _write_run_qc_tsv(run_qc_path)
    lab_action_packet_path = tmp_path / "archive" / "lab_action_packets.tsv"
    write_result_archive_lab_action_packets(
        out_path=lab_action_packet_path,
        run_qc_assessment_tsv_paths=(run_qc_path,),
    )
    manifest_path = _write_result_manifest_json(
        archive_dir=tmp_path / "archive",
        biological_report_dir=biological_report_dir,
        ptm_report_dir=ptm_report_dir,
        run_qc_paths=(run_qc_path,),
        lab_action_packet_paths=(lab_action_packet_path,),
    )

    result = load_result_archive(manifest_path)

    assert result.study_kind is ProteomicsStudyKind.ARCHIVED
    assert result.archive_manifest is not None
    assert result.interactive_result_bundle is not None
    assert result.archived_evidence_graph is not None
    assert any(
        entry.kind is ProteomicsStudyConclusionKind.PTM_NARRATIVE_CLAIM
        for entry in result.biological_conclusions
    )
    assert any(
        entry.kind is ProteomicsStudyConclusionKind.SUPPORTED_CLAIM
        for entry in result.biological_conclusions
    )
    assert any(
        entry.kind is ProteomicsStudyQcKind.LAB_ACTION_PACKET
        for entry in result.qc_surfaces
    )
    assert result.archived_lab_action_packets
    run_packet = result.query_archived_lab_action_packets(
        entity_id="t2.mzml",
        entity_type="run",
    )
    assert len(run_packet) == 1
    assert run_packet[0].problem == "identification_rate_low"
    assert "identification depth" in run_packet[0].recommended_action

    bundle = result.interactive_result_bundle
    protein = result.query_archived_protein(object_id=bundle.proteins[0].object_id)
    peptide = result.query_archived_peptide(peptide_id=bundle.peptides[0].peptide_id)
    ptm_site = result.query_archived_ptm_site(site_key=bundle.ptm_sites[0].site_key)
    pathway = result.query_archived_pathway(pathway_id=bundle.pathways[0].pathway_id)

    assert protein.representative_protein_ref
    assert peptide.sequence
    assert ptm_site.site_key
    assert pathway.supporting_protein_refs

    graph = result.archived_evidence_graph
    protein_node_id = next(
        node.entity_ref for node in graph.nodes if node.entity_type.value == "protein"
    )
    peptide_node_id = next(
        node.entity_ref for node in graph.nodes if node.entity_type.value == "peptide"
    )
    assert (
        query_protein_evidence_summary(
            graph, protein_id=protein_node_id
        ).support_edge_count
        > 0
    )
    assert query_peptide_support_chain(graph, peptide_id=peptide_node_id).step_count > 0
    pathway_nodes = tuple(
        node.entity_ref for node in graph.nodes if node.entity_type.value == "pathway"
    )
    if pathway_nodes:
        assert (
            query_pathway_support_proteins(
                graph, pathway_id=pathway_nodes[0]
            ).support_edge_count
            > 0
        )


def test_result_archive_rehydrates_ptm_only_archives_honestly(tmp_path: Path) -> None:
    ptm_report_dir = _write_ptm_report_dir(tmp_path)
    manifest_path = _write_result_manifest_json(
        archive_dir=tmp_path / "ptm_archive",
        biological_report_dir=None,
        ptm_report_dir=ptm_report_dir,
    )

    result = load_result_archive(manifest_path.parent)

    assert result.study_kind is ProteomicsStudyKind.PTM
    assert result.archived_evidence_graph is None
    assert result.interactive_result_bundle is not None
    assert result.query_archived_ptm_site(
        site_key=result.interactive_result_bundle.ptm_sites[0].site_key
    ).protein_ref
    with pytest.raises(
        ScientificEvidenceError,
        match="archived pathway is missing from result archive",
    ):
        result.query_archived_pathway(pathway_id="missing:pathway")
