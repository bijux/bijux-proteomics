# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.benchmarks.scientific_fixture_corpus import (
    ScientificFixtureCaseKind,
    ScientificFixtureManifest,
    get_scientific_fixture_manifest,
)
from bijux_proteomics.ptm import (
    build_ptm_ambiguity_review_report,
    build_ptm_localization_scoring_report,
    build_ptm_site_table,
    map_ptm_evidence_to_protein_sites,
    parse_ptm_localization_tsv,
)
from bijux_proteomics.sequences import FastaParseMode, parse_fasta_document

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


def test_ambiguous_ptm_fixture_preserves_localized_and_unlocalized_site_meaning() -> (
    None
):
    manifest = get_scientific_fixture_manifest(
        ScientificFixtureCaseKind.AMBIGUOUS_PTM_SITES
    )
    evidence = parse_ptm_localization_tsv(
        _asset_path(manifest, "ptm_localization_table")
    )
    fasta_report = parse_fasta_document(
        _asset_path(manifest, "protein_fasta").read_text(),
        mode=FastaParseMode.STRICT,
    )
    protein_sequences = {
        record.canonical_accession: record.residues
        for record in fasta_report.accepted_records
    }
    mappings = map_ptm_evidence_to_protein_sites(
        evidence.accepted_records,
        protein_sequences=protein_sequences,
    )
    site_table = build_ptm_site_table(mappings)
    localization = build_ptm_localization_scoring_report(
        evidence.accepted_records,
        fragment_ion_support_by_spectrum={
            "scan=ptm-001": ("b5", "y7"),
            "scan=ptm-005": ("b2",),
        },
    )
    review = build_ptm_ambiguity_review_report(
        site_table,
        localization_scoring_report=localization,
        protein_sequences=protein_sequences,
    )

    assert len(evidence.accepted_records) == _expected_count(
        manifest, asset_role="ptm_localization_table", accepted=True
    )
    assert len(evidence.rejected_rows) == _expected_count(
        manifest, asset_role="ptm_localization_table", accepted=False
    )
    assert len(fasta_report.accepted_records) == _expected_count(
        manifest, asset_role="protein_fasta", accepted=True
    )
    assert len(fasta_report.rejected_records) == _expected_count(
        manifest, asset_role="protein_fasta", accepted=False
    )
    assert review.summary.localized_site_count == 3
    assert review.summary.unlocalized_group_count == 2
    ambiguous = next(
        entry
        for entry in review.unlocalized_groups
        if entry.group_key == "P11111:Phospho:17|18|19"
    )
    assert ambiguous.possible_residues == ("S", "T", "Y")
    assert ambiguous.localization_probability == 0.715
