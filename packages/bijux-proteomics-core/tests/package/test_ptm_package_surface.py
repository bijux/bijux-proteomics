# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

import bijux_proteomics.ptm as ptm
from bijux_proteomics.io.formats import parse_experimental_design_table
from bijux_proteomics.quantification import parse_ms1_feature_table
from bijux_proteomics.sequences import FastaParseMode, parse_fasta_document


def _ptm_fixture(name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures" / "ptm" / name


def _fasta_fixture(name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures" / "fasta" / name


def _protein_sequences() -> dict[str, str]:
    report = parse_fasta_document(
        _fasta_fixture("ptm_sites.fasta").read_text(),
        mode=FastaParseMode.STRICT,
    )
    return {
        record.canonical_accession: record.residues
        for record in report.accepted_records
    }


def test_ptm_package_exports_protein_site_mapping_owner_surface() -> None:
    evidence = ptm.parse_ptm_localization_tsv(_ptm_fixture("localization_results.tsv"))
    report = ptm.build_ptm_protein_site_mapping_report(
        evidence.accepted_records,
        protein_sequences=_protein_sequences(),
    )
    rendered = ptm.render_ptm_unmapped_peptide_tsv(report.unmapped_peptides)

    assert hasattr(ptm, "build_ptm_protein_site_mapping_report")
    assert hasattr(ptm, "render_ptm_unmapped_peptide_tsv")
    assert len(report.ambiguous_mappings) == 4
    assert rendered.splitlines()[0].startswith(
        "spectrum_id\tsample_id\tlocalized_peptide"
    )


def test_ptm_package_exports_localization_scoring_owner_surface() -> None:
    evidence = ptm.parse_ptm_localization_tsv(
        _ptm_fixture("localization_probability_results.tsv")
    )
    report = ptm.build_ptm_localization_scoring_report(evidence.accepted_records)
    rendered = ptm.render_ptm_localization_scoring_entry_tsv(report)

    assert hasattr(ptm, "build_ptm_localization_scoring_report")
    assert hasattr(ptm, "render_ptm_localization_scoring_summary_tsv")
    assert hasattr(ptm, "PtmLocalizationConfidenceTier")
    assert report.high_confidence_entry_count == 1
    assert "localization_tier" in rendered.splitlines()[0]


def test_ptm_package_exports_site_quantification_owner_surface() -> None:
    evidence = ptm.parse_ptm_localization_tsv(_ptm_fixture("localization_results.tsv"))
    mappings = ptm.map_ptm_evidence_to_protein_sites(
        evidence.accepted_records,
        protein_sequences=_protein_sequences(),
    )
    site_table = ptm.build_ptm_site_table(mappings)
    features = parse_ms1_feature_table(_ptm_fixture("ptm_features.tsv"))
    report = ptm.build_ptm_site_quantification_report(
        site_table,
        feature_records=features.accepted_records,
    )

    assert hasattr(ptm, "build_ptm_site_quantification_report")
    assert hasattr(ptm, "render_ptm_site_quant_matrix_tsv")
    assert report.summary.site_row_count == 3
    assert report.summary.ambiguous_group_row_count == 2
    assert report.ambiguous_group_quantification is not None


def test_ptm_package_exports_occupancy_owner_surface() -> None:
    evidence = ptm.parse_ptm_localization_tsv(_ptm_fixture("localization_results.tsv"))
    mappings = ptm.map_ptm_evidence_to_protein_sites(
        evidence.accepted_records,
        protein_sequences=_protein_sequences(),
    )
    site_table = ptm.build_ptm_site_table(mappings)
    features = parse_ms1_feature_table(_ptm_fixture("ptm_features.tsv"))
    report = ptm.build_ptm_site_occupancy_report(
        site_table,
        feature_records=features.accepted_records,
    )

    assert hasattr(ptm, "build_ptm_site_occupancy_report")
    assert hasattr(ptm, "PtmOccupancyConfidenceTier")
    target = next(
        entry
        for entry in report.entries
        if entry.site_key == "P11111:S5:Phospho" and entry.sample_id == "C1"
    )
    assert target.confidence_tier.value == "high_confidence"
    assert target.unmodified_feature_count == 1


def test_ptm_package_exports_differential_owner_surface() -> None:
    evidence = ptm.parse_ptm_localization_tsv(_ptm_fixture("localization_results.tsv"))
    mappings = ptm.map_ptm_evidence_to_protein_sites(
        evidence.accepted_records,
        protein_sequences=_protein_sequences(),
    )
    site_table = ptm.build_ptm_site_table(mappings)
    features = parse_ms1_feature_table(_ptm_fixture("ptm_features.tsv"))
    site_quantification = ptm.build_ptm_site_quantification_report(
        site_table,
        feature_records=features.accepted_records,
    )
    design = parse_experimental_design_table(_ptm_fixture("ptm.design.tsv"))
    report = ptm.build_ptm_differential_analysis_report(
        site_quantification,
        design.accepted_entries,
        batch_field="",
    )

    assert hasattr(ptm, "build_ptm_differential_analysis_report")
    assert hasattr(ptm, "render_ptm_site_differential_tsv")
    corrected = next(
        entry
        for entry in report.differential_report.entries
        if entry.site_key == "P11111:S5:Phospho"
    )
    low_localization = next(
        entry
        for entry in report.differential_report.entries
        if entry.site_key == "Q9DEC1:S5:Phospho"
    )
    assert corrected.protein_correction_status == "not_requested"
    assert low_localization.localization_tier.value == "refused"
    assert low_localization.low_localization is True
