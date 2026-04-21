from __future__ import annotations

from bijux_proteomics.domain.sequence import primary_summary_from_sequence as core_primary
from bijux_proteomics_intelligence.domain.sequence import (
    primary_summary_from_sequence as intelligence_primary,
)


def test_intelligence_sequence_forwarding_targets_core() -> None:
    assert intelligence_primary is core_primary
