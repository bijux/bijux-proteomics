# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.study import (
    StudyMetadataRecord,
    validate_experimental_design_records,
)


def test_validate_experimental_design_records_rejects_invalid_design_cases() -> None:
    records = (
        StudyMetadataRecord(
            study_id="S-001",
            cohort_id="C-1",
            condition_id="control",
            sample_id="sample-01",
            replicate_id="R1",
            fraction_id="fraction-1",
            instrument_id="inst-a",
            run_id="run-001",
            batch_id="B1",
            multiplex_channel="bad-channel",
            spectra_file="missing.mzML",
        ),
        StudyMetadataRecord(
            study_id="S-001",
            cohort_id="C-1",
            condition_id="control",
            sample_id="sample-01",
            replicate_id="R2",
            fraction_id="F2",
            instrument_id="inst-a",
            run_id="run-002",
            batch_id="B1",
            multiplex_channel="126",
            spectra_file="present.mzML",
        ),
        StudyMetadataRecord(
            study_id="S-001",
            cohort_id="C-1",
            condition_id="treated",
            sample_id="sample-03",
            replicate_id="R1",
            fraction_id="F1",
            instrument_id="inst-a",
            run_id="run-003",
            batch_id="B2",
            spectra_file="present.mzML",
        ),
    )
    report = validate_experimental_design_records(
        records,
        expected_spectra_files=("present.mzML",),
    )

    codes = {issue.code for issue in report.issues}
    assert report.valid is False
    assert "duplicate_sample_id" in codes
    assert "invalid_fraction_id" in codes
    assert "invalid_multiplex_channel" in codes
    assert "inconsistent_spectra_file" in codes
    assert "missing_replicates" in codes
