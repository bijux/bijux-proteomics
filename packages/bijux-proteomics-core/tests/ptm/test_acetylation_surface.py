# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

import pytest

from bijux_proteomics.ptm import (
    PtmAcetylationType,
    PtmAcetylProteinContext,
    PtmAcetylSiteCandidate,
    analyze_acetylation_sites,
    render_acetylation_site_analysis_tsv,
)


def test_analyze_acetylation_sites_separates_n_terminal_and_lysine_acetylation() -> (
    None
):
    entries = analyze_acetylation_sites(
        (
            PtmAcetylSiteCandidate(
                site_id="P1:A1:Acetyl",
                protein_id="P1",
                residue="A",
                position=1,
                raw_site_log2fc=1.2,
                protein_log2fc=0.5,
            ),
            PtmAcetylSiteCandidate(
                site_id="P1:K8:Acetyl",
                protein_id="P1",
                residue="K",
                position=8,
                raw_site_log2fc=0.9,
                protein_log2fc=0.4,
            ),
        ),
        (
            PtmAcetylProteinContext(
                protein_id="P1",
                start=1,
                end=3,
                domain_context="n_term_tail",
            ),
            PtmAcetylProteinContext(
                protein_id="P1",
                start=5,
                end=12,
                domain_context="acetyl_binding_repeat",
            ),
        ),
    )

    by_site = {entry.site_id: entry for entry in entries}
    n_terminal = by_site["P1:A1:Acetyl"]
    lysine = by_site["P1:K8:Acetyl"]

    assert n_terminal.acetylation_type is PtmAcetylationType.N_TERMINAL_ACETYLATION
    assert n_terminal.n_terminal is True
    assert n_terminal.lysine_position is None
    assert n_terminal.domain_context == "n_term_tail"
    assert n_terminal.abundance_corrected_effect == 0.7

    assert lysine.acetylation_type is PtmAcetylationType.LYSINE_ACETYLATION
    assert lysine.n_terminal is False
    assert lysine.lysine_position == 8
    assert lysine.domain_context == "acetyl_binding_repeat"
    assert lysine.abundance_corrected_effect == 0.5


def test_analyze_acetylation_sites_renders_surface_and_preserves_missing_baselines() -> (
    None
):
    entries = analyze_acetylation_sites(
        (
            PtmAcetylSiteCandidate(
                site_id="P2:S4:Acetyl",
                protein_id="P2",
                residue="S",
                position=4,
                raw_site_log2fc=0.6,
            ),
        ),
        (
            PtmAcetylProteinContext(
                protein_id="P2",
                start=2,
                end=8,
                domain_context="regulatory_loop",
            ),
        ),
    )
    rendered = render_acetylation_site_analysis_tsv(entries)

    assert (
        entries[0].acetylation_type
        is PtmAcetylationType.NONCANONICAL_RESIDUE_ACETYLATION
    )
    assert entries[0].n_terminal is False
    assert entries[0].lysine_position is None
    assert entries[0].domain_context == "regulatory_loop"
    assert entries[0].abundance_corrected_effect is None
    assert rendered.startswith(
        "site_id\tacetylation_type\tlysine_position\tn_terminal\tdomain_context\tabundance_corrected_effect\n"
    )
    assert (
        "P2:S4:Acetyl\tnoncanonical_residue_acetylation\t\tfalse\tregulatory_loop\t\n"
        in rendered
    )


def test_analyze_acetylation_sites_requires_unique_site_ids() -> None:
    with pytest.raises(
        ValueError,
        match="acetylation analysis requires unique site_id rows",
    ):
        analyze_acetylation_sites(
            (
                PtmAcetylSiteCandidate(
                    site_id="P1:K8:Acetyl",
                    protein_id="P1",
                    residue="K",
                    position=8,
                    raw_site_log2fc=0.9,
                ),
                PtmAcetylSiteCandidate(
                    site_id="P1:K8:Acetyl",
                    protein_id="P1",
                    residue="K",
                    position=8,
                    raw_site_log2fc=0.7,
                ),
            ),
            (),
        )
