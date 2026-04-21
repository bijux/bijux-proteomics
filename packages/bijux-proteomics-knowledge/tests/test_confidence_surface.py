from __future__ import annotations

from bijux_proteomics_knowledge.confidence import low_confidence_segments


def test_low_confidence_segments_smoke() -> None:
    segments = low_confidence_segments([95.0, 42.0, 40.0, 93.0], threshold=50.0)
    assert segments == [(2, 3)]
