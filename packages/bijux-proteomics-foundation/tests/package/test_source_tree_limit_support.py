# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics_foundation.testing.source_tree_limits import (
    SourceFileLineCountException,
    build_source_tree_line_count_report,
)


def test_source_tree_line_count_report_classifies_approved_and_unexpected_files(
    tmp_path: Path,
) -> None:
    source_root = tmp_path / "src"
    source_root.mkdir()
    (source_root / "kept_small.py").write_text("x = 1\n")
    (source_root / "approved_large.py").write_text("x = 1\n" * 7)
    (source_root / "unexpected_large.py").write_text("x = 1\n" * 9)

    report = build_source_tree_line_count_report(
        source_root,
        ceiling=5,
        exceptions=(
            SourceFileLineCountException(
                relative_path="approved_large.py",
                allowed_line_count=7,
                temporary_reason="temporary large-file allowance for an owned surface",
            ),
        ),
    )

    assert report.scanned_file_count == 3
    assert report.skipped_marked_generated_count == 0
    assert tuple(item.relative_path for item in report.approved_over_ceiling) == (
        "approved_large.py",
    )
    assert tuple(item.line_count for item in report.approved_over_ceiling) == (7,)
    assert tuple(item.relative_path for item in report.unexpected_over_ceiling) == (
        "unexpected_large.py",
    )
    assert report.stale_exceptions == ()


def test_source_tree_line_count_report_flags_stale_and_exceeded_exceptions(
    tmp_path: Path,
) -> None:
    source_root = tmp_path / "src"
    source_root.mkdir()
    (source_root / "too_large.py").write_text("x = 1\n" * 8)
    (source_root / "no_longer_large.py").write_text("x = 1\n" * 4)

    report = build_source_tree_line_count_report(
        source_root,
        ceiling=5,
        exceptions=(
            SourceFileLineCountException(
                relative_path="too_large.py",
                allowed_line_count=7,
                temporary_reason="temporary large-file allowance for an owned surface",
            ),
            SourceFileLineCountException(
                relative_path="no_longer_large.py",
                allowed_line_count=6,
                temporary_reason="temporary large-file allowance that should be removed",
            ),
        ),
    )

    assert tuple(item.relative_path for item in report.unexpected_over_ceiling) == (
        "too_large.py",
    )
    assert tuple(item.relative_path for item in report.stale_exceptions) == (
        "no_longer_large.py",
    )


def test_source_tree_line_count_report_can_skip_marked_generated_files(
    tmp_path: Path,
) -> None:
    source_root = tmp_path / "src"
    source_root.mkdir()
    (source_root / "kept_small.py").write_text("x = 1\n", encoding="utf-8")
    (source_root / "generated_large.py").write_text(
        "# Generated generated-line-count fixture.\n"
        "# Regenerate with: ./.venv/bin/python -m repo.generated.line_count\n\n"
        + ("x = 1\n" * 20),
        encoding="utf-8",
    )

    report = build_source_tree_line_count_report(
        source_root,
        ceiling=5,
        exclude_marked_generated=True,
    )

    assert report.scanned_file_count == 1
    assert report.skipped_marked_generated_count == 1
    assert report.approved_over_ceiling == ()
    assert report.unexpected_over_ceiling == ()
