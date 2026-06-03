# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.io.formats import (
    ExperimentalDesignEntry,
    parse_experimental_design_table,
)
from bijux_proteomics.study import (
    SampleSheetRepairConfidence,
    build_sample_sheet_repair_suggestion_report,
    render_sample_sheet_repair_suggestions_tsv,
)


def test_sample_sheet_repairs_detect_missing_metadata_sample_and_run_mismatch(
    tmp_path: Path,
) -> None:
    design_path = tmp_path / "design.tsv"
    design_path.write_text(
        "\n".join(
            (
                "sample_id\tcondition\treplicate\tfraction\tspectra_file",
                "control_1\tcontrol\t1\t1\tcontrol_1.raw",
                "treated_1\ttreatment\t1\t1\tmissing_run.raw",
            )
        )
        + "\n",
        encoding="utf-8",
    )

    report = build_sample_sheet_repair_suggestion_report(
        parse_experimental_design_table(design_path),
        observed_sample_ids=("control_1", "treated_1", "treated_2"),
        observed_run_ids=("control_1.raw", "treated_1.raw", "treated_2.raw"),
    )

    missing_sample = next(
        suggestion
        for suggestion in report.suggestions
        if suggestion.code == "missing_metadata_sample"
    )
    run_mismatch = next(
        suggestion
        for suggestion in report.suggestions
        if suggestion.code == "metadata_run_mismatch"
    )

    assert report.summary.missing_metadata_sample_count == 1
    assert report.summary.metadata_run_mismatch_count == 1
    assert missing_sample.confidence is SampleSheetRepairConfidence.HIGH
    assert missing_sample.suggested_fields["sample_id"] == "treated_2"
    assert missing_sample.suggested_fields["spectra_file"] == "treated_2.raw"
    assert run_mismatch.current_value == "missing_run.raw"
    assert run_mismatch.suggested_value == "treated_1.raw"
    assert (
        "confidence"
        in render_sample_sheet_repair_suggestions_tsv(report).splitlines()[0]
    )


def test_sample_sheet_repairs_detect_singleton_condition_typo() -> None:
    report = build_sample_sheet_repair_suggestion_report(
        (
            ExperimentalDesignEntry(
                sample_id="control_1",
                condition="control",
                replicate=1,
                fraction=1,
                spectra_file="control_1.raw",
            ),
            ExperimentalDesignEntry(
                sample_id="control_2",
                condition="control",
                replicate=2,
                fraction=1,
                spectra_file="control_2.raw",
            ),
            ExperimentalDesignEntry(
                sample_id="treated_1",
                condition="treated",
                replicate=1,
                fraction=1,
                spectra_file="treated_1.raw",
            ),
            ExperimentalDesignEntry(
                sample_id="treated_2",
                condition="treated",
                replicate=2,
                fraction=1,
                spectra_file="treated_2.raw",
            ),
            ExperimentalDesignEntry(
                sample_id="treated_3",
                condition="treatd",
                replicate=3,
                fraction=1,
                spectra_file="treated_3.raw",
            ),
        )
    )

    suggestion = next(
        suggestion
        for suggestion in report.suggestions
        if suggestion.code == "singleton_condition_typo"
    )

    assert report.summary.singleton_condition_typo_count == 1
    assert suggestion.current_value == "treatd"
    assert suggestion.suggested_value == "treated"
    assert suggestion.confidence is SampleSheetRepairConfidence.HIGH


def test_sample_sheet_repairs_detect_missing_technical_replicate_ids() -> None:
    report = build_sample_sheet_repair_suggestion_report(
        (
            ExperimentalDesignEntry(
                sample_id="sample_1",
                condition="control",
                replicate=1,
                fraction=1,
                spectra_file="sample_1_run_a.raw",
            ),
            ExperimentalDesignEntry(
                sample_id="sample_1",
                condition="control",
                replicate=1,
                fraction=1,
                spectra_file="sample_1_run_b.raw",
            ),
            ExperimentalDesignEntry(
                sample_id="sample_2",
                condition="treatment",
                replicate=1,
                fraction=1,
                spectra_file="sample_2_run_a.raw",
                technical_replicate_id="tech-1",
            ),
        )
    )

    suggestions = [
        suggestion
        for suggestion in report.suggestions
        if suggestion.code == "missing_technical_replicate_id"
    ]

    assert report.summary.missing_technical_replicate_id_count == 2
    assert {suggestion.suggested_value for suggestion in suggestions} == {
        "sample_1_run_a",
        "sample_1_run_b",
    }
    assert all(
        suggestion.confidence is SampleSheetRepairConfidence.HIGH
        for suggestion in suggestions
    )


def test_sample_sheet_repairs_preserve_parse_rejected_row_count(
    tmp_path: Path,
) -> None:
    path = tmp_path / "invalid_design.tsv"
    path.write_text(
        "\n".join(
            (
                "sample_id\tcondition\treplicate\tfraction\tspectra_file\tsample_role",
                "s1\tcontrol\t1\t1\trun-001.raw\tqc_bridge",
            )
        )
        + "\n",
        encoding="utf-8",
    )
    report = build_sample_sheet_repair_suggestion_report(
        parse_experimental_design_table(path)
    )

    assert report.parse_rejected_row_count == 1
    assert report.summary.suggestion_count == 0
