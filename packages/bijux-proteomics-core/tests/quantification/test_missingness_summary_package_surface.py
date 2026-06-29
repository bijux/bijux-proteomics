# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.quantification.missingness import summaries


def test_missingness_summary_facade_exports_governed_owner_functions() -> None:
    assert tuple(summaries.__all__) == (
        "_build_missingness_condition_summary_report_pure",
        "_build_missingness_condition_summary_report_vectorized",
        "_build_missingness_entity_summary_report_pure",
        "_build_missingness_entity_summary_report_vectorized",
        "_summarize_missing_values_pure",
        "_summarize_missing_values_vectorized",
        "build_missingness_condition_summary_report",
        "build_missingness_entity_summary_report",
        "summarize_missing_values",
    )


def test_missingness_summary_facade_preserves_representative_exports() -> None:
    assert hasattr(summaries, "build_missingness_entity_summary_report")
    assert hasattr(summaries, "build_missingness_condition_summary_report")
    assert hasattr(summaries, "summarize_missing_values")
    assert hasattr(summaries, "_build_missingness_entity_summary_report_vectorized")
    assert hasattr(summaries, "_summarize_missing_values_pure")
