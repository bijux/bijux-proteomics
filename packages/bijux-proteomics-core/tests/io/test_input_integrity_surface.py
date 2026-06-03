# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

import pytest

from bijux_proteomics.io.input_integrity import (
    render_input_integrity_issues_tsv,
    scan_input_integrity,
)


def test_scan_input_integrity_detects_expected_row_level_failures(
    tmp_path: Path,
) -> None:
    invalid_tsv = tmp_path / "invalid_quant.tsv"
    invalid_tsv.write_text(
        ("sample_id\tintensity\tprotein_id\nS1\t100.0\tP1\nS1\tbad\tP2\n\t42.0\tP3\n"),
        encoding="utf-8",
    )
    inconsistent_tsv = tmp_path / "inconsistent.tsv"
    inconsistent_tsv.write_text(
        ("sample_id\tintensity\tprotein_id\nS2,50.0,P4\n"),
        encoding="utf-8",
    )
    broken_encoding = tmp_path / "broken.tsv"
    broken_encoding.write_bytes(b"sample_id\tintensity\nS3\t10.0\nS4\t20.0\xff\n")

    report = scan_input_integrity(
        (
            invalid_tsv,
            inconsistent_tsv,
            broken_encoding,
        )
    )

    issue_codes = {
        (issue.path, issue.issue_code)
        for file_report in report.files
        for issue in file_report.issues
    }
    assert (str(invalid_tsv), "duplicate_id") in issue_codes
    assert (str(invalid_tsv), "invalid_numeric_value") in issue_codes
    assert (str(invalid_tsv), "empty_required_field") in issue_codes
    assert (str(inconsistent_tsv), "inconsistent_delimiter") in issue_codes
    assert (str(inconsistent_tsv), "malformed_row") in issue_codes
    assert (str(broken_encoding), "broken_encoding") in issue_codes

    rendered = render_input_integrity_issues_tsv(report)
    assert "issue_code" in rendered
    assert "invalid_numeric_value" in rendered


def test_scan_input_integrity_streams_large_file_without_read_text(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    large_tsv = tmp_path / "large_input.tsv"
    with large_tsv.open("w", encoding="utf-8", newline="") as handle:
        handle.write("sample_id\tintensity\tprotein_id\n")
        for index in range(5000):
            handle.write(f"S{index}\t{index + 1}.0\tP{index}\n")
        handle.write("S5000\t5001.0\tP5000\textra_column\n")

    def _forbid_read_text(
        self: Path, *args: object, **kwargs: object
    ) -> str:  # pragma: no cover - proof guard
        raise AssertionError(
            "scan_input_integrity must not read whole files with read_text"
        )

    monkeypatch.setattr(Path, "read_text", _forbid_read_text)

    report = scan_input_integrity((large_tsv,))
    file_report = report.files[0]

    assert file_report.scanned_row_count == 5001
    assert any(issue.issue_code == "malformed_row" for issue in file_report.issues)
    assert report.total_issue_count >= 1
