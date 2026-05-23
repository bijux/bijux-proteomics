# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

import bijux_proteomics.targeted as targeted


def _format_fixture(name: str) -> Path:
    return Path(__file__).resolve().parents[1] / "fixtures" / "formats" / name


def test_targeted_package_exports_target_matrix_owner_surface() -> None:
    report = targeted.build_skyline_targeted_matrix_report(
        _format_fixture("skyline_targeted_results.tsv")
    )
    rendered = targeted.render_targeted_matrix_missingness_tsv(report)

    assert hasattr(targeted, "build_targeted_matrix_report")
    assert hasattr(targeted, "render_targeted_matrix_retained_transition_tsv")
    assert hasattr(targeted, "render_targeted_matrix_excluded_transition_tsv")
    assert hasattr(targeted, "render_targeted_matrix_missingness_tsv")
    assert report.summary.retained_transition_count == 4
    assert report.rows[1].total_intensity == 273000.0
    assert "no_observation" in rendered
