from __future__ import annotations

from bijux_proteomics.domain.sequence import primary_summary_from_sequence


def test_core_sequence_summary_surface() -> None:
    summary = primary_summary_from_sequence("ACDE")
    assert summary.length == 4
    assert "A" in summary.aa_composition
