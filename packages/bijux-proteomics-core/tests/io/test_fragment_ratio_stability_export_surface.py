# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.io.fragment_ratio_stability import (
    build_targeted_fragment_ratio_stability_report,
    render_fragment_ratio_stability_fragments_tsv,
    render_fragment_ratio_stability_observations_tsv,
)
from bijux_proteomics.targeted.result_import import build_skyline_result_import_report


def _format_fixture(name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures" / "formats" / name


def test_render_fragment_ratio_stability_exports_keep_cross_run_ratio_review_visible() -> (
    None
):
    report = build_targeted_fragment_ratio_stability_report(
        build_skyline_result_import_report(
            _format_fixture("skyline_targeted_qc_results.tsv")
        )
    )

    fragment_tsv = render_fragment_ratio_stability_fragments_tsv(report)
    observation_tsv = render_fragment_ratio_stability_observations_tsv(report)

    assert fragment_tsv.splitlines()[0] == (
        "data_kind\tanalyte_id\tpeptide_ref\tfragment_id\trun_count\tobserved_run_count\t"
        "expected_ratio\tratio_cv\tdrift_flagged_run_count\tunstable_fragment\t"
        "stability_score\tconcern_codes"
    )
    assert (
        "targeted\tPEPTIDEK/2\tPEPTIDEK\ty8\t4\t3\t0.236842\t0.396731\t1\ttrue\t0.333300\tratio_drift|high_ratio_cv"
        in fragment_tsv
    )
    assert observation_tsv.splitlines()[0] == (
        "data_kind\tanalyte_id\tpeptide_ref\trun_id\tfragment_id\texpected_ratio\t"
        "observed_ratio\tabsolute_ratio_delta\tratio_cv\tdrift_flag\tunstable_fragment\tconcern_codes"
    )
    assert (
        "targeted\tPEPTIDEK/2\tPEPTIDEK\ttreat_r1\ty8\t0.236842\t0.105263\t0.131579\t0.396731\ttrue\ttrue\tratio_drift|high_ratio_cv"
        in observation_tsv
    )
