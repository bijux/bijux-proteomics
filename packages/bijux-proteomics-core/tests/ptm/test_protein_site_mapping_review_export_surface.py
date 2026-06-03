# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.domain.records import ImportedEvidenceProvenance
from bijux_proteomics.identification import TargetDecoyLabel
from bijux_proteomics.ptm import (
    PtmProteinSiteMapping,
    build_ptm_site_ambiguity_report,
    build_ptm_site_coverage_report,
    build_ptm_site_table,
    map_ptm_evidence_to_protein_sites,
    parse_ptm_localization_tsv,
    render_ptm_coordinate_validation_tsv,
    render_ptm_site_ambiguity_tsv,
    render_ptm_site_coverage_tsv,
    validate_ptm_site_coordinates,
)
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


def test_ptm_review_renderers_keep_ambiguity_and_coverage_explicit() -> None:
    evidence = parse_ptm_localization_tsv(_ptm_fixture("localization_results.tsv"))
    mappings = map_ptm_evidence_to_protein_sites(
        evidence.accepted_records,
        protein_sequences=_protein_sequences(),
    )
    site_table = build_ptm_site_table(mappings)
    ambiguity = build_ptm_site_ambiguity_report(site_table)
    coverage = build_ptm_site_coverage_report(mappings)

    ambiguity_lines = render_ptm_site_ambiguity_tsv(ambiguity).splitlines()
    coverage_lines = render_ptm_site_coverage_tsv(coverage).splitlines()

    assert ambiguity_lines[0].startswith("site_key\tprotein_ref\tmodification_name")
    assert any(
        "localized peptide is shared across multiple protein references" in line
        for line in ambiguity_lines
    )
    assert (
        coverage_lines[0]
        == "site_key\tspectrum_count\tpeptide_count\tsample_count\tspectra\tpeptides"
    )
    assert any(
        line.startswith(
            "P11111:S5:Phospho\t4\t1\t4\tscan=ptm-001;scan=ptm-002;scan=ptm-003;scan=ptm-004"
        )
        for line in coverage_lines
    )


def test_ptm_coordinate_validation_renderer_preserves_issue_ledgers() -> None:
    provenance = ImportedEvidenceProvenance(
        source_engine="synthetic-ptm",
        source_files=("mapping.tsv",),
        source_row_numbers=(2,),
        original_identifiers={"spectrum_id": "scan=broken"},
    )
    report = validate_ptm_site_coordinates(
        (
            PtmProteinSiteMapping(
                spectrum_id="scan=broken",
                sample_id="C1",
                protein_ref="P11111",
                localized_peptide="S[Phospho]PEPTIDEK",
                canonical_peptide="S[Phospho]PEPTIDEK",
                sequence="SPEPTIDEK",
                modification_name="Phospho",
                residue="S",
                peptide_site_index=1,
                protein_position=999,
                localization_score=0.8,
                q_value=0.01,
                target_decoy_label=TargetDecoyLabel.TARGET,
                candidate_protein_positions=(999,),
                ambiguous=False,
                shared_peptide=False,
                provenance=provenance,
            ),
        ),
        protein_sequences=_protein_sequences(),
    )

    lines = render_ptm_coordinate_validation_tsv(report).splitlines()

    assert report.valid is False
    assert lines[0] == "spectrum_id\tprotein_ref\tsite_key\tcode\tmessage"
    assert any(
        line.startswith(
            "scan=broken\tP11111\tP11111:S999:Phospho\tprotein_position_out_of_range"
        )
        for line in lines
    )
