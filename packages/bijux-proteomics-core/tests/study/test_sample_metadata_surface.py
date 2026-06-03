# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.study import parse_sample_metadata_table


def test_parse_sample_metadata_table_preserves_optional_fields_and_summary(
    tmp_path: Path,
) -> None:
    path = tmp_path / "samples.tsv"
    path.write_text(
        "\n".join(
            (
                "sample_id\trun_id\tcondition\tbatch\tpair_id\ttimepoint\tplex_id\tchannel\tcohort",
                "ctrl-1\trun-1\tcontrol\tbatch-a\tpair-1\tt0\tplex-a\t126\tdiscovery",
                "case-1\trun-1\tcase\tbatch-a\tpair-1\tt1\tplex-a\t127N\tdiscovery",
            )
        )
        + "\n",
        encoding="utf-8",
    )

    report = parse_sample_metadata_table(path)

    assert report.summary.sample_count == 2
    assert report.summary.run_count == 1
    assert report.summary.condition_count == 2
    assert report.summary.paired_sample_count == 2
    assert report.summary.timepoint_sample_count == 2
    assert report.summary.multiplex_sample_count == 2
    assert not report.rejected_rows
    assert report.accepted_entries[0].metadata["cohort"] == "discovery"
    assert report.accepted_entries[1].channel == "127N"


def test_parse_sample_metadata_table_rejects_ambiguous_shared_runs_without_channels(
    tmp_path: Path,
) -> None:
    path = tmp_path / "samples.tsv"
    path.write_text(
        "\n".join(
            (
                "sample_id\trun_id\tcondition\tbatch",
                "ctrl-1\trun-1\tcontrol\tbatch-a",
                "case-1\trun-1\tcase\tbatch-a",
            )
        )
        + "\n",
        encoding="utf-8",
    )

    report = parse_sample_metadata_table(path)

    assert not report.accepted_entries
    assert len(report.rejected_rows) == 2
    assert {issue.code for row in report.rejected_rows for issue in row.issues} == {
        "ambiguous_shared_run"
    }


def test_parse_sample_metadata_table_rejects_duplicate_channel_assignments(
    tmp_path: Path,
) -> None:
    path = tmp_path / "samples.tsv"
    path.write_text(
        "\n".join(
            (
                "sample_id\trun_id\tcondition\tplex_id\tchannel",
                "ctrl-1\trun-1\tcontrol\tplex-a\t126",
                "case-1\trun-1\tcase\tplex-a\t126",
            )
        )
        + "\n",
        encoding="utf-8",
    )

    report = parse_sample_metadata_table(path)

    assert not report.accepted_entries
    assert len(report.rejected_rows) == 2
    assert {issue.code for row in report.rejected_rows for issue in row.issues} == {
        "duplicate_run_channel_assignment"
    }
