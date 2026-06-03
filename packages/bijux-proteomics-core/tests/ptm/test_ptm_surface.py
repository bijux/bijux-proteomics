# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.ptm import (
    PtmMotifBackgroundMode,
    PtmSiteGroupEvidenceEntry,
    build_ptm_enrichment_input,
    build_ptm_motif_background_report,
    build_ptm_motif_windows,
    build_ptm_protein_site_mapping_report,
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


def test_ptm_localization_parser_keeps_multiple_modifications_as_separate_site_candidates() -> (
    None
):
    report = parse_ptm_localization_tsv(_ptm_fixture("multi_localization_results.tsv"))

    assert report.total_rows == 1
    assert len(report.accepted_records) == 1
    record = report.accepted_records[0]

    assert record.modification_names == ("Phospho", "Phospho")
    assert tuple(
        (site.modification_name, site.residue, site.peptide_site_index)
        for site in record.site_candidates
    ) == (
        ("Phospho", "S", 2),
        ("Phospho", "Y", 4),
    )
    assert all(site.candidate_site_indices for site in record.site_candidates)


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


def test_ptm_localization_parser_rejects_out_of_range_q_values(
    tmp_path: Path,
) -> None:
    evidence_path = tmp_path / "ptm_invalid_q.tsv"
    evidence_path.write_text(
        "\n".join(
            (
                "spectrum_id\tpeptide\tcharge\tscore\tproteins\tlocalization_score\tq_value",
                "scan=1\tPES[Phospho]TIDE\t2\t100\tP11111\t15\t1.2",
            )
        )
        + "\n",
        encoding="utf-8",
    )

    report = parse_ptm_localization_tsv(evidence_path)

    assert report.accepted_records == ()
    assert len(report.rejected_rows) == 1
    assert report.rejected_rows[0].issues[0].code == "invalid_q_value"


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


def test_ptm_site_mapping_keeps_multi_modified_candidates_separate() -> None:
    evidence = parse_ptm_localization_tsv(
        _ptm_fixture("multi_localization_results.tsv")
    )
    mappings = map_ptm_evidence_to_protein_sites(
        evidence.accepted_records,
        protein_sequences=_protein_sequences(),
    )

    assert {
        (mapping.protein_ref, mapping.peptide_site_index, mapping.protein_position)
        for mapping in mappings
    } == {
        ("P11111", 2, 17),
        ("P11111", 4, 19),
        ("P22222", 2, 4),
        ("P22222", 4, 6),
    }


def test_ptm_mapping_report_separates_exact_ambiguous_and_unmapped_ledgers() -> None:
    evidence = parse_ptm_localization_tsv(_ptm_fixture("localization_results.tsv"))
    report = build_ptm_protein_site_mapping_report(
        evidence.accepted_records,
        protein_sequences=_protein_sequences(),
    )

    assert len(report.mappings) == 10
    assert len(report.exact_mappings) == 6
    assert len(report.ambiguous_mappings) == 4
    assert report.unmapped_peptides == ()
    assert all(mapping.ambiguous is False for mapping in report.exact_mappings)
    assert all(mapping.ambiguous is True for mapping in report.ambiguous_mappings)
    assert {mapping.localized_peptide for mapping in report.ambiguous_mappings} == {
        "AS[Phospho]TYK"
    }


def test_ptm_mapping_report_keeps_shared_peptides_exact_when_one_fasta_mapping_survives(
    tmp_path: Path,
) -> None:
    evidence_path = tmp_path / "shared_unique.tsv"
    evidence_path.write_text(
        "\n".join(
            (
                "sample_id\tspectrum_id\tpeptide\tcharge\tscore\tq_value\tproteins\tlocalization_score\tcandidate_sites\tdecoy_label",
                "C1\tscan=shared-unique\tS[Phospho]PEPTIDEK\t2\t110.0\t0.005\tP11111;P40404\t0.990\t1\ttarget",
            )
        )
        + "\n",
        encoding="utf-8",
    )

    evidence = parse_ptm_localization_tsv(evidence_path)
    report = build_ptm_protein_site_mapping_report(
        evidence.accepted_records,
        protein_sequences=_protein_sequences(),
    )

    assert len(report.exact_mappings) == 1
    assert report.ambiguous_mappings == ()
    assert report.unmapped_peptides == ()
    mapping = report.exact_mappings[0]
    assert mapping.shared_peptide is True
    assert mapping.ambiguous is False
    assert mapping.protein_ref == "P11111"


def test_ptm_mapping_report_preserves_unmapped_peptides_when_fasta_cannot_place_site(
    tmp_path: Path,
) -> None:
    evidence_path = tmp_path / "unmapped.tsv"
    evidence_path.write_text(
        "\n".join(
            (
                "sample_id\tspectrum_id\tpeptide\tcharge\tscore\tq_value\tproteins\tlocalization_score\tcandidate_sites\tdecoy_label",
                "C1\tscan=unmapped\tS[Phospho]PEPTIDEK\t2\t110.0\t0.005\tP40404\t0.990\t1\ttarget",
            )
        )
        + "\n",
        encoding="utf-8",
    )

    evidence = parse_ptm_localization_tsv(evidence_path)
    report = build_ptm_protein_site_mapping_report(
        evidence.accepted_records,
        protein_sequences=_protein_sequences(),
    )

    assert report.mappings == ()
    assert report.exact_mappings == ()
    assert report.ambiguous_mappings == ()
    assert len(report.unmapped_peptides) == 1
    unmapped = report.unmapped_peptides[0]
    assert unmapped.reason_code == "missing_protein_sequence"
    assert unmapped.localized_peptide == "S[Phospho]PEPTIDEK"


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
    observed_background = build_ptm_motif_background_report(
        site_table,
        protein_sequences=_protein_sequences(),
        background_mode=PtmMotifBackgroundMode.OBSERVED_SITE_BACKGROUND.value,
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
    assert c1.confidence_tier.value == "high_confidence"
    assert c1.uncertainty.value == "none"
    assert motif.window == "AAASPEP"
    assert "P11111:S5:Phospho" in enrichment.site_ids
    assert "P11111:S5" in enrichment.background_ids
    assert background.total_foreground_sites >= 1
    assert background.background_mode == "whole_proteome_background"
    assert observed_background.background_mode == "observed_site_background"
    assert (
        background.total_background_sites > observed_background.total_background_sites
    )
    assert (
        next(
            entry for entry in background.entries if entry.residue == "S"
        ).background_site_count
        >= 1
    )

    ambiguous = next(
        entry for entry in occupancy if entry.uncertainty.value == "ambiguous_site"
    )
    assert ambiguous.confidence_tier.value == "ambiguous_site"
    assert ambiguous.uncertainty.value == "ambiguous_site"
