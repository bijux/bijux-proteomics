# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

import pytest

from bijux_proteomics.io.formats import ExperimentalDesignEntry
from bijux_proteomics.study import (
    SampleRunAnalysisPolicy,
    build_sample_run_identity_report,
    resolve_sample_run_analysis_entries,
)


def _entry(
    *,
    sample_id: str,
    condition: str,
    spectra_file: str,
    technical_replicate_id: str | None = None,
    batch: str | None = None,
    metadata: dict[str, str] | None = None,
) -> ExperimentalDesignEntry:
    return ExperimentalDesignEntry(
        sample_id=sample_id,
        condition=condition,
        replicate=1,
        fraction=1,
        spectra_file=spectra_file,
        technical_replicate_id=technical_replicate_id,
        batch=batch,
        metadata=metadata or {},
    )


def test_sample_run_identity_report_combines_runs_by_explicit_policy() -> None:
    report = build_sample_run_identity_report(
        (
            _entry(
                sample_id="S1",
                condition="control",
                spectra_file="run-001",
                technical_replicate_id="tech-1",
            ),
            _entry(
                sample_id="S1",
                condition="control",
                spectra_file="run-002",
                technical_replicate_id="tech-2",
            ),
            _entry(
                sample_id="S2",
                condition="treated",
                spectra_file="run-003",
                technical_replicate_id="tech-3",
            ),
        ),
        policy=SampleRunAnalysisPolicy.COMBINE_TECHNICAL_RUNS,
    )

    assert report.summary.biological_sample_count == 2
    assert report.summary.run_count == 3
    assert report.summary.technical_replicate_count == 3
    assert report.summary.analysis_sample_count == 2
    assert report.summary.multi_run_sample_count == 1
    assert len(report.analysis_entries) == 2
    assert report.analysis_entries[0].sample_id == "S1"
    assert report.analysis_entries[0].metadata["run_ids"] == "run-001;run-002"
    assert report.run_assignments[0].analysis_sample_id == "S1"


def test_sample_run_identity_report_separates_runs_by_explicit_policy() -> None:
    report = build_sample_run_identity_report(
        (
            _entry(
                sample_id="S1",
                condition="control",
                spectra_file="run-001",
                technical_replicate_id="tech-1",
            ),
            _entry(
                sample_id="S1",
                condition="control",
                spectra_file="run-002",
                technical_replicate_id="tech-2",
            ),
        ),
        policy=SampleRunAnalysisPolicy.SEPARATE_TECHNICAL_RUNS,
    )

    assert report.summary.analysis_sample_count == 2
    assert {entry.sample_id for entry in report.analysis_entries} == {
        "S1__technical_replicate_tech-1",
        "S1__technical_replicate_tech-2",
    }
    assert all(
        entry.metadata["biological_sample_id"] == "S1"
        for entry in report.analysis_entries
    )


def test_sample_run_identity_report_blocks_conflicting_combined_batch_values() -> None:
    with pytest.raises(
        ValueError,
        match="requires one consistent 'batch' value across runs for biological sample 'S1'",
    ):
        resolve_sample_run_analysis_entries(
            (
                _entry(
                    sample_id="S1",
                    condition="control",
                    spectra_file="run-001",
                    batch="batch-a",
                ),
                _entry(
                    sample_id="S1",
                    condition="control",
                    spectra_file="run-002",
                    batch="batch-b",
                ),
            ),
            required_consistency_fields=("batch",),
        )
