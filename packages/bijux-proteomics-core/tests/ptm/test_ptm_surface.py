# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.ptm import (
    PtmSiteGroupEvidenceEntry,
    build_ptm_enrichment_input,
    build_ptm_motif_background_report,
    build_ptm_motif_windows,
    build_ptm_site_ambiguity_report,
    build_ptm_site_coverage_report,
    build_ptm_site_fdr,
    build_ptm_site_group_evidence,
    build_ptm_site_table,
    estimate_ptm_site_occupancy,
    map_ptm_evidence_to_protein_sites,
    parse_ptm_localization_tsv,
    validate_ptm_site_coordinates,
)
from bijux_proteomics.quantification import parse_ms1_feature_table
from bijux_proteomics.sequences import FastaParseMode, parse_fasta_document


def _ptm_fixture(name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures" / "ptm" / name


def _fasta_fixture(name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures" / "fasta" / name


def _protein_sequences() -> dict[str, str]:
    report = parse_fasta_document(
        _fasta_fixture("ptm_sites.fasta").read_text(), mode=FastaParseMode.STRICT
    )
    return {
        record.canonical_accession: record.residues
        for record in report.accepted_records
    }


def test_ptm_localization_parser_accepts_fixture_and_candidate_sites() -> None:
    report = parse_ptm_localization_tsv(_ptm_fixture("localization_results.tsv"))

    assert report.total_rows == 8
    assert len(report.accepted_records) == 8
    first = report.accepted_records[0]
    ambiguous = next(
        record
        for record in report.accepted_records
        if record.spectrum_id == "scan=ptm-005"
    )

    assert first.modification_names == ("Phospho",)
    assert ambiguous.candidate_site_indices == (2, 3, 4)
    assert ambiguous.target_decoy_label.value == "target"


def test_ptm_localization_parser_preserves_reported_probability() -> None:
    report = parse_ptm_localization_tsv(
        _ptm_fixture("localization_probability_results.tsv")
    )

    assert report.total_rows == 2
    assert report.accepted_records[0].localization_probability == 0.982
    assert report.accepted_records[1].localization_probability == 0.61


def test_ptm_localization_parser_rejects_malformed_rows() -> None:
    report = parse_ptm_localization_tsv(
        _ptm_fixture("malformed_localization_results.tsv")
    )

    assert len(report.accepted_records) == 0
    assert len(report.rejected_rows) == 4
    codes = {issue.code for row in report.rejected_rows for issue in row.issues}
    assert {
        "missing_spectrum_id",
        "invalid_charge",
        "invalid_score",
        "missing_protein_refs",
    } <= codes


def test_ptm_site_mapping_and_table_cover_unique_and_ambiguous_sites() -> None:
    evidence = parse_ptm_localization_tsv(_ptm_fixture("localization_results.tsv"))
    mappings = map_ptm_evidence_to_protein_sites(
        evidence.accepted_records,
        protein_sequences=_protein_sequences(),
    )
    site_table = build_ptm_site_table(mappings)

    assert any(
        mapping.protein_ref == "P11111" and mapping.protein_position == 5
        for mapping in mappings
    )
    assert any(
        mapping.protein_ref == "P22222" and mapping.protein_position == 18
        for mapping in mappings
    )
    assert len(site_table) == 5
    p11111_site = next(
        entry for entry in site_table if entry.site_key == "P11111:S5:Phospho"
    )
    assert p11111_site.spectrum_count == 4
    assert p11111_site.best_q_value == 0.003

    validation = validate_ptm_site_coordinates(
        mappings,
        protein_sequences=_protein_sequences(),
    )
    assert validation.valid is True


def test_ptm_ambiguity_coverage_and_fdr_reports_are_stable() -> None:
    evidence = parse_ptm_localization_tsv(_ptm_fixture("localization_results.tsv"))
    mappings = map_ptm_evidence_to_protein_sites(
        evidence.accepted_records,
        protein_sequences=_protein_sequences(),
    )
    site_table = build_ptm_site_table(mappings)
    ambiguity = build_ptm_site_ambiguity_report(site_table)
    coverage = build_ptm_site_coverage_report(mappings)
    fdr = build_ptm_site_fdr(site_table, threshold=0.1)

    assert len(ambiguity) == 2
    assert all(entry.candidate_positions for entry in ambiguity)
    assert any(entry.site_key == "P11111:S5:Phospho" for entry in coverage)
    decoy = next(entry for entry in fdr.entries if entry.site_key.startswith("Q9DEC1"))
    target = next(
        entry for entry in fdr.entries if entry.site_key == "P11111:S5:Phospho"
    )
    assert target.accepted is True
    assert decoy.accepted is False


def test_ptm_site_group_evidence_preserves_unresolved_candidate_sets() -> None:
    evidence = parse_ptm_localization_tsv(_ptm_fixture("localization_results.tsv"))
    mappings = map_ptm_evidence_to_protein_sites(
        evidence.accepted_records,
        protein_sequences=_protein_sequences(),
    )
    site_table = build_ptm_site_table(mappings)
    groups = build_ptm_site_group_evidence(site_table)

    assert any(isinstance(entry, PtmSiteGroupEvidenceEntry) for entry in groups)
    unresolved = next(entry for entry in groups if entry.unresolved)
    assert len(unresolved.candidate_positions) > 1
    assert unresolved.site_keys


def test_ptm_occupancy_motif_and_enrichment_outputs_follow_fixture_signal() -> None:
    evidence = parse_ptm_localization_tsv(_ptm_fixture("localization_results.tsv"))
    mappings = map_ptm_evidence_to_protein_sites(
        evidence.accepted_records,
        protein_sequences=_protein_sequences(),
    )
    site_table = build_ptm_site_table(mappings)
    features = parse_ms1_feature_table(_ptm_fixture("ptm_features.tsv"))
    occupancy = estimate_ptm_site_occupancy(
        site_table,
        feature_records=features.accepted_records,
    )
    motifs = build_ptm_motif_windows(
        site_table, protein_sequences=_protein_sequences(), flank_size=3
    )
    enrichment = build_ptm_enrichment_input(
        site_table, protein_sequences=_protein_sequences()
    )
    background = build_ptm_motif_background_report(
        site_table,
        protein_sequences=_protein_sequences(),
    )

    c1 = next(
        entry
        for entry in occupancy
        if entry.site_key == "P11111:S5:Phospho" and entry.sample_id == "C1"
    )
    t2 = next(
        entry
        for entry in occupancy
        if entry.site_key == "P11111:S5:Phospho" and entry.sample_id == "T2"
    )
    motif = next(entry for entry in motifs if entry.site_key == "P11111:S5:Phospho")

    assert c1.occupancy_fraction == 0.12
    assert t2.occupancy_fraction == 0.79
    assert c1.uncertainty.value == "none"
    assert motif.window == "AAASPEP"
    assert "P11111:S5:Phospho" in enrichment.site_ids
    assert "P11111:S5" in enrichment.background_ids
    assert background.total_foreground_sites >= 1
    assert (
        next(
            entry for entry in background.entries if entry.residue == "S"
        ).background_site_count
        >= 1
    )

    ambiguous = next(
        entry for entry in occupancy if entry.uncertainty.value == "ambiguous_site"
    )
    assert ambiguous.uncertainty.value == "ambiguous_site"
