# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from math import isclose

from bijux_proteomics.chemistry import (
    PeptideTermini,
    build_peptide_mass_report,
    render_peptide_mass_contributions_tsv,
)


def test_contribution_renderer_emits_stable_residue_mass_table() -> None:
    report = build_peptide_mass_report("ACD", charge=2)

    rendered = render_peptide_mass_contributions_tsv(report)

    assert rendered.splitlines() == [
        "position\tresidue\tmonoisotopic_mass\taverage_mass",
        "1\tA\t71.03711\t71.07880",
        "2\tC\t103.00919\t103.13880",
        "3\tD\t115.02694\t115.08860",
    ]


def test_custom_termini_shift_neutral_mass_by_declared_delta() -> None:
    free_report = build_peptide_mass_report("PEPTIDE", charge=2)
    bare_termini_report = build_peptide_mass_report(
        "PEPTIDE",
        charge=2,
        termini=PeptideTermini(
            n_term_label="bare_n_term",
            c_term_label="bare_c_term",
            n_term_monoisotopic_mass=0.0,
            n_term_average_mass=0.0,
            c_term_monoisotopic_mass=0.0,
            c_term_average_mass=0.0,
        ),
    )

    assert isclose(
        free_report.neutral_monoisotopic_mass
        - bare_termini_report.neutral_monoisotopic_mass,
        18.01056,
        rel_tol=0.0,
        abs_tol=1e-9,
    )
    assert isclose(
        free_report.neutral_average_mass - bare_termini_report.neutral_average_mass,
        18.01528,
        rel_tol=0.0,
        abs_tol=1e-9,
    )
