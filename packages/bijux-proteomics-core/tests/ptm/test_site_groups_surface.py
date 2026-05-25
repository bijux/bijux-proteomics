# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.domain.records import ImportedEvidenceProvenance
from bijux_proteomics.identification import TargetDecoyLabel
from bijux_proteomics.ptm import (
    PtmSiteGroupAmbiguityClass,
    build_site_groups,
    render_ptm_site_group_tsv,
)
from bijux_proteomics.ptm.contracts import PtmProteinSiteMapping


def _mapping(
    spectrum_id: str,
    *,
    protein_ref: str,
    localized_peptide: str,
    canonical_peptide: str,
    sequence: str,
    residue: str,
    protein_position: int,
    candidate_protein_positions: tuple[int, ...],
    ambiguous: bool,
) -> PtmProteinSiteMapping:
    return PtmProteinSiteMapping(
        spectrum_id=spectrum_id,
        sample_id="C1",
        protein_ref=protein_ref,
        localized_peptide=localized_peptide,
        canonical_peptide=canonical_peptide,
        sequence=sequence,
        modification_name="Phospho",
        residue=residue,
        peptide_site_index=2,
        protein_position=protein_position,
        localization_score=24.0,
        q_value=0.01,
        target_decoy_label=TargetDecoyLabel.TARGET,
        candidate_protein_positions=candidate_protein_positions,
        ambiguous=ambiguous,
        shared_peptide=False,
        provenance=ImportedEvidenceProvenance(
            source_engine="ptm-localization",
            source_files=("inline",),
        ),
    )


def test_build_site_groups_assigns_ambiguous_signal_once_per_candidate_group() -> None:
    entries = build_site_groups(
        (
            _mapping(
                "scan=exact-1",
                protein_ref="P11111",
                localized_peptide="S[Phospho]PEPTIDEK",
                canonical_peptide="S[Phospho]PEPTIDEK",
                sequence="SPEPTIDEK",
                residue="S",
                protein_position=5,
                candidate_protein_positions=(5,),
                ambiguous=False,
            ),
            _mapping(
                "scan=amb-1a",
                protein_ref="P11111",
                localized_peptide="AS[Phospho]TYK",
                canonical_peptide="AS[Phospho]TYK",
                sequence="ASTYK",
                residue="S",
                protein_position=17,
                candidate_protein_positions=(17, 18, 19),
                ambiguous=True,
            ),
            _mapping(
                "scan=amb-1b",
                protein_ref="P11111",
                localized_peptide="AT[Phospho]SYK",
                canonical_peptide="AT[Phospho]SYK",
                sequence="ATSYK",
                residue="T",
                protein_position=18,
                candidate_protein_positions=(17, 18, 19),
                ambiguous=True,
            ),
            _mapping(
                "scan=amb-1c",
                protein_ref="P11111",
                localized_peptide="AY[Phospho]STK",
                canonical_peptide="AY[Phospho]STK",
                sequence="AYSTK",
                residue="Y",
                protein_position=19,
                candidate_protein_positions=(17, 18, 19),
                ambiguous=True,
            ),
        )
    )

    assert len(entries) == 2
    exact = next(entry for entry in entries if entry.localized_site == 5)
    grouped = next(
        entry
        for entry in entries
        if entry.ambiguity_class is PtmSiteGroupAmbiguityClass.AMBIGUOUS_SITE_GROUP
    )

    assert exact.candidate_sites == (5,)
    assert exact.ambiguity_class is PtmSiteGroupAmbiguityClass.EXACT_SITE
    assert grouped.site_group_id == "P11111:Phospho:17|18|19"
    assert grouped.candidate_sites == (17, 18, 19)
    assert grouped.localized_site is None
    assert grouped.ambiguity_class is (
        PtmSiteGroupAmbiguityClass.AMBIGUOUS_SITE_GROUP
    )


def test_render_ptm_site_group_tsv_exposes_required_surface() -> None:
    rendered = render_ptm_site_group_tsv(
        build_site_groups(
            (
                _mapping(
                    "scan=exact-1",
                    protein_ref="P11111",
                    localized_peptide="S[Phospho]PEPTIDEK",
                    canonical_peptide="S[Phospho]PEPTIDEK",
                    sequence="SPEPTIDEK",
                    residue="S",
                    protein_position=5,
                    candidate_protein_positions=(5,),
                    ambiguous=False,
                ),
                _mapping(
                    "scan=amb-1a",
                    protein_ref="P11111",
                    localized_peptide="AS[Phospho]TYK",
                    canonical_peptide="AS[Phospho]TYK",
                    sequence="ASTYK",
                    residue="S",
                    protein_position=17,
                    candidate_protein_positions=(17, 18, 19),
                    ambiguous=True,
                ),
            )
        )
    )

    assert rendered.startswith(
        "site_group_id\tprotein_id\tcandidate_sites\tlocalized_site\tambiguity_class\n"
    )
    assert "P11111:Phospho:17|18|19\tP11111\t17;18;19\t\tambiguous_site_group" in rendered
