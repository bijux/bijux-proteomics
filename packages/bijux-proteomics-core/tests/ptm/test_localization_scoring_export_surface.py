# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.ptm import (
    build_ptm_localization_scoring_report,
    parse_ptm_localization_tsv,
    render_ptm_localization_scoring_entry_tsv,
    render_ptm_localization_scoring_summary_tsv,
)


def _fixture_path(name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures" / "ptm" / name


def test_ptm_localization_scoring_tsv_renderers_preserve_probability_and_ions() -> None:
    parsed = parse_ptm_localization_tsv(_fixture_path("localization_results.tsv"))
    report = build_ptm_localization_scoring_report(
        parsed.accepted_records,
        fragment_ion_support_by_spectrum={
            "scan=ptm-001": ("b5", "y7"),
            "scan=ptm-005": ("b2",),
        },
    )

    summary_tsv = render_ptm_localization_scoring_summary_tsv(report)
    entry_tsv = render_ptm_localization_scoring_entry_tsv(report)

    assert summary_tsv.splitlines()[0] == (
        "entry_count\tambiguous_entry_count\tconfident_entry_count\t"
        "high_confidence_entry_count\tsupported_entry_count\trefused_entry_count\t"
        "multi_phosphorylated_entry_count\tfragment_supported_entry_count"
    )
    assert "scan=ptm-001" in entry_tsv
    assert "ambiguity_group" in entry_tsv.splitlines()[0]
    assert "localization_tier" in entry_tsv.splitlines()[0]
    assert "normalized_score" in entry_tsv
    assert "b2" in entry_tsv
