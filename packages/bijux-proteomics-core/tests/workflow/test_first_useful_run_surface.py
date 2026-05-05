# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from bijux_proteomics.sequences.digestion import (
    digest_protein_records,
    get_protease_rule,
)
from bijux_proteomics.identification import (
    SearchResultColumnMapping,
    apply_q_values,
    build_protein_summary_report,
    build_psm_summary_report,
    filter_psms_by_fdr,
    parse_psm_tsv,
)
from bijux_proteomics.io.spectra import (
    annotate_spectrum_fragments,
    build_spectrum_collection_summary,
    parse_mgf,
)
from bijux_proteomics.sequences import FastaParseMode, parse_fasta_document


def _workflow_fixture(name: str) -> Path:
    return Path(__file__).resolve().parents[1] / "fixtures" / "first_useful_run" / name


def test_first_useful_run_fixture_covers_digest_psm_fdr_and_annotation() -> None:
    fasta_report = parse_fasta_document(
        _workflow_fixture("proteins.fasta").read_text(),
        mode=FastaParseMode.STRICT,
    )
    peptides = digest_protein_records(
        fasta_report.accepted_records,
        protease=get_protease_rule("trypsin"),
    )
    assert any(peptide.sequence == "PEPTIDEK" for peptide in peptides)

    psm_report = parse_psm_tsv(
        _workflow_fixture("results.tsv"),
        mapping=SearchResultColumnMapping(
            spectrum_id="spectrum_id",
            peptide="peptide",
            charge="charge",
            score="score",
            protein_refs="proteins",
        ),
    )
    normalized = apply_q_values(psm_report.accepted_records)
    accepted = filter_psms_by_fdr(psm_report.accepted_records, threshold=0.5)
    assert len(accepted) == 1
    assert accepted[0].canonical_peptide == "PEPTIDEK"

    spectrum_report = parse_mgf(_workflow_fixture("spectra.mgf"))
    assert len(spectrum_report.accepted_spectra) == 1
    spectrum = spectrum_report.accepted_spectra[0]
    annotation = annotate_spectrum_fragments(
        spectrum,
        peptide=accepted[0].canonical_peptide,
        tolerance_da=0.02,
    )
    assert annotation.matches

    psm_summary = build_psm_summary_report(normalized)
    protein_summary = build_protein_summary_report(normalized)
    spectrum_summary = build_spectrum_collection_summary(spectrum_report)
    assert psm_summary.total_psms == 2
    assert protein_summary.total_proteins >= 1
    assert spectrum_summary.spectrum_count == 1


def test_first_useful_run_manifest_hashes_match_fixture_pack() -> None:
    manifest = json.loads(_workflow_fixture("fixture_manifest.json").read_text())
    for entry in manifest["files"]:
        path = _workflow_fixture(entry["path"])
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        assert digest == entry["sha256"]
