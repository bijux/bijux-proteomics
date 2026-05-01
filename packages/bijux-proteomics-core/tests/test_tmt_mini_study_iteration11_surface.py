# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.corpus_iteration11 import build_complete_tmt_mini_study_bundle


def test_build_complete_tmt_mini_study_bundle_validates_channel_membership() -> None:
    bundle = build_complete_tmt_mini_study_bundle(
        study_id="tmt-mini-01",
        channel_ids=("126", "127N", "127C", "128N"),
        carrier_channel_id="127N",
        reference_channel_id="126",
        balance_diagnostics_path="outputs/channel_balance.json",
        normalization_report_path="outputs/normalization.json",
        differential_abundance_report_path="outputs/da.json",
    )

    assert bundle.carrier_channel_id == "127N"
    assert bundle.reference_channel_id == "126"
