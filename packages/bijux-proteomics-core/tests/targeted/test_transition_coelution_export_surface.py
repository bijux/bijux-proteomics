# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.targeted.result_import import (
    build_skyline_result_import_report,
)
from bijux_proteomics.targeted.transition_coelution import (
    build_targeted_transition_coelution_report,
    render_targeted_transition_coelution_target_tsv,
    render_targeted_transition_coelution_transition_tsv,
)


def _format_fixture(name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures" / "formats" / name


def test_render_targeted_transition_coelution_exports_keep_coelution_review_visible() -> None:
    import_report = build_skyline_result_import_report(
        _format_fixture("skyline_targeted_qc_results.tsv")
    )
    report = build_targeted_transition_coelution_report(import_report)

    target_tsv = render_targeted_transition_coelution_target_tsv(report)
    transition_tsv = render_targeted_transition_coelution_transition_tsv(report)

    assert "target_id\tsample_id\texpected_transition_count\tobserved_transition_count\tcoeluting_transition_count" in target_tsv
    assert "\talignment_flagged\tcoelution_tier\treliable_transition_support\t" in target_tsv
    assert (
        "PEPTIDEK/2\ttreat_r2\t2\t1\t1\ty7\ty8\ty7\t13.3\t13.3\t12.6\t0.7\tfalse\tinsufficient\tfalse\tfewer than two coeluting transitions support the target"
        in target_tsv
    )
    assert "target_id\tsample_id\ttransition_id\tdetected\tretention_time_minutes\tanchor_transition_id" in transition_tsv
    assert (
        "ACDMPEP/3\ttreat_r2\ty5\ttrue\t20.2\ty5\t20.2\t18.2\t0\t2\ttrue\ttransition is misaligned from the target reference window"
        in transition_tsv
    )
