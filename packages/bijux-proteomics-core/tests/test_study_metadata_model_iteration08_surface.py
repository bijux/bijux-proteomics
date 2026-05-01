# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.study_metadata_iteration08 import (
    StudyMetadataRecord,
    build_study_metadata_model,
)


def test_build_study_metadata_model_counts_studies_samples_and_runs() -> None:
    records = (
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

    model = build_study_metadata_model(records)

    assert model.study_count == 1
    assert model.sample_count == 2
    assert model.run_count == 2
