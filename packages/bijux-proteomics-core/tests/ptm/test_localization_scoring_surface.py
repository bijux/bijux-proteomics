# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.domain.records import ImportedEvidenceProvenance
from bijux_proteomics.identification import TargetDecoyLabel
from bijux_proteomics.ptm import (
    PtmEvidenceRecord,
    PtmLocalizationConfidenceTier,
    PtmLocalizationProbabilitySource,
    build_ptm_localization_scoring_report,
)


def _fixture_path(name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures" / "ptm" / name


def test_ptm_localization_scoring_reports_probability_and_site_determining_ions() -> (
    None
):
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
    assert (
        decisive.probability_source is PtmLocalizationProbabilitySource.NORMALIZED_SCORE
    )
    assert decisive.localization_tier is PtmLocalizationConfidenceTier.SUPPORTED
    assert decisive.ambiguous is False
    assert ambiguous.localization_probability == 0.7
    assert ambiguous.localization_tier is PtmLocalizationConfidenceTier.SUPPORTED
    assert ambiguous.ambiguous is False
    assert ambiguous.ambiguity_group == "Phospho:2|3|4"
    assert ambiguous.site_determining_ions
    assert ambiguous.supported_site_determining_ions == ("b2",)


def test_ptm_localization_high_confidence_requires_probability_or_site_evidence() -> (
    None
):
    from bijux_proteomics.ptm import parse_ptm_localization_tsv

    report = parse_ptm_localization_tsv(_fixture_path("localization_results.tsv"))
    without_support = build_ptm_localization_scoring_report(report.accepted_records)

    decisive = next(
        entry
        for entry in without_support.entries
        if entry.spectrum_id == "scan=ptm-001"
    )
    ambiguous = next(
        entry
        for entry in without_support.entries
        if entry.spectrum_id == "scan=ptm-005"
    )

    assert decisive.localization_probability == 0.99
    assert decisive.localization_tier is PtmLocalizationConfidenceTier.SUPPORTED
    assert ambiguous.localization_tier is PtmLocalizationConfidenceTier.AMBIGUOUS
    assert ambiguous.ambiguous is True


def test_ptm_localization_scoring_uses_imported_probability_for_high_confidence() -> (
    None
):
    from bijux_proteomics.ptm import parse_ptm_localization_tsv

    report = parse_ptm_localization_tsv(
        _fixture_path("localization_probability_results.tsv")
    )
    scoring = build_ptm_localization_scoring_report(report.accepted_records)

    decisive = next(
        entry for entry in scoring.entries if entry.spectrum_id == "scan=ptm-prob-001"
    )

    assert decisive.localization_probability == 0.982
    assert (
        decisive.probability_source
        is PtmLocalizationProbabilitySource.REPORTED_PROBABILITY
    )
    assert decisive.localization_tier is PtmLocalizationConfidenceTier.HIGH_CONFIDENCE
    assert "imported localization probability" in decisive.note


def test_ptm_localization_scoring_uses_site_determining_ions_for_high_confidence() -> (
    None
):
    report = build_ptm_localization_scoring_report(
        (
            PtmEvidenceRecord(
                spectrum_id="scan=ion-high",
                sample_id="C1",
                localized_peptide="AS[Phospho]TYK",
                canonical_peptide="AS[Phospho]TYK",
                sequence="ASTYK",
                charge=2,
                score=95.0,
                q_value=0.02,
                protein_refs=("P11111",),
                target_decoy_label=TargetDecoyLabel.TARGET,
                localization_score=25.0,
                candidate_site_indices=(2, 3, 4),
                modification_names=("Phospho",),
                provenance=ImportedEvidenceProvenance(
                    source_engine="ptm-localization",
                    source_files=("inline",),
                ),
            ),
        )
    )
    initial = report.entries[0]
    supported = build_ptm_localization_scoring_report(
        (
            PtmEvidenceRecord(
                spectrum_id="scan=ion-high",
                sample_id="C1",
                localized_peptide="AS[Phospho]TYK",
                canonical_peptide="AS[Phospho]TYK",
                sequence="ASTYK",
                charge=2,
                score=95.0,
                q_value=0.02,
                protein_refs=("P11111",),
                target_decoy_label=TargetDecoyLabel.TARGET,
                localization_score=25.0,
                candidate_site_indices=(2, 3, 4),
                modification_names=("Phospho",),
                provenance=ImportedEvidenceProvenance(
                    source_engine="ptm-localization",
                    source_files=("inline",),
                ),
            ),
        ),
        fragment_ion_support_by_spectrum={
            "scan=ion-high": initial.site_determining_ions
        },
    ).entries[0]

    assert initial.localization_tier is PtmLocalizationConfidenceTier.AMBIGUOUS
    assert supported.supported_site_determining_ions == initial.site_determining_ions
    assert supported.localization_tier is PtmLocalizationConfidenceTier.HIGH_CONFIDENCE
    assert supported.ambiguous is False
    assert "site-determining fragment ions" in supported.note


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
                provenance=ImportedEvidenceProvenance(
                    source_engine="ptm-localization",
                    source_files=("inline",),
                ),
            ),
        )
    )

    assert len(report.entries) == 2
    assert all(entry.multi_phosphorylated is True for entry in report.entries)
    assert all(entry.site_determining_ions for entry in report.entries)
    assert all(entry.ambiguity_group.startswith("Phospho:") for entry in report.entries)


def test_ptm_localization_scoring_ignores_invalid_candidate_residues() -> None:
    report = build_ptm_localization_scoring_report(
        (
            PtmEvidenceRecord(
                spectrum_id="scan=invalid-candidate",
                sample_id="S1",
                localized_peptide="AS[Phospho]TYEK",
                canonical_peptide="AS[Phospho]TYEK",
                sequence="ASTYEK",
                charge=2,
                score=91.0,
                q_value=0.01,
                protein_refs=("P11111",),
                target_decoy_label=TargetDecoyLabel.TARGET,
                localization_score=0.91,
                candidate_site_indices=(2, 5),
                modification_names=("Phospho",),
                provenance=ImportedEvidenceProvenance(
                    source_engine="ptm-localization",
                    source_files=("inline",),
                ),
            ),
        )
    )

    entry = report.entries[0]

    assert entry.candidate_site_indices == (2,)
    assert entry.ambiguity_group == "Phospho:2"


def test_ptm_localization_scoring_preserves_separate_entries_for_parsed_multi_sites() -> (
    None
):
    from bijux_proteomics.ptm import parse_ptm_localization_tsv

    parsed = parse_ptm_localization_tsv(_fixture_path("multi_localization_results.tsv"))
    report = build_ptm_localization_scoring_report(parsed.accepted_records)

    assert len(report.entries) == 2
    assert [entry.peptide_site_index for entry in report.entries] == [2, 4]
    assert all(entry.multi_phosphorylated is True for entry in report.entries)
    assert all(
        entry.localization_tier is PtmLocalizationConfidenceTier.AMBIGUOUS
        for entry in report.entries
    )
