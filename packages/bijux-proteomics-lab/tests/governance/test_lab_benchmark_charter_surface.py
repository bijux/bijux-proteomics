from __future__ import annotations

from bijux_proteomics_lab.governance.charter import (
    DEFAULT_LAB_CHARTER,
    LabCharterCapability,
)


def test_lab_benchmark_charter_keeps_benchmark_modules_inside_handoff_authority() -> (
    None
):
    handoff_entry = next(
        entry
        for entry in DEFAULT_LAB_CHARTER
        if entry.capability is LabCharterCapability.HANDOFF_PACKETS
    )

    assert "benchmarks/claims.py" in handoff_entry.required_modules
    assert "benchmarks/rehearsals.py" in handoff_entry.required_modules
    assert "artifact integrity" in handoff_entry.release_blocker.lower()
