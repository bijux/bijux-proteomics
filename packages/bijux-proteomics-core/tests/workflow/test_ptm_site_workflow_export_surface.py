# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.ptm import (
    PtmEvidenceCardPolicy,
    PtmProteinCorrectionMode,
    PtmRegulatorEnrichmentPolicy,
)
from bijux_proteomics.workflow import (
    build_ptm_site_workflow_bundle,
    export_ptm_site_workflow_bundle,
)


def _workflow_fixture(name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures" / "workflow" / name


def _ptm_fixture(name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures" / "ptm" / name


def _fasta_fixture(name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures" / "fasta" / name


def test_ptm_site_workflow_export_writes_evidence_review_and_report_assets(
    tmp_path: Path,
) -> None:
    report = build_ptm_site_workflow_bundle(
        _ptm_fixture("localization_results.tsv"),
        _fasta_fixture("ptm_sites.fasta"),
        feature_tsv_path=_ptm_fixture("ptm_features.tsv"),
        design_path=_ptm_fixture("ptm.design.tsv"),
        annotation_tsv_path=_ptm_fixture("ptm_site_annotations.tsv"),
        annotation_target_species="Homo sapiens",
        protein_correction_mode=PtmProteinCorrectionMode.SUBTRACT_UNMODIFIED_PROTEIN,
        batch_field="",
        condition_a="control",
        condition_b="treated",
        regulator_enrichment_policy=PtmRegulatorEnrichmentPolicy(
            max_adjusted_p_value=1.0,
            min_absolute_log2_fold_change=0.0,
        ),
        evidence_card_policy=PtmEvidenceCardPolicy(max_adjusted_p_value=1.0),
    )

    manifest = export_ptm_site_workflow_bundle(report, tmp_path / "ptm_site_report")
    output_dir = tmp_path / "ptm_site_report"

    assert (output_dir / manifest.artifacts.summary_tsv).exists()
    assert (output_dir / manifest.artifacts.accepted_evidence_tsv).exists()
    assert (output_dir / manifest.artifacts.rejected_evidence_tsv).exists()
    assert (output_dir / manifest.artifacts.ptm_report_manifest_json).exists()
    assert "accepted_evidence_count" in (
        output_dir / manifest.artifacts.summary_tsv
    ).read_text(encoding="utf-8")
    assert "localized_peptide" in (
        output_dir / manifest.artifacts.accepted_evidence_tsv
    ).read_text(encoding="utf-8")
    assert "row_number\tissue_codes\tissue_messages\traw_fields" == (
        output_dir / manifest.artifacts.rejected_evidence_tsv
    ).read_text(encoding="utf-8").splitlines()[0]
    assert (output_dir / manifest.ptm_report_manifest.artifacts.peptide_tsv).exists()
    assert (output_dir / manifest.ptm_report_manifest.artifacts.site_tsv).exists()
    assert (
        output_dir / manifest.ptm_report_manifest.artifacts.site_group_summary_tsv
    ).exists()
    assert (
        output_dir / manifest.ptm_report_manifest.artifacts.site_group_matrix_tsv
    ).exists()
    assert (
        output_dir / manifest.ptm_report_manifest.artifacts.site_group_missingness_tsv
    ).exists()
    assert (output_dir / manifest.ptm_report_manifest.artifacts.differential_tsv).exists()
    assert (
        output_dir / manifest.ptm_report_manifest.artifacts.regulator_enrichment_tsv
    ).exists()
    assert (output_dir / manifest.ptm_report_manifest.artifacts.evidence_card_tsv).exists()
    assert (output_dir / manifest.ptm_report_manifest.artifacts.evidence_claim_tsv).exists()
