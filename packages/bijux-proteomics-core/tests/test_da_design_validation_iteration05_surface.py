# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.formats import ExperimentalDesignEntry
from bijux_proteomics.quantification_iteration05 import (
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
