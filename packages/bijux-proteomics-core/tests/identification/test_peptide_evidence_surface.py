# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.identification import PsmRecord
from bijux_proteomics.identification.peptide_evidence import (
    PeptideEvidenceClass,
    PeptideEvidenceTag,
    build_peptide_evidence_report,
    render_peptide_evidence_entries_tsv,
    render_peptide_evidence_summary_tsv,
)
from bijux_proteomics.identification.search_adapters import parse_psm_tsv

from .test_identification_surface import _default_mapping, _psm_fixture


def test_peptide_evidence_report_classifies_all_owned_primary_classes() -> None:
    report = parse_psm_tsv(
        _psm_fixture("peptide_evidence_classes.tsv"), mapping=_default_mapping()
    )

    evidence = build_peptide_evidence_report(
        report.accepted_records,
        threshold=0.05,
        score_orientation="higher_better",
        strong_q_value=0.01,
    )

    by_peptide = {entry.canonical_peptide: entry for entry in evidence.entries}

    assert evidence.summary.total_peptides == 8
    assert evidence.summary.strong_count == 1
    assert evidence.summary.moderate_count == 1
    assert evidence.summary.weak_count == 2
    assert evidence.summary.shared_count == 1
    assert evidence.summary.ambiguous_count == 1
    assert evidence.summary.contaminant_count == 1
    assert evidence.summary.decoy_count == 1
    assert evidence.summary.modified_count == 1
    assert evidence.summary.reproducible_count == 2
    assert by_peptide["STRONGK"].primary_class is PeptideEvidenceClass.STRONG
    assert by_peptide["STRONGK"].spectrum_count == 2
    assert PeptideEvidenceTag.REPRODUCIBLE in by_peptide["STRONGK"].tags
    assert by_peptide["SHAREDFINEK"].primary_class is PeptideEvidenceClass.SHARED
    assert by_peptide["SHAREDK"].primary_class is PeptideEvidenceClass.WEAK
    assert PeptideEvidenceTag.SHARED in by_peptide["SHAREDK"].tags
    assert (
        by_peptide["ACDM[Oxidation]K"].primary_class
        is PeptideEvidenceClass.MODERATE
    )
    assert PeptideEvidenceTag.MODIFIED in by_peptide["ACDM[Oxidation]K"].tags
    assert by_peptide["AMBIGK"].primary_class is PeptideEvidenceClass.AMBIGUOUS
    assert by_peptide["CONTAMK"].primary_class is PeptideEvidenceClass.CONTAMINANT
    assert by_peptide["DECOYSEQ"].primary_class is PeptideEvidenceClass.DECOY

    summary_tsv = render_peptide_evidence_summary_tsv(evidence)
    entries_tsv = render_peptide_evidence_entries_tsv(evidence)

    assert "moderate_count\t1" in summary_tsv
    assert "shared_count\t1" in summary_tsv
    assert "ambiguous_count\t1" in summary_tsv
    assert "reproducibility_hash" in summary_tsv
    assert "STRONGK\tSTRONGK\tstrong\tunique;reproducible" in entries_tsv


def test_peptide_evidence_report_marks_one_weak_shared_peptide_as_not_strong() -> None:
    report = build_peptide_evidence_report(
        (
            PsmRecord.model_validate(
                {
                    "spectrum_id": "scan=1",
                    "peptide": "SHAREDK",
                    "canonical_peptide": "SHAREDK",
                    "charge": 2,
                    "score": 50.0,
                    "q_value": 0.020,
                    "protein_refs": ("P11111", "P22222"),
                }
            ),
            PsmRecord.model_validate(
                {
                    "spectrum_id": "scan=2",
                    "peptide": "DECOYSEQ",
                    "canonical_peptide": "DECOYSEQ",
                    "charge": 2,
                    "score": 55.0,
                    "q_value": 0.010,
                    "protein_refs": ("DECOY_P11111",),
                    "target_decoy_label": "decoy",
                }
            ),
        ),
        threshold=0.05,
        score_orientation="higher_better",
        strong_q_value=0.01,
    )

    shared = next(entry for entry in report.entries if entry.canonical_peptide == "SHAREDK")

    assert shared.primary_class is PeptideEvidenceClass.WEAK
    assert PeptideEvidenceTag.SHARED in shared.tags
    assert shared.accepted is False
