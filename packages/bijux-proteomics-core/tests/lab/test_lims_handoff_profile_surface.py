# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.lab.planning import (
    LimsHandoffEntry,
    build_lims_handoff_profile,
)


def test_build_lims_handoff_profile_exports_versioned_json_and_tsv() -> None:
    profile = build_lims_handoff_profile(
        profile_version="1.0.0",
        handoff_id="handoff-10",
        entries=(
            LimsHandoffEntry(
                sample_id="sample-1",
                target_id="target-a",
                method="prm",
                plate_well="A1",
                replicate_id="R1",
            ),
        ),
    )

    assert profile.profile_version == "1.0.0"
    assert '"handoff_id":"handoff-10"' in profile.json_payload
    assert (
        "sample_id\ttarget_id\tmethod\tplate_well\treplicate_id" in profile.tsv_payload
    )
