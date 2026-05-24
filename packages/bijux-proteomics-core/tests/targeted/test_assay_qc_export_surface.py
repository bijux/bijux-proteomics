# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.io import parse_experimental_design_table
from bijux_proteomics.targeted import (
    build_skyline_result_import_report,
    build_targeted_assay_qc_report,
    render_targeted_assay_qc_coelution_tsv,
    render_targeted_assay_qc_fragment_ratio_tsv,
    render_targeted_assay_qc_replicate_cv_tsv,
    render_targeted_assay_qc_retention_tsv,
    render_targeted_assay_qc_summary_tsv,
    render_targeted_assay_qc_target_tsv,
    render_targeted_assay_qc_transition_coelution_tsv,
    render_targeted_assay_qc_transition_tsv,
    render_targeted_assay_qc_transition_qc_tsv,
    render_targeted_assay_qc_unreliable_tsv,
)


def _format_fixture(name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures" / "formats" / name


def test_render_targeted_assay_qc_exports_keep_review_evidence_visible() -> None:
    import_report = build_skyline_result_import_report(
        _format_fixture("skyline_targeted_qc_results.tsv")
    )
    design_entries = parse_experimental_design_table(
        _format_fixture("skyline_targeted_qc.design.tsv")
    ).accepted_entries
    report = build_targeted_assay_qc_report(import_report, design_entries)

    summary_tsv = render_targeted_assay_qc_summary_tsv(report)
    target_qc_tsv = render_targeted_assay_qc_target_tsv(report)
    transition_tsv = render_targeted_assay_qc_transition_tsv(report)
    coelution_tsv = render_targeted_assay_qc_coelution_tsv(report)
    transition_coelution_tsv = render_targeted_assay_qc_transition_coelution_tsv(report)
    transition_qc_tsv = render_targeted_assay_qc_transition_qc_tsv(report)
    fragment_tsv = render_targeted_assay_qc_fragment_ratio_tsv(report)
    retention_tsv = render_targeted_assay_qc_retention_tsv(report)
    replicate_tsv = render_targeted_assay_qc_replicate_cv_tsv(report)
    unreliable_tsv = render_targeted_assay_qc_unreliable_tsv(report)

    assert "source_name\ttarget_count\tsample_count\ttarget_qc_entry_count" in summary_tsv
    assert (
        "Skyline\t2\t4\t8\t1\t8\t8\t3\t16\t14\t16\t8\t14\t4\t1\t2\t8\t2\t4\t1\t8\t2"
        in summary_tsv
    )
    assert (
        "PEPTIDEK/2\ttreat_r1\ttreatment\t2\t2\t2\ty7;y8\t1\ty7\ty8\t102000\t12.85\t12.6\t0.25\t1\t0.106733\tfalse\t0.875\tfalse\tfewer than two coeluting transitions pass transition-quality review"
        in target_qc_tsv
    )
    assert "PEPTIDEK/2\ttreat_r2\t1\t2\t0.5" in transition_tsv
    assert (
        "PEPTIDEK/2\ttreat_r2\t2\t1\t1\ty7\ty8\ty7\t13.3\t13.3\t12.6\t0.7\tfalse\tinsufficient\tfalse\tfewer than two coeluting transitions support the target"
        in coelution_tsv
    )
    assert (
        "ACDMPEP/3\ttreat_r2\ty5\ttrue\t20.2\ty5\t20.2\t18.2\t0\t2\ttrue\ttransition is misaligned from the target reference window"
        in transition_coelution_tsv
    )
    assert (
        "PEPTIDEK/2\ttreat_r2\ttreatment\ty8\tfalse\t\t\t\t\t\t\tfalse\tfalse\tfalse\t\t\tfalse\tfalse\tfalse\tfalse\tfalse\ttransition not observed"
        in transition_qc_tsv
    )
    assert (
        "PEPTIDEK/2\ttreat_r1\ty8\t12000\t114000\t0.105263\t0.236842\t0.131579\t0.396731\ttrue\ttrue\ttrue"
        in fragment_tsv
    )
    assert "ACDMPEP/3\ttreat_r2\t1\t20.2\t18.2\t2\ttrue" in retention_tsv
    assert "ACDMPEP/3\ttreatment\t2\t2\t35000\t0.525279\ttrue" in replicate_tsv
    assert (
        "PEPTIDEK/2\ttreat_r1\ttreatment\ty8\tinterference\tfewer than two coeluting transitions pass transition-quality review; fragment-ion ratios deviate from the cross-run reference pattern; source quality flags require review"
        in unreliable_tsv
    )
