# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.workflow import (
    AdvancedTmtCompressionStatus,
    AdvancedTmtPeptideDisposition,
    AdvancedTmtProteinConfidenceStatus,
    AdvancedTmtWorkflowConfig,
    run_advanced_tmt_workflow,
)


def _multiplex_fixture(name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures" / "multiplex" / name


def _write_mixed_support_fixture(path: Path) -> None:
    path.write_text(
        "\n".join(
            (
                "id\tModified sequence\tLeading proteins\tExperiment\tIsolation interference [%]\tReporter intensity corrected 126\tReporter intensity corrected 127N\tReporter intensity corrected 128N",
                "1\tPEPTIDE\tP001\tplex-a\t8\t1200\t2400\t6000",
                "2\tDPEPTIDE\tP001\tplex-a\t35\t900\t920\t4100",
                "3\tPEPTIDE\tP001\tplex-b\t12\t1500\t3000\t6500",
                "4\tDPEPTIDE\tP001\tplex-b\t42\t1000\t1030\t4300",
            )
        )
        + "\n",
        encoding="utf-8",
    )


def test_run_advanced_tmt_workflow_excludes_proteins_supported_only_by_high_interference_peptides(
    tmp_path: Path,
) -> None:
    report = run_advanced_tmt_workflow(
        AdvancedTmtWorkflowConfig(
            result_tsv_path=_multiplex_fixture("maxquant_tmt_interference.tsv"),
            design_tsv_path=_multiplex_fixture("tmt.design.tsv"),
            output_dir=tmp_path / "advanced_tmt_review",
            control_channel="126",
            condition_a="control",
            condition_b="treatment",
        )
    )

    output_dir = tmp_path / "advanced_tmt_review"
    peptide_confidence_tsv = (
        output_dir / report.manifest.artifacts.peptide_confidence_tsv
    ).read_text(encoding="utf-8")
    evidence_card_tsv = (
        output_dir / report.manifest.artifacts.evidence_card_tsv
    ).read_text(encoding="utf-8")
    rejected_evidence_tsv = (
        output_dir / report.manifest.artifacts.rejected_evidence_tsv
    ).read_text(encoding="utf-8")
    summary_tsv = (
        output_dir / report.manifest.artifacts.summary_tsv
    ).read_text(encoding="utf-8")

    assert report.summary.high_interference_peptide_count == 2
    assert report.summary.excluded_peptide_count == 2
    assert report.summary.excluded_protein_count == 1
    assert report.manifest.artifacts.reporter_import_summary_tsv == "tmt_reporter_import_summary.tsv"
    assert report.manifest.artifacts.normalization_summary_tsv == "tmt_normalization_summary.tsv"
    assert report.manifest.artifacts.validation_summary_tsv == "tmt_validation_summary.tsv"
    assert report.evidence_cards[0].confidence_status is AdvancedTmtProteinConfidenceStatus.SUPPORTED
    assert report.evidence_cards[1].confidence_status is AdvancedTmtProteinConfidenceStatus.EXCLUDED_DUE_TO_INTERFERENCE
    assert all(
        entry.disposition is AdvancedTmtPeptideDisposition.EXCLUDED_DUE_TO_INTERFERENCE
        for entry in report.peptide_confidence_entries
        if entry.protein_id == "P002"
    )
    assert "P002\tDPEPTIDE" in peptide_confidence_tsv
    assert "excluded_due_to_interference" in peptide_confidence_tsv
    assert "P002\tP002\texcluded_due_to_interference" in evidence_card_tsv
    assert "excluded_due_to_interference" in rejected_evidence_tsv
    assert "excluded_protein_count\t1" in summary_tsv
    assert (output_dir / report.manifest.artifacts.filtered_interference_tsv).exists()
    assert (output_dir / report.manifest.artifacts.differential_results_tsv).exists()


def test_run_advanced_tmt_workflow_downgrades_mixed_support_and_flags_possible_compression(
    tmp_path: Path,
) -> None:
    mixed_result_tsv = tmp_path / "mixed_tmt_support.tsv"
    _write_mixed_support_fixture(mixed_result_tsv)

    report = run_advanced_tmt_workflow(
        AdvancedTmtWorkflowConfig(
            result_tsv_path=mixed_result_tsv,
            design_tsv_path=_multiplex_fixture("tmt.design.tsv"),
            output_dir=tmp_path / "advanced_tmt_mixed_support",
            control_channel="126",
            condition_a="control",
            condition_b="treatment",
        )
    )

    output_dir = tmp_path / "advanced_tmt_mixed_support"
    peptide_confidence_tsv = (
        output_dir / report.manifest.artifacts.peptide_confidence_tsv
    ).read_text(encoding="utf-8")
    compression_tsv = (
        output_dir / report.manifest.artifacts.protein_compression_tsv
    ).read_text(encoding="utf-8")
    evidence_card_tsv = (
        output_dir / report.manifest.artifacts.evidence_card_tsv
    ).read_text(encoding="utf-8")
    rejected_evidence_tsv = (
        output_dir / report.manifest.artifacts.rejected_evidence_tsv
    ).read_text(encoding="utf-8")

    assert report.summary.downgraded_protein_count == 1
    assert report.summary.excluded_protein_count == 0
    assert report.summary.compression_risk_count == 1
    assert all(
        entry.disposition is not AdvancedTmtPeptideDisposition.EXCLUDED_DUE_TO_INTERFERENCE
        for entry in report.peptide_confidence_entries
    )
    assert any(
        entry.disposition is AdvancedTmtPeptideDisposition.DOWNGRADED_BY_INTERFERENCE
        for entry in report.peptide_confidence_entries
        if entry.peptide_sequence == "DPEPTIDE"
    )
    assert report.protein_compression_entries[0].compression_status is (
        AdvancedTmtCompressionStatus.POSSIBLE_INTERFERENCE_COMPRESSION
    )
    assert report.protein_compression_entries[0].attenuation_delta is not None
    assert report.protein_compression_entries[0].attenuation_delta > 0.25
    assert report.evidence_cards[0].confidence_status is (
        AdvancedTmtProteinConfidenceStatus.DOWNGRADED_BY_INTERFERENCE
    )
    assert "downgraded_by_interference" in peptide_confidence_tsv
    assert "possible_interference_compression" in compression_tsv
    assert "P001\tP001\tdowngraded_by_interference" in evidence_card_tsv
    assert "row_number" in rejected_evidence_tsv
