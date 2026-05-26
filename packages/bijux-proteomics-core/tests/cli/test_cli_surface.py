# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

import csv
import json
from pathlib import Path
import shutil

from click.testing import CliRunner
import yaml

from bijux_proteomics.chemistry import (
    FragmentIonSeries,
    calculate_fragment_ions,
    calculate_peptide_mz,
)
from bijux_proteomics.interfaces.cli import cli
from bijux_proteomics.ptm import (
    PtmEvidenceCardPolicy,
    PtmProteinCorrectionMode,
    PtmRegulatorEnrichmentPolicy,
    build_ptm_report_bundle,
    export_ptm_report_bundle,
    parse_ptm_localization_tsv,
    parse_ptm_site_annotation_tsv,
)
from bijux_proteomics.io.formats import parse_experimental_design_table
from bijux_proteomics.io.spectra import SpectrumModel, SpectrumPeak, render_mgf
from bijux_proteomics.quantification import parse_ms1_feature_table
from bijux_proteomics.sequences import FastaParseMode, parse_fasta_document
from bijux_proteomics.workflow import (
    build_biological_result_report_bundle,
    export_biological_result_report_bundle,
    public_benchmark_root,
)

FIXTURE_ROOT = Path(__file__).resolve().parent.parent / "fixtures"


def _write_public_descriptor_copy(
    *,
    source_name: str,
    benchmark_root: Path,
    dataset_id: str,
    accession: str,
) -> None:
    source_path = public_benchmark_root() / source_name / "dataset.yml"
    payload = yaml.safe_load(source_path.read_text(encoding="utf-8"))
    payload["dataset_id"] = dataset_id
    payload["accession"] = accession
    target_dir = benchmark_root / dataset_id
    target_dir.mkdir(parents=True, exist_ok=True)
    (target_dir / "dataset.yml").write_text(
        yaml.safe_dump(payload, sort_keys=False),
        encoding="utf-8",
    )


def _workflow_fixture(name: str) -> Path:
    return FIXTURE_ROOT / "workflow" / name


def _ptm_fixture(name: str) -> Path:
    return FIXTURE_ROOT / "ptm" / name


def _fasta_fixture(name: str) -> Path:
    return FIXTURE_ROOT / "fasta" / name


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


def _build_real_summary_artifacts(tmp_path: Path) -> tuple[Path, Path, Path]:
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
    ptm_annotations = parse_ptm_site_annotation_tsv(
        _ptm_fixture("ptm_site_annotations.tsv")
    )
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
    return biological_dir, ptm_dir, qc_path


def _write_run_qc_tsv_with_status(
    path: Path,
    *,
    qc_status: str,
    reason_codes: str,
    severity: str,
    message: str,
) -> None:
    path.write_text(
        "\n".join(
            (
                "scope\tentity_id\tqc_status\tstatus_reason_codes\tmetric_key\tmetric_label\tobserved_value\tunit\tseverity\tdisposition\tenforced_violation\tmessage",
                (
                    "run\tt2.mzml\t"
                    f"{qc_status}\t{reason_codes}\tidentification_rate\tIdentification rate\t0.05\tfraction\t"
                    f"{severity}\tblock\ttrue\t{message}"
                ),
            )
        )
        + "\n",
        encoding="utf-8",
    )


def _rewrite_first_tsv_row(path: Path, updates: dict[str, str]) -> None:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        if reader.fieldnames is None:
            raise ValueError(f"{path.name!r} must include a header row")
        rows = list(reader)
        if not rows:
            raise ValueError(f"{path.name!r} must include at least one data row")
        rows[0].update(updates)
        fieldnames = list(reader.fieldnames)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, delimiter="\t")
        writer.writeheader()
        writer.writerows(rows)


def _similarity_spectrum(
    spectrum_id: str,
    peaks: tuple[tuple[float, float], ...],
) -> SpectrumModel:
    return SpectrumModel(
        spectrum_id=spectrum_id,
        precursor_mz=500.2,
        precursor_charge=2,
        peaks=tuple(
            SpectrumPeak(mz=mz, intensity=intensity) for mz, intensity in peaks
        ),
    )


def test_program_template_writes_manifest() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(
            cli,
            [
                "program-template",
                "--program-id",
                "prog-1",
                "--name",
                "demo",
                "--objective",
                "screen candidates",
                "--target-id",
                "tgt-1",
                "--target-name",
                "Target",
                "--sequence",
                "ACDEFGHIKLMNPQRSTVWY",
                "--organism",
                "human",
                "--mechanism",
                "stabilize binding state",
                "--out",
                "program.json",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["program_id"] == "prog-1"
        manifest = json.loads(Path("program.json").read_text())
        assert manifest["document_schema"]["schema_version"] == "1.0.0"


def test_public_benchmark_runner_command_emits_suite_summary_failures_and_signal_checks() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(
            cli,
            [
                "public-benchmark-runner",
                "benchmarks/public",
                "--run-output-root",
                "public_benchmark_runs",
                "--summary-tsv-out",
                "public_benchmark.summary.tsv",
                "--failures-tsv-out",
                "public_benchmark.failures.tsv",
                "--signal-assessments-tsv-out",
                "public_benchmark.signals.tsv",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["passed_count"] == 8
        assert payload["failed_count"] == 3
        summary_tsv = Path("public_benchmark.summary.tsv").read_text()
        failures_tsv = Path("public_benchmark.failures.tsv").read_text()
        signal_tsv = Path("public_benchmark.signals.tsv").read_text()
        assert "lfq_cohort_review_package" in summary_tsv
        assert "lfq_sparse_contrast_benchmark_dataset" in summary_tsv
        assert "dia_diann_benchmark_dataset" in summary_tsv
        assert "fragpipe_msfragger_benchmark_dataset" in summary_tsv
        assert "maxquant_lfq_benchmark_dataset" in summary_tsv
        assert "multiplex_tmtpro_review_package" in summary_tsv
        assert "ptm_localization_review_package" in summary_tsv
        assert "targeted_transition_review_package" in summary_tsv
        assert "dia_diann_review_snapshot" in summary_tsv
        assert "missing_required_schema" in failures_tsv or "execution_failed" in failures_tsv
        assert "ptm_site_p11111_s5_up" in signal_tsv
        assert "dia_sig_a_up" in signal_tsv
        assert "maxquant_sig_a_up" in signal_tsv
        assert "fragpipe_sig_a_up" in signal_tsv


def test_build_trust_bundle_command_emits_regenerable_bundle_outputs() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(
            cli,
            [
                "build-trust-bundle",
                "--benchmarks",
                "benchmarks/public",
                "--out",
                "trust_bundle",
                "--summary-tsv-out",
                "trust_bundle.summary.tsv",
                "--manifest-json-out",
                "trust_bundle.manifest.json",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["suite_report"]["passed_count"] == 8
        assert payload["suite_report"]["failed_count"] == 3
        assert Path("trust_bundle/index.html").exists()
        assert Path("trust_bundle/trust_bundle_manifest.json").exists()
        assert Path("trust_bundle/evidence_graphs/index.tsv").exists()
        assert "lfq_cohort_review_package" in Path("trust_bundle.summary.tsv").read_text()
        assert "lfq_sparse_contrast_benchmark_dataset" in Path(
            "trust_bundle.summary.tsv"
        ).read_text()
        assert "multiplex_tmtpro_review_package" in Path(
            "trust_bundle.summary.tsv"
        ).read_text()
        assert "targeted_transition_review_package" in Path(
            "trust_bundle.summary.tsv"
        ).read_text()
        assert "flagship_weak_evidence_benchmark" in Path(
            "trust_bundle.summary.tsv"
        ).read_text()
        assert "cards/index.tsv" in Path("trust_bundle/index.html").read_text()
        assert "evidence_graphs/index.tsv" in Path("trust_bundle/index.html").read_text()


def test_demo_command_runs_from_shipped_inputs_only() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(
            cli,
            [
                "demo",
                "--out-dir",
                "proteomics_demo",
                "--summary-tsv-out",
                "proteomics_demo.summary.tsv",
                "--findings-tsv-out",
                "proteomics_demo.findings.tsv",
                "--claims-tsv-out",
                "proteomics_demo.claims.tsv",
                "--contradictions-tsv-out",
                "proteomics_demo.contradictions.tsv",
                "--belief-audit-tsv-out",
                "proteomics_demo.belief_audit.tsv",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["summary"]["within_local_ten_minute_budget"] is True
        assert payload["summary"]["strong_protein_count"] >= 1
        assert payload["summary"]["downgraded_protein_count"] >= 1
        assert payload["summary"]["supported_claim_count"] >= 1
        assert payload["summary"]["belief_audit_count"] >= 1
        assert Path("proteomics_demo/surprising_demo_report.json").exists()
        assert Path("proteomics_demo/biological_review/biological_report_manifest.json").exists()
        assert Path("proteomics_demo/biological_review/biological_evidence_graph_nodes.tsv").exists()
        assert Path("proteomics_demo/biological_review/biological_protein_cards.tsv").exists()
        assert Path("proteomics_demo/ptm_review/ptm_evidence_cards.tsv").exists()
        assert Path(
            "proteomics_demo/biological_review/biological_pathway_activity_condition_comparisons.tsv"
        ).exists()
        assert Path("proteomics_demo/biological_review/biological_protein_mechanism_cards.tsv").exists()
        assert Path("proteomics_demo/demo_qc_packets.tsv").exists()
        assert Path("proteomics_demo/demo_matrices.tsv").exists()
        assert Path("proteomics_demo/demo_assay_panel.tsv").exists()
        assert Path("proteomics_demo/demo_claims.tsv").exists()
        assert Path("proteomics_demo/demo_claim_contradictions.tsv").exists()
        assert Path("proteomics_demo/demo_belief_audit.tsv").exists()
        assert "strong_protein_count" in Path("proteomics_demo.summary.tsv").read_text()
        assert "weak_or_downgraded_protein" in Path("proteomics_demo.findings.tsv").read_text()
        assert "claim_id" in Path("proteomics_demo.claims.tsv").read_text()
        assert "claim_id" in Path("proteomics_demo.belief_audit.tsv").read_text()


def test_demo_query_command_answers_shipped_interrogation_examples() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(
            cli,
            [
                "demo-query",
                "--out-dir",
                "proteomics_demo_query",
                "--summary-tsv-out",
                "proteomics_demo_query.summary.tsv",
                "--answers-tsv-out",
                "proteomics_demo_query.answers.tsv",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["summary"]["query_count"] == 4
        assert payload["summary"]["answered_query_count"] == 4
        assert Path("proteomics_demo_query/surprising_demo_report.json").exists()
        assert "answered_query_count" in Path(
            "proteomics_demo_query.summary.tsv"
        ).read_text()
        answer_tsv = Path("proteomics_demo_query.answers.tsv").read_text()
        assert "evidence_ids" in answer_tsv
        assert "source_row_refs" in answer_tsv
        assert "confidence_reasons" in answer_tsv
        assert "why_protein_changed" in answer_tsv
        assert "what_validates_target" in answer_tsv


def test_demo_report_command_emits_integrated_scientific_report_outputs() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(
            cli,
            [
                "demo-report",
                "--out-dir",
                "proteomics_demo_report",
                "--summary-tsv-out",
                "proteomics_demo_report.summary.tsv",
                "--sentences-tsv-out",
                "proteomics_demo_report.sentences.tsv",
                "--html-out",
                "proteomics_demo_report.html",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["summary"]["section_count"] == 9
        assert payload["summary"]["scientific_claim_count"] >= 1
        assert (
            payload["summary"]["scientific_claim_count"]
            == payload["summary"]["linked_scientific_claim_count"]
        )
        assert Path("proteomics_demo_report/integrated_scientific_report.json").exists()
        assert Path("proteomics_demo_report/integrated_scientific_report.html").exists()
        assert "linked_scientific_claim_count" in Path(
            "proteomics_demo_report.summary.tsv"
        ).read_text()
        sentence_tsv = Path("proteomics_demo_report.sentences.tsv").read_text()
        assert "scientific_claim" in sentence_tsv
        assert "targeted-evidence-card:protein:P001" in sentence_tsv
        html = Path("proteomics_demo_report.html").read_text()
        assert "Experiment Design" in html
        assert "Belief Audit" in html


def test_public_dataset_comparison_command_emits_dataset_and_combined_outputs() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        benchmark_root = Path("benchmarks")
        _write_public_descriptor_copy(
            source_name="lfq_cohort_review_package",
            benchmark_root=benchmark_root,
            dataset_id="lfq_question_a",
            accession="flagship_public_package:lfq_question_a",
        )
        _write_public_descriptor_copy(
            source_name="lfq_cohort_review_package",
            benchmark_root=benchmark_root,
            dataset_id="lfq_question_b",
            accession="flagship_public_package:lfq_question_b",
        )
        _write_public_descriptor_copy(
            source_name="dda_maxquant_review_snapshot",
            benchmark_root=benchmark_root,
            dataset_id="maxquant_missing_bundle",
            accession="flagship_public_package:maxquant_missing_bundle",
        )

        result = runner.invoke(
            cli,
            [
                "public-dataset-comparison",
                "--benchmarks",
                str(benchmark_root),
                "--run-output-root",
                "public_dataset_runs",
                "--dataset-summary-tsv-out",
                "public_dataset.dataset_summary.tsv",
                "--failure-tsv-out",
                "public_dataset.failures.tsv",
                "--combined-summary-tsv-out",
                "public_dataset.combined_summary.tsv",
                "--effect-comparison-tsv-out",
                "public_dataset.effect.tsv",
                "--meta-analysis-tsv-out",
                "public_dataset.meta.tsv",
                "--pathway-comparison-tsv-out",
                "public_dataset.pathway.tsv",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["summary"]["passed_dataset_count"] == 2
        assert payload["summary"]["failed_dataset_count"] == 1
        assert payload["summary"]["meta_analysis_entry_count"] > 0
        assert "lfq_question_a" in Path("public_dataset.dataset_summary.tsv").read_text()
        assert "missing_required_schema" in Path("public_dataset.failures.tsv").read_text()
        assert "meta_analysis_entry_count" in Path(
            "public_dataset.combined_summary.tsv"
        ).read_text()
        assert "comparison_status" in Path("public_dataset.effect.tsv").read_text()
        assert "combined_log2_fold_change" in Path("public_dataset.meta.tsv").read_text()
        assert "comparison_status" in Path("public_dataset.pathway.tsv").read_text()


def test_public_dataset_evidence_cards_command_emits_card_and_dataset_outputs() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        benchmark_root = Path("benchmarks")
        _write_public_descriptor_copy(
            source_name="lfq_cohort_review_package",
            benchmark_root=benchmark_root,
            dataset_id="lfq_question_a",
            accession="flagship_public_package:lfq_question_a",
        )
        _write_public_descriptor_copy(
            source_name="lfq_cohort_review_package",
            benchmark_root=benchmark_root,
            dataset_id="lfq_question_b",
            accession="flagship_public_package:lfq_question_b",
        )
        _write_public_descriptor_copy(
            source_name="dda_maxquant_review_snapshot",
            benchmark_root=benchmark_root,
            dataset_id="maxquant_missing_bundle",
            accession="flagship_public_package:maxquant_missing_bundle",
        )

        result = runner.invoke(
            cli,
            [
                "public-dataset-evidence-cards",
                "--benchmarks",
                str(benchmark_root),
                "--run-output-root",
                "public_dataset_evidence_runs",
                "--summary-tsv-out",
                "public_dataset_evidence.summary.tsv",
                "--cards-tsv-out",
                "public_dataset_evidence.cards.tsv",
                "--dataset-evidence-tsv-out",
                "public_dataset_evidence.dataset.tsv",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["summary"]["card_count"] > 0
        assert payload["summary"]["failed_dataset_reference_count"] > 0
        assert "card_count" in Path("public_dataset_evidence.summary.tsv").read_text()
        assert "consistent_replication" in Path(
            "public_dataset_evidence.cards.tsv"
        ).read_text()
        assert "dataset_failed" in Path("public_dataset_evidence.dataset.tsv").read_text()


def test_interactive_result_bundle_command_emits_frontend_ready_json_and_summary() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
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
            condition_a="control",
            condition_b="treatment",
        )
        biological_dir = Path("biological_report")
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
        ptm_annotations = parse_ptm_site_annotation_tsv(
            _ptm_fixture("ptm_site_annotations.tsv")
        )
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
        ptm_dir = Path("ptm_report")
        ptm_manifest = export_ptm_report_bundle(ptm_report, ptm_dir)
        (ptm_dir / "ptm_report_manifest.json").write_text(
            ptm_manifest.to_stable_json() + "\n",
            encoding="utf-8",
        )

        _write_run_qc_tsv(Path("run_qc.tsv"))

        result = runner.invoke(
            cli,
            [
                "interactive-result-bundle",
                "--biological-report-dir",
                "biological_report",
                "--ptm-report-dir",
                "ptm_report",
                "--run-qc-assessment-tsv",
                "run_qc.tsv",
                "--summary-tsv-out",
                "interactive_result_bundle.summary.tsv",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        summary = payload["bundle"]["summary"]
        assert summary["sample_count"] >= 6
        assert summary["protein_count"] >= 3
        assert summary["ptm_site_count"] >= 3
        assert summary["graph_node_count"] >= 1
        assert summary["plot_count"] >= 5
        assert any(
            peptide["source_surface"] == "ptm_peptides" and peptide["site_keys"]
            for peptide in payload["bundle"]["peptides"]
        )
        assert "sample_count" in Path(
            "interactive_result_bundle.summary.tsv"
        ).read_text()


def test_result_manifest_command_emits_completeness_and_warning_ledgers() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        biological_dir, ptm_dir, qc_path = _build_real_summary_artifacts(Path.cwd())

        result = runner.invoke(
            cli,
            [
                "result-manifest",
                "--biological-report-dir",
                str(biological_dir),
                "--ptm-report-dir",
                str(ptm_dir),
                "--run-qc-assessment-tsv",
                str(qc_path),
                "--input",
                str(_workflow_fixture("biological_report_features.tsv")),
                "--input",
                str(_workflow_fixture("biological_report.design.tsv")),
                "--command",
                "biological-report biological_report_features.tsv biological_report.design.tsv biological_report_reference.fasta",
                "--command",
                "ptm-site-report localization_results.tsv ptm_features.tsv ptm.design.tsv",
                "--summary-tsv-out",
                "result_manifest.summary.tsv",
                "--file-tsv-out",
                "result_manifest.files.tsv",
                "--warning-tsv-out",
                "result_manifest.warnings.tsv",
                "--manifest-json-out",
                "result_manifest.json",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        summary = payload["report"]["summary"]
        assert summary["command_count"] == 2
        assert summary["missing_required_file_count"] == 0
        assert summary["sample_count"] >= 6
        assert any(
            warning["warning_code"] == "run_qc_failure"
            for warning in payload["report"]["warnings"]
        )
        manifest = json.loads(Path("result_manifest.json").read_text(encoding="utf-8"))
        assert manifest["document_schema"]["document_kind"] == "result_manifest"
        assert "schema_version" in Path("result_manifest.summary.tsv").read_text(
            encoding="utf-8"
        )
        assert "artifact_key" in Path("result_manifest.files.tsv").read_text(
            encoding="utf-8"
        )
        assert "run_qc_failure" in Path("result_manifest.warnings.tsv").read_text(
            encoding="utf-8"
        )


def test_result_search_command_emits_object_ids_and_evidence_snippets() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
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
        biological_dir = Path("biological_report")
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
        ptm_annotations = parse_ptm_site_annotation_tsv(
            _ptm_fixture("ptm_site_annotations.tsv")
        )
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
        ptm_dir = Path("ptm_report")
        ptm_manifest = export_ptm_report_bundle(ptm_report, ptm_dir)
        (ptm_dir / "ptm_report_manifest.json").write_text(
            ptm_manifest.to_stable_json() + "\n",
            encoding="utf-8",
        )

        result = runner.invoke(
            cli,
            [
                "result-search",
                "--biological-report-dir",
                "biological_report",
                "--ptm-report-dir",
                "ptm_report",
                "--query",
                "P11111:S5:Phospho",
                "--summary-tsv-out",
                "result_search.summary.tsv",
                "--hit-tsv-out",
                "result_search.hits.tsv",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["index"]["summary"]["ptm_site_document_count"] >= 3
        assert payload["report"]["summary"]["hit_count"] >= 1
        assert payload["report"]["hits"][0]["object_id"] == "P11111:S5:Phospho"
        assert "indexed_document_count" in Path("result_search.summary.tsv").read_text()
        hit_tsv = Path("result_search.hits.tsv").read_text()
        assert "evidence_snippets" in hit_tsv
        assert "site_key" in hit_tsv


def test_interactive_result_comparison_command_emits_changed_object_payloads() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
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
        ptm_evidence = parse_ptm_localization_tsv(_ptm_fixture("localization_results.tsv"))
        ptm_features = parse_ms1_feature_table(_ptm_fixture("ptm_features.tsv"))
        ptm_annotations = parse_ptm_site_annotation_tsv(
            _ptm_fixture("ptm_site_annotations.tsv")
        )
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

        left_biological_dir = Path("left_biological_report")
        right_biological_dir = Path("right_biological_report")
        left_ptm_dir = Path("left_ptm_report")
        right_ptm_dir = Path("right_ptm_report")

        left_biological_manifest = export_biological_result_report_bundle(
            biological_report,
            left_biological_dir,
        )
        (left_biological_dir / "biological_report_manifest.json").write_text(
            left_biological_manifest.to_stable_json() + "\n",
            encoding="utf-8",
        )
        right_biological_manifest = export_biological_result_report_bundle(
            biological_report,
            right_biological_dir,
        )
        (right_biological_dir / "biological_report_manifest.json").write_text(
            right_biological_manifest.to_stable_json() + "\n",
            encoding="utf-8",
        )

        left_ptm_manifest = export_ptm_report_bundle(ptm_report, left_ptm_dir)
        (left_ptm_dir / "ptm_report_manifest.json").write_text(
            left_ptm_manifest.to_stable_json() + "\n",
            encoding="utf-8",
        )
        right_ptm_manifest = export_ptm_report_bundle(ptm_report, right_ptm_dir)
        (right_ptm_dir / "ptm_report_manifest.json").write_text(
            right_ptm_manifest.to_stable_json() + "\n",
            encoding="utf-8",
        )

        _rewrite_first_tsv_row(
            right_biological_dir / "biological_protein_cards.tsv",
            {"log2_fold_change": "9.5", "evidence_tier": "exploratory"},
        )
        _rewrite_first_tsv_row(
            right_biological_dir / "biological_report_section_confidence.tsv",
            {
                "confidence_label": "invalid",
                "rationale": "comparison side was downgraded by QC review",
            },
        )
        _rewrite_first_tsv_row(
            right_biological_dir / "biological_pathway_entries.tsv",
            {"enrichment_ratio": "0.95", "adjusted_p_value": "0.8"},
        )
        _rewrite_first_tsv_row(
            right_ptm_dir / "ptm_evidence_cards.tsv",
            {
                "protein_correction_status": "uncorrected",
                "mechanism_class": "rewired_signaling",
            },
        )

        _write_run_qc_tsv_with_status(
            Path("left_run_qc.tsv"),
            qc_status="fail",
            reason_codes="identification_rate_low",
            severity="failed",
            message="left run failed QC",
        )
        _write_run_qc_tsv_with_status(
            Path("right_run_qc.tsv"),
            qc_status="pass",
            reason_codes="",
            severity="passed",
            message="right run passed QC",
        )

        result = runner.invoke(
            cli,
            [
                "interactive-result-comparison",
                "--left-biological-report-dir",
                "left_biological_report",
                "--left-ptm-report-dir",
                "left_ptm_report",
                "--left-run-qc-assessment-tsv",
                "left_run_qc.tsv",
                "--right-biological-report-dir",
                "right_biological_report",
                "--right-ptm-report-dir",
                "right_ptm_report",
                "--right-run-qc-assessment-tsv",
                "right_run_qc.tsv",
                "--summary-tsv-out",
                "interactive_result_comparison.summary.tsv",
                "--protein-tsv-out",
                "interactive_result_comparison.proteins.tsv",
                "--ptm-site-tsv-out",
                "interactive_result_comparison.ptm_sites.tsv",
                "--qc-tsv-out",
                "interactive_result_comparison.qc.tsv",
                "--pathway-tsv-out",
                "interactive_result_comparison.pathways.tsv",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        summary = payload["payload"]["summary"]
        assert summary["changed_protein_count"] >= 1
        assert summary["changed_ptm_site_count"] >= 1
        assert summary["changed_qc_entry_count"] >= 2
        assert summary["changed_pathway_count"] >= 1
        assert any(
            reason["code"] == "evidence_tier_changed"
            for entry in payload["payload"]["changed_proteins"]
            for reason in entry["reasons"]
        )
        assert any(
            reason["code"] == "protein_correction_status_changed"
            for entry in payload["payload"]["changed_ptm_sites"]
            for reason in entry["reasons"]
        )
        assert any(
            reason["code"] == "qc_status_changed"
            for entry in payload["payload"]["changed_qc_entries"]
            for reason in entry["reasons"]
        )
        assert any(
            reason["code"] == "enrichment_ratio_changed"
            for entry in payload["payload"]["changed_pathways"]
            for reason in entry["reasons"]
        )
        assert "changed_protein_count" in Path(
            "interactive_result_comparison.summary.tsv"
        ).read_text()
        assert "representative_protein_ref" in Path(
            "interactive_result_comparison.proteins.tsv"
        ).read_text()
        assert "protein_correction_status" in Path(
            "interactive_result_comparison.ptm_sites.tsv"
        ).read_text()
        assert "qc_id" in Path("interactive_result_comparison.qc.tsv").read_text()
        assert "pathway_id" in Path(
            "interactive_result_comparison.pathways.tsv"
        ).read_text()


def test_result_question_answer_command_emits_row_and_graph_citations() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
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
        export_biological_result_report_bundle(
            biological_report,
            Path("biological_report"),
        )
        Path("run_qc.tsv").write_text(
            "\n".join(
                (
                    "scope\tentity_id\tqc_status\tstatus_reason_codes\tmetric_key\tmetric_label\tobserved_value\tunit\tseverity\tdisposition\tenforced_violation\tmessage",
                    "run\tt2.mzml\tfail\tidentification_rate_low\tidentification_rate\tIdentification rate\t0.05\tfraction\tfailed\tblock\ttrue\tidentification rate fell below enforced threshold",
                )
            )
            + "\n",
            encoding="utf-8",
        )

        result = runner.invoke(
            cli,
            [
                "result-question-answer",
                "--biological-report-dir",
                "biological_report",
                "--run-qc-assessment-tsv",
                "run_qc.tsv",
                "--query-kind",
                "sample_qc_failure",
                "--subject-id",
                "T2",
                "--summary-tsv-out",
                "result_query.summary.tsv",
                "--answer-tsv-out",
                "result_query.answers.tsv",
                "--evidence-tsv-out",
                "result_query.evidence.tsv",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        answer = payload["report"]["answers"][0]
        assert answer["status"] == "answered"
        assert "t2.mzml" in answer["result_row_ids"]
        assert any(node_id.startswith("sample:") for node_id in answer["graph_node_ids"])
        assert "answered_query_count" in Path("result_query.summary.tsv").read_text()
        assert "answer_text" in Path("result_query.answers.tsv").read_text()
        assert "graph_node_ids" in Path("result_query.evidence.tsv").read_text()


def test_result_explanation_command_emits_structured_decision_outputs() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        biological_dir = Path("biological_report")
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
                    "pathway:PWY-001\tpathway\tPWY-001\tprotein:P11111",
                    "protein:P11111\tprotein\tP11111\t",
                )
            )
            + "\n",
            encoding="utf-8",
        )
        (biological_dir / "biological_pathway_activity_condition_comparisons.tsv").write_text(
            "\n".join(
                (
                    "pathway_id\tpathway_name\tsource_name\tsource_accession\tcondition_a\tcondition_b\tcondition_a_confidence_status\tcondition_b_confidence_status\tcomparison_confidence_status\tmean_activity_score_a\tmean_activity_score_b\tactivity_score_delta",
                    "PWY-001\tCell Cycle\tReactome\tR-HSA-1640170\tcontrol\ttreated\thigh_confidence\thigh_confidence\tlow_confidence\t0.1\t0.5\t0.4",
                )
            )
            + "\n",
            encoding="utf-8",
        )
        (biological_dir / "biological_pathway_activity_members.tsv").write_text(
            "\n".join(
                (
                    "pathway_id\tpathway_name\tsource_name\tsource_accession\tsample_id\tcondition\tbatch\tmember_kind\tmember_id\tresolved_protein_refs\tobserved_protein_refs\tresolved_protein_count\tobserved_protein_count\tmissing_protein_count\tmember_activity_score\tobserved",
                    "PWY-001\tCell Cycle\tReactome\tR-HSA-1640170\tT1\ttreated\t\tprotein\tCDK1\tP11111\tP11111\t1\t1\t0\t1.2\ttrue",
                )
            )
            + "\n",
            encoding="utf-8",
        )
        (biological_dir / "biological_pathway_activity_unresolved.tsv").write_text(
            "\n".join(
                (
                    "pathway_id\tpathway_name\tsource_name\tsource_accession\tmember_kind\tmember_id\treason",
                    "PWY-001\tCell Cycle\tReactome\tR-HSA-1640170\tprotein\tMCM2\tprotein was not observed in the study matrix",
                )
            )
            + "\n",
            encoding="utf-8",
        )

        result = runner.invoke(
            cli,
            [
                "result-explanation",
                "--biological-report-dir",
                "biological_report",
                "--explanation-kind",
                "pathway_result",
                "--subject-id",
                "PWY-001",
                "--summary-tsv-out",
                "result_explanation.summary.tsv",
                "--explanation-tsv-out",
                "result_explanation.explanations.tsv",
                "--evidence-tsv-out",
                "result_explanation.evidence.tsv",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        explanation = payload["report"]["explanations"][0]
        assert explanation["status"] == "answered"
        assert explanation["confidence"] == "low"
        assert explanation["claim"].startswith("Pathway Cell Cycle shows higher activity")
        assert explanation["opposing_evidence"]
        assert "answered_explanation_count" in Path(
            "result_explanation.summary.tsv"
        ).read_text()
        assert "claim" in Path("result_explanation.explanations.tsv").read_text()
        evidence_tsv = Path("result_explanation.evidence.tsv").read_text()
        assert "evidence_role" in evidence_tsv
        assert "opposing" in evidence_tsv


def test_belief_audit_command_emits_challengeable_conclusion_outputs() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        biological_dir = Path("biological_report")
        ptm_dir = Path("ptm_report")
        biological_dir.mkdir()
        ptm_dir.mkdir()
        (biological_dir / "biological_protein_cards.tsv").write_text(
            "\n".join(
                (
                    "card_id\tgraph_claim_node_id\tgraph_subject_node_id\tgraph_support_node_ids\tgraph_source_row_refs\tprotein_group_id\trepresentative_protein_ref\tprotein_refs\tgene_symbol\tpeptides\tpeptide_count\tunique_peptide_count\tshared_peptide_count\tobserved_sample_count\tmissing_sample_count\tcondition_a\tcondition_b\tlog2_fold_change\tadjusted_p_value\tsignificant\tevidence_tier\twarning_codes",
                    "protein-card-p11111\tclaim:P11111\tprotein:P11111\tpeptide:PEPA;peptide:PEPB\tdifferential:P11111;feature:P11111\tpg-P11111\tP11111\tP11111\tAKT1\tPEPA;PEPB\t2\t2\t0\t4\t0\tcontrol\ttreated\t1.8\t0.01\ttrue\thigh_support\tlow_sequence_coverage",
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
                    "claim:P11111\tclaim\tprotein-card-p11111\tprotein:P11111",
                    "pathway:PWY-001\tpathway\tPWY-001\tprotein:P11111",
                    "sample:T2\tsample\tT2\trun:t2.mzml",
                    "run:t2.mzml\trun\tt2.mzml\tsample:T2",
                )
            )
            + "\n",
            encoding="utf-8",
        )
        (biological_dir / "biological_pathway_activity_condition_comparisons.tsv").write_text(
            "\n".join(
                (
                    "pathway_id\tpathway_name\tsource_name\tsource_accession\tcondition_a\tcondition_b\tcondition_a_confidence_status\tcondition_b_confidence_status\tcomparison_confidence_status\tmean_activity_score_a\tmean_activity_score_b\tactivity_score_delta",
                    "PWY-001\tCell Cycle\tReactome\tR-HSA-1640170\tcontrol\ttreated\thigh_confidence\thigh_confidence\thigh_confidence\t0.2\t1.4\t1.2",
                )
            )
            + "\n",
            encoding="utf-8",
        )
        (biological_dir / "biological_pathway_activity_members.tsv").write_text(
            "\n".join(
                (
                    "pathway_id\tpathway_name\tsource_name\tsource_accession\tsample_id\tcondition\tbatch\tmember_kind\tmember_id\tresolved_protein_refs\tobserved_protein_refs\tresolved_protein_count\tobserved_protein_count\tmissing_protein_count\tmember_activity_score\tobserved",
                    "PWY-001\tCell Cycle\tReactome\tR-HSA-1640170\tT1\ttreated\t\tprotein\tCDK1\tP11111\tP11111\t1\t1\t0\t1.1\ttrue",
                )
            )
            + "\n",
            encoding="utf-8",
        )
        (biological_dir / "biological_pathway_activity_unresolved.tsv").write_text(
            "\n".join(
                (
                    "pathway_id\tpathway_name\tsource_name\tsource_accession\tmember_kind\tmember_id\treason",
                    "PWY-001\tCell Cycle\tReactome\tR-HSA-1640170\tprotein\tMCM2\tprotein was not observed in the study matrix",
                )
            )
            + "\n",
            encoding="utf-8",
        )
        (biological_dir / "biological_regulator_inference.tsv").write_text(
            "\n".join(
                (
                    "regulator\tevidence_type\tsignal_surface\tsource_name\tsource_accession\ttarget_count\tmatched_target_count\tcoverage_fraction\tsupporting_protein_refs\tsupporting_site_keys\tsupporting_pathway_ids\tdirection\tscore\tmean_log2_fold_change\tmean_activity_score_delta\tnote",
                    "CDK1\tpathway_targets\tprotein_change\tReactome\tR-HSA-1640170\t4\t2\t0.5\tP11111\tP11111:S5:Phospho\tPWY-001\tactivated\t1.3\t1.2\t0.8\tregulator inference remains partial because not all pathway targets were observed",
                )
            )
            + "\n",
            encoding="utf-8",
        )
        (biological_dir / "biological_regulator_inference_unresolved.tsv").write_text(
            "\n".join(
                (
                    "regulator\tevidence_type\ttarget_field\ttarget_value\tsource_name\tsource_accession\treason",
                    "CDK1\tpathway_targets\tprotein_ref\tMCM2\tReactome\tR-HSA-1640170\tprotein was not observed in the study matrix",
                )
            )
            + "\n",
            encoding="utf-8",
        )
        (ptm_dir / "ptm_evidence_cards.tsv").write_text(
            "\n".join(
                (
                    "card_id\tsite_key\tprotein_ref\tcondition_a\tcondition_b\tadjusted_p_value\tlog2_fold_change\tcorrected_log2_fold_change\tlocalization_tier\tobserved_sample_count\tprotein_correction_status\tmechanism_reason_codes\twarning_codes\tclaim_ids",
                    "ptm-card-p11111\tP11111:S5:Phospho\tP11111\tcontrol\ttreated\t0.03\t1.5\t0.7\thigh_confidence\t4\tsubtracted_unmodified_protein\tcontext_supported\tshared_peptide_liability\tptm-claim:P11111-S5",
                )
            )
            + "\n",
            encoding="utf-8",
        )
        Path("run_qc.tsv").write_text(
            "\n".join(
                (
                    "scope\tentity_id\tqc_status\tstatus_reason_codes\tmetric_key\tmetric_label\tobserved_value\tunit\tseverity\tdisposition\tenforced_violation\tmessage",
                    "run\tt2.mzml\tfail\tidentification_rate_low\tidentification_rate\tIdentification rate\t0.05\tfraction\tfailed\tblock\ttrue\tidentification rate fell below enforced threshold",
                )
            )
            + "\n",
            encoding="utf-8",
        )
        Path("validation_evidence_cards.tsv").write_text(
            "\n".join(
                (
                    "candidate_id\tcandidate_kind\tdisplay_label\ttarget_protein_ref\tsite_key\tdiscovery_priority_rank\tdiscovery_final_score\tdiscovery_weighted_evidence_total\tdiscovery_penalty_total\tdiscovery_uncertainty\tdiscovery_effect_size\tdiscovery_adjusted_p_value\tdiscovery_support_count\tbiological_role_labels\tbiological_source_ids\tdiscovery_rank_reason_codes\tassay_entry_count\tomitted_reason\ttargeted_validation_verdict\ttargeted_validation_log2_effect\tconfirmed_assay_count\tcontradicted_assay_count\tinconclusive_assay_count\ttargeted_validation_reason_codes\tstability_score\tstability_downgraded\tstability_reason_codes\tredundancy_cluster_id\trepresentative_candidate_id\tredundancy_representative\tredundancy_dropped\tredundancy_reason_codes\tfinal_status\twarning_codes\tnote",
                    "candidate-1\tprotein\tAKT1 candidate\tP11111\t\t1\t0.91\t1.3\t0.1\t0.05\t1.8\t0.01\t3\tkinase_panel\tsupported_claim_1\tstrong_rank\t2\t\tconfirmed\t1.1\t2\t0\t0\torthogonal_support\t0.9\tfalse\t\tcluster-1\tcandidate-1\ttrue\tfalse\t\tconfirmed\tshared_peptide_liability\tconfirmed by targeted assays with one retained warning",
                )
            )
            + "\n",
            encoding="utf-8",
        )
        Path("validation_evidence_card_warnings.tsv").write_text(
            "\n".join(
                (
                    "candidate_id\twarning_code\tnote",
                    "candidate-1\tshared_peptide_liability\tshared peptide evidence can still confound the candidate if orthogonal support drops",
                )
            )
            + "\n",
            encoding="utf-8",
        )

        result = runner.invoke(
            cli,
            [
                "belief-audit",
                "--biological-report-dir",
                "biological_report",
                "--ptm-report-dir",
                "ptm_report",
                "--validation-evidence-card-tsv",
                "validation_evidence_cards.tsv",
                "--validation-evidence-warning-tsv",
                "validation_evidence_card_warnings.tsv",
                "--run-qc-assessment-tsv",
                "run_qc.tsv",
                "--summary-tsv-out",
                "belief_audit.summary.tsv",
                "--belief-audit-tsv-out",
                "belief_audit.tsv",
                "--html-out",
                "belief_audit.html",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        summary = payload["report"]["summary"]
        assert summary["entry_count"] == 6
        assert summary["regulator_entry_count"] == 1
        assert summary["biomarker_entry_count"] == 1
        assert "<h1>Belief Audit</h1>" in Path("belief_audit.html").read_text(
            encoding="utf-8"
        )
        assert "what_would_falsify" in Path("belief_audit.tsv").read_text(
            encoding="utf-8"
        )
        assert "protein_entry_count" in Path("belief_audit.summary.tsv").read_text(
            encoding="utf-8"
        )


def test_analysis_recommendations_command_emits_condition_tied_actions() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        ptm_dir = Path("ptm_report")
        ptm_dir.mkdir()
        (ptm_dir / "ptm_evidence_cards.tsv").write_text(
            "\n".join(
                (
                    "card_id\tsite_key\tprotein_ref\tcondition_a\tcondition_b\tadjusted_p_value\tlog2_fold_change\tcorrected_log2_fold_change\tlocalization_tier\tobserved_sample_count\tprotein_correction_status\tmechanism_reason_codes\twarning_codes\tclaim_ids",
                    "ptm-card-1\tP11111:S5:Phospho\tP11111\tcontrol\ttreated\t0.03\t1.5\t\tmedium_confidence\t4\tnot_requested\tcontext_supported\t\tptm-claim-1",
                )
            )
            + "\n",
            encoding="utf-8",
        )
        Path("run_qc.tsv").write_text(
            "\n".join(
                (
                    "scope\tentity_id\tqc_status\tstatus_reason_codes\tmetric_key\tmetric_label\tobserved_value\tunit\tseverity\tdisposition\tenforced_violation\tmessage",
                    "run\tt2.mzml\tfail\televated_contaminant_fraction;identification_rate_low\tcontaminant_psm_fraction\tContaminant PSM fraction\t0.12\tfraction\tfailed\tblock\ttrue\tcontaminant evidence burden exceeds the expected background range",
                )
            )
            + "\n",
            encoding="utf-8",
        )
        Path("batch_effect_summary.tsv").write_text(
            "\n".join(
                (
                    "batch_field\tdisposition\tglobal_median_log2_abundance\tbatch_count\tflagged_batch_count\tbatch_variance_proxy\tbatch_associated_component_count\tfully_confounded_with_condition\tbatch_correction_blocked\tbatch_warning\tnote",
                    "batch\tblocked\t10.1\t2\t2\t0.8\t2\ttrue\ttrue\tbatch is fully confounded with condition; batch correction is blocked\tbatch estimation detected full confounding between batch and condition and therefore blocks batch correction",
                )
            )
            + "\n",
            encoding="utf-8",
        )

        result = runner.invoke(
            cli,
            [
                "analysis-recommendations",
                "--ptm-report-dir",
                "ptm_report",
                "--run-qc-assessment-tsv",
                "run_qc.tsv",
                "--batch-effect-summary-tsv",
                "batch_effect_summary.tsv",
                "--summary-tsv-out",
                "analysis_recommendations.summary.tsv",
                "--recommendation-tsv-out",
                "analysis_recommendations.tsv",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["report"]["summary"]["recommendation_count"] == 4
        condition_codes = {
            entry["detected_condition_code"]
            for entry in payload["report"]["recommendations"]
        }
        assert condition_codes == {
            "ptm_protein_correction_not_requested",
            "elevated_contamination",
            "failed_run_qc",
            "batch_condition_confounding",
        }
        assert "triggered_condition_codes" in Path(
            "analysis_recommendations.summary.tsv"
        ).read_text()
        recommendation_tsv = Path("analysis_recommendations.tsv").read_text()
        assert "detected_condition_code" in recommendation_tsv
        assert "avoid_batch_correction" in recommendation_tsv


def test_compact_result_summary_command_emits_evidence_constrained_sections() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        biological_dir, ptm_dir, qc_path = _build_real_summary_artifacts(Path.cwd())

        result = runner.invoke(
            cli,
            [
                "compact-result-summary",
                "--biological-report-dir",
                str(biological_dir),
                "--ptm-report-dir",
                str(ptm_dir),
                "--run-qc-assessment-tsv",
                str(qc_path),
                "--overview-tsv-out",
                "compact_result_summary.overview.tsv",
                "--entry-tsv-out",
                "compact_result_summary.entries.tsv",
                "--markdown-out",
                "compact_result_summary.md",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        report = payload["report"]
        assert report["overview"]["section_count"] == 5
        assert report["overview"]["entry_count"] > 0
        by_kind = {
            section["section_kind"]: section
            for section in report["sections"]
        }
        strongest_entries = by_kind["strongest_findings"]["entries"]
        assert strongest_entries
        assert all(
            entry["result_surfaces"] == ["biological_supported_claims"]
            for entry in strongest_entries
        )

        markdown = Path("compact_result_summary.md").read_text(encoding="utf-8")
        assert "## Sample QC" in markdown
        assert "## Strongest findings" in markdown
        assert "## Failed assumptions" in markdown
        assert "## Next validation targets" in markdown
        assert "strongest_finding_count" in Path(
            "compact_result_summary.overview.tsv"
        ).read_text(encoding="utf-8")
        assert "summary_text" in Path(
            "compact_result_summary.entries.tsv"
        ).read_text(encoding="utf-8")


def test_failure_explanation_command_emits_scientific_category_and_fix() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(
            cli,
            [
                "failure-explanation",
                "design table contains rejected rows",
                "--workflow-name",
                "biological-report",
                "--summary-tsv-out",
                "failure_explanation.summary.tsv",
                "--explanation-tsv-out",
                "failure_explanation.tsv",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        explanation = payload["report"]["explanations"][0]
        assert explanation["status"] == "explained"
        assert explanation["failure_category"] == "invalid_design"
        assert explanation["scientific_condition_code"] == "invalid_study_design"
        assert "invalid_design_count" in Path(
            "failure_explanation.summary.tsv"
        ).read_text()
        explanation_tsv = Path("failure_explanation.tsv").read_text()
        assert "scientific_condition_code" in explanation_tsv
        assert "repair rejected design rows" in explanation_tsv


def test_biological_report_command_explains_invalid_design_failure_without_traceback() -> (
    None
):
    runner = CliRunner()
    with runner.isolated_filesystem():
        workflow_dir = FIXTURE_ROOT / "workflow"
        shutil.copy(
            workflow_dir / "biological_report_features.tsv",
            "biological_report_features.tsv",
        )
        Path("bad.design.tsv").write_text(
            "\n".join(
                (
                    "sample_id\tcondition\treplicate",
                    "control_1\tcontrol\tnot_an_integer",
                )
            )
            + "\n",
            encoding="utf-8",
        )
        shutil.copy(
            workflow_dir / "biological_report_reference.fasta",
            "biological_report_reference.fasta",
        )

        result = runner.invoke(
            cli,
            [
                "biological-report",
                "biological_report_features.tsv",
                "bad.design.tsv",
                "biological_report_reference.fasta",
            ],
        )

        assert result.exit_code != 0
        assert "invalid_design" in result.output
        assert "study design is invalid or inconsistent" in result.output
        assert "fix input: repair rejected design rows" in result.output.lower()
        assert "traceback" not in result.output.lower()


def test_sample_sheet_repair_suggestions_command_emits_advisory_json_and_tsv() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        Path("design.tsv").write_text(
            "\n".join(
                (
                    "sample_id\tcondition\treplicate\tfraction\tspectra_file",
                    "control_1\tcontrol\t1\t1\tcontrol_1.raw",
                    "treated_1\ttreatment\t1\t1\tmissing_run.raw",
                )
            )
            + "\n",
            encoding="utf-8",
        )
        Path("observed_samples.txt").write_text(
            "control_1\ntreated_1\ntreated_2\n",
            encoding="utf-8",
        )
        Path("observed_runs.txt").write_text(
            "control_1.raw\ntreated_1.raw\ntreated_2.raw\n",
            encoding="utf-8",
        )

        result = runner.invoke(
            cli,
            [
                "sample-sheet-repair-suggestions",
                "design.tsv",
                "--observed-sample-id-file",
                "observed_samples.txt",
                "--observed-run-id-file",
                "observed_runs.txt",
                "--suggestions-tsv-out",
                "sample_sheet_repairs.tsv",
                "--out",
                "sample_sheet_repairs.json",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["report"]["summary"]["missing_metadata_sample_count"] == 1
        assert payload["report"]["summary"]["metadata_run_mismatch_count"] == 1
        assert (
            payload["outputs"]["suggestions_tsv"] == "sample_sheet_repairs.tsv"
        )
        assert "advisory only" in payload["report"]["note"]
        tsv_output = Path("sample_sheet_repairs.tsv").read_text(encoding="utf-8")
        json_output = json.loads(
            Path("sample_sheet_repairs.json").read_text(encoding="utf-8")
        )
        assert "confidence" in tsv_output.splitlines()[0]
        assert "missing_metadata_sample" in tsv_output
        assert "treated_2.raw" in tsv_output
        assert json_output["report"]["summary"]["suggestion_count"] == 2


def test_experiment_feasibility_command_emits_supported_and_unsupported_outputs() -> (
    None
):
    runner = CliRunner()
    with runner.isolated_filesystem():
        Path("design.tsv").write_text(
            "\n".join(
                (
                    "sample_id\tcondition\treplicate\tfraction\tspectra_file",
                    "control_1\tcontrol\t1\t1\tcontrol_1.raw",
                    "control_2\tcontrol\t2\t1\tcontrol_2.raw",
                    "treated_1\ttreatment\t1\t1\ttreated_1.raw",
                    "treated_2\ttreatment\t2\t1\ttreated_2.raw",
                    "recovery_1\trecovery\t1\t1\trecovery_1.raw",
                )
            )
            + "\n",
            encoding="utf-8",
        )

        result = runner.invoke(
            cli,
            [
                "experiment-feasibility",
                "design.tsv",
                "--valid-contrasts-tsv-out",
                "feasibility.valid.tsv",
                "--invalid-contrasts-tsv-out",
                "feasibility.invalid.tsv",
                "--group-sizes-tsv-out",
                "feasibility.groups.tsv",
                "--model-support-tsv-out",
                "feasibility.models.tsv",
                "--out",
                "feasibility.json",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["report"]["summary"]["valid_contrast_count"] == 1
        assert payload["report"]["summary"]["invalid_contrast_count"] == 2
        assert (
            payload["outputs"]["valid_contrasts_tsv"] == "feasibility.valid.tsv"
        )
        assert "control\ttreatment" in Path("feasibility.valid.tsv").read_text(
            encoding="utf-8"
        )
        assert "insufficient_group_size" in Path(
            "feasibility.invalid.tsv"
        ).read_text(encoding="utf-8")
        assert "underpowered" in Path("feasibility.groups.tsv").read_text(
            encoding="utf-8"
        )
        assert "multi_condition_differential" in Path(
            "feasibility.models.tsv"
        ).read_text(encoding="utf-8")
        assert (
            json.loads(Path("feasibility.json").read_text(encoding="utf-8"))["report"][
                "summary"
            ]["underpowered_condition_count"]
            == 1
        )


def test_protocol_consistency_report_command_emits_blocking_tmt_diagnostics() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        Path("protocol.tsv").write_text(
            "\n".join(
                (
                    "protocol_id\tdigestion_enzyme\tacquisition_type\tlabeling_method\tenrichment_type\tfractionation_mode\tdepletion_mode\tinstrument_platform",
                    "tmt-protocol\tother\tdda\ttmt\tnone\tnone\tnone\tOrbitrap Eclipse",
                )
            )
            + "\n",
            encoding="utf-8",
        )
        Path("reporters.tsv").write_text(
            "\n".join(
                (
                    "source_row_id\tmodified_peptide\tproteins\tmultiplex_group\t126\t127N",
                    "row-1\tPEPTIDE\tP11111\tplex-a\t0\t0",
                )
            )
            + "\n",
            encoding="utf-8",
        )

        result = runner.invoke(
            cli,
            [
                "protocol-consistency-report",
                "protocol.tsv",
                "--reporter-table",
                "reporters.tsv",
                "--diagnostics-tsv-out",
                "protocol_consistency.tsv",
                "--out",
                "protocol_consistency.json",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["report"]["summary"]["status"] == "blocking"
        assert payload["report"]["diagnostics"][0]["code"] == (
            "missing_reporter_channel_signal"
        )
        assert payload["outputs"]["diagnostics_tsv"] == "protocol_consistency.tsv"
        assert "missing_reporter_channel_signal" in Path(
            "protocol_consistency.tsv"
        ).read_text(encoding="utf-8")
        saved = json.loads(
            Path("protocol_consistency.json").read_text(encoding="utf-8")
        )
        assert saved["report"]["summary"]["blocking_diagnostic_count"] == 1


def test_annotate_proteins_command_emits_annotated_unmapped_and_rejected_ledgers() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        interpretation_fixture_dir = FIXTURE_ROOT / "interpretation"
        shutil.copy(
            interpretation_fixture_dir / "protein_annotation_input.tsv",
            "protein_annotation_input.tsv",
        )
        shutil.copy(
            interpretation_fixture_dir / "protein_annotation_custom.tsv",
            "protein_annotation_custom.tsv",
        )
        shutil.copy(
            interpretation_fixture_dir / "protein_annotation_reference.fasta",
            "protein_annotation_reference.fasta",
        )

        result = runner.invoke(
            cli,
            [
                "interpretation",
                "annotate-proteins",
                "protein_annotation_input.tsv",
                "protein_annotation_reference.fasta",
                "--annotation-tsv",
                "protein_annotation_custom.tsv",
                "--summary-tsv-out",
                "protein_annotation.summary.tsv",
                "--annotated-tsv-out",
                "protein_annotation.annotated.tsv",
                "--unmapped-tsv-out",
                "protein_annotation.unmapped.tsv",
                "--rejected-input-tsv-out",
                "protein_annotation.input_rejected.tsv",
                "--rejected-annotation-tsv-out",
                "protein_annotation.annotation_rejected.tsv",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["mapping_report"]["summary"]["input_entry_count"] == 6
        assert payload["mapping_report"]["summary"]["mapped_entry_count"] == 6
        assert payload["mapping_report"]["summary"]["unmapped_entry_count"] == 0
        assert Path("protein_annotation.summary.tsv").read_text().splitlines()[
            0
        ].startswith("input_entry_count\tmapped_entry_count")
        assert "TRP53" in Path("protein_annotation.annotated.tsv").read_text()
        assert "annotation_status" in Path("protein_annotation.annotated.tsv").read_text()
        assert (
            Path("protein_annotation.unmapped.tsv").read_text().splitlines()[0]
            == "row_number\tsource_row_id\tinput_protein_ref\tprotein_ref\taccession_aliases\tinput_metadata\treason"
        )
        assert (
            "protein row requires at least one protein reference"
            in Path("protein_annotation.input_rejected.tsv").read_text()
        )
        assert (
            "duplicate protein annotation for P04637"
            in Path("protein_annotation.annotation_rejected.tsv").read_text()
        )


def test_map_orthologs_command_emits_mapped_unmapped_and_rejected_ledgers() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        interpretation_fixture_dir = FIXTURE_ROOT / "interpretation"
        shutil.copy(interpretation_fixture_dir / "ortholog_input.tsv", "ortholog_input.tsv")
        shutil.copy(
            interpretation_fixture_dir / "ortholog_cli.tsv",
            "ortholog_cli.tsv",
        )

        result = runner.invoke(
            cli,
            [
                "interpretation",
                "map-orthologs",
                "ortholog_input.tsv",
                "ortholog_cli.tsv",
                "--source-species",
                "human",
                "--target-species",
                "mouse",
                "--summary-tsv-out",
                "ortholog.summary.tsv",
                "--mapped-tsv-out",
                "ortholog.mapped.tsv",
                "--unmapped-tsv-out",
                "ortholog.unmapped.tsv",
                "--rejected-input-tsv-out",
                "ortholog.input_rejected.tsv",
                "--rejected-ortholog-tsv-out",
                "ortholog.rejected.tsv",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["mapping_report"]["summary"]["input_entry_count"] == 7
        assert payload["mapping_report"]["summary"]["mapped_entry_count"] == 9
        assert payload["mapping_report"]["summary"]["unmapped_entry_count"] == 1
        assert Path("ortholog.summary.tsv").read_text().splitlines()[0].startswith(
            "source_species\ttarget_species\tinput_entry_count\tmapped_entry_count"
        )
        assert "P005\thuman\tmouse\tM005" in Path("ortholog.mapped.tsv").read_text()
        assert "P999\thuman\tmouse" in Path("ortholog.unmapped.tsv").read_text()
        assert (
            Path("ortholog.input_rejected.tsv").read_text().splitlines()[0]
            == "row_number\tvalues\treason"
        )
        assert (
            "duplicate ortholog relationship for human:P001 -> mouse:M001"
            in Path("ortholog.rejected.tsv").read_text()
        )


def test_map_context_command_emits_mapping_term_unmapped_and_rejected_ledgers() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        interpretation_fixture_dir = FIXTURE_ROOT / "interpretation"
        shutil.copy(
            interpretation_fixture_dir / "biological_context_input.tsv",
            "biological_context_input.tsv",
        )
        shutil.copy(
            interpretation_fixture_dir / "biological_context_single_kind.tsv",
            "biological_context_single_kind.tsv",
        )

        result = runner.invoke(
            cli,
            [
                "interpretation",
                "map-context",
                "biological_context_input.tsv",
                "biological_context_single_kind.tsv",
                "--fixed-context-kind",
                "subcellular_compartment",
                "--summary-tsv-out",
                "context.summary.tsv",
                "--mapped-tsv-out",
                "context.mapped.tsv",
                "--term-tsv-out",
                "context.terms.tsv",
                "--unmapped-tsv-out",
                "context.unmapped.tsv",
                "--rejected-input-tsv-out",
                "context.input_rejected.tsv",
                "--rejected-context-tsv-out",
                "context.context_rejected.tsv",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["mapping_report"]["summary"]["input_entry_count"] == 4
        assert payload["mapping_report"]["summary"]["mapped_entry_count"] == 2
        assert payload["mapping_report"]["summary"]["unmapped_entry_count"] == 2
        assert payload["context_table"]["fixed_context_kind"] == "subcellular_compartment"
        assert "subcellular_compartment" in Path("context.summary.tsv").read_text()
        assert "GO:0005634" in Path("context.mapped.tsv").read_text()
        assert "supporting_protein_refs" in Path("context.terms.tsv").read_text()
        assert "UNKNOWN123" in Path("context.unmapped.tsv").read_text()
        assert Path("context.input_rejected.tsv").read_text().splitlines() == [
            "row_number\tvalues\treason"
        ]
        assert Path("context.context_rejected.tsv").read_text().splitlines() == [
            "row_number\tvalues\treason"
        ]


def test_protein_set_score_command_emits_matrix_condition_and_unresolved_ledgers() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        interpretation_fixture_dir = FIXTURE_ROOT / "interpretation"
        quant_fixture_dir = FIXTURE_ROOT / "quant"
        shutil.copy(quant_fixture_dir / "ms1_features.tsv", "ms1_features.tsv")
        shutil.copy(quant_fixture_dir / "quant.design.tsv", "quant.design.tsv")
        shutil.copy(interpretation_fixture_dir / "protein_sets.tsv", "protein_sets.tsv")
        shutil.copy(
            interpretation_fixture_dir / "protein_sets_invalid.tsv",
            "protein_sets_invalid.tsv",
        )

        result = runner.invoke(
            cli,
            [
                "interpretation",
                "protein-set-score",
                "ms1_features.tsv",
                "protein_sets.tsv",
                "--design",
                "quant.design.tsv",
                "--aggregation",
                "top_n",
                "--top-n",
                "2",
                "--summary-tsv-out",
                "protein_set_score.summary.tsv",
                "--matrix-tsv-out",
                "protein_set_score.matrix.tsv",
                "--sample-score-tsv-out",
                "protein_set_score.samples.tsv",
                "--condition-score-tsv-out",
                "protein_set_score.conditions.tsv",
                "--condition-comparison-tsv-out",
                "protein_set_score.comparisons.tsv",
                "--unresolved-tsv-out",
                "protein_set_score.unresolved.tsv",
                "--rejected-set-tsv-out",
                "protein_set_score.rejected.tsv",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["accepted_features"] == 32
        assert payload["rejected_features"] == 0
        assert payload["report"]["summary"]["set_count"] == 3
        assert payload["report"]["summary"]["condition_comparison_count"] == 3
        assert payload["report"]["summary"]["low_confidence_sample_score_count"] >= 1
        assert payload["outputs"]["matrix_tsv"] == "protein_set_score.matrix.tsv"
        assert (
            "set_id\tset_name\tset_category\tsource_name\tsource_accession\tC1\tC2\tT1\tT2"
            in Path("protein_set_score.matrix.tsv").read_text(encoding="utf-8")
        )
        assert "sample_id\tcondition\tbatch\tactivity_score" in Path(
            "protein_set_score.samples.tsv"
        ).read_text(encoding="utf-8")
        assert "confidence_status" in Path("protein_set_score.samples.tsv").read_text(
            encoding="utf-8"
        )
        assert "condition\tsample_count\tscored_sample_count" in Path(
            "protein_set_score.conditions.tsv"
        ).read_text(encoding="utf-8")
        assert "confidence_status" in Path(
            "protein_set_score.conditions.tsv"
        ).read_text(encoding="utf-8")
        assert "condition_a_confidence_status" in Path(
            "protein_set_score.comparisons.tsv"
        ).read_text(encoding="utf-8")
        assert "P999" in Path("protein_set_score.unresolved.tsv").read_text(
            encoding="utf-8"
        )
        assert Path("protein_set_score.rejected.tsv").read_text(encoding="utf-8").splitlines()[
            0
        ] == "row_number\tvalues\treason"


def test_protein_set_enrichment_command_requires_explicit_background_by_default() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        interpretation_fixture_dir = FIXTURE_ROOT / "interpretation"
        shutil.copy(
            interpretation_fixture_dir / "protein_set_enrichment_foreground.tsv",
            "protein_set_enrichment_foreground.tsv",
        )
        shutil.copy(
            interpretation_fixture_dir / "protein_set_enrichment.tsv",
            "protein_set_enrichment.tsv",
        )

        result = runner.invoke(
            cli,
            [
                "interpretation",
                "protein-set-enrichment",
                "protein_set_enrichment_foreground.tsv",
                "protein_set_enrichment.tsv",
            ],
        )

        assert result.exit_code != 0
        assert (
            "explicit background protein set is required unless "
            "missing_background_policy is membership_universe"
        ) in result.output


def test_protein_set_enrichment_command_emits_result_and_universe_gap_ledgers() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        interpretation_fixture_dir = FIXTURE_ROOT / "interpretation"
        shutil.copy(
            interpretation_fixture_dir / "protein_set_enrichment_foreground.tsv",
            "protein_set_enrichment_foreground.tsv",
        )
        shutil.copy(
            interpretation_fixture_dir / "protein_set_enrichment.tsv",
            "protein_set_enrichment.tsv",
        )

        result = runner.invoke(
            cli,
            [
                "interpretation",
                "protein-set-enrichment",
                "protein_set_enrichment_foreground.tsv",
                "protein_set_enrichment.tsv",
                "--missing-background-policy",
                "membership_universe",
                "--max-adjusted-p-value",
                "1.0",
                "--min-enrichment-ratio",
                "0.0",
                "--summary-tsv-out",
                "protein_set_enrichment.summary.tsv",
                "--result-tsv-out",
                "protein_set_enrichment.result.tsv",
                "--universe-gap-tsv-out",
                "protein_set_enrichment.universe_gap.tsv",
                "--rejected-set-tsv-out",
                "protein_set_enrichment.rejected.tsv",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["report"]["summary"]["background_source"] == "membership_universe"
        assert payload["report"]["summary"]["foreground_universe_gap_count"] == 1
        assert payload["outputs"]["result_tsv"] == "protein_set_enrichment.result.tsv"
        assert Path(
            "protein_set_enrichment.summary.tsv"
        ).read_text().splitlines()[0].startswith("foreground_size\tbackground_size")
        assert "set_id\tset_name\tset_category\tsource_name\tsource_accession" in Path(
            "protein_set_enrichment.result.tsv"
        ).read_text()
        assert "foreground\tP999\tprotein was not present in the membership universe" in (
            Path("protein_set_enrichment.universe_gap.tsv").read_text()
        )
        assert (
            Path("protein_set_enrichment.rejected.tsv").read_text().splitlines()[0]
            == "row_number\tvalues\treason"
        )


def test_ppi_modules_command_emits_edges_modules_isolates_and_enrichment() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        interpretation_fixture_dir = FIXTURE_ROOT / "interpretation"
        shutil.copy(
            interpretation_fixture_dir / "ppi_significant.tsv",
            "ppi_significant.tsv",
        )
        shutil.copy(
            interpretation_fixture_dir / "ppi_edges.tsv",
            "ppi_edges.tsv",
        )
        shutil.copy(
            interpretation_fixture_dir / "ppi_edges_invalid.tsv",
            "ppi_edges_invalid.tsv",
        )
        shutil.copy(
            interpretation_fixture_dir / "protein_set_enrichment.tsv",
            "protein_set_enrichment.tsv",
        )

        result = runner.invoke(
            cli,
            [
                "interpretation",
                "ppi-modules",
                "ppi_significant.tsv",
                "ppi_edges.tsv",
                "--protein-set-tsv",
                "protein_set_enrichment.tsv",
                "--summary-tsv-out",
                "ppi_modules.summary.tsv",
                "--edge-tsv-out",
                "ppi_modules.edges.tsv",
                "--module-tsv-out",
                "ppi_modules.modules.tsv",
                "--isolated-tsv-out",
                "ppi_modules.isolated.tsv",
                "--module-enrichment-tsv-out",
                "ppi_modules.enrichment.tsv",
                "--rejected-edge-tsv-out",
                "ppi_modules.rejected.tsv",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["report"]["summary"]["module_count"] == 1
        assert payload["report"]["summary"]["isolated_protein_count"] == 2
        assert payload["outputs"]["module_tsv"] == "ppi_modules.modules.tsv"
        assert "ppi_module:P001,P002,P003" in Path(
            "ppi_modules.modules.tsv"
        ).read_text(encoding="utf-8")
        assert "P004" in Path("ppi_modules.isolated.tsv").read_text(encoding="utf-8")
        assert "stress_panel" in Path("ppi_modules.enrichment.tsv").read_text(
            encoding="utf-8"
        )
        assert Path("ppi_modules.rejected.tsv").read_text(encoding="utf-8").splitlines()[
            0
        ] == "row_number\tvalues\treason"


def test_go_enrichment_command_emits_term_and_unannotated_ledgers() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        interpretation_fixture_dir = FIXTURE_ROOT / "interpretation"
        shutil.copy(
            interpretation_fixture_dir / "go_foreground.tsv",
            "go_foreground.tsv",
        )
        shutil.copy(
            interpretation_fixture_dir / "go_background.tsv",
            "go_background.tsv",
        )
        shutil.copy(
            interpretation_fixture_dir / "go_annotations.tsv",
            "go_annotations.tsv",
        )

        result = runner.invoke(
            cli,
            [
                "interpretation",
                "go-enrichment",
                "go_foreground.tsv",
                "go_background.tsv",
                "go_annotations.tsv",
                "--summary-tsv-out",
                "go_enrichment.summary.tsv",
                "--term-tsv-out",
                "go_enrichment.term.tsv",
                "--unannotated-tsv-out",
                "go_enrichment.unannotated.tsv",
                "--rejected-annotation-tsv-out",
                "go_enrichment.rejected.tsv",
                "--max-adjusted-p-value",
                "0.6",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["report"]["summary"]["foreground_size"] == 3
        assert payload["report"]["summary"]["background_size"] == 6
        assert payload["report"]["summary"]["evaluated_term_count"] == 3
        assert Path("go_enrichment.summary.tsv").read_text().splitlines()[0].startswith(
            "foreground_size\tbackground_size"
        )
        assert "GO:0006915" in Path("go_enrichment.term.tsv").read_text()
        assert "background\tQ88888" in Path("go_enrichment.unannotated.tsv").read_text()
        assert (
            "duplicate GO membership for P04637 and GO:0006915"
            in Path("go_enrichment.rejected.tsv").read_text()
        )


def test_pathway_enrichment_command_emits_pathway_and_unresolved_ledgers() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        interpretation_fixture_dir = FIXTURE_ROOT / "interpretation"
        shutil.copy(
            interpretation_fixture_dir / "pathway_foreground.tsv",
            "pathway_foreground.tsv",
        )
        shutil.copy(
            interpretation_fixture_dir / "pathway_background.tsv",
            "pathway_background.tsv",
        )
        shutil.copy(
            interpretation_fixture_dir / "pathway_memberships.tsv",
            "pathway_memberships.tsv",
        )
        shutil.copy(
            interpretation_fixture_dir / "protein_annotation_reference.fasta",
            "protein_annotation_reference.fasta",
        )
        shutil.copy(
            interpretation_fixture_dir / "protein_annotation_custom.tsv",
            "protein_annotation_custom.tsv",
        )

        result = runner.invoke(
            cli,
            [
                "interpretation",
                "pathway-enrichment",
                "pathway_foreground.tsv",
                "pathway_background.tsv",
                "pathway_memberships.tsv",
                "--fasta",
                "protein_annotation_reference.fasta",
                "--annotation-tsv",
                "protein_annotation_custom.tsv",
                "--summary-tsv-out",
                "pathway_enrichment.summary.tsv",
                "--pathway-tsv-out",
                "pathway_enrichment.pathway.tsv",
                "--unresolved-tsv-out",
                "pathway_enrichment.unresolved.tsv",
                "--rejected-pathway-tsv-out",
                "pathway_enrichment.rejected.tsv",
                "--max-adjusted-p-value",
                "1.0",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["report"]["summary"]["foreground_size"] == 3
        assert payload["report"]["summary"]["background_size"] == 6
        assert payload["report"]["summary"]["evaluated_entry_count"] == 5
        assert Path("pathway_enrichment.summary.tsv").read_text().splitlines()[
            0
        ].startswith("foreground_size\tbackground_size")
        assert "hsa04115" in Path("pathway_enrichment.pathway.tsv").read_text()
        assert (
            "background\tQ88888\t"
            in Path("pathway_enrichment.unresolved.tsv").read_text()
        )
        assert (
            "duplicate pathway membership for custom:stress and gene member TP53"
            in Path("pathway_enrichment.rejected.tsv").read_text()
        )


def test_pathway_activity_command_emits_matrix_contributions_and_contrasts() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        workflow_fixture_dir = FIXTURE_ROOT / "workflow"
        shutil.copy(
            workflow_fixture_dir / "biological_report_features.tsv",
            "biological_report_features.tsv",
        )
        shutil.copy(
            workflow_fixture_dir / "biological_report.design.tsv",
            "biological_report.design.tsv",
        )
        shutil.copy(
            workflow_fixture_dir / "biological_report_pathways.tsv",
            "biological_report_pathways.tsv",
        )
        shutil.copy(
            workflow_fixture_dir / "biological_report_reference.fasta",
            "biological_report_reference.fasta",
        )

        result = runner.invoke(
            cli,
            [
                "interpretation",
                "pathway-activity",
                "biological_report_features.tsv",
                "biological_report_pathways.tsv",
                "--design-path",
                "biological_report.design.tsv",
                "--fasta",
                "biological_report_reference.fasta",
                "--summary-tsv-out",
                "pathway_activity.summary.tsv",
                "--matrix-tsv-out",
                "pathway_activity.matrix.tsv",
                "--sample-score-tsv-out",
                "pathway_activity.samples.tsv",
                "--condition-score-tsv-out",
                "pathway_activity.conditions.tsv",
                "--condition-comparison-tsv-out",
                "pathway_activity.comparisons.tsv",
                "--member-contribution-tsv-out",
                "pathway_activity.members.tsv",
                "--unresolved-member-tsv-out",
                "pathway_activity.unresolved.tsv",
                "--rejected-pathway-tsv-out",
                "pathway_activity.rejected.tsv",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["report"]["summary"]["pathway_count"] == 1
        assert payload["report"]["summary"]["condition_comparison_count"] == 1
        assert Path("pathway_activity.summary.tsv").read_text().splitlines()[
            0
        ].startswith("entity_level\tmeasure_kind")
        assert "pathway_id\tpathway_name\tsource_name\tsource_accession\tC1\tC2\tC3\tT1\tT2\tT3" in Path(
            "pathway_activity.matrix.tsv"
        ).read_text()
        assert "member_kind\tmember_id\tresolved_protein_refs" in Path(
            "pathway_activity.members.tsv"
        ).read_text()
        assert "condition_a_confidence_status" in Path(
            "pathway_activity.comparisons.tsv"
        ).read_text()
        assert Path("pathway_activity.unresolved.tsv").read_text().splitlines()[0].startswith(
            "pathway_id\tpathway_name\tsource_name"
        )


def test_complex_enrichment_command_emits_complex_and_unresolved_ledgers() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        interpretation_fixture_dir = FIXTURE_ROOT / "interpretation"
        shutil.copy(
            interpretation_fixture_dir / "complex_foreground.tsv",
            "complex_foreground.tsv",
        )
        shutil.copy(
            interpretation_fixture_dir / "complex_background.tsv",
            "complex_background.tsv",
        )
        shutil.copy(
            interpretation_fixture_dir / "complex_memberships.tsv",
            "complex_memberships.tsv",
        )
        shutil.copy(
            interpretation_fixture_dir / "protein_annotation_reference.fasta",
            "protein_annotation_reference.fasta",
        )
        shutil.copy(
            interpretation_fixture_dir / "protein_annotation_custom.tsv",
            "protein_annotation_custom.tsv",
        )

        result = runner.invoke(
            cli,
            [
                "interpretation",
                "complex-enrichment",
                "complex_foreground.tsv",
                "complex_background.tsv",
                "complex_memberships.tsv",
                "--fasta",
                "protein_annotation_reference.fasta",
                "--annotation-tsv",
                "protein_annotation_custom.tsv",
                "--summary-tsv-out",
                "complex_enrichment.summary.tsv",
                "--complex-tsv-out",
                "complex_enrichment.complex.tsv",
                "--unresolved-tsv-out",
                "complex_enrichment.unresolved.tsv",
                "--rejected-complex-tsv-out",
                "complex_enrichment.rejected.tsv",
                "--max-adjusted-p-value",
                "1.0",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["report"]["summary"]["foreground_size"] == 3
        assert payload["report"]["summary"]["background_size"] == 6
        assert payload["report"]["summary"]["evaluated_entry_count"] == 4
        assert Path("complex_enrichment.summary.tsv").read_text().splitlines()[
            0
        ].startswith("foreground_size\tbackground_size")
        assert "CORUM:0176" in Path("complex_enrichment.complex.tsv").read_text()
        assert (
            "background\tQ88888\t"
            in Path("complex_enrichment.unresolved.tsv").read_text()
        )
        assert (
            "duplicate complex membership for custom:stressosome and gene member TP53"
            in Path("complex_enrichment.rejected.tsv").read_text()
        )


def test_complex_activity_command_emits_matrix_contributions_and_limiting_members() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        workflow_fixture_dir = FIXTURE_ROOT / "workflow"
        shutil.copy(
            workflow_fixture_dir / "biological_report_features.tsv",
            "biological_report_features.tsv",
        )
        shutil.copy(
            workflow_fixture_dir / "biological_report.design.tsv",
            "biological_report.design.tsv",
        )
        shutil.copy(
            workflow_fixture_dir / "biological_report_complexes.tsv",
            "biological_report_complexes.tsv",
        )
        shutil.copy(
            workflow_fixture_dir / "biological_report_reference.fasta",
            "biological_report_reference.fasta",
        )

        result = runner.invoke(
            cli,
            [
                "interpretation",
                "complex-activity",
                "biological_report_features.tsv",
                "biological_report_complexes.tsv",
                "--design-path",
                "biological_report.design.tsv",
                "--fasta",
                "biological_report_reference.fasta",
                "--summary-tsv-out",
                "complex_activity.summary.tsv",
                "--matrix-tsv-out",
                "complex_activity.matrix.tsv",
                "--sample-score-tsv-out",
                "complex_activity.samples.tsv",
                "--condition-score-tsv-out",
                "complex_activity.conditions.tsv",
                "--condition-comparison-tsv-out",
                "complex_activity.comparisons.tsv",
                "--member-contribution-tsv-out",
                "complex_activity.members.tsv",
                "--unresolved-member-tsv-out",
                "complex_activity.unresolved.tsv",
                "--rejected-complex-tsv-out",
                "complex_activity.rejected.tsv",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["report"]["summary"]["complex_count"] == 1
        assert payload["report"]["summary"]["condition_comparison_count"] == 1
        assert Path("complex_activity.summary.tsv").read_text().splitlines()[
            0
        ].startswith("entity_level\tmeasure_kind")
        assert "complex_id\tcomplex_name\tsource_name\tsource_accession\tC1\tC2\tC3\tT1\tT2\tT3" in Path(
            "complex_activity.matrix.tsv"
        ).read_text()
        assert "member_kind\tmember_id\tresolved_protein_refs" in Path(
            "complex_activity.members.tsv"
        ).read_text()
        assert "limiting_member_ids" in Path(
            "complex_activity.samples.tsv"
        ).read_text()
        assert "condition_a_confidence_status" in Path(
            "complex_activity.comparisons.tsv"
        ).read_text()
        assert Path("complex_activity.unresolved.tsv").read_text().splitlines()[0].startswith(
            "complex_id\tcomplex_name\tsource_name"
        )


def test_compartment_biology_command_emits_enrichment_activity_and_unknown_localization() -> (
    None
):
    runner = CliRunner()
    with runner.isolated_filesystem():
        workflow_fixture_dir = FIXTURE_ROOT / "workflow"
        shutil.copy(
            workflow_fixture_dir / "biological_report_features.tsv",
            "biological_report_features.tsv",
        )
        shutil.copy(
            workflow_fixture_dir / "biological_report.design.tsv",
            "biological_report.design.tsv",
        )
        shutil.copy(
            workflow_fixture_dir / "biological_report_compartments.tsv",
            "biological_report_compartments.tsv",
        )

        result = runner.invoke(
            cli,
            [
                "interpretation",
                "compartment-biology",
                "biological_report_features.tsv",
                "biological_report_compartments.tsv",
                "--design-path",
                "biological_report.design.tsv",
                "--summary-tsv-out",
                "compartment_biology.summary.tsv",
                "--enrichment-tsv-out",
                "compartment_biology.enrichment.tsv",
                "--matrix-tsv-out",
                "compartment_biology.matrix.tsv",
                "--sample-score-tsv-out",
                "compartment_biology.samples.tsv",
                "--condition-score-tsv-out",
                "compartment_biology.conditions.tsv",
                "--condition-comparison-tsv-out",
                "compartment_biology.comparisons.tsv",
                "--unresolved-member-tsv-out",
                "compartment_biology.unresolved.tsv",
                "--unknown-localization-tsv-out",
                "compartment_biology.unknown.tsv",
                "--rejected-context-tsv-out",
                "compartment_biology.rejected.tsv",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["report"]["summary"]["compartment_count"] == 2
        assert payload["report"]["summary"]["unknown_foreground_protein_count"] == 1
        assert payload["report"]["summary"]["unknown_background_protein_count"] == 2
        assert Path("compartment_biology.summary.tsv").read_text().splitlines()[
            0
        ].startswith("compartment_count\tforeground_protein_count")
        assert "compartment_id\tcompartment_name\tsource_name\tsource_accession" in Path(
            "compartment_biology.enrichment.tsv"
        ).read_text()
        assert "compartment_id\tcompartment_name\tsource_name\tsource_accession\tC1\tC2\tC3\tT1\tT2\tT3" in Path(
            "compartment_biology.matrix.tsv"
        ).read_text()
        assert "condition_a_confidence_status" in Path(
            "compartment_biology.comparisons.tsv"
        ).read_text()
        assert Path("compartment_biology.unresolved.tsv").read_text().splitlines()[0].startswith(
            "compartment_id\tcompartment_name\tsource_name"
        )
        assert "localization_scope\tprotein_ref\treason" == Path(
            "compartment_biology.unknown.tsv"
        ).read_text().splitlines()[0]
        assert "rejected rows" not in result.output
        assert Path("compartment_biology.rejected.tsv").read_text().splitlines()[
            0
        ].startswith("row_number")


def test_regulator_inference_command_emits_separated_site_and_abundance_outputs() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        workflow_fixture_dir = FIXTURE_ROOT / "workflow"
        shutil.copy(
            workflow_fixture_dir / "biological_report_features.tsv",
            "biological_report_features.tsv",
        )
        shutil.copy(
            workflow_fixture_dir / "biological_report.design.tsv",
            "biological_report.design.tsv",
        )
        shutil.copy(
            workflow_fixture_dir / "biological_report_reference.fasta",
            "biological_report_reference.fasta",
        )
        shutil.copy(
            workflow_fixture_dir / "biological_report_pathways.tsv",
            "biological_report_pathways.tsv",
        )
        shutil.copy(
            workflow_fixture_dir / "biological_report_regulator_evidence.tsv",
            "biological_report_regulator_evidence.tsv",
        )
        shutil.copy(
            workflow_fixture_dir / "biological_report_regulator_sites.tsv",
            "biological_report_regulator_sites.tsv",
        )

        result = runner.invoke(
            cli,
            [
                "interpretation",
                "regulator-inference",
                "biological_report_features.tsv",
                "biological_report_regulator_evidence.tsv",
                "--design-path",
                "biological_report.design.tsv",
                "--fasta",
                "biological_report_reference.fasta",
                "--pathway-membership-tsv",
                "biological_report_pathways.tsv",
                "--site-differential-tsv",
                "biological_report_regulator_sites.tsv",
                "--summary-tsv-out",
                "regulator_inference.summary.tsv",
                "--inference-tsv-out",
                "regulator_inference.tsv",
                "--unresolved-target-tsv-out",
                "regulator_inference.unresolved.tsv",
                "--rejected-evidence-tsv-out",
                "regulator_inference.rejected.tsv",
                "--rejected-site-signal-tsv-out",
                "regulator_sites.rejected.tsv",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["report"]["summary"]["entry_count"] == 5
        assert payload["report"]["summary"]["site_regulation_entry_count"] == 1
        assert payload["report"]["summary"]["pathway_activity_entry_count"] == 1
        assert Path("regulator_inference.summary.tsv").read_text().splitlines()[
            0
        ].startswith("condition_a\tcondition_b\tregulator_count")
        assert "regulator\tevidence_type\tsignal_surface" in Path(
            "regulator_inference.tsv"
        ).read_text()
        assert "MAPK14\tkinase_substrate\tsite_regulation" in Path(
            "regulator_inference.tsv"
        ).read_text()
        assert "Stress commander\tpathway\tpathway_activity" in Path(
            "regulator_inference.tsv"
        ).read_text()
        assert "target_field\ttarget_value" in Path(
            "regulator_inference.unresolved.tsv"
        ).read_text()
        assert Path("regulator_inference.rejected.tsv").read_text().splitlines()[
            0
        ] == "row_number\treason\tvalues"
        assert Path("regulator_sites.rejected.tsv").read_text().splitlines()[0] == (
            "row_number\treason\tvalues"
        )


def test_disease_phenotype_command_emits_explicit_annotation_outputs() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        workflow_fixture_dir = FIXTURE_ROOT / "workflow"
        shutil.copy(
            workflow_fixture_dir / "biological_report_features.tsv",
            "biological_report_features.tsv",
        )
        shutil.copy(
            workflow_fixture_dir / "biological_report.design.tsv",
            "biological_report.design.tsv",
        )
        shutil.copy(
            workflow_fixture_dir / "biological_report_disease_phenotype.tsv",
            "biological_report_disease_phenotype.tsv",
        )

        result = runner.invoke(
            cli,
            [
                "interpretation",
                "disease-phenotype",
                "biological_report_features.tsv",
                "biological_report_disease_phenotype.tsv",
                "--design-path",
                "biological_report.design.tsv",
                "--summary-tsv-out",
                "disease_phenotype.summary.tsv",
                "--interpretation-tsv-out",
                "disease_phenotype.tsv",
                "--unknown-annotation-tsv-out",
                "disease_phenotype.unknown.tsv",
                "--rejected-context-tsv-out",
                "disease_phenotype.rejected.tsv",
                "--max-adjusted-p-value",
                "1.0",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["report"]["summary"]["term_count"] == 4
        assert payload["report"]["summary"]["disease_term_count"] == 2
        assert payload["report"]["summary"]["phenotype_term_count"] == 2
        assert Path("disease_phenotype.summary.tsv").read_text().splitlines()[
            0
        ].startswith("term_count\tdisease_term_count\tphenotype_term_count")
        assert "context_kind\tterm_id\tterm_name\tsource_name" in Path(
            "disease_phenotype.tsv"
        ).read_text()
        assert "DOID:162" in Path("disease_phenotype.tsv").read_text()
        assert Path("disease_phenotype.unknown.tsv").read_text().splitlines()[
            0
        ] == "annotation_scope\tprotein_ref\treason"
        assert Path("disease_phenotype.rejected.tsv").read_text().splitlines()[
            0
        ].startswith("row_number")


def test_drug_target_command_emits_direct_and_indirect_outputs() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        workflow_fixture_dir = FIXTURE_ROOT / "workflow"
        shutil.copy(
            workflow_fixture_dir / "biological_report_features.tsv",
            "biological_report_features.tsv",
        )
        shutil.copy(
            workflow_fixture_dir / "biological_report.design.tsv",
            "biological_report.design.tsv",
        )
        shutil.copy(
            workflow_fixture_dir / "biological_report_reference.fasta",
            "biological_report_reference.fasta",
        )
        shutil.copy(
            workflow_fixture_dir / "biological_report_drug_targets.tsv",
            "biological_report_drug_targets.tsv",
        )
        shutil.copy(
            workflow_fixture_dir / "biological_report_pathways.tsv",
            "biological_report_pathways.tsv",
        )

        result = runner.invoke(
            cli,
            [
                "interpretation",
                "drug-target",
                "biological_report_features.tsv",
                "biological_report_drug_targets.tsv",
                "--design-path",
                "biological_report.design.tsv",
                "--fasta",
                "biological_report_reference.fasta",
                "--pathway-membership-tsv",
                "biological_report_pathways.tsv",
                "--summary-tsv-out",
                "drug_target.summary.tsv",
                "--interpretation-tsv-out",
                "drug_target.tsv",
                "--rejected-context-tsv-out",
                "drug_target.rejected.tsv",
                "--rejected-pathway-tsv-out",
                "drug_target.pathways.rejected.tsv",
                "--max-adjusted-p-value",
                "1.0",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["report"]["summary"]["drug_count"] == 1
        assert payload["report"]["summary"]["direct_target_entry_count"] == 1
        assert (
            payload["report"]["summary"]["indirect_pathway_neighbor_entry_count"] == 2
        )
        assert Path("drug_target.summary.tsv").read_text().splitlines()[
            0
        ].startswith("condition_a\tcondition_b\tdrug_count\tentry_count")
        assert "relationship" in Path("drug_target.tsv").read_text()
        assert "direct_target" in Path("drug_target.tsv").read_text()
        assert "indirect_pathway_neighbor" in Path("drug_target.tsv").read_text()
        assert Path("drug_target.rejected.tsv").read_text().splitlines()[
            0
        ].startswith("row_number")
        assert Path("drug_target.pathways.rejected.tsv").read_text().splitlines()[
            0
        ].startswith("row_number")


def test_fasta_commands_cover_parse_stats_dedup_filter_provenance_and_decoy(
    fasta_fixture_dir: Path,
) -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        shutil.copy(fasta_fixture_dir / "valid_records.fasta", "valid.fasta")
        shutil.copy(fasta_fixture_dir / "dedup_input.fasta", "dedup.fasta")
        shutil.copy(
            fasta_fixture_dir / "external_contaminants.fasta",
            "external_contaminants.fasta",
        )
        shutil.copy(
            fasta_fixture_dir / "production_grade_database.fasta",
            "production.fasta",
        )

        parse_result = runner.invoke(
            cli, ["fasta-parse", "valid.fasta", "--mode", "strict"]
        )
        assert parse_result.exit_code == 0
        parse_payload = json.loads(parse_result.output)
        assert parse_payload["total_records"] == 3
        assert parse_payload["database_composition"]["accepted_record_count"] == 3
        assert parse_payload["duplicate_accessions"] == []

        stats_result = runner.invoke(
            cli,
            [
                "fasta-stats",
                "dedup.fasta",
                "--mode",
                "permissive",
                "--duplicate-accession-policy",
                "accept_with_warning",
            ],
        )
        assert stats_result.exit_code == 0
        stats_payload = json.loads(stats_result.output)
        assert stats_payload["duplicate_accession_count"] == 1
        assert stats_payload["duplicate_sequence_count"] == 2

        contaminant_build_result = runner.invoke(
            cli,
            [
                "fasta-contaminants",
                "valid.fasta",
                "--mode",
                "strict",
                "--contaminant-fasta",
                "external_contaminants.fasta",
                "--out-fasta",
                "target_with_contaminants.fasta",
            ],
        )
        assert contaminant_build_result.exit_code == 0
        contaminant_build_payload = json.loads(contaminant_build_result.output)
        assert contaminant_build_payload["appended_builtin_record_count"] == 4
        assert contaminant_build_payload["appended_external_record_count"] == 2
        assert contaminant_build_payload["output_record_count"] == 9
        combined_fasta = Path("target_with_contaminants.fasta").read_text()
        assert combined_fasta.count(">") == 9
        assert ">CON__trypsin_lab" in combined_fasta
        assert ">CON__sp|P02769|ALBU_BOVIN" in combined_fasta

        profile_result = runner.invoke(
            cli,
            [
                "fasta-profile",
                "production.fasta",
                "--mode",
                "strict",
                "--summary-tsv-out",
                "production.summary.tsv",
                "--length-tsv-out",
                "production.length.tsv",
                "--organism-tsv-out",
                "production.organism.tsv",
                "--invalid-sequence-tsv-out",
                "production.invalid.tsv",
            ],
        )
        assert profile_result.exit_code == 0
        profile_payload = json.loads(profile_result.output)
        assert profile_payload["summary"]["input_record_count"] == 9
        assert profile_payload["summary"]["protein_count"] == 6
        assert profile_payload["summary"]["target_count"] == 5
        assert profile_payload["summary"]["decoy_count"] == 1
        assert profile_payload["summary"]["contaminant_count"] == 1
        assert profile_payload["summary"]["organism_annotated_count"] == 5
        assert [row["source_identifier"] for row in profile_payload["invalid_sequence_report"]] == [
            "custom_empty",
            "custom_invalid",
        ]
        assert profile_payload["organism_distribution"] == [
            {
                "organism": "Homo sapiens",
                "protein_count": 4,
                "target_count": 3,
                "decoy_count": 1,
                "contaminant_count": 1,
            },
            {
                "organism": "Mus musculus",
                "protein_count": 1,
                "target_count": 1,
                "decoy_count": 0,
                "contaminant_count": 0,
            },
        ]
        assert (
            Path("production.summary.tsv")
            .read_text()
            .splitlines()[0]
            .startswith("input_record_count\tprotein_count\trejected_record_count")
        )
        assert "1-99\t1\t99\t6\t116" in Path("production.length.tsv").read_text()
        assert "Homo sapiens\t4\t3\t1\t1" in Path("production.organism.tsv").read_text()
        assert (
            "custom_empty\tcustom_empty Example empty\tempty_sequence\tsequence must contain at least one amino-acid residue"
            in Path("production.invalid.tsv").read_text()
        )
        assert (
            "custom_invalid\tcustom_invalid Example invalid\tinvalid_character\tsequence contains invalid non-residue characters"
            in Path("production.invalid.tsv").read_text()
        )

        dedup_result = runner.invoke(
            cli,
            [
                "fasta-dedup",
                "dedup.fasta",
                "--mode",
                "permissive",
                "--duplicate-accession-policy",
                "accept_with_warning",
                "--out-fasta",
                "deduped.fasta",
            ],
        )
        assert dedup_result.exit_code == 0
        dedup_payload = json.loads(dedup_result.output)
        assert dedup_payload["output_records"] == 2
        assert Path("deduped.fasta").read_text().count(">") == 2

        filter_result = runner.invoke(
            cli,
            [
                "fasta-filter",
                "dedup.fasta",
                "--mode",
                "permissive",
                "--duplicate-accession-policy",
                "accept_with_warning",
                "--organism",
                "Homo sapiens",
                "--exclude-contaminants",
                "--out-fasta",
                "filtered.fasta",
            ],
        )
        assert filter_result.exit_code == 0
        filter_payload = json.loads(filter_result.output)
        assert filter_payload["excluded_as_contaminant"] == 1
        assert "CON__CRAP" not in Path("filtered.fasta").read_text()

        provenance_result = runner.invoke(
            cli,
            [
                "fasta-provenance",
                "valid.fasta",
                "--mode",
                "strict",
                "--out",
                "provenance.json",
            ],
        )
        assert provenance_result.exit_code == 0
        provenance_payload = json.loads(Path("provenance.json").read_text())
        assert (
            provenance_payload["document_schema"]["document_kind"]
            == "fasta_provenance_manifest"
        )

        production_result = runner.invoke(
            cli, ["fasta-parse", "production.fasta", "--mode", "strict"]
        )
        assert production_result.exit_code == 0
        production_payload = json.loads(production_result.output)
        assert production_payload["duplicate_accession_policy"] == "reject"
        assert production_payload["duplicate_accessions"] == ["uniprot:P04637"]
        assert production_payload["database_composition"] == {
            "accepted_record_count": 6,
            "target_count": 5,
            "decoy_count": 1,
            "contaminant_count": 1,
            "accession_namespace_counts": {
                "custom": 2,
                "ensembl": 1,
                "refseq": 1,
                "uniprot": 2,
            },
        }

        permissive_duplicate_parse = runner.invoke(
            cli,
            [
                "fasta-parse",
                "dedup.fasta",
                "--mode",
                "permissive",
                "--duplicate-accession-policy",
                "accept_with_warning",
            ],
        )
        assert permissive_duplicate_parse.exit_code == 0
        permissive_duplicate_payload = json.loads(permissive_duplicate_parse.output)
        assert permissive_duplicate_payload["duplicate_accession_policy"] == (
            "accept_with_warning"
        )
        assert len(permissive_duplicate_payload["accepted_records"]) == 4

        decoy_result = runner.invoke(
            cli,
            [
                "fasta-decoy",
                "valid.fasta",
                "--mode",
                "strict",
                "--decoy-mode",
                "reverse",
                "--out-fasta",
                "target_decoy.fasta",
                "--manifest-out",
                "target_decoy.manifest.json",
            ],
        )
        assert decoy_result.exit_code == 0
        decoy_payload = json.loads(decoy_result.output)
        assert decoy_payload["valid"] is True
        assert len(decoy_payload["reproducibility_hash"]) == 64
        assert decoy_payload["generation_report"]["input_target_count"] == 3
        assert decoy_payload["generation_report"]["generated_decoy_count"] == 3
        assert decoy_payload["generation_report"]["decoy_mode"] == "reverse"
        assert Path("target_decoy.fasta").read_text().count(">") == 6
        decoy_manifest = json.loads(Path("target_decoy.manifest.json").read_text())
        assert (
            decoy_manifest["document_schema"]["document_kind"]
            == "decoy_generation_manifest"
        )
        assert (
            decoy_manifest["reproducibility_hash"]
            == decoy_payload["reproducibility_hash"]
        )


def test_sequence_checksum_and_target_decoy_validate_commands(
    fasta_fixture_dir: Path,
) -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        checksum_result = runner.invoke(
            cli,
            ["sequence-checksum", "--sequence", " acd ef "],
        )
        assert checksum_result.exit_code == 0
        checksum_payload = json.loads(checksum_result.output)
        assert checksum_payload["normalized_sequence"] == "ACDEF"
        assert len(checksum_payload["sequence_checksum"]) == 64

        shutil.copy(
            fasta_fixture_dir / "target_decoy_valid.fasta", "target_decoy_valid.fasta"
        )
        validation_result = runner.invoke(
            cli,
            ["target-decoy-validate", "target_decoy_valid.fasta"],
        )
        assert validation_result.exit_code == 0
        validation_payload = json.loads(validation_result.output)
        assert validation_payload["valid"] is True


def test_fasta_decoy_command_reports_shuffle_caveats_and_prefix_collisions() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        Path("homopolymer.fasta").write_text(
            ">sp|P00001|HOMO_HUMAN Homopolymer OS=Homo sapiens GN=HOMO\nAAAAAA\n"
        )
        shuffle_result = runner.invoke(
            cli,
            [
                "fasta-decoy",
                "homopolymer.fasta",
                "--mode",
                "strict",
                "--decoy-mode",
                "shuffle",
                "--seed",
                "11",
                "--out-fasta",
                "homopolymer_decoy.fasta",
            ],
        )
        assert shuffle_result.exit_code == 0
        shuffle_payload = json.loads(shuffle_result.output)
        assert shuffle_payload["generation_report"]["unchanged_sequence_count"] == 1
        assert (
            shuffle_payload["generation_report"]["target_sequence_collision_count"] == 1
        )

        Path("collision.fasta").write_text(
            ">target_one Alpha target [Homo sapiens]\nMPEPTIDE\n"
            ">LAB_target_one Existing prefixed target [Homo sapiens]\nMSEQENCE\n"
        )
        collision_result = runner.invoke(
            cli,
            [
                "fasta-decoy",
                "collision.fasta",
                "--mode",
                "strict",
                "--prefix",
                "LAB_",
                "--out-fasta",
                "collision_decoy.fasta",
            ],
        )
        assert collision_result.exit_code != 0
        assert "collide with existing target accessions" in collision_result.output


def test_digest_command_writes_export_and_manifest(
    fasta_fixture_dir: Path,
) -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        shutil.copy(fasta_fixture_dir / "valid_records.fasta", "valid.fasta")

        result = runner.invoke(
            cli,
            [
                "digest",
                "valid.fasta",
                "--protease",
                "trypsin",
                "--missed-cleavages",
                "1",
                "--digestion-mode",
                "full",
                "--min-length",
                "3",
                "--format",
                "jsonl",
                "--out",
                "peptides.jsonl",
                "--manifest-out",
                "digest.manifest.json",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["protease"] == "trypsin"
        assert payload["output_peptide_count"] > 0
        assert len(payload["policy_hash"]) == 64
        assert Path("peptides.jsonl").exists()
        manifest = json.loads(Path("digest.manifest.json").read_text())
        assert manifest["document_schema"]["document_kind"] == "peptide_digest_manifest"
        assert manifest["policy_hash"] == payload["policy_hash"]


def test_digest_command_supports_fasta_export_and_peptide_protein_sidecar(
    fasta_fixture_dir: Path,
) -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        shutil.copy(fasta_fixture_dir / "valid_records.fasta", "valid.fasta")

        result = runner.invoke(
            cli,
            [
                "digest",
                "valid.fasta",
                "--protease",
                "trypsin",
                "--format",
                "fasta",
                "--out",
                "peptides.fasta",
                "--peptide-protein-table-out",
                "peptide_protein_table.tsv",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["export_format"] == "fasta"
        assert payload["peptide_protein_table_path"] == "peptide_protein_table.tsv"
        assert len(payload["peptide_protein_table_sha256"]) == 64

        fasta_lines = Path("peptides.fasta").read_text().splitlines()
        assert fasta_lines[0].startswith(">")
        assert "|len=" in fasta_lines[0]
        assert "|mass=" in fasta_lines[0]

        table_lines = Path("peptide_protein_table.tsv").read_text().splitlines()
        assert table_lines[0].startswith("sequence\tlength\tneutral_mass")


def test_digest_command_reports_invalid_protease_and_invalid_fasta(
    fasta_fixture_dir: Path,
) -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        shutil.copy(fasta_fixture_dir / "mixed_quality.fasta", "mixed_quality.fasta")

        invalid_protease = runner.invoke(
            cli,
            [
                "digest",
                "mixed_quality.fasta",
                "--protease",
                "not-a-protease",
                "--out",
                "peptides.tsv",
            ],
        )
        assert invalid_protease.exit_code != 0
        assert "unknown protease rule" in invalid_protease.output

        invalid_fasta = runner.invoke(
            cli,
            [
                "digest",
                "mixed_quality.fasta",
                "--protease",
                "trypsin",
                "--mode",
                "strict",
                "--out",
                "peptides.tsv",
            ],
        )
        assert invalid_fasta.exit_code != 0
        assert "rejected records" in invalid_fasta.output


def test_digest_command_supports_builtin_aspn_and_custom_rules() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        Path("proteins.fasta").write_text(
            ">sp|P10001|ALPHA_HUMAN Alpha OS=Homo sapiens GN=ALPHA\nMPEPDADAA\n"
        )

        aspn_result = runner.invoke(
            cli,
            [
                "digest",
                "proteins.fasta",
                "--protease",
                "Asp-N",
                "--out",
                "aspn.tsv",
            ],
        )
        assert aspn_result.exit_code == 0
        aspn_payload = json.loads(aspn_result.output)
        assert aspn_payload["protease"] == "aspn"
        assert aspn_payload["custom_protease"] is None
        aspn_lines = Path("aspn.tsv").read_text().splitlines()
        assert any("\tMPEPDA\t" in line for line in aspn_lines[1:])
        assert any("\tDAA\t" in line for line in aspn_lines[1:])

        custom_result = runner.invoke(
            cli,
            [
                "digest",
                "proteins.fasta",
                "--custom-protease",
                "before=D;block_previous=P",
                "--custom-protease-name",
                "acidic",
                "--out",
                "custom.tsv",
            ],
        )
        assert custom_result.exit_code == 0
        custom_payload = json.loads(custom_result.output)
        assert custom_payload["protease"] == "acidic"
        assert custom_payload["custom_protease"] == "before=D;block_previous=P"
        custom_lines = Path("custom.tsv").read_text().splitlines()
        assert any("\tMPEPDA\t" in line for line in custom_lines[1:])

        conflict_result = runner.invoke(
            cli,
            [
                "digest",
                "proteins.fasta",
                "--protease",
                "lysc",
                "--custom-protease",
                "before=D;block_previous=P",
                "--out",
                "conflict.tsv",
            ],
        )
        assert conflict_result.exit_code != 0
        assert "cannot be combined" in conflict_result.output


def test_digest_command_supports_regex_custom_protease_rule() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        Path("proteins.fasta").write_text(
            ">sp|P10001|ALPHA_HUMAN Alpha OS=Homo sapiens GN=ALPHA\nPEPDADAA\n"
        )

        result = runner.invoke(
            cli,
            [
                "digest",
                "proteins.fasta",
                "--custom-protease",
                "pattern=(?<!P)(?P<site>D);cut_before=site",
                "--custom-protease-name",
                "acidic_regex",
                "--out",
                "regex.tsv",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["protease"] == "acidic_regex"
        assert (
            payload["custom_protease"]
            == "pattern=(?<!P)(?P<site>D);cut_before=site"
        )
        regex_lines = Path("regex.tsv").read_text().splitlines()
        assert any("\tPEPDA\t" in line for line in regex_lines[1:])
        assert any("\tDAA\t" in line for line in regex_lines[1:])


def test_digest_command_reports_invalid_output_path(
    fasta_fixture_dir: Path,
) -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        shutil.copy(fasta_fixture_dir / "valid_records.fasta", "valid.fasta")

        result = runner.invoke(
            cli,
            [
                "digest",
                "valid.fasta",
                "--protease",
                "trypsin",
                "--out",
                "missing/peptides.tsv",
            ],
        )

        assert result.exit_code != 0
        assert "No such file or directory" in result.output


def test_theoretical_digest_command_writes_governed_bundle() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        Path("proteins.fasta").write_text(
            ">sp|P12345|CHEM Protein chemistry\nACDMK\n"
        )

        result = runner.invoke(
            cli,
            [
                "theoretical-digest",
                "proteins.fasta",
                "--protease",
                "trypsin",
                "--static-mod",
                "Carbamidomethyl",
                "--variable-mod",
                "Oxidation",
                "--out-dir",
                "digest_bundle",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["protease"] == "trypsin"
        assert payload["static_modification_names"] == ["Carbamidomethyl"]
        assert payload["variable_modification_names"] == ["Oxidation"]
        assert payload["output_candidate_peptide_count"] == 2
        assert Path("digest_bundle/digest_peptides.tsv").exists()
        assert Path("digest_bundle/peptide_to_protein.tsv").exists()
        assert Path("digest_bundle/digest_summary.tsv").exists()
        assert "ACDM[Oxidation]K" in Path("digest_bundle/digest_peptides.tsv").read_text()
        assert "Carbamidomethyl" in Path("digest_bundle/digest_summary.tsv").read_text()


def test_peptide_index_command_reports_groups_il_equivalence_and_missed_cleavages() -> (
    None
):
    runner = CliRunner()
    with runner.isolated_filesystem():
        Path("database.fasta").write_text(
            ">sp|P10001|ALPHA_HUMAN Alpha OS=Homo sapiens GN=ALPHA\n"
            "MPEPTLDEKAK\n"
            ">sp|P20001|BETA_HUMAN Beta OS=Homo sapiens GN=BETA\n"
            "AKSHADEQKQQ\n"
            ">sp|P20002|GAMMA_HUMAN Gamma OS=Homo sapiens GN=GAMMA\n"
            "MKSHADEQKLL\n"
        )
        Path("groups.tsv").write_text(
            "accession\tprotein_group\nP20001\tGROUP_SHARED\nP20002\tGROUP_SHARED\n"
        )

        result = runner.invoke(
            cli,
            [
                "peptide-index",
                "database.fasta",
                "--peptide",
                "M[+15.9949]PEPTIDEK",
                "--peptide",
                "MPEPTLDEKAK",
                "--peptide",
                "SHADEQK",
                "--protease",
                "trypsin",
                "--missed-cleavages",
                "1",
                "--digestion-mode",
                "full",
                "--il-equivalent",
                "--protein-group-map",
                "groups.tsv",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["protease"] == "trypsin"
        assert payload["missed_cleavages"] == 1
        assert payload["il_equivalent"] is True
        assert payload["protein_group_map_supplied"] is True

        by_query = {
            entry["input_peptide"]: entry for entry in payload["report"]["entries"]
        }
        assert by_query["M[+15.9949]PEPTIDEK"]["canonical_peptide"] == "MPEPTIDEK"
        assert by_query["M[+15.9949]PEPTIDEK"]["il_equivalence_applied"] is True
        assert by_query["M[+15.9949]PEPTIDEK"]["modification_stripped"] is True
        assert by_query["M[+15.9949]PEPTIDEK"]["uniqueness_class"] == "unique"
        assert by_query["MPEPTLDEKAK"]["missed_cleavage_counts"] == [1]
        assert by_query["MPEPTLDEKAK"]["uniqueness_class"] == "unique"
        assert by_query["SHADEQK"]["protein_groups"] == ["GROUP_SHARED"]
        assert by_query["SHADEQK"]["uniqueness_class"] == "shared"
        assert by_query["SHADEQK"]["audit_class"] == "protein_group_specific"


def test_peptide_mass_command_reports_mass_fragments_and_localization() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(
            cli,
            [
                "peptide-mass",
                "PESTIDE",
                "--mod",
                "Phospho@3",
                "--charge",
                "2",
                "--include-neutral-losses",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["canonical_notation"] == "PES[Phospho]TIDE"
        assert payload["charge_state"]["charge"] == 2
        assert payload["fragment_ion_count"] > 0
        assert payload["localization"]["status"] == "advisory"


def test_peptide_mass_command_rejects_invalid_modification_assignment() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(
            cli,
            [
                "peptide-mass",
                "PEPTIDE",
                "--mod",
                "Phospho@1",
            ],
        )

        assert result.exit_code != 0
        assert "not valid on residue" in result.output


def test_isotope_envelope_command_reports_formula_charge_and_tsv() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(
            cli,
            [
                "isotope-envelope",
                "PEPTIDE",
                "--charge",
                "2",
                "--charge",
                "3",
                "--tsv-out",
                "isotopes.tsv",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["canonical_notation"] == "PEPTIDE"
        assert payload["elemental_composition"]["formula"] == "C34H53N7O15"
        assert payload["charges"] == [2, 3]
        assert payload["max_isotope_index"] == 5
        assert len(payload["envelopes"]) == 2
        assert len(payload["envelopes"][0]["peaks"]) == 6
        assert Path("isotopes.tsv").exists()
        assert (
            "canonical_notation\tcharge\tformula\tisotope_index\tmz\tprobability"
            in Path("isotopes.tsv").read_text()
        )


def test_fragment_ions_command_reports_a_b_y_ions_with_charge_spans_and_tsv() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(
            cli,
            [
                "fragment-ions",
                "PESMTIDE",
                "--mod",
                "Phospho@3",
                "--charge",
                "1",
                "--charge",
                "2",
                "--charge",
                "3",
                "--include-neutral-losses",
                "--tsv-out",
                "fragments.tsv",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["counts_by_series"]["a"] > 0
        assert payload["counts_by_series"]["b"] > 0
        assert payload["counts_by_series"]["y"] > 0
        assert payload["counts_by_charge"]["1"] > 0
        assert payload["counts_by_charge"]["2"] > 0
        assert payload["counts_by_charge"]["3"] > 0
        assert payload["neutral_loss_count"] > 0
        assert any(
            ion["series"] == "a" and ion["span_start"] == 1 and ion["span_end"] == 3
            for ion in payload["ions"]
        )
        assert Path("fragments.tsv").exists()
        assert "series\tordinal\tcharge\tspan_start\tspan_end\tsequence" in Path(
            "fragments.tsv"
        ).read_text()


def test_peptide_properties_command_reports_filtering_metrics() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(
            cli,
            [
                "peptide-properties",
                "LVVVVVVIKAKK",
                "--charge",
                "3",
                "--protease",
                "trypsin",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["charge"] == 3
        assert payload["protease"] == "trypsin"
        assert payload["length"] == 12
        assert payload["missed_cleavages"] == 2
        assert payload["flagged_problematic"] is True
        assert "high_hydrophobicity_proxy" in payload["problem_flags"]
        assert "high_missed_cleavages" in payload["problem_flags"]


def test_peptide_properties_command_supports_modifications_and_custom_protease() -> (
    None
):
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(
            cli,
            [
                "peptide-properties",
                "MPEPTIDE",
                "--mod",
                "Oxidation@1",
                "--custom-protease",
                "before=D;block_previous=P",
                "--custom-protease-name",
                "acidic",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["canonical_notation"] == "M[Oxidation]PEPTIDE"
        assert payload["protease"] == "acidic"
        assert payload["custom_protease"] == "before=D;block_previous=P"


def test_peptide_detectability_command_reports_score_tier_and_tsv() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(
            cli,
            [
                "peptide-detectability",
                "AKTIDEK",
                "--charge",
                "2",
                "--protease",
                "trypsin",
                "--uniqueness-class",
                "unique",
                "--observed-psm-count",
                "5",
                "--tsv-out",
                "detectability.tsv",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["detectability_tier"] == "high"
        assert payload["top_tier_length_mass_eligible"] is True
        assert payload["custom_protease"] is None
        assert Path("detectability.tsv").exists()
        assert "detectability_score" in Path("detectability.tsv").read_text()


def test_precursor_mass_error_command_reports_summary_and_exports() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        Path("precursors.tsv").write_text(
            "\n".join(
                (
                    "spectrum_id\tpeptide\tobserved_mz\tcharge",
                    "scan=1\tPEPTIDE\t400.0\t2",
                    "scan=2\tPEPM[Oxidation]IDE\t500.0\t2",
                )
            )
            + "\n",
            encoding="utf-8",
        )

        result = runner.invoke(
            cli,
            [
                "precursor-mass-error",
                "precursors.tsv",
                "--summary-tsv-out",
                "summary.tsv",
                "--observations-tsv-out",
                "observations.tsv",
                "--ppm-distribution-tsv-out",
                "ppm.tsv",
                "--charge-distribution-tsv-out",
                "charge.tsv",
                "--isotope-distribution-tsv-out",
                "isotope.tsv",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["observation_count"] == 2
        assert payload["input_row_count"] == 2
        assert len(payload["observations"]) == 2
        assert Path("summary.tsv").exists()
        assert Path("observations.tsv").exists()
        assert Path("ppm.tsv").exists()
        assert Path("charge.tsv").exists()
        assert Path("isotope.tsv").exists()


def test_modified_peptide_parse_command_normalizes_engine_dialects() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(
            cli,
            [
                "modified-peptide-parse",
                "_(Acetyl (Protein N-term))M(Oxidation (M))PEPTIDE_",
                "--dialect",
                "maxquant",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["dialect"] == "maxquant"
        assert payload["residue_sequence"] == "MPEPTIDE"
        assert (
            payload["canonical_notation"]
            == "[Acetyl@protein-n-term]-M[Oxidation]PEPTIDE"
        )
        assert payload["at_protein_n_term"] is True


def test_modified_peptide_parse_command_distinguishes_lysine_acetylation() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(
            cli,
            [
                "modified-peptide-parse",
                "_PEPK(Acetyl (K))IDE_",
                "--dialect",
                "maxquant",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["dialect"] == "maxquant"
        assert payload["canonical_notation"] == "PEPK[AcetylLys]IDE"
        assert payload["modified_peptide_record"]["modification_names"] == [
            "AcetylLys"
        ]


def test_modified_peptide_parse_command_rejects_malformed_engine_notation() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(
            cli,
            [
                "modified-peptide-parse",
                "M[15.994915PEPTIDE",
                "--dialect",
                "comet",
            ],
        )

        assert result.exit_code != 0
        assert "unterminated bracket modification token" in result.output


def test_modification_resolve_command_reports_builtin_and_unknown_tokens() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        resolved = runner.invoke(
            cli,
            [
                "modification-resolve",
                "deamidation",
                "--residue",
                "N",
            ],
        )
        unknown = runner.invoke(
            cli,
            [
                "modification-resolve",
                "NoSuchModification",
                "--residue",
                "M",
            ],
        )

        assert resolved.exit_code == 0
        resolved_payload = json.loads(resolved.output)
        assert resolved_payload["resolved"] is True
        assert resolved_payload["modification_name"] == "Deamidated"
        assert resolved_payload["controlled_id"] == "UNIMOD:7"
        assert resolved_payload["source"] == "builtin"
        assert resolved_payload["residue_allowed"] is True

        assert unknown.exit_code == 0
        unknown_payload = json.loads(unknown.output)
        assert unknown_payload["resolved"] is False
        assert unknown_payload["source"] == "unknown"
        assert unknown_payload["issues"]


def test_modification_resolve_command_supports_custom_registry() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        Path("registry.json").write_text(
            json.dumps(
                {
                    "document_schema": {
                        "created_by": "bijux-proteomics-core-tests",
                        "document_kind": "peptide_modification_registry",
                        "package_name": "bijux-proteomics-core",
                        "schema_version": "1.0.0",
                        "status": "generated",
                    },
                    "static_modifications": [],
                    "variable_modifications": [
                        {
                            "application": "variable",
                            "controlled_id": "CUSTOM:LYSTAG",
                            "mass_delta_average": 114.1,
                            "mass_delta_monoisotopic": 114.042927,
                            "max_occurrences": 1,
                            "name": "LysTag",
                            "neutral_losses": [],
                            "position": "anywhere",
                            "residues": ["K"],
                        }
                    ],
                }
            )
        )

        result = runner.invoke(
            cli,
            [
                "modification-resolve",
                "CUSTOM:LYSTAG",
                "--residue",
                "K",
                "--registry",
                "registry.json",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["resolved"] is True
        assert payload["source"] == "registry"
        assert payload["modification_name"] == "LysTag"
        assert payload["controlled_id"] == "CUSTOM:LYSTAG"
        assert payload["residue_allowed"] is True


def test_psm_inspect_command_reports_summaries_and_writes_exports() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        source = FIXTURE_ROOT / "psm" / "representative_results.tsv"
        shutil.copy(source, "results.tsv")

        result = runner.invoke(
            cli,
            [
                "psm-inspect",
                "results.tsv",
                "--jsonl-out",
                "normalized.jsonl",
                "--tsv-out",
                "normalized.tsv",
                "--provenance-out",
                "provenance.json",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["accepted_rows"] == 3
        assert payload["psm_summary"]["decoy_psms"] == 1
        assert payload["inspection"]["accepted_rows"] == 3
        assert payload["inspection"]["rejected_rows"] == 0
        assert Path("normalized.jsonl").exists()
        assert Path("normalized.tsv").exists()
        manifest = json.loads(Path("provenance.json").read_text())
        assert (
            manifest["document_schema"]["document_kind"]
            == "search_result_provenance_manifest"
        )


def test_psm_inspect_command_supports_canonical_schema_columns() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        fixture_dir = FIXTURE_ROOT / "search_adapters"
        shutil.copy(
            fixture_dir / "generic_mapper_results.tsv",
            "generic_mapper_results.tsv",
        )

        result = runner.invoke(
            cli,
            [
                "psm-inspect",
                "generic_mapper_results.tsv",
                "--run-id-column",
                "run_name",
                "--spectrum-id-column",
                "scan_ref",
                "--peptide-column",
                "sequence_text",
                "--modified-peptide-column",
                "modified_sequence",
                "--charge-column",
                "z",
                "--score-column",
                "state_score",
                "--q-value-column",
                "qvalue",
                "--protein-refs-column",
                "accessions",
                "--decoy-label-column",
                "decoy_state",
                "--contaminant-label-column",
                "contaminant_state",
                "--tsv-out",
                "normalized.tsv",
            ],
        )

        assert result.exit_code == 0
        normalized_tsv = Path("normalized.tsv").read_text(encoding="utf-8")
        assert "run_id" in normalized_tsv
        assert "peptide_sequence" in normalized_tsv
        assert "modified_peptide" in normalized_tsv
        assert "contaminant_flag" in normalized_tsv
        assert "PES[Phospho]TIDE" in normalized_tsv


def test_psm_inspect_command_reports_quality_distributions_and_writes_ledgers() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        Path("inspection.tsv").write_text(
            "\n".join(
                (
                    "spectrum_id\tpeptide\tcharge\tscore\tq_value\tproteins",
                    "scan=1001\tPEPTIDE\t2\t55.0\t0.005\tP12345",
                    "scan=1002\tAKTIDEK\t3\t44.0\t0.02\tP12345",
                    "scan=1003\tLVVVVVVIKAKK\t2\t31.0\t0.08\tP12345",
                    "scan=1004\tPEPTIDER\tbad\t20.0\t0.2\tP12345",
                )
            )
            + "\n",
            encoding="utf-8",
        )

        result = runner.invoke(
            cli,
            [
                "psm-inspect",
                "inspection.tsv",
                "--summary-tsv-out",
                "inspection.summary.tsv",
                "--score-distribution-tsv-out",
                "inspection.score.tsv",
                "--q-value-distribution-tsv-out",
                "inspection.qvalue.tsv",
                "--charge-distribution-tsv-out",
                "inspection.charge.tsv",
                "--peptide-length-distribution-tsv-out",
                "inspection.length.tsv",
                "--missed-cleavage-distribution-tsv-out",
                "inspection.missed.tsv",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["inspection"]["total_rows"] == 4
        assert payload["inspection"]["accepted_rows"] == 3
        assert payload["inspection"]["rejected_rows"] == 1
        assert payload["inspection"]["protease"] == "trypsin"
        assert Path("inspection.summary.tsv").exists()
        assert Path("inspection.score.tsv").exists()
        assert Path("inspection.qvalue.tsv").exists()
        assert Path("inspection.charge.tsv").exists()
        assert Path("inspection.length.tsv").exists()
        assert Path("inspection.missed.tsv").exists()
        assert "0\t1" in Path("inspection.missed.tsv").read_text(encoding="utf-8")
        assert "1\t1" in Path("inspection.missed.tsv").read_text(encoding="utf-8")
        assert "2\t1" in Path("inspection.missed.tsv").read_text(encoding="utf-8")


def test_fdr_command_filters_by_threshold_and_writes_provenance() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        source = FIXTURE_ROOT / "psm" / "fdr_results.tsv"
        shutil.copy(source, "fdr.tsv")

        result = runner.invoke(
            cli,
            [
                "fdr",
                "fdr.tsv",
                "--threshold",
                "0.5",
                "--jsonl-out",
                "accepted.jsonl",
                "--provenance-out",
                "fdr.provenance.json",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["threshold"] == 0.5
        assert payload["accepted_psms"] == 3
        assert Path("accepted.jsonl").exists()
        manifest = json.loads(Path("fdr.provenance.json").read_text())
        assert manifest["fdr_policy"]["threshold"] == 0.5


def test_fdr_command_writes_ranked_summary_and_entry_ledgers() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        source = FIXTURE_ROOT / "psm" / "fdr_results.tsv"
        shutil.copy(source, "fdr.tsv")

        result = runner.invoke(
            cli,
            [
                "fdr",
                "fdr.tsv",
                "--threshold",
                "0.5",
                "--summary-tsv-out",
                "fdr.summary.tsv",
                "--entries-tsv-out",
                "fdr.entries.tsv",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["fdr_report"]["total_psm_count"] == 5
        assert payload["fdr_report"]["accepted_psm_count"] == 3
        assert payload["score_separation"]["summary"]["warning_tier"] == "unstable"
        assert payload["fdr_unstable"] is True
        assert payload["fdr_reproducibility_hash"]
        assert Path("fdr.summary.tsv").exists()
        assert Path("fdr.entries.tsv").exists()
        summary_tsv = Path("fdr.summary.tsv").read_text(encoding="utf-8")
        entries_tsv = Path("fdr.entries.tsv").read_text(encoding="utf-8")
        assert summary_tsv.startswith(
            "score_orientation\ttie_handling\tthreshold\ttotal_psm_count"
        )
        assert "reproducibility_hash" in summary_tsv
        assert entries_tsv.startswith(
            "rank\ttie_group_rank\ttie_group_size\tspectrum_id\tcanonical_peptide"
        )
        assert "\t0.5\ttrue\n" in entries_tsv


def test_fdr_command_marks_unstable_score_separation_and_writes_ledgers() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        source = FIXTURE_ROOT / "psm" / "fdr_unstable_results.tsv"
        shutil.copy(source, "fdr.tsv")

        result = runner.invoke(
            cli,
            [
                "fdr",
                "fdr.tsv",
                "--threshold",
                "0.5",
                "--score-separation-summary-tsv-out",
                "score_separation.summary.tsv",
                "--score-separation-bins-tsv-out",
                "score_separation.bins.tsv",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["fdr_unstable"] is True
        assert payload["score_separation"]["summary"]["warning_tier"] == "unstable"
        assert payload["score_separation"]["summary"]["overlap_metric"] == 0.75
        assert Path("score_separation.summary.tsv").exists()
        assert Path("score_separation.bins.tsv").exists()
        assert "warning_tier\tfdr_unstable" in Path(
            "score_separation.summary.tsv"
        ).read_text(encoding="utf-8")
        assert Path("score_separation.bins.tsv").read_text(
            encoding="utf-8"
        ).startswith(
            "bin_lower\tbin_upper\ttarget_count\tdecoy_count\tmixed_count\tunknown_count"
        )


def test_fdr_command_preserves_imported_pep_and_writes_error_rate_ledgers() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        shutil.copy(FIXTURE_ROOT / "psm" / "pep_results.tsv", "pep_results.tsv")

        result = runner.invoke(
            cli,
            [
                "fdr",
                "pep_results.tsv",
                "--threshold",
                "0.5",
                "--pep-column",
                "pep",
                "--error-rate-summary-tsv-out",
                "error_rate.summary.tsv",
                "--error-rate-entries-tsv-out",
                "error_rate.entries.tsv",
                "--tsv-out",
                "accepted.tsv",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["error_rate_annotation"]["summary"]["imported_pep_count"] == 3
        assert payload["error_rate_annotation"]["summary"]["computed_local_fdr_count"] == 0
        assert Path("error_rate.summary.tsv").exists()
        assert Path("error_rate.entries.tsv").exists()
        assert "imported_pep_count\tcomputed_local_fdr_count" in Path(
            "error_rate.summary.tsv"
        ).read_text(encoding="utf-8")
        entries_text = Path("error_rate.entries.tsv").read_text(encoding="utf-8")
        accepted_text = Path("accepted.tsv").read_text(encoding="utf-8")
        assert "posterior_error_probability\tlocal_fdr\terror_rate_provenance" in entries_text
        assert "\t0.002\t\timported_pep\n" in entries_text
        assert "posterior_error_probability\tlocal_fdr\terror_rate_provenance" in accepted_text
        assert "\t0.008\t\timported_pep\tQ11111" in accepted_text


def test_fdr_command_computes_local_fdr_when_pep_is_absent() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        shutil.copy(FIXTURE_ROOT / "psm" / "fdr_results.tsv", "fdr.tsv")

        result = runner.invoke(
            cli,
            [
                "fdr",
                "fdr.tsv",
                "--threshold",
                "0.5",
                "--error-rate-summary-tsv-out",
                "error_rate.summary.tsv",
                "--error-rate-entries-tsv-out",
                "error_rate.entries.tsv",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["error_rate_annotation"]["summary"]["imported_pep_count"] == 0
        assert payload["error_rate_annotation"]["summary"]["computed_local_fdr_count"] == 5
        entries_text = Path("error_rate.entries.tsv").read_text(encoding="utf-8")
        assert "\t\t1.0\tcomputed_local_fdr\n" in entries_text


def test_fdr_reference_check_command_writes_summary_and_entry_ledgers() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        shutil.copy(
            FIXTURE_ROOT / "identification" / "target_decoy_reference_cases.json",
            "reference_cases.json",
        )

        result = runner.invoke(
            cli,
            [
                "fdr-reference-check",
                "reference_cases.json",
                "--summary-tsv-out",
                "reference.summary.tsv",
                "--entries-tsv-out",
                "reference.entries.tsv",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["valid"] is True
        assert payload["case_count"] == 2
        assert payload["failed_entry_count"] == 0
        assert Path("reference.summary.tsv").exists()
        assert Path("reference.entries.tsv").exists()
        assert "concatenated_higher_better_reference" in Path(
            "reference.summary.tsv"
        ).read_text(encoding="utf-8")
        assert "scan=5005" in Path("reference.entries.tsv").read_text(encoding="utf-8")


def test_fdr_levels_command_reports_threshold_counts_and_contaminants() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        Path("levels.tsv").write_text(
            "\n".join(
                (
                    "spectrum_id\tpeptide\tcharge\tscore\tproteins",
                    "scan=1001\tPEPTIDE\t2\t100.0\tP11111",
                    "scan=1002\tAKTIDEK\t2\t95.0\tCON__KERATIN_HUMAN",
                    "scan=1003\tDECOYPEP\t2\t90.0\tDECOY_P99999",
                )
            )
            + "\n",
            encoding="utf-8",
        )

        result = runner.invoke(
            cli,
            [
                "fdr-levels",
                "levels.tsv",
                "--summary-tsv-out",
                "levels.summary.tsv",
                "--entries-tsv-out",
                "levels.entries.tsv",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["thresholds"] == [0.01, 0.05, 0.1]
        assert payload["accepted_rows"] == 3
        summary_rows = payload["summaries"]
        psm_one_percent = next(
            row
            for row in summary_rows
            if row["threshold"] == 0.01 and row["evidence_level"] == "psm"
        )
        assert psm_one_percent["accepted_count"] == 2
        assert psm_one_percent["accepted_contaminant_count"] == 1
        assert psm_one_percent["total_decoy_count"] == 1
        assert Path("levels.summary.tsv").exists()
        assert Path("levels.entries.tsv").exists()
        assert "0.01\tpsm\t3\t2\t1\t0\t0\t1\t2\t2\t0\t0\t0\t1" in Path(
            "levels.summary.tsv"
        ).read_text(encoding="utf-8")
        assert "0.05\tprotein\tCON__KERATIN_HUMAN" in Path(
            "levels.entries.tsv"
        ).read_text(encoding="utf-8")


def test_picked_protein_fdr_command_reports_pairs_groups_and_ledgers() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        shutil.copy(
            FIXTURE_ROOT / "psm" / "grouped_picked_fdr_edge_cases.tsv",
            "picked.tsv",
        )

        result = runner.invoke(
            cli,
            [
                "picked-protein-fdr",
                "picked.tsv",
                "--summary-tsv-out",
                "picked.summary.tsv",
                "--entries-tsv-out",
                "picked.entries.tsv",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["thresholds"] == [0.01, 0.05, 0.1]
        assert payload["accepted_rows"] == 10
        summary_rows = payload["summaries"]
        threshold_tenth = next(row for row in summary_rows if row["threshold"] == 0.1)
        assert threshold_tenth["total_count"] == 5
        assert threshold_tenth["grouped_protein_count"] == 2
        assert threshold_tenth["accepted_count"] == 4
        entries = payload["entries"]
        picked_p22222 = next(row for row in entries if row["protein_ref"] == "P22222")
        assert picked_p22222["pair_id"] == "picked:P22222"
        assert picked_p22222["target_ref"] == "P22222"
        assert picked_p22222["decoy_ref"] == "DECOY_P22222"
        assert picked_p22222["partner_ref"] == "DECOY_P22222"
        assert picked_p22222["protein_group_ids"]
        assert Path("picked.summary.tsv").exists()
        assert Path("picked.entries.tsv").exists()
        assert "0.1\t5\t4\t1\t0\t2\t4\t4\t0\t0\t2" in Path(
            "picked.summary.tsv"
        ).read_text(encoding="utf-8")
        assert (
            "picked:P22222\tP22222\tP22222\tDECOY_P22222\tP22222\tDECOY_P22222"
            in Path("picked.entries.tsv").read_text(encoding="utf-8")
        )


def test_protein_groups_command_reports_leading_proteins_and_group_table() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        shutil.copy(
            FIXTURE_ROOT / "psm" / "protein_inference_results.tsv",
            "protein_inference_results.tsv",
        )

        result = runner.invoke(
            cli,
            [
                "protein-groups",
                "protein_inference_results.tsv",
                "--threshold",
                "0.05",
                "--summary-tsv-out",
                "protein_groups.summary.tsv",
                "--group-tsv-out",
                "protein_groups.tsv",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["threshold"] == 0.05
        assert payload["grouped_rows"] == 4
        assert payload["summary"]["total_groups"] == 3
        assert payload["summary"]["ambiguous_group_count"] == 1
        ambiguous = next(
            entry
            for entry in payload["groups"]
            if entry["protein_refs"] == ["P22222", "P44444"]
        )
        assert ambiguous["leading_protein"] == "P22222"
        assert ambiguous["leading_rationale"] == "lexicographic_tiebreak"
        assert ambiguous["shared_peptides"] == ["GLYGLYK", "SHAREDK"]
        assert Path("protein_groups.summary.tsv").exists()
        assert Path("protein_groups.tsv").exists()
        assert "ambiguous_group_count\t1" in Path(
            "protein_groups.summary.tsv"
        ).read_text(encoding="utf-8")
        assert (
            "P22222\tlexicographic_tiebreak\tP22222;P44444\tGLYGLYK;SHAREDK\t\tGLYGLYK;SHAREDK"
            in Path("protein_groups.tsv").read_text(encoding="utf-8")
        )


def test_protein_ambiguity_command_reports_ambiguous_groups_and_ledgers() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        shutil.copy(
            FIXTURE_ROOT / "psm" / "protein_ambiguity_cases.tsv",
            "protein_ambiguity_cases.tsv",
        )

        result = runner.invoke(
            cli,
            [
                "protein-ambiguity",
                "protein_ambiguity_cases.tsv",
                "--threshold",
                "0.05",
                "--summary-tsv-out",
                "protein_ambiguity.summary.tsv",
                "--ambiguity-tsv-out",
                "protein_ambiguity.tsv",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["threshold"] == 0.05
        assert payload["accepted_rows"] == 4
        assert payload["grouped_rows"] == 4
        assert payload["ambiguity_rows"] == 3
        assert payload["summary"]["total_ambiguity_groups"] == 3
        assert payload["summary"]["indistinguishable_group_count"] == 1
        mixed = next(
            entry
            for entry in payload["entries"]
            if entry["protein_refs"] == ["P10001", "P20002"]
        )
        assert mixed["ambiguity_reason"] == "mixed"
        assert mixed["outside_group_proteins"] == ["P30003"]
        external = next(
            entry for entry in payload["entries"] if entry["protein_refs"] == ["P30003"]
        )
        assert external["ambiguity_reason"] == "external_shared_peptides"
        assert external["unique_peptides"] == ["UNIQUEB"]
        assert Path("protein_ambiguity.summary.tsv").exists()
        assert Path("protein_ambiguity.tsv").exists()
        assert "total_ambiguity_groups\t3" in Path(
            "protein_ambiguity.summary.tsv"
        ).read_text(encoding="utf-8")
        assert (
            "P10001\tP10001;P20002\tP10001;P20002\tSHAREDX;SHAREDY\t\tP30003\tmixed"
            in Path("protein_ambiguity.tsv").read_text(encoding="utf-8")
        )


def test_protein_inference_benchmarks_command_emits_catalog_and_ledgers() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(
            cli,
            [
                "protein-inference-benchmarks",
                "--picked-threshold",
                "0.05",
                "--summary-tsv-out",
                "protein_inference_benchmarks.summary.tsv",
                "--scenarios-tsv-out",
                "protein_inference_benchmarks.scenarios.tsv",
                "--assessments-tsv-out",
                "protein_inference_benchmarks.assessments.tsv",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["picked_threshold"] == 0.05
        assert payload["scenario_count"] == 8
        assert payload["homolog_family_scenario_count"] == 1
        assert payload["contaminant_scenario_count"] == 1
        assert payload["all_decoy_scenario_count"] == 1
        assert payload["all_target_scenario_count"] == 1
        assert payload["tied_score_scenario_count"] == 1
        assert payload["missing_fasta_scenario_count"] == 1
        assert payload["hidden_ambiguity_scenario_count"] == 0
        assert payload["reports"][0]["method_assessments"]
        assert Path("protein_inference_benchmarks.summary.tsv").exists()
        assert Path("protein_inference_benchmarks.scenarios.tsv").exists()
        assert Path("protein_inference_benchmarks.assessments.tsv").exists()
        assert "homolog_family_scenario_count\t1" in Path(
            "protein_inference_benchmarks.summary.tsv"
        ).read_text(encoding="utf-8")
        assert "tied-score-ambiguity" in Path(
            "protein_inference_benchmarks.scenarios.tsv"
        ).read_text(encoding="utf-8")
        assert "selected_missing_fasta_proteins" in Path(
            "protein_inference_benchmarks.assessments.tsv"
        ).read_text(encoding="utf-8")


def test_protein_coverage_command_reports_regions_and_shared_peptides() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        psm_fixture_dir = FIXTURE_ROOT / "psm"
        fasta_fixture_dir = FIXTURE_ROOT / "fasta"
        shutil.copy(
            psm_fixture_dir / "protein_inference_results.tsv",
            "protein_inference_results.tsv",
        )
        shutil.copy(
            fasta_fixture_dir / "protein_inference.fasta",
            "protein_inference.fasta",
        )

        result = runner.invoke(
            cli,
            [
                "protein-coverage",
                "protein_inference_results.tsv",
                "--fasta",
                "protein_inference.fasta",
                "--threshold",
                "0.05",
                "--summary-tsv-out",
                "protein_coverage.summary.tsv",
                "--coverage-tsv-out",
                "protein_coverage.tsv",
                "--regions-tsv-out",
                "protein_coverage.regions.tsv",
                "--uncovered-tsv-out",
                "protein_coverage.uncovered.tsv",
                "--peptide-coordinate-tsv-out",
                "protein_coverage.coordinates.tsv",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["accepted_rows"] == 4
        assert payload["summary"]["total_proteins"] == 4
        assert payload["summary"]["proteins_with_shared_peptides"] == 3
        p11111 = next(
            entry for entry in payload["entries"] if entry["protein_ref"] == "P11111"
        )
        assert p11111["covered_ranges"] == [[2, 9], [13, 19]]
        assert p11111["uncovered_ranges"] == [[1, 1], [10, 12], [20, 21]]
        assert p11111["unique_peptides"] == ["PEPTIDEK"]
        assert p11111["shared_peptides"] == ["SHAREDK"]
        assert payload["regions"][0]["protein_ref"] == "P11111"
        assert payload["uncovered_regions"][0]["protein_ref"] == "P11111"
        assert payload["peptide_coordinates"][0]["protein_ref"] == "P11111"
        assert Path("protein_coverage.summary.tsv").exists()
        assert Path("protein_coverage.tsv").exists()
        assert Path("protein_coverage.regions.tsv").exists()
        assert Path("protein_coverage.uncovered.tsv").exists()
        assert Path("protein_coverage.coordinates.tsv").exists()
        assert "proteins_with_shared_peptides\t3" in Path(
            "protein_coverage.summary.tsv"
        ).read_text(encoding="utf-8")
        assert "P11111\t21\t15\t0.7142857142857143\t2-9;13-19" in Path(
            "protein_coverage.tsv"
        ).read_text(encoding="utf-8")
        assert "P11111\t2\t13\t19\t7" in Path("protein_coverage.regions.tsv").read_text(
            encoding="utf-8"
        )
        assert "P11111\t1\t1\t1\t1" in Path(
            "protein_coverage.uncovered.tsv"
        ).read_text(encoding="utf-8")
        assert "P11111\tPEPTIDEK\tPEPTIDEK\tmatched\t1\t2\t9" in Path(
            "protein_coverage.coordinates.tsv"
        ).read_text(encoding="utf-8")


def test_protein_coverage_plot_command_emits_positions_svg_and_html() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        Path("protein_plot.tsv").write_text(
            "\n".join(
                (
                    "spectrum_id\tpeptide\tmodified_peptide\tcharge\tscore\tintensity\tq_value\tproteins",
                    "scan=1\tPEPTIDEK\tPEPTIDEK\t2\t90.0\t1000\t0.005\tP11111",
                    "scan=2\tACDMK\tACDM[Oxidation]K\t2\t70.0\t500\t0.02\tP11111;P22222",
                )
            )
            + "\n",
            encoding="utf-8",
        )
        Path("protein_plot.fasta").write_text(
            "\n".join(
                (
                    ">sp|P11111|PROT1 Example protein 1 OS=Homo sapiens GN=PROT1",
                    "MPEPTIDEKAAACDMKGG",
                    ">sp|P22222|PROT2 Example protein 2 OS=Homo sapiens GN=PROT2",
                    "QQACDMKRR",
                )
            )
            + "\n",
            encoding="utf-8",
        )

        result = runner.invoke(
            cli,
            [
                "protein-coverage-plot",
                "protein_plot.tsv",
                "--fasta",
                "protein_plot.fasta",
                "--modified-peptide-column",
                "modified_peptide",
                "--intensity-column",
                "intensity",
                "--positions-tsv-out",
                "protein_plot.positions.tsv",
                "--svg-out",
                "protein_plot.svg",
                "--html-out",
                "protein_plot.html",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["accepted_rows"] == 2
        assert payload["summary"]["total_position_rows"] == 3
        assert payload["summary"]["modified_position_count"] == 2
        assert payload["summary"]["intensity_position_count"] == 3
        modified = next(
            entry
            for track in payload["tracks"]
            for entry in track["positions"]
            if entry["canonical_peptide"] == "ACDM[Oxidation]K"
            and entry["protein_ref"] == "P11111"
        )
        assert modified["start_residue"] == 12
        assert modified["end_residue"] == 16
        assert modified["confidence_label"] == "medium"
        assert modified["peptide_q_value"] == 0.02
        assert modified["best_intensity"] == 500.0
        assert Path("protein_plot.positions.tsv").exists()
        assert Path("protein_plot.svg").read_text(encoding="utf-8").startswith("<svg")
        assert (
            Path("protein_plot.html").read_text(encoding="utf-8").startswith("<html>")
        )
        assert "ACDM[Oxidation]K" in Path("protein_plot.positions.tsv").read_text(
            encoding="utf-8"
        )


def test_protein_parsimony_command_reports_selected_set_and_ambiguities() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        shutil.copy(
            FIXTURE_ROOT / "psm" / "protein_parsimony_variants.tsv",
            "protein_parsimony_variants.tsv",
        )

        result = runner.invoke(
            cli,
            [
                "protein-parsimony",
                "protein_parsimony_variants.tsv",
                "--threshold",
                "0.05",
                "--variant",
                "greedy_coverage",
                "--review-variant",
                "greedy_coverage",
                "--review-variant",
                "unique_evidence_priority",
                "--summary-tsv-out",
                "protein_parsimony.summary.tsv",
                "--protein-tsv-out",
                "protein_parsimony.proteins.tsv",
                "--ambiguity-tsv-out",
                "protein_parsimony.ambiguities.tsv",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["summary"]["variant"] == "greedy_coverage"
        assert payload["summary"]["selected_protein_count"] == 2
        assert payload["summary"]["unresolved_ambiguity_count"] == 2
        assert payload["unexplained_peptides"] == []
        assert payload["selected_proteins"][0]["protein_ref"] == "P10001"
        assert payload["selected_proteins"][1]["protein_ref"] == "P20002"
        bravoq = next(
            entry
            for entry in payload["unresolved_ambiguities"]
            if entry["subject_id"] == "BRAVOK"
        )
        assert bravoq["candidate_proteins"] == ["P10001", "P20002"]
        assert Path("protein_parsimony.summary.tsv").exists()
        assert Path("protein_parsimony.proteins.tsv").exists()
        assert Path("protein_parsimony.ambiguities.tsv").exists()
        assert "selected_protein_count\t2" in Path(
            "protein_parsimony.summary.tsv"
        ).read_text(encoding="utf-8")
        assert (
            "greedy_coverage\t1\tP10001\tpg-001\tP10001\tALPHAK;BRAVOK;CHARLIEK;DELTAK"
            in Path("protein_parsimony.proteins.tsv").read_text(encoding="utf-8")
        )
        assert "BRAVOK\tpeptide_assignment\tP10001;P20002" in Path(
            "protein_parsimony.ambiguities.tsv"
        ).read_text(encoding="utf-8")


def test_peptide_evidence_command_reports_classes_and_tags() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        shutil.copy(
            FIXTURE_ROOT / "psm" / "peptide_evidence_classes.tsv",
            "peptide_evidence_classes.tsv",
        )

        result = runner.invoke(
            cli,
            [
                "peptide-evidence",
                "peptide_evidence_classes.tsv",
                "--threshold",
                "0.05",
                "--strong-q-value",
                "0.01",
                "--summary-tsv-out",
                "peptide_evidence.summary.tsv",
                "--entries-tsv-out",
                "peptide_evidence.entries.tsv",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["summary"]["total_peptides"] == 8
        assert payload["summary"]["strong_count"] == 1
        assert payload["summary"]["moderate_count"] == 1
        assert payload["summary"]["weak_count"] == 2
        assert payload["summary"]["shared_count"] == 1
        assert payload["summary"]["ambiguous_count"] == 1
        assert payload["summary"]["modified_count"] == 1
        assert payload["summary"]["contaminant_count"] == 1
        assert payload["summary"]["decoy_count"] == 1
        by_peptide = {entry["canonical_peptide"]: entry for entry in payload["entries"]}
        assert by_peptide["STRONGK"]["primary_class"] == "strong"
        assert by_peptide["SHAREDFINEK"]["primary_class"] == "shared"
        assert by_peptide["SHAREDK"]["primary_class"] == "weak"
        assert "shared" in by_peptide["SHAREDK"]["tags"]
        assert "modified" in by_peptide["ACDM[Oxidation]K"]["tags"]
        assert by_peptide["AMBIGK"]["primary_class"] == "ambiguous"
        assert by_peptide["CONTAMK"]["primary_class"] == "contaminant"
        assert by_peptide["DECOYSEQ"]["primary_class"] == "decoy"
        assert Path("peptide_evidence.summary.tsv").exists()
        assert Path("peptide_evidence.entries.tsv").exists()
        assert "strong_count\t1" in Path("peptide_evidence.summary.tsv").read_text(
            encoding="utf-8"
        )
        assert "CONTAMK\tCONTAMK\tcontaminant\tunique;contaminant" in Path(
            "peptide_evidence.entries.tsv"
        ).read_text(encoding="utf-8")


def test_protein_evidence_command_reports_tiers_and_downgrade_reasons() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        shutil.copy(
            FIXTURE_ROOT / "psm" / "protein_evidence_cases.tsv",
            "protein_evidence_cases.tsv",
        )
        shutil.copy(
            FIXTURE_ROOT / "formats" / "protein_evidence.design.tsv",
            "protein_evidence.design.tsv",
        )

        result = runner.invoke(
            cli,
            [
                "protein-evidence",
                "protein_evidence_cases.tsv",
                "--design-tsv",
                "protein_evidence.design.tsv",
                "--run-id-column",
                "run_id",
                "--summary-tsv-out",
                "protein_evidence.summary.tsv",
                "--entries-tsv-out",
                "protein_evidence.entries.tsv",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["summary"]["total_groups"] == 6
        assert payload["summary"]["high_confidence_count"] == 1
        assert payload["summary"]["moderate_count"] == 1
        assert payload["summary"]["weak_count"] == 1
        assert payload["summary"]["ambiguous_count"] == 1
        assert payload["summary"]["contaminant_count"] == 1
        assert payload["summary"]["decoy_count"] == 1
        by_protein = {
            entry["representative_protein"]: entry for entry in payload["entries"]
        }
        assert by_protein["P11111"]["evidence_tier"] == "high_confidence"
        assert by_protein["P22222"]["evidence_tier"] == "moderate"
        assert by_protein["P22222"]["downgrade_reasons"] == ["single_run_only"]
        assert by_protein["P33333"]["evidence_tier"] == "ambiguous"
        assert by_protein["P33333"]["downgrade_reasons"] == ["shared_peptide_only"]
        assert by_protein["P66666"]["evidence_tier"] == "weak"
        assert Path("protein_evidence.summary.tsv").exists()
        assert Path("protein_evidence.entries.tsv").exists()
        assert "shared_peptide_only_count\t1" in Path(
            "protein_evidence.summary.tsv"
        ).read_text(encoding="utf-8")
        assert "\tambiguous\tshared_peptide_only\t" in Path(
            "protein_evidence.entries.tsv"
        ).read_text(encoding="utf-8")


def test_cross_run_reproducibility_command_reports_detection_consistency() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        shutil.copy(
            FIXTURE_ROOT / "psm" / "cross_run_reproducibility.tsv",
            "cross_run_reproducibility.tsv",
        )
        shutil.copy(
            FIXTURE_ROOT / "formats" / "cross_run_reproducibility.design.tsv",
            "cross_run_reproducibility.design.tsv",
        )

        result = runner.invoke(
            cli,
            [
                "cross-run-reproducibility",
                "cross_run_reproducibility.tsv",
                "--design-tsv",
                "cross_run_reproducibility.design.tsv",
                "--run-id-column",
                "run_id",
                "--summary-tsv-out",
                "cross_run_reproducibility.summary.tsv",
                "--entries-tsv-out",
                "cross_run_reproducibility.entries.tsv",
                "--exploratory-entity",
                "PEPC",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["summary"]["total_entries"] == 4
        assert payload["summary"]["condition_specific_count"] == 1
        assert payload["summary"]["single_run_only_count"] == 1
        assert payload["summary"]["exploratory_count"] == 1
        by_entity = {entry["entity_id"]: entry for entry in payload["entries"]}
        assert by_entity["PEPA"]["reproducibility_class"] == "condition_specific"
        assert by_entity["PEPB"]["reproducibility_class"] == "single_run_only"
        assert by_entity["PEPC"]["reproducibility_class"] == "exploratory"
        assert by_entity["PEPD"]["reproducibility_class"] == "reproducible"
        assert by_entity["PEPD"]["condition_specificity"] == 0.5
        assert Path("cross_run_reproducibility.summary.tsv").exists()
        assert Path("cross_run_reproducibility.entries.tsv").exists()
        assert "condition_specific_count\t1" in Path(
            "cross_run_reproducibility.summary.tsv"
        ).read_text(encoding="utf-8")
        assert "PEPB\t1\t4\t0.25" in Path(
            "cross_run_reproducibility.entries.tsv"
        ).read_text(encoding="utf-8")


def test_spectrum_stats_command_reports_collection_summary_and_provenance() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        source = FIXTURE_ROOT / "spectra" / "multi.mgf"
        shutil.copy(source, "multi.mgf")

        result = runner.invoke(
            cli,
            [
                "spectrum-stats",
                "multi.mgf",
                "--provenance-out",
                "multi.provenance.json",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["summary"]["spectrum_count"] == 2
        assert payload["metrics"][0]["peak_count"] >= 1
        provenance = json.loads(Path("multi.provenance.json").read_text())
        assert (
            provenance["document_schema"]["document_kind"]
            == "spectrum_provenance_manifest"
        )


def test_spectrum_parse_command_reports_rejections_and_streaming_profile() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        shutil.copy(FIXTURE_ROOT / "spectra" / "malformed.mgf", "malformed.mgf")

        result = runner.invoke(
            cli,
            [
                "spectrum-parse",
                "malformed.mgf",
                "--chunk-size",
                "2",
                "--accepted-jsonl-out",
                "accepted.jsonl",
                "--rejected-json-out",
                "rejected.json",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["parse_report"]["total_blocks"] == 2
        assert len(payload["parse_report"]["accepted_spectra"]) == 0
        assert len(payload["parse_report"]["rejected_blocks"]) == 2
        assert payload["streaming_profile"]["chunk_size"] == 2
        assert payload["streaming_profile"]["spectrum_count"] == 0
        assert Path("accepted.jsonl").exists()
        assert Path("rejected.json").exists()
        assert json.loads(Path("rejected.json").read_text())[0]["issues"]


def test_spectrum_parse_command_exports_accepted_spectra_details() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        shutil.copy(FIXTURE_ROOT / "spectra" / "multi.mgf", "multi.mgf")

        result = runner.invoke(
            cli,
            [
                "spectrum-parse",
                "multi.mgf",
                "--chunk-size",
                "1",
                "--accepted-jsonl-out",
                "accepted.jsonl",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["summary"]["spectrum_count"] == 2
        assert payload["streaming_profile"]["chunk_count"] == 2
        accepted_rows = Path("accepted.jsonl").read_text().strip().splitlines()
        assert len(accepted_rows) == 2
        first_row = json.loads(accepted_rows[0])
        assert first_row["precursor_mz"] > 0.0
        assert first_row["peaks"]


def test_spectrum_summary_command_reports_mgf_tables_and_exports() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        shutil.copy(FIXTURE_ROOT / "spectra" / "multi.mgf", "multi.mgf")

        result = runner.invoke(
            cli,
            [
                "spectrum-summary",
                "multi.mgf",
                "--summary-tsv-out",
                "summary.tsv",
                "--charge-tsv-out",
                "charge.tsv",
                "--precursor-tsv-out",
                "precursor.tsv",
                "--peak-count-tsv-out",
                "peak.tsv",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["source_kind"] == "mgf"
        assert payload["ms_level_policy"] == "mgf_assumed_ms2"
        assert payload["ms2_spectrum_count"] == 2
        assert Path("summary.tsv").exists()
        assert Path("charge.tsv").exists()
        assert Path("precursor.tsv").exists()
        assert Path("peak.tsv").exists()


def test_spectrum_qc_command_reports_mgf_run_qc_and_exports() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        spectra = (
            SpectrumModel(
                spectrum_id="scan=1",
                precursor_mz=500.2,
                precursor_intensity=500.0,
                precursor_charge=2,
                retention_time_seconds=15.0,
                peaks=(
                    SpectrumPeak(mz=100.0, intensity=50.0),
                    SpectrumPeak(mz=150.0, intensity=40.0),
                    SpectrumPeak(mz=200.0, intensity=30.0),
                ),
            ),
            SpectrumModel(
                spectrum_id="scan=2",
                precursor_mz=600.2,
                precursor_intensity=5000.0,
                precursor_charge=3,
                retention_time_seconds=75.0,
                peaks=(SpectrumPeak(mz=250.0, intensity=15.0),),
            ),
        )
        Path("qc.mgf").write_text(render_mgf(spectra), encoding="utf-8")

        result = runner.invoke(
            cli,
            [
                "spectrum-qc",
                "qc.mgf",
                "--summary-tsv-out",
                "summary.tsv",
                "--msms-tsv-out",
                "msms.tsv",
                "--tic-tsv-out",
                "tic.tsv",
                "--bpc-tsv-out",
                "bpc.tsv",
                "--charge-tsv-out",
                "charge.tsv",
                "--precursor-intensity-tsv-out",
                "precursor.tsv",
                "--flagged-tsv-out",
                "flagged.tsv",
                "--spectrum-qc-tsv-out",
                "spectrum_qc.tsv",
                "--plot-out",
                "plot.json",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["source_kind"] == "mgf"
        assert payload["chromatogram_source"] == "spectrum_derived"
        assert payload["precursor_intensity_observation_count"] == 2
        assert payload["noisy_spectrum_count"] == 1
        assert Path("summary.tsv").exists()
        assert Path("msms.tsv").exists()
        assert Path("tic.tsv").exists()
        assert Path("bpc.tsv").exists()
        assert Path("charge.tsv").exists()
        assert Path("precursor.tsv").exists()
        assert Path("flagged.tsv").exists()
        assert Path("spectrum_qc.tsv").exists()
        assert Path("plot.json").exists()
        assert "quality_tier" in Path("spectrum_qc.tsv").read_text()


def test_spectrum_qc_command_prefers_reported_mzml_chromatograms() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        shutil.copy(
            FIXTURE_ROOT / "formats" / "practical_review.mzml",
            "practical_review.mzml",
        )

        result = runner.invoke(
            cli,
            [
                "spectrum-qc",
                "practical_review.mzml",
                "--kind",
                "mzml",
                "--plot-out",
                "plot.json",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["source_kind"] == "mzml"
        assert payload["chromatogram_source"] == "reported_mzml_chromatograms"
        assert payload["precursor_intensity_observation_count"] == 2
        assert len(payload["tic_trace"]) == 3
        assert Path("plot.json").exists()


def test_spectrum_annotate_command_writes_annotation_and_plot_payload() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        source = FIXTURE_ROOT / "spectra" / "simple.mgf"
        shutil.copy(source, "simple.mgf")

        result = runner.invoke(
            cli,
            [
                "spectrum-annotate",
                "simple.mgf",
                "--peptide",
                "PEPTIDE",
                "--tsv-out",
                "annotation.tsv",
                "--unmatched-peak-tsv-out",
                "unmatched.tsv",
                "--plot-out",
                "plot.json",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert (
            payload["annotation"]["document_schema"]["document_kind"]
            == "spectrum_annotation"
        )
        assert (
            payload["peak_matching_report"]["document_schema"]["document_kind"]
            == "spectrum_peak_matching_report"
        )
        assert payload["annotation"]["matches"]
        assert payload["annotation"]["matched_peak_count"] > 0
        assert payload["annotation"]["explained_intensity_fraction"] > 0.0
        assert payload["peak_matching_report"]["matched_peak_count"] > 0
        assert Path("annotation.tsv").exists()
        assert Path("unmatched.tsv").exists()
        assert Path("plot.json").exists()
        assert (
            Path("unmatched.tsv").read_text().splitlines()[0]
            == "spectrum_id\tpeptide\ttolerance_mode\tmz\tintensity"
        )


def test_spectrum_annotate_command_supports_ppm_tolerance() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        source = FIXTURE_ROOT / "spectra" / "simple.mgf"
        shutil.copy(source, "simple.mgf")

        result = runner.invoke(
            cli,
            [
                "spectrum-annotate",
                "simple.mgf",
                "--peptide",
                "PEPTIDE",
                "--tolerance-ppm",
                "20",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["annotation"]["tolerance_unit"] == "ppm"
        assert payload["annotation"]["tolerance_da"] is None
        assert payload["annotation"]["tolerance_ppm"] == 20.0
        assert payload["peak_matching_report"]["tolerance_mode"] == "ppm"
        assert payload["peak_matching_report"]["tolerance_da"] is None
        assert payload["peak_matching_report"]["tolerance_ppm"] == 20.0


def test_spectrum_score_chimeric_command_emits_mixed_and_clean_review_outputs() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        shutil.copy(
            FIXTURE_ROOT / "formats" / "chimeric_spectrum_review.mzml",
            "chimeric_spectrum_review.mzml",
        )
        shutil.copy(
            FIXTURE_ROOT / "psm" / "chimeric_spectrum_candidates.tsv",
            "chimeric_spectrum_candidates.tsv",
        )

        result = runner.invoke(
            cli,
            [
                "spectrum-score-chimeric",
                "chimeric_spectrum_review.mzml",
                "chimeric_spectrum_candidates.tsv",
                "--kind",
                "mzml",
                "--spectra-tsv-out",
                "chimeric.spectra.tsv",
                "--competition-tsv-out",
                "chimeric.competition.tsv",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["spectrum_kind"] == "mzml"
        assert payload["psm_summary"]["accepted_record_count"] == 4
        assert payload["chimeric_summary"]["spectrum_count"] == 2
        assert payload["chimeric_summary"]["flagged_chimeric_count"] == 1
        assert payload["spectra"][0]["spectrum_id"] == "scan=9002"
        assert payload["spectra"][0]["flagged_chimeric"] is True
        assert payload["spectra"][0]["chimeric_score"] > 0.7
        assert Path("chimeric.spectra.tsv").exists()
        assert Path("chimeric.competition.tsv").exists()
        assert "scan=9002\t400.687246\t400.687246\t399.687246\t401.687246" in Path(
            "chimeric.spectra.tsv"
        ).read_text(encoding="utf-8")
        assert "scan=9002\tTIDEPEP\t2\tP22222\t45.0000" in Path(
            "chimeric.competition.tsv"
        ).read_text(encoding="utf-8")


def test_spectrum_similarity_command_reports_pairwise_comparison() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        query = _similarity_spectrum(
            "query",
            ((100.01, 1.0), (150.01, 0.9), (200.01, 0.7)),
        )
        reference = _similarity_spectrum(
            "reference",
            ((100.0, 1.0), (150.0, 0.9), (200.0, 0.7)),
        )
        Path("query.mgf").write_text(render_mgf((query,)), encoding="utf-8")
        Path("reference.mgf").write_text(render_mgf((reference,)), encoding="utf-8")

        result = runner.invoke(
            cli,
            [
                "spectrum-similarity",
                "query.mgf",
                "reference.mgf",
                "--query-spectrum-id",
                "query",
                "--reference-spectrum-id",
                "reference",
                "--tolerance-da",
                "0.02",
                "--tsv-out",
                "similarity.tsv",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["comparison"]["classification"] == "duplicate_like"
        assert payload["comparison"]["score"] > 0.99
        assert (
            payload["library_report"]["matches"][0]["reference_spectrum_id"]
            == "reference"
        )
        assert Path("similarity.tsv").exists()


def test_spectrum_similarity_command_supports_library_ranking_with_binning() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        query = _similarity_spectrum(
            "query",
            ((100.21, 1.0), (150.19, 0.8), (200.18, 0.6)),
        )
        best = _similarity_spectrum(
            "best-match",
            ((100.0, 1.0), (150.0, 0.8), (200.0, 0.6)),
        )
        other = _similarity_spectrum(
            "other-match",
            ((400.0, 1.0), (450.0, 0.8), (500.0, 0.6)),
        )
        Path("query.mgf").write_text(render_mgf((query,)), encoding="utf-8")
        Path("library.mgf").write_text(render_mgf((other, best)), encoding="utf-8")

        result = runner.invoke(
            cli,
            [
                "spectrum-similarity",
                "query.mgf",
                "library.mgf",
                "--query-spectrum-id",
                "query",
                "--bin-width-da",
                "1.0",
                "--max-matches",
                "2",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["comparison"] is None
        assert payload["library_report"]["parameters"]["matching_mode"] == "binned"
        assert (
            payload["library_report"]["matches"][0]["reference_spectrum_id"]
            == "best-match"
        )
        assert (
            payload["library_report"]["matches"][0]["classification"]
            == "duplicate_like"
        )


def test_spectral_library_import_command_reports_msp_summary_and_candidates() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        shutil.copy(
            FIXTURE_ROOT / "formats" / "review_library.msp", "review_library.msp"
        )

        result = runner.invoke(
            cli,
            [
                "spectral-library-import",
                "review_library.msp",
                "--precursor-mz",
                "508.18",
                "--tolerance-da",
                "0.05",
                "--peptide",
                "PEPM[Oxidation]TIDE",
                "--summary-tsv-out",
                "summary.tsv",
                "--candidates-tsv-out",
                "candidates.tsv",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["import_report"]["source_format"] == "msp"
        assert payload["summary"]["modified_entry_count"] == 1
        assert payload["candidates"]["candidate_count"] == 1
        assert (
            payload["candidates"]["matches"][0]["canonical_peptide"]
            == "PEPM[Oxidation]TIDE"
        )
        assert Path("summary.tsv").exists()
        assert Path("candidates.tsv").exists()


def test_spectral_library_import_command_supports_mgf_library_indexing() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        shutil.copy(
            FIXTURE_ROOT / "formats" / "review_library.mgf", "review_library.mgf"
        )

        result = runner.invoke(
            cli,
            [
                "spectral-library-import",
                "review_library.mgf",
                "--kind",
                "mgf",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["import_report"]["source_format"] == "mgf"
        assert payload["index"]["entry_count"] == 2
        assert "PEPM[Oxidation]TIDE" in payload["index"]["peptide_index"]
        assert payload["candidates"] is None


def test_spectral_library_search_command_reports_ranked_decoy_aware_matches() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        shutil.copy(
            FIXTURE_ROOT / "formats" / "library_search_query.mgf",
            "library_search_query.mgf",
        )
        shutil.copy(
            FIXTURE_ROOT / "formats" / "library_search_reference.msp",
            "library_search_reference.msp",
        )

        result = runner.invoke(
            cli,
            [
                "spectral-library-search",
                "library_search_query.mgf",
                "library_search_reference.msp",
                "--query-kind",
                "mgf",
                "--library-kind",
                "msp",
                "--precursor-tolerance-da",
                "0.03",
                "--tolerance-da",
                "0.02",
                "--tsv-out",
                "library_search.tsv",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["import_report"]["source_format"] == "msp"
        assert payload["library_summary"]["decoy_entry_count"] == 1
        assert payload["search_report"]["search_strategy"] == "concatenated"
        assert payload["search_report"]["advisory_warning"] is None
        assert payload["warnings"] == []
        assert (
            payload["search_report"]["top_match_library_entry_id"] == "msp:1:PEPTIDE/2"
        )
        assert payload["search_report"]["matches"][0]["q_value"] == 0.0
        assert Path("library_search.tsv").exists()


def test_spectral_library_search_command_supports_mgf_library_search_without_decoys() -> (
    None
):
    runner = CliRunner()
    with runner.isolated_filesystem():
        query = _similarity_spectrum(
            "review-query",
            ((100.01, 1500.0), (250.01, 800.0)),
        )
        Path("query.mgf").write_text(render_mgf((query,)), encoding="utf-8")
        shutil.copy(
            FIXTURE_ROOT / "formats" / "review_library.mgf", "review_library.mgf"
        )

        result = runner.invoke(
            cli,
            [
                "spectral-library-search",
                "query.mgf",
                "review_library.mgf",
                "--library-kind",
                "mgf",
                "--tolerance-da",
                "0.02",
                "--max-matches",
                "1",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["import_report"]["source_format"] == "mgf"
        assert payload["search_report"]["search_strategy"] == "no_decoy_advisory"
        assert payload["search_report"]["candidate_count"] == 1
        assert payload["search_report"]["top_match_canonical_peptide"] == "PEPTIDE"
        assert payload["search_report"]["top_match_q_value"] is None
        assert payload["search_report"]["advisory_warning"] == (
            "library search ran without decoy entries; q-values are withheld and this report is advisory only"
        )
        assert payload["warnings"] == [
            "library search ran without decoy entries; q-values are withheld and this report is advisory only"
        ]


def test_validate_command_supports_fasta_psm_mgf_and_mod_registry(
    fasta_fixture_dir: Path,
) -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        shutil.copy(fasta_fixture_dir / "valid_records.fasta", "valid.fasta")
        shutil.copy(
            FIXTURE_ROOT / "psm" / "representative_results.tsv",
            "results.tsv",
        )
        shutil.copy(FIXTURE_ROOT / "spectra" / "simple.mgf", "simple.mgf")
        shutil.copy(
            FIXTURE_ROOT / "modifications" / "valid_registry.json",
            "registry.json",
        )

        fasta_result = runner.invoke(
            cli, ["validate", "valid.fasta", "--kind", "fasta"]
        )
        psm_result = runner.invoke(cli, ["validate", "results.tsv", "--kind", "psm"])
        mgf_result = runner.invoke(cli, ["validate", "simple.mgf", "--kind", "mgf"])
        registry_result = runner.invoke(
            cli, ["validate", "registry.json", "--kind", "mod-registry"]
        )

        assert fasta_result.exit_code == 0
        assert json.loads(fasta_result.output)["valid"] is True
        assert psm_result.exit_code == 0
        assert json.loads(psm_result.output)["valid"] is True
        assert mgf_result.exit_code == 0
        assert json.loads(mgf_result.output)["valid"] is True
        assert registry_result.exit_code == 0
        assert (
            json.loads(registry_result.output)["summary"]["variable_modifications"] >= 1
        )


def test_summarize_command_supports_fasta_psm_and_mgf(fasta_fixture_dir: Path) -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        shutil.copy(fasta_fixture_dir / "valid_records.fasta", "valid.fasta")
        shutil.copy(
            FIXTURE_ROOT / "psm" / "representative_results.tsv",
            "results.tsv",
        )
        shutil.copy(
            FIXTURE_ROOT / "psm" / "contaminant_results.tsv",
            "contaminant_results.tsv",
        )
        shutil.copy(FIXTURE_ROOT / "spectra" / "multi.mgf", "multi.mgf")

        fasta_result = runner.invoke(
            cli, ["summarize", "valid.fasta", "--kind", "fasta"]
        )
        psm_result = runner.invoke(cli, ["summarize", "results.tsv", "--kind", "psm"])
        contaminant_psm_result = runner.invoke(
            cli, ["summarize", "contaminant_results.tsv", "--kind", "psm"]
        )
        mgf_result = runner.invoke(cli, ["summarize", "multi.mgf", "--kind", "mgf"])

        assert fasta_result.exit_code == 0
        fasta_payload = json.loads(fasta_result.output)
        assert fasta_payload["summary"]["total_records"] == 3
        assert fasta_payload["profile"]["summary"]["protein_count"] == 3
        assert fasta_payload["profile"]["summary"]["organism_annotated_count"] == 2
        assert fasta_payload["database_composition"]["target_count"] == 3
        assert fasta_payload["duplicate_accessions"] == []
        assert psm_result.exit_code == 0
        psm_payload = json.loads(psm_result.output)
        assert psm_payload["psm_summary"]["total_psms"] == 3
        assert psm_payload["inspection"]["accepted_rows"] == 3
        assert contaminant_psm_result.exit_code == 0
        contaminant_payload = json.loads(contaminant_psm_result.output)
        assert contaminant_payload["contaminant_report"]["contaminant_psm_count"] == 2
        assert contaminant_payload["inspection"]["accepted_rows"] == 3
        assert (
            contaminant_payload["contaminant_report"]["mixed_reference_psm_count"] == 1
        )
        assert mgf_result.exit_code == 0
        assert json.loads(mgf_result.output)["summary"]["spectrum_count"] == 2


def test_psm_contaminants_command_reports_contaminant_matches() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        shutil.copy(
            FIXTURE_ROOT / "psm" / "contaminant_results.tsv",
            "contaminant_results.tsv",
        )

        result = runner.invoke(
            cli,
            ["psm-contaminants", "contaminant_results.tsv"],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["contaminant_psm_count"] == 2
        assert payload["pure_contaminant_psm_count"] == 1
        assert payload["mixed_reference_psm_count"] == 1
        assert payload["contaminant_protein_counts"] == {
            "CON__K1C10_HUMAN": 1,
            "CON__TRYP_PIG": 1,
        }


def test_psm_contaminants_command_exports_burden_and_protein_ledgers() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        shutil.copy(
            FIXTURE_ROOT / "psm" / "contaminant_burden_results.tsv",
            "contaminant_burden_results.tsv",
        )

        result = runner.invoke(
            cli,
            [
                "psm-contaminants",
                "contaminant_burden_results.tsv",
                "--run-id-column",
                "run_id",
                "--intensity-column",
                "intensity",
                "--burden-tsv-out",
                "contaminant_burden.tsv",
                "--protein-tsv-out",
                "contaminant_proteins.tsv",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["contaminant_evidence"]["summary"]["contaminant_psm_count"] == 3
        assert payload["contaminant_evidence"]["summary"]["contaminant_intensity"] == 1050.0
        assert (
            payload["contaminant_evidence"]["burden_entries"][0][
                "heavy_contaminant_warning"
            ]
            is True
        )
        assert (
            "run-a\t\t3\t2\t1\t1\t2\t2\t2000.0\t1000.0\t0.6666666666666666\t0.5\ttrue"
            in Path("contaminant_burden.tsv").read_text(encoding="utf-8")
        )
        assert (
            "CON__K1C10_HUMAN\trun-a;run-b\t\t2\t2\t850.0"
            in Path("contaminant_proteins.tsv").read_text(encoding="utf-8")
        )


def test_validate_and_summarize_commands_support_mzml_and_design_tables() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        shutil.copy(
            FIXTURE_ROOT / "formats" / "simple.mzml",
            "simple.mzml",
        )
        shutil.copy(
            FIXTURE_ROOT / "formats" / "valid.design.tsv",
            "design.tsv",
        )

        validate_mzml = runner.invoke(
            cli, ["validate", "simple.mzml", "--kind", "mzml"]
        )
        summarize_mzml = runner.invoke(
            cli, ["summarize", "simple.mzml", "--kind", "mzml"]
        )
        validate_design = runner.invoke(
            cli, ["validate", "design.tsv", "--kind", "design-table"]
        )
        summarize_design = runner.invoke(
            cli, ["summarize", "design.tsv", "--kind", "design-table"]
        )

        assert validate_mzml.exit_code == 0
        assert json.loads(validate_mzml.output)["detected_format"] == "mzml"
        assert summarize_mzml.exit_code == 0
        assert json.loads(summarize_mzml.output)["metadata"]["run_id"] == "RUN_001"
        assert validate_design.exit_code == 0
        assert json.loads(validate_design.output)["detected_format"] == "design-table"
        assert summarize_design.exit_code == 0
        assert json.loads(summarize_design.output)["accepted_entries"] == 1


def test_mzml_inspect_command_reports_decoding_and_chromatograms() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        shutil.copy(
            FIXTURE_ROOT / "formats" / "practical_review.mzml",
            "practical_review.mzml",
        )

        result = runner.invoke(
            cli,
            [
                "mzml-inspect",
                "practical_review.mzml",
                "--spectra-jsonl-out",
                "spectra.jsonl",
                "--chromatograms-json-out",
                "chromatograms.json",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["metadata"]["run_id"] == "RUN_PRACTICAL_01"
        assert payload["decoding_support"]["supported"] is True
        assert payload["chromatograms"]["total_chromatograms"] == 2
        assert Path("spectra.jsonl").exists()
        assert Path("chromatograms.json").exists()


def test_mzml_inspect_command_surfaces_tic_and_bpc_trace_kinds() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        shutil.copy(
            FIXTURE_ROOT / "formats" / "practical_review.mzml",
            "practical_review.mzml",
        )

        result = runner.invoke(
            cli,
            [
                "mzml-inspect",
                "practical_review.mzml",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        kinds = {trace["kind"] for trace in payload["chromatograms"]["accepted_traces"]}
        assert kinds == {"tic", "bpc"}
        assert payload["summary"]["spectrum_count"] == 2


def test_xic_extract_command_emits_trace_json_and_tsv() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        shutil.copy(
            FIXTURE_ROOT / "formats" / "xic_review.mzml",
            "xic_review.mzml",
        )
        shutil.copy(
            FIXTURE_ROOT / "formats" / "xic_targets.tsv",
            "xic_targets.tsv",
        )

        result = runner.invoke(
            cli,
            [
                "xic-extract",
                "xic_review.mzml",
                "xic_targets.tsv",
                "--tolerance-ppm",
                "10",
                "--tsv-out",
                "xic_traces.tsv",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["eligible_spectra"] == 3
        assert payload["tolerance_unit"] == "ppm"
        assert len(payload["trace_points"]) == 8
        assert Path("xic_traces.tsv").exists()
        traces_tsv = Path("xic_traces.tsv").read_text(encoding="utf-8")
        assert "target_beta\tscan=7002\t30\t700.000000\t699.993000\t700.007000\t3000\t1" in traces_tsv
        assert "scan=7003" not in traces_tsv


def test_xic_extract_command_rejects_dual_tolerance_modes() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        shutil.copy(
            FIXTURE_ROOT / "formats" / "xic_review.mzml",
            "xic_review.mzml",
        )
        shutil.copy(
            FIXTURE_ROOT / "formats" / "xic_targets.tsv",
            "xic_targets.tsv",
        )

        result = runner.invoke(
            cli,
            [
                "xic-extract",
                "xic_review.mzml",
                "xic_targets.tsv",
                "--tolerance-da",
                "0.01",
                "--tolerance-ppm",
                "10",
            ],
        )

        assert result.exit_code != 0
        assert "provide either tolerance_da or tolerance_ppm, not both" in result.output


def test_xic_pick_peaks_command_emits_peak_and_trace_outputs() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        shutil.copy(
            FIXTURE_ROOT / "formats" / "chromatographic_peak_profile.mzml",
            "chromatographic_peak_profile.mzml",
        )
        shutil.copy(
            FIXTURE_ROOT / "formats" / "chromatographic_peak_targets.tsv",
            "chromatographic_peak_targets.tsv",
        )

        result = runner.invoke(
            cli,
            [
                "xic-pick-peaks",
                "chromatographic_peak_profile.mzml",
                "chromatographic_peak_targets.tsv",
                "--tolerance-ppm",
                "10",
                "--trace-tsv-out",
                "xic_traces.tsv",
                "--peak-tsv-out",
                "chromatographic_peaks.tsv",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert len(payload["peaks"]) == 3
        assert payload["peaks"][0]["overlap_flag"] is True
        assert payload["peaks"][0]["shoulder_flag"] is True
        assert Path("xic_traces.tsv").exists()
        assert Path("chromatographic_peaks.tsv").exists()
        peaks_tsv = Path("chromatographic_peaks.tsv").read_text(encoding="utf-8")
        assert (
            "target_overlap_peak_001\ttarget_overlap\t0\t30\t20\t120\t0\t90\t60\t60\t700\t4\ttrue\ttrue"
            in peaks_tsv
        )
        assert "scan=7107" not in Path("xic_traces.tsv").read_text(encoding="utf-8")


def test_xic_pick_peaks_command_rejects_dual_tolerance_modes() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        shutil.copy(
            FIXTURE_ROOT / "formats" / "chromatographic_peak_profile.mzml",
            "chromatographic_peak_profile.mzml",
        )
        shutil.copy(
            FIXTURE_ROOT / "formats" / "chromatographic_peak_targets.tsv",
            "chromatographic_peak_targets.tsv",
        )

        result = runner.invoke(
            cli,
            [
                "xic-pick-peaks",
                "chromatographic_peak_profile.mzml",
                "chromatographic_peak_targets.tsv",
                "--tolerance-da",
                "0.01",
                "--tolerance-ppm",
                "10",
            ],
        )

        assert result.exit_code != 0
        assert "provide either tolerance_da or tolerance_ppm, not both" in result.output


def test_xic_align_retention_times_command_emits_models_residuals_and_failed_anchors() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        shutil.copy(
            FIXTURE_ROOT / "formats" / "rt_alignment_reference.mzml",
            "rt_alignment_reference.mzml",
        )
        shutil.copy(
            FIXTURE_ROOT / "formats" / "rt_alignment_shifted.mzml",
            "rt_alignment_shifted.mzml",
        )
        shutil.copy(
            FIXTURE_ROOT / "formats" / "rt_alignment_targets.tsv",
            "rt_alignment_targets.tsv",
        )

        result = runner.invoke(
            cli,
            [
                "xic-align-retention-times",
                "rt_alignment_targets.tsv",
                "rt_alignment_reference.mzml",
                "rt_alignment_shifted.mzml",
                "--tolerance-ppm",
                "10",
                "--aligned-rt-tolerance-seconds",
                "5",
                "--model-tsv-out",
                "rt.models.tsv",
                "--residual-tsv-out",
                "rt.residuals.tsv",
                "--failed-anchor-tsv-out",
                "rt.failed.tsv",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["reference_run_id"] == "rt_alignment_reference"
        assert len(payload["run_models"]) == 2
        assert payload["run_models"][1]["status"] == "aligned"
        assert payload["run_models"][1]["alignment_model"] == "confidence_weighted_shift"
        assert payload["run_models"][1]["rt_shift"] == 10.0
        assert payload["run_models"][1]["rt_residual_median"] == 0.0
        assert payload["run_models"][1]["failed_anchor_count"] == 1
        assert payload["run_models"][1]["shift_seconds"] == 10.0
        assert len(payload["flagged_residuals"]) == 1
        assert payload["flagged_residuals"][0]["target_id"] == "anchor_gamma"
        assert payload["flagged_residuals"][0]["outside_aligned_tolerance"] is True
        assert len(payload["failed_anchors"]) == 1
        assert payload["failed_anchors"][0]["reason"] == "missing_run_peak"
        assert payload["outputs"]["model_tsv"] == "rt.models.tsv"
        assert payload["outputs"]["residual_tsv"] == "rt.residuals.tsv"
        assert payload["outputs"]["failed_anchor_tsv"] == "rt.failed.tsv"
        assert Path("rt.models.tsv").exists()
        assert Path("rt.residuals.tsv").exists()
        assert Path("rt.failed.tsv").exists()
        assert (
            "\taligned\t3\tconfidence_weighted_shift\t10\t0\t1\t10\t0\t10\t"
            in Path("rt.models.tsv").read_text(encoding="utf-8")
        )
        assert (
            "anchor_gamma\tanchor_gamma_peak_001\tanchor_gamma_peak_001\t60\t80\t70\t10\t10\t10\ttrue"
            in Path("rt.residuals.tsv").read_text(encoding="utf-8")
        )
        assert (
            "\tanchor_delta\tmissing_run_peak\t1\t0"
            in Path("rt.failed.tsv").read_text(encoding="utf-8")
        )


def test_xic_align_retention_times_command_requires_multiple_runs() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        shutil.copy(
            FIXTURE_ROOT / "formats" / "rt_alignment_reference.mzml",
            "rt_alignment_reference.mzml",
        )
        shutil.copy(
            FIXTURE_ROOT / "formats" / "rt_alignment_targets.tsv",
            "rt_alignment_targets.tsv",
        )

        result = runner.invoke(
            cli,
            [
                "xic-align-retention-times",
                "rt_alignment_targets.tsv",
                "rt_alignment_reference.mzml",
                "--tolerance-ppm",
                "10",
            ],
        )

        assert result.exit_code != 0
        assert "retention-time alignment requires at least two mzML files" in result.output


def test_xic_score_evidence_command_emits_target_and_peptide_scores() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        shutil.copy(
            FIXTURE_ROOT / "formats" / "rt_alignment_reference.mzml",
            "rt_alignment_reference.mzml",
        )
        shutil.copy(
            FIXTURE_ROOT / "formats" / "rt_alignment_shifted.mzml",
            "rt_alignment_shifted.mzml",
        )
        shutil.copy(
            FIXTURE_ROOT / "formats" / "rt_alignment_targets.tsv",
            "rt_alignment_targets.tsv",
        )

        result = runner.invoke(
            cli,
            [
                "xic-score-evidence",
                "rt_alignment_targets.tsv",
                "rt_alignment_reference.mzml",
                "rt_alignment_shifted.mzml",
                "--tolerance-ppm",
                "10",
                "--aligned-rt-tolerance-seconds",
                "5",
                "--target-tsv-out",
                "chrom.target.tsv",
                "--peptide-tsv-out",
                "chrom.peptide.tsv",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["run_ids"] == [
            "rt_alignment_reference",
            "rt_alignment_shifted",
        ]
        assert len(payload["target_entries"]) == 4
        assert len(payload["peptide_entries"]) == 4
        assert payload["target_entries"][0]["chromatographic_evidence_score"] == 1.0
        by_target = {
            entry["target_id"]: entry for entry in payload["target_entries"]
        }
        assert by_target["anchor_gamma"]["rt_agreement_score"] == 0.0
        assert by_target["anchor_delta"]["missing_run_count"] == 1
        assert payload["outputs"]["target_tsv"] == "chrom.target.tsv"
        assert payload["outputs"]["peptide_tsv"] == "chrom.peptide.tsv"
        assert Path("chrom.target.tsv").exists()
        assert Path("chrom.peptide.tsv").exists()
        assert (
            "anchor_gamma\tPEPC\t700.000000\t2\t2\t0\t0.8334\t1.0000\t1.0000\t0.0000\t1.0000\t0.7583"
            in Path("chrom.target.tsv").read_text(encoding="utf-8")
        )
        assert (
            "PEPD\tanchor_delta\t2\t1\t1.0000\t1.0000\t1.0000\t0.0000\t0.5000\t0.7250"
            in Path("chrom.peptide.tsv").read_text(encoding="utf-8")
        )


def test_xic_score_evidence_command_requires_at_least_one_run() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        shutil.copy(
            FIXTURE_ROOT / "formats" / "rt_alignment_targets.tsv",
            "rt_alignment_targets.tsv",
        )

        result = runner.invoke(
            cli,
            [
                "xic-score-evidence",
                "rt_alignment_targets.tsv",
                "--tolerance-ppm",
                "10",
            ],
        )

        assert result.exit_code != 0
        assert "chromatographic evidence scoring requires at least one mzML file" in result.output


def test_dia_fragment_coelution_command_emits_run_and_fragment_outputs() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        shutil.copy(
            FIXTURE_ROOT / "formats" / "dia_fragment_coelution.mzml",
            "dia_fragment_coelution.mzml",
        )
        shutil.copy(
            FIXTURE_ROOT / "formats" / "dia_fragment_targets.tsv",
            "dia_fragment_targets.tsv",
        )

        result = runner.invoke(
            cli,
            [
                "dia-fragment-coelution",
                "dia_fragment_targets.tsv",
                "dia_fragment_coelution.mzml",
                "--tolerance-ppm",
                "10",
                "--run-tsv-out",
                "dia.run.tsv",
                "--fragment-tsv-out",
                "dia.fragment.tsv",
                "--ratio-fragment-tsv-out",
                "dia.ratio_fragment.tsv",
                "--ratio-observation-tsv-out",
                "dia.ratio_observation.tsv",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["run_ids"] == ["dia_fragment_coelution"]
        assert len(payload["run_entries"]) == 2
        assert len(payload["fragment_entries"]) == 6
        assert payload["fragment_ratio_stability_summary"]["analyte_count"] == 2
        assert payload["fragment_ratio_stability_summary"]["fragment_entry_count"] == 5
        assert payload["fragment_ratio_stability_summary"]["unstable_fragment_count"] == 0
        assert len(payload["fragment_ratio_fragments"]) == 5
        assert len(payload["fragment_ratio_observations"]) == 5
        by_precursor = {
            entry["precursor_id"]: entry for entry in payload["run_entries"]
        }
        assert by_precursor["prec_alpha"]["coelution_score"] == 1.0
        assert by_precursor["prec_beta"]["failed_fragment_ids"] == [
            "beta_b4",
            "beta_y8",
        ]
        assert payload["outputs"]["run_tsv"] == "dia.run.tsv"
        assert payload["outputs"]["fragment_tsv"] == "dia.fragment.tsv"
        assert payload["outputs"]["ratio_fragment_tsv"] == "dia.ratio_fragment.tsv"
        assert payload["outputs"]["ratio_observation_tsv"] == "dia.ratio_observation.tsv"
        assert Path("dia.run.tsv").exists()
        assert Path("dia.fragment.tsv").exists()
        assert Path("dia.ratio_fragment.tsv").exists()
        assert Path("dia.ratio_observation.tsv").exists()
        assert (
            "dia_fragment_coelution\tprec_beta\tPEPB\tbeta_y7\t3\t2\t1\t10.0000\t0.5578\t0.2971"
            in Path("dia.run.tsv").read_text(encoding="utf-8")
        )
        assert (
            "dia_fragment_coelution\tprec_beta\tPEPB\tbeta_b4\tbeta_b4\tbeta_y7"
            in Path("dia.fragment.tsv").read_text(encoding="utf-8")
        )
        assert (
            "dia\tprec_alpha\tPEPA\talpha_b4\t1\t1\t0.276008\t\t0\tfalse\t1.000000\tinsufficient_runs"
            in Path("dia.ratio_fragment.tsv").read_text(encoding="utf-8")
        )
        assert (
            "dia\tprec_alpha\tPEPA\tdia_fragment_coelution\talpha_b4\t0.276008\t0.276008\t0.000000\t\tfalse\tfalse"
            in Path("dia.ratio_observation.tsv").read_text(encoding="utf-8")
        )


def test_dia_fragment_coelution_command_requires_at_least_one_run() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        shutil.copy(
            FIXTURE_ROOT / "formats" / "dia_fragment_targets.tsv",
            "dia_fragment_targets.tsv",
        )

        result = runner.invoke(
            cli,
            [
                "dia-fragment-coelution",
                "dia_fragment_targets.tsv",
                "--tolerance-ppm",
                "10",
            ],
        )

        assert result.exit_code != 0
        assert "DIA fragment coelution extraction requires at least one mzML file" in result.output


def test_raw_signal_evidence_card_command_emits_structured_card_outputs() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        shutil.copy(
            FIXTURE_ROOT / "formats" / "raw_signal_card_reference.mzml",
            "raw_signal_card_reference.mzml",
        )
        shutil.copy(
            FIXTURE_ROOT / "formats" / "raw_signal_card_shifted.mzml",
            "raw_signal_card_shifted.mzml",
        )
        shutil.copy(
            FIXTURE_ROOT / "formats" / "raw_signal_card_targets.tsv",
            "raw_signal_card_targets.tsv",
        )
        shutil.copy(
            FIXTURE_ROOT / "formats" / "raw_signal_card_fragment_targets.tsv",
            "raw_signal_card_fragment_targets.tsv",
        )
        shutil.copy(
            FIXTURE_ROOT / "formats" / "chimeric_spectrum_review.mzml",
            "chimeric_spectrum_review.mzml",
        )
        shutil.copy(
            FIXTURE_ROOT / "psm" / "chimeric_spectrum_candidates.tsv",
            "chimeric_spectrum_candidates.tsv",
        )

        result = runner.invoke(
            cli,
            [
                "raw-signal-evidence-card",
                "raw_signal_card_targets.tsv",
                "raw_signal_card_reference.mzml",
                "raw_signal_card_shifted.mzml",
                "--fragment-target-table",
                "raw_signal_card_fragment_targets.tsv",
                "--fragment-ms-level",
                "1",
                "--spectrum-mzml",
                "chimeric_spectrum_review.mzml",
                "--psm-tsv",
                "chimeric_spectrum_candidates.tsv",
                "--precursor-id",
                "prec_peptide",
                "--tolerance-ppm",
                "10",
                "--summary-tsv-out",
                "raw_signal.summary.tsv",
                "--card-tsv-out",
                "raw_signal.cards.tsv",
                "--html-out",
                "raw_signal.cards.html",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        report = payload["report"]
        assert report["summary"]["card_count"] == 1
        assert report["cards"][0]["precursor_id"] == "prec_peptide"
        assert report["cards"][0]["peptide_ref"] == "PEPTIDE"
        assert report["cards"][0]["retention_time_residuals"][0]["residual_seconds"] == 20.0
        assert report["cards"][0]["fragment_run_entries"][1]["failed_fragment_ids"] == [
            "peptide_b4",
            "peptide_y8",
        ]
        assert report["cards"][0]["spectrum_evidence"][0]["spectrum_id"] == "scan=9002"
        assert payload["outputs"]["summary_tsv"] == "raw_signal.summary.tsv"
        assert payload["outputs"]["card_tsv"] == "raw_signal.cards.tsv"
        assert payload["outputs"]["html"] == "raw_signal.cards.html"
        assert Path("raw_signal.summary.tsv").exists()
        assert Path("raw_signal.cards.tsv").exists()
        assert Path("raw_signal.cards.html").exists()
        assert "1\t1\t1\t1\t1" in Path("raw_signal.summary.tsv").read_text(
            encoding="utf-8"
        )
        assert (
            "raw-signal-card:prec_peptide\tprec_peptide\tPEPTIDE\tPEPTIDE precursor"
            in Path("raw_signal.cards.tsv").read_text(encoding="utf-8")
        )
        assert "retention_time_alignment_outside_tolerance" in Path(
            "raw_signal.cards.html"
        ).read_text(encoding="utf-8")


def test_precursor_isotope_fit_command_emits_summary_entry_and_peak_outputs() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        format_dir = FIXTURE_ROOT / "formats"
        shutil.copy(
            format_dir / "precursor_isotope_fit_reference.mzml",
            "precursor_isotope_fit_reference.mzml",
        )
        shutil.copy(
            format_dir / "precursor_isotope_fit_shifted.mzml",
            "precursor_isotope_fit_shifted.mzml",
        )
        shutil.copy(
            format_dir / "precursor_isotope_fit_wrong_charge.mzml",
            "precursor_isotope_fit_wrong_charge.mzml",
        )
        shutil.copy(
            format_dir / "precursor_isotope_fit_targets.tsv",
            "precursor_isotope_fit_targets.tsv",
        )

        result = runner.invoke(
            cli,
            [
                "precursor-isotope-fit",
                "precursor_isotope_fit_targets.tsv",
                "precursor_isotope_fit_reference.mzml",
                "precursor_isotope_fit_shifted.mzml",
                "precursor_isotope_fit_wrong_charge.mzml",
                "--extraction-tolerance-da",
                "0.05",
                "--fit-tolerance-da",
                "0.05",
                "--summary-tsv-out",
                "isotope_fit.summary.tsv",
                "--entry-tsv-out",
                "isotope_fit.entries.tsv",
                "--peak-tsv-out",
                "isotope_fit.peaks.tsv",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        report = payload["report"]
        assert report["summary"]["run_count"] == 3
        assert report["summary"]["flagged_entry_count"] == 2
        assert report["entries"][0]["run_id"] == "precursor_isotope_fit_reference"
        assert report["entries"][1]["concern_codes"] == ["shifted_monoisotopic_mz"]
        assert report["entries"][2]["missing_isotope_indices"] == [1]
        assert payload["outputs"]["summary_tsv"] == "isotope_fit.summary.tsv"
        assert payload["outputs"]["entry_tsv"] == "isotope_fit.entries.tsv"
        assert payload["outputs"]["peak_tsv"] == "isotope_fit.peaks.tsv"
        assert Path("isotope_fit.summary.tsv").exists()
        assert Path("isotope_fit.entries.tsv").exists()
        assert Path("isotope_fit.peaks.tsv").exists()
        assert "3\t3\t2\t0\t1\t0" in Path("isotope_fit.summary.tsv").read_text(
            encoding="utf-8"
        )
        assert (
            "precursor_isotope_fit_shifted\tprec_peptide_ms1\tprec_peptide\tPEPTIDE\t2\t"
            "scan=8403\t30.0000"
            in Path("isotope_fit.entries.tsv").read_text(encoding="utf-8")
        )
        assert (
            "precursor_isotope_fit_wrong_charge\tprec_peptide_ms1\tprec_peptide\tPEPTIDE\t1\t401.188936\t0.267350"
            in Path("isotope_fit.peaks.tsv").read_text(encoding="utf-8")
        )


def test_precursor_isotope_fit_command_requires_at_least_one_run() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        shutil.copy(
            FIXTURE_ROOT / "formats" / "precursor_isotope_fit_targets.tsv",
            "precursor_isotope_fit_targets.tsv",
        )

        result = runner.invoke(
            cli,
            [
                "precursor-isotope-fit",
                "precursor_isotope_fit_targets.tsv",
                "--fit-tolerance-da",
                "0.05",
            ],
        )

        assert result.exit_code != 0
        assert "precursor isotope fit requires at least one mzML file" in result.output


def test_spectrum_summary_command_reports_mzml_ms1_ms2_counts() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        shutil.copy(
            FIXTURE_ROOT / "formats" / "practical_review.mzml",
            "practical_review.mzml",
        )

        result = runner.invoke(
            cli,
            [
                "spectrum-summary",
                "practical_review.mzml",
                "--kind",
                "mzml",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["source_kind"] == "mzml"
        assert payload["ms_level_policy"] == "reported"
        assert payload["ms1_spectrum_count"] == 1
        assert payload["ms2_spectrum_count"] == 1


def test_format_convert_and_bundle_run_commands_materialize_normalized_outputs() -> (
    None
):
    runner = CliRunner()
    with runner.isolated_filesystem():
        shutil.copy(
            FIXTURE_ROOT / "formats" / "simple.mzml",
            "simple.mzml",
        )
        shutil.copy(
            FIXTURE_ROOT / "formats" / "valid.design.tsv",
            "design.tsv",
        )
        shutil.copy(
            FIXTURE_ROOT / "first_useful_run" / "results.tsv",
            "results.tsv",
        )

        convert_result = runner.invoke(
            cli,
            [
                "format-convert",
                "simple.mzml",
                "--kind",
                "mzml",
                "--to",
                "mgf",
                "--out",
                "converted.mgf",
            ],
        )
        bundle_result = runner.invoke(
            cli,
            [
                "bundle-run",
                "--spectra",
                "simple.mzml",
                "--identifications",
                "results.tsv",
                "--design",
                "design.tsv",
                "--out-dir",
                "bundle",
            ],
        )

        assert convert_result.exit_code == 0
        assert json.loads(convert_result.output)["written_record_count"] == 2
        assert Path("converted.mgf").exists()
        assert "BEGIN IONS" in Path("converted.mgf").read_text()
        assert bundle_result.exit_code == 0
        bundle_manifest = json.loads(bundle_result.output)
        assert bundle_manifest["spectrum_count"] == 2
        assert bundle_manifest["psm_count"] == 2
        assert Path("bundle/bundle.manifest.json").exists()


def test_search_adapter_inspect_and_normalize_commands_work() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        fixture_dir = FIXTURE_ROOT / "search_adapters"
        shutil.copy(fixture_dir / "sage_results.tsv", "sage_results.tsv")
        shutil.copy(fixture_dir / "sage_config.json", "sage_config.json")
        shutil.copy(fixture_dir / "generic_results.tsv", "generic_results.tsv")
        shutil.copy(fixture_dir / "generic_mapping.json", "generic_mapping.json")

        inspect_result = runner.invoke(
            cli, ["search-adapter", "inspect", "--adapter", "sage"]
        )
        matrix_result = runner.invoke(cli, ["search-adapter", "inspect"])
        normalize_result = runner.invoke(
            cli,
            [
                "search-adapter",
                "normalize",
                "sage",
                "sage_results.tsv",
                "--adapter-version",
                "0.16.0",
                "--config",
                "sage_config.json",
                "--jsonl-out",
                "sage.jsonl",
                "--provenance-out",
                "sage.provenance.json",
            ],
        )
        generic_result = runner.invoke(
            cli,
            [
                "search-adapter",
                "normalize",
                "generic",
                "generic_results.tsv",
                "--mapping-json",
                "generic_mapping.json",
            ],
        )

        assert inspect_result.exit_code == 0
        assert json.loads(inspect_result.output)["adapter_kind"] == "sage"
        assert matrix_result.exit_code == 0
        assert any(
            row["adapter_kind"] == "comet"
            for row in json.loads(matrix_result.output)["capabilities"]
        )
        assert normalize_result.exit_code == 0
        normalize_payload = json.loads(normalize_result.output)
        assert normalize_payload["accepted_rows"] == 2
        assert Path("sage.jsonl").exists()
        assert Path("sage.provenance.json").exists()
        assert generic_result.exit_code == 0
        assert json.loads(generic_result.output)["adapter"]["adapter_kind"] == "generic"


def test_search_adapter_params_compare_and_conformance_commands_work() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        fixture_dir = FIXTURE_ROOT / "search_adapters"
        shutil.copy(fixture_dir / "comet.params", "comet.params")
        shutil.copy(fixture_dir / "comet_invalid.params", "comet_invalid.params")
        shutil.copy(fixture_dir / "sage_results.tsv", "sage_results.tsv")
        shutil.copy(fixture_dir / "sage_mapping.json", "sage_mapping.json")
        shutil.copy(fixture_dir / "sage_malformed.tsv", "sage_malformed.tsv")

        params_result = runner.invoke(
            cli,
            ["search-adapter", "params", "comet", "comet.params"],
        )
        validate_result = runner.invoke(
            cli,
            ["search-adapter", "validate-config", "comet", "comet_invalid.params"],
        )
        compare_result = runner.invoke(
            cli,
            [
                "search-adapter",
                "compare",
                "sage",
                "sage_results.tsv",
                "generic",
                "sage_results.tsv",
                "--right-mapping-json",
                "sage_mapping.json",
            ],
        )
        conformance_result = runner.invoke(
            cli,
            [
                "search-adapter",
                "conformance",
                "sage",
                "sage_malformed.tsv",
            ],
        )

        assert params_result.exit_code == 0
        assert json.loads(params_result.output)["enzyme"] == "trypsin"
        assert validate_result.exit_code == 0
        validate_payload = json.loads(validate_result.output)
        assert validate_payload["valid"] is False
        assert any(
            issue["code"] == "missing_decoy_strategy"
            for issue in validate_payload["issues"]
        )
        assert compare_result.exit_code == 0
        compare_payload = json.loads(compare_result.output)
        assert compare_payload["exact_match_count"] == 2
        assert conformance_result.exit_code == 0
        conformance_payload = json.loads(conformance_result.output)
        assert conformance_payload["passes"] is False
        assert conformance_payload["rejection_issue_counts"]["invalid_q_value"] == 1


def test_fragpipe_import_command_reports_bundle_summary_and_exports() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        fixture_dir = FIXTURE_ROOT / "search_result_bundles" / "fragpipe"
        shutil.copy(fixture_dir / "psm.tsv", "psm.tsv")
        shutil.copy(fixture_dir / "combined_peptide.tsv", "combined_peptide.tsv")
        shutil.copy(fixture_dir / "combined_protein.tsv", "combined_protein.tsv")
        shutil.copy(fixture_dir / "combined_quant.tsv", "combined_quant.tsv")

        result = runner.invoke(
            cli,
            [
                "fragpipe-import",
                "psm.tsv",
                "--peptide-tsv",
                "combined_peptide.tsv",
                "--protein-tsv",
                "combined_protein.tsv",
                "--quant-tsv",
                "combined_quant.tsv",
                "--summary-tsv-out",
                "fragpipe.summary.tsv",
                "--canonical-psm-tsv-out",
                "fragpipe.canonical_psm.tsv",
                "--psm-tsv-out",
                "fragpipe.psm.tsv",
                "--peptide-review-tsv-out",
                "fragpipe.peptide.tsv",
                "--protein-review-tsv-out",
                "fragpipe.protein.tsv",
                "--open-search-tsv-out",
                "fragpipe.open_search.tsv",
                "--protein-quantity-tsv-out",
                "fragpipe.quant.tsv",
                "--rejected-tsv-out",
                "fragpipe.rejected.tsv",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["summary"]["accepted_psm_count"] == 3
        assert payload["summary"]["open_search_psm_count"] == 1
        assert payload["summary"]["peptide_row_count"] == 2
        assert payload["summary"]["protein_row_count"] == 3
        assert payload["summary"]["canonical_psm_count"] == 3
        assert payload["summary"]["open_search_evidence_count"] == 2
        assert payload["summary"]["protein_quantity_count"] == 6
        assert (
            payload["psm_normalization"]["adapter"]["display_name"]
            == "FragPipe psm export"
        )
        assert payload["canonical_psms"][1]["open_search_candidate"] is True
        assert payload["psm_rows"][1]["open_search_candidate"] is True
        assert payload["open_search_evidence"][0]["mass_difference"] == 42.0106
        assert payload["protein_quantity_rows"][0]["quantity_kind"] == "maxlfq_intensity"
        assert payload["rejected_evidence_rows"] == []
        assert Path("fragpipe.summary.tsv").exists()
        assert Path("fragpipe.canonical_psm.tsv").exists()
        assert Path("fragpipe.psm.tsv").exists()
        assert Path("fragpipe.peptide.tsv").exists()
        assert Path("fragpipe.protein.tsv").exists()
        assert Path("fragpipe.open_search.tsv").exists()
        assert Path("fragpipe.quant.tsv").exists()
        assert Path("fragpipe.rejected.tsv").exists()
        assert Path("fragpipe.rejected.tsv").read_text(encoding="utf-8").startswith(
            "source_file\trow_number\tentity_type\tentity_id\treason_code\tdetail\n"
        )


def test_fragpipe_benchmark_command_reports_import_fidelity_and_exports() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        fixture_dir = FIXTURE_ROOT / "search_result_bundles" / "fragpipe"
        shutil.copy(fixture_dir / "psm.tsv", "psm.tsv")
        shutil.copy(fixture_dir / "combined_peptide.tsv", "combined_peptide.tsv")
        shutil.copy(fixture_dir / "combined_protein.tsv", "combined_protein.tsv")

        result = runner.invoke(
            cli,
            [
                "fragpipe-benchmark",
                "psm.tsv",
                "--peptide-tsv",
                "combined_peptide.tsv",
                "--protein-tsv",
                "combined_protein.tsv",
                "--summary-tsv-out",
                "fragpipe.benchmark.summary.tsv",
                "--count-comparisons-tsv-out",
                "fragpipe.benchmark.counts.tsv",
                "--protein-groups-tsv-out",
                "fragpipe.benchmark.proteins.tsv",
                "--psm-qvalues-tsv-out",
                "fragpipe.benchmark.psm_qvalues.tsv",
                "--peptide-qvalues-tsv-out",
                "fragpipe.benchmark.peptide_qvalues.tsv",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["summary"]["psm_count_matched"] is True
        assert payload["summary"]["peptide_count_matched"] is True
        assert payload["summary"]["protein_group_count_matched"] is True
        assert payload["summary"]["q_value_behavior_matched"] is True
        assert payload["protein_group_comparison"]["matched"] is True
        assert payload["q_value_behavior"]["max_psm_absolute_difference"] == 0.0
        assert Path("fragpipe.benchmark.summary.tsv").exists()
        assert Path("fragpipe.benchmark.counts.tsv").exists()
        assert Path("fragpipe.benchmark.proteins.tsv").exists()
        assert Path("fragpipe.benchmark.psm_qvalues.tsv").exists()
        assert Path("fragpipe.benchmark.peptide_qvalues.tsv").exists()
        assert "source_psm_count" in Path(
            "fragpipe.benchmark.summary.tsv"
        ).read_text(encoding="utf-8")
        assert "comparison_id" in Path(
            "fragpipe.benchmark.counts.tsv"
        ).read_text(encoding="utf-8")
        assert "missing_in_import" in Path(
            "fragpipe.benchmark.proteins.tsv"
        ).read_text(encoding="utf-8")
        assert "absolute_difference" in Path(
            "fragpipe.benchmark.psm_qvalues.tsv"
        ).read_text(encoding="utf-8")


def test_sage_import_command_reports_scores_and_modifications() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        fixture_dir = FIXTURE_ROOT / "search_result_bundles" / "sage"
        shutil.copy(fixture_dir / "sage_psm.tsv", "sage_psm.tsv")
        shutil.copy(fixture_dir / "sage_search.json", "sage_search.json")

        result = runner.invoke(
            cli,
            [
                "sage-import",
                "sage_psm.tsv",
                "--config",
                "sage_search.json",
                "--summary-tsv-out",
                "sage.summary.tsv",
                "--canonical-psm-tsv-out",
                "sage.canonical_psm.tsv",
                "--psm-tsv-out",
                "sage.psm.tsv",
                "--rejected-tsv-out",
                "sage.rejected.tsv",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["dialect_id"] == "sage-psm"
        assert payload["summary"]["accepted_psm_count"] == 3
        assert payload["summary"]["canonical_psm_count"] == 3
        assert payload["summary"]["modified_psm_count"] == 2
        assert payload["summary"]["hyperscore_psm_count"] == 3
        assert payload["summary"]["multi_protein_psm_count"] == 1
        assert payload["parameter_report"]["enzyme"] == "trypsin"
        assert payload["canonical_psms"][0]["record"]["run_id"] == "run01.mzML"
        assert payload["canonical_psms"][1]["record"]["protein_refs"] == [
            "sp|P23456|TRANSFER_HUMAN",
            "sp|P34567|TRANSFER_MOUSE",
        ]
        assert payload["psm_rows"][0]["hyperscore"] == 41.2
        assert payload["rejected_evidence_rows"] == []
        assert Path("sage.summary.tsv").exists()
        assert Path("sage.canonical_psm.tsv").exists()
        assert Path("sage.psm.tsv").exists()
        assert Path("sage.rejected.tsv").exists()


def test_comet_import_command_reports_tabular_and_pepxml_imports() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        fixture_dir = FIXTURE_ROOT / "search_result_bundles" / "comet"
        shutil.copy(fixture_dir / "comet_psm.tsv", "comet_psm.tsv")
        shutil.copy(fixture_dir / "comet.params", "comet.params")
        shutil.copy(fixture_dir / "comet_results.pepxml", "comet_results.pepxml")

        tabular_result = runner.invoke(
            cli,
            [
                "comet-import",
                "comet_psm.tsv",
                "--config",
                "comet.params",
                "--summary-tsv-out",
                "comet.summary.tsv",
                "--canonical-psm-tsv-out",
                "comet.canonical_psm.tsv",
                "--psm-tsv-out",
                "comet.psm.tsv",
                "--rejected-tsv-out",
                "comet.rejected.tsv",
            ],
        )
        pepxml_result = runner.invoke(cli, ["comet-import", "comet_results.pepxml"])

        assert tabular_result.exit_code == 0
        tabular_payload = json.loads(tabular_result.output)
        assert tabular_payload["import_kind"] == "tabular"
        assert tabular_payload["summary"]["accepted_psm_count"] == 3
        assert tabular_payload["summary"]["canonical_psm_count"] == 3
        assert tabular_payload["summary"]["modified_psm_count"] == 2
        assert tabular_payload["summary"]["xcorr_psm_count"] == 3
        assert tabular_payload["parameter_report"]["enzyme"] == "trypsin"
        assert (
            tabular_payload["canonical_psms"][1]["record"]["protein_refs"]
            == ["sp|P23456|TRANSFER_HUMAN", "sp|P34567|TRANSFER_MOUSE"]
        )
        assert tabular_payload["rejected_evidence_rows"] == []
        assert Path("comet.summary.tsv").exists()
        assert Path("comet.canonical_psm.tsv").exists()
        assert Path("comet.psm.tsv").exists()
        assert Path("comet.rejected.tsv").exists()

        assert pepxml_result.exit_code == 0
        pepxml_payload = json.loads(pepxml_result.output)
        assert pepxml_payload["canonical_psms"][0]["record"]["run_id"] == "run01.mzML"
        assert pepxml_payload["import_kind"] == "pepxml"
        assert pepxml_payload["summary"]["accepted_psm_count"] == 3
        assert pepxml_payload["psm_rows"][0]["xcorr"] == 3.52
        assert pepxml_payload["rejected_evidence_rows"] == []


def test_maxquant_import_command_reports_bundle_experiments_and_lfq() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        fixture_dir = FIXTURE_ROOT / "search_result_bundles" / "maxquant"
        shutil.copy(fixture_dir / "evidence.txt", "evidence.txt")
        shutil.copy(fixture_dir / "peptides.txt", "peptides.txt")
        shutil.copy(fixture_dir / "proteinGroups.txt", "proteinGroups.txt")
        shutil.copy(fixture_dir / "maxquant_settings.txt", "maxquant_settings.txt")

        result = runner.invoke(
            cli,
            [
                "maxquant-import",
                "evidence.txt",
                "--peptides-txt",
                "peptides.txt",
                "--protein-groups-txt",
                "proteinGroups.txt",
                "--config",
                "maxquant_settings.txt",
                "--summary-tsv-out",
                "maxquant.summary.tsv",
                "--evidence-tsv-out",
                "maxquant.evidence.tsv",
                "--peptide-tsv-out",
                "maxquant.peptides.tsv",
                "--protein-group-tsv-out",
                "maxquant.proteins.tsv",
                "--lfq-candidate-tsv-out",
                "maxquant.lfq_candidates.tsv",
                "--rejected-tsv-out",
                "maxquant.rejected.tsv",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["summary"]["accepted_evidence_count"] == 4
        assert payload["summary"]["peptide_row_count"] == 4
        assert payload["summary"]["protein_group_row_count"] == 4
        assert payload["summary"]["lfq_candidate_count"] == 4
        assert payload["summary"]["experiment_names"] == ["raw_A", "raw_B"]
        assert payload["summary"]["lfq_experiment_names"] == ["raw_A", "raw_B"]
        assert payload["summary"]["contaminant_evidence_count"] == 1
        assert payload["summary"]["reverse_evidence_count"] == 1
        assert payload["parameter_report"]["enzyme"] == "trypsin"
        assert (
            payload["evidence_normalization"]["adapter"]["display_name"]
            == "MaxQuant bundle evidence"
        )
        assert (
            payload["protein_group_rows"][0]["lfq_intensities"][0]["experiment_name"]
            == "raw_A"
        )
        assert payload["lfq_matrix_candidates"][2]["contaminant_flag"] is True
        assert payload["lfq_matrix_candidates"][0]["member_peptides"] == ["PESTIDE"]
        assert payload["rejected_evidence_rows"] == []
        assert Path("maxquant.summary.tsv").exists()
        assert Path("maxquant.evidence.tsv").exists()
        assert Path("maxquant.peptides.tsv").exists()
        assert Path("maxquant.proteins.tsv").exists()
        assert Path("maxquant.lfq_candidates.tsv").exists()
        assert Path("maxquant.rejected.tsv").exists()


def test_diann_import_command_reports_runs_samples_and_quantities() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        fixture_dir = FIXTURE_ROOT / "search_result_bundles" / "diann"
        shutil.copy(fixture_dir / "diann_report.tsv", "diann_report.tsv")
        shutil.copy(fixture_dir / "diann_config.json", "diann_config.json")

        result = runner.invoke(
            cli,
            [
                "diann-import",
                "diann_report.tsv",
                "--config",
                "diann_config.json",
                "--summary-tsv-out",
                "diann.summary.tsv",
                "--precursor-tsv-out",
                "diann.precursors.tsv",
                "--protein-group-tsv-out",
                "diann.protein_groups.tsv",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["summary"]["accepted_precursor_count"] == 4
        assert payload["summary"]["protein_group_row_count"] == 4
        assert payload["summary"]["run_names"] == ["raw_A", "raw_B"]
        assert payload["summary"]["sample_names"] == ["sample_A", "sample_B"]
        assert payload["summary"]["precursor_quantity_count"] == 4
        assert payload["summary"]["protein_group_quantity_count"] == 4
        assert payload["parameter_report"]["enzyme"] == "trypsin"
        assert payload["normalization"]["adapter"]["display_name"] == "DIA-NN"
        assert payload["precursor_rows"][0]["run_name"] == "raw_A"
        assert payload["precursor_rows"][2]["modified_peptide"] == "ACDM[Oxidation]K"
        assert payload["dia_native_report"]["imported_count"] == 4
        assert payload["dia_native_report"]["imported_protein_groups"][0]["quantity"] == 3400000.0
        assert payload["rejected_evidence_rows"] == []
        assert Path("diann.summary.tsv").exists()
        assert Path("diann.precursors.tsv").exists()
        assert Path("diann.protein_groups.tsv").exists()


def test_diann_import_command_exports_rejected_rows_without_failing() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        Path("diann_invalid.tsv").write_text(
            "\n".join(
                (
                    "Precursor.Id\tStripped.Sequence\tModified.Sequence\tPrecursor.Charge\tQ.Value\tProtein.Group\tProtein.Ids\tRun\tSample\tPrecursor.Quantity\tPG.Quantity\tDecoy",
                    "raw_A_PEPTIDE_2\tPEPTIDE\tPEPTIDE\t2\t0.01\tPG001\tP11111\traw_A\tsample_A\t50\t1000\t0",
                    "raw_B_BADQ_2\tBADQ\tBADQ\t2\t1.2\tPG002\tP22222\traw_B\tsample_B\t120\t2000\t0",
                )
            )
            + "\n",
            encoding="utf-8",
        )

        result = runner.invoke(
            cli,
            [
                "diann-import",
                "diann_invalid.tsv",
                "--summary-tsv-out",
                "diann.summary.tsv",
                "--rejected-tsv-out",
                "diann.rejected.tsv",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["summary"]["accepted_precursor_count"] == 1
        assert payload["summary"]["rejected_precursor_count"] == 1
        assert payload["rejected_evidence_rows"][0]["reason_code"] == "invalid_q_value"
        assert Path("diann.rejected.tsv").read_text(encoding="utf-8").startswith(
            "source_file\trow_number\tentity_type\tentity_id\treason_code\tdetail\n"
        )
        assert payload["normalization"] is None
        assert payload["rejected_rows"][0]["issues"][0]["code"] == "invalid_q_value"
        assert Path("diann.rejected.tsv").read_text(encoding="utf-8").count(
            "raw_B_BADQ_2"
        ) == 1


def test_diann_precursor_matrix_command_emits_sample_matrix_outputs() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        fixture_dir = FIXTURE_ROOT / "search_result_bundles" / "diann"
        shutil.copy(fixture_dir / "diann_report.tsv", "diann_report.tsv")

        result = runner.invoke(
            cli,
            [
                "diann-precursor-matrix",
                "diann_report.tsv",
                "--summary-tsv-out",
                "diann.matrix.summary.tsv",
                "--matrix-tsv-out",
                "diann.matrix.tsv",
                "--qvalue-tsv-out",
                "diann.qvalues.tsv",
                "--metadata-tsv-out",
                "diann.metadata.tsv",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["source_name"] == "DIA-NN"
        assert payload["sample_ids"] == ["sample_A", "sample_B"]
        assert payload["policy"]["q_value_filter_timing"] == "before_matrix_construction"
        assert payload["summary"]["precursor_row_count"] == 2
        assert payload["summary"]["observed_cell_count"] == 3
        assert payload["summary"]["excluded_decoy_count"] == 1
        assert payload["rows"][0]["modified_peptide"] == "ACDM[Oxidation]K"
        assert payload["outputs"]["summary_tsv"] == "diann.matrix.summary.tsv"
        assert payload["outputs"]["matrix_tsv"] == "diann.matrix.tsv"
        assert payload["outputs"]["qvalue_tsv"] == "diann.qvalues.tsv"
        assert payload["outputs"]["metadata_tsv"] == "diann.metadata.tsv"
        assert Path("diann.matrix.summary.tsv").exists()
        assert Path("diann.matrix.tsv").exists()
        assert Path("diann.qvalues.tsv").exists()
        assert Path("diann.metadata.tsv").exists()
        assert "precursor_key\tpeptide_sequence\tmodified_peptide" in Path(
            "diann.matrix.tsv"
        ).read_text(encoding="utf-8")
        assert "source_name\tsample_count\trun_count\tprecursor_row_count" in Path(
            "diann.matrix.summary.tsv"
        ).read_text(encoding="utf-8")
        assert "\t0.0021\t0.0024\n" in Path("diann.qvalues.tsv").read_text(
            encoding="utf-8"
        )
        assert "retained_observation_count" in Path("diann.metadata.tsv").read_text(
            encoding="utf-8"
        )


def test_spectronaut_precursor_matrix_command_emits_sample_matrix_outputs() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        fixture_dir = FIXTURE_ROOT / "search_result_bundles" / "spectronaut"
        shutil.copy(fixture_dir / "spectronaut_report.tsv", "spectronaut_report.tsv")
        shutil.copy(
            fixture_dir / "spectronaut_settings.txt",
            "spectronaut_settings.txt",
        )

        result = runner.invoke(
            cli,
            [
                "spectronaut-precursor-matrix",
                "spectronaut_report.tsv",
                "--config",
                "spectronaut_settings.txt",
                "--summary-tsv-out",
                "spectronaut.matrix.summary.tsv",
                "--matrix-tsv-out",
                "spectronaut.matrix.tsv",
                "--qvalue-tsv-out",
                "spectronaut.qvalues.tsv",
                "--metadata-tsv-out",
                "spectronaut.metadata.tsv",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["source_name"] == "Spectronaut"
        assert payload["sample_ids"] == ["sample_A", "sample_B"]
        assert payload["summary"]["precursor_row_count"] == 2
        assert payload["summary"]["excluded_decoy_count"] == 1
        assert payload["outputs"]["metadata_tsv"] == "spectronaut.metadata.tsv"
        assert Path("spectronaut.matrix.summary.tsv").exists()
        assert Path("spectronaut.matrix.tsv").exists()
        assert Path("spectronaut.qvalues.tsv").exists()
        assert Path("spectronaut.metadata.tsv").exists()
        assert "precursor_key\tpeptide_sequence\tmodified_peptide" in Path(
            "spectronaut.matrix.tsv"
        ).read_text(encoding="utf-8")
        assert "excluded_q_value_observation_count" in Path(
            "spectronaut.metadata.tsv"
        ).read_text(encoding="utf-8")


def test_diann_protein_matrix_command_emits_peptide_and_protein_outputs() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        fixture_dir = FIXTURE_ROOT / "search_result_bundles" / "diann"
        shutil.copy(fixture_dir / "diann_report.tsv", "diann_report.tsv")

        result = runner.invoke(
            cli,
            [
                "diann-protein-matrix",
                "diann_report.tsv",
                "--target-kind",
                "protein_group",
                "--shared-peptides",
                "include",
                "--summary-tsv-out",
                "diann.protein.summary.tsv",
                "--peptide-tsv-out",
                "diann.peptide.matrix.tsv",
                "--protein-tsv-out",
                "diann.protein.matrix.tsv",
                "--rollup-evidence-tsv-out",
                "diann.rollup.evidence.tsv",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["source_name"] == "DIA-NN"
        assert payload["sample_ids"] == ["sample_A", "sample_B"]
        assert payload["peptide_rollup_method"] == "max"
        assert payload["target_kind"] == "protein_group"
        assert payload["shared_peptide_policy"] == "include"
        assert payload["protein_rollup_method"] == "sum"
        assert payload["peptide_summary"]["peptide_row_count"] == 2
        assert payload["protein_summary"]["protein_row_count"] == 2
        assert payload["protein_summary"]["observed_cell_count"] == 3
        assert payload["protein_summary"]["rollup_evidence_entry_count"] >= 6
        assert payload["protein_rows"][0]["entity_id"] == "PG001"
        assert payload["outputs"]["summary_tsv"] == "diann.protein.summary.tsv"
        assert payload["outputs"]["peptide_tsv"] == "diann.peptide.matrix.tsv"
        assert payload["outputs"]["protein_tsv"] == "diann.protein.matrix.tsv"
        assert payload["outputs"]["rollup_evidence_tsv"] == "diann.rollup.evidence.tsv"
        assert Path("diann.protein.summary.tsv").exists()
        assert Path("diann.peptide.matrix.tsv").exists()
        assert Path("diann.protein.matrix.tsv").exists()
        assert Path("diann.rollup.evidence.tsv").exists()
        assert "peptide_key\tpeptide_sequence\tmodified_peptide" in Path(
            "diann.peptide.matrix.tsv"
        ).read_text(encoding="utf-8")
        assert "entity_id\ttarget_kind\tprotein_refs\tpeptide_count" in Path(
            "diann.protein.matrix.tsv"
        ).read_text(encoding="utf-8")
        assert "rollup_stage\ttarget_entity_level\ttarget_entity_id" in Path(
            "diann.rollup.evidence.tsv"
        ).read_text(encoding="utf-8")
        assert "source_name\ttarget_kind\tshared_peptide_policy\trollup_method" in (
            Path("diann.protein.summary.tsv").read_text(encoding="utf-8")
        )


def test_spectronaut_protein_matrix_command_emits_rollup_outputs() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        fixture_dir = FIXTURE_ROOT / "search_result_bundles" / "spectronaut"
        shutil.copy(fixture_dir / "spectronaut_report.tsv", "spectronaut_report.tsv")
        shutil.copy(
            fixture_dir / "spectronaut_settings.txt",
            "spectronaut_settings.txt",
        )

        result = runner.invoke(
            cli,
            [
                "spectronaut-protein-matrix",
                "spectronaut_report.tsv",
                "--config",
                "spectronaut_settings.txt",
                "--summary-tsv-out",
                "spectronaut.protein.summary.tsv",
                "--peptide-tsv-out",
                "spectronaut.peptide.matrix.tsv",
                "--protein-tsv-out",
                "spectronaut.protein.matrix.tsv",
                "--rollup-evidence-tsv-out",
                "spectronaut.rollup.evidence.tsv",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["source_name"] == "Spectronaut"
        assert payload["sample_ids"] == ["sample_A", "sample_B"]
        assert payload["protein_summary"]["protein_row_count"] == 2
        assert payload["outputs"]["rollup_evidence_tsv"] == "spectronaut.rollup.evidence.tsv"
        assert Path("spectronaut.rollup.evidence.tsv").exists()
        assert "rollup_stage\ttarget_entity_level\ttarget_entity_id" in Path(
            "spectronaut.rollup.evidence.tsv"
        ).read_text(encoding="utf-8")


def test_diann_run_qc_command_emits_qc_ledgers_and_outlier_calls() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        fixture_dir = FIXTURE_ROOT / "search_result_bundles" / "diann"
        shutil.copy(
            fixture_dir / "diann_run_qc_report.tsv",
            "diann_run_qc_report.tsv",
        )

        result = runner.invoke(
            cli,
            [
                "diann-run-qc",
                "diann_run_qc_report.tsv",
                "--summary-tsv-out",
                "diann.run_qc.summary.tsv",
                "--run-tsv-out",
                "diann.run_qc.runs.tsv",
                "--intensity-tsv-out",
                "diann.run_qc.intensity.tsv",
                "--correlation-tsv-out",
                "diann.run_qc.correlation.tsv",
                "--outlier-tsv-out",
                "diann.run_qc.outliers.tsv",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["source_name"] == "DIA-NN"
        assert payload["summary"]["run_count"] == 3
        assert payload["summary"]["flagged_run_count"] == 1
        assert payload["summary"]["weak_run_flag_count"] == 5
        assert payload["run_entries"][2]["run_name"] == "raw_C"
        assert payload["run_entries"][2]["weak_run_flag_count"] == 5
        assert payload["run_entries"][2]["flagged"] is True
        assert payload["outlier_runs"][0]["run_name"] == "raw_C"
        assert payload["outlier_runs"][0]["flags"][0]["threshold_name"] == "high_missing_fraction"
        assert payload["outputs"]["summary_tsv"] == "diann.run_qc.summary.tsv"
        assert payload["outputs"]["run_tsv"] == "diann.run_qc.runs.tsv"
        assert payload["outputs"]["intensity_tsv"] == "diann.run_qc.intensity.tsv"
        assert (
            payload["outputs"]["correlation_tsv"]
            == "diann.run_qc.correlation.tsv"
        )
        assert payload["outputs"]["outlier_tsv"] == "diann.run_qc.outliers.tsv"
        assert Path("diann.run_qc.summary.tsv").exists()
        assert Path("diann.run_qc.runs.tsv").exists()
        assert Path("diann.run_qc.intensity.tsv").exists()
        assert Path("diann.run_qc.correlation.tsv").exists()
        assert Path("diann.run_qc.outliers.tsv").exists()
        assert "run_name\tsample_name\tprecursor_id_count" in Path(
            "diann.run_qc.runs.tsv"
        ).read_text(encoding="utf-8")
        assert "weak_run_flag_count" in Path(
            "diann.run_qc.summary.tsv"
        ).read_text(encoding="utf-8")
        assert "run_name_a\tsample_name_a\trun_name_b\tsample_name_b" in Path(
            "diann.run_qc.correlation.tsv"
        ).read_text(encoding="utf-8")
        assert "reason_code\treason\tthreshold_name\tthreshold_value\tobserved_value" in Path(
            "diann.run_qc.outliers.tsv"
        ).read_text(encoding="utf-8")
        assert "raw_C\tsample_C\tlow_precursor_coverage" in Path(
            "diann.run_qc.outliers.tsv"
        ).read_text(encoding="utf-8")


def test_tmt_reporter_matrix_command_emits_mapping_totals_and_matrices() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        fixture_dir = FIXTURE_ROOT / "multiplex"
        shutil.copy(
            fixture_dir / "maxquant_tmt_evidence.tsv",
            "maxquant_tmt_evidence.tsv",
        )
        shutil.copy(fixture_dir / "tmt.design.tsv", "tmt.design.tsv")

        result = runner.invoke(
            cli,
            [
                "multiplex",
                "tmt-reporter-matrix",
                "maxquant_tmt_evidence.tsv",
                "tmt.design.tsv",
                "--source-kind",
                "maxquant",
                "--summary-tsv-out",
                "tmt.summary.tsv",
                "--channel-mapping-tsv-out",
                "tmt.channel_mapping.tsv",
                "--channel-totals-tsv-out",
                "tmt.channel_totals.tsv",
                "--peptide-matrix-tsv-out",
                "tmt.peptide_matrix.tsv",
                "--protein-matrix-tsv-out",
                "tmt.protein_matrix.tsv",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["source_kind"] == "maxquant"
        assert payload["source_report"]["summary"]["accepted_row_count"] == 4
        assert payload["feature_bundle"]["summary"]["missing_channel_count"] == 2
        assert payload["report"]["summary"]["peptide_row_count"] == 2
        assert payload["report"]["summary"]["protein_row_count"] == 2
        assert payload["outputs"]["summary_tsv"] == "tmt.summary.tsv"
        assert payload["outputs"]["peptide_matrix_tsv"] == "tmt.peptide_matrix.tsv"
        assert Path("tmt.summary.tsv").exists()
        assert Path("tmt.channel_mapping.tsv").exists()
        assert Path("tmt.channel_totals.tsv").exists()
        assert Path("tmt.peptide_matrix.tsv").exists()
        assert Path("tmt.protein_matrix.tsv").exists()
        assert "plex_a_129N" in Path("tmt.peptide_matrix.tsv").read_text(
            encoding="utf-8"
        )
        assert "P001" in Path("tmt.protein_matrix.tsv").read_text(encoding="utf-8")
        assert "total_intensity" in Path("tmt.channel_totals.tsv").read_text(
            encoding="utf-8"
        )
        assert "mapped_to_design" in Path("tmt.channel_mapping.tsv").read_text(
            encoding="utf-8"
        )


def test_tmt_normalize_command_emits_distribution_and_normalized_matrices() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        fixture_dir = FIXTURE_ROOT / "multiplex"
        shutil.copy(
            fixture_dir / "maxquant_tmt_evidence.tsv",
            "maxquant_tmt_evidence.tsv",
        )
        shutil.copy(fixture_dir / "tmt.design.tsv", "tmt.design.tsv")

        result = runner.invoke(
            cli,
            [
                "multiplex",
                "tmt-normalize",
                "maxquant_tmt_evidence.tsv",
                "tmt.design.tsv",
                "--source-kind",
                "maxquant",
                "--method",
                "reference_channel",
                "--summary-tsv-out",
                "tmt.normalize.summary.tsv",
                "--transform-tsv-out",
                "tmt.normalize.transforms.tsv",
                "--distribution-tsv-out",
                "tmt.normalize.distributions.tsv",
                "--peptide-matrix-tsv-out",
                "tmt.normalize.peptides.tsv",
                "--protein-matrix-tsv-out",
                "tmt.normalize.proteins.tsv",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["source_kind"] == "maxquant"
        assert (
            payload["report"]["summary"]["method"] == "reference_channel"
        )
        assert payload["report"]["summary"]["reference_group_count"] == 2
        assert Path("tmt.normalize.summary.tsv").exists()
        assert Path("tmt.normalize.transforms.tsv").exists()
        assert Path("tmt.normalize.distributions.tsv").exists()
        assert Path("tmt.normalize.peptides.tsv").exists()
        assert Path("tmt.normalize.proteins.tsv").exists()
        assert "reference_group_count" in Path(
            "tmt.normalize.summary.tsv"
        ).read_text(encoding="utf-8")
        assert "reference_channel" in Path(
            "tmt.normalize.transforms.tsv"
        ).read_text(encoding="utf-8")
        assert "stage\tmultiplex_group\tmultiplex_channel" in Path(
            "tmt.normalize.distributions.tsv"
        ).read_text(encoding="utf-8")
        assert "plex_a_128N" in Path("tmt.normalize.peptides.tsv").read_text(
            encoding="utf-8"
        )
        assert "entity_id\ttarget_kind\tprotein_refs" in Path(
            "tmt.normalize.proteins.tsv"
        ).read_text(encoding="utf-8")


def test_tmt_interference_command_emits_filtered_and_channel_summary_outputs() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        fixture_dir = FIXTURE_ROOT / "multiplex"
        shutil.copy(
            fixture_dir / "maxquant_tmt_interference.tsv",
            "maxquant_tmt_interference.tsv",
        )
        shutil.copy(fixture_dir / "tmt.design.tsv", "tmt.design.tsv")

        result = runner.invoke(
            cli,
            [
                "multiplex",
                "tmt-interference",
                "maxquant_tmt_interference.tsv",
                "tmt.design.tsv",
                "--source-kind",
                "maxquant",
                "--summary-tsv-out",
                "tmt.interference.summary.tsv",
                "--observation-tsv-out",
                "tmt.interference.observations.tsv",
                "--filtered-tsv-out",
                "tmt.interference.filtered.tsv",
                "--channel-summary-tsv-out",
                "tmt.interference.channels.tsv",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["source_kind"] == "maxquant"
        assert payload["report"]["summary"]["observed_channel_row_count"] == 12
        assert payload["report"]["summary"]["filtered_channel_row_count"] == 6
        assert payload["report"]["summary"]["channel_summary_count"] == 6
        assert Path("tmt.interference.summary.tsv").exists()
        assert Path("tmt.interference.observations.tsv").exists()
        assert Path("tmt.interference.filtered.tsv").exists()
        assert Path("tmt.interference.channels.tsv").exists()
        assert "filtered_channel_row_count" in Path(
            "tmt.interference.summary.tsv"
        ).read_text(encoding="utf-8")
        assert "threshold_exceeded" in Path(
            "tmt.interference.observations.tsv"
        ).read_text(encoding="utf-8")
        assert "considered unreliable" in Path(
            "tmt.interference.filtered.tsv"
        ).read_text(encoding="utf-8")
        assert "mean_interference_fraction" in Path(
            "tmt.interference.channels.tsv"
        ).read_text(encoding="utf-8")


def test_tmt_report_command_emits_report_directory_and_manifest() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        fixture_dir = FIXTURE_ROOT / "multiplex"
        shutil.copy(
            fixture_dir / "maxquant_tmt_interference.tsv",
            "maxquant_tmt_interference.tsv",
        )
        shutil.copy(fixture_dir / "tmt.design.tsv", "tmt.design.tsv")

        result = runner.invoke(
            cli,
            [
                "multiplex",
                "tmt-report",
                "maxquant_tmt_interference.tsv",
                "tmt.design.tsv",
                "--control-channel",
                "126",
                "--output-dir",
                "tmt_report",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["source_kind"] == "maxquant"
        assert payload["control_channel"] == "126"
        assert payload["report"]["summary"]["sample_qc_entry_count"] == 8
        report_dir = Path("tmt_report")
        assert (report_dir / "tmt_workflow_manifest.json").exists()
        assert (report_dir / "tmt_workflow_summary.tsv").exists()
        assert (report_dir / "tmt_reporter_import_summary.tsv").exists()
        assert (report_dir / "tmt_reporter_rows.tsv").exists()
        assert (report_dir / "tmt_reporter_rejected_rows.tsv").exists()
        assert (report_dir / "tmt_metadata_summary.tsv").exists()
        assert (report_dir / "tmt_channel_assignments.tsv").exists()
        assert (report_dir / "label_based_report_manifest.json").exists()
        assert (report_dir / "label_based_report_summary.tsv").exists()
        assert (report_dir / "label_based_sample_qc.tsv").exists()
        assert (report_dir / "tmt_channel_totals.tsv").exists()
        assert (report_dir / "tmt_interference_summary.tsv").exists()
        assert (report_dir / "tmt_interference_observations.tsv").exists()
        assert (report_dir / "tmt_filtered_interference.tsv").exists()
        assert (report_dir / "tmt_interference_channel_summary.tsv").exists()
        assert (report_dir / "tmt_protein_ratios.tsv").exists()
        assert (report_dir / "label_based_differential_results.tsv").exists()
        assert "accepted_input_row_count" in (
            report_dir / "tmt_workflow_summary.tsv"
        ).read_text(encoding="utf-8")
        assert "quality_entry_count" in (
            report_dir / "label_based_report_summary.tsv"
        ).read_text(encoding="utf-8")
        assert "assay_axis" in (
            report_dir / "label_based_sample_qc.tsv"
        ).read_text(encoding="utf-8")
        assert "total_intensity" in (
            report_dir / "tmt_channel_totals.tsv"
        ).read_text(encoding="utf-8")
        assert "threshold_exceeded_count" in (
            report_dir / "tmt_interference_summary.tsv"
        ).read_text(encoding="utf-8")
        assert "mean_interference_fraction" in (
            report_dir / "tmt_interference_channel_summary.tsv"
        ).read_text(encoding="utf-8")
        assert "ratio" in (
            report_dir / "tmt_protein_ratios.tsv"
        ).read_text(encoding="utf-8")


def test_tmt_ratio_command_emits_peptide_protein_and_missing_ratio_outputs() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        fixture_dir = FIXTURE_ROOT / "multiplex"
        shutil.copy(
            fixture_dir / "maxquant_tmt_evidence.tsv",
            "maxquant_tmt_evidence.tsv",
        )
        shutil.copy(fixture_dir / "tmt.design.tsv", "tmt.design.tsv")

        result = runner.invoke(
            cli,
            [
                "multiplex",
                "tmt-ratios",
                "maxquant_tmt_evidence.tsv",
                "tmt.design.tsv",
                "--source-kind",
                "maxquant",
                "--control-channel",
                "126",
                "--summary-tsv-out",
                "tmt.ratio.summary.tsv",
                "--peptide-tsv-out",
                "tmt.ratio.peptides.tsv",
                "--protein-tsv-out",
                "tmt.ratio.proteins.tsv",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["source_kind"] == "maxquant"
        assert payload["control_channel"] == "126"
        assert payload["report"]["summary"]["control_channel"] == "126"
        assert payload["report"]["summary"]["normalization_method"] == "none"
        assert payload["report"]["summary"]["peptide_ratio_count"] == 12
        assert payload["report"]["summary"]["protein_ratio_count"] == 12
        assert payload["report"]["summary"]["missing_ratio_count"] == 8
        assert Path("tmt.ratio.summary.tsv").exists()
        assert Path("tmt.ratio.peptides.tsv").exists()
        assert Path("tmt.ratio.proteins.tsv").exists()
        assert "missing_ratio_count" in Path("tmt.ratio.summary.tsv").read_text(
            encoding="utf-8"
        )
        assert "sample_channel_missing" in Path(
            "tmt.ratio.peptides.tsv"
        ).read_text(encoding="utf-8")
        assert "P001" in Path("tmt.ratio.proteins.tsv").read_text(encoding="utf-8")


def test_silac_quantify_command_emits_peptide_and_protein_ratio_outputs() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        fixture_dir = FIXTURE_ROOT / "isotope_labeling"
        shutil.copy(fixture_dir / "silac_features.tsv", "silac_features.tsv")

        result = runner.invoke(
            cli,
            [
                "isotope-labeling",
                "silac-quantify",
                "silac_features.tsv",
                "--labels",
                "light,medium,heavy",
                "--collapse-charge-states",
                "--summary-tsv-out",
                "silac.summary.tsv",
                "--peptide-tsv-out",
                "silac.peptides.tsv",
                "--protein-tsv-out",
                "silac.proteins.tsv",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["import_report"]["summary"]["sample_count"] == 2
        assert payload["report"]["summary"]["expected_label_count"] == 3
        assert payload["report"]["summary"]["peptide_ratio_count"] == 8
        assert payload["report"]["summary"]["protein_ratio_count"] == 8
        assert payload["report"]["summary"]["missing_ratio_count"] == 4
        assert Path("silac.summary.tsv").exists()
        assert Path("silac.peptides.tsv").exists()
        assert Path("silac.proteins.tsv").exists()
        assert "protein_ratio_count" in Path("silac.summary.tsv").read_text(
            encoding="utf-8"
        )
        assert "numerator_label_missing" in Path("silac.peptides.tsv").read_text(
            encoding="utf-8"
        )
        assert "sample_a\tP001\tP001\tPEPTIDE\tmedium\tlight\t2000.0\t1500.0" in Path(
            "silac.proteins.tsv"
        ).read_text(encoding="utf-8")


def test_silac_differential_command_emits_matrix_result_and_balance_outputs() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        fixture_dir = FIXTURE_ROOT / "isotope_labeling"
        shutil.copy(
            fixture_dir / "silac_differential_features.tsv",
            "silac_differential_features.tsv",
        )
        shutil.copy(
            fixture_dir / "silac_differential.design.tsv",
            "silac_differential.design.tsv",
        )

        result = runner.invoke(
            cli,
            [
                "isotope-labeling",
                "silac-differential",
                "silac_differential_features.tsv",
                "silac_differential.design.tsv",
                "--raw-matrix-tsv-out",
                "silac.diff.raw.tsv",
                "--normalized-matrix-tsv-out",
                "silac.diff.normalized.tsv",
                "--results-tsv-out",
                "silac.diff.results.tsv",
                "--balance-tsv-out",
                "silac.diff.balance.tsv",
                "--volcano-tsv-out",
                "silac.diff.volcano.tsv",
                "--volcano-json-out",
                "silac.diff.volcano.json",
                "--volcano-svg-out",
                "silac.diff.volcano.svg",
                "--volcano-html-out",
                "silac.diff.volcano.html",
                "--volcano-top-label-count",
                "1",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["report"]["design_matrix"]["sample_count"] == 4
        assert payload["report"]["differential_abundance_report"] is not None
        assert payload["volcano_review"]["labeled_point_count"] == 1
        assert Path("silac.diff.raw.tsv").exists()
        assert Path("silac.diff.normalized.tsv").exists()
        assert Path("silac.diff.results.tsv").exists()
        assert Path("silac.diff.balance.tsv").exists()
        assert Path("silac.diff.volcano.tsv").exists()
        assert Path("silac.diff.volcano.json").exists()
        assert Path("silac.diff.volcano.svg").exists()
        assert Path("silac.diff.volcano.html").exists()
        assert "member_peptides" in Path("silac.diff.raw.tsv").read_text(
            encoding="utf-8"
        )
        assert "adjusted_p_value" in Path("silac.diff.results.tsv").read_text(
            encoding="utf-8"
        )
        assert "raw_p_value" in Path(
            "silac.diff.volcano.tsv"
        ).read_text(encoding="utf-8")
        assert '"source_kind": "label_based"' in Path(
            "silac.diff.volcano.json"
        ).read_text(encoding="utf-8")
        assert "<svg" in Path("silac.diff.volcano.svg").read_text(encoding="utf-8")
        assert "Volcano plot:" in Path("silac.diff.volcano.html").read_text(
            encoding="utf-8"
        )


def test_silac_report_command_emits_report_directory_and_manifest() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        fixture_dir = FIXTURE_ROOT / "isotope_labeling"
        shutil.copy(
            fixture_dir / "silac_differential_features.tsv",
            "silac_differential_features.tsv",
        )
        shutil.copy(
            fixture_dir / "silac_differential.design.tsv",
            "silac_differential.design.tsv",
        )

        result = runner.invoke(
            cli,
            [
                "isotope-labeling",
                "silac-report",
                "silac_differential_features.tsv",
                "silac_differential.design.tsv",
                "--output-dir",
                "silac_report",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["report"]["summary"]["sample_qc_entry_count"] == 4
        report_dir = Path("silac_report")
        assert (report_dir / "label_based_report_manifest.json").exists()
        assert (report_dir / "label_based_report_summary.tsv").exists()
        assert (report_dir / "label_based_sample_qc.tsv").exists()
        assert (report_dir / "silac_ratio_summary.tsv").exists()
        assert (report_dir / "silac_protein_ratios.tsv").exists()
        assert (report_dir / "label_based_differential_results.tsv").exists()
        assert "protein_ratio_count" in (
            report_dir / "label_based_report_summary.tsv"
        ).read_text(encoding="utf-8")
        assert "assay_axis" in (
            report_dir / "label_based_sample_qc.tsv"
        ).read_text(encoding="utf-8")
        assert "reference_label" in (
            report_dir / "silac_protein_ratios.tsv"
        ).read_text(encoding="utf-8")


def test_silac_validate_command_emits_label_distribution_and_weak_outputs() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        fixture_dir = FIXTURE_ROOT / "isotope_labeling"
        shutil.copy(fixture_dir / "silac_features.tsv", "silac_features.tsv")

        result = runner.invoke(
            cli,
            [
                "isotope-labeling",
                "silac-validate",
                "silac_features.tsv",
                "--labels",
                "light,medium,heavy",
                "--summary-tsv-out",
                "silac.validation.summary.tsv",
                "--label-tsv-out",
                "silac.validation.labels.tsv",
                "--distribution-tsv-out",
                "silac.validation.distribution.tsv",
                "--weak-tsv-out",
                "silac.validation.weak.tsv",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["report"]["summary"]["sample_count"] == 2
        assert payload["report"]["summary"]["missing_pair_member_count"] == 2
        assert payload["report"]["summary"]["abnormal_distribution_count"] == 1
        assert payload["report"]["summary"]["weak_label_count"] == 2
        assert "sample_b\tmedium\t2\t1\t1" in Path(
            "silac.validation.labels.tsv"
        ).read_text(encoding="utf-8")
        assert "sample_b\tmedium\t1500.0\t2200.0" in Path(
            "silac.validation.distribution.tsv"
        ).read_text(encoding="utf-8")
        assert "weak_total_intensity" in Path(
            "silac.validation.weak.tsv"
        ).read_text(encoding="utf-8")


def test_tmt_validate_command_emits_channel_distribution_and_weak_outputs() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        fixture_dir = FIXTURE_ROOT / "multiplex"
        shutil.copy(
            fixture_dir / "maxquant_tmt_evidence.tsv",
            "maxquant_tmt_evidence.tsv",
        )
        shutil.copy(fixture_dir / "tmt.design.tsv", "tmt.design.tsv")

        result = runner.invoke(
            cli,
            [
                "isotope-labeling",
                "tmt-validate",
                "maxquant_tmt_evidence.tsv",
                "tmt.design.tsv",
                "--source-kind",
                "maxquant",
                "--summary-tsv-out",
                "tmt.validation.summary.tsv",
                "--channel-tsv-out",
                "tmt.validation.channels.tsv",
                "--distribution-tsv-out",
                "tmt.validation.distribution.tsv",
                "--weak-tsv-out",
                "tmt.validation.weak.tsv",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["source_kind"] == "maxquant"
        assert payload["report"]["summary"]["expected_channel_count"] == 8
        assert payload["report"]["summary"]["missing_channel_count"] == 2
        assert payload["report"]["summary"]["weak_channel_count"] == 2
        assert "plex-a\t129N\tplex_a_129N" in Path(
            "tmt.validation.channels.tsv"
        ).read_text(encoding="utf-8")
        assert "plex-a\t126\tplex_a_126" in Path(
            "tmt.validation.distribution.tsv"
        ).read_text(encoding="utf-8")
        assert "channel_missing" in Path("tmt.validation.weak.tsv").read_text(
            encoding="utf-8"
        )


def test_multiplex_validate_metadata_command_emits_assignment_issue_outputs() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        fixture_dir = FIXTURE_ROOT / "multiplex"
        shutil.copy(
            fixture_dir / "tmt_metadata_issues.design.tsv",
            "tmt_metadata_issues.design.tsv",
        )

        result = runner.invoke(
            cli,
            [
                "multiplex",
                "validate-metadata",
                "tmt_metadata_issues.design.tsv",
                "--summary-tsv-out",
                "multiplex.metadata.summary.tsv",
                "--channel-tsv-out",
                "multiplex.metadata.channels.tsv",
                "--duplicate-tsv-out",
                "multiplex.metadata.duplicates.tsv",
                "--missing-condition-tsv-out",
                "multiplex.metadata.conditions.tsv",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["report"]["summary"]["multiplex_group_count"] == 2
        assert payload["report"]["summary"]["missing_channel_assignment_count"] == 1
        assert payload["report"]["summary"]["duplicate_assignment_count"] == 2
        assert payload["report"]["summary"]["missing_condition_count"] == 1
        assert "plex-b\t129N\t\t\t\tFalse" in Path(
            "multiplex.metadata.channels.tsv"
        ).read_text(encoding="utf-8")
        assert "duplicate_channel_assignment\tplex-b\t127N" in Path(
            "multiplex.metadata.duplicates.tsv"
        ).read_text(encoding="utf-8")
        assert "plex-b\t128N\tplex_b_128N\tpooled_reference" in Path(
            "multiplex.metadata.conditions.tsv"
        ).read_text(encoding="utf-8")


def test_tmt_integrate_plexes_command_emits_alignment_effect_and_matrix_outputs() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        fixture_dir = FIXTURE_ROOT / "multiplex"
        shutil.copy(
            fixture_dir / "maxquant_tmt_evidence.tsv",
            "maxquant_tmt_evidence.tsv",
        )
        shutil.copy(fixture_dir / "tmt.design.tsv", "tmt.design.tsv")

        result = runner.invoke(
            cli,
            [
                "multiplex",
                "tmt-integrate-plexes",
                "maxquant_tmt_evidence.tsv",
                "tmt.design.tsv",
                "--source-kind",
                "maxquant",
                "--summary-tsv-out",
                "tmt.integration.summary.tsv",
                "--alignment-tsv-out",
                "tmt.integration.alignment.tsv",
                "--plex-effect-tsv-out",
                "tmt.integration.effects.tsv",
                "--protein-matrix-tsv-out",
                "tmt.integration.proteins.tsv",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["source_kind"] == "maxquant"
        assert payload["report"]["summary"]["multiplex_group_count"] == 2
        assert payload["report"]["summary"]["integrated_sample_count"] == 4
        assert payload["report"]["summary"]["protein_row_count"] == 2
        assert payload["outputs"]["summary_tsv"] == "tmt.integration.summary.tsv"
        assert Path("tmt.integration.summary.tsv").exists()
        assert Path("tmt.integration.alignment.tsv").exists()
        assert Path("tmt.integration.effects.tsv").exists()
        assert Path("tmt.integration.proteins.tsv").exists()
        assert "bridge_sample_id" in Path(
            "tmt.integration.alignment.tsv"
        ).read_text(encoding="utf-8")
        assert "ratio_to_global_bridge_median" in Path(
            "tmt.integration.effects.tsv"
        ).read_text(encoding="utf-8")
        assert "P001" in Path("tmt.integration.proteins.tsv").read_text(
            encoding="utf-8"
        )


def test_tmt_differential_command_emits_matrix_result_and_balance_outputs() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        fixture_dir = FIXTURE_ROOT / "multiplex"
        shutil.copy(
            fixture_dir / "maxquant_tmt_evidence.tsv",
            "maxquant_tmt_evidence.tsv",
        )
        shutil.copy(fixture_dir / "tmt.design.tsv", "tmt.design.tsv")

        result = runner.invoke(
            cli,
            [
                "multiplex",
                "tmt-differential",
                "maxquant_tmt_evidence.tsv",
                "tmt.design.tsv",
                "--source-kind",
                "maxquant",
                "--raw-matrix-tsv-out",
                "tmt.diff.raw.tsv",
                "--normalized-matrix-tsv-out",
                "tmt.diff.normalized.tsv",
                "--results-tsv-out",
                "tmt.diff.results.tsv",
                "--balance-tsv-out",
                "tmt.diff.balance.tsv",
                "--volcano-tsv-out",
                "tmt.diff.volcano.tsv",
                "--volcano-json-out",
                "tmt.diff.volcano.json",
                "--volcano-svg-out",
                "tmt.diff.volcano.svg",
                "--volcano-html-out",
                "tmt.diff.volcano.html",
                "--volcano-top-label-count",
                "1",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["source_kind"] == "maxquant"
        assert payload["report"]["design_matrix"]["sample_count"] == 4
        assert payload["report"]["differential_abundance_report"] is not None
        assert payload["volcano_review"]["labeled_point_count"] == 1
        assert Path("tmt.diff.raw.tsv").exists()
        assert Path("tmt.diff.normalized.tsv").exists()
        assert Path("tmt.diff.results.tsv").exists()
        assert Path("tmt.diff.balance.tsv").exists()
        assert Path("tmt.diff.volcano.tsv").exists()
        assert Path("tmt.diff.volcano.json").exists()
        assert Path("tmt.diff.volcano.svg").exists()
        assert Path("tmt.diff.volcano.html").exists()
        assert "member_peptides" in Path("tmt.diff.raw.tsv").read_text(
            encoding="utf-8"
        )
        assert "adjusted_p_value" in Path("tmt.diff.results.tsv").read_text(
            encoding="utf-8"
        )
        assert "raw_p_value" in Path("tmt.diff.volcano.tsv").read_text(
            encoding="utf-8"
        )
        assert '"source_kind": "label_based"' in Path(
            "tmt.diff.volcano.json"
        ).read_text(encoding="utf-8")
        assert "<svg" in Path("tmt.diff.volcano.svg").read_text(encoding="utf-8")
        assert "Volcano plot:" in Path("tmt.diff.volcano.html").read_text(
            encoding="utf-8"
        )
        assert "interquartile_range" in Path("tmt.diff.balance.tsv").read_text(
            encoding="utf-8"
        )


def test_diann_library_coverage_command_emits_identity_and_scope_ledgers() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        fixture_dir = FIXTURE_ROOT / "search_result_bundles" / "diann"
        format_dir = FIXTURE_ROOT / "formats"
        shutil.copy(
            fixture_dir / "diann_library_coverage.tsv",
            "diann_library_coverage.tsv",
        )
        shutil.copy(
            format_dir / "diann_library_coverage.msp",
            "diann_library_coverage.msp",
        )
        shutil.copy(
            format_dir / "diann_library_coverage.design.tsv",
            "diann_library_coverage.design.tsv",
        )

        result = runner.invoke(
            cli,
            [
                "diann-library-coverage",
                "diann_library_coverage.tsv",
                "diann_library_coverage.msp",
                "--design",
                "diann_library_coverage.design.tsv",
                "--summary-tsv-out",
                "diann.library.summary.tsv",
                "--sample-tsv-out",
                "diann.library.samples.tsv",
                "--condition-tsv-out",
                "diann.library.conditions.tsv",
                "--peptide-tsv-out",
                "diann.library.peptides.tsv",
                "--protein-tsv-out",
                "diann.library.proteins.tsv",
                "--outside-library-peptide-tsv-out",
                "diann.library.outside.peptides.tsv",
                "--outside-library-protein-tsv-out",
                "diann.library.outside.proteins.tsv",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["source_name"] == "DIA-NN"
        assert payload["library_source_format"] == "msp"
        assert payload["summary"]["library_peptide_count"] == 5
        assert payload["summary"]["detected_peptide_count"] == 4
        assert payload["summary"]["observed_outside_library_peptide_count"] == 1
        assert payload["summary"]["library_protein_count"] == 5
        assert payload["summary"]["detected_protein_count"] == 4
        assert payload["summary"]["observed_outside_library_protein_count"] == 1
        assert payload["condition_entries"][0]["condition"] == "control"
        assert payload["condition_entries"][0]["detected_peptide_count"] == 4
        assert payload["condition_entries"][1]["condition"] == "treatment"
        assert payload["condition_entries"][1]["detected_peptide_count"] == 1
        assert payload["peptide_entries"][0]["canonical_peptide"] == "LIVNLY"
        assert payload["peptide_entries"][0]["detected_overall"] is False
        assert payload["protein_entries"][-1]["protein_ref"] == "P44444"
        assert payload["protein_entries"][-1]["detected_overall"] is False
        assert (
            payload["observed_outside_library_peptide_entries"][0]["canonical_peptide"]
            == "PEPNOVEL"
        )
        assert (
            payload["observed_outside_library_protein_entries"][0]["protein_ref"]
            == "P55555"
        )
        assert payload["outputs"]["summary_tsv"] == "diann.library.summary.tsv"
        assert payload["outputs"]["sample_tsv"] == "diann.library.samples.tsv"
        assert (
            payload["outputs"]["condition_tsv"] == "diann.library.conditions.tsv"
        )
        assert payload["outputs"]["peptide_tsv"] == "diann.library.peptides.tsv"
        assert payload["outputs"]["protein_tsv"] == "diann.library.proteins.tsv"
        assert (
            payload["outputs"]["outside_library_peptide_tsv"]
            == "diann.library.outside.peptides.tsv"
        )
        assert (
            payload["outputs"]["outside_library_protein_tsv"]
            == "diann.library.outside.proteins.tsv"
        )
        assert Path("diann.library.summary.tsv").exists()
        assert Path("diann.library.samples.tsv").exists()
        assert Path("diann.library.conditions.tsv").exists()
        assert Path("diann.library.peptides.tsv").exists()
        assert Path("diann.library.proteins.tsv").exists()
        assert Path("diann.library.outside.peptides.tsv").exists()
        assert Path("diann.library.outside.proteins.tsv").exists()
        assert "sample_id\tdetected_peptide_count\tdetected_protein_count" in Path(
            "diann.library.samples.tsv"
        ).read_text(encoding="utf-8")
        assert "control\tsample_A;sample_B\t4\t4" in Path(
            "diann.library.conditions.tsv"
        ).read_text(encoding="utf-8")
        assert "LIVNLY\tP44444\tfalse\t0\t0" in Path(
            "diann.library.peptides.tsv"
        ).read_text(encoding="utf-8")
        assert "P44444\tfalse\t0\t0" in Path(
            "diann.library.proteins.tsv"
        ).read_text(encoding="utf-8")
        assert "PEPNOVEL\tP55555\tsample_A\tcontrol\t1\t1" in Path(
            "diann.library.outside.peptides.tsv"
        ).read_text(encoding="utf-8")
        assert "P55555\tsample_A\tcontrol\t1\t1" in Path(
            "diann.library.outside.proteins.tsv"
        ).read_text(encoding="utf-8")


def test_target_panel_review_command_emits_dia_panel_outputs() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        fixture_dir = FIXTURE_ROOT / "search_result_bundles" / "diann"
        format_dir = FIXTURE_ROOT / "formats"
        shutil.copy(
            fixture_dir / "diann_library_coverage.tsv",
            "diann_library_coverage.tsv",
        )
        shutil.copy(format_dir / "dia_target_panel.tsv", "dia_target_panel.tsv")

        result = runner.invoke(
            cli,
            [
                "target-panel-review",
                "diann_library_coverage.tsv",
                "dia_target_panel.tsv",
                "--source-kind",
                "dia_peptide",
                "--summary-tsv-out",
                "target.summary.tsv",
                "--target-tsv-out",
                "target.targets.tsv",
                "--missing-tsv-out",
                "target.missing.tsv",
                "--intensity-tsv-out",
                "target.intensity.tsv",
                "--matrix-tsv-out",
                "target.matrix.tsv",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["source_kind"] == "dia_peptide"
        assert payload["source_name"] == "DIA-NN"
        assert payload["summary"]["total_target_count"] == 4
        assert payload["summary"]["matched_target_count"] == 3
        assert payload["summary"]["missing_target_count"] == 1
        assert payload["matched_targets"][0]["modified_peptide"] == "PEPALFA"
        assert payload["matched_targets"][0]["expected_charge"] == 2
        assert payload["matched_targets"][1]["target_id"] == "dia-p22222"
        assert payload["missing_targets"][0]["target_id"] == "dia-missing-protein"
        assert payload["outputs"]["summary_tsv"] == "target.summary.tsv"
        assert payload["outputs"]["matrix_tsv"] == "target.matrix.tsv"
        assert Path("target.summary.tsv").exists()
        assert Path("target.targets.tsv").exists()
        assert Path("target.missing.tsv").exists()
        assert Path("target.intensity.tsv").exists()
        assert Path("target.matrix.tsv").exists()
        assert "dia-missing-protein\tprotein\t\t\t" in Path(
            "target.missing.tsv"
        ).read_text(encoding="utf-8")
        assert "dia-pepalfa\tpeptide\tPEPALFA|PG001\tPEPALFA\tPEPALFA\t2\t2\tP11111" in Path(
            "target.matrix.tsv"
        ).read_text(encoding="utf-8")


def test_target_panel_review_command_emits_lfq_protein_panel_outputs() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        quant_dir = FIXTURE_ROOT / "quant"
        format_dir = FIXTURE_ROOT / "formats"
        shutil.copy(
            quant_dir / "target_panel_ms1_features.tsv",
            "target_panel_ms1_features.tsv",
        )
        shutil.copy(format_dir / "lfq_target_panel.tsv", "lfq_target_panel.tsv")

        result = runner.invoke(
            cli,
            [
                "target-panel-review",
                "target_panel_ms1_features.tsv",
                "lfq_target_panel.tsv",
                "--source-kind",
                "lfq_protein_lfq",
                "--summary-tsv-out",
                "lfq.target.summary.tsv",
                "--target-tsv-out",
                "lfq.target.targets.tsv",
                "--missing-tsv-out",
                "lfq.target.missing.tsv",
                "--intensity-tsv-out",
                "lfq.target.intensity.tsv",
                "--matrix-tsv-out",
                "lfq.target.matrix.tsv",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["source_kind"] == "lfq_protein_lfq"
        assert payload["source_name"] == "feature"
        assert payload["summary"]["total_target_count"] == 4
        assert payload["summary"]["matched_target_count"] == 1
        assert payload["summary"]["missing_target_count"] == 3
        assert payload["matched_targets"][0]["target_id"] == "lfq-p003"
        assert payload["matched_targets"][0]["modified_peptide"] is None
        assert payload["matched_targets"][0]["expected_charge"] is None
        assert payload["missing_targets"][0]["reason"] == (
            "peptide targets require a peptide-level matrix"
        )
        assert payload["outputs"]["target_tsv"] == "lfq.target.targets.tsv"
        assert payload["outputs"]["intensity_tsv"] == "lfq.target.intensity.tsv"
        assert Path("lfq.target.summary.tsv").exists()
        assert Path("lfq.target.targets.tsv").exists()
        assert Path("lfq.target.missing.tsv").exists()
        assert Path("lfq.target.intensity.tsv").exists()
        assert Path("lfq.target.matrix.tsv").exists()
        assert "lfq-p003\tprotein\t\t\tP003\t4" in Path(
            "lfq.target.targets.tsv"
        ).read_text(encoding="utf-8")
        assert "lfq-apeptide\tpeptide\tAPEPTIDE\t2\tpeptide targets require a peptide-level matrix" in (
            Path("lfq.target.missing.tsv").read_text(encoding="utf-8")
        )


def test_transition_qc_command_emits_transition_and_weak_outputs() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        format_dir = FIXTURE_ROOT / "formats"
        shutil.copy(format_dir / "transition_quant.tsv", "transition_quant.tsv")

        result = runner.invoke(
            cli,
            [
                "transition-qc",
                "transition_quant.tsv",
                "--summary-tsv-out",
                "transition.summary.tsv",
                "--transition-tsv-out",
                "transition.rows.tsv",
                "--sample-tsv-out",
                "transition.samples.tsv",
                "--weak-tsv-out",
                "transition.weak.tsv",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["source_name"] == "transition table"
        assert payload["sample_ids"] == ["s1", "s2", "s3"]
        assert payload["summary"]["transition_count"] == 4
        assert payload["summary"]["weak_transition_count"] == 1
        assert payload["entries"][0]["precursor_charge"] == 2
        assert payload["entries"][0]["median_retention_time_minutes"] == 12.45
        assert payload["weak_transitions"][0]["transition_id"] == "tr_y6_b"
        assert payload["outputs"]["summary_tsv"] == "transition.summary.tsv"
        assert payload["outputs"]["transition_tsv"] == "transition.rows.tsv"
        assert payload["outputs"]["sample_tsv"] == "transition.samples.tsv"
        assert payload["outputs"]["weak_tsv"] == "transition.weak.tsv"
        assert Path("transition.summary.tsv").exists()
        assert Path("transition.rows.tsv").exists()
        assert Path("transition.samples.tsv").exists()
        assert Path("transition.weak.tsv").exists()
        assert "source_name\tprecursor_count\ttransition_count" in Path(
            "transition.summary.tsv"
        ).read_text(encoding="utf-8")
        assert "tr_y7_a\tprec_a\t2\tPEPTIDEK\tP001\ty7" in Path(
            "transition.rows.tsv"
        ).read_text(encoding="utf-8")
        assert "tr_y7_a\tprec_a\ts1\trun_a\t120000\t12.5\t0.002\t160000\t0.75\t1\ttrue" in (
            Path("transition.samples.tsv").read_text(encoding="utf-8")
        )
        assert "tr_y6_b\tprec_b\t1\t3\t0.333333\t0.0789474" in Path(
            "transition.weak.tsv"
        ).read_text(encoding="utf-8")


def test_targeted_target_matrix_command_emits_targeted_review_outputs() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        format_dir = FIXTURE_ROOT / "formats"
        shutil.copy(
            format_dir / "skyline_targeted_results.tsv",
            "skyline_targeted_results.tsv",
        )

        result = runner.invoke(
            cli,
            [
                "targeted-target-matrix",
                "skyline_targeted_results.tsv",
                "--source-kind",
                "skyline_export",
                "--summary-tsv-out",
                "targeted.summary.tsv",
                "--observation-tsv-out",
                "targeted.observations.tsv",
                "--target-tsv-out",
                "targeted.targets.tsv",
                "--sample-tsv-out",
                "targeted.samples.tsv",
                "--flagged-tsv-out",
                "targeted.flagged.tsv",
                "--retained-transition-tsv-out",
                "targeted.retained.tsv",
                "--excluded-transition-tsv-out",
                "targeted.excluded.tsv",
                "--missingness-tsv-out",
                "targeted.missingness.tsv",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["source_kind"] == "skyline_export"
        assert payload["source_name"] == "Skyline"
        assert payload["import_summary"]["observation_count"] == 6
        assert payload["matrix_summary"]["target_count"] == 2
        assert payload["matrix_summary"]["retained_transition_count"] == 4
        assert payload["matrix_summary"]["excluded_transition_count"] == 2
        assert payload["matrix_summary"]["quality_flag_count"] == 2
        assert payload["targets"][1]["target_id"] == "PEPTIDEK/2"
        assert payload["targets"][1]["total_intensity"] == 273000.0
        assert payload["retained_transitions"][0]["transition_id"] == "y5"
        assert payload["excluded_transitions"][-1]["transition_id"] == "y8"
        missing_entry = next(
            entry
            for entry in payload["missingness"]
            if entry["target_id"] == "ACDMPEP/3" and entry["sample_id"] == "sample_B"
        )
        assert missing_entry["missing_reason"] == "no_observation"
        assert payload["outputs"]["summary_tsv"] == "targeted.summary.tsv"
        assert payload["outputs"]["observation_tsv"] == "targeted.observations.tsv"
        assert payload["outputs"]["target_tsv"] == "targeted.targets.tsv"
        assert payload["outputs"]["sample_tsv"] == "targeted.samples.tsv"
        assert payload["outputs"]["flagged_tsv"] == "targeted.flagged.tsv"
        assert payload["outputs"]["retained_transition_tsv"] == "targeted.retained.tsv"
        assert payload["outputs"]["excluded_transition_tsv"] == "targeted.excluded.tsv"
        assert payload["outputs"]["missingness_tsv"] == "targeted.missingness.tsv"
        assert Path("targeted.summary.tsv").exists()
        assert Path("targeted.observations.tsv").exists()
        assert Path("targeted.targets.tsv").exists()
        assert Path("targeted.samples.tsv").exists()
        assert Path("targeted.flagged.tsv").exists()
        assert Path("targeted.retained.tsv").exists()
        assert Path("targeted.excluded.tsv").exists()
        assert Path("targeted.missingness.tsv").exists()
        assert "Skyline\t2\t2\t3\t1\t0\t4\t2\t2" in Path("targeted.summary.tsv").read_text(
            encoding="utf-8"
        )
        assert "skyline_export\ty8\tPEPTIDEK/2\t2\tPEPTIDEK\tsample_B\t8000" in Path(
            "targeted.observations.tsv"
        ).read_text(encoding="utf-8")
        assert "PEPTIDEK/2\tPEPTIDEK\tP001\ty7;y8\ty7;y8\ty8\t2\t1\t2\t273000" in Path(
            "targeted.targets.tsv"
        ).read_text(encoding="utf-8")
        assert "PEPTIDEK/2\tsample_B\ty7;y8\ty7\ty8\t2\t1\t1\t115000\t12.4\tinterference\t\ttrue" in (
            Path("targeted.samples.tsv").read_text(encoding="utf-8")
        )
        assert "PEPTIDEK/2\tPEPTIDEK\tP001\t1\t1" in Path(
            "targeted.flagged.tsv"
        ).read_text(encoding="utf-8")
        assert "PEPTIDEK/2\tsample_B\ty7\t115000\t12.4\tpass" in Path(
            "targeted.retained.tsv"
        ).read_text(encoding="utf-8")
        assert "PEPTIDEK/2\tsample_B\ty8\t8000\t12.7\tinterference\tquality_filter" in Path(
            "targeted.excluded.tsv"
        ).read_text(encoding="utf-8")
        assert "ACDMPEP/3\tsample_B\t0\t0\t0\ttrue\tno_observation" in Path(
            "targeted.missingness.tsv"
        ).read_text(encoding="utf-8")


def test_targeted_assay_qc_command_emits_targeted_qc_review_outputs() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        format_dir = FIXTURE_ROOT / "formats"
        shutil.copy(
            format_dir / "skyline_targeted_qc_results.tsv",
            "skyline_targeted_qc_results.tsv",
        )
        shutil.copy(
            format_dir / "skyline_targeted_qc.design.tsv",
            "skyline_targeted_qc.design.tsv",
        )

        result = runner.invoke(
            cli,
            [
                "targeted-assay-qc",
                "skyline_targeted_qc_results.tsv",
                "skyline_targeted_qc.design.tsv",
                "--source-kind",
                "skyline_export",
                "--summary-tsv-out",
                "assay.summary.tsv",
                "--target-qc-tsv-out",
                "assay.targets.tsv",
                "--transition-tsv-out",
                "assay.transitions.tsv",
                "--coelution-tsv-out",
                "assay.coelution.tsv",
                "--transition-coelution-tsv-out",
                "assay.transition_coelution.tsv",
                "--transition-qc-tsv-out",
                "assay.transition_qc.tsv",
                "--fragment-ratio-tsv-out",
                "assay.fragments.tsv",
                "--retention-tsv-out",
                "assay.retention.tsv",
                "--replicate-cv-tsv-out",
                "assay.replicate_cv.tsv",
                "--unreliable-tsv-out",
                "assay.unreliable.tsv",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["source_kind"] == "skyline_export"
        assert payload["source_name"] == "Skyline"
        assert payload["import_summary"]["observation_count"] == 14
        assert payload["design_summary"]["accepted_entry_count"] == 4
        assert payload["assay_qc_summary"]["target_count"] == 2
        assert payload["assay_qc_summary"]["reliable_target_entry_count"] == 1
        assert payload["assay_qc_summary"]["flagged_coelution_target_entry_count"] == 3
        assert payload["assay_qc_summary"]["flagged_replicate_cv_entry_count"] == 1
        assert payload["fragment_ratio_stability_summary"]["fragment_entry_count"] == 4
        assert payload["fragment_ratio_stability_summary"]["unstable_fragment_count"] == 1
        assert (
            payload["fragment_ratio_stability_summary"]["drift_flagged_observation_count"]
            == 2
        )
        assert payload["transition_coelution_summary"]["coeluting_transition_entry_count"] == 14
        assert payload["outputs"]["summary_tsv"] == "assay.summary.tsv"
        assert payload["outputs"]["target_qc_tsv"] == "assay.targets.tsv"
        assert payload["outputs"]["transition_tsv"] == "assay.transitions.tsv"
        assert payload["outputs"]["coelution_tsv"] == "assay.coelution.tsv"
        assert (
            payload["outputs"]["transition_coelution_tsv"]
            == "assay.transition_coelution.tsv"
        )
        assert payload["outputs"]["transition_qc_tsv"] == "assay.transition_qc.tsv"
        assert payload["outputs"]["fragment_ratio_tsv"] == "assay.fragments.tsv"
        assert payload["outputs"]["retention_tsv"] == "assay.retention.tsv"
        assert payload["outputs"]["replicate_cv_tsv"] == "assay.replicate_cv.tsv"
        assert payload["outputs"]["unreliable_tsv"] == "assay.unreliable.tsv"
        assert Path("assay.summary.tsv").exists()
        assert Path("assay.targets.tsv").exists()
        assert Path("assay.transitions.tsv").exists()
        assert Path("assay.coelution.tsv").exists()
        assert Path("assay.transition_coelution.tsv").exists()
        assert Path("assay.transition_qc.tsv").exists()
        assert Path("assay.fragments.tsv").exists()
        assert Path("assay.retention.tsv").exists()
        assert Path("assay.replicate_cv.tsv").exists()
        assert Path("assay.unreliable.tsv").exists()
        assert "Skyline\t2\t4\t8\t1\t8\t8\t3\t16\t14\t16\t8\t14\t4\t1\t2\t8\t2\t4\t1\t8\t2" in Path(
            "assay.summary.tsv"
        ).read_text(encoding="utf-8")
        assert "PEPTIDEK/2\ttreat_r1\ttreatment\t2\t2\t2\ty7;y8\t1\ty7\ty8\t102000" in Path(
            "assay.targets.tsv"
        ).read_text(encoding="utf-8")
        assert "PEPTIDEK/2\ttreat_r2\t1\t2\t0.5" in Path(
            "assay.transitions.tsv"
        ).read_text(encoding="utf-8")
        assert "PEPTIDEK/2\ttreat_r2\t2\t1\t1\ty7\ty8\ty7\t13.3\t13.3\t12.6\t0.7\tfalse\tinsufficient\tfalse\tfewer than two coeluting transitions support the target" in Path(
            "assay.coelution.tsv"
        ).read_text(encoding="utf-8")
        assert "ACDMPEP/3\ttreat_r2\ty5\ttrue\t20.2\ty5\t20.2\t18.2\t0\t2\ttrue\ttransition is misaligned from the target reference window" in Path(
            "assay.transition_coelution.tsv"
        ).read_text(encoding="utf-8")
        assert "PEPTIDEK/2\ttreat_r2\ttreatment\ty8\tfalse" in Path(
            "assay.transition_qc.tsv"
        ).read_text(encoding="utf-8")
        assert "PEPTIDEK/2\ttreat_r1\ty8\t12000\t114000\t0.105263\t0.236842\t0.131579\t0.396731\ttrue\ttrue\ttrue" in Path(
            "assay.fragments.tsv"
        ).read_text(encoding="utf-8")
        assert "ACDMPEP/3\ttreat_r2\t1\t20.2\t18.2\t2\ttrue" in Path(
            "assay.retention.tsv"
        ).read_text(encoding="utf-8")
        assert "ACDMPEP/3\ttreatment\t2\t2\t35000\t0.525279\ttrue" in Path(
            "assay.replicate_cv.tsv"
        ).read_text(encoding="utf-8")
        assert (
            "PEPTIDEK/2\ttreat_r1\ttreatment\ty8\tinterference\tfewer than two coeluting transitions pass transition-quality review; fragment-ion ratios deviate from the cross-run reference pattern; source quality flags require review"
            in Path("assay.unreliable.tsv").read_text(encoding="utf-8")
        )


def test_targeted_carryover_review_command_emits_ordered_candidates() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        format_dir = FIXTURE_ROOT / "formats"
        shutil.copy(
            format_dir / "skyline_targeted_carryover_results.tsv",
            "skyline_targeted_carryover_results.tsv",
        )
        shutil.copy(
            format_dir / "skyline_targeted_carryover.design.tsv",
            "skyline_targeted_carryover.design.tsv",
        )

        result = runner.invoke(
            cli,
            [
                "targeted-carryover-review",
                "skyline_targeted_carryover_results.tsv",
                "skyline_targeted_carryover.design.tsv",
                "--source-kind",
                "skyline_export",
                "--summary-tsv-out",
                "carryover.summary.tsv",
                "--candidate-tsv-out",
                "carryover.candidates.tsv",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["source_kind"] == "skyline_export"
        assert payload["source_name"] == "Skyline"
        assert payload["import_summary"]["observation_count"] == 10
        assert payload["design_summary"]["accepted_entry_count"] == 4
        assert payload["design_summary"]["rejected_row_count"] == 0
        assert payload["carryover_summary"]["run_count"] == 4
        assert payload["carryover_summary"]["precursor_count"] == 2
        assert payload["carryover_summary"]["candidate_entry_count"] == 2
        assert payload["outputs"]["summary_tsv"] == "carryover.summary.tsv"
        assert payload["outputs"]["candidate_tsv"] == "carryover.candidates.tsv"
        assert len(payload["candidates"]) == 2
        assert payload["candidates"][0]["source_run_id"] == "source_high.raw"
        assert payload["candidates"][0]["affected_run_id"] == "blank_after_source.raw"
        assert payload["candidates"][0]["carryover_score"] == 0.9333
        assert Path("carryover.summary.tsv").exists()
        assert Path("carryover.candidates.tsv").exists()
        assert "Skyline\t4\t2\t2\t2\t1" in Path(
            "carryover.summary.tsv"
        ).read_text(encoding="utf-8")
        assert (
            "source_high.raw\tsource_high\t1\tblank_after_source.raw\tblank_after_source\t2\t1\tCARRYPEP/2\tCARRYPEP\tP100\t200000\t4000\t0.020000\t0.9333\thigh_intensity_previous_run|low_level_repeated_signal|immediate_run_order_followup"
            in Path("carryover.candidates.tsv").read_text(encoding="utf-8")
        )


def test_targeted_carryover_review_command_requires_run_order() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        format_dir = FIXTURE_ROOT / "formats"
        shutil.copy(
            format_dir / "skyline_targeted_carryover_results.tsv",
            "skyline_targeted_carryover_results.tsv",
        )
        shutil.copy(
            format_dir / "skyline_targeted_qc.design.tsv",
            "skyline_targeted_qc.design.tsv",
        )

        result = runner.invoke(
            cli,
            [
                "targeted-carryover-review",
                "skyline_targeted_carryover_results.tsv",
                "skyline_targeted_qc.design.tsv",
                "--source-kind",
                "skyline_export",
            ],
        )

        assert result.exit_code != 0
        assert "run_order is required for carryover analysis" in result.output


def test_targeted_peptide_selection_command_emits_ranked_observed_and_fallback_peptides() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        Path("protein_cards.tsv").write_text(
            "protein_group_id\trepresentative_protein_ref\tprotein_refs\tgene_symbol\tpeptides\n"
            "protein_group_1\tP00001\tP00001\tKIN1\tPEPTIDER;AAASHALEDK;AAAMMMWNQK\n"
            "protein_group_2\tP00002\tP00002\tKIN2\t\n",
            encoding="utf-8",
        )
        Path("peptide_evidence.tsv").write_text(
            "peptide\tcanonical_peptide\tprimary_class\ttags\tpeptide_q_value\taccepted\tpsm_count\tspectrum_count\trun_count\tdetection_frequency\treplicate_consistency\tcondition_specificity\tdetected_condition_count\treproducibility_class\texploratory_override\tbest_score\tcharge_states\trun_ids\tprotein_refs\ttarget_decoy_label\ttarget_decoy_contaminant_class\tcontaminant_flag\texplanation\n"
            "PEPTIDER\tPEPTIDER\tstrong\tunique;reproducible\t0.001\ttrue\t6\t6\t4\t1.0\t0.95\t0.1\t2\treproducible\tfalse\t125.0\t2\trun1;run2;run3;run4\tP00001\ttarget\ttarget\tfalse\tstrong observed peptide support\n"
            "AAASHALEDK\tAAASHALEDK\tstrong\tshared;reproducible\t0.002\ttrue\t5\t5\t3\t0.75\t0.8\t0.2\t2\treproducible\tfalse\t118.0\t2\trun1;run2;run3\tP00001;O00003\ttarget\ttarget\tfalse\tshared peptide support\n"
            "AAAMMMWNQK\tAAAMMMWNQK\tstrong\tunique;reproducible\t0.003\ttrue\t12\t12\t4\t1.0\t0.95\t0.1\t2\treproducible\tfalse\t130.0\t2\trun1;run2;run3;run4\tP00001\ttarget\ttarget\tfalse\thigh-confidence but chemically risky peptide\n",
            encoding="utf-8",
        )
        Path("targets.fasta").write_text(
            ">sp|P00001|KIN1 GN=KIN1\n"
            "PEPTIDERAAASHALEDKAAAMMMWNQK\n"
            ">sp|P00002|KIN2 GN=KIN2\n"
            "KTARGETVKAAALIGHTR\n"
            ">sp|O00003|OFF1 GN=OFF1\n"
            "KAAASHALEDK\n",
            encoding="utf-8",
        )

        result = runner.invoke(
            cli,
            [
                "targeted-peptide-selection",
                "protein_cards.tsv",
                "peptide_evidence.tsv",
                "targets.fasta",
                "--top-peptides-per-target",
                "1",
                "--summary-tsv-out",
                "selector.summary.tsv",
                "--selected-tsv-out",
                "selector.selected.tsv",
                "--rejected-tsv-out",
                "selector.rejected.tsv",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["protease"] == "trypsin"
        assert payload["missed_cleavages"] == 0
        assert payload["top_peptides_per_target"] == 1
        assert payload["target_count"] == 2
        assert payload["peptide_evidence_count"] == 3
        assert payload["fasta_summary"]["accepted_record_count"] == 3
        assert payload["selection_summary"]["selected_entry_count"] == 2
        assert payload["selection_summary"]["observed_selected_entry_count"] == 1
        assert payload["selection_summary"]["theoretical_selected_entry_count"] == 1
        assert payload["outputs"]["summary_tsv"] == "selector.summary.tsv"
        assert payload["outputs"]["selected_tsv"] == "selector.selected.tsv"
        assert payload["outputs"]["rejected_tsv"] == "selector.rejected.tsv"
        assert payload["selected_entries"][0]["target_protein_ref"] == "P00001"
        assert payload["selected_entries"][0]["candidate_source"] == "observed_discovery"
        assert payload["selected_entries"][0]["peptide_sequence"] == "PEPTIDER"
        assert payload["selected_entries"][1]["target_protein_ref"] == "P00002"
        assert payload["selected_entries"][1]["candidate_source"] == "theoretical_digest"
        assert payload["selected_entries"][1]["peptide_sequence"] == "AAALIGHTR"
        assert Path("selector.summary.tsv").exists()
        assert Path("selector.selected.tsv").exists()
        assert Path("selector.rejected.tsv").exists()
        assert "selected_entry_count\t2" in Path("selector.summary.tsv").read_text(
            encoding="utf-8"
        )
        assert (
            "P00001\tprotein_group_1\tKIN1\t1\tobserved_discovery\tPEPTIDER"
            in Path("selector.selected.tsv").read_text(encoding="utf-8")
        )
        assert (
            "P00002\tprotein_group_2\tKIN2\t1\ttheoretical_digest\tAAALIGHTR"
            in Path("selector.selected.tsv").read_text(encoding="utf-8")
        )
        assert "AAASHALEDK" in Path("selector.rejected.tsv").read_text(
            encoding="utf-8"
        )
        assert "AAAMMMWNQK" in Path("selector.rejected.tsv").read_text(
            encoding="utf-8"
        )


def test_targeted_transition_selection_command_emits_ranked_fragments() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        Path("selected_peptides.tsv").write_text(
            "target_protein_ref\ttarget_protein_group_id\tgene_symbol\trank\tcandidate_source\tpeptide_sequence\tcanonical_peptide\tobserved_in_discovery\tobserved_psm_count\trun_count\tdetection_frequency\treplicate_consistency\tprimary_evidence_class\tuniqueness_class\tuniqueness_score\tdetectability_score\tdetectability_tier\tsuitability_score\tliability_tier\tliability_codes\tselection_score\tselection_reasons\n"
            "P00001\tprotein_group_1\tKIN1\t1\tobserved_discovery\tPEPTIDER\tPEPTIDER\ttrue\t6\t4\t1.0\t0.95\tstrong\tunique\t1.0\t0.9\thigh\t0.9\tpreferred\t\t0.9\tstrong observed peptide support\n",
            encoding="utf-8",
        )
        precursor_mz = calculate_peptide_mz("PEPTIDER", charge=2)
        fragments = calculate_fragment_ions(
            "PEPTIDER",
            charges=(1,),
            series=(FragmentIonSeries.Y, FragmentIonSeries.B),
        )
        mz_by_label = {
            f"{fragment.series.value}{fragment.ordinal}+{fragment.charge}": fragment.mz_monoisotopic
            for fragment in fragments
        }
        Path("library.mgf").write_text(
            render_mgf(
                (
                    SpectrumModel(
                        spectrum_id="library:PEPTIDER",
                        title="SEQ=PEPTIDER|PEPTIDE=PEPTIDER|PROTEINS=P00001",
                        precursor_mz=precursor_mz,
                        precursor_charge=2,
                        peaks=(
                            SpectrumPeak(mz=mz_by_label["y7+1"], intensity=1000.0),
                            SpectrumPeak(mz=mz_by_label["y6+1"], intensity=850.0),
                            SpectrumPeak(mz=mz_by_label["y5+1"], intensity=700.0),
                            SpectrumPeak(mz=mz_by_label["b5+1"], intensity=250.0),
                            SpectrumPeak(mz=175.0, intensity=500.0),
                        ),
                    ),
                )
            ),
            encoding="utf-8",
        )

        result = runner.invoke(
            cli,
            [
                "targeted-transition-selection",
                "selected_peptides.tsv",
                "--spectral-library",
                "library.mgf",
                "--summary-tsv-out",
                "transition.summary.tsv",
                "--selected-tsv-out",
                "transition.selected.tsv",
                "--rejected-tsv-out",
                "transition.rejected.tsv",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["selected_peptide_count"] == 1
        assert payload["spectral_library"]["accepted_entry_count"] == 1
        assert payload["selection_summary"]["selected_transition_count"] >= 3
        assert payload["peptide_entries"][0]["target_protein_ref"] == "P00001"
        assert payload["peptide_entries"][0]["selected_transition_count"] >= 3
        assert payload["peptide_entries"][0]["selected_transitions"][0]["fragment_label"] == "y7+1"
        assert payload["outputs"]["summary_tsv"] == "transition.summary.tsv"
        assert payload["outputs"]["selected_tsv"] == "transition.selected.tsv"
        assert payload["outputs"]["rejected_tsv"] == "transition.rejected.tsv"
        assert "selected_transition_count" in Path("transition.summary.tsv").read_text(
            encoding="utf-8"
        )
        assert "y7+1" in Path("transition.selected.tsv").read_text(encoding="utf-8")
        assert "fragment_too_short" in Path("transition.rejected.tsv").read_text(
            encoding="utf-8"
        )


def test_targeted_assay_interference_command_downgrades_high_risk_panel_entries() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        Path("selected_peptides.tsv").write_text(
            "target_protein_ref\ttarget_protein_group_id\tgene_symbol\trank\tcandidate_source\tpeptide_sequence\tcanonical_peptide\tobserved_in_discovery\tobserved_psm_count\trun_count\tdetection_frequency\treplicate_consistency\tprimary_evidence_class\tuniqueness_class\tuniqueness_score\tdetectability_score\tdetectability_tier\tsuitability_score\tliability_tier\tliability_codes\tselection_score\tselection_reasons\n"
            "P00001\tprotein_group_1\tKIN1\t1\tobserved_discovery\tAAALIGHTR\tAAALIGHTR\ttrue\t6\t4\t1.0\t0.95\tstrong\tunique\t1.0\t0.9\thigh\t0.9\tpreferred\t\t0.9\tstrong observed peptide support\n"
            "P00002\tprotein_group_2\tKIN2\t1\tobserved_discovery\tAAAIIGHTR\tAAAIIGHTR\ttrue\t6\t4\t1.0\t0.95\tstrong\tunique\t1.0\t0.9\thigh\t0.9\tpreferred\t\t0.9\tstrong observed peptide support\n"
            "P00003\tprotein_group_3\tKIN3\t1\tobserved_discovery\tPEPTIDER\tPEPTIDER\ttrue\t6\t4\t1.0\t0.95\tstrong\tunique\t1.0\t0.9\thigh\t0.9\tpreferred\t\t0.9\tstrong observed peptide support\n",
            encoding="utf-8",
        )
        spectra: list[SpectrumModel] = []
        for protein_ref, peptide, retention_time_minutes in (
            ("P00001", "AAALIGHTR", 10.0),
            ("P00002", "AAAIIGHTR", 10.2),
            ("P00003", "PEPTIDER", 25.0),
        ):
            precursor_mz = calculate_peptide_mz(peptide, charge=2)
            fragments = calculate_fragment_ions(
                peptide,
                charges=(1,),
                series=(FragmentIonSeries.Y, FragmentIonSeries.B),
            )
            mz_by_label = {
                f"{fragment.series.value}{fragment.ordinal}+{fragment.charge}": fragment.mz_monoisotopic
                for fragment in fragments
            }
            spectra.append(
                SpectrumModel(
                    spectrum_id=f"library:{peptide}",
                    title=f"SEQ={peptide}|PEPTIDE={peptide}|PROTEINS={protein_ref}",
                    precursor_mz=precursor_mz,
                    precursor_charge=2,
                    retention_time_seconds=retention_time_minutes * 60.0,
                    peaks=(
                        SpectrumPeak(mz=mz_by_label["y7+1"], intensity=1000.0),
                        SpectrumPeak(mz=mz_by_label["y6+1"], intensity=850.0),
                        SpectrumPeak(mz=mz_by_label["y5+1"], intensity=700.0),
                        SpectrumPeak(mz=mz_by_label["b5+1"], intensity=250.0),
                        SpectrumPeak(mz=175.0, intensity=500.0),
                    ),
                )
            )
        Path("library.mgf").write_text(render_mgf(tuple(spectra)), encoding="utf-8")
        Path("targets.fasta").write_text(
            ">sp|P00001|KIN1 GN=KIN1\nAAALIGHTR\n"
            ">sp|P00002|KIN2 GN=KIN2\nAAAIIGHTR\n"
            ">sp|P00003|KIN3 GN=KIN3\nPEPTIDER\n",
            encoding="utf-8",
        )

        transition_result = runner.invoke(
            cli,
            [
                "targeted-transition-selection",
                "selected_peptides.tsv",
                "--spectral-library",
                "library.mgf",
                "--selected-tsv-out",
                "transition.selected.tsv",
            ],
        )

        assert transition_result.exit_code == 0

        result = runner.invoke(
            cli,
            [
                "targeted-assay-interference",
                "selected_peptides.tsv",
                "transition.selected.tsv",
                "targets.fasta",
                "--spectral-library",
                "library.mgf",
                "--summary-tsv-out",
                "assay_interference.summary.tsv",
                "--assay-tsv-out",
                "assay_interference.assays.tsv",
                "--transition-tsv-out",
                "assay_interference.transitions.tsv",
                "--panel-tsv-out",
                "assay_interference.panel.tsv",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["selected_peptide_count"] == 3
        assert payload["selected_transition_assay_count"] == 3
        assert payload["spectral_library"]["accepted_entry_count"] == 3
        assert payload["fasta_summary"]["accepted_record_count"] == 3
        assert payload["interference_summary"]["high_risk_assay_count"] >= 2
        assert payload["interference_summary"]["panel_export_assay_count"] == 1
        assert {entry["peptide_sequence"] for entry in payload["panel_entries"]} == {
            "PEPTIDER"
        }
        assert payload["outputs"]["summary_tsv"] == "assay_interference.summary.tsv"
        assert payload["outputs"]["assay_tsv"] == "assay_interference.assays.tsv"
        assert payload["outputs"]["transition_tsv"] == "assay_interference.transitions.tsv"
        assert payload["outputs"]["panel_tsv"] == "assay_interference.panel.tsv"
        assert "high_risk_assay_count\t2" in Path(
            "assay_interference.summary.tsv"
        ).read_text(encoding="utf-8")
        assert "AAALIGHTR" in Path("assay_interference.assays.tsv").read_text(
            encoding="utf-8"
        )
        assert "PEPTIDER" in Path("assay_interference.panel.tsv").read_text(
            encoding="utf-8"
        )
        assert "AAALIGHTR" not in Path("assay_interference.panel.tsv").read_text(
            encoding="utf-8"
        )


def test_targeted_panel_builder_command_emits_reviewable_transition_list_rows() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        Path("biomarker.candidates.tsv").write_text(
            "candidate_id\tcandidate_kind\tdisplay_label\ttarget_protein_ref\tsite_key\tpriority_rank\tfinal_score\tweighted_evidence_total\tpenalty_total\tuncertainty\teffect_size\tadjusted_p_value\tsupport_count\teffect_score\trobustness_score\tdetectability_score\tspecificity_score\tannotation_score\tassay_feasibility_score\tsample_qc_score\tannotation_labels\trank_reason_codes\tsource_ids\tranking_note\n"
            "protein:P11111\tprotein\tROBUST1\tP11111\t\t1\t0.91\t0.91\t0.00\t0.00\t1.4\t0.003\t4\t0.70\t0.91\t0.95\t0.94\t0.55\t0.92\t0.90\tpathway:stress\tassay_ready\tbio-card-1\tstrong validation-ready candidate\n"
            "protein:P22222\tprotein\tWARN2\tP22222\t\t2\t0.61\t0.70\t0.18\t0.00\t0.8\t0.020\t3\t0.40\t0.34\t0.62\t0.40\t0.30\t0.58\t0.90\tcontext:secreted\tweak_robustness\tbio-card-2\tcandidate carries evidence penalties\n"
            "ptm_site:P33333:S21\tptm_site\tP33333 S21 phospho-site\tP33333\tP33333:S21:phosphorylation\t3\t0.73\t0.73\t0.00\t0.00\t1.0\t0.005\t5\t0.50\t0.80\t0.70\t0.80\t0.70\t0.30\t0.90\tregulator:KINASE_A\tsite_specific\tptm-card-1\tsite-specific candidate\n",
            encoding="utf-8",
        )
        Path("selected_peptides.tsv").write_text(
            "target_protein_ref\ttarget_protein_group_id\tgene_symbol\trank\tcandidate_source\tpeptide_sequence\tcanonical_peptide\tobserved_in_discovery\tobserved_psm_count\trun_count\tdetection_frequency\treplicate_consistency\tprimary_evidence_class\tuniqueness_class\tuniqueness_score\tdetectability_score\tdetectability_tier\tsuitability_score\tliability_tier\tliability_codes\tselection_score\tselection_reasons\n"
            "P11111\tprotein_group_1\tROBUST1\t1\tobserved_discovery\tPEPTIDER\tPEPTIDER\ttrue\t6\t4\t1.0\t0.95\tstrong\tunique\t1.0\t0.95\thigh\t0.92\tpreferred\t\t0.95\tselected for targeted follow-up\n"
            "P22222\tprotein_group_2\tWARN2\t1\tobserved_discovery\tAAASHALEDK\tAAASHALEDK\ttrue\t5\t3\t0.75\t0.80\tstrong\tshared\t0.45\t0.62\tmedium\t0.58\tcaution\tdeamidation\t0.64\tselected for targeted follow-up\n",
            encoding="utf-8",
        )
        Path("assay_interference.assays.tsv").write_text(
            "assay_entry_id\ttarget_protein_ref\ttarget_protein_group_id\tgene_symbol\tpeptide_sequence\tcanonical_peptide\tpeptide_rank\tprecursor_charge\tprecursor_mz\tselected_transition_count\texported_transition_count\tshared_peptide_penalty\tpanel_overlap_transition_count\tbackground_overlap_peptide_count\tlibrary_overlap_peptide_count\tcoeluting_library_overlap_peptide_count\tintrinsic_transition_risk_score\tinterference_risk_score\tinterference_risk_tier\tdowngrade_reasons\tpanel_export_allowed\tpanel_export_caveat\tsource_library_entry_id\n"
            "assay:P11111:PEPTIDER\tP11111\tprotein_group_1\tROBUST1\tPEPTIDER\tPEPTIDER\t1\t2\t501.250000\t3\t3\t0.000000\t0\t0\t0\t0\t0.120000\t0.080000\tlow\t\ttrue\tassay is retained for panel export because interference evidence remains below the governed refusal threshold\tmgf:1:SEQ=PEPTIDER|PEPTIDE=PEPTIDER|PROTEINS=P11111\n"
            "assay:P22222:AAASHALEDK\tP22222\tprotein_group_2\tWARN2\tAAASHALEDK\tAAASHALEDK\t1\t2\t551.250000\t4\t3\t0.350000\t1\t1\t0\t0\t0.420000\t0.520000\tmedium\tlibrary_fragment_overlap\ttrue\tassay is retained but still carries measurable interference risk\t\n",
            encoding="utf-8",
        )
        Path("assay_interference.transitions.tsv").write_text(
            "assay_entry_id\ttarget_protein_ref\ttarget_protein_group_id\tgene_symbol\tpeptide_sequence\tcanonical_peptide\tprecursor_charge\tprecursor_mz\tfragment_label\tion_type\tfragment_ordinal\tfragment_charge\tfragment_sequence\tfragment_mz\texpected_relative_intensity\tselected_transition_rank\tintrinsic_interference_risk_score\tpanel_overlap_transition_count\tbackground_overlap_peptide_count\tlibrary_overlap_peptide_count\tcoeluting_library_overlap_peptide_count\tinterference_risk_score\tinterference_risk_tier\tdowngrade_reasons\texport_allowed\texport_caveat\n"
            "assay:P11111:PEPTIDER\tP11111\tprotein_group_1\tROBUST1\tPEPTIDER\tPEPTIDER\t2\t501.250000\ty7+1\ty\t7\t1\tPEPTIDER\t701.400000\t0.900000\t1\t0.120000\t0\t0\t0\t0\t0.100000\tlow\t\ttrue\ttransition is retained for targeted panel export\n"
            "assay:P11111:PEPTIDER\tP11111\tprotein_group_1\tROBUST1\tPEPTIDER\tPEPTIDER\t2\t501.250000\ty6+1\ty\t6\t1\tEPTIDER\t602.300000\t0.800000\t2\t0.110000\t0\t0\t0\t0\t0.090000\tlow\t\ttrue\ttransition is retained for targeted panel export\n"
            "assay:P22222:AAASHALEDK\tP22222\tprotein_group_2\tWARN2\tAAASHALEDK\tAAASHALEDK\t2\t551.250000\ty8+1\ty\t8\t1\tASHALEDK\t812.500000\t0.850000\t1\t0.220000\t1\t1\t0\t0\t0.410000\tmedium\tlibrary_fragment_overlap\ttrue\ttransition is retained for targeted panel export\n",
            encoding="utf-8",
        )
        Path("library.mgf").write_text(
            render_mgf(
                (
                    SpectrumModel(
                        spectrum_id="SEQ=PEPTIDER|PEPTIDE=PEPTIDER|PROTEINS=P11111",
                        title="SEQ=PEPTIDER|PEPTIDE=PEPTIDER|PROTEINS=P11111",
                        precursor_mz=501.25,
                        precursor_charge=2,
                        retention_time_seconds=18.4 * 60.0,
                        peaks=(
                            SpectrumPeak(mz=701.4, intensity=1000.0),
                            SpectrumPeak(mz=602.3, intensity=800.0),
                        ),
                    ),
                )
            ),
            encoding="utf-8",
        )

        result = runner.invoke(
            cli,
            [
                "targeted-panel-builder",
                "biomarker.candidates.tsv",
                "selected_peptides.tsv",
                "assay_interference.assays.tsv",
                "assay_interference.transitions.tsv",
                "--spectral-library",
                "library.mgf",
                "--summary-tsv-out",
                "panel.summary.tsv",
                "--assay-tsv-out",
                "panel.assays.tsv",
                "--panel-tsv-out",
                "panel.transitions.tsv",
                "--omitted-tsv-out",
                "panel.omitted.tsv",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["summary"]["biomarker_candidate_count"] == 3
        assert payload["summary"]["retained_assay_count"] == 2
        assert payload["summary"]["panel_transition_count"] == 3
        assert payload["summary"]["omitted_candidate_count"] == 1
        assert payload["panel_entries"][0]["biomarker_candidate_id"] == "protein:P11111"
        assert payload["panel_entries"][0]["expected_retention_time_minutes"] == 18.4
        assert payload["assay_entries"][1]["warning_codes"] == [
            "candidate_penalized",
            "elevated_interference_risk",
            "missing_expected_retention_time",
            "non_unique_target",
            "reduced_transition_support",
        ]
        assert payload["omitted_candidates"][0]["candidate_id"] == "ptm_site:P33333:S21"
        assert payload["outputs"]["panel_tsv"] == "panel.transitions.tsv"
        assert Path("panel.summary.tsv").exists()
        assert Path("panel.assays.tsv").exists()
        assert Path("panel.transitions.tsv").exists()
        assert Path("panel.omitted.tsv").exists()
        assert "retained_assay_count\t2" in Path("panel.summary.tsv").read_text(
            encoding="utf-8"
        )
        assert "expected_retention_time_minutes" in Path(
            "panel.transitions.tsv"
        ).read_text(encoding="utf-8")
        assert "uniqueness_class" in Path("panel.transitions.tsv").read_text(
            encoding="utf-8"
        )
        assert "candidate_penalized" in Path("panel.assays.tsv").read_text(
            encoding="utf-8"
        )
        assert "ptm_site:P33333:S21" in Path("panel.omitted.tsv").read_text(
            encoding="utf-8"
        )


def test_validation_experiment_planner_command_flags_underpowered_designs() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        Path("biomarker.candidates.tsv").write_text(
            "candidate_id\tcandidate_kind\tdisplay_label\ttarget_protein_ref\tsite_key\tpriority_rank\tfinal_score\tweighted_evidence_total\tpenalty_total\tuncertainty\teffect_size\tadjusted_p_value\tsupport_count\teffect_score\trobustness_score\tdetectability_score\tspecificity_score\tannotation_score\tassay_feasibility_score\tsample_qc_score\tannotation_labels\trank_reason_codes\tsource_ids\tranking_note\n"
            "protein:P11111\tprotein\tROBUST1\tP11111\t\t1\t0.91\t0.91\t0.00\t0.10\t1.10\t0.003\t4\t0.70\t0.85\t0.95\t0.94\t0.55\t0.92\t0.90\tpathway:stress\tassay_ready\tbio-card-1\tstrong validation-ready candidate\n"
            "protein:P22222\tprotein\tWARN2\tP22222\t\t2\t0.61\t0.70\t0.18\t0.30\t0.55\t0.020\t3\t0.40\t0.38\t0.62\t0.40\t0.30\t0.58\t0.90\tcontext:secreted\tweak_robustness\tbio-card-2\tcandidate carries evidence penalties\n",
            encoding="utf-8",
        )
        Path("selected_peptides.tsv").write_text(
            "target_protein_ref\ttarget_protein_group_id\tgene_symbol\trank\tcandidate_source\tpeptide_sequence\tcanonical_peptide\tobserved_in_discovery\tobserved_psm_count\trun_count\tdetection_frequency\treplicate_consistency\tprimary_evidence_class\tuniqueness_class\tuniqueness_score\tdetectability_score\tdetectability_tier\tsuitability_score\tliability_tier\tliability_codes\tselection_score\tselection_reasons\n"
            "P11111\tprotein_group_1\tROBUST1\t1\tobserved_discovery\tPEPTIDER\tPEPTIDER\ttrue\t6\t4\t0.95\t0.92\tstrong\tunique\t1.0\t0.95\thigh\t0.92\tpreferred\t\t0.95\tselected for targeted follow-up\n"
            "P22222\tprotein_group_2\tWARN2\t1\tobserved_discovery\tAAASHALEDK\tAAASHALEDK\ttrue\t5\t3\t0.58\t0.62\tstrong\tshared\t0.45\t0.62\tmedium\t0.58\tcaution\tdeamidation\t0.64\tselected for targeted follow-up\n",
            encoding="utf-8",
        )
        Path("panel.assays.tsv").write_text(
            "assay_entry_id\tbiomarker_candidate_id\tbiomarker_candidate_kind\tbiomarker_display_label\tbiomarker_priority_rank\ttarget_protein_ref\ttarget_protein_group_id\tgene_symbol\tpeptide_sequence\tcanonical_peptide\tuniqueness_class\tuniqueness_score\tprecursor_charge\tprecursor_mz\texpected_retention_time_minutes\tretention_window_start_minutes\tretention_window_end_minutes\tselected_transition_count\texported_transition_count\tassay_interference_risk_tier\twarning_codes\twarning_note\tsource_library_entry_id\n"
            "assay:P11111:PEPTIDER\tprotein:P11111\tprotein\tROBUST1\t1\tP11111\tprotein_group_1\tROBUST1\tPEPTIDER\tPEPTIDER\tunique\t1.000000\t2\t501.250000\t18.400000\t16.900000\t19.900000\t3\t3\tlow\t\tassay retained for targeted panel review\tmgf:1:SEQ=PEPTIDER|PEPTIDE=PEPTIDER|PROTEINS=P11111\n"
            "assay:P22222:AAASHALEDK\tprotein:P22222\tprotein\tWARN2\t2\tP22222\tprotein_group_2\tWARN2\tAAASHALEDK\tAAASHALEDK\tshared\t0.450000\t2\t551.250000\t\t\t\t4\t2\tmedium\tcandidate_penalized;non_unique_target;reduced_transition_support\tassay retained for targeted panel review\t\n",
            encoding="utf-8",
        )
        Path("panel.omitted.tsv").write_text(
            "candidate_id\tcandidate_kind\tdisplay_label\ttarget_protein_ref\tsite_key\tpriority_rank\tomission_reason\n"
            "ptm_site:P33333:S21\tptm_site\tP33333 S21 phospho-site\tP33333\tP33333:S21:phosphorylation\t3\tPTM-site candidate requires site-specific targeted assay design before validation planning\n",
            encoding="utf-8",
        )
        Path("power.variance.tsv").write_text(
            "entity_id\tprotein_refs\tobserved_sample_count\tmissing_sample_count\tmissing_fraction\tcontributing_condition_count\tused_global_variance_fallback\tpooled_log2_variance\tpooled_log2_stddev\n"
            "protein:P11111\tP11111\t8\t1\t0.08\t2\tfalse\t0.078400\t0.280000\n"
            "protein:P22222\tP22222\t8\t3\t0.36\t0\ttrue\t0.176400\t0.420000\n",
            encoding="utf-8",
        )

        result = runner.invoke(
            cli,
            [
                "validation-experiment-planner",
                "biomarker.candidates.tsv",
                "selected_peptides.tsv",
                "panel.assays.tsv",
                "--panel-omitted-tsv",
                "panel.omitted.tsv",
                "--power-variance-tsv",
                "power.variance.tsv",
                "--proposed-samples-per-group",
                "6",
                "--summary-tsv-out",
                "validation.summary.tsv",
                "--plan-tsv-out",
                "validation.plan.tsv",
                "--warning-tsv-out",
                "validation.warnings.tsv",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["summary"]["biomarker_candidate_count"] == 2
        assert payload["summary"]["planned_assay_count"] == 2
        assert payload["summary"]["omitted_candidate_count"] == 1
        assert payload["summary"]["underpowered_assay_count"] == 1
        by_assay = {
            entry["assay_entry_id"]: entry for entry in payload["plan_entries"]
        }
        assert by_assay["assay:P11111:PEPTIDER"]["planning_mode"] == "pilot_backed"
        assert by_assay["assay:P11111:PEPTIDER"]["underpowered"] is False
        assert by_assay["assay:P22222:AAASHALEDK"]["underpowered"] is True
        assert (
            by_assay["assay:P22222:AAASHALEDK"][
                "recommended_minimum_samples_per_group"
            ]
            > 6
        )
        warning_codes = {
            entry["warning_code"]: entry for entry in payload["warnings"]
        }
        assert "site_candidate_not_panelized" in warning_codes
        assert Path("validation.summary.tsv").exists()
        assert Path("validation.plan.tsv").exists()
        assert Path("validation.warnings.tsv").exists()
        assert "recommended_panel_samples_per_group" in Path(
            "validation.summary.tsv"
        ).read_text(encoding="utf-8")
        assert "planning_mode" in Path("validation.plan.tsv").read_text(
            encoding="utf-8"
        )
        assert "underpowered_design" in Path("validation.warnings.tsv").read_text(
            encoding="utf-8"
        )


def test_targeted_result_validator_command_preserves_confirmed_contradicted_and_inconclusive_targets() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        Path("biomarker.candidates.tsv").write_text(
            "candidate_id\tcandidate_kind\tdisplay_label\ttarget_protein_ref\tsite_key\tpriority_rank\tfinal_score\tweighted_evidence_total\tpenalty_total\tuncertainty\teffect_size\tadjusted_p_value\tsupport_count\teffect_score\trobustness_score\tdetectability_score\tspecificity_score\tannotation_score\tassay_feasibility_score\tsample_qc_score\tannotation_labels\trank_reason_codes\tsource_ids\tranking_note\n"
            "protein:P11111\tprotein\tROBUST1\tP11111\t\t1\t0.91\t0.91\t0.00\t0.10\t1.10\t0.003\t4\t0.70\t0.85\t0.95\t0.94\t0.55\t0.92\t0.90\tpathway:stress\tassay_ready\tbio-card-1\tstrong validation-ready candidate\n"
            "protein:P22222\tprotein\tWARN2\tP22222\t\t2\t0.71\t0.75\t0.00\t0.20\t0.90\t0.010\t3\t0.55\t0.74\t0.70\t0.80\t0.40\t0.84\t0.90\tcontext:secreted\tassay_ready\tbio-card-2\tdiscovery claimed treatment increase\n"
            "ptm_site:P33333:S21\tptm_site\tP33333 S21 site\tP33333\tP33333:S21:phosphorylation\t3\t0.67\t0.70\t0.00\t0.20\t0.80\t0.020\t2\t0.50\t0.66\t0.30\t0.60\t0.25\t0.40\t0.90\tptm:site\tlow_assay_feasibility\tptm-card-1\tsite candidate was not converted into a site-specific assay\n",
            encoding="utf-8",
        )
        Path("panel.assays.tsv").write_text(
            "assay_entry_id\tbiomarker_candidate_id\tbiomarker_candidate_kind\tbiomarker_display_label\tbiomarker_priority_rank\ttarget_protein_ref\ttarget_protein_group_id\tgene_symbol\tpeptide_sequence\tcanonical_peptide\tuniqueness_class\tuniqueness_score\tprecursor_charge\tprecursor_mz\texpected_retention_time_minutes\tretention_window_start_minutes\tretention_window_end_minutes\tselected_transition_count\texported_transition_count\tassay_interference_risk_tier\twarning_codes\twarning_note\tsource_library_entry_id\n"
            "assay:P11111:PEPTIDER\tprotein:P11111\tprotein\tROBUST1\t1\tP11111\tprotein_group_1\tROBUST1\tPEPTIDER\tPEPTIDER\tunique\t1.000000\t2\t501.250000\t18.400000\t16.900000\t19.900000\t3\t3\tlow\t\tassay retained for targeted panel review\tmgf:1:SEQ=PEPTIDER|PEPTIDE=PEPTIDER|PROTEINS=P11111\n"
            "assay:P22222:AAAAK\tprotein:P22222\tprotein\tWARN2\t2\tP22222\tprotein_group_2\tWARN2\tAAAAK\tAAAAK\tunique\t1.000000\t2\t451.250000\t18.400000\t16.900000\t19.900000\t3\t3\tlow\t\tassay retained for targeted panel review\tmgf:2:SEQ=AAAAK|PEPTIDE=AAAAK|PROTEINS=P22222\n",
            encoding="utf-8",
        )
        Path("targeted_results.tsv").write_text(
            "ProteinName\tPeptideModifiedSequence\tPrecursorCharge\tPrecursorMz\tFragmentIon\tProductMz\tReplicateName\tArea\tRetentionTime\tPeakQuality\n"
            "P11111\tPEPTIDER\t2\t501.25\ty7\t789.4\tcontrol_r1\t25000\t12.50\tpass\n"
            "P11111\tPEPTIDER\t2\t501.25\ty8\t902.5\tcontrol_r1\t20000\t12.56\tpass\n"
            "P11111\tPEPTIDER\t2\t501.25\ty7\t789.4\tcontrol_r2\t27000\t12.48\tpass\n"
            "P11111\tPEPTIDER\t2\t501.25\ty8\t902.5\tcontrol_r2\t21000\t12.55\tpass\n"
            "P11111\tPEPTIDER\t2\t501.25\ty7\t789.4\ttreat_r1\t120000\t12.51\tpass\n"
            "P11111\tPEPTIDER\t2\t501.25\ty8\t902.5\ttreat_r1\t98000\t12.57\tpass\n"
            "P11111\tPEPTIDER\t2\t501.25\ty7\t789.4\ttreat_r2\t118000\t12.52\tpass\n"
            "P11111\tPEPTIDER\t2\t501.25\ty8\t902.5\ttreat_r2\t95000\t12.58\tpass\n"
            "P22222\tAAAAK\t2\t451.25\ty3\t360.2\tcontrol_r1\t90000\t18.40\tpass\n"
            "P22222\tAAAAK\t2\t451.25\ty4\t431.2\tcontrol_r1\t87000\t18.47\tpass\n"
            "P22222\tAAAAK\t2\t451.25\ty3\t360.2\tcontrol_r2\t92000\t18.41\tpass\n"
            "P22222\tAAAAK\t2\t451.25\ty4\t431.2\tcontrol_r2\t86000\t18.48\tpass\n"
            "P22222\tAAAAK\t2\t451.25\ty3\t360.2\ttreat_r1\t93000\t18.42\tpass\n"
            "P22222\tAAAAK\t2\t451.25\ty4\t431.2\ttreat_r1\t85000\t18.46\tpass\n"
            "P22222\tAAAAK\t2\t451.25\ty3\t360.2\ttreat_r2\t91500\t18.40\tpass\n"
            "P22222\tAAAAK\t2\t451.25\ty4\t431.2\ttreat_r2\t85500\t18.45\tpass\n",
            encoding="utf-8",
        )
        Path("targeted.design.tsv").write_text(
            "sample_id\tcondition\treplicate\tfraction\tspectra_file\tidentifications_file\n"
            "control_r1\tcontrol\t1\t1\tcontrol_r1.raw\tcontrol_r1.tsv\n"
            "control_r2\tcontrol\t2\t1\tcontrol_r2.raw\tcontrol_r2.tsv\n"
            "treat_r1\ttreatment\t1\t1\ttreat_r1.raw\ttreat_r1.tsv\n"
            "treat_r2\ttreatment\t2\t1\ttreat_r2.raw\ttreat_r2.tsv\n",
            encoding="utf-8",
        )

        result = runner.invoke(
            cli,
            [
                "targeted-result-validator",
                "biomarker.candidates.tsv",
                "panel.assays.tsv",
                "targeted_results.tsv",
                "targeted.design.tsv",
                "--source-kind",
                "skyline_export",
                "--case-condition",
                "treatment",
                "--control-condition",
                "control",
                "--summary-tsv-out",
                "validation.summary.tsv",
                "--confirmed-tsv-out",
                "validation.confirmed.tsv",
                "--contradicted-tsv-out",
                "validation.contradicted.tsv",
                "--inconclusive-tsv-out",
                "validation.inconclusive.tsv",
                "--evidence-tsv-out",
                "validation.evidence.tsv",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["source_kind"] == "skyline_export"
        assert payload["summary"]["discovery_claim_count"] == 3
        assert payload["summary"]["confirmed_count"] == 1
        assert payload["summary"]["contradicted_count"] == 1
        assert payload["summary"]["inconclusive_count"] == 1
        assert payload["confirmed_targets"][0]["candidate_id"] == "protein:P11111"
        assert payload["contradicted_targets"][0]["candidate_id"] == "protein:P22222"
        assert payload["inconclusive_targets"][0]["candidate_id"] == "ptm_site:P33333:S21"
        assay_evidence_by_candidate = {
            entry["candidate_id"]: entry for entry in payload["assay_evidence"]
        }
        assert assay_evidence_by_candidate["protein:P11111"]["matched_target_id"] == "PEPTIDER/2"
        assert assay_evidence_by_candidate["protein:P22222"]["matched_target_id"] == "AAAAK/2"
        assert Path("validation.summary.tsv").exists()
        assert Path("validation.confirmed.tsv").exists()
        assert Path("validation.contradicted.tsv").exists()
        assert Path("validation.inconclusive.tsv").exists()
        assert Path("validation.evidence.tsv").exists()
        assert "confirmed_count\t1" in Path("validation.summary.tsv").read_text(
            encoding="utf-8"
        )
        assert "protein:P11111" in Path("validation.confirmed.tsv").read_text(
            encoding="utf-8"
        )
        assert "validation_effect_flat_against_discovery" in Path(
            "validation.contradicted.tsv"
        ).read_text(encoding="utf-8")
        assert "site_specific_validation_not_available" in Path(
            "validation.inconclusive.tsv"
        ).read_text(encoding="utf-8")
        assert "assay:P11111:PEPTIDER" in Path("validation.evidence.tsv").read_text(
            encoding="utf-8"
        )


def test_biomarker_stability_analysis_command_downgrades_unstable_candidates() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        Path("biomarker.candidates.tsv").write_text(
            "candidate_id\tcandidate_kind\tdisplay_label\ttarget_protein_ref\tsite_key\tpriority_rank\tfinal_score\tweighted_evidence_total\tpenalty_total\tuncertainty\teffect_size\tadjusted_p_value\tsupport_count\teffect_score\trobustness_score\tdetectability_score\tspecificity_score\tannotation_score\tassay_feasibility_score\tsample_qc_score\tannotation_labels\trank_reason_codes\tsource_ids\tranking_note\n"
            "protein:P11111\tprotein\tROBUST1\tP11111\t\t1\t0.92\t0.92\t0.00\t0.10\t1.00\t0.003\t4\t0.70\t0.88\t0.95\t0.94\t0.55\t0.90\t0.90\tpathway:stress\tassay_ready\tbio-card-1\tstrong candidate\n"
            "protein:P22222\tprotein\tBATCHY2\tP22222\t\t2\t0.84\t0.84\t0.05\t0.20\t0.80\t0.010\t3\t0.55\t0.79\t0.70\t0.80\t0.40\t0.86\t0.90\tcontext:secreted\tassay_ready\tbio-card-2\tcandidate with technical sensitivity\n"
            "protein:P33333\tprotein\tONECOND3\tP33333\t\t3\t0.80\t0.80\t0.02\t0.20\t0.70\t0.020\t2\t0.50\t0.72\t0.65\t0.75\t0.25\t0.84\t0.90\tcontext:restricted\tassay_ready\tbio-card-3\tcandidate visible only in one condition\n",
            encoding="utf-8",
        )
        Path("panel.assays.tsv").write_text(
            "assay_entry_id\tbiomarker_candidate_id\tbiomarker_candidate_kind\tbiomarker_display_label\tbiomarker_priority_rank\ttarget_protein_ref\ttarget_protein_group_id\tgene_symbol\tpeptide_sequence\tcanonical_peptide\tuniqueness_class\tuniqueness_score\tprecursor_charge\tprecursor_mz\texpected_retention_time_minutes\tretention_window_start_minutes\tretention_window_end_minutes\tselected_transition_count\texported_transition_count\tassay_interference_risk_tier\twarning_codes\twarning_note\tsource_library_entry_id\n"
            "assay:P11111:PEPTIDER\tprotein:P11111\tprotein\tROBUST1\t1\tP11111\tprotein_group_1\tROBUST1\tPEPTIDER\tPEPTIDER\tunique\t1.000000\t2\t501.250000\t18.400000\t16.900000\t19.900000\t2\t2\tlow\t\tassay retained\tmgf:1:SEQ=PEPTIDER|PEPTIDE=PEPTIDER|PROTEINS=P11111\n"
            "assay:P22222:AAAAK\tprotein:P22222\tprotein\tBATCHY2\t2\tP22222\tprotein_group_2\tBATCHY2\tAAAAK\tAAAAK\tunique\t1.000000\t2\t451.250000\t18.400000\t16.900000\t19.900000\t2\t2\tlow\t\tassay retained\tmgf:2:SEQ=AAAAK|PEPTIDE=AAAAK|PROTEINS=P22222\n"
            "assay:P33333:BBBBK\tprotein:P33333\tprotein\tONECOND3\t3\tP33333\tprotein_group_3\tONECOND3\tBBBBK\tBBBBK\tunique\t1.000000\t2\t551.250000\t16.400000\t14.900000\t17.900000\t2\t2\tlow\t\tassay retained\tmgf:3:SEQ=BBBBK|PEPTIDE=BBBBK|PROTEINS=P33333\n",
            encoding="utf-8",
        )
        Path("targeted_results.tsv").write_text(
            "ProteinName\tPeptideModifiedSequence\tPrecursorCharge\tPrecursorMz\tFragmentIon\tProductMz\tReplicateName\tArea\tRetentionTime\tPeakQuality\n"
            "P11111\tPEPTIDER\t2\t501.25\ty7\t789.4\tcontrol_t0_plasma_b1_r1\t10000\t12.50\tpass\n"
            "P11111\tPEPTIDER\t2\t501.25\ty8\t902.5\tcontrol_t0_plasma_b1_r1\t8200\t12.56\tpass\n"
            "P11111\tPEPTIDER\t2\t501.25\ty7\t789.4\tcontrol_t0_plasma_b2_r2\t10200\t12.48\tpass\n"
            "P11111\tPEPTIDER\t2\t501.25\ty8\t902.5\tcontrol_t0_plasma_b2_r2\t8300\t12.55\tpass\n"
            "P11111\tPEPTIDER\t2\t501.25\ty7\t789.4\tcontrol_t1_serum_b1_r1\t9800\t12.51\tpass\n"
            "P11111\tPEPTIDER\t2\t501.25\ty8\t902.5\tcontrol_t1_serum_b1_r1\t7900\t12.57\tpass\n"
            "P11111\tPEPTIDER\t2\t501.25\ty7\t789.4\tcontrol_t1_serum_b2_r2\t10100\t12.52\tpass\n"
            "P11111\tPEPTIDER\t2\t501.25\ty8\t902.5\tcontrol_t1_serum_b2_r2\t8100\t12.58\tpass\n"
            "P11111\tPEPTIDER\t2\t501.25\ty7\t789.4\ttreat_t0_plasma_b1_r1\t21000\t12.50\tpass\n"
            "P11111\tPEPTIDER\t2\t501.25\ty8\t902.5\ttreat_t0_plasma_b1_r1\t17000\t12.56\tpass\n"
            "P11111\tPEPTIDER\t2\t501.25\ty7\t789.4\ttreat_t0_plasma_b2_r2\t20800\t12.48\tpass\n"
            "P11111\tPEPTIDER\t2\t501.25\ty8\t902.5\ttreat_t0_plasma_b2_r2\t16800\t12.55\tpass\n"
            "P11111\tPEPTIDER\t2\t501.25\ty7\t789.4\ttreat_t1_serum_b1_r1\t21400\t12.51\tpass\n"
            "P11111\tPEPTIDER\t2\t501.25\ty8\t902.5\ttreat_t1_serum_b1_r1\t17100\t12.57\tpass\n"
            "P11111\tPEPTIDER\t2\t501.25\ty7\t789.4\ttreat_t1_serum_b2_r2\t21100\t12.52\tpass\n"
            "P11111\tPEPTIDER\t2\t501.25\ty8\t902.5\ttreat_t1_serum_b2_r2\t16950\t12.58\tpass\n"
            "P22222\tAAAAK\t2\t451.25\ty3\t360.2\tcontrol_t0_plasma_b1_r1\t12000\t18.40\tpass\n"
            "P22222\tAAAAK\t2\t451.25\ty4\t431.2\tcontrol_t0_plasma_b1_r1\t10000\t18.47\tpass\n"
            "P22222\tAAAAK\t2\t451.25\ty3\t360.2\tcontrol_t0_plasma_b2_r2\t36000\t18.41\tpass\n"
            "P22222\tAAAAK\t2\t451.25\ty4\t431.2\tcontrol_t0_plasma_b2_r2\t30000\t18.48\tpass\n"
            "P22222\tAAAAK\t2\t451.25\ty3\t360.2\tcontrol_t1_serum_b1_r1\t12200\t18.42\tpass\n"
            "P22222\tAAAAK\t2\t451.25\ty4\t431.2\tcontrol_t1_serum_b1_r1\t10100\t18.46\tpass\n"
            "P22222\tAAAAK\t2\t451.25\ty3\t360.2\tcontrol_t1_serum_b2_r2\t35500\t18.40\tpass\n"
            "P22222\tAAAAK\t2\t451.25\ty4\t431.2\tcontrol_t1_serum_b2_r2\t29500\t18.45\tpass\n"
            "P22222\tAAAAK\t2\t451.25\ty3\t360.2\ttreat_t0_plasma_b1_r1\t14000\t18.40\tpass\n"
            "P22222\tAAAAK\t2\t451.25\ty4\t431.2\ttreat_t0_plasma_b1_r1\t11500\t18.47\tpass\n"
            "P22222\tAAAAK\t2\t451.25\ty3\t360.2\ttreat_t0_plasma_b2_r2\t37000\t18.41\tpass\n"
            "P22222\tAAAAK\t2\t451.25\ty4\t431.2\ttreat_t0_plasma_b2_r2\t30500\t18.48\tpass\n"
            "P22222\tAAAAK\t2\t451.25\ty3\t360.2\ttreat_t1_serum_b1_r1\t14100\t18.42\tpass\n"
            "P22222\tAAAAK\t2\t451.25\ty4\t431.2\ttreat_t1_serum_b1_r1\t11600\t18.46\tpass\n"
            "P22222\tAAAAK\t2\t451.25\ty3\t360.2\ttreat_t1_serum_b2_r2\t37200\t18.40\tpass\n"
            "P22222\tAAAAK\t2\t451.25\ty4\t431.2\ttreat_t1_serum_b2_r2\t30700\t18.45\tpass\n"
            "P33333\tBBBBK\t2\t551.25\ty3\t460.2\ttreat_t0_plasma_b1_r1\t16000\t16.40\tpass\n"
            "P33333\tBBBBK\t2\t551.25\ty4\t531.2\ttreat_t0_plasma_b1_r1\t13500\t16.47\tpass\n"
            "P33333\tBBBBK\t2\t551.25\ty3\t460.2\ttreat_t0_plasma_b2_r2\t15800\t16.41\tpass\n"
            "P33333\tBBBBK\t2\t551.25\ty4\t531.2\ttreat_t0_plasma_b2_r2\t13300\t16.48\tpass\n"
            "P33333\tBBBBK\t2\t551.25\ty3\t460.2\ttreat_t1_serum_b1_r1\t16200\t16.42\tpass\n"
            "P33333\tBBBBK\t2\t551.25\ty4\t531.2\ttreat_t1_serum_b1_r1\t13650\t16.46\tpass\n"
            "P33333\tBBBBK\t2\t551.25\ty3\t460.2\ttreat_t1_serum_b2_r2\t16100\t16.40\tpass\n"
            "P33333\tBBBBK\t2\t551.25\ty4\t531.2\ttreat_t1_serum_b2_r2\t13700\t16.45\tpass\n",
            encoding="utf-8",
        )
        Path("targeted.design.tsv").write_text(
            "sample_id\tcondition\treplicate\tfraction\tspectra_file\tidentifications_file\tbatch\ttimepoint\tsample_type\n"
            "control_t0_plasma_b1_r1\tcontrol\t1\t1\tcontrol_t0_plasma_b1_r1.raw\tcontrol_t0_plasma_b1_r1.tsv\tb1\tt0\tplasma\n"
            "control_t0_plasma_b2_r2\tcontrol\t2\t1\tcontrol_t0_plasma_b2_r2.raw\tcontrol_t0_plasma_b2_r2.tsv\tb2\tt0\tplasma\n"
            "control_t1_serum_b1_r1\tcontrol\t3\t1\tcontrol_t1_serum_b1_r1.raw\tcontrol_t1_serum_b1_r1.tsv\tb1\tt1\tserum\n"
            "control_t1_serum_b2_r2\tcontrol\t4\t1\tcontrol_t1_serum_b2_r2.raw\tcontrol_t1_serum_b2_r2.tsv\tb2\tt1\tserum\n"
            "treat_t0_plasma_b1_r1\ttreatment\t1\t1\ttreat_t0_plasma_b1_r1.raw\ttreat_t0_plasma_b1_r1.tsv\tb1\tt0\tplasma\n"
            "treat_t0_plasma_b2_r2\ttreatment\t2\t1\ttreat_t0_plasma_b2_r2.raw\ttreat_t0_plasma_b2_r2.tsv\tb2\tt0\tplasma\n"
            "treat_t1_serum_b1_r1\ttreatment\t3\t1\ttreat_t1_serum_b1_r1.raw\ttreat_t1_serum_b1_r1.tsv\tb1\tt1\tserum\n"
            "treat_t1_serum_b2_r2\ttreatment\t4\t1\ttreat_t1_serum_b2_r2.raw\ttreat_t1_serum_b2_r2.tsv\tb2\tt1\tserum\n",
            encoding="utf-8",
        )

        result = runner.invoke(
            cli,
            [
                "biomarker-stability-analysis",
                "biomarker.candidates.tsv",
                "panel.assays.tsv",
                "targeted_results.tsv",
                "targeted.design.tsv",
                "--source-kind",
                "skyline_export",
                "--summary-tsv-out",
                "stability.summary.tsv",
                "--stability-tsv-out",
                "stability.entries.tsv",
                "--subgroup-tsv-out",
                "stability.subgroups.tsv",
                "--adjusted-candidate-tsv-out",
                "stability.candidates.tsv",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["summary"]["candidate_count"] == 3
        assert payload["summary"]["downgraded_candidate_count"] == 2
        entries_by_id = {entry["candidate_id"]: entry for entry in payload["entries"]}
        assert entries_by_id["protein:P11111"]["downgraded"] is False
        assert entries_by_id["protein:P22222"]["downgraded"] is True
        assert "batch_sensitive_signal" in entries_by_id["protein:P22222"][
            "instability_reasons"
        ]
        assert entries_by_id["protein:P33333"]["downgraded"] is True
        assert "single_condition_signal_only" in entries_by_id["protein:P33333"][
            "instability_reasons"
        ]
        assert Path("stability.summary.tsv").exists()
        assert Path("stability.entries.tsv").exists()
        assert Path("stability.subgroups.tsv").exists()
        assert Path("stability.candidates.tsv").exists()
        assert "downgraded_candidate_count\t2" in Path(
            "stability.summary.tsv"
        ).read_text(encoding="utf-8")
        assert "batch_sensitive_signal" in Path("stability.entries.tsv").read_text(
            encoding="utf-8"
        )
        subgroup_tsv = Path("stability.subgroups.tsv").read_text(encoding="utf-8")
        assert "candidate_id\tdimension\tsubgroup_value" in subgroup_tsv
        assert "protein:P22222\tbatch\tb2" in subgroup_tsv
        assert "protein:P11111" in Path("stability.candidates.tsv").read_text(
            encoding="utf-8"
        )


def test_biomarker_panel_redundancy_analysis_command_reduces_highly_correlated_candidates() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        Path("biomarker.candidates.tsv").write_text(
            "candidate_id\tcandidate_kind\tdisplay_label\ttarget_protein_ref\tsite_key\tpriority_rank\tfinal_score\tpenalty_total\trank_reason_codes\tranking_note\n"
            "protein:P11111\tprotein\tREP1\tP11111\t\t1\t0.92\t0.05\tassay_ready\tprimary candidate\n"
            "protein:P22222\tprotein\tRED2\tP22222\t\t2\t0.81\t0.09\tassay_ready\thighly correlated neighbor\n"
            "protein:P33333\tprotein\tDISTINCT3\tP33333\t\t3\t0.76\t0.10\tassay_ready\tdistinct candidate\n",
            encoding="utf-8",
        )
        Path("panel.assays.tsv").write_text(
            "assay_entry_id\tbiomarker_candidate_id\tbiomarker_candidate_kind\tbiomarker_display_label\tbiomarker_priority_rank\ttarget_protein_ref\ttarget_protein_group_id\tgene_symbol\tpeptide_sequence\tcanonical_peptide\tuniqueness_class\tprecursor_charge\tselected_transition_count\texported_transition_count\twarning_codes\twarning_note\n"
            "assay:P11111:PEPTIDER\tprotein:P11111\tprotein\tREP1\t1\tP11111\tprotein_group_1\tREP1\tPEPTIDER\tPEPTIDER\tunique\t2\t2\t2\t\tassay retained\n"
            "assay:P22222:AAAAK\tprotein:P22222\tprotein\tRED2\t2\tP22222\tprotein_group_2\tRED2\tAAAAK\tAAAAK\tunique\t2\t2\t2\t\tassay retained\n"
            "assay:P33333:BBBBK\tprotein:P33333\tprotein\tDISTINCT3\t3\tP33333\tprotein_group_3\tDISTINCT3\tBBBBK\tBBBBK\tunique\t2\t2\t2\t\tassay retained\n",
            encoding="utf-8",
        )
        Path("targeted_results.tsv").write_text(
            "ProteinName\tPeptideModifiedSequence\tPrecursorCharge\tPrecursorMz\tFragmentIon\tProductMz\tReplicateName\tArea\tRetentionTime\tPeakQuality\n"
            "P11111\tPEPTIDER\t2\t501.25\ty7\t789.4\tcontrol_r1\t10000\t12.50\tpass\n"
            "P11111\tPEPTIDER\t2\t501.25\ty8\t902.5\tcontrol_r1\t8200\t12.56\tpass\n"
            "P11111\tPEPTIDER\t2\t501.25\ty7\t789.4\tcontrol_r2\t10500\t12.49\tpass\n"
            "P11111\tPEPTIDER\t2\t501.25\ty8\t902.5\tcontrol_r2\t8400\t12.55\tpass\n"
            "P11111\tPEPTIDER\t2\t501.25\ty7\t789.4\ttreat_r1\t22000\t12.50\tpass\n"
            "P11111\tPEPTIDER\t2\t501.25\ty8\t902.5\ttreat_r1\t17800\t12.56\tpass\n"
            "P11111\tPEPTIDER\t2\t501.25\ty7\t789.4\ttreat_r2\t22500\t12.49\tpass\n"
            "P11111\tPEPTIDER\t2\t501.25\ty8\t902.5\ttreat_r2\t18100\t12.55\tpass\n"
            "P22222\tAAAAK\t2\t451.25\ty3\t360.2\tcontrol_r1\t8000\t18.40\tpass\n"
            "P22222\tAAAAK\t2\t451.25\ty4\t431.2\tcontrol_r1\t6600\t18.47\tpass\n"
            "P22222\tAAAAK\t2\t451.25\ty3\t360.2\tcontrol_r2\t8400\t18.41\tpass\n"
            "P22222\tAAAAK\t2\t451.25\ty4\t431.2\tcontrol_r2\t6900\t18.48\tpass\n"
            "P22222\tAAAAK\t2\t451.25\ty3\t360.2\ttreat_r1\t17600\t18.40\tpass\n"
            "P22222\tAAAAK\t2\t451.25\ty4\t431.2\ttreat_r1\t14400\t18.47\tpass\n"
            "P22222\tAAAAK\t2\t451.25\ty3\t360.2\ttreat_r2\t18000\t18.41\tpass\n"
            "P22222\tAAAAK\t2\t451.25\ty4\t431.2\ttreat_r2\t14700\t18.48\tpass\n"
            "P33333\tBBBBK\t2\t551.25\ty3\t460.2\tcontrol_r1\t20000\t16.40\tpass\n"
            "P33333\tBBBBK\t2\t551.25\ty4\t531.2\tcontrol_r1\t16200\t16.47\tpass\n"
            "P33333\tBBBBK\t2\t551.25\ty3\t460.2\tcontrol_r2\t20500\t16.42\tpass\n"
            "P33333\tBBBBK\t2\t551.25\ty4\t531.2\tcontrol_r2\t16600\t16.46\tpass\n"
            "P33333\tBBBBK\t2\t551.25\ty3\t460.2\ttreat_r1\t9000\t16.41\tpass\n"
            "P33333\tBBBBK\t2\t551.25\ty4\t531.2\ttreat_r1\t7300\t16.48\tpass\n"
            "P33333\tBBBBK\t2\t551.25\ty3\t460.2\ttreat_r2\t9200\t16.40\tpass\n"
            "P33333\tBBBBK\t2\t551.25\ty4\t531.2\ttreat_r2\t7500\t16.45\tpass\n",
            encoding="utf-8",
        )
        Path("targeted.design.tsv").write_text(
            "sample_id\tcondition\treplicate\tfraction\tspectra_file\tidentifications_file\tbatch\n"
            "control_r1\tcontrol\t1\t1\tcontrol_r1.raw\tcontrol_r1.tsv\tb1\n"
            "control_r2\tcontrol\t2\t1\tcontrol_r2.raw\tcontrol_r2.tsv\tb1\n"
            "treat_r1\ttreatment\t1\t1\ttreat_r1.raw\ttreat_r1.tsv\tb1\n"
            "treat_r2\ttreatment\t2\t1\ttreat_r2.raw\ttreat_r2.tsv\tb1\n",
            encoding="utf-8",
        )

        result = runner.invoke(
            cli,
            [
                "biomarker-panel-redundancy-analysis",
                "biomarker.candidates.tsv",
                "panel.assays.tsv",
                "targeted_results.tsv",
                "targeted.design.tsv",
                "--source-kind",
                "skyline_export",
                "--summary-tsv-out",
                "redundancy.summary.tsv",
                "--cluster-tsv-out",
                "redundancy.clusters.tsv",
                "--reduced-candidate-tsv-out",
                "redundancy.candidates.tsv",
                "--dropped-candidate-tsv-out",
                "redundancy.dropped.tsv",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["summary"]["candidate_count"] == 3
        assert payload["summary"]["cluster_count"] == 2
        assert payload["summary"]["dropped_candidate_count"] == 1
        cluster_with_drop = next(
            entry for entry in payload["clusters"] if entry["dropped_count"] == 1
        )
        assert cluster_with_drop["representative_candidate_id"] == "protein:P11111"
        assert "protein:P22222" in cluster_with_drop["dropped_candidate_ids"]
        candidates_by_id = {
            entry["candidate_id"]: entry for entry in payload["candidates"]
        }
        assert candidates_by_id["protein:P11111"]["representative"] is True
        assert candidates_by_id["protein:P22222"]["dropped"] is True
        assert "high_signal_correlation" in candidates_by_id["protein:P22222"][
            "redundancy_reason_codes"
        ]
        assert payload["outputs"]["summary_tsv"] == "redundancy.summary.tsv"
        assert Path("redundancy.summary.tsv").exists()
        assert Path("redundancy.clusters.tsv").exists()
        assert Path("redundancy.candidates.tsv").exists()
        assert Path("redundancy.dropped.tsv").exists()
        assert "dropped_candidate_count\t1" in Path(
            "redundancy.summary.tsv"
        ).read_text(encoding="utf-8")
        assert "cluster:001" in Path("redundancy.clusters.tsv").read_text(
            encoding="utf-8"
        )
        assert "protein:P22222" in Path("redundancy.dropped.tsv").read_text(
            encoding="utf-8"
        )


def test_validation_evidence_cards_command_derives_candidate_status_from_evidence() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        Path("biomarker.candidates.tsv").write_text(
            "candidate_id\tcandidate_kind\tdisplay_label\ttarget_protein_ref\tsite_key\tpriority_rank\tfinal_score\tweighted_evidence_total\tpenalty_total\tuncertainty\teffect_size\tadjusted_p_value\tsupport_count\teffect_score\trobustness_score\tdetectability_score\tspecificity_score\tannotation_score\tassay_feasibility_score\tsample_qc_score\tannotation_labels\trank_reason_codes\tsource_ids\tranking_note\n"
            "protein:P11111\tprotein\tKIN1\tP11111\t\t1\t0.920000\t0.920000\t0.020000\t0.040000\t1.7\t0.002\t4\t0.9\t0.9\t0.9\t0.9\t0.8\t0.9\t0.9\tpathway:stress_response;domain:kinase\tassay_ready\tprotein-card:KIN1\tstrong kinase biomarker candidate\n"
            "protein:P22222\tprotein\tKIN2\tP22222\t\t2\t0.810000\t0.810000\t0.080000\t0.070000\t1.2\t0.01\t3\t0.8\t0.8\t0.8\t0.8\t0.7\t0.8\t0.8\tpathway:stress_response\tassay_ready\tprotein-card:KIN2\tcorrelated neighbor candidate\n"
            "ptm_site:P33333:S21\tptm_site\tP33333 S21\tP33333\tP33333:S21:phosphorylation\t3\t0.790000\t0.790000\t0.030000\t0.050000\t1.1\t0.005\t5\t0.8\t0.8\t0.8\t0.8\t0.8\t0.8\t0.8\tmechanism:site_specific;ortholog:conserved\tassay_ready\tptm-card:P33333:S21\tsite-specific phosphosite candidate\n"
            "protein:P44444\tprotein\tKIN4\tP44444\t\t4\t0.770000\t0.770000\t0.010000\t0.060000\t0.9\t0.02\t2\t0.7\t0.7\t0.7\t0.7\t0.6\t0.7\t0.7\tpathway:repair\tassay_ready\tprotein-card:KIN4\tcandidate requires stability review\n",
            encoding="utf-8",
        )
        Path("panel.assays.tsv").write_text(
            "assay_entry_id\tbiomarker_candidate_id\tbiomarker_candidate_kind\tbiomarker_display_label\tbiomarker_priority_rank\ttarget_protein_ref\ttarget_protein_group_id\tgene_symbol\tpeptide_sequence\tcanonical_peptide\tuniqueness_class\tuniqueness_score\tprecursor_charge\tprecursor_mz\texpected_retention_time_minutes\tretention_window_start_minutes\tretention_window_end_minutes\tselected_transition_count\texported_transition_count\tassay_interference_risk_tier\twarning_codes\twarning_note\tsource_library_entry_id\n"
            "assay:P11111:PEPTIDER\tprotein:P11111\tprotein\tKIN1\t1\tP11111\tprotein_group_1\tKIN1\tPEPTIDER\tPEPTIDER\tunique\t1.000000\t2\t501.250000\t12.500000\t11.000000\t14.000000\t3\t3\tlow\t\tassay retained for panel export\t\n"
            "assay:P22222:AAAAK\tprotein:P22222\tprotein\tKIN2\t2\tP22222\tprotein_group_2\tKIN2\tAAAAK\tAAAAK\tunique\t1.000000\t2\t451.250000\t18.400000\t17.000000\t20.000000\t3\t3\tlow\t\tassay retained for panel export\t\n"
            "assay:P44444:LOWUNIQ\tprotein:P44444\tprotein\tKIN4\t4\tP44444\tprotein_group_4\tKIN4\tLOWUNIQ\tLOWUNIQ\tshared\t0.400000\t2\t601.250000\t22.100000\t20.500000\t23.500000\t2\t2\tmedium\tnon_unique_target\tshared assay retained with caveat\t\n",
            encoding="utf-8",
        )
        Path("panel.omitted.tsv").write_text(
            "candidate_id\tcandidate_kind\tdisplay_label\ttarget_protein_ref\tsite_key\tpriority_rank\tomission_reason\n"
            "ptm_site:P33333:S21\tptm_site\tP33333 S21\tP33333\tP33333:S21:phosphorylation\t3\tsite-specific candidate remains omitted because no governed site-resolved targeted assay is available\n",
            encoding="utf-8",
        )
        Path("confirmed.tsv").write_text(
            "candidate_id\tcandidate_kind\tdisplay_label\ttarget_protein_ref\tsite_key\tpriority_rank\tdiscovery_effect_size\tdiscovery_direction\tvalidation_log2_effect\tvalidation_direction\tverdict\tassay_evidence_count\tconfirmed_assay_count\tcontradicted_assay_count\tinconclusive_assay_count\treason_codes\tnote\n"
            "protein:P11111\tprotein\tKIN1\tP11111\t\t1\t1.7\tup\t1.5\tup\tconfirmed\t1\t1\t0\t0\tvalidation_effect_matches_discovery\ttargeted validation matches discovery direction and effect\n",
            encoding="utf-8",
        )
        Path("inconclusive.tsv").write_text(
            "candidate_id\tcandidate_kind\tdisplay_label\ttarget_protein_ref\tsite_key\tpriority_rank\tdiscovery_effect_size\tdiscovery_direction\tvalidation_log2_effect\tvalidation_direction\tverdict\tassay_evidence_count\tconfirmed_assay_count\tcontradicted_assay_count\tinconclusive_assay_count\treason_codes\tnote\n"
            "protein:P44444\tprotein\tKIN4\tP44444\t\t4\t0.9\tup\t0.1\tflat\tinconclusive\t1\t0\t0\t1\tnon_unique_validation_assay;weak_validation_effect\tshared assay and weak targeted effect leave the candidate unresolved\n",
            encoding="utf-8",
        )
        Path("validation.evidence.tsv").write_text(
            "candidate_id\tassay_entry_id\ttarget_protein_ref\tpeptide_sequence\tcanonical_peptide\tprecursor_charge\tuniqueness_class\tmatched_target_id\tmatched_target_count\tcase_condition\tcontrol_condition\tcase_reliable_sample_count\tcontrol_reliable_sample_count\tcase_mean_log2_intensity\tcontrol_mean_log2_intensity\tvalidation_log2_effect\tdiscovery_effect_size\tdiscovery_direction\tvalidation_direction\tverdict\treason_codes\tnote\n"
            "protein:P11111\tassay:P11111:PEPTIDER\tP11111\tPEPTIDER\tPEPTIDER\t2\tunique\ttarget:1\t1\ttreatment\tcontrol\t2\t2\t16.0\t14.5\t1.5\t1.7\tup\tup\tconfirmed\tvalidation_effect_matches_discovery\tunique assay confirms the discovery signal\n"
            "protein:P44444\tassay:P44444:LOWUNIQ\tP44444\tLOWUNIQ\tLOWUNIQ\t2\tshared\ttarget:2\t1\ttreatment\tcontrol\t2\t2\t13.2\t13.1\t0.1\t0.9\tup\tflat\tinconclusive\tnon_unique_validation_assay;weak_validation_effect\tshared assay does not resolve the discovery claim\n",
            encoding="utf-8",
        )
        Path("stability.candidates.tsv").write_text(
            "candidate_id\tcandidate_kind\tdisplay_label\ttarget_protein_ref\tsite_key\tpriority_rank\tfinal_score\tpenalty_total\trank_reason_codes\tranking_note\toriginal_priority_rank\toriginal_final_score\tstability_score\tstability_penalty\tdowngraded\tinstability_reasons\n"
            "protein:P44444\tprotein\tKIN4\tP44444\t\t4\t0.580000\t0.200000\tsample_type_sensitive_signal\tsubgroup behavior suggests sample-type-sensitive instability\t4\t0.770000\t0.580000\t0.190000\ttrue\tsample_type_sensitive_signal\n",
            encoding="utf-8",
        )
        Path("redundancy.candidates.tsv").write_text(
            "candidate_id\tcandidate_kind\tdisplay_label\ttarget_protein_ref\tsite_key\tpriority_rank\tfinal_score\tpenalty_total\trank_reason_codes\tranking_note\tcluster_id\trepresentative_candidate_id\trepresentative\tdropped\tshared_sample_count\tmax_redundant_correlation\tredundancy_reason_codes\n"
            "protein:P11111\tprotein\tKIN1\tP11111\t\t1\t0.920000\t0.020000\tassay_ready\trepresentative retained for correlated cluster\tcluster:001\tprotein:P11111\ttrue\tfalse\t4\t0.970000\thigh_signal_correlation\n"
            "protein:P22222\tprotein\tKIN2\tP22222\t\t2\t0.810000\t0.080000\tassay_ready\tdropped in favor of the representative correlated marker\tcluster:001\tprotein:P11111\tfalse\ttrue\t4\t0.970000\thigh_signal_correlation;lower_scoring_cluster_member\n",
            encoding="utf-8",
        )

        result = runner.invoke(
            cli,
            [
                "validation-evidence-cards",
                "biomarker.candidates.tsv",
                "panel.assays.tsv",
                "--panel-omitted-tsv",
                "panel.omitted.tsv",
                "--confirmed-tsv",
                "confirmed.tsv",
                "--inconclusive-tsv",
                "inconclusive.tsv",
                "--validation-evidence-tsv",
                "validation.evidence.tsv",
                "--stability-candidate-tsv",
                "stability.candidates.tsv",
                "--redundancy-candidate-tsv",
                "redundancy.candidates.tsv",
                "--summary-tsv-out",
                "validation_cards.summary.tsv",
                "--card-tsv-out",
                "validation_cards.cards.tsv",
                "--assay-tsv-out",
                "validation_cards.assays.tsv",
                "--warning-tsv-out",
                "validation_cards.warnings.tsv",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["summary"]["candidate_count"] == 4
        assert payload["summary"]["confirmed_count"] == 1
        assert payload["summary"]["inconclusive_count"] == 1
        assert payload["summary"]["deprioritized_as_redundant_count"] == 1
        assert payload["summary"]["blocked_by_assay_design_count"] == 1
        cards_by_id = {entry["candidate_id"]: entry for entry in payload["cards"]}
        assert cards_by_id["protein:P11111"]["final_status"] == "confirmed"
        assert (
            cards_by_id["protein:P22222"]["final_status"]
            == "deprioritized_as_redundant"
        )
        assert (
            cards_by_id["ptm_site:P33333:S21"]["final_status"]
            == "blocked_by_assay_design"
        )
        assert cards_by_id["protein:P44444"]["final_status"] == "inconclusive"
        assert "pathway:stress_response" in cards_by_id["protein:P11111"][
            "biological_role_labels"
        ]
        assert payload["outputs"]["card_tsv"] == "validation_cards.cards.tsv"
        assert Path("validation_cards.summary.tsv").exists()
        assert Path("validation_cards.cards.tsv").exists()
        assert Path("validation_cards.assays.tsv").exists()
        assert Path("validation_cards.warnings.tsv").exists()
        assert "confirmed_count\t1" in Path(
            "validation_cards.summary.tsv"
        ).read_text(encoding="utf-8")
        assert "deprioritized_as_redundant" in Path(
            "validation_cards.cards.tsv"
        ).read_text(encoding="utf-8")
        assert "assay:P11111:PEPTIDER" in Path(
            "validation_cards.assays.tsv"
        ).read_text(encoding="utf-8")
        assert "stability_downgraded" in Path(
            "validation_cards.warnings.tsv"
        ).read_text(encoding="utf-8")


def test_biomarker_candidate_ranking_command_prioritizes_validation_ready_candidates() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        biological_report_dir = Path("biological_report")
        biological_report_dir.mkdir()
        biological_report_dir.joinpath("biological_report_summary.tsv").write_text(
            "field\tvalue\n"
            "experiment_confidence_score\t0.92\n",
            encoding="utf-8",
        )
        biological_report_dir.joinpath("biological_protein_cards.tsv").write_text(
            "card_id\tprotein_group_id\trepresentative_protein_ref\tgene_symbol\tidentity_level\tunique_peptide_count\tshared_peptide_count\tevidence_tier\tpathway_ids\tcontext_ids\tfunctional_regions\tproteogenomic_support_class\tptm_sites\twarning_codes\n"
            "protein-card:strong\tprotein_group_strong\tP11111\tROBUST1\tprotein_level\t3\t0\thigh\tstress_response\tcytosol\tkinase_domain\tshared\tS15\t\n"
            "protein-card:famous\tprotein_group_famous\tP22222\tFAMOUS1\tgene_level\t0\t2\twarning\tapoptosis;cell_cycle\tsecreted;membrane\thotspot;motif\tvariant_only\tS34;T56\tlow_support\n",
            encoding="utf-8",
        )
        biological_report_dir.joinpath("biological_differential.tsv").write_text(
            "entity_id\tlog2_fold_change\tadjusted_p_value\trobustness_score\n"
            "protein_group_strong\t1.8\t0.002\t0.91\n"
            "protein_group_famous\t0.2\t0.045\t0.18\n",
            encoding="utf-8",
        )
        ptm_report_dir = Path("ptm_report")
        ptm_report_dir.mkdir()
        ptm_report_dir.joinpath("ptm_evidence_cards.tsv").write_text(
            "card_id\tsite_key\tprotein_ref\tresidue\tposition\tmodification_name\tidentity_level\tlocalization_tier\tmechanism_class\tpeptide_spectrum_count\tobserved_sample_count\tcentered_windows\tortholog_conservation_status\tfunctional_regions\tregulators\twarning_codes\n"
            "ptm-card:1\tP33333:S21:phosphorylation\tP33333\tS\t21\tphosphorylation\tprotein_level\thigh\tsite_specific\t7\t4\tRXXS\tconserved\tactivation_loop\tKINASE_A\t\n",
            encoding="utf-8",
        )
        ptm_report_dir.joinpath("ptm_differential.tsv").write_text(
            "site_key\tlow_localization\tambiguous\tshared_peptide\tlog2_fold_change\tadjusted_p_value\timputation_dependent_hit\tprotein_correction_status\n"
            "P33333:S21:phosphorylation\tfalse\tfalse\tfalse\t1.1\t0.004\tfalse\tcorrected\n",
            encoding="utf-8",
        )
        Path("selected_peptides.tsv").write_text(
            "target_protein_ref\tdetectability_score\tuniqueness_score\tsuitability_score\n"
            "P11111\t0.96\t0.98\t0.94\n"
            "P22222\t0.05\t0.10\t0.04\n",
            encoding="utf-8",
        )
        Path("assay_interference.assays.tsv").write_text(
            "target_protein_ref\tinterference_risk_score\tpanel_export_allowed\texported_transition_count\n"
            "P11111\t0.08\ttrue\t4\n"
            "P22222\t0.96\tfalse\t1\n",
            encoding="utf-8",
        )

        result = runner.invoke(
            cli,
            [
                "biomarker-candidate-ranking",
                "--biological-report-dir",
                "biological_report",
                "--ptm-report-dir",
                "ptm_report",
                "--selected-peptide-tsv",
                "selected_peptides.tsv",
                "--assay-interference-assay-tsv",
                "assay_interference.assays.tsv",
                "--summary-tsv-out",
                "biomarker.summary.tsv",
                "--candidate-tsv-out",
                "biomarker.candidates.tsv",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["biological_report_dir"] == "biological_report"
        assert payload["ptm_report_dir"] == "ptm_report"
        assert payload["summary"]["candidate_count"] == 3
        assert payload["summary"]["protein_candidate_count"] == 2
        assert payload["summary"]["ptm_site_candidate_count"] == 1
        assert payload["entries"][0]["candidate_id"] == "protein:protein_group_strong"
        assert payload["entries"][0]["candidate_kind"] == "protein"
        assert "assay_ready" in payload["entries"][0]["rank_reason_codes"]
        assert payload["entries"][-1]["candidate_id"] == "protein:protein_group_famous"
        assert "annotation_outpaces_evidence" in payload["entries"][-1][
            "rank_reason_codes"
        ]
        assert payload["outputs"]["summary_tsv"] == "biomarker.summary.tsv"
        assert payload["outputs"]["candidate_tsv"] == "biomarker.candidates.tsv"
        assert Path("biomarker.summary.tsv").exists()
        assert Path("biomarker.candidates.tsv").exists()
        assert "candidate_count\t3" in Path("biomarker.summary.tsv").read_text(
            encoding="utf-8"
        )
        candidate_tsv = Path("biomarker.candidates.tsv").read_text(encoding="utf-8")
        assert "protein:protein_group_strong\tprotein\tROBUST1\tP11111" in candidate_tsv
        assert "ptm_site:P33333:S21:phosphorylation\tptm_site" in candidate_tsv
        assert "annotation_outpaces_evidence" in candidate_tsv


def test_dia_dda_compare_command_emits_overlap_conflict_and_differential_outputs() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        workflow_dir = FIXTURE_ROOT / "workflow"
        shutil.copy(
            workflow_dir / "dia_dda_comparison_diann.tsv",
            "dia_dda_comparison_diann.tsv",
        )
        shutil.copy(
            workflow_dir / "dia_dda_comparison_dda_psms.tsv",
            "dia_dda_comparison_dda_psms.tsv",
        )
        shutil.copy(
            workflow_dir / "dia_dda_comparison_dia_differential.tsv",
            "dia_dda_comparison_dia_differential.tsv",
        )
        shutil.copy(
            workflow_dir / "dia_dda_comparison_dda_differential.tsv",
            "dia_dda_comparison_dda_differential.tsv",
        )

        result = runner.invoke(
            cli,
            [
                "dia-dda-compare",
                "dia_dda_comparison_diann.tsv",
                "dia_dda_comparison_dda_psms.tsv",
                "--dia-differential-tsv",
                "dia_dda_comparison_dia_differential.tsv",
                "--dda-differential-tsv",
                "dia_dda_comparison_dda_differential.tsv",
                "--summary-tsv-out",
                "dia_dda.summary.tsv",
                "--protein-overlap-tsv-out",
                "dia_dda.protein.tsv",
                "--peptide-overlap-tsv-out",
                "dia_dda.peptide.tsv",
                "--correlation-tsv-out",
                "dia_dda.correlation.tsv",
                "--exclusive-tsv-out",
                "dia_dda.exclusive.tsv",
                "--conflicts-tsv-out",
                "dia_dda.conflicts.tsv",
                "--differential-tsv-out",
                "dia_dda.differential.tsv",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["dia_source_name"] == "DIA-NN"
        assert payload["dda_source_name"] == "DDA PSM"
        assert payload["summary"]["shared_protein_count"] == 2
        assert payload["summary"]["shared_peptide_count"] == 2
        assert payload["summary"]["conflicting_peptide_count"] == 1
        assert payload["summary"]["shared_intensity_correlation_entry_count"] == 5
        assert payload["summary"]["exclusive_evidence_entry_count"] == 6
        assert payload["summary"]["conflicting_evidence_entry_count"] == 1
        assert payload["summary"]["conflicting_differential_count"] == 1
        assert payload["outputs"]["summary_tsv"] == "dia_dda.summary.tsv"
        assert payload["outputs"]["protein_overlap_tsv"] == "dia_dda.protein.tsv"
        assert payload["outputs"]["peptide_overlap_tsv"] == "dia_dda.peptide.tsv"
        assert payload["outputs"]["correlation_tsv"] == "dia_dda.correlation.tsv"
        assert payload["outputs"]["exclusive_tsv"] == "dia_dda.exclusive.tsv"
        assert payload["outputs"]["conflicts_tsv"] == "dia_dda.conflicts.tsv"
        assert payload["outputs"]["differential_tsv"] == "dia_dda.differential.tsv"
        assert Path("dia_dda.summary.tsv").exists()
        assert Path("dia_dda.protein.tsv").exists()
        assert Path("dia_dda.peptide.tsv").exists()
        assert Path("dia_dda.correlation.tsv").exists()
        assert Path("dia_dda.exclusive.tsv").exists()
        assert Path("dia_dda.conflicts.tsv").exists()
        assert Path("dia_dda.differential.tsv").exists()
        assert "DIA-NN\tDDA PSM\t4\t4\t2\t2\t2\t4\t4\t2\t1\t1\t1\t6\t1\t5\t2\t3\t4\t1\t1\t1\t1" in Path(
            "dia_dda.summary.tsv"
        ).read_text(encoding="utf-8")
        assert "P55555\tdia_only\t2\t0\t2e+06\t0" in Path(
            "dia_dda.protein.tsv"
        ).read_text(encoding="utf-8")
        assert "CONFLICTSEQ\tconflicting\t2\t2\t1.02e+06\t930000\tP77777\tP88888" in Path(
            "dia_dda.peptide.tsv"
        ).read_text(encoding="utf-8")
        assert "protein\tP22222\t2\t1.23e+06\t826000\t1" in Path(
            "dia_dda.correlation.tsv"
        ).read_text(encoding="utf-8")
        assert "dia\tpeptide\tDIAONLY\t2\t1.46e+06\tP55555" in Path(
            "dia_dda.exclusive.tsv"
        ).read_text(encoding="utf-8")
        assert "peptide\tCONFLICTSEQ\tconflicting\tprotein_assignment_mismatch" in Path(
            "dia_dda.conflicts.tsv"
        ).read_text(encoding="utf-8")
        assert "protein\tP44444\tcontrol\ttreatment\ttreatment_vs_control\tconflicting\t1.1\t-1.2\t0.02\t0.03\ttrue\ttrue\topposite\tdifferential_direction_mismatch" in Path(
            "dia_dda.differential.tsv"
        ).read_text(encoding="utf-8")


def test_biological_report_command_emits_report_directory_and_manifest() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        workflow_dir = FIXTURE_ROOT / "workflow"
        shutil.copy(
            workflow_dir / "biological_report_features.tsv",
            "biological_report_features.tsv",
        )
        shutil.copy(
            workflow_dir / "biological_report.design.tsv",
            "biological_report.design.tsv",
        )
        shutil.copy(
            workflow_dir / "biological_report_reference.fasta",
            "biological_report_reference.fasta",
        )
        interpretation_dir = FIXTURE_ROOT / "interpretation"
        shutil.copy(
            interpretation_dir / "protein_annotation_custom.tsv",
            "protein_annotation_custom.tsv",
        )
        shutil.copy(
            workflow_dir / "biological_report_context.tsv",
            "biological_report_context.tsv",
        )
        shutil.copy(
            workflow_dir / "biological_report_go.tsv",
            "biological_report_go.tsv",
        )
        shutil.copy(
            workflow_dir / "biological_report_pathways.tsv",
            "biological_report_pathways.tsv",
        )
        shutil.copy(
            workflow_dir / "biological_report_complexes.tsv",
            "biological_report_complexes.tsv",
        )
        shutil.copy(
            workflow_dir / "biological_report_context.tsv",
            "biological_report_context.tsv",
        )

        result = runner.invoke(
            cli,
            [
                "biological-report",
                "biological_report_features.tsv",
                "biological_report.design.tsv",
                "biological_report_reference.fasta",
                "--context-annotation-tsv",
                "biological_report_context.tsv",
                "--go-annotation-tsv",
                "biological_report_go.tsv",
                "--pathway-membership-tsv",
                "biological_report_pathways.tsv",
                "--complex-membership-tsv",
                "biological_report_complexes.tsv",
                "--condition-a",
                "control",
                "--condition-b",
                "treatment",
                "--output-dir",
                "biological_report",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["design_rows"] == 6
        assert payload["report"]["summary"]["protein_count"] == 5
        assert payload["report"]["summary"]["significant_protein_count"] >= 3
        assert payload["report"]["summary"]["protein_card_count"] == 5
        assert payload["report"]["summary"]["experiment_confidence_score"] > 0.0
        assert payload["report"]["summary"]["experiment_confidence_tier"] in {
            "high_confidence",
            "moderate_confidence",
            "low_confidence",
        }
        assert (
            payload["report"]["claim_validation_report"]["summary"][
                "supported_claim_count"
            ]
            >= 1
        )
        assert payload["report"]["biological_hypothesis_report"]["summary"][
            "hypothesis_count"
        ] >= 1
        assert (
            payload["report"]["experiment_confidence_report"]["summary"][
                "component_count"
            ]
            == 7
        )
        assert payload["report"]["summary"]["context_entry_count"] == 3
        assert payload["report"]["summary"]["go_enriched_term_count"] == 1
        assert payload["export_manifest"]["context_summary_included"] is True
        assert payload["export_manifest"]["go_summary_included"] is True
        report_dir = Path("biological_report")
        assert (report_dir / "biological_report_manifest.json").exists()
        assert (report_dir / "biological_report_summary.tsv").exists()
        assert (report_dir / "biological_differential.tsv").exists()
        assert (report_dir / "biological_protein_card_summary.tsv").exists()
        assert (report_dir / "biological_protein_cards.tsv").exists()
        assert (report_dir / "biological_experiment_confidence_summary.tsv").exists()
        assert (report_dir / "biological_experiment_confidence_components.tsv").exists()
        assert (report_dir / "biological_claim_validation_summary.tsv").exists()
        assert (report_dir / "biological_supported_claims.tsv").exists()
        assert (report_dir / "biological_rejected_claims.tsv").exists()
        assert (report_dir / "biological_hypothesis_summary.tsv").exists()
        assert (report_dir / "biological_hypotheses.tsv").exists()
        assert (report_dir / "biological_rejected_hypothesis_candidates.tsv").exists()
        assert (report_dir / "biological_annotations.tsv").exists()
        assert (report_dir / "biological_context_summary.tsv").exists()
        assert (report_dir / "biological_context_mappings.tsv").exists()
        assert (report_dir / "biological_context_terms.tsv").exists()
        assert (report_dir / "biological_go_terms.tsv").exists()
        assert (report_dir / "biological_pathway_entries.tsv").exists()
        assert (report_dir / "biological_complex_entries.tsv").exists()
        assert (report_dir / "biological_heatmap_matrix.tsv").exists()
        assert (report_dir / "biological_sample_pca_scores.tsv").exists()
        assert (report_dir / "biological_volcano.html").exists()
        assert (report_dir / "biological_report.html").exists()
        assert "annotation_entry_count" in (
            report_dir / "biological_report_summary.tsv"
        ).read_text(encoding="utf-8")
        assert "protein_card_count" in (
            report_dir / "biological_report_summary.tsv"
        ).read_text(encoding="utf-8")
        assert "experiment_confidence_score" in (
            report_dir / "biological_report_summary.tsv"
        ).read_text(encoding="utf-8")
        assert "overall_score" in (
            report_dir / "biological_experiment_confidence_summary.tsv"
        ).read_text(encoding="utf-8")
        assert "supported_claim_count" in (
            report_dir / "biological_claim_validation_summary.tsv"
        ).read_text(encoding="utf-8")
        assert "hypothesis_count" in (
            report_dir / "biological_hypothesis_summary.tsv"
        ).read_text(encoding="utf-8")
        assert "evidence_node_ids" in (
            report_dir / "biological_hypotheses.tsv"
        ).read_text(encoding="utf-8")
        assert "card_id" in (
            report_dir / "biological_protein_cards.tsv"
        ).read_text(encoding="utf-8")
        assert "context_entry_count" in (
            report_dir / "biological_report_summary.tsv"
        ).read_text(encoding="utf-8")
        assert "annotation_status" in (
            report_dir / "biological_annotations.tsv"
        ).read_text(encoding="utf-8")
        assert "context_kind" in (
            report_dir / "biological_context_mappings.tsv"
        ).read_text(encoding="utf-8")
        assert "gene_symbol" in (
            report_dir / "biological_annotations.tsv"
        ).read_text(encoding="utf-8")
        assert "go_term_id" in (
            report_dir / "biological_go_terms.tsv"
        ).read_text(encoding="utf-8")
        assert "pathway_id" in (
            report_dir / "biological_pathway_entries.tsv"
        ).read_text(encoding="utf-8")
        assert "complex_id" in (
            report_dir / "biological_complex_entries.tsv"
        ).read_text(encoding="utf-8")
        assert "Volcano plot:" in (
            report_dir / "biological_volcano.html"
        ).read_text(encoding="utf-8")
        assert "Protein mechanism cards" in (
            report_dir / "biological_report.html"
        ).read_text(encoding="utf-8")
        assert "Experiment confidence" in (
            report_dir / "biological_report.html"
        ).read_text(encoding="utf-8")
        assert "Validated biological claims" in (
            report_dir / "biological_report.html"
        ).read_text(encoding="utf-8")
        assert "Biological hypotheses" in (
            report_dir / "biological_report.html"
        ).read_text(encoding="utf-8")
        assert "Biological result report" in (
            report_dir / "biological_report.html"
        ).read_text(encoding="utf-8")


def test_biological_report_command_adapts_selection_policy_to_protocol_context() -> (
    None
):
    runner = CliRunner()
    with runner.isolated_filesystem():
        workflow_dir = FIXTURE_ROOT / "workflow"
        shutil.copy(
            workflow_dir / "biological_report_features.tsv",
            "biological_report_features.tsv",
        )
        shutil.copy(
            workflow_dir / "biological_report.design.tsv",
            "biological_report.design.tsv",
        )
        shutil.copy(
            workflow_dir / "biological_report_reference.fasta",
            "biological_report_reference.fasta",
        )
        Path("protocol.tsv").write_text(
            "\n".join(
                (
                    "protocol_id\tdigestion_enzyme\tacquisition_type\tlabeling_method\tenrichment_type\tfractionation_mode\tdepletion_mode\tinstrument_platform",
                    "prot-001\ttrypsin\tdda\ttmt\tnone\tnone\tnone\tOrbitrap Exploris",
                )
            )
            + "\n",
            encoding="utf-8",
        )

        result = runner.invoke(
            cli,
            [
                "biological-report",
                "biological_report_features.tsv",
                "biological_report.design.tsv",
                "biological_report_reference.fasta",
                "--protocol-context-tsv",
                "protocol.tsv",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["report"]["selection_policy"]["min_absolute_log2_fold_change"] == 0.58
        assert payload["report"]["selection_policy"]["heatmap_max_entity_count"] == 80


def test_dda_biological_report_command_emits_psm_parsimony_lfq_and_report_assets() -> (
    None
):
    runner = CliRunner()
    with runner.isolated_filesystem():
        workflow_dir = FIXTURE_ROOT / "workflow"
        shutil.copy(
            workflow_dir / "dda_biological_results.tsv",
            "dda_biological_results.tsv",
        )
        shutil.copy(
            workflow_dir / "dda_biological_mapping.json",
            "dda_biological_mapping.json",
        )
        shutil.copy(
            workflow_dir / "biological_report.design.tsv",
            "biological_report.design.tsv",
        )
        shutil.copy(
            workflow_dir / "biological_report_reference.fasta",
            "biological_report_reference.fasta",
        )
        interpretation_dir = FIXTURE_ROOT / "interpretation"
        shutil.copy(
            interpretation_dir / "protein_annotation_custom.tsv",
            "protein_annotation_custom.tsv",
        )
        shutil.copy(
            workflow_dir / "biological_report_context.tsv",
            "biological_report_context.tsv",
        )
        shutil.copy(
            workflow_dir / "biological_report_go.tsv",
            "biological_report_go.tsv",
        )
        shutil.copy(
            workflow_dir / "biological_report_pathways.tsv",
            "biological_report_pathways.tsv",
        )
        shutil.copy(
            workflow_dir / "biological_report_complexes.tsv",
            "biological_report_complexes.tsv",
        )

        result = runner.invoke(
            cli,
            [
                "dda-biological-report",
                "dda_biological_results.tsv",
                "biological_report.design.tsv",
                "biological_report_reference.fasta",
                "--adapter-kind",
                "generic",
                "--mapping-path",
                "dda_biological_mapping.json",
                "--go-annotation-tsv",
                "biological_report_go.tsv",
                "--pathway-membership-tsv",
                "biological_report_pathways.tsv",
                "--complex-membership-tsv",
                "biological_report_complexes.tsv",
                "--condition-a",
                "control",
                "--condition-b",
                "treatment",
                "--output-dir",
                "dda_biological_report",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["design_rows"] == 6
        assert payload["report"]["summary"]["accepted_psm_count"] == 30
        assert payload["report"]["summary"]["filtered_psm_count"] == 3
        assert payload["report"]["summary"]["inferred_protein_count"] == 5
        assert payload["report"]["biological_report"]["summary"][
            "significant_protein_count"
        ] >= 3
        report_dir = Path("dda_biological_report")
        assert (report_dir / "dda_biological_report_manifest.json").exists()
        assert (report_dir / "dda_biological_psms.tsv").exists()
        assert (report_dir / "dda_biological_filtered_psms.tsv").exists()
        assert (report_dir / "dda_parsimony_proteins.tsv").exists()
        assert (report_dir / "dda_protein_lfq_matrix.tsv").exists()
        assert (report_dir / "biological_report_manifest.json").exists()
        assert (report_dir / "biological_report.html").exists()
        assert "filter_reasons" in (
            report_dir / "dda_biological_filtered_psms.tsv"
        ).read_text(encoding="utf-8")
        assert "selected_protein_count" in (
            report_dir / "dda_parsimony_summary.tsv"
        ).read_text(encoding="utf-8")
        assert "entity_id" in (
            report_dir / "dda_protein_lfq_matrix.tsv"
        ).read_text(encoding="utf-8")
        assert "Biological result report" in (
            report_dir / "biological_report.html"
        ).read_text(encoding="utf-8")


def test_diann_biological_report_command_emits_matrix_qc_differential_and_report_assets() -> (
    None
):
    runner = CliRunner()
    with runner.isolated_filesystem():
        workflow_dir = FIXTURE_ROOT / "workflow"
        shutil.copy(
            workflow_dir / "diann_biological_report.tsv",
            "diann_biological_report.tsv",
        )
        shutil.copy(
            workflow_dir / "diann_biological.design.tsv",
            "diann_biological.design.tsv",
        )
        shutil.copy(
            workflow_dir / "biological_report_reference.fasta",
            "biological_report_reference.fasta",
        )
        shutil.copy(
            FIXTURE_ROOT / "interpretation" / "protein_annotation_custom.tsv",
            "protein_annotation_custom.tsv",
        )
        shutil.copy(
            workflow_dir / "biological_report_context.tsv",
            "biological_report_context.tsv",
        )
        shutil.copy(
            workflow_dir / "biological_report_go.tsv",
            "biological_report_go.tsv",
        )
        shutil.copy(
            workflow_dir / "biological_report_pathways.tsv",
            "biological_report_pathways.tsv",
        )
        shutil.copy(
            workflow_dir / "biological_report_complexes.tsv",
            "biological_report_complexes.tsv",
        )

        result = runner.invoke(
            cli,
            [
                "diann-biological-report",
                "diann_biological_report.tsv",
                "diann_biological.design.tsv",
                "biological_report_reference.fasta",
                "--annotation-tsv",
                "protein_annotation_custom.tsv",
                "--context-annotation-tsv",
                "biological_report_context.tsv",
                "--go-annotation-tsv",
                "biological_report_go.tsv",
                "--pathway-membership-tsv",
                "biological_report_pathways.tsv",
                "--complex-membership-tsv",
                "biological_report_complexes.tsv",
                "--condition-a",
                "control",
                "--condition-b",
                "treatment",
                "--output-dir",
                "diann_biological_report",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["design_rows"] == 6
        assert payload["report"]["summary"]["filtered_q_value_row_count"] == 1
        assert payload["report"]["summary"]["precursor_matrix_row_count"] == 5
        assert payload["report"]["summary"]["protein_matrix_row_count"] == 5
        assert payload["report"]["summary"]["go_enriched_term_count"] == 1
        assert payload["report"]["summary"]["flagged_run_count"] == 0
        assert payload["report"]["summary"]["rejected_evidence_count"] == 0
        assert payload["report"]["summary"]["protein_card_count"] == 5
        assert payload["report"]["summary"]["context_term_count"] == 3
        report_dir = Path("diann_biological_report")
        assert (report_dir / "diann_biological_report_manifest.json").exists()
        assert (report_dir / "diann_import_summary.tsv").exists()
        assert (report_dir / "diann_import_rejected_rows.tsv").exists()
        assert (report_dir / "diann_import_rejected_evidence.tsv").exists()
        assert (report_dir / "diann_precursor_quantity_matrix.tsv").exists()
        assert (report_dir / "diann_precursor_metadata.tsv").exists()
        assert (report_dir / "diann_peptide_quantity_matrix.tsv").exists()
        assert (report_dir / "diann_protein_quantity_matrix.tsv").exists()
        assert (report_dir / "diann_protein_rollup_evidence.tsv").exists()
        assert (report_dir / "diann_run_qc_runs.tsv").exists()
        assert (report_dir / "diann_differential_results.tsv").exists()
        assert (report_dir / "biological_report_manifest.json").exists()
        assert (report_dir / "biological_protein_cards.tsv").exists()
        assert (report_dir / "biological_context_mappings.tsv").exists()
        assert (report_dir / "biological_report.html").exists()
        assert "accepted_precursor_count" in (
            report_dir / "diann_import_summary.tsv"
        ).read_text(encoding="utf-8")
        assert "reason_code" in (
            report_dir / "diann_import_rejected_evidence.tsv"
        ).read_text(encoding="utf-8")
        assert "card_id" in (
            report_dir / "biological_protein_cards.tsv"
        ).read_text(encoding="utf-8")
        assert "context_kind" in (
            report_dir / "biological_context_mappings.tsv"
        ).read_text(encoding="utf-8")
        assert "precursor_key" in (
            report_dir / "diann_precursor_quantity_matrix.tsv"
        ).read_text(encoding="utf-8")
        assert "excluded_q_value_observation_count" in (
            report_dir / "diann_precursor_metadata.tsv"
        ).read_text(encoding="utf-8")
        assert "peptide_key" in (
            report_dir / "diann_peptide_quantity_matrix.tsv"
        ).read_text(encoding="utf-8")
        assert "rollup_stage" in (
            report_dir / "diann_protein_rollup_evidence.tsv"
        ).read_text(encoding="utf-8")
        assert "run_name\tsample_name\tprecursor_id_count" in (
            report_dir / "diann_run_qc_runs.tsv"
        ).read_text(encoding="utf-8")
        assert "weak_run_flag_count" in (
            report_dir / "diann_run_qc_summary.tsv"
        ).read_text(encoding="utf-8")
        assert "entity_id\tcondition_a\tcondition_b" in (
            report_dir / "diann_differential_results.tsv"
        ).read_text(encoding="utf-8")
        assert "Biological result report" in (
            report_dir / "biological_report.html"
        ).read_text(encoding="utf-8")


def test_diann_benchmark_command_reports_count_and_quantity_fidelity() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        workflow_dir = FIXTURE_ROOT / "workflow"
        shutil.copy(
            workflow_dir / "diann_biological_report.tsv",
            "diann_biological_report.tsv",
        )

        result = runner.invoke(
            cli,
            [
                "diann-benchmark",
                "diann_biological_report.tsv",
                "--summary-tsv-out",
                "diann.benchmark.summary.tsv",
                "--count-comparisons-tsv-out",
                "diann.benchmark.counts.tsv",
                "--protein-quantities-tsv-out",
                "diann.benchmark.proteins.tsv",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["summary"]["precursor_count_matched"] is True
        assert payload["summary"]["q_value_filtering_matched"] is True
        assert payload["summary"]["protein_quantities_matched"] is True
        assert payload["count_comparison_count"] == 5
        assert payload["protein_quantity_comparison_count"] == 30
        assert Path("diann.benchmark.summary.tsv").exists()
        assert Path("diann.benchmark.counts.tsv").exists()
        assert Path("diann.benchmark.proteins.tsv").exists()
        assert "protein_quantities_matched\ttrue" in Path(
            "diann.benchmark.summary.tsv"
        ).read_text(encoding="utf-8")
        assert "excluded_q_value_rows\t1\t1\ttrue" in Path(
            "diann.benchmark.counts.tsv"
        ).read_text(encoding="utf-8")
        assert "PG001\tT1\t1600\t1600\t0\ttrue" in Path(
            "diann.benchmark.proteins.tsv"
        ).read_text(encoding="utf-8")


def test_public_case_study_command_emits_summary_and_biological_report_assets() -> (
    None
):
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(
            cli,
            [
                "public-case-study",
                "--summary-tsv-out",
                "public_case_study.summary.tsv",
                "--report-dir",
                "public_case_study_report",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert (
            payload["case_study_id"]
            == "public_case_study:lfq_cohort_biological_case_study"
        )
        assert payload["summary"]["protein_count"] == 3
        assert payload["summary"]["significant_protein_count"] == 1
        assert payload["summary"]["go_enriched_term_count"] == 1
        report_dir = Path("public_case_study_report")
        assert Path("public_case_study.summary.tsv").exists()
        assert (report_dir / "public_case_study_manifest.json").exists()
        assert (report_dir / "public_case_study_summary.tsv").exists()
        assert (report_dir / "biological-report").is_dir()
        assert (
            report_dir / "biological-report" / "biological_report_manifest.json"
        ).exists()
        assert (report_dir / "biological-report" / "biological_report.html").exists()
        assert (
            report_dir
            / "biological-report"
            / "biological_report_section_confidence.tsv"
        ).exists()
        assert "public_case_study:lfq_cohort_biological_case_study" in Path(
            "public_case_study.summary.tsv"
        ).read_text(encoding="utf-8")
        assert "biological_report_summary.tsv" in (
            report_dir / "public_case_study_manifest.json"
        ).read_text(encoding="utf-8")
        assert "Biological result report" in (
            report_dir / "biological-report" / "biological_report.html"
        ).read_text(encoding="utf-8")
        assert "Section confidence" in (
            report_dir / "biological-report" / "biological_report.html"
        ).read_text(encoding="utf-8")


def test_maxquant_biological_report_command_emits_import_lfq_and_report_assets() -> (
    None
):
    runner = CliRunner()
    with runner.isolated_filesystem():
        workflow_dir = FIXTURE_ROOT / "workflow"
        bundle_dir = workflow_dir / "maxquant_biological"
        shutil.copy(bundle_dir / "evidence.txt", "evidence.txt")
        shutil.copy(bundle_dir / "peptides.txt", "peptides.txt")
        shutil.copy(bundle_dir / "proteinGroups.txt", "proteinGroups.txt")
        shutil.copy(bundle_dir / "design.tsv", "design.tsv")
        shutil.copy(bundle_dir / "maxquant_settings.txt", "maxquant_settings.txt")
        shutil.copy(
            workflow_dir / "biological_report_reference.fasta",
            "biological_report_reference.fasta",
        )
        shutil.copy(
            FIXTURE_ROOT / "interpretation" / "protein_annotation_custom.tsv",
            "protein_annotation_custom.tsv",
        )
        shutil.copy(
            workflow_dir / "biological_report_context.tsv",
            "biological_report_context.tsv",
        )
        shutil.copy(
            workflow_dir / "biological_report_go.tsv",
            "biological_report_go.tsv",
        )
        shutil.copy(
            workflow_dir / "biological_report_pathways.tsv",
            "biological_report_pathways.tsv",
        )
        shutil.copy(
            workflow_dir / "biological_report_complexes.tsv",
            "biological_report_complexes.tsv",
        )

        result = runner.invoke(
            cli,
            [
                "maxquant-biological-report",
                "evidence.txt",
                "peptides.txt",
                "proteinGroups.txt",
                "design.tsv",
                "biological_report_reference.fasta",
                "--config-path",
                "maxquant_settings.txt",
                "--annotation-tsv",
                "protein_annotation_custom.tsv",
                "--context-annotation-tsv",
                "biological_report_context.tsv",
                "--go-annotation-tsv",
                "biological_report_go.tsv",
                "--pathway-membership-tsv",
                "biological_report_pathways.tsv",
                "--complex-membership-tsv",
                "biological_report_complexes.tsv",
                "--condition-a",
                "control",
                "--condition-b",
                "treatment",
                "--output-dir",
                "maxquant_biological_report",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["design_rows"] == 6
        assert payload["report"]["summary"]["accepted_protein_group_count"] == 5
        assert payload["report"]["summary"]["filtered_protein_group_count"] == 3
        assert payload["report"]["summary"]["enrichment_foreground_protein_count"] == 3
        assert payload["report"]["summary"]["quantified_protein_count"] == 5
        assert payload["report"]["summary"]["protein_card_count"] == 5
        assert payload["report"]["summary"]["context_term_count"] == 3
        assert payload["report"]["summary"]["go_enriched_term_count"] == 1
        report_dir = Path("maxquant_biological_report")
        assert (report_dir / "maxquant_biological_report_manifest.json").exists()
        assert (report_dir / "maxquant_import_summary.tsv").exists()
        assert (report_dir / "maxquant_accepted_protein_groups.tsv").exists()
        assert (report_dir / "maxquant_filtered_protein_groups.tsv").exists()
        assert (report_dir / "maxquant_biological_foreground.tsv").exists()
        assert (report_dir / "maxquant_lfq_matrix.tsv").exists()
        assert (report_dir / "biological_report_manifest.json").exists()
        assert (report_dir / "biological_protein_cards.tsv").exists()
        assert (report_dir / "biological_context_mappings.tsv").exists()
        assert (report_dir / "biological_report.html").exists()
        assert "accepted_evidence_count" in (
            report_dir / "maxquant_import_summary.tsv"
        ).read_text(encoding="utf-8")
        assert "filter_reasons" in (
            report_dir / "maxquant_filtered_protein_groups.tsv"
        ).read_text(encoding="utf-8")
        assert "card_id" in (
            report_dir / "maxquant_biological_foreground.tsv"
        ).read_text(encoding="utf-8")
        assert "\ttrue\t" not in (
            report_dir / "maxquant_biological_foreground.tsv"
        ).read_text(encoding="utf-8")
        assert "entity_id\tprotein_refs\tmember_peptides" in (
            report_dir / "maxquant_lfq_matrix.tsv"
        ).read_text(encoding="utf-8")
        assert "card_id" in (
            report_dir / "biological_protein_cards.tsv"
        ).read_text(encoding="utf-8")
        assert "context_kind" in (
            report_dir / "biological_context_mappings.tsv"
        ).read_text(encoding="utf-8")


def test_proteomics_run_command_emits_diann_result_package() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        workflow_dir = FIXTURE_ROOT / "workflow"
        shutil.copy(
            workflow_dir / "diann_biological_report.tsv",
            "diann_biological_report.tsv",
        )
        shutil.copy(
            workflow_dir / "diann_biological.design.tsv",
            "diann_biological.design.tsv",
        )
        shutil.copy(
            workflow_dir / "biological_report_reference.fasta",
            "biological_report_reference.fasta",
        )
        shutil.copy(workflow_dir / "biological_report_go.tsv", "biological_report_go.tsv")
        shutil.copy(
            workflow_dir / "biological_report_pathways.tsv",
            "biological_report_pathways.tsv",
        )
        shutil.copy(
            workflow_dir / "biological_report_complexes.tsv",
            "biological_report_complexes.tsv",
        )

        result = runner.invoke(
            cli,
            [
                "run",
                "--engine",
                "diann",
                "--report",
                "diann_biological_report.tsv",
                "--metadata",
                "diann_biological.design.tsv",
                "--proteins-fasta",
                "biological_report_reference.fasta",
                "--contrast",
                "control-treatment",
                "--go-annotation-tsv",
                "biological_report_go.tsv",
                "--pathway-membership-tsv",
                "biological_report_pathways.tsv",
                "--complex-membership-tsv",
                "biological_report_complexes.tsv",
                "--out",
                "proteomics_run",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["metadata_rows"] == 6
        assert payload["run"]["engine"] == "diann"
        assert payload["run"]["summary"]["protein_count"] == 5
        report_dir = Path("proteomics_run")
        assert (report_dir / "proteomics_run_manifest.json").exists()
        assert (report_dir / "proteomics_run_summary.tsv").exists()
        assert (report_dir / "proteomics_qc_summary.tsv").exists()
        assert (report_dir / "proteomics_normalized_matrix.tsv").exists()
        assert (report_dir / "proteomics_differential.tsv").exists()
        assert (report_dir / "proteomics_enrichment.tsv").exists()
        assert (report_dir / "proteomics_report.html").exists()
        assert "engine\tdiann" in (report_dir / "proteomics_run_summary.tsv").read_text(
            encoding="utf-8"
        )


def test_proteomics_run_command_accepts_explicit_case_control_contrast() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        workflow_dir = FIXTURE_ROOT / "workflow"
        shutil.copy(
            workflow_dir / "diann_biological_report.tsv",
            "diann_biological_report.tsv",
        )
        shutil.copy(
            workflow_dir / "diann_biological.design.tsv",
            "diann_biological.design.tsv",
        )
        shutil.copy(
            workflow_dir / "biological_report_reference.fasta",
            "biological_report_reference.fasta",
        )

        result = runner.invoke(
            cli,
            [
                "run",
                "--engine",
                "diann",
                "--report",
                "diann_biological_report.tsv",
                "--metadata",
                "diann_biological.design.tsv",
                "--proteins-fasta",
                "biological_report_reference.fasta",
                "--contrast",
                "case-control:treatment-control",
                "--out",
                "proteomics_run",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["run"]["summary"]["condition_a"] == "treatment"
        assert payload["run"]["summary"]["condition_b"] == "control"


def test_proteomics_run_command_emits_maxquant_result_package() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        workflow_dir = FIXTURE_ROOT / "workflow"
        bundle_dir = workflow_dir / "maxquant_biological"
        shutil.copy(bundle_dir / "evidence.txt", "evidence.txt")
        shutil.copy(bundle_dir / "peptides.txt", "peptides.txt")
        shutil.copy(bundle_dir / "proteinGroups.txt", "proteinGroups.txt")
        shutil.copy(bundle_dir / "design.tsv", "design.tsv")
        shutil.copy(bundle_dir / "maxquant_settings.txt", "maxquant_settings.txt")
        shutil.copy(
            workflow_dir / "biological_report_reference.fasta",
            "biological_report_reference.fasta",
        )
        shutil.copy(workflow_dir / "biological_report_go.tsv", "biological_report_go.tsv")
        shutil.copy(
            workflow_dir / "biological_report_pathways.tsv",
            "biological_report_pathways.tsv",
        )
        shutil.copy(
            workflow_dir / "biological_report_complexes.tsv",
            "biological_report_complexes.tsv",
        )

        result = runner.invoke(
            cli,
            [
                "run",
                "--engine",
                "maxquant",
                "--report",
                "evidence.txt",
                "--peptides",
                "peptides.txt",
                "--protein-groups",
                "proteinGroups.txt",
                "--metadata",
                "design.tsv",
                "--proteins-fasta",
                "biological_report_reference.fasta",
                "--contrast",
                "control-treatment",
                "--config-path",
                "maxquant_settings.txt",
                "--go-annotation-tsv",
                "biological_report_go.tsv",
                "--pathway-membership-tsv",
                "biological_report_pathways.tsv",
                "--complex-membership-tsv",
                "biological_report_complexes.tsv",
                "--out",
                "proteomics_run",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["metadata_rows"] == 6
        assert payload["run"]["engine"] == "maxquant"
        assert payload["run"]["summary"]["protein_count"] == 5
        report_dir = Path("proteomics_run")
        assert (report_dir / "proteomics_run_manifest.json").exists()
        assert (report_dir / "proteomics_run_summary.tsv").exists()
        assert (report_dir / "proteomics_normalized_matrix.tsv").exists()
        assert (report_dir / "proteomics_differential.tsv").exists()
        assert (report_dir / "proteomics_enrichment.tsv").exists()
        assert (report_dir / "proteomics_report.html").exists()
        assert "P04637" in (report_dir / "proteomics_normalized_matrix.tsv").read_text(
            encoding="utf-8"
        )


def test_proteomics_run_command_emits_fragpipe_result_package() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        workflow_dir = FIXTURE_ROOT / "workflow"
        shutil.copy(
            workflow_dir / "fragpipe_biological_psms.tsv",
            "fragpipe_biological_psms.tsv",
        )
        shutil.copy(
            workflow_dir / "fragpipe_biological_proteins.tsv",
            "fragpipe_biological_proteins.tsv",
        )
        shutil.copy(
            workflow_dir / "biological_report.design.tsv",
            "biological_report.design.tsv",
        )
        shutil.copy(
            workflow_dir / "biological_report_reference.fasta",
            "biological_report_reference.fasta",
        )
        shutil.copy(workflow_dir / "biological_report_go.tsv", "biological_report_go.tsv")
        shutil.copy(
            workflow_dir / "biological_report_pathways.tsv",
            "biological_report_pathways.tsv",
        )
        shutil.copy(
            workflow_dir / "biological_report_complexes.tsv",
            "biological_report_complexes.tsv",
        )

        result = runner.invoke(
            cli,
            [
                "run",
                "--engine",
                "fragpipe",
                "--report",
                "fragpipe_biological_psms.tsv",
                "--source-protein-tsv",
                "fragpipe_biological_proteins.tsv",
                "--metadata",
                "biological_report.design.tsv",
                "--proteins-fasta",
                "biological_report_reference.fasta",
                "--contrast",
                "control-treatment",
                "--go-annotation-tsv",
                "biological_report_go.tsv",
                "--pathway-membership-tsv",
                "biological_report_pathways.tsv",
                "--complex-membership-tsv",
                "biological_report_complexes.tsv",
                "--out",
                "proteomics_run",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["metadata_rows"] == 6
        assert payload["run"]["engine"] == "fragpipe"
        assert payload["run"]["fragpipe_workflow"]["summary"]["accepted_psm_count"] == 30
        assert (
            payload["run"]["fragpipe_workflow"]["summary"][
                "protein_group_discrepancy_count"
            ]
            == 2
        )
        report_dir = Path("proteomics_run")
        assert (report_dir / "proteomics_run_manifest.json").exists()
        assert (report_dir / "proteomics_qc_summary.tsv").exists()
        assert (report_dir / "proteomics_normalized_matrix.tsv").exists()
        assert (report_dir / "proteomics_differential.tsv").exists()
        assert (report_dir / "proteomics_enrichment.tsv").exists()
        assert (report_dir / "proteomics_report.html").exists()
        assert (report_dir / "dda_source_protein_discrepancies.tsv").exists()
        assert "go\tgene_ontology" in (
            report_dir / "proteomics_enrichment.tsv"
        ).read_text(encoding="utf-8")
        assert "workflow_only" in (
            report_dir / "dda_source_protein_discrepancies.tsv"
        ).read_text(encoding="utf-8")


def test_proteomics_run_command_rejects_incomplete_maxquant_inputs() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        workflow_dir = FIXTURE_ROOT / "workflow"
        bundle_dir = workflow_dir / "maxquant_biological"
        shutil.copy(bundle_dir / "evidence.txt", "evidence.txt")
        shutil.copy(bundle_dir / "design.tsv", "design.tsv")
        shutil.copy(
            workflow_dir / "biological_report_reference.fasta",
            "biological_report_reference.fasta",
        )

        result = runner.invoke(
            cli,
            [
                "run",
                "--engine",
                "maxquant",
                "--report",
                "evidence.txt",
                "--metadata",
                "design.tsv",
                "--proteins-fasta",
                "biological_report_reference.fasta",
                "--contrast",
                "control-treatment",
                "--out",
                "proteomics_run",
            ],
        )

        assert result.exit_code != 0
        assert "MaxQuant runs require --peptides" in result.output


def test_maxquant_benchmark_command_reports_import_lfq_and_differential_fidelity() -> (
    None
):
    runner = CliRunner()
    with runner.isolated_filesystem():
        bundle_dir = FIXTURE_ROOT / "workflow" / "maxquant_biological"
        shutil.copy(bundle_dir / "evidence.txt", "evidence.txt")
        shutil.copy(bundle_dir / "peptides.txt", "peptides.txt")
        shutil.copy(bundle_dir / "proteinGroups.txt", "proteinGroups.txt")
        shutil.copy(bundle_dir / "design.tsv", "design.tsv")
        shutil.copy(bundle_dir / "maxquant_settings.txt", "maxquant_settings.txt")

        result = runner.invoke(
            cli,
            [
                "maxquant-benchmark",
                "evidence.txt",
                "--peptides-txt",
                "peptides.txt",
                "--protein-groups-txt",
                "proteinGroups.txt",
                "--config",
                "maxquant_settings.txt",
                "--design-tsv",
                "design.tsv",
                "--condition-a",
                "control",
                "--condition-b",
                "treatment",
                "--summary-tsv-out",
                "maxquant.benchmark.summary.tsv",
                "--protein-identity-tsv-out",
                "maxquant.benchmark.proteins.tsv",
                "--filtering-tsv-out",
                "maxquant.benchmark.filtering.tsv",
                "--lfq-tsv-out",
                "maxquant.benchmark.lfq.tsv",
                "--differential-tsv-out",
                "maxquant.benchmark.differential.tsv",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["summary"]["protein_identity_matched"] is True
        assert payload["summary"]["lfq_values_matched"] is True
        assert payload["summary"]["differential_comparison_applied"] is True
        assert payload["summary"]["differential_matched"] is True
        assert payload["filtering_comparison_count"] == 8
        assert payload["lfq_comparison_count"] == 30
        assert payload["differential_comparison_count"] == 5
        assert Path("maxquant.benchmark.summary.tsv").exists()
        assert Path("maxquant.benchmark.proteins.tsv").exists()
        assert Path("maxquant.benchmark.filtering.tsv").exists()
        assert Path("maxquant.benchmark.lfq.tsv").exists()
        assert Path("maxquant.benchmark.differential.tsv").exists()
        assert "lfq_values_matched\ttrue" in Path(
            "maxquant.benchmark.summary.tsv"
        ).read_text(encoding="utf-8")
        assert "CON__KRT1\tfiltered\tfiltered" in Path(
            "maxquant.benchmark.filtering.tsv"
        ).read_text(encoding="utf-8")
        assert "P04637\tT1\t1600\t1600\t0\ttrue" in Path(
            "maxquant.benchmark.lfq.tsv"
        ).read_text(encoding="utf-8")


def test_dia_differential_command_emits_matrices_results_and_plot_ledgers() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        diann_dir = FIXTURE_ROOT / "search_result_bundles" / "diann"
        format_dir = FIXTURE_ROOT / "formats"
        shutil.copy(
            diann_dir / "diann_differential_report.tsv",
            "diann_differential_report.tsv",
        )
        shutil.copy(
            format_dir / "diann_differential.design.tsv",
            "diann_differential.design.tsv",
        )

        result = runner.invoke(
            cli,
            [
                "dia-differential",
                "diann_differential_report.tsv",
                "diann_differential.design.tsv",
                "--source-kind",
                "diann",
                "--matrix-tsv-out",
                "dia.raw.tsv",
                "--normalized-matrix-tsv-out",
                "dia.normalized.tsv",
                "--differential-tsv-out",
                "dia.differential.tsv",
                "--qc-summary-tsv-out",
                "dia.qc.tsv",
                "--design-matrix-tsv-out",
                "dia.design.tsv",
                "--design-coefficients-tsv-out",
                "dia.coefficients.tsv",
                "--volcano-tsv-out",
                "dia.volcano.tsv",
                "--volcano-json-out",
                "dia.volcano.json",
                "--volcano-svg-out",
                "dia.volcano.svg",
                "--volcano-html-out",
                "dia.volcano.html",
                "--volcano-top-label-count",
                "1",
                "--sample-balance-tsv-out",
                "dia.balance.tsv",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["source_kind"] == "diann"
        assert payload["source_name"] == "DIA-NN"
        assert payload["matrix_summary"]["entity_count"] == 3
        assert payload["normalization_comparison"]["method"] == "median"
        assert payload["qc_summary"]["contrast_count"] == 1
        assert payload["qc_summary"]["significant_entry_count"] == 2
        assert payload["differential_abundance"]["condition_a"] == "control"
        assert payload["differential_abundance"]["condition_b"] == "treatment"
        assert payload["volcano_plot"]["significant_point_count"] == 2
        assert payload["volcano_review"]["labeled_point_count"] == 1
        assert payload["outputs"]["matrix_tsv"] == "dia.raw.tsv"
        assert payload["outputs"]["normalized_matrix_tsv"] == "dia.normalized.tsv"
        assert payload["outputs"]["differential_tsv"] == "dia.differential.tsv"
        assert payload["outputs"]["qc_summary_tsv"] == "dia.qc.tsv"
        assert payload["outputs"]["design_matrix_tsv"] == "dia.design.tsv"
        assert payload["outputs"]["design_coefficients_tsv"] == "dia.coefficients.tsv"
        assert payload["outputs"]["volcano_tsv"] == "dia.volcano.tsv"
        assert payload["outputs"]["volcano_json"] == "dia.volcano.json"
        assert payload["outputs"]["volcano_svg"] == "dia.volcano.svg"
        assert payload["outputs"]["volcano_html"] == "dia.volcano.html"
        assert payload["outputs"]["sample_balance_tsv"] == "dia.balance.tsv"
        assert Path("dia.raw.tsv").exists()
        assert Path("dia.normalized.tsv").exists()
        assert Path("dia.differential.tsv").exists()
        assert Path("dia.qc.tsv").exists()
        assert Path("dia.design.tsv").exists()
        assert Path("dia.coefficients.tsv").exists()
        assert Path("dia.volcano.tsv").exists()
        assert Path("dia.volcano.json").exists()
        assert Path("dia.volcano.svg").exists()
        assert Path("dia.volcano.html").exists()
        assert Path("dia.balance.tsv").exists()
        assert "PG001\tP11111\tPESTIDE\t100000\t110000\t400000\t420000" in Path(
            "dia.raw.tsv"
        ).read_text(encoding="utf-8")
        assert "PG001\tcontrol\ttreatment\t\t2\t2" in Path(
            "dia.differential.tsv"
        ).read_text(encoding="utf-8")
        assert "sample_id\tcondition\tbatch\tpair_id\tintercept" in Path(
            "dia.design.tsv"
        ).read_text(encoding="utf-8")
        assert "PG001\tcondition[treatment]" in Path(
            "dia.coefficients.tsv"
        ).read_text(encoding="utf-8")
        assert "contrast_count\t1" in Path("dia.qc.tsv").read_text(encoding="utf-8")
        assert "raw_p_value" in Path("dia.volcano.tsv").read_text(encoding="utf-8")
        assert "PG001\tP11111\t2.00208\t0.00729495\t0.0136062\t1.86626\ttrue" in Path(
            "dia.volcano.tsv"
        ).read_text(encoding="utf-8")
        assert '"source_kind": "dia"' in Path("dia.volcano.json").read_text(
            encoding="utf-8"
        )
        assert "<svg" in Path("dia.volcano.svg").read_text(encoding="utf-8")
        assert "Volcano plot: control vs treatment" in Path(
            "dia.volcano.html"
        ).read_text(encoding="utf-8")
        assert "C1\tbefore\t600000\t200000\t100000" in Path(
            "dia.balance.tsv"
        ).read_text(encoding="utf-8")


def test_spectronaut_import_command_reports_samples_quantities_and_modifications() -> (
    None
):
    runner = CliRunner()
    with runner.isolated_filesystem():
        fixture_dir = FIXTURE_ROOT / "search_result_bundles" / "spectronaut"
        shutil.copy(fixture_dir / "spectronaut_report.tsv", "spectronaut_report.tsv")
        shutil.copy(
            fixture_dir / "spectronaut_settings.txt",
            "spectronaut_settings.txt",
        )

        result = runner.invoke(
            cli,
            [
                "spectronaut-import",
                "spectronaut_report.tsv",
                "--config",
                "spectronaut_settings.txt",
                "--summary-tsv-out",
                "spectronaut.summary.tsv",
                "--precursor-tsv-out",
                "spectronaut.precursors.tsv",
                "--precursor-quantity-tsv-out",
                "spectronaut.precursor_quantities.tsv",
                "--protein-group-tsv-out",
                "spectronaut.protein_groups.tsv",
                "--protein-group-quantity-tsv-out",
                "spectronaut.protein_group_quantities.tsv",
                "--rejected-tsv-out",
                "spectronaut.rejected.tsv",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["summary"]["accepted_precursor_count"] == 4
        assert payload["summary"]["protein_group_row_count"] == 4
        assert payload["summary"]["modified_precursor_count"] == 3
        assert payload["summary"]["sample_names"] == ["sample_A", "sample_B"]
        assert payload["summary"]["run_names"] == ["raw_A", "raw_B"]
        assert payload["summary"]["precursor_quantity_count"] == 4
        assert payload["summary"]["protein_group_quantity_count"] == 4
        assert payload["summary"]["precursor_quantity_row_count"] == 4
        assert payload["summary"]["protein_group_quantity_row_count"] == 4
        assert payload["parameter_report"]["enzyme"] == "trypsin"
        assert (
            payload["normalization"]["adapter"]["display_name"]
            == "Spectronaut review report"
        )
        assert payload["precursor_evidence_rows"] == payload["precursor_rows"]
        assert payload["precursor_rows"][0]["modified_peptide"] == "PES[Phospho]TIDE"
        assert payload["precursor_quantity_rows"][0]["precursor_id"] == "sn_rawA_pestide_2"
        assert payload["protein_group_quantity_rows"][0]["protein_group_id"] == "PG001"
        assert payload["rejected_evidence_rows"] == []
        assert Path("spectronaut.summary.tsv").exists()
        assert Path("spectronaut.precursors.tsv").exists()
        assert Path("spectronaut.precursor_quantities.tsv").exists()
        assert Path("spectronaut.protein_groups.tsv").exists()
        assert Path("spectronaut.protein_group_quantities.tsv").exists()
        assert Path("spectronaut.rejected.tsv").exists()


def test_psm_map_command_reports_unmapped_columns_and_normalized_rows() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        fixture_dir = FIXTURE_ROOT / "search_adapters"
        shutil.copy(
            fixture_dir / "generic_mapper_results.tsv",
            "generic_mapper_results.tsv",
        )
        shutil.copy(
            fixture_dir / "generic_mapper_mapping.yaml",
            "generic_mapper_mapping.yaml",
        )

        result = runner.invoke(
            cli,
            [
                "psm-map",
                "generic_mapper_results.tsv",
                "--mapping",
                "generic_mapper_mapping.yaml",
                "--normalized-tsv-out",
                "mapped.tsv",
                "--rejected-tsv-out",
                "rejected.tsv",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["column_mapping"]["score_orientation"] == "higher_better"
        assert payload["normalization"]["adapter"]["score_orientation"] == "higher_better"
        assert payload["summary"]["accepted_rows"] == 2
        assert payload["summary"]["mapped_run_count"] == 2
        assert payload["summary"]["unmapped_source_columns"] == [
            "analyst_note",
            "instrument",
        ]
        assert payload["mapped_rows"][0]["run_id"] == "run_A"
        assert payload["mapped_rows"][0]["peptide_sequence"] == "PESTIDE"
        assert payload["mapped_rows"][0]["modified_peptide"] == "PES[Phospho]TIDE"
        assert payload["mapped_rows"][1]["target_decoy_label"] == "decoy"
        assert payload["mapped_rows"][1]["target_decoy_contaminant_class"] == "mixed"
        assert payload["mapped_rows"][1]["contaminant_flag"] is True
        assert payload["rejected_evidence_rows"] == []
        assert Path("mapped.tsv").exists()
        assert Path("rejected.tsv").exists()
        assert Path("rejected.tsv").read_text(encoding="utf-8").startswith(
            "source_file\trow_number\tentity_type\tentity_id\treason_code\tdetail\n"
        )


def test_psm_map_command_blocks_missing_required_mapping() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        fixture_dir = FIXTURE_ROOT / "search_adapters"
        shutil.copy(
            fixture_dir / "generic_mapper_results.tsv",
            "generic_mapper_results.tsv",
        )
        Path("generic_mapper_mapping.yaml").write_text(
            "\n".join(
                (
                    "run_id: run_name",
                    "spectrum_id: scan_ref",
                    "peptide: sequence_text",
                    "charge: z",
                    "score: state_score",
                    "protein_refs: accessions",
                    "decoy_label: decoy_state",
                )
            )
            + "\n",
            encoding="utf-8",
        )

        result = runner.invoke(
            cli,
            [
                "psm-map",
                "generic_mapper_results.tsv",
                "--mapping",
                "generic_mapper_mapping.yaml",
            ],
        )

        assert result.exit_code != 0
        assert "score_orientation" in result.output


def test_openms_import_command_reports_idxml_and_feature_bundle() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        fixture_dir = FIXTURE_ROOT / "search_result_bundles" / "openms"
        shutil.copy(fixture_dir / "openms.idxml", "openms.idxml")
        shutil.copy(fixture_dir / "openms_features.tsv", "openms_features.tsv")

        result = runner.invoke(
            cli,
            [
                "openms-import",
                "openms.idxml",
                "--feature-table",
                "openms_features.tsv",
                "--summary-tsv-out",
                "openms.summary.tsv",
                "--psm-tsv-out",
                "openms.psm.tsv",
                "--protein-tsv-out",
                "openms.protein.tsv",
                "--feature-tsv-out",
                "openms.feature.tsv",
                "--rejected-feature-tsv-out",
                "openms.rejected_features.tsv",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["summary"]["accepted_psm_count"] == 3
        assert payload["summary"]["accepted_feature_count"] == 4
        assert payload["summary"]["rejected_feature_count"] == 1
        assert payload["summary"]["feature_sample_count"] == 2
        assert payload["feature_parse_summary"]["rejected_rows"] == 1
        assert payload["psm_rows"][0]["spectrum_id"].endswith("scan=1002")
        assert payload["protein_rows"][0]["target_decoy_label"] == "decoy"
        assert payload["feature_rows"][2]["peptide_sequence"] == "M[Oxidation]PEPTIDE"
        assert payload["rejected_feature_rows"][0]["row_number"] == 6
        assert payload["rejected_feature_rows"][0]["issues"][0]["code"] == "invalid_intensity"
        assert payload["rejected_evidence_rows"][0]["reason_code"] == "invalid_intensity"
        assert Path("openms.summary.tsv").exists()
        assert Path("openms.psm.tsv").exists()
        assert Path("openms.protein.tsv").exists()
        assert Path("openms.feature.tsv").exists()
        assert Path("openms.rejected_features.tsv").exists()
        assert Path("openms.rejected_features.tsv").read_text(
            encoding="utf-8"
        ).startswith("source_file\trow_number\tentity_type\tentity_id\treason_code\tdetail\n")


def test_fdr_command_writes_audit_and_calibration_outputs() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        fixture_dir = FIXTURE_ROOT / "psm"
        shutil.copy(fixture_dir / "fdr_results.tsv", "fdr_results.tsv")

        result = runner.invoke(
            cli,
            [
                "fdr",
                "fdr_results.tsv",
                "--threshold",
                "0.5",
                "--score-orientation",
                "higher_better",
                "--audit-out",
                "audit.json",
                "--calibration-out",
                "calibration.json",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["accepted_psms"] == 3
        assert payload["audit_trail"]["reproducibility_hash"]
        assert Path("audit.json").exists()
        assert Path("calibration.json").exists()


def test_infer_proteins_command_emits_grouping_and_coverage_artifacts() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        psm_fixture_dir = FIXTURE_ROOT / "psm"
        fasta_fixture_dir = FIXTURE_ROOT / "fasta"
        shutil.copy(
            psm_fixture_dir / "protein_inference_results.tsv",
            "protein_inference_results.tsv",
        )
        shutil.copy(
            fasta_fixture_dir / "protein_inference.fasta", "protein_inference.fasta"
        )

        result = runner.invoke(
            cli,
            [
                "infer-proteins",
                "protein_inference_results.tsv",
                "--threshold",
                "0.05",
                "--fasta",
                "protein_inference.fasta",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["accepted_psms"] == 4
        assert len(payload["protein_groups"]) >= 3
        assert {entry["protein_ref"] for entry in payload["parsimony_proteins"]} == {
            "P11111",
            "P22222",
            "P33333",
        }
        assert any(
            entry["canonical_peptide"] == "SHAREDK"
            for entry in payload["razor_assignments"]
        )
        assert any(
            entry["protein_ref"] == "P11111" for entry in payload["protein_coverage"]
        )


def test_quantify_command_emits_quant_matrix_and_differential_outputs() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        fixture_dir = FIXTURE_ROOT / "quant"
        shutil.copy(fixture_dir / "ms1_features.tsv", "ms1_features.tsv")
        shutil.copy(fixture_dir / "quant.design.tsv", "quant.design.tsv")

        result = runner.invoke(
            cli,
            [
                "quantify",
                "ms1_features.tsv",
                "--design",
                "quant.design.tsv",
                "--entity-level",
                "protein",
                "--aggregation",
                "top_n",
                "--top-n",
                "2",
                "--normalization",
                "median",
                "--imputation",
                "low_intensity",
                "--condition-a",
                "control",
                "--condition-b",
                "treatment",
                "--differential-tsv-out",
                "quantify.differential.tsv",
                "--batch-effect-summary-tsv-out",
                "quantify.batch_effect_summary.tsv",
                "--batch-effect-batches-tsv-out",
                "quantify.batch_effect_batches.tsv",
                "--batch-effect-components-tsv-out",
                "quantify.batch_effect_components.tsv",
                "--design-matrix-tsv-out",
                "quantify.design.tsv",
                "--design-coefficients-tsv-out",
                "quantify.design_coefficients.tsv",
                "--design-contrasts-tsv-out",
                "quantify.design_contrasts.tsv",
                "--limma-assay-tsv-out",
                "quantify.limma_assay.tsv",
                "--limma-samples-tsv-out",
                "quantify.limma_samples.tsv",
                "--limma-design-tsv-out",
                "quantify.limma_design.tsv",
                "--limma-contrasts-tsv-out",
                "quantify.limma_contrasts.tsv",
                "--msstats-input-tsv-out",
                "quantify.msstats.tsv",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["accepted_features"] == 32
        assert payload["rejected_features"] == 0
        assert payload["table"]["entity_level"] == "protein"
        assert payload["table"]["normalization_method"] == "median"
        assert payload["missing_summary"]["entries"][0]["zero_count"] == 1
        assert payload["missingness_entity_summary"]["entries"]
        assert payload["missingness_condition_summary"]["entries"]
        assert payload["missingness_intensity_dependence"]["plot_points"]
        assert payload["missingness_mechanism_report"]["entries"]
        assert (
            payload["missingness_mechanism_report"]["summary_counts"][
                "missing_completely_at_random"
            ]
            >= 1
        )
        assert payload["normalization_comparison"]["method"] == "median"
        assert payload["normalization_comparison"]["after"]
        assert payload["normalization_strategy"]["recommended_method"] is not None
        assert payload["imputation_report"]["method"] == "low_intensity"
        assert payload["imputation_report"]["imputed_value_count"] > 0
        assert payload["imputation_sensitivity"]["entries"]
        assert tuple(
            entry["method"] for entry in payload["imputation_sensitivity"]["entries"]
        ) == ("none", "low_intensity", "knn")
        assert payload["imputation_sensitivity"]["overlap_entries"]
        assert payload["imputation_sensitivity"]["changed_significance_entries"]
        assert payload["imputation_sensitivity"]["imputation_dependent_hits"]
        assert payload["batch_effect"]["disposition"] == "ADVISORY"
        assert payload["batch_effect"]["batch_variance_proxy"] >= 0.0
        assert payload["batch_effect"]["principal_components"]
        assert payload["batch_effect"]["batch_correction_blocked"] is False
        assert payload["replicate_correlations"]["entries"]
        assert payload["replicate_qc"]["replicate_cv_report"]["entries"]
        assert payload["replicate_qc"]["sample_pca_report"]["entries"]
        assert payload["replicate_qc"]["condition_clustering_report"] is not None
        assert payload["replicate_cv"]["entries"]
        assert payload["sample_pca"]["entries"]
        assert payload["condition_clustering"]["condition_count"] == 2
        assert payload["design_matrix"]["columns"]
        assert payload["design_model_fit"]["coefficient_entries"]
        assert payload["limma_compatible_package"]["sample_annotations"]
        assert payload["msstats_compatible_input_report"]["rows"]
        assert payload["differential_abundance"]["condition_a"] == "control"
        assert (
            payload["differential_abundance"]["assumption_report"]["test_type"]
            == "linear_model_contrast"
        )
        assert (
            payload["differential_abundance"]["assumption_report"][
                "multiple_testing_scope"
            ]
            == "benjamini_hochberg_report_wide_entities"
        )
        assert payload["differential_abundance"]["contrast_name"] == "control_vs_treatment"
        assert all(
            "imputation_significance_change_reason" in entry
            and "imputation_dependent_hit" in entry
            for entry in payload["differential_abundance"]["entries"]
        )
        assert payload["outputs"]["differential_tsv"] == "quantify.differential.tsv"
        assert (
            payload["outputs"]["batch_effect_summary_tsv"]
            == "quantify.batch_effect_summary.tsv"
        )
        assert (
            payload["outputs"]["batch_effect_batches_tsv"]
            == "quantify.batch_effect_batches.tsv"
        )
        assert (
            payload["outputs"]["batch_effect_components_tsv"]
            == "quantify.batch_effect_components.tsv"
        )
        assert payload["outputs"]["design_matrix_tsv"] == "quantify.design.tsv"
        assert (
            payload["outputs"]["design_coefficients_tsv"]
            == "quantify.design_coefficients.tsv"
        )
        assert (
            payload["outputs"]["design_contrasts_tsv"]
            == "quantify.design_contrasts.tsv"
        )
        assert payload["outputs"]["limma_assay_tsv"] == "quantify.limma_assay.tsv"
        assert payload["outputs"]["limma_samples_tsv"] == "quantify.limma_samples.tsv"
        assert payload["outputs"]["limma_design_tsv"] == "quantify.limma_design.tsv"
        assert (
            payload["outputs"]["limma_contrasts_tsv"]
            == "quantify.limma_contrasts.tsv"
        )
        assert payload["outputs"]["msstats_input_tsv"] == "quantify.msstats.tsv"
        assert Path("quantify.differential.tsv").exists()
        assert Path("quantify.batch_effect_summary.tsv").exists()
        assert Path("quantify.batch_effect_batches.tsv").exists()
        assert Path("quantify.batch_effect_components.tsv").exists()
        assert Path("quantify.design.tsv").exists()
        assert Path("quantify.design_coefficients.tsv").exists()
        assert Path("quantify.design_contrasts.tsv").exists()
        assert Path("quantify.limma_assay.tsv").exists()
        assert Path("quantify.limma_samples.tsv").exists()
        assert Path("quantify.limma_design.tsv").exists()
        assert Path("quantify.limma_contrasts.tsv").exists()
        assert "imputation_significance_change_reason" in Path(
            "quantify.differential.tsv"
        ).read_text(encoding="utf-8")


def test_quantify_command_reports_confounded_batch_correction_block() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        fixture_dir = FIXTURE_ROOT / "quant"
        shutil.copy(fixture_dir / "ms1_features.tsv", "features.tsv")
        Path("design.tsv").write_text(
            "\n".join(
                [
                    "sample_id\tcondition\treplicate\tfraction\tspectra_file\tidentifications_file\tbatch\tinstrument\tsearch_engine",
                    "C1\tcontrol\t1\t1\tc1.mzml\tc1.tsv\tbatch-a\torbitrap-a\tsage",
                    "C2\tcontrol\t2\t1\tc2.mzml\tc2.tsv\tbatch-a\torbitrap-b\tsage",
                    "T1\ttreatment\t1\t1\tt1.mzml\tt1.tsv\tbatch-b\torbitrap-a\tsage",
                    "T2\ttreatment\t2\t1\tt2.mzml\tt2.tsv\tbatch-b\torbitrap-b\tsage",
                ]
            )
            + "\n",
            encoding="utf-8",
        )

        result = runner.invoke(
            cli,
            [
                "quantify",
                "features.tsv",
                "--design",
                "design.tsv",
                "--design-batch-field",
                "",
                "--entity-level",
                "protein",
                "--aggregation",
                "sum",
                "--normalization",
                "median",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["batch_effect"]["fully_confounded_with_condition"] is True
        assert payload["batch_effect"]["batch_correction_blocked"] is True
        assert payload["batch_effect"]["disposition"] == "ENFORCED"
        assert "batch is fully confounded with condition" in (
            payload["batch_effect"]["batch_warning"] or ""
        )


def test_quantify_command_reports_paired_differential_broken_pairs() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        Path("paired_features.tsv").write_text(
            "\n".join(
                (
                    "feature_id\tsample_id\tpeptide\tproteins\tintensity\tcharge\tmz\tretention_time_seconds\tmissing_reason",
                    "pf001\tC1\tPEPA\tP001\t1000\t2\t500.2\t1200\t",
                    "pf002\tT1\tPEPA\tP001\t1900\t2\t500.2\t1201\t",
                    "pf003\tC2\tPEPA\tP001\t1100\t2\t500.2\t1202\t",
                    "pf004\tT2\tPEPA\tP001\t2200\t2\t500.2\t1203\t",
                    "pf005\tC3\tPEPA\tP001\t900\t2\t500.2\t1204\t",
                    "pf101\tC1\tPEPB\tP002\t500\t2\t600.2\t1300\t",
                    "pf102\tT1\tPEPB\tP002\t850\t2\t600.2\t1301\t",
                    "pf103\tC2\tPEPB\tP002\t520\t2\t600.2\t1302\t",
                    "pf104\tT2\tPEPB\tP002\t900\t2\t600.2\t1303\t",
                    "pf105\tC3\tPEPB\tP002\t510\t2\t600.2\t1304\t",
                )
            ),
            encoding="utf-8",
        )
        Path("paired.design.tsv").write_text(
            "\n".join(
                (
                    "sample_id\tcondition\treplicate\tfraction\tspectra_file\tidentifications_file\tbatch\tinstrument\tsearch_engine\tpair_id",
                    "C1\tcontrol\t1\t1\tc1.mzml\tc1.tsv\tbatch-a\torbitrap-a\tsage\tpair-1",
                    "T1\ttreatment\t1\t1\tt1.mzml\tt1.tsv\tbatch-a\torbitrap-a\tsage\tpair-1",
                    "C2\tcontrol\t2\t1\tc2.mzml\tc2.tsv\tbatch-b\torbitrap-b\tsage\tpair-2",
                    "T2\ttreatment\t2\t1\tt2.mzml\tt2.tsv\tbatch-b\torbitrap-b\tsage\tpair-2",
                    "C3\tcontrol\t3\t1\tc3.mzml\tc3.tsv\tbatch-c\torbitrap-c\tsage\tpair-3",
                )
            ),
            encoding="utf-8",
        )

        result = runner.invoke(
            cli,
            [
                "quantify",
                "paired_features.tsv",
                "--design",
                "paired.design.tsv",
                "--entity-level",
                "protein",
                "--aggregation",
                "sum",
                "--normalization",
                "none",
                "--imputation",
                "none",
                "--condition-a",
                "control",
                "--condition-b",
                "treatment",
                "--design-batch-field",
                "",
                "--differential-tsv-out",
                "paired.differential.tsv",
                "--broken-pairs-tsv-out",
                "paired.broken.tsv",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert (
            payload["differential_abundance"]["assumption_report"]["test_type"]
            == "paired_t_test"
        )
        assert payload["differential_abundance"]["broken_pairs"][0]["pair_id"] == "pair-3"
        assert payload["outputs"]["differential_tsv"] == "paired.differential.tsv"
        assert "complete_pair_count" in Path("paired.differential.tsv").read_text(
            encoding="utf-8"
        )
        assert "pair-3" in Path("paired.broken.tsv").read_text(encoding="utf-8")
        assert "P001\tcontrol\ttreatment" in Path(
            "paired.differential.tsv"
        ).read_text(encoding="utf-8")
        assert "contrast_name" in Path("paired.differential.tsv").read_text(
            encoding="utf-8"
        )
        assert payload["outputs"]["broken_pairs_tsv"] == "paired.broken.tsv"
        assert any(
            entry["entity_id"] == "P001" and entry["log2_fold_change"] > 0
            for entry in payload["differential_abundance"]["entries"]
        )


def test_quantify_command_reports_log2_normalization_preparation_explicitly() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        fixture_dir = FIXTURE_ROOT / "quant"
        shutil.copy(fixture_dir / "ms1_features.tsv", "ms1_features.tsv")
        shutil.copy(fixture_dir / "quant.design.tsv", "quant.design.tsv")

        result = runner.invoke(
            cli,
            [
                "quantify",
                "ms1_features.tsv",
                "--design",
                "quant.design.tsv",
                "--entity-level",
                "protein",
                "--aggregation",
                "sum",
                "--normalization",
                "log2_median_centering",
                "--imputation",
                "none",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["table"]["normalization_method"] == "log2_median_centering"
        assert payload["normalization_comparison"]["method"] == "log2_median_centering"
        assert payload["normalization_comparison"]["before_distributions"]
        assert payload["normalization_comparison"]["after_distributions"]
        assert payload["normalization_comparison"]["log_transform_preparation"]
        assert {
            entry["handling_strategy"]
            for entry in payload["normalization_comparison"]["log_transform_preparation"]
        } == {"exclude_nonpositive_values_before_log2_centering"}
        assert all(
            entry["zero_count"] == 1
            for entry in payload["normalization_comparison"]["log_transform_preparation"]
        )
        assert any(
            entry["method"] == "log2_median_centering"
            for entry in payload["normalization_strategy"]["entries"]
        )


def test_quantify_command_reports_group_aware_imputation_provenance() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        fixture_dir = FIXTURE_ROOT / "quant"
        shutil.copy(fixture_dir / "ms1_features.tsv", "ms1_features.tsv")
        shutil.copy(fixture_dir / "quant.design.tsv", "quant.design.tsv")

        result = runner.invoke(
            cli,
            [
                "quantify",
                "ms1_features.tsv",
                "--design",
                "quant.design.tsv",
                "--entity-level",
                "protein",
                "--aggregation",
                "sum",
                "--normalization",
                "median",
                "--imputation",
                "group_aware_low_intensity",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["table"]["imputation_method"] == "group_aware_low_intensity"
        assert payload["imputation_report"]["method"] == "group_aware_low_intensity"
        assert payload["imputation_report"]["entries"]
        assert tuple(
            entry["method"] for entry in payload["imputation_sensitivity"]["entries"]
        ) == (
            "none",
            "low_intensity",
            "knn",
            "group_aware_low_intensity",
        )
        first_entry = payload["imputation_report"]["entries"][0]
        assert first_entry["strategy"] == "condition_low_intensity_floor"
        assert first_entry["reference_group"] in {"control", "treatment"}
        imputed_row = next(
            value
            for value in payload["table"]["values"]
            if value["entity_id"] == "P004"
            and value["sample_id"] == "C1"
        )
        assert imputed_row["imputation_provenance"]["method"] == (
            "group_aware_low_intensity"
        )


def test_quantify_command_blocks_confounded_design_matrices() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        fixture_dir = FIXTURE_ROOT / "quant"
        shutil.copy(fixture_dir / "ms1_features.tsv", "ms1_features.tsv")
        Path("confounded.design.tsv").write_text(
            "\n".join(
                (
                    "sample_id\tcondition\treplicate\tfraction\tspectra_file\tidentifications_file\tbatch\tinstrument\tsearch_engine\tpair_id\ttimepoint\tage_years",
                    "C1\tcontrol\t1\t1\tc1.mzml\tc1.tsv\tbatch-a\torbitrap-a\tsage\tpair-a\tt0\t40",
                    "C2\tcontrol\t2\t1\tc2.mzml\tc2.tsv\tbatch-a\torbitrap-a\tsage\tpair-a\tt0\t40",
                    "T1\ttreatment\t1\t1\tt1.mzml\tt1.tsv\tbatch-b\torbitrap-b\tsage\tpair-b\tt1\t60",
                    "T2\ttreatment\t2\t1\tt2.mzml\tt2.tsv\tbatch-b\torbitrap-b\tsage\tpair-b\tt1\t60",
                )
            )
            + "\n",
            encoding="utf-8",
        )

        result = runner.invoke(
            cli,
            [
                "quantify",
                "ms1_features.tsv",
                "--design",
                "confounded.design.tsv",
                "--entity-level",
                "protein",
                "--aggregation",
                "sum",
                "--design-pairing-field",
                "pair_id",
                "--design-covariate",
                "timepoint",
                "--design-covariate",
                "age_years",
            ],
        )

        assert result.exit_code != 0
        assert "design matrix is confounded or rank-deficient" in result.output


def test_quantify_command_requires_explicit_timepoint_order_for_unordered_labels() -> (
    None
):
    runner = CliRunner()
    with runner.isolated_filesystem():
        Path("time_course_features.tsv").write_text(
            "\n".join(
                (
                    "feature_id\tsample_id\tpeptide\tproteins\tintensity\tcharge\tmz\tretention_time_seconds",
                    "tc001\tc_base_1\tPEPA\tP001\t100\t2\t500.2\t1200",
                    "tc002\tc_base_2\tPEPA\tP001\t110\t2\t500.2\t1201",
                    "tc003\tc_end_1\tPEPA\tP001\t130\t2\t500.2\t1202",
                    "tc004\tc_end_2\tPEPA\tP001\t140\t2\t500.2\t1203",
                    "tc005\tt_base_1\tPEPA\tP001\t100\t2\t500.2\t1204",
                    "tc006\tt_base_2\tPEPA\tP001\t110\t2\t500.2\t1205",
                    "tc007\tt_end_1\tPEPA\tP001\t410\t2\t500.2\t1206",
                    "tc008\tt_end_2\tPEPA\tP001\t430\t2\t500.2\t1207",
                )
            )
            + "\n",
            encoding="utf-8",
        )
        Path("time_course.design.tsv").write_text(
            "\n".join(
                (
                    "sample_id\tcondition\treplicate\tfraction\tspectra_file\tidentifications_file\tbatch\tinstrument\tsearch_engine\ttimepoint",
                    "c_base_1\tcontrol\t1\t1\tc_base_1.mzml\tc_base_1.tsv\tbatch-a\torbitrap-a\tsage\tbaseline",
                    "c_base_2\tcontrol\t2\t1\tc_base_2.mzml\tc_base_2.tsv\tbatch-a\torbitrap-a\tsage\tbaseline",
                    "c_end_1\tcontrol\t3\t1\tc_end_1.mzml\tc_end_1.tsv\tbatch-b\torbitrap-b\tsage\tendpoint",
                    "c_end_2\tcontrol\t4\t1\tc_end_2.mzml\tc_end_2.tsv\tbatch-b\torbitrap-b\tsage\tendpoint",
                    "t_base_1\ttreatment\t1\t1\tt_base_1.mzml\tt_base_1.tsv\tbatch-a\torbitrap-a\tsage\tbaseline",
                    "t_base_2\ttreatment\t2\t1\tt_base_2.mzml\tt_base_2.tsv\tbatch-a\torbitrap-a\tsage\tbaseline",
                    "t_end_1\ttreatment\t3\t1\tt_end_1.mzml\tt_end_1.tsv\tbatch-b\torbitrap-b\tsage\tendpoint",
                    "t_end_2\ttreatment\t4\t1\tt_end_2.mzml\tt_end_2.tsv\tbatch-b\torbitrap-b\tsage\tendpoint",
                )
            )
            + "\n",
            encoding="utf-8",
        )

        result = runner.invoke(
            cli,
            [
                "quantify",
                "time_course_features.tsv",
                "--design",
                "time_course.design.tsv",
                "--entity-level",
                "protein",
                "--aggregation",
                "sum",
                "--normalization",
                "none",
                "--imputation",
                "none",
                "--design-batch-field",
                "",
                "--time-course-tsv-out",
                "time_course.tsv",
            ],
        )

        assert result.exit_code != 0
        assert "unordered timepoint labels require an explicit order file" in result.output


def test_quantify_command_emits_time_course_differential_outputs() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        Path("time_course_features.tsv").write_text(
            "\n".join(
                (
                    "feature_id\tsample_id\tpeptide\tproteins\tintensity\tcharge\tmz\tretention_time_seconds",
                    "tc001\tc_base_1\tPEPA\tP001\t100\t2\t500.2\t1200",
                    "tc002\tc_base_2\tPEPA\tP001\t110\t2\t500.2\t1201",
                    "tc003\tc_end_1\tPEPA\tP001\t130\t2\t500.2\t1202",
                    "tc004\tc_end_2\tPEPA\tP001\t140\t2\t500.2\t1203",
                    "tc005\tt_base_1\tPEPA\tP001\t100\t2\t500.2\t1204",
                    "tc006\tt_base_2\tPEPA\tP001\t110\t2\t500.2\t1205",
                    "tc007\tt_end_1\tPEPA\tP001\t410\t2\t500.2\t1206",
                    "tc008\tt_end_2\tPEPA\tP001\t430\t2\t500.2\t1207",
                    "tc101\tc_base_1\tPEPB\tP002\t200\t2\t600.2\t1300",
                    "tc102\tc_base_2\tPEPB\tP002\t210\t2\t600.2\t1301",
                    "tc103\tc_end_1\tPEPB\tP002\t240\t2\t600.2\t1302",
                    "tc104\tc_end_2\tPEPB\tP002\t250\t2\t600.2\t1303",
                    "tc105\tt_base_1\tPEPB\tP002\t205\t2\t600.2\t1304",
                    "tc106\tt_base_2\tPEPB\tP002\t215\t2\t600.2\t1305",
                    "tc107\tt_end_1\tPEPB\tP002\t245\t2\t600.2\t1306",
                    "tc108\tt_end_2\tPEPB\tP002\t255\t2\t600.2\t1307",
                )
            )
            + "\n",
            encoding="utf-8",
        )
        Path("time_course.design.tsv").write_text(
            "\n".join(
                (
                    "sample_id\tcondition\treplicate\tfraction\tspectra_file\tidentifications_file\tbatch\tinstrument\tsearch_engine\ttimepoint",
                    "c_base_1\tcontrol\t1\t1\tc_base_1.mzml\tc_base_1.tsv\tbatch-a\torbitrap-a\tsage\tbaseline",
                    "c_base_2\tcontrol\t2\t1\tc_base_2.mzml\tc_base_2.tsv\tbatch-a\torbitrap-a\tsage\tbaseline",
                    "c_end_1\tcontrol\t3\t1\tc_end_1.mzml\tc_end_1.tsv\tbatch-b\torbitrap-b\tsage\tendpoint",
                    "c_end_2\tcontrol\t4\t1\tc_end_2.mzml\tc_end_2.tsv\tbatch-b\torbitrap-b\tsage\tendpoint",
                    "t_base_1\ttreatment\t1\t1\tt_base_1.mzml\tt_base_1.tsv\tbatch-a\torbitrap-a\tsage\tbaseline",
                    "t_base_2\ttreatment\t2\t1\tt_base_2.mzml\tt_base_2.tsv\tbatch-a\torbitrap-a\tsage\tbaseline",
                    "t_end_1\ttreatment\t3\t1\tt_end_1.mzml\tt_end_1.tsv\tbatch-b\torbitrap-b\tsage\tendpoint",
                    "t_end_2\ttreatment\t4\t1\tt_end_2.mzml\tt_end_2.tsv\tbatch-b\torbitrap-b\tsage\tendpoint",
                )
            )
            + "\n",
            encoding="utf-8",
        )
        Path("timepoint.order.txt").write_text(
            "baseline\nendpoint\n",
            encoding="utf-8",
        )

        result = runner.invoke(
            cli,
            [
                "quantify",
                "time_course_features.tsv",
                "--design",
                "time_course.design.tsv",
                "--entity-level",
                "protein",
                "--aggregation",
                "sum",
                "--normalization",
                "none",
                "--imputation",
                "none",
                "--design-batch-field",
                "",
                "--design-timepoint-order-file",
                "timepoint.order.txt",
                "--time-course-tsv-out",
                "time_course.tsv",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["time_course_differential"] is not None
        assert payload["time_course_differential"]["ordered_timepoints"] == [
            "baseline",
            "endpoint",
        ]
        assert payload["outputs"]["time_course_tsv"] == "time_course.tsv"
        assert Path("time_course.tsv").read_text(encoding="utf-8").startswith(
            "entity_id\tcondition\treference_condition"
        )
        assert "interaction_p_value" in Path("time_course.tsv").read_text(
            encoding="utf-8"
        )


def test_heatmap_matrix_command_emits_normalized_matrix_payload() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        fixture_dir = FIXTURE_ROOT / "quant"
        shutil.copy(fixture_dir / "ms1_features.tsv", "ms1_features.tsv")
        shutil.copy(fixture_dir / "quant.design.tsv", "quant.design.tsv")

        result = runner.invoke(
            cli,
            [
                "heatmap-matrix",
                "ms1_features.tsv",
                "--design",
                "quant.design.tsv",
                "--entity-level",
                "protein",
                "--aggregation",
                "top_n",
                "--top-n",
                "2",
                "--summary-tsv-out",
                "heatmap.summary.tsv",
                "--matrix-tsv-out",
                "heatmap.matrix.tsv",
                "--row-metadata-tsv-out",
                "heatmap.rows.tsv",
                "--column-metadata-tsv-out",
                "heatmap.columns.tsv",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["accepted_features"] == 32
        assert payload["rejected_features"] == 0
        assert payload["heatmap_report"]["summary"]["entity_level"] == "protein"
        assert payload["heatmap_report"]["summary"]["z_scored"] is True
        assert payload["outputs"]["summary_tsv"] == "heatmap.summary.tsv"
        assert payload["outputs"]["matrix_tsv"] == "heatmap.matrix.tsv"
        assert payload["outputs"]["row_metadata_tsv"] == "heatmap.rows.tsv"
        assert payload["outputs"]["column_metadata_tsv"] == "heatmap.columns.tsv"
        assert Path("heatmap.summary.tsv").exists()
        assert Path("heatmap.matrix.tsv").exists()
        assert Path("heatmap.rows.tsv").exists()
        assert Path("heatmap.columns.tsv").exists()
        assert "entity_level\tmeasure_kind\taggregation_method" in Path(
            "heatmap.summary.tsv"
        ).read_text(encoding="utf-8")
        assert "entity_id\tC1\tC2\tT1\tT2" in Path("heatmap.matrix.tsv").read_text(
            encoding="utf-8"
        )
        assert "protein_refs\tmember_peptides" in Path("heatmap.rows.tsv").read_text(
            encoding="utf-8"
        )
        assert "column_index\tsample_id\tcondition" in Path(
            "heatmap.columns.tsv"
        ).read_text(encoding="utf-8")


def test_heatmap_matrix_command_applies_filter_and_missing_value_policy() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        fixture_dir = FIXTURE_ROOT / "quant"
        shutil.copy(fixture_dir / "ms1_features.tsv", "ms1_features.tsv")
        shutil.copy(fixture_dir / "quant.design.tsv", "quant.design.tsv")

        result = runner.invoke(
            cli,
            [
                "heatmap-matrix",
                "ms1_features.tsv",
                "--design",
                "quant.design.tsv",
                "--entity-level",
                "protein",
                "--aggregation",
                "top_n",
                "--top-n",
                "2",
                "--protein-ref",
                "P001",
                "--min-observed-fraction",
                "1.0",
                "--no-z-score",
                "--missing-value-policy",
                "drop_rows",
                "--matrix-tsv-out",
                "heatmap.filtered.tsv",
                "--row-metadata-tsv-out",
                "heatmap.rows.tsv",
                "--column-metadata-tsv-out",
                "heatmap.columns.tsv",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["heatmap_report"]["summary"]["output_entity_count"] == 1
        assert payload["heatmap_report"]["summary"]["filtered_protein_ref_count"] >= 1
        assert payload["heatmap_report"]["summary"]["z_scored"] is False
        assert (
            payload["heatmap_report"]["summary"]["missing_value_policy"] == "drop_rows"
        )
        assert (
            payload["heatmap_report"]["column_metadata"][0]["missing_value_policy"]
            == "drop_rows"
        )
        assert "P001" in Path("heatmap.filtered.tsv").read_text(encoding="utf-8")
        assert "P002" not in Path("heatmap.filtered.tsv").read_text(encoding="utf-8")
        assert "missing_value_policy" in Path("heatmap.rows.tsv").read_text(
            encoding="utf-8"
        )
        assert "missing_value_policy" in Path("heatmap.columns.tsv").read_text(
            encoding="utf-8"
        )


def test_sample_exploration_command_emits_scores_distances_and_clusters() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        fixture_dir = FIXTURE_ROOT / "quant"
        shutil.copy(fixture_dir / "ms1_features.tsv", "ms1_features.tsv")
        shutil.copy(fixture_dir / "quant.design.tsv", "quant.design.tsv")

        result = runner.invoke(
            cli,
            [
                "sample-exploration",
                "ms1_features.tsv",
                "--design",
                "quant.design.tsv",
                "--entity-level",
                "protein",
                "--aggregation",
                "top_n",
                "--top-n",
                "2",
                "--summary-tsv-out",
                "sample_exploration.summary.tsv",
                "--scores-tsv-out",
                "sample_exploration.scores.tsv",
                "--explained-variance-tsv-out",
                "sample_exploration.variance.tsv",
                "--correlations-tsv-out",
                "sample_exploration.correlations.tsv",
                "--distances-tsv-out",
                "sample_exploration.distances.tsv",
                "--clusters-tsv-out",
                "sample_exploration.clusters.tsv",
                "--outliers-tsv-out",
                "sample_exploration.outliers.tsv",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["accepted_features"] == 32
        assert payload["rejected_features"] == 0
        assert (
            payload["sample_exploration_report"]["summary"]["entity_level"]
            == "protein"
        )
        assert (
            payload["sample_exploration_report"]["summary"][
                "pairwise_correlation_count"
            ]
            == 6
        )
        assert (
            payload["sample_exploration_report"]["summary"][
                "pairwise_distance_count"
            ]
            == 6
        )
        assert payload["sample_exploration_report"]["sample_correlation_report"]["entries"]
        assert "outlier_reasons" in payload["sample_exploration_report"]["sample_pca_report"]["entries"][0]
        assert payload["outputs"]["summary_tsv"] == "sample_exploration.summary.tsv"
        assert payload["outputs"]["scores_tsv"] == "sample_exploration.scores.tsv"
        assert (
            payload["outputs"]["explained_variance_tsv"]
            == "sample_exploration.variance.tsv"
        )
        assert (
            payload["outputs"]["correlations_tsv"]
            == "sample_exploration.correlations.tsv"
        )
        assert (
            payload["outputs"]["distances_tsv"]
            == "sample_exploration.distances.tsv"
        )
        assert payload["outputs"]["clusters_tsv"] == "sample_exploration.clusters.tsv"
        assert payload["outputs"]["outliers_tsv"] == "sample_exploration.outliers.tsv"
        assert Path("sample_exploration.summary.tsv").exists()
        assert Path("sample_exploration.scores.tsv").exists()
        assert Path("sample_exploration.variance.tsv").exists()
        assert Path("sample_exploration.correlations.tsv").exists()
        assert Path("sample_exploration.distances.tsv").exists()
        assert Path("sample_exploration.clusters.tsv").exists()
        assert Path("sample_exploration.outliers.tsv").exists()
        assert "entity_level\tmeasure_kind\taggregation_method" in Path(
            "sample_exploration.summary.tsv"
        ).read_text(encoding="utf-8")
        assert "sample_id\tcondition\tbatch\tpc1\tpc2" in Path(
            "sample_exploration.scores.tsv"
        ).read_text(encoding="utf-8")
        assert "component_index\tcomponent_label\texplained_variance_ratio" in Path(
            "sample_exploration.variance.tsv"
        ).read_text(encoding="utf-8")
        assert "sample_id_a\tsample_id_b\tcondition_a\tcondition_b" in Path(
            "sample_exploration.correlations.tsv"
        ).read_text(encoding="utf-8")
        assert "sample_id_a\tsample_id_b\tcondition_a\tcondition_b" in Path(
            "sample_exploration.distances.tsv"
        ).read_text(encoding="utf-8")
        assert "merge_order\tmember_sample_ids\tleft_sample_ids\tright_sample_ids" in Path(
            "sample_exploration.clusters.tsv"
        ).read_text(encoding="utf-8")
        assert "sample_id\tcondition\tbatch\toutlier_reasons" in Path(
            "sample_exploration.outliers.tsv"
        ).read_text(encoding="utf-8")


def test_power_estimate_command_emits_variance_and_effect_size_grid() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        fixture_dir = FIXTURE_ROOT / "quant"
        shutil.copy(fixture_dir / "ms1_features.tsv", "ms1_features.tsv")
        shutil.copy(fixture_dir / "quant.design.tsv", "quant.design.tsv")

        result = runner.invoke(
            cli,
            [
                "power-estimate",
                "ms1_features.tsv",
                "--design",
                "quant.design.tsv",
                "--entity-level",
                "protein",
                "--aggregation",
                "top_n",
                "--top-n",
                "2",
                "--replicates-per-condition",
                "2",
                "--replicates-per-condition",
                "4",
                "--replicates-per-condition",
                "6",
                "--summary-tsv-out",
                "power.summary.tsv",
                "--variance-tsv-out",
                "power.variance.tsv",
                "--effect-size-grid-tsv-out",
                "power.grid.tsv",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["accepted_features"] == 32
        assert payload["rejected_features"] == 0
        assert payload["power_estimation_report"]["summary"]["entity_level"] == "protein"
        assert payload["power_estimation_report"]["variance_entries"]
        assert payload["power_estimation_report"]["effect_size_grid"]
        assert (
            payload["power_estimation_report"]["summary"][
                "weaker_power_with_fewer_replicates"
            ]
            is True
        )
        assert payload["outputs"]["summary_tsv"] == "power.summary.tsv"
        assert payload["outputs"]["variance_tsv"] == "power.variance.tsv"
        assert payload["outputs"]["effect_size_grid_tsv"] == "power.grid.tsv"
        assert Path("power.summary.tsv").exists()
        assert Path("power.variance.tsv").exists()
        assert Path("power.grid.tsv").exists()
        assert "fdr_target\ttarget_power" in Path("power.summary.tsv").read_text(
            encoding="utf-8"
        )
        assert "entity_id\tprotein_refs\tobserved_sample_count" in Path(
            "power.variance.tsv"
        ).read_text(encoding="utf-8")
        assert "replicates_per_condition\tevaluable_entity_count" in Path(
            "power.grid.tsv"
        ).read_text(encoding="utf-8")


def test_quantify_command_emits_multi_condition_differential_collection() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        fixture_dir = FIXTURE_ROOT / "quant"
        shutil.copy(
            fixture_dir / "multi_condition_ms1_features.tsv",
            "multi_condition_ms1_features.tsv",
        )
        shutil.copy(
            fixture_dir / "multi_condition.design.tsv",
            "multi_condition.design.tsv",
        )

        result = runner.invoke(
            cli,
            [
                "quantify",
                "multi_condition_ms1_features.tsv",
                "--design",
                "multi_condition.design.tsv",
                "--entity-level",
                "protein",
                "--aggregation",
                "sum",
                "--normalization",
                "median",
                "--differential-tsv-out",
                "quantify.multi_condition.tsv",
                "--multi-contrast-consistency-tsv-out",
                "quantify.multi_condition.consistency.tsv",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["design_matrix"] is not None
        assert payload["design_model_fit"] is not None
        assert payload["differential_abundance"] is None
        assert payload["differential_abundance_multi_condition"] is not None
        assert payload["multi_contrast_consistency"] is not None
        assert payload["outputs"]["differential_tsv"] == "quantify.multi_condition.tsv"
        assert (
            payload["outputs"]["multi_contrast_consistency_tsv"]
            == "quantify.multi_condition.consistency.tsv"
        )
        assert Path("quantify.multi_condition.tsv").exists()
        assert Path("quantify.multi_condition.consistency.tsv").exists()
        tsv = Path("quantify.multi_condition.tsv").read_text(encoding="utf-8")
        consistency_tsv = Path("quantify.multi_condition.consistency.tsv").read_text(
            encoding="utf-8"
        )
        assert "P001\tcontrol\trescue" in tsv
        assert "P001\tcontrol\ttreatment" in tsv
        assert "direction_conflict" in consistency_tsv
        assert (
            payload["differential_abundance_multi_condition"]["condition_count"] == 3
        )
        assert len(payload["differential_abundance_multi_condition"]["reports"]) == 3
        assert payload["multi_contrast_consistency"]["summary"]["entity_count"] >= 1
        assert all(
            entry["adjusted_p_value"] is not None
            for report in payload["differential_abundance_multi_condition"]["reports"]
            for entry in report["entries"]
        )


def test_quantify_command_validates_imported_statistical_backend_results() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        fixture_dir = FIXTURE_ROOT / "quant"
        shutil.copy(fixture_dir / "ms1_features.tsv", "ms1_features.tsv")
        shutil.copy(fixture_dir / "quant.design.tsv", "quant.design.tsv")
        shutil.copy(fixture_dir / "limma_results.tsv", "limma_results.tsv")
        shutil.copy(fixture_dir / "msstats_results.tsv", "msstats_results.tsv")

        result = runner.invoke(
            cli,
            [
                "quantify",
                "ms1_features.tsv",
                "--design",
                "quant.design.tsv",
                "--entity-level",
                "protein",
                "--aggregation",
                "top_n",
                "--top-n",
                "2",
                "--normalization",
                "median",
                "--imputation",
                "low_intensity",
                "--condition-a",
                "control",
                "--condition-b",
                "treatment",
                "--limma-results",
                "limma_results.tsv",
                "--msstats-results",
                "msstats_results.tsv",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["limma_result_import"]["row_count"] == 2
        assert payload["msstats_result_import"]["row_count"] == 2
        assert payload["limma_validation"]["matched_row_count"] == 2
        assert payload["limma_validation"]["directionally_concordant_count"] == 2
        assert payload["msstats_validation"]["matched_row_count"] == 2
        assert payload["msstats_validation"]["directionally_concordant_count"] == 2
        assert (
            payload["limma_validation"]["mean_absolute_log2_fold_change_delta"]
            is not None
        )
        assert (
            payload["msstats_validation"]["mean_absolute_log2_fold_change_delta"]
            is not None
        )


def test_peptide_matrix_command_emits_feature_backed_matrix_and_ledgers() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        fixture_dir = FIXTURE_ROOT / "quant"
        shutil.copy(
            fixture_dir / "peptide_matrix_features.tsv",
            "peptide_matrix_features.tsv",
        )

        result = runner.invoke(
            cli,
            [
                "peptide-matrix",
                "peptide_matrix_features.tsv",
                "--input-kind",
                "feature",
                "--grouping-mode",
                "modified_peptide",
                "--separate-charge-states",
                "--summary-tsv-out",
                "peptide_matrix.summary.tsv",
                "--matrix-tsv-out",
                "peptide_matrix.matrix.tsv",
                "--missingness-tsv-out",
                "peptide_matrix.missingness.tsv",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["input_kind"] == "feature"
        assert payload["accepted_source_records"] == 7
        assert payload["rejected_source_records"] == 0
        assert payload["report"]["summary"]["peptide_row_count"] == 4
        assert Path("peptide_matrix.summary.tsv").exists()
        assert Path("peptide_matrix.matrix.tsv").exists()
        assert Path("peptide_matrix.missingness.tsv").exists()
        assert "feature\tmodified_peptide\ttrue\tsum" in Path(
            "peptide_matrix.summary.tsv"
        ).read_text(encoding="utf-8")
        assert "PEM[Oxidation]TIDE/z2" in Path("peptide_matrix.matrix.tsv").read_text(
            encoding="utf-8"
        )


def test_peptide_matrix_command_emits_psm_backed_matrix_and_skipped_counts() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        fixture_dir = FIXTURE_ROOT / "quant"
        shutil.copy(
            fixture_dir / "peptide_matrix_psms.tsv",
            "peptide_matrix_psms.tsv",
        )

        result = runner.invoke(
            cli,
            [
                "peptide-matrix",
                "peptide_matrix_psms.tsv",
                "--input-kind",
                "psm",
                "--grouping-mode",
                "modified_peptide",
                "--run-column",
                "run_id",
                "--spectrum-id-column",
                "spectrum_id",
                "--modified-peptide-column",
                "modified_peptide",
                "--score-column",
                "score",
                "--summary-tsv-out",
                "peptide_matrix_psm.summary.tsv",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["input_kind"] == "psm"
        assert payload["accepted_source_records"] == 7
        assert payload["rejected_source_records"] == 0
        assert payload["report"]["summary"]["accepted_source_record_count"] == 5
        assert payload["report"]["summary"]["skipped_source_record_count"] == 2
        assert payload["report"]["rows"][0]["values"]
        summary_tsv = Path("peptide_matrix_psm.summary.tsv").read_text(encoding="utf-8")
        assert "skipped_source_record_count" in summary_tsv
        assert (
            "psm\tmodified_peptide\tfalse\tsum\t5\t2\t2\t2\t3\t0\t1\t0\t" in summary_tsv
        )


def test_peptide_matrix_command_emits_precursor_mask_and_aggregation_ledgers() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        fixture_dir = FIXTURE_ROOT / "quant"
        shutil.copy(
            fixture_dir / "peptide_matrix_precursors.tsv",
            "peptide_matrix_precursors.tsv",
        )

        result = runner.invoke(
            cli,
            [
                "peptide-matrix",
                "peptide_matrix_precursors.tsv",
                "--input-kind",
                "precursor",
                "--grouping-mode",
                "modified_peptide",
                "--aggregation",
                "top_n",
                "--top-n",
                "2",
                "--summary-tsv-out",
                "peptide_matrix_precursor.summary.tsv",
                "--missingness-mask-tsv-out",
                "peptide_matrix_precursor.mask.tsv",
                "--aggregation-table-tsv-out",
                "peptide_matrix_precursor.aggregation.tsv",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["input_kind"] == "precursor"
        assert payload["accepted_source_records"] == 7
        assert payload["rejected_source_records"] == 0
        assert payload["report"]["summary"]["filtered_cell_count"] == 1
        assert payload["report"]["summary"]["missing_cell_count"] == 1
        assert payload["report"]["aggregation_entries"][0]["aggregation_method"] == "top_n"
        assert Path("peptide_matrix_precursor.summary.tsv").exists()
        assert Path("peptide_matrix_precursor.mask.tsv").exists()
        assert Path("peptide_matrix_precursor.aggregation.tsv").exists()
        assert "precursor\tmodified_peptide\tfalse\ttop_n\t7\t0\t3\t2\t4\t0\t1\t1\t" in Path(
            "peptide_matrix_precursor.summary.tsv"
        ).read_text(encoding="utf-8")
        assert "missing_not_observed" in Path(
            "peptide_matrix_precursor.mask.tsv"
        ).read_text(encoding="utf-8")
        assert "ppq001;ppq002" in Path(
            "peptide_matrix_precursor.aggregation.tsv"
        ).read_text(encoding="utf-8")


def test_protein_matrix_command_emits_feature_backed_rollup_and_ledgers() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        fixture_dir = FIXTURE_ROOT / "quant"
        shutil.copy(
            fixture_dir / "protein_matrix_features.tsv",
            "protein_matrix_features.tsv",
        )

        result = runner.invoke(
            cli,
            [
                "protein-matrix",
                "protein_matrix_features.tsv",
                "--input-kind",
                "feature",
                "--target-kind",
                "protein",
                "--aggregation",
                "top_n",
                "--top-n",
                "2",
                "--unique-peptide-only",
                "--summary-tsv-out",
                "protein_matrix.summary.tsv",
                "--matrix-tsv-out",
                "protein_matrix.matrix.tsv",
                "--missingness-tsv-out",
                "protein_matrix.missingness.tsv",
                "--contributions-tsv-out",
                "protein_matrix.contributions.tsv",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["input_kind"] == "feature"
        assert payload["accepted_source_records"] == 8
        assert payload["rejected_source_records"] == 0
        assert payload["report"]["summary"]["protein_row_count"] == 2
        assert payload["report"]["summary"]["unique_only"] is True
        assert Path("protein_matrix.summary.tsv").exists()
        assert Path("protein_matrix.matrix.tsv").exists()
        assert Path("protein_matrix.missingness.tsv").exists()
        assert Path("protein_matrix.contributions.tsv").exists()
        assert (
            payload["report"]["rows"][0]["values"][0]["shared_peptide_policy"]
            == "unique_only"
        )
        assert "feature\tmodified_peptide\tprotein\tfalse\ttop_n\ttrue" in Path(
            "protein_matrix.summary.tsv"
        ).read_text(encoding="utf-8")
        assert "P1\tprotein\tP1\t2\t2\t0\tPEPAAK;PEPMTK\t1600\t2100" in Path(
            "protein_matrix.matrix.tsv"
        ).read_text(encoding="utf-8")
        contribution_tsv = Path("protein_matrix.contributions.tsv").read_text(
            encoding="utf-8"
        )
        assert "included_abundance_fraction" in contribution_tsv
        assert (
            "P1\tprotein\tS1\tPEPAAK\tPEPAAK\tP1\t1000\tobserved\tfalse\ttrue\ttrue\t1600\t1\t0.625000\t0.625000\tunique_only"
            in contribution_tsv
        )
        assert (
            "P1\tprotein\tS1\tSHAREDK\tSHAREDK\tP1\t300\tobserved\ttrue\tfalse\tfalse\t1600\t3\t\t0.187500\tunique_only"
            in contribution_tsv
        )


def test_protein_matrix_command_emits_psm_backed_group_rollup() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        fixture_dir = FIXTURE_ROOT / "quant"
        shutil.copy(
            fixture_dir / "peptide_matrix_psms.tsv",
            "peptide_matrix_psms.tsv",
        )

        result = runner.invoke(
            cli,
            [
                "protein-matrix",
                "peptide_matrix_psms.tsv",
                "--input-kind",
                "psm",
                "--target-kind",
                "protein_group",
                "--run-column",
                "run_id",
                "--spectrum-id-column",
                "spectrum_id",
                "--modified-peptide-column",
                "modified_peptide",
                "--score-column",
                "score",
                "--summary-tsv-out",
                "protein_matrix_psm.summary.tsv",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["input_kind"] == "psm"
        assert payload["accepted_source_records"] == 7
        assert payload["rejected_source_records"] == 0
        assert payload["report"]["summary"]["protein_row_count"] == 1
        assert payload["report"]["rows"][0]["target_kind"] == "protein_group"
        summary_tsv = Path("protein_matrix_psm.summary.tsv").read_text(encoding="utf-8")
        assert "target_kind" in summary_tsv
        assert "psm\tmodified_peptide\tprotein_group\tfalse\tsum\tfalse" in summary_tsv


def test_protein_lfq_command_emits_feature_backed_matrix_and_pairwise_ledgers() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        fixture_dir = FIXTURE_ROOT / "quant"
        shutil.copy(
            fixture_dir / "protein_lfq_features.tsv",
            "protein_lfq_features.tsv",
        )

        result = runner.invoke(
            cli,
            [
                "protein-lfq",
                "protein_lfq_features.tsv",
                "--input-kind",
                "feature",
                "--target-kind",
                "protein",
                "--minimum-shared-peptides",
                "2",
                "--summary-tsv-out",
                "protein_lfq.summary.tsv",
                "--matrix-tsv-out",
                "protein_lfq.matrix.tsv",
                "--pairwise-tsv-out",
                "protein_lfq.pairwise.tsv",
                "--missingness-tsv-out",
                "protein_lfq.missingness.tsv",
                "--disconnected-components-tsv-out",
                "protein_lfq.disconnected.tsv",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["input_kind"] == "feature"
        assert payload["accepted_source_records"] == 10
        assert payload["rejected_source_records"] == 0
        assert payload["report"]["aggregation_method"] == "sum"
        assert payload["report"]["summary"]["protein_row_count"] == 2
        assert payload["report"]["summary"]["total_pairwise_ratio_count"] == 2
        assert Path("protein_lfq.summary.tsv").exists()
        assert Path("protein_lfq.matrix.tsv").exists()
        assert Path("protein_lfq.pairwise.tsv").exists()
        assert Path("protein_lfq.missingness.tsv").exists()
        assert Path("protein_lfq.disconnected.tsv").exists()
        assert "feature\tmodified_peptide\tprotein\tfalse\tsum\tfalse\t2" in Path(
            "protein_lfq.summary.tsv"
        ).read_text(encoding="utf-8")
        assert (
            "P1\tprotein\tP1\t3\t3\t0\t2\t1\tPEPAAK;PEPCCK;PEPVVK\t447.214\t894.427\t223.607"
            in Path("protein_lfq.matrix.tsv").read_text(encoding="utf-8")
        )
        assert "P1\tprotein\tS1\tS2\t2\t1\t2\tPEPAAK;PEPVVK" in Path(
            "protein_lfq.pairwise.tsv"
        ).read_text(encoding="utf-8")
        disconnected_tsv = Path("protein_lfq.disconnected.tsv").read_text(
            encoding="utf-8"
        )
        assert (
            "P2\tprotein\tP2\t1\tS1\tS2;S3\t1\t0\tDISCAAK" in disconnected_tsv
        )
        assert (
            "P2\tprotein\tP2\t2\tS2\tS1;S3\t1\t0\tDISCAAK" in disconnected_tsv
        )
        assert (
            "P2\tprotein\tP2\t3\tS3\tS1;S2\t1\t0\tDISCVVK" in disconnected_tsv
        )
        assert (
            payload["outputs"]["disconnected_components_tsv"]
            == "protein_lfq.disconnected.tsv"
        )


def test_protein_lfq_command_emits_peptide_profile_inconsistency_output() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        fixture_dir = FIXTURE_ROOT / "quant"
        shutil.copy(
            fixture_dir / "protein_profile_inconsistency_features.tsv",
            "protein_profile_inconsistency_features.tsv",
        )

        result = runner.invoke(
            cli,
            [
                "protein-lfq",
                "protein_profile_inconsistency_features.tsv",
                "--input-kind",
                "feature",
                "--target-kind",
                "protein",
                "--minimum-shared-peptides",
                "1",
                "--peptide-profile-tsv-out",
                "protein_lfq.peptide_profile.tsv",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["input_kind"] == "feature"
        assert (
            payload["peptide_profile_inconsistency_report"]["summary"][
                "inconsistent_entry_count"
            ]
            == 1
        )
        assert payload["outputs"]["peptide_profile_tsv"] == "protein_lfq.peptide_profile.tsv"
        peptide_profile_tsv = Path("protein_lfq.peptide_profile.tsv").read_text(
            encoding="utf-8"
        )
        assert "directional_profile_inversion" in peptide_profile_tsv
        assert "PEPVVK" in peptide_profile_tsv


def test_protein_lfq_command_emits_psm_backed_group_rollup_and_skipped_rows() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        fixture_dir = FIXTURE_ROOT / "quant"
        shutil.copy(
            fixture_dir / "protein_lfq_psms.tsv",
            "protein_lfq_psms.tsv",
        )

        result = runner.invoke(
            cli,
            [
                "protein-lfq",
                "protein_lfq_psms.tsv",
                "--input-kind",
                "psm",
                "--target-kind",
                "protein",
                "--run-column",
                "run_id",
                "--spectrum-id-column",
                "spectrum_id",
                "--modified-peptide-column",
                "modified_peptide",
                "--score-column",
                "score",
                "--summary-tsv-out",
                "protein_lfq_psm.summary.tsv",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["input_kind"] == "psm"
        assert payload["accepted_source_records"] == 9
        assert payload["rejected_source_records"] == 0
        assert payload["report"]["summary"]["protein_row_count"] == 1
        assert payload["report"]["summary"]["total_pairwise_ratio_count"] == 3
        summary_tsv = Path("protein_lfq_psm.summary.tsv").read_text(encoding="utf-8")
        assert "aggregation_method" in summary_tsv
        assert "psm\tmodified_peptide\tprotein\tfalse\tsum\tfalse\t1" in summary_tsv


def test_ptm_summarize_command_emits_site_reports_and_occupancy() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        ptm_fixture_dir = FIXTURE_ROOT / "ptm"
        fasta_fixture_dir = FIXTURE_ROOT / "fasta"
        shutil.copy(
            ptm_fixture_dir / "localization_results.tsv", "localization_results.tsv"
        )
        shutil.copy(ptm_fixture_dir / "ptm_features.tsv", "ptm_features.tsv")
        shutil.copy(fasta_fixture_dir / "ptm_sites.fasta", "ptm_sites.fasta")

        result = runner.invoke(
            cli,
            [
                "ptm",
                "summarize",
                "localization_results.tsv",
                "ptm_sites.fasta",
                "--features",
                "ptm_features.tsv",
                "--threshold",
                "0.1",
                "--flank-size",
                "3",
                "--occupancy-summary-tsv-out",
                "ptm.occupancy.summary.tsv",
                "--occupancy-tsv-out",
                "ptm.occupancy.tsv",
                "--occupancy-counterpart-tsv-out",
                "ptm.occupancy.counterpart.tsv",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["accepted_rows"] == 8
        assert any(
            entry["site_key"] == "P11111:S5:Phospho" for entry in payload["site_table"]
        )
        assert payload["ambiguity_review"]["summary"]["localized_site_count"] == 3
        assert payload["ambiguity_review"]["summary"]["unlocalized_group_count"] == 2
        assert payload["fdr_report"]["entries"][-1]["accepted"] is False
        assert any(
            entry["sample_id"] == "T2" and entry["occupancy_fraction"] == 0.79
            for entry in payload["occupancy"]
        )
        assert payload["occupancy_report"]["summary"]["entry_count"] >= 1
        assert payload["occupancy_report"]["summary"]["high_confidence_count"] >= 1
        assert any(
            entry["confidence_tier"] == "high_confidence"
            for entry in payload["occupancy"]
        )
        assert payload["occupancy_counterpart_report"]["entries"]
        assert payload["occupancy_counterpart_report"]["missing_unmodified_evidence_count"] >= 0
        assert payload["site_quantification"]["ambiguity_policy"] == "preserve"
        assert payload["site_group_quantification"]["summary"]["group_row_count"] == 2
        assert any(
            row["site_key"] == "P11111:S5:Phospho"
            for row in payload["site_quantification"]["rows"]
        )
        assert any(
            row["group_key"] == "P11111:Phospho:17|18|19"
            for row in payload["site_group_quantification"]["rows"]
        )
        assert "entry_count" in Path("ptm.occupancy.summary.tsv").read_text()
        assert "S[Phospho]PEPTIDEK" in Path("ptm.occupancy.tsv").read_text()
        assert "counterpart_status" in Path(
            "ptm.occupancy.counterpart.tsv"
        ).read_text()


def test_ptm_parse_peptide_command_emits_explicit_site_records() -> None:
    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "ptm",
            "parse-peptide",
            "[Acetyl]-M[Oxidation]STY[Phospho]K",
            "--protein-ref",
            "P22222",
            "--peptide-start-position",
            "15",
            "--sample-id",
            "T1",
            "--spectrum-id",
            "scan=ptm-peptide-002",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["canonical_peptide"] == "[Acetyl]-M[Oxidation]STY[Phospho]K"
    assert payload["modification_names"] == ["Acetyl", "Oxidation", "Phospho"]
    assert [site["residue"] for site in payload["sites"]] == ["M", "M", "Y"]
    assert [site["peptide_position"] for site in payload["sites"]] == [1, 1, 4]
    assert [site["protein_position"] for site in payload["sites"]] == [15, 15, 18]


def test_ptm_parse_peptides_command_emits_review_ledgers() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        ptm_fixture_dir = FIXTURE_ROOT / "ptm"
        shutil.copy(ptm_fixture_dir / "ptm_peptides.tsv", "ptm_peptides.tsv")

        result = runner.invoke(
            cli,
            [
                "ptm",
                "parse-peptides",
                "ptm_peptides.tsv",
                "--summary-tsv-out",
                "ptm_peptides.summary.tsv",
                "--record-tsv-out",
                "ptm_peptides.records.tsv",
                "--site-tsv-out",
                "ptm_peptides.sites.tsv",
                "--rejected-tsv-out",
                "ptm_peptides.rejected.tsv",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["summary"] == {
            "accepted_record_count": 3,
            "rejected_row_count": 2,
            "parsed_site_count": 5,
            "protein_mapped_site_count": 4,
            "multi_modified_record_count": 1,
        }
        assert Path("ptm_peptides.summary.tsv").read_text().splitlines()[1] == "3\t2\t5\t4\t1"
        assert "AAS[Phospho]PEP" in Path("ptm_peptides.records.tsv").read_text()
        assert "UNIMOD:21\tS\t3\t6\tanywhere" in Path(
            "ptm_peptides.sites.tsv"
        ).read_text()
        assert "invalid_peptide_start_position" in Path(
            "ptm_peptides.rejected.tsv"
        ).read_text()


def test_ptm_map_sites_command_emits_site_mapping_ledgers() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        ptm_fixture_dir = FIXTURE_ROOT / "ptm"
        fasta_fixture_dir = FIXTURE_ROOT / "fasta"
        shutil.copy(
            ptm_fixture_dir / "localization_results.tsv",
            "localization_results.tsv",
        )
        shutil.copy(fasta_fixture_dir / "ptm_sites.fasta", "ptm_sites.fasta")

        result = runner.invoke(
            cli,
            [
                "ptm",
                "map-sites",
                "localization_results.tsv",
                "ptm_sites.fasta",
                "--mapping-tsv-out",
                "ptm.mapping.tsv",
                "--exact-mapping-tsv-out",
                "ptm.exact.tsv",
                "--ambiguous-mapping-tsv-out",
                "ptm.ambiguous.tsv",
                "--unmapped-tsv-out",
                "ptm.unmapped.tsv",
                "--site-table-tsv-out",
                "ptm.site_table.tsv",
                "--ambiguity-tsv-out",
                "ptm.ambiguity.tsv",
                "--coverage-tsv-out",
                "ptm.coverage.tsv",
                "--validation-tsv-out",
                "ptm.validation.tsv",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["accepted_rows"] == 8
        assert payload["mapping_count"] == 10
        assert payload["exact_mapping_count"] == 6
        assert payload["ambiguous_mapping_count"] == 4
        assert payload["unmapped_peptide_count"] == 0
        assert payload["site_count"] == 5
        assert payload["ambiguity_count"] == 2
        assert payload["ambiguity_review"]["summary"]["possible_residue_count"] == 6
        assert payload["coordinate_validation"]["valid"] is True
        assert "shared_peptide" in Path("ptm.mapping.tsv").read_text()
        assert "scan=ptm-001" in Path("ptm.exact.tsv").read_text()
        assert "scan=ptm-005" in Path("ptm.ambiguous.tsv").read_text()
        assert Path("ptm.unmapped.tsv").read_text().splitlines()[0].startswith(
            "spectrum_id\tsample_id\tlocalized_peptide"
        )
        assert "P11111:S5:Phospho" in Path("ptm.site_table.tsv").read_text()
        assert (
            "P11111:Phospho:17|18|19"
            in Path("ptm.ambiguity.tsv").read_text()
        )
        assert "S;T;Y" in Path("ptm.ambiguity.tsv").read_text()
        assert "scan=ptm-001" in Path("ptm.coverage.tsv").read_text()
        assert (
            Path("ptm.validation.tsv").read_text().splitlines()[0]
            == "spectrum_id\tprotein_ref\tsite_key\tcode\tmessage"
        )


def test_ptm_map_sites_command_exports_separate_multi_modified_candidates() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        ptm_fixture_dir = FIXTURE_ROOT / "ptm"
        fasta_fixture_dir = FIXTURE_ROOT / "fasta"
        shutil.copy(
            ptm_fixture_dir / "multi_localization_results.tsv",
            "multi_localization_results.tsv",
        )
        shutil.copy(fasta_fixture_dir / "ptm_sites.fasta", "ptm_sites.fasta")

        result = runner.invoke(
            cli,
            [
                "ptm",
                "map-sites",
                "multi_localization_results.tsv",
                "ptm_sites.fasta",
                "--candidate-tsv-out",
                "ptm.candidates.tsv",
                "--mapping-tsv-out",
                "ptm.mapping.tsv",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["accepted_rows"] == 1
        assert payload["site_candidate_count"] == 2
        assert payload["mapping_count"] == 4
        assert "Phospho\tUNIMOD:21\tS\t2" in Path("ptm.candidates.tsv").read_text()
        assert "Phospho\tUNIMOD:21\tY\t4" in Path("ptm.candidates.tsv").read_text()
        assert "\t2\t17\t" in Path("ptm.mapping.tsv").read_text()
        assert "\t4\t19\t" in Path("ptm.mapping.tsv").read_text()


def test_ptm_map_sites_command_preserves_exact_shared_and_unmapped_ledgers() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        fasta_fixture_dir = FIXTURE_ROOT / "fasta"
        shutil.copy(fasta_fixture_dir / "ptm_sites.fasta", "ptm_sites.fasta")
        Path("mapping_input.tsv").write_text(
            "\n".join(
                (
                    "sample_id\tspectrum_id\tpeptide\tcharge\tscore\tq_value\tproteins\tlocalization_score\tcandidate_sites\tdecoy_label",
                    "C1\tscan=shared-unique\tS[Phospho]PEPTIDEK\t2\t110.0\t0.005\tP11111;P40404\t0.990\t1\ttarget",
                    "C1\tscan=unmapped\tS[Phospho]PEPTIDEK\t2\t110.0\t0.005\tP40404\t0.990\t1\ttarget",
                )
            )
            + "\n",
            encoding="utf-8",
        )

        result = runner.invoke(
            cli,
            [
                "ptm",
                "map-sites",
                "mapping_input.tsv",
                "ptm_sites.fasta",
                "--exact-mapping-tsv-out",
                "ptm.exact.tsv",
                "--ambiguous-mapping-tsv-out",
                "ptm.ambiguous.tsv",
                "--unmapped-tsv-out",
                "ptm.unmapped.tsv",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["mapping_count"] == 1
        assert payload["exact_mapping_count"] == 1
        assert payload["ambiguous_mapping_count"] == 0
        assert payload["unmapped_peptide_count"] == 1
        assert "scan=shared-unique" in Path("ptm.exact.tsv").read_text()
        assert Path("ptm.ambiguous.tsv").read_text().splitlines() == [
            "spectrum_id\tsample_id\tprotein_ref\tlocalized_peptide\tcanonical_peptide\tmodification_name\tresidue\tpeptide_site_index\tprotein_position\tlocalization_score\tq_value\tcandidate_protein_positions\tambiguous\tshared_peptide\ttarget_decoy_label"
        ]
        assert "scan=unmapped" in Path("ptm.unmapped.tsv").read_text()
        assert "missing_protein_sequence" in Path("ptm.unmapped.tsv").read_text()


def test_ptm_ambiguity_review_command_emits_localized_and_group_quant_ledgers() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        ptm_fixture_dir = FIXTURE_ROOT / "ptm"
        fasta_fixture_dir = FIXTURE_ROOT / "fasta"
        shutil.copy(
            ptm_fixture_dir / "localization_results.tsv",
            "localization_results.tsv",
        )
        shutil.copy(ptm_fixture_dir / "ptm_features.tsv", "ptm_features.tsv")
        shutil.copy(fasta_fixture_dir / "ptm_sites.fasta", "ptm_sites.fasta")
        Path("fragment_support.json").write_text(
            json.dumps(
                {
                    "scan=ptm-001": ["b5", "y7"],
                    "scan=ptm-005": ["b2"],
                }
            ),
            encoding="utf-8",
        )

        result = runner.invoke(
            cli,
            [
                "ptm",
                "ambiguity-review",
                "localization_results.tsv",
                "ptm_sites.fasta",
                "--features",
                "ptm_features.tsv",
                "--fragment-support-json",
                "fragment_support.json",
                "--summary-tsv-out",
                "ptm.ambiguity.summary.tsv",
                "--localized-tsv-out",
                "ptm.localized.tsv",
                "--unlocalized-tsv-out",
                "ptm.unlocalized.tsv",
                "--group-quant-summary-tsv-out",
                "ptm.group_quant.summary.tsv",
                "--group-quant-matrix-tsv-out",
                "ptm.group_quant.matrix.tsv",
                "--group-quant-missingness-tsv-out",
                "ptm.group_quant.missingness.tsv",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["ambiguity_review"]["summary"]["localized_site_count"] == 3
        assert payload["ambiguity_review"]["summary"]["unlocalized_group_count"] == 2
        assert payload["site_group_quantification"]["summary"]["group_row_count"] == 2
        assert Path("ptm.ambiguity.summary.tsv").read_text().splitlines()[0].startswith(
            "localized_site_count\tunlocalized_group_count"
        )
        assert "P11111:S5:Phospho" in Path("ptm.localized.tsv").read_text()
        assert "P11111:Phospho:17|18|19" in Path("ptm.unlocalized.tsv").read_text()
        assert "group_key\tprotein_ref" in Path("ptm.group_quant.matrix.tsv").read_text()
        assert "sample_id\tobserved_count" in Path(
            "ptm.group_quant.missingness.tsv"
        ).read_text()


def test_ptm_score_localization_command_emits_probability_ledgers() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        ptm_fixture_dir = FIXTURE_ROOT / "ptm"
        shutil.copy(
            ptm_fixture_dir / "localization_probability_results.tsv",
            "localization_probability_results.tsv",
        )
        Path("fragment_support.json").write_text(
            json.dumps(
                {
                    "scan=ptm-prob-001": ["b5", "y7"],
                    "scan=ptm-prob-002": ["b2"],
                }
            ),
            encoding="utf-8",
        )

        result = runner.invoke(
            cli,
            [
                "ptm",
                "score-localization",
                "localization_probability_results.tsv",
                "--fragment-support-json",
                "fragment_support.json",
                "--summary-tsv-out",
                "ptm.localization.summary.tsv",
                "--entry-tsv-out",
                "ptm.localization.entries.tsv",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["accepted_rows"] == 2
        assert (
            payload["localization_scoring"]["entries"][0]["probability_source"]
            == "reported_probability"
        )
        assert (
            payload["localization_scoring"]["entries"][0]["localization_tier"]
            == "high_confidence"
        )
        assert "reported_probability" in Path(
            "ptm.localization.entries.tsv"
        ).read_text()
        assert "localization_tier" in Path(
            "ptm.localization.entries.tsv"
        ).read_text().splitlines()[0]
        assert Path("ptm.localization.summary.tsv").read_text().splitlines()[0] == (
            "entry_count\tambiguous_entry_count\tconfident_entry_count\t"
            "high_confidence_entry_count\tsupported_entry_count\trefused_entry_count\t"
            "multi_phosphorylated_entry_count\tfragment_supported_entry_count"
        )


def test_ptm_summary_and_mapping_commands_accept_localization_probability_column() -> (
    None
):
    runner = CliRunner()
    with runner.isolated_filesystem():
        ptm_fixture_dir = FIXTURE_ROOT / "ptm"
        fasta_fixture_dir = FIXTURE_ROOT / "fasta"
        shutil.copy(
            ptm_fixture_dir / "localization_probability_results.tsv",
            "localization_probability_results.tsv",
        )
        shutil.copy(fasta_fixture_dir / "ptm_sites.fasta", "ptm_sites.fasta")

        summarize_result = runner.invoke(
            cli,
            [
                "ptm",
                "summarize",
                "localization_probability_results.tsv",
                "ptm_sites.fasta",
                "--localization-probability-column",
                "localization_probability",
            ],
        )
        map_sites_result = runner.invoke(
            cli,
            [
                "ptm",
                "map-sites",
                "localization_probability_results.tsv",
                "ptm_sites.fasta",
                "--localization-probability-column",
                "localization_probability",
            ],
        )

        assert summarize_result.exit_code == 0
        assert map_sites_result.exit_code == 0
        assert json.loads(summarize_result.output)["accepted_rows"] == 2
        assert json.loads(map_sites_result.output)["accepted_rows"] == 2


def test_ptm_quantify_sites_command_emits_site_matrix_outputs() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        ptm_fixture_dir = FIXTURE_ROOT / "ptm"
        fasta_fixture_dir = FIXTURE_ROOT / "fasta"
        shutil.copy(
            ptm_fixture_dir / "localization_results.tsv",
            "localization_results.tsv",
        )
        shutil.copy(ptm_fixture_dir / "ptm_features.tsv", "ptm_features.tsv")
        shutil.copy(fasta_fixture_dir / "ptm_sites.fasta", "ptm_sites.fasta")

        result = runner.invoke(
            cli,
            [
                "ptm",
                "quantify-sites",
                "localization_results.tsv",
                "ptm_sites.fasta",
                "ptm_features.tsv",
                "--ambiguity-policy",
                "exclude",
                "--summary-tsv-out",
                "ptm.site_quant.summary.tsv",
                "--matrix-tsv-out",
                "ptm.site_quant.matrix.tsv",
                "--missingness-tsv-out",
                "ptm.site_quant.missingness.tsv",
                "--excluded-tsv-out",
                "ptm.site_quant.excluded.tsv",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["accepted_rows"] == 8
        assert payload["feature_rows"] == 12
        assert payload["site_quantification"]["ambiguity_policy"] == "exclude"
        assert "P11111:S5:Phospho" in Path("ptm.site_quant.matrix.tsv").read_text()
        assert "P11111:S17:Phospho" not in Path(
            "ptm.site_quant.matrix.tsv"
        ).read_text()
        assert (
            "P11111:S17:Phospho\tP11111:Phospho:17|18|19"
            in Path("ptm.site_quant.excluded.tsv").read_text()
        )


def test_ptm_quantify_sites_command_emits_ambiguity_group_matrix_outputs() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        ptm_fixture_dir = FIXTURE_ROOT / "ptm"
        fasta_fixture_dir = FIXTURE_ROOT / "fasta"
        shutil.copy(
            ptm_fixture_dir / "localization_results.tsv",
            "localization_results.tsv",
        )
        shutil.copy(ptm_fixture_dir / "ptm_features.tsv", "ptm_features.tsv")
        shutil.copy(fasta_fixture_dir / "ptm_sites.fasta", "ptm_sites.fasta")

        result = runner.invoke(
            cli,
            [
                "ptm",
                "quantify-sites",
                "localization_results.tsv",
                "ptm_sites.fasta",
                "ptm_features.tsv",
                "--ambiguous-group-summary-tsv-out",
                "ptm.site_groups.summary.tsv",
                "--ambiguous-group-matrix-tsv-out",
                "ptm.site_groups.matrix.tsv",
                "--ambiguous-group-missingness-tsv-out",
                "ptm.site_groups.missingness.tsv",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["site_quantification"]["summary"]["site_row_count"] == 3
        assert (
            payload["site_quantification"]["summary"]["ambiguous_group_row_count"] == 2
        )
        assert "P11111:Phospho:17|18|19" in Path(
            "ptm.site_groups.matrix.tsv"
        ).read_text()
        assert "group_row_count" in Path("ptm.site_groups.summary.tsv").read_text()


def test_ptm_quantify_sites_command_rejects_group_exports_under_exclude_policy() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        ptm_fixture_dir = FIXTURE_ROOT / "ptm"
        fasta_fixture_dir = FIXTURE_ROOT / "fasta"
        shutil.copy(
            ptm_fixture_dir / "localization_results.tsv",
            "localization_results.tsv",
        )
        shutil.copy(ptm_fixture_dir / "ptm_features.tsv", "ptm_features.tsv")
        shutil.copy(fasta_fixture_dir / "ptm_sites.fasta", "ptm_sites.fasta")

        result = runner.invoke(
            cli,
            [
                "ptm",
                "quantify-sites",
                "localization_results.tsv",
                "ptm_sites.fasta",
                "ptm_features.tsv",
                "--ambiguity-policy",
                "exclude",
                "--ambiguous-group-matrix-tsv-out",
                "ptm.site_groups.matrix.tsv",
            ],
        )

        assert result.exit_code != 0
        assert "ambiguous-group TSV outputs require --ambiguity-policy preserve" in (
            result.output
        )


def test_ptm_estimate_occupancy_command_emits_occupancy_ledgers() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        ptm_fixture_dir = FIXTURE_ROOT / "ptm"
        fasta_fixture_dir = FIXTURE_ROOT / "fasta"
        shutil.copy(
            ptm_fixture_dir / "localization_results.tsv",
            "localization_results.tsv",
        )
        shutil.copy(ptm_fixture_dir / "ptm_features.tsv", "ptm_features.tsv")
        shutil.copy(fasta_fixture_dir / "ptm_sites.fasta", "ptm_sites.fasta")

        result = runner.invoke(
            cli,
            [
                "ptm",
                "estimate-occupancy",
                "localization_results.tsv",
                "ptm_sites.fasta",
                "ptm_features.tsv",
                "--summary-tsv-out",
                "ptm.occupancy.summary.tsv",
                "--occupancy-tsv-out",
                "ptm.occupancy.tsv",
                "--counterpart-tsv-out",
                "ptm.occupancy.counterpart.tsv",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["accepted_rows"] == 8
        assert payload["feature_rows"] == 12
        assert payload["occupancy_report"]["summary"]["entry_count"] >= 1
        assert payload["occupancy_report"]["summary"]["high_confidence_count"] >= 1
        assert any(
            entry["confidence_tier"] == "high_confidence"
            for entry in payload["occupancy_report"]["entries"]
        )
        assert "S[Phospho]PEPTIDEK" in Path("ptm.occupancy.tsv").read_text()
        assert "confidence_tier" in Path("ptm.occupancy.tsv").read_text()
        assert "counterpart_status" in Path(
            "ptm.occupancy.counterpart.tsv"
        ).read_text()


def test_ptm_differential_command_emits_site_results_and_volcano() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        ptm_fixture_dir = FIXTURE_ROOT / "ptm"
        fasta_fixture_dir = FIXTURE_ROOT / "fasta"
        shutil.copy(
            ptm_fixture_dir / "localization_results.tsv",
            "localization_results.tsv",
        )
        shutil.copy(ptm_fixture_dir / "ptm_features.tsv", "ptm_features.tsv")
        shutil.copy(ptm_fixture_dir / "ptm.design.tsv", "ptm.design.tsv")
        shutil.copy(fasta_fixture_dir / "ptm_sites.fasta", "ptm_sites.fasta")

        result = runner.invoke(
            cli,
            [
                "ptm",
                "differential",
                "localization_results.tsv",
                "ptm_sites.fasta",
                "ptm_features.tsv",
                "ptm.design.tsv",
                "--protein-correction-mode",
                "subtract_unmodified_protein",
                "--design-batch-field",
                "",
                "--results-tsv-out",
                "ptm.differential.tsv",
                "--volcano-tsv-out",
                "ptm.volcano.tsv",
                "--volcano-json-out",
                "ptm.volcano.json",
                "--volcano-svg-out",
                "ptm.volcano.svg",
                "--volcano-html-out",
                "ptm.volcano.html",
                "--volcano-top-label-count",
                "1",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["accepted_rows"] == 8
        assert payload["feature_rows"] == 12
        assert payload["protein_correction_mode"] == "subtract_unmodified_protein"
        assert payload["volcano_review"]["labeled_point_count"] == 1
        low_localization = next(
            entry
            for entry in payload["differential_report"]["entries"]
            if entry["site_key"] == "Q9DEC1:S5:Phospho"
        )
        assert low_localization["localization_tier"] == "refused"
        assert low_localization["low_localization"] is True
        corrected = next(
            entry
            for entry in payload["differential_report"]["entries"]
            if entry["site_key"] == "P11111:S5:Phospho"
        )
        assert corrected["protein_correction_status"] == "high_confidence_corrected"
        assert "P11111:S5:Phospho" in Path("ptm.differential.tsv").read_text()
        assert "localization_tier\tlow_localization" in Path(
            "ptm.differential.tsv"
        ).read_text()
        assert "plotted_log2_fold_change" in Path("ptm.volcano.tsv").read_text()
        assert Path("ptm.volcano.json").exists()
        assert Path("ptm.volcano.svg").exists()
        assert Path("ptm.volcano.html").exists()
        assert '"source_kind": "ptm"' in Path("ptm.volcano.json").read_text(
            encoding="utf-8"
        )
        assert "<svg" in Path("ptm.volcano.svg").read_text(encoding="utf-8")
        assert "Volcano plot:" in Path("ptm.volcano.html").read_text(
            encoding="utf-8"
        )


def test_ptm_differential_command_exports_paired_broken_pair_ledger() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        ptm_fixture_dir = FIXTURE_ROOT / "ptm"
        fasta_fixture_dir = FIXTURE_ROOT / "fasta"
        shutil.copy(
            ptm_fixture_dir / "localization_results.tsv",
            "localization_results.tsv",
        )
        shutil.copy(ptm_fixture_dir / "ptm_features.tsv", "ptm_features.tsv")
        shutil.copy(fasta_fixture_dir / "ptm_sites.fasta", "ptm_sites.fasta")
        Path("ptm_paired.design.tsv").write_text(
            "\n".join(
                (
                    "sample_id\tcondition\treplicate\tfraction\tspectra_file\tbatch\tpair_id",
                    "C1\tcontrol\t1\t1\tC1.raw\tbatch-a\tpair-1",
                    "C2\tcontrol\t2\t1\tC2.raw\tbatch-a\tpair-2",
                    "T1\ttreated\t1\t1\tT1.raw\tbatch-b\tpair-1",
                    "T2\ttreated\t2\t1\tT2.raw\tbatch-b\tpair-2",
                )
            ),
            encoding="utf-8",
        )

        result = runner.invoke(
            cli,
            [
                "ptm",
                "differential",
                "localization_results.tsv",
                "ptm_sites.fasta",
                "ptm_features.tsv",
                "ptm_paired.design.tsv",
                "--design-pairing-field",
                "pair_id",
                "--design-batch-field",
                "",
                "--broken-pairs-tsv-out",
                "ptm.broken.tsv",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["differential_report"]["broken_pairs"] == []
        assert any(
            entry["complete_pair_count"] == 2
            for entry in payload["differential_report"]["entries"]
        )
        assert Path("ptm.broken.tsv").read_text(encoding="utf-8").startswith(
            "condition_a\tcondition_b\tpair_id"
        )


def test_ptm_motif_enrichment_command_emits_windows_terms_and_logo() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        ptm_fixture_dir = FIXTURE_ROOT / "ptm"
        fasta_fixture_dir = FIXTURE_ROOT / "fasta"
        shutil.copy(
            ptm_fixture_dir / "localization_results.tsv",
            "localization_results.tsv",
        )
        shutil.copy(ptm_fixture_dir / "ptm_features.tsv", "ptm_features.tsv")
        shutil.copy(ptm_fixture_dir / "ptm.design.tsv", "ptm.design.tsv")
        shutil.copy(fasta_fixture_dir / "ptm_sites.fasta", "ptm_sites.fasta")

        result = runner.invoke(
            cli,
            [
                "ptm",
                "motif-enrichment",
                "localization_results.tsv",
                "ptm_sites.fasta",
                "ptm_features.tsv",
                "ptm.design.tsv",
                "--flank-size",
                "3",
                "--max-adjusted-p-value",
                "1.0",
                "--min-absolute-log2-fold-change",
                "0.5",
                "--direction",
                "upregulated",
                "--design-batch-field",
                "",
                "--background-mode",
                "whole_proteome_background",
                "--window-tsv-out",
                "ptm.motif.windows.tsv",
                "--frequency-tsv-out",
                "ptm.motif.frequency.tsv",
                "--enriched-term-tsv-out",
                "ptm.motif.terms.tsv",
                "--logo-tsv-out",
                "ptm.motif.logo.tsv",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["accepted_rows"] == 8
        assert payload["feature_rows"] == 12
        assert (
            payload["motif_enrichment_report"]["background_mode"]
            == "whole_proteome_background"
        )
        assert payload["motif_enrichment_report"]["regulated_site_count"] == 1
        assert any(
            term["residue"] == "P"
            for term in payload["motif_enrichment_report"]["enriched_terms"]
        )
        assert "whole_proteome_background" in Path("ptm.motif.windows.tsv").read_text()
        assert "centered_window" in Path("ptm.motif.windows.tsv").read_text()
        assert "regulated_frequency" in Path("ptm.motif.frequency.tsv").read_text()
        assert "exclusive_to_regulated" in Path("ptm.motif.terms.tsv").read_text()
        assert "window_role" in Path("ptm.motif.logo.tsv").read_text()


def test_ptm_annotate_sites_command_emits_mapped_unmapped_and_biology_outputs() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        ptm_fixture_dir = FIXTURE_ROOT / "ptm"
        fasta_fixture_dir = FIXTURE_ROOT / "fasta"
        shutil.copy(
            ptm_fixture_dir / "localization_results.tsv",
            "localization_results.tsv",
        )
        shutil.copy(
            ptm_fixture_dir / "ptm_site_annotations.tsv",
            "ptm_site_annotations.tsv",
        )
        shutil.copy(fasta_fixture_dir / "ptm_sites.fasta", "ptm_sites.fasta")

        result = runner.invoke(
            cli,
            [
                "ptm",
                "annotate-sites",
                "localization_results.tsv",
                "ptm_sites.fasta",
                "ptm_site_annotations.tsv",
                "--summary-tsv-out",
                "ptm.annotation.summary.tsv",
                "--mapped-tsv-out",
                "ptm.annotation.mapped.tsv",
                "--unmapped-tsv-out",
                "ptm.annotation.unmapped.tsv",
                "--function-tsv-out",
                "ptm.annotation.function.tsv",
                "--kinase-tsv-out",
                "ptm.annotation.kinase.tsv",
                "--phosphatase-tsv-out",
                "ptm.annotation.phosphatase.tsv",
                "--pathway-tsv-out",
                "ptm.annotation.pathway.tsv",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["accepted_rows"] == 8
        assert payload["annotation_rows"] == 5
        assert payload["rejected_annotation_rows"] == 1
        assert payload["target_species"] == "Homo sapiens"
        assert payload["mapping_report"]["summary"]["matched_annotation_count"] == 3
        assert "species_mismatch_count" in Path("ptm.annotation.summary.tsv").read_text()
        assert "P11111:S5:Phospho" in Path("ptm.annotation.mapped.tsv").read_text()
        assert "Mus musculus" in Path("ptm.annotation.unmapped.tsv").read_text()
        assert "activation-linked phosphosite" in Path(
            "ptm.annotation.function.tsv"
        ).read_text()
        assert "AKT1" in Path("ptm.annotation.kinase.tsv").read_text()
        assert "PPP2CA" in Path("ptm.annotation.phosphatase.tsv").read_text()
        assert "MAPK signaling" in Path("ptm.annotation.pathway.tsv").read_text()


def test_ptm_annotate_context_command_emits_site_context_outputs() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        ptm_fixture_dir = FIXTURE_ROOT / "ptm"
        fasta_fixture_dir = FIXTURE_ROOT / "fasta"
        shutil.copy(
            ptm_fixture_dir / "localization_results.tsv",
            "localization_results.tsv",
        )
        shutil.copy(
            ptm_fixture_dir / "ptm_site_context.tsv",
            "ptm_site_context.tsv",
        )
        shutil.copy(fasta_fixture_dir / "ptm_sites.fasta", "ptm_sites.fasta")

        result = runner.invoke(
            cli,
            [
                "ptm",
                "annotate-context",
                "localization_results.tsv",
                "ptm_sites.fasta",
                "ptm_site_context.tsv",
                "--summary-tsv-out",
                "ptm.context.summary.tsv",
                "--context-tsv-out",
                "ptm.context.entries.tsv",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["accepted_rows"] == 8
        assert payload["context_rows"] == 5
        assert payload["rejected_context_rows"] == 1
        assert payload["context_report"]["summary"]["outside_annotation_site_count"] == 1
        assert "outside_annotation_site_count" in Path(
            "ptm.context.summary.tsv"
        ).read_text()
        exported = Path("ptm.context.entries.tsv").read_text()
        assert "Q9DEC1:S5:Phospho" in exported
        assert "outside_provided_annotations" in exported
        assert "activation_segment" in exported


def test_ptm_regulator_enrichment_command_emits_supporting_site_ledgers() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        ptm_fixture_dir = FIXTURE_ROOT / "ptm"
        fasta_fixture_dir = FIXTURE_ROOT / "fasta"
        shutil.copy(
            ptm_fixture_dir / "localization_results.tsv",
            "localization_results.tsv",
        )
        shutil.copy(ptm_fixture_dir / "ptm_features.tsv", "ptm_features.tsv")
        shutil.copy(ptm_fixture_dir / "ptm.design.tsv", "ptm.design.tsv")
        shutil.copy(
            ptm_fixture_dir / "ptm_site_annotations.tsv",
            "ptm_site_annotations.tsv",
        )
        shutil.copy(fasta_fixture_dir / "ptm_sites.fasta", "ptm_sites.fasta")

        result = runner.invoke(
            cli,
            [
                "ptm",
                "regulator-enrichment",
                "localization_results.tsv",
                "ptm_sites.fasta",
                "ptm_features.tsv",
                "ptm.design.tsv",
                "ptm_site_annotations.tsv",
                "--design-batch-field",
                "",
                "--max-adjusted-p-value",
                "1.0",
                "--min-absolute-log2-fold-change",
                "0.5",
                "--summary-tsv-out",
                "ptm.regulator.summary.tsv",
                "--results-tsv-out",
                "ptm.regulator.results.tsv",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["accepted_rows"] == 8
        assert payload["annotation_rows"] == 5
        assert (
            payload["regulator_enrichment_report"]["summary"]["evaluated_regulator_count"]
            >= 1
        )
        assert "supporting_sites" in Path("ptm.regulator.results.tsv").read_text()
        assert "AKT1" in Path("ptm.regulator.results.tsv").read_text()
        assert "P11111:S5:Phospho" in Path("ptm.regulator.results.tsv").read_text()
        assert "evaluated_regulator_count" in Path(
            "ptm.regulator.summary.tsv"
        ).read_text()


def test_ptm_report_command_emits_full_report_bundle() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        ptm_fixture_dir = FIXTURE_ROOT / "ptm"
        fasta_fixture_dir = FIXTURE_ROOT / "fasta"
        shutil.copy(
            ptm_fixture_dir / "localization_results.tsv",
            "localization_results.tsv",
        )
        shutil.copy(ptm_fixture_dir / "ptm_features.tsv", "ptm_features.tsv")
        shutil.copy(ptm_fixture_dir / "ptm.design.tsv", "ptm.design.tsv")
        shutil.copy(
            ptm_fixture_dir / "ptm_site_annotations.tsv",
            "ptm_site_annotations.tsv",
        )
        shutil.copy(fasta_fixture_dir / "ptm_sites.fasta", "ptm_sites.fasta")
        Path("fragment_support.json").write_text(
            json.dumps(
                {
                    "scan=ptm-001": ["b5", "y7"],
                    "scan=ptm-005": ["b2"],
                }
            ),
            encoding="utf-8",
        )

        result = runner.invoke(
            cli,
            [
                "ptm",
                "report",
                "localization_results.tsv",
                "ptm_sites.fasta",
                "ptm_features.tsv",
                "ptm.design.tsv",
                "--fragment-support-json",
                "fragment_support.json",
                "--annotation-tsv",
                "ptm_site_annotations.tsv",
                "--species",
                "Homo sapiens",
                "--protein-correction-mode",
                "subtract_unmodified_protein",
                "--design-batch-field",
                "",
                "--max-adjusted-p-value",
                "1.0",
                "--min-absolute-log2-fold-change",
                "0.0",
                "--card-max-adjusted-p-value",
                "1.0",
                "--output-dir",
                "ptm_report",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["accepted_rows"] == 8
        assert payload["feature_rows"] == 12
        assert payload["design_rows"] == 4
        assert payload["report"]["summary"]["quantified_site_row_count"] == 3
        assert payload["report"]["summary"]["differential_site_count"] == 3
        assert payload["report"]["summary"]["evidence_card_count"] == 3
        assert payload["report"]["summary"]["narrative_claim_count"] == 3
        assert payload["export_manifest"]["motif_summary_included"] is True
        report_dir = Path("ptm_report")
        assert (report_dir / "ptm_site_workflow_manifest.json").exists()
        assert (report_dir / "ptm_report_manifest.json").exists()
        assert (report_dir / "ptm_site_workflow_summary.tsv").exists()
        assert (report_dir / "ptm_site_workflow_accepted_evidence.tsv").exists()
        assert (report_dir / "ptm_evidence_cards.tsv").exists()
        assert (report_dir / "ptm_evidence_claims.tsv").exists()
        assert "card_id" in (report_dir / "ptm_evidence_cards.tsv").read_text()
        assert "card_id" in (report_dir / "ptm_evidence_claims.tsv").read_text()
        assert (report_dir / "ptm_site_workflow_rejected_evidence.tsv").exists()
        assert (report_dir / "ptm_peptides.tsv").exists()
        assert (report_dir / "ptm_sites.tsv").exists()
        assert (report_dir / "ptm_localization.tsv").exists()
        assert (report_dir / "ptm_site_quant_matrix.tsv").exists()
        assert (report_dir / "ptm_differential.tsv").exists()
        assert (report_dir / "ptm_motif_terms.tsv").exists()
        assert "accepted_evidence_count" in (
            report_dir / "ptm_site_workflow_summary.tsv"
        ).read_text()
        assert "S[Phospho]PEPTIDEK" in (report_dir / "ptm_peptides.tsv").read_text()
        assert "P11111:S5:Phospho" in (report_dir / "ptm_sites.tsv").read_text()
        assert "probability_source" in (
            report_dir / "ptm_localization.tsv"
        ).read_text()
        assert "corrected_log2_fold_change" in (
            report_dir / "ptm_differential.tsv"
        ).read_text()
        assert "exclusive_to_regulated" in (
            report_dir / "ptm_motif_terms.tsv"
        ).read_text()


def test_qc_report_command_emits_json_tsv_html_manifest_and_benchmark() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        fixture_dir = FIXTURE_ROOT / "production_run"
        for name in (
            "spectra.mgf",
            "results.tsv",
            "proteins.fasta",
            "design.tsv",
            "qc_policy.json",
        ):
            shutil.copy(fixture_dir / name, name)

        result = runner.invoke(
            cli,
            [
                "qc",
                "report",
                "spectra.mgf",
                "results.tsv",
                "proteins.fasta",
                "--design",
                "design.tsv",
                "--policy",
                "qc_policy.json",
                "--tsv-out",
                "qc.tsv",
                "--html-out",
                "qc.html",
                "--manifest-out",
                "qc.manifest.json",
                "--benchmark-out",
                "qc.benchmark.json",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["run_report"]["run_id"] == "spectra"
        assert payload["run_assessment"]["policy_name"] == "production-demo-qc"
        assert payload["run_assessment"]["qc_status"] in {"pass", "caution", "fail"}
        assert isinstance(payload["run_assessment"]["status_reasons"], list)
        assert Path("qc.tsv").read_text().startswith(
            "scope\tentity_id\tqc_status\tstatus_reason_codes\tmetric_key"
        )
        assert "Bijux Proteomics QC Report" in Path("qc.html").read_text()
        assert "<strong>Status</strong>:" in Path("qc.html").read_text()
        manifest = json.loads(Path("qc.manifest.json").read_text())
        benchmark = json.loads(Path("qc.benchmark.json").read_text())
        assert manifest["document_schema"]["document_kind"] == "qc_evidence_manifest"
        assert (
            benchmark["document_schema"]["document_kind"]
            == "proteomics_performance_snapshot"
        )


def test_qc_report_command_reports_structured_policy_errors() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        fixture_dir = FIXTURE_ROOT / "production_run"
        for name in ("spectra.mgf", "results.tsv", "proteins.fasta"):
            shutil.copy(fixture_dir / name, name)
        Path("bad-policy.json").write_text("{not valid json}\n")

        result = runner.invoke(
            cli,
            [
                "qc",
                "report",
                "spectra.mgf",
                "results.tsv",
                "proteins.fasta",
                "--policy",
                "bad-policy.json",
            ],
        )

    assert result.exit_code != 0
    assert "QC_POLICY_INVALID" in result.output


def test_qc_report_command_adapts_default_policy_to_protocol_context() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        fixture_dir = FIXTURE_ROOT / "production_run"
        for name in ("spectra.mgf", "results.tsv", "proteins.fasta"):
            shutil.copy(fixture_dir / name, name)
        Path("protocol.tsv").write_text(
            "\n".join(
                (
                    "protocol_id\tdigestion_enzyme\tacquisition_type\tlabeling_method\tenrichment_type\tfractionation_mode\tdepletion_mode\tinstrument_platform",
                    "targeted-protocol\ttrypsin\ttargeted\tlabel_free\tnone\tnone\tnone\tTSQ Altis",
                )
            )
            + "\n",
            encoding="utf-8",
        )

        result = runner.invoke(
            cli,
            [
                "qc",
                "report",
                "spectra.mgf",
                "results.tsv",
                "proteins.fasta",
                "--protocol-context-tsv",
                "protocol.tsv",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["run_assessment"]["policy_name"].endswith(":targeted-protocol")


def test_qc_report_command_emits_protocol_consistency_report() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        Path("spectra.mgf").write_text(
            render_mgf(
                (
                    SpectrumModel(
                        spectrum_id="scan-001",
                        precursor_mz=500.2,
                        precursor_charge=2,
                        peaks=(SpectrumPeak(mz=500.2, intensity=1000.0),),
                    ),
                    SpectrumModel(
                        spectrum_id="scan-002",
                        precursor_mz=600.2,
                        precursor_charge=2,
                        peaks=(SpectrumPeak(mz=600.2, intensity=1100.0),),
                    ),
                )
            ),
            encoding="utf-8",
        )
        Path("results.tsv").write_text(
            "\n".join(
                (
                    "spectrum_id\tpeptide\tcharge\tscore\tproteins\tq_value",
                    "scan-001\tACDEFGK\t2\t120\tP11111\t0.01",
                    "scan-002\tCDEFG\t2\t95\tP11111\t0.02",
                )
            )
            + "\n",
            encoding="utf-8",
        )
        Path("proteins.fasta").write_text(
            ">sp|P11111|Protein 1\nKACDEFGKRAA\n",
            encoding="utf-8",
        )
        Path("protocol.tsv").write_text(
            "\n".join(
                (
                    "protocol_id\tdigestion_enzyme\tacquisition_type\tlabeling_method\tenrichment_type\tfractionation_mode\tdepletion_mode\tinstrument_platform",
                    "trypsin-protocol\ttrypsin\tdda\tlabel_free\tnone\tnone\tnone\tOrbitrap Eclipse",
                )
            )
            + "\n",
            encoding="utf-8",
        )

        result = runner.invoke(
            cli,
            [
                "qc",
                "report",
                "spectra.mgf",
                "results.tsv",
                "proteins.fasta",
                "--protocol-context-tsv",
                "protocol.tsv",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["protocol_consistency_report"]["summary"]["status"] == "blocking"
        assert payload["protocol_consistency_report"]["diagnostics"][0]["code"] == (
            "digestion_specificity_mismatch"
        )


def test_workflow_plan_command_emits_runtime_bundle_and_sidecar_outputs() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        fixture_dir = FIXTURE_ROOT / "production_run"
        for name in (
            "spectra.mgf",
            "results.tsv",
            "proteins.fasta",
            "design.tsv",
            "ms1_features.tsv",
        ):
            shutil.copy(fixture_dir / name, name)

        result = runner.invoke(
            cli,
            [
                "workflow-plan",
                "--proteins",
                "proteins.fasta",
                "--spectra",
                "spectra.mgf",
                "--identifications",
                "results.tsv",
                "--features",
                "ms1_features.tsv",
                "--design",
                "design.tsv",
                "--sample-id",
                "sample-A",
                "--search-adapter",
                "generic",
                "--dag-out",
                "workflow.dag.json",
                "--job-out",
                "workflow.slurm",
                "--checkpoint-out",
                "workflow.checkpoint.json",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["manifest"]["workflow_id"].startswith(
            "sample-a-generic-workflow"
        )
        assert payload["dag_plan"]["nodes"][0]["step_kind"] == "validate-inputs"
        assert payload["search_contract"]["adapter_kind"] == "generic"
        assert Path("workflow.dag.json").exists()
        assert "#SBATCH --job-name=" in Path("workflow.slurm").read_text()
        checkpoint = json.loads(Path("workflow.checkpoint.json").read_text())
        assert checkpoint["document_schema"]["document_kind"] == "workflow_checkpoint"


def test_workflow_validate_command_checks_runtime_integrity() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        fixture_dir = FIXTURE_ROOT / "production_run"
        for name in (
            "spectra.mgf",
            "results.tsv",
            "proteins.fasta",
            "design.tsv",
            "ms1_features.tsv",
        ):
            shutil.copy(fixture_dir / name, name)

        result = runner.invoke(
            cli,
            [
                "workflow-validate",
                "--proteins",
                "proteins.fasta",
                "--spectra",
                "spectra.mgf",
                "--identifications",
                "results.tsv",
                "--features",
                "ms1_features.tsv",
                "--design",
                "design.tsv",
                "--sample-id",
                "sample-A",
                "--search-adapter",
                "generic",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["valid"] is True
        assert "cache-manifest" in payload["checked_surfaces"]
