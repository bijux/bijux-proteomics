# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

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
from bijux_proteomics.sequences import FastaParseMode, parse_fasta_document
from bijux_proteomics.workflow import (
    build_biological_result_report_bundle,
    build_result_manifest_from_artifacts,
    export_biological_result_report_bundle,
    render_result_manifest_file_tsv,
    render_result_manifest_summary_tsv,
    render_result_manifest_warning_tsv,
    write_result_archive_lab_action_packets,
)


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


def test_result_manifest_preserves_completeness_counts_and_warning_ledgers(
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
        pathway_membership_tsv_path=_workflow_fixture("biological_report_pathways.tsv"),
        complex_membership_tsv_path=_workflow_fixture("biological_report_complexes.tsv"),
        go_annotation_tsv_path=_workflow_fixture("biological_report_go.tsv"),
        condition_a="control",
        condition_b="treatment",
    )
    biological_dir = tmp_path / "biological_report"
    biological_manifest = export_biological_result_report_bundle(
        biological_report,
        biological_dir,
    )
    (biological_dir / "biological_report_manifest.json").write_text(
        biological_manifest.to_stable_json() + "\n",
        encoding="utf-8",
    )

    ptm_evidence = parse_ptm_localization_tsv(_ptm_fixture("localization_results.tsv"))
    ptm_features = parse_ms1_feature_table(_ptm_fixture("ptm_features.tsv"))
    ptm_annotations = parse_ptm_site_annotation_tsv(_ptm_fixture("ptm_site_annotations.tsv"))
    ptm_report = build_ptm_report_bundle(
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
    ptm_dir = tmp_path / "ptm_report"
    ptm_manifest = export_ptm_report_bundle(ptm_report, ptm_dir)
    (ptm_dir / "ptm_report_manifest.json").write_text(
        ptm_manifest.to_stable_json() + "\n",
        encoding="utf-8",
    )

    qc_path = tmp_path / "run_qc.tsv"
    _write_run_qc_tsv(qc_path)
    lab_action_packet_path = tmp_path / "lab_action_packets.tsv"
    packets = write_result_archive_lab_action_packets(
        out_path=lab_action_packet_path,
        run_qc_assessment_tsv_paths=(qc_path,),
    )

    report = build_result_manifest_from_artifacts(
        biological_report_dir=biological_dir,
        ptm_report_dir=ptm_dir,
        run_qc_assessment_tsv_paths=(qc_path,),
        lab_action_packet_tsv_paths=(lab_action_packet_path,),
        input_paths=(
            _workflow_fixture("biological_report_features.tsv"),
            _workflow_fixture("biological_report.design.tsv"),
        ),
        commands=(
            "biological-report biological_report_features.tsv biological_report.design.tsv biological_report_reference.fasta",
            "ptm-site-report localization_results.tsv ptm_features.tsv ptm.design.tsv",
        ),
    )

    assert report.document_schema.document_kind == "result_manifest"
    assert report.document_schema.content_hash is not None
    assert report.summary.command_count == 2
    assert report.summary.input_count >= 6
    assert report.summary.file_count >= 20
    assert report.summary.missing_required_file_count == 0
    assert report.summary.sample_count >= 6
    assert report.summary.protein_count >= 3
    assert len(packets) == 1
    assert any(
        entry.input_kind.value == "lab_action_packet"
        and entry.path == str(lab_action_packet_path)
        for entry in report.inputs
    )
    assert any(
        entry.relative_path == "biological_supported_claims.tsv" and entry.exists
        for entry in report.files
    )
    assert any(
        entry.warning_code == "run_qc_failure" for entry in report.warnings
    )
    assert "schema_version" in render_result_manifest_summary_tsv(report)
    assert "artifact_key" in render_result_manifest_file_tsv(report)
    warning_tsv = render_result_manifest_warning_tsv(report)
    assert "warning_code" in warning_tsv
    assert "run_qc_failure" in warning_tsv
