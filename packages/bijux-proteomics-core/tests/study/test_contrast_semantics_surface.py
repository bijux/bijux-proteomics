# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.domain import ContrastKind, SampleMetadata
from bijux_proteomics.study import (
    parse_study_contrast_specifications,
    parse_study_contrast_table,
)


def _sample_metadata() -> tuple[SampleMetadata, ...]:
    return (
        SampleMetadata(
            sample_id="ctrl-1",
            run_id="run-1",
            condition="control",
            pair_id="pair-a",
            timepoint="t0",
        ),
        SampleMetadata(
            sample_id="case-1",
            run_id="run-2",
            condition="case",
            pair_id="pair-a",
            timepoint="t1",
        ),
        SampleMetadata(
            sample_id="rescue-1",
            run_id="run-3",
            condition="rescue",
            pair_id="pair-b",
            timepoint="t2",
        ),
    )


def test_parse_study_contrast_specifications_supports_explicit_families() -> None:
    report = parse_study_contrast_specifications(
        (
            "case-control:case-control",
            "paired:case-control",
            "time-course:rescue-case",
            "multi-condition:control,case,rescue",
            "case-control",
        ),
        sample_metadata=_sample_metadata(),
    )

    assert not report.rejected_specifications
    assert report.summary.requested_specification_count == 5
    assert report.summary.expanded_contrast_count == 7
    assert report.summary.case_control_count == 1
    assert report.summary.paired_count == 1
    assert report.summary.time_course_count == 1
    assert report.summary.multi_condition_count == 3
    assert report.summary.pairwise_count == 1
    assert report.contrasts[0].kind is ContrastKind.CASE_CONTROL
    assert report.contrasts[1].pair_id_field == "pair_id"
    assert report.contrasts[2].timepoint_field == "timepoint"
    assert report.contrasts[3].condition_set == ("control", "case", "rescue")


def test_parse_study_contrast_specifications_rejects_missing_semantic_support() -> None:
    report = parse_study_contrast_specifications(
        (
            "paired:case-rescue",
            "multi-condition:control,missing,rescue",
        ),
        sample_metadata=_sample_metadata(),
    )

    assert not report.contrasts
    issue_codes = {
        issue.code
        for rejected in report.rejected_specifications
        for issue in rejected.issues
    }
    assert "missing_paired_comparison" in issue_codes
    assert "unknown_condition" in issue_codes


def test_parse_study_contrast_table_expands_multi_condition_rows(
    tmp_path: Path,
) -> None:
    path = tmp_path / "contrasts.tsv"
    path.write_text(
        "\n".join(
            (
                "contrast_id\tkind\tleft_condition\tright_condition\tcondition_set\tpair_id_field\ttimepoint_field",
                "case_vs_control\tcase_control\tcase\tcontrol\t\t\t",
                "paired_case_vs_control\tpaired\tcase\tcontrol\t\tpair_id\t",
                "trajectory\ttime_course\trescue\tcase\t\t\ttimepoint",
                "all_conditions\tmulti_condition\t\t\tcontrol,case,rescue\t\t",
            )
        )
        + "\n",
        encoding="utf-8",
    )

    report = parse_study_contrast_table(path, sample_metadata=_sample_metadata())

    assert not report.rejected_specifications
    assert report.summary.requested_specification_count == 4
    assert report.summary.expanded_contrast_count == 6
    assert report.summary.multi_condition_count == 3
    contrast_ids = {contrast.contrast_id for contrast in report.contrasts}
    assert "case_vs_control" in contrast_ids
    assert "all_conditions__control__vs__case" in contrast_ids
