# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.targeted import (
    build_skyline_result_import_report,
    build_targeted_matrix_report,
    render_targeted_matrix_flagged_tsv,
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

    assert "source_kind\ttransition_id\tprecursor_id\tpeptide_sequence" in observation_tsv
    assert "source_name\ttarget_count\tsample_count" in summary_tsv
    assert "target_id\tpeptide_sequence\tprotein_ref\tsource_transition_ids" in target_tsv
    assert "target_id\tsample_id\tsource_transition_ids\tintensity" in sample_tsv
    assert "target_id\tpeptide_sequence\tprotein_ref\tquality_flag_count" in flagged_tsv
    assert "skyline_export\ty8\tPEPTIDEK/2\tPEPTIDEK\tsample_B\t8000\t12.7\tinterference" in observation_tsv
    assert "Skyline\t2\t2\t3\t1\t2" in summary_tsv
    assert "PEPTIDEK/2\tPEPTIDEK\tP001\ty7;y8\t2\t281000\t140500\t12.55\t1\t1" in target_tsv
    assert "PEPTIDEK/2\tsample_B\ty7;y8\t123000\t12.55\tinterference\ttrue" in sample_tsv
    assert "PEPTIDEK/2\tPEPTIDEK\tP001\t1\t1" in flagged_tsv
