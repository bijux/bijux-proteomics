# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics_intelligence.domain import low_confidence_segments


def test_low_confidence_segments_stay_intelligence_owned() -> None:
    plddt: list[float] = [50.0] * 8 + [80.0] * 2 + [40.0] * 10

    assert low_confidence_segments(plddt, thresh=70, min_len=8) == [(0, 8), (10, 20)]
