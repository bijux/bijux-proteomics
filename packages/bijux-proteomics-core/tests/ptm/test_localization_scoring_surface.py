# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.identification import TargetDecoyLabel
from bijux_proteomics.ptm import (
    PtmEvidenceRecord,
    PtmLocalizationProbabilitySource,
    build_ptm_localization_scoring_report,
)


def _fixture_path(name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures" / "ptm" / name


def test_ptm_localization_scoring_reports_probability_and_site_determining_ions() -> None:
    from bijux_proteomics.ptm import parse_ptm_localization_tsv

    report = parse_ptm_localization_tsv(_fixture_path("localization_results.tsv"))
    scoring = build_ptm_localization_scoring_report(
        report.accepted_records,
        fragment_ion_support_by_spectrum={
            "scan=ptm-005": ("b2", "y2"),
        },
    )

    decisive = next(
        entry for entry in scoring.entries if entry.spectrum_id == "scan=ptm-001"
    )
    ambiguous = next(
        entry for entry in scoring.entries if entry.spectrum_id == "scan=ptm-005"
    )

    assert decisive.localization_probability == 0.99
    assert decisive.probability_source is PtmLocalizationProbabilitySource.NORMALIZED_SCORE
    assert decisive.ambiguous is False
    assert ambiguous.localization_probability == 0.7
    assert ambiguous.ambiguous is True
    assert ambiguous.site_determining_ions
    assert ambiguous.supported_site_determining_ions == ("b2",)


def test_ptm_localization_scoring_supports_multi_phosphorylated_peptides() -> None:
    report = build_ptm_localization_scoring_report(
        (
            PtmEvidenceRecord(
                spectrum_id="scan=multi-phospho",
                sample_id="C1",
                localized_peptide="S[Phospho]ATY[Phospho]K",
                canonical_peptide="S[Phospho]ATY[Phospho]K",
                sequence="SATYK",
                charge=2,
                score=120.0,
                q_value=0.01,
                protein_refs=("P1",),
                target_decoy_label=TargetDecoyLabel.TARGET,
                localization_score=0.92,
                candidate_site_indices=(),
                modification_names=("Phospho", "Phospho"),
            ),
        )
    )

    assert len(report.entries) == 2
    assert all(entry.multi_phosphorylated is True for entry in report.entries)
    assert all(entry.site_determining_ions for entry in report.entries)


def test_ptm_localization_scoring_preserves_separate_entries_for_parsed_multi_sites() -> None:
    from bijux_proteomics.ptm import parse_ptm_localization_tsv

    parsed = parse_ptm_localization_tsv(_fixture_path("multi_localization_results.tsv"))
    report = build_ptm_localization_scoring_report(parsed.accepted_records)

    assert len(report.entries) == 2
    assert [entry.peptide_site_index for entry in report.entries] == [2, 4]
    assert all(entry.multi_phosphorylated is True for entry in report.entries)
