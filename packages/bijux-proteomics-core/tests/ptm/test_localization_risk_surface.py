# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.chemistry import (
    FragmentIonSeries,
    calculate_fragment_ions,
    parse_modified_peptide,
)
from bijux_proteomics.domain.records import ImportedEvidenceProvenance
from bijux_proteomics.identification import TargetDecoyLabel
from bijux_proteomics.io.spectra import SpectrumPeak
from bijux_proteomics.ptm.contracts import PtmEvidenceRecord
from bijux_proteomics.ptm.localization_risk import (
    PtmLocalizationRisk,
    detect_false_localization,
    render_false_localization_tsv,
)
from bijux_proteomics.ptm.localization_scoring import (
    build_ptm_localization_scoring_report,
)


def test_false_localization_detector_marks_equal_fragment_support_as_ambiguous() -> (
    None
):
    candidates = _competing_localization_candidates()

    rows = detect_false_localization(
        candidates,
        (SpectrumPeak(mz=50.0, intensity=80.0),),
    )
    rendered = render_false_localization_tsv(rows)
    by_pair = {(row.candidate_site, row.competing_site): row for row in rows}

    assert (
        by_pair[("Phospho@2", "Phospho@4")].localization_risk
        is PtmLocalizationRisk.AMBIGUOUS
    )
    assert (
        by_pair[("Phospho@4", "Phospho@2")].localization_risk
        is PtmLocalizationRisk.AMBIGUOUS
    )
    assert by_pair[("Phospho@2", "Phospho@4")].site_determining_ions == ()
    assert by_pair[("Phospho@4", "Phospho@2")].site_determining_ions == ()
    assert "localization_risk" in rendered


def test_false_localization_detector_marks_weaker_candidate_as_likely_false() -> None:
    candidates = _competing_localization_candidates()
    s2_support_ion, s2_support_mz = _site_determining_fragment_support(
        candidates,
        "AS[Phospho]YTK",
    )

    rows = detect_false_localization(
        candidates,
        (SpectrumPeak(mz=s2_support_mz, intensity=120.0),),
    )
    by_pair = {(row.candidate_site, row.competing_site): row for row in rows}

    assert (
        by_pair[("Phospho@2", "Phospho@4")].localization_risk
        is PtmLocalizationRisk.SUPPORTED
    )
    assert by_pair[("Phospho@2", "Phospho@4")].site_determining_ions == (
        s2_support_ion,
    )
    assert (
        by_pair[("Phospho@4", "Phospho@2")].localization_risk
        is PtmLocalizationRisk.LIKELY_FALSE_LOCALIZATION
    )
    assert by_pair[("Phospho@4", "Phospho@2")].site_determining_ions == ()


def _competing_localization_candidates() -> tuple[PtmEvidenceRecord, ...]:
    provenance = ImportedEvidenceProvenance(
        source_engine="ptm-localization",
        source_files=("inline",),
    )
    return (
        PtmEvidenceRecord(
            spectrum_id="scan=competing-ptm",
            sample_id="C1",
            localized_peptide="AS[Phospho]YTK",
            canonical_peptide="AS[Phospho]YTK",
            sequence="ASYTK",
            charge=2,
            score=95.0,
            q_value=0.02,
            protein_refs=("P11111",),
            target_decoy_label=TargetDecoyLabel.TARGET,
            localization_score=25.0,
            candidate_site_indices=(2, 4),
            modification_names=("Phospho",),
            provenance=provenance,
        ),
        PtmEvidenceRecord(
            spectrum_id="scan=competing-ptm",
            sample_id="C1",
            localized_peptide="ASYT[Phospho]K",
            canonical_peptide="ASYT[Phospho]K",
            sequence="ASYTK",
            charge=2,
            score=92.0,
            q_value=0.02,
            protein_refs=("P11111",),
            target_decoy_label=TargetDecoyLabel.TARGET,
            localization_score=18.0,
            candidate_site_indices=(2, 4),
            modification_names=("Phospho",),
            provenance=provenance,
        ),
    )


def _site_determining_fragment_support(
    candidates: tuple[PtmEvidenceRecord, ...],
    localized_peptide: str,
) -> tuple[str, float]:
    scoring = build_ptm_localization_scoring_report(candidates)
    target = next(
        entry
        for entry in scoring.entries
        if entry.localized_peptide == localized_peptide
    )
    ion_label = target.site_determining_ions[0]
    series = FragmentIonSeries(ion_label[0])
    ordinal = int(ion_label[1:])
    ions = calculate_fragment_ions(
        parse_modified_peptide(localized_peptide),
        charges=(1,),
        series=(FragmentIonSeries.B, FragmentIonSeries.Y),
        include_neutral_losses=False,
    )
    mz = next(
        ion.mz_monoisotopic
        for ion in ions
        if ion.series is series and ion.ordinal == ordinal
    )
    return (f"{ion_label}+1", mz)
