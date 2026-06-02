# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.io.formats import ExperimentalDesignEntry
from bijux_proteomics.quantification import parse_ms1_feature_table
from bijux_proteomics_runtime.workflows.runs import run_quant_workflow_end_to_end


def _fixture_path(name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures" / "ptm" / name


def test_run_quant_workflow_end_to_end_builds_review_bundle_runtime_report() -> None:
    features = parse_ms1_feature_table(
        _fixture_path("ptm_features.tsv")
    ).accepted_records
    design_entries = (
        ExperimentalDesignEntry(
            sample_id="C1",
            condition="control",
            replicate=1,
            fraction=1,
            spectra_file="c1.mzML",
            batch="B1",
        ),
        ExperimentalDesignEntry(
            sample_id="C2",
            condition="control",
            replicate=2,
            fraction=1,
            spectra_file="c2.mzML",
            batch="B2",
        ),
        ExperimentalDesignEntry(
            sample_id="T1",
            condition="treated",
            replicate=1,
            fraction=1,
            spectra_file="t1.mzML",
            batch="B1",
        ),
        ExperimentalDesignEntry(
            sample_id="T2",
            condition="treated",
            replicate=2,
            fraction=1,
            spectra_file="t2.mzML",
            batch="B2",
        ),
    )

    report = run_quant_workflow_end_to_end(features, design_entries=design_entries)

    assert report.status.value == "completed"
    assert report.feature_record_count == len(features)
    assert report.design_entry_count == 4
    assert report.condition_count == 2
    assert report.review_bundle_hash
    assert report.steps[-1].step_id == "review-bundle"
