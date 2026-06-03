# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.targeted.result_import import (
    build_skyline_result_import_report,
)
from bijux_proteomics.targeted.transition_coelution import (
    build_targeted_transition_coelution_report,
)


def _format_fixture(name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures" / "formats" / name


def test_build_targeted_transition_coelution_report_keeps_target_alignment_visible() -> (
    None
):
    import_report = build_skyline_result_import_report(
        _format_fixture("skyline_targeted_qc_results.tsv")
    )

    report = build_targeted_transition_coelution_report(import_report)

    assert report.source_name == "Skyline"
    assert report.summary.target_entry_count == 8
    assert report.summary.flagged_target_entry_count == 3
    peptk_treat_r2 = next(
        entry
        for entry in report.target_entries
        if entry.target_id == "PEPTIDEK/2" and entry.sample_id == "treat_r2"
    )
    assert peptk_treat_r2.coeluting_transition_count == 1
    assert peptk_treat_r2.coeluting_transition_ids == ("y7",)
    assert peptk_treat_r2.noncoeluting_transition_ids == ("y8",)
    assert peptk_treat_r2.coelution_tier.value == "insufficient"
    assert peptk_treat_r2.reliable_transition_support is False
    assert peptk_treat_r2.reliability_reasons == (
        "fewer than two coeluting transitions support the target",
    )
    acdmpep_treat_r1 = next(
        entry
        for entry in report.target_entries
        if entry.target_id == "ACDMPEP/3" and entry.sample_id == "treat_r1"
    )
    assert acdmpep_treat_r1.coeluting_transition_count == 2
    assert acdmpep_treat_r1.coelution_tier.value == "reliable"
    assert acdmpep_treat_r1.absolute_alignment_delta_minutes == 1.25
    assert acdmpep_treat_r1.alignment_flagged is True


def test_build_targeted_transition_coelution_report_flags_transition_shift_and_missingness() -> (
    None
):
    import_report = build_skyline_result_import_report(
        _format_fixture("skyline_targeted_qc_results.tsv")
    )

    report = build_targeted_transition_coelution_report(import_report)

    shifted_transition = next(
        entry
        for entry in report.transition_entries
        if entry.target_id == "ACDMPEP/3"
        and entry.sample_id == "treat_r2"
        and entry.transition_id == "y5"
    )
    missing_transition = next(
        entry
        for entry in report.transition_entries
        if entry.target_id == "PEPTIDEK/2"
        and entry.sample_id == "treat_r2"
        and entry.transition_id == "y8"
    )
    assert shifted_transition.coeluting is True
    assert shifted_transition.coelution_delta_minutes == 0.0
    assert shifted_transition.reference_delta_minutes == 2.0
    assert shifted_transition.failure_reasons == (
        "transition is misaligned from the target reference window",
    )
    assert missing_transition.detected is False
    assert missing_transition.coeluting is False
    assert missing_transition.failure_reasons == ("transition not observed",)
