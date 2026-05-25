# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.io.formats import ExperimentalDesignEntry
from bijux_proteomics.quantification.review import (
    validate_differential_abundance_design_context,
)


def _design() -> tuple[ExperimentalDesignEntry, ...]:
    return (
        ExperimentalDesignEntry(
            sample_id="s1",
            condition="case",
            replicate=1,
            fraction=1,
            spectra_file="s1.mzml",
            batch="b1",
        ),
        ExperimentalDesignEntry(
            sample_id="s2",
            condition="case",
            replicate=2,
            fraction=1,
            spectra_file="s2.mzml",
            batch="b1",
        ),
        ExperimentalDesignEntry(
            sample_id="s3",
            condition="ctrl",
            replicate=1,
            fraction=1,
            spectra_file="s3.mzml",
            batch="b2",
        ),
    )


def test_validate_differential_abundance_design_context_reports_contrast_and_replicate_issues() -> (
    None
):
    report = validate_differential_abundance_design_context(
        _design(),
        contrasts=(("case", "ctrl"), ("ctrl", "ctrl"), ("case", "missing")),
        covariates=("batch", "instrument", "unknown_cov"),
        min_replicates_per_condition=2,
        multiple_testing_scope="per_contrast",
    )

    assert report.valid is False
    issue_codes = {issue.code for issue in report.issues}
    assert "degenerate_contrast" in issue_codes
    assert "unknown_contrast_condition" in issue_codes
    assert "insufficient_replicates" in issue_codes


def test_validate_differential_abundance_design_context_ignores_technical_run_inflation() -> (
    None
):
    report = validate_differential_abundance_design_context(
        (
            ExperimentalDesignEntry(
                sample_id="case-1",
                condition="case",
                replicate=1,
                fraction=1,
                spectra_file="case-1_run-1.mzml",
                technical_replicate_id="tech-1",
            ),
            ExperimentalDesignEntry(
                sample_id="case-1",
                condition="case",
                replicate=1,
                fraction=1,
                spectra_file="case-1_run-2.mzml",
                technical_replicate_id="tech-2",
            ),
            ExperimentalDesignEntry(
                sample_id="ctrl-1",
                condition="ctrl",
                replicate=1,
                fraction=1,
                spectra_file="ctrl-1_run-1.mzml",
                technical_replicate_id="tech-3",
            ),
            ExperimentalDesignEntry(
                sample_id="ctrl-1",
                condition="ctrl",
                replicate=1,
                fraction=1,
                spectra_file="ctrl-1_run-2.mzml",
                technical_replicate_id="tech-4",
            ),
        ),
        contrasts=(("case", "ctrl"),),
        min_replicates_per_condition=2,
    )

    assert report.valid is False
    assert any(issue.code == "insufficient_replicates" for issue in report.issues)
