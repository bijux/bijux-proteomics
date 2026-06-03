# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.io.formats import ExperimentalDesignEntry
from bijux_proteomics.lab import check_cohort_balance, render_cohort_balance_tsv


def _entry(
    *,
    sample_id: str,
    condition: str,
    replicate: int,
    metadata: dict[str, str] | None = None,
) -> ExperimentalDesignEntry:
    return ExperimentalDesignEntry(
        sample_id=sample_id,
        condition=condition,
        replicate=replicate,
        fraction=1,
        spectra_file=f"{sample_id}.mzml",
        metadata=metadata or {},
    )


def test_check_cohort_balance_blocks_condition_confounded_covariate() -> None:
    rows = check_cohort_balance(
        (
            _entry(
                sample_id="control_1",
                condition="control",
                replicate=1,
                metadata={"sex": "female"},
            ),
            _entry(
                sample_id="control_2",
                condition="control",
                replicate=2,
                metadata={"sex": "female"},
            ),
            _entry(
                sample_id="case_1",
                condition="case",
                replicate=1,
                metadata={"sex": "male"},
            ),
            _entry(
                sample_id="case_2",
                condition="case",
                replicate=2,
                metadata={"sex": "male"},
            ),
        )
    )
    lookup = {row.covariate: row for row in rows}

    sex = lookup["sex"]
    assert sex.group_counts == "female[case=0,control=2];male[case=2,control=0]"
    assert sex.imbalance_score == 1.0
    assert sex.confounded_with_condition is True
    assert "blocks naive subgroup interpretation" in sex.analysis_warning


def test_check_cohort_balance_renders_tsv_and_keeps_balanced_covariate_unblocked() -> (
    None
):
    rows = check_cohort_balance(
        (
            _entry(
                sample_id="control_1",
                condition="control",
                replicate=1,
                metadata={"sex": "female", "site": "north"},
            ),
            _entry(
                sample_id="control_2",
                condition="control",
                replicate=2,
                metadata={"sex": "male", "site": "south"},
            ),
            _entry(
                sample_id="case_1",
                condition="case",
                replicate=1,
                metadata={"sex": "female", "site": "north"},
            ),
            _entry(
                sample_id="case_2",
                condition="case",
                replicate=2,
                metadata={"sex": "male", "site": "south"},
            ),
        )
    )
    lookup = {row.covariate: row for row in rows}
    rendered = render_cohort_balance_tsv(rows)

    assert lookup["sex"].confounded_with_condition is False
    assert lookup["sex"].imbalance_score == 0.0
    assert "without blocking subgroup interpretation" in lookup["sex"].analysis_warning
    assert rendered.startswith(
        "covariate\tgroup_counts\timbalance_score\tconfounded_with_condition\tanalysis_warning\n"
    )
