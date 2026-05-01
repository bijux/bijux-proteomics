# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.study_metadata_iteration08 import (
    StudyMetadataRecord,
    build_sample_lineage_report,
)


def test_build_sample_lineage_report_marks_missing_surface_links() -> None:
    metadata = (
        StudyMetadataRecord(
            study_id="S-001",
            cohort_id="C-1",
            condition_id="control",
            sample_id="sample-01",
            replicate_id="R1",
            fraction_id="F1",
            instrument_id="inst-a",
            run_id="run-001",
            batch_id="B1",
        ),
        StudyMetadataRecord(
            study_id="S-001",
            cohort_id="C-1",
            condition_id="treated",
            sample_id="sample-02",
            replicate_id="R1",
            fraction_id="F1",
            instrument_id="inst-a",
            run_id="run-002",
            batch_id="B1",
        ),
    )
    report = build_sample_lineage_report(
        metadata,
        identification_samples=("sample-01", "sample-02"),
        quant_samples=("sample-01", "sample-02"),
        ptm_samples=("sample-01",),
        qc_samples=("sample-01", "sample-02"),
        evidence_samples=("sample-01", "sample-02"),
        lab_samples=("sample-01",),
    )

    assert report.fully_traced_sample_count == 1
    assert report.missing_lineage_sample_count == 1
    missing = next(entry for entry in report.entries if entry.sample_id == "sample-02")
    assert "ptm" in missing.missing_surfaces
    assert "lab" in missing.missing_surfaces
