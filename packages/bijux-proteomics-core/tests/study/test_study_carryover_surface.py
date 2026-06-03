# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

import pytest

from bijux_proteomics.study import (
    CarryoverIntensityEntry,
    CarryoverRunOrderEntry,
    detect_carryover,
    render_carryover_detection_tsv,
)


def test_detect_carryover_flags_known_injected_followup_signal() -> None:
    rows = detect_carryover(
        (
            CarryoverRunOrderEntry(run_id="source_high.raw", run_order=1),
            CarryoverRunOrderEntry(run_id="blank_after_source.raw", run_order=2),
            CarryoverRunOrderEntry(run_id="target_sample.raw", run_order=3),
            CarryoverRunOrderEntry(run_id="wash_blank.raw", run_order=4),
        ),
        (
            CarryoverIntensityEntry(
                run_id="source_high.raw",
                entity_id="CARRYPEP/2",
                intensity=200000.0,
            ),
            CarryoverIntensityEntry(
                run_id="blank_after_source.raw",
                entity_id="CARRYPEP/2",
                intensity=4000.0,
            ),
            CarryoverIntensityEntry(
                run_id="target_sample.raw",
                entity_id="CARRYPEP/2",
                intensity=2000.0,
            ),
            CarryoverIntensityEntry(
                run_id="wash_blank.raw",
                entity_id="CARRYPEP/2",
                intensity=25000.0,
            ),
            CarryoverIntensityEntry(
                run_id="source_high.raw",
                entity_id="STABLEPEP/2",
                intensity=30000.0,
            ),
            CarryoverIntensityEntry(
                run_id="blank_after_source.raw",
                entity_id="STABLEPEP/2",
                intensity=12000.0,
            ),
        ),
    )
    rendered = render_carryover_detection_tsv(rows)

    assert len(rows) == 2
    assert rows[0].source_run == "source_high.raw"
    assert rows[0].affected_run == "blank_after_source.raw"
    assert rows[0].entity_id == "CARRYPEP/2"
    assert rows[0].source_intensity == 200000.0
    assert rows[0].affected_intensity == 4000.0
    assert rows[0].carryover_score == 0.9333
    assert rows[1].affected_run == "target_sample.raw"
    assert rows[1].carryover_score == 0.8
    assert (
        "source_run\taffected_run\tentity_id\tsource_intensity\taffected_intensity\tcarryover_score"
        in rendered
    )
    assert (
        "source_high.raw\tblank_after_source.raw\tCARRYPEP/2\t200000\t4000\t0.9333"
        in rendered
    )


def test_detect_carryover_requires_explicit_run_order() -> None:
    with pytest.raises(
        ValueError, match="run_order is required for carryover analysis"
    ):
        detect_carryover(
            (),
            (
                CarryoverIntensityEntry(
                    run_id="source_high.raw",
                    entity_id="CARRYPEP/2",
                    intensity=200000.0,
                ),
            ),
        )
