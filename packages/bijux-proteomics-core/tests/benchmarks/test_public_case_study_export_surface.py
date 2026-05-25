# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.benchmarks import (
    build_lfq_cohort_biological_case_study_report,
    export_public_biological_case_study_report,
    write_public_biological_case_study_bundle,
)


def test_public_case_study_export_writes_summary_and_biological_report_bundle(
    tmp_path: Path,
) -> None:
    report = build_lfq_cohort_biological_case_study_report()

    manifest = write_public_biological_case_study_bundle(report, tmp_path)
    compatibility_manifest = export_public_biological_case_study_report(
        report,
        tmp_path / "compatibility",
    )

    summary_path = tmp_path / manifest.artifacts.summary_tsv
    biological_manifest_path = tmp_path / manifest.artifacts.biological_report_manifest_json
    assert summary_path.is_file()
    assert biological_manifest_path.is_file()
    assert "public_case_study:lfq_cohort_biological_case_study" in summary_path.read_text(
        encoding="utf-8"
    )
    assert "biological_report_summary.tsv" in biological_manifest_path.read_text(
        encoding="utf-8"
    )
    assert manifest.summary.go_enriched_term_count == 1
    assert compatibility_manifest.artifacts.summary_tsv == manifest.artifacts.summary_tsv
