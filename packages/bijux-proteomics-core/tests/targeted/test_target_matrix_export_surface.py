# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.targeted import (
    build_skyline_result_import_report,
    build_targeted_matrix_report,
    render_targeted_matrix_excluded_transition_tsv,
    render_targeted_matrix_flagged_tsv,
    render_targeted_matrix_missingness_tsv,
    render_targeted_matrix_retained_transition_tsv,
    render_targeted_matrix_sample_tsv,
    render_targeted_matrix_summary_tsv,
    render_targeted_matrix_target_tsv,
    render_targeted_result_observation_tsv,
)


def _format_fixture(name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures" / "formats" / name


def test_render_targeted_exports_keep_observations_and_flags_visible() -> None:
    import_report = build_skyline_result_import_report(
        _format_fixture("skyline_targeted_results.tsv")
    )
    matrix_report = build_targeted_matrix_report(import_report)

    observation_tsv = render_targeted_result_observation_tsv(import_report)
    summary_tsv = render_targeted_matrix_summary_tsv(matrix_report)
    target_tsv = render_targeted_matrix_target_tsv(matrix_report)
    sample_tsv = render_targeted_matrix_sample_tsv(matrix_report)
    flagged_tsv = render_targeted_matrix_flagged_tsv(matrix_report)
    retained_tsv = render_targeted_matrix_retained_transition_tsv(matrix_report)
    excluded_tsv = render_targeted_matrix_excluded_transition_tsv(matrix_report)
    missingness_tsv = render_targeted_matrix_missingness_tsv(matrix_report)

    assert (
        "source_kind\ttransition_id\tprecursor_id\tprecursor_charge\tpeptide_sequence"
        in observation_tsv
    )
    assert "source_name\ttarget_count\tsample_count" in summary_tsv
    assert (
        "target_id\tpeptide_sequence\tprotein_ref\tsource_transition_ids" in target_tsv
    )
    assert (
        "target_id\tsample_id\tsource_transition_ids\tretained_transition_ids\texcluded_transition_ids\tobserved_transition_count"
        in sample_tsv
    )
    assert "target_id\tpeptide_sequence\tprotein_ref\tquality_flag_count" in flagged_tsv
    assert "target_id\tsample_id\ttransition_id\tintensity" in retained_tsv
    assert "target_id\tsample_id\ttransition_id\tintensity" in excluded_tsv
    assert "target_id\tsample_id\tobserved_transition_count" in missingness_tsv
    assert (
        "skyline_export\ty8\tPEPTIDEK/2\t2\tPEPTIDEK\tsample_B\t8000\t12.7\tinterference"
        in observation_tsv
    )
    assert "Skyline\t2\t2\t3\t1\t0\t4\t2\t2" in summary_tsv
    assert (
        "PEPTIDEK/2\tPEPTIDEK\tP001\ty7;y8\ty7;y8\ty8\t2\t1\t2\t273000\t136500\t12.5\t1\t1"
        in target_tsv
    )
    assert (
        "PEPTIDEK/2\tsample_B\ty7;y8\ty7\ty8\t2\t1\t1\t115000\t12.4\tinterference\t\ttrue"
        in sample_tsv
    )
    assert "PEPTIDEK/2\tPEPTIDEK\tP001\t1\t1" in flagged_tsv
    assert "PEPTIDEK/2\tsample_B\ty7\t115000\t12.4\tpass" in retained_tsv
    assert (
        "PEPTIDEK/2\tsample_B\ty8\t8000\t12.7\tinterference\tquality_filter"
        in excluded_tsv
    )
    assert "ACDMPEP/3\tsample_B\t0\t0\t0\ttrue\tno_observation" in missingness_tsv
