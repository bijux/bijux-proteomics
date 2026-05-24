# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.io.dia_fragment_coelution import (
    DiaFragmentTracePoint,
    render_dia_fragment_trace_coelution_tsv,
    score_fragment_coelution,
)


def test_score_fragment_coelution_lists_shifted_fragments_and_lowers_score() -> None:
    rows = score_fragment_coelution(
        (
            *_trace("prec_alpha", "frag_y7", ((10.0, 10.0), (20.0, 60.0), (30.0, 10.0))),
            *_trace("prec_alpha", "frag_b4", ((10.0, 8.0), (20.0, 55.0), (30.0, 8.0))),
            *_trace("prec_alpha", "frag_y8", ((20.0, 9.0), (30.0, 50.0), (40.0, 9.0))),
        ),
        apex_tolerance_seconds=5.0,
        min_correlation=0.8,
    )
    rendered = render_dia_fragment_trace_coelution_tsv(rows)
    row = rows[0]

    assert row.precursor_id == "prec_alpha"
    assert row.fragment_count == 3
    assert row.apex_rt_spread == 10.0
    assert row.failed_fragments == ("frag_y8",)
    assert row.coelution_score < 0.8
    assert "precursor_id\tfragment_count\tapex_rt_spread\tmean_trace_correlation\tfailed_fragments\tcoelution_score" in rendered
    assert "prec_alpha\t3\t10.0000" in rendered


def _trace(
    precursor_id: str,
    fragment_id: str,
    points: tuple[tuple[float, float], ...],
) -> tuple[DiaFragmentTracePoint, ...]:
    return tuple(
        DiaFragmentTracePoint(
            precursor_id=precursor_id,
            fragment_id=fragment_id,
            rt=rt,
            intensity=intensity,
        )
        for rt, intensity in points
    )
