# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

import pytest

from bijux_proteomics.ptm import (
    PtmKinaseConfidenceTier,
    PtmKinaseMotifMatch,
    PtmKinaseSiteResult,
    PtmKinaseSubstrateMatch,
    infer_kinases,
    render_ptm_kinase_inference_tsv,
)


def test_infer_kinases_keeps_motif_plus_substrate_above_motif_only() -> None:
    entries = infer_kinases(
        (
            PtmKinaseSiteResult(
                site_id="P11111:S5:Phospho",
                protein_id="P11111",
                signed_effect=1.6,
            ),
            PtmKinaseSiteResult(
                site_id="P11111:T8:Phospho",
                protein_id="P11111",
                signed_effect=1.2,
            ),
        ),
        (
            PtmKinaseMotifMatch(
                kinase="MAPK1",
                site_id="P11111:S5:Phospho",
                motif_score=0.93,
            ),
            PtmKinaseMotifMatch(
                kinase="PKA",
                site_id="P11111:T8:Phospho",
                motif_score=0.95,
            ),
        ),
        (
            PtmKinaseSubstrateMatch(
                kinase="MAPK1",
                site_id="P11111:S5:Phospho",
            ),
        ),
    )

    assert tuple(entry.kinase for entry in entries) == ("MAPK1", "PKA")
    mapk1, pka = entries
    assert mapk1.motif_support_count == 1
    assert mapk1.known_substrate_support_count == 1
    assert mapk1.supporting_sites == ("P11111:S5:Phospho",)
    assert mapk1.confidence_tier is PtmKinaseConfidenceTier.MOTIF_PLUS_SUBSTRATE
    assert pka.confidence_tier is PtmKinaseConfidenceTier.MOTIF_ONLY
    assert mapk1.combined_score > pka.combined_score


def test_infer_kinases_ignores_nonmatching_sites_and_renders_required_surface() -> None:
    entries = infer_kinases(
        (
            PtmKinaseSiteResult(
                site_id="Q9DEC1:S12:Phospho",
                protein_id="Q9DEC1",
                signed_effect=-0.8,
            ),
        ),
        (
            PtmKinaseMotifMatch(
                kinase="AKT1",
                site_id="Q9DEC1:S12:Phospho",
                motif_score=0.72,
            ),
            PtmKinaseMotifMatch(
                kinase="ERK2",
                site_id="Q9DEC1:S99:Phospho",
                motif_score=0.99,
            ),
        ),
        (
            PtmKinaseSubstrateMatch(
                kinase="AKT1",
                site_id="Q9DEC1:S99:Phospho",
            ),
        ),
    )
    rendered = render_ptm_kinase_inference_tsv(entries)

    assert len(entries) == 1
    entry = entries[0]
    assert entry.kinase == "AKT1"
    assert entry.motif_support_count == 1
    assert entry.known_substrate_support_count == 0
    assert entry.supporting_sites == ("Q9DEC1:S12:Phospho",)
    assert rendered.startswith(
        "kinase\tmotif_support_count\tknown_substrate_support_count\tcombined_score\tsupporting_sites\tconfidence_tier\n"
    )
    assert "AKT1\t1\t0\t0.864000\tQ9DEC1:S12:Phospho\tmotif_only\n" in rendered


def test_infer_kinases_requires_unique_site_ids() -> None:
    with pytest.raises(
        ValueError,
        match="kinase inference requires unique site_id phosphosite results",
    ):
        infer_kinases(
            (
                PtmKinaseSiteResult(
                    site_id="P11111:S5:Phospho",
                    protein_id="P11111",
                    signed_effect=1.0,
                ),
                PtmKinaseSiteResult(
                    site_id="P11111:S5:Phospho",
                    protein_id="P11111",
                    signed_effect=1.2,
                ),
            ),
            (),
            (),
        )
