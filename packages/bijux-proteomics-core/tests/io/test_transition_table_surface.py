# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.io import parse_transition_table


def _format_fixture(name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures" / "formats" / name


def test_parse_transition_table_accepts_transition_observations() -> None:
    report = parse_transition_table(_format_fixture("transition_quant.tsv"))

    assert report.rejected_rows == ()
    assert len(report.accepted_entries) == 7
    assert report.accepted_entries[0].transition_id == "tr_y7_a"
    assert report.accepted_entries[0].precursor_id == "prec_a"
    assert report.accepted_entries[0].precursor_charge == 2
    assert report.accepted_entries[0].sample_id == "s1"
    assert report.accepted_entries[0].peptide_sequence == "PEPTIDEK"
    assert report.accepted_entries[0].fragment_label == "y7"
    assert report.accepted_entries[0].retention_time_minutes == 12.5
    assert report.accepted_entries[0].metadata["platform"] == "prm"
    assert report.accepted_entries[-1].precursor_charge == 3
    assert report.accepted_entries[-1].sample_id == "s3"


def test_parse_transition_table_rejects_rows_without_precursor_id() -> None:
    report = parse_transition_table(_format_fixture("transition_quant.invalid.tsv"))

    assert report.accepted_entries == ()
    assert len(report.rejected_rows) == 1
    assert report.rejected_rows[0].reason == "transition row requires precursor_id"


def test_parse_transition_table_rejects_negative_intensity_and_invalid_q_value(
    tmp_path: Path,
) -> None:
    table_path = tmp_path / "transition_quant.invalid_values.tsv"
    table_path.write_text(
        "\n".join(
            (
                "transition\tprecursor\tcharge\tsample\tarea\tqvalue",
                "tr_a\tprec_a\t2\ts1\t-5\t0.01",
                "tr_b\tprec_b\t2\ts2\t10\t1.5",
            )
        )
        + "\n",
        encoding="utf-8",
    )

    report = parse_transition_table(table_path)

    assert report.accepted_entries == ()
    assert len(report.rejected_rows) == 2
    assert "negative numeric value" in report.rejected_rows[0].reason
    assert "invalid q-value" in report.rejected_rows[1].reason


def test_parse_transition_table_requires_charge_but_keeps_retention_time_optional(
    tmp_path: Path,
) -> None:
    table_path = tmp_path / "transition_quant_charge.tsv"
    table_path.write_text(
        "\n".join(
            (
                "transition\tprecursor\tcharge\tsample\tarea\trt",
                "tr_a\tprec_a\t2\ts1\t10\t",
                "tr_b\tprec_b\t\ts2\t20\t12.5",
            )
        )
        + "\n",
        encoding="utf-8",
    )

    report = parse_transition_table(table_path)

    assert len(report.accepted_entries) == 1
    assert report.accepted_entries[0].transition_id == "tr_a"
    assert report.accepted_entries[0].retention_time_minutes is None
    assert len(report.rejected_rows) == 1
    assert report.rejected_rows[0].reason == "transition row requires precursor_charge"


def test_parse_transition_table_rejects_duplicates_only_within_sample_and_precursor(
    tmp_path: Path,
) -> None:
    table_path = tmp_path / "transition_quant_duplicates.tsv"
    table_path.write_text(
        "\n".join(
            (
                "transition\tprecursor\tcharge\tsample\tarea\tfragment\tproduct_mz",
                "tr_shared\tprec_a\t2\ts1\t10\ty7\t700.1",
                "tr_shared\tprec_b\t3\ts1\t20\ty7\t710.1",
                "tr_shared\tprec_a\t2\ts1\t30\ty8\t720.1",
            )
        )
        + "\n",
        encoding="utf-8",
    )

    report = parse_transition_table(table_path)

    assert len(report.accepted_entries) == 1
    assert report.accepted_entries[0].precursor_id == "prec_b"
    assert len(report.rejected_rows) == 2
    assert all("duplicate" in row.reason.lower() for row in report.rejected_rows)
