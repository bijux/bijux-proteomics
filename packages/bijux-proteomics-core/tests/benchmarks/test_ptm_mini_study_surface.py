# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.benchmarks.corpora import build_complete_ptm_mini_study_bundle


def test_build_complete_ptm_mini_study_bundle_requires_lab_target_suggestions() -> None:
    bundle = build_complete_ptm_mini_study_bundle(
        study_id="ptm-mini-01",
        localization_report_path="outputs/localization.json",
        motif_report_path="outputs/motif.json",
        occupancy_report_path="outputs/occupancy.json",
        quant_report_path="outputs/quant.json",
        caveats=("site ambiguity remains for low-intensity spectra",),
        lab_target_suggestions=("validate S123 on P11111",),
    )

    assert bundle.study_id == "ptm-mini-01"
    assert bundle.lab_target_suggestions[0].startswith("validate")
