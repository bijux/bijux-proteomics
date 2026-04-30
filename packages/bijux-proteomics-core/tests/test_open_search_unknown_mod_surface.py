# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.open_search_unknown_mod import (
    UnknownModificationHypothesis,
    build_open_search_unknown_mod_report,
)


def test_build_open_search_unknown_mod_report_keeps_hypotheses_as_advisory() -> None:
    report = build_open_search_unknown_mod_report(
        "peptidem",
        mass_shifts=(
            UnknownModificationHypothesis(
                mass_shift_da=79.9663,
                site_index=4,
                residue="T",
                confidence=0.71,
                note="mass shift is compatible with phospho but localization is ambiguous",
            ),
        ),
    )

    assert report.peptide_sequence == "PEPTIDEM"
    assert report.has_unknown_mass_shift is True
    assert report.hypotheses[0].advisory_only is True
    assert report.hypotheses[0].promoted_as_identification is False
