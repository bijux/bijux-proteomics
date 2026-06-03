# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.benchmarks.scientific_fixture_corpus import (
    ScientificFixtureCaseKind,
    ScientificFixtureManifest,
    get_scientific_fixture_manifest,
)
from bijux_proteomics.identification import (
    SearchResultColumnMapping,
    build_contaminant_peptide_match_report,
    build_protein_coverage_review_report,
    filter_psms_by_fdr,
    parse_psm_tsv,
    select_best_psm_per_spectrum,
)
from bijux_proteomics.sequences import (
    DuplicateAccessionPolicy,
    FastaParseMode,
    deduplicate_fasta_records,
    parse_fasta_document,
    validate_target_decoy_database,
)

REPO_ROOT = Path(__file__).resolve().parents[4]


def _repo_path(repo_relative_path: str) -> Path:
    return REPO_ROOT / repo_relative_path


def _asset_path(manifest: ScientificFixtureManifest, role: str) -> Path:
    asset = next(asset for asset in manifest.input_assets if asset.role == role)
    return _repo_path(asset.repo_relative_path)


def _expected_count(
    manifest: ScientificFixtureManifest,
    *,
    asset_role: str,
    accepted: bool,
) -> int:
    expectations = manifest.accepted_rows if accepted else manifest.rejected_rows
    return next(
        expectation.expected_count
        for expectation in expectations
        if expectation.asset_role == asset_role
    )


def _psm_mapping() -> SearchResultColumnMapping:
    return SearchResultColumnMapping(
        spectrum_id="spectrum_id",
        peptide="peptide",
        charge="charge",
        score="score",
        q_value="q_value",
        protein_refs="proteins",
    )


def test_shared_peptide_fixture_keeps_non_unique_protein_support_visible() -> None:
    manifest = get_scientific_fixture_manifest(
        ScientificFixtureCaseKind.SHARED_PEPTIDES
    )
    psm_report = parse_psm_tsv(
        _asset_path(manifest, "psm_table"), mapping=_psm_mapping()
    )
    fasta_report = parse_fasta_document(
        _asset_path(manifest, "protein_fasta").read_text(),
        mode=FastaParseMode.STRICT,
    )
    accepted = filter_psms_by_fdr(psm_report.accepted_records, threshold=0.05)
    protein_sequences = {
        record.canonical_accession: record.residues
        for record in fasta_report.accepted_records
    }
    coverage = build_protein_coverage_review_report(
        accepted,
        protein_sequences=protein_sequences,
        threshold=0.05,
    )

    assert len(psm_report.accepted_records) == _expected_count(
        manifest, asset_role="psm_table", accepted=True
    )
    assert len(psm_report.rejected_rows) == _expected_count(
        manifest, asset_role="psm_table", accepted=False
    )
    assert len(fasta_report.accepted_records) == _expected_count(
        manifest, asset_role="protein_fasta", accepted=True
    )
    assert coverage.summary.proteins_with_shared_peptides == 3
    assert coverage.summary.proteins_with_unique_peptides == 2
    p22222 = next(entry for entry in coverage.entries if entry.protein_ref == "P22222")
    assert p22222.shared_peptides == ("GLYGLYK", "SHAREDK")


def test_isoform_fixture_preserves_distinct_isoform_identity_under_deduplication() -> (
    None
):
    manifest = get_scientific_fixture_manifest(ScientificFixtureCaseKind.ISOFORMS)
    report = parse_fasta_document(
        _asset_path(manifest, "isoform_fasta").read_text(),
        mode=FastaParseMode.PERMISSIVE,
        duplicate_accession_policy=DuplicateAccessionPolicy.ACCEPT_WITH_WARNING,
    )
    deduplicated, dedup_report = deduplicate_fasta_records(report.accepted_records)

    assert len(report.accepted_records) == _expected_count(
        manifest, asset_role="isoform_fasta", accepted=True
    )
    assert len(report.rejected_records) == _expected_count(
        manifest, asset_role="isoform_fasta", accepted=False
    )
    assert report.duplicate_accessions == ("uniprot:P12345-2",)
    assert len(deduplicated) == 2
    assert {record.isoform for record in deduplicated} == {None, 2}
    assert dedup_report.duplicate_accessions == ("sp|P12345-2|PROT_HUMAN_DUP",)


def test_contaminant_fixture_separates_pure_and_mixed_carryover() -> None:
    manifest = get_scientific_fixture_manifest(ScientificFixtureCaseKind.CONTAMINANTS)
    psm_report = parse_psm_tsv(
        _asset_path(manifest, "psm_table"), mapping=_psm_mapping()
    )
    contaminant_report = build_contaminant_peptide_match_report(
        psm_report.accepted_records
    )
    contaminant_fasta = parse_fasta_document(
        _asset_path(manifest, "contaminant_fasta").read_text(),
        mode=FastaParseMode.STRICT,
    )

    assert len(psm_report.accepted_records) == _expected_count(
        manifest, asset_role="psm_table", accepted=True
    )
    assert len(contaminant_fasta.accepted_records) == _expected_count(
        manifest, asset_role="contaminant_fasta", accepted=True
    )
    assert contaminant_report.contaminant_psm_count == 2
    assert contaminant_report.pure_contaminant_psm_count == 1
    assert contaminant_report.mixed_reference_psm_count == 1
    assert contaminant_report.contaminant_protein_counts == {
        "CON__K1C10_HUMAN": 1,
        "CON__TRYP_PIG": 1,
    }


def test_decoy_fixture_proves_complete_target_decoy_pairs() -> None:
    manifest = get_scientific_fixture_manifest(ScientificFixtureCaseKind.DECOYS)
    report = parse_fasta_document(
        _asset_path(manifest, "target_decoy_fasta").read_text(),
        mode=FastaParseMode.STRICT,
    )
    validation = validate_target_decoy_database(report.accepted_records)

    assert len(report.accepted_records) == _expected_count(
        manifest, asset_role="target_decoy_fasta", accepted=True
    )
    assert len(report.rejected_records) == _expected_count(
        manifest, asset_role="target_decoy_fasta", accepted=False
    )
    assert validation.valid is True
    assert validation.target_count == 2
    assert validation.decoy_count == 2
    assert validation.missing_decoys == ()


def test_chimeric_spectrum_fixture_keeps_competing_psms_reviewable() -> None:
    manifest = get_scientific_fixture_manifest(
        ScientificFixtureCaseKind.CHIMERIC_SPECTRUM
    )
    report = parse_psm_tsv(_asset_path(manifest, "psm_table"), mapping=_psm_mapping())
    selected = select_best_psm_per_spectrum(report.accepted_records)

    assert len(report.accepted_records) == _expected_count(
        manifest, asset_role="psm_table", accepted=True
    )
    assert len(report.rejected_rows) == _expected_count(
        manifest, asset_role="psm_table", accepted=False
    )
    assert len(selected) == 2
    best_scan_2001 = next(
        record for record in selected if record.spectrum_id == "scan=2001"
    )
    assert best_scan_2001.canonical_peptide == "PEPTIDER"
    assert best_scan_2001.score == 47.0
