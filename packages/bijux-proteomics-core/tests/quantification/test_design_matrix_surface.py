# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

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
            metadata={"age_years": "41", "sex": "female"},
        ),
        ExperimentalDesignEntry(
            sample_id="t1",
            cohort="discovery",
            condition="treatment",
            replicate=1,
            fraction=1,
            spectra_file="t1.mzml",
            batch="batch-a",
            pair_id="pair-a",
            metadata={"age_years": "41", "sex": "female"},
        ),
        ExperimentalDesignEntry(
            sample_id="c2",
            cohort="validation",
            condition="control",
            replicate=2,
            fraction=1,
            spectra_file="c2.mzml",
            batch="batch-b",
            pair_id="pair-b",
            metadata={"age_years": "55", "sex": "male"},
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
            metadata={"age_years": "55", "sex": "male"},
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
    )

    assert report.sample_count == 4
    assert report.column_count == 5
    assert [column.column_name for column in report.columns] == [
        "intercept",
        "condition[treatment]",
        "batch[batch-b]",
        "pair_id[pair-b]",
        "covariate[age_years]",
    ]
    assert report.rows[0].sample_id == "c1"
    assert report.rows[0].pair_id == "pair-a"
    assert report.rows[0].metadata["sex"] == "female"
    assert report.rows[0].column_values == (1.0, 0.0, 0.0, 0.0, 41.0)
    assert report.rows[-1].column_values == (1.0, 1.0, 1.0, 1.0, 55.0)
    assert len(report.contrasts) == 1
    assert report.contrasts[0].contrast_name == "control_vs_treatment"
    assert report.contrasts[0].coefficient_weights == {
        "condition[treatment]": -1.0
    }
