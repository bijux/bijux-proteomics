# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

import pytest

from bijux_proteomics.io.formats import ExperimentalDesignEntry
from bijux_proteomics.quantification import build_quant_design_matrix_report


def _design() -> tuple[ExperimentalDesignEntry, ...]:
    return (
        ExperimentalDesignEntry(
            sample_id="c1",
            cohort="discovery",
            condition="control",
            replicate=1,
            fraction=1,
            spectra_file="c1.mzml",
            batch="batch-a",
            pair_id="pair-a",
            metadata={"age_years": "40", "sex": "female", "timepoint": "t0"},
        ),
        ExperimentalDesignEntry(
            sample_id="t1",
            cohort="discovery",
            condition="treatment",
            replicate=1,
            fraction=1,
            spectra_file="t1.mzml",
            batch="batch-b",
            pair_id="pair-a",
            metadata={"age_years": "43", "sex": "female", "timepoint": "t1"},
        ),
        ExperimentalDesignEntry(
            sample_id="c2",
            cohort="validation",
            condition="control",
            replicate=2,
            fraction=1,
            spectra_file="c2.mzml",
            batch="batch-a",
            pair_id="pair-b",
            metadata={"age_years": "51", "sex": "male", "timepoint": "t1"},
        ),
        ExperimentalDesignEntry(
            sample_id="t2",
            cohort="validation",
            condition="treatment",
            replicate=2,
            fraction=1,
            spectra_file="t2.mzml",
            batch="batch-b",
            pair_id="pair-b",
            metadata={"age_years": "47", "sex": "male", "timepoint": "t0"},
        ),
        ExperimentalDesignEntry(
            sample_id="c3",
            cohort="validation",
            condition="control",
            replicate=3,
            fraction=1,
            spectra_file="c3.mzml",
            batch="batch-b",
            pair_id="pair-c",
            metadata={"age_years": "59", "sex": "female", "timepoint": "t0"},
        ),
        ExperimentalDesignEntry(
            sample_id="t3",
            cohort="validation",
            condition="treatment",
            replicate=3,
            fraction=1,
            spectra_file="t3.mzml",
            batch="batch-a",
            pair_id="pair-c",
            metadata={"age_years": "64", "sex": "female", "timepoint": "t1"},
        ),
        ExperimentalDesignEntry(
            sample_id="c4",
            cohort="validation",
            condition="control",
            replicate=4,
            fraction=1,
            spectra_file="c4.mzml",
            batch="batch-b",
            pair_id="pair-d",
            metadata={"age_years": "73", "sex": "male", "timepoint": "t1"},
        ),
        ExperimentalDesignEntry(
            sample_id="t4",
            cohort="validation",
            condition="treatment",
            replicate=4,
            fraction=1,
            spectra_file="t4.mzml",
            batch="batch-a",
            pair_id="pair-d",
            metadata={"age_years": "67", "sex": "male", "timepoint": "t0"},
        ),
    )


def test_build_quant_design_matrix_report_preserves_condition_batch_pairing_and_covariates() -> (
    None
):
    report = build_quant_design_matrix_report(
        _design(),
        batch_field="batch",
        pairing_field="pair_id",
        covariate_fields=("age_years",),
        timepoint_field="timepoint",
    )

    assert report.sample_count == 8
    assert report.column_count == 8
    assert report.timepoint_field == "timepoint"
    assert [column.column_name for column in report.columns] == [
        "intercept",
        "condition[treatment]",
        "batch[batch-b]",
        "pair_id[pair-b]",
        "pair_id[pair-c]",
        "pair_id[pair-d]",
        "timepoint[t1]",
        "covariate[age_years]",
    ]
    assert report.rows[0].sample_id == "c1"
    assert report.rows[0].pair_id == "pair-a"
    assert report.rows[0].metadata["sex"] == "female"
    assert report.rows[0].metadata["timepoint"] == "t0"
    assert report.rows[0].column_values == (1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 40.0)
    assert report.rows[-1].column_values == (
        1.0,
        1.0,
        0.0,
        0.0,
        0.0,
        1.0,
        0.0,
        67.0,
    )
    assert len(report.contrasts) == 1
    assert report.contrasts[0].contrast_name == "control_vs_treatment"
    assert report.contrasts[0].coefficient_weights == {
        "condition[treatment]": -1.0
    }
    assert report.contrasts[0].coefficient_vector == (
        0.0,
        -1.0,
        0.0,
        0.0,
        0.0,
        0.0,
        0.0,
        0.0,
    )


def test_build_quant_design_matrix_report_blocks_confounded_designs() -> None:
    confounded_design = (
        ExperimentalDesignEntry(
            sample_id="c1",
            condition="control",
            replicate=1,
            fraction=1,
            spectra_file="c1.mzml",
            batch="batch-a",
            pair_id="pair-a",
            metadata={"timepoint": "t0", "age_years": "40"},
        ),
        ExperimentalDesignEntry(
            sample_id="t1",
            condition="treatment",
            replicate=1,
            fraction=1,
            spectra_file="t1.mzml",
            batch="batch-b",
            pair_id="pair-b",
            metadata={"timepoint": "t1", "age_years": "60"},
        ),
        ExperimentalDesignEntry(
            sample_id="c2",
            condition="control",
            replicate=2,
            fraction=1,
            spectra_file="c2.mzml",
            batch="batch-a",
            pair_id="pair-a",
            metadata={"timepoint": "t0", "age_years": "40"},
        ),
        ExperimentalDesignEntry(
            sample_id="t2",
            condition="treatment",
            replicate=2,
            fraction=1,
            spectra_file="t2.mzml",
            batch="batch-b",
            pair_id="pair-b",
            metadata={"timepoint": "t1", "age_years": "60"},
        ),
    )

    with pytest.raises(
        ValueError,
        match="design matrix is confounded or rank-deficient; aliased columns:",
    ):
        build_quant_design_matrix_report(
            confounded_design,
            batch_field="batch",
            pairing_field="pair_id",
            timepoint_field="timepoint",
            covariate_fields=("age_years",),
        )
